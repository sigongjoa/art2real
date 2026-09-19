# -*- coding: utf-8 -*-
"""**보충의 반 칸을 없앤다** (2026-09-19).

    python 보충경계.py 검사       자가검사 · 배관 (재현 게이트 포함)
    python 보충경계.py [n]        경계 17장 중 아직 안 한 장 n 개 -> out/기록/보충경계_진행.jsonl
    python 보충경계.py 범위 [n]   두 겹 형상 5장
    python 보충경계.py 판정       -> out/기록/보충경계_<때>.json
    python 보충경계.py 그림       -> out/보충경계_단면.png · out/보충경계_장별.png

판정은 `claudedocs/plan_보충경계_20260919.md` 「Q」 절 그대로다 — 돌리기 전에 적었다.

어제 D(불리언+높이장보충)는 못덮음에서 졌다 (A 0.0036 -> D 0.0068). 반 칸이 세 축 모두에 있다.

    x · z   `hull.carve` 가 **칸 중심**에서 1024² 마스크를 찍는다 -> 테두리 칸이 꺼진다
    y       `기본_높이장` 이 lo · hi 를 **칸 번호**로 쓴다 -> 같은 칸을 복셀로 채우면 [lo-0.5, hi+0.5] 인데 높이장은 [lo, hi]

고침 셋 — (a) y 를 칸 전체로 · (b) 발자국을 한 칸 넓히고 높이를 이웃에서 외삽 · (c) **정확 hull 로 되자르기**.
(c) 가 안전판이다: 패치가 hull 을 넘을 수 없으므로 (b) 의 팽창이 밖으로 새지 않는다.

**A · B · D 는 어제 `보충격자_진행.jsonl` 에서 읽는다.** 같은 코드(`실험_20260918/보충격자.py` 를 한 줄도 안 고치고 import)
· 같은 입력 · 같은 씨앗이라 결정적이고, RAM 예산 6GB 에서 다시 도는 값은 낭비다. 대신 **B 의 못덮음을 장마다 다시 재서
어제 값과 맞춘다** (재현 게이트) — 어긋나면 그 장을 버린다.
"""
import ctypes
import json
import os
import sys
import gc
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
import 표면 as SF
import 대조 as C_
import 정답 as J
from 겉면채점 import bench_cases, fill_slices
from 생성깎기 import voxelize, sil_fit, fill_gaps
from 면 import roughness
from 불리언 import gen_manifold, to_trimesh, prism, P192
import 보충격자 as BG                      # **고치지 않는다** — 어제 숫자와 갈라지면 맞댈 수 없다

PROG = os.path.join(HERE, "out", "기록", "보충경계_진행.jsonl")
TAG = "보충경계 v1 · D′(반 칸 고침) · D′→복셀 · B⁺(D′부피) · 넘침 · A·B·D 는 09-18 재사용 (2026-09-19)"
NEW = ("B 불리언+복셀보충", "D′ 보충경계", "D′→복셀", "B⁺ (D′부피)")      # 오늘 계산하는 판본
OLD = ("A 복셀+보충", "B 불리언+복셀보충", "D 불리언+높이장보충")           # 어제 jsonl 에서 읽는 판본
겹 = ["cloak_Chest_Closed_AngpV0HxD8", "cloak_Chest_O72u4Drp8k", "cloak_Cloche_Qz9XMYysBQ",
      "mech_Drill_8uBbH7Dvmb", "mech_Mech_4UvIHxnoSR"]                   # 두 겹 형상 (뚜껑 · 챙 · 벌어진 팔)
NPT = BG.NPT                                                             # 60000 — 어제와 같은 자


def 봉우리GB():
    """이 프로세스가 지금까지 찍은 **최고 작업집합**. 단조라 단계마다 찍으면 차가 곧 그 단계의 봉우리다."""
    import psutil
    return round(psutil.Process().memory_info().peak_wset / 1e9, 2)


def 여유GB():
    import psutil
    return round(psutil.virtual_memory().available / 1e9, 1)


# ── 반 칸을 없앤 높이장 ───────────────────────────────────────────────────────

def 넓히기(a, on, on2):
    """새로 켜진 칸의 높이를 **원래 켜진 이웃의 평균**으로 외삽한다 (8-이웃)."""
    k = np.ones((3, 3), np.float32)
    f = lambda x: cv2.filter2D(x.astype(np.float32), -1, k, borderType=cv2.BORDER_CONSTANT)
    cnt, s = f(on), f(np.where(on, a, 0.0))
    out = np.asarray(a, np.float32).copy()
    new = on2 & ~on
    out[new] = np.where(cnt[new] > 0, s[new] / np.maximum(cnt[new], 1.0), 0.0)
    return out


def 기본_높이장2(masks, bs, grow=1):
    """`보충격자.기본_높이장` 과 같은 규칙인데 **반 칸을 없앤다.**

    (a) y: lo · hi 는 칸 번호(중심)다. 같은 칸을 복셀로 채우면 [lo-0.5, hi+0.5] 를 차지한다.
    (b) x · z: 발자국을 한 칸 넓히고 새 칸의 높이를 이웃에서 외삽한다. 밖으로 새는 것은 ∩hull 이 막는다."""
    keep, axes = H.carve(masks, back_sign=bs)
    deps = H.ellipse_depths(keep, axes, bs)
    lam = H.DEPTH_LAM
    u, _, z = axes
    X2, Z2 = np.meshgrid(u, z, indexing="ij")
    j = np.arange(H.N)[None, :, None]
    lo = np.where(keep, j, H.N).min(1).astype(np.float32) - 0.5          # (a)
    hi = np.where(keep, j, -1).max(1).astype(np.float32) + 0.5
    D = np.maximum(hi - lo, 0.0)
    on = keep.any(1)

    def sample(v):
        a, sign = W.VIEW_AXIS[v]
        py, px = W.topix((bs if v == "back" else sign) * X2, Z2)
        return deps[v][py, px]

    def norm(h):
        top = np.where(on, h, 0.0).max(0, keepdims=True)
        return np.where(on, h / np.maximum(top, 1e-6), 0.0)

    jf = lo + (1.0 - norm(sample("front"))) * lam * D
    jb = hi - (1.0 - norm(sample("back"))) * lam * D
    if grow:
        on2 = cv2.dilate(on.astype(np.uint8), np.ones((3, 3), np.uint8),
                         iterations=grow).astype(bool)                   # (b)
        jf, jb = 넓히기(jf, on, on2), 넓히기(jb, on, on2)
        on = on2
    # 새로 켜진 칸의 앞뒤가 뒤집히면 자기교차가 나고 불리언이 조용히 망가진다 (조사 ①)
    assert (jb[on] >= jf[on] - 1e-5).all(), "확장 칸에서 앞뒤가 뒤집혔다 (jf > jb)"
    return BG.height_solid(jf, jb, on, axes), axes


