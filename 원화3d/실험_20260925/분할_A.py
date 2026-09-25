# -*- coding: utf-8 -*-
"""방식 A — 골격 블록 + 평면 컷 + 거울 짓기 (2026-09-25).

    python 분할_A.py            -> out/분할후보/A1 · A2 · A3 /lab.npy  (채점은 채점.py 로)

A1  블록만: 머리 · 가슴 · 복부 · 허리 / 다리(허벅지 · 무릎 · 정강이 · 발) × 2 / 팔 × 2 (어깨 · 윗팔 · 팔끝 · 무기)
A2  A1 + 블록 앞뒤 반쪽 (가르는 면 = 그 블록 옆 실루엣이 가장 넓은 깊이 y)
A3  A2 + 가로 컷 높이를 ±3 칸 안에서 패널라인이 가장 많이 지나는 곳으로 스냅
컷은 모두 축 평면(가로 z = c · 세로 x = c · 깊이 y = c) · 대칭 구역은 x<=축 반만 짓고 거울로 복사.
블록 높이(z 색인)는 몸 단면 폭(잘록한 곳)과 원화 색 경계를 보고 손으로 정했다 — 아래 컷 표."""
import os, sys
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
from scipy import ndimage
sys.path[:0] = [r"G:\art2real\원화3d\실험_20260925"]
import 채점 as C

O, 축 = C.O, int(round(C.축i))          # 축 = 100 (x=100 이 거울 면 위)
N = O.shape[0]
X, Y, Zi = np.meshgrid(np.arange(N), np.arange(N), np.arange(N), indexing="ij")
dx = np.abs(X - 축)

# 컷 표 (z 색인). 몸 z 19..170 = 전고 125 mm → 1 칸 ≈ 0.83 mm
컷 = dict(머리=152, 가슴=133, 복부=121, 허리=104, 무릎위=88, 무릎아래=78, 발목=33,
         L어깨=141, L윗팔=120, L칼=88, R어깨=141, R윗팔=124, R대포=97)
# 팔 = 몸통에서 떨어진 쪽 (세로 평면 |x-축| >= 18 · 좌우 같은 면) + 칼날 · 대포
def 팔(c):
    L = ((X <= 축 - 18) & (Zi >= c["무릎위"])) | ((X < 66) & (Zi >= c["발목"]))
    R = ((X >= 축 + 18) & (Zi >= c["무릎위"])) | ((X >= 128) & (Zi >= 60))
    return L & O, R & O


