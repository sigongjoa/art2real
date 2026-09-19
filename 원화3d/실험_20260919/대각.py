# -*- coding: utf-8 -*-
"""**대각 실루엣 — 복셀을 뺀 팔이 사람 각도에서 나은가** (2026-09-19).

    python 대각.py 검사        자가검사 + 배관 1·4 (기록만 있으면 도는 것)
    python 대각.py [n]         얼린 28장 중 아직 안 한 장 n 개 -> out/기록/대각_진행.jsonl
    python 대각.py 판정        -> out/기록/대각_<때>.json
    python 대각.py 그림        -> out/대각_접촉지.png · out/대각_장별.png

판정은 `claudedocs/plan_대각실루엣_20260919.md` 「Q」 절 그대로다 — 돌리기 전에 적었다. **문턱을 안 고친다.**

점수판의 자(IoU 128 · 못덮음 · 넘침)는 전부 **축 방향**이라 두 팔을 못 가른다 (상관 +0.935).
이 스크립트는 정답과 판본을 수직축 둘레로 30 · 45 · 60° 돌려 정면으로 찍은 실루엣을 잰다.
판본은 여섯이고 **하나 만들고 재고 바로 버린다** — 여섯을 동시에 들면 봉우리가 20GB 를 넘본다 (09-19 보충경계 실측 27.1GB).
"""
import gc
import json
import os
import sys
import time

import cv2
import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
for d in ("실험_20260913", "실험_20260915", "실험_20260916", "실험_20260918", "실험_20260919"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import hull as H
import win as W
import 대조 as C_
import 정답 as J
from 겉면채점 import bench_cases, fill_slices
from 생성깎기 import build as gen_build, voxelize, sil_fit
from 면 import roughness
from 불리언 import fitted
import 보충격자 as BG
import 보충경계 as BE

PROG = os.path.join(HERE, "out", "기록", "대각_진행.jsonl")
SILD = os.path.join(HERE, "out", "기록", "대각_실루엣")
TAG = "대각 v1 · 판본 6 · 대각 30·45·60 · 구멍 · 축 1024 부풀리기없음 · IoU128 (2026-09-19)"

ANG = (30, 45, 60)
ROTSIGN = +1                      # z 둘레 회전 부호. 배관 1 이 정한다 — 안 맞으면 멈추고 보고한다
MINPX = 20                        # 구멍으로 셀 배경 성분의 최소 화소
HEAVY_F = 600_000                 # 이 면 수를 넘는 판본은 거칠기를 뺀다 (표시한다)
NPT = BE.NPT                      # 60000 — 09-18 · 09-19 와 같은 자

VARS = ("V 현행", "A 복셀배포", "D′ 제안", "G 생", "균일@D′", "D′→복셀")
관찰4 = ("mech_Drill_8uBbH7Dvmb", "robot_Robot_ejDr8lRglP",
         "cloak_Chest_Closed_AngpV0HxD8", "avatarsample_d")
겹 = BE.겹                        # 두 겹 형상 5장 — 면 100만 이상. 맨 뒤로 민다

# 09-19 오케스트레이터 스크래치 (재현 기준값 · 판정 아님)
관찰값 = {"mech_Drill_8uBbH7Dvmb": {"V 현행": 0.558, "B∩hull": 0.756,
                                    "구멍": {"V 현행": 8, "B∩hull": 4, "G 생": 4, "정답": 2}},
          "robot_Robot_ejDr8lRglP": {"V 현행": 0.828, "B∩hull": 0.741,
                                     "구멍": {"V 현행": 2, "B∩hull": 8, "G 생": 10, "정답": 1}}}


# ── 자 ───────────────────────────────────────────────────────────────────────

def rotz(V, deg):
    """수직축(z) 둘레 회전. 판본과 정답에 **같은 부호**로 건다."""
    t = np.radians(ROTSIGN * float(deg))
    c, s = np.cos(t), np.sin(t)
    R = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
    return np.asarray(V, float) @ R.T


def sil(mesh, view="front", bs=None, deg=0.0):
    """1024² 직교 실루엣. **부풀리기 없음** — `win.silhouette` 그대로다."""
    V = np.asarray(mesh.vertices, float)
    if deg:
        V = rotz(V, deg)
    return np.asarray(W.silhouette(V, np.asarray(mesh.faces), view, bs)).astype(bool)


def iou(a, b):
    return round(float((a & b).sum() / max((a | b).sum(), 1)), 5)


def holes(mask, minpx=MINPX):
    """실루엣 안쪽에 뚫린 구멍 수 — 배경 성분 중 **테두리에 안 닿고** minpx 이상인 것."""
    n, lab = cv2.connectedComponents((~mask).astype(np.uint8), connectivity=4)
    edge = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])).tolist())
    cnt = np.bincount(lab.ravel(), minlength=n)
    return int(sum(1 for i in range(1, n) if i not in edge and cnt[i] >= minpx))