# ── 판본 ─────────────────────────────────────────────────────────────────────

def prepare(case):
    ctx = BG.prepare(case)
    ctx.pop("hf", None)                                                  # 어제 D 전용 — 오늘은 안 쓴다
    gc.collect()
    m, _ = 기본_높이장2(ctx["masks"], ctx["bs"])
    ctx["hf2"] = gen_manifold(m)
    del m
    gc.collect()
    return ctx


def inflate(mesh, vol):
    """무게중심 기준 균일 확대로 부피를 `vol` 에 맞춘다 — 대조군 ③ 「B 를 D′ 의 부피로 민 것」.

    ponytail: 참 오프셋(민코프스키 합)이 아니다. 60만 면에서 그건 이 예산에 안 들어간다.
    확대는 얇은 곳을 상대적으로 더 밀어 **못덮음에 관대한 상한**이 된다 — 그 상한이 넘침을 물면 결론은 더 강하다."""
    s = (float(vol) / max(abs(mesh.volume), 1e-12)) ** (1.0 / 3.0)
    c = np.asarray(mesh.centroid, float)
    m = mesh.copy()
    m.apply_translation(-c)
    m.apply_scale(s)
    m.apply_translation(c)
    return m


def make(ctx, name, cache=None):
    """판본 하나. `cache` 는 D′ 메시 (D′→복셀 · B⁺ 가 쓴다)."""
    import manifold3d as m3
    if name == "B 불리언+복셀보충":
        return BG.make(ctx, name)
    if name == "D′ 보충경계":
        if ctx["gp"] is None:
            return ctx["bool"]
        pat = m3.Manifold.batch_boolean([ctx["hf2"], ctx["hull"], ctx["gp"]], m3.OpType.Intersect)
        return to_trimesh(m3.Manifold.batch_boolean([ctx["B"], pat], m3.OpType.Add))
    if name == "D′→복셀":
        return C_.to_mesh(voxelize(cache, ctx["axes"]), ctx["axes"])
    raise KeyError(name)


# ── 채점 ─────────────────────────────────────────────────────────────────────

def score(truth, mesh, pitch):
    return BG.score(truth, mesh, pitch)


def 잰다(m, ctx, truth, 무엇, 봉=None, 딱지=""):
    """`무엇` 에 든 것만 잰다 — 어제 있는 값은 다시 안 잰다 (RAM · 시간).

    `봉` 은 단계별 봉우리 사전이다. **어느 단계가 봉우리인지 모르면 줄일 수도 없다** (09-19 오케스트레이터 지적)."""
    def 찍(이름):
        if 봉 is not None:
            봉["%s·%s" % (딱지, 이름)] = 봉우리GB()
    vx = voxelize(m, ctx["axes"])
    찍("voxelize")
    sf = sil_fit(vx, ctx["masks"], ctx["bs"], ctx["axes"])
    r = {"면": int(len(m.faces)), "부피": round(float(abs(m.volume)), 6),
         "못덮음": round(max(sf["못덮음_front"], sf["못덮음_side"]), 4),
         "넘침": round(max(sf["넘침_front"], sf["넘침_side"]), 4),
         "조각": SF.pieces(vx), "닫힘": bool(m.is_watertight)}
    del vx
    gc.collect()
    찍("실루엣·조각")
    if "거칠기" in 무엇:
        r["거칠기"] = roughness(m, n=NPT)["거칠기"]
        gc.collect()
        찍("거칠기")
    for k, p in (("iou", J.PITCH), ("iou192", P192)):          # 격자 둘을 동시에 안 든다
        if k in 무엇 and truth is not None:
            r[k] = score(truth, m, p)
            gc.collect()
            찍(k)
    return r


def one(case, 범위=False):
    """`범위=True` (두 겹 5장): **B 를 오늘 온전히 잰다** — 이 5장은 어제 판정에 없어 재사용할 값이 없다.
    대신 D′→복셀 · B⁺ 를 뺀다 (Q-범위는 D′ 대 B 의 비열등 시험이고, 면 111만~234만이라 예산이 안 된다)."""
    t0 = time.time()
    봉 = {"시작": 봉우리GB()}
    ctx = prepare(case)
    봉["prepare(불리언·hull·높이장)"] = 봉우리GB()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    out = {"case": case, "판": TAG, "범위": bool(범위),
           "빈자리": {v: round(float(ctx["gaps"][v].sum() / max(ctx["masks"][v].sum(), 1)), 4) for v in W.VIEWS}}

    d2 = make(ctx, "D′ 보충경계")
    봉["D′ 불리언"] = 봉우리GB()
    # 범위(두 겹 5장)는 iou192 를 안 잰다 — Q-범위 문턱이 128 만 쓴다. 판본은 안 바뀐다
    out["D′ 보충경계"] = 잰다(d2, ctx, truth, ("거칠기", "iou") if 범위 else ("거칠기", "iou", "iou192"), 봉, "D′")
    if not 범위:
        dv = make(ctx, "D′→복셀", cache=d2)
        out["D′→복셀"] = 잰다(dv, ctx, truth, ("거칠기", "iou"), 봉, "Dv")
        del dv
        gc.collect()

    b = make(ctx, "B 불리언+복셀보충")
    봉["B 불리언"] = 봉우리GB()
    out["B 불리언+복셀보충"] = 잰다(b, ctx, truth, ("거칠기", "iou") if 범위 else (), 봉, "B")
    if 범위:
        del b
    else:
        bp = inflate(b, out["D′ 보충경계"]["부피"])
        del b
        gc.collect()
        out["B⁺ (D′부피)"] = 잰다(bp, ctx, truth, ("iou",), 봉, "B⁺")
        del bp
    del d2, ctx
    gc.collect()
    out["초"] = round(time.time() - t0, 1)
    out["봉우리GB"] = 봉우리GB()
    out["단계봉우리GB"] = 봉
    out["여유GB"] = 여유GB()
    return out


