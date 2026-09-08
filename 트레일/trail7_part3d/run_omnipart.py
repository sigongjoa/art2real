# -*- coding: utf-8 -*-
"""OmniPart(MIT) 로컬 실행. RTX 3050 8GB · torch 2.5.1+cu124 · py3.11 · run_partcrafter 와 같은 venv.

    venv/Scripts/python.exe run_omnipart.py in/pauldron_front.png in/pauldron_front_mask.npy out/op_front

PartCrafter 와 갈리는 점이 입력이다 — **2D 파트 마스크를 우리가 준다.** 어제 PartCrafter 가
뿔을 사방으로 뻗은 성게로 낸 건 뿔이 어디로 나야 하는지 몰라서였다. 여기서는 캡 1 · 뿔 4 를
화소로 찍어준다 (in/pauldron_front_mask.npy, 1024² int32, 0=배경).

윈도우 우회 세 가지:
  * shim/flash_attn        — 희소 어텐션은 백엔드 목록이 [xformers, flash_attn] 뿐이라 env 로 못 피한다.
                             둘 다 윈도우 휠이 없어 이름을 빌려주고 SDPA 로 받는다
  * shim/torch_scatter     — PartField 인코더가 쓰는 scatter 3종. 휠 없음 + nvcc 없음
  * process_utils 안 씀    — 그게 nvdiffrast·xatlas·pyvista·pymeshfix·igraph 를 끌고 온다.
                             판정기는 기하만 재니 텍스처 굽기가 통째로 필요 없다.
"""
import argparse, os, sys, time

os.environ.setdefault("ATTN_BACKEND", "flash_attn")   # 이름만 flash_attn — shim 이 SDPA 로 받는다
os.environ.setdefault("SPCONV_ALGO", "native")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")

import numpy as np
import cv2
import torch
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "shim"))
OP = os.path.join(HERE, "OmniPart")
sys.path.insert(0, OP)


