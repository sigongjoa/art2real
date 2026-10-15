# 66 편(영역) 위쪽 화면 판 — 재료 out/영상05/대화/66_영역/자료/(실험_20261013/캐드부품/재료66.py) · 숫자는 결과판정53_영역 · 천장51 · 나 판0
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/66_영역/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 40, 50), (130, 130, 140), (220, 160, 30)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _그림(c, n, box, 가까이=False):
    im = Image.open(A + n + ".png").convert("RGBA"); im = im.crop(im.getbbox()) if not 가까이 else im
    x0, y0, x1, y1 = box; s = min((x1 - x0) / im.width, (y1 - y0) / im.height); im = im.resize((int(im.width * s), int(im.height * s)), Image.NEAREST); c.alpha_composite(im, (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2))
def _막대(c, 줄, 제목, 아래, 최소=.5, 폭=.4):
    d = ImageDraw.Draw(c); e = _쉬움(1); X0, W_ = 380, 470; 자 = lambda v: X0 + int(W_ * (v - 최소) / 폭); d.text((500, 75), 제목, font=F(40), fill=먹, anchor="mm")
    for i, (t, v, 색) in enumerate(줄):
        y = 150 + i * 115; d.text((40, y + 32), t, font=F(34), fill=먹, anchor="lm"); w = 자(v); d.rounded_rectangle((X0, y, max(w, X0 + 1), y + 64), 12, fill=색); d.text((w + 12, y + 32), "%.2f" % v, font=F(36), fill=색, anchor="lm")
    d.text((500, 655), 아래, font=F(28), fill=회, anchor="mm"); return c
def 판(키, p):
    if 키 == "표":
        c = _카드(빨); d = ImageDraw.Draw(c); d.text((500, 80), "712 개 부품 중", font=F(40), fill=먹, anchor="mm")
        for i, (t, n, 색) in enumerate((("정답 깊이로 지으면 0.90 · 모델 0.58", 112, 빨), ("정답 깊이로도 0.5 아래", 89, 회), ("둘 다 잘 됨", 413, 초))):
            y = 170 + i * 150; d.rounded_rectangle((60, y, 60 + int(560 * n / 413 * _쉬움(p * 1.5)), y + 80), 14, fill=색); d.text((640, y + 40), "%d 개" % n, font=F(44), fill=색, anchor="lm"); d.text((60, y + 105), t, font=F(30), fill=먹, anchor="lm")
        return c
    if 키 == "영역":
        c = _카드(금); d = ImageDraw.Draw(c); _그림(c, "942_영역", (250, 120, 750, 600), True); d.text((500, 75), "원뿔 컵 위 그림 · 선으로 닫힌 칸 255 개", font=F(38), fill=먹, anchor="mm"); d.text((500, 650), "색 하나 = 칸 하나", font=F(30), fill=회, anchor="mm"); return c
    if 키 == "상관":
        c = _카드(금); d = ImageDraw.Draw(c); _그림(c, "상관", (60, 120, 940, 620)); d.text((500, 75), "칸이 많을수록 모델이 더 모자람(상관 +0.42)", font=F(36), fill=먹, anchor="mm"); return c
    if 키 == "천장": return _막대(_카드(빨), (("그대로", .801, 초), ("칸마다 깊이 하나", .687, 빨), ("칸마다 평면", .704, 빨), ("그려진 세 면만 평면", .769, 금)), "정답 깊이에 칸 규칙을 걸면", "모델 없이 · 712 개 평균")
    if 키 == "모델": return _막대(_카드(금), (("모델 그대로", .697, 초), ("칸마다 다수결", .643, 빨), ("칸마다 평면", .649, 빨)), "모델 예측에 칸 규칙을 걸면", "712 개 평균 · 학습은 그대로", .5, .3)
    if 키 == "원통":
        c = _카드(빨); d = ImageDraw.Draw(c); _그림(c, "475_앞깊이", (60, 130, 940, 600)); d.text((500, 75), "너트를 앞에서 본 깊이 · 색 = 깊이", font=F(38), fill=먹, anchor="mm"); d.text((500, 650), "선 사이 한 칸 안에서도 색이 바뀐다", font=F(32), fill=빨, anchor="mm"); return c
    raise KeyError(키)
