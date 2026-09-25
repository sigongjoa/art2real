# -*- coding: utf-8 -*-
"""분할 E — 건프라 색분할: 원화 색 → 도색 단위 → 부품 (2026-09-25).

    python 분할_E.py [판본=E1]    -> out/분할후보/<판본>/lab.npy · 색판.png

① 앞 · 뒤 창 판 색을 도색 색 9 가지로 양자화 (먹선 · 가는 검정은 주변 색으로 메움 · 음영 회색은 흰색)
② 격자 (x, z) 기둥마다 앞 · 뒤 색을 뜨고, 칸은 가까운 겉 쪽 색 (깊이로 섞기)
③ 색마다 3D 연결 성분 → 큰 흰 · 검 성분은 관절 잘록함(높이 단면 넓이 극소)에서 z 평면으로 한 번 더
④ 작은 조각은 닿은 면이 가장 넓은 이웃에 합침
⑤ 대칭 구역(팔 아님)은 왼쪽 반을 거울 복사"""
import os, sys, json, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
from PIL import Image
from scipy import ndimage

t0 = time.time()
판본 = sys.argv[1] if len(sys.argv) > 1 else "E1"
D = r"G:\art2real\원화3d\out\분할후보"
I = np.load(os.path.join(D, "입력.npz"))
O, ux, z, 축i = I["O"], I["ux"], I["z"], float(I["축i"])
U0, U1, Z0, Z1, RES = -0.6, 0.6, -0.1, 1.1, 1024  # win.py 값 (채점.py _열 과 같은 변환)
N = O.shape[0]

# ── ① 도색 팔레트 ──────────────────────────────────────────
이름 = ["흰", "검", "파랑", "금", "주황", "보라", "빨강", "은"]
팔 = np.array([[.95, .95, .95], [.18, .18, .2], [.35, .4, .7], [.85, .7, .2],
              [.95, .55, .15], [.5, .5, .75], [.75, .15, .15], [.7, .85, .9]])


def 양자화(rgb):
    rgb = np.clip(rgb.astype(np.float32), 0, 1)
    mx, mn = rgb.max(-1), rgb.min(-1); c = mx - mn; sat = c / np.maximum(mx, 1e-3)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]; cc = np.maximum(c, 1e-6)
    h = np.where(mx == r, ((g - b) / cc) % 6, np.where(mx == g, (b - r) / cc + 2, (r - g) / cc + 4)) * 60
    q = np.where(mx > 0.42, 0, 1)                      # 무채색: 밝으면 흰(음영 흡수) · 어두우면 검
    유 = (sat > 0.2) & (mx > 0.25)
    q = np.where(유 & ((h < 18) | (h > 330)), 6, q)
    q = np.where(유 & (h >= 18) & (h < 40), 4, q)
    q = np.where(유 & (h >= 40) & (h < 75), 3, q)
    q = np.where(유 & (h >= 180) & (h < 236), 2, q)
    q = np.where(유 & (h >= 236) & (h <= 330), 5, q)
    return q


def 판라벨(rgb, 먹):
    q = 양자화(rgb)
    검 = q == 1
    # 먹선 = 가는 검정: 열기(반지름 4 px)로 안 남는 검정 + 원화 먹선
    굵은검 = ndimage.binary_opening(검, iterations=4)
    먹선 = (검 & ~굵은검) | (먹 & ~굵은검)
    q = q.copy(); q[먹선] = -1
    _, (r, c) = ndimage.distance_transform_edt(q < 0, return_indices=True)
    q = q[r, c]
    return ndimage.median_filter(q, 5)


def 열(판):  # 창 판 → 격자 (x, z) 기둥 · 최근접
    col = np.clip(np.round((ux - U0) / (U1 - U0) * RES - 0.5), 0, RES - 1).astype(int)
    row = np.clip(np.round((Z1 - z) / (Z1 - Z0) * RES - 0.5), 0, RES - 1).astype(int)
    return 판[row[None, :], col[:, None]]  # (x, z)


앞판 = 판라벨(I["색앞"], I["원앞"]); 뒤판 = 판라벨(I["색뒤"], I["원뒤"])
cf, cb = 열(앞판), 열(뒤판)

