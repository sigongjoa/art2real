# -*- coding: utf-8 -*-
"""**lam 은 깊이맵 신뢰도다** — 지금 기본값과 「타원을 끝까지 믿기」를 판정 규약으로 맞댄다.

    python 람.py <벤치> [n]        벤치 = 실물 · 마네킹 · 스캔 · 도형

2026-09-12 에 네 장에서 본 것: `타원 lam1.00` 이 지금 기본값(`파이프 lam0.20`)을 인물에서
+0.04~0.08 이기고 궤짝에서 -0.118 로 무너진다. **네 장은 결론이 아니라 후보다.** 여기서 벤치에 건다.

판정은 `대조.py` 규약 그대로 — **격자 둘**(128·192)에서 같은 방향이어야 하고, **제 부피 대조군**
둘(`even_control` 사방으로 밈 · `depth_control` 앞뒤로만 밈)을 이겨야 하고, **깨짐 셋**
(찢김·조각·실루엣 손실)을 같이 적는다. 대조군은 **후보 판본의 부피**에 맞춘다.

케이스마다 한 줄 적고 이어 돈다 (이 PC 는 긴 실행이 메모리로 죽는다)."""
import gc
import json
import os
import sys
import time

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
os.chdir(HERE)
import numpy as np
import trimesh
import 오라클 as O

H, W, J, C, SF = O.H, O.W, O.J, O.C, __import__("표면")
REC = os.path.join(HERE, "out", "기록")
P192 = (W.U1 - W.U0) / 192.0
TAG = "람 · 파이프0.20 대 타원1.00 · 제부피대조 둘 · 격자둘 · 깨짐셋 (2026-09-12)"
VERS = [("파이프0.20", "파이프", 0.20, 2.0),          # 지금 기본값 (hull.LAM)
        ("타원1.00", "타원", 1.00, 2.0)]              # 후보


def cases_of(bench):
    if bench == "실물":
        return [c["name"] for c in json.load(
            open(os.path.join(HERE, "벤치.json"), encoding="utf-8"))["cases"]]
    if bench == "도형":
        import 도형 as SH
        return ["도형_" + n for n, *_ in SH.FORMS]
    return sorted(n for n in os.listdir(os.path.join(HERE, "out", "시트"))
                  if n.startswith(bench + "_"))


def one(case):
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    T, ot = J.grid(truth)
    T2, ot2 = J.grid(truth, P192)

    def score(vox_or_mesh, axes):
        m = vox_or_mesh if isinstance(vox_or_mesh, trimesh.Trimesh) else C.to_mesh(vox_or_mesh, axes)
        G, og = J.grid(m)
        A, B = J.common(T, ot, G, og)
        G2, og2 = J.grid(m, P192)
        A2, B2 = J.common(T2, ot2, G2, og2)
        return {"iou": float((A & B).sum() / max((A | B).sum(), 1)),
                "iou192": float((A2 & B2).sum() / max((A2 | B2).sum(), 1)),
                "vol": float(B.sum() / max(A.sum(), 1))}

    row = {"case": case, "판": TAG}
    plain, axes, vx = None, None, {}
    for label, which, lam, ex in VERS:
        pl, dv, ax, _ = O.build(case, truth, lam, which, ex)
        if plain is None:
            plain, axes = pl, ax
            row["이진"] = score(plain, axes)
        vx[label] = dv
        row[label] = score(dv, axes)
        row[label].update({"찢김": float(SF.tear(dv)), "조각": int(SF.pieces(dv)),
                           "실루엣": float(SF.sil_loss(dv, plain))})
    # **제 부피 대조군 — 후보 부피에 맞춘다.** 정보를 안 쓰고 같은 부피만큼 깎으면 얼마인가
    cand = vx["타원1.00"]
    em, et = H.even_control(plain, axes, C.to_mesh(cand, axes).volume)
    yc, _ = H.depth_control(plain, int(cand.sum()))
    row["균일"] = score(em, axes)
    row["앞뒤균일"] = score(yc, axes)
    row["초"] = round(time.time() - t0, 1)
    del plain, vx, cand, em, yc
    gc.collect()
    return row


