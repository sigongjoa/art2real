# -*- coding: utf-8 -*-
r"""디테일 대조 — 원화 선 지도 vs PG 디자인 판 모델 선 지도, 부위별 (2026-09-26).

    python 실험_20260925/디테일대조.py
    -> out/출력/오메가몬_PG/디자인/디테일_대조.md · 디테일_대조.png · 디테일_대조_상위5.png · 디테일_대조.json

사용자: 「디테일이 부족하다」 → 어느 부위에서 무슨 종류의 선이 몇 개 빠졌는지 숫자로.

원화 선(정면·옆·뒤, 원화 화소 공간 1024²):
  ① 실루엣   알파 마스크 바깥 윤곽
  ② 패널     먹선 중 양 끝이 갈래점·실루엣에 붙은 것 (닫힌 영역을 가른다), 양쪽 색 같음
  ③ 단차·무늬 먹선 중 끝이 자유로운 것 · 짧은 닫힌 고리 (단차 · 홈 · 장식), 양쪽 색 같음
  ④ 색 경계   먹선 양쪽 색 부류가 다른 것 + 먹선 없는 색 부류 경계
모델 선(STL 을 원화와 같은 사상 · 같은 화소로 정사영 z 버퍼 렌더 · 순수 numpy):
  ① 실루엣   깊이 버퍼 배경 경계
  ② 부품경계 부품 id 가 바뀌는 곳 (색 다르면 ④) · 법선 불연속 > 25°(모서리)
  ③ 단차     같은 부품 안 깊이 불연속 > 1 mm
겹침: 원화 선분의 화소 중 모델 선까지 2 mm 안인 비율 ≥ 0.5 이면 짝 있음(초록) · 아니면 빠짐(빨강) · 모델 선 중 원화 선 2 mm 밖은 파랑.
부위: 관절.json 피벗 높이 + 좌우 x 로 상자. 선분 = 골격화 → 갈래점 끊기 → RDP(2 px).
분류 (빠진 원화 선 → 넣을 방법): ② → (a) 패널라인 홈 · ③ → (b) 단차 판 · ④ → (d) 색 분할 부품 ·
  ① 실루엣 빠짐 중 짧은 것(≤ 15 mm) → (c) 소형 부품 · 긴 것 → (e) 모양 변경.
⚠ 원화 선 종류는 자유 끝·색 부류로 나눈 발견법이다. 셀 음영(같은 색 부류 안 명암 계단)은 선으로 안 센다."""
import os, sys, json, glob, time
import numpy as np, trimesh
from PIL import Image
from scipy import ndimage
from skimage.morphology import skeletonize
from skimage.draw import line as sk_line

ROOT = r"G:\art2real\원화3d"; D = os.path.join(ROOT, r"out\출력\오메가몬_PG\디자인"); ART = r"G:\art2real\트레일\trail7_part3d\in"
sys.path[:0] = [ROOT, os.path.join(ROOT, "실험_20260924")]
import hull as H
from 선다듬기 import _경로들, _rdp
t0 = time.time()
def log(*a): print("[%4.0fs]" % (time.time() - t0), *a, flush=True)
관 = {a["이름"]: a["피벗mm"][2] for a in json.load(open(os.path.join(ROOT, r"out\가동\관절.json"), encoding="utf-8"))["관절"]}
허용mm = 2.0; 단차mm = 1.0; 모서리도 = 25.0; RDP = 2.0
# 보기: (원화 파일, cx, r0, s, 회전(월드→화면 [X, Y, 깊이(클수록 가까움)]), 화면X→몸 x 부호)
보기 = {"정면": ("omega_front_clean.png", 534.0, 951.0, 0.342, np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float), +1),
      "옆": ("omega_side.png", 462.0, 938.0, 0.349, np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], float), None),
      "뒤": ("omega_back.png", 505.0, 929.6, 0.3535, np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]], float), +1)}   # 뒤 원화는 「거울 뒤」(방패·칼이 정면과 같은 화면 왼쪽) → 화면 X = +x
종류색 = {"실루엣": (0.15, 0.15, 0.15), "패널": (0.10, 0.45, 0.90), "단차무늬": (0.90, 0.45, 0.05), "색경계": (0.65, 0.10, 0.70),
        "부품경계": (0.10, 0.45, 0.90), "단차": (0.90, 0.45, 0.05), "모서리": (0.20, 0.65, 0.35)}

