# -*- coding: utf-8 -*-
"""**출력 분할 — 척도 정규화와 머리보존 제약** (2026-09-19). 계획 `claudedocs/plan_출력분할제약_20260919.md`.

    python 출력분할제약.py 검사          자가검사 (P4) · 정규화 상수 · 제약이 이등분을 거절하나
    python 출력분할제약.py [n]           아직 안 한 장 n 개 -> out/기록/출력분할제약_진행.jsonl
    python 출력분할제약.py 판정          -> out/기록/출력분할제약_판정_<때>.json
    python 출력분할제약.py 그림 <케이스>  판본별 절단면 그림 -> out/출력분할제약_<케이스>.png
    python 출력분할제약.py 논문자료       판정 json · 장별 csv 를 논문/출력분할/ 로

09-17 `실험_20260917/출력분할.py` 를 **import 해서** 쓴다 — `Ctx` 를 상속해 `cut_candidates`(척도) 와
`feasible`(머리보존)만 덮고 `beam` · `measure` · `build` · `random_cuts` · 그림 함수는 그대로다.
판본 M1 은 정규화 · 제약을 끈 것이므로 09-17 절단면과 **정확히 같아야 한다** (배관 P2).
"""
import json
import os
import sys
import time

import numpy as np
from scipy import ndimage

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, os.path.join(HERE, "실험_20260917"))
import 출력분할 as P                                                  # noqa: E402  (os.chdir(HERE) 는 여기서 일어난다)

PROG = os.path.join(HERE, "out", "기록", "출력분할제약_진행.jsonl")
TAG = ("출력분할제약 v2 · 09-17 v2b 탐색 그대로 (법선13 · 오프셋2 · 빔4 · 1/8 표본) · "
       "M1 기준 재현 · N 후보범위정규화(p95−p5) · N65 달성범위정규화(α=6.5) · X 머리보존(0.10) · "
       "NX65 둘 다 · C2 · C3 무작위 씨앗10 (2026-09-19)")
KS = P.KS
ALPHA = 6.5             # 달성 범위 비 — 0 단계 표(30장 k3 중앙 Δf_support 0.1638 / f_seam 0.0251)에서 그대로 온다
HEAD_TOL = 0.10                                                       # 한 절단면이 머리에서 떼어 갈 수 있는 최대 몫
MIN_RAM_GB = 6.0
# (이름, 점수 방식, 머리보존 제약). 한 장 10분 벽 때문에 빔은 다섯이 한계다 — 계획의 NX(= N + 제약) 자리에
# NX65 를 둔다. 배관 게이트(은둔자)에서 N 의 절단면이 M1 과 한 글자도 다르지 않아 N + 제약 = X 가 되기 때문이다.
VARIANTS = (("M1", "raw", False), ("N", "norm", False), ("N65", "alpha", False),
            ("X", "raw", True), ("NX65", "alpha", True))


# ───────────────────────── 머리 (목 위) ─────────────────────────

def head_of(ctx):
    """목 = z 상반부(0.5 ~ 0.9)에서 가로 단면적이 가장 작은 층. 머리 = 그 위. -> (행 마스크, 목 z)"""
    z = ctx.idx[:, 2]
    z0, ext = int(z.min()), int(z.max() - z.min()) + 1
    area = np.bincount(z - z0, minlength=ext).astype(float)
    lo, hi = int(0.50 * ext), max(int(0.90 * ext), int(0.50 * ext) + 2)
    j = lo + int(np.argmin(area[lo:hi]))
    return (z - z0) > j, j


def head_spread(ctx, parts):
    """머리분산 = 1 − max_i |머리 ∩ 부품 i| / |머리|. 0 = 머리가 한 부품에 통째로 · 0.5 = 반으로 갈림."""
    ht = int(ctx.head.sum())
    if ht == 0:
        return None
    return round(1.0 - max(int(ctx.head[p].sum()) for p in parts) / ht, 4)


# ───────────────────────── 판본 ─────────────────────────

