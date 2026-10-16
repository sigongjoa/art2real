# 65 편(천장) 위쪽 화면 판 — 재료 out/영상05/대화/65_천장/자료/(실험_20261013/캐드부품/재료65.py) · 숫자는 결과판정52대조 · 결과판정51_천장
from PIL import Image, ImageDraw, ImageFont
# 화풍 시험판(강조색 · Anatomy kit · 10-16)
A = "G:/art2real/out/영상05/대화/65_천장_강조색/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 40, 50), (130, 130, 140), (220, 160, 30)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _그림(c, n, box):
    im = Image.open(A + n + ".png").convert("RGBA"); im = im.crop(im.getbbox())
    x0, y0, x1, y1 = box; s = min((x1 - x0) / im.width, (y1 - y0) / im.height); im = im.resize((int(im.width * s), int(im.height * s))); c.alpha_composite(im, (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2))
def _둘(c, a, b, ta, tb, ca, cb, 아래):
    d = ImageDraw.Draw(c); _그림(c, a, (40, 150, 480, 600)); _그림(c, b, (520, 150, 960, 600))
    d.text((260, 90), ta, font=F(40), fill=ca, anchor="mm"); d.text((740, 90), tb, font=F(40), fill=cb, anchor="mm"); d.text((500, 650), 아래, font=F(32), fill=회, anchor="mm"); return c
def 판(키, p):
    if 키 == "컵위":
        c = _카드(빨); d = ImageDraw.Draw(c); _그림(c, "화풍_위만", (60, 125, 940, 615)); d.text((500, 80), "위에서만 깎음  0.20", font=F(42), fill=빨, anchor="mm"); d.text((500, 655), "옆에서 파인 곳은 못 만든다", font=F(32), fill=회, anchor="mm"); return c
    if 키 == "컵여섯":
        c = _카드(초); d = ImageDraw.Draw(c); _그림(c, "화풍_여섯", (60, 125, 940, 615)); d.text((500, 80), "여섯 방향 깎음  0.67", font=F(42), fill=초, anchor="mm"); d.text((500, 655), "원뿔 컵 · 정답 깊이 · 학습 전", font=F(32), fill=회, anchor="mm"); return c
    if 키 in ("천장", "천장끝", "느림", "느림끝"):   # 10-16 모션 카드(Remotion · LottieFiles motion-design 값 · 투명 PNG 프레임) — 처음 줄은 p 로 움직이고 다시 나오면 마지막 프레임
        폴, n, 테, 제 = ("천장모션2", 150, 금, "정답을 넣었을 때 · 712 개 평균") if 키.startswith("천장") else ("느림모션2", 150, 빨, "부품 40 개 CAD 짓는 시간")
        i = n - 1 if 키.endswith("끝") else min(n - 1, int(min(max(p, 0), 1) * n)); c = _카드(테); d = ImageDraw.Draw(c)
        c.alpha_composite(Image.open(A + "%s/프레임_%03d.png" % (폴, i)).convert("RGBA")); d.text((500, 80), 제, font=F(42), fill=먹, anchor="mm"); return c
    if 키 == "천장_옛":
        c = _카드(금); d = ImageDraw.Draw(c); e = _쉬움(p * 1.5); X0, W_ = 330, 520; 자 = lambda v: X0 + int(W_ * (v - .5) / .4)
        d.text((500, 80), "정답을 넣었을 때 · 712 개 평균", font=F(40), fill=먹, anchor="mm")
        for i, (t, v, 색) in enumerate((("틀만", .635, 회), ("위에서만", .680, 빨), ("여섯 방향", .803, 초))):
            y = 170 + i * 150; d.text((50, y + 35), t, font=F(38), fill=먹, anchor="lm"); w = 자(.5 + (v - .5) * e); d.rounded_rectangle((X0, y, max(w, X0 + 1), y + 70), 14, fill=색); d.text((w + 15, y + 35), "%.2f" % v, font=F(40), fill=색, anchor="lm")
        d.text((500, 650), "모델 없이 · 정답 깊이로 지은 CAD", font=F(30), fill=회, anchor="mm"); return c
    if 키 == "느림_옛":
        c = _카드(빨); d = ImageDraw.Draw(c); e = _쉬움(p * 1.5); X0, W_ = 360, 480
        d.text((500, 90), "부품 40 개 CAD 짓는 시간", font=F(42), fill=먹, anchor="mm")
        for i, (t, v, 색) in enumerate((("하나씩 깎기", 36, 빨), ("코드로 바로", 3.5, 초))):
            y = 200 + i * 200; d.text((50, y + 40), t, font=F(38), fill=먹, anchor="lm"); w = X0 + int(W_ * v / 36 * e); d.rounded_rectangle((X0, y, max(w, X0 + 1), y + 80), 14, fill=색); d.text((min(w + 15, 820), y - 32), "%g 분" % v, font=F(40), fill=색, anchor="lm")
        d.text((500, 640), "같은 모양 · 불리언 수천 번 → 한 번", font=F(32), fill=회, anchor="mm"); return c
    if 키 in ("광선위", "광선여섯"):   # 10-16 광선 깎기 프레임(Anatomy 강조색 · rays.mjs · 구간 위 0~23 · 결과1 24~31 · 아래 32~55 · 결과2 56~63 · 옆 64~71) — 대사 진행 p 로 프레임을 넘긴다
        a, b, 테, 제 = (0, 31, 빨, "위에서만 광선") if 키 == "광선위" else (32, 71, 초, "아래 · 옆에서도 광선")
        n = min(b, a + int(min(max(p, 0), 1) * (b - a + 1))); c = _카드(테); d = ImageDraw.Draw(c); im = Image.open(A + "광선/프레임_%03d.png" % n).convert("RGBA").crop((185, 25, 815, 680)); k = min(880 / im.width, 490 / im.height); im = im.resize((int(im.width * k), int(im.height * k))); c.alpha_composite(im, (500 - im.width // 2, 370 - im.height // 2))   # 프레임마다 같은 자르기(전부의 bbox 197,37–801,668) — 프레임마다 getbbox 면 크기가 흔들린다
        d.text((500, 80), 제, font=F(42), fill=테, anchor="mm"); d.text((500, 655), "광선이 처음 맞는 곳까지만 깎인다", font=F(30), fill=회, anchor="mm"); return c
    raise KeyError(키)