# ── 기록 ─────────────────────────────────────────────────────────────────────

def rows(path=PROG, tag=TAG):
    out = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == tag:
                assert r["case"] not in out, "%s 가 같은 판으로 두 번 적혔다" % r["case"]
                out[r["case"]] = r
    return out


def 어제():
    """09-18 보충격자 진행 기록 — A · B · D 를 여기서 읽는다."""
    return BG.rows()


def 경계집합():
    """얼린 집합 = 어제 17장. 가벼운 순."""
    y = 어제()
    return [c for c in BG.todo_cases() if c in y]


def run(n, cases=None, 범위=False):
    done = rows()
    y = 어제()
    for c in [x for x in (cases or 경계집합()) if x not in done][:n]:
        if 범위 and 여유GB() < 12:
            # 두 겹 장은 봉우리가 20GB 를 넘본다. 여유가 없으면 시작도 안 한다 (다른 줄기를 죽인다)
            print("  %-38s 건너뜀 — 여유 %.1fGB (12GB 필요)" % (c[:38], 여유GB()), flush=True)
            continue
        r = one(c, 범위=범위)
        if c in y:                                     # **재현 게이트** — B 의 못덮음이 어제와 같나
            g = abs(r["B 불리언+복셀보충"]["못덮음"] - y[c]["B 불리언+복셀보충"]["못덮음"])
            r["재현"] = round(float(g), 5)
            assert g <= 1e-4, "%s: B 못덮음이 어제와 다르다 (%.5f)" % (c, g)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        b, d = r["B 불리언+복셀보충"], r["D′ 보충경계"]
        if 범위:
            print("  %-38s [두 겹] 거칠기 B %.3f -> D′ %.3f · IoU %.3f -> %.3f · 못덮음 %.4f -> %.4f · 넘침 %.4f -> %.4f · 조각 %d · 면 %d · %.0f초 · %.1fGB"
                  % (c[:38], b["거칠기"], d["거칠기"], b["iou"], d["iou"], b["못덮음"], d["못덮음"],
                     b["넘침"], d["넘침"], d["조각"], d["면"], r["초"], r["봉우리GB"]), flush=True)
            print("    단계봉우리GB " + " · ".join("%s %.1f" % (k, v) for k, v in r["단계봉우리GB"].items()), flush=True)
            continue
        a = y.get(c, {})
        print("  %-38s 못덮음 A %s D %s -> D′ %.4f (B⁺ %.4f) · 거칠기 D′ %.3f (→복셀 %.3f) · IoU %.3f · 넘침 B %.4f B⁺ %.4f D′ %.4f · %.0f초 · %.1fGB"
              % (c[:38],
                 ("%.4f" % a["A 복셀+보충"]["못덮음"]) if a else "  -   ",
                 ("%.4f" % a["D 불리언+높이장보충"]["못덮음"]) if a else "  -   ",
                 d["못덮음"], r["B⁺ (D′부피)"]["못덮음"],
                 d["거칠기"], r["D′→복셀"]["거칠기"], d["iou"],
                 b["넘침"], r["B⁺ (D′부피)"]["넘침"], d["넘침"],
                 r["초"], r["봉우리GB"]), flush=True)


# ── 판정 ─────────────────────────────────────────────────────────────────────

def _med(v):
    return round(float(np.median(v)), 5)


def 집계(cs, y, rs):
    """장 목록 -> 판본별 중앙값 표 (어제 값과 오늘 값을 합쳐서)."""
    g = lambda c, n, k: (rs[c][n][k] if n in rs[c] and k in rs[c][n] else y[c][n][k])
    tab = {}
    for n in ("A 복셀+보충", "B 불리언+복셀보충", "D 불리언+높이장보충", "D′ 보충경계", "D′→복셀", "B⁺ (D′부피)"):
        row = {}
        for k in ("거칠기", "iou", "iou192", "못덮음", "넘침", "조각", "면", "부피"):
            vals = []
            for c in cs:
                src = rs[c] if (n in rs[c] and k in rs[c][n]) else (y.get(c) or {})
                if n in src and k in src[n]:
                    vals.append(src[n][k])
            if vals:
                row[k] = round(float(np.median(vals)), 5)
        tab[n] = row
    return tab


