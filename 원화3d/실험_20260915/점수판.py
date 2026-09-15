# -*- coding: utf-8 -*-
"""**기본 파이프라인 점수판** — 옛 기본(파이프 lam0.20) 대 새 기본(`hull.carve_default`) (2026-09-15).

    python 점수판.py 검사     자가검사만
    python 점수판.py [n]      아직 안 한 장 n 개 -> out/기록/점수판_진행.jsonl
    python 점수판.py 판정     -> out/기록/점수판_<때>.json

판정은 `claudedocs/plan_점수판_20260915.md` 「판정」 절 그대로다 — 돌리기 전에 적었다.
점수 = 실물 28장 · 속 채운 정답 · 격자 128 · IoU 중앙값. 값은 [속 빈 정답, 속 채운 정답].
"""
import json
import os
import sys
import time

import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260915"))
os.chdir(HERE)
import hull as H
import 대조 as C
import 오라클 as O
import 정답 as J
import win as W
from 겉면채점 import bench_cases, fill_slices

PROG = os.path.join(HERE, "out", "기록", "점수판_진행.jsonl")
TAG = "점수판 · 실물28 · 옛 기본(파이프 lam0.20) · 새 기본(hull.carve_default) · 빈/속채운 · 격자128·192 (2026-09-15)"
P192 = (W.U1 - W.U0) / 192.0


def cases():
    return [c for c in bench_cases() if c != "소체"]


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[r["case"]] = r
    return out


def score(truth, mesh):
    out = {}
    for tag, p in (("", J.PITCH), ("·192", P192)):
        T, ot = J.grid(truth, p)
        F = fill_slices(T)
        G, og = J.grid(mesh, p)
        A, B = J.common(T, ot, G, og)
        Fc, _ = J.common(F, ot, G, og)
        iou = lambda X: round(float((X & B).sum() / max((X | B).sum(), 1)), 5)
        out[tag] = [iou(A), iou(Fc)]
    return out


def one(c):
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
    _, old, axes, _ = O.build(c, truth, H.LAM, "파이프")
    s_old = score(truth, O.C.to_mesh(old, axes))
    _, new, axes2, _ = C.build(c)
    s_new = score(truth, O.C.to_mesh(new, axes2))
    return {"case": c, "판": TAG, "기본값": "%s lam%.2f" % (H.DEPTH, H.DEPTH_LAM),
            "옛": s_old[""], "옛·192": s_old["·192"], "새": s_new[""], "새·192": s_new["·192"], "초": round(time.time() - t0, 1)}


def pipe(r):
    b = {x["case"]: x for x in map(json.loads, open(os.path.join(HERE, "out", "기록", "겉면채점_벤치_진행.jsonl"), encoding="utf-8"))}[r["case"]]
    c = {x["case"]: x for x in map(json.loads, open(os.path.join(HERE, "out", "기록", "천장_실물.jsonl"), encoding="utf-8"))}[r["case"]]
    return abs(r["새"][1] - b["타원1.00"][1]), abs(r["옛"][0] - c["파이프0.20"]["iou"])


def adopt(d):
    """채택 규칙 — 중앙 > 0 · 과반 승 · 한 장씩 빼도 중앙 > 0."""
    d = np.asarray(d, float)
    loo = [float(np.median(np.delete(d, i))) for i in range(len(d))]
    return {"중앙": round(float(np.median(d)), 4), "승": int((d > 0).sum()), "장": len(d),
            "한 장 빼기 최소 중앙": round(min(loo), 4),
            "통과": bool(np.median(d) > 0 and (d > 0).sum() > len(d) / 2 and min(loo) > 0)}


def judge():
    rs = rows()
    cs = [c for c in cases() if c in rs]
    out = {"판": TAG, "장": len(cs)}
    if len(cs) < len(cases()):
        out["판정"] = "%d/%d 장 — 판정 안 함" % (len(cs), len(cases()))
        return out
    pd = [pipe(rs[c]) for c in cs]
    out["배관 최대차 새 · 옛"] = [round(max(p[0] for p in pd), 6), round(max(p[1] for p in pd), 6)]
    if max(p[0] for p in pd) >= 1e-4 or max(p[1] for p in pd) >= 0.002:
        out["배관"] = "어긋남 — 숫자를 버린다"
        return out
    out["배관"] = "통과"
    for tag, name in (("", "격자128"), ("·192", "격자192")):
        old = np.array([rs[c]["옛" + tag][1] for c in cs])
        new = np.array([rs[c]["새" + tag][1] for c in cs])
        out[name] = {"점수 옛 → 새 (속 채운 정답 중앙)": [round(float(np.median(old)), 4), round(float(np.median(new)), 4)],
                     "속 빈 정답 중앙 옛 → 새": [round(float(np.median([rs[c]["옛" + tag][0] for c in cs])), 4),
                                           round(float(np.median([rs[c]["새" + tag][0] for c in cs])), 4)],
                     "채택 규칙": adopt(new - old),
                     "지는 장": {c: round(float(n - o), 4) for c, o, n in zip(cs, old, new) if n < o}}
    ok = out["격자128"]["채택 규칙"]["통과"] and out["격자192"]["채택 규칙"]["통과"]
    out["다음"] = "새 기본을 남긴다" if ok else "hull.DEPTH 를 파이프로 되돌린다"
    return out


def selfcheck():
    r = adopt([0.1, 0.2, -0.05, 0.3, 0.15])
    assert r["통과"] and r["승"] == 4, "채택 규칙 %s" % r
    assert not adopt([0.5, -0.1, -0.1, -0.1, 0.5])["통과"], "과반이 지는데 통과했다"
    assert not adopt([0.01, 0.01, -0.3, -0.3, 0.01, -0.3])["통과"], "한 장 빼면 뒤집히는데 통과했다"
    print("  자가검사 통과 — 채택 규칙 (중앙 · 과반 · 한 장 빼기)")


def main():
    selfcheck()
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        return
    if a != "판정":
        done = rows()
        for c in [c for c in cases() if c not in done][:int(a)]:
            r = one(c)
            with open(PROG, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            pn, po = pipe(r)
            print("  %-28s 옛 %.3f/%.3f · 새 %.3f/%.3f · 배관차 새 %.6f 옛 %.4f · %.0f초" % (c[:28], *r["옛"], *r["새"], pn, po, r["초"]), flush=True)
            if pn >= 1e-4 or po >= 0.002:
                print("  배관 어긋남 — 멈춘다")
                return
        print("  남은 것 %d 장" % (len(cases()) - len(rows())))
    if a == "판정" or len(rows()) >= len(cases()):
        v = judge()
        print(json.dumps(v, ensure_ascii=False, indent=1))
        p = os.path.join(HERE, "out", "기록", "점수판_%s.json" % time.strftime("%Y%m%d_%H%M"))
        json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  -> %s" % p)


if __name__ == "__main__":
    main()