def 블록(c):
    """블록 이름 배열 (문자열 대신 정수 코드 + 이름 표). 대칭 구역은 왼쪽 다리 이름만 쓴다."""
    L, R = 팔(c); 이름 = []; lab = np.zeros(O.shape, np.int32)
    def 넣(n, M):
        이름.append(n); lab[M & (lab == 0)] = len(이름)
    몸 = O & ~L & ~R
    넣("머리", 몸 & (Zi >= c["머리"]))
    넣("가슴", 몸 & (Zi >= c["가슴"]))
    넣("복부", 몸 & (Zi >= c["복부"]))
    허리면 = c["허리"] + c.get("허리기울", 0.0) * (dx - 15)          # 허벅지 윗단: 바깥으로 오르는 평면(A4~)
    넣("허리", 몸 & ((Zi >= 허리면) | (dx <= 3)))                # 가랑이 V 도 허리에
    다 = 몸 & (X < 축)                                          # 왼 다리만 (오른쪽은 거울)
    넣("L허벅지", 다 & (Zi >= c["무릎위"]))
    넣("L무릎", 다 & (Zi >= c["무릎아래"]))
    넣("L정강이", 다 & (Zi >= c["발목"]))
    넣("L발", 다)
    # 칼 팔 (워그레이몬) — 어깨 방패 / 윗팔(검은 팔 x>=71) / 팔끝(드라몬 머리 · 손) / 칼날
    넣("L어깨", L & (Zi >= c["L어깨"]))
    넣("L윗팔", L & (Zi >= c["L윗팔"]) & (X >= 71))
    if "색컷" in c:                                             # 주황(드라몬 머리) ↔ 검정(팔 · 손) 평면 (A5~)
        v = c["색컷"]                                           # (a, b, o): x-z 평면 · (a, b, d, o): 3 차원 평면 (A7)
        쪽 = (v[0] * X + v[1] * Zi >= v[2]) if len(v) == 3 else (v[0] * X + v[1] * Y + v[2] * Zi >= v[3])
        넣("L팔끝주황", L & (Zi >= c["L칼"]) & 쪽)
    넣("L팔끝", L & (Zi >= c["L칼"]))
    넣("L칼", L)
    # 대포 팔 (메탈가루루몬) — 어깨 / 윗팔(x<=128) / 늑대 머리 / 대포
    넣("R어깨", R & (Zi >= c["R어깨"]))
    넣("R윗팔", R & (Zi >= c["R윗팔"]) & (X <= 128))
    if "대포색" in c:                                           # 늑대(보라) ↔ 대포(회검) 색 경계 평면 (A7)
        a, b_, o = c["대포색"]; 넣("R늑대", R & (a * X + b_ * Zi >= o))
    else:
        넣("R늑대", R & (Zi >= c["R대포"] + c.get("대포기울", 0.0) * (X - 138)))   # 늑대 턱 (A4~ 기울임)
    넣("R대포", R)
    return lab, 이름


선판 = ndimage.binary_dilation(C._열(C.I["선앞"], 1) | C._열(C.I["선뒤"], C.bs), iterations=2)   # (x, z) · 채점과 같은 2 칸
앞칸 = np.argmax(O, 1); 뒤칸 = N - 1 - np.argmax(O[:, ::-1], 1)


def 기울스냅(c, 폭=3, 각=20, 허벅지각=None):
    """허벅지 윗단 · 늑대 턱 평면을 (높이 ±폭 · 기울기 ±각°) 안에서 겉 패널라인이 가장 많이 지나는 곳으로.
    기준 기울기 = 그 블록 (x, z) 주축에 수직 · 점수 = 평면이 지나는 겉 칸 중 선 위 몫 − 작은 벗어남 벌점."""
    c = dict(c); L, R = 팔(c)
    def 주축각(M):
        P = np.argwhere(M.any(1)).astype(float); P -= P.mean(0)
        v = np.linalg.svd(P, full_matrices=False)[2][0]            # (x, z) 주축
        v = v if v[1] >= 0 else -v
        return float(np.clip(np.degrees(np.arctan2(-v[0], v[1])), -45, 45))   # 주축에 수직인 면의 기울기 (z = c + tanθ·x)
    def 점수(zc, t, xs, x0):
        zp = np.round(zc + t * (xs - x0)).astype(int); ok = (zp >= 0) & (zp < N)
        xs, zp = xs[ok].astype(int), zp[ok]; 몸 = O[xs, :, zp].any(1)
        return (선판[xs, zp] & 몸).sum() / max(몸.sum(), 1)
    for 키, 기키, M, xs, x0, 부호 in (
            ("허리", "허리기울", O & ~L & ~R & (X < 축 - 3) & (Zi < c["허리"] + 8) & (Zi >= c["무릎위"]), np.arange(72, 97), 축 - 15, -1),
            ("R대포", "대포기울", R & (Zi < c["R윗팔"]), np.arange(121, 151), 138, 1)):
        θ0 = 주축각(M); 최 = None; 폭각 = 허벅지각 if (키 == "허리" and 허벅지각) else 각
        for zc in range(c[키] - 폭, c[키] + 폭 + 1):
            for θ in np.arange(θ0 - 폭각, θ0 + 폭각 + 1, 5):
                t = np.tan(np.radians(θ)); 값 = 점수(zc, t, xs.astype(float), x0) - 0.01 * abs(zc - c[키]) - 0.001 * abs(θ - θ0)
                if 최 is None or 값 > 최[0]: 최 = (값, zc, t, θ)
        c[키] = 최[1]; c[기키] = 부호 * 최[2] if 키 == "허리" else 최[2]
        print("  기울 스냅 %s: 주축 수직 %.0f° → %.0f° · 높이 %d · 선 몫 %.2f" % (키, θ0, 최[3], 최[1], 최[0]), flush=True)
    return c


