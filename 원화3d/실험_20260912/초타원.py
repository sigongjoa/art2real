# -*- coding: utf-8 -*-
"""도형 11개 · **단면 지수를 쓴다** — 타원(p=2)이 고정인 게 손해인가.

    python 초타원.py <벤치> [n]        벤치 = 도형 · 마네킹 · 스캔 · 실물
    python 초타원.py 그림 <벤치> [케이스 ...]   단면
    python 초타원.py 3d <벤치> [케이스 ...]     깎은 것을 3D 로 + IoU
    python 초타원.py 각도 <벤치> <케이스>       한 케이스를 각도 다섯으로

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
LAM = 0.20                                 # 깊이맵만 보므로 lam 은 안 쓴다 (build 가 요구해서 준다)
REC = os.path.join(HERE, "out", "기록")
BENCHES = ("도형", "마네킹", "스캔", "실물")            # 쉬움 · 중간 둘 · 어려움


def cases_of(bench):
    if bench == "도형":
        import 도형 as SH
        return ["도형_" + n for n, *_ in SH.FORMS]
    if bench == "실물":
        return [c["name"] for c in json.load(
            open(os.path.join(HERE, "벤치.json"), encoding="utf-8"))["cases"]]
    return sorted(n for n in os.listdir(os.path.join(HERE, "out", "시트"))
                  if n.startswith(bench + "_"))


def frozen_corr():
    """p=2 는 어제 잰 타원과 같아야 한다 — 같은 규약(`O.RUN_TAG`)으로 잰 기록만 쓴다.

    도형 11개는 `오라클_20260912_1144.json`, 실물 일부는 `오라클_벤치_진행.jsonl`.
    마네킹·스캔은 얼린 값이 없다 — 그 케이스는 문이 없다 (없는 걸 있다고 적지 않는다)."""
    out = {}
    f = os.path.join(REC, "오라클_20260912_1144.json")
    if os.path.exists(f):
        for r in json.load(open(f, encoding="utf-8"))["rows"]:
            out[r["case"]] = r.get("상관_타원")
    f = os.path.join(REC, "오라클_벤치_진행.jsonl")
    if os.path.exists(f):
        for l in open(f, encoding="utf-8"):
            r = json.loads(l)
            if r.get("판") == O.RUN_TAG:
                out[r["case"]] = r.get("상관_타원")
    return out


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
    sat = {v: ref[v] > 0.999 for v in ref}          # 정답이 그 기둥의 맨 앞까지 차 있는 화소
    for p in PS:
        cand = O.ellipse_depths(plain, axes, bs, p)
        c = O.map_corr({"오라클": dpo, "타원": cand, "파이프": cand}, plain, axes, bs)["상관_타원"]
        # **갈라서 적는다.** 두기둥대각에서 평균 하나가 반대로 가는 두 흐름을 덮었다 (2026-09-12).
        # 유령 덩어리는 「정답이 뒤」 쪽에만 있어서, 섞으면 지수가 하는 일이 안 보인다
        d = {v: np.abs(read_at_voxels(cand, plain, axes, bs, v) - ref[v]) for v in ("front", "back")}
        g = lambda f: float(np.mean([f(d[v], sat[v]) for v in ("front", "back")]))
        row["p"]["%.1f" % p] = {
            "상관": c,
            "오차": g(lambda a, m: a.mean()),
            "오차_정답앞": g(lambda a, m: a[m].mean() if m.any() else np.nan),
            "오차_정답뒤": g(lambda a, m: a[~m].mean() if (~m).any() else np.nan)}
    row["초"] = round(time.time() - t0, 1)
    del plain, dpo
    gc.collect()
    return row


def main():
    O.H.register_sheets()
    if len(sys.argv) > 1 and sys.argv[1] == "각도":     # python 초타원.py 각도 <벤치> <케이스>
        bench = sys.argv[2]
        rec = {json.loads(l)["case"]: json.loads(l) for l in
               open(os.path.join(REC, "초타원_%s.jsonl" % bench), encoding="utf-8")}
        c = sys.argv[3] if "_" in sys.argv[3] else bench + "_" + sys.argv[3]
        if len(sys.argv) > 4 and sys.argv[4] == "후보":      # 지금 기본값 대 후보
            angles(c, rec[c], azs=[0, 45, 90], vers=[
                ("깎기 · 파이프 lam 0.20 (지금)", "파이프", 0.20, 2.0),
                ("깎기 · 타원 lam 1.00 (후보)", "타원", 1.00, 2.0)])
        elif len(sys.argv) > 4 and sys.argv[4] == "lam":     # lam 을 푸는 걸 보는 프리셋
            angles(c, rec[c], azs=[0, 45, 90], vers=[
                ("깎기 · 타원 lam 0.50", "타원", 0.50, 2.0),
                ("깎기 · 타원 lam 1.00", "타원", 1.00, 2.0),
                ("깎기 · 오라클 lam 0.50", "오라클", 0.50, 2.0),
                ("깎기 · 오라클 lam 1.00", "오라클", 1.00, 2.0)])
        else:
            angles(c, rec[c])
        return
    if len(sys.argv) > 1 and sys.argv[1] == "3d":       # python 초타원.py 3d <벤치> [케이스 ...]
        bench = sys.argv[2] if len(sys.argv) > 2 else "실물"
        rec = {json.loads(l)["case"]: json.loads(l) for l in
               open(os.path.join(REC, "초타원_%s.jsonl" % bench), encoding="utf-8")}
        want = [n if "_" in n else bench + "_" + n for n in sys.argv[3:]]
        three_d([(c, rec[c]) for c in want])
        return
    if len(sys.argv) > 1 and sys.argv[1] == "그림":     # python 초타원.py 그림 <벤치> [케이스 ...]
        bench = sys.argv[2] if len(sys.argv) > 2 else "도형"
        want = [n if "_" in n else bench + "_" + n for n in sys.argv[3:]]
        figure(want or ["도형_상자", "도형_원기둥", "도형_L자", "도형_토러스옆"], bench)
        return
    bench = sys.argv[1] if len(sys.argv) > 1 else "도형"
    assert bench in BENCHES, "벤치는 %s 중 하나 (%s 는 없다)" % (" · ".join(BENCHES), bench)
    out = os.path.join(REC, "초타원_%s.jsonl" % bench)
    cases = cases_of(bench)
    if len(sys.argv) > 2:
        cases = cases[:int(sys.argv[2])]
    done = {}
    if os.path.exists(out):
        for l in open(out, encoding="utf-8"):
            r = json.loads(l)
            done[r["case"]] = r
    frozen = frozen_corr()
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
        print("  %-26s %s | 최선 p %s%s" % (
            short(case), " ".join("%.3f" % r["p"]["%.1f" % p]["오차"] for p in PS),
            min(PS, key=lambda p: r["p"]["%.1f" % p]["오차"]),
            "" if case in frozen else "  (얼린 값 없음)"), flush=True)
    report(rows, bench)


def short(case):
    return case.split("_", 1)[1][:24] if "_" in case else case[:24]


def report(rows, bench="도형"):
    print("\n  [%s] 깊이맵 오차 (오라클과 · 낮을수록 좋다) · 부품 수는 한 높이 최대" % bench)
    print("  %-26s %4s | %s | %s" % ("케이스", "부품", " ".join("p%-5.1f" % p for p in PS), "최선 p  p=2 대비"))
    best = []
    for r in rows:
        e = [r["p"]["%.1f" % p]["오차"] for p in PS]
        bp = PS[int(np.argmin(e))]
        best.append(bp)
        print("  %-26s %4d | %s | %5.1f  %+.4f" % (
            short(r["case"]), r["부품"], " ".join("%.4f" % x for x in e),
            bp, min(e) - r["p"]["2.0"]["오차"]))
    # **갈라서** — 정답이 맨 앞인 화소 / 그 뒤인 화소. 섞으면 지수가 하는 일이 안 보인다
    print("\n  갈라 보기 (중앙) · 정답앞 = 정답이 그 기둥 맨 앞까지 찬 화소 · 정답뒤 = 그 뒤")
    print("  %-8s %10s %10s" % ("p", "정답앞", "정답뒤"))
    for p in PS:
        k = "%.1f" % p
        print("  %-8s %10.4f %10.4f" % (k,
              np.nanmedian([r["p"][k].get("오차_정답앞", np.nan) for r in rows]),
              np.nanmedian([r["p"][k].get("오차_정답뒤", np.nan) for r in rows])))
    n = len(rows)
    print("\n  %d 장 · p=2 고정 대비 **부품마다 제 p** 를 주면 오차가 얼마나 빠지나" % n)
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



def figure(cases, bench="도형"):
    """**비포/애프터를 모양으로.** 높이 50% 단면 · 검정 선 = 정답 단면 · 아래가 앞(-y).

    왼쪽이 hull(이진), 가운데가 지금 쓰는 타원(p=2), 오른쪽이 그 도형이 원하는 p 의 초타원.
    깊이맵이 아니라 **단면 모양 가정 자체**를 그린다 — 깎기가 읽는 것이 이 모양의 앞·뒤다."""
    from PIL import Image, ImageDraw
    sys.path.insert(0, HERE)
    from 계획 import _font
    rows = {json.loads(l)["case"]: json.loads(l) for l in
            open(os.path.join(REC, "초타원_%s.jsonl" % bench), encoding="utf-8")}
    S, G, LW, TOP, RH = 200, 16, 232, 154, 248
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
    d.text((24, 96), "hull 부피가 정답의 1.7배를 넘으면 주황 — 그 케이스의 p 는 모양이 아니라 "
                     "**부피를 깎는 손잡이**로 이긴다 (p<2 는 그냥 작다)", fill=(90, 90, 90), font=f3)
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
        # **hull 이 얼마나 뚱뚱한가.** 지수가 모양이 아니라 부피 손잡이로 쓰이는 케이스를
        # 눈으로 가려내려고 적는다 (2026-09-12 · wizard_o87 이 2.0배라 p<2 가 이겼다).
        # **벤치와 같은 셈** (`대조.py:307` 의 vol) — 정답이 non-watertight 라 trimesh 부피는 못 쓴다
        tg, otg = O.J.grid(truth)                  # 이름 조심 — G 는 이 함수의 칸 사이 여백이다
        hg, ohg = O.J.grid(O.C.to_mesh(plain, axes))
        ta, ha = O.J.common(tg, otg, hg, ohg)
        vr = float(ha.sum()) / max(float(ta.sum()), 1.0)
        # **좌표가 맞나** — `오라클.figure` 의 문을 실물용으로 눅였다. 도형은 hull 이 정답을 완전히
        # 덮지만 실물은 아니다 (못덮음 중앙 0.6% · 최대 5.4% — cloak_Chest_Closed). 그래서 조금
        # 삐져나오는 건 적기만 하고, **크게 어긋난 것**(좌표 뒤집힘)만 멈춘다
        over = 0.0
        if sec is not None:
            (tx0, ty0, _), (tx1, ty1, _) = sec.bounds
            sp = max(xs[1] - xs[0], ys[1] - ys[0], 1e-9)
            over = max(xs[0] - tx0, tx1 - xs[1], ys[0] - ty0, ty1 - ys[1], 0.0) / sp
            assert over < 0.15, "%s: 정답 단면이 hull 밖으로 %.0f%% — 좌표가 어긋났다" % (case, 100 * over)
        cx, cy = sum(xs) / 2, sum(ys) / 2
        span = max(xs[1] - xs[0], ys[1] - ys[0]) * 1.15 + 4 * du
        q = (np.arange(S) + 0.5) / S - 0.5
        ix = np.round((cx + q * span - u[0]) / du).astype(int)
        iy = np.round((cy - q * span - u[0]) / du).astype(int)    # 행이 내려갈수록 앞
        ok = ((ix >= 0) & (ix < len(u)))[None, :] & ((iy >= 0) & (iy < len(u)))[:, None]
        ix, iy = np.clip(ix, 0, len(u) - 1), np.clip(iy, 0, len(u) - 1)
        y0 = TOP + r * RH
        nm = short(case)                       # 긴 이름은 접어서 — 칸을 넘지 않게
        ln = [nm[i:i + 22] for i in range(0, len(nm), 22)][:2]
        for t, tx in enumerate(ln):
            d.text((24, y0 + 66 + 20 * t), tx, fill=(20, 20, 20), font=f3 if len(nm) > 14 else f2)
        d.text((24, y0 + 70 + 20 * len(ln)), "부품 %d · hull 부피 %.2f배" % (rows[case]["부품"], vr),
               fill=(120, 120, 120) if vr < 1.7 else (190, 90, 40), font=f3)
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
        print("  %-38s 단면 z=%.3f · 원하는 p %4.1f · hull 부피 %.2f배 · 정답이 hull 밖 %.1f%%"
              % (case[:38], z[k], bp, vr, 100 * over), flush=True)
        del plain, masks
        gc.collect()
    im.save(os.path.join(HERE, "out", "초타원단면_%s.png" % bench))
    print("  -> out/초타원단면_%s.png" % bench)

def three_d(cases, lam=0.50, az=35):
    """**깎은 것을 3D 로 본다** — 단면 말고. 그리고 여기서 처음으로 **IoU** 를 잰다.

    한 줄에 정답 · hull(이진) · 깎기 p=2 · 깎기 p=그 케이스 최선. 넷을 `라벨._same_frame` 으로
    한 격자에 올리고 `각도.shot` 으로 같은 각도 · **같은 색 눈금**에 칠한다 (빨강이 카메라 쪽).

    깊이맵 오차가 줄었다고 IoU 가 오른다는 보장은 없다 — 그걸 여기서 처음 본다."""
    from PIL import Image, ImageDraw
    sys.path.insert(0, HERE)
    import 라벨 as LB
    import 각도 as A
    from 계획 import _font
    R, G, LW, TOP, RH = 300, 16, 232, 150, 348
    im = Image.new("RGB", (LW + 4 * (R + G) + G, TOP + len(cases) * RH + 64), "white")
    d = ImageDraw.Draw(im)
    f1, f2, f3 = _font(26), _font(15), _font(13)
    d.text((24, 18), "깎은 것을 3D 로 — 단면이 아니라 물건", fill=(20, 20, 20), font=f1)
    d.text((24, 56), "z 축으로 %d도 돌려 본 앞면 · 색은 깊이 (빨강이 카메라 쪽) · 네 장이 같은 격자 · 같은 눈금 · "
                     "lam %.2f" % (az, lam), fill=(90, 90, 90), font=f3)
    d.text((24, 76), "칸 아래 = 3D IoU (판정 격자 128). **이 실험에서 IoU 를 재는 건 여기가 처음이다** — "
                     "깊이맵 오차가 줄어도 IoU 가 오른다는 보장은 없다", fill=(90, 90, 90), font=f3)
    d.text((24, 96), "p=2 는 지금 쓰는 타원 · 오른쪽은 그 케이스가 원하는 지수 (정답 깊이에 맞춰 고른 것 — 상한)",
           fill=(90, 90, 90), font=f3)
    for j, name in enumerate(("정답", "hull (이진)", "깎기 · 타원 p=2", "깎기 · 원하는 p")):
        d.text((LW + G + j * (R + G), TOP - 24), name, fill=(40, 40, 40), font=f2)
    # **케이스마다 적고 이어 돈다** — 케이스당 build 두 번이라 이 PC 에선 한 번에 다 못 돈다
    cache = os.path.join(REC, "3d")
    os.makedirs(cache, exist_ok=True)
    for r, (case, rec) in enumerate(cases):
        e = {q: rec["p"]["%.1f" % q]["오차"] for q in PS}
        bp = min(PS, key=lambda q: e[q])
        key = os.path.join(cache, "%s_lam%.2f_az%d" % (case, lam, az))
        if os.path.exists(key + ".json"):
            sc = json.load(open(key + ".json", encoding="utf-8"))["iou"]
            strip = Image.open(key + ".png")
            tiles = [strip.crop((j * R, 0, (j + 1) * R, R)) for j in range(4)]
        else:
            truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
            plain, d2, axes, _ = O.build(case, truth, lam, "타원", 2.0)
            _, db, _, _ = O.build(case, truth, lam, "타원", bp)
            iou = O._iou_fn(truth)
            sc = [None, iou(plain, axes), iou(d2, axes), iou(db, axes)]
            vox = LB._same_frame(case, plain, d2, axes, extra=[db])   # 정답 · 이진 · p2 · best
            ds = [A.depth(v, az) for v in vox]
            lo = min(x[h].min() for x, h in ds)
            hi = max(x[h].max() for x, h in ds)
            tiles = [A.paint(x, h, R=R, span=(lo, hi)) for x, h in ds]
            tiles = [t if isinstance(t, Image.Image) else Image.fromarray(t) for t in tiles]
            strip = Image.new("RGB", (4 * R, R), "white")
            for j, t in enumerate(tiles):
                strip.paste(t.resize((R, R)), (j * R, 0))
            strip.save(key + ".png")
            json.dump({"case": case, "iou": sc, "p": bp, "lam": lam, "az": az},
                      open(key + ".json", "w", encoding="utf-8"), ensure_ascii=False)
            del plain, d2, db, vox, ds
            gc.collect()
        y0 = TOP + r * RH
        nm = short(case)
        for t, tx in enumerate([nm[i:i + 22] for i in range(0, len(nm), 22)][:2]):
            d.text((24, y0 + 96 + 20 * t), tx, fill=(20, 20, 20), font=f3)
        d.text((24, y0 + 140), "원하는 p %.1f" % bp, fill=(120, 120, 120), font=f3)
        for j, tile in enumerate(tiles):
            x0 = LW + G + j * (R + G)
            im.paste(tile.resize((R, R)), (x0, y0))
            d.rectangle([x0, y0, x0 + R - 1, y0 + R - 1], outline=(215, 215, 215))
            if sc[j] is not None:
                dv = sc[j] - sc[2]
                txt = "IoU %.4f" % sc[j] + ("" if j != 3 else "  (%+.4f)" % dv)
                d.text((x0, y0 + R + 6), txt, font=f3,
                       fill=(40, 40, 40) if j != 3 else (30, 130, 70) if dv > 0 else (190, 60, 40))
        print("  %-38s hull %.4f · 깎기 p=2 %.4f · p=%.1f %.4f (%+.4f)"
              % (case[:38], sc[1], sc[2], bp, sc[3], sc[3] - sc[2]), flush=True)
    im.save(os.path.join(HERE, "out", "초타원3d.png"))
    print("  -> out/초타원3d.png")


def angles(case, rec, lam=0.50, azs=None, vers=None):
    """**한 케이스를 여러 각도에서.** 한 면만 보면 옆에서 무너진 걸 못 본다 (2026-09-12).

    줄 = 판본 (정답 · hull · 깎기 p=2 · 깎기 원하는 p) · 칸 = z 축 회전각.
    스무 장이 **같은 격자 · 같은 색 눈금**이라 각도끼리도 판본끼리도 맞대진다.
    복셀은 `out/기록/3d/<case>_lam<..>_vox.npz` 에 눌러 담는다 — 각도를 바꿔 다시 그릴 때
    build 를 또 돌리지 않으려고."""
    from PIL import Image, ImageDraw
    sys.path.insert(0, HERE)
    import 라벨 as LB
    import 각도 as A
    from 계획 import _font
    azs = azs or list(A.AZ)
    e = {q: rec["p"]["%.1f" % q]["오차"] for q in PS}
    bp = min(PS, key=lambda q: e[q])
    cache = os.path.join(REC, "3d")
    os.makedirs(cache, exist_ok=True)
    # 판본 = (라벨, 깊이맵, lam, 지수). 안 주면 옛 다섯 줄 (한 lam 에서 지수만 바꾼다)
    vers = vers or [("깎기 · 타원 p=2", "타원", lam, 2.0),
                    ("깎기 · p=%.1f" % bp, "타원", lam, bp),
                    ("깎기 · 오라클 (정답 깊이)", "오라클", lam, 2.0)]
    tag = "_".join("%s%.2f-%.1f" % (w[:2], l, e) for _, w, l, e in vers)
    key = os.path.join(cache, "%s_%s_vox.npz" % (case, tag))
    N = len(vers) + 2                            # 정답 · hull · 판본들
    if os.path.exists(key):
        z = np.load(key)
        shp = tuple(z["shape"])
        vox = [np.unpackbits(z["v%d" % i])[:int(np.prod(shp))].astype(bool).reshape(shp) for i in range(N)]
        sc = list(z["iou"])
    else:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        iou = O._iou_fn(truth)
        made, plain, axes = [], None, None
        for _, which, l, ex in vers:
            # **오라클은 정답 깊이다** — 깎기의 천장. lam 은 그 깊이를 어디까지 믿느냐다
            pl, dv, ax, _ = O.build(case, truth, l, which, ex)
            if plain is None:
                plain, axes = pl, ax
            made.append(dv)
            print("     구움 %s lam %.2f 지수 %.1f" % (which, l, ex), flush=True)
        sc = [np.nan, iou(plain, axes)] + [iou(m, axes) for m in made]
        vox = LB._same_frame(case, plain, made[0], axes, extra=made[1:])
        np.savez_compressed(key, shape=np.array(vox[0].shape), iou=np.array(sc),
                            **{"v%d" % i: np.packbits(v) for i, v in enumerate(vox)})
        del plain, made
        gc.collect()
    names = ["정답", "hull (이진)"] + [v[0] for v in vers]
    R, G, LW, TOP, RH = 236, 14, 176, 150, 288
    im = Image.new("RGB", (LW + len(azs) * (R + G) + G, TOP + N * RH + 62), "white")
    d = ImageDraw.Draw(im)
    f1, f2, f3 = _font(26), _font(15), _font(13)
    d.text((24, 18), "%s — 각도 %d개로 본다" % (short(case), len(azs)), fill=(20, 20, 20), font=f1)
    d.text((24, 56), "z 축 회전 · 색은 깊이 (**빨강이 카메라 쪽**) · 모든 칸이 같은 격자 · 같은 눈금",
           fill=(90, 90, 90), font=f3)
    d.text((24, 76), "**한 면만 보면 옆에서 무너진 걸 못 본다.** 앞에서 멀쩡한 판본이 90도에서 갈라지는지 본다",
           fill=(90, 90, 90), font=f3)
    d.text((24, 96), "부품 %d · 원하는 p %.1f (정답 깊이에 맞춰 고른 것 — 상한)" % (rec["부품"], bp),
           fill=(90, 90, 90), font=f3)
    for j, az in enumerate(azs):
        d.text((LW + G + j * (R + G), TOP - 24), "%d도" % az, fill=(40, 40, 40), font=f2)
    shots = [[A.depth(v, az) for az in azs] for v in vox]
    lo = min(x[h].min() for row in shots for x, h in row)
    hi = max(x[h].max() for row in shots for x, h in row)
    for r in range(N):
        y0 = TOP + r * RH
        d.text((24, y0 + 96), names[r], fill=(20, 20, 20), font=f2)
        if np.isfinite(sc[r]):
            dv = sc[r] - sc[2]                   # 첫 깎기 줄과의 차
            d.text((24, y0 + 120), "IoU %.4f%s" % (sc[r], "" if r <= 2 else "  (%+.4f)" % dv), font=f3,
                   fill=(40, 40, 40) if r <= 2 else (30, 130, 70) if dv > 0 else (190, 60, 40))
        for j, (x, h) in enumerate(shots[r]):
            tile = A.paint(x, h, R=R, span=(lo, hi))
            tile = tile if isinstance(tile, Image.Image) else Image.fromarray(tile)
            x0 = LW + G + j * (R + G)
            im.paste(tile.resize((R, R)), (x0, y0))
            d.rectangle([x0, y0, x0 + R - 1, y0 + R - 1], outline=(215, 215, 215))
        print("  %s · 각도 %s 그림" % (names[r], azs), flush=True)
    # **90도에서 앞뒤가 남아 있나.** 옆에서 본 깊이(=원래 앞뒤축)의 퍼짐을 판본마다 잰다.
    # 정답은 팔 하나가 앞 하나가 뒤라 퍼짐이 크고, 유령으로 뭉치면 한 덩어리라 작다
    side = [A.depth(v, 90) for v in vox]
    band, arm = None, [None, None]
    for r, (x, h) in enumerate(side):
        if r == 0:                                # 정답에서 「깊이가 제일 퍼진 높이 띠」를 고른다
            col = np.where(h.any(0), np.ptp(np.where(h, x, np.nan), axis=0, ), 0.0) if False else None
            sp = np.array([np.ptp(x[h[:, k], k]) if h[:, k].any() else 0.0 for k in range(h.shape[1])])
            k0 = int(np.argmax(sp)); band = slice(max(k0 - 6, 0), k0 + 7)
        v = [np.ptp(x[h[:, k], k]) for k in range(*band.indices(h.shape[1])) if h[:, k].any()]
        # **양팔 색차** — 0도에서 본 앞면 깊이를 어깨 띠의 양쪽 끝 15% 에서 잰다.
        # 「정답은 한 팔이 파란데 다들 빨갛다」가 이 숫자다 (칸이 클수록 앞뒤가 갈라져 있다)
        fx, fh = A.depth(vox[r], 0)
        if r == 0:
            xs0 = np.nonzero(fh[:, band].any(1))[0]
            w0 = max(len(xs0) // 6, 1)
            arm[:] = [xs0[:w0], xs0[-w0:]]
        def mean_at(idx):
            g = [fx[q, k] for q in idx for k in range(*band.indices(fh.shape[1])) if fh[q, k]]
            return float(np.mean(g)) if g else float("nan")
        gap = abs(mean_at(arm[0]) - mean_at(arm[1]))
        d.text((24, TOP + r * RH + 148), "0도 양팔 깊이차 %.0f칸" % gap,
               fill=(120, 120, 120) if r else (40, 40, 40), font=f3)
        d.text((24, TOP + r * RH + 168), "90도 퍼짐 %.0f칸" % (np.mean(v) if v else 0.0),
               fill=(170, 170, 170), font=f3)
        print("     %-24s 0도 양팔 깊이차 %5.1f 칸 · 90도 퍼짐 %.1f 칸"
              % (names[r], gap, np.mean(v) if v else 0.0), flush=True)
    out = os.path.join(HERE, "out", "초타원각도_%s.png" % short(case))
    im.save(out)
    print("  -> %s" % os.path.relpath(out, HERE))


if __name__ == "__main__":
    main()
