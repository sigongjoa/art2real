# -*- coding: utf-8 -*-
"""**3판을 기하로 깎는다.** 학습 없음, 생성 없음, 지어낼 여지 없음.

    python hull.py                 # 오메가몬 3판 -> out/hull.glb + 증명 그림

정면·측면·후면 실루엣이 각각 기둥을 만들고, 그 교집합이 형상의 **상한**이다
(Laurentini 의 visual hull). 오목부는 못 잡지만 **시점과 치수는 원리적으로 안 무너진다** —
없는 걸 지어내는 단계가 아예 없기 때문이다.

## 원화를 창에 앉히는 규약

턴어라운드 3판은 **같은 인물을 같은 키로** 그린다. 그래서 판마다 실루엣 높이를 창의
z 범위에 맞추면 세 판이 한 배율을 공유한다 — 이게 고전 화법기하의 전제다(Church Part I).
가로는 중심선 정렬.

**지시선을 먼저 뗀다.** `omega_side` 는 지시선 때문에 bbox 가로가 1024 인데 실제 물건은
248 이다(4.1배). 그대로 앉히면 인물이 창 왼쪽 구석으로 쭈그러든다.

그런데 bbox 키는 **인물의 키가 아니다.** 판마다 튀어나온 게 달라서(칼끝·머리카락·망토)
bbox 로 재면 같은 인물이 판마다 다른 배율로 앉는다. 그래서 앉힌 뒤에 front 를 기준으로
side·back 을 다시 맞춘다 — `align`.

## 이게 안 잡는 것

- 오목부 — 겨드랑이, 견갑 안쪽, 다리 사이. hull 은 언제나 실제보다 두껍다
- 3판이 서로 안 맞으면 hull 이 **과하게 깎인다.** 그 손실이 곧 「눈속임의 양」이다
"""
import os
import sys

import numpy as np
import trimesh
from scipy import ndimage
from skimage import measure

import win as W

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
IN7 = os.path.normpath(os.path.join(HERE, "..", "트레일", "trail7_part3d", "in"))
N = 256                                          # 복셀 격자. 창 한 변
BACK_SIGN = +1                                   # 오메가몬 시트의 후면 좌우 규약. **케이스 데이터**

# 케이스마다 다른 것은 여기 둘뿐이다 — 파일 이름과 후면 좌우 규약.
# `back_sign` 은 짐작하지 않는다. 양쪽으로 깎아보고 원화를 더 잘 덮는 쪽이다 (`pick_back_sign`).
CASES = {
    "오메가몬": {"src": {"front": "omega_front_clean.png", "side": "omega_side.png",
                         "back": "omega_back.png"}, "back_sign": +1},
    # 3D 모델에서 뽑은 판. **정답 메시가 같이 있다** (`시트.py`). 손그림이 아니라
    # 세 판이 자동으로 일치하므로 `align` 은 항등에 가깝게 나와야 맞다
    "소체": {"src": {"front": "front.png", "side": "side.png", "back": "back.png"},
             "dir": os.path.join("out", "시트", "소체"), "back_sign": -1},
}
# ⚠ `pauldron_front/side/back` 을 케이스로 넣지 말 것. **턴어라운드가 아니다** —
# 정면은 뿔 4개 달린 어깨갑, 측면은 아치 두 개 뚫린 다른 물건, 후면은 방패+천+원통이고
# 높이도 1024/732/704 로 제각각이다. trail7 스크립트도 front 만 쓴다.
# 2026-09-09 에 이걸 3판으로 착각하고 판수 표에 넣었다가 무효로 뺐다.
CASE = "오메가몬"                                 # 기본 케이스
THRESH = 0.06                                    # 못 덮기 문턱. 정렬 뒤 잰 값 위에 얹었다
LAM = 0.20                                       # 부조가 쓰는 기둥 깊이 비율. **측면 판이 잰 값**
# 짐작한 값이 아니다. 부조는 안쪽으로만 깎으니 깎을수록 측면 실루엣이 줄고, 측면 판은
# 그 높이의 진짜 깊이를 그린 **데이터**다. 그래서 측면과 안 싸우는 최대 진폭이 답이다.
# 쓸어서 잰 값 (복셀끼리 비교, 마칭큐브 몫 제외):
#     lam   0.45   0.35   0.25   0.20   0.15   0.10
#     side  8.29%  6.57%  4.57%  3.70%  2.96%  2.08%   <- 측면이 잃는 양
#     형태  2.25   1.78   1.29   1.05   0.82   0.60    <- 클수록 상자에서 멀다
# front 는 어느 값에서도 0.00% 다 — 깊이 깎기는 정면 실루엣을 원리적으로 안 건드린다.
# 0.5 를 넘으면 기둥이 비므로 상한은 어차피 0.5 다.

SMOOTH = 2.0                                     # 깊이맵을 **부품 안에서만** 미는 반지름 (512² 화소)
# 잰 값에서 왔다. 깎은 표면의 계단(x 2차차분 / 깊이범위)이 정답 메시의 2~3배였다:
#     정답 0.019 / 0.013   이진 hull 0.030 / 0.004   깊이 깎기 0.045 / 0.039   (소체 / robot)
# 그리고 그 값이 깊이맵 자체의 계단(0.036 / 0.043)과 거의 같았다 — 깎기가 계단을 만드는 게
# 아니라 **깊이맵의 계단을 표면에 그대로 새긴다.** 마칭큐브는 무죄다 (메시 왕복 뒤 오히려 준다).
# 0 이면 예전 동작 그대로. 부품 경계를 넘어 밀면 판 사이의 골이 메워지므로 라벨 안에서만 민다.

SMOOTH_OUT = 0.0                                 # **결과**를 미는 가우시안 σ (칸). 0 이면 끔 (`smooth_field`)
# **꺼 뒀다.** σ2 는 찢김을 푼다 (knight · robot: 오라클0.50 찢김 28~31% -> 1~7%, 정답 6~11%). 그런데
# 오메가몬 정면 실루엣을 먹는다 — 못 덮은 4.07% -> 7.45%, 아래 되받아 재기 assert(6%)에 걸렸다
# (2026-09-11). 칼끝·가시 같은 가는 것이 흐림에 사라진다. 3D 로 흐리면 실루엣이 같이 흐려지므로,
# 실루엣을 안 건드리는 스무딩(앞·뒷면 깊이만 미는 것)이 들어올 때까지 끈다. 함수는 벤치가 쓴다.


def declutter(m, minh=8):
    """지시선 제거 — 열 높이가 minh 화소 미만인 열을 버린다 (trail7 규칙)."""
    return m & (m.sum(0) >= minh)[None, :]


