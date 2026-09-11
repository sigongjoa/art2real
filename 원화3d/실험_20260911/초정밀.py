# -*- coding: utf-8 -*-
"""**해상도 트랙 시연** — 거친 결은 최소 단위(칸 · 화소) 탓인가. 한 케이스로 네 판을 나란히.

    python 초정밀.py [케이스]      -> out/초정밀_<케이스>.png + 표

    정답
    0/1 hull              지금 파이프라인 (0/1 마스크 · 0/1 칸)
    연속장                 0/1 마스크의 2D 부호거리를 기둥으로 밀어 최솟값 (단위 큐브에 거리)
    연속장 + 덮임 비율      `시트.py --초정밀` 의 알파(가장자리 화소에 덮인 비율)로 화소보다 촘촘한
                          부호거리 · 기둥 표본은 쌍선형 보간 (정수 화소로 안 자른다)

잰다: 정답 IoU (격자128) · 챔퍼 (정답 표면까지, 키 단위) · **계단 거칠기** = 꼭짓점이 이웃 평균에서
떨어진 거리 (칸 단위, 중앙값) — 찢김(>3칸)은 못 보는 한 칸 안쪽의 결을 재려고 둔다."""
import json
import os
import subprocess
import sys

import cv2
import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy import ndimage

SCR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCR)
import 벤치smooth as BS                                # cwd -> 원화3d · 오라클 을 부른다
import 벤치그림 as RG
from 계획 import _font

O, H, W = BS.O, BS.O.H, BS.O.W
import 표면 as SF
PX = W.RES / (W.Z1 - W.Z0) * (W.U1 - W.U0) / H.N    # 칸 하나 = 4 화소


def rough(m, du):
    """꼭짓점이 이웃 평균에서 떨어진 거리의 중앙값 (칸). 매끈한 면일수록 작다."""
    L = trimesh.smoothing.laplacian_calculation(m)
    V = np.asarray(m.vertices)
    return float(np.median(np.linalg.norm(V - L.dot(V), axis=1)) / du)


def sdf2(a, soft):
    """2D 부호거리 (화소, 안 +). `soft` 면 가장자리 화소에서 덮인 비율로 화소보다 촘촘하게 고친다."""
    m = a > 0.5
    d = np.where(m, ndimage.distance_transform_edt(m) - 0.5, -(ndimage.distance_transform_edt(~m) - 0.5))
    if soft:
        d = np.where(np.abs(d) <= 1.0, a - 0.5, d)
    return d.astype(np.float32)


