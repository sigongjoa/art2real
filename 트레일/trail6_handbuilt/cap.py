# -*- coding: utf-8 -*-
"""갑주 캡을 albedo 분할에서 뽑는다 — 윤곽 + **능선이 지나는 높이**.

    python cap.py     ->  parts/cap.json

70번에서 "고리를 균일하게 늘려 선을 벌지 마라. 원화가 선을 그은 자리에 놓아라" 고
적어놓고 그 자리를 몰라서 GROOVE_AT 노브로 때웠다. 이제 97~98번의 판 분해가 그걸 준다.

    cap 마스크    albedo 분할의 라벤더 판을 모은 것 (+ 먹선 띠 — 79번)
    poly_xz       그 윤곽. 81번의 모서리 앵커 + 편차 채움
    crease_z      **캡 안쪽 판 경계가 가로지르는 높이** = 고리를 놓을 자리
                  경계 화소를 z 로 히스토그램해서 봉우리를 뽑는다
"""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
T4 = os.path.join(HERE, "..", "trail4_gen3d")
RES = 1024
MINPK = 0.30      # 최대 봉우리의 이 비율 넘는 것만 능선으로 본다


def hue(mc):
    r, g, b = mc
    if r - b > 20 and r - g < 60:
        return "gold"
    if b - r > 8:
        return "lav"
    return "white" if min(mc) > 170 else "dark"


def main():
    import sys
    sys.path.insert(0, HERE)
    from measure import outline, with_ink

    cc = lambda u: (u + 0.6) / 1.2 * (RES - 1)
    rr = lambda z: (1.1 - z) / 1.2 * (RES - 1)
    wz = lambda r: 1.1 - r * 1.2 / (RES - 1)
    wc = lambda c: -0.6 + c * 1.2 / (RES - 1)

    raw = np.load(os.path.join(T4, "rgb_front.npy"))
    rgb = raw[..., :3].astype(np.uint8)
    sil = raw[..., 3] > 0
    y0, y1 = int(rr(0.985)), int(rr(0.775))
    x0, x1 = int(cc(0.118)), int(cc(0.252))
    C = rgb[y0:y1, x0:x1]
    S = sil[y0:y1, x0:x1]
    H, W = S.shape
    L = np.load(os.path.join(HERE, "out", "_L_alb.npy"))

    lav = np.zeros((H, W), bool)
    for v in np.unique(L):
        if v <= 1:
            continue
        m = L == v
        if m.sum() >= 40 and hue(np.median(C[m], axis=0)) == "lav":
            lav |= m
    n, lb, st, _ = cv2.connectedComponentsWithStats(lav.astype(np.uint8), 8)
    cap = lb == (1 + int(np.argmax([st[i, cv2.CC_STAT_AREA] for i in range(1, n)])))
    cap = cv2.morphologyEx(cap.astype(np.uint8), cv2.MORPH_CLOSE,
                           cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))).astype(bool)
    # 먹선까지 포함해야 원화의 형태다 (79번)
    full = np.zeros((RES, RES), bool)
    full[y0:y1, x0:x1] = cap
    cap_ink = with_ink(full, raw[..., :3].astype(np.int16), sil)
    poly_px, ncor = outline(cap_ink, tol=1.5)
    # outline() 은 **화소 좌표**를 준다. 월드로 옮긴다 (measure.py 는 호출부에서 옮긴다)
    poly = np.array([[wc(px), wz(py)] for px, py in poly_px])
    print("캡 %d 화소 -> 먹선 포함 %d 화소   윤곽 %d정점 (모서리 %d)"
          % (cap.sum(), cap_ink.sum(), len(poly), ncor))

    # 캡 **안쪽**의 판 경계 = 능선. z 로 히스토그램
    inner = cv2.erode(cap.astype(np.uint8),
                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))).astype(bool)
    B = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (1, 0)):
        a = L[:H - dy, :W - dx]
        b = L[dy:, dx:]
        B[:H - dy, :W - dx] |= (a > 1) & (b > 1) & (a != b)
    B &= inner
    ys, xs = np.nonzero(B)
    print("캡 안쪽 판 경계 %d 화소" % len(ys))
    zs = np.array([wz(y + y0) for y in ys])
    zlo, zhi = float(poly[:, 1].min()), float(poly[:, 1].max())
    nb = 26
    hist, edges = np.histogram(zs, bins=nb, range=(zlo, zhi))
    sm = np.convolve(hist, np.ones(3) / 3, "same")
    peaks = []
    for i in range(1, nb - 1):
        if sm[i] >= sm[i - 1] and sm[i] >= sm[i + 1] and sm[i] >= MINPK * sm.max():
            peaks.append(float((edges[i] + edges[i + 1]) / 2))
    # 너무 붙은 봉우리는 합친다
    merged = []
    for z in sorted(peaks):
        if merged and z - merged[-1] < (zhi - zlo) * 0.05:
            merged[-1] = (merged[-1] + z) / 2
        else:
            merged.append(z)
    print("능선 높이 %d개: %s" % (len(merged), [round(z, 4) for z in merged]))
    print("  (캡 z %.4f .. %.4f)" % (zlo, zhi))
    json.dump({"poly_xz": [[float(a), float(b)] for a, b in poly],
               "corners": int(ncor),
               "z": [zlo, zhi],
               "crease_z": merged},
              open(os.path.join(HERE, "parts", "cap.json"), "w"), indent=1)
    print("-> parts/cap.json")


if __name__ == "__main__":
    main()