def to_win(m, *extra):
    """원화 마스크를 창에 앉힌다. **키로 한 번** 재고 가로는 중심 정렬.

    창의 z 는 [-0.1, 1.1] 이고 물건은 z=0..1 에 선다 — `win.normalize` 와 같은 규약.

    `extra` 로 준 배열은 **마스크와 똑같은 변환**으로 함께 옮긴다 (깊이맵). 변환을 두 군데
    적어두면 언젠가 어긋나므로 한 군데서만 만든다. 반환은 extra 가 없으면 마스크 하나."""
    import cv2
    ys, xs = np.where(m)
    y0, y1, x0c, x1c = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    h = int(round(W.RES / (W.Z1 - W.Z0)))        # z 1.0 이 차지하는 화소 수
    w = max(1, int(round((x1c - x0c) * h / (y1 - y0))))
    top = int(round((W.Z1 - 1.0) / (W.Z1 - W.Z0) * W.RES))
    x0 = (W.RES - w) // 2
    ys0, ys1 = max(top, 0), min(top + h, W.RES)
    xs0, xs1 = max(x0, 0), min(x0 + w, W.RES)

    def place(a, dtype):
        c = a[y0:y1, x0c:x1c]
        r = cv2.resize(c.astype(np.float32), (w, h), interpolation=cv2.INTER_NEAREST)
        out = np.zeros((W.RES, W.RES), dtype)
        out[ys0:ys1, xs0:xs1] = r[:ys1 - ys0, :xs1 - xs0].astype(dtype)
        return out

    got = place(m, bool)
    if not extra:
        return got
    return (got,) + tuple(place(a, np.float32) for a in extra)


def project(masks, back_sign=BACK_SIGN):
    """복셀 없이 hull 의 세 실루엣. **front·back 이 같은 u 축이라** 한 장에서 닫힌다:

        voxel[x, y, z] = F[z,x] & B[z,x] & S[z,y]      ->  x 와 y 가 분리된다

    그래서 front 실루엣은 (F&B) 에서 **깊이가 없는 높이의 행만 지우면** 된다. 복셀 격자보다
    정확하고(이산화 없음) 1000배 빠르다 — `align` 이 이걸 수백 번 부른다. 최종 메시는 `carve`.
    """
    flip = back_sign != W.VIEW_AXIS["front"][1]        # 후면 규약이 뒤집히면 열을 뒤집는다
    f, s = masks["front"], masks["side"]
    b = masks["back"][:, ::-1] if flip else masks["back"]
    both = f & b
    pf = both & s.any(1)[:, None]                     # 그 높이에 깊이가 없으면 남을 수 없다
    ps = s & both.any(1)[:, None]
    return {"front": pf, "side": ps, "back": pf[:, ::-1] if flip else pf}


def miss(masks, back_sign=BACK_SIGN):
    """시점마다 hull 이 원화를 **못 덮은** 비율. hull 은 상한이니 0 이어야 맞다.
    남은 값이 곧 판들이 서로 싸운 양이다."""
    p = project(masks, back_sign)
    return {v: float((masks[v] & ~p[v]).sum()) / max(int(masks[v].sum()), 1) for v in W.VIEWS}


def _warp_one(a, v, p):
    """`align` 의 5개 값 중 시점 `v` 몫을 배열 하나에 바른다. front 는 기준이라 안 움직인다.
    마스크든 깊이맵이든 **같은 값을 발라야** 두 장이 어긋나지 않는다."""
    if v == "front":
        return a
    return W.warp_art(a, 0, p[0], p[1]) if v == "side" else W.warp_art(a, p[2], p[3], p[4])


def _warp(masks, p):
    return {v: _warp_one(m, v, p) for v, m in masks.items()}


def align(masks, back_sign=BACK_SIGN):
    """front 고정, side·back 을 맞춘다. 목적은 **못 덮은 양의 합**.

    **미지수는 6개가 아니라 5개다.** side 의 가로 이동은 hull 을 깊이(y)로 밀 뿐이라 세 실루엣
    중 무엇도 안 바꾼다. 알려진 값을 넣고 되찾아 보면 side dy·s 와 back 셋은 정확히 나오는데
    side dx 만 안 나오고, 그런데도 잔여비용이 0 이다 (`demo`). 못 보는 값을 억지로 푸는 대신
    창의 중심정렬을 그대로 둔다 — y=0 이 허리라는 규약이 그 자리다.

    좌표하강. 화소 단위라 값이 계단이고 기울기법을 못 쓴다. 평가가 1ms 라 이걸로 충분하다.
    ponytail: 항등에서 출발하는 국소 탐색이다. 판이 크게 어긋난 시트가 오면 다중 출발.
    """
    p, step = [0., 1., 0., 0., 1.], [16., .04, 16., 16., .04]
    cost = lambda q: sum(miss(_warp(masks, q), back_sign).values())
    while step[0] >= 1 or step[1] >= .002:
        moved = False
        for i in range(5):
            base = cost(p)
            for d in (+step[i], -step[i]):
                q = list(p); q[i] += d
                c = cost(q)
                if c < base - 1e-9:
                    p, base, moved = q, c, True
        if not moved:
            step = [t / 2 for t in step]
    return p


def carve(masks, back_sign=BACK_SIGN):
    """복셀 격자를 세 시점으로 깎는다. 격자는 창과 같은 좌표에 있다.

    **후면의 좌우 규약은 케이스 데이터다.** 렌더 규약(az180 화면 x = -x)을 그린 그림에
    그대로 대면 안 된다 — 오메가몬은 검과 포가 좌우로 갈린 비대칭 물건이라, 규약이
    뒤집히면 검이 포를 깎는다. 실측: -1 이면 정면 0.577 / 후면 0.554,
    +1 이면 정면 0.933 / 후면 0.919. 이 시트는 +1 이다."""
    u = W.U0 + (np.arange(N) + 0.5) / N * (W.U1 - W.U0)     # x 가로, y 깊이
    z = W.Z0 + (np.arange(N) + 0.5) / N * (W.Z1 - W.Z0)
    X, Y, Z = np.meshgrid(u, u, z, indexing="ij")
    keep = np.ones(X.shape, bool)
    for v, m in masks.items():
        a, sign = W.VIEW_AXIS[v]
        if v == "back":
            sign = back_sign
        py, px = W.topix(sign * (X if a == 0 else Y), Z)
        keep &= m[py, px]
    return keep, (u, u, z)


def register_sheets():
    """`시트.py` 가 만든 판을 케이스로 자동 등록한다. **정답 메시가 딸린 것들이다.**

    `back_sign` 은 여기선 케이스 데이터가 아니다 — `시트.py` 가 `W.VIEW_AXIS["back"]`
    (부호 -1) 로 그렸으니 깎을 때도 -1 이어야 한다. 그리는 규약과 깎는 규약이 같은 값을 쓴다."""
    root = os.path.join(OUT, "시트")
    if not os.path.isdir(root):
        return
    for n in sorted(os.listdir(root)):
        d = os.path.join(root, n)
        if n not in CASES and os.path.exists(os.path.join(d, "front.png")):
            CASES[n] = {"src": {v: "%s.png" % v for v in W.VIEWS},
                        "dir": os.path.join("out", "시트", n), "back_sign": -1}


def art_dir(case=None):
    """케이스의 원화가 어디 있나. 기본은 트레일의 원화 창고."""
    d = CASES[case or CASE].get("dir")
    return os.path.join(HERE, d) if d else IN7