def verdict():
    rs = rows()
    y = 어제()
    cs = [c for c in 경계집합() if c in rs]
    ex = [c for c in 겹 if c in rs]
    assert len(cs) >= 15, "경계 집합이 %d 장만 돌았다" % len(cs)
    dif = lambda a, b, k: [(rs[c][a][k] if k in rs[c].get(a, {}) else y[c][a][k])
                           - (rs[c][b][k] if k in rs[c].get(b, {}) else y[c][b][k]) for c in cs]
    A, B, D, D2, DV, BP = ("A 복셀+보충", "B 불리언+복셀보충", "D 불리언+높이장보충",
                           "D′ 보충경계", "D′→복셀", "B⁺ (D′부피)")
    q = {}
    m1 = dif(D2, A, "못덮음")
    win = int(sum(np.array(dif(D2, D, "못덮음")) < 0))
    q["Q-경계1 못덮음"] = {"D′−A 중앙": _med(m1), "D′<D 인 장": win, "n": len(cs),
                          "어제 D−A": 0.0029, "통과": bool(_med(m1) <= 0 and win > len(cs) / 2)}
    m2 = dif(D2, B, "거칠기")
    worse = int(sum(np.array(m2) > 0))
    q["Q-경계2 거칠기"] = {"D′−B 중앙": _med(m2), "D′ 가 더 거친 장": worse,
                          "어제 D−B": -0.041, "통과": bool(_med(m2) < 0 and worse < len(cs) / 2)}
    i1, i2 = _med(dif(D2, A, "iou")), _med(dif(D2, A, "iou192"))
    q["Q-경계3 형상"] = {"128": i1, "192": i2, "어제 D−A 128": 0.00459,
                         "통과": bool(i1 >= -0.005 and i2 >= -0.005)}
    m4 = _med(dif(DV, D2, "거칠기"))
    q["Q-경계4 격자 회피"] = {"중앙": m4, "어제": 0.2401, "통과": bool(m4 > 0.1)}
    ov = _med(dif(BP, D2, "넘침"))
    q["Q-대조 B⁺"] = {"넘침(B⁺)−넘침(D′) 중앙": ov,
                      "못덮음(B⁺) 중앙": _med([rs[c][BP]["못덮음"] for c in cs]),
                      "못덮음(D′) 중앙": _med([rs[c][D2]["못덮음"] for c in cs]),
                      "iou(B⁺) 중앙": _med([rs[c][BP]["iou"] for c in cs]),
                      "통과": bool(ov > 0)}
    v = {"판": TAG, "n": len(cs), "케이스": cs, "중앙": 집계(cs, y, rs),
         "Q": q, "봉우리GB 최대": max([rs[c].get("봉우리GB", 0) for c in rs] or [0])}
    # **제외의 근거를 숫자로 남긴다** — 「메모리로 미룸」만 적으면 다음 바퀴가 고칠 곳을 모른다
    kp = os.path.join(HERE, "out", "기록", "보충경계_겹수.json")
    v["제외"] = {"장": [c for c in 겹 if c not in rs], "까닭": "봉우리 RAM",
                 "실측": {"cloak_Chest_Closed_AngpV0HxD8": {"면(불리언∩hull)": 1117174, "봉우리GB": 27.1,
                                                            "초": 470, "결과": "중단 — 기계 34.2GB 를 다른 실험과 나눠 쓴다"}},
                 "대신 잰 것": "겹수 — 메시 없이 기둥당 hull 구간 수 (out/기록/보충경계_겹수.json)"}
    if os.path.exists(kp):
        v["제외"]["겹수 중앙"] = json.load(open(kp, encoding="utf-8"))["중앙"]
    if ex:
        # **Q-범위** — 두 겹 형상. B 도 오늘 온전히 쟀다 (이 5장은 어제 판정에 없다). 비열등 시험이다.
        gd = lambda k: [rs[c][D2][k] - rs[c][B][k] for c in ex]
        rr, ii, mm2, pp = gd("거칠기"), gd("iou"), gd("못덮음"), gd("조각")
        crit = {"① 거칠기 D′≤B 인 장": int(sum(np.array(rr) <= 0)),
                "② iou D′−B 중앙(128)": _med(ii),
                "③ 못덮음 D′−B 중앙": _med(mm2),
                "④ 닫힘 D′": int(sum(rs[c][D2]["닫힘"] for c in ex)),
                "④ 조각 는 장": int(sum(np.array(pp) > 0))}
        crit["통과"] = bool(crit["① 거칠기 D′≤B 인 장"] >= 4 and crit["② iou D′−B 중앙(128)"] >= -0.010
                          and crit["③ 못덮음 D′−B 중앙"] <= 0.002 and crit["④ 닫힘 D′"] == len(ex)
                          and crit["④ 조각 는 장"] == 0)
        v["범위"] = {"n": len(ex), "케이스": ex, "판정": crit,
                     "장별": {c: {k: {"B": rs[c][B].get(k), "D′": rs[c][D2].get(k)}
                                 for k in ("거칠기", "iou", "iou192", "못덮음", "넘침", "조각", "닫힘", "면", "부피")}
                             | {"봉우리GB": rs[c].get("봉우리GB"), "초": rs[c].get("초")} for c in ex}}
    p = os.path.join(HERE, "out", "기록", "보충경계_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %-20s %8s %8s %8s %8s %7s %9s" % ("판본", "거칠기", "IoU128", "못덮음", "넘침", "조각", "면"))
    for n, d in v["중앙"].items():
        print("  %-20s %8s %8s %8s %8s %7s %9s"
              % (n, *[("%.4f" % d[k]) if k in d else "-" for k in ("거칠기", "iou", "못덮음", "넘침")],
                 ("%.1f" % d["조각"]) if "조각" in d else "-", ("%d" % d["면"]) if "면" in d else "-"))
    print("  Q", json.dumps(q, ensure_ascii=False))
    print("  ->", p)
    return v


def 논문자료():
    """줄기 논문이 읽을 판정 json · 장별 csv 를 `논문/보충격자/` 에 둔다 (숫자를 손으로 안 박는다)."""
    import csv
    import glob
    import shutil
    d = os.path.join(HERE, "논문", "보충격자")
    os.makedirs(os.path.join(d, "그림"), exist_ok=True)
    shutil.copyfile(sorted(glob.glob(os.path.join(HERE, "out", "기록", "보충경계_2026*.json")))[-1],
                    os.path.join(d, "판정_경계.json"))
    shutil.copyfile(sorted(glob.glob(os.path.join(HERE, "out", "기록", "보충경계2_2026*.json")))[-1],
                    os.path.join(d, "판정_추가.json"))
    for src, dst in (("기록/보충경계_겹수.json", "겹수.json"),
                     ("보충경계_반칸.png", "그림/반칸.png"), ("보충경계_장별.png", "그림/경계장별.png")):
        s = os.path.join(HERE, "out", src)
        if os.path.exists(s):
            shutil.copyfile(s, os.path.join(d, dst))
    rs, y = rows(), 어제()
    with open(os.path.join(d, "장별_경계.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case", "두겹", "못덮음_A", "못덮음_B", "못덮음_D", "못덮음_Dp", "못덮음_Bp",
                    "넘침_B", "넘침_Dp", "넘침_Bp", "거칠기_B", "거칠기_D", "거칠기_Dp", "거칠기_Dv",
                    "iou_A", "iou_D", "iou_Dp", "iou_Bp", "면_Dp"])
        for c, r in sorted(rs.items()):
            a = y.get(c, {})
            g = lambda n, k: ("%.4f" % a[n][k]) if n in a and k in a[n] else ""      # 어제 값
            t = lambda n, k: ("%.4f" % r[n][k]) if n in r and k in r[n] else ""      # 오늘 값
            w.writerow([c, int(c in 겹),
                        g("A 복셀+보충", "못덮음"), t("B 불리언+복셀보충", "못덮음"),
                        g("D 불리언+높이장보충", "못덮음"), t("D′ 보충경계", "못덮음"),
                        t("B⁺ (D′부피)", "못덮음"),
                        t("B 불리언+복셀보충", "넘침"), t("D′ 보충경계", "넘침"), t("B⁺ (D′부피)", "넘침"),
                        g("B 불리언+복셀보충", "거칠기") or t("B 불리언+복셀보충", "거칠기"),
                        g("D 불리언+높이장보충", "거칠기"),
                        t("D′ 보충경계", "거칠기"), t("D′→복셀", "거칠기"),
                        g("A 복셀+보충", "iou") or t("B 불리언+복셀보충", "iou"),
                        g("D 불리언+높이장보충", "iou"),
                        t("D′ 보충경계", "iou"), t("B⁺ (D′부피)", "iou"),
                        r["D′ 보충경계"]["면"]])
    print("  -> %s" % d)


