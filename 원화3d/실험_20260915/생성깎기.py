# -*- coding: utf-8 -*-
"""**생성 앞단 + 3판 깎기** (시험 B · 2026-09-15).

    python 생성깎기.py 검사                  자가검사만
    python 생성깎기.py 잰다 [케이스...]       -> out/기록/생성깎기_진행.jsonl
    python 생성깎기.py 그림 [케이스...]       정답 · 지금 기본 · 생성 · 생성∩hull · +보충 · 천장 -> out/생성깎기그림.png

판정은 `claudedocs/plan_생성깎기_20260915.md` 그대로다. 사용자 결정: TripoSG 를 앞단에 두고 깎아 나간다.
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
import 오라클 as O
import 정답 as J
import 표면 as SF
import win as W
from 겉면채점 import fill_slices
import 생성3D as G3

PROG = os.path.join(HERE, "out", "기록", "생성깎기_진행.jsonl")
VARS = ("생성", "생성∩hull", "생성∩hull+보충")
P192 = (W.U1 - W.U0) / 192.0


def build(case):
    """마스크 · 이진 hull · 지금 기본(타원 lam1.00) — `대조.build` 와 같은 격자."""
    masks = G3.art_masks(case)
    bs = H.CASES[case]["back_sign"]
    plain, axes = H.carve(masks, back_sign=bs)
    deps = {v: np.ones((W.RES, W.RES), np.float32) for v in W.VIEWS}
    base, _ = H.carve_default(masks, deps, back_sign=bs)
    return masks, bs, plain, base, axes


def voxelize(mesh, axes):
    """메시 -> hull 격자 (N×N×N). 복셀 중심이 메시 속이면 참. `정답.grid` 로 굽고 hull 격자 중심에 옮긴다."""
    u, _, z = axes
    p = u[1] - u[0]
    Gd, og = J.grid(mesh, p)
    out = np.zeros((len(u), len(u), len(z)), bool)
    idx = [np.rint((np.arange(Gd.shape[i]) + og[i]) * p / p).astype(int) for i in range(3)]
    gx = np.rint((idx[0] * p - u[0]) / p).astype(int)
    gy = np.rint((idx[1] * p - u[0]) / p).astype(int)
    gz = np.rint((idx[2] * p - z[0]) / p).astype(int)
    xs, ys, zs = np.nonzero(Gd)
    X, Y, Z = gx[xs], gy[ys], gz[zs]
    ok = (X >= 0) & (X < len(u)) & (Y >= 0) & (Y < len(u)) & (Z >= 0) & (Z < len(z))
    out[X[ok], Y[ok], Z[ok]] = True
    return out


def fill_gaps(gh, base, plain):
    """깎은 생성이 원화 실루엣을 비운 곳 — 정면(x,z) · 측면(y,z) 투영이 hull 에는 있고 gh 에는 없는 칸의 광선 위에 지금 기본 복셀을 더한다."""
    out = gh.copy()
    miss_f = plain.any(1) & ~gh.any(1)              # (x, z)
    miss_s = plain.any(0) & ~gh.any(0)              # (y, z)
    out |= base & miss_f[:, None, :]
    out |= base & miss_s[None, :, :]
    return out


def variants(case):
    masks, bs, plain, base, axes = build(case)
    g = trimesh.load(os.path.join(G3.GEN, G3.MODEL, case + ".glb"), force="mesh")
    _, V, yaw, mir = G3.orient(g.vertices, masks)
    V = G3.fit_to_art(V, masks)
    gen = voxelize(trimesh.Trimesh(V, np.asarray(g.faces), process=False), axes)
    gh = gen & plain
    return {"지금 기본": base, "생성": gen, "생성∩hull": gh, "생성∩hull+보충": fill_gaps(gh, base, plain)}, plain, axes, masks, bs


def sil_fit(vox, masks, bs, axes):
    """복셀 실루엣 대 원화 마스크 — 못덮음 · 넘침 (정면 · 측면). 복셀 중심을 창 화소로 찍는다."""
    u, _, z = axes
    out = {}
    for view, ax in (("front", 1), ("side", 0)):
        proj = vox.any(ax)                           # front: (x, z) · side: (y, z)
        g = np.zeros((W.RES, W.RES), np.uint8)
        a, b = np.nonzero(proj)
        py, px = W.topix(W.VIEW_AXIS[view][1] * u[a], z[b])
        g[py, px] = 1
        s = cv2.dilate(g, np.ones((5, 5), np.uint8)).astype(bool)
        m = masks[view]
        out["못덮음_" + view] = round(float((m & ~s).sum() / max(m.sum(), 1)), 4)
        out["넘침_" + view] = round(float((s & ~m).sum() / max(s.sum(), 1)), 4)
    return out


def measure(cases):
    for c in cases:
        t0 = time.time()
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        grids = {tag: (p, *J.grid(truth, p)) for tag, p in (("", J.PITCH), ("·192", P192))}
        vs, plain, axes, masks, bs = variants(c)
        row = {"case": c, "판": "생성깎기 v2 · 원형도 속채움 · TripoSG 3판맞춤 · ∩hull · +보충 · 속채운 정답 (2026-09-15)"}
        for name, vox in vs.items():
            mesh = O.C.to_mesh(vox, axes)
            r = {"조각": SF.pieces(vox)}
            for tag, (p, T, ot) in grids.items():
                Gd, og = J.grid(mesh, p)
                # 원형도 같은 규칙으로 속을 채운다 — 생성 메시는 치마 · 뚜껑이 속 빈 껍질로 나올 수 있다 (09-15 사후: avatarsample_g 모양은 맞는데 IoU 가 낮았다)
                A, B = J.common(fill_slices(T), ot, fill_slices(Gd), og)
                r["iou" + tag] = round(float((A & B).sum() / max((A | B).sum(), 1)), 5)
            r.update(sil_fit(vox, masks, bs, axes))
            row[name] = r
        row["초"] = round(time.time() - t0, 1)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print("  %-26s " % c[:26] + " · ".join("%s %.3f/%.3f 조각%d 넘침f%.3f s%.3f" % (k, v["iou"], v["iou·192"], v["조각"], v["넘침_front"], v["넘침_side"])
                                             for k, v in row.items() if isinstance(v, dict)) + " · %.0f초" % row["초"], flush=True)


def figure(cases):
    import 속채움그림 as SC
    from 점수판그림 import FRONT_VIEW, SHAPE
    from 계획 import _font
    rows = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            rows[r["case"]] = r
    S, Gp, TOP, LW = SC.S, 14, 140, 250
    cols = ("정답 (GT)", "지금 기본", "생성", "생성∩hull", "생성∩hull+보충", "천장")
    im = Image.new("RGB", (LW + len(cols) * (S + Gp) + 20, TOP + len(cases) * (S + Gp) + 20), "white")
    d = ImageDraw.Draw(im)
    d.text((24, 14), "TripoSG 를 앞단에 두고 원화 3판으로 깎는다", font=_font(30), fill=(20, 20, 20))
    d.text((24, 58), "생성 = TripoSG(정면 한 장) 을 원화 폭 · 깊이에 맞춤 · ∩hull = 원화 실루엣 밖을 깎음 · +보충 = 원화 실루엣이 비는 곳만 지금 기본으로 채움",
           font=_font(17), fill=(90, 90, 90))
    d.text((24, 84), "같은 각도 · 같은 틀 · 자르지 않음 · 숫자 = 속 채운 정답 IoU (격자 128)", font=_font(17), fill=(90, 90, 90))
    for i, n in enumerate(cols):
        d.text((LW + i * (S + Gp) + S // 2 - 60, TOP - 30), n, font=_font(20), fill=(30, 30, 30))
    SC.VIEW = FRONT_VIEW
    bn = {r["case"]: r for r in map(json.loads, open(os.path.join(HERE, "out", "기록", "겉면채점_벤치_진행.jsonl"), encoding="utf-8"))}
    for rr, c in enumerate(cases):
        y = TOP + rr * (S + Gp)
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        vs, plain, axes, masks, bs = variants(c)
        _, ora, ax3, _ = O.build(c, truth, 1.00, "오라클")
        meshes = [truth] + [O.C.to_mesh(vs[k], axes) for k in ("지금 기본",) + VARS] + [O.C.to_mesh(ora, ax3)]
        grids = [J.grid(m) for m in meshes]
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
        row = rows.get(c, {})
        labels = [""] + ["%.3f" % row[k]["iou"] if k in row else "" for k in ("지금 기본",) + VARS] + ["%.3f" % bn[c]["오라클1.00"][1]]
        for i, a in enumerate(full):
            t = SC.paint([(a, SHAPE)], frame)
            x = LW + i * (S + Gp)
            im.paste(Image.fromarray(cv2.cvtColor(t, cv2.COLOR_BGR2RGB)), (x, y))
            if labels[i]:
                d.text((x + 8, y + S - 24), labels[i], font=_font(18), fill=(40, 40, 40))
        print("  %s 그림" % c, flush=True)
    p = os.path.join(HERE, "out", "생성깎기그림.png")
    im.save(p)
    print("  -> %s" % p)


def selfcheck():
    plain = np.zeros((10, 10, 10), bool)
    plain[2:8, 2:8, 2:8] = True
    base = plain.copy()
    gh = np.zeros_like(plain)
    gh[2:8, 2:5, 2:8] = True                         # 앞 절반만 — 정면 투영은 다 덮고 측면(y 5..7)이 빈다
    f = fill_gaps(gh, base, plain)
    assert f[4, 6, 4] and not f[0, 0, 0] and f.sum() == plain.sum(), "보충이 측면 빈 곳을 못 채웠다 (%d)" % f.sum()
    print("  자가검사 통과 — 보충")


if __name__ == "__main__":
    a = sys.argv[1:]
    H.register_sheets()
    selfcheck()
    if a[:1] == ["잰다"]:
        measure(a[1:] or G3.PILOT)
    elif a[:1] == ["그림"]:
        figure(a[1:] or G3.PILOT)