# ── 부위 상자 (몸 좌표 mm) ──
def 부위(x, z, 옆=False):
    """첫 맞는 상자. 옆 보기는 x 자리에 y(앞 = 작은 값)."""
    if 옆:
        if z > 관["목위"]: return "머리"
        if z > 232 and x > 8: return "어깨"
        if z > 관["목아래"]: return "목/목깃"
        if z > 관["가슴복부"]: return "가슴"
        if z > 관["복부허리"]: return "복부"
        if z > 관["L고관절"]: return "허리/스커트"
        if z > 137: return "허벅지"
        if z > 121: return "무릎"
        if z > 관["L발목볼"]: return "정강이"
        return "발"
    s = "L" if x < 0 else "R"; a = abs(x)
    if x < -58 and z < 148 and (z > 30 or x < -80): return "칼"      # 발톱(x −58~−80 · z < 30) 제외
    if x > 50 and 90 < z < 150: return "대포"
    if a <= 26 and z > 관["목위"]: return "머리"
    if 28 <= a <= 78 and z > 232: return "어깨 " + s
    if a <= 28 and z > 관["목아래"]: return "목/목깃"
    if a > 36 and z > 205: return "윗팔 " + s if a <= 56 and z > 212 else "팔끝 " + s
    if a > 36 and z > 140: return "팔끝 " + s
    if z > 관["가슴복부"]: return "가슴"
    if z > 관["복부허리"]: return "복부"
    if z > 관["L고관절"] or (a < 12 and z > 145): return "허리/스커트"
    if z > 137: return "허벅지"
    if z > 121: return "무릎"
    if z > 관["L발목볼"]: return "정강이"
    return "발"
부위순 = ["머리", "목/목깃", "가슴", "복부", "허리/스커트", "허벅지", "무릎", "정강이", "발", "어깨 L", "어깨 R", "어깨", "윗팔 L", "윗팔 R", "팔끝 L", "팔끝 R", "칼", "대포"]

# ── 원화 ──
def 색부류(rgb):
    """RGB(0..1) → 부류 번호. 흰(+회) · 검 · 금 · 주황 · 빨강 · 파랑 · 하늘. 명암 계단(셀 음영)은 같은 부류."""
    mx, mn = rgb.max(-1), rgb.min(-1); v = mx; sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    c = np.full(v.shape, 1, np.int8)                                  # 흰 (회색 셀 음영도 흰 — 명암은 선이 아니다)
    c[v < 0.32] = 3                                                   # 검
    col = sat >= 0.22
    c[col & (v >= 0.32) & (h >= 38) & (h < 70)] = 4                   # 금
    c[col & (v >= 0.32) & (h >= 12) & (h < 38)] = 5                   # 주황
    c[col & (v >= 0.32) & ((h < 12) | (h >= 335))] = 6                # 빨강
    c[col & (v >= 0.32) & (h >= 200) & (h < 290)] = 7                 # 파랑
    c[col & (v >= 0.32) & (h >= 160) & (h < 200)] = 8                 # 하늘(칼)
    return c
