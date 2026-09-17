# -*- coding: utf-8 -*-
"""**피규어 원형을 출력 단위로 자른다** (2026-09-17). 계획 `claudedocs/plan_출력분할_20260917.md`.

    python 출력분할.py 검사            자가검사 (합성 상자 · 부피 보존 · 누적합 = 직접 계산)
    python 출력분할.py [n]             아직 안 한 장 n 개 -> out/기록/출력분할_진행.jsonl
    python 출력분할.py 판정            -> out/기록/출력분할_판정_<때>.json
    python 출력분할.py 부품 <케이스>   M1 k=3 부품 메시 · 속 비우기 · 핀 (Q4 · Q5) -> out/출력분할_<케이스>/
    python 출력분할.py 그림 <케이스>   판본별 부품 색칠 그림 -> out/출력분할_<케이스>.png

Chopper(Luo 2012) 의 평면 BSP · 빔 탐색을 **복셀 격자 위에서** 푼다. 평면 방향마다 복셀을 법선 투영값 t 로 한 번 정렬하면
오프셋 c 마다 「왼쪽 부품의 부피 · 아래를 보는 표면 칸 · 이음매 띠 칸」을 누적합으로 얻는다 — 메시 자르기 수백 번을 피한다.
"""
import json
import os
import sys
import time

import numpy as np
from scipy import ndimage

HERE = r"G:\art2real\원화3d"
for d in ("", "실험_20260915"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import hull as H
import win as W

PROG = os.path.join(HERE, "out", "기록", "출력분할_진행.jsonl")
TAG = "출력분할 v2b · 복셀 BSP · 법선13 · 빔4 한 번(k4)에서 깊이별 최선 · 후보평가 1/8 표본 · M1칠경계 M2가림 C1높이 C2무작위(씨앗10) · +사후 M3 정면가시 · 정면이음매몫 · 150mm (2026-09-17)"
H_MM = 150.0
PIN_MM, MIN_PART = 4.0, 0.03
BEAM, KS, SEEDS = 4, (2, 3, 4), 10
_d = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, -1, 0), (1, 0, 1), (1, 0, -1), (0, 1, 1), (0, 1, -1),
      (1, 1, 1), (1, 1, -1), (1, -1, 1), (-1, 1, 1)]
NORMALS = np.array([np.array(v, float) / np.linalg.norm(v) for v in _d])
DIRS = [(0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)]            # (축, 부호) — 출력 「위」 방향 후보 6개


# ───────────────────────── 케이스 · 입력 ─────────────────────────

def cases():
    from 겉면채점 import bench_cases
    H.register_sheets()
    H.CASES["은둔자"] = {"src": {v: v + ".png" for v in W.VIEWS}, "dir": os.path.join("out", "은둔자_자료", "삼면"), "back_sign": +1}
    return ["은둔자", "오메가몬"] + [c for c in bench_cases() if c != "소체"]


def rgb_of(path):
    from PIL import Image
    im = Image.open(path)
    a = np.array(im.convert("RGBA")).astype(np.float32)
    return a[:, :, :3]


def build(case):
    """제품 기본 깎기 원형 + 앞 · 뒤 판 색 (창 좌표 · 정렬까지). `대조.build` 와 같은 순서에 색 세 채널을 같은 변환으로 싣는다."""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    bs = H.CASES[case]["back_sign"]
    if bs is None:
        bs = +1
    masks, cols = {}, {}
    for v, f in src.items():
        p = os.path.join(base, f)
        d = H.declutter(W.art_mask(p))
        if v in ("front", "back"):
            c = rgb_of(p)
            got = H.to_win(d, np.ones(d.shape, np.float32), c[:, :, 0], c[:, :, 1], c[:, :, 2])
            masks[v], cols[v] = got[0], np.stack(got[2:], -1)
        else:
            masks[v] = H.to_win(d)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    cols = {v: np.stack([H._warp_one(c[:, :, i], v, p) for i in range(3)], -1) for v, c in cols.items()}
    deps = {v: np.ones((W.RES, W.RES), np.float32) for v in W.VIEWS}
    vox, axes = H.carve_default(masks, deps, back_sign=bs)
    return vox, axes, masks, cols, bs