def pick_back_sign(masks):
    """후면 좌우 규약을 **잰다.** 양쪽으로 hull 을 만들어 원화를 더 잘 덮는 쪽.

    렌더 규약(az180 화면 x = -x)을 그린 시트에 그대로 대면 안 된다 — 오메가몬은 검과 포가
    좌우로 갈린 비대칭 물건이라 규약이 뒤집히면 검이 포를 깎는다."""
    best, sign = None, +1
    for s0 in (+1, -1):
        tot = sum(miss(masks, s0).values())
        if best is None or tot < best:
            best, sign = tot, s0
    return sign


def load_labels(v, m, case=None):
    """`깊이.py` 가 낸 판 라벨을 원화 화소 크기로. `load_depth` 와 **같은 변환**이라야 한다.

    **라벨 0 을 제일 가까운 판으로 채운다.** 0 은 선 띠고, 선은 두 판 사이의 골이라 그 양쪽
    벽은 각각 이웃 판의 것이다. 안 채우면 부품이 덩어리를 다 못 덮는다 — 실측으로 복셀
    262,621 중 28,249(10.8%)가 어느 부품에도 안 들어갔다.

    깊이맵 쪽은 반대로 **안 채운다**. 거기서 0 은 「모르는 것」이라 채우면 없는 깊이를
    지어내지만, 여기서 0 은 「경계」라 어느 쪽 판인지가 답이 있다."""
    import cv2
    from scipy import ndimage
    lab = np.load(os.path.join(OUT, "깊이", case or CASE, v, "labels_grown.npy"))
    if (lab == 0).any() and (lab > 0).any():
        idx = ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
        lab = lab[tuple(idx)]
    return cv2.resize(lab.astype(np.float32), (m.shape[1], m.shape[0]),
                      interpolation=cv2.INTER_NEAREST)


def _smooth_parts(d, lab, sigma=SMOOTH):
    """깊이맵을 **부품 라벨 안에서만** 민다. 골(lab==0)은 손대지 않는다.

    판 경계를 넘어 밀면 판 사이의 골이 메워진다 — 그 골이 깎기가 홈을 파는 근거다.
    라벨마다 정규화 합성곱(값·마스크를 같이 흐리고 나눈다)이라 라벨 밖 값이 안 새어든다."""
    if sigma <= 0:
        return d
    import cv2
    out = d.copy()
    for L in np.unique(lab):
        if L == 0:
            continue
        m = (lab == L).astype(np.float32)
        num = cv2.GaussianBlur(d * m, (0, 0), sigma)
        den = cv2.GaussianBlur(m, (0, 0), sigma)
        out = np.where(lab == L, num / np.maximum(den, 1e-6), out)
    return out


def _upsize(h, size):
    """nan 을 안 번지게 키운다. **NEAREST 가 계단을 두 배로 만들던 자리다.**

    값과 「아는 곳」 마스크를 같이 선형보간하고 나눈다 — nan 은 마스크로만 빠지고
    아는 값끼리만 섞인다."""
    import cv2
    known = (~np.isnan(h)).astype(np.float32)
    val = cv2.resize(np.nan_to_num(h) * known, size, interpolation=cv2.INTER_LINEAR)
    kn = cv2.resize(known, size, interpolation=cv2.INTER_LINEAR)
    return np.where(kn > 0.5, val / np.maximum(kn, 1e-6), np.nan)


def load_depth(v, m, groove=3, case=None):
    """`깊이.py` 가 낸 깊이맵을 원화 화소 크기로 되돌리고 0~1 로 정규화한다.

    art3d 는 512² 로 줄여 돌았고 원화는 1024² 다. **프레임이 같으니** 되키우면 맞는다 —
    잘라내기·중심맞추기는 `to_win` 이 마스크와 함께 해준다.

    **깊이 0 은 두 가지다.** 판 경계의 골(진짜 0)과 라벨이 안 붙은 자리(모르는 것).
    가르는 건 거리다 — 라벨에서 `groove` 화소 안쪽이면 골, 그보다 멀면 모르는 것이다.
    그리고 **모르는 자리는 안 깎는다** (h=1, hull 표면 그대로). 모르는 걸 0 으로 읽으면
    「제일 들어간 곳」이 되어 발이 통째로 날아간다 — 실측으로 side 못 덮음이
    0.00 에서 21.0% 로 뛰었다. 지어내지 않는 쪽은 안 깎는 쪽이다."""
    import cv2
    # **판보다 낡은 깊이맵은 쓰지 않는다.** 판을 다시 구우면 깊이맵도 다시 내야 한다.
    # 2026-09-12: 거꾸로 선 마네킹을 고쳐 다시 구웠는데 09-10 깊이맵이 남아 있어,
    # 거꾸로 깊이를 바로 선 마스크에 얹고 있었다 (조용히, 값만 이상하게)
    dp = os.path.join(OUT, "깊이", case or CASE, v, "depth.npy")
    sp = os.path.join(OUT, "시트", case or CASE, "truth.glb")
    if os.path.exists(sp) and os.path.exists(dp) and os.path.getmtime(dp) < os.path.getmtime(sp):
        raise RuntimeError("%s/%s 깊이맵이 판보다 낡았다 — python 깊이.py %s 로 다시 낼 것"
                           % (case or CASE, v, case or CASE))
    d = np.load(dp).astype(np.float32)
    lab = np.load(os.path.join(OUT, "깊이", case or CASE, v, "labels_grown.npy"))
    near = cv2.distanceTransform((lab == 0).astype(np.uint8), cv2.DIST_L2, 3) <= groove
    d = _smooth_parts(d, lab, SMOOTH)
    h = np.where((lab > 0) | near, d, np.nan)                # nan = 모르는 것
    h = _upsize(h, (m.shape[1], m.shape[0]))
    hi = np.nanmax(np.where(m, h, np.nan)) if m.any() else 1.0
    return np.nan_to_num(np.clip(h / max(float(hi), 1e-6), 0, 1), nan=1.0)


