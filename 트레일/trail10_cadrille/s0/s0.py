# -*- coding: utf-8 -*-
"""S0 — cadrille 를 학습 없이 우리 8 GB 에서: 원래 일(회색 렌더 · 점 → CadQuery)을 하는가 (2026-10-05)
대조: DeepCAD 시험 메시 3 개(논문 분포 · 배관 확인) · 대상: 우리 CAD v57 부품 4 개(차양 · 뿔 · 얼굴판 · 마스크)
정규화는 DeepCAD 시험과 같게: 긴 변 1 · 가운데 0.5 (단위 상자). 점 모드 입력 = (점 − 0.5)·2, 출력 코드 좌표/100 ≈ 그 좌표.
python s0/s0.py  →  s0/out/<이름>_<모드>.py · .stl · s0/out/결과.json · s0/out/시트.png"""
import os, sys, glob, json, time, traceback
import numpy as np, torch, trimesh
from PIL import Image, ImageOps
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "stub")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # pytorch3d 는 FPS 에만 쓰임 → 자리표시
from functools import partial
from transformers import AutoProcessor
from cadrille import Cadrille, collate
R = os.path.dirname(os.path.abspath(__file__)); O = os.path.join(R, "out"); os.makedirs(O, exist_ok=True)
W = os.path.join(os.path.dirname(R), "weights")

def unit(m):  # 긴 변 1 · 가운데 0.5
    m = m.copy(); lo, hi = m.bounds; m.apply_translation(-(lo + hi) / 2); m.apply_scale(1.0 / (hi - lo).max()); m.apply_translation([0.5, 0.5, 0.5]); return m

def fps(v, k):
    idx = [0]; d = np.linalg.norm(v - v[0], axis=1)
    for _ in range(k - 1): i = int(d.argmax()); idx.append(i); d = np.minimum(d, np.linalg.norm(v - v[i], axis=1))
    return v[idx]

def item_pc(m):
    v, _ = trimesh.sample.sample_surface(m, 8192); return {"point_cloud": ((fps(v, 256) - 0.5) * 2).astype(np.float32), "description": "Generate cadquery code"}

def item_img(m):
    import open3d   # 0.18 은 이 PC 에서 세그폴트 · 0.19 는 됨 → 학습 때와 같은 open3d 렌더
    from dataset import mesh_to_image
    o = open3d.geometry.TriangleMesh(); o.vertices = open3d.utility.Vector3dVector(np.asarray(m.vertices)); o.triangles = open3d.utility.Vector3iVector(np.asarray(m.faces))
    o.paint_uniform_color(np.array([255, 255, 136]) / 255.0); o.compute_vertex_normals()
    ims = [ImageOps.expand(mesh_to_image(o, camera_distance=-0.9, front=f, img_size=128), border=3, fill="black") for f in [[1, 1, 1], [-1, -1, -1], [-1, 1, -1], [1, -1, 1]]]
    a = [np.array(i) for i in ims]; g = Image.fromarray(np.vstack((np.hstack((a[0], a[1])), np.hstack((a[2], a[3])))))
    return {"video": [g], "description": "Generate cadquery code"}, g

def run_code(code):
    import cadquery as cq
    ns = {"cq": cq}; exec(code, ns)
    obj = ns.get("r") or next((v for v in ns.values() if isinstance(v, cq.Workplane)), None)
    if obj is None: raise RuntimeError("Workplane 없음")
    p = os.path.join(O, "_tmp.stl"); cq.exporters.export(obj, p); return trimesh.load(p)

def iou(a, b, n=64):
    g = (np.indices((n, n, n)).reshape(3, -1).T + 0.5) / n * 2 - 1
    ia = a.contains(g) if a.is_watertight else np.zeros(len(g), bool); ib = b.contains(g) if b.is_watertight else np.zeros(len(g), bool)
    u = (ia | ib).sum(); return float((ia & ib).sum() / u) if u else 0.0

t0 = time.time()
model = Cadrille.from_pretrained(os.path.join(W, "cadrille"), torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda")
proc = AutoProcessor.from_pretrained(os.path.join(W, "qwen2vl2b"), min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28, padding_side="left")
print("모델", round(time.time() - t0, 1), "s · GPU", round(torch.cuda.memory_allocated() / 1e9, 2), "GB")
res = {}
for f in sorted(glob.glob(os.path.join(R, "in", "*.stl"))):
    name = os.path.basename(f)[:-4]; gt = unit(trimesh.load(f)); gt2 = gt.copy(); gt2.apply_translation([-0.5] * 3); gt2.apply_scale(2.0)
    gt.export(os.path.join(O, name + "_gt.stl"))
    for mode in ("pc", "img"):
        key = f"{name}_{mode}"; r = {}
        try:
            if mode == "pc": it = item_pc(gt)
            else: it, g = item_img(gt); g.save(os.path.join(O, key + "_입력.png"))
            it["file_name"] = key
            b = collate([it], processor=proc, n_points=256, eval=True)
            t = time.time()
            with torch.no_grad():
                out = model.generate(input_ids=b["input_ids"].cuda(), attention_mask=b["attention_mask"].cuda(), point_clouds=b["point_clouds"].cuda(), is_pc=b["is_pc"].cuda(), is_img=b["is_img"].cuda(),
                                     pixel_values_videos=b["pixel_values_videos"].cuda() if b.get("pixel_values_videos") is not None else None,
                                     video_grid_thw=b["video_grid_thw"].cuda() if b.get("video_grid_thw") is not None else None, max_new_tokens=768)
            code = proc.batch_decode([out[0][len(b["input_ids"][0]):]], skip_special_tokens=True)[0]
            r["초"] = round(time.time() - t, 1); r["최대GPU"] = round(torch.cuda.max_memory_allocated() / 1e9, 2)
            open(os.path.join(O, key + ".py"), "w", encoding="utf-8").write(code)
            pm = run_code(code); pm.apply_scale(1 / 100.0); pm.export(os.path.join(O, key + ".stl"))
            r["실행"] = True; r["IoU"] = round(iou(gt2, pm), 3); r["코드줄"] = code.count("\n") + 1
        except Exception as e:
            r["실행"] = r.get("실행", False); r["오류"] = (str(e) or type(e).__name__)[:200]
        res[key] = r; print(key, r, flush=True)
json.dump(res, open(os.path.join(O, "결과.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
