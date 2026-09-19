# -*- coding: utf-8 -*-
"""등위값별 메시 → 3판맞춤 → 불리언∩hull → 45° 여분·부족·IoU · 부피 대 정답. 관찰."""
import os, sys, json, gc
import numpy as np, cv2, trimesh
HERE = r"G:\art2real\원화3d"; sys.path.insert(0, HERE)
for d in ("실험_20260913", "실험_20260915", "실험_20260918"): sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import win as W, 깊이색 as DC
from 조각묶기 import masks_of
from 불리언 import boolean_hull
import 생성3D as G3

CASE = "mech_Drill_8uBbH7Dvmb"
OUT = os.path.join("out", "등위")
J = json.load(open(os.path.join(OUT, CASE + "_levels.json"), encoding="utf-8"))

def rotz(P, deg):
    a = np.deg2rad(deg); c, s = np.cos(a), np.sin(a)
    return P @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T
def sil(m, deg):
    return np.asarray(W.silhouette(rotz(np.asarray(m.vertices), deg), np.asarray(m.faces), "front", None)).astype(bool)
def iou(a, b): return float((a & b).sum() / max((a | b).sum(), 1))
def fit(g, masks):
    _, V, yaw, mir = G3.orient(g.vertices, masks)
    return trimesh.Trimesh(G3.fit_to_art(V, masks), np.asarray(g.faces), process=False)
def ov(t, s):
    img = np.full(t.shape + (3,), 255, np.uint8); img[t & s] = (200, 200, 200); img[t & ~s] = (225, 60, 60); img[s & ~t] = (60, 110, 225)
    ys, xs = np.nonzero(t | s); return img[ys.min()-10:ys.max()+10, xs.min()-10:xs.max()+10]

truth = trimesh.load(os.path.join("out", "시트", CASE, "truth.glb"), force="mesh")
masks, bs = masks_of(CASE)
T = {d: sil(truth, d) for d in (0, 45, 90)}
vt = abs(truth.volume)
print("정답 부피 %.5f" % vt)
print("%6s  %8s  %8s | %s | %s | %s" % ("level", "생부피비", "컷부피비", "45° 여분 부족 IoU (생)", "45° 여분 부족 IoU (∩hull)", "0°/90° 부족 (∩hull)"))
tiles = []; rows = []
for r in J["levels"]:
    g = fit(trimesh.load(r["path"], force="mesh"), masks)
    D = boolean_hull(g, masks, bs)
    def st(m, d):
        s = sil(m, d); t = T[d]
        return (s & ~t).sum() / t.sum(), (t & ~s).sum() / t.sum(), iou(t, s)
    og, ug, ig = st(g, 45); od, ud, idd = st(D, 45)
    _, u0, _ = st(D, 0); _, u9, _ = st(D, 90)
    print("%+6.2f  %8.3f  %8.3f | %.3f %.3f %.3f | %.3f %.3f %.3f | %.3f %.3f"
          % (r["level"], abs(g.volume) / vt, abs(D.volume) / vt, og, ug, ig, od, ud, idd, u0, u9), flush=True)
    rows.append(dict(level=r["level"], gen_vol=abs(g.volume) / vt, cut_vol=abs(D.volume) / vt,
                     gen45=dict(over=og, miss=ug, iou=ig), cut45=dict(over=od, miss=ud, iou=idd), miss0=u0, miss90=u9))
    tiles.append(("level %+.2f  IoU %.3f  여분 %.3f 부족 %.3f" % (r["level"], idd, od, ud), [ov(T[45], sil(D, 45))]))
    del g, D; gc.collect()
json.dump(rows, open(os.path.join(OUT, CASE + "_등위재기.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
DC.grid(tiles, ["정답 vs ∩hull @45°"], "TripoSG 마칭큐브 등위값 — 드릴 · 불리언∩hull 뒤 45° 겹침",
        "빨강 정답에만 · 파랑 우리에만. 등위값을 안쪽으로 잡으면 파랑(두께 여분)이 줄어야 한다 — 대신 빨강(부족)이 언제 생기나",
        os.path.join(OUT, CASE + "_등위.png"))
print("saved", os.path.join(OUT, CASE + "_등위.png"))