def carve_depth(masks, deps, lam=LAM, back_sign=BACK_SIGN):
    """hull 안쪽을 앞·뒤 깊이맵으로 깎는다. **hull 이 상한이라 진폭을 지어내지 않는다.**

    이진 hull 은 높이마다 (x집합)×(y집합) 이라 단면이 축정렬 직사각형밖에 못 된다 —
    앞면 y 가 x 에 아예 안 의존한다. 그래서 45도에서 덩어리로 보인다.

    hull 이 허용하는 기둥 [lo, hi] 을 깊이가 **안쪽에서** 자른다:

        jf = lo + (1-hf)·lam·(hi-lo)      앞면.  hf=1(제일 튀어나온 데)이면 hull 표면
        jb = hi - (1-hb)·lam·(hi-lo)      뒷면
        lam <= 0.5 라야 jf <= jb 다 — 기둥이 비지 않는다

    깊이의 골(판 경계)이 그대로 홈이 되고, 판 안쪽은 평면이라 각이 산다.

    **side 는 이진 그대로 둔다.** 측면 판은 한쪽 면만 보여줘서 반대쪽을 못 말한다.
    거울로 채우면 오메가몬에 없는 대칭을 지어내는 것이다 (검과 포는 좌우가 다르다)."""
    keep, axes = carve(masks, back_sign)
    u, _, z = axes
    X2, Z2 = np.meshgrid(u, z, indexing="ij")        # (x, z) — carve 와 같은 표본화
    j = np.arange(N)[None, :, None]
    lo = np.where(keep, j, N).min(1).astype(np.float32)          # (x, z) 앞면 칸
    hi = np.where(keep, j, -1).max(1).astype(np.float32)         # (x, z) 뒷면 칸
    D = np.maximum(hi - lo, 0.0)

    def sample(v):
        a, sign = W.VIEW_AXIS[v]
        py, px = W.topix((back_sign if v == "back" else sign) * X2, Z2)
        return deps[v][py, px]

    # **높이마다 정규화한다.** 그림 전체 최댓값으로 나누면 어느 높이에도 hull 표면에 닿는
    # 점이 없어서 기둥이 양쪽에서 다 줄고, 그러면 **측면 실루엣이 깎인다** — 측면 판은
    # 깊이 방향 투영이라 깊이를 줄이면 곧바로 못 덮는다 (실측: side 못 덮음 0.00 -> 28.65%).
    # 높이별로 max=1 이면 그 높이의 제일 튀어나온 x 가 hull 표면에 닿고, 기둥이 이어져서
    # x 를 따라 합치면 [lo, hi] 를 그대로 덮는다.
    on = keep.any(1)                                  # (x, z) 그 높이에 물건이 있나
    def norm(h):
        top = np.where(on, h, 0.0).max(0, keepdims=True)
        return np.where(on, h / np.maximum(top, 1e-6), 0.0)

    jf = lo + (1.0 - norm(sample("front"))) * lam * D
    jb = hi - (1.0 - norm(sample("back"))) * lam * D
    if ZSMOOTH > 0:
        jf, jb = zsmooth(jf, jb, lo, hi, on, ZSMOOTH)
    return keep & (j >= jf[:, None, :]) & (j <= jb[:, None, :]), axes


ZSMOOTH = 0.0                                    # 앞·뒷면 깊이를 **높이 방향으로만** 미는 σ (칸). 0 이면 끔
# 시험 중 (2026-09-11). 3D 로 흐리는 `SMOOTH_OUT` 은 실루엣을 먹어서 껐다 — 이건 실루엣을 안 건드린다.


def zsmooth(jf, jb, lo, hi, on, s):
    """**찢김을 편다 — 실루엣은 그대로.** `carve_depth` 의 높이별 정규화가 윗줄·아랫줄을 다른 눈금으로
    깎아 앞면이 가로로 찢어진다 (오라클0.50 에서 위아래 >3칸 튐 28~31%, 정답 6~11%). 그 정규화는 옆
    실루엣을 지키는 장치라 못 끈다. 대신 깎은 결과의 앞·뒷면 깊이(2D)를 z 방향으로만 민다:

        정면 실루엣  기둥을 안 지운다 (민 값이 앞뒤가 뒤집히면 그 기둥은 원래 값)
        hull 밖      앞면 >= lo · 뒷면 <= hi 로 자른다
        측면 실루엣  높이마다 제일 앞·제일 뒤 칸은 원래 값을 지킨다"""
    w = on.astype(np.float32)
    den = np.maximum(ndimage.gaussian_filter1d(w, s, axis=1), 1e-6)
    sm = lambda a: ndimage.gaussian_filter1d(np.where(on, a, 0.0).astype(np.float32), s, axis=1) / den
    f, b = np.maximum(sm(jf), lo), np.minimum(sm(jb), hi)
    bad = f > b - 1                                  # 앞뒤가 뒤집히거나 칸이 안 남으면 원래 값
    f, b = np.where(bad, jf, f), np.where(bad, jb, b)
    zf = np.where(on, jf, np.inf).min(0, keepdims=True)
    zb = np.where(on, jb, -np.inf).max(0, keepdims=True)
    f = np.where(on & (jf <= zf), jf, f)             # 높이마다 제일 앞 — 측면 실루엣의 앞 끝
    b = np.where(on & (jb >= zb), jb, b)             # 높이마다 제일 뒤 — 뒤 끝
    return np.where(on, f, jf), np.where(on, b, jb)


def surfaces(vox):
    """복셀 덩어리의 앞면·뒷면 칸 (x, z). 깊이 축으로 제일 앞·제일 뒤."""
    j = np.arange(N)[None, :, None]
    return (np.where(vox, j, N).min(1).astype(float),
            np.where(vox, j, -1).max(1).astype(float))


def box_score(vox):
    """**단면이 얼마나 상자인가.** 이진 hull 은 앞면 y 가 x 에 안 의존해서 0 이 나온다.

    높이마다, 차 있는 x 열들의 앞면·뒷면 칸이 x 를 따라 얼마나 변하는지(표준편차)를 재고
    복셀 칸 단위로 평균한다. 0 이면 순수 상자, 클수록 형태가 있다."""
    lo, hi = surfaces(vox)
    on = vox.any(1)
    out = []
    for k in range(N):
        c = on[:, k]
        if c.sum() < 8:
            continue
        out.append((lo[c, k].std() + hi[c, k].std()) / 2)
    return float(np.mean(out)) if out else 0.0


def mesh_from(vox, axes):
    """복셀 -> 메시. 경계에 0 을 한 겹 둘러 마칭큐브가 닫히게 한다."""
    p = np.pad(vox.astype(np.float32), 1)
    V, F, _, _ = measure.marching_cubes(p, 0.5)
    ux, uy, uz = axes
    sx, sy, sz = ux[1] - ux[0], uy[1] - uy[0], uz[1] - uz[0]
    V = np.stack([ux[0] + (V[:, 0] - 1) * sx,
                  uy[0] + (V[:, 1] - 1) * sy,
                  uz[0] + (V[:, 2] - 1) * sz], 1)
    return V, F


def sdf_of(vox):
    """복셀 -> 부호거리장 (칸 단위, 안 + · 밖 −). 수준 0 면이 `mesh_from`(불 0.5) 면과 같다 —
    맞닿은 안·밖 칸이 +1 · −1 이라 0 이 정확히 가운데서 난다."""
    return (ndimage.distance_transform_edt(vox) - ndimage.distance_transform_edt(~vox)).astype(np.float32)


def smooth_field(f, keep_sdf, sigma=None):
    """**결과를 매끈하게.** 장을 가우시안(σ 칸)으로 흐리고 hull 장과 min — hull 밖으로 못 부푼다.
    부풀면 원화 실루엣에 없는 걸 지어내는 셈이라 막는다. σ 0 이면 `min(f, hull)` 이라 그대로다.

    왜 넣었나 (2026-09-11): 깎은 판본이 **가로로 찢어진다.** 위아래 이웃 줄끼리 앞면이 3칸 넘게
    튀는 쌍이 오라클0.50 에서 28~31% (정답 6~11%). σ2 면 1~7% 로 준다. 원인은 `carve_depth` 의
    높이별 정규화인데, 그건 옆 실루엣을 지키는 장치라 끄지 못한다 (README 「스무딩 시험」).
    **대조군에도 같은 σ 를 건다** — 안 그러면 스무딩이 올린 IoU 가 깊이맵 실력으로 읽힌다."""
    s = SMOOTH_OUT if sigma is None else sigma
    g = ndimage.gaussian_filter(f, s) if s > 0 else f
    return np.minimum(g, keep_sdf)


