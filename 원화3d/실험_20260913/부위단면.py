# -*- coding: utf-8 -*-
"""**부위마다 단면을 고른다** — 딱딱하다고 읽힌 판은 지금 규칙(직사각), 나머지는 타원.

    python 부위단면.py 조각 [어려운|실물]      정면 판 -> 맥락 조각 -> out/부위단면/
    py -3.11 부위단면.py 라벨                  SigLIP 2 넷 부류(천 · 피부 · 머리 · 딱딱함) -> out/부위단면/예측_siglip_맥락.jsonl
    python 부위단면.py 판정 [어려운|실물]      재현 검사 -> 판본 IoU (케이스마다 적고 이어 돈다) -> out/기록/부위단면_<세트>_<날짜>.json
    python 부위단면.py 그림                    어려운 세트 규칙 4장 -> out/부위단면_그림.png

`어려운벤치.py` 결과: 타원 계열이 인물에서 +0.05~0.085, 각진 것에서 −0.01~−0.12. 한 기본값으로는 못 덮는다.
그래서 **부위마다** 고른다. 판단 재료는 오늘 만든 재질 라벨 — `재질넷.py` 에서 SigLIP 2 맥락이
천 -> 딱딱함 0.8% · 딱딱함 -> 천 5.2% 로 갈랐다.

## 판본

    기준      파이프 lam0.20 (지금 hull.py)                           ← 어려운벤치 기록과 **같은 값이 나와야** 한다
    기준국소   같은 복셀에 ITK국소 메시                                 ← 선택과 메시 단계를 맞춘 대조군
    전부      타원1.00 + ZSMOOTH σ2 + ITK국소                        ← 어려운벤치 기록과 같은 값이 나와야 한다
    선택      정면 기둥 (x, z) 마다: 그 화소의 판이 「딱딱함」이면 기준 복셀, 아니면 타원1.00+Z2 복셀 -> ITK국소

라벨은 **정면 판만** 쓴다 (기둥이 정면 화소다). 선 띠는 가장 가까운 판으로 채운다 (`앞뒤.fill`). 라벨 없는 판(50 화소 미만)은 타원.

## 판정 — 어려운 11장 (2026-09-13 밤, 돌리기 전에 적음)

    선택이 기준보다 · 전부보다   ΔIoU 평균 > 0 — 격자 128 · 192 둘 다
    과반 승은 안 쓴다 — 딱딱함으로 골라진 케이스는 기준과 같아 이김이 원리적으로 안 나온다 (이길 수 없는 규약)
    천장 = 케이스마다 기준 · 전부 중 나은 쪽. 천장이 둘 다 이기는지 먼저 본다

결과: **통과** (기준 +0.0105 · +0.0075 · 전부 +0.0243 · +0.0224 · 천장의 61%). 사후 대조 기준국소 대비 +0.0075 · +0.0067.

## 판정 — 실물 28장 (2026-09-13 밤, 돌리기 전에 적음)

벤치.json 29장에서 `소체`(base_female 과 md5 같음)를 뺀 28장. 11장 결과를 본 뒤라 **기준국소를 판정에 넣는다**:

    선택이 기준보다 · 기준국소보다 · 전부보다   ΔIoU 평균 > 0 — 격자 128 · 192 둘 다 (셋 다)

## ⚠ 이 시험이 못 가르는 것

딱딱한 물건(궤짝 · 북엔드 · 드릴 · 건물 · 미믹)은 **그림 결부터 다르다** (로우폴리 단색 · 스캔). SigLIP 이 재질이 아니라 결로
딱딱함을 고를 수 있고, 이 벤치에선 그게 우연히 맞는 답이 된다. 손그림 메카(오메가몬)에서 되는지는 여기서 안 나온다.
wizard_o87 은 정면 판이 모자 챙을 위에서 본 원판이라(에셋이 누움) 97% 딱딱함으로 읽혔다 — 판 방향 문제.
"""
import json
import os
import sys
import time

import numpy as np

HERE = r"G:\art2real\원화3d"
SCR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, SCR)
OUT = os.path.join(HERE, "out", "부위단면")
MIN_PX = 50
VERS = ("기준", "기준국소", "전부", "선택")


def cases(which="어려운"):
    if which == "실물":
        b = json.load(open(os.path.join(HERE, "벤치.json"), encoding="utf-8"))["cases"]
        return [c["name"] for c in b if c["name"] != "소체"]          # 소체 = base_female (md5 같음)
    import 어려운벤치 as B
    return B.CASES


