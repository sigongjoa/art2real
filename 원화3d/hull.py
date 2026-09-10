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
    d = np.load(os.path.join(OUT, "깊이", case or CASE, v, "depth.npy")).astype(np.float32)
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
    return keep & (j >= jf[:, None, :]) & (j <= jb[:, None, :]), axes


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
        masks[v], deps[v] = to_win(d, load_depth(v, d, case=case))

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

    plain, _ = carve(masks, back_sign=bs)
    vox, axes = carve_depth(masks, deps, back_sign=bs)
    print("\n  복셀 %d/%d 남음 (%.1f%%)" % (vox.sum(), vox.size, 100 * vox.sum() / vox.size))
    print("  단면 형태값  이진 hull %.2f -> 깊이 깎기 %.2f 칸  (0 이면 순수 상자)"
          % (box_score(plain), box_score(vox)))
    assert vox.any(1).sum() >= plain.any(1).sum() * 0.98, "깊이 깎기가 실루엣을 갉았다 — lam 을 낮출 것"
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