def 색판(a, sign):
    col = (sign * C.ux - C.W.U0) / (C.W.U1 - C.W.U0) * C.W.RES - 0.5; row = (C.W.Z1 - C.z) / (C.W.Z1 - C.W.Z0) * C.W.RES - 0.5
    Cc, R = np.meshgrid(col, row, indexing="ij")
    return np.stack([ndimage.map_coordinates(a[..., k].astype(np.float32), [R, Cc], order=1) for k in range(3)], -1)


def 색컷(c):
    """칼 팔 끝 (x, z) 투영에서 주황과 검정을 가장 잘 가르는 직선 → 깊이 방향으로 뻗은 평면 (균형 정확도 최대)."""
    L, _ = 팔(c); M = (L & (Zi >= c["L칼"]) & ~((Zi >= c["L윗팔"]) & (X >= 71)) & ~(Zi >= c["L어깨"])).any(1)
    p = 색판(C.I["색앞"], 1); r, g, b = p[..., 0], p[..., 1], p[..., 2]
    주 = M & (r > .6) & (b < .4) & (r - b > .3); 검 = M & (p.max(-1) < .3)
    xz = np.argwhere(M).astype(float); 주v = 주[M]; 검v = 검[M]; 최 = None
    for φ in np.radians(np.arange(0, 360, 5)):
        a, b_ = np.cos(φ), np.sin(φ); s = xz @ [a, b_]
        for o in np.quantile(s, np.linspace(.05, .95, 37)):
            q = s >= o; 값 = (q & 주v).sum() / 주v.sum() + (~q & 검v).sum() / 검v.sum()
            if 최 is None or 값 / 2 > 최[0]: 최 = (값 / 2, a, b_, o)
    print("  색컷: 법선 (%.2f, %.2f) · 균형 정확도 %.2f" % (최[1], 최[2], 최[0]), flush=True)
    c = dict(c); c["색컷"] = 최[1:]; return c


def _판별(P, 참, 거, 법선들):
    """점 P 를 평면 n·p >= o 로 참 / 거짓 가르기 — 균형 정확도 최대인 (n, o, 값)."""
    최 = None
    for n in 법선들:
        s = P @ n
        for o in np.quantile(s, np.linspace(.03, .97, 48)):
            q = s >= o; 값 = ((q & 참).sum() / 참.sum() + (~q & 거).sum() / 거.sum()) / 2
            if 최 is None or 값 > 최[2]: 최 = (n, o, 값)
    return 최


