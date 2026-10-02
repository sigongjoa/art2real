# -*- coding: utf-8 -*-
"""장마다 뽑힌 3D 껍질을 면으로 나누기 (10-02 사용자 「뽑힌 3D 에서 면분할 먼저 해 봐 · 면분할 안 하니깐 이상하게 붙이잖아」).
껍질 = 각도접힌판.py 의 판_<n>.ply(화소 높이장). 면분할.나누기 — 꺾인 변(이웃 면 사이 각 ≥ 문턱)에서 자른다.
껍질은 접힌 판이라 면과 면 사이가 오목 · 볼록 둘 다 꺾임 → 오목만=False · 문턱 10°(문턱별 면 수: 원화 먹선 칸 수와 가장 가까움).
잰다: 원화 먹선 칸(정답 아님 · 같은 그림의 2D 칸)과 얼마나 같은 자리에서 갈리나 — 면분할.채점(조각 · 칸 넓이 겹침).
출력 out/오메가몬2/지표/각도데이터/면_<n>.ply(면마다 색) · 면분할.json · 면분할_시트.png(렌더는 껍질면분할_렌더)"""
import os, sys, json, numpy as np, trimesh
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "오메가몬", "지표")); from 면분할 import 나누기, 채점
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; 문턱 = 10; 결과 = {}
rng = np.random.RandomState(7)
for n in "123456":
    m = trimesh.load(os.path.join(O, f"판_{n}.ply"), process=False); lab, cut = 나누기(m, 문턱=문턱, k=0, 작은비=0.004, 오목만=False)
    # 면 → 원화 칸(화소 순서 = 각도접힌판 의 np.nonzero(m) 순서)
    z = np.load(os.path.join(O, f"{n}.npz")); L = z["라벨"]; ys, xs = np.nonzero(L > 0); y0, x0 = ys.min(), xs.min()
    mm = np.load(os.path.join(O, f"판_{n}_Z.npz"))["m"]; py, px = np.nonzero(mm); 칸 = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)]
    gt = 칸[m.faces[:, 0]]
    try: s = 채점(lab, gt, m.area_faces)
    except Exception as e: s = {"오류": str(e)}
    pal = rng.randint(60, 240, (lab.max() + 1, 3)); fc = np.c_[pal[lab], np.full(len(lab), 255)].astype(np.uint8)
    c = trimesh.Trimesh(m.vertices[m.faces].reshape(-1, 3), np.arange(3 * len(m.faces)).reshape(-1, 3), process=False); c.visual.vertex_colors = np.repeat(fc, 3, axis=0); c.export(os.path.join(O, f"면_{n}.ply"))   # 블렌더가 PLY 면 색을 안 읽음 → 면마다 꼭짓점 따로 · 꼭짓점 색
    결과[n] = {"면": int(lab.max() + 1), "먹선 칸": int(L.max()), "채점": s}; print(n, 결과[n])
json.dump(결과, open(os.path.join(O, "면분할.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
