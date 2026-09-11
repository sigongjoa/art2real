# -*- coding: utf-8 -*-
"""**남은 줄무늬 = hull 의 칸 계단.** 최종 메시를 Taubin 으로 다듬어 본다 -> out/메시스무딩_<케이스>.png

    python 메시스무딩.py <벤치lam4.jsonl> 케이스

면 스무딩(`hull.ZSMOOTH`)은 깎기가 만든 찢김만 편다. 45도에서 보이는 줄무늬 상당수는 이진 hull 에도
있다 — 줄마다 직사각형 단면의 모서리가 칸 단위로 들쭉날쭉해서. Taubin(λ 0.5 · μ −0.53)은 부피를 거의
보존하며 꼭짓점을 조금씩 옮긴다. 잰다:
    IoU          정답 대비 (대조군도 같은 반복으로 다듬는다)
    실루엣       다듬기 전 hull 실루엣 대비 **잃은 것 · 튀어나온 것** (정면·측면·후면 중 큰 쪽)
    이동         꼭짓점 최대 이동 (칸) — 한 칸 안이면 계단만 편 것"""
import json
import os
import sys

import numpy as np
import trimesh

SCR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCR)
import 벤치smooth as BS
import 벤치그림 as RG
from PIL import Image, ImageDraw
from 계획 import _font

O, H, W = BS.O, BS.O.H, BS.O.W
ITERS = (0, 10, 30)


def main():
    rows = {json.loads(l)["case"]: json.loads(l) for l in open(sys.argv[1], encoding="utf-8")}
    case = sys.argv[2]
    O.H.register_sheets()
    H.ZSMOOTH = 2.0                                     # 찢김은 면 스무딩으로 먼저 편다
    truth = trimesh.load(os.path.join(O.OUT, "시트", case, "truth.glb"), force="mesh")
    T, ot = O.J.grid(truth)
    bs = O.H.CASES[case]["back_sign"]

    def iou(m):
        G, og = O.J.grid(m)
        A, B = O.J.common(T, ot, G, og)
        return float((A & B).sum() / max((A | B).sum(), 1))

    plain, p20, axes, _ = O.build(case, truth, 0.20, "파이프")
    o50 = O.build(case, truth, 0.50, "오라클")[1]
    keep = H.sdf_of(plain)
    du = axes[0][1] - axes[0][0]
    base = {"이진": BS.mesh(keep, axes), "대조군": BS.mesh(keep - rows[case]["t"]["파이프0.20"], axes),
            "파이프0.20": BS.mesh(H.sdf_of(p20), axes), "오라클0.50": BS.mesh(H.sdf_of(o50), axes)}
    ref = {v: np.asarray(W.silhouette(np.asarray(base["이진"].vertices), np.asarray(base["이진"].faces), v,
                                      bs if v == "back" else None)).astype(bool) for v in W.VIEWS}
    res, meshes = {}, {}
    print("  %s  (면 스무딩 σ2 위에 Taubin · 실루엣은 다듬기 전 hull 대비)" % case)
    for it in ITERS:
        for k, m0 in base.items():
            m = m0.copy()
            if it:
                trimesh.smoothing.filter_taubin(m, lamb=0.5, nu=0.53, iterations=it)
            mv = float(np.linalg.norm(np.asarray(m.vertices) - np.asarray(m0.vertices), axis=1).max() / du)
            lost = gain = 0.0
            for v in W.VIEWS:
                s = np.asarray(W.silhouette(np.asarray(m.vertices), np.asarray(m.faces), v,
                                            bs if v == "back" else None)).astype(bool)
                a = ref[v]
                lost = max(lost, (a & ~s).sum() / max(a.sum(), 1))
                gain = max(gain, (s & ~a).sum() / max(a.sum(), 1))
            res[(k, it)] = (iou(m), lost, gain, mv)
            meshes[(k, it)] = m
        c = res[("대조군", it)][0]
        for k in base:
            x, lost, gain, mv = res[(k, it)]
            print("    Taubin %2d  %-10s IoU %.4f%s · 실루엣 잃음 %.2f%% 튀어나옴 %.2f%% · 최대 이동 %.2f칸"
                  % (it, k, x, "" if k in ("이진", "대조군") else " (대조 %+.4f)" % (x - c),
                     100 * lost, 100 * gain, mv), flush=True)
    H.ZSMOOTH = 0.0
    R = RG.rot(np.asarray(base["이진"].vertices))
    lo, hi = R.min(0), R.max(0)
    span = max(hi[0] - lo[0], hi[2] - lo[2]) * 1.04
    frame = ((lo[0] + hi[0]) / 2 - span / 2, (lo[2] + hi[2]) / 2 - span / 2), span
    S, G, LW, TOP = 300, 10, 130, 84
    tint = {"이진": RG.TINT["이진 hull"], "대조군": RG.TINT["대조군"], "파이프0.20": RG.TINT["파이프0.20"],
            "오라클0.50": RG.TINT["오라클0.50"]}
    im = Image.new("RGB", (LW + (len(ITERS) + 1) * (S + G) + G, TOP + len(base) * (S + 48)), "white")
    d = ImageDraw.Draw(im)
    f1, f2, f3 = _font(22), _font(15), _font(12)
    d.text((16, 12), "%s — 면 스무딩 σ2 + Taubin 0·10·30회 · 45도" % case, fill=(20, 20, 20), font=f1)
    d.text((16, 44), "실루엣 = 다듬기 전 hull 대비 잃은 몫 / 튀어나온 몫 · 이동 = 꼭짓점 최대 이동 (칸)", fill=(90, 90, 90), font=f3)
    d.text((LW + G, TOP - 22), "정답", fill=(40, 40, 40), font=f2)
    for c, it in enumerate(ITERS):
        d.text((LW + G + (c + 1) * (S + G), TOP - 22), "Taubin %d회" % it, fill=(40, 40, 40), font=f2)
    im.paste(Image.fromarray(RG.render(truth, frame, S, RG.TINT["정답"])), (LW + G, TOP))
    for i, k in enumerate(base):
        y0 = TOP + i * (S + 48)
        d.text((12, y0 + S // 2), k, fill=(20, 20, 20), font=f2)
        for c, it in enumerate(ITERS):
            x0 = LW + G + (c + 1) * (S + G)
            im.paste(Image.fromarray(RG.render(meshes[(k, it)], frame, S, tint[k])), (x0, y0))
            x, lost, gain, mv = res[(k, it)]
            dv = x - res[("대조군", it)][0]
            l1 = "IoU %.4f" % x + ("" if k in ("이진", "대조군") else "  (대조 %+.4f)" % dv)
            l2 = "실루엣 −%.2f%% +%.2f%% · 이동 %.2f칸" % (100 * lost, 100 * gain, mv)
            col = (60, 60, 60) if k in ("이진", "대조군") else (30, 130, 70) if dv > 0 else (190, 60, 40)
            d.text((x0, y0 + S + 4), l1, fill=col, font=f3)
            d.text((x0, y0 + S + 22), l2, fill=(90, 90, 90), font=f3)
    p = os.path.join(RG.HERE, "out", "메시스무딩_%s.png" % case)
    im.save(p)
    print("  ->", p)


if __name__ == "__main__":
    main()