def 칼깊이컷(c):
    """칼 팔 끝: 겉 칸마다 색으로 주황 / 검정 판정 (앞 겉 = 색앞, 뒤 겉 = 색뒤) → 3 차원 평면 (앞뒤 방향 허용)."""
    L, _ = 팔(c); M = L & (Zi >= c["L칼"]) & ~((Zi >= c["L윗팔"]) & (X >= 71)) & ~(Zi >= c["L어깨"])
    P, 주, 검 = [], [], []
    for 판, 칸 in ((색판(C.I["색앞"], 1), 앞칸), (색판(C.I["색뒤"], C.bs), 뒤칸)):
        xs, zs_ = np.nonzero(M.any(1)); ys = 칸[xs, zs_]; ok = M[xs, ys, zs_]      # 몸 겉 칸이 이 블록인 기둥만
        xs, ys, zs_ = xs[ok], ys[ok], zs_[ok]; p = 판[xs, zs_]
        P.append(np.c_[xs, ys, zs_]); 주.append((p[:, 0] > .6) & (p[:, 2] < .4) & (p[:, 0] - p[:, 2] > .3)); 검.append(p.max(1) < .3)
    P = np.concatenate(P).astype(float); 주 = np.concatenate(주); 검 = np.concatenate(검)
    u = np.radians(np.arange(0, 360, 10)); w = np.radians(np.arange(-80, 81, 10))
    법선들 = [np.array([np.cos(a) * np.cos(b), np.sin(b), np.sin(a) * np.cos(b)]) for a in u for b in w]   # (x, y, z)
    n, o, 값 = _판별(P, 주, 검, 법선들)
    print("  칼 깊이 컷: 겉 칸 주황 %d · 검정 %d → 법선 (x %.2f, y %.2f, z %.2f) · 균형 정확도 %.2f" % (주.sum(), 검.sum(), *n, 값), flush=True)
    c = dict(c); c["색컷"] = (n[0], n[1], n[2], o); return c


def 대포색컷(c):
    """대포 팔 아래(윗팔 아래): 앞 판 색 보라(늑대) ↔ 회검(대포) 을 가르는 x-z 기운 평면."""
    _, R = 팔(c); M = (R & (Zi < c["R윗팔"])).any(1)
    p = 색판(C.I["색앞"], 1); r, g, b = p[..., 0], p[..., 1], p[..., 2]
    보 = M & (b > .5) & (b > r + .05) & (b > g + .05); 회 = M & (p.max(-1) < .35)
    xz = np.argwhere(M).astype(float)
    법선들 = [np.array([np.cos(a), np.sin(a)]) for a in np.radians(np.arange(0, 360, 5))]
    n, o, 값 = _판별(xz, 보[M], 회[M], 법선들)
    print("  대포 색 컷: 보라 %d · 회검 %d → 법선 (x %.2f, z %.2f) (수평에서 %.0f°) · 균형 정확도 %.2f" % (
        보.sum(), 회.sum(), *n, np.degrees(np.arctan2(-n[0], n[1])), 값), flush=True)
    c = dict(c); c["대포색"] = (n[0], n[1], o); return c


def 자동높이(c):
    """몸통 · 다리 컷 높이를 폭(단면 넓이) 프로파일에서 찾는다. 팔 컷은 손 값 그대로 (어깨만 자동)."""
    L, R = 팔(c); 몸 = O & ~L & ~R
    zs = np.nonzero(O.any((0, 1)))[0]; z0, H = zs[0], zs[-1] - zs[0]
    가 = ndimage.uniform_filter1d((몸 & (dx <= 17)).sum((0, 1)).astype(float), 3)
    다 = ndimage.uniform_filter1d((몸 & (X < 축 - 3)).sum((0, 1)).astype(float), 3)
    구 = lambda a, lo, hi: np.arange(int(z0 + lo * H), int(z0 + hi * H))
    k = 구(가, .75, .95); 머리 = k[np.argmax(가[k - 2] - 가[k + 2])]         # 목 = 올라가며 넓이가 가장 크게 주는 곳 (머리가 목보다 좁다)
    k = 구(가, .55, .8); 잘 = k[np.argmin(가[k])]                          # 복부 잘록
    위 = 잘
    while 가[위 + 1] < 1.3 * 가[잘]: 위 += 1                               # 잘록 띠 위끝 → 가슴 컷
    아 = 잘
    while 가[아 - 1] < 1.3 * 가[잘]: 아 -= 1                               # 아래끝 → 복부/허리 컷
    가운 = O[축 - 1:축 + 2].any((0, 1))
    허리 = z0 + 1
    while 허리 < zs[-1] and not 가운[허리]: 허리 += 1                      # 두 다리가 붙는 높이
    k = 구(다, .35, .55); 무 = k[np.argmin(다[k])]                          # 무릎 잘록
    k = 구(다, .05, .25); 발 = k[np.argmax(다[k - 2] - 다[k + 2])] + 1      # 발등: 내려가며 넓이가 가장 크게 느는 곳
    def 붙음(kk):                                                      # 이 높이에서 몸통(축) 덩어리가 팔 쪽(x <= 축-18)까지 닿나
        cc = ndimage.label(O[:, :, kk])[0]; m = np.unique(cc[축][cc[축] > 0])
        return len(m) > 0 and np.isin(cc[:축 - 18], m).any()
    어 = [kk for kk in zs if 붙음(kk)]
    새 = dict(c, 머리=int(머리), 가슴=int(위 + 1), 복부=int(아), 허리=int(허리 + 2), 무릎위=int(무 + 2), 무릎아래=int(무 - 8),
             발목=int(발), L어깨=int(min(어)) - 1 if 어 else c["L어깨"])
    새["R어깨"] = 새["L어깨"]
    print("  자동 높이 (손 값과 차):", {k: "%d (%+d)" % (새[k], 새[k] - c[k]) for k in 새 if k in c and not isinstance(c[k], tuple)}, flush=True)
    return 새