def even_control(plain, axes, target_volume, step=0.25, cache=None):
    """**균일 침식 대조군** — hull 을 목표 부피까지 매끈하게 안으로 민 면. 정보를 0 만큼 쓴다.

    한 겹씩 벗기던 예전 규약은 한 겹에 부피가 20% 넘게 빠져 **부피가 안 맞았다** (2026-09-11,
    avatarsample_d 1겹 0.768 — 파이프0.20(0.863)이 0.768 짜리와 대어져 왔다). 칸을 무작위로 벗기면 점박이
    표면이 측정에 안 잡혀 너무 약했고, 겹 사이를 선형 보간하면 IoU 곡선이 볼록이라 과소평가했다.
    그래서 부호거리장의 수준 t 를 부피 곡선(step 간격)에서 찾아 그 면을 쓴다 — 매끈하고 부피가 연속으로
    맞는다. `target_volume` 은 판본 **메시** 부피다 (같은 마칭큐브로 잰 것끼리). -> (메시, t)"""
    c = {} if cache is None else cache               # 판본이 여럿이면 곡선을 케이스당 한 번만 그린다
    if "keep" not in c:
        c["keep"] = sdf_of(plain)
    keep = c["keep"]

    def vol(t):
        V, F = mesh_from_field(keep - t, axes)
        return abs(trimesh.Trimesh(V, F, process=False).volume)
    if "ts" not in c:
        c["ts"], c["vs"] = [0.0], [vol(0.0)]
    ts, vs = c["ts"], c["vs"]
    # 상한은 hull 의 최대 안쪽 거리다 — 12 칸 고정이던 때 cape_Hat 이 12 칸을 깎고도 목표의 1.7 배라 멈췄다 (2026-09-14)
    while vs[-1] > target_volume and ts[-1] < float(keep.max()):
        ts.append(ts[-1] + step)
        vs.append(vol(ts[-1]))
    t = float(np.interp(target_volume, vs[::-1], ts[::-1]))

    def at(t):
        V, F = mesh_from_field(keep - t, axes)
        m = trimesh.Trimesh(V, F, process=True)
        if m.volume < 0:
            m.invert()
        return m, m.volume / max(target_volume, 1e-12) - 1
    m, err = at(t)
    if abs(err) >= 0.02 and vs[-1] <= target_volume:
        # 얇은 물건은 한 step 안에서 챙이 통째로 사라져 곡선이 꺾인다 — 보간이 틀린 그 구간만 이분법으로
        # 좁힌다 (2026-09-14, cape_Hat 오라클 lam1.00 이 hull 의 26% 라 74.8% 어긋났다). 맞던 케이스는 안 탄다
        k = next(i for i, v in enumerate(vs) if v <= target_volume)
        lo, hi = ts[k - 1], ts[k]
        for _ in range(30):
            t = (lo + hi) / 2
            m, err = at(t)
            if abs(err) < 0.01:
                break
            lo, hi = (t, hi) if err > 0 else (lo, t)
    assert abs(err) < 0.02, "대조군 부피가 목표와 %.1f%% 어긋난다 — step 을 줄일 것" % (100 * err)
    return m, t


def depth_control(plain, target_voxels, iters=20):
    """**실루엣을 지키는 대조군** — 모든 기둥을 앞·뒤로 **같은 비율 q** 만큼 판다. 정보를 0 만큼 쓴다.

    깊이 깎기와 같은 방향(y)으로만 깎아 정면 실루엣을 원리적으로 안 건드린다. 사방으로 미는
    `even_control` 은 원화 실루엣을 9.5% 잃었다 (2026-09-11 `대조.py`) — 대조군만 윤곽을 줄여 부피를
    빼는 셈이라 불공평할 수 있어서 만들었다. q 는 `target_voxels`(판본 칸 수)에 맞춰 이분법으로 찾는다.

    **측면 실루엣도 지킨다.** 모든 기둥을 똑같이 깎으면 옆에서 본 앞뒤 폭이 준다. 깊이 깎기는 높이별
    정규화로 제일 튀어나온 기둥이 hull 앞면에 닿아 측면을 지킨다 — 그래서 여기서도 **높이마다 제일 앞
    기둥의 앞면 · 제일 뒤 기둥의 뒷면은 그대로** 둔다. 칸이 하나도 안 남는 얇은 기둥은 가운데 칸을
    남긴다 (정면 실루엣에 구멍이 안 나게). -> (칸 판, q)"""
    n = plain.shape[1]
    j = np.arange(n)[None, :, None]
    lo = np.where(plain, j, n).min(1).astype(np.float32)
    hi = np.where(plain, j, -1).max(1).astype(np.float32)
    D = np.maximum(hi - lo, 0.0)
    on = plain.any(1)
    zi = np.arange(plain.shape[2])
    xf = np.argmin(np.where(on, lo, np.inf), axis=0)       # 높이마다 제일 앞 기둥
    xb = np.argmax(np.where(on, hi, -np.inf), axis=0)      # 높이마다 제일 뒤 기둥
    mid = plain & (j == np.round((lo + hi) / 2)[:, None, :])

    def cut(q):
        jf, jb = lo + q * D, hi - q * D
        jf[xf, zi], jb[xb, zi] = lo[xf, zi], hi[xb, zi]
        return (plain & (j >= jf[:, None, :]) & (j <= jb[:, None, :])) | mid
    a, b = 0.0, 0.5
    for _ in range(iters):
        q = (a + b) / 2
        a, b = (q, b) if cut(q).sum() > target_voxels else (a, q)
    q = (a + b) / 2
    return cut(q), q


def mesh_from_field(f, axes):
    """장의 수준 0 면 -> 메시. 좌표 규약은 `mesh_from` 과 같다."""
    p = np.pad(f, 1, constant_values=-1.0)
    V, F, _, _ = measure.marching_cubes(p, 0.0)
    ux, uy, uz = axes
    sx, sy, sz = ux[1] - ux[0], uy[1] - uy[0], uz[1] - uz[0]
    V = np.stack([ux[0] + (V[:, 0] - 1) * sx,
                  uy[0] + (V[:, 1] - 1) * sy,
                  uz[0] + (V[:, 2] - 1) * sz], 1)
    return V, F


def superellipse(plain, p=2.0):
    """높이마다 hull 단면(축정렬 직사각형들)에 **내접 초타원** — |x/a|^p + |y/b|^p <= 1.

    p=2 는 타원(= 2026-09-11 의 가정), 클수록 상자에 가고 1 이면 마름모다. **부품마다**
    따로 넣는다 (높이마다 연결성분별로). `ellipse_depths` 와 단면 그림이 같은 것을 본다.
    (2026-09-15 `오라클.py` 에서 옮겼다 — 기본값이 되어 제품 경로가 쓴다. 오라클은 여기서 가져간다)"""
    n = plain.shape[0]
    I, Jg = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    E = np.zeros_like(plain)
    for k in range(plain.shape[2]):
        lab, _ = ndimage.label(plain[:, :, k])
        for idx, s in enumerate(ndimage.find_objects(lab), 1):
            a, b = (s[0].stop - s[0].start) / 2, (s[1].stop - s[1].start) / 2
            ic, jc = s[0].start + a - 0.5, s[1].start + b - 0.5
            q = np.abs((I[s] - ic) / a) ** p + np.abs((Jg[s] - jc) / b) ** p
            E[s[0], s[1], k] |= (q <= 1) & (lab[s] == idx)
    return E


