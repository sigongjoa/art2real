# -*- coding: utf-8 -*-
"""**로컬 3D 생성 모델을 같은 벤치에** (시험 A · 2026-09-15).

    python 생성3D.py 검사                  자가검사만
    python 생성3D.py 잰다 [케이스...]       out/생성3D/<모델>/<케이스>.glb 를 채점 -> out/기록/생성3D_진행.jsonl
    python 생성3D.py 그림 [케이스...]       정답 · 지금 기본 · TripoSG · 천장 -> out/생성3D그림.png

판정은 `claudedocs/plan_로컬생성3D_20260915.md` 그대로다.
**정렬은 정답을 안 본다** — 수직축 4방향 × 좌우 반전 중 원화 정면 · 측면 마스크(파이프라인 입력)와 실루엣이 가장 맞는 것.
"""
import json
import os
import sys
import time

import cv2
import numpy as np
import trimesh
from PIL import Image, ImageDraw

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260915"))
os.chdir(HERE)
import hull as H
import 대조 as C
import 오라클 as O
import 정답 as J
import 표면 as SF
import win as W
from 겉면채점 import fill_slices

GEN = os.path.join(HERE, "out", "생성3D")
PROG = os.path.join(HERE, "out", "기록", "생성3D_진행.jsonl")
MODEL = "triposg"
PILOT = ("avatarsample_g", "wizard_Evil_Wizard_bdxawstqtq", "cloak_Chest_Closed_AngpV0HxD8", "mech_Drill_8uBbH7Dvmb")
P192 = (W.U1 - W.U0) / 192.0
K5 = np.ones((5, 5), np.uint8)


def art_masks(case):
    """파이프라인 입력과 같은 창 마스크 (앉히기 · 정렬까지)."""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    ms = {v: H.to_win(H.declutter(W.art_mask(os.path.join(base, f)))) for v, f in src.items()}
    p = H.align(ms, back_sign=H.CASES[case]["back_sign"])
    return H._warp(ms, p)


def splat(V, view, sign=None):
    """조밀한 생성 메시(정점 수백만)는 삼각형 대신 **정점을 찍고 닫는다** — 실루엣이 거의 같고 수백 배 빠르다."""
    a, s0 = W.VIEW_AXIS[view]
    py, px = W.topix((s0 if sign is None else sign) * V[:, a], V[:, 2])
    g = np.zeros((W.RES, W.RES), np.uint8)
    ok = (py >= 0) & (py < W.RES) & (px >= 0) & (px < W.RES)
    g[py[ok], px[ok]] = 1
    return cv2.morphologyEx(g, cv2.MORPH_CLOSE, K5).astype(bool)


def orient(V0, masks):
    """glTF(y 위) -> 창(x 가로 · y 깊이 · z 위). 수직축 4방향 × 좌우 반전 중 정면 + 측면 실루엣 IoU 합이 가장 큰 것."""
    base = W.to_world(np.asarray(V0, np.float64), "xyz")
    best = None
    for k in range(4):
        c, s = np.cos(k * np.pi / 2), np.sin(k * np.pi / 2)
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        for mir in (1, -1):
            V = W.normalize(base @ R.T * np.array([mir, 1, 1]))
            sc = W.iou(splat(V, "front"), masks["front"]) + W.iou(splat(V, "side"), masks["side"])
            if best is None or sc > best[0]:
                best = (sc, V, k * 90, mir)
    return best


def fit_to_art(V, masks):
    """**3판맞춤 (정답 안 봄).** 가로(x)는 원화 정면 실루엣의 폭 · 자리, 깊이(y)는 원화 측면 실루엣의 폭 · 자리에 맞춰 늘이고 옮긴다.
    단일 이미지 모델은 두께를 추측한다 — 그 두께를 원화 측면이 말하는 두께로 바꾸는 것뿐이다. 키(z)는 `normalize` 그대로."""
    V = V.copy()
    for axis, view in ((0, "front"), (1, "side")):
        cols = np.nonzero(masks[view].any(0))[0]
        if len(cols) == 0:
            continue
        sign = W.VIEW_AXIS[view][1]
        ulo, uhi = sorted(sign * (W.U0 + (np.array([cols.min(), cols.max() + 1])) / W.RES * (W.U1 - W.U0)))
        lo, hi = V[:, axis].min(), V[:, axis].max()
        V[:, axis] = ulo + (V[:, axis] - lo) / max(hi - lo, 1e-9) * (uhi - ulo)
    return V


def score(case, mesh_path, fit=False):
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    g = trimesh.load(mesh_path, force="mesh")
    masks = art_masks(case)
    sc, V, yaw, mir = orient(g.vertices, masks)
    if fit:
        V = fit_to_art(V, masks)
    m = trimesh.Trimesh(V, np.asarray(g.faces), process=False)
    row = {"case": case, "모델": MODEL + ("·3판맞춤" if fit else ""), "회전": yaw, "반전": mir, "정렬점수": round(float(sc), 4), "면": int(len(g.faces))}
    for tag, p in (("", J.PITCH), ("·192", P192)):
        T, ot = J.grid(truth, p)
        G, og = J.grid(m, p)
        A, B = J.common(fill_slices(T), ot, G, og)
        row["iou" + tag] = round(float((A & B).sum() / max((A | B).sum(), 1)), 5)
        if not tag:
            row["조각"] = SF.pieces(G, minv=50)
    bs = H.CASES[case]["back_sign"]
    for v in W.VIEWS:
        s = splat(V, v, bs if v == "back" else None)
        a = masks[v]
        row["못덮음_" + v] = round(float((a & ~s).sum() / max(a.sum(), 1)), 4)
        row["넘침_" + v] = round(float((s & ~a).sum() / max(s.sum(), 1)), 4)
    return row, m