def 축(mesh, masks, bs):
    """축 실루엣 못덮음 · 넘침 (0° · 1024 · **부풀리기 없음**). 정면 · 측면의 최대값 — 09-18/19 와 같은 규약."""
    mc, ov = [], []
    for v in ("front", "side"):
        s = sil(mesh, v, bs if v == "back" else None)
        m = masks[v]
        mc.append(float((m & ~s).sum() / max(m.sum(), 1)))
        ov.append(float((s & ~m).sum() / max(s.sum(), 1)))
    return round(max(mc), 4), round(max(ov), 4)


def iou128(truth_grids, mesh):
    """(점수판 규약, 양쪽채움 규약). 점수판(`겉면채점.bench_one`)은 **정답만** 채운다 — 배관 4 가 그 값을 맞댄다."""
    TF, T, ot = truth_grids
    Gd, og = J.grid(mesh, J.PITCH)
    A, B = J.common(TF, ot, Gd, og)
    a = round(float((A & B).sum() / max((A | B).sum(), 1)), 5)
    A2, B2 = J.common(TF, ot, fill_slices(Gd), og)
    b = round(float((A2 & B2).sum() / max((A2 | B2).sum(), 1)), 5)
    return a, b


# ── 한 장 ────────────────────────────────────────────────────────────────────

def 잰다(m, tsil, masks, bs, tg, 가볍=False):
    r = {"면": int(len(m.faces)), "부피": round(float(abs(m.volume)), 6), "닫힘": bool(m.is_watertight)}
    s45 = None
    for a in ANG:
        s = sil(m, "front", None, a)
        r["대각%d" % a] = iou(s, tsil[a])
        if a == 45:
            r["구멍45"] = holes(s)
            s45 = s
    r["못덮음"], r["넘침"] = 축(m, masks, bs)
    r["iou128"], r["iou128양쪽"] = iou128(tg, m)
    if 가볍 and len(m.faces) <= HEAVY_F:
        r["거칠기"] = roughness(m, n=NPT)["거칠기"]
    else:
        r["거칠기생략"] = True
    gc.collect()
    return r, s45