class Ctx2(P.Ctx):
    """09-17 Ctx + 척도 정규화 · 머리보존 제약. 둘 다 끄면 09-17 과 비트 단위로 같은 후보 점수를 낸다."""

    def __init__(self, vox, axes, masks, cols, bs):
        super().__init__(vox, axes, masks, cols, bs)
        self.head, self.neck_z = head_of(self)
        self.mode = "raw"                                             # raw | norm (후보 범위) | alpha (달성 범위)
        self.alpha = 1.0
        self.guard = False
        self.r_s = self.r_u = 1.0

    @property
    def norm(self):
        return self.mode == "norm"

    @norm.setter
    def norm(self, v):
        self.mode = "norm" if v else "raw"

    # --- 후보: 원 단위 (seam, Δsup) 를 그대로 돌려준다 (09-17 cut_candidates 와 같은 순서 · 같은 산술) ---
    def raw_candidates(self, rows_full, pen):
        out = []
        rows = rows_full[self.sub[rows_full]]
        n = len(rows)
        if n < 2 / P.MIN_PART:
            return out
        minv = P.MIN_PART * self.sub.sum()
        base_sup = self.support(rows) * 8
        for k in range(len(P.NORMALS)):
            t = self.T[rows, k]
            o = np.argsort(t, kind="stable")
            ts = t[o]
            E = np.cumsum(self.E[rows][o], 0)
            tot = E[-1]
            Sp = self.S[rows][o] * pen[rows][o]
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
                cross = (b - a) * 8
                if cross / 1.74 < self.pin_cells:
                    continue
                out.append((seam, sup - base_sup, k, float(c)))
        return out

    def set_scales(self, pen):
        """정규화 상수를 **케이스마다 한 번** 뿌리 후보 집합에서 정한다 — 걸음마다 바꾸면 빔의 누적 비용 비교가 깨진다."""
        raw = self.raw_candidates(np.arange(len(self.idx)), pen)
        if not raw:
            self.r_s = self.r_u = 1.0
            return
        s = np.array([r[0] for r in raw]); u = np.array([r[1] for r in raw])
        rng = lambda a: float(max(np.percentile(a, 95) - np.percentile(a, 5), 1e-6))
        self.r_s, self.r_u = rng(s), rng(u)

    def cut_candidates(self, rows_full, pen):
        raw = self.raw_candidates(rows_full, pen)
        if self.mode == "norm":                                       # 후보 범위 정규화 (계획에 얼린 것)
            return [(seam / self.r_s + dsup / self.r_u, k, c) for seam, dsup, k, c in raw]
        if self.mode == "alpha":                                      # 달성 범위 정규화 — 이음매 항에 α 배
            return [((self.alpha * seam + dsup) / self.n_surf, k, c) for seam, dsup, k, c in raw]
        return [((seam + dsup) / self.n_surf, k, c) for seam, dsup, k, c in raw]

    def feasible(self, rows, k, c):
        if not super().feasible(rows, k, c):
            return False
        if not self.guard:
            return True
        ht = int(self.head.sum())
        if ht == 0:
            return True
        h = self.head[rows]
        if not h.any():
            return True
        L = self.T[rows, k] < c
        return min(int((h & L).sum()), int((h & ~L).sum())) <= HEAD_TOL * ht


def meas(ctx, parts, cuts):
    m = P.measure(ctx, parts, cuts)
    m["머리분산"] = head_spread(ctx, parts)
    return m


def replay(ctx, cuts, ref_sup=None, tol=5e-4):
    """기록에 남은 절단면 목록으로 같은 분할을 다시 세운다 (빔을 다시 돌리지 않는다).

    한 평면이 여러 부품을 동시에 가를 수 있어 「어느 부품에 걸었나」가 한 가지로 정해지지 않는다.
    가능한 배정을 전부 훑고, 기록된 서포트몫을 되찾는 것을 고른다 (서포트는 행 연산이라 싸다).
    """
    best = []

    def rec(parts, i):
        if best:
            return
        if i == len(cuts):
            if ref_sup is None:
                best.append(parts); return
            s = sum(ctx.support(p) for p in parts) / ctx.n_surf
            if abs(s - ref_sup) <= tol:
                best.append(parts)
            return
        k, c = cuts[i]
        opts = []
        for j, p in enumerate(parts):
            t = ctx.T[p, k]
            L, R = p[t < c], p[t >= c]
            if len(L) and len(R):
                opts.append((-min(len(L), len(R)), j, L, R))
        for _, j, L, R in sorted(opts, key=lambda x: x[0]):
            rec(parts[:j] + [L, R] + parts[j + 1:], i + 1)
            if best:
                return

    rec([np.arange(len(ctx.idx))], 0)
    return best[0] if best else None


