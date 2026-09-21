# -*- coding: utf-8 -*-
"""**타원 깎기를 연속 장으로 다시 쓴다** — 벤치 28 장에서 지금 기본과 겨룬다 (2026-09-21).

    python 장타원.py 검사
    python 장타원.py [n]       아직 안 한 장 n 개 -> out/기록/장타원_진행.jsonl
    python 장타원.py 판정      -> out/기록/장타원_<때>.json
    python 장타원.py 그림      -> out/장타원_접촉지.png

09-21 `연속hull` 이 보였다 — 마칭큐브에 0/1 복셀 대신 연속 장을 주면 거칠기 0.28 → 0.10.
그건 이진 hull 끼리의 비교였다. **지금 기본은 타원 깎기**(`hull.carve_default` · 09-15 채택)라,
같은 생각을 기본에 걸려면 **타원 깎기도 연속 장으로** 써야 한다.

**가정은 하나도 안 바꾼다** — 높이마다 hull 단면(x 구간 × y 구간 직사각형)에 **내접 타원**.
`hull.superellipse(p=2)` 와 같은 모양이다. 바꾸는 것은 표현뿐이다:

    지금   256³ 복셀에 타원을 0/1 로 찍고 -> 마칭큐브(0.5)         계단 · 가로 찢김
    여기   g = 1 − ((x−cx)/a)² − ((y−cy)/b)² 를 **연속값으로** -> 마칭큐브(0)
           구간의 끝은 1024² 마스크에서 읽는다 (격자보다 4 배 촘촘)

판본 셋 — **기준**(지금 기본 · 복셀 타원) · **장타원** · **연속이진**(둥글림 없는 연속 장 — 「연속 장의 몫」과
「둥글림의 몫」을 가르는 대조군).

**문턱을 돌리기 전에 적는다.** 점수는 점수판과 같다 — 실물 28 장 · 속 채운 정답 · IoU.

    Q1  장타원 − 기준 의 IoU(128) **차 중앙 >= −0.005**  (매끄러움을 사느라 형태를 잃지 않는다)
    Q2  장타원의 **거칠기 중앙이 기준의 절반 아래**
    Q3  격자 192 에서도 차 중앙 >= −0.005  (자를 바꿔도 같은 방향)

**기본값은 이 바퀴가 안 바꾼다** — 통과해도 사람이 정한다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260920")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260919")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260916")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260915")
import 연속hull as CH
H, W, LR = CH.H, CH.W, CH.LR
HERE, OUT = CH.HERE, CH.OUT
import 점수판 as SB
import 대조 as C
PROG = os.path.join(OUT, "장타원_진행.jsonl")
TAG = "장타원 v1 · 기준(복셀 타원) 대 장타원 대 연속이진 · 실물28 · 속채운 IoU 128·192 · 거칠기 (2026-09-21)"
판본 = ("기준", "장타원", "연속이진")
Q1여유, Q3여유 = -0.005, -0.005


def 구간(occ):
    """1D bool -> [(시작칸, 끝칸+1), …]."""
    d = np.diff(np.concatenate(([0], occ.astype(np.int8), [0])))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def _축값(runs, u):
    """격자 좌표 u 마다 (정규화 제곱거리 X, 반폭 a). 구간 밖이면 제일 가까운 구간의 값(X > 1)."""
    px = (W.U1 - W.U0) / W.RES
    X = np.full(len(u), 4.0, np.float32)
    A = np.full(len(u), px, np.float32)
    for c0, c1 in runs:
        x0, x1 = W.U0 + c0 * px, W.U0 + c1 * px
        a, cx = max((x1 - x0) / 2, px / 2), (x0 + x1) / 2
        q = ((u - cx) / a) ** 2
        better = q < X
        X[better], A[better] = q[better], a
    return X, A


def 타원장(masks, bs, N=None):
    """높이마다 단면 직사각형에 내접 타원 — **연속값**. 안 +, 칸 단위."""
    N = N or H.N
    u = W.U0 + (np.arange(N) + 0.5) / N * (W.U1 - W.U0)
    z = W.Z0 + (np.arange(N) + 0.5) / N * (W.Z1 - W.Z0)
    rows = np.clip(((W.Z1 - z) / (W.Z1 - W.Z0) * W.RES).astype(int), 0, W.RES - 1)
    F, S = masks["front"], masks["side"]
    B = masks["back"][:, ::-1] if bs < 0 else masks["back"]      # 뒤 판의 열을 세계 x 순서로
    cell = (W.U1 - W.U0) / N
    g = np.full((N, N, N), -2.0, np.float32)
    for k, r in enumerate(rows):
        xr, yr = 구간(F[r] & B[r]), 구간(S[r])
        if not xr or not yr:
            continue
        X, A = _축값(xr, u)
        Y, Bh = _축값(yr, u)
        g[:, :, k] = (1.0 - X[:, None] - Y[None, :]) * np.minimum(A[:, None], Bh[None, :]) / 2 / cell
    return g, (u, u, z)


def 메시(field, axes):
    V, F = H.mesh_from_field(field, axes)
    m = trimesh.Trimesh(V, F, process=False)                  # process=True 는 넓이 0 인 면을 만들어 메시를 연다 (09-21)
    if m.volume < 0:
        m.invert()
    return m


def 재다(m, truth):
    from 면 import dihedral, roughness
    s = SB.score(truth, m)
    d = dihedral(m)
    return {"iou128": s[""][1], "iou192": s["·192"][1], "iou128빈": s[""][0],
            "거칠기": roughness(m)["거칠기"], "계단": d["계단"], "평평": d["평평"],
            "면": int(len(m.faces)), "닫힘": bool(m.is_watertight)}


def one(case):
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    masks = LR.CG.G3.art_masks(case) if hasattr(LR, "CG") else None
    if masks is None:
        import 생성3D as G3
        masks = G3.art_masks(case)
    bs = H.CASES[case]["back_sign"]
    _, deep, axes, _ = C.build(case)
    r = {"case": case, "판": TAG, "기본값": "%s lam%.2f" % (H.DEPTH, H.DEPTH_LAM)}
    ms = {"기준": C.to_mesh(deep, axes)}
    g, ax = 타원장(masks, bs)
    ms["장타원"] = 메시(g, ax)
    f, ax2 = CH.연속장(masks, bs)
    ms["연속이진"] = 메시(f / ((W.U1 - W.U0) / H.N), ax2)
    d = os.path.join(HERE, "out", "장타원", case)
    os.makedirs(d, exist_ok=True)
    for n, m in ms.items():
        r[n] = 재다(m, truth)
        m.export(os.path.join(d, "%s.glb" % n))
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


def run(n):
    H.register_sheets()
    for c in [x for x in SB.cases() if x not in rows()][:n]:
        r = one(c)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  %-36s IoU %s · 거칠기 %s · %.0f초"
              % (c[:36], " ".join("%s %.3f" % (n_, r[n_]["iou128"]) for n_ in 판본),
                 " ".join("%.3f" % r[n_]["거칠기"] for n_ in 판본), r["초"]), flush=True)


def verdict():
    rs = rows()
    cs = sorted(rs)
    med = lambda x: round(float(np.median(x)), 5)
    col = lambda n, k: [rs[c][n][k] for c in cs]
    v = {"판": TAG, "때": time.strftime("%Y%m%d_%H%M"), "장": len(cs),
         "안잰": [c for c in SB.cases() if c not in rs],
         "중앙": {n: {k: med(col(n, k)) for k in ("iou128", "iou192", "거칠기", "계단", "평평")} for n in 판본}}
    for n in ("장타원", "연속이진"):
        d128 = [rs[c][n]["iou128"] - rs[c]["기준"]["iou128"] for c in cs]
        d192 = [rs[c][n]["iou192"] - rs[c]["기준"]["iou192"] for c in cs]
        v[n + " − 기준"] = {"IoU128 차 중앙": med(d128), "승": int(sum(x > 0 for x in d128)), "패": int(sum(x < 0 for x in d128)),
                          "최악": round(float(min(d128)), 5), "최악장": cs[int(np.argmin(d128))],
                          "IoU192 차 중앙": med(d192),
                          "거칠기 비(중앙)": round(med(col(n, "거칠기")) / max(med(col("기준", "거칠기")), 1e-9), 4)}
    a = v["장타원 − 기준"]
    v["Q1"] = {"문턱": "IoU128 차 중앙 >= %g" % Q1여유, "값": a["IoU128 차 중앙"], "통과": bool(a["IoU128 차 중앙"] >= Q1여유)}
    v["Q2"] = {"문턱": "거칠기 중앙이 기준의 절반 아래", "값": a["거칠기 비(중앙)"], "통과": bool(a["거칠기 비(중앙)"] < 0.5)}
    v["Q3"] = {"문턱": "IoU192 차 중앙 >= %g" % Q3여유, "값": a["IoU192 차 중앙"], "통과": bool(a["IoU192 차 중앙"] >= Q3여유)}
    v["표"] = {c: {n: rs[c][n] for n in 판본} for c in cs}
    p = os.path.join(OUT, "장타원_%s.json" % v["때"])
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %-10s %8s %8s %8s %8s %8s" % ("판본", "IoU128", "IoU192", "거칠기", "계단", "평평"))
    for n in 판본:
        x = v["중앙"][n]
        print("  %-10s %8.4f %8.4f %8.4f %8.4f %8.4f" % (n, x["iou128"], x["iou192"], x["거칠기"], x["계단"], x["평평"]))
    for k in ("장타원 − 기준", "연속이진 − 기준", "Q1", "Q2", "Q3"):
        print("\n  %s %s" % (k, json.dumps(v[k], ensure_ascii=False)))
    print("\n  ->", p)
    return v


def 그림(cases=None):
    import 폴리싱 as PL
    import 앨리어싱 as AL
    rs = rows()
    cs = cases or [c for c in ("cloak_Chest_Closed_AngpV0HxD8", "mech_Drill_8uBbH7Dvmb", "knight_Warrior_RaWl2GJ0NZ",
                               "wizard_Evil_Wizard_bdxawstqtq", "avatarsample_g", "monster_Mimic_B8HrWzkuNp") if c in rs]
    R = []
    for c in cs:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        fr = AL.frame_of(truth, 45)
        ts = [PL.shaded(truth, 45, fr, S=400)]
        for n in 판본:
            ts.append(PL.shaded(trimesh.load(os.path.join(HERE, "out", "장타원", c, "%s.glb" % n), force="mesh"), 45, fr, S=400))
        R.append(("%s\nIoU %s\n거칠기 %s" % (c[:20], " ".join("%.3f" % rs[c][n]["iou128"] for n in 판본),
                                          " ".join("%.2f" % rs[c][n]["거칠기"] for n in 판본)), ts))
    LR.DC.grid(R, ("정답", "기준 (복셀 타원 · 지금 기본)", "장타원 (같은 가정 · 연속 장)", "연속이진 (둥글림 없음)"),
               "장타원 — 타원 깎기를 연속 장으로 (45° 명암 · 같은 빛 · 같은 틀)",
               "IoU(속 채운 정답 · 128) · 거칠기를 장 이름 아래 기준 · 장타원 · 연속이진 순서로 적었다",
               os.path.join(HERE, "out", "장타원_접촉지.png"), S=330)


def selfcheck():
    # 정사각 기둥 마스크 -> 단면이 **원**이어야 한다. 부피 = π a² h
    m = np.zeros((W.RES, W.RES), bool)
    m[300:700, 400:600] = True
    g, ax = 타원장({"front": m, "side": m, "back": m}, +1, N=128)
    t = 메시(g, ax)
    px = (W.U1 - W.U0) / W.RES
    기대 = np.pi * (100 * px) ** 2 * (400 * px)
    assert t.is_watertight and abs(t.volume - 기대) / 기대 < 0.03, (t.volume, 기대)
    assert 구간(np.array([0, 1, 1, 0, 1], bool)) == [(1, 3), (4, 5)]
    print("  자가검사 통과 — 원기둥 부피 %.5f (기대 %.5f)" % (t.volume, 기대))


if __name__ == "__main__":
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        selfcheck()
    elif a == "판정":
        verdict()
    elif a == "그림":
        그림()
    else:
        run(int(a))
