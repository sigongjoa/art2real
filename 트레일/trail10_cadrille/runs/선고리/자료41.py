# 쇼츠 41 재료 PNG (venv 에서) — 부품 #10 · 화소 깎기 조각 빨강 · 화소 주머니 테두리 · 선 고리 결과 돌림 · 단계 PNG 칸 잘라내기
import os, sys, json, numpy as np, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [H, os.path.join(R, "윤곽2"), os.path.join(R, "조각0"), os.path.join(R, "윤곽0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
from render import render
from PIL import Image
O = "G:/art2real/out/영상05/대화/41_부스러기범인/자료/"; i = 10
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 그(m, a, cols=None, c=480):
    return render(np.asarray(m.vertices), np.asarray(m.faces), [np.cos(a), np.sin(a), .7], img_size=c, cols=cols)
화 = 정(trimesh.load(os.path.join(R, "윤곽2", "결과_기울기02g", "%02d_깎음.stl" % i)))
조 = 화.split(only_watertight=False); 큰 = max(조, key=lambda m: len(m.faces))
cols = np.tile([0.45, 0.68, 0.98], (len(화.faces), 1))
# 큰 덩어리 밖 면 = 조각 → 빨강 (면 중심이 큰 덩어리 면 중심 집합에 없으면)
from scipy.spatial import cKDTree
d, _ = cKDTree(큰.triangles_center).query(화.triangles_center); cols[d > 1e-6] = [0.95, 0.2, 0.2]
선 = 정(trimesh.load(os.path.join(H, "결과_A", "%02d_선고리.stl" % i)))
for t in range(12):
    a = 2 * np.pi * t / 12
    그(화, a, cols).save(O + "화소_%02d.png" % t); 그(선, a, np.tile([0.45, 0.68, 0.98], (len(선.faces), 1))).save(O + "선고리_%02d.png" % t)
# 화소 주머니 테두리 (앞 그림 · 256²)
import 깊이깎기 as G
from 실물보기 import 실물보기
from s0 import unit
S = [r["부품"] for k in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % k), encoding="utf-8"))]
m = unit(trimesh.load(G.RR + S[i], force="mesh")); mb = trimesh.load(os.path.join(R, "윤곽0", "결과", "%02d_교차.stl" % i)); mb.apply_translation([1, 1, 1]); mb.apply_scale(.5)
Sr, Dr = 실물보기(m, 256); Sh, Dh = 실물보기(mb, 256)
k = 4; a = np.full((256, 256, 3), 255, np.uint8); a[Sr[k] > .5] = (232, 236, 244)
rng = np.random.default_rng(1)
for pts, dd, *_ in G.주머니(Dr[k], Dh[k], Sr[k]):
    p = np.array([[(b + .05) / 1.1 * 256 - .5, (q + .05) / 1.1 * 256 - .5] for q, b in pts], np.int32)
    cv2.fillPoly(a, [p], tuple(int(c) for c in rng.integers(80, 230, 3))); cv2.polylines(a, [p], True, (220, 40, 40), 1)
Image.fromarray(a).resize((768, 768), Image.NEAREST).save(O + "화소테두리.png")
# 단계 PNG 칸 (3 = 닫힌 고리 · 0 = 입력)
P = Image.open(os.path.join(H, "단계_%02d.png" % i)); Wd, Hd = 1000, 820
for j, n in ((0, "입력"), (2, "벡터"), (3, "고리"), (4, "깊이")):
    x, y = 10 + (j % 2) * (Wd + 10), 10 + (j // 2) * (Hd + 10); P.crop((x, y + 72, x + Wd, y + Hd - 200)).save(O + "단계_%s.png" % n)
print("ok")
