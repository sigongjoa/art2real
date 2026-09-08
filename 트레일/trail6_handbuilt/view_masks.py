# -*- coding: utf-8 -*-
"""판마다 **견갑만 남기는 마스크**. 크롭만으로는 목·어깨가 섞인다 (side white 16판).

    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b --python view_masks.py

    side  sh_pauldron.json 의 측면 윤곽 (있는 걸 쓴다)
    back  마스크가 없다 -> **메시 실루엣을 후면으로 투영**해서 만든다.
          형태는 이미 있으니(리토폴로지 723 쿼드) 원화에서 추측할 이유가 없다.
    front 대조군. panels.json 판 합집합이 이미 마스크다

산출: out/mask_<view>.npy (크롭 좌표계) · 판별 남는 판 수를 찍는다
"""
import bpy, os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mask2d
from mask2d import topix

OUT = os.path.join(HERE, "out")
MINPX = 40
VW = json.load(open(os.path.join(HERE, "parts", "views.json"), encoding="utf-8"))
SH = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))

# ── back 마스크: 메시를 후면으로 투영 ────────────────────────────────────────
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "panel_q800.blend"))
o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
me = o.data
nf = len(me.polygons)
V = np.empty(len(me.vertices)*3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
full = {}
for view, ax, sign in (("back", 0, -1.0), ("side", 1, 1.0)):
    m = np.zeros((mask2d.RES, mask2d.RES), bool)
    for p in me.polygons:
        vs = V[list(p.vertices)]
        py, px = topix(sign*vs[:, ax], vs[:, 2])
        # 경계상자로 채우면 실루엣이 부풀어 남의 부품을 문다 (후면에 적갈색이 들어왔다).
        # 부채꼴 삼각화 + 무게중심 좌표로 **면 안쪽만** 칠한다.
        for k in range(1, len(py) - 1):
            xa = np.array([px[0], px[k], px[k+1]], float)
            ya = np.array([py[0], py[k], py[k+1]], float)
            x0, x1 = int(xa.min()), int(np.ceil(xa.max())) + 1
            y0, y1 = int(ya.min()), int(np.ceil(ya.max())) + 1
            if x1 <= x0 or y1 <= y0:
                continue
            gy, gx = np.mgrid[y0:y1, x0:x1]
            qx, qy = gx + .5, gy + .5
            det = (ya[1]-ya[2])*(xa[0]-xa[2]) + (xa[2]-xa[1])*(ya[0]-ya[2])
            if abs(det) < 1e-9:
                continue
            w0 = ((ya[1]-ya[2])*(qx-xa[2]) + (xa[2]-xa[1])*(qy-ya[2])) / det
            w1 = ((ya[2]-ya[0])*(qx-xa[2]) + (xa[0]-xa[2])*(qy-ya[2])) / det
            hit = (w0 >= -.002) & (w1 >= -.002) & (w0 + w1 <= 1.002)
            if hit.any():
                m[gy[hit], gx[hit]] = True
    full[view] = m
    print("%s 메시 투영 실루엣 %d px" % (view, m.sum()))

# side 는 커밋된 윤곽이 있으면 그걸 쓴다 (실측이 추측보다 낫다)
sd = [np.array(SH["side"]["poly_yz"], float)]
for h in SH["side"].get("horns", []):
    if isinstance(h, dict) and "poly_yz" in h:
        sd.append(np.array(h["poly_yz"], float))
full["side"] = mask2d.raster(sd)
print("side 커밋된 윤곽 %d px" % full["side"].sum())

for view in ("side", "back"):
    x0, x1, y0, y1 = VW[view]["win"]
    sub = full[view][y0:y1, x0:x1]
    L = np.load(os.path.join(OUT, "_L_alb_%s.npy" % view))
    before = [int(v) for v in np.unique(L) if v > 1 and (L == v).sum() >= MINPX]
    keep = []
    for v in before:                                 # 판의 절반 이상이 마스크 안이면 남긴다
        mm = L == v
        if (mm & sub).sum() >= 0.5 * mm.sum() and (mm & sub).sum() >= MINPX:
            keep.append(v)
    np.save(os.path.join(OUT, "mask_%s.npy" % view), sub)
    np.save(os.path.join(OUT, "keep_%s.npy" % view), np.array(keep, np.int32))
    print("%-5s 판 %d -> %d개 (마스크 %d px, 크롭의 %.0f%%)"
          % (view, len(before), len(keep), sub.sum(), sub.mean()*100))
