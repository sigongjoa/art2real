# -*- coding: utf-8 -*-
"""**단면 조각 묶기 — 얇은 판 없애기** (2026-09-15).

    python 조각묶기.py 검사     자가검사만
    python 조각묶기.py [n]      아직 안 한 장 n 개 (첫 장은 닫힌 궤짝) -> out/기록/조각묶기_진행.jsonl
    python 조각묶기.py 판정     -> out/기록/조각묶기_<때>.json
    python 조각묶기.py 그림     -> out/조각묶기그림.png

판정은 `claudedocs/plan_조각묶기_20260915.md` 「판정」 절 그대로다 — 돌리기 전에 적었다.
판본은 타원을 넣는 **단위**만 바꾼다. 깊이 규약 · lam 1.00 · 깎기(`hull.carve_depth`)는 기본(`hull.carve_default`)과 같다.
"""
import json
import os
import sys
import time

import cv2
import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260915"))
os.chdir(HERE)
import hull as H
import 오라클 as O
import 정답 as J
import 표면 as SF
import win as W
from 겉면채점 import bench_cases, fill_slices
from 깨짐 import thin_share

PROG = os.path.join(HERE, "out", "기록", "조각묶기_진행.jsonl")
TAG = "조각묶기 · 실물28 · 기본/묶기k3·k5·k9/대응/얇은유지 · 타원 lam1.00 · 속채운 정답 · 격자128·192 (2026-09-15)"
VARS = ("기본", "묶기k3", "묶기k5", "묶기k9", "대응", "얇은유지")
P192 = (W.U1 - W.U0) / 192.0
THIN = 4


def masks_of(case):
    """`대조.build` 와 같은 앉히기 · 정렬 (타원 기본은 깊이맵을 안 쓴다)."""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    bs = H.CASES[case]["back_sign"]
    ms = {v: H.to_win(H.declutter(W.art_mask(os.path.join(base, f)))) for v, f in src.items()}
    p = H.align(ms, back_sign=bs)
    return H._warp(ms, p), bs


def ellipse_in(box, shape, p=2.0):
    """상자 (x0, x1, y0, y1) 에 내접 타원 — `hull.superellipse` 와 같은 중심 · 반폭 규약."""
    x0, x1, y0, y1 = box
    a, b = (x1 - x0) / 2, (y1 - y0) / 2
    ic, jc = x0 + a - 0.5, y0 + b - 0.5
    I, Jg = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1), indexing="ij")
    out = np.zeros(shape, bool)
    out[x0:x1, y0:y1] = (np.abs((I - ic) / a) ** p + np.abs((Jg - jc) / b) ** p) <= 1
    return out


def boxes(s):
    lab, _ = ndimage.label(s)
    return lab, [(sl[0].start, sl[0].stop, sl[1].start, sl[1].stop) for sl in ndimage.find_objects(lab)]


def section(plain, how):
    """높이마다 단면에 넣을 모양 E. how 는 판본 이름."""
    E = np.zeros_like(plain)
    zs = np.nonzero(plain.any((0, 1)))[0]
    B = {k: boxes(plain[:, :, k]) for k in zs} if how == "대응" else None
    for k in zs:
        s = plain[:, :, k]
        if how.startswith("묶기"):
            kk = int(how[3:])
            joined = ndimage.binary_closing(s, structure=np.ones((1, kk), bool)) | s     # 깊이(y) 축으로만 묶는다
            _, bx = boxes(joined)
            for bb in bx:
                E[:, :, k] |= ellipse_in(bb, s.shape)
            continue
        lab, bx = boxes(s)
        for idx, bb in enumerate(bx, 1):
            if how == "얇은유지" and min(bb[1] - bb[0], bb[3] - bb[2]) <= THIN:
                E[:, :, k] |= lab == idx                                                # 얇은 조각은 안 깎는다
                continue
            if how == "대응":
                best, area = bb, (bb[1] - bb[0]) * (bb[3] - bb[2])
                for kn in (k - 1, k + 1):
                    for nb in (B[kn][1] if kn in B else []):
                        inside = nb[0] <= bb[0] + 1 and nb[1] >= bb[1] - 1 and nb[2] <= bb[2] + 1 and nb[3] >= bb[3] - 1
                        na = (nb[1] - nb[0]) * (nb[3] - nb[2])
                        if inside and na > area:
                            best, area = nb, na
                bb = best
            E[:, :, k] |= ellipse_in(bb, s.shape)
    return E


