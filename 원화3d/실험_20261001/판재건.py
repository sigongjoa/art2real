# -*- coding: utf-8 -*-
"""판 다시 짓기 (10-04 사용자 「판 다시 짓기」 · 디테일 모양 5 바퀴).
막힌 곳: 정면 판이 잔 삼각형 더미(6B 들로니 + 능선 + 여러 판 겹침). → 원화 칸 하나 = 큰 면 하나, 이웃 칸과 꼭짓점 공유.
  ① 정면 칸(C1 · 20 화소 이상)마다 먹선 가운데까지 넓힌 윤곽 → 다각형(eps 2.5)
  ② 모든 칸의 꼭짓점을 4 화소 안에서 하나로 묶음(공유 꼭짓점 → 판 사이 틈 · 조각 불가)
  ③ 꼭짓점 깊이 = 겹9(지금 최선)의 가장 앞 겉(z-버퍼 3×3 중앙값) — 창 깊이 · 옆 단면 · 부리 깊이가 이미 든 면을 찍기만(새 모양 아님)
  ④ 칸 다각형 안 들로니 · 앞을 보게
  빼는 칸: 눈 윤곽 안(눈 모듈 그대로) · 뿔 칸 1 · 2(뿔 그대로)
  합침: 겹9 의 소체(+거울) · 눈 모듈 면 · 뿔 · 안테나 + 새 칸 판 → 왼쪽 반 거울(소체 · 뿔 · 안테나 제외)
출력 out/오메가몬2/블렌더/판재건.ply"""
import os, json, numpy as np, cv2, trimesh
from scipy.spatial import Delaunay
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
z = np.load(os.path.join(A, "1.npz")); L = z["라벨"]; yy, xx = np.nonzero(L > 0); y0, x0 = yy.min(), xx.min()
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape; py, px = np.mgrid[0:H, 0:W]; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
C1 = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)] * m1
xa = json.load(open(os.path.join(A, "기준선.json"), encoding="utf-8"))["정면 축(판 화소 열)"]["A 중심"] - cu
눈판 = np.zeros((H, W), np.uint8)
for P_ in json.load(open(os.path.join(B, "저폴리눈_앞윤곽.json"), encoding="utf-8")).values(): cv2.fillPoly(눈판, [np.round(np.array(P_)).astype(np.int32)], 1)
best = trimesh.load(os.path.join(B, "겹9.ply"), process=False); hull = trimesh.load(os.path.join(B, "겹6_소체.ply"), process=False); nh = len(hull.faces)
# ③ z-버퍼 (가장 앞 = 가장 작은 y)
zb = np.full((H, W), np.inf); P2 = np.c_[best.vertices[:, 0] + cu, -best.vertices[:, 2]]; dz = best.vertices[:, 1]
for f in np.argsort(-dz[best.faces].mean(1)):
    mk = np.zeros((H, W), np.uint8); cv2.fillPoly(mk, [np.round(P2[best.faces[f]]).astype(np.int32)], 1); zb[mk > 0] = dz[best.faces[f]].mean()
from scipy import ndimage
_e = ~np.isfinite(zb); _, (_iy, _ix) = ndimage.distance_transform_edt(_e, return_indices=True); zb = zb[_iy, _ix]   # 모양 8: 머리 가장자리 밖 꼭짓점도 가장 가까운 겉 깊이(빈 칸 10 · 28 · 36 의 원인)
def 깊이(x, r):
    r0, x0_ = int(round(r)), int(round(x)); w = zb[max(0, r0 - 1):r0 + 2, max(0, x0_ - 1):x0_ + 2]; w = w[np.isfinite(w)]
    return float(np.median(w)) if len(w) else np.nan
# ① 칸 다각형
# 모양 7 바퀴: 아래 얼굴 잔 칸(미늘 10여 개)이 칸마다 면이라 이빨처럼 읽힘(위키 「이빨 금지 · 지그재그는 포갠 V 판」) → 저폴리부리 세 묶음으로 합침
if os.environ.get("GROUP") == "1":
    for 묶음 in ([25, 26], [28, 29, 30, 31, 32, 33, 34, 35, 37], [36, 38, 39, 40, 41, 42]):
        C1[np.isin(C1, 묶음)] = 묶음[0]
ids, cnt = np.unique(C1[C1 > 0], return_counts=True); 칸들 = []
for c, n in zip(ids, cnt):
    if n < 20 or c in (1, 2): continue
    yy_, xx_ = np.nonzero(C1 == c)
    if 눈판[int(yy_.mean()), int(xx_.mean())]: continue
    mk = cv2.dilate((C1 == c).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2)
    cs, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); poly = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 2.5, True).reshape(-1, 2).astype(float)
    if len(poly) >= 3: 칸들.append((int(c), poly))
# ② 꼭짓점 묶기
모두 = np.concatenate([p for _, p in 칸들]); 대표 = []; 번호 = np.zeros(len(모두), int)
for i, p in enumerate(모두):
    if 대표:
        d = np.hypot(*(np.array(대표) - p).T); j = int(np.argmin(d))
        if d[j] < 4.0: 번호[i] = j; continue
    대표.append(p); 번호[i] = len(대표) - 1
