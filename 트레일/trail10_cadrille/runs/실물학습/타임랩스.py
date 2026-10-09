# -*- coding: utf-8 -*-
"""실물학습 타임랩스 — 300 스텝마다 실물 시험 부품 6 개(사전0 0·2·6·8·14·32)의 AI 예측(파랑) · 위 사람 부품(노랑) · loss 곡선 → mp4"""
import os, sys, json, glob, subprocess, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); sys.path[:0] = [os.path.join(R, "조각0"), os.path.join(os.path.dirname(R), "s0")]
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 300; V = [1, 0.6, 0.8]; RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
SNAPI = [0, 2, 6, 8, 14, 32]
def 그림(a):
    P, 파랑, 실물 = a
    from 평가 import 메시
    from render import render
    try:
        if 실물: m = trimesh.load(RR + P, force="mesh"); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.84 / max(m.extents)); m.apply_translation([.5] * 3)
        else: m = 메시(P); m.apply_scale(0.42); m.apply_translation([.5] * 3)
        return np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), V, img_size=C, cols=np.tile([0.45, 0.68, 0.98], (len(m.faces), 1)) if 파랑 else None))
    except Exception: return np.full((C, C, 3), 245, np.uint8)
if __name__ == "__main__":
    from multiprocessing import Pool
    S = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(H, "스냅", "*.json")))]
    부품 = [r["부품"] for k in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % k), encoding="utf-8"))]
    with Pool(4) as pool:
        G = pool.map(그림, [(부품[i], False, True) for i in SNAPI]); A = pool.map(그림, [(p, True, False) for s in S for p in s["예측"]])
    O = os.path.join(H, "프레임"); os.makedirs(O, exist_ok=True)
    L = [(s["스텝"], s["손실"]) for s in S if s["손실"] is not None]; xm = max(a for a, _ in L); ym = max(b for _, b in L)
    for k, s in enumerate(S):
        im = Image.new("RGB", (C * 6, C * 2 + 350), "white"); d = ImageDraw.Draw(im)
        for j in range(6): im.paste(Image.fromarray(G[j]), (j * C, 110)); im.paste(Image.fromarray(A[k * 6 + j]), (j * C, 110 + C))
        d.text((20, 15), "실물 부품으로 학습 · 스텝 %d" % s["스텝"], font=F(44), fill="black")
        d.text((20, 112), "사람 부품", font=F(26), fill=(120, 120, 120)); d.text((20, 112 + C), "AI", font=F(26), fill=(60, 110, 220))
        gx, gy, gw, gh = 80, C * 2 + 150, C * 6 - 140, 170
        pts = [(gx + gw * a / xm, gy + gh - gh * b / ym) for a, b in L]; d.line(pts, fill=(225, 225, 225), width=3)
        now = [q for (a, _), q in zip(L, pts) if a <= s["스텝"]]
        if len(now) > 1: d.line(now, fill=(200, 40, 40), width=5)
        d.text((gx + 10, gy - 30), "loss", font=F(26), fill=(200, 40, 40))
        im.save(os.path.join(O, "%04d.png" % k))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "5", "-i", os.path.join(O, "%04d.png"), "-vf", "tpad=stop_mode=clone:stop_duration=2,scale=1800:-2", "-pix_fmt", "yuv420p", os.path.join(H, "타임랩스.mp4")], check=True)
    print("ok", len(S))
