# -*- coding: utf-8 -*-
"""영상 35 용 3D — 시험 부품 6 개의 정답 · 1~3 판 예측 STL + 학습 전 안개(부드러운 점유의 등치면) · 점수 json"""
import os, sys, json, glob, numpy as np, torch, trimesh
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from 평가 import 메시
O = "G:/art2real/원화3d/과정/영상05/장난감/35_외우기만한AI/결과"; os.makedirs(O, exist_ok=True)
R = os.path.dirname(H); ids = list(range(3600, 3606)); 점수 = {}
for k, i in enumerate(ids):
    Q = json.load(open(os.path.join(H, "정답", "%04d.json" % i), encoding="utf-8")); 메시(Q).export(os.path.join(O, "%d_정답.stl" % k))
    for 판, d in (("1판", "조각0"), ("2판", "조각1"), ("3판", "조각2")):
        E = json.load(open(os.path.join(R, d, "평가.json"), encoding="utf-8")); P = E["예측"][i - 3600]
        try: 메시(P).export(os.path.join(O, "%d_%s.stl" % (k, 판)))
        except Exception as e: print("못 지음", k, 판, e)
        점수["%d_%s" % (k, 판)] = E["디코더"][i - 3600]["edge_f1"]
json.dump(점수, open(os.path.join(O, "점수.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
# 학습 전 안개: 무작위 디코더의 부드러운 점유(τ 0.05) → 0.5 등치면
from 조각 import 격자, 점유, 정답칸
from 학습 import 디코더, K
from skimage.measure import marching_cubes
torch.manual_seed(0); n = 48; g = 격자(n, "cuda")[None]; X = torch.from_numpy(np.load(os.path.join(H, "특징.npy")))
m = 디코더().cuda()
with torch.no_grad():
    lg, c, s = m(X[[2]].cuda().float()); occ = 점유(g, lg.softmax(-1), c, s, 0.05)[0].reshape(n, n, n).cpu().numpy()
v, f, _, _ = marching_cubes(occ, level=min(0.5, occ.max() * 0.6)); v = v / n * 1.1 - .05
trimesh.Trimesh((v - .5) * 2, f).export(os.path.join(O, "안개.stl"))
메시(json.load(open(os.path.join(H, "정답", "0002.json"), encoding="utf-8"))).export(os.path.join(O, "안개_정답.stl"))
print("ok", 점수)
