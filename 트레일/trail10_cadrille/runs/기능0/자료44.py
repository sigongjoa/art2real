# 쇼츠 44 「시험지를 새로 만들었다」 재료 — 화면 부품은 변형 허용 라이선스만(검증 32 · 개발은 42 편 격자 18) · 10-12
# python runs/기능0/자료44.py  →  G:/art2real/out/영상05/대화/44_시험지/자료/
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
from render import render
from PIL import Image
O = "G:/art2real/out/영상05/대화/44_시험지/자료/"; os.makedirs(O, exist_ok=True); RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
L = json.load(open(os.path.join(H, "라벨.json"), encoding="utf-8"))["부품"]
뺌 = {2, 3, 18, 19, 20, 21, 28, 29}   # ND · 표준 라이선스 — 화면 밖
검 = [i for i in range(40) if i not in 뺌]; 개 = [1, 2, 3, 4, 5, 6, 8, 10, 13, 17, 20, 21, 22, 24, 31, 32, 33, 34]
노, 초, 회 = (0.95, 0.85, 0.35), (0.55, 0.8, 0.5), (0.6, 0.6, 0.65)
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 찍(m, 색, c=240, v=(1, .6, .8)): return Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), list(v), img_size=c, cols=np.tile(색, (len(m.faces), 1)))))
def 사람(k): return 정(trimesh.load(RR + L[k]["부품"], force="mesh"))
for i in 검: 찍(사람("검증/%02d" % i), 노).save(O + "검_%02d.png" % i)
for i in 개: 찍(사람("시험/%02d" % i), 노).save(O + "개_%02d.png" % i)
for t in range(12):   # 터빈 · 바퀴 돌림판(회전체)
    a = 2 * np.pi * t / 12; v = [np.cos(a), np.sin(a), .7]
    for nm, k in (("터빈", "검증/30"), ("바퀴", "검증/32")): 찍(사람(k), 노, 420, v).save(O + "%s_%02d.png" % (nm, t))
for i in (13, 21, 33):   # 가린 쌍 보기: 사람 / 교차 · 사람 / 우리(앞 판 B_모델T)
    찍(사람("시험/%02d" % i), 노, 300).save(O + "쌍사_%02d.png" % i)
    for nm, d in (("쌍교", "B_교차"), ("쌍우", "B_모델T")): 찍(정(trimesh.load(os.path.join(H, d, "%02d.stl" % i))), 초, 300).save(O + "%s_%02d.png" % (nm, i))
json.dump({"검": 검, "개": 개}, open(O + "목록.json", "w")); print("ok", len(검), len(개))
