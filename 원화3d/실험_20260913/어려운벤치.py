# -*- coding: utf-8 -*-
"""**오메가몬에서 본 판본을 정답 있는 어려운 벤치에 건다** — 매끈해 보이는 것 말고 맞는 것.

    python 어려운벤치.py          -> out/기록/어려운벤치_진행.jsonl (케이스마다 적고 이어 돈다) + 판정
    python 어려운벤치.py 그림     -> out/깊이색_어려운벤치.png (정답도 같이 깊이색으로)

`찢김.py` 가 오메가몬에서 「타원 쪽이 가로 띠를 푼다」를 보였는데 오메가몬은 정답이 없다. 메카는 각지고, 타원은 09-12 에
**각진 것에 진** 후보다. 그래서 같은 판본을 정답 메시가 있는 케이스에 건다.

## 케이스 — README 09-12 에 이미 적힌 두 목록의 합집합 (11장)

    어려운 6장        지금 규칙 IoU 가 낮은 차례: statue_Town_Center · cape_Hat · avatarsample_d_darkness ·
                     wizard_Evil_Wizard · avatarsample_g · wizard_Wizard_o87
    타원이 진 7장      cloak_Chest_Closed · 스캔_Victor_Bookend · cloak_Chest_O72u4 · mech_Drill · cape_Hat ·
                     monster_Mimic · statue_Town_Center

## 판본 (`찢김.py` 와 같다)

    기준 (파이프 lam0.20) · Z2 (+ZSMOOTH σ2) · 타원1.00 · 타원1.00+Z2 · 전부 (타원1.00+Z2+ITK국소)

## 판정 — 돌리기 전에 적는다 (2026-09-13 밤)

벤치 규약 그대로 (`오라클.report`): 3D IoU 격자 128 · 192 둘.

    기준보다 낫다   ΔIoU(판본 − 기준) 평균 > 0 이고 과반 케이스에서 이긴다 — **격자 둘 다**
    제 대조군      판본 부피에 맞춘 균일 침식(`hull.even_control`)을 평균 > 0 · 과반으로 이긴다 — 격자 둘 다
    「좋아졌다」 = 둘 다. 찢김(`표면.tear`) · 실루엣 손실(`표면.sil_loss`) · 덩어리 수는 같이 적는다

11장은 적다 — 여기서 나오는 건 「어려운 쪽에서 방향이 맞나」이지 벤치 전체 판정이 아니다.
"""
import gc
import json
import os
import sys
import time

import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
SCR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, SCR)
os.chdir(HERE)
import hull as H
import win as W
import 오라클 as O
import 표면 as SF
import 앨리어싱 as AL

HARD6 = ["statue_Town_Center_cuQuFJEIfH", "cape_Hat_Stylised_lNN3PlrjSa", "avatarsample_d_darkness",
         "wizard_Evil_Wizard_bdxawstqtq", "avatarsample_g", "wizard_Wizard_o87Upt5uHX"]
LOST7 = ["cloak_Chest_Closed_AngpV0HxD8", "스캔_Victor_Reversible_Bookend", "cloak_Chest_O72u4Drp8k",
         "mech_Drill_8uBbH7Dvmb", "cape_Hat_Stylised_lNN3PlrjSa", "monster_Mimic_B8HrWzkuNp",
         "statue_Town_Center_cuQuFJEIfH"]
CASES = list(dict.fromkeys(HARD6 + LOST7))
SPEC = {"기준": ("파이프", 0.20, 0.0), "Z2": ("파이프", 0.20, 2.0), "타원1.00": ("타원", 1.00, 0.0),
        "타원1.00+Z2": ("타원", 1.00, 2.0), "전부": ("타원", 1.00, 2.0)}
VARIANTS = tuple(SPEC)
P192 = (W.U1 - W.U0) / 192.0
TAG = "어려운벤치 · 5판본 · 격자2 · 제부피대조 (2026-09-13 밤)"
PROG = os.path.join(HERE, "out", "기록", "어려운벤치_진행.jsonl")


def versions(case, truth):
    """판본마다 (메시, 점유 칸) · 이진 hull · 축."""
    out, plain, axes = {}, None, None
    for name, (which, lam, z) in SPEC.items():
        H.ZSMOOTH = z
        try:
            pl, vox, ax, _ = O.build(case, truth, lam, which)
        finally:
            H.ZSMOOTH = 0.0
        plain, axes = pl, ax
        if name == "전부":
            mesh, occ = AL.variant("ITK국소", vox, axes)
        else:
            mesh, occ = O.C.to_mesh(vox, axes), vox
        out[name] = (mesh, occ)
    return out, plain, axes


def one(case):
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    iou128, iou192 = O._iou_fn(truth), O._iou_fn(truth, P192)
    V, plain, axes = versions(case, truth)
    row = {"case": case, "판": TAG, "이진": iou128(plain, axes), "이진·192": iou192(plain, axes)}
    cache = {}
    for name, (mesh, occ) in V.items():
        em, _ = H.even_control(plain, axes, mesh.volume, cache=cache)
        row[name] = iou128(mesh, axes)
        row[name + "·192"] = iou192(mesh, axes)
        row["균일@" + name] = iou128(em, axes)
        row["균일@%s·192" % name] = iou192(em, axes)
        row["찢김_" + name] = SF.tear(occ)
        row["실루엣_" + name] = SF.sil_loss(occ, plain)
        row["조각_" + name] = SF.pieces(occ)
    row["초"] = round(time.time() - t0, 1)
    del V, truth
    gc.collect()
    return row


