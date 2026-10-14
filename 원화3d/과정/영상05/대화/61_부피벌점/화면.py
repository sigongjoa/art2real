# 61 편(부피 벌점) 위쪽 화면 판 — 재료 out/영상05/대화/61_부피벌점/자료/(실험_20261013/캐드부품/재료61.py) · 숫자는 결과판정40 · 41 · 42 · 벌점42 그림
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/61_부피벌점/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 40, 50), (130, 130, 140), (220, 160, 30)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _그림(c, n, box, 기준=None):   # 3D 는 같은 부품끼리 같은 잘라내기 상자(기준)
    im = Image.open(A + n + ".png").convert("RGBA"); im = im.crop(Image.open(A + 기준 + ".png").convert("RGBA").getbbox() if 기준 else im.getbbox())
    x0, y0, x1, y1 = box; s = min((x1 - x0) / im.width, (y1 - y0) / im.height); im = im.resize((int(im.width * s), int(im.height * s))); c.alpha_composite(im, (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2))
def _둘(c, a, b, 왼, 오, 색왼=먹, 색오=먹, 기준=None):
    d = ImageDraw.Draw(c); _그림(c, a, (40, 150, 490, 620), 기준); _그림(c, b, (510, 150, 960, 620), 기준); d.text((265, 95), 왼, font=F(38), fill=색왼, anchor="mm"); d.text((735, 95), 오, font=F(38), fill=색오, anchor="mm")
def 판(키, p):
    c = _카드(빨 if 키 in ("판사라짐", "칠41", "남은판") else 금 if 키 in ("선비교", "벌점") else 초); d = ImageDraw.Draw(c)
    if 키 == "판사라짐": _둘(c, "261_틀", "261_39", "틀로 찍음 0.90", "모델이 깎음 0.05", 초, 빨, "261_틀"); return c
    if 키 == "선비교": _둘(c, "선_30", "선_261", "진짜 구멍: 안쪽 선", "이 판: 안쪽 선 없음", 초, 빨); return c
    if 키 == "칠41": _둘(c, "칠_261_정답", "칠_261_41", "정답: 꽉 찬 판", "벌점 낮춘 모델", 초, 빨); d.text((500, 650), "빨강 = 뚫음", font=F(32), fill=빨, anchor="mm"); return c
    if 키 in ("벌점", "벌점2"):
        _그림(c, "기둥_261", (40, 140, 480, 470)); _그림(c, "기둥_605", (520, 140, 960, 470)); d.text((260, 100), "부품을 날림", font=F(38), fill=빨, anchor="mm"); d.text((740, 100), "색만 틀림 · 모양 같음", font=F(38), fill=먹, anchor="mm")
        e = _쉬움(p * 1.5)
        for x, (예, 새) in ((260, (.91, .89)), (740, (1.00, .04))):
            d.text((x, 530), "칸 벌점 %.2f" % 예, font=F(40), fill=회, anchor="mm")
            if 키 == "벌점2": d.text((x, 610), "부피 벌점 %.2f" % (새 * e if e < 1 else 새), font=F(48), fill=빨 if 새 > .5 else 초, anchor="mm")
        return c
    if 키 == "판정":
        e = _쉬움(p * 1.5); X0, W_ = 300, 600; 자 = lambda v: X0 + int(W_ * (v - .6) / .08)
        for i_, (t, v, 색) in enumerate((("틀만", .647, 회), ("예전 학습", .653, 빨), ("부피로 학습", .665, 초))):
            y = 150 + i_ * 140; d.text((50, y + 32), t, font=F(36), fill=먹, anchor="lm"); w = 자(.6 + (v - .6) * e); d.rounded_rectangle((X0, y, max(w, X0 + 1), y + 64), 12, fill=색); d.text((w + 15, y + 32), "%.3f" % v, font=F(38), fill=색, anchor="lm")
        x = 자(.657); [d.line((x, yy, x, yy + 18), fill=먹, width=5) for yy in range(120, 580, 30)]; d.text((x, 615), "기준 0.657", font=F(34), fill=먹, anchor="mm"); d.text((X0, 615), "0.60", font=F(26), fill=회, anchor="mm"); d.text((500, 665), "처음 보는 시험 부품 803 개", font=F(28), fill=회, anchor="mm"); return c
    if 키 == "전후323": _둘(c, "323_39", "323_42", "예전 학습 0.14", "부피로 학습 0.58", 빨, 초, "323_틀"); return c
    if 키 == "남은판": _둘(c, "261_틀", "261_42", "틀로 찍음 0.90", "부피로 학습 0.30", 초, 빨, "261_틀"); return c
    raise KeyError(키)
