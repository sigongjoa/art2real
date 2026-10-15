# 64 편(섬) 위쪽 화면 판 — 재료 out/영상05/대화/64_섬/자료/(실험_20261013/캐드부품/재료64.py) · 숫자는 결과판정50 · 부피IoU_50
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/64_섬/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 40, 50), (130, 130, 140), (220, 160, 30)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _그림(c, n, box):
    im = Image.open(A + n + ".png").convert("RGBA"); im = im.crop(im.getbbox())
    x0, y0, x1, y1 = box; s = min((x1 - x0) / im.width, (y1 - y0) / im.height); im = im.resize((int(im.width * s), int(im.height * s))); c.alpha_composite(im, (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2))
def _둘(c, a, b, ta, tb, ca, cb, 아래):
    d = ImageDraw.Draw(c); _그림(c, a, (40, 150, 480, 600)); _그림(c, b, (520, 150, 960, 600))
    d.text((260, 90), ta, font=F(40), fill=ca, anchor="mm"); d.text((740, 90), tb, font=F(40), fill=cb, anchor="mm"); d.text((500, 650), 아래, font=F(32), fill=회, anchor="mm"); return c
def 판(키, p):
    if 키 == "너트": return _둘(_카드(빨), "475_정답", "475_옛", "정답", "만든 것  0.28", 초, 빨, "너트 · 같은 모델 칠")
    if 키 == "칠": return _둘(_카드(금), "475_정답칠", "475_모델칠", "정답 칠", "모델 칠", 먹, 먹, "회색 윗면 · 빨강 구멍 · 파랑 파인 곳")
    if 키 == "단면":
        c = _카드(빨); d = ImageDraw.Draw(c); _그림(c, "475_정답칠", (60, 170, 440, 550))
        d.ellipse((90, 200, 410, 520), outline=빨, width=10); d.text((250, 110), "바깥선만 땀", font=F(40), fill=빨, anchor="mm")
        _그림(c, "475_옛", (520, 170, 960, 550)); d.text((740, 110), "안쪽 고리도 깎임", font=F(40), fill=빨, anchor="mm"); d.text((500, 650), "파랑 영역 안의 섬을 못 봄", font=F(32), fill=회, anchor="mm"); return c
    if 키 == "너트새": return _둘(_카드(초), "475_옛", "475_새", "고치기 전  0.28", "고친 뒤  0.67", 빨, 초, "너트 · 같은 모델 칠 · 학습 그대로")
    if 키 == "플랜지": return _둘(_카드(초), "264_옛", "264_새", "고치기 전  0.42", "고친 뒤  0.91", 빨, 초, "플랜지 · 712 개 평균 0.653 → 0.663")
    if 키 == "컵": return _둘(_카드(금), "942_정답", "942_새", "정답", "고친 뒤  0.17", 초, 금, "원뿔 컵 · 위에서만 깎는 방식의 한계")
    raise KeyError(키)
