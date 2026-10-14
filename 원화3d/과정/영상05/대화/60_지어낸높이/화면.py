# 60 편(지어낸 높이) 위쪽 화면 판 — 재료 out/영상05/대화/60_지어낸높이/자료/(실험_20261013/캐드부품/재료60.py · 시험 182 번) · 숫자는 결과판정38
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/60_지어낸높이/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 40, 50), (130, 130, 140), (220, 160, 30)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _그림(c, n, box):   # box 안에 비율 유지로
    im = Image.open(A + n + ".png").convert("RGBA"); im = im.crop(Image.open(A + "틀.png").convert("RGBA").getbbox() if n in ("틀", "최종", "지워짐") else im.getbbox()); x0, y0, x1, y1 = box; s = min((x1 - x0) / im.width, (y1 - y0) / im.height); im = im.resize((int(im.width * s), int(im.height * s))); c.alpha_composite(im, (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2))
def _둘(c, a, b, 왼, 오, 색왼=먹, 색오=먹):
    d = ImageDraw.Draw(c); _그림(c, a, (40, 150, 490, 620)); _그림(c, b, (510, 150, 960, 620)); d.text((265, 95), 왼, font=F(38), fill=색왼, anchor="mm"); d.text((735, 95), 오, font=F(38), fill=색오, anchor="mm")
def _막대(d, p, 줄, y0=200):
    e = _쉬움(p * 1.5)
    for i, (t, v, 색) in enumerate(줄):
        y = y0 + i * 150; d.text((60, y + 30), t, font=F(36), fill=먹, anchor="lm"); w = int(520 * v * e); d.rounded_rectangle((330, y, 330 + max(w, 1), y + 64), 12, fill=색); d.text((330 + w + 20, y + 32), "%.3f" % (v * e), font=F(40), fill=색, anchor="lm")
def 판(키, p):
    c = _카드(빨 if 키 in ("전후", "지워짐", "판정") else 금 if 키 in ("입력", "칠", "단면", "포갬") else 초); d = ImageDraw.Draw(c)
    if 키 == "전후": _둘(c, "틀", "최종", "틀로 찍음 0.89", "모델이 깎음 0.17", 초, 빨); return c
    if 키 == "입력": _둘(c, "선_위", "선_앞", "위에서 본 그림", "앞에서 본 그림"); d.text((500, 640), "값은 0 과 1 뿐", font=F(34), fill=회, anchor="mm"); return c
    if 키 == "칠": _둘(c, "칠_정답", "칠_모델", "정답", "모델", 초, 금); return c
    if 키 == "단면":
        _그림(c, "단면", (60, 170, 940, 560)); d.text((330, 110), "■ 정답 0.67", font=F(38), fill=초, anchor="mm"); d.text((690, 110), "■ 모델 0.86", font=F(38), fill=빨, anchor="mm")
        d.text((500, 620), "옆에서 자른 모양 · 위에서 판 깊이", font=F(30), fill=회, anchor="mm"); return c
    if 키 == "지워짐": _둘(c, "틀", "지워짐" if p > .35 else "틀", "세 방향 틀", "위에서 더 판 뒤", 초, 빨); return c
    if 키 == "포갬":
        _그림(c, "포갬", (150, 120, 850, 620)); d.text((300, 80), "■ 위 그림", font=F(36), fill=(0, 150, 255), anchor="mm"); d.text((700, 80), "■ 앞 그림", font=F(36), fill=(255, 0, 150), anchor="mm")
        d.text((500, 650), "빨간 원: 위에선 판 · 앞에선 허공", font=F(32), fill=빨, anchor="mm"); return c
    if 키 == "판정": _막대(d, p, (("틀만", .694, 초), ("모델이 깎음", .678, 빨))); d.text((500, 600), "시험 부품 200 개 평균", font=F(32), fill=회, anchor="mm"); return c
    raise KeyError(키)
