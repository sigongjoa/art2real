# -*- coding: utf-8 -*-
"""**처음으로 형태를 채점한다.** hull 을 원화가 아니라 **진짜 메시**와 대본다.

    python 정답.py check           채점기 자체검사 (답을 아는 상자 두 개)
    python 정답.py [케이스]        ->  out/정답_<케이스>.png + 표

지금까지의 검증은 전부 실루엣끼리였다. hull 을 되던져 원화와 겹치는 것뿐이라
「형태가 맞나」가 아니라 「그림자가 맞나」를 잰다. trail7 이 그걸 적어뒀다 —
「판정기에 두께 항이 필요하다. 지금은 이 실패가 숫자로 안 잡힌다.」

`시트.py` 로 3D 모델에서 판을 뽑으면 원본 메시가 정답으로 남는다. 그걸 쓴다.

## 재는 것

    3D IoU        형태가 맞나. **이게 두께 항이다**
    부피비         hull 은 상한이라 1.0 을 넘어야 정상. 밑돌면 과하게 깎은 것
    시점별 실루엣   그림자만 맞고 형태가 틀린 경우를 가려낸다

## 주의

정답 메시(VRM)는 **watertight 가 아니다** — 속눈썹·옷 같은 열린 껍질이 있다.
`voxelized().fill()` 이 근사라 3D IoU 에 몇 %의 바닥 오차가 깔린다. 절대값보다
**케이스 사이 비교와 변경 전후 비교**로 읽는 게 맞다.
"""
import os
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull as H
import win as W
from 계획 import _font

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
PITCH = (W.U1 - W.U0) / 128.0                    # 정답 격자. 128 이면 1.2/128 = 0.0094


def grid(mesh, pitch=PITCH):
    """메시 -> (채운 복셀 bool 배열, 원점 인덱스). 격자는 pitch 로 세계에 고정된다.

    **`trimesh.fill()` 을 안 쓴다.** 그건 광선 교차 홀짝이라 닫힌 메시를 전제하는데,
    게임/VRM 메시는 거의 다 열려 있다(속눈썹·옷자락). 새면 정답 부피가 부풀고 그러면
    `부피비 < 1` 이 나오는데, visual hull 은 상한이라 **원리적으로 불가능한 값**이다.
    실측으로 48장 중 9장이 그랬고 전부 non-watertight 였다.

    대신 **바깥에서 홍수채우기**를 한다 — 표면 껍질을 굽고, 경계 밖에서 6방향으로 번지고,
    안 닿은 곳이 속이다. 구멍이 복셀 한 칸보다 작으면 안 샌다."""
    from scipy import ndimage
    v = mesh.voxelized(pitch=pitch)
    shell = np.asarray(v.matrix, bool)
    pad = np.pad(shell, 1)
    outside = ndimage.binary_fill_holes(~pad) if False else None
    free = ~pad
    lab, _ = ndimage.label(free)                 # 6방향 이웃(기본 구조요소)
    out_lab = lab[0, 0, 0]
    solid = ~((lab == out_lab) | pad) | pad      # 바깥에 안 닿은 빈 곳 + 껍질
    a = solid[1:-1, 1:-1, 1:-1]
    o = np.rint(np.asarray(v.transform)[:3, 3] / pitch).astype(int)
    return a, o


# 불변식 문턱. **잰 값에서 왔다** — 35장에서 이진 hull 의 못덮음 중앙값이 0.008 이다.
# 이산화(복셀 격자 + 마칭큐브)로 몇 % 는 어쩔 수 없지만 그 이상이면 뭔가 틀린 것이다.
MISS_MAX, VOL_MIN = 0.06, 0.95


def invariant(A, B):
    """**visual hull 은 정답을 포함한다.** 이진 hull 이 이걸 어기면 잰 게 틀린 것이다.

    어기는 경우로 실제로 본 것 둘:
      - 정답 메시가 non-watertight 라 채우기가 새서 정답 부피가 부푼다 (부피비 < 1)
      - 정답에 멀리 떨어진 떠돌이 정점이 있어 `normalize` 가 물건을 쪼그라뜨린다.
        그러면 렌더된 실루엣은 창을 다 못 채우고 `to_win` 이 그걸 다시 늘려서
        **hull 과 정답의 배율이 어긋난다** (부피비 8.84 인데 못덮음 0.398 이 나온다)

    깊이 깎기에는 안 건다 — 그건 일부러 안쪽을 깎으니 못 덮는 게 정상이다."""
    miss = (A & ~B).sum() / max(A.sum(), 1)
    vol = B.sum() / max(A.sum(), 1)
    why = []
    if miss > MISS_MAX:
        why.append("이진 hull 이 정답을 %.1f%% 못 덮는다 (문턱 %.0f%%)" % (100 * miss, 100 * MISS_MAX))
    if vol < VOL_MIN:
        why.append("이진 부피비 %.2f — hull 은 상한이라 1 미만이 나올 수 없다" % vol)
    return why