# ───────────────────────── 한 장 ─────────────────────────

def s17_records():
    p = os.path.join(HERE, "out", "기록", "출력분할_사후S_진행.jsonl")
    if not os.path.exists(p):
        return {}
    return {r["case"]: r for r in map(json.loads, open(p, encoding="utf-8")) if r.get("판") == P.TAG_S}


def p17_records():
    return P.done()


def run_case(case):
    t0 = time.time()
    vox, axes, masks, cols, bs = P.build(case)
    ctx = Ctx2(vox, axes, masks, cols, bs)
    pen1 = np.where(ctx.B, 0.0, 1.0)
    ctx.set_scales(pen1)
    row = {"case": case, "판": TAG, "표면칸": ctx.n_surf, "재질경계몫": round(float(ctx.B.sum()) / ctx.n_surf, 4),
           "머리몫": round(float(ctx.head.sum()) / len(ctx.idx), 4), "목z": int(ctx.neck_z),
           "r_s": round(ctx.r_s, 2), "r_u": round(ctx.r_u, 2),
           "암시무게 r_s/r_u": round(ctx.r_s / max(abs(ctx.r_u), 1e-6), 3),
           "M0": meas(ctx, [np.arange(len(ctx.idx))], [])}

    beams = {}
    for name, mode, guard in VARIANTS:
        ctx.mode, ctx.alpha, ctx.guard = mode, ALPHA, guard
        beams[name] = P.beam(ctx, pen1, max(KS))
    ctx.mode, ctx.guard = "raw", False

    s17 = s17_records().get(case)
    p17 = p17_records().get(case)
    for K in KS:
        r = {}
        for name, _, _ in VARIANTS:
            st = beams[name][K]
            r[name] = meas(ctx, st[1], st[2])
            r[name]["절단"] = st[2]
        # C2 (제약 없는 무작위) · C3 (머리보존 제약 안의 무작위) — 같은 씨앗. C2 − C3 낙차가 제약이 거저 가져간 몫이다.
        # 09-17 C2 는 원화 2D 자가 생기기 전이라 그 열이 없다 → 같은 씨앗 · 같은 코드로 다시 잰다.
        for nm, gd in (("C2", False), ("C3", True)):
            ctx.guard = gd
            rs = [meas(ctx, *P.random_cuts(ctx, K, sd)) for sd in range(P.SEEDS)]
            ctx.guard = False
            r[nm] = {k: (round(float(np.median([x[k] for x in rs])), 4)
                         if isinstance(rs[0][k], (int, float)) and rs[0][k] is not None else None) for k in rs[0]}
        # C1 은 결정적이라 그대로 다시 센다 · S 는 09-17 절단면을 되살려 머리분산만 새로 잰다
        p, c = P.height_cuts(ctx, K)
        r["C1"] = meas(ctx, p, c)
        if s17 and ("k%d" % K) in s17:
            pr = replay(ctx, s17["k%d" % K]["절단"], s17["k%d" % K]["서포트몫"])
            r["S"] = meas(ctx, pr, []) if pr is not None else {"재현실패": True}
        # 09-17 M1 재현 확인 (배관 P2)
        if p17 and ("k%d" % K) in p17:
            a = [tuple(x) for x in p17["k%d" % K]["M1"]["절단"]]
            b = [tuple(x) for x in r["M1"]["절단"]]
            r["P2_M1일치"] = bool(a == b)
            r["P2_M1_09_17"] = {x: p17["k%d" % K]["M1"][x] for x in ("칠경계일치", "서포트몫", "정면이음매몫")}
            if s17 and ("M1_k%d" % K) in s17:                          # 원화 2D 자는 09-17 사후 기록에만 있다
                r["P2_M1_09_17"]["칠경계일치_원화2D"] = s17["M1_k%d" % K]["칠경계일치_원화2D"]
        row["k%d" % K] = r
    row["초"] = round(time.time() - t0, 1)
    with open(PROG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    k3 = row["k3"]
    hs = " ".join("%s %s" % (n, k3[n]["머리분산"]) for n, _, _ in VARIANTS)
    a2 = " ".join("%s %.3f" % (n, k3[n]["칠경계일치_원화2D"]) for n, _, _ in VARIANTS)
    print("  %-24s 머리몫 %.3f · 머리분산 %s (S %s C3 %s) · 원화2D %s · 서포트 M1 %.3f N65 %.3f · P2 %s · %.0f초"
          % (case[:24], row["머리몫"], hs, k3.get("S", {}).get("머리분산"), k3["C3"]["머리분산"], a2,
             k3["M1"]["서포트몫"], k3["N65"]["서포트몫"], k3.get("P2_M1일치"), row["초"]), flush=True)


def done():
    if not os.path.exists(PROG):
        return {}
    return {r["case"]: r for r in map(json.loads, open(PROG, encoding="utf-8")) if r.get("판") == TAG}


# ───────────────────────── 판정 ─────────────────────────

def verdict():
    have = done()
    cs = [c for c in P.cases() if c in have]
    bd = json.load(open(os.path.join(HERE, "out", "기록", "출력분할_사후_경계있는장.json"), encoding="utf-8"))["케이스"]
    sub = [c for c in cs if c in bd]                                   # 경계 있는 23장 (09-17 이 얼린 것)
    p17 = p17_records()
    med = lambda a: round(float(np.median(a)), 4)

    def rule(d):
        d = np.array([x for x in d if x is not None], float)
        if len(d) == 0:
            return {"장": 0, "통과": False}
        loo = min(float(np.median(np.delete(d, i))) for i in range(len(d))) if len(d) > 1 else float(d[0])
        return {"중앙차": med(d), "승": int((d > 0).sum()), "패": int((d < 0).sum()), "장": len(d),
                "한장빼기최소": round(loo, 4),
                "통과": bool(np.median(d) > 0 and (d > 0).sum() * 2 > len(d) and loo > 0)}

    out = {"판": TAG, "장": len(cs), "경계있는장": len(sub), "케이스": cs}
    # 0 단계 — 두 항의 달성 범위를 같은 단위(칸 / 표면칸)로. 09-17 기록에서 그대로 뽑는다.
    out["척도"] = {}
    for K in KS:
        k = "k%d" % K
        row = {}
        for m in ("M1", "M2", "M3", "C1", "C2"):
            fs, fu = [], []
            for c in cs:
                if c not in p17:
                    continue
                d, ns = p17[c][k][m], p17[c]["표면칸"]
                if d.get("이음매칸") is None:
                    continue
                fs.append(d["이음매칸"] * (1 - d["칠경계일치"]) / ns)
                fu.append(p17[c]["M0"]["서포트몫"] - d["서포트몫"])
            if fs:
                row[m] = {"f_seam": med(fs), "Δf_support": med(fu), "비": round(float(np.median(fu) / np.median(fs)), 2)}
        out["척도"][k] = row
    out["척도"]["r_s/r_u 중앙 (후보 범위)"] = med([have[c]["암시무게 r_s/r_u"] for c in cs])
    out["척도"]["ALPHA"] = ALPHA
    out["배관"] = {
        "P1 부피보존": "measure 안 assert — 모든 측정 통과",
        "P2 M1 절단면 09-17 일치": {"k%d" % K: sum(bool(have[c]["k%d" % K].get("P2_M1일치")) for c in cs) for K in KS},
        "P3 머리몫 0.02~0.45 벗어난 장": [c for c in cs if not (0.02 <= have[c]["머리몫"] <= 0.45)],
        "S 재현 실패한 장": [c for c in cs if have[c]["k3"].get("S", {}).get("재현실패")],
    }
    ok3 = [c for c in cs if 0.02 <= have[c]["머리몫"] <= 0.45]

    g = lambda m, key, K, where: [have[c]["k%d" % K][m].get(key) for c in where]
    for K in KS:
        k = "k%d" % K
        hs = lambda m: g(m, "머리분산", K, ok3)
        a2 = lambda m: g(m, "칠경계일치_원화2D", K, sub)
        s17 = s17_records()
        base = [s17[c]["기저_원화2D경계몫"] for c in sub if c in s17]   # 기저 = 표면 칸 중 원화 2D 경계 몫
        sub_b = [c for c in sub if c in s17]
        q = {
            "Q1_머리분산_N<M1": rule([b - a for a, b in zip(hs("N"), hs("M1"))]),
            "Q1_N_머리분산중앙": med([x for x in hs("N") if x is not None]),
            "Q1b_머리분산_N65<M1": rule([b - a for a, b in zip(hs("N65"), hs("M1"))]),
            "Q1b_N65_머리분산중앙": med([x for x in hs("N65") if x is not None]),
            "Q1_정면이음매_N<M1": rule([b - a for a, b in zip(g("N", "정면이음매몫", K, cs), g("M1", "정면이음매몫", K, cs))]),
            "Q1b_정면이음매_N65<M1": rule([b - a for a, b in zip(g("N65", "정면이음매몫", K, cs), g("M1", "정면이음매몫", K, cs))]),
            "Q2_N>기저": rule([have[c][k]["N"]["칠경계일치_원화2D"] - b for c, b in zip(sub_b, base)]),
            "Q2b_N65>기저": rule([have[c][k]["N65"]["칠경계일치_원화2D"] - b for c, b in zip(sub_b, base)]),
            "Q2_기저중앙": med(base) if base else None,
            "Q3_머리분산_X<M1": rule([b - a for a, b in zip(hs("X"), hs("M1"))]),
            "Q3_X−C3": med([a - b for a, b in zip(a2("X"), a2("C3"))]),
            "Q3_M1−C2": med([a - b for a, b in zip(a2("M1"), a2("C2"))]),
            "Q3_C3−C2": med([a - b for a, b in zip(a2("C3"), a2("C2"))]),
            "Q4_머리분산_NX65<N65": rule([b - a for a, b in zip(hs("NX65"), hs("N65"))]),
            "Q4_절대차_NX65_N65": med([abs(a - b) for a, b in zip(hs("NX65"), hs("N65")) if a is not None and b is not None]),
            "Q4_머리분산_NX65<X": rule([b - a for a, b in zip(hs("NX65"), hs("X"))]),
            "중앙_경계있는장": {m: {"칠경계일치_원화2D": med(a2(m))} for m in ("M1", "N", "N65", "X", "NX65", "C1", "C2", "C3")},
            "중앙_전체": {m: {"머리분산": med([x for x in hs(m) if x is not None]),
                                          "서포트몫": med(g(m, "서포트몫", K, ok3)),
                                          "정면이음매몫": med(g(m, "정면이음매몫", K, ok3)),
                                          "이음매길이mm": med(g(m, "이음매길이mm", K, ok3))}
                                      for m in ("M1", "N", "N65", "X", "NX65", "C1", "C2", "C3")},
        }
        sm = [have[c][k].get("S", {}).get("머리분산") for c in ok3]
        sm = [x for x in sm if x is not None]
        if sm:
            q["S_머리분산중앙"] = med(sm); q["S_장수"] = len(sm)
        q["M0_서포트중앙"] = med([have[c]["M0"]["서포트몫"] for c in ok3])
        q["M0_머리분산"] = 0.0
        out[k] = q

    q = out["k3"]
    B = "중앙_경계있는장"
    Hm = "중앙_전체"
    m1med = q[B]["M1"]["칠경계일치_원화2D"]
    q1 = bool(q["Q1_머리분산_N<M1"]["통과"] and q["Q1_N_머리분산중앙"] <= 0.10)
    q1b = bool(q["Q1b_머리분산_N65<M1"]["통과"] and q["Q1b_N65_머리분산중앙"] <= 0.10)
    q2 = bool(q[B]["N"]["칠경계일치_원화2D"] >= m1med - 0.02)
    q2b = bool(q[B]["N65"]["칠경계일치_원화2D"] >= m1med - 0.02)
    cost_ok = (q["Q3_X−C3"] is not None and q["Q3_M1−C2"] is not None
               and q["Q3_X−C3"] > q["Q3_M1−C2"] - 0.02)
    q3 = bool(q["Q3_머리분산_X<M1"]["통과"] and cost_ok)
    scale_ok = q1 or q1b
    if scale_ok and q["Q4_절대차_NX65_N65"] <= 0.02:
        q4 = "척도"
    elif scale_ok and q["Q4_머리분산_NX65<N65"]["통과"]:
        q4 = "둘 다"
    elif (not scale_ok) and q3:
        q4 = "자유도"
    elif scale_ok:
        q4 = "척도"
    else:
        q4 = "못 막음"
    pick = {"척도": ("N65" if q1b else "N"), "둘 다": "NX65", "자유도": "X"}.get(q4)
    q5 = None
    if pick:
        pm, ph, ps = q[B][pick]["칠경계일치_원화2D"], q[Hm][pick]["머리분산"], q[Hm][pick]["서포트몫"]
        c1s = q[Hm]["C1"]["서포트몫"]
        q5 = {"판본": pick, "칠경계일치_원화2D": pm, "머리분산": ph, "서포트몫": ps, "C1 서포트몫": c1s,
              "통과": bool(pm >= m1med - 0.02 and ph <= 0.10 and ps <= c1s)}
    # 사후 (결과를 보고 정한 것 — 계획의 분기표에 「둘 다 단독으로는 지지만 합치면 이긴다」 칸이 없었다)
    hs3 = lambda m: [have[c]["k3"][m].get("머리분산") for c in ok3]
    a23 = lambda m: [have[c]["k3"][m].get("칠경계일치_원화2D") for c in sub]
    out["사후_NX65"] = {
        "설명": "계획에 없던 조합 판본. 아래 숫자는 사전 등록된 규칙이 아니라 결과를 본 뒤의 관찰이다.",
        "머리분산 NX65<M1": rule([b - a for a, b in zip(hs3("NX65"), hs3("M1"))]),
        "원화2D NX65>M1": rule([a - b for a, b in zip(a23("NX65"), a23("M1"))]),
        "원화2D NX65>C3 (자유도 맞춘 대조)": rule([a - b for a, b in zip(a23("NX65"), a23("C3"))]),
        "원화2D NX65>X (정규화가 제약 위에 더 주는 몫)": rule([a - b for a, b in zip(a23("NX65"), a23("X"))]),
        "서포트몫 중앙 NX65": med([x for x in (have[c]["k3"]["NX65"]["서포트몫"] for c in ok3)]),
    }
    out["판정"] = {"Q1_후보범위정규화": q1, "Q1b_달성범위정규화": q1b,
                   "Q2_N_대가": q2, "Q2b_N65_대가": q2b,
                   "Q3_제약": q3, "Q4_원인": q4, "Q5_기본값자격": q5,
                   "기준_0917": {"M1": 0.508, "S": 0.4399, "기저": 0.3878}}
    p = os.path.join(HERE, "out", "기록", "출력분할제약_판정_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out["판정"], ensure_ascii=False, indent=1))
    print(json.dumps(out["k3"]["중앙_전체"], ensure_ascii=False))
    print(json.dumps(out["k3"]["중앙_경계있는장"], ensure_ascii=False))
    print("  ->", p)
    return out


# ───────────────────────── 자가검사 (P4) ─────────────────────────

def selfcheck():
    vox = np.zeros((40, 40, 60), bool); vox[10:30, 12:28, 5:55] = True
    ctx = Ctx2.__new__(Ctx2)
    ctx.vox = vox
    s6 = ndimage.generate_binary_structure(3, 1)
    ctx.surf = vox & ~ndimage.binary_erosion(vox, s6, border_value=0)
    ctx.bound = np.zeros_like(vox); ctx.occ = ndimage.uniform_filter(vox.astype(np.float32), size=7)
    ctx.expo = []
    for ax, sg in P.DIRS:
        ctx.expo.append((vox & ~np.roll(vox, sg, axis=ax)) & ctx.surf)
    ctx.idx = np.argwhere(vox); f = lambda a: a[vox]
    ctx.S, ctx.B, ctx.O = f(ctx.surf), f(ctx.bound), f(ctx.occ)
    ctx.E = np.stack([f(e) for e in ctx.expo], 1); ctx.n_surf = int(ctx.S.sum())
    ctx.vmm = 1.0; ctx.pin_cells = 4.0
    ctx.T = (ctx.idx.astype(np.float32) @ P.NORMALS.T.astype(np.float32))
    ctx.sub = ((ctx.idx % 2) == 0).all(1)
    ctx.front = vox & (np.arange(vox.shape[1])[None, :, None] ==
                       np.where(vox, np.arange(vox.shape[1])[None, :, None], vox.shape[1]).min(1)[:, None, :])
    ctx.F = ctx.front[vox]
    ctx.bound_art = np.zeros_like(vox)
    ctx.head, ctx.neck_z = head_of(ctx)
    ctx.norm = ctx.guard = False; ctx.r_s = ctx.r_u = 1.0
    pen = np.ones(len(ctx.idx))

    # 1. 머리분산 — 머리를 세로(x)로 정확히 반 가르는 평면은 0.5 에 가깝고, 위아래로 자르면 0
    assert 0.02 <= ctx.head.mean() <= 0.60, ctx.head.mean()
    rows = np.arange(len(ctx.idx))
    xmid = float(np.median(ctx.idx[:, 0]))
    Lx, Rx = rows[ctx.idx[:, 0] < xmid], rows[ctx.idx[:, 0] >= xmid]
    assert head_spread(ctx, [Lx, Rx]) > 0.35, head_spread(ctx, [Lx, Rx])
    zc = ctx.neck_z + int(ctx.idx[:, 2].min())
    Lz, Rz = rows[ctx.idx[:, 2] <= zc], rows[ctx.idx[:, 2] > zc]
    assert head_spread(ctx, [Lz, Rz]) == 0.0, head_spread(ctx, [Lz, Rz])

    # 2. 제약 — 켜면 머리를 반 가르는 x 평면을 거절하고, 목 평면은 받는다
    ctx.guard = True
    assert not ctx.feasible(rows, 0, xmid), "머리를 반 가르는 평면을 거절하지 못했다"
    assert ctx.feasible(rows, 2, float(zc) + 0.5), "목 절단면까지 거절했다"
    ctx.guard = False

    # 3. 정규화 — 상수가 유한 · 양수 · 안 켰을 때 후보 점수가 09-17 과 같다
    a = P.Ctx.cut_candidates(ctx, rows, pen)
    b = ctx.cut_candidates(rows, pen)
    assert len(a) == len(b) and all(x == y for x, y in zip(a, b)), "정규화 꺼도 09-17 후보와 다르다"
    ctx.set_scales(pen)
    assert np.isfinite(ctx.r_s) and np.isfinite(ctx.r_u) and ctx.r_s > 0 and ctx.r_u > 0, (ctx.r_s, ctx.r_u)
    ctx.norm = True
    nb = ctx.cut_candidates(rows, pen)
    assert len(nb) == len(b) and any(abs(x[0] - y[0]) > 1e-9 for x, y in zip(nb, b)), "정규화가 점수를 안 바꿨다"
    ctx.norm = False

    # 4. 되살리기 — 아는 절단면 둘을 되살리면 같은 분할이 나온다
    parts, cuts = P.height_cuts(ctx, 2)
    pr = replay(ctx, cuts)
    assert pr is not None and sorted(len(p) for p in pr) == sorted(len(p) for p in parts), "되살리기 실패"
    print("  자가검사 통과 — 머리분산 · 제약 거절/허용 · 정규화 항등 · 되살리기 (r_s %.1f r_u %.1f)" % (ctx.r_s, ctx.r_u))


# ───────────────────────── 그림 ─────────────────────────

def figure(case):
    sys.path.insert(0, os.path.join(HERE, "실험_20260913"))
    import 앨리어싱 as AL
    import trimesh
    from PIL import Image, ImageDraw
    from 계획 import _font
    vox, axes, masks, cols, bs = P.build(case)
    ctx = Ctx2(vox, axes, masks, cols, bs)
    pen1 = np.where(ctx.B, 0.0, 1.0)
    ctx.set_scales(pen1)
    rows = []
    for name, mode, guard in (("M1 09-17 · f_seam + f_support", "raw", False),
                              ("N 후보범위 정규화", "norm", False),
                              ("N65 달성범위 정규화 (α = 6.5)", "alpha", False),
                              ("X 머리보존 제약", "raw", True),
                              ("NX65 둘 다", "alpha", True)):
        ctx.mode, ctx.alpha, ctx.guard = mode, ALPHA, guard
        rows.append((name, P.beam(ctx, pen1, 3)[3][1]))
    ctx.mode, ctx.guard = "raw", False
    ref_vox = vox[::2, ::2, ::2]
    ref = trimesh.Trimesh(*P.H.mesh_from(ref_vox, tuple(np.arange(n, dtype=float) for n in ref_vox.shape)), process=False)
    azs = (0, 45, 90, 180)
    fr = {az: AL.frame_of(ref, az) for az in azs}
    tiles = []
    hv = np.full(vox.shape, -1, np.int32)
    hv[tuple(ctx.idx.T)] = 0
    hv[tuple(ctx.idx[ctx.head].T)] = 1
    V, F, C = P.label_mesh(hv, np.array([(200, 200, 195), (220, 90, 60)], float))
    tiles.append(("머리 마스크 (붉은색 = 목 위 · 제약이 지키는 곳)", [P.shade_labels(V, F, C, az, fr[az]) for az in azs]))
    for name, parts in rows:
        lv = np.full(vox.shape, -1, np.int32)
        for i, pr in enumerate(parts):
            lv[tuple(ctx.idx[pr].T)] = i
        V, F, C = P.label_mesh(lv, P.PALETTE)
        m = meas(ctx, parts, [])
        tiles.append(("%s · 머리분산 %.3f · 칠경계 %.3f · 서포트 %.3f"
                      % (name, m["머리분산"], m["칠경계일치_원화2D"], m["서포트몫"]),
                      [P.shade_labels(V, F, C, az, fr[az]) for az in azs]))
        print("  %s 그림" % name, flush=True)
    S_, G, LW, TOP = 360, 8, 30, 70
    im = Image.new("RGB", (LW + 4 * (S_ + G), TOP + len(tiles) * (S_ + 34 + G)), "white")
    d = ImageDraw.Draw(im)
    d.text((14, 12), "%s — 출력 단위 분할 k = 3 (부품 4) · 절단면이 보이는 네 판본 · 같은 틀" % case, font=_font(24), fill=(20, 20, 20))
    for i, (name, ts) in enumerate(tiles):
        y = TOP + i * (S_ + 34 + G)
        d.text((LW, y), name, font=_font(17), fill=(30, 30, 30))
        for j, t in enumerate(ts):
            im.paste(Image.fromarray(t), (LW + j * (S_ + G), y + 28))
    p = os.path.join(HERE, "out", "출력분할제약_%s.png" % case)
    im.save(p)
    print("  ->", p)


def paper_data():
    import csv, glob, shutil
    D = os.path.join(HERE, "논문", "출력분할")
    os.makedirs(os.path.join(D, "그림"), exist_ok=True)
    v = sorted(glob.glob(os.path.join(HERE, "out", "기록", "출력분할제약_판정_*.json")))[-1]
    shutil.copy(v, os.path.join(D, "판정_제약.json"))
    have = done()
    with open(os.path.join(D, "장별_제약.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        keys = ("머리분산", "칠경계일치_원화2D", "서포트몫", "정면이음매몫", "이음매길이mm")
        w.writerow(["case", "표면칸", "머리몫", "r_s", "r_u", "M0_서포트몫"]
                   + ["%s_%s" % (m, k) for m in ("M1", "N", "N65", "X", "NX65", "C1", "C2", "C3") for k in keys])
        for c in P.cases():
            if c not in have:
                continue
            r = have[c]; k3 = r["k3"]
            w.writerow([c, r["표면칸"], r["머리몫"], r["r_s"], r["r_u"], r["M0"]["서포트몫"]]
                       + [k3[m].get(k) for m in ("M1", "N", "N65", "X", "NX65", "C1", "C2", "C3") for k in keys])
    for c in ("은둔자", "오메가몬"):
        g = os.path.join(HERE, "out", "출력분할제약_%s.png" % c)
        if os.path.exists(g):
            shutil.copy(g, os.path.join(D, "그림", "제약_%s.png" % c))
    print("  ->", D)


def wait_ram():
    import psutil
    while True:
        gb = psutil.virtual_memory().available / 2 ** 30
        if gb >= MIN_RAM_GB:
            return gb
        print("  여유 RAM %.1fGB < %.1f — 30초 쉰다" % (gb, MIN_RAM_GB), flush=True)
        time.sleep(30)


if __name__ == "__main__":
    a = sys.argv[1:] or ["검사"]
    selfcheck()
    if a[0] == "검사":
        pass
    elif a[0] == "판정":
        verdict()
    elif a[0] == "논문자료":
        paper_data()
    elif a[0] == "그림":
        P.cases()
        for c in a[1:]:
            print("  RAM %.1fGB" % wait_ram(), flush=True)
            figure(c)
    elif a[0].isdigit():
        have = done()
        todo = [c for c in P.cases() if c not in have][: int(a[0])]
        for c in todo:
            print("  RAM %.1fGB · %s" % (wait_ram(), c), flush=True)
            run_case(c)
    else:
        P.cases()
        for c in a:
            print("  RAM %.1fGB · %s" % (wait_ram(), c), flush=True)
            run_case(c)
