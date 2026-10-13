# 50 편(구멍) 위쪽 화면 판 — 재료 out/설명/구멍 (실험_20261013/구멍/짓기 · 렌더 · 재기.py) · 점수는 실제로 잰 IoU
import json, math
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/설명/구멍/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); 코 = lambda n: ImageFont.truetype("C:/Windows/Fonts/consola.ttf", n)
파, 초, 빨, 먹, 회, 노 = (60, 110, 230), (50, 160, 80), (220, 50, 50), (40, 40, 50), (120, 120, 130), (230, 170, 30)
IOU = {int(k): v for k, v in json.load(open(A + "iou.json")).items() if k.isdigit()}   # 10-13 iou.json 에 시안용 「4엇」 · 0~2 도 들어감
def _카드(w, h, 테):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _붙(c, p, xy, s): im = Image.open(A + p).convert("RGBA").resize((s, s)); c.alpha_composite(im, xy)
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _코드(c, r, xy, 강조):
    d = ImageDraw.Draw(c); x, y = xy; d.rounded_rectangle((x, y, x + 900, y + 190), 20, fill=(28, 30, 38))
    d.text((x + 30, y + 30), "cq.Workplane().box(20, 20, 20)", font=코(40), fill=(200, 210, 230))
    d.text((x + 30, y + 100), "  .faces('>Z').hole(", font=코(40), fill=(200, 210, 230)); w = d.textlength("  .faces('>Z').hole(", font=코(40))
    d.text((x + 30 + w, y + 100), "%d" % (2 * r), font=코(40), fill=강조); w2 = d.textlength("%d" % (2 * r), font=코(40)); d.text((x + 30 + w + w2, y + 100), ")", font=코(40), fill=(200, 210, 230))
def 판(키, p):
    if 키 == "첫시도":
        c = _카드(1000, 700, 빨); d = ImageDraw.Draw(c); _붙(c, "그림_목표.png", (40, 110), 430); _붙(c, "비스듬_r3.png", (520, 100), 450)
        d.text((255, 60), "그림 (정답)", font=F(44), fill=먹, anchor="mm"); d.text((745, 60), "AI 가 뚫은 구멍", font=F(44), fill=빨, anchor="mm")
        if p > .4: d.ellipse((675, 195, 815, 280), outline=빨, width=8)
        return c
    if 키 == "코드":
        c = _카드(1000, 700, 먹); d = ImageDraw.Draw(c); d.text((500, 70), "AI 가 쓴 코드", font=F(48), fill=먹, anchor="mm")
        _코드(c, 3, (50, 140), (255, 120, 110)); d.text((500, 420), "지름 6 = 반지름 3", font=F(56), fill=빨, anchor="mm"); d.text((500, 520), "아무 숫자나 넣음", font=F(40), fill=회, anchor="mm"); return c
    if 키 == "짓기":
        c = _카드(1000, 700, 파); d = ImageDraw.Draw(c); _코드(c, 3, (50, 40), (255, 120, 110))
        e = _쉬움(p * 2.5); s = int(280 + 130 * e); _붙(c, "비스듬_r3.png", (500 - s // 2, 240 + (410 - s) // 2), s)
        d.text((500, 665), "코드 실행 → CAD", font=F(36), fill=파, anchor="mm"); return c
    if 키 == "비교":   # 앞 반: CAD 단면 · 그림 나란히 / 뒤 반: 겹침 + 점수
        c = _카드(1000, 700, 초); d = ImageDraw.Draw(c)
        im = Image.open(A + "위_r3.png").convert("RGBA").resize((300, 300)); bg = Image.new("RGBA", (300, 300), (60, 60, 70, 255)); bg.alpha_composite(im); c.alpha_composite(bg, (40, 120))
        d.text((190, 85), "위에서 본 CAD", font=F(34), fill=먹, anchor="mm")
        if p < .5:
            _붙(c, "그림_목표.png", (360, 120), 300); d.text((510, 85), "그림", font=F(34), fill=먹, anchor="mm"); d.text((690, 270), "겹치면?", font=F(54), fill=회, anchor="lm")
        else:
            _붙(c, "겹침_r3.png", (520, 120), 440); d.text((740, 85), "파랑 = CAD · 빨강 = 그림", font=F(30), fill=먹, anchor="mm"); d.text((270, 520), "IoU %.3f" % IOU[3], font=F(64), fill=빨, anchor="mm")
        return c
    if 키 == "여러개":
        c = _카드(1000, 700, 초); d = ImageDraw.Draw(c); n = min(4, 1 + int(p * 5))
        for k, r in enumerate((3, 4, 5, 6)):
            x = 20 + k * 245
            if k < n:
                _붙(c, "겹침_r%d.png" % r, (x, 110), 225); col = 초 if r == 5 else 먹
                d.text((x + 112, 370), "반지름 %d" % r, font=F(36), fill=col, anchor="mm"); d.text((x + 112, 430), "%.3f" % IOU[r], font=F(48), fill=col, anchor="mm")
                if r == 5: d.rounded_rectangle((x - 6, 100, x + 231, 465), 20, outline=초, width=8)
        d.text((500, 60), "여러 크기로 지어서 겹쳐 봄", font=F(40), fill=먹, anchor="mm"); d.text((500, 560), "오 쪽으로 고친다", font=F(54), fill=초 if n == 4 else (250, 250, 252), anchor="mm"); return c
    if 키 == "반복":   # 코드 → CAD → 렌더 → 비교 → 고침 고리 · 도는 점
        c = _카드(1000, 700, 노); d = ImageDraw.Draw(c); 마디 = ("코드", "CAD", "렌더", "그림과 비교", "AI 고침"); cx, cy, R = 500, 360, 240
        pts = [(cx + R * math.cos(-math.pi / 2 + 2 * math.pi * k / 5), cy + R * math.sin(-math.pi / 2 + 2 * math.pi * k / 5)) for k in range(5)]
        for k in range(5): d.line((pts[k], pts[(k + 1) % 5]), fill=회, width=6)
        a = -math.pi / 2 + 2 * math.pi * (p * 2 % 1); d.ellipse((cx + R * math.cos(a) - 18, cy + R * math.sin(a) - 18, cx + R * math.cos(a) + 18, cy + R * math.sin(a) + 18), fill=노)
        for (x, y), t in zip(pts, 마디):
            w = d.textlength(t, font=F(40)) + 40; d.rounded_rectangle((x - w / 2, y - 36, x + w / 2, y + 36), 18, fill=(28, 30, 38)); d.text((x, y), t, font=F(40), fill="white", anchor="mm")
        d.text((cx, cy), "×수천 번", font=F(52), fill=노, anchor="mm"); return c
    if 키 == "다음":
        c = _카드(1000, 700, 빨); d = ImageDraw.Draw(c); _붙(c, "비스듬_r5.png", (40, 120), 420)
        d.text((720, 300), "구멍 하나 →", font=F(52), fill=먹, anchor="mm"); d.text((720, 400), "진짜 로봇 부품?", font=F(60), fill=빨, anchor="mm"); return c
    raise KeyError(키)
