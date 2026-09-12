# -*- coding: utf-8 -*-
"""**넘치는 몫을 셋으로 가른다** — 깎기가 걷은 것 · 더 걷을 수 있는 것 · 못 걷는 것.

    python 천장.py <벤치> [n]

깎기(`carve_depth`)는 기둥마다 앞을 `depth_front` 까지, 뒤를 `depth_back` 까지 자른다.
그래서 결과는 **기둥당 한 덩어리**다. 치마 속처럼 한 기둥에 겹이 둘이어야 하는 것은
**어떤 lam · 어떤 깊이맵으로도** 못 만든다.

그 경계가 곧 **정답 깊이 + lam 1.00** 이다 (기둥마다 정답의 앞뒤 끝까지 정확히 자른 것).
그러니 hull 의 넘치는 몫은 이렇게 갈린다:

    hull  ---(지금 깎기)--->  지금  ---(깊이맵을 고치면)--->  오라클1.00  ---(못 넘음)--->  정답
          걷은 것                    아직 남은 · 닿을 수 있는 것        기둥당 한 덩어리라 못 걷는 것

케이스마다 적고 이어 돈다."""
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

J, C, W = O.J, O.C, O.W
REC = os.path.join(HERE, "out", "기록")
P192 = (W.U1 - W.U0) / 192.0
TAG = "천장 · hull · 파이프0.20 · 타원1.00 · 오라클1.00 (2026-09-12)"
VERS = [("파이프0.20", "파이프", 0.20), ("타원1.00", "타원", 1.00), ("오라클1.00", "오라클", 1.00)]


def cases_of(bench):
    if bench == "실물":
        return [c["name"] for c in json.load(
            open(os.path.join(HERE, "벤치.json"), encoding="utf-8"))["cases"]]
    return sorted(n for n in os.listdir(os.path.join(HERE, "out", "시트"))
                  if n.startswith(bench + "_"))


def one(case):
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    T, ot = J.grid(truth)

    def sc(v, axes):
        G, og = J.grid(C.to_mesh(v, axes))
        A, B = J.common(T, ot, G, og)
        return {"iou": float((A & B).sum() / max((A | B).sum(), 1)),
                "vol": float(B.sum() / max(A.sum(), 1)),
                "miss": float((A & ~B).sum() / max(A.sum(), 1))}

    row = {"case": case, "판": TAG}
    plain, axes = None, None
    for label, which, lam in VERS:
        pl, dv, ax, _ = O.build(case, truth, lam, which)
        if plain is None:
            plain, axes = pl, ax
            row["이진"] = sc(plain, axes)
        row[label] = sc(dv, axes)
        del dv
        gc.collect()
    row["초"] = round(time.time() - t0, 1)
    del plain
    gc.collect()
    return row


def report(rows, bench):
    v = lambda k: np.array([r[k]["vol"] for r in rows])
    i = lambda k: np.array([r[k]["iou"] for r in rows])
    n = len(rows)
    hull, now, cand, ceil = v("이진"), v("파이프0.20"), v("타원1.00"), v("오라클1.00")
    over = hull - 1.0                                  # hull 이 정답보다 넘치는 몫
    print("\n  [%s] %d 장 · 넘치는 몫을 어디까지 걷나 (부피비 · 1.0 이 정답)" % (bench, n))
    print("    hull        %.2f   (넘치는 몫 %.2f)" % (np.median(hull), np.median(over)))
    print("    지금        %.2f   걷은 몫 %.0f%%" % (np.median(now), 100 * np.median((hull - now) / over)))
    print("    후보        %.2f   걷은 몫 %.0f%%" % (np.median(cand), 100 * np.median((hull - cand) / over)))
    print("    오라클1.00   %.2f   걷은 몫 %.0f%%   ← **이 표현의 끝** (기둥당 한 덩어리)"
          % (np.median(ceil), 100 * np.median((hull - ceil) / over)))
    print("    정답        1.00")
    print("\n  넘치는 몫 %.2f 를 셋으로" % np.median(over))
    a = np.median((hull - now) / over)
    b = np.median((now - ceil) / over)
    c = np.median((ceil - 1.0) / over)
    print("    지금 이미 걷은 것                       %.0f%%" % (100 * a))
    print("    깊이맵을 고치면 더 걷을 수 있는 것          %.0f%%   ← 여기가 남은 일" % (100 * b))
    print("    기둥당 한 덩어리라 **못 걷는 것**          %.0f%%   ← 표현을 바꿔야 닿는다" % (100 * c))
    print("\n  IoU 중앙   hull %.4f · 지금 %.4f · 후보 %.4f · **천장 %.4f**" % (
        np.median(i("이진")), np.median(i("파이프0.20")), np.median(i("타원1.00")),
        np.median(i("오라클1.00"))))
    print("\n  못 걷는 몫이 큰 차례 (속이 빈 물건)")
    k = np.argsort(-(ceil - 1.0))
    for x in k[:6]:
        r = rows[x]
        print("    %-30s 천장 부피 %.2f · 천장 IoU %.4f (지금 %.4f)" % (
            r["case"][:30], r["오라클1.00"]["vol"], r["오라클1.00"]["iou"], r["파이프0.20"]["iou"]))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "그림":
        figure(sys.argv[2] if len(sys.argv) > 2 else "실물")
        return
    O.H.register_sheets()
    bench = sys.argv[1] if len(sys.argv) > 1 else "실물"
    out = os.path.join(REC, "천장_%s.jsonl" % bench)
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
            print("  %-30s hull %.2f -> 지금 %.2f -> 후보 %.2f -> 천장 %.2f · %.0f초" % (
                c[:30], r["이진"]["vol"], r["파이프0.20"]["vol"], r["타원1.00"]["vol"],
                r["오라클1.00"]["vol"], r["초"]), flush=True)
        rows.append(r)
    report(rows, bench)



