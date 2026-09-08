# -*- coding: utf-8 -*-
"""선의 **원인 네 가지**를 따로 검출하고, 하나씩 넣으면서 깊이 솔브를 재본다.

    python causes.py

문헌(Waltz 1975 / Malik 1987)이 쓰는 분류다. 선 하나의 원인은 넷이고 셋을 지우면 안 된다.

    깊이 불연속    가림(occluding) · 림(limb)      획이 굵다
    방향 불연속    볼록(convex) · 오목(concave)    나머지 — 여기가 형태다
    조명 불연속    그림자(shadow)                  같은 재질, 밝기만 다르다
    반사율 불연속  재질 경계                       색상이 다르다

판정 자는 **hold-out 상관**이다 — 측면 원화는 솔브에 안 쓰므로 정직한 시험이다(66번).
"""
import json
import os
from collections import defaultdict

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
T4 = os.path.join(HERE, "..", "trail4_gen3d")
RES = 1024
cc = lambda u: (u + 0.6) / 1.2 * (RES - 1)
rr = lambda z: (1.1 - z) / 1.2 * (RES - 1)
z_of = lambda r: 1.1 - r * 1.2 / (RES - 1)
CUT_TH = 4.0          # 획 두께 임계 (px). 접힘 2.0~3.4 vs 가림 4.0~7.8 로 갈렸다
A0 = {"lav": 205., "gold": 235., "white": 250., "dark": 95.}


def load():
    raw = np.load(os.path.join(T4, "rgb_front.npy"))
    rgb = raw[..., :3].astype(np.uint8)
    sil = raw[..., 3] > 0
    y0, y1 = int(rr(0.985)), int(rr(0.775))
    x0, x1 = int(cc(0.118)), int(cc(0.252))
    return rgb[y0:y1, x0:x1], sil[y0:y1, x0:x1], y0


def hue_class(mc):
    r, g, b = mc
    if r - b > 20 and r - g < 60:
        return "gold"
    if b - r > 8:
        return "lav"
    return "white" if mc.min() > 170 else "dark"


def build(C, S):
    L = np.load(os.path.join(HERE, "out", "_L.npy"))
    ids = sorted([v for v in np.unique(L) if v > 1])
    ren = {v: i for i, v in enumerate(ids)}
    P = len(ids)
    kind, tone, col = {}, np.zeros(P), {}
    for v in ids:
        i = ren[v]
        m = L == v
        mc = C[m].mean(0)
        kind[i] = hue_class(mc)
        tone[i] = mc.max()
        col[i] = mc
    H, W = L.shape
    adj = defaultdict(list)
    for dy, dx in ((0, 1), (1, 0)):
        a = L[:H - dy, :W - dx]
        b = L[dy:, dx:]
        m = (a > 1) & (b > 1) & (a != b)
        ys, xs = np.nonzero(m)
        for yy, xx in zip(ys, xs):
            i, j = ren[int(a[yy, xx])], ren[int(b[yy, xx])]
            adj[(min(i, j), max(i, j))].append((xx + 0.5 * dx, yy + 0.5 * dy))
    edges = {k: np.array(v, float) for k, v in adj.items() if len(v) >= 8}
    return L, ids, ren, P, kind, tone, col, edges


def classify(edges, kind, tone, col):
    """원인 넷으로 가른다. 순서가 중요하다 — 재질이 먼저, 그다음 가림, 그다음 그림자."""
    eth = {(int(a), int(b)): t for a, b, t in np.load(os.path.join(HERE, "out", "_edgeth.npy"))}
    out = {}
    for (i, j) in edges:
        th = eth.get((i, j), 0.0)
        if kind[i] != kind[j]:
            out[(i, j)] = "material"          # 반사율 불연속
        elif th >= CUT_TH:
            out[(i, j)] = "occlude"           # 깊이 불연속 — 획이 굵다
        else:
            # 같은 재질 · 가는 획. 밝기비가 셀의 명/암 쌍이면 조명, 아니면 방향
            lo, hi = sorted([tone[i], tone[j]])
            ratio = lo / max(hi, 1e-6)
            out[(i, j)] = "shadow" if 0.45 <= ratio <= 0.82 else "fold"
    return out