def report(rows, bench):
    def g(k, f="iou"):
        return np.array([r[k][f] for r in rows])
    n = len(rows)
    print("\n  [%s] %d 장 · %s" % (bench, n, TAG))
    print("  %-30s %8s %8s %8s %8s %8s" % ("케이스", "hull", "파이프.20", "타원1.0", "차", "차192"))
    for r in rows:
        a, b = r["파이프0.20"], r["타원1.00"]
        print("  %-30s %8.4f %8.4f %8.4f %+8.4f %+8.4f" % (
            r["case"][:30], r["이진"]["iou"], a["iou"], b["iou"],
            b["iou"] - a["iou"], b["iou192"] - a["iou192"]))
    d128, d192 = g("타원1.00") - g("파이프0.20"), g("타원1.00", "iou192") - g("파이프0.20", "iou192")
    same = (np.sign(d128) == np.sign(d192))
    print("\n  후보(타원1.00) - 지금(파이프0.20)")
    print("    격자128  중앙 %+.4f · 평균 %+.4f · 이긴 장 %d/%d" % (
        np.median(d128), d128.mean(), int((d128 > 0).sum()), n))
    print("    격자192  중앙 %+.4f · 평균 %+.4f · 이긴 장 %d/%d" % (
        np.median(d192), d192.mean(), int((d192 > 0).sum()), n))
    print("    두 격자가 같은 방향인 장 %d/%d — **결론은 이 장들로만**" % (int(same.sum()), n))
    both = d128[same]
    if len(both):
        print("    그 장들만: 중앙 %+.4f · 이긴 장 %d/%d" % (
            np.median(both), int((both > 0).sum()), len(both)))
    print("\n  후보가 대조군을 이기나 (제 부피 · 정보를 안 쓴 것)")
    for k in ("균일", "앞뒤균일"):
        e = g("타원1.00") - g(k)
        e2 = g("타원1.00", "iou192") - g(k, "iou192")
        v = "통과" if (e.mean() > 0 and (e > 0).sum() > n / 2
                     and e2.mean() > 0 and (e2 > 0).sum() > n / 2) else "짐"
        print("    %-6s %+.4f (%d/%d) · 192 %+.4f (%d/%d)  %s" % (
            k, e.mean(), int((e > 0).sum()), n, e2.mean(), int((e2 > 0).sum()), n, v))
    print("\n  깨짐 셋 (중앙 / 최악)")
    for k in ("파이프0.20", "타원1.00"):
        print("    %-10s 찢김 %.1f%%/%.1f%% · 조각 %d/%d · 실루엣 손실 %.2f%%/%.2f%%" % (
            k, 100 * np.median(g(k, "찢김")), 100 * g(k, "찢김").max(),
            int(np.median(g(k, "조각"))), int(g(k, "조각").max()),
            100 * np.median(g(k, "실루엣")), 100 * g(k, "실루엣").max()))
    print("\n  부피 (정답 대비 · 1.0 이 맞다)  hull %.2f · 파이프 %.2f · 타원1.00 %.2f" % (
        np.median(g("이진", "vol")), np.median(g("파이프0.20", "vol")), np.median(g("타원1.00", "vol"))))


def main():
    O.H.register_sheets()
    bench = sys.argv[1] if len(sys.argv) > 1 else "실물"
    out = os.path.join(REC, "람_%s.jsonl" % bench)
    cases = cases_of(bench)
    if len(sys.argv) > 2:
        cases = cases[:int(sys.argv[2])]
    done = {}
    if os.path.exists(out):
        for l in open(out, encoding="utf-8"):
            r = json.loads(l)
            if r.get("판") == TAG:
                done[r["case"]] = r
    rows = []
    for c in cases:
        r = done.get(c)
        if r is None:
            r = one(c)
            with open(out, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print("  %-30s %8.4f -> %8.4f (%+.4f) · %.0f초" % (
                c[:30], r["파이프0.20"]["iou"], r["타원1.00"]["iou"],
                r["타원1.00"]["iou"] - r["파이프0.20"]["iou"], r["초"]), flush=True)
        rows.append(r)
    report(rows, bench)


if __name__ == "__main__":
    main()
