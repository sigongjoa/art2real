# 59 편(천장) 위쪽 화면 판 — 렌더 out/영상05/대화/59_천장/자료/브래킷_*.png(재료59.py · 시험 131) · 숫자는 결과판정34 · 33
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/59_천장/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 40, 50), (130, 130, 140), (220, 160, 30)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _렌(n, s):
    im = Image.open(A + "브래킷_%s.png" % n).convert("RGB").crop((60, 60, 540, 540)).resize((s, s)); m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).rounded_rectangle((3, 3, s - 3, s - 3), 22, fill=255); im = im.convert("RGBA"); im.putalpha(m); return im
def _둘(c, a, b, 왼, 오, 색왼=먹, 색오=먹):
    d = ImageDraw.Draw(c); c.alpha_composite(_렌(a, 430), (50, 150)); c.alpha_composite(_렌(b, 430), (520, 150)); d.text((265, 100), 왼, font=F(36), fill=색왼, anchor="mm"); d.text((735, 100), 오, font=F(36), fill=색오, anchor="mm")
def _공(d, x0, y0, s, 채움):   # 옆에서 자른 브래킷 단면(工) · 채움 = 날개 밑 빈 곳 색(None 이면 비움)
    위, 기, 아 = (x0, y0, x0 + 6 * s, y0 + s), (x0 + 2 * s, y0 + s, x0 + 4 * s, y0 + 4 * s), (x0, y0 + 4 * s, x0 + 6 * s, y0 + 5 * s)
    if 채움: [d.rectangle(r, fill=채움) for r in ((x0, y0 + s, x0 + 2 * s, y0 + 4 * s), (x0 + 4 * s, y0 + s, x0 + 6 * s, y0 + 4 * s))]
    for r in (위, 기, 아): d.rectangle(r, fill=(180, 190, 210), outline=먹, width=3)
def _화살(d, a, b, 색):
    d.line((a, b), fill=색, width=6); import math; t = math.atan2(b[1] - a[1], b[0] - a[0])
    d.polygon([b, (b[0] - 22 * math.cos(t - .4), b[1] - 22 * math.sin(t - .4)), (b[0] - 22 * math.cos(t + .4), b[1] - 22 * math.sin(t + .4))], fill=색)
def _막대(d, p, 줄, y0=150):
    e = _쉬움(p * 1.5)
    for i, (t, v, 색) in enumerate(줄):
        y = y0 + i * 130; d.text((60, y + 30), t, font=F(34), fill=먹, anchor="lm"); w = int(560 * v * e); d.rounded_rectangle((300, y, 300 + max(w, 1), y + 60), 12, fill=색); d.text((300 + w + 20, y + 30), "%.3f" % (v * e) if e < 1 else "%.3f" % v, font=F(38), fill=색, anchor="lm")
def 판(키, p):
    c = _카드(빨 if 키 in ("정답대위", "위에서", "막힘") else 금 if 키 in ("격자", "격자점수") else 초); d = ImageDraw.Draw(c)
    if 키 == "정답대위": _둘(c, "정답", "1", "정답", "정답 넣고 지은 것", 초, 빨); return c
    if 키 == "격자":
        for j, (n, x) in enumerate(((6, 120), (12, 560))):
            s = 320 / n
            for k in range(n + 1): d.line((x + k * s, 190, x + k * s, 510), fill=회, width=2); d.line((x, 190 + k * s, x + 320, 190 + k * s), fill=회, width=2)
            if j == 0 or p > .3: d.text((x + 160, 130), ("칸 48" if j == 0 else "칸 96"), font=F(38), fill=먹 if j == 0 else 금, anchor="mm")
        d.text((500, 350), "→", font=F(70), fill=회, anchor="mm"); return c
    if 키 == "격자점수": _막대(d, p, (("칸 48", .685, 회), ("칸 96", .702, 금))); d.text((500, 560), "정답을 넣고 재도", font=F(36), fill=회, anchor="mm"); return c
    if 키 == "위에서":
        _공(d, 320, 220, 60, (250, 200, 200) if p > .3 else None)
        for x in (360, 500, 640): _화살(d, (x, 90), (x, 200), 금)
        if p > .3: d.text((215, 400), "?", font=F(70), fill=빨, anchor="mm"); d.text((785, 400), "?", font=F(70), fill=빨, anchor="mm")
        d.text((500, 610), "옆에서 자른 모양", font=F(30), fill=회, anchor="mm"); return c
    if 키 == "세방향":
        _공(d, 320, 220, 60, None)
        for x in (360, 500, 640): _화살(d, (x, 90), (x, 200), 금)
        if p > .2: [_화살(d, (120, y), (305, y), 초) for y in (330, 400, 470)]
        if p > .4: [_화살(d, (880, y), (695, y), 초) for y in (330, 400, 470)]
        d.text((500, 610), "위 · 앞 · 옆에서 파기", font=F(30), fill=초, anchor="mm"); return c
    if 키 == "숫자": _막대(d, p, (("위에서만", .685, 회), ("윤곽 셋", .830, 금), ("세 방향", .912, 초))); d.text((500, 600), "시험 부품 200 개 · 학습 없음", font=F(32), fill=회, anchor="mm"); return c
    if 키 == "전후": _둘(c, "1", "3", "위에서만 0.14", "세 방향 0.90", 빨, 초); return c
    if 키 == "막힘": _막대(d, p, (("모델", .599, 빨), ("정답 · 세 방향", .912, 초)), 220); return c
    raise KeyError(키)