def 원화선(이름):
    f, cx, r0, s, R, sg = 보기[이름]
    im = np.array(Image.open(os.path.join(ART, f)).convert("RGBA"))
    A = im[:, :, 3] > 127
    op = ndimage.binary_opening(A, np.ones((11, 1), bool)); 빠 = A & ~op   # 삼면도 안내선(가로 가는 선 · 화면 가장자리에 닿음) 제거
    lab, n = ndimage.label(빠, np.ones((3, 3), bool))
    for k in range(1, n + 1):
        ys, xs = np.where(lab == k)
        if xs.min() == 0 or xs.max() == 1023: A[lab == k] = False
    lab, n = ndimage.label(A); A = lab == (np.bincount(lab.ravel())[1:].argmax() + 1)   # 가장 큰 덩어리
    실루 = A & ~ndimage.binary_erosion(A, iterations=1)
    먹 = H.ink_map(os.path.join(ART, f)) & ndimage.binary_erosion(A, iterations=3)
    rgb = ndimage.median_filter(im[:, :, :3], size=(5, 5, 1)).astype(np.float32) / 255
    부 = 색부류(rgb); 먹넓 = ndimage.binary_dilation(먹, iterations=2)
    idx = ndimage.distance_transform_edt(먹넓 | ~A, return_distances=False, return_indices=True)
    부 = 부[tuple(idx)]; 부[~A] = 0                                   # 먹선 자리를 가까운 색으로 메움
    색경 = np.zeros_like(A)
    for d in ((0, 1), (1, 0)):
        a, b = np.roll(부, d, (0, 1)), 부
        색경 |= (a != b) & (a > 0) & (b > 0)
    색경 &= ndimage.binary_erosion(A, iterations=3)
    색경_먹없음 = 색경 & ~ndimage.binary_dilation(먹, iterations=4)
    경로, sk, 갈 = _경로들(먹)
    붙 = ndimage.binary_dilation(갈 | 실루, iterations=3)
    종류 = {"실루엣": 실루, "패널": np.zeros_like(A), "단차무늬": np.zeros_like(A), "색경계": 색경_먹없음}
    for P in 경로:
        Q = np.rint(P).astype(int); ys, xs = np.clip(Q[:, 1], 0, 1023), np.clip(Q[:, 0], 0, 1023)
        # 양쪽 색: 경로 화소마다 접선에 수직 ±4 px
        t = np.gradient(P, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-9; nrm = np.c_[-t[:, 1], t[:, 0]] * 4
        pa, pb = np.rint(P + nrm).astype(int), np.rint(P - nrm).astype(int)
        ca = 부[np.clip(pa[:, 1], 0, 1023), np.clip(pa[:, 0], 0, 1023)]; cb = 부[np.clip(pb[:, 1], 0, 1023), np.clip(pb[:, 0], 0, 1023)]
        다름 = ((ca != cb) & (ca > 0) & (cb > 0)).mean()
        if 다름 >= 0.5: k = "색경계"
        else:
            양끝 = 붙[ys[0], xs[0]] and 붙[ys[-1], xs[-1]]
            고리 = np.linalg.norm(P[0] - P[-1]) < 4 and len(P) < 120
            k = "단차무늬" if (고리 or not 양끝) else "패널"
        종류[k][ys, xs] = True
    return dict(A=A, rgb=im[:, :, :3], 종류=종류, 갈=갈, 색=부)

# ── 모델 ──
def 부품읽기():
    부품 = {}
    for blk in ("몸통", "다리", "머리어깨"):
        info = json.load(open(os.path.join(D, blk, "부품.json"), encoding="utf-8"))["부품"]
        for n, p in info.items():
            f = os.path.join(D, blk, p.get("파일", n + ".stl"))
            if not os.path.exists(f): 부품[n] = None; continue
            c = p.get("색")
            if isinstance(c, str): c = {"흰": (0.93, 0.93, 0.95), "검정": (0.22, 0.22, 0.25), "금": (0.9, 0.72, 0.2)}.get(c)
            if c is None: c = (0.3, 0.38, 0.75) if "파랑" in n else (0.22, 0.22, 0.25) if n.startswith("복부") else (0.9, 0.72, 0.2) if "금뿔" in n else (0.9, 0.9, 0.92)
            부품[n] = (trimesh.load(f), tuple(c))
    return 부품
def 래스터(V, F, cx, r0, s, W=1024):
    """정사영 z 버퍼 (순수 numpy). V 는 화면 좌표 [X, Y, 깊이]. → 깊이 버퍼(mm · 배경 -inf), 삼각형 id(-1 배경)."""
    u = V[:, 0] / s + cx; v = r0 - V[:, 1] / s; P = np.c_[u, v]
    T = P[F]; Z = V[F][:, :, 2]
    x0, y0 = np.floor(T[:, :, 0].min(1)).astype(int), np.floor(T[:, :, 1].min(1)).astype(int)
    x1, y1 = np.ceil(T[:, :, 0].max(1)).astype(int), np.ceil(T[:, :, 1].max(1)).astype(int)
    size = np.maximum(x1 - x0, y1 - y0) + 1
    zb = np.full(W * W, -np.inf); tid = np.full(W * W, -1, np.int64)
    area = (T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1]) - (T[:, 1, 1] - T[:, 0, 1]) * (T[:, 2, 0] - T[:, 0, 0])
    ok = np.abs(area) > 1e-9
    for i in np.where(ok & (size > 128))[0]: _삼각(T[i], Z[i], area[i], i, zb, tid, W)
    for lo, S in ((0, 4), (4, 8), (8, 16), (16, 32), (32, 64), (64, 128)):
        sel = np.where(ok & (size > lo) & (size <= S))[0]
        if len(sel) == 0: continue
        dx, dy = np.meshgrid(np.arange(S), np.arange(S)); dx, dy = dx.ravel(), dy.ravel()
        chunk = max(1, 4_000_000 // (S * S))
        for c0 in range(0, len(sel), chunk):
            ii = sel[c0:c0 + chunk]; px = x0[ii][:, None] + dx[None]; py = y0[ii][:, None] + dy[None]
            t = T[ii]; cxp, cyp = px + 0.5, py + 0.5
            w0 = ((t[:, 1, 0] - t[:, 0, 0])[:, None] * (cyp - t[:, 0, 1][:, None]) - (t[:, 1, 1] - t[:, 0, 1])[:, None] * (cxp - t[:, 0, 0][:, None]))
            w1 = ((t[:, 2, 0] - t[:, 1, 0])[:, None] * (cyp - t[:, 1, 1][:, None]) - (t[:, 2, 1] - t[:, 1, 1])[:, None] * (cxp - t[:, 1, 0][:, None]))
            w2 = ((t[:, 0, 0] - t[:, 2, 0])[:, None] * (cyp - t[:, 2, 1][:, None]) - (t[:, 0, 1] - t[:, 2, 1])[:, None] * (cxp - t[:, 2, 0][:, None]))
            a = area[ii][:, None]; b0, b1, b2 = w1 / a, w2 / a, w0 / a
            inside = (b0 >= -1e-6) & (b1 >= -1e-6) & (b2 >= -1e-6) & (px >= 0) & (px < W) & (py >= 0) & (py < W)
            z = b0 * Z[ii][:, 0:1] + b1 * Z[ii][:, 1:2] + b2 * Z[ii][:, 2:3]
            idx = (py * W + px)[inside]; zz = z[inside]; ti = np.broadcast_to(ii[:, None], px.shape)[inside]
            np.maximum.at(zb, idx, zz)
            win = zz >= zb[idx]; tid[idx[win]] = ti[win]
    return zb.reshape(W, W), tid.reshape(W, W)
def _삼각(t, z, area, i, zb, tid, W):
    x0, x1 = max(int(np.floor(t[:, 0].min())), 0), min(int(np.ceil(t[:, 0].max())), W - 1)
    y0, y1 = max(int(np.floor(t[:, 1].min())), 0), min(int(np.ceil(t[:, 1].max())), W - 1)
    if x1 < x0 or y1 < y0: return
    px, py = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1)); cxp, cyp = px + 0.5, py + 0.5
    w0 = (t[1, 0] - t[0, 0]) * (cyp - t[0, 1]) - (t[1, 1] - t[0, 1]) * (cxp - t[0, 0])
    w1 = (t[2, 0] - t[1, 0]) * (cyp - t[1, 1]) - (t[2, 1] - t[1, 1]) * (cxp - t[1, 0])
    w2 = (t[0, 0] - t[2, 0]) * (cyp - t[2, 1]) - (t[0, 1] - t[2, 1]) * (cxp - t[2, 0])
    b0, b1, b2 = w1 / area, w2 / area, w0 / area; inside = (b0 >= -1e-6) & (b1 >= -1e-6) & (b2 >= -1e-6)
    zz = (b0 * z[0] + b1 * z[1] + b2 * z[2])[inside]; idx = (py * W + px)[inside]
    np.maximum.at(zb, idx, zz); win = zz >= zb[idx]; tid[idx[win]] = i
