# 67 편(잘됨) 위쪽 화면 판 — 재료 out/영상05/대화/67_잘됨/자료/(실험_20261013/캐드부품/재료67.py) · 숫자는 학습54나_판0 부피IoU · 묶음55
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/67_잘됨/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 40, 50), (130, 130, 140), (220, 160, 30)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _그림(c, n, box):
    im = Image.open(A + n + ".png").convert("RGBA"); im = im.crop(im.getbbox())
    x0, y0, x1, y1 = box; s = min((x1 - x0) / im.width, (y1 - y0) / im.height); im = im.resize((int(im.width * s), int(im.height * s))); c.alpha_composite(im, (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2))
def 판(키, p):
    if 키 in ("잘됨", "모양"):
        c = _카드(초 if 키 == "잘됨" else 금); d = ImageDraw.Draw(c)
        for i, (n, t) in enumerate((("447_정답", "판"), ("760_정답", "고리"), ("667_정답", "막대"), ("365_정답", "판"))):
            x = 40 + i * 235; _그림(c, n, (x, 170, x + 215, 520))
            if 키 == "모양": d.text((x + 107, 580), t, font=F(44), fill=금, anchor="mm")
        d.text((500, 85), "0.9 넘은 부품 244 개 중 넷" if 키 == "잘됨" else "열어 보니 · 밀어낸 모양", font=F(42), fill=먹, anchor="mm"); return c
    if 키 == "틀":
        c = _카드(빨); d = ImageDraw.Draw(c); _그림(c, "365_정답", (40, 160, 470, 520)); _그림(c, "365_틀", (530, 160, 960, 520))
        d.text((255, 100), "정답", font=F(40), fill=초, anchor="mm"); d.text((745, 100), "윤곽만 겹친 것 0.997", font=F(40), fill=금, anchor="mm")
        d.text((500, 610), "244 개 중 154 개는 모델 없이도 0.9", font=F(40), fill=빨, anchor="mm"); return c
    if 키 == "전체":
        c = _카드(금); d = ImageDraw.Draw(c); d.text((500, 80), "712 개 · 모델 대 윤곽만", font=F(42), fill=먹, anchor="mm"); e = _쉬움(p * 1.5)
        for i, (t, n, 색) in enumerate((("모델이 더 나음", 309, 초), ("거의 같음", 346, 회), ("모델이 더 못함", 57, 빨))):
            y = 170 + i * 150; d.text((50, y + 40), t, font=F(36), fill=먹, anchor="lm"); w = 400 + int(460 * n / 346 * e); d.rounded_rectangle((400, y, max(w, 401), y + 80), 14, fill=색); d.text((min(w + 15, 880), y + 40), "%d" % n, font=F(44), fill=색, anchor="lm")
        return c
    raise KeyError(키)
