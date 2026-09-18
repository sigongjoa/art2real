# -*- coding: utf-8 -*-
"""**생성선택 — 장마다 생성과 타원 기본 중 하나 고르기** (2026-09-19).

    python 생성선택.py 검사        자가검사만 (선택기 정의 · 한 장 빼기 · 신호 계산)
    python 생성선택.py 신호 [n]    아직 안 한 장 n 개 -> out/기록/생성선택_진행.jsonl
    python 생성선택.py 판정        -> out/기록/생성선택_<때>.json   (Q-천장을 맨 먼저)
    python 생성선택.py 그림        이긴 장 · 진 장을 정답과 나란히 -> out/생성선택.png

판정은 `claudedocs/plan_생성선택_20260919.md` 그대로다 — 돌리기 전에 적었다.
점수는 새로 안 잰다: `out/기록/생성깎기_진행.jsonl` v2 (속 채운 정답 · 격자 128·192) 를 그대로 읽는다.

**2026-09-19 실행 결과: `Q-천장` 에서 멈췄다.** 그래서 `신호` 명령과 `verdict` 의 Q-신호 · Q-이득 갈래는
**한 번도 안 돌았다** (계획 「분기」의 「Q-천장 짐 → 거기서 멈춘다」). 코드는 계획에 사전 등록한 정의 그대로
남겨 둔다 — 지우면 「무엇을 재기로 했었나」가 기록에서 사라진다. 자가검사는 그 갈래까지 검사한다.
"""
import json
import os
import sys
import time

