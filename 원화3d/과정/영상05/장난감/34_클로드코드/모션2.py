# -*- coding: utf-8 -*-
"""34 모션 그래픽 2판 — 레퍼런스 실측(Kurzgesagt · 신비한 건축사전, 10-08)을 그대로:
 · 한 번에 그래픽 하나 — 앞 것이 나간 뒤 다음 것(Kurzgesagt 22.1~22.9 초)
 · 이름표 = 물체에서 선이 먼저 자라고(0.2 초) → 세로선이 옆으로 벌어져 알약(0.3 초 · 글자는 벌어진 만큼) · 의미 색 채움 + 흰 글씨 · 상자 · 외곽선 없음
 · 퇴장 = 알약이 선으로 접힘(0.25 초)
 · 큰 숫자 = 빈 곳에 흰 글씨 + 부드러운 그림자만(건축사전 378m) · 0.2 초 페이드
 · 강조 = 물체가 직접 깜빡(블렌더 쪽 · 장면.py blink) · 자막 = 작은 흰 글씨, 상자 없음
anim/NNNN.png + 앵커프레임.json → 모션2/NNNN.png → 모션2_시안.mp4"""
import json, os, glob, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D = "G:/art2real/out/영상05/장난감/34_클로드코드/"; FPS = 24; W, H = 1080, 1920
KB = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
T = json.load(open(D + "시간표.json", encoding="utf-8")); AF = json.load(open(D + "frames/앵커프레임.json", encoding="utf-8"))
LINES = [l.split("\t")[1] for l in open("G:/art2real/원화3d/과정/영상05/장난감/34_클로드코드/대본.tsv", encoding="utf-8").read().strip().split("\n")[1:]]
GRN, RED = (52, 199, 105), (232, 72, 64)
ease = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3   # 확 들어와 부드럽게 멈춤

# 줄마다 그래픽 순서(줄 안 비율 a 에서 시작 · b 에서 퇴장 시작)
PLAN = {2: [("숫자", "1 / 10", 0.04, 0.38), ("알약", ("클로드0", "똑같다", GRN), 0.45, 0.93)],
        4: [("숫자", "3 / 10", 0.04, 0.36), ("알약", ("빈자리", "관절 공이 없다", RED), 0.42, 0.93)]}

def big_number(base, s, a):   # 그림자 층 + 흰 글씨 · a = 불투명도
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = KB(190)
    d.text((W // 2 + 6, 470 + 10), s, font=f, fill=(0, 0, 0, int(120 * a)), anchor="mm"); lay = lay.filter(ImageFilter.GaussianBlur(14))
    d = ImageDraw.Draw(lay); d.text((W // 2, 470), s, font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm"); base.alpha_composite(lay)

def pill(base, p, s, col, t_in, t_out):   # t_in = 등장 뒤 초 · t_out = 퇴장 뒤 초(음수면 아직)
    x, y = p[0] * W, p[1] * H; d = ImageDraw.Draw(base); f = KB(74)
    ln = ease(t_in / 0.2) if t_out < 0 else 1.0; L = 150 * ln
    gw = ease((t_in - 0.2) / 0.3) if t_out < 0 else 1 - ease(t_out / 0.25)
    if t_out >= 0 and gw <= 0.01: ln = 1 - ease((t_out - 0.25) / 0.15); L = 150 * ln
    if L > 2:
        d.line((x, y, x, y - L), fill=col + (255,), width=6); d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=col + (255,))
    if gw > 0:
        tw = d.textlength(s, font=f); full = tw + 64; w = max(10, full * gw); h = 116; cy = y - 160 - h / 2
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.rounded_rectangle((x - w / 2, cy - h / 2, x + w / 2, cy + h / 2), h / 2, fill=col + (255,))
        txt = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(txt).text((x, cy + 2), s, font=f, fill=(255, 255, 255, 255), anchor="mm")
        mask = Image.new("L", (W, H), 0); m_ = max(0, w / 2 - 18); ImageDraw.Draw(mask).rectangle((x - m_, 0, x + m_, H), fill=255)   # 벌어진 만큼만 글자
        lay.paste(txt, (0, 0), Image.composite(txt, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask).split()[3])
        base.alpha_composite(lay)

def caption(base, s):   # 「자막이 잘 안 보이잖아」 2 번째: 상자 대신 아래 1/4 을 어둡게 깔고(그라데이션) 80px 흰 글씨
    g = Image.new("L", (1, H), 0)
    for y in range(H): g.putpixel((0, y), int(175 * min(max((y - 1300) / 260, 0), 1)))
    base.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (W, H), 8)] * 3, g.resize((W, H)))))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = KB(80)
    d.text((W // 2, 1588), s, font=f, fill=(0, 0, 0, 200), anchor="mm"); lay = lay.filter(ImageFilter.GaussianBlur(8))
    ImageDraw.Draw(lay).text((W // 2, 1580), s, font=f, fill=(255, 255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(10, 10, 12, 255)); base.alpha_composite(lay)

os.makedirs(D + "모션2", exist_ok=True); n = 0
for k in (2, 4):
    f0, f1 = T["lines"][k]; L = f1 - f0; ws = LINES[k].replace(",", " ").replace(".", " ").split(); parts = [" ".join(ws[i:i + 3]) for i in range(0, len(ws), 3)]   # 3 낱말씩(쉼표 없는 줄이 통째로 넘쳤다)
    for fr in range(f0, f1 + 1):
        src = D + "anim/%04d.png" % fr
        if not os.path.exists(src): continue
        im = Image.open(src).convert("RGBA"); u = (fr - f0) / L
        for kind, arg, a, b in PLAN[k]:
            t_in = (u - a) * L / FPS; t_out = (u - b) * L / FPS
            if t_in < 0 or t_out > 0.45: continue
            if kind == "숫자":
                al = ease(t_in / 0.2) if t_out < 0 else 1 - ease(t_out / 0.2)
                if al > 0: big_number(im, arg, al)
            else:
                nm, s, col = arg; pill(im, AF[str(fr)][nm], s, col, t_in, t_out)
        caption(im, parts[min(int(u * len(parts)), len(parts) - 1)])
        im.convert("RGB").save(D + "모션2/%04d.png" % n); n += 1
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", D + "모션2/%04d.png", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", D + "모션2_시안.mp4"])
print("frames", n)
