# -*- coding: utf-8 -*-
"""깎을 수 있는 **숄더패드 블록아웃**을 짓는다 — 쿼드 격자 + 테두리를 실루엣에 스냅.

    python pad.py     ->  parts/pad.json

크랙 그래프로 지은 앞판은 삼각 스프라 손댈 수가 없었다. 여기서는
    격자          안쪽은 균일 쿼드 (섭디비전·조각 다 먹는다)
    테두리 스냅   격자 계단(IoU 0.844)을 원화 윤곽에 붙여 없앤다
    깊이          어깨 돔 (107번) — 노브 아님
"""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = 1024
wc = lambda c: -0.6 + c * 1.2 / (RES - 1)
wz = lambda r: 1.1 - r * 1.2 / (RES - 1)
N = int(os.environ.get("PAD_N", 40))


def main():
    B = json.load(open(os.path.join(HERE, "parts", "base.json")))
    M = cv2.imread(os.path.join(HERE, "out", "cap_mask.png"), 0) > 127
    ys, xs = np.nonzero(M)
    u0, u1 = wc(xs.min()) - 0.002, wc(xs.max()) + 0.002
    z0, z1 = wz(ys.max()) - 0.002, wz(ys.min()) + 0.002

    def inside(u, z):
        c = int(round((u + 0.6) / 1.2 * (RES - 1)))
        r = int(round((1.1 - z) / 1.2 * (RES - 1)))
        return 0 <= c < RES and 0 <= r < RES and M[r, c]

    def dome(u, z):
        t = ((u - B["cx"]) / B["ax"]) ** 2 + ((z - B["cz"]) / B["az"]) ** 2
        return B["cy"] - B["ay"] * max(1.0 - t, 0.02) ** 0.5

    P = np.array([[u0 + (u1 - u0) * i / N, z0 + (z1 - z0) * j / N]
                  for i in range(N + 1) for j in range(N + 1)])
    idx = lambda i, j: i * (N + 1) + j
    faces = []
    for i in range(N):
        for j in range(N):
            cs = [idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)]
            if all(inside(*P[c]) for c in cs):        # 네 모서리 전부 안쪽일 때만
                faces.append(cs)
    used = sorted({v for f in faces for v in f})
    ren = {v: k for k, v in enumerate(used)}
    V = P[used]
    F = [[ren[v] for v in f] for f in faces]

    # 테두리 정점을 원화 윤곽으로 스냅 — 격자 계단을 없앤다
    from collections import Counter
    ec = Counter()
    for f in F:
        for a, b in zip(f, f[1:] + f[:1]):
            ec[(min(a, b), max(a, b))] += 1
    bnd = sorted({v for e, c in ec.items() if c == 1 for v in e})
    cnt = max(cv2.findContours(M.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0],
              key=cv2.contourArea).reshape(-1, 2)
    C = np.stack([[wc(p[0]) for p in cnt], [wz(p[1]) for p in cnt]], 1)
    moved = 0.0
    for v in bnd:
        d = np.linalg.norm(C - V[v], axis=1)
        k = int(np.argmin(d))
        moved = max(moved, float(d[k]))
        V[v] = C[k]
    print("격자 %dx%d -> 정점 %d 면 %d   테두리 %d개 스냅 (최대 이동 %.4f)"
          % (N, N, len(V), len(F), len(bnd), moved))

    Y = [dome(u, z) for u, z in V]
    json.dump(dict(verts=[[float(u), float(y), float(z)] for (u, z), y in zip(V, Y)],
                   faces=F, bnd=bnd),
              open(os.path.join(HERE, "parts", "pad.json"), "w"))
    print("-> parts/pad.json   깊이 %.4f..%.4f" % (min(Y), max(Y)))


if __name__ == "__main__":
    main()
