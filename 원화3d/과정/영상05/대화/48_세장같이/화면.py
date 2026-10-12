# 48 편 위쪽 화면 판 — 재료 out/영상05/대화/47_증류/자료 (기능0/자료47.py · 시험 #21 Robot Head BY-NC-SA) · 들어 올림 정육면체는 그 선 그림 셋을 면에 붙임
import math, numpy as np
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/47_증류/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
노, 파, 주, 초, 빨, 먹, 보 = (190, 150, 30), (60, 120, 220), (220, 110, 40), (60, 160, 80), (220, 50, 50), (40, 40, 50), (150, 90, 200)
def _카드(w, h, 테=(255, 255, 255)):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _붙(c, p, xy, s): c.alpha_composite(Image.open(A + p).convert("RGBA").resize((s, s)), xy)
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _도장(d, xy, t, col, s=1.0):
    x, y = xy; w = int(len(t) * 34 * s + 40); d.rounded_rectangle((x - w // 2, y - int(30 * s), x + w // 2, y + int(30 * s)), 16, fill=col); d.text((x, y), t, font=F(int(40 * s)), fill="white", anchor="mm")
def _계수(dst, src):   # 출력 네 점 → 입력 네 점 원근 변환 계수
    M = []; b = []
    for (x, y), (u, v) in zip(dst, src): M += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]; b += [u, v]
    return np.linalg.solve(np.array(M, float), np.array(b, float))
def _면(c, img, quad):
    s = img.size[0]; w = img.convert("RGBA").transform(c.size, Image.PERSPECTIVE, tuple(_계수(quad, [(0, 0), (s, 0), (s, s), (0, s)])), Image.BICUBIC)
    m = Image.new("L", c.size, 0); ImageDraw.Draw(m).polygon(quad, fill=255); c.paste(w, (0, 0), m)
def 판(키, p):
    if 키 == "홈바닥":
        c = Image.new("RGBA", (1000, 640), (0, 0, 0, 0))
        for j, (src, tt, col) in enumerate((("정답_2.png", "선생 — 홈이 깊다", 보), ("학생_2.png", "학생 — 자국만", 빨))):
            k = _카드(470, 560, col); _붙(k, src, (25, 30), 420); ImageDraw.Draw(k).text((235, 505), tt, font=F(38), fill=col, anchor="mm"); c.alpha_composite(k, (j * 530, 40))
        return c
    if 키 in ("한장씩", "단서"):
        c = _카드(1000, 640, 빨 if 키 == "한장씩" else 초); d = ImageDraw.Draw(c)
        for j, (k, tt) in enumerate(((2, "앞"), (0, "옆"), (4, "위"))):
            x = 40 + j * 315 + (int(20 * math.sin(p * 9 + j)) if 키 == "한장씩" else 0); _붙(c, "선_%d.png" % k, (x, 120), 290); d.text((x + 145, 440), tt, font=F(40), fill=먹, anchor="mm")
        if 키 == "한장씩":
            for j in (1, 2): d.line((40 + j * 315 - 12, 120, 40 + j * 315 - 12, 410), fill=빨, width=8)
            d.text((500, 55), "한 장씩 따로 본 학생", font=F(44), fill=빨, anchor="mm")
        else:
            d.text((500, 55), "깊이 단서는 다른 그림에", font=F(44), fill=초, anchor="mm")
            if p > .3: d.ellipse((40 + 0 * 315 + 60, 170, 40 + 0 * 315 + 230, 370), outline=빨, width=8); d.text((185, 540), "홈 자리", font=F(36), fill=빨, anchor="mm"); d.text((500, 540), "깊이 단서?", font=F(36), fill=초, anchor="mm"); d.text((815, 540), "깊이 단서?", font=F(36), fill=초, anchor="mm")
        return c
    if 키 == "들어올림":   # 세 장이 날아와 정육면체 세 면에 붙음
        c = _카드(1000, 700, 초); d = ImageDraw.Draw(c); e = _쉬움(p * 1.6); cx, cy, s = 500, 360, 245
        top = [(cx, cy - s), (cx + s * .87, cy - s * .5), (cx, cy), (cx - s * .87, cy - s * .5)]
        left = [(cx - s * .87, cy - s * .5), (cx, cy), (cx, cy + s), (cx - s * .87, cy + s * .5)]
        right = [(cx, cy), (cx + s * .87, cy - s * .5), (cx + s * .87, cy + s * .5), (cx, cy + s)]
        for q, (k, 면, dx, dy) in enumerate(((4, top, 0, -260), (2, left, -330, 120), (0, right, 330, 120))):
            off = (1 - e); quad = [(x + dx * off, y + dy * off) for x, y in 면]; _면(c, Image.open(A + "선_%d.png" % k), [tuple(map(int, t)) for t in quad])
            d.polygon([tuple(map(int, t)) for t in quad], outline=초 + (255,), width=4)
        if e > .95: d.text((500, 650), "칸마다 세 그림을 같이 본다", font=F(38), fill=초, anchor="mm")
        return c
    if 키 == "학습중":
        c = _카드(1000, 640, 초); d = ImageDraw.Draw(c); d.text((500, 180), "3D 학생 배우는 중…", font=F(70), fill=초, anchor="mm")
        d.rounded_rectangle((150, 330, 850, 400), 30, outline=초, width=6); d.rounded_rectangle((158, 338, 158 + int(684 * (.25 + .5 * p)), 392), 24, fill=초)
        d.text((500, 500), "부품 2,735개 · 64 × 64 × 64 칸", font=F(36), fill=먹, anchor="mm"); return c
    if 키 == "천장":
        c = _카드(1000, 640, 보); d = ImageDraw.Draw(c); d.text((500, 55), "깊이를 완벽히 알면?", font=F(46), fill=보, anchor="mm"); e = _쉬움(p * 2)
        for j, (tt, v, col) in enumerate((("지금 (홈 안 팜)", .275, 주), ("정답 깊이로 판 홈", None, 보))):
            x = 280 + j * 440; h = int(380 * (v or 0) / .5 * e) if v else 0
            if v: d.rectangle((x - 90, 560 - h, x + 90, 560), fill=col); d.text((x, 540 - h), "%d%%" % round(v * 100 * e), font=F(56), fill=col, anchor="mb")
            else: d.text((x, 400), "?", font=F(int(220 + 30 * math.sin(p * 8))), fill=col, anchor="mm")
            d.text((x, 600), tt, font=F(32), fill=먹, anchor="mm")
        return c
    if 키 == "모양":
        c = _카드(1000, 640, 주); d = ImageDraw.Draw(c); d.text((500, 160), "깊이가 아니라", font=F(64), fill=먹, anchor="mm"); d.text((500, 300), "홈 모양이 문제?", font=F(84), fill=주, anchor="mm")
        d.text((500, 470), "평평한 바닥 기둥만 팔 줄 안다", font=F(40), fill=빨, anchor="mm"); return c
    raise KeyError(키)
