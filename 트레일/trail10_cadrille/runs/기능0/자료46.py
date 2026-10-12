# 쇼츠 46 「재심」 재료 — 화면 부품은 변형 허용만: 검증2 #13 VacPack(BY-NC) · #38 BB-8(BY-NC) · #31 Curveball Mech(BY) · 시험 #34 Dummy13(42 편 확인) · #11 Volt(ND) 는 뺌 · 10-12
# python runs/기능0/자료46.py  →  G:/art2real/out/영상05/대화/46_재심/자료/
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
from render import render
from PIL import Image
O = "G:/art2real/out/영상05/대화/46_재심/자료/"; os.makedirs(O, exist_ok=True); RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
L = json.load(open(os.path.join(H, "라벨.json"), encoding="utf-8"))["부품"]
노, 파, 주 = (0.95, 0.85, 0.35), (0.45, 0.68, 0.98), (0.95, 0.6, 0.4)
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 찍(m, 색, c=360, v=(1, .6, .8)): return Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), list(v), img_size=c, cols=np.tile(색, (len(m.faces), 1)))))
for s, i, 접 in (("검증2", 13, "_검증2"), ("검증2", 38, "_검증2"), ("검증2", 31, "_검증2"), ("시험", 34, "")):
    k = "%s/%02d" % (s, i); 찍(정(trimesh.load(RR + L[k]["부품"], force="mesh")), 노).save(O + "사_%s%02d.png" % (s, i))
    찍(정(trimesh.load(os.path.join(H, "B_교차%s/%02d.stl" % (접, i)))), 파).save(O + "교_%s%02d.png" % (s, i)); 찍(정(trimesh.load(os.path.join(H, "B_C%s/%02d.stl" % (접, i)))), 주).save(O + "C_%s%02d.png" % (s, i))
for t in range(12):   # 링 돌림판 — 각진 다각형 대 둥근 링
    a = 2 * np.pi * t / 12; v = [np.cos(a), np.sin(a), .5]
    for nm, d in (("링교", "B_교차_검증2"), ("링C", "B_C_검증2")): 찍(정(trimesh.load(os.path.join(H, d, "13.stl"))), 파 if nm == "링교" else 주, 420, v).save(O + "%s_%02d.png" % (nm, t))
print("ok")