def 모델선(이름, 부품):
    f, cx, r0, s, R, sg = 보기[이름]
    Vs, Fs, Ns, pid, cols = [], [], [], [], []; off = 0
    for k, (n, v) in enumerate(부품.items()):
        if v is None: continue
        m, c = v; V = np.asarray(m.vertices, float) @ R.T; F = np.asarray(m.faces)
        N = np.asarray(m.face_normals) @ R.T
        Vs.append(V); Fs.append(F + off); Ns.append(N); pid.append(np.full(len(F), k)); cols.append(np.tile(c, (len(F), 1))); off += len(V)
    V, F, N, pid, cols = np.vstack(Vs), np.vstack(Fs), np.vstack(Ns), np.concatenate(pid), np.vstack(cols)
    zb, tid = 래스터(V, F, cx, r0, s)
    A = tid >= 0
    nb = np.zeros((1024, 1024, 3)); nb[A] = N[tid[A]]
    pb = np.full((1024, 1024), -1); pb[A] = pid[tid[A]]
    cb = np.ones((1024, 1024, 3)); cb[A] = cols[tid[A]]
    실루 = A & ~ndimage.binary_erosion(A, iterations=1)
    경계 = np.zeros_like(A); 색경 = np.zeros_like(A); 단 = np.zeros_like(A); 모 = np.zeros_like(A)
    for d in ((0, 1), (1, 0)):
        a_ok = A & np.roll(A, d, (0, 1)); ok = a_ok & ~실루 & ~np.roll(실루, d, (0, 1))
        pd = (pb != np.roll(pb, d, (0, 1))) & ok
        cd = (np.abs(cb - np.roll(cb, d, (0, 1))).sum(-1) > 0.1) & pd
        경계 |= pd & ~cd; 색경 |= cd
        nz = np.minimum(np.abs(nb[..., 2]), np.abs(np.roll(nb[..., 2], d, (0, 1)))) > 0.3
        dz = np.abs(zb - np.roll(zb, d, (0, 1))) > 단차mm
        단 |= dz & ok & nz & ~pd
        cosang = np.clip((nb * np.roll(nb, (d[0], d[1], 0), (0, 1, 2))).sum(-1), -1, 1)
        모 |= (np.degrees(np.arccos(cosang)) > 모서리도) & ok & nz & ~pd & ~dz
    종류 = {"실루엣": 실루, "부품경계": 경계, "색경계": 색경, "단차": 단, "모서리": 모}
    L = np.array([0.35, -0.6, 0.72]); L /= np.linalg.norm(L); Ls = R @ L
    sh = 0.35 + 0.65 * np.clip(nb @ Ls, 0, 1); img = np.ones((1024, 1024, 3)); img[A] = np.clip(cb[A] * sh[A][:, None], 0, 1)
    return dict(A=A, 종류=종류, 렌더=img, zb=zb)

# ── 선분화 · 부위별 집계 · 겹침 ──
def 선분들(mask):
    """골격화 → 경로 → RDP → [(꼭짓점 배열 px)]."""
    경로, sk, 갈 = _경로들(mask)
    return [_rdp(P, RDP) for P in 경로], 갈