# ── 검토가 시킨 추가 판본 (2026-09-19 밤) ───────────────────────────────────

PROG2 = os.path.join(HERE, "out", "기록", "보충경계2_진행.jsonl")
TAG2 = "보충경계2 v1 · A⁻(균일 침식 · D′부피) · D_c(팽창 없이) · D_ab(되자르기 없이) · 메카 둘 (2026-09-19)"


def rows2():
    """PROG2 는 한 장이 여러 줄로 나뉜다 (침식 · 갈래 · 메카가 따로 돈다) — 장마다 **합친다**."""
    out = {}
    if os.path.exists(PROG2):
        for line in open(PROG2, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG2:
                out.setdefault(r["case"], {}).update(r)
    return out


def A복셀(case):
    """A(현행 배포 구성)의 칸 판. **불리언을 안 탄다** — 침식 대조군에는 생성 메시 복셀과 보충만 있으면 된다."""
    from 불리언 import fitted
    masks, bs, plain, base, axes = BG.gen_build(case)
    gen = fitted(case, masks)
    vox = voxelize(gen, axes) & plain
    del gen
    gc.collect()
    return (vox | fill_gaps(vox, base, plain) & ~vox), masks, bs, axes


def 침식(n=1):
    """**A⁻ = A 를 D′ 의 부피까지 균일 침식** (`hull.even_control`). 규약 ①(정보 0) 과 ③(이기려는 판본을
    내 부피로 민 것)을 동시에 만족하는 자리다. D′ 는 A 보다 부피가 9% 작으므로 **A 를 줄여야** 짝이 맞는다.
    B⁺ 는 확대 방향이라 이 자리를 대신하지 못한다 (검토 지적)."""
    rs, done = rows(), rows2()
    for c in [x for x in 경계집합() if x in rs and "A⁻ (D′부피 균일침식)" not in done.get(x, {})][:n]:
        t0 = time.time()
        tgt = rs[c]["D′ 보충경계"]["부피"]
        Av, masks, bs, axes = A복셀(c)
        m, t = H.even_control(Av, axes, tgt)
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        ctx = {"axes": axes, "masks": masks, "bs": bs}
        r = {"case": c, "판": TAG2, "A⁻ (D′부피 균일침식)": 잰다(m, ctx, truth, ("거칠기", "iou", "iou192")),
             "침식t": round(float(t), 3), "초": round(time.time() - t0, 1), "봉우리GB": 봉우리GB()}
        del m, Av
        gc.collect()
        with open(PROG2, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        a = r["A⁻ (D′부피 균일침식)"]
        print("  %-38s A⁻ IoU %.3f (D′ %.3f · A %s) · 못덮음 %.4f · 거칠기 %.3f · t %.2f · %.0f초"
              % (c[:38], a["iou"], rs[c]["D′ 보충경계"]["iou"],
                 ("%.3f" % 어제()[c]["A 복셀+보충"]["iou"]) if c in 어제() else "-",
                 a["못덮음"], a["거칠기"], t, r["초"]), flush=True)


def 갈래(n=1):
    """**반 칸 고침 셋 중 무엇이 일하나.** 경고가 이미 기록에 있다 — C(hull 로만 채움)의 못덮음 0.0026 이
    D′ 0.0031 보다 낫다. (c) 되자르기 하나로 이미 회복될 수 있다는 뜻이다.

        D_c   = Y  ∩ Q ∩ P    팽창 없이, 되자르기만
        D_ab  = Y⁺ ∩ P        팽창만, 되자르기 없이"""
    import manifold3d as m3
    done = rows2()
    for c in [x for x in 경계집합() if not done.get(x, {}).get("D_c")][:n]:
        t0 = time.time()
        ctx = BG.prepare(c)                                    # ctx["hf"] = 팽창 없는 높이장 Y
        hf2, _ = 기본_높이장2(ctx["masks"], ctx["bs"])
        ctx["hf2"] = gen_manifold(hf2)
        del hf2
        gc.collect()
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        r = {"case": c, "판": TAG2}
        for name, parts in (("D_c", ["hf", "hull", "gp"]), ("D_ab", ["hf2", "gp"])):
            if ctx["gp"] is None:
                continue
            pat = m3.Manifold.batch_boolean([ctx[k] for k in parts], m3.OpType.Intersect)
            m = to_trimesh(m3.Manifold.batch_boolean([ctx["B"], pat], m3.OpType.Add))
            r[name] = 잰다(m, ctx, truth, ("거칠기", "iou"))
            del m, pat
            gc.collect()
        r["초"] = round(time.time() - t0, 1)
        r["봉우리GB"] = 봉우리GB()
        del ctx
        gc.collect()
        with open(PROG2, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        rr = rows()
        print("  %-30s 못덮음 D_c %.4f · D_ab %.4f · D′ %.4f || 거칠기 %.3f · %.3f · %.3f · %.0f초 · %.1fGB"
              % (c[:30], r["D_c"]["못덮음"], r["D_ab"]["못덮음"], rr[c]["D′ 보충경계"]["못덮음"],
                 r["D_c"]["거칠기"], r["D_ab"]["거칠기"], rr[c]["D′ 보충경계"]["거칠기"],
                 r["초"], r["봉우리GB"]), flush=True)


def 메카(n=1):
    """**두 겹 상위 둘** (`mech_Mech` K≥2 0.623 = 벤치 1위 · `mech_Drill` 뭉갬 2위). A1 이 겨냥한 자리다.
    거칠기(KD-트리) · IoU 를 빼고 **못덮음 · 넘침 · 조각 · 닫힘만** 잰다 — 봉우리가 거기 몰린다."""
    done = rows2()
    for c in [x for x in ("mech_Mech_4UvIHxnoSR", "mech_Drill_8uBbH7Dvmb")
              if not done.get(x, {}).get("D′ 보충경계")][:n]:
        if 여유GB() < 12:
            print("  %-30s 건너뜀 — 여유 %.1fGB" % (c[:30], 여유GB()), flush=True)
            continue
        t0 = time.time()
        ctx = prepare(c)
        r = {"case": c, "판": TAG2, "두겹": True}
        for name in ("D′ 보충경계", "B 불리언+복셀보충"):
            m = make(ctx, name)
            r[name] = 잰다(m, ctx, None, ())                    # 못덮음 · 넘침 · 조각 · 닫힘만
            del m
            gc.collect()
        r["초"] = round(time.time() - t0, 1)
        r["봉우리GB"] = 봉우리GB()
        del ctx
        gc.collect()
        with open(PROG2, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        b, d = r["B 불리언+복셀보충"], r["D′ 보충경계"]
        print("  %-30s [두 겹] 못덮음 B %.4f -> D′ %.4f · 넘침 %.4f -> %.4f · 조각 %d -> %d · 닫힘 %s/%s · %.0f초 · %.1fGB"
              % (c[:30], b["못덮음"], d["못덮음"], b["넘침"], d["넘침"], b["조각"], d["조각"],
                 b["닫힘"], d["닫힘"], r["초"], r["봉우리GB"]), flush=True)


def 판정2():
    """검토가 시킨 추가 판본의 판정 -> out/기록/보충경계2_<때>.json."""
    from scipy.stats import wilcoxon
    rs, r2, y = rows(), rows2(), 어제()
    cs = [c for c in 경계집합() if c in rs]
    K = "A⁻ (D′부피 균일침식)"
    ec = [c for c in cs if K in r2.get(c, {})]
    gc_ = [c for c in cs if "D_c" in r2.get(c, {})]
    mk = [c for c in ("mech_Mech_4UvIHxnoSR", "mech_Drill_8uBbH7Dvmb") if "D′ 보충경계" in r2.get(c, {})]
    v = {"판": TAG2}

    def 짝(a, b, k, cc):
        d = np.array([a(c)[k] - b(c)[k] for c in cc], float)
        try:
            p = float(wilcoxon(d).pvalue)
        except Exception:
            p = float("nan")
        return {"중앙": round(float(np.median(d)), 5), "D′우세": int((d < 0).sum() if k in ("못덮음", "넘침", "거칠기", "조각") else (d > 0).sum()),
                "n": len(cc), "p": round(p, 4)}

    # ① 균일 침식 대조군 (규약 ①·③) — D′ 가 A 보다 부피가 9% 작으므로 **A 를 줄여** 짝을 맞춘다
    v["Q-침식 (A⁻ 대 D′ · 같은 부피)"] = {k: 짝(lambda c: rs[c]["D′ 보충경계"], lambda c: r2[c][K], k, ec)
                                         for k in ("iou", "iou192", "못덮음", "넘침", "거칠기")}
    v["Q-침식 (A⁻ 대 D′ · 같은 부피)"]["A⁻ 중앙"] = {k: round(float(np.median([r2[c][K][k] for c in ec])), 4)
                                                   for k in ("iou", "iou192", "못덮음", "넘침", "거칠기", "부피")}
    v["Q-침식 (A⁻ 대 D′ · 같은 부피)"]["부피 맞음"] = round(float(np.median(
        [r2[c][K]["부피"] / rs[c]["D′ 보충경계"]["부피"] for c in ec])), 4)
    # ② 기전 갈래 — (b) 팽창 · (c) 되자르기 중 무엇이 일하나
    v["Q-갈래 (b 팽창 · c 되자르기)"] = {"n": len(gc_), "케이스": gc_, "중앙": {
        n: {k: round(float(np.median([(y[c]["D 불리언+높이장보충"] if n == "D" else
                                       rs[c]["D′ 보충경계"] if n == "D′" else r2[c][n]).get(k, np.nan)
                                      for c in gc_])), 4)
            for k in ("못덮음", "넘침", "거칠기")
            if not np.isnan(np.median([(y[c]["D 불리언+높이장보충"] if n == "D" else
                                        rs[c]["D′ 보충경계"] if n == "D′" else r2[c][n]).get(k, np.nan)
                                       for c in gc_]))} for n in ("D", "D_c", "D_ab", "D′")}}
    # ③ 두 겹 상위 둘 (벤치 층화 1 · 2위) — 거칠기 · IoU 는 메모리로 못 쟀다
    v["Q-범위 (두 겹 상위 둘)"] = {"n": len(mk), "장별": {c: {
        k: {"B": r2[c]["B 불리언+복셀보충"][k], "D′": r2[c]["D′ 보충경계"][k]}
        for k in ("못덮음", "넘침", "조각", "닫힘", "면")} | {"봉우리GB": r2[c].get("봉우리GB"), "초": r2[c].get("초")}
        for c in mk}}
    # ④ 조각 — 「모든 판본 전부 1」은 거짓이었다
    v["조각"] = {n: {"≠1 인 장": int(sum((rs[c][n] if n in rs[c] else y[c][n])["조각"] != 1 for c in cs)),
                    "최악": int(max((rs[c][n] if n in rs[c] else y[c][n])["조각"] for c in cs)), "n": len(cs)}
                for n in ("A 복셀+보충", "B 불리언+복셀보충", "D 불리언+높이장보충", "D′ 보충경계",
                          "D′→복셀", "B⁺ (D′부피)")}
    # ⑤ 검토가 시킨 재계산 — 숫자를 논문에 손으로 안 박으려고 여기 남긴다
    A_, B_, Dp_ = "A 복셀+보충", "B 불리언+복셀보충", "D′ 보충경계"
    gA = lambda c, n, k: rs[c][n][k] if (n in rs[c] and k in rs[c][n]) else y[c][n][k]
    v["D′ 대 B"] = {k: 짝(lambda c: rs[c][Dp_], lambda c: rs[c][B_], k, cs) for k in ("못덮음", "넘침")}
    v["D′ 대 D"] = {"못덮음": 짝(lambda c: rs[c][Dp_], lambda c: y[c]["D 불리언+높이장보충"], "못덮음", cs)}
    vr = np.array([gA(c, Dp_, "부피") / gA(c, A_, "부피") for c in cs])
    vb = np.array([rs[c]["B⁺ (D′부피)"]["부피"] / rs[c][B_]["부피"] for c in cs])
    v["부피"] = {"D′/A 중앙": round(float(np.median(vr)), 4), "D′ 가 작은 장": int((vr < 1).sum()), "n": len(cs),
                "B⁺/B 중앙": round(float(np.median(vb)), 4),
                "B⁺ 가 B 보다 못덮음 나빠진 장": int(sum(rs[c]["B⁺ (D′부피)"]["못덮음"] > rs[c][B_]["못덮음"] for c in cs))}
    v["발자국 덮음 (1024²)"] = {"한 장 빈자리 전체": {"D": 0.961, "D′": 1.0},
                              "그림 자리 (knight_Z6Z)": {"D": 0.977, "D′": 0.999},
                              "합성 원 테두리띠": {"D": 0.9569, "D′": 0.9933}}
    v["hull 밖으로 샌 패치 부피몫"] = {"D": 0.0173, "D′": 0.0}
    # ⑥ 거칠기 추정기 드리프트 (어제 기록의 두 판 8장)
    v["거칠기 드리프트"] = {"설명": "같은 기하가 같은 면 수 · 같은 부피로 돌아와도 삼각형 순서가 달라 표본점이 바뀐다",
                          "완전일치": "면 · 부피 · IoU128 · IoU192 · 못덮음 24/24", "거칠기 최대": 0.0041,
                          "거칠기 중앙": 0.0016, "효과 대비": "D′−B −0.0472 는 최대 드리프트의 11.5배"}
    p = os.path.join(HERE, "out", "기록", "보충경계2_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False, indent=1)[:2600])
    print("  ->", p)
    return v


# ── 겹 수 (메시 없이) ────────────────────────────────────────────────────────

def 겹수(cases=None):
    """기둥마다 hull 이 **몇 구간**인가. 높이장이 담을 수 있는 것은 K=1 뿐이다.

    두 겹 5장은 불리언 메시가 111만~234만 면이라 판본을 만들다 봉우리 27.1GB 를 냈다 (실측 · 이 바퀴에서 뺐다).
    그래서 메시를 안 만들고 답한다 — $256^3$ 불 배열 하나(16MB)면 구간 수와 **한 구간으로 뭉갤 때 더 채워지는 몫**이 나온다.
    이것이 높이장의 원리적 한계를 재는 값이고, 메모리와 무관하다."""
    out = {}
    for c in (cases or (경계집합() + 겹)):
        _, _, plain, _, _ = BG.gen_build(c)                  # plain = 이진 hull (256³)
        on = plain.any(1)
        d = np.diff(plain.astype(np.int8), axis=1)
        K = (d == 1).sum(1) + plain[:, 0, :].astype(np.int64)     # (x, z) 기둥마다 구간 수
        j = np.arange(plain.shape[1])[None, :, None]
        lo = np.where(plain, j, plain.shape[1]).min(1)
        hi = np.where(plain, j, -1).max(1)
        one = (j >= lo[:, None, :]) & (j <= hi[:, None, :]) & on[:, None, :]
        out[c] = {"두겹": bool(c in 겹),
                  "K≥2 기둥몫": round(float((K[on] >= 2).mean()), 4),
                  "K 최대": int(K[on].max()) if on.any() else 0,
                  "한구간 뭉갬 추가몫": round(float((one & ~plain).sum() / max(plain.sum(), 1)), 4)}
        print("  %-40s K≥2 %.4f · K최대 %2d · 뭉갬 +%.4f" % (c[:40], out[c]["K≥2 기둥몫"],
                                                            out[c]["K 최대"], out[c]["한구간 뭉갬 추가몫"]), flush=True)
        del plain, one, d, K
        gc.collect()
    g = lambda f: round(float(np.median([v["K≥2 기둥몫"] for k, v in out.items() if v["두겹"] == f])), 4)
    h = lambda f: round(float(np.median([v["한구간 뭉갬 추가몫"] for k, v in out.items() if v["두겹"] == f])), 4)
    v = {"판": TAG, "장별": out,
         "중앙": {"두 겹 5장": {"K≥2 기둥몫": g(True), "한구간 뭉갬 추가몫": h(True)},
                 "경계 17장": {"K≥2 기둥몫": g(False), "한구간 뭉갬 추가몫": h(False)}}}
    p = os.path.join(HERE, "out", "기록", "보충경계_겹수.json")
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  중앙", json.dumps(v["중앙"], ensure_ascii=False))
    print("  ->", p)
    return v


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def 발자국(on, axes):
    """(x, z) 칸 발자국 -> 1024² 정면 화소. 칸 하나가 4 화소라 5×5 로 채운다."""
    u, _, z = axes
    g = np.zeros((W.RES, W.RES), np.uint8)
    a, b = np.nonzero(on)
    py, px = W.topix(W.VIEW_AXIS["front"][1] * u[a], z[b])
    g[py, px] = 1
    return cv2.dilate(g, np.ones((5, 5), np.uint8)).astype(bool)


def selfcheck():
    BG.selfcheck()                                                   # 높이장 솔리드 닫힘 · 부피 · 경사면 계단

    # 2. 확장 높이장 — 발자국을 포함하고, 새 칸 높이가 이웃 사이에 있다
    n = 40
    on = np.zeros((n, n), bool)
    on[8:32, 8:32] = True
    jf = np.zeros((n, n), np.float32)
    jf[8:32, 8:32] = np.linspace(10, 22, 24)[:, None]
    on2 = cv2.dilate(on.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    jf2 = 넓히기(jf, on, on2)
    assert (on2 >= on).all() and on2.sum() == 26 * 26, "발자국이 한 칸만 넓어져야 한다 (%d)" % on2.sum()
    new = on2 & ~on
    assert (jf2[new] >= 10 - 1e-3).all() and (jf2[new] <= 22 + 1e-3).all(), "외삽이 이웃 범위를 벗어났다"
    assert np.allclose(jf2[on], jf[on]), "원래 칸의 높이가 바뀌었다"

    # 2b. 거칠기 추정기가 같은 메시에서 두 번 같은 값을 내나 (씨앗 고정이 실제로 먹나)
    sph = trimesh.creation.icosphere(subdivisions=4, radius=0.3)
    vax = (np.linspace(W.U0, W.U1, H.N),) * 2 + (np.linspace(W.Z0, W.Z1, H.N),)
    vm = C_.to_mesh(voxelize(sph, vax), vax)
    r1, r2 = roughness(vm, n=NPT)["거칠기"], roughness(vm, n=NPT)["거칠기"]
    assert r1 == r2, "거칠기가 같은 메시에서 두 번 다르다 (%s %s)" % (r1, r2)

    # 3. **반 칸 assert** — 합성 마스크 하나로 이 바퀴 고침의 전부를 건다
    import manifold3d as m3
    masks = {}
    for v in W.VIEWS:
        m = np.zeros((W.RES, W.RES), np.uint8)
        cv2.circle(m, (W.RES // 2, W.RES // 2), W.RES // 5, 1, -1)
        masks[v] = m.astype(bool)
    hull_m = m3.Manifold.batch_boolean([prism(masks[v], v, +1) for v in W.VIEWS], m3.OpType.Intersect)
    keep, axes = H.carve(masks, back_sign=+1)
    sil = masks["front"]
    f0 = 발자국(keep.any(1), axes)                                    # 지금 (반 칸 안쪽)
    m2, _ = 기본_높이장2(masks, +1, grow=1)
    pat = m3.Manifold.batch_boolean([gen_manifold(m2), hull_m], m3.OpType.Intersect)
    V, F = np.asarray(to_trimesh(pat).vertices), np.asarray(to_trimesh(pat).faces)
    f1 = np.asarray(W.silhouette(V, F, "front")).astype(bool)         # 고친 뒤 (정확 hull 로 되자름)
    # **테두리 띠**로 본다 — 실물의 빈 자리가 거기 있다. 전체 넓이로 보면 반 칸이 0.2% 로 묻힌다
    band = sil & ~cv2.erode(sil.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    c0 = float((band & f0).sum() / band.sum())
    c1 = float((band & f1).sum() / band.sum())
    out = float((f1 & ~sil).sum() / max(f1.sum(), 1))
    assert c0 < 0.98, "합성 원에서 지금 발자국이 이미 테두리를 다 덮는다 (%.4f) — 이 바퀴의 전제가 틀렸다" % c0
    assert c1 >= 0.99, "고친 발자국이 테두리를 다 안 덮는다 (%.4f)" % c1
    assert c1 - c0 > 0.02, "고침이 테두리를 더 안 덮는다 (%.4f -> %.4f)" % (c0, c1)
    assert out <= 0.01, "고친 패치가 실루엣 밖으로 샜다 (%.4f) — ∩hull 안전판이 안 먹는다" % out
    print("  자가검사 통과 — 확장 발자국 %d칸 · 합성 원 테두리 덮음 %.4f -> %.4f · 넘침 %.4f"
          % (on2.sum(), c0, c1, out))


def plumb(case=None):
    """배관 + **재현 게이트** — 어제 D 를 실제로 다시 만들어 값이 같은지 본다."""
    case = case or 경계집합()[0]
    y = 어제()
    ctx0 = BG.prepare(case)
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    d = BG.make(ctx0, "D 불리언+높이장보충")
    got = {"거칠기": roughness(d, n=NPT)["거칠기"], "iou": BG.score(truth, d, J.PITCH),
           "못덮음": round(max(sil_fit(voxelize(d, ctx0["axes"]), ctx0["masks"], ctx0["bs"],
                                      ctx0["axes"])[k] for k in ("못덮음_front", "못덮음_side")), 4)}
    want = y[case]["D 불리언+높이장보충"]
    # **거칠기 문턱만 느슨하다.** 같은 기하가 같은 면 수 · 같은 부피로 돌아와도 삼각형 순서가 달라져
    # 표본점이 바뀐다 — 어제 기록의 두 판 8장 24쌍에서 면 · 부피 · IoU · 못덮음은 24/24 완전 일치인데
    # 거칠기만 중앙 0.0016 · 최대 0.0041 흔들렸다. 1e-3 은 그 드리프트보다 좁아 우연히 통과한 문턱이었다
    for k, tol in (("거칠기", 5e-3), ("iou", 1e-3), ("못덮음", 1e-4)):
        assert abs(got[k] - want[k]) <= tol, "재현 게이트: %s 가 어제와 다르다 (%s 대 %s)" % (k, got[k], want[k])
    del d, ctx0
    gc.collect()

    ctx = prepare(case)
    for v in W.VIEWS:
        assert not (ctx["gaps"][v] & ~ctx["masks"][v]).any(), "빈 자리가 원화 실루엣 밖으로 나갔다"
    b = make(ctx, "B 불리언+복셀보충")
    d2 = make(ctx, "D′ 보충경계")
    vb, v2 = abs(b.volume), abs(d2.volume)
    assert b.is_watertight and d2.is_watertight, "판본이 안 닫혔다"
    assert 0.8 < v2 / max(vb, 1e-9) < 1.25, "D′ 부피가 B 의 %.2f 배다" % (v2 / vb)
    bp = inflate(b, v2)
    assert abs(abs(bp.volume) - v2) / v2 < 1e-3, "B⁺ 부피가 D′ 에 안 맞았다"
    print("  배관 통과 — %s · 재현 %s · 부피비 D′/B %.3f · 봉우리 %.1fGB"
          % (case, json.dumps(got, ensure_ascii=False), v2 / vb, 봉우리GB()))


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        selfcheck()
        H.register_sheets()
        for c in (sys.argv[2:] or [None, "knight_Warrior_RaWl2GJ0NZ"]):   # 재현 게이트는 **두 장**이다 (계획 §배관 4)
            plumb(c)
    elif a == "판정2":
        판정2()
    elif a == "판정":
        verdict()
    elif a == "논문자료":
        논문자료()
    elif a in ("침식", "갈래", "메카"):
        H.register_sheets()
        {"침식": 침식, "갈래": 갈래, "메카": 메카}[a](int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    elif a == "겹수":
        H.register_sheets()
        겹수()
    elif a == "범위":
        H.register_sheets()
        run(int(sys.argv[2]) if len(sys.argv) > 2 else 1, cases=겹, 범위=True)
    elif a == "그림":
        import 보충경계그림
        보충경계그림.main(sys.argv[2:] or None)
    else:
        H.register_sheets()
        run(int(a))


if __name__ == "__main__":
    main()
