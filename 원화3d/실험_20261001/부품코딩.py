# -*- coding: utf-8 -*-
"""모은 정보로 머리를 코드로 짓기 1 판 (10-03 사용자 「이 정도 정보면 니가 코딩할 수 있지 않아?」).
지어내는 숫자 없음 — 부품마다 모양 · 자리는 전부 원화에서 잰 것:
  부품 마스크 = 각도이름(장마다 먹선 칸 → 부품 ID 대응표 · 부품ID.py)
  카메라 = 특징맞춤2(FIXANG=1 — 각도는 사람이 정함 0/90/35/40 · 크기 · 이동만 특징점 53 개로)
  부품 하나 = 정면 마스크 × 옆 마스크 의 두 장 헐(세계 좌표에서 · 옆 마스크는 특징점 잔차만큼 넓힘)
  옆 그림은 인물 왼쪽(= 정면 그림 오른쪽 「/오른」)만 보임 → 「/왼」 부품은 대칭 평면 x0 로 거울. 가운데 부품은 그대로.
  옆에 안 보이는 부품(눈 둘레 테 등)은 정면 마스크 × 그 부품 3/4 마스크.
부품헐.py(10-02 실패)와 다른 점: 부품마다 높이를 억지로 늘려 맞추지 않음 — 모든 부품이 같은 카메라 둘을 씀.
출력 각도데이터/부품코딩.ply(부품 색) · 부품코딩.json"""
import os, json, numpy as np, trimesh, cv2
from skimage import measure
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"
J = json.load(open(os.path.join(O, "특징맞춤2.json"), encoding="utf-8")); B = json.load(open(os.path.join(O, "부품ID.json"), encoding="utf-8"))
x0 = J["대칭 평면 x0(정면 화소, 가운데 기준)"]; 색 = B["부품 ID"]
def 마스크(n):
    z = np.load(os.path.join(O, f"{n}.npz")); L = z["라벨"]; ys, xs = np.nonzero(L > 0); y0, x0_ = ys.min(), xs.min()
    m = np.load(os.path.join(O, f"판_{n}_Z.npz"))["m"]; py, px = np.nonzero(m); cell = np.zeros(m.shape, int)
    cell[py, px] = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0_ + 2 * px, 0, L.shape[1] - 1)]
    out = {}
    for e in B["대응표"][n]:
        if e["부품"] == "미정" or e["부품"].startswith("F"): continue   # 무늬(번개)는 부품이 아님
        k = (e["부품"], e["쪽"]); out[k] = out.get(k, np.zeros(m.shape, bool)) | np.isin(cell, e["칸"])
    return out
def 투영(n, P):
    a = J["장별"][n]; R = np.array(a["R"]); c = P @ R.T; return a["크기"] * c[:, 0] + a["tx"], -a["크기"] * c[:, 1] + a["ty"]
M = {n: 마스크(n) for n in "123"}
# 1 판 렌더: 마스크(노랑)가 투구(초록)에서 아래로 떨어져 뜸 — 특징점으로 푼 옆 · 3/4 의 크기 · 세로 이동이 정면과 어긋남.
# 고침: 두 장에 다 있는 부품마다 위끝 · 아래끝 · 가운데 높이(정면 z 와 그 장 화소 행)를 맞춰 크기 s · 세로 이동 ty 를 다시 풂(가로 · 깊이는 그대로).
cu1 = J["장별"]["1"]["tx"]; cv1 = J["장별"]["1"]["ty"]
for n in "23":
    a = J["장별"][n]; R = np.array(a["R"]); fz, rv = [], []
    for k, fm in M["1"].items():
        if k not in M[n] or fm.sum() < 30 or M[n][k].sum() < 30: continue
        y1 = np.nonzero(fm.any(1))[0]; y2 = np.nonzero(M[n][k].any(1))[0]
        for q1, q2 in ((y1.min(), y2.min()), (y1.max(), y2.max()), (y1.mean(), y2.mean())): fz.append(-(q1 - cv1)); rv.append(q2)
    fz, rv = np.array(fz), np.array(rv); up = np.linalg.norm(R[1, [2]])   # 위 축이 z 를 얼마나 담나(pitch)
    A_ = np.c_[-fz * up, np.ones(len(fz))]; s_, ty_ = np.linalg.lstsq(A_, rv, rcond=None)[0]
    print(n, "크기", round(a["크기"], 3), "→", round(float(s_), 3), " ty", round(a["ty"], 1), "→", round(float(ty_), 1), " 맞춘 점", len(fz), " 잔차", round(float(np.abs(A_ @ [s_, ty_] - rv).mean()), 1))
    a["tx"] = a["tx"] + 0; a["크기"], a["ty"] = float(s_), float(ty_)
