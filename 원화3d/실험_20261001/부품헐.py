# -*- coding: utf-8 -*-
"""이름으로 짝지은 정면 · 옆 → 부품마다 두 장 헐 → 한 머리 (10-02 「니가 알아서」 · 각도이름 다음).
컷끼리 위치를 믿지 않는다(manga-position-unreliable): 두 장 사이에 옮기는 것은 **부품 이름**과 **그 부품의 높이 범위 맞춤**뿐.
  부품 b: 정면 마스크 F_b(u, v) — 가로 · 높이 · 정면 안에서의 자리   (정면 = 가로 · 높이 주 뷰)
          옆 마스크 S_b(w, v')  — 깊이 · 옆에서의 자리(옆 안에서는 부품끼리 앞뒤가 같은 컷이라 믿음)
          v' 는 부품마다 따로 F_b 의 높이 범위로 늘려 맞춤(두 컷의 머리 높이는 같은 HP=600 로 이미 맞음)
          헐_b = {(u, v, w): F_b(u, v) ∧ S_b(w, v'(v))}  — 좌우는 옆 하나뿐(인물 왼쪽)이라 대칭으로 씀
  옆에 없는 부품(눈 둘레 테 · 안테나 뿌리 등)은 빼고 목록에 적는다. 생성 AI 없음.
출력 out/오메가몬2/지표/각도데이터/부품헐.ply(부품 색) · 부품헐.json"""
import os, json, numpy as np, cv2, trimesh
from skimage import measure
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; 이름 = json.load(open(os.path.join(O, "이름.json"), encoding="utf-8"))
바탕 = lambda s: s.split("/")[0].replace("?", "").replace("(뒤)", "").replace("(뒤에서)", "").replace(" 뒤끝", "").strip()
DS = 3
def 마스크들(n):
    L = np.load(os.path.join(O, n + ".npz"))["라벨"][::DS, ::DS]; out = {}
    for nm, cs in 이름[n].items():
        b = 바탕(nm)
        if b: out[b] = out.get(b, np.zeros(L.shape, bool)) | np.isin(L, cs)
    return out, L > 0
F, Fh = 마스크들("1"); S, Sh = 마스크들("2")
ys, xs = np.nonzero(Fh); u0, u1, v0, v1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
ys2, xs2 = np.nonzero(Sh); w0, w1 = xs2.min(), xs2.max() + 1; Wd = w1 - w0
T20 = ["e6194b", "3cb44b", "ffe119", "4363d8", "f58231", "911eb4", "46f0f0", "f032e6", "bcf60c", "fabebe", "008080", "e6beff", "9a6324", "fffac8", "800000", "aaffc3", "808000", "ffd8b1", "000075"]
모두 = sorted({바탕(n) for v in 이름.values() for n in v} - {""}); col = {b: [int(T20[i][k:k + 2], 16) for k in (0, 2, 4)] for i, b in enumerate(모두)}
meshes = []; 결과 = {"쓴 부품": {}, "옆에 없어 뺌": [], "정면에 없어 뺌": []}
for b in 모두:
    if b not in F: 결과["정면에 없어 뺌"].append(b); continue
    if b not in S: 결과["옆에 없어 뺌"].append(b); continue
    f = F[b][v0:v1, u0:u1]; s = S[b][:, w0:w1]
    fy = np.nonzero(f.any(1))[0]; sy = np.nonzero(s.any(1))[0]
    if len(fy) < 2 or len(sy) < 2: continue
    V = np.zeros((u1 - u0, v1 - v0, Wd), bool)
    for v in range(fy[0], fy[-1] + 1):
        vv = int(round(sy[0] + (v - fy[0]) * (sy[-1] - sy[0]) / max(1, fy[-1] - fy[0])))
        V[:, v, :] = f[v][:, None] & s[vv][None, :]
    if V.sum() < 20: continue
    vt, fc, _, _ = measure.marching_cubes(np.pad(V, 1).astype(np.float32), 0.5); vt -= 1
    k = 100.0 / (v1 - v0); m = trimesh.Trimesh(np.c_[vt[:, 0] * k, (vt[:, 2] - Wd / 2) * k, -vt[:, 1] * k], fc)   # 블렌더: x 오른 · y 앞이 음(옆 그림 왼쪽 = 부리 = 앞) · z 위
    trimesh.smoothing.filter_taubin(m, iterations=4); m.visual.vertex_colors = np.tile(col[b] + [255], (len(m.vertices), 1)).astype(np.uint8); meshes.append(m)
    결과["쓴 부품"][b] = {"복셀": int(V.sum()), "높이 정면px": int(fy[-1] - fy[0]), "높이 옆px": int(sy[-1] - sy[0])}
머리 = trimesh.util.concatenate(meshes); 머리.export(os.path.join(O, "부품헐.ply"))
json.dump(결과, open(os.path.join(O, "부품헐.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False)[:900])