def measure(cases, fit=False):
    sb = {r["case"]: r for r in map(json.loads, open(os.path.join(HERE, "out", "기록", "점수판_진행.jsonl"), encoding="utf-8"))}
    bn = {r["case"]: r for r in map(json.loads, open(os.path.join(HERE, "out", "기록", "겉면채점_벤치_진행.jsonl"), encoding="utf-8"))}
    for c in cases:
        path = os.path.join(GEN, MODEL, c + ".glb")
        if not os.path.exists(path):
            print("  %s — 생성 메시 없음" % c)
            continue
        t0 = time.time()
        row, _ = score(c, path, fit=fit)
        row["지금기본"], row["천장"] = sb[c]["새"][1], bn[c]["오라클1.00"][1]
        row["초"] = round(time.time() - t0, 1)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print("  %-28s TripoSG %.3f (192 %.3f) · 지금 기본 %.3f · 천장 %.3f · 조각 %d · 회전 %d 반전 %d · 못덮음 f%.3f s%.3f · 넘침 f%.3f s%.3f · %.0f초" % (
            c[:28], row["iou"], row["iou·192"], row["지금기본"], row["천장"], row["조각"], row["회전"], row["반전"],
            row["못덮음_front"], row["못덮음_side"], row["넘침_front"], row["넘침_side"], row["초"]), flush=True)


def figure(cases):
    import 속채움그림 as SC
    from 점수판그림 import FRONT_VIEW, SHAPE
    from 계획 import _font
    rows = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            rows[r["case"]] = r
    S, G, TOP, LW = SC.S, 16, 140, 250
    cols = ("정답 (GT)", "지금 기본", "TripoSG (로컬)", "천장")
    im = Image.new("RGB", (LW + len(cols) * (S + G) + 20, TOP + len(cases) * (S + G) + 20), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 14), "정답 · 지금 파이프라인 · 로컬 생성 모델(TripoSG) · 천장", font=_font(30), fill=(20, 20, 20))
    d.text((24, 58), "같은 각도(앞 · 오른쪽 · 위) · 같은 틀 · 자르지 않음 · 숫자 = 속 채운 정답 IoU (격자 128)", font=_font(18), fill=(90, 90, 90))
    d.text((24, 84), "TripoSG 는 정면 한 장만 본다 · 방향은 원화 정면 · 측면 실루엣으로만 맞췄다 (정답 안 봄)", font=_font(18), fill=(90, 90, 90))
    for i, n in enumerate(cols):
        d.text((LW + i * (S + G) + S // 2 - 60, TOP - 30), n, font=_font(21), fill=(30, 30, 30))
    SC.VIEW = FRONT_VIEW
    for r, c in enumerate(cases):
        y = TOP + r * (S + G)
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        _, new, ax, _ = C.build(c)
        _, ora, ax3, _ = O.build(c, truth, 1.00, "오라클")
        _, gm = score(c, os.path.join(GEN, MODEL, c + ".glb"))
        grids = [J.grid(truth), J.grid(O.C.to_mesh(new, ax)), J.grid(gm), J.grid(O.C.to_mesh(ora, ax3))]
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
        d.text((24, y + S // 2 - 30), c[:24], font=_font(17), fill=(30, 30, 30))
        rr = rows.get(c, {})
        labels = ["", "%.3f" % rr.get("지금기본", float("nan")), "%.3f" % rr.get("iou", float("nan")), "%.3f" % rr.get("천장", float("nan"))]
        for i, a in enumerate(full):
            t = SC.paint([(a, SHAPE)], frame)
            x = LW + i * (S + G)
            im.paste(Image.fromarray(cv2.cvtColor(t, cv2.COLOR_BGR2RGB)), (x, y))
            if labels[i]:
                d.text((x + 8, y + S - 24), labels[i], font=_font(18), fill=(40, 40, 40))
        print("  %s 그림" % c, flush=True)
    p = os.path.join(HERE, "out", "생성3D그림.png")
    im.save(p)
    print("  -> %s" % p)


def selfcheck():
    # 정렬 — 상자를 90도 돌려 넣으면 원래 방향을 되찾는다 (정면이 가로로 긴 상자)
    box = trimesh.creation.box((0.6, 1.0, 0.3))          # glTF: x 가로 0.6 · y 위 1.0 · z 깊이 0.3
    masks = {"front": splat(W.normalize(W.to_world(np.asarray(box.vertices), "xyz")), "front"),
             "side": splat(W.normalize(W.to_world(np.asarray(box.vertices), "xyz")), "side")}
    Vr = np.asarray(box.vertices) @ np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]]).T   # y 축 90도
    sc, V, yaw, mir = orient(Vr, masks)
    assert sc > 1.9, "돌린 상자를 되찾지 못했다 (%.3f · %d)" % (sc, yaw)
    print("  자가검사 통과 — 방향 되찾기 (점수 %.3f · 회전 %d)" % (sc, yaw))


if __name__ == "__main__":
    a = sys.argv[1:]
    H.register_sheets()
    selfcheck()
    if a[:1] == ["잰다"]:
        measure(a[1:] or PILOT)
    elif a[:1] == ["잰다맞춤"]:
        measure(a[1:] or PILOT, fit=True)
    elif a[:1] == ["그림"]:
        figure(a[1:] or PILOT)
