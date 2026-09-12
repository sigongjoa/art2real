# -*- coding: utf-8 -*-
"""도형 11개 · **단면 지수를 쓴다** — 타원(p=2)이 고정인 게 손해인가.

    python 초타원.py <out.jsonl> [n]

`ellipse_depths` 는 높이마다 부품(연결성분)에 **타원**을 내접시킨다 — 지수 2 가 박혀 있다.
초타원 |x/a|^p + |y/b|^p <= 1 은 그 지수를 푼다 (p=2 타원 · 크면 상자 · 1 이면 마름모).

**이건 상한 측정이지 추정기가 아니다.** p 를 정답 깊이에 맞춰 고르므로 의뢰에는 못 쓴다.
묻는 것 하나 — **도형마다 원하는 p 가 다른가.** 전부 2 를 원하면 부품별 지수는 죽은 길이고,
상자가 6 을 원하고 구가 2 를 원하면 **부품마다 달라야 할 이유가 생긴다** (그 다음이 선화에서 읽기).

싼 자로 잰다 — IoU 가 아니라 **깊이맵이 오라클과 얼마나 닮았나** (`오라클.map_corr` 과
같은 읽기 규약, 복셀 중심 · 높이마다 max=1). 케이스마다 한 줄 적고 이어 돈다.

얼린 값으로 막는다 — p=2 의 상관은 `out/기록/오라클_20260912_1144.json` 의 `상관_타원` 과
같아야 한다. 리팩터가 옛 타원을 바꿨으면 여기서 걸린다."""
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

PS = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 10.0)
FROZEN = os.path.join(HERE, "out", "기록", "오라클_20260912_1144.json")
LAM = 0.20                                 # 깊이맵만 보므로 lam 은 안 쓴다 (build 가 요구해서 준다)


def read_at_voxels(img, plain, axes, back_sign, v="front"):
    """`carve_depth` 가 읽는 자리에서 깊이를 읽고 높이마다 max=1 로 — `map_corr` 과 같은 규약."""
    u, _, z = axes
    X2, Z2 = np.meshgrid(u, z, indexing="ij")
    py, px = O.W.topix((back_sign if v == "back" else O.W.VIEW_AXIS[v][1]) * X2, Z2)
    on = plain.any(1)
    h = img[v][py, px]
    return (h / np.maximum(np.where(on, h, 0.0).max(0, keepdims=True), 1e-6))[on]


def one(case):
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    bs = O.H.CASES[case]["back_sign"]
    t0 = time.time()
    plain, _, axes, dpo = O.build(case, truth, LAM, "오라클")      # 오라클 깊이맵 · hull · 축
    ref = {v: read_at_voxels(dpo, plain, axes, bs, v) for v in ("front", "back")}
    row = {"case": case, "부품": int(max(
        len(np.unique(O.ndimage.label(plain[:, :, k])[0])) - 1 for k in range(plain.shape[2]))), "p": {}}
    for p in PS:
        cand = O.ellipse_depths(plain, axes, bs, p)
        c = O.map_corr({"오라클": dpo, "타원": cand, "파이프": cand}, plain, axes, bs)["상관_타원"]
        diff = [np.abs(read_at_voxels(cand, plain, axes, bs, v) - ref[v]).mean() for v in ("front", "back")]
        row["p"]["%.1f" % p] = {"상관": c, "오차": float(np.mean(diff))}
    row["초"] = round(time.time() - t0, 1)
    del plain, dpo
    gc.collect()
    return row


