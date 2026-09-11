# -*- coding: utf-8 -*-
"""벤치 안에서 채점되는 **모양 그 자체**를 45도에서 본다 -> out/벤치모양.png

    python 벤치그림.py <벤치lam4.jsonl> 케이스 [케이스 ...]

열: 정답 · 이진 hull · 대조군(파이프0.50 부피로 매끈하게 민 것) · 파이프0.20 · 파이프0.50 ·
타원0.50 · 오라클0.50. 모두 **같은 렌더러**(메시 -> 면 음영, 화가 알고리즘)로 그려서 차이가
렌더 탓이 아니다. 칸 아래 숫자는 벤치 기록의 3D IoU (격자128)."""
import json
import os
import sys

import cv2
import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy import ndimage

SCR = os.path.dirname(os.path.abspath(__file__))
HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, SCR)
os.chdir(HERE)
import 오라클 as O
import 벤치lam as B
from 계획 import _font

AZ = np.radians(45)
LIGHT = np.array([-0.45, -1.0, 0.75]); LIGHT /= np.linalg.norm(LIGHT)
COLS = [("정답", None), ("이진 hull", "이진"), ("대조군", "균일@파이프0.50"), ("파이프0.20", "파이프0.20"),
        ("파이프0.50", "파이프0.50"), ("타원0.50", "타원0.50"), ("오라클0.50", "오라클0.50")]
TINT = {"정답": (235, 235, 235), "이진 hull": (215, 215, 215), "대조군": (250, 205, 150),
        "파이프0.20": (175, 200, 240), "파이프0.50": (120, 160, 230), "타원0.50": (200, 175, 235),
        "오라클0.50": (150, 215, 170)}


def rot(V):
    c, s = np.cos(AZ), np.sin(AZ)
    return np.stack([c * V[:, 0] - s * V[:, 1], s * V[:, 0] + c * V[:, 1], V[:, 2]], 1)


def render(mesh, frame, S, tint):
    """카메라는 -y 쪽에서 +y 를 본다. 먼 면부터 칠해 가까운 면이 남는다."""
    V, F = rot(np.asarray(mesh.vertices)), np.asarray(mesh.faces)
    N = rot(np.asarray(mesh.face_normals))
    (x0, z0), span = frame
    px = ((V[:, 0] - x0) / span * S).astype(np.float32)
    py = ((1 - (V[:, 2] - z0) / span) * S).astype(np.float32)
    P = np.round(np.stack([px, py], 1)).astype(np.int32)[F]
    shade = 0.22 + 0.78 * np.clip(N @ LIGHT, 0, 1)
    img = np.full((S, S, 3), 250, np.uint8)
    for i in np.argsort(V[F][:, :, 1].mean(1))[::-1]:
        c = tuple(int(t * shade[i]) for t in tint)
        cv2.fillConvexPoly(img, P[i], c)
    return img


def main():
    rows = {json.loads(l)["case"]: json.loads(l) for l in open(sys.argv[1], encoding="utf-8")}
    cases = sys.argv[2:]
    O.H.register_sheets()
    S, G, LW, TOP, RH = 190, 10, 190, 110, 190 + 34
    im = Image.new("RGB", (LW + len(COLS) * (S + G) + G, TOP + len(cases) * RH + 20), "white")
    d = ImageDraw.Draw(im)
    f1, f2, f3 = _font(24), _font(14), _font(13)
    d.text((24, 16), "벤치 안에서 채점되는 모양 — 45도 (원화 세 장 중 어느 것도 안 그린 각도)", fill=(20, 20, 20), font=f1)
    d.text((24, 52), "같은 렌더러로 그렸다 · 칸 아래 = 3D IoU (격자128) · 대조군 = hull 을 파이프0.50 부피까지 "
                     "매끈하게 안으로 민 것 (정보 0)", fill=(90, 90, 90), font=f3)
    for j, (name, _) in enumerate(COLS):
        d.text((LW + G + j * (S + G), TOP - 24), name, fill=(40, 40, 40), font=f2)
    for i, case in enumerate(cases):
        r = rows[case]
        truth = trimesh.load(os.path.join(O.OUT, "시트", case, "truth.glb"), force="mesh")
        plain, p20, axes, _ = O.build(case, truth, 0.20, "파이프")
        vox = {"이진": plain, "파이프0.20": p20,
               "파이프0.50": O.build(case, truth, 0.50, "파이프")[1],
               "타원0.50": O.build(case, truth, 0.50, "타원")[1],
               "오라클0.50": O.build(case, truth, 0.50, "오라클")[1]}
        meshes = {"정답": truth, **{k: O.C.to_mesh(v, axes) for k, v in vox.items()}}
        sdf = (ndimage.distance_transform_edt(plain) - ndimage.distance_transform_edt(~plain)).astype(np.float32)
        meshes["균일@파이프0.50"] = B.sdf_mesh(sdf, axes, r["t"]["파이프0.50"])
        R = rot(np.asarray(meshes["이진"].vertices))           # 한 줄은 hull 에 맞춘 같은 틀
        lo, hi = R.min(0), R.max(0)
        span = max(hi[0] - lo[0], hi[2] - lo[2]) * 1.06
        frame = ((lo[0] + hi[0]) / 2 - span / 2, (lo[2] + hi[2]) / 2 - span / 2), span
        y0 = TOP + i * RH
        d.text((24, y0 + 80), case[:22], fill=(20, 20, 20), font=f2)
        for j, (name, key) in enumerate(COLS):
            x0 = LW + G + j * (S + G)
            src = meshes["정답"] if key is None else meshes[key]
            im.paste(Image.fromarray(render(src, frame, S, TINT[name])), (x0, y0))
            d.rectangle([x0, y0, x0 + S - 1, y0 + S - 1], outline=(220, 220, 220))
            if key is not None:
                v = r["128"][key]
                txt = "%.4f" % v
                if key not in ("이진", "균일@파이프0.50"):
                    dv = v - r["128"]["균일@" + key]
                    txt += "  (%+.4f)" % dv
                    col = (30, 130, 70) if dv > 0 else (190, 60, 40)
                else:
                    col = (60, 60, 60)
                d.text((x0, y0 + S + 4), txt, fill=col, font=f3)
        print("  %s 그림" % case, flush=True)
    im.save(os.path.join(HERE, "out", "벤치모양.png"))
    print("  -> out/벤치모양.png")


if __name__ == "__main__":
    main()
