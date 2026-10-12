# 45 편 위쪽 화면 판 — 판(키, 진행 0~1) → RGBA (≤ 1000 × 760) · 재료 out/영상05/대화/45_판결/자료 (트레일 기능0/자료45.py)
# 화면 부품은 변형 허용 라이선스만: 회전 #17 TALON(BY-NC) · #26 Mandalorian(BY-NC-SA) · #30 Jet Engine(BY) · #32 Dante(BY-NC-SA) · 시험 #22 #4(42 편 확인) · #28 #29 타이거 전차(ND)는 뺌
import math
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/45_판결/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
노, 파, 초, 빨, 보, 먹 = (190, 150, 30), (60, 120, 220), (60, 160, 80), (220, 50, 50), (170, 90, 190), (40, 40, 50)
def _카드(w, h, 테=(255, 255, 255)):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _붙(c, p, xy, s): c.alpha_composite(Image.open(A + p).convert("RGBA").resize((s, s)), xy)
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _도장(d, xy, t, col, s=1.0):
    x, y = xy; w = int(len(t) * 34 * s + 40); d.rounded_rectangle((x - w // 2, y - int(30 * s), x + w // 2, y + int(30 * s)), 16, fill=col); d.text((x, y), t, font=F(int(40 * s)), fill="white", anchor="mm")
def 판(키, p):
    if 키 == "점수판":   # 막대가 자라 오름 — 처음 보는 부품 40 통과율
        c = _카드(1000, 700, 빨); d = ImageDraw.Draw(c); d.text((500, 55), "처음 보는 부품 40개 · 통과율", font=F(44), fill=먹, anchor="mm"); e = _쉬움(p * 2.5)
        for j, (t, v, col) in enumerate((("우리", .35, 초), ("그림자 3개 겹침", .45, 파))):
            x = 220 + j * 420; h = int(440 * v / .5 * e); d.rectangle((x - 90, 620 - h, x + 90, 620), fill=col); d.text((x, 600 - h), "%d%%" % round(v * 100 * e), font=F(64), fill=col, anchor="mb"); d.text((x, 660), t, font=F(36), fill=먹, anchor="mm")
        return c
    if 키 == "함정":   # 20 칸 중 19 칸 초록
        c = _카드(1000, 640, 초); d = ImageDraw.Draw(c); d.text((500, 55), "몰래 넣은 함정 쌍", font=F(44), fill=먹, anchor="mm"); n = min(20, int(p * 30))
        for q in range(20):
            x, y = 120 + (q % 10) * 80, 170 + (q // 10) * 130; col = (200, 205, 215) if q >= n else (초 if q != 13 else 빨)
            d.rounded_rectangle((x - 32, y - 45, x + 32, y + 45), 12, fill=col)
        d.text((500, 520), "똑같은 쌍 10 · 엉뚱한 쌍 10", font=F(36), fill=먹, anchor="mm"); return c
    if 키 == "범인":
        c = _카드(1000, 700, 빨); d = ImageDraw.Draw(c)
        for r_, i in enumerate((22, 4)):
            y = 30 + r_ * 330
            for j, (src, t, col) in enumerate((("뒤사", "사람", 노), ("뒤교", "그림자 겹침 ✓", 파), ("뒤우", "우리", 빨))):
                _붙(c, "%s_%02d.png" % (src, i), (30 + j * 320, y), 290)
                d.text((175 + j * 320, y + 300), t.replace(" ✓", ""), font=F(28), fill=col, anchor="mm")
        if p > .3: _도장(d, (500, 345), "우리 = 얇은 조각 · 찢긴 벽", 빨, 0.9)
        return c
    if 키 == "회전체":
        c = Image.new("RGBA", (1000, 640), (0, 0, 0, 0))
        for j, (i, tt) in enumerate(((30, "제트 엔진 터빈"), (32, "바퀴"))):
            k = _카드(470, 560, 보); s = int(380 + 30 * math.sin(p * 6 + j)); _붙(k, "사_%02d.png" % i, ((470 - s) // 2, 30), s); ImageDraw.Draw(k).text((235, 505), tt, font=F(40), fill=보, anchor="mm"); c.alpha_composite(k, (j * 530, 40))
        return c
    if 키 == "각진상자":
        c = Image.new("RGBA", (1000, 640), (0, 0, 0, 0))
        for j, (src, tt, col) in enumerate((("사_17.png", "사람이 만든 것", 노), ("교_17.png", "그림자 겹침", 파))):
            k = _카드(470, 560, col); _붙(k, src, (25, 30), 420); ImageDraw.Draw(k).text((235, 505), tt, font=F(40), fill=col, anchor="mm"); c.alpha_composite(k, (j * 530, 40))
        return c
    if 키 in ("돌림", "돌림끝"):
        c = _카드(1000, 700, 보); d = ImageDraw.Draw(c); t = 11 if 키 == "돌림끝" else min(11, int(p * 1.3 * 12))
        _붙(c, "돌림_%02d.png" % t, (210, 90), 580); d.text((500, 50), "%d°" % round(20 + (340 * t / 11)), font=F(52), fill=보, anchor="mm"); return c
    if 키 == "오대일":   # 네 쌍(화면 허용) + 5 대 1
        c = _카드(1000, 760, 보); d = ImageDraw.Draw(c); d.text((500, 40), "그림자 겹침  vs  한 바퀴 돌림", font=F(38), fill=먹, anchor="mm")
        for q, i in enumerate((17, 26, 30, 32)):
            x, y = 20 + (q % 2) * 490, 80 + (q // 2) * 300
            _붙(c, "교_%02d.png" % i, (x, y), 230); _붙(c, "회_%02d.png" % i, (x + 235, y), 230)
            if p * 5 > q: d.text((x + 115, y + 245), "실패" if i in (17, 26) else "애매", font=F(28), fill=빨 if i in (17, 26) else (200, 140, 30), anchor="mm"); d.text((x + 350, y + 245), "통과" if i != 30 else "애매", font=F(28), fill=초 if i != 30 else (200, 140, 30), anchor="mm")
        if p > .6: _도장(d, (500, 700), "6개 중 5 대 1", 보, 1.2)
        return c
    raise KeyError(키)