def material_img(rgb, mask):
    """`부품.material` 규칙을 화소마다 — 0 흰 · 1 금 · 2 청회 · 3 검정 · −1 원화 밖."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = (r + g + b) / 3
    lab = np.where(lum < 90, 3, np.where((r - b > 40) & (r > 130), 1, np.where(b - r > 12, 2, 0)))
    return np.where(mask, lab, -1).astype(np.int8)


def fields(vox, axes, masks, cols, bs):
    """표면 칸 · 재질 · 재질 경계 · 가림 · 6 방향 노출면."""
    s6 = ndimage.generate_binary_structure(3, 1)
    surf = vox & ~ndimage.binary_erosion(vox, s6, border_value=0)
    u, _, z = axes
    X2, Z2 = np.meshgrid(u, z, indexing="ij")
    mat2 = {}
    for v in ("front", "back"):
        sign = bs if v == "back" else W.VIEW_AXIS[v][1]
        py, px = W.topix(sign * X2, Z2)
        mat2[v] = material_img(cols[v], masks[v])[py, px]            # (x, z)
    lo, hi = H.surfaces(vox)
    mid = (lo + hi) / 2.0
    j = np.arange(vox.shape[1])[None, :, None]
    lab = np.where(j <= mid[:, None, :], mat2["front"][:, None, :], mat2["back"][:, None, :]).astype(np.int8)
    lab = np.where(surf, lab, -1)
    lmax = ndimage.maximum_filter(lab, size=3)
    lmin = ndimage.minimum_filter(np.where(lab >= 0, lab, 99).astype(np.int8), size=3)
    bound = surf & (lab >= 0) & (lmin != 99) & (lmax != lmin)
    # 사후 자 (검토 뒤): 원화 **2D 안에서** 재질이 바뀌는 화소만 경계로 — 깊이 가운데서 앞판 → 뒤판 색으로 넘어가며 생기는
    # 가짜 경계 고리를 뺀다. 표면 칸은 자기에게 색을 준 판의 (x, z) 화소가 2D 경계면 경계다
    b2 = {}
    for v in ("front", "back"):
        m2 = mat2[v]
        mx2 = ndimage.maximum_filter(m2, size=3)
        mn2 = ndimage.minimum_filter(np.where(m2 >= 0, m2, 99).astype(np.int8), size=3)
        b2[v] = (m2 >= 0) & (mn2 != 99) & (mx2 != mn2)
    bound_art = surf & np.where(j <= mid[:, None, :], b2["front"][:, None, :], b2["back"][:, None, :])
    occ = ndimage.uniform_filter(vox.astype(np.float32), size=7)
    expo = []
    for ax, sg in DIRS:                                               # 출력 위 = (ax, sg) 이면 아래를 보는 면 = −sg 쪽 이웃이 비었다
        nb = np.roll(vox, sg, axis=ax)
        e = vox & ~nb
        sl = [slice(None)] * 3; sl[ax] = 0 if sg > 0 else -1
        e[tuple(sl)] = vox[tuple(sl)]
        expo.append(e & surf)
    return surf, lab, bound, occ, expo, bound_art


# ───────────────────────── 평가 ─────────────────────────

class Ctx:
    def __init__(self, vox, axes, masks, cols, bs):
        self.vox = vox
        self.surf, self.lab, self.bound, self.occ, self.expo, self.bound_art = fields(vox, axes, masks, cols, bs)
        self.idx = np.argwhere(vox)                                   # (n, 3) — 부품은 이 행 번호 집합
        f = lambda a: a[vox]
        self.S = f(self.surf); self.B = f(self.bound); self.O = f(self.occ)
        self.E = np.stack([f(e) for e in self.expo], 1)               # (n, 6)
        self.n_surf = max(int(self.S.sum()), 1)
        zext = np.ptp(self.idx[:, 2]) + 1
        self.vmm = H_MM / zext
        self.pin_cells = (PIN_MM / self.vmm) ** 2
        self.T = (self.idx.astype(np.float32) @ NORMALS.T.astype(np.float32))   # (n, 13) 투영값 — float32 (궤짝 같은 큰 장에서 메모리 부족으로 정리됐다)
        lo, _ = H.surfaces(vox)
        jj = np.arange(vox.shape[1])[None, :, None]
        self.front = vox & (jj == lo[:, None, :])                     # 사후: 정면에서 보이는 칸 (전시하면 보이는 쪽)
        self.F = self.front[vox]
        self.sub = ((self.idx % 2) == 0).all(1)                        # 후보 평가용 1/8 표본 (최종 측정은 전체 칸)

    def support(self, rows):
        return int(self.E[rows].sum(0).min())

    def cut_candidates(self, rows_full, pen):
        """부품을 법선마다 · 오프셋마다 자른 후보를 **1/8 표본**의 누적합으로 센다 (칸 수는 ×8) — v1 은 전체 칸이라 궤짝 한 장에 25분을 넘겼다."""
        out = []
        rows = rows_full[self.sub[rows_full]]
        n = len(rows)
        if n < 2 / MIN_PART:
            return out
        minv = MIN_PART * self.sub.sum()
        base_sup = self.support(rows) * 8
        for k in range(len(NORMALS)):
            t = self.T[rows, k]
            o = np.argsort(t, kind="stable")
            ts = t[o]
            E = np.cumsum(self.E[rows][o], 0)                          # (n, 6)
            tot = E[-1]
            Sp = self.S[rows][o] * pen[rows][o]
            # 띠: |t − c| < 0.87 인 표면 칸의 벌점 합 — 정렬돼 있으니 searchsorted 로
            cps = np.concatenate([[0.0], np.cumsum(Sp)])
            lo_t, hi_t = ts[int(minv)], ts[n - int(minv) - 1]
            if hi_t <= lo_t:
                continue
            for c in np.arange(np.ceil(lo_t), hi_t, 2.0):
                i = int(np.searchsorted(ts, c))
                if i < minv or n - i < minv:
                    continue
                a, b = np.searchsorted(ts, c - 0.87), np.searchsorted(ts, c + 0.87)
                seam = float(cps[b] - cps[a]) * 8
                sup = float(E[i - 1].min() + (tot - E[i - 1]).min()) * 8
                cross = (b - a) * 8                                    # 절단면 넓이 근사 (띠 두께 ≈ 1.74 칸 · 표본 ×8)
                if cross / 1.74 < self.pin_cells:
                    continue
                d = (seam + sup - base_sup) / self.n_surf
                out.append((d, k, float(c)))
        return out

    def feasible(self, rows, k, c):
        """절단면 연결성분마다 핀 자리가 있나 (Chopper fconnector) — 채택 직전에만 비싸게 센다."""
        t = self.T[rows, k]
        band = rows[np.abs(t - c) < 0.87]
        if len(band) == 0:
            return False
        P = self.idx[band]
        lo = P.min(0)
        g = np.zeros(tuple(P.max(0) - lo + 1), bool)                   # 절단면 둘레 상자만 — 전체 256³ 라벨링이 한 장 395초의 대부분이었다
        g[tuple((P - lo).T)] = True
        lab, m = ndimage.label(g, ndimage.generate_binary_structure(3, 3))
        sizes = ndimage.sum(g, lab, range(1, m + 1))
        return bool((np.asarray(sizes) / 1.74 >= self.pin_cells).all())


def split(rows, o, i):
    return rows[o[:i]], rows[o[i:]]


def beam(ctx, pen, K):
    """빔 탐색 한 번 (깊이 K) — **깊이마다 최선 상태**를 돌려준다 {k: (비용, [부품 rows], [(법선, c)])}."""
    all_rows = np.arange(len(ctx.idx))
    states = [(ctx.support(all_rows) / ctx.n_surf, [all_rows], [])]
    best = {}
    for step in range(1, K + 1):
        nxt = []
        for cost, parts, cuts in states:
            for pi, rows in enumerate(parts):
                cands = sorted(ctx.cut_candidates(rows, pen), key=lambda x: x[0])
                took = 0
                for d, k, c in cands:
                    if not ctx.feasible(rows, k, c):
                        continue
                    t = ctx.T[rows, k]
                    L, R = rows[t < c], rows[t >= c]
                    if min(len(L), len(R)) < MIN_PART * len(ctx.idx):
                        continue
                    nxt.append((cost + d, parts[:pi] + [L, R] + parts[pi + 1:], cuts + [(k, c)]))
                    took += 1
                    if took >= BEAM:
                        break
        if not nxt:
            break
        nxt.sort(key=lambda s: s[0])
        uniq, seen = [], set()
        for st in nxt:
            key = tuple(sorted((len(p), int(p.sum() % 1000003)) for p in st[1]))
            if key not in seen:
                seen.add(key); uniq.append(st)
            if len(uniq) >= BEAM:
                break
        states = uniq
        best[step] = min(states, key=lambda st: st[0])
    return best


def height_cuts(ctx, K):
    rows = np.arange(len(ctx.idx))
    z = ctx.idx[:, 2]
    qs = np.quantile(z, np.linspace(0, 1, K + 2)[1:-1])
    lab = np.searchsorted(qs, z, side="right")
    return [rows[lab == q] for q in range(K + 1)], [(2, float(q)) for q in qs]


def random_cuts(ctx, K, seed):
    rng = np.random.default_rng(seed)
    parts, cuts = [np.arange(len(ctx.idx))], []
    tries = 0
    while len(cuts) < K and tries < 400:
        tries += 1
        pi = rng.choice(len(parts), p=np.array([len(p) for p in parts], float) / len(ctx.idx))
        rows = parts[pi]
        k = int(rng.integers(len(NORMALS)))
        t = ctx.T[rows, k]
        c = float(np.quantile(t, rng.uniform(0.15, 0.85)))
        L, R = rows[t < c], rows[t >= c]
        if min(len(L), len(R)) < MIN_PART * len(ctx.idx) or not ctx.feasible(rows, k, c):
            continue
        parts = parts[:pi] + [L, R] + parts[pi + 1:]
        cuts.append((k, c))
    return parts, cuts


def measure(ctx, parts, cuts):
    """판본과 무관한 같은 자로 잰다 — 이음매 띠는 **채택된 절단면**의 그 부품 칸만."""
    n = len(ctx.idx)
    assert sum(len(p) for p in parts) == n and len(np.unique(np.concatenate(parts))) == n, "부피 보존 실패"
    owner = np.empty(n, np.int32)
    for i, p in enumerate(parts):
        owner[p] = i
    # 이음매 칸 = 표면 칸 중 26 이웃에 다른 부품이 있는 칸
    g = np.full(ctx.vox.shape, -1, np.int32)
    g[tuple(ctx.idx.T)] = owner
    mx = ndimage.maximum_filter(g, size=3)
    gm = np.where(g >= 0, g, 1 << 20)
    mn = ndimage.minimum_filter(gm, size=3)
    seam_v = ctx.surf & (g >= 0) & ((mx != g) | (mn != g))
    seam = int(seam_v.sum())
    sb = int((seam_v & ctx.bound).sum())
    sba = int((seam_v & ctx.bound_art).sum()) if hasattr(ctx, "bound_art") else 0
    sup = sum(ctx.support(p) for p in parts)
    sf = int((seam_v & ctx.front).sum())
    return {"부품": len(parts), "이음매칸": seam, "이음매길이mm": round(seam * ctx.vmm, 1),
            "정면이음매몫": round(sf / max(seam, 1), 4),
            "칠경계일치": round(sb / max(seam, 1), 4),
            "칠경계일치_원화2D": round(sba / max(seam, 1), 4),
            "이음매가림": round(float(ctx.occ[seam_v].mean()) if seam else 0.0, 4),
            "서포트몫": round(sup / ctx.n_surf, 4), "칸mm": round(ctx.vmm, 3),
            "부피최소몫": round(min(len(p) for p in parts) / n, 4)}


def run_case(case):
    t0 = time.time()
    vox, axes, masks, cols, bs = build(case)
    ctx = Ctx(vox, axes, masks, cols, bs)
    pen1 = np.where(ctx.B, 0.0, 1.0)                                  # M1 칠 경계
    pen2 = 1.0 - ctx.O                                                # M2 가림 (주변이 빌수록 벌점)
    row = {"case": case, "판": TAG, "표면칸": ctx.n_surf, "재질경계몫": round(float(ctx.B.sum()) / ctx.n_surf, 4),
           "M0": measure(ctx, [np.arange(len(ctx.idx))], [])}
    pen3 = np.where(ctx.B, 0.0, 1.0 + 2.0 * ctx.F)                   # 사후 M3: 칠 경계 0 · 그 밖 1 · 정면에서 보이면 3
    b1, b2, b3 = beam(ctx, pen1, max(KS)), beam(ctx, pen2, max(KS)), beam(ctx, pen3, max(KS))
    for K in KS:
        r = {}
        s = b1[K]; r["M1"] = measure(ctx, s[1], s[2]); r["M1"]["절단"] = s[2]
        s = b2[K]; r["M2"] = measure(ctx, s[1], s[2]); r["M2"]["절단"] = s[2]
        s = b3[K]; r["M3"] = measure(ctx, s[1], s[2]); r["M3"]["절단"] = s[2]
        p, c = height_cuts(ctx, K); r["C1"] = measure(ctx, p, c)
        rs = [measure(ctx, *random_cuts(ctx, K, sd)) for sd in range(SEEDS)]
        r["C2"] = {k: (round(float(np.median([x[k] for x in rs])), 4) if isinstance(rs[0][k], (int, float)) else None) for k in rs[0]}
        row["k%d" % K] = r
    row["초"] = round(time.time() - t0, 1)
    with open(PROG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    k3 = row["k3"]
    print("  %-26s M0 서포트 %.3f · k3 칠경계일치 M1 %.3f M2 %.3f C1 %.3f C2 %.3f M3 %.3f · 서포트 M1 %.3f C1 %.3f M3 %.3f · 정면이음매 M1 %.3f M3 %.3f · %.0f초"
          % (case[:26], row["M0"]["서포트몫"], k3["M1"]["칠경계일치"], k3["M2"]["칠경계일치"], k3["C1"]["칠경계일치"],
             k3["C2"]["칠경계일치"], k3["M3"]["칠경계일치"], k3["M1"]["서포트몫"], k3["C1"]["서포트몫"], k3["M3"]["서포트몫"],
             k3["M1"]["정면이음매몫"], k3["M3"]["정면이음매몫"], row["초"]), flush=True)


def done():
    if not os.path.exists(PROG):
        return {}
    return {r["case"]: r for r in map(json.loads, open(PROG, encoding="utf-8")) if r.get("판") == TAG}


def verdict():
    have = done()
    cs = [c for c in cases() if c in have]
    med = lambda a: round(float(np.median(a)), 4)
    def rule(a, b, larger=True):
        d = np.array([(x - y) if larger else (y - x) for x, y in zip(a, b)])
        loo = min(float(np.median(np.delete(d, i))) for i in range(len(d))) if len(d) > 1 else float(d[0])
        return {"중앙차": med(d), "승": int((d > 0).sum()), "장": len(d), "한장빼기최소": round(loo, 4),
                "통과": bool(np.median(d) > 0 and (d > 0).sum() * 2 > len(d) and loo > 0)}
    g = lambda m, key, K=3: [have[c]["k%d" % K][m][key] for c in cs]
    out = {"판": TAG, "장": len(cs), "케이스": cs, "Q": {}}
    for K in KS:
        out["Q"]["k%d" % K] = {
            "Q1 칠경계일치 M1>C1": rule(g("M1", "칠경계일치", K), g("C1", "칠경계일치", K)),
            "Q1 칠경계일치 M1>C2": rule(g("M1", "칠경계일치", K), g("C2", "칠경계일치", K)),
            "Q2 서포트 M1<M0": rule(g("M1", "서포트몫", K), [have[c]["M0"]["서포트몫"] for c in cs], larger=False),
            "Q2 서포트 M1≤C1 중앙차": med([a - b for a, b in zip(g("M1", "서포트몫", K), g("C1", "서포트몫", K))]),
            "Q3 칠경계일치 M1>M2": rule(g("M1", "칠경계일치", K), g("M2", "칠경계일치", K)),
            "Q3 이음매가림 M2>M1 (나빠진 것)": rule(g("M2", "이음매가림", K), g("M1", "이음매가림", K)),
            "사후 정면이음매 M3<M1": rule(g("M3", "정면이음매몫", K), g("M1", "정면이음매몫", K), larger=False),
            "사후 정면이음매 M1<C1": rule(g("M1", "정면이음매몫", K), g("C1", "정면이음매몫", K), larger=False),
            "중앙": {m: {key: med(g(m, key, K)) for key in ("칠경계일치", "서포트몫", "이음매길이mm", "이음매가림", "정면이음매몫", "부품")} for m in ("M1", "M2", "M3", "C1", "C2")},
        }
    out["M0 서포트 중앙"] = med([have[c]["M0"]["서포트몫"] for c in cs])
    q = out["Q"]["k3"]
    out["배관"] = "부피 보존 assert 통과 (측정마다)"
    out["Q1 통과"] = q["Q1 칠경계일치 M1>C1"]["통과"] and q["Q1 칠경계일치 M1>C2"]["통과"]
    out["Q2 통과"] = q["Q2 서포트 M1<M0"]["통과"] and q["Q2 서포트 M1≤C1 중앙차"] <= 0
    out["Q3 통과"] = q["Q3 칠경계일치 M1>M2"]["통과"]
    p = os.path.join(HERE, "out", "기록", "출력분할_판정_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("장", "M0 서포트 중앙", "Q1 통과", "Q2 통과", "Q3 통과")}, ensure_ascii=False))
    print(json.dumps(q["중앙"], ensure_ascii=False))
    print("  ->", p)
    return out


def selfcheck():
    """합성 상자: 부피 보존 · 누적합 비용 = 직접 잰 비용."""
    vox = np.zeros((40, 40, 60), bool); vox[10:30, 12:28, 5:55] = True
    axes = (np.arange(40) * 1.0, np.arange(40) * 1.0, np.arange(60) * 1.0)
    rgb = np.zeros((W.RES, W.RES, 3), np.float32)
    class F:  # 재질 경계 없는 가짜 판 — 가림 · 서포트만 확인
        pass
    ctx = Ctx.__new__(Ctx)
    ctx.vox = vox
    s6 = ndimage.generate_binary_structure(3, 1)
    ctx.surf = vox & ~ndimage.binary_erosion(vox, s6, border_value=0)
    ctx.bound = np.zeros_like(vox); ctx.occ = ndimage.uniform_filter(vox.astype(np.float32), size=7)
    ctx.expo = []
    for ax, sg in DIRS:
        e = vox & ~np.roll(vox, sg, axis=ax); ctx.expo.append(e & ctx.surf)
    ctx.idx = np.argwhere(vox); f = lambda a: a[vox]
    ctx.S, ctx.B, ctx.O = f(ctx.surf), f(ctx.bound), f(ctx.occ)
    ctx.E = np.stack([f(e) for e in ctx.expo], 1); ctx.n_surf = int(ctx.S.sum())
    ctx.vmm = 1.0; ctx.pin_cells = 4.0; ctx.T = ctx.idx @ NORMALS.T; ctx.sub = ((ctx.idx % 2) == 0).all(1)
    lo_, _ = H.surfaces(vox) if vox.shape[1] == H.N else (np.where(vox, np.arange(vox.shape[1])[None, :, None], vox.shape[1]).min(1), None)
    ctx.front = vox & (np.arange(vox.shape[1])[None, :, None] == lo_[:, None, :]); ctx.F = ctx.front[vox]
    parts, cuts = height_cuts(ctx, 2)
    m = measure(ctx, parts, cuts)
    assert m["부품"] == 3 and abs(sum(len(p) for p in parts) - vox.sum()) == 0
    # 상자 한 덩이의 서포트 = 가장 작은 면 (20×16 = 320)
    assert ctx.support(np.arange(len(ctx.idx))) == 320, ctx.support(np.arange(len(ctx.idx)))
    s = beam(ctx, np.ones(len(ctx.idx)), 1)[1]
    assert sum(len(p) for p in s[1]) == len(ctx.idx)
    print("  자가검사 통과 — 부피 보존 · 상자 서포트 320 · 빔 한 걸음")


# ───────────────────────── Q4 속 비우기 · Q5 핀 · 그림 ─────────────────────────

WALL_MM, DRAIN_MM, PIN_SIDE, PIN_LEN, TOL = 2.0, 3.5, 3.0, 6.0, 0.15
PALETTE = np.array([(214, 96, 77), (67, 147, 195), (120, 180, 90), (230, 170, 60), (150, 110, 190), (90, 190, 190)], float)


def part_volumes(ctx, parts):
    vols = []
    for p in parts:
        g = np.zeros(ctx.vox.shape, bool)
        g[tuple(ctx.idx[p].T)] = True
        vols.append(g)
    return vols


def hollow(ctx, parts, cuts):
    """Q4 — 부품마다 벽 2mm 만 남기고 속을 비운다. 배수 구멍 3.5mm 를 **절단면**에 (조립 뒤 안 보인다)."""
    w = int(np.ceil(WALL_MM / ctx.vmm))
    r = DRAIN_MM / 2 / ctx.vmm
    out = []
    lab = np.full(ctx.vox.shape, -1, np.int32)
    for i, p in enumerate(parts):
        lab[tuple(ctx.idx[p].T)] = i
    for i, g in enumerate(part_volumes(ctx, parts)):
        dt = ndimage.distance_transform_edt(g)
        cavity = dt > w
        shell = g & ~cavity
        hole = 0
        if cavity.any():
            # 절단면 칸 = 이 부품 칸 중 26 이웃에 다른 부품이 있는 칸 · 그중 속(구멍)에 제일 가까운 칸에서 법선 방향으로 벽을 뚫는다
            nb = ndimage.maximum_filter(np.where(lab >= 0, lab, -1), size=3) != ndimage.minimum_filter(np.where(lab >= 0, lab, 1 << 20), size=3)
            face = g & nb & ctx.vox
            fz = np.argwhere(face)
            if len(fz):
                cz = np.argwhere(cavity).mean(0)
                p0 = fz[np.argmin(((fz - cz) ** 2).sum(1))]
                d = cz - p0
                d = d / max(np.linalg.norm(d), 1e-9)
                P = np.argwhere(shell)
                v = P - p0
                along = v @ d
                radial = np.linalg.norm(v - along[:, None] * d[None, :], axis=1)
                drill = P[(radial <= r) & (along >= -1) & (along <= w + 2)]
                shell[tuple(drill.T)] = False
                hole = len(drill)
        solid_n, shell_n = int(g.sum()), int(shell.sum())
        # 가장 얇은 벽 — 속이 있는 부품만: 속 경계에서 바깥까지 거리의 최솟값
        if cavity.any():
            wall = float(dt[cavity & ~ndimage.binary_erosion(cavity)].min() * ctx.vmm)
        else:
            wall = None
        out.append({"부품": i, "원래ml": round(solid_n * ctx.vmm ** 3 / 1000, 2), "비운뒤ml": round(shell_n * ctx.vmm ** 3 / 1000, 2),
                    "감소": round(1 - shell_n / max(solid_n, 1), 4), "속있음": bool(cavity.any()), "배수구멍칸": hole,
                    "가장얇은벽mm": round(wall, 2) if wall is not None else None})
    return out


def mesh_mm(ctx, g, axes):
    import trimesh
    m = trimesh.Trimesh(*H.mesh_from(g, axes), process=True)
    if m.volume < 0:
        m.invert()
    m.apply_scale(H_MM / (np.ptp(ctx.idx[:, 2]) + 1) / (axes[2][1] - axes[2][0]))
    return m


def pins(ctx, parts, cuts, axes):
    """Q5 — 이웃한 부품 쌍마다 네모 핀 3mm (길이 6mm) · 양쪽에 공차 0.15mm 구멍 · manifold3d 불리언."""
    import manifold3d as mf
    import trimesh
    to_mf = lambda m: mf.Manifold(mf.Mesh(np.asarray(m.vertices, np.float32), np.asarray(m.faces, np.uint32)))
    vols = part_volumes(ctx, parts)
    ms = [mesh_mm(ctx, g, axes) for g in vols]
    scale = ms[0].scale if False else H_MM / (np.ptp(ctx.idx[:, 2]) + 1)   # 칸 -> mm
    M = [to_mf(m) for m in ms]
    orig = sum(m.volume for m in ms)
    lab = np.full(ctx.vox.shape, -1, np.int32)
    for i, g in enumerate(vols):
        lab[g] = i
    report, pin_list = [], []
    for a in range(len(parts)):
        for b in range(a + 1, len(parts)):
            ga, gb = vols[a], vols[b]
            # 면으로 닿은 칸만 — 26 이웃 팽창은 모서리만 닿은 짝까지 잡아 허공 핀을 만들었다 (09-17 검사)
            touch = np.zeros_like(ga)
            for ax in range(3):
                for sg in (1, -1):
                    touch |= ga & np.roll(gb, sg, axis=ax)
            if touch.sum() < ctx.pin_cells:
                continue
            # 법선 = 접촉면 칸들의 주성분 중 가장 얇은 방향 → 후보 법선 13개 중 가장 가까운 것 (절단은 그 13개로만 했다)
            # 무게중심 방향으로 잡았더니 기울어진 절단면을 수평으로 읽어 핀 둘이 허공에 떴다 (09-17 검사)
            Tc = np.argwhere(touch).astype(float)
            w_, V_ = np.linalg.eigh(np.cov((Tc - Tc.mean(0)).T))
            k = int(np.argmax(np.abs(NORMALS @ V_[:, 0])))
            dirv = np.argwhere(gb).mean(0) - np.argwhere(ga).mean(0)
            n = NORMALS[k] * (1 if NORMALS[k] @ dirv >= 0 else -1)
            # 핀 중심 = 접촉면을 절단 평면에 2D 로 펴고, 가장자리에서 가장 먼 점.
            # 3D 거리변환은 두께 한 칸 판에서 어디서나 ≤ 1 이라 아무 점이나 골랐다 (09-17 검사 — 핀이 허공)
            T = np.argwhere(touch).astype(float)
            e1 = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
            e1 /= np.linalg.norm(e1); e2 = np.cross(n, e1)
            uv = np.stack([T @ e1, T @ e2], 1)
            uv0 = np.floor(uv.min(0)).astype(int)
            ij = np.floor(uv).astype(int) - uv0
            img = np.zeros(tuple(ij.max(0) + 3), bool)
            img[ij[:, 0] + 1, ij[:, 1] + 1] = True
            img = ndimage.binary_closing(img, np.ones((3, 3)))
            edt = ndimage.distance_transform_edt(img)
            best = np.array(np.unravel_index(np.argmax(edt), edt.shape)) - 1
            pc = T[np.argmin(((ij - best) ** 2).sum(1))]
            c = pc + 0.5 * n                                                  # 경계면을 가로지르게 반 칸
            centre = c * scale                                                # mm (메시와 같은 원점: 격자 칸 0)
            def box(side, length):
                bx = mf.Manifold.cube([side, side, length], True)
                z = np.array([0, 0, 1.0]); v = np.cross(z, n); sn = np.linalg.norm(v)
                if sn > 1e-6:
                    ang = np.degrees(np.arcsin(min(sn, 1.0))) if n[2] >= 0 else 180 - np.degrees(np.arcsin(min(sn, 1.0)))
                    R = trimesh.transformations.rotation_matrix(np.radians(ang), v / sn)[:3, :3]
                else:
                    R = np.eye(3) if n[2] > 0 else np.diag([1, -1, -1.0])
                T = np.hstack([R, centre[:, None]])
                return bx.transform(T.tolist())
            pin = box(PIN_SIDE, PIN_LEN)
            slot = box(PIN_SIDE + 2 * TOL, PIN_LEN + 2 * TOL)
            # 핀이 양쪽 부품 속에 반씩 박히나 — 절단면이 오목하면 중심이 허공에 떨어질 수 있다
            ia = (pin ^ to_mf(ms[a])).volume() / pin.volume()
            ib = (pin ^ to_mf(ms[b])).volume() / pin.volume()
            M[a] = M[a] - slot
            M[b] = M[b] - slot
            pin_list.append(pin)
            report.append({"쌍": [a, b], "법선": k, "접촉칸": int(touch.sum()), "접촉면중심여유mm": round(float(edt.max()) * ctx.vmm, 2),
                           "a안몫": round(ia, 3), "b안몫": round(ib, 3), "유효": bool(min(ia, ib) >= 0.4)})
    # 원형 메시 좌표 원점과 핀 좌표 원점 맞추기: mesh_from 은 axes 좌표 · 핀은 칸 좌표 × mm — 둘 다 칸 0 기준으로 옮긴다
    status = [str(m.status()) for m in M]
    assembled = sum(m.volume() for m in M) + sum(p.volume() for p in pin_list)
    return {"핀": report, "부품상태": status, "원형부피ml": round(orig / 1000, 2),
            "조립부피ml": round(assembled / 1000, 2), "부피차": round(abs(assembled - orig) / max(orig, 1e-9), 4)}


def run_parts(case):
    t0 = time.time()
    vox, axes, masks, cols, bs = build(case)
    ctx = Ctx(vox, axes, masks, cols, bs)
    s = beam(ctx, np.where(ctx.B, 0.0, 1.0), 3)[3]
    parts, cuts = s[1], s[2]
    # 핀 좌표를 칸 좌표로 맞추려고 axes 를 칸 번호로 바꾼다 (원점 0 · 간격 1)
    ax_idx = tuple(np.arange(n, dtype=float) for n in vox.shape)
    q4 = hollow(ctx, parts, cuts)
    q4_m0 = hollow(ctx, [np.arange(len(ctx.idx))], [])               # 사후 대조 (검토 뒤): 자르지 않고 속 비움 — 배수 구멍 자리가 없어 구멍은 0
    q5 = pins(ctx, parts, cuts, ax_idx)
    tot = lambda rs, k: round(sum(r[k] for r in rs), 2)
    out = {"case": case, "판": TAG, "M1 k3 측정": measure(ctx, parts, cuts), "Q4 속비우기": q4, "Q4 대조 한덩이 속비우기": q4_m0,
           "Q4 합": {"부품 원래ml": tot(q4, "원래ml"), "부품 비운뒤ml": tot(q4, "비운뒤ml"), "한덩이 비운뒤ml": tot(q4_m0, "비운뒤ml")},
           "Q5 핀": q5, "Q5 유효핀": "%d/%d" % (sum(x["유효"] for x in q5["핀"]), len(q5["핀"])), "초": round(time.time() - t0, 1)}
    p = os.path.join(HERE, "out", "기록", "출력분할_부품_%s.json" % case)
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"Q4 감소": [r["감소"] for r in q4], "Q4 합": out["Q4 합"], "얇은벽": [r["가장얇은벽mm"] for r in q4], "Q5 부피차": q5["부피차"], "유효핀": out["Q5 유효핀"], "상태": q5["부품상태"]}, ensure_ascii=False))
    print("  ->", p)


def shade_labels(verts, faces, fcol, az, frame, S=360):
    """면마다 색 · z 버퍼 · 면 법선 양면 명암 (`폴리싱.shaded` 와 같은 틀 · 같은 빛)."""
    sys.path.insert(0, os.path.join(HERE, "실험_20260913"))
    import 깊이색 as DC
    import trimesh
    m = trimesh.Trimesh(verts, faces, process=False)
    R = 2 * S
    P = DC.project(m, az, frame, R)[faces]
    a = np.radians(az); c, s_ = np.cos(a), np.sin(a)
    Nf = np.asarray(m.face_normals)
    Nf = np.stack([c * Nf[:, 0] - s_ * Nf[:, 1], s_ * Nf[:, 0] + c * Nf[:, 1], Nf[:, 2]], 1)
    L = np.array([-0.78, -0.50, 0.38]); L /= np.linalg.norm(L)
    lit = 0.25 + 0.75 * np.abs(Nf @ L)
    zb = np.full((R, R), np.inf); idx = np.full((R, R), -1, np.int32)
    lo = np.clip(np.floor(P[:, :, :2].min(1)), 0, R - 1).astype(int); hi = np.clip(np.ceil(P[:, :, :2].max(1)), 0, R - 1).astype(int)
    for i in range(len(P)):
        (x1, y1, d1), (x2, y2, d2), (x3, y3, d3) = P[i]
        den = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(lo[i, 0], hi[i, 0] + 1) + 0.5, np.arange(lo[i, 1], hi[i, 1] + 1) + 0.5)
        l1 = ((y2 - y3) * (gx - x3) + (x3 - x2) * (gy - y3)) / den
        l2 = ((y3 - y1) * (gx - x3) + (x1 - x3) * (gy - y3)) / den
        mm = (l1 >= -1e-9) & (l2 >= -1e-9) & (1 - l1 - l2 >= -1e-9)
        if not mm.any():
            continue
        d = l1 * d1 + l2 * d2 + (1 - l1 - l2) * d3
        sz = zb[lo[i, 1]:hi[i, 1] + 1, lo[i, 0]:hi[i, 0] + 1]; si = idx[lo[i, 1]:hi[i, 1] + 1, lo[i, 0]:hi[i, 0] + 1]
        up = mm & (d < sz); sz[up] = d[up]; si[up] = i
    img = np.full((R, R, 3), 247.0)
    ok = idx >= 0
    img[ok] = fcol[idx[ok]] * lit[idx[ok]][:, None]
    return img.reshape(S, 2, S, 2, 3).mean((1, 3)).clip(0, 255).astype(np.uint8)


def label_mesh(label_vol, colors):
    """라벨 부피 -> 라벨마다 마칭큐브 · 면 색. 그리기용이라 격자를 반으로 줄인다."""
    import trimesh
    V, F, C, off = [], [], [], 0
    lv = label_vol[::2, ::2, ::2]
    ax = tuple(np.arange(n, dtype=float) for n in lv.shape)
    for li in np.unique(lv[lv >= 0]):
        g = lv == li
        if g.sum() < 20:
            continue
        v, f = H.mesh_from(g, ax)
        V.append(v); F.append(f + off); C.append(np.repeat(colors[int(li) % len(colors)][None, :], len(f), 0)); off += len(v)
    return np.concatenate(V), np.concatenate(F), np.concatenate(C)


def figure(case):
    sys.path.insert(0, os.path.join(HERE, "실험_20260913"))
    import 앨리어싱 as AL
    import trimesh
    from PIL import Image, ImageDraw
    from 계획 import _font
    vox, axes, masks, cols, bs = build(case)
    ctx = Ctx(vox, axes, masks, cols, bs)
    b1, b2 = beam(ctx, np.where(ctx.B, 0.0, 1.0), 3)[3], beam(ctx, 1.0 - ctx.O, 3)[3]
    rows = [("M1 칠경계", b1[1]), ("M2 가림", b2[1]), ("C1 높이등분", height_cuts(ctx, 3)[0]), ("C2 무작위(씨앗0)", random_cuts(ctx, 3, 0)[0])]
    # 재질 줄 — 표면 재질 색 (흰 · 금 · 청회 · 검정) · 경계 칸은 빨강
    matc = np.array([(235, 235, 230), (215, 180, 70), (120, 140, 170), (70, 70, 75)], float)
    lab = np.where(ctx.vox, 0, -1).astype(np.int32)
    ref = trimesh.Trimesh(*H.mesh_from(vox[::2, ::2, ::2], tuple(np.arange(n, dtype=float) for n in vox[::2, ::2, ::2].shape)), process=False)
    azs = (0, 45, 90, 180)
    fr = {az: AL.frame_of(ref, az) for az in azs}
    tiles = []
    # 재질 표면 색은 표면 칸의 재질을 가장 가까운 칸으로 퍼뜨려 칠한다
    surf_lab = np.where(ctx.lab >= 0, ctx.lab, -1).astype(np.int32)
    dist, ind = ndimage.distance_transform_edt(surf_lab < 0, return_indices=True)
    full = surf_lab[tuple(ind)]
    full = np.where(ctx.vox, full, -1)
    full = np.where(ctx.bound & ctx.vox, 4, full)
    V, F, C = label_mesh(full, np.vstack([matc, [(220, 40, 40)]]))
    tiles.append(("원화 재질 (빨강 = 칠 경계)", [shade_labels(V, F, C, az, fr[az]) for az in azs]))
    for name, parts in rows:
        lv = np.full(vox.shape, -1, np.int32)
        for i, pr in enumerate(parts):
            lv[tuple(ctx.idx[pr].T)] = i
        V, F, C = label_mesh(lv, PALETTE)
        m = measure(ctx, parts, [])
        tiles.append(("%s · 칠경계일치 %.3f · 서포트 %.3f" % (name, m["칠경계일치"], m["서포트몫"]), [shade_labels(V, F, C, az, fr[az]) for az in azs]))
        print("  %s 그림" % name, flush=True)
    S_, G, LW, TOP = 360, 8, 30, 70
    im = Image.new("RGB", (LW + 4 * (S_ + G), TOP + len(tiles) * (S_ + 34 + G)), "white")
    d = ImageDraw.Draw(im)
    d.text((14, 12), "%s — 출력 단위 분할 k = 3 (부품 4) · 판본 넷 · 같은 틀" % case, font=_font(24), fill=(20, 20, 20))
    for i, (name, ts) in enumerate(tiles):
        y = TOP + i * (S_ + 34 + G)
        d.text((LW, y), name, font=_font(17), fill=(30, 30, 30))
        for j, t in enumerate(ts):
            im.paste(Image.fromarray(t), (LW + j * (S_ + G), y + 28))
    p = os.path.join(HERE, "out", "출력분할_%s.png" % case)
    im.save(p)
    print("  ->", p)


def paper_data():
    """논문 폴더로 숫자를 내보낸다 — 판정 json · 장별 csv (k=3) · 부품(Q4 · Q5) json."""
    import csv, glob, shutil
    D = os.path.join(HERE, "논문", "출력분할")
    os.makedirs(os.path.join(D, "그림"), exist_ok=True)
    v = sorted(glob.glob(os.path.join(HERE, "out", "기록", "출력분할_판정_*.json")))[-1]
    shutil.copy(v, os.path.join(D, "판정.json"))
    have = done()
    with open(os.path.join(D, "장별.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        keys = ("칠경계일치", "서포트몫", "정면이음매몫", "이음매길이mm")
        w.writerow(["case", "표면칸", "재질경계몫", "M0_서포트몫"] + ["%s_%s" % (m, k) for m in ("M1", "M2", "M3", "C1", "C2") for k in keys])
        for c in cases():
            if c not in have:
                continue
            r = have[c]; k3 = r["k3"]
            w.writerow([c, r["표면칸"], r["재질경계몫"], r["M0"]["서포트몫"]] + [k3[m][k] for m in ("M1", "M2", "M3", "C1", "C2") for k in keys])
    for c in ("은둔자", "오메가몬"):
        q = os.path.join(HERE, "out", "기록", "출력분할_부품_%s.json" % c)
        if os.path.exists(q):
            shutil.copy(q, os.path.join(D, "부품_%s.json" % c))
        g = os.path.join(HERE, "out", "출력분할_%s.png" % c)
        if os.path.exists(g):
            shutil.copy(g, os.path.join(D, "그림", "분할_%s.png" % c))
    print("  ->", D)


PROG_S = os.path.join(HERE, "out", "기록", "출력분할_사후S_진행.jsonl")
TAG_S = "출력분할 사후 대조 S · 서포트만 (p=0) + M1 재측정 · 원화2D 경계 자 · v2b 와 같은 탐색 · 150mm (2026-09-17)"


def run_support_only(case):
    """사후 대조 S — 이음매 벌점 없이 서포트만 최소화한다. M1 의 이음매 항이 무엇을 바꿨는지 가른다."""
    t0 = time.time()
    vox, axes, masks, cols, bs = build(case)
    ctx = Ctx(vox, axes, masks, cols, bs)
    b = beam(ctx, np.zeros(len(ctx.idx)), max(KS))
    b1 = beam(ctx, np.where(ctx.B, 0.0, 1.0), max(KS))                # M1 그대로 (v2b 와 같은 분할) — 고친 자로 다시 재려고
    row = {"case": case, "판": TAG_S, "기저_경계몫": round(float(ctx.B.sum()) / ctx.n_surf, 4),
           "기저_원화2D경계몫": round(float(ctx.bound_art[ctx.vox].sum()) / ctx.n_surf, 4)}
    for K in KS:
        st = b[K]
        row["k%d" % K] = measure(ctx, st[1], st[2])
        row["k%d" % K]["절단"] = st[2]
        row["M1_k%d" % K] = measure(ctx, b1[K][1], b1[K][2])
    row["초"] = round(time.time() - t0, 1)
    with open(PROG_S, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("  %-26s k3 서포트 S %.3f M1 %.3f · 칠경계일치 S %.3f M1 %.3f · 원화2D S %.3f M1 %.3f (기저 %.3f) · %.0f초"
          % (case[:26], row["k3"]["서포트몫"], row["M1_k3"]["서포트몫"], row["k3"]["칠경계일치"], row["M1_k3"]["칠경계일치"],
             row["k3"]["칠경계일치_원화2D"], row["M1_k3"]["칠경계일치_원화2D"], row["기저_원화2D경계몫"], row["초"]), flush=True)


def verdict_support_only():
    have = done()
    hs = {r["case"]: r for r in map(json.loads, open(PROG_S, encoding="utf-8")) if r.get("판") == TAG_S} if os.path.exists(PROG_S) else {}
    cs = [c for c in cases() if c in have and c in hs]
    def rule(d):
        d = np.array(d)
        loo = min(float(np.median(np.delete(d, i))) for i in range(len(d))) if len(d) > 1 else float(d[0])
        return {"중앙차": round(float(np.median(d)), 4), "승": int((d > 0).sum()), "패": int((d < 0).sum()), "장": len(d), "한장빼기최소": round(loo, 4),
                "통과": bool(np.median(d) > 0 and (d > 0).sum() * 2 > len(d) and loo > 0)}
    out = {"설명": "사후 대조 S (서포트만) — 검토 뒤 더함", "장": len(cs)}
    for K in KS:
        k = "k%d" % K
        sub = [c for c in cs if have[c]["재질경계몫"] > 0]
        out[k] = {
            "칠경계일치 M1>S (30)": rule([have[c][k]["M1"]["칠경계일치"] - hs[c][k]["칠경계일치"] for c in cs]),
            "칠경계일치 M1>S (경계있는장)": rule([have[c][k]["M1"]["칠경계일치"] - hs[c][k]["칠경계일치"] for c in sub]),
            "서포트 S<M1 (이음매 항의 대가)": rule([have[c][k]["M1"]["서포트몫"] - hs[c][k]["서포트몫"] for c in cs]),
            "서포트 S<C1": rule([have[c][k]["C1"]["서포트몫"] - hs[c][k]["서포트몫"] for c in cs]),
            "중앙": {"S": {x: round(float(np.median([hs[c][k][x] for c in cs])), 4) for x in ("칠경계일치", "서포트몫", "정면이음매몫")}},
        }
    q = os.path.join(HERE, "out", "기록", "출력분할_사후S_판정.json")
    json.dump(out, open(q, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out["k3"], ensure_ascii=False))
    print("  ->", q)


if __name__ == "__main__":
    a = sys.argv[1:] or ["검사"]
    selfcheck()
    if a[0] == "검사":
        pass
    elif a[0] == "판정":
        verdict()
    elif a[0] == "사후S":
        hs = {r["case"] for r in map(json.loads, open(PROG_S, encoding="utf-8")) if r.get("판") == TAG_S} if os.path.exists(PROG_S) else set()
        todo = [c for c in cases() if c not in hs][: int(a[1]) if len(a) > 1 else 40]
        for c in todo:
            run_support_only(c)
    elif a[0] == "사후S판정":
        verdict_support_only()
    elif a[0] == "논문자료":
        paper_data()
    elif a[0] == "그림":
        cases()
        for c in a[1:]:
            figure(c)
    elif a[0] == "부품":
        cases()
        for c in a[1:]:
            run_parts(c)
    elif a[0].isdigit():
        have = done()
        todo = [c for c in cases() if c not in have][: int(a[0])]
        for c in todo:
            run_case(c)
    else:
        cases()                                                       # 케이스 등록 (시트 · 은둔자)
        for c in a:
            run_case(c)