def ellipse_depths(plain, axes, back_sign, p=2.0, E=None):
    """hull 만 보고 **오라클을 추정한다** — 높이마다 단면에 초타원을 내접시킨다.

    이진 hull 의 단면은 높이마다 축정렬 직사각형 몇 개다 (x구간 × y구간). 그 안에 내접
    초타원(`superellipse`, p=2 면 타원)을 넣고, 그 앞·뒤 표면으로 `오라클.oracle_depth` 와 **같은
    규약**의 깊이를 만든다. 정답을 안 본다. 대신 **「단면 모양」 가정 하나**를 넣는다.

    `carve_depth` 는 깊이를 **복셀 중심 화소에서만** 읽으므로 그 화소에만 찍는다. 나머지는
    1 (= 안 깎는다) 이라, 자가검사도 복셀 중심에서 읽어야 헛통과가 안 난다."""
    u, _, z = axes
    n = len(u)
    E = superellipse(plain, p) if E is None else E        # E 를 주면 그 단면으로 (조각 묶기 실험 · 09-15)
    j = np.arange(n)[None, :, None]
    jf, jb = np.where(E, j, n).min(1), np.where(E, j, -1).max(1)  # (x, z) 앞면·뒷면 칸
    has = jf < n
    out = {v: np.ones((W.RES, W.RES), np.float32) for v in W.VIEWS}
    if not has.any():
        return out
    ys = np.nonzero(E.any((0, 2)))[0]
    lo, hi = u[ys.min()], u[ys.max()]                    # **물건의 y 범위 하나로** — oracle 과 같다
    span = max(hi - lo, 1e-9)
    hf = np.where(has, (hi - u[np.clip(jf, 0, n - 1)]) / span, 1.0)
    hb = np.where(has, (u[np.clip(jb, 0, n - 1)] - lo) / span, 1.0)
    X2, Z2 = np.meshgrid(u, z, indexing="ij")
    for v, h in (("front", hf), ("back", hb)):
        py, px = W.topix((back_sign if v == "back" else W.VIEW_AXIS[v][1]) * X2, Z2)
        out[v][py, px] = np.clip(h, 0, 1)
    return out


# **기본 깎기 (2026-09-15 에 바꿨다).** 타원 단면 · lam 1.00. 09-12 에 벤치 셋 45장 판정을 지나고도 기본값에 안 들어가
# 사흘 동안 제품이 제자리였다 (메모리 `progress-needs-scoreboard`). 판정 · 점수판은 `실험_20260915/점수판.py`.
# "파이프" 로 두면 옛 기본 — 깊이.py 깊이맵 · lam `LAM`. `LAM` 은 옛 판본들이 「파이프0.20」 이름으로 쓰니 안 바꾼다.
DEPTH = "타원"
DEPTH_LAM = 1.00
# ── 2026-09-21 채택 ──────────────────────────────────────────────────────────
FIELD = True        # **깎기를 0/1 복셀이 아니라 연속 장으로.** 가정(높이마다 내접 타원)은 그대로고
                    # 표현만 바꾼다. 벤치 28 장 · 속 채운 IoU 중앙 0.7413 -> **0.7687** (25 승 3 패 ·
                    # 192 격자에서도 +0.027 · 한 장 빼기 통과 · 거칠기 0.327 -> 0.071).
                    # 근거 `실험_20260921/장타원.py`. False 면 옛 복셀 경로.
SMOOTH_Z = 3.0      # 장을 **높이 방향으로만** 편다 (칸). 울퉁불퉁(높이마다 따로 풀어 생긴 층)을 잡는다.
                    # ⚠ **벤치로 검증 안 했다** — 오메가몬 한 장을 눈으로 보고 골랐다. 값을 산다:
                    # 못덮음 앞 3.59 -> 4.19%(σ2) -> 5.04%(σ4). 0 이면 끈다.
SMOOTH_GUARD = 1.0  # 표면이 어디서도 이만큼(칸) 넘게 안 물러난다 — 칼끝 · 가시를 지킨다
INK = True          # 원화의 **먹선**을 앞 · 뒤에서 표면에 골로 새긴다. ⚠ **벤치로 검증 안 했다**
INK_DEPTH = 0.006   # 홈 깊이 (창 단위) — **지어낸 값**


def _구간(occ):
    d = np.diff(np.concatenate(([0], occ.astype(np.int8), [0])))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def _축값(runs, u):
    """격자 u 마다 (정규화 제곱거리, 반폭). 구간 밖이면 제일 가까운 구간 값(> 1)."""
    px = (W.U1 - W.U0) / W.RES
    X = np.full(len(u), 4.0, np.float32)
    A = np.full(len(u), px, np.float32)
    for c0, c1 in runs:
        x0, x1 = W.U0 + c0 * px, W.U0 + c1 * px
        a, cx = max((x1 - x0) / 2, px / 2), (x0 + x1) / 2
        q = ((u - cx) / a) ** 2
        b = q < X
        X[b], A[b] = q[b], a
    return X, A


def field_ellipse(masks, back_sign=BACK_SIGN, n=None):
    """**연속 장 타원** — `ellipse_depths` + `carve_depth` 와 같은 가정(높이마다 단면 직사각형에
    내접 타원)을 복셀 이진화 없이 쓴다. 구간의 끝은 **1024 마스크**에서 읽는다 (격자보다 4 배 촘촘).
    돌려주는 것은 칸 단위 연속값 (안 +). 2026-09-21 채택 — `실험_20260921/장타원.py`."""
    n = n or N
    u = W.U0 + (np.arange(n) + 0.5) / n * (W.U1 - W.U0)
    z = W.Z0 + (np.arange(n) + 0.5) / n * (W.Z1 - W.Z0)
    rows = np.clip(((W.Z1 - z) / (W.Z1 - W.Z0) * W.RES).astype(int), 0, W.RES - 1)
    F, S = masks["front"], masks["side"]
    B = masks["back"][:, ::-1] if back_sign < 0 else masks["back"]
    cell = (W.U1 - W.U0) / n
    g = np.full((n, n, n), -2.0, np.float32)
    for k, r in enumerate(rows):
        xr, yr = _구간(F[r] & B[r]), _구간(S[r])
        if not xr or not yr:
            continue
        X, A = _축값(xr, u)
        Y, Bh = _축값(yr, u)
        g[:, :, k] = (1.0 - X[:, None] - Y[None, :]) * np.minimum(A[:, None], Bh[None, :]) / 2 / cell
    return g, (u, u, z)


