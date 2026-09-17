# -*- coding: utf-8 -*-
"""음영민감도 SDXL 판 · CV 판을 한 장에 — 입력 · 옆 실루엣 겹침(회색 겹침 · 빨강 원화만 · 파랑 생성만) · 씨앗별 P."""
import json, os, sys, glob
import cv2, numpy as np, trimesh
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 음영민감도 as M, 음영민감도_cv as C
import 생성3D as G3, win as W
from 생성깎기 import voxelize
from 조각생성 import trim
from 계획 import _font


def side_overlay(path, masks, axes):
    u, _, z = axes
    g = trim(trimesh.load(path, force="mesh"))
    _, V, _, _ = G3.orient(g.vertices, masks)
    vox = voxelize(trimesh.Trimesh(V, np.asarray(g.faces), process=False), axes)
    a, b = np.nonzero(vox.any(0))
    g2 = np.zeros((W.RES, W.RES), np.uint8)
    py, px = W.topix(u[a], z[b]); g2[py, px] = 1
    s = cv2.dilate(g2, np.ones((5, 5), np.uint8)).astype(bool); m = masks["side"]
    img = np.full((W.RES, W.RES, 3), 255, np.uint8)
    img[m & ~s] = (220, 60, 60); img[s & ~m] = (60, 90, 220); img[m & s] = (130, 130, 130)
    ys, xs = np.nonzero(m | s)
    return img[max(ys.min() - 10, 0):ys.max() + 10, max(xs.min() - 60, 0):xs.max() + 60]


def load_P(pat):
    q = [x for x in sorted(glob.glob(os.path.join("out", "기록", pat))) if "판정" not in x][-1]
    return {(r["판본"], r["씨앗"]): r["P"] for r in json.load(open(q, encoding="utf-8"))["행"]}


def main():
    masks, bs, axes = M.setup()
    rows = [("SDXL 판", M.S, ["k0", "k1", "C"], load_P("음영민감도_2*.json"), {"k0": "원화", "k1": "SDXL 명암 ×1", "C": "대조: 무작위 얼룩"}),
            ("CV 판", C.S, ["k0", "H1", "E1", "F1"], load_P("음영민감도CV_*.json"), {"k0": "원화 (창 좌표)", "H1": "hull 깊이 명암", "E1": "푸아송 돔 명암", "F1": "대조: 빛 뒤집음"})]
    TH, G, LW, TOP = 300, 10, 110, 90
    ncol = 4
    im = Image.new("RGB", (LW + ncol * (2 * 150 + TH + 3 * G), TOP + 2 * (TH + 70)), "white")
    d = ImageDraw.Draw(im)
    d.text((16, 12), "은둔자 음영 민감도 — 음영만 바꿔도 TripoSG 의 옆모습은 안 바뀐다 (씨앗 42 그림)", fill="black", font=_font(24))
    d.text((16, 48), "옆 겹침: 회색 = 겹침 · 빨강 = 원화 옆에만 · 파랑 = 생성에만 · P = 옆 못덮음+넘침 (씨앗 42 / 7 / 123 · 낮을수록 좋음)", fill=(80, 80, 80), font=_font(15))
    for r, (name, S, vs, P, lab) in enumerate(rows):
        y = TOP + r * (TH + 70)
        d.text((12, y + TH // 2), name, fill="black", font=_font(18))
        for c, v in enumerate(vs):
            x = LW + c * (2 * 150 + TH + 3 * G)
            d.text((x, y), "%s · P %s" % (lab[v], " / ".join("%.2f" % P[v, s] for s in M.SEEDS)), fill="black", font=_font(14))
            inp = Image.open(os.path.join(S, v + ".png")).convert("RGBA")
            bg = Image.new("RGBA", inp.size, "white"); bg.alpha_composite(inp); bg = bg.convert("RGB"); bg.thumbnail((150, TH))
            im.paste(bg, (x, y + 24))
            ov = Image.fromarray(side_overlay(os.path.join(S, "tri", "%s_s42.glb" % v), masks, axes)); ov.thumbnail((150 + TH, TH))
            im.paste(ov, (x + 160, y + 24))
            print("  ", name, v, flush=True)
    q = os.path.join("out", "은둔자_음영민감도.png")
    im.save(q); print(" ->", q)


if __name__ == "__main__":
    main()