# ── ② 깊이로 섞기: 칸마다 앞 겉 · 뒤 겉 중 가까운 쪽 색 ───────────────
has = O.any(1)
iy = np.arange(N)[None, :, None]
앞 = np.argmax(O, 1)[:, None, :]; 뒤 = (N - 1 - np.argmax(O[:, ::-1], 1))[:, None, :]  # 앞 = 작은 y? 채점과 같게
# 채점.py: 앞 = argmax(O,1) 를 앞 판 선과 맞춘다 → 작은 y 가 앞
색 = np.where(iy - 앞 <= 뒤 - iy, cf[:, None, :], cb[:, None, :])
색 = np.where(O, 색, -1)

# ── ③ 팔 구역 · 대칭 구역 ─────────────────────────────────────
X, Zi = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
팔2 = ((np.abs(X - 축i) > 20) & (Zi >= 62)) | ((X < 64) & (Zi >= 28))  # 워그레이몬 팔·칼 / 가루몬 팔·대포 (x, z)
팔구 = O & 팔2[:, None, :]
대 = O & ~팔구
if 판본 >= "E1":
    # 대칭 구역은 왼쪽 반(x ≤ 축)의 색을 거울로 (팔 제외)
    j = np.round(2 * 축i - np.arange(N)).astype(int)
    오 = np.arange(N) > 축i
    src = 색[j.clip(0, N - 1)]
    m = 대 & 오[:, None, None] & 대[j.clip(0, N - 1)] & (src >= 0)
    색 = np.where(m, src, 색)

# 관절 잘록함 높이 (다리 · 몸통 넓이 극소 · 입력에서 잰 값): 발목 28 · 정강이 위 85 · 가랑이 100 · 허리 123 · 목 150
자름 = [28, 85, 100, 123, 150]
블록 = np.zeros(O.shape, np.int32)
for k in 자름: 블록[:, :, k:] += 1
블록 = np.where(대, 블록, 99)  # 팔은 높이로 안 가름
if 판본 >= "E3":  # 머리: 목 위 가운데 기둥 (|dx| ≤ 10.5) 을 옷깃 · 어깨에서 떼어 낸다 — 세로 평면 둘
    머리 = (np.abs(X - 축i) <= 10.5)[:, None, :] & (Zi >= 150)[:, None, :]
    블록 = np.where(대 & 머리, 50, 블록)

def 합치기(lab, 문턱, 같은색=True):
    while True:
        크 = np.bincount(lab.ravel(), minlength=lab.max() + 1); 크[0] = 0
        작 = [i for i in np.argsort(크) if 0 < 크[i] < 문턱]
        if not 작: return lab
        i = 작[0]; m = lab == i
        이 = ndimage.binary_dilation(m) & ~m & (lab > 0)
        if not 이.any(): lab[m] = 0; continue  # 떠 있는 부스러기
        후, 닿 = np.unique(lab[이], return_counts=True)
        if 같은색:
            c0 = np.bincount(색[m][색[m] >= 0]).argmax()
            같 = np.array([np.bincount(색[lab == h][색[lab == h] >= 0]).argmax() == c0 for h in 후])
            if 같.any(): 후, 닿 = 후[같], 닿[같]
        lab[m] = 후[np.argmax(닿)]


def 평면화(lab, 띠=6, 한계=2.5, 새=None):
    """맞닿은 짝마다 경계 칸에 평면을 맞추고, 경계 띠 안의 두 부품 칸을 그 평면의 어느 쪽인지로 다시 나눈다.
    ponytail: 짝마다 전체 스캔 O(짝 × N³) — 짝이 수십 개라 1 분 안쪽."""
    짝 = {}
    for a in range(3):
        a0 = np.take(lab, range(0, N - 1), axis=a); a1 = np.take(lab, range(1, N), axis=a)
        d = (a0 != a1) & (a0 > 0) & (a1 > 0)
        for (i, j, k), p, q in zip(np.argwhere(d), a0[d], a1[d]):
            짝.setdefault((min(p, q), max(p, q)), []).append((i, j, k))
    for (p, q), pts in sorted(짝.items(), key=lambda t: -len(t[1])):
        P = np.array(pts, float)
        if len(P) < 20 or (새 is not None and p not in 새 and q not in 새): continue
        c = P.mean(0); _, s, vt = np.linalg.svd(P - c, full_matrices=False); nrm = vt[-1]
        if s[-1] / np.sqrt(len(P)) > 한계: continue  # 굽은 경계(색 섬 둘레)는 평면이 아니다 — 그대로
        lo = np.maximum(P.min(0).astype(int) - 띠, 0); hi = np.minimum(P.max(0).astype(int) + 띠 + 1, N)
        sl = tuple(slice(l, h) for l, h in zip(lo, hi))
        L = lab[sl]; m = (L == p) | (L == q)
        if not m.any(): continue
        g = np.stack(np.meshgrid(*[np.arange(l, h) for l, h in zip(lo, hi)], indexing="ij"), -1)
        sd = (g - c) @ nrm
        근 = ndimage.distance_transform_edt(~((L == p) & ndimage.binary_dilation(L == q) | (L == q) & ndimage.binary_dilation(L == p))) <= 띠
        mm = m & 근 & (np.abs(sd) <= 띠)
        # 어느 쪽이 p 인지: 띠 안 p 칸의 부호 다수결
        sp = np.sign(np.median(sd[(L == p) & mm])) if ((L == p) & mm).any() else 1
        if sp == 0: sp = 1
        L[mm] = np.where(sd[mm] * sp >= 0, p, q)
    return lab


