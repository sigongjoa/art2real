# -*- coding: utf-8 -*-
"""판 선을 패드에 **박을 수 있는 형태**로 준비한다.

    python lines.py     ->  parts/lines.json

graph.py 의 호(크랙 그래프)는 albedo 판 경계다. 그런데 그 바깥 테두리는 먹선을
안 품어서 캡 실루엣(cap_mask)보다 안쪽이다. 호를 그냥 넣으면 끝이 허공에 뜬다.

    outline    cap_mask 윤곽 (먹선 포함 — 79번). 이게 패드 테두리다
    arcs       판 사이 호만. **끝이 뜬 것은 진행 방향으로 윤곽까지 늘린다**
               -> 제약 삼각화가 닫힌 영역으로 받는다
"""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = 1024
wc = lambda c: -0.6 + c * 1.2 / (RES - 1)
wz = lambda r: 1.1 - r * 1.2 / (RES - 1)


def main():
    M = cv2.imread(os.path.join(HERE, "out", "cap_mask.png"), 0) > 127
    cnt = max(cv2.findContours(M.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0],
              key=cv2.contourArea).reshape(-1, 2)
    C = np.array([[wc(p[0]), wz(p[1])] for p in cnt])
    # 윤곽 재표본 (호 길이 균일)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([C, C[:1]]), axis=0), axis=1))]
    t = np.arange(0, d[-1], 0.0035)
    OUT = np.stack([np.interp(t, d, np.r_[C[:, 0], C[0, 0]]),
                    np.interp(t, d, np.r_[C[:, 1], C[0, 1]])], 1)
    # 마스크 윤곽은 화소 톱니가 있다. 닫힌 고리를 따라 가우스로 편다 (104번과 같은 이유)
    k = 11
    g = np.exp(-0.5 * ((np.arange(k) - k // 2) / 2.2) ** 2)
    g /= g.sum()
    OUT = np.stack([np.convolve(np.r_[OUT[-(k // 2):, i], OUT[:, i], OUT[:k // 2, i]], g, "valid")
                    for i in (0, 1)], 1)

    G = json.load(open(os.path.join(HERE, "parts", "graph.json")))
    P = {p["id"]: p for p in json.load(open(os.path.join(HERE, "parts", "panels.json")))["panels"]}
    V = np.array(G["verts"])
    inpoly = lambda p: cv2.pointPolygonTest(cnt.astype(np.int32),
                                            (float((p[0] + 0.6) / 1.2 * (RES - 1)),
                                             float((1.1 - p[1]) / 1.2 * (RES - 1))), True)

    arcs = []
    for a in G["arcs"]:
        labs = [l for l in a["pair"] if l in P]
        if len(labs) < 2:            # 배경과의 경계 = 바깥. 윤곽이 대신한다
            continue
        pts = V[a["v"]].tolist()
        # 끝이 캡 안쪽 깊숙이 떠 있으면 진행 방향으로 윤곽까지 늘린다
        for end in (0, -1):
            k = 1 if end == 0 else -2
            p = np.array(pts[end])
            q = np.array(pts[k])
            v = p - q
            n = np.linalg.norm(v)
            if n < 1e-6:
                continue
            v /= n
            if inpoly(p) > 0.004:                       # 윤곽에서 4mm 이상 안쪽 = 뜬 끝
                best = None
                for s in np.arange(0.002, 0.020, 0.001):   # 멀리 늘리면 얇은 삼각형(가시)이 된다
                    c = p + v * s
                    if inpoly(c) <= 0:
                        best = c
                        break
                if best is not None:
                    j = int(np.argmin(np.linalg.norm(OUT - best, axis=1)))
                    if np.linalg.norm(OUT[j] - best) < 0.010:   # 엉뚱한 데로 스냅하면 버린다
                        pts[end] = OUT[j].tolist()
        arcs.append([[float(x), float(z)] for x, z in pts])
    print("판 사이 호 %d개   윤곽 정점 %d개" % (len(arcs), len(OUT)))
    json.dump(dict(outline=[[float(x), float(z)] for x, z in OUT], arcs=arcs),
              open(os.path.join(HERE, "parts", "lines.json"), "w"))
    print("-> parts/lines.json")


if __name__ == "__main__":
    main()