def field_hull(masks, back_sign=BACK_SIGN, n=None):
    """이진 hull 의 연속 장 — 판마다 2D 부호거리장을 만들어 최솟값(교집합). 상한 노릇을 한다."""
    n = n or N
    u = W.U0 + (np.arange(n) + 0.5) / n * (W.U1 - W.U0)
    z = W.Z0 + (np.arange(n) + 0.5) / n * (W.Z1 - W.Z0)
    cell = (W.U1 - W.U0) / n

    def d2(mask):
        a = ndimage.distance_transform_edt(mask) - 0.5
        b = ndimage.distance_transform_edt(~mask) - 0.5
        return (np.where(mask, a, -b) * ((W.U1 - W.U0) / W.RES)).astype(np.float32)

    def 표본(S2, uu, zz):
        col = (uu - W.U0) / (W.U1 - W.U0) * W.RES - 0.5
        row = (W.Z1 - zz) / (W.Z1 - W.Z0) * W.RES - 0.5
        C, R = np.meshgrid(col, row, indexing="ij")
        return ndimage.map_coordinates(S2, [R, C], order=1, mode="nearest").astype(np.float32)

    Sf = 표본(d2(masks["front"]), u, z)
    Ss = 표본(d2(masks["side"]), u, z)
    Sb = 표본(d2(masks["back"]), back_sign * u, z)
    f = np.minimum(np.minimum(Sf[:, None, :], Ss[None, :, :]), Sb[:, None, :])
    return f / cell, (u, u, z)


def field_default(masks, back_sign=BACK_SIGN, n=None):
    """제품 기본 — 연속 장 타원 + (켜져 있으면) 높이 방향 스무딩. hull 밖으로는 못 나간다."""
    g, axes = field_ellipse(masks, back_sign, n)
    if SMOOTH_Z > 0:
        f, _ = field_hull(masks, back_sign, n)
        g = np.minimum(np.maximum(ndimage.gaussian_filter1d(g, SMOOTH_Z, axis=2), g - SMOOTH_GUARD), f)
    return g, axes


def ink_map(png, 어둠=120, 선최대굵기=5, 칠최소=60, 닫기=2, 조각최소=20, 테두리=2):
    """원화 -> **먹선** bool. 어두운 화소 중 가는 것 + **굵은 칠의 테두리**(칠을 통째로 빼면 거기
    닿는 선이 잘린다 — 조각 434 개로 부서졌다) + 닫기로 틈 잇기 + 점 부스러기 버리기.
    맨 바깥 윤곽은 뺀다(3D 에서 곧 모양의 가장자리라 파면 윤곽이 패인다).
    2026-09-21 · `실험_20260921/먹선.py`. ⚠ 값들은 눈으로 골랐다."""
    import cv2
    im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_UNCHANGED)
    a = im[:, :, 3] > 127 if im.ndim == 3 and im.shape[2] == 4 else np.ones(im.shape[:2], bool)
    g = cv2.cvtColor(im[:, :, :3] if im.ndim == 3 else im, cv2.COLOR_BGR2GRAY)
    C = np.ones((3, 3), bool)
    dark = (g < 어둠) & a
    k = 선최대굵기 // 2 + 1
    칠 = ndimage.binary_dilation(ndimage.binary_opening(dark, iterations=k), iterations=k) & dark
    lab, _ = ndimage.label(칠, C)
    sz = np.bincount(lab.ravel())
    큰칠 = np.isin(lab, np.where(sz >= 칠최소)[0][1:]) if sz.size > 1 else np.zeros_like(칠)
    테 = 큰칠 & ~ndimage.binary_erosion(큰칠, iterations=2)
    sel = ndimage.binary_closing((dark & ~칠) | 테, C, iterations=닫기)
    sel &= ndimage.binary_erosion(a, iterations=테두리)
    lab2, _ = ndimage.label(sel, C)
    s2 = np.bincount(lab2.ravel())
    return np.isin(lab2, np.where(s2 >= 조각최소)[0][1:]) if s2.size > 1 else sel


def carve_ink(mesh, raw, p, back_sign, case, depth=None):
    """먹선을 앞 · 뒤에서 표면에 골로 새긴다 — **시선 방향 안쪽으로만** 밀어 실루엣이 안 바뀐다."""
    depth = INK_DEPTH if depth is None else depth
    src, base = CASES[case]["src"], art_dir(case)
    m = mesh.subdivide()
    V = np.asarray(m.vertices, float).copy()
    Nn = np.asarray(m.vertex_normals)
    for v, sign, 방향 in (("front", +1, -1), ("back", back_sign, +1)):
        선 = ink_map(os.path.join(base, src[v]))
        _, w2 = to_win(declutter(raw[v]), 선.astype(np.float32))
        창선 = _warp_one(w2, v, p)
        부드 = np.clip(ndimage.gaussian_filter(창선, 1.0) * 1.6, 0, 1)
        본다 = Nn[:, 1] * 방향 > 0.35
        py, px = W.topix(sign * V[:, 0], V[:, 2])
        V[:, 1] -= 방향 * depth * np.where(본다, 부드[py, px], 0.0)
    return trimesh.Trimesh(V, np.asarray(m.faces), process=False)


def carve_default(masks, deps, back_sign=BACK_SIGN):
    """제품 · 벤치가 같이 쓰는 기본 깎기. 타원이면 `deps` 를 안 쓴다 (hull 에서 만든다)."""
    if DEPTH == "파이프":
        return carve_depth(masks, deps, lam=LAM, back_sign=back_sign)
    plain, axes = carve(masks, back_sign)
    return carve_depth(masks, ellipse_depths(plain, axes, back_sign), lam=DEPTH_LAM, back_sign=back_sign)