def carve(masks, bs, how):
    plain, axes = H.carve(masks, back_sign=bs)
    E = None if how == "기본" else section(plain, how)
    deps = H.ellipse_depths(plain, axes, bs, E=E)
    vox, _ = H.carve_depth(masks, deps, lam=H.DEPTH_LAM, back_sign=bs)
    return plain, vox, axes


def scorer(truth):
    g = {}
    for tag, p in (("", J.PITCH), ("·192", P192)):
        T, ot = J.grid(truth, p)
        g[tag] = (p, fill_slices(T), ot)

    def score(mesh):
        out = {}
        for tag, (p, F, ot) in g.items():
            G, og = J.grid(mesh, p)
            A, B_ = J.common(F, ot, G, og)
            out[tag] = round(float((A & B_).sum() / max((A | B_).sum(), 1)), 5)
        return out
    return score


def one(c):
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
    score = scorer(truth)
    masks, bs = masks_of(c)
    row = {"case": c, "판": TAG}
    for how in VARS:
        _, vox, axes = carve(masks, bs, how)
        s = score(O.C.to_mesh(vox, axes))
        row[how] = {"iou": s[""], "iou192": s["·192"], "조각": SF.pieces(vox), "얇은판": round(thin_share(vox), 5)}
    row["초"] = round(time.time() - t0, 1)
    return row


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[r["case"]] = r
    return out


def pipe(r):
    sb = {x["case"]: x for x in map(json.loads, open(os.path.join(HERE, "out", "기록", "점수판_진행.jsonl"), encoding="utf-8"))}
    return abs(r["기본"]["iou"] - sb[r["case"]]["새"][1])


def judge():
    rs = rows()
    cs = [c for c in bench_cases() if c != "소체"]
    if any(c not in rs for c in cs):
        return {"판정": "%d/%d 장 — 판정 안 함" % (len(rs), len(cs))}
    R = [rs[c] for c in cs]
    out = {"판": TAG, "장": len(R), "배관 최대차": round(max(pipe(r) for r in R), 6)}
    if out["배관 최대차"] >= 1e-4:
        out["배관"] = "어긋남 — 숫자를 버린다"
        return out
    out["배관"] = "통과"
    base = {k: np.array([r["기본"][k] for r in R]) for k in ("iou", "iou192")}
    pieces0 = sum(r["기본"]["조각"] for r in R)
    thin0 = {r["case"]: r["기본"]["얇은판"] for r in R}
    ok = []
    for how in VARS[1:]:
        d = {k: np.array([r[how][k] for r in R]) - base[k] for k in ("iou", "iou192")}
        c1 = all(float(np.median(d[k])) >= 0 and float(d[k].min()) >= -0.01 for k in d)
        c2 = all(rs[c][how]["얇은판"] <= 0.5 * thin0[c] for c in ("cloak_Chest_Closed_AngpV0HxD8", "wizard_Wizard_o87Upt5uHX"))
        pieces = sum(r[how]["조각"] for r in R)
        c3 = pieces <= pieces0
        out[how] = {"128 중앙 · 차 중앙 · 최저": [round(float(np.median(base["iou"] + d["iou"])), 4), round(float(np.median(d["iou"])), 4), round(float(d["iou"].min()), 4)],
                    "192 차 중앙 · 최저": [round(float(np.median(d["iou192"])), 4), round(float(d["iou192"].min()), 4)],
                    "오른 장 · 떨어진 장 (128)": [int((d["iou"] > 0.0005).sum()), int((d["iou"] < -0.0005).sum())],
                    "얇은판 궤짝 · 로봇형 마법사": [rs["cloak_Chest_Closed_AngpV0HxD8"][how]["얇은판"], rs["wizard_Wizard_o87Upt5uHX"][how]["얇은판"]],
                    "조각 합": pieces, "① 안 떨어짐": c1, "② 판 줄음": c2, "③ 안 깨짐": c3}
        if c1 and c2 and c3:
            ok.append((float(np.median(base["iou"] + d["iou"])), how))
    out["기본 128 중앙 · 조각 합 · 얇은판 궤짝·로봇형 마법사"] = [round(float(np.median(base["iou"])), 4), pieces0,
                                                         [thin0["cloak_Chest_Closed_AngpV0HxD8"], thin0["wizard_Wizard_o87Upt5uHX"]]]
    out["다음"] = ("%s 를 새 기본으로" % max(ok)[1]) if ok else "기본 그대로 — 결과만 적는다"
    return out