st = 1.5; ax = np.arange(-140, 140, st); az = np.arange(-170, 160, st); ay = np.arange(-170, 170, st)
X, Y, Z = np.meshgrid(ax, ay, az, indexing="ij"); P = np.c_[X.ravel(), Y.ravel(), Z.ravel()]
def 안(n, mask, P, 넓힘=0):
    if 넓힘: mask = cv2.dilate(mask.astype(np.uint8), np.ones((2 * 넓힘 + 1,) * 2, np.uint8)) > 0
    u, v = 투영(n, P); u = np.round(u).astype(int); v = np.round(v).astype(int); H, W = mask.shape; ok = (u >= 0) & (u < W) & (v >= 0) & (v < H)
    r = np.zeros(len(P), bool); r[ok] = mask[v[ok], u[ok]]; return r
넓힘 = {"2": int(round(J["장별"]["2"]["잔차 중앙(그 장 화소)"])), "3": int(round(J["장별"]["3"]["잔차 중앙(그 장 화소)"] / 2))}
meshes = []; 결과 = {}
for (pid, 쪽), fm in sorted(M["1"].items()):
    if fm.sum() < 30: continue
    거울 = 쪽 == "왼"; 짝 = (pid, "오른" if 거울 else 쪽)
    Q = P.copy()
    if 거울: Q[:, 0] = 2 * x0 - Q[:, 0]                     # 왼 부품은 오른쪽 옆 마스크로 보고 거울
    keep = 안("1", fm, P)
    if 짝 in M["2"] and M["2"][짝].sum() >= 30: keep &= 안("2", M["2"][짝], Q, 넓힘["2"]); 둘째 = "옆"
    elif 짝 in M["3"] and M["3"][짝].sum() >= 30: keep &= 안("3", M["3"][짝], Q, 넓힘["3"]); 둘째 = "3/4"
    else: 결과[f"{pid}/{쪽}"] = "둘째 장 없음 · 뺌"; continue
    if keep.sum() < 50: 결과[f"{pid}/{쪽}"] = f"헐 비었음({둘째})"; continue
    V = keep.reshape(X.shape); vt, fc, _, _ = measure.marching_cubes(np.pad(V, 1).astype(np.float32), 0.5); vt = (vt - 1) * st + np.array([ax[0], ay[0], az[0]])
    me = trimesh.Trimesh(np.c_[vt[:, 0], -vt[:, 1], vt[:, 2]], fc); trimesh.smoothing.filter_taubin(me, iterations=6)   # 블렌더: 앞 = −y
    me.visual.vertex_colors = np.tile(list(색[pid]) + [255], (len(me.vertices), 1)).astype(np.uint8); meshes.append(me)
    ys_ = vt[:, 1]; 결과[f"{pid}/{쪽}"] = {"둘째 장": 둘째, "복셀": int(keep.sum()), "깊이 범위": [round(float(ys_.min()), 1), round(float(ys_.max()), 1)]}
trimesh.util.concatenate(meshes).export(os.path.join(O, "부품코딩.ply"))
json.dump({"x0": x0, "넓힘(화소)": 넓힘, "부품": 결과}, open(os.path.join(O, "부품코딩.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in 결과.items(): print(k, v)
