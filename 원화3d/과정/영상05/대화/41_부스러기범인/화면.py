# 41 편 위쪽 화면 판 — 판(키, 진행 0~1) → RGBA (≤ 1000 × 760) · 재료는 out/영상05/대화/41_부스러기범인/자료 (트레일 선고리/자료41.py)
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/41_부스러기범인/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
코드 = [l for l in open("G:/art2real/트레일/trail10_cadrille/runs/선고리/코드_10_A.py", encoding="utf-8").read().splitlines() if l.startswith("# 포켓") or l.startswith("r = r.cut")]
def _카드(w, h, 테=(255, 255, 255), 바탕=(250, 250, 252)):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=바탕 + (255,), outline=테 + (255,), width=8); return c
def _넣(c, im, box):   # 흰 여백을 잘라 내고 칸에 꽉 차게
    import numpy as np
    a = np.asarray(im.convert("RGB")); ys, xs = np.nonzero((a < 240).any(-1))
    if len(xs): im = im.crop((max(xs.min() - 12, 0), max(ys.min() - 12, 0), xs.max() + 12, ys.max() + 12))
    im = im.convert("RGBA"); s = min(box[2] / im.width, box[3] / im.height); im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS); c.alpha_composite(im, (box[0] + (box[2] - im.width) // 2, box[1] + (box[3] - im.height) // 2))
def _제목(c, t, col=(30, 30, 40)): ImageDraw.Draw(c).text((c.width // 2, 50), t, font=F(46), fill=col, anchor="mm")
def 판(키, p):
    t = int(p * 11.99) % 12
    if 키 == "조각":
        c = _카드(1000, 740, (255, 80, 80)); _제목(c, "빨강 = 떨어진 부스러기", (220, 50, 50)); _넣(c, Image.open(A + "화소_%02d.png" % t), (40, 90, 920, 630)); return c
    if 키 == "테두리":
        c = _카드(1000, 740, (255, 80, 80)); _제목(c, "판 자리 = 화소 테두리 그대로", (220, 50, 50)); _넣(c, Image.open(A + "화소테두리.png"), (60, 95, 880, 620)); return c
    if 키 == "스텝":
        c = _카드(1000, 600); d = ImageDraw.Draw(c); d.rounded_rectangle((330, 120, 670, 440), 30, fill=(255, 240, 200), outline=(200, 150, 40), width=6)
        d.text((500, 230), "STEP", font=F(90), fill=(160, 110, 20), anchor="mm"); d.text((500, 350), "부품.step", font=F(44), fill=(90, 70, 30), anchor="mm"); d.text((500, 520), "CAD 파일 맞음", font=F(44), fill=(40, 40, 50), anchor="mm"); return c
    if 키 == "입력": c = _카드(1000, 620); _제목(c, "앞 · 옆 · 위 선 그림"); _넣(c, Image.open(A + "단계_입력.png"), (20, 90, 960, 500)); return c
    if 키 == "고리": c = _카드(1000, 620); _제목(c, "닫힌 선 = 스케치 하나 (회색 = 작아서 버림)"); _넣(c, Image.open(A + "단계_고리.png"), (20, 90, 960, 500)); return c
    if 키 == "깊이": c = _카드(1000, 660); _제목(c, "초록 = 깊이만큼 판다"); _넣(c, Image.open(A + "단계_깊이.png"), (20, 90, 960, 550)); return c
    if 키 == "비교":
        c = Image.new("RGBA", (1000, 620), (0, 0, 0, 0)); a = _카드(480, 560, (255, 80, 80)); b = _카드(480, 560, (90, 220, 120))
        _넣(a, Image.open(A + "화소_%02d.png" % t), (20, 20, 440, 460)); _넣(b, Image.open(A + "선고리_%02d.png" % t), (20, 20, 440, 460))
        ImageDraw.Draw(a).text((240, 515), "화소로 판 것", font=F(40), fill=(220, 50, 50), anchor="mm"); ImageDraw.Draw(b).text((240, 515), "선 그대로 판 것", font=F(40), fill=(40, 160, 70), anchor="mm")
        c.alpha_composite(a, (0, 40)); c.alpha_composite(b, (520, 40)); return c
    if 키 == "코드":
        c = _카드(1000, 740, (90, 170, 255), (24, 28, 40)); d = ImageDraw.Draw(c); d.text((40, 40), "코드_10_A.py", font=F(34), fill=(150, 200, 255))
        n = max(1, int(p * 1.6 * len(코드))); y = 100
        for j, l in enumerate(코드[:n][-6:]):
            주 = l.startswith("#")
            if 주: s = l.split(" · ")[0] + " · " + l.split(" · ")[1] + " · " + l.split(" · ")[2].split(" ")[0] if l.count(" · ") >= 2 else l
            else: s = "r = r.cut(" + l.split('Workplane(')[1][:4] + " 스케치 → 밀어내기)"
            if 주 and p > .5 and j == 0: d.rectangle((30, y - 6, 970, y + 52), fill=(80, 70, 20))
            d.text((40, y), s, font=F(38 if 주 else 32), fill=(255, 220, 120) if 주 else (210, 220, 235)); y += 98 if not 주 else 56
        return c
    if 키 == "막대":
        c = _카드(1000, 640); d = ImageDraw.Draw(c); _제목(c, "35 개 부품 · 같은 자")
        for j, (n_, a_, b_, 최) in enumerate((("통과 수", 33, 30, 35), ("부스러기 조각", 148, 9, 150))):
            y = 140 + j * 240; d.text((40, y), n_, font=F(40), fill=(30, 30, 40))
            for k, (v, 색, 이름) in enumerate(((a_, (150, 150, 160), "화소"), (b_, (90, 170, 255), "선"))):
                w = int(640 * v / 최 * min(1, p * 2.5)); yy = y + 60 + k * 70; d.text((40, yy + 25), 이름, font=F(34), fill=(60, 60, 70), anchor="lm")
                d.rounded_rectangle((150, yy, 150 + max(w, 8), yy + 50), 14, fill=색); d.text((165 + max(w, 8), yy + 25), str(v), font=F(36), fill=(30, 30, 40), anchor="lm")
        return c
    raise KeyError(키)