def one(case):
    t0 = time.time()
    봉 = {"시작": BE.봉우리GB()}
    찍 = lambda k: 봉.__setitem__(k, BE.봉우리GB())

    masks, bs, plain, base, axes = gen_build(case)
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    tsil = {a: sil(truth, "front", None, a) for a in ANG}
    T, ot = J.grid(truth, J.PITCH)
    tg = (fill_slices(T), T, ot)
    out = {"case": case, "판": TAG, "회전부호": ROTSIGN,
           "정답": {"구멍45": holes(tsil[45]), "면": int(len(truth.faces))}}
    sils = {"정답": tsil[45]}
    del truth
    찍("정답")

    rec = {}
    m = C_.to_mesh(base, axes)                                   # V — 지금 점수판 기본
    rec["V 현행"], sils["V 현행"] = 잰다(m, tsil, masks, bs, tg, 가볍=True)
    del m, base
    gc.collect()
    찍("V")

    ctx = BE.prepare(case)                                       # 불리언 · hull · 보충 기둥 · 높이장
    찍("prepare")

    s = sil(ctx["bool"], "front", None, 45)                      # 배관 1 기준값 (판본 아님)
    out["B∩hull"] = {"대각45": iou(s, tsil[45]), "구멍45": holes(s), "면": int(len(ctx["bool"].faces))}
    del s
    찍("B∩hull")

    m = fitted(case, masks)                                      # G — TripoSG 생
    rec["G 생"], sils["G 생"] = 잰다(m, tsil, masks, bs, tg, 가볍=True)
    del m
    gc.collect()
    찍("G")

    m = BG.make(ctx, "A 복셀+보충")                              # A — 생성∩hull+보충 복셀판 (현행 배포)
    rec["A 복셀배포"], sils["A 복셀배포"] = 잰다(m, tsil, masks, bs, tg, 가볍=True)
    del m
    gc.collect()
    찍("A")

    m = BE.make(ctx, "D′ 보충경계")                              # D′ — 제안
    rec["D′ 제안"], sils["D′ 제안"] = 잰다(m, tsil, masks, bs, tg, 가볍=True)
    vol = float(abs(m.volume))
    찍("D′")
    vx = voxelize(m, axes)
    del m
    gc.collect()
    # 배관 2 — 09-19 보충경계와 **같은 자**(복셀 + 5×5 부풀리기)로 D′ 못덮음을 다시 잰다
    out["재현_못덮음"] = round(float(max(sil_fit(vx, masks, bs, axes)[k] for k in ("못덮음_front", "못덮음_side"))), 4)
    m = C_.to_mesh(vx, axes)                                     # D′→복셀 — 해상도 대조군
    del vx
    gc.collect()
    rec["D′→복셀"], _ = 잰다(m, tsil, masks, bs, tg, 가볍=True)
    del m, ctx
    gc.collect()
    찍("D′→복셀")

    try:                                                         # 균일@D′ — 정보 0 대조군
        m, t = H.even_control(plain, axes, vol)
        rec["균일@D′"], _ = 잰다(m, tsil, masks, bs, tg, 가볍=True)
        rec["균일@D′"]["침식t"] = round(float(t), 4)
        rec["균일@D′"]["부피오차"] = round(rec["균일@D′"]["부피"] / max(vol, 1e-12) - 1, 4)
        del m
    except AssertionError as e:
        rec["균일@D′"] = {"실패": str(e)}                        # 배관 3 — 이 장은 Q6 에서 뺀다
    del plain
    gc.collect()
    찍("균일")

    out["판본"] = rec
    out["초"] = round(time.time() - t0, 1)
    out["봉우리GB"] = BE.봉우리GB()
    out["단계봉우리GB"] = 봉
    out["여유GB"] = BE.여유GB()

    os.makedirs(SILD, exist_ok=True)
    np.savez_compressed(os.path.join(SILD, case + ".npz"),
                        **{k: np.packbits(v) for k, v in sils.items()})
    return out


# ── 기록 ─────────────────────────────────────────────────────────────────────

def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[r["case"]] = r
    return out


def 순서():
    """얼린 28장. **배관 1 을 먼저 통과시키려고 드릴 · 로봇을 맨 앞에** 두고, 두 겹 5장은 맨 뒤로 민다."""
    cs = [c for c in bench_cases() if c != "소체"]
    앞 = [c for c in ("mech_Drill_8uBbH7Dvmb", "robot_Robot_ejDr8lRglP") if c in cs]
    뒤 = [c for c in cs if c in 겹 and c not in 앞]
    return 앞 + [c for c in cs if c not in 앞 and c not in 뒤] + 뒤


def 배관1(r):
    """4장 관찰값 재현 — 드릴 45° V 0.558 · B∩hull 0.756 (±0.01). **어긋나면 회전 규약이 다른 것이다.**"""
    k = 관찰값.get(r["case"])
    if not k:
        return None
    got = {"V 현행": r["판본"]["V 현행"]["대각45"], "B∩hull": r["B∩hull"]["대각45"]}
    d = {n: round(got[n] - k[n], 4) for n in got}
    return {"기대": {n: k[n] for n in got}, "잰값": got, "차": d,
            "통과": bool(max(abs(v) for v in d.values()) <= 0.01)}