def main(case=None, out_name="hull.glb"):
    os.makedirs(OUT, exist_ok=True)
    case = case or CASE
    src, base = CASES[case]["src"], art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks, deps = {}, {}
    for v, m in raw.items():
        d = declutter(m)
        bb = lambda a: (np.ptp(np.where(a.any(0))[0]) + 1, np.ptp(np.where(a.any(1))[0]) + 1)
        print("  %-6s bbox %s -> 지시선 뺀 뒤 %s" % (v, bb(m), bb(d)))
        dep = load_depth(v, d, case=case) if DEPTH == "파이프" else np.ones(d.shape, np.float32)   # 타원은 깊이맵이 필요 없다
        masks[v], deps[v] = to_win(d, dep)

    bs = CASES[case]["back_sign"] or pick_back_sign(masks)
    if CASES[case]["back_sign"] is None:
        print("  후면 좌우 규약을 재서 골랐다: %+d" % bs)
    fmt = lambda d: " · ".join("%s %.2f%%" % (v, 100 * d[v]) for v in W.VIEWS)
    print("")
    print("  정렬 전  %s" % fmt(miss(masks, bs)))
    p = align(masks, back_sign=bs)
    masks = _warp(masks, p)
    deps = {v: _warp_one(a, v, p) for v, a in deps.items()}      # 깊이맵도 **같은 값**으로
    print("  side(dy %+.0f s %.4f) · back(dx %+.0f dy %+.0f s %.4f)  <- 잰 값. 판이 바뀌면 다시 나온다" % tuple(p))
    print("  정렬 후  %s" % fmt(miss(masks, bs)))

    if FIELD:
        # 2026-09-21 채택 — 연속 장. 복셀 이진화를 안 거친다 (`장타원.py` · 벤치 28 장 +0.028)
        g, axes = field_default(masks, back_sign=bs)
        print("\n  기본 깎기 연속 장 타원 · 높이 스무딩 σ %.1f 칸 (가드 %.1f)" % (SMOOTH_Z, SMOOTH_GUARD))
        V, F = mesh_from_field(g, axes)
        mesh = trimesh.Trimesh(V, F, process=False)   # process=True 는 넓이 0 인 면을 만들어 메시를 연다
    else:
        plain, _ = carve(masks, back_sign=bs)
        vox, axes = carve_default(masks, deps, back_sign=bs)
        print("\n  기본 깎기 %s lam %.2f" % (DEPTH, DEPTH_LAM if DEPTH != "파이프" else LAM))
        print("  복셀 %d/%d 남음 (%.1f%%)" % (vox.sum(), vox.size, 100 * vox.sum() / vox.size))
        print("  단면 형태값  이진 hull %.2f -> 깊이 깎기 %.2f 칸  (0 이면 순수 상자)"
              % (box_score(plain), box_score(vox)))
        assert vox.any(1).sum() >= plain.any(1).sum() * 0.98, "깊이 깎기가 실루엣을 갉았다 — DEPTH_LAM(타원) 이나 LAM(파이프)을 낮출 것"
        if SMOOTH_OUT > 0:
            V, F = mesh_from_field(smooth_field(sdf_of(vox), sdf_of(plain)), axes)
            print("  스무딩 σ %.1f 칸 (hull 밖으로 못 부풂)" % SMOOTH_OUT)
        else:
            V, F = mesh_from(vox, axes)
        mesh = trimesh.Trimesh(V, F, process=True)
    # 출력 위생 둘. 눈으로는 안 보이고 슬라이서가 걸린다
    #   ① 부유 파편 — 몇 복셀짜리 조각이 공중에 뜬다. 제일 큰 덩어리만 남긴다
    #   ② 뒤집힌 법선 — 부피가 음수로 나온다. 안팎이 뒤집힌 채로는 캐스팅 못 한다
    parts = mesh.split(only_watertight=False)
    if len(parts) > 1:
        big = max(parts, key=lambda q: abs(q.volume))
        print("  부유 파편 %d 개 버림 (제일 큰 덩어리만)" % (len(parts) - 1))
        mesh = big
    if mesh.volume < 0:
        mesh.invert()
    if INK:
        mesh = carve_ink(mesh, raw, p, bs, case)
        print("  먹선 새김 (깊이 %.3f · 시선 방향 안쪽으로만) · 면 %d" % (INK_DEPTH, len(mesh.faces)))
    mesh.export(os.path.join(OUT, out_name))
    print("  메시 정점 %d · 면 %d · 부피 %.4f · 닫힘 %s -> out/%s"
          % (len(mesh.vertices), len(mesh.faces), mesh.volume, mesh.is_watertight, out_name))

    # 되받아 재기 — hull 은 제 3판과 (거의) 일치해야 한다. 안 그러면 앉히기가 틀린 것
    Vh, Fh = np.asarray(mesh.vertices), np.asarray(mesh.faces)
    print()
    for v in W.VIEWS:
        s = W.silhouette(Vh, Fh, v, bs if v == "back" else None)
        a, q = masks[v].astype(bool), np.asarray(s).astype(bool)
        m1 = (a & ~q).sum() / max(a.sum(), 1)
        print("  %-6s 원화 대 hull  IoU %.3f  못 덮은 %.2f%%" % (v, W.iou(masks[v], s), 100 * m1))
        # hull 은 형상의 **상한**이다. 되받아 재서 원화를 못 덮으면 판들이 싸운 것이다.
        #
        # 이 숫자만 보면 원인을 못 고른다. `겹침.py` 로 어디인지 봐야 한다.
        # 2026-09-08 에 빨강이 경계를 따라 고르지 않고 **발에 뭉쳐** 있었다 (42% 가 z<0.26).
        # `align` 로 절반쯤 걷어냈다. 남은 것이 정렬로 못 없애는 양 — 작화 모순이다.
        #
        # ponytail: 문턱은 정렬 뒤 잰 값 위에 얹었다. 판이 나아지면 같이 내린다.
        assert m1 < THRESH, "%s: hull 이 원화를 %.1f%% 못 덮는다 — 겹침.py 로 어디인지 볼 것" % (v, 100 * m1)
    return masks, mesh


# ------------------------------------------------------------------ 자체검사

def _fig():
    """자체검사용 인물 비슷한 마스크. **좌우 비대칭**이라 가로 이동이 결정된다."""
    m = np.zeros((W.RES, W.RES), bool)
    m[300:900, 460:560] = True                   # 몸통
    m[200:300, 480:545] = True                   # 머리
    m[380:520, 560:700] = True                   # 한쪽 팔만
    m[860:940, 425:500] = True                   # 발
    return m


def demo():
    """정답을 아는 경우로 `align` 을 되받는다. 같은 판을 알려진 값만큼 어긋뜨리고 되찾게 한다."""
    f = _fig()
    for dx, dy, s in ((12., -9., 1.03), (-20., 14., 0.96)):
        w = W.warp_art(f, -dx / s, -dy / s, 1 / s)          # 이 워프의 역 (규약: s*(x-c)+c+dx)
        m = {"front": f, "side": w, "back": w}
        assert max(miss(m).values()) > 0.02, "어긋뜨렸는데 hull 이 멀쩡하다 — 목적함수가 못 본다"
        p = align(m)
        assert abs(p[2] - dx) < 2 and abs(p[3] - dy) < 2 and abs(p[4] - s) < .01,             "back 을 못 되찾았다: %s 넣었는데 %s 나왔다" % ((dx, dy, s), p[2:])
        assert abs(p[0] - dy) < 2 and abs(p[1] - s) < .01,             "side 의 dy·s 를 못 되찾았다: %s" % (p[:2],)
        assert max(miss(_warp(m, p)).values()) < 0.01, "되찾았다는데 아직 덜 덮는다"
    # side 의 가로는 못 본다 — 이게 미지수가 6 이 아니라 5 인 이유다
    a = {"front": f, "side": f, "back": f}
    b = dict(a, side=W.warp_art(f, 30, 0, 1.0))
    assert miss(a) == miss(b), "side 를 가로로 밀었는데 실루엣이 바뀐다 — 5개 가정이 틀렸다"
    print("자체검사 통과 — 어긋뜨린 값 되찾음, side 가로는 실루엣이 못 본다(미지수 5)")


register_sheets()                                # import 시점에 판 케이스를 붙인다


if __name__ == "__main__":
    # 케이스를 `시트.py` 가 자동 등록하는데(register_sheets) 여기서 고를 길이 없었다.
    #   python hull.py 무진      -> out/시트/무진 의 세 판으로 세운다
    if "check" in sys.argv:
        demo()
    else:
        args = [a for a in sys.argv[1:] if not a.startswith("-")]
        # 케이스를 주면 이름을 달아 쓴다 — `정답.py` 가 out/hull_<케이스>.glb 를 찾는다.
        if args:
            main(args[0], out_name=f"hull_{args[0]}.glb")
        else:
            main()
