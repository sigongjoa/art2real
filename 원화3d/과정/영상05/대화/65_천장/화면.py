# 65 편(천장) 위쪽 화면 판 — 재료 out/영상05/대화/65_천장/자료/(실험_20261013/캐드부품/재료65.py) · 숫자는 결과판정52대조 · 결과판정51_천장
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/65_천장/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 40, 50), (130, 130, 140), (220, 160, 30)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _그림(c, n, box):
    im = Image.open(A + n + ".png").convert("RGBA"); im = im.crop(im.getbbox())
    x0, y0, x1, y1 = box; s = min((x1 - x0) / im.width, (y1 - y0) / im.height); im = im.resize((int(im.width * s), int(im.height * s))); c.alpha_composite(im, (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2))
def _둘(c, a, b, ta, tb, ca, cb, 아래):
    d = ImageDraw.Draw(c); _그림(c, a, (40, 150, 480, 600)); _그림(c, b, (520, 150, 960, 600))
    d.text((260, 90), ta, font=F(40), fill=ca, anchor="mm"); d.text((740, 90), tb, font=F(40), fill=cb, anchor="mm"); d.text((500, 650), 아래, font=F(32), fill=회, anchor="mm"); return c
def 판(키, p):
    if 키 == "컵위": return _둘(_카드(빨), "942_정답", "942_위", "정답", "위에서만 깎음  0.20", 초, 빨, "원뿔 컵 · 정답 칠을 그대로 넣음")
    if 키 == "컵여섯": return _둘(_카드(초), "942_위", "942_여섯", "위에서만  0.20", "여섯 방향  0.67", 빨, 초, "원뿔 컵 · 둘 다 정답을 넣음 · 학습 전")
    if 키 == "천장":
        c = _카드(금); d = ImageDraw.Draw(c); e = _쉬움(p * 1.5); X0, W_ = 330, 520; 자 = lambda v: X0 + int(W_ * (v - .5) / .4)
        d.text((500, 80), "정답을 넣었을 때 · 712 개 평균", font=F(40), fill=먹, anchor="mm")
        for i, (t, v, 색) in enumerate((("틀만", .635, 회), ("위에서만", .680, 빨), ("여섯 방향", .803, 초))):
            y = 170 + i * 150; d.text((50, y + 35), t, font=F(38), fill=먹, anchor="lm"); w = 자(.5 + (v - .5) * e); d.rounded_rectangle((X0, y, max(w, X0 + 1), y + 70), 14, fill=색); d.text((w + 15, y + 35), "%.2f" % v, font=F(40), fill=색, anchor="lm")
        d.text((500, 650), "모델 없이 · 정답 깊이로 지은 CAD", font=F(30), fill=회, anchor="mm"); return c
    if 키 == "느림":
        c = _카드(빨); d = ImageDraw.Draw(c); e = _쉬움(p * 1.5); X0, W_ = 360, 480
        d.text((500, 90), "부품 40 개 CAD 짓는 시간", font=F(42), fill=먹, anchor="mm")
        for i, (t, v, 색) in enumerate((("하나씩 깎기", 36, 빨), ("코드로 바로", 3.5, 초))):
            y = 200 + i * 200; d.text((50, y + 40), t, font=F(38), fill=먹, anchor="lm"); w = X0 + int(W_ * v / 36 * e); d.rounded_rectangle((X0, y, max(w, X0 + 1), y + 80), 14, fill=색); d.text((min(w + 15, 820), y - 32), "%g 분" % v, font=F(40), fill=색, anchor="lm")
        d.text((500, 640), "같은 모양 · 불리언 수천 번 → 한 번", font=F(32), fill=회, anchor="mm"); return c
    raise KeyError(키)