def 거울라벨(lab):
    j = np.round(2 * 축i - np.arange(N)).astype(int).clip(0, N - 1)
    오 = (np.arange(N) > 축i)[:, None, None]
    src = lab[j]
    m = 대 & 오 & 대[j] & (src > 0)
    lab = np.where(m, src, lab)
    # 좌우 복사본이 같은 번호 → 연결 성분으로 다시 번호
    out = np.zeros_like(lab); n = 0
    for v in range(1, lab.max() + 1):
        l, k = ndimage.label(lab == v)
        out[l > 0] = l[l > 0] + n; n += k
    return 합치기(out, int(0.002 * O.sum()), 같은색=False)


if 판본 < "E5":
    # ── ④ 색 × 블록 연결 성분 ────────────────────────────────────
    키 = np.where(O, 색 * 100 + 블록, -1)
    lab = np.zeros(O.shape, np.int32); n = 0
    for v in np.unique(키[키 >= 0]):
        l, k = ndimage.label(키 == v)  # 6 이웃
        lab[l > 0] = l[l > 0] + n; n += k


    lab = 합치기(lab, int(0.003 * O.sum()))
    lab = 합치기(lab, int(0.006 * O.sum()), 같은색=False)
    _, lab = np.unique(lab, return_inverse=True); lab = lab.reshape(O.shape)
    lab = np.where(O, lab, 0)




if 판본 < "E5":
    if 판본 >= "E2":
        lab = 평면화(lab, 한계=1.5 if 판본 >= "E4" else 2.5)
        lab = 거울라벨(lab)
        _, lab = np.unique(lab, return_inverse=True); lab = lab.reshape(O.shape); lab = np.where(O, lab, 0)

    os.makedirs(os.path.join(D, 판본), exist_ok=True)
    np.save(os.path.join(D, 판본, "lab.npy"), lab.astype(np.int16))
    P = (np.vstack([팔, [[1, 1, 1]]]) * 255).astype(np.uint8)
    Image.fromarray(np.concatenate([P[앞판], P[뒤판]], 1)).save(os.path.join(D, 판본, "색판.png"))
    print(판본, "부품", lab.max(), "· %.1f s" % (time.time() - t0))


# ── E5 하이브리드: A4 블록 평면 컷을 뼈대로, 색 경계로만 더 가른다 ──────────────
def 크게보기(lab, 경로):
    """앞 · 뒤 · 왼옆 · 오른옆 (부품 색 + 경계 검정 + 깊이 음영) · 4 배."""
    rng = np.random.default_rng(3); col = (rng.uniform(.3, .95, (lab.max() + 1, 3)) * 255).astype(np.uint8)
    판 = []
    for L, 뒤집 in ((lab, False), (lab[:, ::-1], True), (lab.transpose(1, 0, 2), False), (lab.transpose(1, 0, 2)[:, ::-1], True)):
        d = np.argmax(L > 0, 1); h = (L > 0).any(1)
        img = np.where(h, np.take_along_axis(L, d[:, None, :], 1)[:, 0, :], 0)
        e = np.zeros_like(h)
        for a in (0, 1): e |= np.pad(np.diff(img, axis=a) != 0, [(0, 1) if k == a else (0, 0) for k in range(2)])
        e |= np.pad(np.abs(np.diff(d.astype(int), axis=1)) > 6, [(0, 0), (0, 1)]) & False
        sh = 1 - 0.45 * (d - d[h].min()) / max(1, np.ptp(d[h]))
        rgb = (col[img] * sh[..., None]).astype(np.uint8); rgb[e & h] = 0; rgb[~h] = 255
        rgb = np.transpose(rgb, (1, 0, 2))[::-1]
        if 뒤집: rgb = rgb[:, ::-1]
        판.append(rgb[15:178, 30:170] if len(판) < 2 else rgb[15:178, 65:130])
    im = np.concatenate(판, 1)
    Image.fromarray(im).resize((im.shape[1] * 4, im.shape[0] * 4), Image.NEAREST).save(경로)


