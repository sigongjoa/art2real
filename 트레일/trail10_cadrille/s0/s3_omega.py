# -*- coding: utf-8 -*-
"""S3 — 학습 없는 cadrille 를 오메가몬 머리에 바로: TripoSG T6 머리를 부위 20 개(PartField 군집)로 나눠 부위마다 설계도 → 실행 → 머리 좌표로 되돌려 합침 (2026-10-05)
python s0/s3_omega.py <모드 pc|img>  →  원화3d/out/오메가몬2/블렌더/cadrille_<모드>.ply · s0/omega/<모드>/부위NN.py · 결과.json"""
import os, sys, json, time, numpy as np, torch, trimesh
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.dirname(H), os.path.join(H, "stub"), H]
from transformers import AutoProcessor
from cadrille import Cadrille, collate
import s0 as S
B = "G:/art2real/원화3d/out/오메가몬2/블렌더/"; L = "G:/art2real/원화3d/out/오메가몬2/지표/트리포분할/"
mode = sys.argv[1]; O = os.path.join(H, "omega", mode); os.makedirs(O, exist_ok=True)
T6 = trimesh.load(B + "트리포_T6.ply", process=False); lab = np.load(L + "트리포_T6_라벨20.npy")
G = json.load(open(L + "트리포_T6_그래프20.json", encoding="utf-8")); 이름 = {d["id"]: d["이름(눈)"] for d in G["노드"]}
W = os.path.join(os.path.dirname(H), "weights")
model = Cadrille.from_pretrained(os.path.join(W, "cadrille"), torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda")
proc = AutoProcessor.from_pretrained(os.path.join(W, "qwen2vl2b"), min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28, padding_side="left")
parts, res = [], {}
for k in sorted(set(lab.tolist())):
    if "지움" in 이름.get(k, ""): continue
    sub = trimesh.Trimesh(T6.vertices, T6.faces[lab == k], process=True); sub.remove_unreferenced_vertices()
    lo, hi = sub.bounds; c = (lo + hi) / 2; s = (hi - lo).max()
    u = sub.copy(); u.apply_translation(-c); u.apply_scale(1 / s); u.apply_translation([0.5] * 3)
    r = {"이름": 이름.get(k, str(k))}
    try:
        it = S.item_pc(u) if mode == "pc" else S.item_img(u)[0]
        it["file_name"] = str(k); b = collate([it], processor=proc, n_points=256, eval=True)
        with torch.no_grad():
            out = model.generate(input_ids=b["input_ids"].cuda(), attention_mask=b["attention_mask"].cuda(), point_clouds=b["point_clouds"].cuda(), is_pc=b["is_pc"].cuda(), is_img=b["is_img"].cuda(),
                                 pixel_values_videos=b["pixel_values_videos"].cuda() if b.get("pixel_values_videos") is not None else None,
                                 video_grid_thw=b["video_grid_thw"].cuda() if b.get("video_grid_thw") is not None else None, max_new_tokens=768)
        code = proc.batch_decode([out[0][len(b["input_ids"][0]):]], skip_special_tokens=True)[0]
        open(os.path.join(O, "부위%02d.py" % k), "w", encoding="utf-8").write(code)
        pm = S.run_code(code); pm.apply_scale(1 / 200.0); pm.apply_translation([0.5] * 3)   # 코드 좌표 → 단위 상자
        pm.apply_translation([-0.5] * 3); pm.apply_scale(s); pm.apply_translation(c)          # 단위 상자 → 머리 좌표
        parts.append(pm); r["실행"] = True; r["면"] = len(pm.faces)
    except Exception as e:
        r["실행"] = False; r["오류"] = (str(e) or type(e).__name__)[:120]
    res[k] = r; print(k, r, flush=True)
json.dump(res, open(os.path.join(O, "결과.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
m = trimesh.util.concatenate(parts); m.visual.vertex_colors = np.tile([228, 232, 240, 255], (len(m.vertices), 1)).astype(np.uint8)
m.export(B + f"cadrille_{mode}.ply"); print("부위", len(parts), "/", len(res))