def 조각정리(lab, 영역, 최소=0.003):
    """부품마다 가장 큰 덩어리만 남기고 떨어진 조각 · 0.3% 미만 부품은 가장 넓게 닿은 이웃에 붙인다."""
    lab = np.where(영역, lab, 0); 전 = O.sum()
    for _ in range(3):
        for k in np.unique(lab)[1:]:
            cc, n = ndimage.label(lab == k)
            if n < 2: continue
            크 = np.bincount(cc.ravel()); 크[0] = 0
            for j in np.nonzero(크)[0]:
                if j == 크.argmax(): continue
                M = cc == j; 테 = ndimage.binary_dilation(M) & ~M & (lab > 0) & (lab != k)
                if 테.any(): lab[M] = np.bincount(lab[테]).argmax()
    while True:
        크 = np.bincount(lab.ravel()); 크[0] = 0
        작 = [k for k in np.argsort(크) if 0 < 크[k] < 최소 * 전]
        if not 작: break
        M = lab == 작[0]; 테 = ndimage.binary_dilation(M) & ~M & (lab > 0)
        if not 테.any(): break
        lab[M] = np.bincount(lab[테]).argmax()
    return lab


def 앞뒤(lab, 이름, 가를, y스냅=0):
    """가를 블록마다 옆 실루엣(x,z 로 본 넓이)이 가장 넓은 깊이 y 에서 깊이 평면으로 반 가른다.
    y스냅>0 이면 ±y스냅 안에서 겉에 드러나는 이음 칸이 (선 위 − 선 밖) 가장 큰 y 로 (A5~)."""
    lab = lab.copy(); 새 = list(이름)
    for n in 가를:
        if n not in 이름: continue
        k = 이름.index(n) + 1; M = lab == k
        if M.sum() < 400: continue
        넓 = M.sum((0, 2)); y0 = int(np.argmax(넓))
        if y스냅:
            점 = []
            for yy in range(y0 - y스냅, y0 + y스냅 + 1):
                이음 = M[:, yy, :] & M[:, yy - 1, :]                     # (x, z) 에서 y=yy 면을 지나는 칸
                드 = 이음 & ((앞칸 == yy - 1) | (앞칸 == yy) | (뒤칸 == yy - 1) | (뒤칸 == yy))
                점.append((드 & 선판).sum() - (드 & ~선판).sum() - 0.5 * abs(yy - y0))
            y0 = y0 - y스냅 + int(np.argmax(점))
        새.append(n + "뒤"); lab[M & (Y < y0)] = len(새)
        새[k - 1] = n + "앞"
    return lab, 새


