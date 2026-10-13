# 49 편 위쪽 화면 판 — 재료 out/영상05/대화/49_진짜그림/자료 (기능0/자료49.py · 메카2 삼면.png 자체 디자인) · 돌림 프레임 36 장
import math
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/49_진짜그림/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
파, 주, 초, 빨, 먹 = (60, 110, 230), (230, 130, 40), (60, 160, 80), (220, 50, 50), (40, 40, 50)
def _카드(w, h, 테=(255, 255, 255)):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _붙(c, p, xy, s):   # 흰 바탕은 투명으로(카드 테두리를 안 덮게)
    im = Image.open(A + p).convert("RGBA").resize((s, s)); a = im.convert("L").point(lambda v: 0 if v > 248 else 255); im.putalpha(a); c.alpha_composite(im, xy)
def _돌(이름, p, 시작=0, 속=.5): return "%s_%02d.png" % (이름, int((시작 + p * 속) * 36) % 36)
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def 판(키, p):
    if 키 in ("삼면", "위없음"):
        c = _카드(1000, 700, 빨 if 키 == "위없음" else 파); im = Image.open(A + "삼면.png").convert("RGBA"); im = im.resize((940, int(940 * im.height / im.width)))
        c.alpha_composite(im, (30, 40)); d = ImageDraw.Draw(c)
        for j, t in enumerate(("앞", "옆", "뒤")): d.text((30 + 940 * (.17, .48, .82)[j], 675), t, font=F(38), fill=먹, anchor="mm")
        if 키 == "위없음" and p > .15:
            d.rounded_rectangle((330, 250, 670, 420), 30, fill=(255, 255, 255, 235), outline=빨, width=8); d.text((500, 335), "위 ?", font=F(int(110 + 10 * math.sin(p * 9))), fill=빨, anchor="mm")
        return c
    if 키 == "머리그림":
        c = _카드(1000, 640, 파); d = ImageDraw.Draw(c)
        for j, (k, t) in enumerate((("머리_앞그림.png", "앞"), ("머리_옆그림.png", "옆"))): _붙(c, k, (60 + j * 470, 50), 420); d.text((270 + j * 470, 595), t, font=F(40), fill=먹, anchor="mm")
        if p > .3:   # 같은 높이 띠
            y0, y1 = 64, 456
            for y in (y0, y1): d.line((40, y, 960, y), fill=빨, width=5)
            d.text((500, 30), "같은 높이로 자름", font=F(34), fill=빨, anchor="mm")
        return c
    if 키 in ("앞판", "옆판"):
        앞 = 키 == "앞판"; col = 파 if 앞 else 주; c = _카드(1000, 700, col); d = ImageDraw.Draw(c)
        _붙(c, "머리_앞그림.png" if 앞 else "머리_옆그림.png", (40, 150), 300); d.text((190, 480), "앞 그림" if 앞 else "옆 그림", font=F(38), fill=먹, anchor="mm")
        d.polygon([(360, 280), (410, 300), (360, 320)], fill=col)
        _붙(c, _돌("머리_앞판" if 앞 else "머리_옆판", p), (420, 70), 560)
        d.text((700, 655), "앞모양을 뒤로 밀기" if 앞 else "옆모양을 옆으로 밀기", font=F(40), fill=col, anchor="mm"); return c
    if 키 == "겹침":
        c = _카드(1000, 700, 초); d = ImageDraw.Draw(c)
        이름 = "머리_겹침" if p < .5 else "머리_교차"; _붙(c, _돌(이름, p, 0, .4), (170, 40), 660)
        d.text((500, 660), "파랑 ∩ 주황" if p < .5 else "겹친 곳만 남김", font=F(42), fill=초 if p >= .5 else 먹, anchor="mm"); return c
    if 키 in ("머리결과", "발"):
        부 = "머리" if 키 == "머리결과" else "발"; c = _카드(1000, 640, 초); d = ImageDraw.Draw(c)
        _붙(c, 부 + "_앞그림.png", (30, 40), 270); _붙(c, 부 + "_옆그림.png", (30, 320), 270)
        _붙(c, _돌(부 + "_교차", p, .1, .7), (330, 0), 640); d.text((165, 615), "그림", font=F(34), fill=먹, anchor="mm"); d.text((650, 615), "만든 것", font=F(34), fill=초, anchor="mm"); return c
    if 키 == "볏":
        c = _카드(1000, 640, 빨); d = ImageDraw.Draw(c)
        _붙(c, "머리_앞그림.png", (20, 80), 310); _붙(c, "머리_옆그림.png", (345, 80), 310); _붙(c, _돌("머리_교차", 0, 0, 0), (670, 80), 310)
        for j, t in enumerate(("앞", "옆", "만든 것")): d.text((175 + j * 325, 420), t, font=F(36), fill=먹, anchor="mm")
        if p > .2:
            d.ellipse((130, 70, 220, 190), outline=빨, width=7)        # 앞 볏(가운데 위)
            d.ellipse((345 + 20, 70, 345 + 150, 220), outline=빨, width=7)   # 옆 볏(앞쪽으로 기움)
            d.ellipse((670 + 120, 120, 670 + 210, 200), outline=빨, width=7)   # 남은 토막
            d.text((500, 520), "볏 자리가 앞 · 옆에서 다르다", font=F(44), fill=빨, anchor="mm")
        return c
    if 키 in ("영번", "영번묻기"):   # 묻는 줄은 ? 만 · 답하는 줄에서 0 번이 하나씩
        묻 = 키 == "영번묻기"; c = _카드(1000, 640, 먹 if 묻 else 빨); d = ImageDraw.Draw(c); e = 0 if 묻 else _쉬움(p * 2.5)
        for j, t in enumerate(("회전", "공 관절", "3D 학생")):
            y = 120 + j * 150; d.text((300, y), t, font=F(64), fill=먹, anchor="lm")
            if 묻: d.text((760, y), "?", font=F(80), fill=먹, anchor="mm")
            elif e * 3 > j: d.text((760, y), "0 번", font=F(80), fill=빨, anchor="mm")
        if not 묻: d.text((500, 580), "남은 건 그림자 두 장", font=F(44), fill=초, anchor="mm")
        return c
    if 키 == "예고":
        c = _카드(1000, 640, 주); d = ImageDraw.Draw(c); _붙(c, "머리_옆그림.png", (40, 60), 440); _붙(c, _돌("머리_교차", p, 0, .3), (500, 60), 460)
        d.ellipse((60, 60, 230, 300), outline=주, width=9); d.text((500, 590), "다음: 잘린 볏 되살리기", font=F(46), fill=주, anchor="mm"); return c
    raise KeyError(키)