def build_crops(which):
    import cv2
    import 재질 as R
    os.chdir(HERE)
    path = os.path.join(OUT, "판_맥락.jsonl")
    items = {json.loads(l)["key"]: json.loads(l) for l in open(path, encoding="utf-8")} if os.path.exists(path) else {}
    for case in cases(which):
        if any(it["case"] == case for it in items.values()):
            continue
        lab, img = R.view_data(case, "front")
        os.makedirs(os.path.join(OUT, "맥락", case), exist_ok=True)
        for k in np.unique(lab):
            m = lab == k
            if k == 0 or m.sum() < MIN_PX:
                continue
            key = "맥락/%s/front_%d.png" % (case, k)
            cv2.imencode(".png", R.context_tile(img, m))[1].tofile(os.path.join(OUT, key))
            items[key] = {"key": key, "members": [key], "case": case, "k": int(k)}
        print("  %-30s 판 누적 %d" % (case[:30], len(items)), flush=True)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(it, ensure_ascii=False) + "\n" for it in items.values())


def run_labels():
    import 재질 as R
    import 재질넷 as N
    N.setup()                                        # 넷 부류 문장 · 동의어
    R.OUT = OUT
    R.run_model("siglip", "맥락")


def labels_of(case):
    """정면 판 번호 -> 예측 부류 (0 천 · 1 피부 · 2 머리 · 3 딱딱함)."""
    items = {json.loads(l)["key"]: json.loads(l) for l in open(os.path.join(OUT, "판_맥락.jsonl"), encoding="utf-8")}
    pred = {json.loads(l)["key"]: json.loads(l)["pred"] for l in open(os.path.join(OUT, "예측_siglip_맥락.jsonl"), encoding="utf-8")}
    return {it["k"]: pred[k] for k, it in items.items() if it["case"] == case and k in pred}


def versions(case, truth):
    """판본 넷 -> {이름: 메시}, 축, 딱딱함 기둥 비율."""
    import cv2
    import hull as H
    import win as W
    import 오라클 as O
    import 앞뒤 as A
    import 앨리어싱 as AL
    src, base = H.CASES[case]["src"], H.art_dir(case)
    bs = H.CASES[case]["back_sign"]
    masks, deps, raw = {}, {}, {}
    for v, f in src.items():
        raw[v] = H.declutter(W.art_mask(os.path.join(base, f)))
        masks[v], deps[v] = H.to_win(raw[v], H.load_depth(v, raw[v], case=case))
    # 정면 딱딱함 지도 — 판 라벨(512, 선 띠 채움) -> 원화 크기 -> 마스크와 같은 변환
    lab = A.fill(np.load(os.path.join(HERE, "out", "깊이", case, "front", "labels.npy")), A.sheet_mask(case, "front"))
    hard_ids = [k for k, c in labels_of(case).items() if c == 3]
    hard = cv2.resize(np.isin(lab, hard_ids).astype(np.uint8), raw["front"].shape[::-1], interpolation=cv2.INTER_NEAREST)
    _, hardwin = H.to_win(raw["front"], hard.astype(np.float32))
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    deps = {v: H._warp_one(a, v, p) for v, a in deps.items()}
    hardwin = H._warp_one(hardwin, "front", p)
    plain, axes = H.carve(masks, back_sign=bs)
    vox_pipe, _ = H.carve_depth(masks, deps, lam=0.20, back_sign=bs)
    H.ZSMOOTH = 2.0
    try:
        vox_ell, _ = H.carve_depth(masks, O.ellipse_depths(plain, axes, bs), lam=1.00, back_sign=bs)
    finally:
        H.ZSMOOTH = 0.0
    u, _, z = axes
    X2, Z2 = np.meshgrid(u, z, indexing="ij")
    py, px = W.topix(X2, Z2)
    col = hardwin[py, px] > 0.5
    on = plain.any(1)
    vox_sel = np.where(col[:, None, :], vox_pipe, vox_ell)
    out = {"기준": O.C.to_mesh(vox_pipe, axes), "기준국소": AL.variant("ITK국소", vox_pipe, axes)[0],
           "전부": AL.variant("ITK국소", vox_ell, axes)[0], "선택": AL.variant("ITK국소", vox_sel, axes)[0]}
    return out, axes, float((col & on).sum() / max(on.sum(), 1))


