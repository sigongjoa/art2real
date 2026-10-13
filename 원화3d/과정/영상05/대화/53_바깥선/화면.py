# 53 편 위쪽 화면 판 — 재료 out/영상05/대화/53_바깥선/자료/*.npz (실험_20261013/구멍/재료53.py) · 렌더 out/설명/구멍/빛_r*.png
import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
A = "G:/art2real/out/영상05/대화/53_바깥선/자료/"; R = "G:/art2real/out/설명/구멍/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 파, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 110, 220), (40, 40, 50), (130, 130, 140), (220, 160, 30)
_D = {}
def D(n):
    if n not in _D: _D[n] = dict(np.load(A + n + ".npz"))
    return _D[n]
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _렌더(p, s):
    im = Image.open(R + p).convert("RGB").crop((180, 160, 720, 700)).resize((s, s)); m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).rounded_rectangle((4, 4, s - 4, s - 4), 24, fill=255); im = im.convert("RGBA"); im.putalpha(m); return im
def _판(n, s, 물=None, 윤곽=0.0, 회색안=False):   # 128 그림을 s 크기로: 선(검정) · 물(파랑) · 바깥 선(초록, 0~1 만큼 그려짐)
    d = D(n); g = d["그림"]; k = s / 128; img = np.full((128, 128, 3), 250, np.uint8)
    if 물 is not None: w = d["물"]; m = (w >= 0) & (w <= 물); img[m] = (150, 200, 245)
    img[g > .3] = (175, 175, 185) if 회색안 else (30, 30, 35)
    im = Image.fromarray(img).resize((s, s), Image.NEAREST); dr = ImageDraw.Draw(im)
    if 윤곽 > 0:
        ct = d["윤곽"]; n_ = max(2, int(len(ct) * min(윤곽, 1))); p = [(x * k + k / 2, y * k + k / 2) for x, y in ct[:n_]]; dr.line(p, fill=초, width=7)
    return im
def 판(키, p):
    if 키 == "상자들":
        c = _카드(빨); d = ImageDraw.Draw(c)
        for j in range(6): c.alpha_composite(_렌더("빛_r52_s0000_%d.png" % j, 290), (40 + (j % 3) * 310, 60 + (j // 3) * 310))
        d.text((500, 30), "52 편 걸음 0 — 6 칸 모두 직사각형", font=F(36), fill=빨, anchor="mm"); return c
    if 키 == "바깥선":
        c = _카드(초); d = ImageDraw.Draw(c); c.paste(_판("머리", 520, 윤곽=_쉬움(p * 1.4), 회색안=p > .5), (240, 60)); d.text((500, 640), "제일 바깥을 두르는 선", font=F(40), fill=초, anchor="mm"); return c
    if 키 == "물붓기":
        c = _카드(파); d = ImageDraw.Draw(c); w = D("머리")["물"]; 끝 = int(w.max() * min(1, p * 1.5))
        c.paste(_판("머리", 520, 물=끝, 윤곽=1.0 if p > .7 else 0, 회색안=p > .7), (240, 50))
        d.text((500, 640), "테두리에서 물 붓기 → 닿는 곳 = 바깥" if p <= .7 else "물이 멈춘 경계 = 바깥 선 · 안쪽은 무시", font=F(36), fill=파 if p <= .7 else 초, anchor="mm"); return c
    if 키 == "원판정":
        c = _카드(금); d = ImageDraw.Draw(c)
        for j, n in enumerate(("원기둥", "머리")):
            x0 = 40 + j * 480; im = _판(n, 440, 회색안=True); dr = ImageDraw.Draw(im); dd = D(n); k = 440 / 128; cx, cy = dd["중심"] * k + k / 2; ct = dd["윤곽"]
            for i in range(0, len(ct), max(1, len(ct) // 24))[: int(24 * min(1, p * 1.6)) + 1]:
                x, y = ct[i] * k + k / 2; dr.line((cx, cy, x, y), fill=금, width=3)
            dr.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=빨); c.paste(im, (x0, 60))
            if p > .6:
                원 = bool(dd["원"][0]); d.text((x0 + 220, 540), "거리가 거의 같음 → 원" if 원 else "들쭉날쭉 → 다각형", font=F(32), fill=초 if 원 else 빨, anchor="mm")
                d.text((x0 + 220, 590), "흩어짐 %.1f%%" % (100 * dd["흩어짐"][0]), font=F(30), fill=회, anchor="mm")
        return c
    if 키 == "꼭짓점":
        c = _카드(파); d = ImageDraw.Draw(c); dd = D("머리"); s = 560; k = s / 128; im = Image.new("RGB", (s, s), (250, 250, 250)); dr = ImageDraw.Draw(im)
        ct = dd["윤곽"]; vx = dd["꼭짓점"]; t = min(1, p * 1.5)
        dr.line([(x * k, y * k) for x, y in ct] + [(ct[0][0] * k, ct[0][1] * k)], fill=(190, 190, 200), width=3)
        if t < .5:
            for x, y in ct: dr.ellipse((x * k - 3, y * k - 3, x * k + 3, y * k + 3), fill=회)
            n = len(ct)
        else:
            q = [(x * k, y * k) for x, y in vx]; dr.line(q + [q[0]], fill=파, width=5)
            for x, y in q: dr.ellipse((x - 8, y - 8, x + 8, y + 8), fill=빨)
            n = len(vx)
        c.paste(im, (220, 40)); d.text((500, 640), "윤곽 점 %d 개" % n if t < .5 else "꺾이는 점만 %d 개" % n, font=F(40), fill=회 if t < .5 else 파, anchor="mm"); return c
    if 키 == "밀기":
        c = _카드(초); d = ImageDraw.Draw(c); dd = D("머리"); s = 300; k = s / 128; im = Image.new("RGB", (s, s), (250, 250, 250)); dr = ImageDraw.Draw(im)
        q = [(x * k, y * k) for x, y in dd["꼭짓점"]]; dr.polygon(q, fill=(200, 225, 250), outline=파); c.paste(im, (40, 200))
        d.text((420, 340), "→", font=F(80), fill=회, anchor="mm"); c.alpha_composite(_렌더("빛_r윤곽바탕_2.png", 470), (490, 110))
        d.text((190, 540), "윤곽", font=F(34), fill=먹, anchor="mm"); d.text((725, 620), "CadQuery 로 밀어 올림", font=F(34), fill=초, anchor="mm"); return c
    if 키 == "비교":
        c = _카드(초); d = ImageDraw.Draw(c)
        for j, (n, r) in enumerate((("원기둥", "빛_r윤곽바탕_0.png"), ("상자", "빛_r윤곽바탕_1.png"), ("머리", "빛_r윤곽바탕_2.png"))):
            x0 = 30 + j * 320; c.paste(_판(n, 300), (x0 + 5, 40)); c.alpha_composite(_렌더(r, 300), (x0 + 5, 360))
        return c
    raise KeyError(키)
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