def figure(bench="실물"):
    """넘치는 몫을 셋으로 가른 그림 — 걷은 것 · 닿을 수 있는 것 · 못 걷는 것."""
    from PIL import Image, ImageDraw
    sys.path.insert(0, HERE)
    from 계획 import _font
    rows = [json.loads(l) for l in open(os.path.join(REC, "천장_%s.jsonl" % bench), encoding="utf-8")
            if json.loads(l).get("판") == TAG]
    v = lambda k: np.array([r[k]["vol"] for r in rows])
    i = lambda k: np.array([r[k]["iou"] for r in rows])
    hull, now, cand, ceil = v("이진"), v("파이프0.20"), v("타원1.00"), v("오라클1.00")
    over = hull - 1.0
    a, b, c = (np.median((hull - cand) / over), np.median((cand - ceil) / over),
               np.median((ceil - 1.0) / over))
    tot = a + b + c
    a, b, c = a / tot, b / tot, c / tot
    W_, H_ = 1180, 530
    im = Image.new("RGB", (W_, H_), "white")
    d = ImageDraw.Draw(im)
    f1, f2, f3 = _font(28), _font(17), _font(14)
    d.text((30, 22), "hull 이 넘치는 몫을 셋으로 — %s 벤치 %d 장" % (bench, len(rows)),
           fill=(20, 20, 20), font=f1)
    d.text((30, 62), "hull 은 정답 부피의 %.2f 배다. 그 넘치는 몫(%.2f)을 누가 걷나."
           % (np.median(hull), np.median(over)), fill=(90, 90, 90), font=f3)
    X0, X1, Y = 30, W_ - 30, 120
    Wd = X1 - X0
    segs = [("후보가 이미 걷었다 (타원 lam1.00)", a, (120, 175, 120)),
            ("깊이맵을 고치면 걷는다", b, (232, 176, 60)),
            ("기둥당 한 덩어리라 못 걷는다", c, (200, 80, 66))]
    x = X0
    for name, f, col in segs:
        w = int(Wd * f)
        d.rectangle([x, Y, x + w, Y + 74], fill=col)
        d.text((x + 10, Y + 16), "%.0f%%" % (100 * f), fill=(255, 255, 255), font=f1)
        d.text((x + 10, Y + 90), name, fill=(40, 40, 40), font=f2)
        x += w
    d.text((30, Y + 130), "가운데(노랑)가 남은 일이다 — 표현은 그대로 두고 깊이맵만 고치면 닿는다.",
           fill=(40, 40, 40), font=f2)
    d.text((30, Y + 156), "오른쪽(빨강)은 치마 속·망토 속이다. 깎기는 기둥마다 앞뒤를 자르므로 "
                          "결과가 늘 기둥당 한 덩어리라, 어떤 lam·어떤 깊이맵으로도 못 만든다.",
           fill=(90, 90, 90), font=f3)
    Y2 = Y + 210
    d.text((30, Y2), "3D IoU 중앙 (같은 29 장)", fill=(20, 20, 20), font=f2)
    lad = [("hull (안 깎음)", np.median(i("이진")), (170, 170, 170)),
           ("지금 · 파이프 lam0.20", np.median(i("파이프0.20")), (150, 185, 235)),
           ("후보 · 타원 lam1.00", np.median(i("타원1.00")), (120, 175, 120)),
           ("천장 · 정답 깊이 lam1.00", np.median(i("오라클1.00")), (232, 176, 60))]
    for k, (nm, val, col) in enumerate(lad):
        y = Y2 + 34 + k * 30
        d.rectangle([330, y, 330 + int(760 * val), y + 22], fill=col)
        d.text((30, y + 3), nm, fill=(40, 40, 40), font=f3)
        d.text((330 + int(760 * val) + 8, y + 3), "%.4f" % val, fill=(40, 40, 40), font=f3)
    im.save(os.path.join(HERE, "out", "천장_%s.png" % bench))
    print("  -> out/천장_%s.png" % bench)

if __name__ == "__main__":
    main()
