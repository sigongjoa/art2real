# -*- coding: utf-8 -*-
"""깊이학습 타임랩스 — 스냅마다: 시험 6 부품 × (입력 선 · AI 깊이 · 실물 깊이) 음영 + 손실 곡선 · 1080×1920 프레임 → mp4
python runs/깊이학습/타임랩스.py"""
import os, glob, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
T = np.load(os.path.join(H, "시험.npz"))["X"].astype(np.float32); SN = [0, 5, 17, 18, 31, 35]; V = 4   # 위에서 본 방향
def 음영(D, S, 색):
    gy, gx = np.gradient(-D * 128); n = np.dstack([-gx, -gy, np.ones_like(D) * 1.5]); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    l = np.clip(n @ np.array([-.5, -.6, .65]) / np.linalg.norm([-.5, -.6, .65]), 0, 1) * .75 + .25
    im = np.ones(D.shape + (3,)) * 30; im[S > .5] = (l[..., None] * np.array(색))[S > .5]; return Image.fromarray(im.astype(np.uint8)).resize((300, 300), Image.NEAREST)
fs = sorted(glob.glob(os.path.join(H, "스냅", "*.npz"))); L = [(int(os.path.basename(f)[:5]), float(np.load(f)["손실"])) for f in fs]
O = os.path.join(H, "타임랩스"); os.makedirs(O, exist_ok=True)
for fi, f in enumerate(fs):
    z = np.load(f); P = z["P"].astype(np.float32).reshape(6, 6, 128, 128); st = int(os.path.basename(f)[:5])
    cv = Image.new("RGB", (1080, 1920), (18, 20, 30)); d = ImageDraw.Draw(cv)
    d.text((540, 70), "그림 → 깊이 학습", font=F(68), fill="white", anchor="mm"); d.text((540, 150), "스텝 %d · 에폭 %.1f" % (st, float(z["에폭"])), font=F(44), fill=(150, 200, 255), anchor="mm")
    for j, t in enumerate(["입력: 선", "AI 깊이", "진짜 깊이"]): d.text((40 + 150 + j * 340, 225), t, font=F(36), fill=[(220, 220, 220), (110, 170, 255), (255, 220, 90)][j], anchor="mm")
    for r, (i, k) in enumerate(zip(SN, range(6))):
        if r >= 4: break
        y = 260 + r * 320; S, Lin, Dh, D = T[i, :, V]
        cv.paste(Image.fromarray((255 - Lin * 255).astype(np.uint8)).convert("RGB").resize((300, 300), Image.NEAREST), (40, y))
        cv.paste(음영(P[k, V], S, (110, 170, 255)), (380, y)); cv.paste(음영(D, S, (255, 220, 90)), (720, y))
    # 손실 곡선
    x0, y0, w, h = 80, 1580, 920, 280; d.rectangle((x0, y0, x0 + w, y0 + h), outline=(80, 80, 100), width=2)
    pts = [(s, l) for s, l in L if np.isfinite(l)]
    if pts:
        mx, lo, hi = max(s for s, _ in L) or 1, min(l for _, l in pts), max(l for _, l in pts)
        q = [(x0 + s / mx * w, y0 + h - (l - lo) / max(hi - lo, 1e-6) * h) for s, l in pts if s <= st]
        if len(q) > 1: d.line(q, fill=(255, 120, 120), width=4)
    d.text((x0, y0 - 40), "손실", font=F(32), fill=(255, 120, 120))
    cv.save(os.path.join(O, "%04d.png" % fi))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "8", "-i", os.path.join(O, "%04d.png"), "-vf", "tpad=stop_mode=clone:stop_duration=2", "-pix_fmt", "yuv420p", os.path.join(H, "타임랩스.mp4")]); print("ok", len(fs))