if "E5" <= 판본 < "E8":
    import 분할_A as A
    c4 = A.기울스냅(A.스냅(dict(A.컷)))
    AL, AR = A.팔(c4)
    대 = O & ~AL & ~AR                                   # 거울 구역은 A 와 같게 (거울라벨이 쓴다)
    lab = np.load(os.path.join(D, "A4", "lab.npy")).astype(np.int32); lab = np.where(O, lab, 0)
    n0 = lab.max()
    # 겉 색 판: 앞 · 뒤 색이 같으면 통째 그 색, 다르면 각 겉에서 T 칸까지만 그 색 · 속은 색 없음(-1)
    T = 3
    d앞, d뒤 = iy - 앞, 뒤 - iy
    색2 = np.where(cf[:, None, :] == cb[:, None, :], cf[:, None, :],
                  np.where(d앞 <= T, cf[:, None, :], np.where(d뒤 <= T, cb[:, None, :], -1)))
    색2 = np.where(O, 색2, -1)
    j = np.round(2 * 축i - np.arange(N)).astype(int).clip(0, N - 1)
    m = 대 & (np.arange(N) > 축i)[:, None, None] & 대[j]
    색2 = np.where(m, 색2[j], 색2)
    최소 = int((0.005 if 판본 >= "E6" else 0.003) * O.sum()); 새 = set(); 기록 = []
    for p in range(1, n0 + 1):
        M = lab == p
        c = 색2[M]; c = c[c >= 0]
        if not len(c): continue
        주 = np.bincount(c).argmax()
        for k in np.unique(c):
            if k == 주 or (판본 >= "E6" and 주 in (0, 1) and k in (0, 1)): continue   # E6~: 흰↔검 은 안 가름 (먹 · 음영 흔적이 많다)
            판부 = 판본 >= "E7" and (M & 대).sum() > 0.5 * M.sum() and 주 == 0 and k == 2   # 대칭 구역 흰 위 파랑 = 가슴 무늬 판
            A_ = ndimage.binary_closing(M & (색2 == k), iterations=5 if 판부 else 2) & M   # 가는 무늬 사이를 메워 판 하나로
            l, nk = ndimage.label(A_)
            크 = np.bincount(l.ravel()); 크[0] = 0
            for i in np.nonzero(크 >= (int(0.003 * O.sum()) if 판부 else 최소))[0]:
                v = lab.max() + 1; lab[l == i] = v; 새.add(v); 기록.append((p, 이름[주], 이름[k], int(크[i])))
    print("색 부품 %d 개:" % len(새), 기록, flush=True)
    쟤 = lambda t: print("  %s: 색 부품 %d 개 남음 · 칸 %d" % (t, sum((lab == v).any() for v in 새), sum((lab == v).sum() for v in 새)), flush=True)
    쟤("가른 뒤")
    lab = 평면화(lab, 한계=1.5, 새=새); 쟤("평면화 뒤")
    lab = 거울라벨(lab)
    _, lab = np.unique(lab, return_inverse=True); lab = lab.reshape(O.shape); lab = np.where(O, lab, 0)
    os.makedirs(os.path.join(D, 판본), exist_ok=True)
    np.save(os.path.join(D, 판본, "lab.npy"), lab.astype(np.int16))
    크게보기(lab, os.path.join(D, 판본, "크게.png"))
    print(판본, "부품", lab.max(), "· %.1f s" % (time.time() - t0))