FIG = ("wizard_Wizard_o87Upt5uHX", "cloak_Chest_Closed_AngpV0HxD8", "cloak_Chest_O72u4Drp8k", "mech_Drill_8uBbH7Dvmb",
       "wizard_Evil_Wizard_bdxawstqtq", "hairsample_male")
FIG_VARS = ("기본", "묶기k3", "묶기k9", "대응", "얇은유지")


def figure(cases=FIG):
    """정답 · 기본 · 묶기k3 · 묶기k9 · 대응 · 얇은유지 — 같은 각도 · 같은 틀 · 같은 회색 (`점수판그림` 과 같은 그리기)."""
    import 속채움그림 as SC
    from 점수판그림 import FRONT_VIEW, SHAPE
    from 계획 import _font
    rs = rows()
    S, G, TOP, LW = SC.S, 14, 150, 250
    cols = ("정답 (GT)",) + FIG_VARS
    im = Image.new("RGB", (LW + len(cols) * (S + G) + 20, TOP + len(cases) * (S + G) + 20), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 14), "단면 조각 묶기 — 얇은 판 없애기 (타원 lam 1.00, 넣는 단위만 다르다)", font=_font(30), fill=(20, 20, 20))
    d.text((24, 58), "기본 = 조각마다 타원 · 묶기k = 깊이 축 k 칸 틈을 묶고 타원 · 대응 = 위아래 높이의 큰 조각 상자로 · 얇은유지 = 두께 4 칸 이하 조각은 안 깎음",
           font=_font(17), fill=(90, 90, 90))
    d.text((24, 84), "숫자 = 속 채운 정답 IoU (격자 128) · 조각 수 · 같은 각도(앞 · 오른쪽 · 위) · 자르지 않음", font=_font(17), fill=(90, 90, 90))
    for i, name in enumerate(cols):
        d.text((LW + i * (S + G) + S // 2 - 45, TOP - 32), name, font=_font(21), fill=(30, 30, 30))
    SC.VIEW = FRONT_VIEW
    for r, c in enumerate(cases):
        y = TOP + r * (S + G)
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        masks, bs = masks_of(c)
        grids = [J.grid(truth)]
        for how in FIG_VARS:
            _, vox, axes = carve(masks, bs, how)
            grids.append(J.grid(O.C.to_mesh(vox, axes)))
        lo = np.minimum.reduce([o for _, o in grids])
        hi = np.maximum.reduce([o + g.shape for g, o in grids])
        full = []
        for g, o in grids:
            a = np.zeros(hi - lo + 2, bool)
            a[tuple(slice(o[i] - lo[i] + 1, o[i] - lo[i] + 1 + g.shape[i]) for i in range(3))] = g
            full.append(a)
        r_, u_, _ = SC.basis()
        pts = np.argwhere(np.logical_or.reduce(full))
        X, Y = pts @ r_, pts @ u_
        span = max(np.ptp(X), np.ptp(Y)) * 1.06
        frame = (((X.max() + X.min()) / 2 - span / 2, (Y.max() + Y.min()) / 2 - span / 2), span)
        d.text((24, y + S // 2 - 20), c[:24], font=_font(17), fill=(30, 30, 30))
        for i, a in enumerate(full):
            t = SC.paint([(a, SHAPE)], frame)
            x = LW + i * (S + G)
            im.paste(Image.fromarray(cv2.cvtColor(t, cv2.COLOR_BGR2RGB)), (x, y))
            if i and c in rs:
                m = rs[c][FIG_VARS[i - 1]]
                d.text((x + 6, y + S - 22), "%.3f · 조각 %d" % (m["iou"], m["조각"]), font=_font(16), fill=(40, 40, 40))
        print("  %s 그림" % c, flush=True)
    p = os.path.join(HERE, "out", "조각묶기그림.png")
    im.save(p)
    print("  -> %s" % p)


def selfcheck():
    # 1 깊이(y) 1 칸 틈으로 갈린 단면 — 묶기k3 는 하나의 타원 (가운데를 지난다), 기본 규칙은 조각 둘
    v = np.zeros((20, 21, 3), bool)
    v[2:18, 2:10, 1] = v[2:18, 11:19, 1] = True
    E = section(v, "묶기k3")
    assert E[10, 10, 1] and ndimage.label(E[:, :, 1])[1] == 1, "묶기가 틈 너머로 안 이었다"
    assert ndimage.label(v[:, :, 1])[1] == 2
    # 2 가로(x) 틈은 안 잇는다 — 다리 사이
    w = np.zeros((21, 20, 3), bool)
    w[2:10, 2:18, 1] = w[11:19, 2:18, 1] = True
    assert ndimage.label(section(w, "묶기k9")[:, :, 1])[1] == 2, "가로 틈까지 이었다"
    # 3 얇은유지 — 두께 3 칸 조각은 조각 그대로
    t = np.zeros((20, 20, 3), bool)
    t[2:18, 5:8, 1] = True
    assert np.array_equal(section(t, "얇은유지")[:, :, 1], t[:, :, 1]), "얇은 조각을 깎았다"
    # 4 대응 — 얇은 띠가 위 높이의 큰 조각 상자 안에 있으면 그 상자로
    q = np.zeros((20, 20, 3), bool)
    q[2:18, 2:18, 0] = True
    q[2:18, 16:18, 1] = True
    Eq = section(q, "대응")
    assert Eq[10, 10, 1], "대응이 큰 조각 상자를 안 썼다"
    print("  자가검사 통과 — 묶기(깊이 축만) · 얇은유지 · 대응")


def main():
    H.register_sheets()
    selfcheck()
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        return
    if a == "그림":
        return figure()
    if a != "판정":
        done = rows()
        order = ["cloak_Chest_Closed_AngpV0HxD8"] + [c for c in bench_cases() if c not in ("소체", "cloak_Chest_Closed_AngpV0HxD8")]
        for c in [c for c in order if c not in done][:int(a)]:
            r = one(c)
            with open(PROG, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print("  %-28s 배관차 %.6f · " % (c[:28], pipe(r)) + " · ".join("%s %.3f/%d/%.4f" % (k, r[k]["iou"], r[k]["조각"], r[k]["얇은판"]) for k in VARS)
                  + " · %.0f초" % r["초"], flush=True)
            if pipe(r) >= 1e-4:
                print("  배관 어긋남 — 멈춘다")
                return
        print("  %d/28 장" % len(rows()))
    if a == "판정" or len(rows()) >= 28:
        v = judge()
        print(json.dumps(v, ensure_ascii=False, indent=1))
        p = os.path.join(HERE, "out", "기록", "조각묶기_%s.json" % time.strftime("%Y%m%d_%H%M"))
        json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  -> %s" % p)


if __name__ == "__main__":
    main()
