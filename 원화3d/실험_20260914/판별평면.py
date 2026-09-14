# -*- coding: utf-8 -*-
"""**판마다 평면이면 충분한가** — 정답 깊이를 판 단위로 뭉개서 천장이 얼마나 남나 (2026-09-14).

    python 판별평면.py 검사     자가검사만
    python 판별평면.py [n]      아직 안 한 케이스 n 장 (기본 1) -> out/기록/판별평면_진행.jsonl
    python 판별평면.py 판정     모인 것으로 판정 -> out/기록/판별평면_<때>.json
    python 판별평면.py 그림     -> out/깊이색_판별평면.png

열린 궤짝은 지금 깊이맵으로 hull 과 ±0.001 인데 정답 깊이를 넣으면 +0.13 이다
(`claudedocs/research_각진깊이_20260914.md`). 「판마다 평면 + 앞뒤」로 그 +0.13 에 닿을 수 있나를
**방법을 짓기 전에** 오라클로 잰다.

## 판본 (lam 1.00, 기준만 0.20)

    이진 · 기준(파이프) · 오라클 · 상수·정답면 · 적합·정답면(배관 검사) · 상수·원화판 · 적합·원화판

## 판정 — 돌리기 전에 적었다 (`claudedocs/plan_판별평면_20260914.md`)

    천장몫(k) = (IoU k − 이진) / (오라클 − 이진). 천장 ≤ 0.01 인 장은 뺀다. 각진 7장만 판정
    배관       |적합·정답면 − 오라클| < 0.02 모든 장. 아니면 숫자를 버린다
    Q1 표현    상수·정답면 천장몫 중앙 ≥ 0.8 · 제 부피 대조군 통과 (격자 둘 평균>0 · 과반)
    Q2 분할    상수·원화판 또는 적합·원화판 천장몫 중앙 ≥ 0.5 · 제 부피 대조군 통과
    Q1 X -> 멈춤 · Q1 O Q2 O -> 게이트 B (옆판 평면 후보) · Q1 O Q2 X -> 게이트 A (벤치 선)
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
sys.path.insert(0, os.path.join(HERE, "실험_20260913"))
os.chdir(HERE)
import hull as H
import win as W
import 오라클 as O
import 표면 as SF

ANGULAR = ["cloak_Chest_Closed_AngpV0HxD8", "cloak_Chest_O72u4Drp8k", "스캔_Victor_Reversible_Bookend",
           "mech_Drill_8uBbH7Dvmb", "cape_Hat_Stylised_lNN3PlrjSa", "monster_Mimic_B8HrWzkuNp",
           "statue_Town_Center_cuQuFJEIfH"]
PEOPLE = ["base_male", "sakurada_fumiriya", "avatarsample_g", "wizard_Evil_Wizard_bdxawstqtq"]
CASES = ANGULAR + PEOPLE
SPEC = {                                     # 이름: (깊이맵, 판, 뭉개기)
    "기준": ("파이프", None, None),
    "오라클": ("오라클", None, None),
    "상수·정답면": ("오라클", "정답면", "상수"),
    "적합·정답면": ("오라클", "정답면", "적합"),
    "상수·원화판": ("오라클", "원화판", "상수"),
    "적합·원화판": ("오라클", "원화판", "적합"),
}
LAM = 1.00
P192 = (W.U1 - W.U0) / 192.0
TAG = "판별평면 · 오라클 뭉개기 · lam1.00 · 격자2 · 제부피대조 (2026-09-14)"
PROG = os.path.join(HERE, "out", "기록", "판별평면_진행.jsonl")


def flatten(dep, lab, mask, mode):
    """판마다 깊이를 평면 하나로. `상수` = 중앙값 (정면을 보는 축정렬 면 — Manhattan) ·
    `적합` = h = a·x + b·y + c 최소제곱 (기울어진 면까지). 판 밖(`mask` 밖 · `lab<=0`)은 그대로."""
    out = dep.copy()
    ys, xs = np.nonzero(mask & (lab > 0))
    if len(ys) == 0:
        return out
    L = lab[ys, xs]
    o = np.argsort(L, kind="stable")
    ys, xs, L = ys[o], xs[o], L[o]
    cuts = np.flatnonzero(np.diff(L)) + 1
    for yy, xx in zip(np.split(ys, cuts), np.split(xs, cuts)):
        h = dep[yy, xx].astype(np.float64)
        if mode == "상수" or len(h) < 3:
            out[yy, xx] = np.median(h)
        else:
            A = np.stack([xx, yy, np.ones_like(xx)], 1).astype(np.float64)
            coef = np.linalg.lstsq(A, h, rcond=None)[0]
            out[yy, xx] = A @ coef
    return np.clip(out, 0, 1).astype(np.float32)


def facet_ids(truth, view):
    """정답 메시 -> 그 시점에서 **보이는 평면 조각 번호** (0 = 빈 곳).

    `오라클.oracle_depth` 와 같은 프레임 · 같은 화가 순서라 두 장이 화소마다 맞는다.
    같은 평면에 붙은 삼각형 묶음(`trimesh` facets)은 한 번호, 어디에도 안 묶인 삼각형은 제 번호."""
    Vw = np.asarray(truth.vertices, np.float64)
    F = np.asarray(truth.faces, np.int64)
    facets = truth.facets
    fid = np.arange(len(F), dtype=np.float64) + len(facets) + 1      # 낱 삼각형은 뒤 번호
    for k, fs in enumerate(facets, 1):
        fid[fs] = k
    y = Vw[:, 1]
    sx = +1.0 if view == "front" else float(O.BACK)
    py, px = W.topix(sx * Vw[:, 0], Vw[:, 2])
    P = np.stack([px, py], 1).astype(np.int32)[F]
    order = np.argsort(y[F].max(1))[::-1] if view == "front" else np.argsort(y[F].min(1))
    img = np.zeros((W.RES, W.RES), np.float32)
    for i in order:                                                 # 먼 것부터 -> 가까운 것이 남는다
        cv2.fillConvexPoly(img, P[i], float(fid[i]))
    return img


def post_for(case, truth, labels, mode):
    """`O.build(post=)` 에 넣을 함수. 정답 깊이를 `labels` 판마다 `mode` 로 뭉갠다."""
    def post(v, d, dep):
        assert dep.shape == d.shape, "깊이맵과 원화 마스크 모양이 다르다 %s %s" % (dep.shape, d.shape)
        lab = facet_ids(truth, v) if labels == "정답면" else H.load_labels(v, d, case=case)
        return flatten(dep, lab, d, mode)
    return post


def one(case):
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    iou128, iou192 = O._iou_fn(truth), O._iou_fn(truth, P192)
    row, cache, plain = {"case": case, "판": TAG}, {}, None
    for name, (which, labels, mode) in SPEC.items():
        post = post_for(case, truth, labels, mode) if labels else None
        pl, vox, axes, _ = O.build(case, truth, H.LAM if which == "파이프" else LAM, which, post=post)
        if plain is None:
            plain = pl
            row["이진"], row["이진·192"] = iou128(pl, axes), iou192(pl, axes)
        mesh = O.C.to_mesh(vox, axes)
        em, _ = H.even_control(plain, axes, mesh.volume, cache=cache)
        row[name], row[name + "·192"] = iou128(mesh, axes), iou192(mesh, axes)
        row["균일@" + name], row["균일@%s·192" % name] = iou128(em, axes), iou192(em, axes)
        row["찢김_" + name], row["조각_" + name] = SF.tear(vox), SF.pieces(vox)
        row["실루엣_" + name] = SF.sil_loss(vox, plain)
        del vox, mesh, em
        gc.collect()
    row["배관차"] = abs(row["적합·정답면"] - row["오라클"])
    row["초"] = round(time.time() - t0, 1)
    return row


def selfcheck():
    # 1 상수 — 판 안은 중앙값, 판 밖은 그대로
    dep = np.ones((8, 8), np.float32)
    lab = np.zeros((8, 8), np.float32)
    m = np.zeros((8, 8), bool)
    lab[1:4, 1:4], lab[4:7, 4:7], m[1:7, 1:7] = 1, 2, True
    dep[1:4, 1:4] = [[.1, .2, .3]] * 3
    dep[4:7, 4:7] = .7
    f = flatten(dep, lab, m, "상수")
    assert np.allclose(f[1:4, 1:4], .2) and np.allclose(f[4:7, 4:7], .7) and f[0, 0] == 1, "상수 뭉개기가 틀렸다"
    # 2 적합 — 기울어진 판은 그대로 되찾는다
    yy, xx = np.mgrid[0:8, 0:8]
    ramp = (0.05 * xx + 0.02 * yy + 0.1).astype(np.float32)
    g = flatten(ramp, np.ones((8, 8), np.float32), np.ones((8, 8), bool), "적합")
    assert np.abs(g - ramp).max() < 1e-5, "평면 적합이 기울기를 못 되찾는다"
    # 3 정답 면 번호 — `오라클.selfcheck` 와 같은 물건. 몸통 앞면은 한 번호, 앞으로 튀어나온 혹은 다른 번호
    big = trimesh.creation.box((0.6, 0.4, 1.0))
    bump = trimesh.creation.box((0.2, 0.2, 0.3))
    bump.apply_translation([0, -0.30, 0])
    mm = trimesh.util.concatenate([big, bump])
    mm.vertices = W.normalize(np.asarray(mm.vertices, np.float64))
    ids = facet_ids(mm, "front")
    at = lambda u, z: float(ids[tuple(int(v[0]) for v in W.topix(np.array([u]), np.array([z])))])
    body, hump, body2 = at(0.25, 0.5), at(0.0, 0.5), at(-0.25, 0.8)
    assert body > 0 and hump > 0 and body != hump and body == body2, \
        "정답 면 번호가 틀렸다 (몸통 %g · 혹 %g · 몸통2 %g)" % (body, hump, body2)
    print("  자가검사 통과 — 상수 · 적합 · 정답 면 번호 (몸통 %g · 혹 %g)" % (body, hump))


def judge(rows):
    """계획 「판정」 절 그대로. 각진 장만 판정에 쓴다."""
    rs = [r for r in rows if r["case"] in ANGULAR]
    n = len(rs)
    g = lambda k: np.array([r[k] for r in rs])
    bad = [r["case"] for r in rs if r["배관차"] >= 0.02]
    if bad:
        return {"배관": "어긋남 — 숫자를 버린다", "어긋난 장": bad}
    ceil = g("오라클") - g("이진")
    live = ceil > 0.01
    out = {"배관": "통과", "천장 있는 장": int(live.sum())}
    for k, need in (("상수·정답면", 0.8), ("상수·원화판", 0.5), ("적합·원화판", 0.5)):
        frac = (g(k) - g("이진"))[live] / ceil[live]
        ctrl = [g(k) - g("균일@" + k), g(k + "·192") - g("균일@%s·192" % k)]
        ok_c = all(d.mean() > 0 and (d > 0).sum() > n / 2 for d in ctrl)
        med = float(np.median(frac)) if live.any() else float("nan")
        out[k] = {"천장몫중앙": med, "기준": need, "제대조군": bool(ok_c), "통과": bool(med >= need and ok_c)}
    q1 = out["상수·정답면"]["통과"]
    q2 = out["상수·원화판"]["통과"] or out["적합·원화판"]["통과"]
    out["다음"] = ("멈춤 — 판마다 평면이 모자라다" if not q1 else
                  "게이트 B — 옆판에서 평면 후보" if q2 else "게이트 A — 벤치 선부터")
    return out


def report(rows):
    names = ["이진"] + list(SPEC)
    print("\n  케이스별 IoU (격자128) · 배관차")
    print("  %-26s " % "케이스" + " ".join("%11s" % k for k in names) + "   배관차")
    for r in rows:
        mark = "" if r["case"] in ANGULAR else "  (참고)"
        print("  %-26s " % r["case"][:26] + " ".join("%11.4f" % r[k] for k in names) + "   %.4f%s" % (r["배관차"], mark))
    v = judge(rows)
    print("\n  판정 (각진 %d 장)" % len([r for r in rows if r["case"] in ANGULAR]))
    print("  " + json.dumps(v, ensure_ascii=False, indent=1).replace("\n", "\n  "))
    p = os.path.join(HERE, "out", "기록", "판별평면_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"때": time.strftime("%Y-%m-%d %H:%M"), "판": TAG, "케이스": CASES, "판정": v, "rows": rows},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  기록 -> %s" % os.path.relpath(p, HERE))


def figure(cases=("cloak_Chest_O72u4Drp8k", "cloak_Chest_Closed_AngpV0HxD8", "mech_Drill_8uBbH7Dvmb",
                  "스캔_Victor_Reversible_Bookend")):
    """정답 · 이진 · 오라클 · 뭉갠 셋을 45도 깊이색으로. 같은 줄은 틀 · 깊이 범위가 같다 (이진에 맞춤)."""
    import 깊이색 as DC
    import 앨리어싱 as AL
    cols = ["정답", "이진", "오라클", "상수·정답면", "상수·원화판", "적합·원화판"]
    rows = []
    for case in cases:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        M = {}
        for name in cols[1:]:
            which, labels, mode = SPEC.get(name, ("오라클", None, None))
            post = post_for(case, truth, labels, mode) if labels else None
            pl, vox, axes, _ = O.build(case, truth, LAM, which, post=post)
            M[name] = O.C.to_mesh(pl if name == "이진" else vox, axes)
        fr, dr = AL.frame_of(M["이진"], 45), DC.depth_range(M["이진"], 45)
        tiles = [DC.colorize(DC.zbuffer(truth, 45, fr, 360), dr)]
        tiles += [DC.colorize(DC.zbuffer(M[k], 45, fr, 360), dr) for k in cols[1:]]
        rows.append((case[:14], tiles))
        print("  %s 그림" % case, flush=True)
    DC.grid(rows, cols, "판별 평면 — 정답 깊이를 판마다 평면으로 뭉개면 (45도 · lam 1.00)",
            "상수·정답면 = 정답 메시 평면 조각마다 중앙값 · 상수/적합·원화판 = 원화 판 분할마다. 첫 칸이 정답이다",
            os.path.join(HERE, "out", "깊이색_판별평면.png"), S=300)


def main():
    H.register_sheets()
    selfcheck()
    arg = sys.argv[1] if len(sys.argv) > 1 else "1"
    if arg == "검사":
        return
    if arg == "그림":
        figure()
        return
    done = {}
    if os.path.exists(PROG):
        for l in open(PROG, encoding="utf-8"):
            r = json.loads(l)
            if r.get("판") == TAG:
                done[r["case"]] = r
    if arg != "판정":
        for c in [c for c in CASES if c not in done][:int(arg)]:
            r = one(c)
            with open(PROG, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            done[c] = r
            print("  %-26s 이진 %.4f · 오라클 %.4f · 상수·정답면 %.4f · 상수·원화판 %.4f · 배관차 %.4f · %.0f초" % (
                c[:26], r["이진"], r["오라클"], r["상수·정답면"], r["상수·원화판"], r["배관차"], r["초"]), flush=True)
    rows = [done[c] for c in CASES if c in done]
    if len(rows) == len(CASES) or arg == "판정":
        report(rows)
    else:
        print("  %d/%d 장 — 다시 돌리면 이어 돈다" % (len(rows), len(CASES)))


if __name__ == "__main__":
    main()
