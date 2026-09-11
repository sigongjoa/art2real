# -*- coding: utf-8 -*-
"""**공통 좌표창.** 배율은 케이스당 한 번이고, 시점마다 다시 잡지 않는다.

    python win.py          # 자체검사

창은 새로 정하지 않는다. `trail6/mask2d.py` · `trail4/mesh_win.py` 규약을 그대로 쓴다:

    1024² · u ∈ [-0.6, 0.6] · z ∈ [-0.1, 1.1] · 직교
    z=0 접지 · x=0 중심선 · y=0 허리 · **앞이 -y**
    front(az0) 화면가로 = +x   side(az90) = +y   back(az180) = -x

**창의 가로가 1.2 다 — 가로/키 비가 1.2 를 넘는 물건은 잘린다.** T포즈 사람은 들어가지만
(실측 0.83~0.87) 팔을 넓게 벌린 괴물·메카는 안 들어간다 (2.15 · 1.82 · 1.70).
잘리면 hull 이 정답을 40~64% 못 덮는데, 이건 `정답.invariant` 가 잡는다.
넓히려면 `trail6/mask2d.py` 를 건드려야 하고 그러면 이전 측정값과 비교가 끊긴다 —
`ponytail: 넓은 물건이 사업에 들어오면 그때 창을 넓히고 기준선을 다시 잡는다.`

## 왜 이 파일이 있나

이전 판정기는 시점마다 실루엣 bbox 로 배율을 다시 잡았다. 그러면 **측면의 폭이 곧 깊이**
라는 정보가 정규화에서 지워진다 — 판때기도 측면에서 제 bbox 로 늘어나 굵기를 되찾는다.
「크기부터 다르다」를 못 보게 만든 게 정확히 그 재정규화다.

높이로 **한 번만** 재고, 세 시점이 그 배율을 공유한다. 그러면 측면 폭은 잰 값이 된다.

## 삼각형은 하나씩 칠한다

`cv2.fillPoly` 에 여러 개를 한 번에 넘기면 합집합이 아니라 **짝수-홀수**다 — 앞면과
뒷면이 서로를 지운다 (판때기 12면: 한꺼번에 5,533 화소 / 하나씩 744,309).
91.8만 면에 1.0초라 값도 싸다.
"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "트레일", "trail6_handbuilt"))
import mask2d                                     # noqa: E402  좌표 변환은 여기 하나뿐이다

RES, U0, U1, Z0, Z1 = mask2d.RES, mask2d.U0, mask2d.U1, mask2d.Z0, mask2d.Z1
topix = mask2d.topix                              # 좌표 변환은 저장소에 이것 하나뿐이다
VIEWS = ("front", "side", "back")

# 시점 -> (창의 u 로 쓸 월드축, 부호). CONTRACT: 앞이 -y
VIEW_AXIS = {"front": (0, +1), "side": (1, +1), "back": (0, -1)}


def to_world(V, axes="xzy"):
    """메시 좌표를 월드(x 가로, y 깊이, z 위)로 돌린다.

    `axes` 는 **만든 도구의 성질**이지 물건의 성질이 아니다 — 짐작하지 않고 케이스에 적는다.
        xzy : 블렌더/OpenSCAD 처럼 z 가 위 (trail6 손모델)
        xyz : glTF 규약, y 가 위 (PartCrafter · TripoSG · OmniPart GLB)
    문자열은 (가로, 위, 깊이) 로 읽는다 — "xyz" 면 가로=x, 위=y, 깊이=z."""
    h, u, d = (("xyz".index(c)) for c in axes)
    return np.stack([V[:, h], V[:, d], V[:, u]], 1)      # -> (x가로, y깊이, z위)


def normalize(W):
    """월드 좌표를 창에 앉힌다. **높이로 한 번** 재고 x·y 를 중앙에, z 최저를 0 에.

    trail4 `mesh_win.py` 와 같은 규약이다 (s = 1/(hi.z-lo.z), 그 뒤 접지·중앙정렬)."""
    lo, hi = W.min(0), W.max(0)
    s = 1.0 / max(hi[2] - lo[2], 1e-9)
    W = W * s
    lo, hi = W.min(0), W.max(0)
    return W - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])


def silhouette(W, F, view, sign=None):
    """창 안의 직교 실루엣. 배율은 이미 `normalize` 에서 정해졌다 — 여기서 다시 안 잡는다.

    `sign` 은 후면의 좌우 규약을 **케이스별로** 덮어쓸 때 쓴다. 렌더는 az180 에서 화면 x = -x
    지만 그린 시트는 그렇지 않을 수 있다 — 깎을 때와 잴 때가 다른 규약을 쓰면 안 되니
    한 값을 양쪽에 넘긴다."""
    a, s0 = VIEW_AXIS[view]
    sign = s0 if sign is None else sign
    py, px = mask2d.topix(sign * W[:, a], W[:, 2])
    P = np.stack([px, py], 1).astype(np.int32)
    g = np.zeros((RES, RES), np.uint8)
    for tri in P[np.asarray(F)]:
        # ponytail: 파이썬 반복문. 면이 1,000만을 넘으면 바리센트릭 벡터화로 간다
        cv2.fillConvexPoly(g, tri, 1)
    return g.astype(bool)


def warp_art(m, dx, dy, s):
    """원화 마스크를 창에 맞춘다. **trail4 `fit_search.py` 39번 규약 그대로**:

        표본좌표 = s*(x - c) + c + dx

    `cv2.warpAffine` 은 순방향 매핑이라 이것과 반대다. 한 번 반대로 짰다가 기존 IoU 0.803 이
    0.539 로 나온 적이 있다 — 규약이 다르면 비교 자체가 안 된다."""
    c, ax = RES / 2, np.arange(RES)
    sx = np.clip(np.rint(s * (ax - c) + c + dx), 0, RES - 1).astype(int)
    sy = np.clip(np.rint(s * (ax - c) + c + dy), 0, RES - 1).astype(int)
    return m[np.ix_(sy, sx)]


def art_mask(png):
    """원화 → 마스크. **알파가 있으면 알파가 곧 실루엣이다** (> 127). 없으면 색으로 가른다 (< 250).

    색으로 가르면 흰 부분이 배경으로 빠진다 — `시트.py` 판의 흰 가슴판·셔츠가 그래서 hull 에 터널을
    냈다 (2026-09-11, 29장 중 9장 > 1%). 그래서 `시트.py` 가 알파를 같이 적는다. 오메가몬 원화도 알파가
    0/255 로 깨끗하다. 예전엔 알파를 흰 바탕에 얹어 색으로 읽었다 — `IMREAD_COLOR` 로 열면 투명한 데가
    검게 들어와 전경이 99% 로 잡히는 걸 막으려던 것인데, 알파를 직접 쓰면 그 문제도 없다."""
    im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_UNCHANGED)
    if im.ndim == 3 and im.shape[2] == 4:
        return im[:, :, 3] > 127
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    return (im[:, :, :3] < 250).any(2)


def iou(a, b):
    return float((a & b).sum()) / max(int((a | b).sum()), 1)


# ------------------------------------------------------------------ 자체검사

def _box(sx, sy, sz):
    """축정렬 상자 하나. (정점, 면)"""
    s = np.array([sx, sy, sz], float) / 2
    V = np.array([[i, j, k] for i in (-1, 1) for j in (-1, 1) for k in (-1, 1)], float) * s
    F = np.array([[0, 1, 3], [0, 3, 2], [4, 7, 5], [4, 6, 7], [0, 4, 5], [0, 5, 1],
                  [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])
    return V, F


def demo():
    # 1) 삼각형을 한꺼번에 칠하면 XOR 이 된다 — 하나씩 칠하는 게 이 파일의 전제
    V, F = _box(1.0, 0.02, 1.4)
    P = np.stack(mask2d.topix(V[:, 0], V[:, 2])[::-1], 1).astype(np.int32)
    xor = np.zeros((RES, RES), np.uint8); cv2.fillPoly(xor, P[F], 1)
    one = np.zeros((RES, RES), np.uint8)
    for t in P[F]:
        cv2.fillConvexPoly(one, t, 1)
    assert one.sum() > 20 * max(xor.sum(), 1), "한꺼번에 칠하면 앞뒤가 서로를 지운다 (%d vs %d)" % (xor.sum(), one.sum())

    # 2) **배율은 시점이 공유한다.** 판때기는 측면에서 얇아야 한다 (재정규화되면 안 된다)
    #    상자는 x 1.0(가로) · y 0.02(깊이) · z 1.4(위) 라 축 문자열은 "xzy" 다
    W = normalize(to_world(V, "xzy"))
    f = silhouette(W, F, "front")
    s = silhouette(W, F, "side")
    assert f.sum() > 30 * s.sum(), "측면이 정면만큼 넓다 = 시점마다 배율을 다시 잡은 것 (%d vs %d)" % (f.sum(), s.sum())

    # 3) 높이 정규화는 크기에 안 휘둘린다 — 10배 키운 같은 물건은 같은 실루엣
    V2, F2 = _box(10.0, 0.2, 14.0)
    assert iou(f, silhouette(normalize(to_world(V2, "xzy")), F2, "front")) > 0.99, "높이 정규화가 배율에 흔들린다"

    # 4) 접지와 중앙정렬 — z 최저 0, x 중앙 0
    assert abs(W[:, 2].min()) < 1e-9 and abs(W[:, 0].mean()) < 1e-9, "접지·중앙정렬이 안 맞는다"

    # 5) 축 규약 — 같은 물건을 y-up 으로 주면 "xyz" 가 "xzy" 와 같은 그림을 내야 한다
    Vy = V[:, [0, 2, 1]]                        # y 와 z 를 맞바꾼 같은 물건 = y 가 위
    assert iou(f, silhouette(normalize(to_world(Vy, "xyz")), F, "front")) > 0.99, "축 규약이 안 맞는다"

    # 6) warp_art 규약 — 배율 1, 이동 0 이면 원본 그대로
    m = np.zeros((RES, RES), bool); m[300:700, 400:600] = True
    assert (warp_art(m, 0, 0, 1.0) == m).all(), "항등 워프가 원본을 안 낸다"

    print("자체검사 통과 — 정면 %d 화소 / 측면 %d 화소 (배율 공유)" % (f.sum(), s.sum()))


if __name__ == "__main__":
    demo()