def bake_exr(npy, exr):
    """part_id 맵을 OmniPart 규약대로 굽는다 — [h,w,3] float32, 세 채널에 같은 id."""
    m = np.load(npy).astype(np.float32)
    cv2.imwrite(exr, np.repeat(m[:, :, None], 3, axis=2))
    chk = cv2.imread(exr, cv2.IMREAD_UNCHANGED)
    assert chk is not None and chk.shape == m.shape + (3,), "EXR 를 못 썼다 (OpenEXR 지원 확인)"
    assert set(np.unique(chk[..., 0]).astype(int)) == set(np.unique(m).astype(int))
    return exr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("mask", help="1024² int32 .npy (0=배경) 또는 이미 구운 .exr")
    ap.add_argument("out")
    ap.add_argument("--steps", type=int, default=25)
    ap.add_argument("--guidance", type=float, default=7.5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--reuse", action="store_true", help="복셀·잠재를 이전 결과로 건너뛴다")
    ap.add_argument("--sscfg", type=float, default=7.5, help="희소구조 guidance. 7.5 에서 깊이가 뭉개지면 12 로")
    ap.add_argument("--nomesh", action="store_true", help="잠재까지만 — 메시는 mesh_from_slat.py 가 잇는다")
    a = ap.parse_args()

    img = os.path.abspath(os.path.join(HERE, a.image))
    out = os.path.abspath(os.path.join(HERE, a.out))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    mask = os.path.abspath(os.path.join(HERE, a.mask))
    if mask.endswith(".npy"):
        mask = bake_exr(mask, mask[:-4] + ".exr")
        print("마스크 EXR", mask)

    os.chdir(OP)
    from omegaconf import OmegaConf
    from huggingface_hub import hf_hub_download
    from modules.bbox_gen.models.autogressive_bbox_gen import BboxGen
    from modules.inference_utils import (load_img_mask, prepare_bbox_gen_input,
                                         prepare_part_synthesis_input, gen_mesh_from_bounds)
    from modules.part_synthesis.pipelines import OmniPartImageTo3DPipeline

    t0 = time.time()
    pf = hf_hub_download(repo_id="omnipart/OmniPart_modules", filename="partfield_encoder.ckpt", local_dir="ckpt")
    bg = hf_hub_download(repo_id="omnipart/OmniPart_modules", filename="bbox_gen.ckpt", local_dir="ckpt")
    print("가중치 (%.0fs)" % (time.time()-t0))

    torch.manual_seed(a.seed)
    img_white, img_black, ordered_mask, vis = load_img_mask(img, mask)
    vis.save(out + "_maskvis.png")
    print("파트 %d개 (배경 제외)" % int(ordered_mask.max()))

    pipe = OmniPartImageTo3DPipeline.from_pretrained("omnipart/OmniPart")
    pipe.to("cuda")   # TRELLIS Pipeline.to 는 self 를 안 돌려준다 — 체이닝 금지
    # 8GB 에서 파이프라인 전체가 7.33GiB 를 문다(실측). 안 쓰는 디코더를 먼저 버린다 —
    # formats=["mesh"] 라 가우시안·복사장 디코더는 한 번도 안 불린다 (omnipart_image_to_parts.py:376~380)
    for k in ("slat_decoder_gs", "slat_decoder_rf"):
        pipe.models.pop(k, None)
    torch.cuda.empty_cache()
    print("VRAM %.2fGiB (디코더 2개 버린 뒤)" % (torch.cuda.memory_allocated()/2**30))
    vx = out + "_voxel.npy"
    if a.reuse and os.path.exists(vx):
        coords = np.load(vx)                   # 시드 고정이라 같은 그림·같은 시드면 같은 복셀이다 (90초 절약)
    else:
        coords = pipe.get_coords(img_black, num_samples=1, seed=a.seed,
                                 sparse_structure_sampler_params={"steps": 25, "cfg_strength": a.sscfg}).cpu().numpy()
        np.save(vx, coords)
    print("복셀 %d개  (%.0fs)" % (len(coords), time.time()-t0))

    # 복셀을 뽑고 나면 희소구조 모델 둘은 쓸 일이 없다 (get_coords 전용)
    for k in ("sparse_structure_flow_model", "sparse_structure_decoder"):
        pipe.models.pop(k, None)
    torch.cuda.empty_cache()

    # 상자 생성기가 도는 동안 파이프라인을 통째로 CPU 로 내린다.
    # 8GB 에서는 디코더를 버린 것만으로 모자랐다 — 상자 생성기 forward 가 448MiB 를 더 달란다(실측).
    pipe.to("cpu")
    torch.cuda.empty_cache()

    cfg = OmegaConf.load("configs/bbox_gen.yaml").model.args
    cfg.partfield_encoder_path = pf
    cfg.decoder_use_flash_attention = False   # transformers 는 dist-info 로 flash_attn 을 확인해 shim 이 안 통한다.
                                              # 설정 스위치가 있어 소스를 안 고쳐도 된다 (autogressive_bbox_gen.py:104)
    bbm = BboxGen(cfg)
    bbm.load_state_dict(torch.load(bg), strict=False)
    bbm.to("cuda").eval().half()
    print("VRAM %.2fGiB (상자 생성기 올린 뒤)" % (torch.cuda.memory_allocated()/2**30))
    bboxes = bbm.generate(prepare_bbox_gen_input(out + "_voxel.npy", img_white, ordered_mask))["bboxes"][0]
    del bbm
    torch.cuda.empty_cache()
    pipe.to("cuda")
    np.save(out + "_bboxes.npy", bboxes)
    gen_mesh_from_bounds(bboxes).export(out + "_bboxes.glb")
    print("파트 상자 %d개  (%.0fs)" % (len(bboxes), time.time()-t0))

    psi = prepare_part_synthesis_input(out + "_voxel.npy", out + "_bboxes.npy", ordered_mask)

    from modules.part_synthesis.modules.sparse.basic import SparseTensor
    from modules.part_synthesis.representations.mesh.cube2mesh import SparseFeatures2Mesh

    # get_slat 을 그대로 못 쓴다 — 그 안의 decode_slat 이 파트 전부를 **한 번에** 메시로 편다.
    # 8GB 에서 거기서 터졌다(decoder_mesh.py:209, spconv OOM). 조립을 풀어 하나씩 편다.
    sl = out + "_slat.npz"
    if a.reuse and os.path.exists(sl):
        z = np.load(sl)                    # 샘플링도 시드 고정이라 재현된다 (70초 절약)
        slat = SparseTensor(coords=torch.from_numpy(z["coords"]).cuda(),
                            feats=torch.from_numpy(z["feats"]).cuda())
    else:
        cond = pipe.get_cond(img_black.unsqueeze(0))
        torch.manual_seed(a.seed)
        slat = pipe.sample_slat(cond, psi["coords"], [psi["part_layouts"]], psi["masks"],
                                {"steps": a.steps, "cfg_strength": a.guidance})
        slat = pipe.divide_slat(slat, [psi["part_layouts"]])
        np.savez(sl, coords=slat.coords.cpu().numpy(), feats=slat.feats.float().cpu().numpy())
        del cond
    print("잠재 파트 %d개  (%.0fs)" % (slat.shape[0], time.time()-t0))

    for k in ("image_cond_model", "slat_flow_model"):   # 여기서부터 안 쓴다
        pipe.models.pop(k, None)
    torch.cuda.empty_cache()

    # 파트 수보다 하나 많으면 0번이 전체 형태다 (upstream save_parts_outputs 가 그걸 건너뛴다).
    # **그걸 펴지 않는다** — 제일 크고 어차피 버린다. 8GB 에서 OOM 이 나던 게 이 한 덩어리였다.
    # (fp16 autocast 로 줄이는 길은 막혔다: 디코더가 h.type(x.dtype) 로 입력 dtype 을 따라가는데
    #  메시 추출기 안은 fp32 버퍼를 쓴다 — utils_cube.get_dense_attrs)
    if a.nomesh:
        print("잠재까지 저장했다 — mesh_from_slat.py 로 이으면 된다")
        return

    # 메시 추출만 CPU 로 내린다. FlexiCubes 격자가 res=256(잠재 64×4) 고정이라
    # 조밀 텐서 하나가 1.3GiB, 큐브 인덱스가 1GiB 다 — 8GB 에서 GPU 로는 못 편다.
    # 희소 합성곱·업샘플은 GPU 에 그대로 두고 마지막 단계만 옮긴다.
    dec = pipe.models["slat_decoder_mesh"]
    cpu_ext = SparseFeatures2Mesh(device="cpu", res=dec.mesh_extractor.res,
                                  use_color=dec.mesh_extractor.use_color)

    class _CpuFeats:                       # cube2mesh 는 .coords 와 .feats 만 본다
        def __init__(self, t):
            self.coords, self.feats = t.coords.cpu(), t.feats.float().cpu()

    def to_representation_cpu(x):
        return [cpu_ext(_CpuFeats(x[i]), training=False) for i in range(x.shape[0])]

    dec.to_representation = to_representation_cpu

    skip0 = slat.shape[0] == int(ordered_mask.max()) + 1
    print("VRAM %.2fGiB (펼치기 직전)  0번 건너뜀=%s" % (torch.cuda.memory_allocated()/2**30, skip0))
    meshes = []
    for i in range(slat.shape[0]):
        if skip0 and i == 0:
            meshes.append(None)
            continue
        one = SparseTensor(coords=slat[i].coords, feats=slat[i].feats)
        meshes.append(dec(one)[0])
        torch.cuda.empty_cache()
        print("  펼침 %d/%d  VRAM %.2fGiB" % (i, slat.shape[0]-1, torch.cuda.memory_allocated()/2**30))

    sc = trimesh.Scene()
    for i, m in enumerate(meshes):
        if m is None:
            continue
        tm = trimesh.Trimesh(m.vertices.detach().cpu().numpy(), m.faces.detach().cpu().numpy())
        j = i-1 if skip0 else i
        tm.export("%s_p%d.obj" % (out, j))
        sc.add_geometry(tm, node_name="part%d" % j)
        print("  파트%d  면 %d" % (j, len(tm.faces)))
    sc.export(out + ".glb")
    print("저장 %s.glb  (%.0fs)" % (out, time.time()-t0))


if __name__ == "__main__":
    main()
