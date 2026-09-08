# -*- coding: utf-8 -*-
"""판 경계망을 **한 번만** 폴리곤화한다 — 정점 공유가 공짜가 되게.

    python graph.py     ->  parts/graph.json

판마다 따로 윤곽을 뽑으면 이웃과 정점이 안 맞아 꿰맬 수가 없다
(거리 병합 0.002 로 531->506, 홀 엣지 513개. 거리를 키우면 작은 판이 무너진다).

**크랙 그래프**를 쓴다. 화소가 아니라 화소 사이의 금을 엣지로 놓는다.

    가로 금  모서리(r,c)-(r,c+1)   위아래 화소 라벨이 다르면 존재
    세로 금  모서리(r,c)-(r+1,c)   좌우 화소 라벨이 다르면 존재

금마다 라벨쌍이 하나로 정해진다 — "경계점이면 이어라" 식 8이웃 추적처럼
갈라지지 않는다. 차수 3 이상인 모서리가 **접합점**(다면체 꼭짓점)이고,
접합점 사이의 금 사슬이 **호**다. 호를 한 번 단순화해서 두 판이 그대로 쓴다.
"""
import json
import os
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = 1024
wc = lambda c: -0.6 + c * 1.2 / (RES - 1)
wz = lambda r: 1.1 - r * 1.2 / (RES - 1)
STEP = int(os.environ.get("GSTEP", 4))
SMOOTH = float(os.environ.get("GSMOOTH", 2.0))   # 계단 없애기. 끝점(접합점)은 고정


def main():
    L = np.load(os.path.join(HERE, "out", "_L_alb.npy"))
    J = json.load(open(os.path.join(HERE, "parts", "panels.json")))
    x0, x1, y0, y1 = J["win"]
    keep = {p["id"] for p in J["panels"]}
    H, W = L.shape
    P = np.zeros((H + 2, W + 2), np.int32)
    P[1:-1, 1:-1] = np.where(np.isin(L, list(keep)), L, 0)

    inc = defaultdict(list)      # 모서리 -> [(이웃모서리, 라벨쌍)]
    for r in range(H + 2):
        for c in range(W + 1):
            a, b = P[r - 1, c] if r > 0 else 0, P[r, c] if r < H + 2 else 0
            if r == 0 or r == H + 2:
                continue
            if a != b:
                pr = (min(a, b), max(a, b))
                inc[(r, c)].append(((r, c + 1), pr))
                inc[(r, c + 1)].append(((r, c), pr))
    for r in range(H + 1):
        for c in range(1, W + 2):
            a, b = P[r, c - 1], P[r, c]
            if a != b:
                pr = (min(a, b), max(a, b))
                inc[(r, c)].append(((r + 1, c), pr))
                inc[(r + 1, c)].append(((r, c), pr))
    deg = {k: len(v) for k, v in inc.items()}
    junc = {k for k, d in deg.items() if d != 2}
    print("금이 닿는 모서리 %d   접합점(차수!=2) %d" % (len(deg), len(junc)))

    # 호 추적: 접합점에서 출발해 차수 2 를 따라간다
    used = set()
    arcs = []
    for j in junc:
        for nb, pr in inc[j]:
            if (j, nb) in used:
                continue
            chain, prev, cur = [j], j, nb
            used.add((j, nb))
            used.add((nb, j))
            while cur not in junc:
                chain.append(cur)
                nxt = [n for n, _ in inc[cur] if n != prev][0]
                used.add((cur, nxt))
                used.add((nxt, cur))
                prev, cur = cur, nxt
            chain.append(cur)
            arcs.append((pr, chain))
    # 접합점이 없는 닫힌 고리 (판이 이웃 하나에 완전히 둘러싸인 경우)
    for k in inc:
        for nb, pr in inc[k]:
            if (k, nb) in used:
                continue
            chain, prev, cur = [k], k, nb
            used.add((k, nb)); used.add((nb, k))
            while cur != k:
                chain.append(cur)
                nxt = [n for n, _ in inc[cur] if n != prev][0]
                used.add((cur, nxt)); used.add((nxt, cur))
                prev, cur = cur, nxt
            chain.append(k)
            arcs.append((pr, chain))

    def smooth(ch):
        """크랙 경로는 가로·세로 금만 밟아서 계단이다. 사슬을 따라 가우스로 편다.
        **끝점(접합점)은 고정** — 거기가 이웃 호와 공유하는 정점이다."""
        if len(ch) < 5 or SMOOTH <= 0:
            return [(float(a), float(b)) for a, b in ch]
        A = np.array(ch, float)
        k = max(3, int(SMOOTH * 3) | 1)
        g = np.exp(-0.5 * ((np.arange(k) - k // 2) / SMOOTH) ** 2)
        g /= g.sum()
        pad = np.vstack([np.repeat(A[:1], k // 2, 0), A, np.repeat(A[-1:], k // 2, 0)])
        B = np.stack([np.convolve(pad[:, i], g, "valid") for i in (0, 1)], 1)
        B[0], B[-1] = A[0], A[-1]
        return [tuple(v) for v in B]

    w = lambda rc: [float(wc(rc[1] + x0 - 1.5)), float(wz(rc[0] + y0 - 1.5))]
    verts, key2i = [], {}

    def vid(rc):
        rc = (round(rc[0], 3), round(rc[1], 3))
        if rc not in key2i:
            key2i[rc] = len(verts)
            verts.append(w(rc))
        return key2i[rc]

    out = []
    for pr, ch0 in arcs:
        ch = smooth(ch0)
        body = ch[::STEP]
        if body[-1] != ch[-1]:
            body.append(ch[-1])
        seq = [vid(p) for p in body]
        seq = [seq[0]] + [v for i, v in enumerate(seq[1:], 1) if v != seq[i - 1]]
        if len(seq) >= 2:
            out.append(dict(pair=[int(pr[0]), int(pr[1])], v=seq))
    per = defaultdict(int)
    for a in out:
        for lab in a["pair"]:
            if lab in keep:
                per[lab] += 1
    print("호 %d개   공유 정점 %d개" % (len(out), len(verts)))
    print("판별 호 수: %s" % dict(sorted(per.items())))
    json.dump(dict(win=J["win"], verts=verts, arcs=out),
              open(os.path.join(HERE, "parts", "graph.json"), "w"))
    print("-> parts/graph.json")


if __name__ == "__main__":
    main()
