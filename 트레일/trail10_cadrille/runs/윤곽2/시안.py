# -*- coding: utf-8 -*-
"""쇼츠 시안 두 가지(8 초 · 24fps · 1080×1920) — A 밈 편집(회전 · 줌 펀치 · 흔들림 · 퍽 도장) · B 대결(VS · 체력바 · K.O.)
python runs/윤곽2/시안.py <출력 폴더>"""
import os, sys, math, json, subprocess, wave, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
from render import render
from PIL import Image, ImageDraw, ImageFont, ImageFilter
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
W, Hh, FPS = 1080, 1920, 24; O = sys.argv[1]; os.makedirs(O, exist_ok=True)
부품 = [r["부품"] for k in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % k), encoding="utf-8"))]
def 돌림(m, n, C, blue):   # n 각도 회전 렌더
    m = m.copy(); lo, hi = m.bounds; m.apply_translation(-(lo + hi) / 2); m.apply_scale(0.8 / (hi - lo).max()); out = []
    for k in range(n):
        a = 2 * math.pi * k / n; Rz = trimesh.transformations.rotation_matrix(a, [0, 1, 0]); mm = m.copy(); mm.apply_transform(Rz); mm.apply_translation([.5] * 3)
        im = render(np.asarray(mm.vertices), np.asarray(mm.faces), [1, 0.5, 0.9], img_size=C, cols=np.tile([0.45, 0.68, 0.98], (len(mm.faces), 1)) if blue else None)
        a_ = np.asarray(im.convert("RGB")); mask = (a_.min(-1) < 250).astype(np.uint8) * 255; im = im.convert("RGBA"); im.putalpha(Image.fromarray(mask)); out.append(im)
    return out
사람 = 돌림(trimesh.load(RR + 부품[25], force="mesh"), 48, 760, False)
부스 = 돌림(trimesh.load(os.path.join(H, "결과", "25_깎음.stl")), 48, 760, True)
def 흔들(t, t0, amp=40, dur=.35): u = t - t0; return (0, 0) if not 0 <= u < dur else (int(amp * (1 - u / dur) * math.sin(u * 90)), int(amp * .6 * (1 - u / dur) * math.cos(u * 70)))
def 글(d, xy, s, n, fill=(255, 255, 255), stroke=10, sf=(0, 0, 0)):
    if n < 8: return
    d.text(xy, s, font=F(n), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=sf)
def 팝(t, t0, d=.18): u = (t - t0) / d; return 0 if u < 0 else (1.35 - .35 * min(1, u) if u < 1 else 1.0) if u < 1 else 1.0
def 붙(im, sp, xy, s=1.0):
    if s <= 0.05: return
    if s != 1.0: sp = sp.resize((int(sp.width * s), int(sp.height * s)))
    im.alpha_composite(sp, (int(xy[0] - sp.width / 2), int(xy[1] - sp.height / 2)))
# ── A 밈 편집 ──
def A(fr):
    t = fr / FPS; im = Image.new("RGBA", (W, Hh), (18, 18, 24, 255)); d = ImageDraw.Draw(im)
    k = int(t * 12) % 48
    if t < 2.4:   # 사람 부품이 돌며 날아 들어옴
        x = W / 2 + max(0, 1 - t / .4) * 900; 붙(im, 사람[k], (x, 980), 1.0)
        if t > .3: 글(d, (540, 330), "사람이 만든 부품", int(90 * 팝(t, .3)), (255, 230, 60))
    elif t < 5.6:   # AI 결과 — 부스러기 · 줌 펀치
        z = 1.0 + (.55 * min(1, (t - 3.3) / .15) if t > 3.3 else 0); cx, cy = 540, 980 - (200 if t > 3.3 else 0)
        붙(im, 부스[k], (cx, cy), z)
        글(d, (540, 330), "AI가 깎은 결과", int(90 * 팝(t, 2.4)), (120, 190, 255))
        if t > 3.3:
            r = 210; d.ellipse((540 - r, 860 - r, 540 + r, 860 + r), outline=(255, 50, 50), width=16)
            글(d, (820, 640), "퍽!", int(170 * 팝(t, 3.35)), (255, 60, 60), 12, (255, 255, 255))
        if t > 4.4: 글(d, (540, 1450), "둥근 면 = 홈?? ", int(96 * 팝(t, 4.4)), (255, 255, 255), 10)
    else:   # 판정 도장
        붙(im, 부스[k], (540, 980), .9); im.alpha_composite(Image.new("RGBA", (W, Hh), (0, 0, 0, 120)))
        d = ImageDraw.Draw(im); s = 팝(t, 5.6, .22)
        st = Image.new("RGBA", (900, 380), (0, 0, 0, 0)); ds = ImageDraw.Draw(st); ds.rounded_rectangle((10, 10, 890, 370), 40, outline=(255, 50, 50), width=22)
        ds.text((450, 190), "부스러기 10개", font=F(130), fill=(255, 50, 50), anchor="mm"); st = st.rotate(-8, expand=True)
        붙(im, st, (540, 900), s)
    ox, oy = 흔들(t, 3.3) if t < 4 else 흔들(t, 5.6, 30); out = Image.new("RGBA", (W, Hh), (18, 18, 24, 255)); out.alpha_composite(im, (ox, oy)); return out