def main():
    import 도형 as SH
    if len(sys.argv) > 1 and sys.argv[1] == "그림":          # python 초타원.py 그림 [도형 이름들]
        names = sys.argv[2:] or ["상자", "원기둥", "L자", "토러스옆"]
        figure(["도형_" + n for n in names])
        return
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "기록", "초타원_도형.jsonl")
    cases = ["도형_" + n for n, *_ in SH.FORMS]
    if len(sys.argv) > 2:
        cases = cases[:int(sys.argv[2])]
    done = {}
    if os.path.exists(out):
        for l in open(out, encoding="utf-8"):
            r = json.loads(l)
            done[r["case"]] = r
    frozen = {r["case"]: r.get("상관_타원") for r in json.load(open(FROZEN, encoding="utf-8"))["rows"]}
    rows = []
    for case in cases:
        r = done.get(case)
        if r is None:
            r = one(case)
            with open(out, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        # **얼린 값의 문** — p=2 는 어제 잰 타원과 같은 깊이맵이어야 한다
        a, b = r["p"]["2.0"]["상관"], frozen.get(case)
        assert b is None or (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-9, \
            "%s: p=2 가 얼린 타원과 다르다 (%.6f 대 %.6f)" % (case, a, b)
        rows.append(r)
        print("  %-14s %s | 최선 p %s" % (
            case.replace("도형_", ""),
            " ".join("%.3f" % r["p"]["%.1f" % p]["오차"] for p in PS),
            min(PS, key=lambda p: r["p"]["%.1f" % p]["오차"])), flush=True)
    report(rows)


def report(rows):
    print("\n  깊이맵 오차 (오라클과 · 낮을수록 좋다) · 부품 수는 한 높이 최대")
    print("  %-14s %4s | %s | %s" % ("도형", "부품", " ".join("p%-5.1f" % p for p in PS), "최선 p  p=2 대비"))
    best = []
    for r in rows:
        e = [r["p"]["%.1f" % p]["오차"] for p in PS]
        bp = PS[int(np.argmin(e))]
        best.append(bp)
        print("  %-14s %4d | %s | %5.1f  %+.4f" % (
            r["case"].replace("도형_", ""), r["부품"], " ".join("%.4f" % x for x in e),
            bp, min(e) - r["p"]["2.0"]["오차"]))
    n = len(rows)
    print("\n  11 장 · p=2 고정 대비 **부품마다 제 p** 를 주면 오차가 얼마나 빠지나")
    e2 = np.array([r["p"]["2.0"]["오차"] for r in rows])
    eb = np.array([min(r["p"]["%.1f" % p]["오차"] for p in PS) for r in rows])
    print("    p=2 고정       오차 중앙 %.4f" % np.median(e2))
    print("    케이스마다 최선 오차 중앙 %.4f  (%+.4f · 좋아진 장 %d/%d)" % (
        np.median(eb), np.median(eb - e2), int((eb < e2 - 1e-6).sum()), n))
    for p in PS:                                   # 고정 p 하나로 전부 덮을 수 있나
        e = np.array([r["p"]["%.1f" % p]["오차"] for r in rows])
        print("    p=%-5.1f 고정  오차 중앙 %.4f  (p=2 대비 %+.4f · 이긴 장 %d/%d)" % (
            p, np.median(e), np.median(e - e2), int((e < e2 - 1e-6).sum()), n))
    print("\n  최선 p 의 분포 %s" % dict(zip(*[list(x) for x in np.unique(best, return_counts=True)])))
    print("  **갈리면** 부품별 지수에 머리 위가 있다. 전부 같으면 고정 p 하나로 끝난다")



def figure(cases):
    """**비포/애프터를 모양으로.** 높이 50% 단면 · 검정 선 = 정답 단면 · 아래가 앞(-y).

    왼쪽이 hull(이진), 가운데가 지금 쓰는 타원(p=2), 오른쪽이 그 도형이 원하는 p 의 초타원.
    깊이맵이 아니라 **단면 모양 가정 자체**를 그린다 — 깎기가 읽는 것이 이 모양의 앞·뒤다."""
    from PIL import Image, ImageDraw
    sys.path.insert(0, HERE)
    from 계획 import _font
    rows = {json.loads(l)["case"]: json.loads(l) for l in
            open(os.path.join(HERE, "out", "기록", "초타원_도형.jsonl"), encoding="utf-8")}
    S, G, LW, TOP, RH = 200, 16, 150, 154, 248
    cols = [("hull (이진)", (205, 205, 205)), ("지금 · 타원 p=2", (196, 168, 232)),
            ("이 도형이 원하는 p", (140, 210, 160))]
    im = Image.new("RGB", (LW + 3 * (S + G) + G, TOP + len(cases) * RH + 54), "white")
    d = ImageDraw.Draw(im)
    f1, f2, f3 = _font(26), _font(15), _font(13)
    d.text((24, 18), "단면 지수 — 지금의 타원(p=2) vs 그 도형이 원하는 초타원", fill=(20, 20, 20), font=f1)
    d.text((24, 56), "높이 50% 단면 · 검정 선 = 정답 · 칠 = 가정한 단면 · 아래가 앞(-y) · "
                     "칸 아래 = 깊이맵 오차 (오라클과 · 낮을수록 좋다)", fill=(90, 90, 90), font=f3)
    d.text((24, 76), "초타원 |x/a|^p + |y/b|^p <= 1 을 **부품마다** hull 단면에 내접시킨다. p 는 정답 깊이에 "
                     "맞춰 골랐다 — **상한이지 추정기가 아니다**", fill=(90, 90, 90), font=f3)
    d.text((24, 96), "묻는 것: 도형마다 원하는 p 가 갈리나 (갈리면 부품별 지수에 머리 위가 있다)",
           fill=(90, 90, 90), font=f3)
    for j, (name, _) in enumerate(cols):
        d.text((LW + G + j * (S + G), TOP - 24), name, fill=(40, 40, 40), font=f2)
    for r, case in enumerate(cases):
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        plain, _, axes, _ = O.build(case, truth, LAM, "타원")
        u, _, z = axes
        du = u[1] - u[0]
        e = {p: rows[case]["p"]["%.1f" % p]["오차"] for p in PS}
        bp = min(PS, key=lambda p: e[p])
        masks = [plain, O.superellipse(plain, 2.0), O.superellipse(plain, bp)]
        z0, z1 = truth.bounds[:, 2]
        k = int(np.argmin(np.abs(z - (z0 + 0.5 * (z1 - z0)))))
        sec = truth.section(plane_origin=[0, 0, z[k]], plane_normal=[0, 0, 1])
        ii, jj = np.nonzero(plain[:, :, k])
        xs, ys = [u[ii.min()], u[ii.max()]], [u[jj.min()], u[jj.max()]]
        cx, cy = sum(xs) / 2, sum(ys) / 2
        span = max(xs[1] - xs[0], ys[1] - ys[0]) * 1.15 + 4 * du
        q = (np.arange(S) + 0.5) / S - 0.5
        ix = np.round((cx + q * span - u[0]) / du).astype(int)
        iy = np.round((cy - q * span - u[0]) / du).astype(int)    # 행이 내려갈수록 앞
        ok = ((ix >= 0) & (ix < len(u)))[None, :] & ((iy >= 0) & (iy < len(u)))[:, None]
        ix, iy = np.clip(ix, 0, len(u) - 1), np.clip(iy, 0, len(u) - 1)
        y0 = TOP + r * RH
        d.text((24, y0 + 76), case.replace("도형_", ""), fill=(20, 20, 20), font=f2)
        d.text((24, y0 + 100), "부품 %d" % rows[case]["부품"], fill=(120, 120, 120), font=f3)
        for j, (name, col) in enumerate(cols):
            tile = np.full((S, S, 3), 250, np.uint8)
            tile[masks[j][:, :, k][ix[None, :], iy[:, None]] & ok] = col
            x0 = LW + G + j * (S + G)
            im.paste(Image.fromarray(tile), (x0, y0))
            d.rectangle([x0, y0, x0 + S - 1, y0 + S - 1], outline=(215, 215, 215))
            for L in (sec.discrete if sec is not None else []):
                d.line([(x0 + ((x - cx) / span + 0.5) * S, y0 + (0.5 - (y - cy) / span) * S)
                        for x, y, _ in L], fill=(15, 15, 15), width=2)
            if j:
                p = 2.0 if j == 1 else bp
                dv = e[p] - e[2.0]
                d.text((x0, y0 + S + 4), "p=%.1f  오차 %.4f%s" % (
                    p, e[p], "" if j == 1 else "  (%+.4f)" % dv), font=f3,
                    fill=(40, 40, 40) if j == 1 else (30, 130, 70) if dv < 0 else (150, 150, 150))
        print("  %-14s 단면 z=%.3f · 원하는 p %.1f" % (case, z[k], bp), flush=True)
        del plain, masks
        gc.collect()
    path = os.path.join(HERE, "out", "초타원단면.png")
    im.save(path)
    print("  -> out/초타원단면.png")

if __name__ == "__main__":
    main()