def field(arts, bs, soft):
    """판마다 2D 부호거리를 기둥으로 밀어 최솟값 (칸 단위). `soft` 면 쌍선형 보간으로 표본한다."""
    u = W.U0 + (np.arange(H.N) + 0.5) / H.N * (W.U1 - W.U0)
    z = W.Z0 + (np.arange(H.N) + 0.5) / H.N * (W.Z1 - W.Z0)
    X, Y, Z = np.meshgrid(u, u, z, indexing="ij")
    Fh = np.full(X.shape, np.inf, np.float32)
    for v, a in arts.items():
        d2 = sdf2(a, soft) / PX
        ax, sign = W.VIEW_AXIS[v]
        s = (bs if v == "back" else sign) * (X if ax == 0 else Y)
        if soft:
            pxf = (s - W.U0) / (W.U1 - W.U0) * W.RES - 0.5
            pyf = (W.Z1 - Z) / (W.Z1 - W.Z0) * W.RES - 0.5
            smp = ndimage.map_coordinates(d2, [pyf.ravel(), pxf.ravel()], order=1, mode="nearest").reshape(X.shape)
        else:
            py, px = W.topix(s, Z)
            smp = d2[py, px]
        Fh = np.minimum(Fh, smp.astype(np.float32))
    return Fh, (u, u, z)


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else "knight_Warrior_RaWl2GJ0NZ"
    ss_case = case + "_초정밀"
    todo = dict(json.load(open(os.path.join(SCR, "재렌더목록.json"), encoding="utf-8")))
    d_ss = os.path.join(O.OUT, "시트", ss_case)
    if not os.path.exists(os.path.join(d_ss, "front.png")):
        r = subprocess.run([sys.executable, "시트.py", todo[case], "--이름", ss_case, "--초정밀"],
                           capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, r.stderr[-300:]
    O.H.register_sheets()
    bs = H.CASES[case]["back_sign"]
    truth = trimesh.load(os.path.join(O.OUT, "시트", case, "truth.glb"), force="mesh")
    T, ot = O.J.grid(truth)

    def iou(m):
        G, og = O.J.grid(m)
        A, B = O.J.common(T, ot, G, og)
        return float((A & B).sum() / max((A | B).sum(), 1))

    # 0/1 마스크 — 지금 파이프라인과 같은 경로 (정렬까지)
    d_bin = os.path.join(O.OUT, "시트", case)
    masks = {v: H.to_win(H.declutter(W.art_mask(os.path.join(d_bin, v + ".png")))) for v in W.VIEWS}
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    plain, axes = H.carve(masks, back_sign=bs)
    # 덮임 비율 — 같은 변환(to_win · warp)을 태운다. 판 렌더는 창 좌표 그대로라 거의 항등이다
    cov = {}
    for v in W.VIEWS:
        im = cv2.imdecode(np.fromfile(os.path.join(d_ss, v + ".png"), np.uint8), cv2.IMREAD_UNCHANGED)
        a = im[:, :, 3].astype(np.float32) / 255.0
        _, ca = H.to_win(H.declutter(a > 0.5), a)
        cov[v] = H._warp_one(ca, v, p)
    du = axes[0][1] - axes[0][0]
    F_bin, _ = field({v: masks[v].astype(np.float32) for v in W.VIEWS}, bs, soft=False)
    F_cov, _ = field(cov, bs, soft=True)
    meshes = {"0/1 hull (지금)": O.C.to_mesh(plain, axes),
              "연속장 · 0/1 마스크": BS.mesh(F_bin, axes),
              "연속장 · 덮임 비율": BS.mesh(F_cov, axes)}
    res = {}
    print("  %s   (정답 IoU 격자128 · 챔퍼 키 단위 · 계단 거칠기 칸 — 작을수록 매끈)" % case)
    print("    %-20s 계단 거칠기 %.4f칸" % ("정답", rough(truth, du)))
    for k, m in meshes.items():
        ch = SF.chamfer(truth, m)["챔퍼"]
        res[k] = (iou(m), ch, rough(m, du))
        print("    %-20s IoU %.4f · 챔퍼 %.4f · 계단 거칠기 %.4f칸" % (k, *res[k]), flush=True)
    R = RG.rot(np.asarray(meshes["0/1 hull (지금)"].vertices))
    lo, hi = R.min(0), R.max(0)
    span = max(hi[0] - lo[0], hi[2] - lo[2]) * 1.04
    frame = ((lo[0] + hi[0]) / 2 - span / 2, (lo[2] + hi[2]) / 2 - span / 2), span
    S, G = 440, 12
    im = Image.new("RGB", (4 * (S + G) + G, S + 120), "white")
    d = ImageDraw.Draw(im)
    d.text((G, 12), "%s — 최소 단위를 줄이면 결이 사라지나 (45도 · 같은 렌더러 · 흐림 없음)" % case,
           fill=(20, 20, 20), font=_font(22))
    cols = [("정답", truth, RG.TINT["정답"])] + [(k, m, (205, 205, 205)) for k, m in meshes.items()]
    for i, (k, m, tint) in enumerate(cols):
        x = G + i * (S + G)
        d.text((x, 50), k, fill=(40, 40, 40), font=_font(15))
        im.paste(Image.fromarray(RG.render(m, frame, S, tint)), (x, 76))
        if k in res:
            d.text((x, 76 + S + 6), "IoU %.4f · 챔퍼 %.4f · 계단 %.3f칸" % res[k], fill=(60, 60, 60), font=_font(13))
    out = os.path.join(O.OUT, "초정밀_%s.png" % case)
    im.save(out)
    print("  ->", out)


if __name__ == "__main__":
    main()
