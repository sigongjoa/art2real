# 47 편 위쪽 화면 판 — 재료 out/영상05/대화/47_증류/자료 (기능0/자료47.py) · 42 편 21 사람 돌림판 · 화면 부품: 시험 #21 Robot Head(BY-NC-SA) 하나
import math
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/47_증류/자료/"; A42 = "G:/art2real/out/영상05/대화/42_각진덩어리/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
노, 파, 주, 초, 빨, 먹, 보 = (190, 150, 30), (60, 120, 220), (220, 110, 40), (60, 160, 80), (220, 50, 50), (40, 40, 50), (150, 90, 200)
def _카드(w, h, 테=(255, 255, 255)):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _붙(c, p, xy, s): c.alpha_composite(Image.open(p if ":" in p else A + p).convert("RGBA").resize((s, s)), xy)
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _도장(d, xy, t, col, s=1.0):
    x, y = xy; w = int(len(t) * 34 * s + 40); d.rounded_rectangle((x - w // 2, y - int(30 * s), x + w // 2, y + int(30 * s)), 16, fill=col); d.text((x, y), t, font=F(int(40 * s)), fill="white", anchor="mm")
def _둘(a, b, ta, tb, ca, cb, 화살=True):
    c = Image.new("RGBA", (1000, 640), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    for j, (src, tt, col) in enumerate(((a, ta, ca), (b, tb, cb))):
        k = _카드(470, 560, col); _붙(k, src, (25, 30), 420); ImageDraw.Draw(k).text((235, 505), tt, font=F(38), fill=col, anchor="mm"); c.alpha_composite(k, (j * 530, 40))
    if 화살: d.text((500, 320), "→", font=F(80), fill="white", stroke_width=6, stroke_fill=(10, 10, 20), anchor="mm")
    return c
def 판(키, p):
    t = int(p * 11.99) % 12
    if 키 == "선생학생": return _둘(A42 + "21사람_%02d.png" % t, "선_2.png", "선생 — 3D 를 다 봄", "학생 — 선 그림만", 보, 초, False)
    if 키 == "선생": return _둘(A42 + "21사람_%02d.png" % t, "정답_2.png", "3D 모델", "선생이 아는 깊이", 보, 보)
    if 키 == "문제지":
        c = _카드(1000, 640, 빨); d = ImageDraw.Draw(c); d.text((500, 55), "실제로 손에 있는 것", font=F(44), fill=빨, anchor="mm")
        for j, k in enumerate((0, 2, 4)): _붙(c, "선_%d.png" % k, (40 + j * 315, 140), 290)
        d.text((500, 520), "앞 · 옆 · 위 선 그림 세 장", font=F(38), fill=먹, anchor="mm"); return c
    if 키 == "따라하기":
        c = _카드(1000, 640, 초); d = ImageDraw.Draw(c); e = _쉬움(p * 2)
        for j, (src, tt, col) in enumerate((("선_2.png", "선 그림", 먹), ("학생_2.png", "학생 답", 초), ("정답_2.png", "선생 답", 보))):
            if j == 1 and e < .3: continue
            _붙(c, src, (30 + j * 320, 90), 300); d.text((180 + j * 320, 430), tt, font=F(36), fill=col, anchor="mm")
        d.text((345, 240), "→", font=F(60), fill=먹, anchor="mm"); d.text((660, 240), "=", font=F(60), fill=먹, anchor="mm"); d.text((500, 540), "학생이 선생 답을 따라 하게", font=F(38), fill=초, anchor="mm"); return c
    if 키 == "증류":   # 큰 원 → 작은 원 (지식이 흘러 들어감)
        c = _카드(1000, 640, 보); d = ImageDraw.Draw(c); e = _쉬움(p * 2)
        d.ellipse((80, 160, 400, 480), fill=보 + (255,)); d.text((240, 320), "선생\n3D", font=F(56), fill="white", anchor="mm", align="center")
        r = int(70 + 40 * e); d.ellipse((760 - r, 320 - r, 760 + r, 320 + r), fill=초 + (255,)); d.text((760, 320), "학생", font=F(44), fill="white", anchor="mm")
        for q in range(6):
            x = 420 + (q * 50 + int(p * 300)) % 270; d.ellipse((x - 10, 310, x + 10, 330), fill=보 + (255,))
        d.text((500, 560), "선 그림만으로 선생 흉내", font=F(38), fill=먹, anchor="mm"); return c
    if 키 == "오차":
        c = _카드(1000, 640, 초); d = ImageDraw.Draw(c); e = _쉬움(p * 2); d.text((500, 55), "깊이 오차 (작을수록 좋음)", font=F(42), fill=먹, anchor="mm")
        for j, (tt, v, col) in enumerate((("그림자만 겹침", .050, 파), ("학생", .041, 초))):
            y = 170 + j * 200; d.text((60, y - 10), tt, font=F(40), fill=col); w = int(820 * v / .055 * e); d.rounded_rectangle((60, y + 50, 60 + w, y + 120), 18, fill=col); d.text((70 + w, y + 85), "%.3f" % v, font=F(38), fill=col, anchor="lm")
        return c
    if 키 == "홈바닥":
        c = _둘("정답_2.png", "학생_2.png", "선생 — 홈이 깊다", "학생 — 자국만", 보, 빨, False); d = ImageDraw.Draw(c)
        if p > .2:
            for x0 in (25, 555): d.ellipse((x0 + 110, 220, x0 + 360, 430), outline=빨, width=10)
        return c
    raise KeyError(키)
