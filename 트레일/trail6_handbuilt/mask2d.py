# -*- coding: utf-8 -*-
"""견갑이 각 판에서 차지하는 **경계**. 색이 아니라 여기로 남의 부품을 거른다.

    python mask2d.py        # 커밋된 실측 화소 수와 맞는지 자체검사

블렌더 안에서도 밖에서도 돈다 (bpy·PIL 안 쓴다). tri_paint.py 가 두 군데서 쓴다 —
면 중심 하나하나를 거를 때, 그리고 판정에서 1024² 마스크를 깔 때.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES, U0, U1, Z0, Z1 = 1024, -0.6, 0.6, -0.1, 1.1
UAX = {"front": 0, "side": 1}          # 판의 화면 u 가 무슨 월드축인가 (bake_art.py 규약)


def load():
    """정면은 판 18개 중 라벤더+금(= 캡 + 뿔), 측면은 견갑 실측 윤곽."""
    sh = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
    pn = json.load(open(os.path.join(HERE, "parts", "panels.json"), encoding="utf-8"))
    fr = [np.array(p["poly"], float) for p in pn["panels"] if p["hue"] in ("lav", "gold")]
    sd = [np.array(sh["side"]["poly_yz"], float)]
    for h in sh["side"].get("horns", []):
        if isinstance(h, dict) and "poly_yz" in h:
            sd.append(np.array(h["poly_yz"], float))
    return {"front": fr, "side": sd}


def inside(polylist, P):
    """짝수-홀수 교차. P (n,2) -> (n,) bool. 폴리곤 여러 장의 합집합."""
    x, y = P[:, 0], P[:, 1]
    out = np.zeros(len(P), bool)
    for poly in polylist:
        c = np.zeros(len(P), bool)
        for i in range(len(poly)):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % len(poly)]
            if y0 == y1:
                continue
            c ^= ((y0 > y) != (y1 > y)) & (x < (x1 - x0) * (y - y0) / (y1 - y0) + x0)
        out |= c
    return out


def topix(u, z):
    """월드 (u, z) -> 화소 (행, 열). **좌표 변환은 여기 하나뿐이다** —
    raster 는 /RES 로 굽고 조회는 *(RES-1) 로 읽던 반 화소 어긋남이 있었다."""
    px = np.clip((np.asarray(u, float) - U0) / (U1 - U0) * RES, 0, RES - 1e-9).astype(int)
    py = np.clip((Z1 - np.asarray(z, float)) / (Z1 - Z0) * RES, 0, RES - 1e-9).astype(int)
    return py, px


def grid():
    """화소 중심의 월드 좌표 (RES, RES) 두 장."""
    gy, gx = np.mgrid[0:RES, 0:RES]
    return U0 + (gx + 0.5) / RES * (U1 - U0), Z1 - (gy + 0.5) / RES * (Z1 - Z0)


def raster(polylist):
    """1024² 판 마스크. 화소 중심으로 찍는다."""
    u, z = grid()
    return inside(polylist, np.stack([u.ravel(), z.ravel()], 1)).reshape(RES, RES)


def _dilate(m):
    o = m.copy()
    o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
    return o


def target_px():
    """그 판에서 견갑이 차지한다고 **측정된** 화소 수. 팽창 횟수를 여기에 맞춘다."""
    sh = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
    pn = json.load(open(os.path.join(HERE, "parts", "panels.json"), encoding="utf-8"))
    return {"front": sum(p["px"] for p in pn["panels"] if p["hue"] in ("lav", "gold")),
            "side": sh["side"]["px"]}


def fitted():
    """판마다 마스크 하나. 폴리곤은 화소 윤곽의 근사라 정면은 10.9% 작다 —
    그대로 쓰면 실루엣 가장자리의 **정상 면**을 남의 색으로 오해해 물어버린다.
    팽창 횟수는 눈으로 안 찍는다. 측정 화소 수에 제일 가까운 횟수를 고른다."""
    P, want, out = load(), target_px(), {}
    for k in P:
        m = raster(P[k])
        err = abs(int(m.sum()) - want[k])
        n = 0
        for i in range(1, 5):
            m2 = _dilate(m)
            e = abs(int(m2.sum()) - want[k])
            if e >= err:
                break
            m, err, n = m2, e, i
        out[k] = m
        print("  %-5s 마스크 %6d px  (측정 %6d, 팽창 %d회, 차이 %+.1f%%)"
              % (k, m.sum(), want[k], n, (int(m.sum()) - want[k]) / want[k] * 100))
    return out


def lookup(mask, u, z):
    """월드 (u, z) -> 그 판 마스크. u 가 무슨 축인지는 UAX 가 정한다."""
    py, px = topix(u, z)
    return mask[py, px]


def _check():
    # 정사각형 하나 — 안/밖/모서리
    sq = [np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])]
    got = inside(sq, np.array([[.5, .5], [1.5, .5], [.5, 1.5], [-.1, .5], [.5, -.1]]))
    assert list(got) == [True, False, False, False, False], got

    # 구멍 뚫린 도넛: 겹치는 두 장은 합집합이다 (XOR 아님)
    inn = [np.array([[.4, .4], [.6, .4], [.6, .6], [.4, .6]])]
    assert inside(sq + inn, np.array([[.5, .5]]))[0]

    # 오목한 U 자 — 홀짝 교차가 맞아야 가운데 홈이 밖으로 나온다
    u = [np.array([[0., 0.], [3., 0.], [3., 3.], [2., 3.], [2., 1.], [1., 1.], [1., 3.], [0., 3.]])]
    assert list(inside(u, np.array([[.5, 2.], [1.5, 2.], [2.5, 2.], [1.5, .5]]))) == \
        [True, False, True, True]

    # 커밋된 실측과 맞나. panels/sh_pauldron 은 화소 수를 같이 적어 뒀다
    P = load()
    sh = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
    pn = json.load(open(os.path.join(HERE, "parts", "panels.json"), encoding="utf-8"))
    want_f = sum(p["px"] for p in pn["panels"] if p["hue"] in ("lav", "gold"))
    want_s = sh["side"]["px"]
    for key, want in (("front", want_f), ("side", want_s)):
        got = int(raster(P[key]).sum())
        err = abs(got - want) / want
        print("%-5s  폴리곤 %2d장  래스터 %6d px   측정 %6d px   차이 %.1f%%"
              % (key, len(P[key]), got, want, err * 100))
        # 폴리곤은 화소 윤곽을 근사한 것이라 정확히는 안 맞는다. 15% 넘으면 좌표계가 틀린 것
        assert err < 0.15, "%s 마스크가 실측과 %.1f%% 어긋난다 — 좌표창을 의심하라" % (key, err * 100)
    M = fitted()
    want = target_px()
    for k in M:
        e = abs(int(M[k].sum()) - want[k]) / want[k]
        assert e < 0.02, "%s 맞춘 마스크가 아직 %.1f%% 어긋난다" % (k, e * 100)
    # lookup 은 raster 와 같은 화소를 봐야 한다 (좌표 규약 하나뿐이라는 검사)
    u, z = grid()
    assert (lookup(M["front"], u.ravel(), z.ravel()).reshape(RES, RES) == M["front"]).all()
    print("mask2d OK")


if __name__ == "__main__":
    _check()
