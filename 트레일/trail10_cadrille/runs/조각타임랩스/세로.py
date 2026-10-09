# -*- coding: utf-8 -*-
"""학습 타임랩스 → 세로 쇼츠 프레임(1080×1920) — 부품 4 개 2×2(큰 = AI 파랑 · 구석 = 정답) · 위 스텝 · loss 곡선 · 줄마다 스냅 구간을 정해 섞어 넘김
python runs/조각타임랩스/세로.py <시간표.json> <frames 폴더>"""
import os, sys, json, glob, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); sys.path[:0] = [os.path.join(R, "조각0"), os.path.join(os.path.dirname(R), "s0")]
from PIL import Image, ImageDraw, ImageFont, ImageFilter
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
PARTS = [1, 3, 4, 5]; T = 500; g = 170; V = [1, 0.6, 0.8]
def 그림(a):
    P, C, 파랑 = a
    from 평가 import 메시
    from render import render
    try:
        m = 메시(P); m.apply_scale(0.42); m.apply_translation([.5] * 3)
        im = render(np.asarray(m.vertices), np.asarray(m.faces), V, img_size=C, cols=np.tile([0.45, 0.68, 0.98], (len(m.faces), 1)) if 파랑 else None)
        return np.asarray(im)
    except Exception: return np.full((C, C, 3), 255, np.uint8)
if __name__ == "__main__":
    from multiprocessing import Pool
    TL = json.load(open(sys.argv[1], encoding="utf-8"))["lines"]; O = sys.argv[2]; os.makedirs(O, exist_ok=True)
    S = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(H, "스냅", "*.json")))]
    Q = [json.load(open(os.path.join(R, "조각0", "정답", "%04d.json" % (3600 + k)), encoding="utf-8")) for k in PARTS]
    with Pool(6) as pool:
        G = pool.map(그림, [(q, g, False) for q in Q]); A = pool.map(그림, [(s["예측"][k], T, True) for s in S for k in PARTS])
    A = np.stack(A).reshape(len(S), len(PARTS), T, T, 3).astype(np.float32)
    L = [(s["스텝"], s["손실"]) for s in S if s["손실"] is not None]; xm = max(a for a, _ in L); ym = max(b for _, b in L)
    # 줄 → 스냅 구간(시작 · 끝 · 끝에서 멈추는 비율)
    plan = [(0, 0, 0), (0, 0, 0), (0, 4, .2), (4, 9, 0), (9, 20, .1), (20, 34, 0), (34, 90, .3), (90, 90, 0)]
    def 스냅(fr):
        for (f0, f1), (a, b, hold) in zip(TL, plan):
            if f0 <= fr <= f1:
                u = min(1, (fr - f0) / max(1, (f1 - f0) * (1 - hold))); return a + (b - a) * u
        return 90
    BG = (30, 31, 36)
    for fr in range(1, TL[-1][1] + 1):
        x = 스냅(fr); i0 = int(np.floor(x)); i1 = min(i0 + 1, len(S) - 1); w = x - i0
        tiles = (A[i0] * (1 - w) + A[i1] * w).astype(np.uint8); s = S[int(round(x))]
        im = Image.new("RGB", (1080, 1920), BG); d = ImageDraw.Draw(im)
        d.text((540, 95), "학습 %s 스텝" % format(s["스텝"], ","), font=F(78), fill="white", anchor="mm")
        gx, gy, gw, gh = 70, 190, 940, 210   # loss 곡선
        d.rounded_rectangle((40, 170, 1040, 420), 24, fill=(44, 45, 52))
        pts = [(gx + gw * a / xm, gy + gh - gh * b / ym) for a, b in L]; d.line(pts, fill=(80, 80, 90), width=4)
        now = [q for (a, _), q in zip(L, pts) if a <= s["스텝"]]
        if len(now) > 1: d.line(now, fill=(240, 80, 70), width=7)
        if now: d.ellipse((now[-1][0] - 12, now[-1][1] - 12, now[-1][0] + 12, now[-1][1] + 12), fill=(240, 80, 70))
        d.text((gx + 8, gy - 8), "틀린 정도" + ("" if s["손실"] is None else "  %.2f" % s["손실"]), font=F(34), fill=(240, 120, 110))
        for k in range(4):
            x0, y0 = 30 + (k % 2) * 520, 450 + (k // 2) * 520
            m = Image.new("L", (T, T), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, T - 1, T - 1), 28, fill=255)
            im.paste(Image.fromarray(tiles[k]), (x0, y0), m)
            gi = Image.fromarray(G[k]); ImageDraw.Draw(gi).rectangle((0, 0, g - 1, g - 1), outline=(240, 180, 40), width=6); im.paste(gi, (x0 + 12, y0 + 12))
            d.text((x0 + 12 + g // 2, y0 + 12 + g + 6), "정답", font=F(28), fill=(200, 150, 30), anchor="ma")
        im.save(os.path.join(O, "%04d.png" % fr))
    print("ok", TL[-1][1])