def merge_shadow(P, cls):
    """그림자 경계는 **같은 면**이다. 두 판을 합친다."""
    par = {}
    def find(x):
        while par.get(x, x) != x:
            x = par[x]
        return x
    for (i, j), c in cls.items():
        if c == "shadow":
            a, b = find(i), find(j)
            if a != b:
                par[b] = a
    mp, nxt, grp = {}, 0, {}
    for k in range(P):
        r = find(k)
        if r not in mp:
            mp[r] = nxt
            nxt += 1
        grp[k] = mp[r]
    return grp, nxt


def silhouette_normals(L, S):
    """실루엣에 닿은 판마다 안쪽 법선과 접촉 길이. Lumo 의 아이디어 —
    실루엣에서는 표면이 시선과 나란하니 그 판은 가파르게 기울어야 한다."""
    out = defaultdict(lambda: [np.zeros(2), 0])
    er = cv2.erode(S.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    bd = S & ~er
    dt = cv2.distanceTransform(S.astype(np.uint8), cv2.DIST_L2, 5)
    gy, gx = np.gradient(dt)
    ys, xs = np.nonzero(bd)
    for y, x in zip(ys, xs):
        v = int(L[y, x])
        if v <= 1:
            continue
        n = np.array([gx[y, x], gy[y, x]])
        nn = np.linalg.norm(n)
        if nn < 1e-6:
            continue
        out[v][0] += n / nn
        out[v][1] += 1
    return out


def main():
    C, S, y0 = load()
    L, ids, ren, P, kind, tone, col, edges = build(C, S)
    cls = classify(edges, kind, tone, col)
    n = defaultdict(int)
    for c in cls.values():
        n[c] += 1
    print("선의 원인별 경계 수 (전체 %d)" % len(edges))
    for c in ("material", "occlude", "shadow", "fold"):
        print("   %-9s %3d" % (c, n[c]))

    H, W = L.shape
    sx, sy, sc = W / 2, H / 2, max(W, H) / 2.
    lam = np.clip(np.array([tone[i] / A0[kind[i]] for i in range(P)]), 0.05, 1.0)
    sil_n = silhouette_normals(L, S)

    spec = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
    sp = [tuple(p) for p in spec["side"]["poly_yz"]]

    def span(zv):
        h = []
        for k in range(len(sp)):
            (a0, b0), (a1, b1) = sp[k], sp[(k + 1) % len(sp)]
            if (b0 - zv) * (b1 - zv) > 0 or b0 == b1:
                continue
            h.append(a0 + (a1 - a0) * (zv - b0) / (b1 - b0))
        return (min(h), max(h)) if len(h) >= 2 else None

    def solve(drop, grp, ngrp, use_sil, wsh=0.6, wsil=0.8, ssil=0.9):
        rows, rhs = [], []
        for (i, j), pts in edges.items():
            if cls[(i, j)] in drop:
                continue
            gi, gj = grp[i], grp[j]
            if gi == gj:
                continue
            q = pts[np.linspace(0, len(pts) - 1, min(len(pts), 24)).astype(int)]
            for (px, py) in q:
                X, Y = (px - sx) / sc, (py - sy) / sc
                r = np.zeros(3 * ngrp)
                r[3 * gi:3 * gi + 3] = [X, Y, 1]
                r[3 * gj:3 * gj + 3] = [-X, -Y, -1]
                rows.append(r); rhs.append(0.)
        for g in range(ngrp):
            mem = [i for i in range(P) if grp[i] == g]
            lm = float(np.mean([lam[i] for i in mem]))
            r = np.zeros(3 * ngrp)
            r[3 * g] = -1.0
            rows.append(wsh * r); rhs.append(wsh * (lm - 1.0) * 0.0)   # placeholder, 아래서 빛으로 대체
        rows = rows[:-ngrp]; rhs = rhs[:-ngrp]
        return rows, rhs

    def run(drop, use_sil, tag):
        grp, ngrp = merge_shadow(P, cls) if "shadow" in drop else ({k: k for k in range(P)}, P)
        best = None
        for lz in (0.7, 0.85):
            for th in np.arange(0, 2 * np.pi, np.pi / 6):
                s = np.sqrt(max(1 - lz * lz, 1e-6))
                l = np.array([s * np.cos(th), s * np.sin(th), lz])
                rows, rhs = [], []
                for (i, j), pts in edges.items():
                    if cls[(i, j)] in drop:
                        continue
                    gi, gj = grp[i], grp[j]
                    if gi == gj:
                        continue
                    q = pts[np.linspace(0, len(pts) - 1, min(len(pts), 24)).astype(int)]
                    for (px, py) in q:
                        X, Y = (px - sx) / sc, (py - sy) / sc
                        r = np.zeros(3 * ngrp)
                        r[3 * gi:3 * gi + 3] = [X, Y, 1]
                        r[3 * gj:3 * gj + 3] = [-X, -Y, -1]
                        rows.append(r); rhs.append(0.)
                for g in range(ngrp):
                    mem = [i for i in range(P) if grp[i] == g]
                    lm = float(np.mean([lam[i] for i in mem]))
                    r = np.zeros(3 * ngrp)
                    r[3 * g] = -l[0]; r[3 * g + 1] = -l[1]
                    rows.append(0.6 * r); rhs.append(0.6 * (lm - l[2]))
                if use_sil:
                    for v, (acc, cnt) in sil_n.items():
                        if cnt < 6:
                            continue
                        g = grp[ren[v]]
                        nrm = acc / max(np.linalg.norm(acc), 1e-9)
                        for d in (0, 1):
                            r = np.zeros(3 * ngrp)
                            r[3 * g + d] = 1.0
                            rows.append(0.8 * r); rhs.append(0.8 * (-0.9 * nrm[d]))
                r = np.zeros(3 * ngrp); r[2] = 1.
                rows.append(10 * r); rhs.append(0.)
                A = np.array(rows); bv = np.array(rhs)
                p, _, rank, _ = np.linalg.lstsq(A, bv, rcond=None)
                rms = float(np.sqrt(((A @ p - bv) ** 2).mean()))
                if best is None or rms < best[0]:
                    best = (rms, p, rank, A.shape[0], l, ngrp, grp)
        rms, p, rank, meq, l, ngrp, grp = best
        a, b, c = p[0::3], p[1::3], p[2::3]
        Xg, Yg = np.meshgrid((np.arange(W) - sx) / sc, (np.arange(H) - sy) / sc)
        Z = np.full((H, W), np.nan)
        for v in ids:
            g = grp[ren[v]]
            m = L == v
            Z[m] = a[g] * Xg[m] + b[g] * Yg[m] + c[g]
        fin = np.isfinite(Z)
        A2 = []
        for r_ in range(0, H, 3):
            m = fin[r_] & S[r_]
            if m.sum() < 8:
                continue
            s2 = span(z_of(r_ + y0))
            if s2 is None:
                continue
            zz = Z[r_][m]
            A2.append((zz.max() - zz.min(), s2[1] - s2[0]))
        A2 = np.array(A2)
        corr = float(np.corrcoef(A2[:, 0], A2[:, 1])[0, 1]) if len(A2) > 4 else float("nan")
        print("%-38s 판 %2d  식 %4d  rank %3d/%3d  rms %.4f   hold-out r = %+.3f"
              % (tag, ngrp, meq, rank, 3 * ngrp, rms, corr))
        return corr, Z

    print()
    print("한 단계씩 넣으며 hold-out 상관을 본다 (측면 원화는 솔브에 안 쓴다)")
    run(set(), False, "S0  아무것도 안 가름")
    run({"material"}, False, "S1  + 반사율 경계 제외")
    run({"material", "shadow"}, False, "S2  + 조명(그림자) 판 병합")
    run({"material", "shadow", "occlude"}, False, "S3  + 깊이(가림) 연속 해제")
    corr, Z = run({"material", "shadow", "occlude"}, True, "S4  + 실루엣 법선 (Lumo)")
    np.save(os.path.join(HERE, "out", "_Z4.npy"), Z)


if __name__ == "__main__":
    main()
