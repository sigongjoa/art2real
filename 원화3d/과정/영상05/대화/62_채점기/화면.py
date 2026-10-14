# 62 편(채점기) 위쪽 화면 판 — 재료 out/영상05/대화/62_채점기/자료/(실험_20261013/캐드부품/재료62.py · 669 번) · 숫자는 감사 기록(log.md 10-14) · 결과판정46
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/62_채점기/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 40, 50), (130, 130, 140), (220, 160, 30)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _그림(c, n, box, 기준=None):
    im = Image.open(A + n + ".png").convert("RGBA"); im = im.crop(Image.open(A + 기준 + ".png").convert("RGBA").getbbox() if 기준 else im.getbbox())
    x0, y0, x1, y1 = box; s = min((x1 - x0) / im.width, (y1 - y0) / im.height); im = im.resize((int(im.width * s), int(im.height * s))); c.alpha_composite(im, (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2))
def 판(키, p):
    c = _카드(빨 if 키 in ("옛", "감사", "겹침") else 초); d = ImageDraw.Draw(c)
    if 키 == "옛": _그림(c, "옛", (80, 130, 920, 620), "옛"); d.text((500, 80), "빨강 = 틀 밖에 생긴 칸 4285", font=F(40), fill=빨, anchor="mm"); d.text((500, 650), "깎기는 빼기만 하는데", font=F(32), fill=회, anchor="mm"); return c
    if 키 == "감사":
        _그림(c, "옛", (40, 150, 490, 600), "옛"); _그림(c, "옛_두번째", (510, 150, 960, 600), "옛")
        d.text((265, 100), "첫 번째: 틀 밖 4285", font=F(38), fill=빨, anchor="mm"); d.text((735, 100), "두 번째: 틀 밖 13", font=F(38), fill=금, anchor="mm"); d.text((500, 650), "같은 모양 · 옛 채점기로 두 번", font=F(32), fill=회, anchor="mm"); return c
    if 키 == "겹침": _그림(c, "겹침_0", (60, 150, 480, 600)); _그림(c, "겹침_1", (520, 150, 940, 600)); d.text((270, 100), "시험 부품", font=F(40), fill=먹, anchor="mm"); d.text((730, 100), "학습 부품", font=F(40), fill=먹, anchor="mm"); d.text((500, 650), "똑같은 그림 · 91 개", font=F(36), fill=빨, anchor="mm"); return c
    if 키 == "새": _그림(c, "새", (80, 130, 920, 620), "옛"); d.text((500, 80), "새 채점: 틀 밖 0 칸", font=F(40), fill=초, anchor="mm"); return c
    if 키 == "판정":
        e = _쉬움(p * 1.5); X0, W_ = 300, 600; 자 = lambda v: X0 + int(W_ * (v - .6) / .07)
        for i_, (t, v, 색) in enumerate((("틀만", .635, 회), ("예전 학습", .642, 빨), ("부피로 학습", .653, 초))):
            y = 150 + i_ * 140; d.text((50, y + 32), t, font=F(36), fill=먹, anchor="lm"); w = 자(.6 + (v - .6) * e); d.rounded_rectangle((X0, y, max(w, X0 + 1), y + 64), 12, fill=색); d.text((w + 15, y + 32), "%.3f" % v, font=F(38), fill=색, anchor="lm")
        x = 자(.645); [d.line((x, yy, x, yy + 18), fill=먹, width=5) for yy in range(120, 580, 30)]; d.text((x, 615), "기준 0.645", font=F(34), fill=먹, anchor="mm"); d.text((500, 665), "새 채점 · 겹친 부품 뺀 712 개", font=F(28), fill=회, anchor="mm"); return c
    raise KeyError(키)
