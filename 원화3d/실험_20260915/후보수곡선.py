# -*- coding: utf-8 -*-
"""**평면 후보 수 곡선 (B1′)** — 균일 후보를 K · 2K · 4K · 8K 로 늘리면 상수·원화판에 닿나 (2026-09-15).

    python 후보수곡선.py 검사     자가검사만
    python 후보수곡선.py [n]      아직 안 한 장 n 개 (첫 장은 열린 궤짝) -> out/기록/후보수곡선_진행.jsonl
    python 후보수곡선.py 판정     -> out/기록/후보수곡선_<때>.json

판정은 `claudedocs/plan_후보수곡선_20260915.md` 「판정」 절 그대로다 — 돌리기 전에 적었다.
후보 · 배정은 `실험_20260914/옆판후보.py` 를 그대로 쓴다 (배정 = 오라클). 값은 [속 빈 정답, 속 채운 정답].
"""
import gc
import json
import os
import sys
import time

import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, os.path.join(HERE, "실험_20260914"))
sys.path.insert(0, os.path.join(HERE, "실험_20260915"))
import 옆판후보 as PB
from 겉면채점 import fill_slices

B, P, H, W, O = PB.B, PB.P, PB.H, PB.W, PB.O
import 정답 as J

CASES = PB.CASES
MS = (1, 2, 4, 8)
LAM = PB.LAM
TAG = "후보수곡선 · _선2 · 오라클 배정 · 균일×1·2·4·8 · lam1.00 · 빈/속채운 정답 · 격자2 (2026-09-15)"
PROG = os.path.join(HERE, "out", "기록", "후보수곡선_진행.jsonl")
NAMES = ("이진", "오라클", "상수·원화판") + tuple("균일×%d" % m for m in MS)


def uniform(sy, m):
    """옆판 후보 수의 m 배를 옆판 후보의 맨 앞~맨 뒤에 고르게 (m=1 이 09-14 후보·균일)."""
    return np.linspace(sy.min(), sy.max(), len(sy) * m)


def scorer(truth):
    """격자마다 정답 복셀 · 속채움을 한 번 굽고, 메시마다 [속 빈, 속 채운] IoU."""
    grids = {}
    for tag, p in (("", J.PITCH), ("·192", P.P192)):
        T, ot = J.grid(truth, p)
        grids[tag] = (p, T, fill_slices(T), ot)

    def score(mesh):
        out = {}
        for tag, (p, T, F, ot) in grids.items():
            G, og = J.grid(mesh, p)
            A, B_ = J.common(T, ot, G, og)
            Fc, _ = J.common(F, ot, G, og)
            iou = lambda X: round(float((X & B_).sum() / max((X | B_).sum(), 1)), 5)
            out[tag] = [iou(A), iou(Fc)]
        return out
    return score


def one(case):
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", B.NEW(case), "truth.glb"), force="mesh")
    score = scorer(truth)
    C, lo, hi = PB.cands_of(case, truth)
    sy = C["후보·옆판"]
    row = {"case": case, "판": TAG, "K": len(sy)}
    plain, vox, axes, _ = O.build(B.NEW(case), truth, LAM, "오라클")
    for name, v in (("이진", plain), ("오라클", vox)):
        s = score(O.C.to_mesh(v, axes))
        row[name], row[name + "·192"] = s[""], s["·192"]
    del plain, vox
    for name in NAMES[2:]:
        ys = None if name == "상수·원화판" else uniform(sy, int(name.split("×")[1]))
        _, vox, axes, _ = O.build(B.NEW(case), truth, LAM, "오라클", post=PB.post_of(case, ys, lo, hi))
        s = score(O.C.to_mesh(vox, axes))
        row[name], row[name + "·192"] = s[""], s["·192"]
        del vox
        gc.collect()
    row["초"] = round(time.time() - t0, 1)
    return row


def pipe(row):
    """속 빈 정답 · 128 이 09-14 기록과 같나 — 균일×1 대 옆판후보 후보·균일 · 상수·원화판 대 벤치선."""
    old = B.read_prog(PB.PROG, PB.TAG)[row["case"]]
    bench = B.read_prog(B.PROG, B.TAG)[row["case"]]
    return max(abs(row["균일×1"][0] - old["후보·균일"]), abs(row["상수·원화판"][0] - bench["상수·원화판"]))


def judge(rows):
    out = {"판": TAG, "장": len(rows)}
    diffs = [pipe(r) for r in rows]
    out["배관 최대차"] = round(max(diffs), 6)
    if max(diffs) >= 1e-4:
        out["배관"] = "어긋남 — 숫자를 버린다"
        return out
    out["배관"] = "통과"
    for j, truthname in ((1, "속 채운 정답"), (0, "속 빈 정답")):
        blk = {}
        for tag in ("", "·192"):
            g = lambda k: np.array([r[k + tag][j] for r in rows])
            ceil = g("오라클") - g("이진")
            live = ceil > 0.01
            frac = lambda k: float(np.median((g(k) - g("이진"))[live] / ceil[live]))
            S = frac("상수·원화판")
            curve = {"균일×%d" % m: round(frac("균일×%d" % m), 4) for m in MS}
            reach = [m for m in MS if curve["균일×%d" % m] >= 0.8 * S]
            blk["격자" + (tag or "128")] = {"천장 있는 장": int(live.sum()), "S 상수·원화판": round(S, 4), "곡선": curve,
                                         "0.8S 에 닿는 가장 작은 m": (reach[0] if reach else None)}
        out[truthname] = blk
    ms = [b["0.8S 에 닿는 가장 작은 m"] for b in out["속 채운 정답"].values()]
    m = None if None in ms else max(ms)
    out["m (속 채운 정답 · 격자 둘 중 큰 쪽)"] = m
    out["K 중앙"] = float(np.median([r["K"] for r in rows]))
    out["다음"] = ("결과만 적는다 — 8K 로도 닿지 않는다" if m is None else
                  "게이트 C — 판마다 후보를 원화에서 고르는 규칙" if m <= 2 else
                  "후보 방식 대신 판마다 깊이 한 값을 직접 추정")
    return out


