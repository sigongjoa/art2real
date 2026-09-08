# -*- coding: utf-8 -*-
"""판 그래프를 뽑는다 — 각 판의 윤곽 / 밝기(밝음·그늘) / 이웃과 공유하는 경계.

    python panels.py     ->  parts/panels.json

103번: 그림자는 **화면 밖 방향을 담은 유일한 단서**다. 벗기지 말고 푼다.
그 풀이의 입력이 이 파일이다.

    poly      판 윤곽 (월드 x,z). 81번의 모서리 앵커 + 편차 채움
    lit       재질별 오츠로 가른 밝음/그늘
    edges     (i,j, 공유 화소 목록, ink)  ink=True 면 가림선이라 깊이가 안 이어진다
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
MINPX = 40
INK_V = 110        # 이보다 어두우면 먹선
INK_W = 2.5        # 경계에 걸친 먹선이 이만큼 두꺼우면 가림선으로 본다


def hue(mc):
    r, g, b = mc
    if r - b > 20 and r - g < 60:
        return "gold"
    if b - r > 8:
        return "lav"
    return "white" if min(mc) > 170 else "dark"


def otsu(v):
    h = np.histogram(v, bins=64, range=(0, 256))[0].astype(float)
    tot, cum = h.sum(), np.cumsum(h)
    mu = np.cumsum(h * (np.arange(64) * 4 + 2))
    best, bt = -1, 128
    for k in range(1, 63):
        w0, w1 = cum[k], tot - cum[k]
        if w0 < 1 or w1 < 1:
            continue
        var = w0 * w1 * (mu[k] / w0 - (mu[-1] - mu[k]) / w1) ** 2
        if var > best:
            best, bt = var, k * 4 + 2
    return bt


def main():
    import sys
    sys.path.insert(0, HERE)
    from measure import outline

    raw = np.load(os.path.join(T4, "rgb_front.npy"))
    y0, y1 = int(rr(0.985)), int(rr(0.775))
    x0, x1 = int(cc(0.118)), int(cc(0.252))
    C = raw[y0:y1, x0:x1, :3].astype(np.int16)
    L = np.load(os.path.join(HERE, "out", "_L_alb.npy"))
    H, W = L.shape
    V = C.max(2)
    ink = V < INK_V
    dt_ink = cv2.distanceTransform(ink.astype(np.uint8), cv2.DIST_L2, 5)

    ids = [int(v) for v in np.unique(L) if v > 1 and (L == v).sum() >= MINPX]
    P = {}
    for v in ids:
        m = L == v
        k = hue(np.median(C[m], axis=0))
        P[v] = dict(mask=m, hue=k, px=int(m.sum()))
    # 밝음/그늘 — 재질별 오츠
    for k in ("lav", "gold"):
        vs = [v for v in ids if P[v]["hue"] == k]
        if not vs:
            continue
        allv = np.concatenate([V[P[v]["mask"] & ~ink] for v in vs])
        t = otsu(allv)
        for v in vs:
            mv = V[P[v]["mask"] & ~ink]
            P[v]["lit"] = bool(np.median(mv) >= t) if len(mv) else True
            P[v]["V"] = float(np.median(mv)) if len(mv) else 0.0
        print("%s 판 %d개  오츠 임계 %d" % (k, len(vs), t))

    # 이웃과 공유 경계
    edges = {}
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        a = L[max(0, -0):H - dy, max(0, -dx):W - max(dx, 0)] if dx >= 0 else L[:H - dy, -dx:]
        # 단순하게 간다 — 시프트 두 장을 직접 만든다
        A = L[:H - dy, max(dx, 0):W + min(dx, 0)]
        B = L[dy:, max(-dx, 0):W + min(-dx, 0)]
        ys, xs = np.nonzero((A > 1) & (B > 1) & (A != B))
        for yy, xx in zip(ys, xs):
            i, j = int(A[yy, xx]), int(B[yy, xx])
            if i not in P or j not in P:
                continue
            key = (min(i, j), max(i, j))
            px = (xx + max(dx, 0), yy)
            edges.setdefault(key, []).append(px)

    out_edges = []
    for (i, j), pts in edges.items():
        if len(pts) < 6:
            continue
        w = float(np.median([dt_ink[p[1], p[0]] for p in pts])) * 2
        pts = pts[:: max(1, len(pts) // 24)]           # 24점이면 평면 두 개 잇기에 충분
        out_edges.append(dict(i=i, j=j, n=len(edges[(i, j)]), ink_w=w,
                              occl=bool(w >= INK_W),
                              pts=[[wc(p[0] + x0), wz(p[1] + y0)] for p in pts]))

    recs = []
    for v in ids:
        m = P[v]["mask"].astype(bool)
        full = np.zeros((RES, RES), bool)
        full[y0:y1, x0:x1] = m
        try:
            poly_px, ncor = outline(full, tol=1.2)
            poly = [[float(wc(a)), float(wz(b))] for a, b in poly_px]
        except Exception:
            poly, ncor = [], 0
        ys, xs = np.nonzero(m)
        recs.append(dict(id=v, hue=P[v]["hue"], px=P[v]["px"], lit=P[v].get("lit", True),
                         V=P[v].get("V", 0.0), ncor=int(ncor), poly=poly,
                         cx=float(wc(xs.mean() + x0)), cz=float(wz(ys.mean() + y0))))
    recs.sort(key=lambda r: -r["px"])
    print("\n판 %d개  (라벤더 %d / 금 %d)   경계 %d개 (가림 %d)"
          % (len(recs), sum(r["hue"] == "lav" for r in recs), sum(r["hue"] == "gold" for r in recs),
             len(out_edges), sum(e["occl"] for e in out_edges)))
    for r in recs:
        print("  %3d %-4s px%-5d %-5s V%3.0f  중심(%+.4f,%.4f) 정점%d"
              % (r["id"], r["hue"], r["px"], "밝음" if r["lit"] else "그늘", r["V"],
                 r["cx"], r["cz"], len(r["poly"])))
    json.dump(dict(win=[x0, x1, y0, y1], panels=recs, edges=out_edges),
              open(os.path.join(HERE, "parts", "panels.json"), "w"), indent=1)
    print("-> parts/panels.json")


if __name__ == "__main__":
    main()