def 선분표(종류들, 이름, dt_상대=None):
    """종류별 선분 목록: (종류, 부위, 길이mm, 짝비율, 중점px)."""
    f, cx, r0, s, R, sg = 보기[이름]; rows = []; 갈합 = _경로들(np.any(list(종류들.values()), 0))[2]   # 교차점은 모든 종류를 합친 선에서
    for k, m in 종류들.items():
        segs, 갈 = 선분들(m)
        for P in segs:
            for i in range(len(P) - 1):
                a, b = P[i], P[i + 1]; L = np.linalg.norm(b - a) * s
                if L < 0.5: continue
                mid = (a + b) / 2; X, Z = (mid[0] - cx) * s, (r0 - mid[1]) * s
                bw = 부위(X, Z, True) if sg is None else 부위(sg * X, Z)
                짝 = None
                if dt_상대 is not None:
                    rr, cc = sk_line(int(round(a[1])), int(round(a[0])), int(round(b[1])), int(round(b[0])))
                    rr, cc = np.clip(rr, 0, 1023), np.clip(cc, 0, 1023); 짝 = float((dt_상대[rr, cc] * s <= 허용mm).mean())
                rows.append((k, bw, float(L), 짝, (float(mid[0]), float(mid[1])), (a.tolist(), b.tolist())))
    return rows, 갈합
def 집계(원rows, 모rows, 원갈, 모갈, 이름):
    f, cx, r0, s, R, sg = 보기[이름]; out = {}
    def bw_of(y, x): X, Z = (x - cx) * s, (r0 - y) * s; return 부위(X, Z, True) if sg is None else 부위(sg * X, Z)
    갈부 = {}
    for name, g in (("원", 원갈), ("모", 모갈)):
        ys, xs = np.where(g); c = {}
        for y, x in zip(ys, xs): b = bw_of(y, x); c[b] = c.get(b, 0) + 1
        갈부[name] = c
    for b in 부위순:
        o = [r for r in 원rows if r[1] == b]; m = [r for r in 모rows if r[1] == b]
        if not o and not m: continue
        oL = sum(r[2] for r in o); 빠 = [r for r in o if r[3] < 0.5]; 빠L = sum(r[2] for r in 빠)
        종 = {}
        for r in 빠: 종[r[0]] = 종.get(r[0], 0) + r[2]
        mL = sum(r[2] for r in m); 파 = [r for r in m if r[3] < 0.5]
        out[b] = dict(원화선분=len(o), 원화길이mm=round(oL, 1), 원화교차점=갈부["원"].get(b, 0), 모델선분=len(m), 모델길이mm=round(mL, 1), 모델교차점=갈부["모"].get(b, 0),
                      빠진선분=len(빠), 빠진길이mm=round(빠L, 1), 빠진비율=round(빠L / oL, 3) if oL else None,
                      빠진종류mm={k: round(v, 1) for k, v in sorted(종.items(), key=lambda q: -q[1])},
                      모델만선분=len(파), 모델만길이mm=round(sum(r[2] for r in 파), 1))
    return out
def 방법(빠rows):
    """빠진 원화 선분 → (a)~(e). 실루엣은 이어진 빠진 조각의 길이로 (c)/(e)."""
    cnt = {k: 0 for k in "abcde"}; 예 = {k: [] for k in "abcde"}
    for r in 빠rows:
        k, b = r[0], r[1]
        if k == "패널": g = "a"
        elif k == "단차무늬": g = "b"
        elif k == "색경계": g = "d"
        else: g = "c" if r[2] <= 15 else "e"
        cnt[g] += 1
        if len(예[g]) < 6 and b not in [e[0] for e in 예[g]]: 예[g].append((b, round(r[2], 1)))
    return cnt, 예

# ── 그림 ──
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
def 선그림(base, 종류들, 굵기=2):
    img = base.copy()
    for k, m in 종류들.items():
        mm = ndimage.binary_dilation(m, iterations=굵기 - 1) if 굵기 > 1 else m
        img[mm] = 종류색[k]
    return img
def 겹침그림(base, 원rows, 모rows, 굵기=2):
    img = base.copy(); G = np.zeros((1024, 1024), bool); Rm = np.zeros_like(G); B = np.zeros_like(G)
    for r in 모rows:
        if r[3] < 0.5: a, b = r[5]; rr, cc = sk_line(int(round(a[1])), int(round(a[0])), int(round(b[1])), int(round(b[0]))); B[np.clip(rr, 0, 1023), np.clip(cc, 0, 1023)] = True
    for r in 원rows:
        a, b = r[5]; rr, cc = sk_line(int(round(a[1])), int(round(a[0])), int(round(b[1])), int(round(b[0]))); (G if r[3] >= 0.5 else Rm)[np.clip(rr, 0, 1023), np.clip(cc, 0, 1023)] = True
    for m, c in ((B, (0.2, 0.4, 1.0)), (G, (0.1, 0.7, 0.2)), (Rm, (0.95, 0.1, 0.1))):
        img[ndimage.binary_dilation(m, iterations=굵기 - 1)] = c
    return img
def 상자(A, pad=20):
    ys, xs = np.where(A); return max(ys.min() - pad, 0), min(ys.max() + pad, 1023), max(xs.min() - pad, 0), min(xs.max() + pad, 1023)