def 거울짓기(lab, 이름):
    """x<=축 인 대칭 구역을 x>축 으로 복사. L 다리 이름 → R 짝(새 번호) · 가운데 블록은 같은 번호."""
    L, R = 팔(컷)
    대칭 = O & ~L & ~R
    짝 = np.arange(len(이름) + 1)
    for i, n in enumerate(이름):
        if n.startswith("L") and not any(n.startswith(p) for p in ("L어깨", "L윗팔", "L팔끝", "L칼")):
            이름.append("R" + n[1:]); 짝[i + 1] = len(이름)
    짝 = np.concatenate([짝, np.arange(len(짝), len(이름) + 1)])
    j = np.clip(2 * 축 - X[:, 0, 0], 0, N - 1)
    거 = lab[j]                                            # 거울 자리의 라벨
    쓸 = 대칭 & (X > 축) & 대칭[j] & (거 > 0)
    lab = lab.copy(); lab[대칭 & (X > 축)] = 0
    lab[쓸] = 짝[거[쓸]]
    남 = 대칭 & (lab == 0)                                  # 거울에 짝이 없는 칸(몸이 조금 비대칭) → 가까운 라벨
    if 남.any():
        i = ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
        lab[남] = lab[tuple(i)][남]
    return lab, 이름


def 스냅(c, 폭=3):
    """가로 컷 높이마다 ±폭 안에서, 그 높이 겉(앞 · 뒤 첫 칸)에 패널라인이 가장 많은 z 로."""
    선 = C._열(C.I["선앞"], 1) | C._열(C.I["선뒤"], C.bs)       # (x, z) 판
    has = O.any(1); 줄 = (선 & has).sum(0) / np.maximum(has.sum(0), 1)
    c = dict(c)
    for k in ("머리", "가슴", "복부", "허리", "무릎위", "무릎아래", "발목", "L윗팔", "L칼", "R윗팔", "R대포"):
        후 = np.arange(c[k] - 폭, c[k] + 폭 + 1)
        c[k] = int(후[np.argmax(줄[후] - 0.01 * np.abs(후 - c[k]))])  # 같으면 원래 자리
    return c


def 짓기(이름표, c, 가를, y스냅=0):
    global 컷
    컷 = c
    lab, 이름 = 블록(c)
    if 가를: lab, 이름 = 앞뒤(lab, 이름, 가를, y스냅)
    L, R = 팔(c)
    lab = 조각정리(lab, O & ((X <= 축) | L | R))
    lab, 이름 = 거울짓기(lab, 이름)
    _, lab = np.unique(lab, return_inverse=True); lab = lab.reshape(O.shape)
    os.makedirs(os.path.join(C.D, 이름표), exist_ok=True)
    np.save(os.path.join(C.D, 이름표, "lab.npy"), lab.astype(np.int16))
    print(이름표, "부품", lab.max(), "컷", c, flush=True)


if __name__ == "__main__":
    가를 = ["머리", "가슴", "복부", "허리", "L허벅지", "L정강이", "L발", "L윗팔", "L팔끝", "R윗팔", "R늑대", "R대포"]
    c0 = dict(컷)
    짓기("A1", c0, [])
    짓기("A2", c0, 가를)
    c3 = 스냅(c0)
    짓기("A3", c3, 가를)
    c4 = 기울스냅(c3); 짓기("A4", c4, 가를)                                  # (a)
    c5 = 색컷(c4); 짓기("A5", c5, 가를 + ["L팔끝주황"], y스냅=3)              # (a)+(b)+(c)
    c6 = 색컷(기울스냅(스냅(자동높이(c0)))); 짓기("A6", c6, 가를 + ["L팔끝주황"], y스냅=3)
    c7 = 대포색컷(칼깊이컷(기울스냅(c3, 허벅지각=35))); 짓기("A7", c7, 가를)      # 칼 깊이 · 허벅지 ±35° · 대포 색
    for n in sys.argv[1:] or ("A1", "A2", "A3", "A4", "A5", "A6", "A7"): C.채점(n)