import cv2
import numpy as np

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
for d in ("실험_20260915", "실험_20260918"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import hull as H
import win as W
from 겉면채점 import bench_cases

PROG = os.path.join(HERE, "out", "기록", "생성선택_진행.jsonl")
TAG = "생성선택 v1 · 실물28 · B=지금 기본 · G=생성∩hull+보충 · 원화 신호 + 09-18 이상신호 (2026-09-19)"
IOU_TAG = "생성깎기 v2 · 원형도 속채움 · TripoSG 3판맞춤 · ∩hull · +보충 · 속채운 정답 (2026-09-15)"
SIGJSON = os.path.join(HERE, "out", "기록", "이상신호_20260918_1208.json")
B, G = "지금 기본", "생성∩hull+보충"
GRIDS = ("iou", "iou·192")
BASE_MED = {"iou": 0.7413, "iou·192": 0.7265}       # 배관 ① — README 「5.」의 점수판 값
NBOOT, NRAND, SEED = 2000, 2000, 20260919
# 원화 · 중간 산출물에서 읽는 신호. 부호 = +1 이면 「클수록 생성이 이긴다」고 걸어 본다는 뜻이 아니라,
# 문턱을 양쪽 방향 다 시험하므로 여기선 이름만 쓴다.
ART = ("부피비", "면적비", "채움도", "둘레비", "구멍", "세로비")
ANOM = ("못덮음", "가는곳", "조각", "찢김", "실루엣", "불일치")


# ---------------------------------------------------------------- 신호

def mask_shape(m):
    """정면 마스크 하나에서 읽는 모양 값 — 채움도 · 둘레비 · 구멍 · 세로비."""
    u8 = m.astype(np.uint8)
    area = float(u8.sum())
    cnts, hier = cv2.findContours(u8, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if not cnts or area < 1:
        return {"채움도": 1.0, "둘레비": 1.0, "구멍": 0, "세로비": 1.0}
    outer = [c for c, h in zip(cnts, hier[0]) if h[3] < 0]
    peri = sum(cv2.arcLength(c, True) for c in outer)
    hull_area = sum(cv2.contourArea(cv2.convexHull(c)) for c in outer)
    ys, xs = np.nonzero(m)
    return {"채움도": round(area / max(hull_area, 1.0), 4),
            "둘레비": round(peri * peri / (4 * np.pi * area), 4),
            "구멍": int((hier[0][:, 3] >= 0).sum()),
            "세로비": round(float(np.ptp(ys) + 1) / max(float(np.ptp(xs) + 1), 1.0), 4)}


def one(case):
    """한 장의 신호. 복셀은 `생성깎기.variants` 로 다시 짓는다 (조각 수로 배관 검사)."""
    import 표면 as SF
    from 생성깎기 import variants
    t0 = time.time()
    vs, plain, axes, masks, bs = variants(case)
    vb, vg = vs[B], vs[G]
    r = {"case": case, "판": TAG,
         "부피비": round(float(vg.sum()) / max(float(vb.sum()), 1.0), 4),
         "면적비": round(float(masks["side"].sum()) / max(float(masks["front"].sum()), 1.0), 4),
         "조각_B": SF.pieces(vb), "조각_G": SF.pieces(vg)}
    r.update(mask_shape(masks["front"]))
    r["초"] = round(time.time() - t0, 1)
    return r


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            x = json.loads(line)
            if x.get("판") == TAG:
                out[x["case"]] = x
    return out


def run(n, only=()):
    import psutil
    done = rows()
    todo = [c for c in (only or cases()) if c not in done][:n]
    for c in todo:
        while psutil.virtual_memory().available < 6 * 2 ** 30:
            print("  여유 RAM %.1fGB — 30초 쉰다" % (psutil.virtual_memory().available / 2 ** 30), flush=True)
            time.sleep(30)
        r = one(c)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  %-38s 부피비 %.3f · 채움도 %.3f · 둘레비 %6.2f · 구멍 %d · %.0f초"
              % (c[:38], r["부피비"], r["채움도"], r["둘레비"], r["구멍"], r["초"]), flush=True)
    print("  남은 것 %d 장" % (len(cases()) - len(rows())))


# ---------------------------------------------------------------- 판정

def cases():
    return [c for c in bench_cases() if c != "소체"]


def iou_rows():
    out = {}
    for line in open(os.path.join(HERE, "out", "기록", "생성깎기_진행.jsonl"), encoding="utf-8"):
        x = json.loads(line)
        if x.get("판") == IOU_TAG:
            out[x["case"]] = x
    return out


def med(a):
    return round(float(np.median(a)), 5)


def pick_med(b, g, sel):
    """선택 벡터(참이면 생성)로 고른 값의 중앙."""
    return med(np.where(sel, g, b))


def boot_ci(d, rng, n=NBOOT):
    """중앙차의 95% 부트스트랩 구간 (장 재표본)."""
    idx = rng.integers(0, len(d), (n, len(d)))
    s = np.median(d[idx], axis=1)
    return [round(float(np.percentile(s, 2.5)), 5), round(float(np.percentile(s, 97.5)), 5)]


def auc(score, lab):
    """ROC AUC — 순위로 센다. lab 은 참/거짓."""
    lab = np.asarray(lab, bool)
    if lab.all() or (~lab).all():
        return 0.5
    r = np.asarray(score, float).argsort().argsort() + 1.0
    n1, n0 = lab.sum(), (~lab).sum()
    return float((r[lab].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def thresh_rule(x, y, w):
    """훈련 장에서 고르는 한 신호 · 한 문턱. y = 생성이 이겼나 · w = 이길 때의 IoU 이득.
    후보 문턱은 값들의 중점. 부호 두 방향 다 시험하고, **훈련 장의 IoU 이득 합**이 가장 큰 규칙을 고른다."""
    v = np.unique(x)
    cand = [(-np.inf, +1)] + [(t, s) for t in (v[:-1] + v[1:]) / 2 for s in (+1, -1)]
    best, bg = (-np.inf, +1), -np.inf
    for t, s in cand:
        sel = (x > t) if s > 0 else (x <= t)
        gain = float(w[sel].sum())
        if gain > bg:
            bg, best = gain, (t, s)
    return best


def apply_rule(x, rule):
    t, s = rule
    return (x > t) if s > 0 else (x <= t)


def verdict():
    rng = np.random.default_rng(SEED)
    R, S = iou_rows(), rows()
    cs = [c for c in cases() if c in R]
    out = {"판": TAG, "장": len(cs), "얼린집합": cs, "배관": {}}

    # ---- 배관 ① 기본 중앙 재현
    pipe_ok = True
    for t in GRIDS:
        m = med([R[c][B][t] for c in cs])
        out["배관"]["기본중앙_" + t] = m
        pipe_ok = pipe_ok and abs(m - BASE_MED[t]) < 1e-4 and len(cs) == 28
    # ---- 배관 ② 조각 수가 09-18 기록과 같나. **입력이 없으면 통과로 찍지 않는다** (검토 지적 5)
    old = {x["case"]: x["조각"] for x in json.load(open(SIGJSON, encoding="utf-8"))["순위"]}
    shared = [c for c in cs if c in S and c in old]
    if len(shared) < len(cs):
        out["배관"]["배관②"] = "미실시 — 신호 기록이 %d/%d 장뿐이다 (`신호` 를 먼저 돌려라)" % (len(shared), len(cs))
        pipe_ok = False
    else:
        bad = [c for c in shared if S[c]["조각_G"] != old[c]]
        out["배관"]["배관②"] = "통과 (%d장 조각 수 일치)" % len(shared) if not bad else "어긋남"
        out["배관"]["조각불일치"] = bad
        pipe_ok = pipe_ok and not bad
    out["배관"]["통과"] = bool(pipe_ok)

    # ---- Q-천장 (맨 먼저 · 기존 jsonl 만 읽는다)
    q1, ceil_gain = {}, {}
    for t in GRIDS:
        b = np.array([R[c][B][t] for c in cs])
        g = np.array([R[c][G][t] for c in cs])
        o = np.maximum(b, g)
        assert (o >= b).all() and (o >= g).all(), "배관 ③ — 완벽 선택기가 max 가 아니다"
        ceil_gain[t] = med(o) - med(b)
        ci = boot_ci(o - b, rng)                          # **한 번만 부른다** — 보고와 판정이 같은 표본 (검토 지적 4)
        # 점 추정(중앙의 차)과 같은 양의 구간도 같이 낸다 (검토 지적 6 — 계획의 G* 정의는 중앙의 차다)
        idx = rng.integers(0, len(cs), (NBOOT, len(cs)))
        dm = np.median(o[idx], axis=1) - np.median(b[idx], axis=1)
        q1[t] = {"기본중앙": med(b), "생성중앙": med(g), "천장중앙": med(o),
                 "천장이득": round(ceil_gain[t], 5), "천장이득 95%구간": [round(float(np.percentile(dm, 2.5)), 5), round(float(np.percentile(dm, 97.5)), 5)],
                 "짝지은차중앙": med(o - b), "짝지은차 95%구간": ci,
                 "천장이득(평균)": round(float(o.mean() - b.mean()), 5), "천장이득(최악사례)": round(float(o.min() - b.min()), 5),
                 "생성이이긴장": int((g > b).sum()),
                 "문턱": 0.020, "점추정통과": bool(ceil_gain[t] >= 0.020), "구간통과": bool(ci[0] > 0),
                 "통과": bool(ceil_gain[t] >= 0.020 and ci[0] > 0)}
        # 한 장 빼기 — 천장이득이 얼마나 흔들리나 (검토가 짚은 취약성)
        loo_g = [med(np.delete(o, i)) - med(np.delete(b, i)) for i in range(len(cs))]
        q1[t]["한장빼기 천장이득"] = [round(min(loo_g), 5), round(max(loo_g), 5)]
        q1[t]["한장빼기 문턱통과 횟수"] = int(sum(x >= 0.020 for x in loo_g))
    q1["통과"] = bool(q1["iou"]["통과"] and q1["iou·192"]["통과"])
    q1["갈림"] = bool(q1["iou"]["통과"] != q1["iou·192"]["통과"])
    out["Q-천장"] = q1

    # ---- 언제나-대조군 · 무작위 대조군 (천장과 무관하게 싸다 — 같이 적는다)
    ctrl = {}
    for t in GRIDS:
        b = np.array([R[c][B][t] for c in cs])
        g = np.array([R[c][G][t] for c in cs])
        o = np.maximum(b, g)
        gain = med(o) - med(b)
        n, k = len(cs), int((g > b).sum())
        rs = np.median(np.where(rng.random((NRAND, n)) < 0.5, g, b), axis=1)
        # **R_k 수맞춤 무작위** — 계획이 대조군 ② 로 못 박았는데 천장 절에서 안 쟀었다 (검토 지적 2).
        # 「생성으로 돌린 장 수」는 완벽 선택기와 같게 주고 **어느 장인지만** 무작위로 한다.
        sel = np.zeros((NRAND, n), bool)
        for j in range(NRAND):
            sel[j, rng.permutation(n)[:k]] = True
        rk = np.median(np.where(sel, g, b), axis=1) - med(b)
        # **짝 섞기 널** — G 점수를 장 사이에 섞어 B 와 짝지은 뒤 오라클을 잰다 (검토 지적 3).
        # 두 팔이 서로 무관할 때 max 산술만으로 나오는 이득이다. 실제가 이보다 낮으면 **상보성이 우연 이하**다.
        pm = np.array([med(np.maximum(b, rng.permutation(g))) - med(b) for _ in range(NRAND)])
        ctrl[t] = {"C0 언제나기본": med(b), "C1 언제나생성": med(g), "O 완벽": med(o), "천장이득": round(gain, 5),
                   "R 무작위중앙": round(float(np.median(rs)), 5),
                   "R 무작위 95%": [round(float(np.percentile(rs, 2.5)), 5), round(float(np.percentile(rs, 97.5)), 5)],
                   "R 무작위가 천장이득 이상일 확률": round(float((rs - med(b) >= gain).mean()), 5),
                   "R_k 수맞춤 k": k, "R_k 이득중앙": round(float(np.median(rk)), 5),
                   "R_k 95%": [round(float(np.percentile(rk, 2.5)), 5), round(float(np.percentile(rk, 97.5)), 5)],
                   "R_k 가 천장이득 이상일 확률": round(float((rk >= gain).mean()), 5),
                   "짝섞기 오라클이득 중앙": round(float(np.median(pm)), 5),
                   "짝섞기 95%": [round(float(np.percentile(pm, 2.5)), 5), round(float(np.percentile(pm, 97.5)), 5)],
                   "짝섞기가 실제 이상일 확률": round(float((pm >= gain).mean()), 5)}
    out["대조군"] = ctrl

    # ---- 강건성 (사후 · 계획에 없던 것 — 판정을 바꾸지 않는다)
    rb = {}
    rk2 = lambda a: a.argsort().argsort() + 1.0
    for t in GRIDS:
        b = np.array([R[c][B][t] for c in cs])
        g = np.array([R[c][G][t] for c in cs])
        o = np.maximum(b, g)
        idx = rng.integers(0, len(cs), (NBOOT, len(cs)))
        dm = np.median(o[idx], axis=1) - np.median(b[idx], axis=1)     # 점수판이 실제로 재는 양: 중앙의 차
        rs = np.median(np.where(rng.random((NRAND, len(cs))) < 0.5, g, b), axis=1)
        srt = np.argsort(b)
        rb[t] = {"중앙의차 95%구간": [round(float(np.percentile(dm, 2.5)), 5), round(float(np.percentile(dm, 97.5)), 5)],
                 "중앙의차 > 0 비율": round(float((dm > 0).mean()), 4),
                 "무작위가 기본을 이기는 비율": round(float((rs > med(b)).mean()), 4),
                 "무작위가 +0.020 을 넘는 비율": round(float((rs > med(b) + 0.020).mean()), 4),
                 "중앙을 정하는 장": [cs[srt[len(cs) // 2 - 1]], cs[srt[len(cs) // 2]]],
                 "천장에서 값이 바뀐 장": int((o > b).sum())}
        # 커버리지 곡선 — 진짜 이득이 큰 장부터 k 개만 G 로 돌렸을 때의 중앙 이득.
        # 천장이 몇 장에서 나오는지를 보여 준다 (검토가 계산한 것 · risk-coverage 의 우리 판)
        order = np.argsort(-(g - b))
        cov = []
        for k in range(0, len(cs) + 1):
            s = np.zeros(len(cs), bool); s[order[:k]] = True
            cov.append(round(med(np.where(s, g, b)) - med(b), 5))
        rb[t]["커버리지곡선"] = cov
        # 두 팔 점수의 상관 — 짝 섞기 널이 왜 실제보다 높은지의 기전. 같은 장에서 같이 어렵다.
        rb[t]["두팔상관 피어슨"] = round(float(np.corrcoef(b, g)[0, 1]), 4)
        rb[t]["두팔상관 스피어만"] = round(float(np.corrcoef(rk2(b), rk2(g))[0, 1]), 4)
        rb[t]["천장에 닿는 최소 장 수"] = int(next(k for k, v in enumerate(cov) if v >= max(cov) - 1e-9))
    # 선택 대상을 넷으로 늘려도 천장이 오르나 (계획은 두 팔로 제한했다 — 그 제한이 원인인지 본다)
    for t in GRIDS:
        arms = [np.array([R[c][k][t] for c in cs]) for k in (B, "생성", "생성∩hull", G)]
        rb[t]["네팔천장이득"] = round(med(np.maximum.reduce(arms)) - med(arms[0]), 5)
    out["강건성(사후)"] = rb

    # ---- 이미 가진 량이 라우터가 되나 (사후 · 순위상관만 — Q-신호를 대신하지 않는다)
    anom = {x["case"]: x for x in json.load(open(SIGJSON, encoding="utf-8"))["순위"]}
    d = np.array([R[c][G]["iou"] - R[c][B]["iou"] for c in cs])
    F = {k: np.array([float(anom[c][k]) for c in cs]) for k in ANOM + ("이상점수",)}
    if all(c in S for c in cs):       # 이 바퀴에서 더한 원화 · 중간 산출물 신호 (부피비 등)
        F.update({k: np.array([float(S[c][k]) for c in cs]) for k in ART})
    for arm, tg in ((B, "B"), (G, "G")):
        for k in ("못덮음_front", "못덮음_side", "넘침_front", "넘침_side"):
            F[tg + "." + k] = np.array([R[c][arm][k] for c in cs])
    F["B.iou"] = np.array([R[c][B]["iou"] for c in cs])
    rk = lambda a: a.argsort().argsort() + 1.0
    rho = {k: round(float(np.corrcoef(rk(v), rk(d))[0, 1]), 4) for k, v in F.items()}
    top = max(rho, key=lambda k: abs(rho[k]))
    out["기존량 순위상관(사후)"] = {"량 수": len(rho), "최대절대": abs(rho[top]), "최대량": top,
                              "부호주의": "조각 수 · 이상점수가 양수 = 부서진 장일수록 생성이 이긴다 (라우팅과 반대 방향)",
                              "전부": dict(sorted(rho.items(), key=lambda kv: -abs(kv[1])))}

    if not q1["통과"]:
        out["Q-신호"] = "안 함 — Q-천장에서 멈춘다 (계획 「분기」)"
        out["Q-이득"] = "안 함"
        out["다음"] = ("장별 선택기로는 점수판 중앙이 못 오른다. 계획의 후보 (나) — 생성 메시를 층 속채움으로 메운 뒤 ∩hull."
                       if not q1["갈림"] else "격자 128·192 가 갈렸다 — 결론을 안 쓴다")
        return save(out)

    # ---- Q-신호 · Q-이득 (천장이 섰을 때만)
    cs2 = [c for c in cs if c in S]
    lab = np.array([R[c][G]["iou"] > R[c][B]["iou"] for c in cs2])
    anom = {x["case"]: x for x in json.load(open(SIGJSON, encoding="utf-8"))["순위"]}
    feats = {n: np.array([float(S[c][n]) for c in cs2]) for n in ART}
    feats.update({n: np.array([float(anom[c][n]) for c in cs2]) for n in ANOM if all(n in anom[c] for c in cs2)})
    q2 = {"장": len(cs2), "생성이이긴장": int(lab.sum()), "신호": {}}
    for n, x in feats.items():
        a = auc(x, lab)
        q2["신호"][n] = {"AUC": round(max(a, 1 - a), 4), "방향": "클수록 생성" if a >= 0.5 else "작을수록 생성"}
    best = max(q2["신호"], key=lambda n: q2["신호"][n]["AUC"])
    q2["최고신호"], q2["최고AUC"] = best, q2["신호"][best]["AUC"]
    q2["문턱"] = 0.75
    # **AUC 는 `max(a, 1-a)` 로 방향을 사후에 고르고 량도 여럿에서 고른다 — 널 중앙이 0.5 가 아니다.**
    # 문턱 0.75 를 그냥 쓰면 느슨하다. 라벨을 섞은 널에서 「가장 좋은 량의 AUC」 분포를 내고 95 분위를 같이 적는다.
    nul = np.zeros(NRAND)
    for j in range(NRAND):
        y = rng.permutation(lab)
        nul[j] = max(max(auc(x, y), 1 - auc(x, y)) for x in feats.values())
    q2["널 최고AUC 95분위"] = round(float(np.percentile(nul, 95)), 4)
    q2["널을 넘나"] = bool(q2["최고AUC"] > q2["널 최고AUC 95분위"])

    # 한 장 빼기 — 27장에서 문턱을 고르고 남긴 장에 건다
    loo, full = {}, {}
    for t in GRIDS:
        b = np.array([R[c][B][t] for c in cs2])
        g = np.array([R[c][G][t] for c in cs2])
        w = g - b
        x = feats[best]
        sel_loo = np.zeros(len(cs2), bool)
        for i in range(len(cs2)):
            k = np.ones(len(cs2), bool); k[i] = False
            sel_loo[i] = apply_rule(x[i:i + 1], thresh_rule(x[k], lab[k], w[k]))[0]
        sel_full = apply_rule(x, thresh_rule(x, lab, w))
        rk = np.zeros(NRAND)
        for j in range(NRAND):
            p = rng.permutation(len(cs2))[:int(sel_loo.sum())]
            s = np.zeros(len(cs2), bool); s[p] = True
            rk[j] = np.median(np.where(s, g, b))
        cg = med(np.maximum(b, g)) - med(b)
        loo[t] = {"S* 중앙": pick_med(b, g, sel_loo), "S* 생성고른장": int(sel_loo.sum()),
                  "S* 맞힌장": int((sel_loo == lab).sum()) if t == "iou" else None,
                  "S 전체적합중앙": pick_med(b, g, sel_full), "S 생성고른장": int(sel_full.sum()),
                  "기본중앙": med(b), "천장중앙": med(np.maximum(b, g)),
                  "천장몫": round((pick_med(b, g, sel_loo) - med(b)) / cg, 4) if cg > 0 else None,
                  "R_k 수맞춤 중앙": round(float(np.median(rk)), 5),
                  "R_k 95%": [round(float(np.percentile(rk, 2.5)), 5), round(float(np.percentile(rk, 97.5)), 5)],
                  "통과": bool(pick_med(b, g, sel_loo) > med(b))}
        full[t] = loo[t]
    q2["한장빼기정확도"] = round(float(loo["iou"]["S* 맞힌장"]) / len(cs2), 4)
    # 계획 「Q-신호」의 둘째 조건 — 한 장 빼기 정확도가 장 수 맞춤 무작위 선택기의 정확도 95 분위를 넘어야 한다.
    k = int(loo["iou"]["S* 생성고른장"])
    accs = np.zeros(NRAND)
    for j in range(NRAND):
        s = np.zeros(len(cs2), bool); s[rng.permutation(len(cs2))[:k]] = True
        accs[j] = (s == lab).mean()
    q2["R_k 정확도 95분위"] = round(float(np.percentile(accs, 95)), 4)
    q2["정확도가 널을 넘나"] = bool(q2["한장빼기정확도"] > q2["R_k 정확도 95분위"])
    q2["통과"] = bool(q2["최고AUC"] >= 0.75 and q2["널을 넘나"] and q2["정확도가 널을 넘나"])
    out["Q-신호"] = q2
    q3 = dict(loo)
    q3["천장몫문턱"] = 0.5
    q3["통과"] = bool(all(loo[t]["통과"] for t in GRIDS) and (loo["iou"]["천장몫"] or 0) >= 0.5)
    out["Q-이득"] = q3
    out["다음"] = ("기본값 교체 후보 — 새 에이전트 검토 뒤 사람이 결정" if q2["통과"] and q3["통과"]
                   else "신호로는 못 가른다 — 천장은 있으나 열쇠가 없다")
    return save(out)


def save(out):
    p = os.path.join(HERE, "out", "기록", "생성선택_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    q = out["Q-천장"]
    print("  배관 %s · %s" % (out["배관"]["통과"], out["배관"].get("배관②")))
    for t in GRIDS:
        print("  Q-천장 %-8s 기본 %.4f → 천장 %.4f · 이득 %+.4f (문턱 +0.020 → %s) · 구간 %s (→ %s) · 평균이득 %+.4f · 한장빼기 %s %d/28"
              % (t, q[t]["기본중앙"], q[t]["천장중앙"], q[t]["천장이득"], "통과" if q[t]["점추정통과"] else "짐",
                 q[t]["짝지은차 95%구간"], "통과" if q[t]["구간통과"] else "짐", q[t]["천장이득(평균)"],
                 q[t]["한장빼기 천장이득"], q[t]["한장빼기 문턱통과 횟수"]))
    for t in GRIDS:
        c = out["대조군"][t]
        print("  대조군 %-8s 동전 P(≥천장) %.4f · R_k(k=%d) 이득 %+.4f P(≥천장) %.4f · **짝섞기 오라클이득 %+.4f · P(≥실제) %.3f**"
              % (t, c["R 무작위가 천장이득 이상일 확률"], c["R_k 수맞춤 k"], c["R_k 이득중앙"],
                 c["R_k 가 천장이득 이상일 확률"], c["짝섞기 오라클이득 중앙"], c["짝섞기가 실제 이상일 확률"]))
    for t in GRIDS:
        print("  커버리지 %-8s 천장에 닿는 최소 장 수 %d / %d" % (t, out["강건성(사후)"][t]["천장에 닿는 최소 장 수"], out["장"]))
    if isinstance(out.get("Q-신호"), dict):
        s = out["Q-신호"]
        print("  Q-신호 최고 %s AUC %.3f (문턱 0.75) · 한 장 빼기 정확도 %.3f · %s"
              % (s["최고신호"], s["최고AUC"], s["한장빼기정확도"], "통과" if s["통과"] else "짐"))
        for t in GRIDS:
            e = out["Q-이득"][t]
            print("  Q-이득 %-8s S* %.4f (기본 %.4f · 천장 %.4f · 몫 %s) · R_k %.4f %s"
                  % (t, e["S* 중앙"], e["기본중앙"], e["천장중앙"], e["천장몫"], e["R_k 수맞춤 중앙"], e["R_k 95%"]))
    else:
        print("  " + str(out["Q-신호"]))
    print("  다음: %s" % out["다음"])
    print("  ->", p)
    return out


# ---------------------------------------------------------------- 그림

def figure():
    """생성이 크게 이긴 장 · 크게 진 장을 정답 · 지금 기본 · 생성과 나란히."""
    import trimesh
    from PIL import Image, ImageDraw
    import 오라클 as O
    import 속채움그림 as SC
    from 점수판그림 import FRONT_VIEW, SHAPE
    from 계획 import _font
    from 생성깎기 import variants
    R = iou_rows()
    cs = [c for c in cases() if c in R]
    d_ = sorted(cs, key=lambda c: R[c][G]["iou"] - R[c][B]["iou"])
    picks = [(c, "생성이 진다") for c in d_[:4]] + [(c, "생성이 이긴다") for c in d_[-4:][::-1]]
    S_, Gp, TOP, LW = SC.S, 14, 150, 280
    cols = ("정답 (GT)", "지금 기본 B", "생성∩hull+보충 G")
    im = Image.new("RGB", (LW + len(cols) * (S_ + Gp) + 20, TOP + len(picks) * (S_ + Gp) + 20), "white")
    dr = ImageDraw.Draw(im)
    dr.text((24, 14), "생성이 이기는 장과 지는 장 — 갈림은 「속이 비었나」다", font=_font(30), fill=(20, 20, 20))
    dr.text((24, 58), "위 넷 = 생성이 크게 지는 장 (망토 · 치마 · 머리) · 아래 넷 = 생성이 크게 이기는 장 (메카 · 로봇 · 사람형)",
            font=_font(17), fill=(90, 90, 90))
    dr.text((24, 84), "같은 각도 · 같은 틀 · 자르지 않음 · 숫자 = 속 채운 정답 IoU (격자 128)", font=_font(17), fill=(90, 90, 90))
    for i, n in enumerate(cols):
        dr.text((LW + i * (S_ + Gp) + 20, TOP - 30), n, font=_font(20), fill=(30, 30, 30))
    SC.VIEW = FRONT_VIEW
    import 정답 as J
    for rr, (c, why) in enumerate(picks):
        y = TOP + rr * (S_ + Gp)
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        vs, plain, axes, masks, bs = variants(c)
        meshes = [truth] + [O.C.to_mesh(vs[k], axes) for k in (B, G)]
        grids = [J.grid(m) for m in meshes]
        lo = np.minimum.reduce([o for _, o in grids])
        hi = np.maximum.reduce([o + g.shape for g, o in grids])
        full = []
        for g, o in grids:
            a = np.zeros(hi - lo + 2, bool)
            a[tuple(slice(o[i] - lo[i] + 1, o[i] - lo[i] + 1 + g.shape[i]) for i in range(3))] = g
            full.append(a)
        r_, u_, _ = SC.basis()
        pts = np.argwhere(np.logical_or.reduce(full))
        X, Y = pts @ r_, pts @ u_
        span = max(np.ptp(X), np.ptp(Y)) * 1.06
        frame = (((X.max() + X.min()) / 2 - span / 2, (Y.max() + Y.min()) / 2 - span / 2), span)
        dr.text((24, y + S_ // 2 - 30), c[:26], font=_font(17), fill=(30, 30, 30))
        dr.text((24, y + S_ // 2 - 6), "%s  %+.3f" % (why, R[c][G]["iou"] - R[c][B]["iou"]), font=_font(17),
                fill=(160, 40, 40) if "진다" in why else (40, 110, 60))
        labels = ["", "%.3f" % R[c][B]["iou"], "%.3f" % R[c][G]["iou"]]
        for i, a in enumerate(full):
            t = SC.paint([(a, SHAPE)], frame)
            x = LW + i * (S_ + Gp)
            im.paste(Image.fromarray(cv2.cvtColor(t, cv2.COLOR_BGR2RGB)), (x, y))
            if labels[i]:
                dr.text((x + 8, y + S_ - 24), labels[i], font=_font(18), fill=(40, 40, 40))
        print("  %s 그림" % c, flush=True)
    p = os.path.join(HERE, "out", "생성선택.png")
    im.save(p)
    print("  ->", p)


# ---------------------------------------------------------------- 자가검사

def selfcheck():
    # 완벽 선택기는 max 이고, 중앙은 늘 기본 이상이다
    b = np.array([0.1, 0.5, 0.9, 0.3, 0.7])
    g = np.array([0.4, 0.2, 0.95, 0.8, 0.1])
    o = np.maximum(b, g)
    assert med(o) >= med(b) and med(o) >= med(g), "천장이 두 팔보다 낮다"
    assert pick_med(b, g, g > b) == med(o), "완벽 선택 = max 가 아니다"
    assert pick_med(b, g, np.zeros(5, bool)) == med(b), "언제나 기본이 기본이 아니다"
    # 문턱 규칙: 신호가 라벨을 그대로 알려주면 훈련 장을 다 맞혀야 한다
    x = np.array([0.0, 1.0, 0.0, 1.0, 1.0, 0.0])
    lab = x > 0.5
    w = np.where(lab, +0.1, -0.1)
    assert (apply_rule(x, thresh_rule(x, lab, w)) == lab).all(), "완벽 신호에서 문턱이 안 선다"
    # 부호가 뒤집힌 신호도 잡아야 한다
    assert (apply_rule(-x, thresh_rule(-x, lab, w)) == lab).all(), "반대 부호 신호를 못 잡는다"
    # 쓸모없는 신호에서는 한 장 빼기가 무너져야 한다 (전체 적합만 이기는 자리)
    assert auc(x, lab) == 1.0 and abs(auc(np.arange(6.0), np.array([1, 0, 1, 0, 1, 0], bool)) - 0.5) < 0.2, "AUC 가 틀렸다"
    # 모양 신호 — 답을 아는 도형
    m = np.zeros((200, 200), bool); m[50:150, 60:140] = True
    s = mask_shape(m)
    assert abs(s["채움도"] - 1.0) < 0.05 and s["구멍"] == 0, "속 찬 사각형 %s" % s
    m2 = m.copy(); m2[80:120, 80:120] = False
    assert mask_shape(m2)["구멍"] == 1, "구멍을 못 센다"
    m3 = np.zeros((200, 200), bool); m3[50:150, 60:140] = True; m3[50:100, 80:120] = False   # C 모양 — 파였다
    assert mask_shape(m3)["채움도"] < 0.95, "파인 실루엣에서 채움도가 안 떨어진다"
    print("  자가검사 통과 — 완벽 선택기 · 문턱 규칙(양쪽 부호) · AUC · 모양 신호")


def main():
    a = sys.argv[1:] or ["검사"]
    selfcheck()
    if a[0] == "검사":
        return
    H.register_sheets()
    if a[0] == "신호":
        rest = a[1:]
        n = int(rest[0]) if rest and rest[0].isdigit() else 28
        run(n, only=[c for c in rest if not c.isdigit()])
    elif a[0] == "판정":
        verdict()
    elif a[0] == "그림":
        figure()


if __name__ == "__main__":
    main()