대표 = np.array(대표); 깊 = np.array([깊이(x, r) for x, r in 대표])
# 모양 6 바퀴: 점마다 따로 찍은 깊이가 이웃끼리 튐 → 공유 꼭짓점 그래프(칸 다각형 이웃 변) 위에서 깊이만 라플라시안 두 번(λ 0.5)
if int(os.environ.get("SMOOTH", "0")):
    이웃 = [set() for _ in range(len(대표))]; k2 = 0
    for c, poly in 칸들:
        ids2 = 번호[k2:k2 + len(poly)]; k2 += len(poly)
        for a, b in zip(ids2, np.roll(ids2, -1)):
            if a != b: 이웃[a].add(b); 이웃[b].add(a)
    for _ in range(int(os.environ.get("SMOOTH"))):
        새 = 깊.copy()
        for i, nb in enumerate(이웃):
            nb = [j for j in nb if not np.isnan(깊[j])]
            if nb and not np.isnan(깊[i]): 새[i] = 0.5 * 깊[i] + 0.5 * np.mean(깊[nb])
        깊 = 새
# ④ 칸마다 삼각형
VV, CC = [], []; k = 0; 빈 = 0
for c, poly in 칸들:
    ids_ = 번호[k:k + len(poly)]; k += len(poly)
    ids_ = list(dict.fromkeys(ids_.tolist()))
    if len(ids_) < 3 or np.isnan(깊[ids_]).any(): 빈 += 1; print('빈 칸', c, len(ids_), int(np.isnan(깊[ids_]).sum()) if len(ids_) else -1); continue
    Q = 대표[ids_]
    try: tri = Delaunay(Q)
    except Exception: 빈 += 1; continue
    for t in tri.simplices:
        if cv2.pointPolygonTest(Q.astype(np.float32), tuple(Q[t].mean(0)), False) < 0: continue
        v3 = np.c_[Q[t, 0] - cu, 깊[np.array(ids_)[t]] - float(os.environ.get('OFF', '0')), -Q[t, 1]]   # 모양 8: 갑주는 소체 앞(OFF)
        n = np.cross(v3[1] - v3[0], v3[2] - v3[0])
        if n[1] > 0: v3 = v3[::-1]
        VV.append(v3); CC.append([232, 234, 244, 255])
판 = np.array(VV); 판C = np.repeat(np.array(CC)[:, None, :], 3, 1)
# 겹9 에서 남길 것: 소체 · 눈 모듈(눈 윤곽 안) · 뿔 · 안테나
bv = best.vertices[best.faces]; bc = best.visual.vertex_colors[best.faces]; c0 = bc[:, 0, :3].astype(int); cen = best.triangles_center
bpx = np.clip(np.round(cen[:, 0] + cu).astype(int), 0, W - 1); bpr = np.clip(np.round(-cen[:, 2]).astype(int), 0, H - 1)
뿔 = np.isin(c0[:, 0], [230, 200, 190]) & np.isin(c0[:, 2], [242, 222, 212]); 노랑 = (c0[:, 0] > 150) & (c0[:, 2] < 120)
소체 = (c0[:, 0] == 226) & (c0[:, 1] == 228) & (c0[:, 2] == 240); 눈 = (눈판[bpr, bpx] > 0) & (cen[:, 1] > -30) & ~소체
# 왼쪽 반 거울: 새 판만
pc = 판.mean(1); 왼 = pc[:, 0] <= xa + 1.5; Lf = 판[왼]; LC = 판C[왼]; R = Lf.copy(); R[:, :, 0] = 2 * xa - R[:, :, 0]; R = R[:, ::-1]
HV = hull.vertices[hull.faces]; HV = HV[HV.mean(1)[:, 0] <= xa + 1.5]   # 모양 9: 소체도 왼쪽 반만 거울(오른쪽이 판 따라 다르게 깎인 소체의 거울 사본이 왼쪽 판을 가렸다)
HM = HV.copy(); HM[:, :, 0] = 2 * xa - HM[:, :, 0]; HM = HM[:, ::-1]; HC = hull.visual.vertex_colors[hull.faces][hull.triangles_center[:, 0] <= xa + 1.5]
parts_v = [Lf, R, HV, HM, bv[눈 | 뿔 | 노랑]]; parts_c = [LC, LC[:, ::-1], HC, HC[:, ::-1], bc[눈 | 뿔 | 노랑]]
V = np.concatenate(parts_v).reshape(-1, 3); C = np.concatenate(parts_c).reshape(-1, 4)
_np = np.concatenate([Lf, R]).reshape(-1, 3); trimesh.Trimesh(_np, np.arange(len(_np)).reshape(-1, 3), vertex_colors=np.concatenate([LC, LC[:, ::-1]]).reshape(-1, 4), process=False).export(os.path.join(B, "판재건_판.ply"), encoding="ascii")   # 모양 10: 새 판만(겹.py PLATES 용)
trimesh.Trimesh(V, np.arange(len(V)).reshape(-1, 3), vertex_colors=C, process=False).export(os.path.join(B, "판재건" + os.environ.get("SMOOTH", "") + ("V" if os.environ.get("GROUP") == "1" else "") + os.environ.get("TAGP", "") + ".ply"), encoding="ascii")
print({"칸": len(칸들), "공유 꼭짓점": len(대표), "판 삼각형": len(판), "빈 칸": 빈, "눈 모듈 면": int(눈.sum()), "뿔": int(뿔.sum()), "안테나": int(노랑.sum())})
