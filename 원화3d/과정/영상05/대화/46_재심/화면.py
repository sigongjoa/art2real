# 46 편 위쪽 화면 판 — 재료 out/영상05/대화/46_재심/자료 (기능0/자료46.py) · 42 편 재료(21 사람 · 교차 돌림판)
# 화면 부품은 변형 허용만: 검증2 #13 VacPack(BY-NC) · #38 BB-8(BY-NC) · #31 Curveball Mech(BY) · 시험 #34 Dummy13 · #21 Robot Head(42 편) · Volt(ND) 뺌
import math, random
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/46_재심/자료/"; A42 = "G:/art2real/out/영상05/대화/42_각진덩어리/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
노, 파, 주, 초, 빨, 먹 = (190, 150, 30), (60, 120, 220), (220, 110, 40), (60, 160, 80), (220, 50, 50), (40, 40, 50)
def _카드(w, h, 테=(255, 255, 255)):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _붙(c, p, xy, s): c.alpha_composite(Image.open(p if ":" in p else A + p).convert("RGBA").resize((s, s)), xy)
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _도장(d, xy, t, col, s=1.0):
    x, y = xy; w = int(len(t) * 34 * s + 40); d.rounded_rectangle((x - w // 2, y - int(30 * s), x + w // 2, y + int(30 * s)), 16, fill=col); d.text((x, y), t, font=F(int(40 * s)), fill="white", anchor="mm")
def 판(키, p):
    t = int(p * 11.99) % 12
    if 키 == "점수판":
        c = _카드(1000, 700, 주); d = ImageDraw.Draw(c); d.text((500, 55), "처음 보는 부품 40개 · 재심", font=F(44), fill=먹, anchor="mm"); e = _쉬움(p * 2.5)
        for j, (tt, col) in enumerate((("우리", 주), ("그림자 3개 겹침", 파))):
            x = 220 + j * 420; h = int(400 * e); d.rectangle((x - 90, 620 - h, x + 90, 620), fill=col); d.text((x, 600 - h), "%d" % round(21 * e), font=F(72), fill=col, anchor="mb"); d.text((x, 660), tt, font=F(36), fill=먹, anchor="mm")
        return c
    if 키 in ("링교", "링C"):
        c = _카드(1000, 700, 파 if 키 == "링교" else 주); d = ImageDraw.Draw(c); _붙(c, "%s_%02d.png" % (키, t), (230, 90), 540)
        d.text((500, 50), "그림자 겹침 — 다각형" if 키 == "링교" else "한 바퀴 돌림 — 동그라미", font=F(44), fill=파 if 키 == "링교" else 주, anchor="mm"); return c
    if 키 == "링판정":
        c = _카드(1000, 700, 먹); d = ImageDraw.Draw(c)
        for r_, i in enumerate((13, 38)):
            y = 30 + r_ * 330
            for j, (src, col) in enumerate((("사", 노), ("교", 파), ("C", 주))):
                _붙(c, "%s_검증2%02d.png" % (src, i), (40 + j * 320, y), 280)
                if j and p > .2: _도장(d, (180 + j * 320, y + 290), "통과", 초, .8)
        return c
    if 키 == "공둘":
        c = _카드(1000, 700, 주); d = ImageDraw.Draw(c)
        for r_, (s, i, 말, col) in enumerate((("시험", 34, "공 관절 ✓", 초), ("검증2", 31, "공 아닌데 공", 빨))):
            y = 30 + r_ * 330
            for j, src in enumerate(("사", "교", "C")): _붙(c, "%s_%s%02d.png" % (src, s, i), (40 + j * 320, y), 280)
            if p > .3 * (r_ + 1): _도장(d, (820, y + 290), 말.replace(" ✓", ""), col, .8)
        return c
    if 키 == "형태":
        c = Image.new("RGBA", (1000, 640), (0, 0, 0, 0))
        for j, (src, tt, col) in enumerate(((A42 + "21사람_%02d.png" % t, "사람이 만든 것", 노), (A42 + "21교차_%02d.png" % t, "규칙으로 잡은 형태", 파))):
            k = _카드(470, 560, col); _붙(k, src, (25, 30), 420); ImageDraw.Draw(k).text((235, 505), tt, font=F(38), fill=col, anchor="mm"); c.alpha_composite(k, (j * 530, 40))
        return c
    if 키 == "디테일":   # 같은 그림에 동그라미 — 창 · 속 빈 곳
        c = _카드(1000, 700, 빨); d = ImageDraw.Draw(c); _붙(c, A42 + "21사람_03.png", (230, 70), 540)
        if p > .3: d.ellipse((330, 170, 670, 560), outline=빨, width=12)
        d.text((500, 650), "그림자에는 안 보이는 창 · 속 빈 곳", font=F(38), fill=빨, anchor="mm"); return c
    if 키 == "학습":   # 2,883 칸이 하나씩 초록으로
        c = _카드(1000, 700, 초); d = ImageDraw.Draw(c); d.text((500, 50), "학습 부품 2,883개", font=F(44), fill=초, anchor="mm"); n = int(min(1, p * 1.4) * 900)
        rng = random.Random(4); 순 = list(range(900)); rng.shuffle(순); 켜 = set(순[:n])
        for q in range(900): x, y = 40 + (q % 45) * 20.5, 110 + (q // 45) * 27; d.rounded_rectangle((x, y, x + 16, y + 21), 4, fill=초 if q in 켜 else (205, 210, 220))
        return c
    raise KeyError(키)
