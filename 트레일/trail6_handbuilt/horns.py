# -*- coding: utf-8 -*-
"""금 부품(뿔)만 뽑아 **축과 폭 프로파일**로 적는다.

    python horns.py     ->  parts/horns.json  +  out/proof_horns_each.png

97~98번의 albedo 기반 분할 위에서 금 판만 모으고, 붙어 있는 뿔을
**거리변환의 국소 최대** 씨앗으로 가른다. 전역 임계는 굵은 뿔에만 씨앗을 줘서
가는 뿔이 엉뚱한 데 흡수된다(실제로 화살표가 서로 교차했다).

뿔마다 적는 것:
    axis      뿌리 -> 끝 (월드 x,z). 캡 중심에서 먼 쪽이 끝이다
    profile   축을 따라 N 지점에서 잰 **반폭** (월드 단위)
              -> PCA 반지름 하나보다 낫다. 실루엣이 정의로 맞는다
    y         깊이는 정면 원화가 안 준다. **노브다** (기본 = 캡 중앙 y)
"""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
T4 = os.path.join(HERE, "..", "trail4_gen3d")
RES = 1024
NSTA = 9          # 폭을 재는 지점 수
SEED_WIN = 7      # 국소 최대 창


def wc(c):
    return -0.6 + c * 1.2 / (RES - 1)


def wz(r):
    return 1.1 - r * 1.2 / (RES - 1)


def hue(mc):
    r, g, b = mc
    if r - b > 20 and r - g < 60:
        return "gold"
    if b - r > 8:
        return "lav"
    return "white" if min(mc) > 170 else "dark"


def main():
    cc = lambda u: (u + 0.6) / 1.2 * (RES - 1)
    rr = lambda z: (1.1 - z) / 1.2 * (RES - 1)
    raw = np.load(os.path.join(T4, "rgb_front.npy"))
    rgb = raw[..., :3].astype(np.uint8)
    sil = raw[..., 3] > 0
    y0, y1 = int(rr(0.985)), int(rr(0.775))
    x0, x1 = int(cc(0.118)), int(cc(0.252))
    C = rgb[y0:y1, x0:x1]
    S = sil[y0:y1, x0:x1]
    H, W = S.shape
    L = np.load(os.path.join(HERE, "out", "_L_alb.npy"))

    gold = np.zeros((H, W), bool)
    for v in np.unique(L):
        if v <= 1:
            continue
        m = L == v
        if m.sum() >= 40 and hue(np.median(C[m], axis=0)) == "gold":
            gold |= m
    gm = cv2.morphologyEx(gold.astype(np.uint8), cv2.MORPH_CLOSE,
                          cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    dt = cv2.distanceTransform(gm, cv2.DIST_L2, 5)
    mx = cv2.dilate(dt, np.ones((SEED_WIN, SEED_WIN), np.uint8))
    seed = (dt >= mx - 1e-6) & (dt > 1.5) & (gm > 0)
    n, lb, st, _ = cv2.connectedComponentsWithStats(seed.astype(np.uint8), 8)
    order = sorted(range(1, n), key=lambda i: -dt[lb == i].max())
    mk = np.zeros(lb.shape, np.int32)
    for k, i in enumerate(order, start=2):
        mk[lb == i] = k
    mk[gm == 0] = 1
    mk[(gm > 0) & (mk == 0)] = 0
    ws = cv2.watershed(cv2.cvtColor(C, cv2.COLOR_RGB2BGR), mk.copy())

    capc = np.array([np.nonzero(S)[1].mean(), np.nonzero(S)[0].mean()])
    out = []
    for v in sorted([v for v in np.unique(ws) if v > 1],
                    key=lambda v: -((ws == v) & (gm > 0)).sum()):
        m = (ws == v) & (gm > 0)
        if m.sum() < 60:
            continue
        ys, xs = np.nonzero(m)
        pts = np.stack([xs, ys], 1).astype(float)
        mu = pts.mean(0)
        _, _, vt = np.linalg.svd(pts - mu, full_matrices=False)
        ax = vt[0]
        t = (pts - mu) @ ax
        e0, e1 = mu + ax * t.min(), mu + ax * t.max()
        tip, root = (e0, e1) if np.linalg.norm(e0 - capc) > np.linalg.norm(e1 - capc) else (e1, e0)
        d = tip - root
        Lp = np.hypot(*d)
        if Lp < 1e-6:
            continue
        u = d / Lp
        perp = np.array([-u[1], u[0]])
        s = (pts - root) @ u
        q = (pts - root) @ perp
        prof = []
        for k in range(NSTA):
            a = Lp * k / (NSTA - 1)
            sel = np.abs(s - a) <= max(Lp / (NSTA - 1) * 0.7, 1.0)
            # 축을 따라 그 지점의 **반폭**. 없으면 0 (끝점)
            prof.append(float(np.abs(q[sel]).max() * 1.2 / (RES - 1)) if sel.any() else 0.0)
        out.append({
            "px": int(m.sum()),
            "root_xz": [wc(root[0] + x0), wz(root[1] + y0)],
            "tip_xz": [wc(tip[0] + x0), wz(tip[1] + y0)],
            "length": float(Lp * 1.2 / (RES - 1)),
            "halfwidth": prof,
        })
    for i, h in enumerate(out):
        print("%d  px%-5d  len %.4f  반폭 %s"
              % (i, h["px"], h["length"], [round(x, 4) for x in h["halfwidth"]]))
    json.dump({"nsta": NSTA, "horns": out},
              open(os.path.join(HERE, "parts", "horns.json"), "w"), indent=1)
    print("-> parts/horns.json  (뿔 %d개)" % len(out))


if __name__ == "__main__":
    main()
