# -*- coding: utf-8 -*-
"""**어깨 위에 덧댄 판**이라는 사실을 쓴다 — 밑바탕 곡면을 원화에서 잰다.

    python base.py     ->  parts/base.json

106번: 그늘 부호 15개로 판 15개(30자유도)를 못 정했다. 나머지를 "기울기 최소"
정칙화가 채워서 그럴듯하지만 원화가 아닌 형태가 됐다.

빠진 건 정보가 아니라 **전제**였다. 견갑은 공중에 뜬 껍질이 아니라 어깨 관절
위에 덧댄 판이다. 어깨는 공이고, 그 깊이는 자유도가 아니라 **측정값**이다.

    a_x  정면 캡 실루엣의 가로 반경
    a_z  정면 캡 실루엣의 세로 반경
    a_y  측면 실루엣에서 캡 z 대역의 깊이 반경

판마다 그 타원체 앞면에 최소제곱 평면을 맞춘다. **노브가 없다** —
그리고 그늘은 이 풀이에 안 들어갔으니, 그늘이 맞는지가 **held-out 검사**가 된다.
"""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
T4 = os.path.join(HERE, "..", "trail4_gen3d")
RES = 1024
cc = lambda u: (u + 0.6) / 1.2 * (RES - 1)
rr = lambda z: (1.1 - z) / 1.2 * (RES - 1)
wc = lambda c: -0.6 + c * 1.2 / (RES - 1)
wz = lambda r: 1.1 - r * 1.2 / (RES - 1)
BULGE = float(os.environ.get("BULGE", 1.0))     # 타원체를 이만큼 부풀린다 (1 = 실측)


def main():
    J = json.load(open(os.path.join(HERE, "parts", "panels.json")))
    x0, x1, y0, y1 = J["win"]
    L = np.load(os.path.join(HERE, "out", "_L_alb.npy"))
    keep = [p for p in J["panels"] if p["hue"] in ("lav", "gold")]
    cap = np.isin(L, [p["id"] for p in keep])
    ys, xs = np.nonzero(cap)
    cxw = [wc(x + x0) for x in xs]
    czw = [wz(y + y0) for y in ys]
    cx, ax = (max(cxw) + min(cxw)) / 2, (max(cxw) - min(cxw)) / 2
    cz, az = (max(czw) + min(czw)) / 2, (max(czw) - min(czw)) / 2

    # 측면 깊이. 실루엣의 연결 성분을 그냥 재면 **몸통까지 잡는다** (0.344 가 나왔다).
    # measure.py 가 견갑만 떼어 둔 것을 쓴다
    sp = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json")))
    ay = (max(sp["side"]["y"]) - min(sp["side"]["y"])) / 2
    cy = float(os.environ.get("CY", 0.027))
    print("어깨 타원체 (원화 실측)")
    print("  중심 x %+.4f  z %.4f  y %+.4f" % (cx, cz, cy))
    print("  반경 ax %.4f (정면 가로)  az %.4f (정면 세로)  ay %.4f (측면 깊이)" % (ax, az, ay))
    ax, az, ay = ax * BULGE, az * BULGE, ay * BULGE

    def surf(x, z):
        """앞면 깊이. 타원체 밖이면 테두리로 잘라 접선 연장."""
        t = ((x - cx) / ax) ** 2 + ((z - cz) / az) ** 2
        return cy - ay * np.sqrt(np.clip(1.0 - t, 0.02, None))

    out = []
    for p in keep:
        m = L == p["id"]
        yy, xx = np.nonzero(m)
        X = np.array([wc(v + x0) for v in xx])
        Z = np.array([wz(v + y0) for v in yy])
        Y = surf(X, Z)
        A = np.stack([X, Z, np.ones_like(X)], 1)
        (a, b, c), *_ = np.linalg.lstsq(A, Y, rcond=None)
        rms = float(np.sqrt(((A @ [a, b, c] - Y) ** 2).mean()))
        nz = np.array([a, -1.0, b])
        nz /= np.linalg.norm(nz)
        out.append(dict(id=p["id"], a=float(a), b=float(b), c=float(c), lit=p["lit"],
                        hue=p["hue"], rms=rms, normal=[float(v) for v in nz], poly=p["poly"]))

    # held-out 검사: 이 풀이는 그늘을 **안 봤다**. 어떤 광원이 라벨을 몇 개 맞추나
    N = np.array([r["normal"] for r in out])
    lit = np.array([r["lit"] for r in out])
    best = (-1, None)
    import math
    for el in range(-75, 90, 15):
        for az_ in range(0, 360, 15):
            ce, se = math.cos(math.radians(el)), math.sin(math.radians(el))
            l = np.array([ce * math.cos(math.radians(az_)), -se, ce * math.sin(math.radians(az_))])
            ok = int((((N @ l) > 0) == lit).sum())
            if ok > best[0]:
                best = (ok, (az_, el, l))
    print("\nheld-out: 어깨 돔이 그늘 라벨을 %d/%d 맞춘다  (광원 방위 %d 고도 %+d)"
          % (best[0], len(out), best[1][0], best[1][1]))
    print("  무작위 기대 %.1f개   판별 평면 맞춤 오차 %.4f (평균)"
          % (len(out) / 2, float(np.mean([r["rms"] for r in out]))))
    json.dump(dict(cx=cx, cz=cz, cy=cy, ax=ax, az=az, ay=ay,
                   light=[float(v) for v in best[1][2]], ok=best[0], planes=out),
              open(os.path.join(HERE, "parts", "base.json"), "w"), indent=1)
    print("-> parts/base.json")


if __name__ == "__main__":
    main()