# ── E8 (A4 뼈대) · E9 (A7 뼈대): 팔 색 = 평면 한 장 · 가슴 파랑 = 볼록 껍질 판 하나 · 색 부품은 앞 블록에서만 ──
def 색평면(P, 색v, 주, k):
    """칸 좌표 P 에서 주색 · 강조색을 가장 잘 가르는 평면 (법선 = (x,z) 안 5° 간격 + 깊이 y) · 균형 정확도."""
    a, b = 색v == 주, 색v == k; 최 = (0, None, None)
    법 = [np.array([np.cos(t), 0, np.sin(t)]) for t in np.radians(np.arange(0, 360, 5))] + [np.array([0, 1., 0]), np.array([0, -1., 0])]
    for n in 법:
        s = P @ n
        for o in np.quantile(s[a | b], np.linspace(.05, .95, 37)):
            q = s >= o; 값 = ((q & b).sum() / b.sum() + (~q & a).sum() / a.sum()) / 2
            if 값 > 최[0]: 최 = (값, n, o)
    return 최


if 판본 >= "E8":
    from skimage.morphology import convex_hull_image
    import 분할_A as A
    c4 = A.기울스냅(A.스냅(dict(A.컷)))
    AL, AR = A.팔(c4)
    대 = O & ~AL & ~AR
    뼈 = "A7" if 판본 >= "E9" else "A4"
    lab = np.load(os.path.join(D, 뼈, "lab.npy")).astype(np.int32); lab = np.where(O, lab, 0)
    n0 = lab.max(); T = 3
    d앞, d뒤 = iy - 앞, 뒤 - iy
    색2 = np.where(cf[:, None, :] == cb[:, None, :], cf[:, None, :],
                  np.where(d앞 <= T, cf[:, None, :], np.where(d뒤 <= T, cb[:, None, :], -1)))
    색2 = np.where(O, 색2, -1)
    겉앞 = O & (d앞 == 0); 겉뒤 = O & (d뒤 == 0)
    최소 = int(0.005 * O.sum()); 새 = set(); 기록 = []
    # ① 팔 부품: 앞 블록(앞 겉 노출 ≥ 뒤 겉 노출)만 · 유채색이 낀 짝만 · 평면 한 장
    for p in range(1, n0 + 1):
        M = lab == p
        if (M & 대).sum() > 0.5 * M.sum() or (M & 겉앞).sum() < (M & 겉뒤).sum(): continue
        for _ in range(2):                                   # 한 부품에서 많아야 두 번
            M = lab == p; c = 색2[M]; c = c[c >= 0]
            if not len(c): break
            cnt = np.bincount(c, minlength=8); 주 = cnt.argmax()
            후 = [k for k in np.argsort(-cnt) if k != 주 and cnt[k] >= 최소 and not (주 in (0, 1) and k in (0, 1))]
            if not 후: break
            k = 후[0]; P = np.argwhere(M).astype(float)
            값, n, o = 색평면(P, 색2[M], 주, k)
            q = P @ n >= o; 크 = q.sum(), (~q).sum()
            if 값 < 0.75 or min(크) < 최소: break
            v = lab.max() + 1; idx = P[q].astype(int); lab[idx[:, 0], idx[:, 1], idx[:, 2]] = v; 새.add(v)
            기록.append((p, 이름[주], 이름[k], "법선(%.2f,%.2f,%.2f)" % tuple(n), round(float(값), 2), int(크[0])))
    # ② 가슴 파랑: 대칭 구역 앞 파랑 (복부 컷~목) 을 좌우 합친 (x,z) 볼록 껍질 · 앞 겉 T 칸 판 하나
    j = np.round(2 * 축i - np.arange(N)).astype(int).clip(0, N - 1)
    zz = np.arange(N)
    파 = (cf == 2) & 대.any(1) & ((zz >= c4["복부"]) & (zz < c4["머리"]))[None, :]
    파 = 파 | 파[j]
    if 파.sum() > 20:
        껍 = convex_hull_image(파)
        판M = 대 & 껍[:, None, :] & (d앞 <= T) & (lab > 0)
        v = lab.max() + 1; lab[판M] = v; 새.add(v); 기록.append(("가슴판", int(판M.sum())))
    print("색 부품 %d 개:" % len(새), 기록, flush=True)
    lab = 평면화(lab, 한계=1.5, 새=새)
    lab = 거울라벨(lab)
    _, lab = np.unique(lab, return_inverse=True); lab = lab.reshape(O.shape); lab = np.where(O, lab, 0)
    os.makedirs(os.path.join(D, 판본), exist_ok=True)
    np.save(os.path.join(D, 판본, "lab.npy"), lab.astype(np.int16))
    크게보기(lab, os.path.join(D, 판본, "크게.png"))
    print(판본, "(뼈대 %s) 부품" % 뼈, lab.max(), "· %.1f s" % (time.time() - t0))
