# -*- coding: utf-8 -*-
"""**판이 몇 장 있어야 하나.** 사업이 고객에게 뭘 달라고 할지가 이 값에서 나온다.

    python 판수.py

`hull.py` 는 직교 3판을 전제한다. 그런데 사업 문장은 「2D 원화**밖에** 없는 IP 소유자」다.
개인 IP 가 턴어라운드 3판을 갖고 있을 확률은 낮으니, **몇 장까지 줄일 수 있나**가
제품 사양을 정한다.

3판으로 깎은 것을 기준(1.000)으로 놓고, 판을 빼고 깎은 것과 **3D IoU** 로 비교한다.
측면이 없을 때는 가정 하나만 쓴다 — 높이마다 깊이 = k x 그 높이의 정면 폭. 생성은 안 쓴다.

## 잰 값 (2026-09-09) — **케이스 하나뿐이다**

    케이스     깊이/폭 중앙(사분위)   정면+측면   정면+후면   정면만
    오메가몬     0.21 (0.18~0.35)        0.959      0.567     0.548

**후면은 빼도 되고 측면은 못 뺀다** — 로 읽히지만, 한 케이스라 아직 결론이 아니다.

처음엔 견갑을 두 번째 케이스로 넣었다가 뺐다. `pauldron_front/side/back` 은
**턴어라운드가 아니다** — 정면은 뿔 4개 어깨갑, 측면은 아치 뚫린 다른 물건, 후면은
방패+천+원통이고 높이가 1024/732/704 다. 그걸로 낸 「깊이/폭이 케이스마다 8배 다르다」는
**무효다.** 검증 없이 파일 이름만 보고 3판으로 묶은 결과다.

## 그래서 진짜로 나온 결론

**이 저장소에 유효한 3판 세트는 오메가몬 하나뿐이다.** 야스호 3장은 전부 정면(포즈만 다름),
스탠드 3종은 각각 다른 캐릭터, 견갑 3장은 서로 다른 물건이다.

「더 테스트한다」가 지금 물리적으로 불가능하다. **필요한 건 코드가 아니라 두 번째 턴어라운드**다.
그게 들어오기 전까지 이 파일의 표는 한 줄로 남는다.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull as H
import win as W

CASES = {
    "오메가몬": {"front": "omega_front_clean.png", "side": "omega_side.png",
                 "back": "omega_back.png"},
}   # 두 번째 유효 케이스가 생기면 여기 추가한다. 견갑은 턴어라운드가 아니라 넣으면 안 된다


def synth_side(front, k):
    """측면 판을 지어낸다 — 높이마다 정면 폭의 k 배를 가운데에. **이게 유일한 가정이다.**"""
    out = np.zeros_like(front)
    c = W.RES // 2
    for r in range(W.RES):
        xs = np.where(front[r])[0]
        if len(xs) == 0:
            continue
        d = max(int(round(k * (xs.max() - xs.min() + 1))), 1)
        out[r, max(c - d // 2, 0):min(c + d - d // 2, W.RES)] = True
    return out


def iou3(a, b):
    return float((a & b).sum()) / max(int((a | b).sum()), 1)


def depth_ratio(m):
    """측면이 실제로 준 깊이/폭. 높이마다 재고 중앙값."""
    r = []
    for row in range(W.RES):
        fx = np.where(m["front"][row])[0]
        sx = np.where(m["side"][row])[0]
        if len(fx) > 4 and len(sx) > 2:
            r.append((sx.max() - sx.min() + 1) / (fx.max() - fx.min() + 1))
    return np.array(r)


def main():
    print("  케이스     깊이/폭 중앙(사분위)   정면+측면   정면+후면   정면만")
    got = {}
    for name, src in CASES.items():
        m = {v: H.to_win(H.declutter(W.art_mask(os.path.join(H.IN7, f)))) for v, f in src.items()}
        m = H._warp(m, H.align(m))
        ref, _ = H.carve(m)
        k = depth_ratio(m)
        s = synth_side(m["front"], 0.3)
        out = []
        for mm in ({"front": m["front"], "side": m["side"], "back": m["front"]},
                   dict(m, side=s),
                   {"front": m["front"], "back": m["front"], "side": s}):
            v, _ = H.carve(mm)
            out.append(iou3(ref, v))
        got[name] = out
        print("  %-8s   %.2f (%.2f~%.2f)        %.3f      %.3f     %.3f"
              % (name, np.median(k), np.percentile(k, 25), np.percentile(k, 75), *out))

    fs = [v[0] for v in got.values()]
    fb = [v[1] for v in got.values()]
    print("\n  후면 빼기 %.3f · 측면 빼기 %.3f" % (min(fs), max(fb)))
    assert min(fs) > 0.85, "후면을 뺐는데 %.3f 로 무너진다 — 결론을 다시 써야 한다" % min(fs)
    assert max(fb) < 0.75, "측면 없이도 %.3f 가 나온다 — 결론을 다시 써야 한다" % max(fb)
    print("  => 정면+측면이면 되고 정면만으로는 안 된다. **다만 케이스 %d 개짜리 결론이다**"
          % len(got))
    if len(got) < 2:
        print("     두 번째 턴어라운드가 들어오기 전까지 이건 관찰이지 결론이 아니다")


if __name__ == "__main__":
    main()