def run(n, cases=None):
    done = rows()
    todo = [c for c in (cases or 순서()) if c not in done][:n]
    for c in todo:
        for _ in range(40):                                      # 봉우리 예산 12GB — 여유가 없으면 시작도 안 한다
            if BE.여유GB() >= 8:
                break
            print("  %-38s 대기 — 여유 %.1fGB (8GB 필요)" % (c[:38], BE.여유GB()), flush=True)
            time.sleep(30)
        else:
            print("  %-38s 건너뜀 — 20분 기다려도 여유 8GB 미만" % c[:38], flush=True)
            continue
        r = one(c)
        g = 배관1(r)
        if g:
            r["배관1"] = g
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        v, d = r["판본"]["V 현행"], r["판본"]["D′ 제안"]
        print("  %-38s 45° V %.3f  A %.3f  D′ %.3f  G %.3f  균일 %s  D′→복셀 %.3f  (D′−V %+.3f) · 구멍 정답%d V%d D′%d · %.0f초 · %.1fGB"
              % (c[:38], v["대각45"], r["판본"]["A 복셀배포"]["대각45"], d["대각45"], r["판본"]["G 생"]["대각45"],
                 ("%.3f" % r["판본"]["균일@D′"]["대각45"]) if "대각45" in r["판본"]["균일@D′"] else "실패",
                 r["판본"]["D′→복셀"]["대각45"], d["대각45"] - v["대각45"],
                 r["정답"]["구멍45"], v["구멍45"], d["구멍45"], r["초"], r["봉우리GB"]), flush=True)
        if g:
            print("    배관1 %s — %s" % ("통과" if g["통과"] else "짐", json.dumps(g["차"], ensure_ascii=False)), flush=True)
            if not g["통과"]:
                print("    ** 배관 1 이 졌다. 회전 규약이 다르다 — 여기서 멈춘다. **", flush=True)
                return


# ── 판정 ─────────────────────────────────────────────────────────────────────

def _st(d):
    """짝지은 차 한 뭉치 -> 중앙 · 평균 · 최악 · 최선 · 승."""
    a = np.asarray(d, float)
    return {"중앙": round(float(np.median(a)), 5), "평균": round(float(a.mean()), 5),
            "최악": round(float(a.min()), 5), "최선": round(float(a.max()), 5),
            "승": int((a > 0).sum()), "n": int(len(a))}


