# -*- coding: utf-8 -*-
"""캐시한 잠재(`*_slat.npz`)를 메시로만 편다. run_omnipart.py 의 마지막 단계를 떼어낸 것.

    venv/Scripts/python.exe mesh_from_slat.py out/op_front            # 남은 파트 전부
    venv/Scripts/python.exe mesh_from_slat.py out/op_front --part 2   # 한 파트만

왜 떼어냈나: 메시 추출이 CPU 라 느린데(파트당 수 분) 그동안 앞 단계(파이프라인 적재 2분,
복셀 90초, 잠재 70초)를 매번 다시 태울 이유가 없다. 파트 하나 끝날 때마다 OBJ 로 떨군다.

디코더 하나만 올린다 — 8GB 에 1.6GiB 면 된다.
"""
import argparse, os, sys, time

os.environ.setdefault("ATTN_BACKEND", "flash_attn")
os.environ.setdefault("SPCONV_ALGO", "native")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import numpy as np
import torch
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "shim"))
sys.path.insert(0, os.path.join(HERE, "OmniPart"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", help="run_omnipart.py 에 준 것과 같은 접두사")
    ap.add_argument("--part", type=int, default=None, help="이 파트만 (0=전체형태, 보통 건너뜀)")
    ap.add_argument("--skip0", type=int, default=1)
    ap.add_argument("--maxvox", type=int, default=0, help="이 복셀 수를 넘는 파트는 건너뛴다 (0=제한없음)")
    a = ap.parse_args()
    out = os.path.abspath(os.path.join(HERE, a.out))

    os.chdir(os.path.join(HERE, "OmniPart"))
    from modules.part_synthesis import models
    from modules.part_synthesis.modules.sparse.basic import SparseTensor
    from modules.part_synthesis.representations.mesh.cube2mesh import SparseFeatures2Mesh

    z = np.load(out + "_slat.npz")
    slat = SparseTensor(coords=torch.from_numpy(z["coords"]).cuda(),
                        feats=torch.from_numpy(z["feats"]).cuda())
    n = slat.shape[0]

    t0 = time.time()
    dec = models.from_pretrained("omnipart/OmniPart/slat_decoder_mesh/model").cuda().eval()
    print("디코더 적재 %.0fs · VRAM %.2fGiB · 잠재 파트 %d개" % (time.time()-t0, torch.cuda.memory_allocated()/2**30, n))

    # 조밀 격자(res=256)만 CPU 로. 8GB 에서 이 단계가 6.6GiB 를 달라고 해서 터졌다.
    cpu_ext = SparseFeatures2Mesh(device="cpu", res=dec.mesh_extractor.res,
                                  use_color=dec.mesh_extractor.use_color)

    class _CpuFeats:                        # cube2mesh 는 .coords 와 .feats 만 본다
        def __init__(self, t):
            self.coords, self.feats = t.coords.cpu(), t.feats.float().cpu()

    dec.to_representation = lambda x: [cpu_ext(_CpuFeats(x[i]), training=False) for i in range(x.shape[0])]

    # GPU 쪽 FlexiCubes 격자는 이제 죽은 무게다 — reg_v/reg_c 가 res=256 이라 1.5GiB 를 문다.
    # 이걸 버려야 큰 파트(복셀 16k)의 희소 합성곱이 8GB 안에 들어온다.
    dec.mesh_extractor = cpu_ext
    torch.cuda.empty_cache()
    print("격자 버린 뒤 VRAM %.2fGiB" % (torch.cuda.memory_allocated()/2**30))

    dev = "cuda"
    # 파트 하나가 전체의 95% 를 드는 일이 있다(op_clean12 의 1번 = 16136/17037).
    # 작은 것부터 처리해 CPU 로 떨어지는 걸 맨 뒤로 민다.
    nv = np.bincount(z["coords"][:, 0], minlength=n)
    todo = [a.part] if a.part is not None else sorted(range(a.skip0, n), key=lambda i: nv[i])
    if a.maxvox:
        skipped = [i for i in todo if nv[i] > a.maxvox]
        todo = [i for i in todo if nv[i] <= a.maxvox]
        if skipped:
            print("복셀 %d 초과로 건너뜀: %s" % (a.maxvox, ["%d(%d)" % (i, nv[i]) for i in skipped]))
    for i in todo:
        f = "%s_p%d.obj" % (out, i - a.skip0)
        if os.path.exists(f):
            print("  파트%d 이미 있음 — 건너뜀" % (i - a.skip0))
            continue
        t = time.time()
        # 복셀이 많은 파트는 희소 합성곱마저 8GB 를 넘는다 — 넘치면 그 파트만 CPU 로 민다.
        # ponytail: 한 번 넘치면 남은 파트도 CPU. 파트마다 되돌리는 것보다 싸다.
        try:
            if dev == "cuda":
                m = dec(SparseTensor(coords=slat[i].coords, feats=slat[i].feats))[0]
            else:
                raise torch.OutOfMemoryError("cpu 모드")
        except torch.OutOfMemoryError:
            if dev == "cuda":
                print("  VRAM 초과 — 여기서부터 디코더를 CPU 로 내린다")
                dec.cpu(); dev = "cpu"
            torch.cuda.empty_cache()
            m = dec(SparseTensor(coords=slat[i].coords.cpu(), feats=slat[i].feats.float().cpu()))[0]
        torch.cuda.empty_cache()
        tm = trimesh.Trimesh(m.vertices.detach().cpu().numpy(), m.faces.detach().cpu().numpy())
        tm.export(f)
        print("  파트%d  정점 %d  면 %d  (%.0fs)" % (i - a.skip0, len(tm.vertices), len(tm.faces), time.time()-t))

    objs = sorted(f for f in os.listdir(os.path.dirname(out))
                  if f.startswith(os.path.basename(out) + "_p") and f.endswith(".obj"))
    if len(objs) == n - a.skip0:
        sc = trimesh.Scene()
        for f in objs:
            sc.add_geometry(trimesh.load(os.path.join(os.path.dirname(out), f)), node_name=f[:-4])
        sc.export(out + ".glb")
        print("저장 %s.glb  (파트 %d개)" % (out, len(objs)))
    else:
        print("파트 %d/%d — 아직 다 안 됐다" % (len(objs), n - a.skip0))


if __name__ == "__main__":
    main()
