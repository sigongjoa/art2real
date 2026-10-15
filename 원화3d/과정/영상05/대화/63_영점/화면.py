# 63 편(영점) 위쪽 화면 판 — 숫자는 실험_20261013/캐드부품/평가49.py 8 개 시험 두 번(10-15 · 3.13 파이썬 · venv)
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); M = lambda n: ImageFont.truetype("C:/Windows/Fonts/consola.ttf", n)
초, 빨, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 40, 50), (130, 130, 140), (220, 160, 30)
틀48 = (.864, .704, .914, 0, .638, .341, .731, .677); 틀96 = (.809, .882, .829, .204, .657, .349, .726, .668)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _표(d, 오른, 색, 머리, p):
    d.text((330, 60), "48 칸", font=F(40), fill=먹, anchor="mm"); d.text((700, 60), 머리, font=F(40), fill=색, anchor="mm")
    n = min(8, int(p * 16) + 1)
    for i in range(n):
        y = 120 + i * 64; d.text((90, y), "부품 %d" % (i + 1), font=F(34), fill=회, anchor="lm"); d.text((330, y), "%.3f" % 틀48[i], font=F(38), fill=먹, anchor="mm")
        v = 오른[i]; d.text((700, y), "%.3f" % v, font=F(40), fill=초 if (v > 0 and 틀48[i] == 0) else 색, anchor="mm")
def 판(키, p):
    if 키 == "영점": c = _카드(빨); _표(ImageDraw.Draw(c), (0,) * 8, 빨, "96 칸", p); return c
    if 키 == "새": c = _카드(초); d = ImageDraw.Draw(c); _표(d, 틀96, 먹, "96 칸 · 고친 뒤", p); d.rounded_rectangle((560, 120 + 3 * 64 - 30, 840, 120 + 3 * 64 + 30), 14, outline=초, width=5); return c
    if 키 == "시간":
        c = _카드(금); d = ImageDraw.Draw(c); e = _쉬움(p * 1.5); X0, W_ = 330, 440
        for i, (t, v, 색) in enumerate((("실패한 판", 1.6, 빨), ("제대로 잰 판", 15.9, 초))):
            y = 190 + i * 200; d.text((50, y + 40), t, font=F(38), fill=먹, anchor="lm"); w = X0 + int(W_ * v / 15.9 * e); d.rounded_rectangle((X0, y, max(w, X0 + 1), y + 80), 14, fill=색); d.text((min(w + 15, 860), y - 30), "%.1f 초" % v, font=F(40), fill=색, anchor="lm")
        d.text((500, 90), "부품 하나 채점 시간", font=F(42), fill=먹, anchor="mm"); d.text((500, 640), "712 개 × 15.9 초 = 약 3 시간", font=F(36), fill=회, anchor="mm"); return c
    if 키 == "오류":
        c = _카드(빨); d = ImageDraw.Draw(c); d.rounded_rectangle((50, 70, 950, 300), 20, fill=(30, 30, 40))
        d.text((80, 110), "ModuleNotFoundError:", font=M(44), fill=(255, 110, 110)); d.text((80, 180), "No module named 'open3d'", font=M(44), fill=(255, 110, 110))
        d.text((500, 345), "↓", font=F(60), fill=회, anchor="mm")
        d.rounded_rectangle((50, 400, 950, 600), 20, fill=(30, 30, 40)); d.text((80, 440), "except Exception:", font=M(48), fill=(200, 200, 210)); d.text((140, 515), "return (0.0, 0.0)", font=M(48), fill=(255, 200, 80))
        d.text((500, 650), "실패가 0 점으로 적힘", font=F(34), fill=빨, anchor="mm"); return c
    raise KeyError(키)