def verdict():
    rs = rows()
    전체 = 순서()
    cs = [c for c in 전체 if c in rs]
    안잰 = [c for c in 전체 if c not in rs]
    cs24 = [c for c in cs if c not in 관찰4]
    P = lambda c, v, k: rs[c]["판본"][v][k]

    def 쌍(a, b, k, sel):
        return _st([P(c, a, k) - P(c, b, k) for c in sel])

    def 셋(a, b, k):
        """분모 셋 — 28(빠진 장 표시) · 4장 뺀 24 · 완주."""
        return {"완주(%d)" % len(cs): 쌍(a, b, k, cs),
                "24장(4장 뺌 · %d)" % len(cs24): 쌍(a, b, k, cs24),
                "28장 목표": {"안 잰 장": 안잰, "n": len(cs)}}

    q6 = [c for c in cs if "대각45" in rs[c]["판본"]["균일@D′"]
          and abs(rs[c]["판본"]["균일@D′"].get("부피오차", 1)) <= 0.01]
    q6_24 = [c for c in q6 if c not in 관찰4]

    d1, d1_24 = 쌍("D′ 제안", "V 현행", "대각45", cs), 쌍("D′ 제안", "V 현행", "대각45", cs24)
    d30, d60 = 쌍("D′ 제안", "V 현행", "대각30", cs), 쌍("D′ 제안", "V 현행", "대각60", cs)
    q = {}
    q["Q1 D′>V (사람 각도)"] = {
        "45°": 셋("D′ 제안", "V 현행", "대각45"), "30°": d30, "60°": d60,
        "문턱": "중앙 ≥ +0.02 · 승 ≥ 15/28 · 30·60 부호 같음 · 24장에서도 중앙 ≥ +0.02",
        "통과": bool(d1["중앙"] >= 0.02 and d1["승"] >= 15
                    and np.sign(d30["중앙"]) == np.sign(d1["중앙"]) == np.sign(d60["중앙"])
                    and d1_24["중앙"] >= 0.02)}
    d2 = 쌍("D′ 제안", "A 복셀배포", "대각45", cs)
    q["Q2 복셀만 뺀 몫 (D′ 대 A)"] = {"45°": 셋("D′ 제안", "A 복셀배포", "대각45"),
                                      "문턱": "중앙 ≥ +0.02 · 승 과반",
                                      "통과": bool(d2["중앙"] >= 0.02 and d2["승"] * 2 > len(cs))}
    d3 = 쌍("D′→복셀", "D′ 제안", "대각45", cs)
    q["Q3 이득이 복셀 회피에서 오나"] = {"45°": 셋("D′→복셀", "D′ 제안", "대각45"),
                                        "문턱": "D′→복셀 − D′ 중앙 ≤ −0.02", "통과": bool(d3["중앙"] <= -0.02)}
    mc = lambda v, sel: round(float(np.median([P(c, v, "못덮음") for c in sel])), 5)
    ov = lambda v, sel: round(float(np.median([P(c, v, "넘침") for c in sel])), 5)
    q["Q4 축 실루엣 약속"] = {"못덮음": {"D′": mc("D′ 제안", cs), "V": mc("V 현행", cs), "A": mc("A 복셀배포", cs)},
                              "넘침": {"D′": ov("D′ 제안", cs), "V": ov("V 현행", cs), "A": ov("A 복셀배포", cs)},
                              "문턱": "D′ 못덮음 중앙 ≤ V + 0.005 · 넘침 ≤ V + 0.005",
                              "통과": bool(mc("D′ 제안", cs) <= mc("V 현행", cs) + 0.005
                                          and ov("D′ 제안", cs) <= ov("V 현행", cs) + 0.005)}
    hl = lambda v, sel: round(float(np.median([abs(P(c, v, "구멍45") - rs[c]["정답"]["구멍45"]) for c in sel])), 5)
    q["Q5 구멍"] = {"|구멍−정답| 중앙": {v: hl(v, cs) for v in VARS if v != "균일@D′"},
                    "정답 구멍 중앙": round(float(np.median([rs[c]["정답"]["구멍45"] for c in cs])), 5),
                    "문턱": "D′ ≤ V (동률은 통과)", "통과": bool(hl("D′ 제안", cs) <= hl("V 현행", cs))}
    d6 = 쌍("D′ 제안", "균일@D′", "대각45", q6)
    q["Q6 정보 0 대조군"] = {"45°": d6, "24장": 쌍("D′ 제안", "균일@D′", "대각45", q6_24),
                            "쓴 장": len(q6), "뺀 장(부피 1% 밖 · 실패)": [c for c in cs if c not in q6],
                            "문턱": "중앙 > 0 · 승 과반", "통과": bool(d6["중앙"] > 0 and d6["승"] * 2 > len(q6))}
    q["최악 하한"] = {"D′−V 45° 최악": d1["최악"], "최악 장": min(cs, key=lambda c: P(c, "D′ 제안", "대각45") - P(c, "V 현행", "대각45")),
                      "문턱": "≥ −0.10", "통과": bool(d1["최악"] >= -0.10)}

    # 배관 ────────────────────────────────────────────────────────────────
    배관 = {}
    배관["1 4장 관찰 재현"] = {c: rs[c]["배관1"] for c in 관찰값 if c in rs and "배관1" in rs[c]}
    배관["1 4장 관찰 재현"]["통과"] = bool(배관["1 4장 관찰 재현"]
                                          and all(v["통과"] for v in 배관["1 4장 관찰 재현"].values() if isinstance(v, dict)))
    y = {}
    for p in ("보충경계2_진행.jsonl", "보충경계_진행.jsonl"):
        f = os.path.join(HERE, "out", "기록", p)
        if os.path.exists(f):
            for line in open(f, encoding="utf-8"):
                r = json.loads(line)
                if "D′ 보충경계" in r and "못덮음" in r["D′ 보충경계"]:
                    y.setdefault(r["case"], r["D′ 보충경계"]["못덮음"])
    g2 = {c: {"09-19": y[c], "오늘": rs[c]["재현_못덮음"], "차": round(rs[c]["재현_못덮음"] - y[c], 5)}
          for c in cs if c in y and "재현_못덮음" in rs[c]}
    배관["2 D′ 재현 (못덮음 1e-3)"] = {"장": len(g2), "최대차": round(max([abs(v["차"]) for v in g2.values()] or [0]), 5),
                                       "장별": g2, "통과": bool(g2 and max(abs(v["차"]) for v in g2.values()) <= 1e-3)}
    g3 = {c: rs[c]["판본"]["균일@D′"].get("부피오차", "실패") for c in cs}
    배관["3 균일@D′ 부피 1%"] = {"맞은 장": len(q6), "전체": len(cs), "장별": g3,
                                 "통과": bool(len(q6) == len(cs)), "비고": "안 맞는 장은 Q6 에서 뺐다"}
    bp = os.path.join(HERE, "out", "기록", "겉면채점_벤치_진행.jsonl")
    b = {}
    if os.path.exists(bp):
        for line in open(bp, encoding="utf-8"):
            r = json.loads(line)
            if "타원1.00" in r:
                b[r["case"]] = r["타원1.00"][1]
    g4 = {c: round(P(c, "V 현행", "iou128") - b[c], 6) for c in cs if c in b}
    배관["4 V IoU128 = 09-15 점수판"] = {"장": len(g4), "최대차": round(max([abs(v) for v in g4.values()] or [9]), 6),
                                         "어긋난 장": {k: v for k, v in g4.items() if abs(v) > 1e-9},
                                         "통과": bool(len(g4) == len(cs) and max(abs(v) for v in g4.values()) < 1e-9)}

    표 = {}
    for v in VARS:
        sel = q6 if v == "균일@D′" else cs
        표[v] = {k: round(float(np.median([P(c, v, k) for c in sel if k in rs[c]["판본"][v]])), 5)
                 for k in ("대각30", "대각45", "대각60", "구멍45", "못덮음", "넘침", "iou128", "iou128양쪽", "면", "부피")
                 if any(k in rs[c]["판본"][v] for c in sel)}
        rr = [P(c, v, "거칠기") for c in sel if "거칠기" in rs[c]["판본"][v]]
        표[v]["거칠기(잰 장 %d)" % len(rr)] = round(float(np.median(rr)), 5) if rr else None

    out = {"판": TAG, "회전부호": ROTSIGN,
           "분모": {"28장 얼린 집합": len(전체), "완주": len(cs), "24장(4장 뺌)": len(cs24),
                    "안 잰 장": 안잰, "관찰 4장": [c for c in 관찰4 if c in cs]},
           "배관": 배관, "Q": q, "중앙표": 표,
           "장별": {c: {"D′−V 45": round(P(c, "D′ 제안", "대각45") - P(c, "V 현행", "대각45"), 5),
                        "D′−A 45": round(P(c, "D′ 제안", "대각45") - P(c, "A 복셀배포", "대각45"), 5),
                        **{v: {k: rs[c]["판본"][v].get(k) for k in
                               ("대각30", "대각45", "대각60", "구멍45", "못덮음", "넘침", "iou128", "iou128양쪽",
                                "거칠기", "거칠기생략", "면", "부피", "닫힘")} for v in VARS},
                        "정답구멍45": rs[c]["정답"]["구멍45"], "B∩hull45": rs[c]["B∩hull"]["대각45"],
                        "봉우리GB": rs[c].get("봉우리GB"), "초": rs[c].get("초")} for c in cs},
           "봉우리GB 최대": max([rs[c].get("봉우리GB", 0) for c in cs] or [0])}
    p = os.path.join(HERE, "out", "기록", "대각_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("  분모 — 얼린 28 · 완주 %d · 24장 %d · 안 잰 장 %s" % (len(cs), len(cs24), 안잰 or "없음"))
    print("  %-12s %8s %8s %8s %8s %8s %8s %8s" % ("판본", "대각30", "대각45", "대각60", "구멍45", "못덮음", "넘침", "IoU128"))
    for v in VARS:
        d = 표[v]
        print("  %-12s %8s %8s %8s %8s %8s %8s %8s"
              % (v, *[("%.4f" % d[k]) if k in d else "-" for k in
                      ("대각30", "대각45", "대각60", "구멍45", "못덮음", "넘침", "iou128")]))
    for k, v in 배관.items():
        print("  배관 %-28s %s" % (k, "통과" if v.get("통과") else "짐"))
    for k, v in q.items():
        print("  %-26s %s" % (k, "통과" if v.get("통과") else "짐"))
    print("  ->", p)
    return out


# ── 그림 ─────────────────────────────────────────────────────────────────────

def _load(case):
    z = np.load(os.path.join(SILD, case + ".npz"))
    return {k: np.unpackbits(z[k])[:W.RES * W.RES].reshape(W.RES, W.RES).astype(bool) for k in z.files}


def 그림():
    from PIL import Image, ImageDraw
    from 계획 import _font
    rs = rows()
    cs = [c for c in 순서() if c in rs and os.path.exists(os.path.join(SILD, c + ".npz"))]
    dv = {c: rs[c]["판본"]["D′ 제안"]["대각45"] - rs[c]["판본"]["V 현행"]["대각45"] for c in cs}

    # ① 접촉지 — 관찰 4장 + D′−V 최선 · 최악 장
    pick = [c for c in 관찰4 if c in cs]
    for c in (max(dv, key=dv.get), min(dv, key=dv.get)):
        if c not in pick:
            pick.append(c)
    cols = ("정답", "G 생", "A 복셀배포", "D′ 제안", "V 현행", "겹침 (빨강=정답만 · 파랑=D′만)")
    S, Gp, TOP, LW = 300, 12, 150, 250
    im = Image.new("RGB", (LW + len(cols) * (S + Gp) + 20, TOP + len(pick) * (S + 34) + 20), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 14), "45° 대각 실루엣 — 사람이 보는 각도에서 무엇이 메워지나", font=_font(30), fill=(20, 20, 20))
    d.text((24, 56), "z 축 둘레 45° 회전 뒤 정면 직교 투영 · 1024² · 부풀리기 없음 · 숫자 = 정답 실루엣과의 IoU (괄호는 구멍 수)",
           font=_font(17), fill=(90, 90, 90))
    d.text((24, 82), "복셀을 거치는 팔(V · A)은 세 축 그림자가 겹치는 구조를 판으로 메운다 — 대각에서만 보인다",
           font=_font(17), fill=(90, 90, 90))
    for i, n in enumerate(cols):
        d.text((LW + i * (S + Gp), TOP - 28), n, font=_font(18), fill=(30, 30, 30))
    for r_, c in enumerate(pick):
        y = TOP + r_ * (S + 34)
        sl = _load(c)
        d.text((16, y + S // 2 - 20), c[:26], font=_font(16), fill=(30, 30, 30))
        d.text((16, y + S // 2 + 2), "D′−V %+.3f" % dv[c], font=_font(16), fill=(120, 40, 40))
        ys, xs = np.nonzero(sl["정답"] | sl["D′ 제안"] | sl["V 현행"])
        y0, y1 = max(ys.min() - 12, 0), min(ys.max() + 12, W.RES)
        x0, x1 = max(xs.min() - 12, 0), min(xs.max() + 12, W.RES)
        n_ = max(y1 - y0, x1 - x0)
        crop = lambda a: cv2.resize(a[y0:y0 + n_, x0:x0 + n_].astype(np.uint8), (S, S), interpolation=cv2.INTER_AREA)
        for i, n in enumerate(cols):
            if i < 5:
                a = crop(sl[cols[i]])
                rgb = np.stack([255 - a * 200] * 3, 2).astype(np.uint8)
                lab = "%.3f (%d)" % (rs[c]["판본"][n]["대각45"], rs[c]["판본"][n]["구멍45"]) if n in rs[c]["판본"] \
                    else "구멍 %d" % rs[c]["정답"]["구멍45"]
            else:
                t_, p_ = crop(sl["정답"]).astype(bool), crop(sl["D′ 제안"]).astype(bool)
                rgb = np.full((S, S, 3), 255, np.uint8)
                rgb[t_ & ~p_] = (220, 40, 40)
                rgb[p_ & ~t_] = (40, 90, 220)
                rgb[t_ & p_] = (190, 190, 190)
                lab = "IoU %.3f" % rs[c]["판본"]["D′ 제안"]["대각45"]
            x = LW + i * (S + Gp)
            im.paste(Image.fromarray(rgb), (x, y))
            d.text((x + 6, y + S + 6), lab, font=_font(17), fill=(40, 40, 40))
        print("  %s 접촉지" % c, flush=True)
    p1 = os.path.join(HERE, "out", "대각_접촉지.png")
    im.save(p1)

    # ② 장별 막대
    order = sorted(cs, key=lambda c: dv[c])
    Wd, Hh, L, B = 1500, 620, 330, 90
    im2 = Image.new("RGB", (Wd, Hh), "white")
    d2 = ImageDraw.Draw(im2)
    d2.text((24, 14), "장별 D′ − V · 45° 대각 실루엣 IoU (%d장)" % len(order), font=_font(28), fill=(20, 20, 20))
    d2.text((24, 52), "빨간 이름 = 가설을 만든 관찰 4장 · 세로선 = 0", font=_font(16), fill=(90, 90, 90))
    mx = max(0.02, max(abs(v) for v in dv.values()) * 1.15)
    x0 = L + (Wd - L - 40) / 2
    sc = (Wd - L - 40) / 2 / mx
    hgt = (Hh - B - 90) / max(len(order), 1)
    d2.line([(x0, 88), (x0, Hh - B + 4)], fill=(150, 150, 150), width=2)
    for i, c in enumerate(order):
        y = 92 + i * hgt
        v = dv[c]
        col = (40, 110, 200) if v > 0 else (200, 60, 50)
        d2.rectangle([min(x0, x0 + v * sc), y + 1, max(x0, x0 + v * sc), y + hgt - 2], fill=col)
        d2.text((14, y - 1), c[:34], font=_font(14), fill=(190, 40, 40) if c in 관찰4 else (60, 60, 60))
        d2.text((x0 + v * sc + (6 if v > 0 else -56), y - 1), "%+.3f" % v, font=_font(14), fill=(60, 60, 60))
    med = float(np.median(list(dv.values())))
    d2.text((24, Hh - B + 16), "중앙 %+.4f · 승 %d/%d · 최악 %+.4f · 최선 %+.4f"
            % (med, sum(1 for v in dv.values() if v > 0), len(dv), min(dv.values()), max(dv.values())),
            font=_font(20), fill=(20, 20, 20))
    p2 = os.path.join(HERE, "out", "대각_장별.png")
    im2.save(p2)
    print("  ->", p1)
    print("  ->", p2)
    return p1, p2


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def selfcheck():
    # 회전: 정사각 기둥을 45° 돌리면 정면 폭이 √2 배가 된다
    box = trimesh.creation.box((0.3, 0.3, 0.6))
    w0 = sil(box, "front", None, 0).any(0).sum()
    w45 = sil(box, "front", None, 45).any(0).sum()
    assert 1.34 < w45 / w0 < 1.50, "45° 회전이 폭을 √2 배로 안 만든다 (%.3f)" % (w45 / w0)
    # 같은 각도로 돌린 같은 메시끼리는 IoU 1
    assert iou(sil(box, "front", None, 45), sil(box, "front", None, 45)) == 1.0
    # 구멍: 고리 하나 -> 1 · 테두리에 닿은 배경은 안 센다
    m = np.zeros((W.RES, W.RES), bool)
    m[200:600, 200:600] = True
    m[350:450, 350:450] = False
    assert holes(m) == 1, "고리에서 구멍 1 이 안 나온다 (%d)" % holes(m)
    m[300:310, 300:302] = False                                  # 20 화소 = 문턱 (≥ 이므로 센다)
    assert holes(m) == 2, "20 화소 구멍을 안 센다"
    m[280:282, 280:282] = False                                  # 4 화소 — 버린다
    assert holes(m) == 2, "4 화소 부스러기를 셌다"
    # 회전을 정답과 판본에 같은 부호로 건다 — 부호가 달랐다면 아래가 1 이 아니다
    b2 = box.copy()
    b2.apply_translation([0.0, 0.0, 0.0])
    assert iou(sil(box, "front", None, 30), sil(b2, "front", None, 30)) == 1.0
    print("  자가검사 통과 — 회전 · 구멍 · IoU")


if __name__ == "__main__":
    a = sys.argv[1:]
    H.register_sheets()
    selfcheck()
    if a[:1] == ["검사"]:
        pass
    elif a[:1] == ["판정"]:
        verdict()
    elif a[:1] == ["그림"]:
        그림()
    else:
        run(int(a[0]) if a and a[0].isdigit() else 1, a[1:] or None)