def figure(cases=("cloak_Chest_O72u4Drp8k", "스캔_Victor_Reversible_Bookend", "cape_Hat_Stylised_lNN3PlrjSa", "statue_Town_Center_cuQuFJEIfH")):
    """45도 깊이색 — 정답 · 이진 · 상수·원화판 · 균일×1 · ×2 · ×8. 후보가 촘촘해지면 판 깊이가 어디서 정답에 붙나."""
    import 깊이색 as DC
    import 앨리어싱 as AL
    rows = []
    for case in cases:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", B.NEW(case), "truth.glb"), force="mesh")
        C, lo, hi = PB.cands_of(case, truth)
        sy = C["후보·옆판"]
        M = {}
        for name in ("상수·원화판", "균일×1", "균일×2", "균일×8"):
            ys = None if name == "상수·원화판" else uniform(sy, int(name.split("×")[1]))
            pl, vox, axes, _ = O.build(B.NEW(case), truth, LAM, "오라클", post=PB.post_of(case, ys, lo, hi))
            M.setdefault("이진", O.C.to_mesh(pl, axes))
            M[name] = O.C.to_mesh(vox, axes)
        fr, dr = AL.frame_of(M["이진"], 45), DC.depth_range(M["이진"], 45)
        tiles = [DC.colorize(DC.zbuffer(truth, 45, fr, 360), dr)]
        tiles += [DC.colorize(DC.zbuffer(M[k], 45, fr, 360), dr) for k in ("이진", "상수·원화판", "균일×1", "균일×2", "균일×8")]
        rows.append(("%s · K %d" % (case[:14], len(sy)), tiles))
        print("  %s 그림" % case, flush=True)
    DC.grid(rows, ["정답", "이진", "상수·원화판", "균일 ×1", "균일 ×2", "균일 ×8"],
            "평면 후보 수 — 판마다 깊이를 후보 중 가장 가까운 것으로 (45도 · lam 1.00 · 오라클 배정)",
            "상수·원화판 = 판마다 정답 깊이 중앙값 · 균일 ×m = 옆판 후보 수 K 의 m 배를 고르게. 색 = 카메라에서 거리",
            os.path.join(HERE, "out", "깊이색_후보수곡선.png"), S=300)
    print("  -> out/깊이색_후보수곡선.png")


def selfcheck():
    sy = np.array([0.1, 0.3, 0.7])
    u1, u4 = uniform(sy, 1), uniform(sy, 4)
    assert len(u1) == 3 and np.allclose(u1, [0.1, 0.4, 0.7]) and len(u4) == 12 and np.isclose(u4[0], 0.1) and np.isclose(u4[-1], 0.7), "균일 후보"
    # 후보가 촘촘해질수록 배정 오차는 줄어야 한다 (0~1 사이 값 100 개)
    v = np.linspace(0.0, 1.0, 100)
    err = [np.abs(v[:, None] - np.linspace(0, 1, k)[None]).min(1).mean() for k in (3, 6, 12, 24)]
    assert all(a > b for a, b in zip(err, err[1:])), "후보가 늘어도 오차가 안 준다 %s" % err
    PB.selfcheck()
    print("  자가검사 통과 — 균일 후보 · 촘촘할수록 오차 감소")


def main():
    H.register_sheets()
    selfcheck()
    arg = sys.argv[1] if len(sys.argv) > 1 else "1"
    if arg == "검사":
        return
    if arg == "그림":
        return figure()
    done = B.read_prog(PROG, TAG)
    if arg != "판정":
        order = ["cloak_Chest_O72u4Drp8k"] + [c for c in CASES if c != "cloak_Chest_O72u4Drp8k"]
        for c in [c for c in order if c not in done][:int(arg)]:
            r = one(c)
            with open(PROG, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            done[c] = r
            d = pipe(r)
            print("  %-26s K %d · 배관차 %.6f · " % (c[:26], r["K"], d)
                  + " · ".join("%s %.3f/%.3f" % (k, r[k][0], r[k][1]) for k in NAMES) + " · %.0f초" % r["초"], flush=True)
            if d >= 1e-4:
                print("  배관 어긋남 — 멈춘다")
                return
    rows = [done[c] for c in CASES if c in done]
    if len(rows) == len(CASES) or arg == "판정":
        v = judge(rows)
        print(json.dumps(v, ensure_ascii=False, indent=1))
        p = os.path.join(HERE, "out", "기록", "후보수곡선_%s.json" % time.strftime("%Y%m%d_%H%M"))
        json.dump({"판정": v, "rows": rows}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  -> %s" % p)
    else:
        print("  %d/%d 장 — 다시 돌리면 이어 돈다" % (len(rows), len(CASES)))


if __name__ == "__main__":
    main()
