# -*- coding: utf-8 -*-
"""깊이를 **측면 윤곽에서** 읽는다. 반경 하나로 압축하지 않는다.

    python depth.py            -> parts/depth.json
    python depth.py --check    -> 자체 검사

base.py 는 측면 윤곽 66점·모서리 27개를 `ay = (max-min)/2` 숫자 하나로 줄였다.
그래서 밑바탕이 타원체가 됐고, 판을 그 위에 앉히자 견갑이 어깨 공이 됐다.

여기서는 **높이마다** 읽는다 — 1절의 "z 로 쌓기" 와 같은 생각이다.

    정면 윤곽 poly_xz  ->  그 높이의 x 범위   (폭)
    측면 윤곽 poly_yz  ->  그 높이의 y 범위   (앞면·뒷면 깊이)

앞면은 측정값이다. **뒷면은 아니다** — 후면 원화에서 이 견갑은 방패에 가려 있다.
뒷면 y 는 측면 윤곽이 주는 뒤쪽 끝일 뿐이고, 그 x 단면은 모른다.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NBAND = 48          # 높이 표본 수. 원화 z 대역이 0.13 이니 화소로 ~2.8px 간격
# 창은 스윕으로 골랐다 (sweep_smooth.sh). 정면 IoU 는 평활에 안 변하고 (윤곽만 쓴다)
# 값은 측면에서만 치른다:  창0 거칠기1153/측면0.891 -> 창15 거칠기70/측면0.856
SMOOTH = int(os.environ.get("SMOOTH", 15))  # 대역 평활 창 (대역 수). 0 이면 끄기

# 윤곽은 **화소로 딴 것**이라 높이별 함수가 톱니다 (yf 2차차분 RMS 1153, 타원체는 13.6).
# 그 톱니가 표면에 가로 주름으로 찍힌다. 정보는 진짜고 잡음만 걷어낸다 (LESSONS 81).


def smooth(v, w):
    if w < 3:
        return v
    w = w if w % 2 else w + 1
    k = np.hanning(w); k /= k.sum()
    pad = np.r_[np.repeat(v[0], w // 2), v, np.repeat(v[-1], w // 2)]   # 끝은 값 유지
    return np.convolve(pad, k, mode="valid")


def spans(poly, z, eps=1e-9):
    """닫힌 다각형을 높이 z 로 스캔해 [min, max] 를 준다. 없으면 None."""
    p = np.asarray(poly, float)
    a, b = p, np.roll(p, -1, axis=0)
    za, zb = a[:, 1], b[:, 1]
    hit = ((za <= z) & (zb > z)) | ((zb <= z) & (za > z))
    if not hit.any():
        return None
    t = (z - za[hit]) / np.where(np.abs(zb[hit] - za[hit]) < eps, eps, zb[hit] - za[hit])
    xs = a[hit, 0] + t * (b[hit, 0] - a[hit, 0])
    return float(xs.min()), float(xs.max())


def build():
    s = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
    # 폭은 **메시가 실제로 쓰는 윤곽**(lines.json)에서 뜬다. sh_pauldron 의 32점 폴리곤을
    # 쓰면 대역 폭이 메시보다 좁아 t 가 ±1 에 못 닿고, 테두리가 평평해진다
    F = json.load(open(os.path.join(HERE, "parts", "lines.json")))["outline"]
    S = s["side"]["poly_yz"]
    zf = [p[1] for p in F]
    zs = [p[1] for p in S]
    z0, z1 = max(min(zf), min(zs)), min(max(zf), max(zs))   # 두 윤곽이 **겹치는** 대역만
    zz = np.linspace(z0, z1, NBAND)
    bands = []
    for z in zz:
        fx = spans(F, z)
        sy = spans(S, z)
        if fx is None or sy is None:
            continue
        if fx[1] - fx[0] < 1e-4 or sy[1] - sy[0] < 1e-4:
            continue      # 끝 대역은 스캔선이 꼭짓점을 스쳐 폭이 0 이 된다. 버린다
        bands.append(dict(z=float(z), x0=fx[0], x1=fx[1], yf=sy[0], yb=sy[1]))
    if SMOOTH >= 3 and len(bands) >= SMOOTH:
        for key in ("x0", "x1", "yf", "yb"):
            sm = smooth(np.array([b[key] for b in bands]), SMOOTH)
            for b, v in zip(bands, sm):
                b[key] = float(v)
    out = dict(z0=float(z0), z1=float(z1), n=len(bands), bands=bands, smooth=SMOOTH,
               note="yf 는 앞면(측정), yb 는 측면 윤곽의 뒤쪽 끝. 뒷면 x 단면은 모른다")
    json.dump(out, open(os.path.join(HERE, "parts", "depth.json"), "w"), indent=1)
    print("대역 %d개  z %.4f..%.4f" % (len(bands), z0, z1))
    w = [b["x1"] - b["x0"] for b in bands]
    d = [b["yb"] - b["yf"] for b in bands]
    print("  폭   %.4f..%.4f  (평균 %.4f)" % (min(w), max(w), float(np.mean(w))))
    print("  깊이 %.4f..%.4f  (평균 %.4f)" % (min(d), max(d), float(np.mean(d))))
    print("  ay 한 숫자였을 때의 지름 %.4f" % (2 * 0.0762))
    return out


def check():
    """대역이 실제로 변하는가 — 변하지 않으면 타원체와 다를 게 없다."""
    o = json.load(open(os.path.join(HERE, "parts", "depth.json")))
    b = o["bands"]
    assert len(b) >= NBAND // 2, "대역이 너무 적다: %d" % len(b)
    w = np.array([x["x1"] - x["x0"] for x in b])
    d = np.array([x["yb"] - x["yf"] for x in b])
    assert (w > 0).all() and (d > 0).all(), "폭/깊이가 0 이하인 대역이 있다"
    # 깊이가 높이에 따라 실제로 변해야 의미가 있다 (타원체면 부드러운 반원 하나)
    rel = float(d.std() / d.mean())
    z = np.array([x["z"] for x in b]); dz = float(np.diff(z).mean())
    yf = np.array([x["yf"] for x in b])
    r2 = float(np.sqrt(((np.diff(yf, 2) / dz ** 2) ** 2).mean()))
    flip = int((np.diff(np.sign(np.diff(yf))) != 0).sum())
    print("깊이 변동 %.3f (0 이면 균일)  폭 변동 %.3f" % (rel, float(w.std() / w.mean())))
    print("yf 거칠기: 2차차분 RMS %.1f  기울기 부호바뀜 %d회  (타원체는 13.6 / 1회)" % (r2, flip))
    assert r2 < 150, "yf 가 아직 톱니다 (%.1f) — 표면에 가로 주름이 찍힌다" % r2
    assert rel > 0.02, "깊이가 사실상 균일하다 — 측면 윤곽을 쓸 이유가 없다"
    print("OK")


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    else:
        build()
        if "--nocheck" not in sys.argv:
            check()