# ── B 대결 ──
def B(fr):
    t = fr / FPS; im = Image.new("RGBA", (W, Hh), (25, 10, 40, 255)); d = ImageDraw.Draw(im); k = int(t * 12) % 48
    if t < 1.6:   # VS 화면
        sl = min(1, t / .3); d.polygon([(0, 0), (W * .62 * sl, 0), (W * .38 * sl, Hh), (0, Hh)], fill=(40, 90, 200))
        d.polygon([(W, 0), (W - W * .38 * sl, 0), (W - W * .62 * sl, Hh), (W, Hh)], fill=(200, 50, 60))
        글(d, (270, 700), "학습한\nAI", 110); 글(d, (810, 1250), "그림자\n세 장", 110)
        if t > .5: 글(d, (540, 960), "VS", int(260 * 팝(t, .5)), (255, 220, 40), 14)
    else:
        hp_ai = 36 - 34 * min(1, max(0, (t - 2.0) / 1.2)); hp_sh = 36 - 12 * min(1, max(0, (t - 3.6) / 1.2))
        for j, (nm, hp, c, y) in enumerate((("학습한 AI", hp_ai, (60, 120, 230), 230), ("그림자 세 장", hp_sh, (230, 70, 80), 420))):
            글(d, (60 + 260, y - 60), nm, 64); d.rounded_rectangle((60, y, 1020, y + 70), 20, fill=(60, 60, 70)); d.rounded_rectangle((60, y, 60 + 960 * hp / 36, y + 70), 20, fill=c)
            글(d, (1000, y - 60), "%d / 36" % round(36 - (36 - hp)), 60, (255, 255, 255), 8)
        붙(im, 부스[k] if t < 3.6 else 사람[k], (540, 1180), .95)
        if t > 3.2 and t < 3.6 + 0.1: pass
        if 3.2 < t: 글(d, (330, 760), "2개", int(150 * 팝(t, 3.2)), (120, 170, 255), 12)
        if 4.8 < t: 글(d, (750, 760), "24개", int(150 * 팝(t, 4.8)), (255, 120, 120), 12)
        if t > 6.2:
            s = 팝(t, 6.2, .2); st = Image.new("RGBA", (800, 320), (0, 0, 0, 0)); ds = ImageDraw.Draw(st); ds.text((400, 160), "K.O.", font=F(250), fill=(255, 220, 40), anchor="mm", stroke_width=14, stroke_fill=(0, 0, 0))
            붙(im, st.rotate(10, expand=True), (540, 1200), s * 1.1)
    ox, oy = 흔들(t, .5, 35) if t < 1 else 흔들(t, 6.2, 45); out = Image.new("RGBA", (W, Hh), (25, 10, 40, 255)); out.alpha_composite(im, (ox, oy)); return out
# ── 효과음(합성) ──
SR = 24000
def 소리(events, dur):
    a = np.zeros(int(dur * SR), np.float32); t = np.arange(int(.3 * SR)) / SR
    kinds = {"퍽": (np.sin(2 * np.pi * (110 - 60 * t) * t) * np.exp(-t * 16) + .5 * np.random.default_rng(0).standard_normal(len(t)) * np.exp(-t * 40)) * 12000,
             "휙": np.random.default_rng(1).standard_normal(len(t)) * np.sin(np.pi * t / t[-1]) ** 2 * 3000,
             "뿅": np.sin(2 * np.pi * (500 + 2600 * t) * t) * np.exp(-t * 30) * 9000,
             "땡": sum(np.sin(2 * np.pi * f * t) / (j + 1) for j, f in enumerate((880, 1320, 1760))) * np.exp(-t * 6) * 5000}
    for tt, k in events: s = int(tt * SR); y = kinds[k]; a[s:s + len(y)] += y[:max(0, len(a) - s)]
    return np.clip(a, -32767, 32767).astype(np.int16)
for nm, fn, ev in (("A_밈편집", A, [(0, "휙"), (.3, "뿅"), (2.4, "휙"), (2.45, "뿅"), (3.3, "퍽"), (4.4, "뿅"), (5.6, "퍽")]),
                   ("B_대결", B, [(0, "휙"), (.5, "퍽"), (2.0, "휙"), (3.2, "뿅"), (4.8, "뿅"), (6.2, "퍽"), (6.25, "땡")])):
    wav = os.path.join(O, nm + ".wav")
    with wave.open(wav, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(소리(ev, 8).tobytes())
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, Hh), "-r", str(FPS), "-i", "-", "-i", wav,
                          "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-shortest", os.path.join(O, nm + ".mp4")], stdin=subprocess.PIPE)
    for fr in range(8 * FPS): p.stdin.write(fn(fr).convert("RGB").tobytes())
    p.stdin.close(); p.wait(); print("ok", nm)