def report(rows):
    n = len(rows)
    g = lambda k: np.array([r[k] for r in rows])
    print("\n  %d 장 · 3D IoU (격자128 · 192)" % n)
    print("  %-11s %-15s %-26s %-26s %s" % ("판본", "IoU 평균", "기준 대비 (128 · 192)", "제 대조군 대비 (128 · 192)", "찢김 · 실루엣손실 · 조각 최악"))
    verdict = {}
    for k in VARIANTS:
        base = [g("기준"), g("기준·192")]
        mine = [g(k), g(k + "·192")]
        ctrl = [g("균일@" + k), g("균일@%s·192" % k)]
        dvb = [m - b for m, b in zip(mine, base)]
        dvc = [m - c for m, c in zip(mine, ctrl)]
        ok_b = all(d.mean() > 0 and (d > 0).sum() > n / 2 for d in dvb)
        ok_c = all(d.mean() > 0 and (d > 0).sum() > n / 2 for d in dvc)
        if k != "기준":
            verdict[k] = {"기준보다": ok_b, "제대조군": ok_c, "좋아졌다": ok_b and ok_c}
        print("  %-11s %.4f · %.4f   %s   %+.4f (%2d/%d) · %+.4f (%2d/%d)   %.1f%% · %.2f%% · %d" % (
            k, mine[0].mean(), mine[1].mean(),
            ("%+.4f (%2d/%d) · %+.4f (%2d/%d)" % (dvb[0].mean(), (dvb[0] > 0).sum(), n, dvb[1].mean(), (dvb[1] > 0).sum(), n))
            if k != "기준" else "%-24s" % "—",
            dvc[0].mean(), (dvc[0] > 0).sum(), n, dvc[1].mean(), (dvc[1] > 0).sum(), n,
            100 * np.median(g("찢김_" + k)), 100 * np.median(g("실루엣_" + k)), g("조각_" + k).max()))
    print("\n  케이스별 IoU (격자128)")
    print("  %-30s " % "케이스" + " ".join("%11s" % k for k in VARIANTS))
    for r in rows:
        print("  %-30s " % r["case"][:30] + " ".join("%11.4f" % r[k] for k in VARIANTS))
    print("\n  판정 (기준보다 · 제 대조군 · 둘 다 = 좋아졌다)")
    for k, v in verdict.items():
        print("    %-11s 기준보다 %s · 제 대조군 %s · **%s**" % (k, "O" if v["기준보다"] else "X", "O" if v["제대조군"] else "X",
                                                        "좋아졌다" if v["좋아졌다"] else "아니다"))
    p = os.path.join(HERE, "out", "기록", "어려운벤치_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"때": time.strftime("%Y-%m-%d %H:%M"), "판": TAG, "케이스": CASES, "판정": verdict, "rows": rows},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  기록 -> %s" % os.path.relpath(p, HERE))


def figure(cases=("cloak_Chest_Closed_AngpV0HxD8", "mech_Drill_8uBbH7Dvmb", "wizard_Evil_Wizard_bdxawstqtq", "avatarsample_g")):
    """규칙: 각진 물건 둘(궤짝 · 드릴) · 인물 둘(마법사 · avatarsample_g). 정답을 첫 칸에 — 매끈한 것이 맞는 것인지 본다."""
    import 깊이색 as DC
    O.H.register_sheets()
    rows = []
    cols = ["정답"] + list(VARIANTS)
    for case in cases:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        V, _, _ = versions(case, truth)
        fr, dr = AL.frame_of(V["기준"][0], 45), DC.depth_range(V["기준"][0], 45)
        tiles = [DC.colorize(DC.zbuffer(truth, 45, fr, 360), dr)]
        tiles += [DC.colorize(DC.zbuffer(V[k][0], 45, fr, 360), dr) for k in VARIANTS]
        rows.append((case[:14], tiles))
        print("  %s 그림" % case, flush=True)
    DC.grid(rows, cols, "어려운 벤치 — 정답 vs 판본 · 깊이색 + 등깊이선 (45도 · z 버퍼)",
            "첫 칸이 정답이다. 등깊이선이 정답과 닮을수록 맞다 — 매끈한 것과 맞는 것은 다르다. 같은 줄은 틀 · 깊이 범위가 같다 (기준에 맞춤)",
            os.path.join(HERE, "out", "깊이색_어려운벤치.png"), S=300)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "그림":
        figure()
        return
    O.H.register_sheets()
    done = {}
    if os.path.exists(PROG):
        for l in open(PROG, encoding="utf-8"):
            r = json.loads(l)
            if r.get("판") == TAG:
                done[r["case"]] = r
    for c in CASES:
        if c in done:
            continue
        r = one(c)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        done[c] = r
        print("  %-30s " % c[:30] + " · ".join("%s %.4f" % (k, r[k]) for k in VARIANTS) + " · %.0f초" % r["초"], flush=True)
    rows = [done[c] for c in CASES if c in done]
    if len(rows) == len(CASES):
        report(rows)
    else:
        print("  %d/%d 장 — 다시 돌리면 이어 돈다" % (len(rows), len(CASES)))


if __name__ == "__main__":
    main()