def main():
    부품 = 부품읽기(); 없 = [n for n, v in 부품.items() if v is None]
    log("부품", len(부품) - len(없), "STL 없음", 없)
    결과 = {"설명": __doc__, "STL없는부품": 없, "보기": {}}; 그림 = {}
    for 이름 in ("정면", "옆", "뒤"):
        원 = 원화선(이름); log(이름, "원화 선", {k: int(v.sum()) for k, v in 원["종류"].items()})
        모 = 모델선(이름, 부품); log(이름, "모델 선", {k: int(v.sum()) for k, v in 모["종류"].items()})
        원합 = np.any([v for v in 원["종류"].values()], 0); 모합 = np.any([v for v in 모["종류"].values()], 0)
        dt모 = ndimage.distance_transform_edt(~모합); dt원 = ndimage.distance_transform_edt(~원합)
        원rows, 원갈 = 선분표(원["종류"], 이름, dt모); 모rows, 모갈 = 선분표(모["종류"], 이름, dt원)
        표 = 집계(원rows, 모rows, 원갈, 모갈, 이름)
        빠 = [r for r in 원rows if r[3] < 0.5]; cnt, 예 = 방법(빠)
        부위방법 = {}
        for r in 빠:
            g = "a" if r[0] == "패널" else "b" if r[0] == "단차무늬" else "d" if r[0] == "색경계" else ("c" if r[2] <= 15 else "e")
            부위방법.setdefault(r[1], {k: 0 for k in "abcde"})[g] += 1
        oL = sum(r[2] for r in 원rows); 빠L = sum(r[2] for r in 빠)
        결과["보기"][이름] = dict(원화선분=len(원rows), 원화길이mm=round(oL, 1), 빠진길이mm=round(빠L, 1), 빠진비율=round(빠L / oL, 3),
                          빠진종류mm={k: round(sum(r[2] for r in 빠 if r[0] == k), 1) for k in ("실루엣", "패널", "단차무늬", "색경계")},
                          원화종류mm={k: round(sum(r[2] for r in 원rows if r[0] == k), 1) for k in ("실루엣", "패널", "단차무늬", "색경계")},
                          모델선분=len(모rows), 모델길이mm=round(sum(r[2] for r in 모rows), 1), 모델만길이mm=round(sum(r[2] for r in 모rows if r[3] < 0.5), 1),
                          모델종류mm={k: round(sum(r[2] for r in 모rows if r[0] == k), 1) for k in ("실루엣", "부품경계", "색경계", "단차", "모서리")},
                          부위=표, 방법수=cnt, 방법예=예, 부위방법=부위방법)
        log(이름, "빠진 비율 %.3f · 방법 %s" % (빠L / oL, cnt))
        그림[이름] = (원, 모, 원rows, 모rows, 표)
    json.dump(결과, open(os.path.join(D, "디테일_대조.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 그림 1: 판 × (원화 선 | 모델 선 | 겹침)
    fig, axs = plt.subplots(3, 3, figsize=(27, 30))
    for i, 이름 in enumerate(("정면", "옆", "뒤")):
        원, 모, 원rows, 모rows, 표 = 그림[이름]; A = 원["A"] | 모["A"]; y0, y1, x0, x1 = 상자(A)
        base원 = 0.55 + 0.45 * (원["rgb"].astype(float) / 255); base원[~원["A"]] = 1
        base모 = 0.55 + 0.45 * 모["렌더"]
        v = 결과["보기"][이름]
        for j, (img, t) in enumerate(((선그림(base원, 원["종류"]), "%s 원화 선 지도 — 선분 %d · %.0f mm (검=실루엣 파랑=패널 주황=단차·무늬 보라=색경계)" % (이름, v["원화선분"], v["원화길이mm"])),
                                     (선그림(base모, 모["종류"]), "%s 모델 선 지도 — 선분 %d · %.0f mm (검=실루엣 파랑=부품경계 보라=색 주황=단차 초록=모서리>25°)" % (이름, v["모델선분"], v["모델길이mm"])),
                                     (겹침그림(base원, 원rows, 모rows), "%s 겹침 — 초록 짝 있음 · 빨강 빠짐 %.0f mm (%.0f%%) · 파랑 모델에만 %.0f mm" % (이름, v["빠진길이mm"], 100 * v["빠진비율"], v["모델만길이mm"])))):
            ax = axs[i, j]; ax.imshow(img[y0:y1, x0:x1]); ax.set_title(t, fontsize=11); ax.axis("off")
    fig.suptitle("오메가몬 원화 vs PG 디자인 판 — 선 대조 (2 mm 안 짝 · 부위 = 관절 높이 상자)", fontsize=16); fig.tight_layout(rect=[0, 0, 1, 0.985])
    fig.savefig(os.path.join(D, "디테일_대조.png"), dpi=70); plt.close(fig); log("그림 1")

    # 그림 2: 가장 많이 빠진 부위 상위 5 (정면 · 빠진 길이 기준) — 원화 오림 | 모델 렌더 + 빠진 선 | 겹침
    원, 모, 원rows, 모rows, 표 = 그림["정면"]; f, cx, r0, s, R, sg = 보기["정면"]
    상위 = sorted([(b, v) for b, v in 표.items() if v["원화길이mm"] > 20], key=lambda q: -q[1]["빠진길이mm"])[:5]
    결과["상위5_정면"] = [b for b, _ in 상위]
    fig, axs = plt.subplots(5, 3, figsize=(21, 30))
    for i, (b, v) in enumerate(상위):
        pts = np.array([r[4] for r in 원rows if r[1] == b] + [r[4] for r in 모rows if r[1] == b])
        x0, x1 = int(pts[:, 0].min()) - 15, int(pts[:, 0].max()) + 15; y0, y1 = int(pts[:, 1].min()) - 15, int(pts[:, 1].max()) + 15
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, 1023), min(y1, 1023)
        base원 = 원["rgb"].astype(float) / 255; base원[~원["A"]] = 1
        빠 = np.zeros((1024, 1024), bool)
        for r in 원rows:
            if r[1] == b and r[3] < 0.5: a, c = r[5]; rr, cc = sk_line(int(round(a[1])), int(round(a[0])), int(round(c[1])), int(round(c[0]))); 빠[np.clip(rr, 0, 1023), np.clip(cc, 0, 1023)] = True
        m1 = 모["렌더"].copy(); m1[ndimage.binary_dilation(빠, iterations=1)] = (0.95, 0.1, 0.1)
        for j, (img, t) in enumerate(((base원, "%s 원화" % b), (m1, "%s 모델 렌더 + 빨강 = 빠진 원화 선" % b),
                                     (겹침그림(0.55 + 0.45 * base원, [r for r in 원rows if r[1] == b], [r for r in 모rows if r[1] == b]), "겹침 · 빠짐 %.0f/%.0f mm (%.0f%%) · 종류 %s" % (v["빠진길이mm"], v["원화길이mm"], 100 * (v["빠진비율"] or 0), " ".join("%s %.0f" % kv for kv in v["빠진종류mm"].items()))))):
            ax = axs[i, j]; ax.imshow(img[y0:y1, x0:x1]); ax.set_title(t, fontsize=12); ax.axis("off")
    fig.suptitle("정면 · 빠진 선 길이 상위 5 부위", fontsize=16); fig.tight_layout(rect=[0, 0, 1, 0.985])
    fig.savefig(os.path.join(D, "디테일_대조_상위5.png"), dpi=70); plt.close(fig); log("그림 2")
    json.dump(결과, open(os.path.join(D, "디테일_대조.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # md
    L = ["# 디테일 대조 — 원화 선 vs PG 디자인 판 (2026-09-26)", "",
         "「디테일이 부족하다」를 선으로 잰다. 원화(정면·옆·뒤)에서 선을 뽑아 종류별로 나누고, 같은 사상·같은 화소로 정사영 렌더한 모델(깊이·법선·부품 id 버퍼)의 선과 2 mm 안 짝을 찾는다.",
         "그림: `디테일_대조.png`(판 × 원화 선 | 모델 선 | 겹침) · `디테일_대조_상위5.png`(정면 상위 5 부위 확대). 숫자: `디테일_대조.json`. 코드: `실험_20260925/디테일대조.py`.", "",
         "선 종류 — 원화: ① 실루엣 ② 패널(먹선 양 끝이 갈래·실루엣에 붙음, 양쪽 색 같음) ③ 단차·무늬(끝이 자유롭거나 짧은 고리) ④ 색 경계(먹선 양쪽 색 부류 다름 + 먹선 없는 색 경계). "
         "모델: 실루엣 · 부품경계(id 바뀜) · 색경계 · 단차(같은 부품 깊이 > 1 mm) · 모서리(법선 > 25°). 선분 = 골격화 → 갈래 끊기 → RDP 2 px. 빠진 비율 = 빠진 길이 / 원화 길이.",
         "부위 = 관절.json 피벗 높이 + 좌우 x 상자 (어깨 |x| 28~78 · z > 232, 팔끝 |x| > 36 · z 140~232, 칼 x < −58 · z < 148(발톱 제외) · 대포 x > 50 · z 90~150). 뒤 원화는 좌우가 정면과 같은 「거울 뒤」라 모델도 화면 X = +x 로 렌더했다(비평_조립.py 의 yaw 180 겹침은 좌우가 바뀌어 있다).", ""]
    # 한눈에: 판별 빠진 비율 · 상위 5 부위 · 종류 분포 · 모델에만
    L += ["## 한눈에", "", "| 판 | 원화 mm | 빠짐 mm | 빠진 비율 | 빠진 종류(mm) | 모델에만 mm(원화에 없는 선 — 다면 모서리·이음) |", "|---|---|---|---|---|---|"]
    for 이름 in ("정면", "옆", "뒤"):
        v = 결과["보기"][이름]; L.append("| %s | %.0f | %.0f | **%.0f%%** | %s | %.0f |" % (이름, v["원화길이mm"], v["빠진길이mm"], 100 * v["빠진비율"], " ".join("%s %.0f" % kv for kv in sorted(v["빠진종류mm"].items(), key=lambda q: -q[1])), v["모델만길이mm"]))
    v = 결과["보기"]["정면"]; 상 = sorted([(b, r) for b, r in v["부위"].items() if r["원화길이mm"] > 20], key=lambda q: -q[1]["빠진길이mm"])[:5]
    L += ["", "정면에서 가장 많이 빠진 부위 5: " + " · ".join("**%s** %.0f/%.0f mm (%.0f%%, %s)" % (b, r["빠진길이mm"], r["원화길이mm"], 100 * r["빠진비율"], " ".join("%s %.0f" % kv for kv in list(r["빠진종류mm"].items())[:2])) for b, r in 상),
          "넣을 방법(정면 선분 수): " + " · ".join("(%s) %d" % kv for kv in v["방법수"].items()) + " — (a) 패널라인 홈 (b) 단차 판 (c) 소형 부품 (d) 색 분할 (e) 모양 변경", ""]
    if 없: L += ["⚠ STL 없는 부품(부품.json 에 있으나 파일 없음 · 모델 선에서 빠짐): " + " · ".join(없), ""]
    for 이름 in ("정면", "옆", "뒤"):
        v = 결과["보기"][이름]
        L += ["## %s — 원화 %d 선분 %.0f mm · 모델 %d 선분 %.0f mm · **빠짐 %.0f mm (%.0f%%)** · 모델에만 %.0f mm" % (이름, v["원화선분"], v["원화길이mm"], v["모델선분"], v["모델길이mm"], v["빠진길이mm"], 100 * v["빠진비율"], v["모델만길이mm"]), "",
              "원화 종류별 mm: " + " · ".join("%s %.0f" % kv for kv in v["원화종류mm"].items()) + " / 빠진 종류별 mm: " + " · ".join("%s %.0f" % kv for kv in v["빠진종류mm"].items()),
              "모델 종류별 mm: " + " · ".join("%s %.0f" % kv for kv in v["모델종류mm"].items()), "",
              "| 부위 | 원화 선분 | 원화 mm | 교차점 | 모델 선분 | 모델 mm | 교차점 | 빠진 선분 | 빠진 mm | **빠진 비율** | 빠진 종류(mm) | 모델에만 mm | (a) 홈 | (b) 단차판 | (c) 소형부품 | (d) 색분할 | (e) 모양 |", "|" + "---|" * 17]
        for b, r in sorted(v["부위"].items(), key=lambda q: -(q[1]["빠진비율"] or 0)):
            pm = v["부위방법"].get(b, {k: 0 for k in "abcde"})
            L.append("| %s | %d | %.0f | %d | %d | %.0f | %d | %d | %.0f | %s | %s | %.0f | %d | %d | %d | %d | %d |" % (
                b, r["원화선분"], r["원화길이mm"], r["원화교차점"], r["모델선분"], r["모델길이mm"], r["모델교차점"], r["빠진선분"], r["빠진길이mm"],
                ("%.0f%%" % (100 * r["빠진비율"])) if r["빠진비율"] is not None else "-", " ".join("%s %.0f" % kv for kv in r["빠진종류mm"].items()) or "-", r["모델만길이mm"], pm["a"], pm["b"], pm["c"], pm["d"], pm["e"]))
        L += ["", "빠진 선을 넣을 방법 (선분 수): " + " · ".join("(%s) %d" % kv for kv in v["방법수"].items()), "예: " + " / ".join("(%s) %s" % (k, ", ".join("%s %.0f mm" % e for e in es)) for k, es in v["방법예"].items() if es), ""]
    L += ["## 읽는 법", "- (a) 규칙 패널라인 홈: 원화 ② 패널 선 중 빠진 것 — 부품 겉에 V 홈으로 새기면 된다(선다듬기.홈파기).",
          "- (b) 단차 판(0.6~1 mm 올림): 원화 ③ 끝이 자유로운 선·짧은 고리 — 면 위에 얕은 판을 올리거나 파서 그림자 선이 생기게.",
          "- (c) 별도 소형 부품: 빠진 실루엣 조각 ≤ 15 mm — 가시·뿔·덕트처럼 밖으로 튀어나온 작은 것.",
          "- (d) 색 분할 부품: 원화 ④ 색 경계 중 모델에 없는 것 — 부품을 색으로 더 나누거나 도색 경계 홈.",
          "- (e) 모양 변경: 빠진 실루엣 조각 > 15 mm — 겉모양 자체가 원화와 다르다.",
          "- 모델에만 있는 파랑 선은 원화에 없는 선 — 부품 이음·격자 계단·다면 모서리. 많으면 「공장 선」이 아니라 「부서진 면」으로 읽힌다."]
    open(os.path.join(D, "디테일_대조.md"), "w", encoding="utf-8").write("\n".join(L))
    log("끝", os.path.join(D, "디테일_대조.md"))

if __name__ == "__main__":
    main()