def common(a, oa, b, ob):
    """두 격자를 같은 인덱스 공간에 올린다. 세계 좌표가 같으니 정수 오프셋뿐이다."""
    lo = np.minimum(oa, ob)
    hi = np.maximum(oa + a.shape, ob + b.shape)
    A = np.zeros(hi - lo, bool); B = np.zeros(hi - lo, bool)
    sa = tuple(slice(oa[i] - lo[i], oa[i] - lo[i] + a.shape[i]) for i in range(3))
    sb = tuple(slice(ob[i] - lo[i], ob[i] - lo[i] + b.shape[i]) for i in range(3))
    A[sa] = a; B[sb] = b
    return A, B


def score(case="소체"):
    t = trimesh.load(os.path.join(OUT, "시트", case, "truth.glb"), force="mesh")
    h = trimesh.load(os.path.join(OUT, "hull_%s.glb" % case), force="mesh")
    T, ot = grid(t)
    Hh, oh = grid(h)
    A, B = common(T, ot, Hh, oh)                 # A = 정답, B = hull
    inter, union = (A & B).sum(), (A | B).sum()
    out = {"3D IoU": inter / max(union, 1),
           "부피비": B.sum() / max(A.sum(), 1),
           "정답을 못 덮음": (A & ~B).sum() / max(A.sum(), 1),
           "정답 밖으로 나감": (B & ~A).sum() / max(B.sum(), 1)}
    sil = {}
    for ax, nm in ((1, "front"), (0, "side"), (1, "back")):
        pa, pb = A.any(ax), B.any(ax)
        sil[nm] = (pa & pb).sum() / max((pa | pb).sum(), 1)
    return A, B, out, sil


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else "소체"
    A, B, out, sil = score(case)
    print("  케이스 %s — hull 대 **진짜 메시**" % case)
    for k, v in out.items():
        print("    %-16s %.3f" % (k, v))
    print("    시점 실루엣      " + " · ".join("%s %.3f" % (k, v) for k, v in sil.items()))
    print("    (정답 복셀 %d · hull 복셀 %d)" % (A.sum(), B.sum()))

    # 단면 몇 장을 겹쳐 본다 — 숫자가 어디서 왔는지
    S, ks = 240, [int(A.shape[2] * f) for f in (0.82, 0.62, 0.42, 0.18)]
    sheet = Image.new("RGB", (len(ks) * (S + 14) + 14, S + 96), "white")
    d = ImageDraw.Draw(sheet)
    d.text((14, 12), "%s — 정답(회색) 위에 hull(빨강 테두리). 3D IoU %.3f"
           % (case, out["3D IoU"]), font=_font(19), fill=(20, 20, 20))
    d.text((14, 38), "파랑 = hull 이 정답 밖으로 나간 자리 · 초록 = 정답인데 hull 이 못 덮음",
           font=_font(12), fill=(120, 120, 120))
    for i, k in enumerate(ks):
        a, b = A[:, :, k], B[:, :, k]
        g = np.full(a.shape + (3,), 255, np.uint8)
        g[a & b] = (150, 150, 150); g[~a & b] = (60, 110, 220); g[a & ~b] = (40, 160, 70)
        im = Image.fromarray(np.rot90(g)).resize((S, S), Image.NEAREST)
        sheet.paste(im, (14 + i * (S + 14), 62))
        d.rectangle([14 + i * (S + 14), 62, 13 + i * (S + 14) + S, 61 + S], outline=(210, 210, 210))
    sheet.save(os.path.join(OUT, "정답_%s.png" % case))
    print("  -> out/정답_%s.png" % case)


def demo():
    """**채점기 자체를 시험한다.** 상자 안에 든 작은 상자는 답을 아는 경우다."""
    big = trimesh.creation.box(extents=[0.4, 0.3, 1.0])
    small = trimesh.creation.box(extents=[0.2, 0.15, 0.5])
    A, oa = grid(small)                          # 정답 = 작은 상자
    B, ob = grid(big)                            # hull = 큰 상자 (정답을 품는다)
    A, B = common(A, oa, B, ob)
    miss = (A & ~B).sum() / A.sum()
    vol = B.sum() / A.sum()
    assert miss < 0.01, "품고 있는데 못 덮는다고 나온다 (%.3f) — grid 나 common 이 틀렸다" % miss
    assert 6.0 < vol < 10.0, "부피비가 %.2f — 기대는 8배쯤이다 (0.4·0.3·1.0 / 0.2·0.15·0.5)" % vol
    assert not invariant(A, B), "품는 경우인데 불변식이 걸린다"
    # 반대로, 어긋난 경우는 반드시 걸려야 한다
    A2, B2 = common(*grid(small), *grid(trimesh.creation.box(extents=[0.1, 0.1, 0.1])))
    assert invariant(A2, B2), "정답보다 작은 hull 인데 불변식이 안 걸린다"
    print("자체검사 통과 — 못덮음 %.3f · 부피비 %.2f · 불변식이 양방향으로 운다" % (miss, vol))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        demo()
    else:
        main()
