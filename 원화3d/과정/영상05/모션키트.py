# -*- coding: utf-8 -*-
"""장난감 CG 쇼츠 모션 그래픽 키트 (10-08 · 레퍼런스 실측: Kurzgesagt · 신비한 건축사전 0.1 초 프레임 띠)
규칙(사용자 「짜친다」 뒤 레퍼런스를 직접 보고 잰 것 · claudedocs/research_모션그래픽_20261008.md):
 · 한 번에 그래픽 하나 — 앞 것이 나간 뒤 다음 것
 · 알약 = 물체에서 선이 먼저 자람(0.2 초) → 세로선이 옆으로 벌어짐(0.3 초 · 글자는 벌어진 만큼) · 의미 색 채움 + 흰 글씨 · 검정 상자 · 외곽선 없음 · 퇴장 = 선으로 접힘(0.25 초)
 · 큰 숫자/낱말 = 빈 위쪽에 흰 글씨 + 부드러운 그림자만 · 0.2 초 페이드
 · 강조는 물체가 직접 빛남(블렌더 장면 쪽 · 장난감_공용.깜빡) · 자막 = 아래 1/4 그라데이션 + 80px 흰 글씨(「자막이 잘 안 보이잖아」)
편 폴더 `모션.json` = {"줄번호": [["숫자", "1 / 10", a, b], ["알약", ["앵커이름", "글자", [r, g, b]], a, b]]} — a·b 는 그 줄 안 비율(등장 · 퇴장 시작)
앵커 = 장면.py 가 `앵커프레임(T, cams, {"이름": (x, y, z)}, ARGS[2])` 로 남긴 frames/앵커프레임.json"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
W, H, FPS = (1920, 1080, 24) if os.environ.get("TOY_LAND") else (1080, 1920, 24)   # 10-08 가로
KB = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
ease = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3
COL = {"초록": (52, 199, 105), "빨강": (232, 72, 64), "노랑": (240, 180, 40), "하늘": (70, 150, 230)}

def big_number(base, s, a):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = KB(190 if len(s) <= 7 else 130)
    d.text((W // 2 + 6, int(H * .25)), s, font=f, fill=(0, 0, 0, int(120 * a)), anchor="mm"); lay = lay.filter(ImageFilter.GaussianBlur(14))
    ImageDraw.Draw(lay).text((W // 2, int(H * .245)), s, font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm"); base.alpha_composite(lay)

def pill(base, p, s, col, t_in, t_out):
    x, y = p[0] * W, p[1] * H; d = ImageDraw.Draw(base); f = KB(74)
    ln = ease(t_in / 0.2) if t_out < 0 else 1.0
    gw = ease((t_in - 0.2) / 0.3) if t_out < 0 else 1 - ease(t_out / 0.25)
    if t_out >= 0 and gw <= 0.01: ln = 1 - ease((t_out - 0.25) / 0.15)
    L = 150 * ln
    if L > 2: d.line((x, y, x, y - L), fill=tuple(col) + (255,), width=6); d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=tuple(col) + (255,))
    if gw > 0:
        tw = d.textlength(s, font=f); w = max(10, (tw + 64) * gw); h = 116; cy = y - 160 - h / 2
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lay).rounded_rectangle((x - w / 2, cy - h / 2, x + w / 2, cy + h / 2), h / 2, fill=tuple(col) + (255,))
        txt = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(txt).text((x, cy + 2), s, font=f, fill=(255, 255, 255, 255), anchor="mm")
        m = Image.new("L", (W, H), 0); h_ = max(0, w / 2 - 18); ImageDraw.Draw(m).rectangle((x - h_, 0, x + h_, H), fill=255)
        lay.paste(txt, (0, 0), Image.composite(txt, Image.new("RGBA", (W, H), (0, 0, 0, 0)), m).split()[3]); base.alpha_composite(lay)

_GRAD = None
def caption(base, s):
    global _GRAD
    if _GRAD is None:
        g = Image.new("L", (1, H), 0)
        for y in range(H): g.putpixel((0, y), int(175 * min(max((y - H * .677) / (H * .135), 0), 1)))
        _GRAD = Image.merge("RGBA", (*[Image.new("L", (W, H), 8)] * 3, g.resize((W, H))))
    base.alpha_composite(_GRAD); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    w = s.split(); lines = [s] if d.textlength(s, font=KB(62 if W > H else 80)) <= W - 120 else [" ".join(w[:(len(w) + 1) // 2]), " ".join(w[(len(w) + 1) // 2:])]
    sz = 62 if W > H else 80   # 가로는 한 단계 작게
    while sz > 48 and max(d.textlength(l, font=KB(sz)) for l in lines) > W - 120: sz -= 4   # 넘치면 줄임(34 편 23 초에 화면 밖으로)
    f = KB(sz)
    for j, l in enumerate(lines): d.text((W // 2, int(H * .827) + j * (sz + 16)), l, font=f, fill=(0, 0, 0, 200), anchor="mm")
    lay = lay.filter(ImageFilter.GaussianBlur(8)); d = ImageDraw.Draw(lay)
    for j, l in enumerate(lines): d.text((W // 2, int(H * .823) + j * (sz + 16)), l, font=f, fill=(255, 255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(10, 10, 12, 255))
    base.alpha_composite(lay)

def apply(im, fr, k, line_range, plan, anchors):
    """im = RGBA 프레임 · k = 지금 줄 · plan = 모션.json · anchors = 앵커프레임.json"""
    f0, f1 = line_range; L = max(1, f1 - f0); u = (fr - f0) / L
    for kind, arg, a, b in plan.get(str(k), []):
        t_in = (u - a) * L / FPS; t_out = (u - b) * L / FPS
        if t_in < 0 or t_out > 0.45: continue
        if kind == "숫자":
            al = ease(t_in / 0.2) if t_out < 0 else 1 - ease(t_out / 0.2)
            if al > 0: big_number(im, arg, al)
        elif kind == "알약":
            nm, s, col = arg; col = COL.get(col, col)
            if str(fr) in anchors: pill(im, anchors[str(fr)][nm], s, col, t_in, t_out)
    return im

if __name__ == "__main__":   # 자기 검사: 회색 바탕에 숫자 · 알약 · 자막이 그려지는가
    im = Image.new("RGBA", (W, H), (90, 90, 95, 255))
    apply(im, 50, 0, (0, 100), {"0": [["숫자", "1 / 10", 0.0, 0.9], ["알약", ["p", "똑같다", "초록"], 0.2, 0.9]]}, {"50": {"p": (0.5, 0.6)}})
    caption(im, "한 번에 똑같이 나왔어요")
    assert max(im.crop((W // 2 - 300, 420, W // 2 + 300, 520)).convert('L').getdata()) > 230, '흰 숫자 없음'
    assert im.getpixel((W // 2, int(0.6 * H) - 160 - 58 - 40))[:3] == (52, 199, 105), "알약 색"   # 글자 위쪽 알약 몸통
    print("ok")
