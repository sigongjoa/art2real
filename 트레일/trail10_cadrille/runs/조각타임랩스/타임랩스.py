# -*- coding: utf-8 -*-
"""학습 타임랩스 — 150 스텝마다 남긴 시험 부품 6 개 예측을 3D 로 그려 한 장씩(위 = 정답 · 아래 = 그 순간 AI) → mp4"""
import os, sys, json, glob, subprocess, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); sys.path[:0] = [os.path.join(R, "조각0"), os.path.join(os.path.dirname(R), "s0")]
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 300; V = [1, 0.6, 0.8]

def 그림(P):
    from 평가 import 메시
    from render import render
    try:
        m = 메시(P); m.apply_scale(0.42); m.apply_translation([.5] * 3)   # 정답과 같은 틀([-1,1] → 단위 상자 안) — 크기 차이도 보이게
        return np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), V, img_size=C))
    except Exception: return np.full((C, C, 3), 245, np.uint8)

if __name__ == "__main__":
    from multiprocessing import Pool
    S = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(H, "스냅", "*.json")))]
    Q = [json.load(open(os.path.join(R, "조각0", "정답", "%04d.json" % i), encoding="utf-8")) for i in range(3600, 3606)]
    with Pool(12) as pool:
        G = pool.map(그림, Q); A = pool.map(그림, [p for s in S for p in s["예측"]])
    O = os.path.join(H, "프레임"); os.makedirs(O, exist_ok=True)
    for k, s in enumerate(S):
        im = Image.new("RGB", (C * 6, C * 2 + 130), "white"); d = ImageDraw.Draw(im)
        for j in range(6): im.paste(Image.fromarray(G[j]), (j * C, 110)); im.paste(Image.fromarray(A[k * 6 + j]), (j * C, 110 + C))
        d.text((20, 15), "학습 스텝 %d · 에폭 %d" % (s["스텝"], s["에폭"]), font=F(44), fill="black")
        d.text((C * 6 - 20, 20), "loss %s" % ("—" if s["손실"] is None else "%.2f" % s["손실"]), font=F(40), fill=(200, 40, 40), anchor="ra")
        d.text((20, 112), "정답", font=F(28), fill=(120, 120, 120)); d.text((20, 112 + C), "AI", font=F(28), fill=(60, 110, 220))
        im.save(os.path.join(O, "%04d.png" % k))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "4", "-i", os.path.join(O, "%04d.png"), "-vf", "scale=1800:-2", "-pix_fmt", "yuv420p", os.path.join(H, "타임랩스.mp4")], check=True)
    print("ok", len(S))
