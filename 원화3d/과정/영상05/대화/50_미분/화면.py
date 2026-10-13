# 50 편 위쪽 화면 판 — 재료 out/설명/미분 (실험_20261013/미분그림.py 블렌더 렌더 · 예시 그림 · 점수는 예시)
import math
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/설명/미분/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
노, 초, 빨, 먹, 회 = (230, 180, 40), (60, 160, 80), (220, 50, 50), (40, 40, 50), (120, 120, 130)
def _카드(w, h, 테):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _붙(c, p, xy, w):
    im = Image.open(A + p).convert("RGBA"); im = im.resize((w, int(im.height * w / im.width))); c.alpha_composite(im, xy); return im.height
def _화소(접두, p, 테, 말0, 말1, 색1):   # 앞 반은 폭 3.0 · 뒤 반은 폭 3.4
    c = _카드(1000, 700, 테); d = ImageDraw.Draw(c); 뒤 = p > .45
    _붙(c, "%s_%s.png" % (접두, "34" if 뒤 else "30"), (145, 100), 710)
    d.rounded_rectangle((40, 22, 960, 82), 18, fill=(30, 32, 40)); d.text((500, 52), (말1 if 뒤 else 말0), font=F(40), fill=(색1 if 뒤 else (240, 240, 245)), anchor="mm")
    return c
def 판(키, p):
    if 키 == "딱딱": return _화소("1_딱딱", p, 빨, "상자 폭 3.0", "폭 3.4 — 켜진 칸 똑같음", (255, 110, 100))
    if 키 == "부드": return _화소("2_부드", p, 초, "흐리게 · 폭 3.0", "폭 3.4 — 가장자리 칸이 밝아짐", (110, 220, 130))
    if 키 == "보상":
        c = _카드(1000, 700, 노); d = ImageDraw.Draw(c); h = _붙(c, "3_보상.png", (20, 40), 960)
        for k, (t, s) in enumerate((("상자", ".55"), ("원기둥", ".48"), ("구멍 블록", ".93"), ("ㄱ자", ".41"))):
            if p > .15 + .12 * k: d.text((150 + k * 235, 40 + h + 20), "%s %s" % (t, s), font=F(34), fill=초 if k == 2 else 먹, anchor="mm")
        d.text((500, 650), "후보 코드를 지어 보고 점수 (예시)", font=F(34), fill=회, anchor="mm"); return c
    if 키 == "다듬기":
        c = _카드(1000, 700, 초); d = ImageDraw.Draw(c); k = min(3, int(p * 4.2))
        _붙(c, "4_다듬기_%d.png" % k, (250, 40), 500)
        d.text((500, 600), "구멍 반지름  %s" % ("0.15", "0.30", "0.42", "0.50 = 목표")[k], font=F(48), fill=초 if k == 3 else 먹, anchor="mm")
        d.text((500, 655), "흰 테 = 목표", font=F(30), fill=회, anchor="mm"); return c
    if 키 == "예고":
        c = _카드(1000, 700, 노); d = ImageDraw.Draw(c)
        for j, (t, col) in enumerate((("① 흐리게 그리기", 초), ("② 점수로 배우기", 노), ("③ 숫자만 찔러 보기", 초))):
            if p > j * .2: d.text((500, 170 + j * 150), t, font=F(70), fill=col, anchor="mm")
        d.text((500, 620), "다음: 진짜 부품에서 비교", font=F(42), fill=빨, anchor="mm"); return c
    raise KeyError(키)