def judge(which):
    import gc
    import trimesh
    import hull as H
    import 오라클 as O
    import 어려운벤치 as B
    os.chdir(HERE)
    H.register_sheets()
    rec = sorted(f for f in os.listdir(os.path.join(HERE, "out", "기록")) if f.startswith("어려운벤치_2"))[-1]
    old = {r["case"]: r for r in json.load(open(os.path.join(HERE, "out", "기록", rec), encoding="utf-8"))["rows"]}
    tag = "부위단면 · %s · 기준 기준국소 전부 선택 · 격자2 (2026-09-13 밤)" % which
    prog = os.path.join(HERE, "out", "기록", "부위단면_%s_진행.jsonl" % which)
    done = {}
    if os.path.exists(prog):
        for l in open(prog, encoding="utf-8"):
            r = json.loads(l)
            if r.get("판") == tag:
                done[r["case"]] = r
    for case in cases(which):
        if case in done:
            continue
        t0 = time.time()
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        i128, i192 = O._iou_fn(truth), O._iou_fn(truth, B.P192)
        V, axes, frac = versions(case, truth)
        r = {"case": case, "판": tag, "딱딱함기둥": frac}
        for k, m in V.items():
            r[k], r[k + "·192"] = i128(m, axes), i192(m, axes)
        if case in old:                                   # **재현 검사** — 어려운벤치에 있던 케이스는 같은 값이어야 한다
            for k in ("기준", "전부"):
                assert abs(r[k] - old[case][k]) < 1e-3, "%s %s: 기록 %.4f 와 다르다 (%.4f) — 조립이 어긋났다" % (
                    case, k, old[case][k], r[k])
        with open(prog, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        done[case] = r
        print("  %-30s 딱딱함 %3.0f%% · 기준 %.4f · 기준국소 %.4f · 전부 %.4f · 선택 %.4f · %.0f초" % (
            case[:30], 100 * frac, r["기준"], r["기준국소"], r["전부"], r["선택"], time.time() - t0), flush=True)
        del V, truth
        gc.collect()
    rows = [done[c] for c in cases(which) if c in done]
    if len(rows) < len(cases(which)):
        print("  %d/%d 장 — 다시 돌리면 이어 돈다" % (len(rows), len(cases(which))))
        return
    g = lambda k: np.array([r[k] for r in rows])
    n = len(rows)
    wtl = lambda d: "%d·%d·%d" % ((d > 1e-4).sum(), (abs(d) <= 1e-4).sum(), (d < -1e-4).sum())
    ceil = {s: np.maximum(g("기준" + s), g("전부" + s)) for s in ("", "·192")}
    print("\n  [%s] %d 장 · 3D IoU" % (which, n))
    print("  %-8s %-17s %-32s %-32s %s" % ("판본", "IoU 128 · 192", "vs 기준 (승·무·패)", "vs 기준국소", "vs 전부"))
    table = [(k, g(k), g(k + "·192")) for k in VERS] + [("천장", ceil[""], ceil["·192"])]
    for name, a, b2 in table:
        cells = []
        for ref in ("기준", "기준국소", "전부"):
            d = [a - g(ref), b2 - g(ref + "·192")]
            cells.append("%+.4f · %+.4f (%s)" % (d[0].mean(), d[1].mean(), wtl(d[0])))
        print("  %-8s %.4f · %.4f   %-32s %-32s %s" % (name, a.mean(), b2.mean(), *cells))
    beats = {ref: all((g("선택" + s) - g(ref + s)).mean() > 0 for s in ("", "·192")) for ref in ("기준", "기준국소", "전부")}
    ok_ceil = all((ceil[s] - g("기준" + s)).mean() > 0 and (ceil[s] - g("전부" + s)).mean() > 0 for s in ("", "·192"))
    need = ("기준", "전부") if which == "어려운" else ("기준", "기준국소", "전부")
    ok = all(beats[k] for k in need)
    print("\n  규약 점검 — 천장이 기준 · 전부를 이기나: %s" % ("O" if ok_ceil else "X"))
    print("  판정 — 선택이 " + " · ".join("%s보다 %s" % (k, "O" if beats[k] else "X") for k in need) +
          " · **%s**" % ("부위별이 낫다" if ok else "아니다"))
    if ok:
        print("  천장까지 걷은 몫 (128): %.0f%%" % (100 * (g("선택") - g("기준")).mean() / max((ceil[""] - g("기준")).mean(), 1e-9)))
    print("\n  케이스별 (128) — 선택 − 기준 이 큰 차례")
    for r in sorted(rows, key=lambda r: -(r["선택"] - r["기준"])):
        print("    %-30s 딱딱함 %3.0f%% · 기준 %.4f · 전부 %.4f · 선택 %.4f · Δ %+.4f" % (
            r["case"][:30], 100 * r["딱딱함기둥"], r["기준"], r["전부"], r["선택"], r["선택"] - r["기준"]))
    p = os.path.join(HERE, "out", "기록", "부위단면_%s_%s.json" % (which, time.strftime("%Y%m%d_%H%M")))
    json.dump({"때": time.strftime("%Y-%m-%d %H:%M"), "판": tag, "판정": {**beats, "통과": ok, "천장규약": ok_ceil},
               "rows": rows}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  기록 -> %s" % os.path.relpath(p, HERE))


def figure(which="어려운"):
    """규칙으로 고른 4장. 열: 딱딱함 지도(정면, 초록 = 딱딱함으로 읽힌 판) · 정답 · 기준 · 전부 · 선택 (45도 깊이색 + 등깊이선).

    어려운   선택이 기준보다 가장 크게 오른 2 + 천장(기준 · 전부 중 나은 쪽)에서 가장 크게 놓친 2
    실물     선택이 **전부보다** 가장 크게 이긴 2 + 가장 크게 진 2 — 실물 판정이 갈린 자리"""
    import cv2
    import trimesh
    import hull as H
    import 재질 as R
    import 앞뒤 as A
    import 앨리어싱 as AL
    import 깊이색 as DC
    os.chdir(HERE)
    H.register_sheets()
    prefix = "부위단면_2" if which == "어려운" else "부위단면_실물_2"
    rec = sorted(f for f in os.listdir(os.path.join(HERE, "out", "기록")) if f.startswith(prefix))[-1]
    rows = json.load(open(os.path.join(HERE, "out", "기록", rec), encoding="utf-8"))["rows"]
    if which == "어려운":
        gain = sorted(rows, key=lambda r: -(r["선택"] - r["기준"]))
        miss = sorted(rows, key=lambda r: -(max(r["기준"], r["전부"]) - r["선택"]))
    else:
        gain = sorted(rows, key=lambda r: -(r["선택"] - r["전부"]))
        miss = sorted(rows, key=lambda r: r["선택"] - r["전부"])
    picks = list(dict.fromkeys([r["case"] for r in gain[:2]] + [r["case"] for r in miss[:2]]))
    by = {r["case"]: r for r in rows}
    out = []
    for case in picks:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        V, axes, frac = versions(case, truth)
        lab, img = R.view_data(case, "front")
        F = A.fill(lab, A.sheet_mask(case, "front"))
        hard = np.isin(F, [k for k, c in labels_of(case).items() if c == 3])
        tint = img[:, :, ::-1].astype(np.float32)
        on = F > 0
        tint[on & hard] = tint[on & hard] * 0.35 + np.array([60, 190, 90]) * 0.65
        tint[on & ~hard] = tint[on & ~hard] * 0.55 + np.array([120, 150, 235]) * 0.45
        ys, xs = np.nonzero(on)
        h = max(np.ptp(ys), np.ptp(xs)) // 2 + 6
        cy, cx = (ys.min() + ys.max()) // 2, (xs.min() + xs.max()) // 2
        tiles = [cv2.resize(tint[max(cy - h, 0):cy + h, max(cx - h, 0):cx + h].astype(np.uint8), (300, 300),
                            interpolation=cv2.INTER_NEAREST)]
        fr, dr = AL.frame_of(V["기준"], 45), DC.depth_range(V["기준"], 45)
        tiles.append(DC.colorize(DC.zbuffer(truth, 45, fr, 300), dr))
        tiles += [DC.colorize(DC.zbuffer(V[k], 45, fr, 300), dr) for k in ("기준", "전부", "선택")]
        r = by[case]
        out.append(("%s\n딱딱함 %.0f%%\n기준 %.3f\n전부 %.3f\n선택 %.3f" % (case[:16], 100 * frac, r["기준"], r["전부"], r["선택"]), tiles))
        print("  %s 그림" % case, flush=True)
    DC.grid(out, ["딱딱함 지도 (정면)", "정답", "기준 (직사각)", "전부 (타원)", "선택 (부위별)"],
            "부위마다 단면을 골랐다 — 딱딱함 판은 직사각, 나머지는 타원 (45도 깊이색 + 등깊이선)",
            "첫 칸 초록 = SigLIP 이 딱딱함으로 읽은 판 · 파랑 = 나머지. " + (
                "위 둘 = 선택이 기준보다 가장 크게 오른 케이스, 아래 = 천장에서 가장 크게 놓친 케이스" if which == "어려운" else
                "실물 28장 — 위 둘 = 선택이 전부(타원)보다 가장 크게 이긴 케이스, 아래 둘 = 가장 크게 진 케이스"),
            os.path.join(HERE, "out", "부위단면_그림.png" if which == "어려운" else "부위단면_실물_그림.png"), S=300)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else ""
    which = sys.argv[2] if len(sys.argv) > 2 else "어려운"
    if what == "조각":
        build_crops(which)
    elif what == "라벨":
        run_labels()
    elif what == "판정":
        judge(which)
    elif what == "그림":
        figure(which)
    else:
        print(__doc__)
