# 56 편 위쪽 화면 판 — 재료 out/영상05/대화/56_몸통/자료/재료.npz(시험 120 원통 · 3 ㄱ자 판: 위 · 앞 · 옆 그림 + 2b 모델 지도) · 렌더 out/설명/구멍/빛_r31_* · 빛_r33_* · 숫자는 결과판정31b · 33
import numpy as np
from PIL import Image, ImageDraw, ImageFont
R = "G:/art2real/out/설명/구멍/"; Z = np.load("G:/art2real/out/영상05/대화/56_몸통/자료/재료.npz"); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 파, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 110, 220), (40, 40, 50), (130, 130, 140), (220, 160, 30)
색 = np.array([[245, 245, 245], [205, 215, 230], [230, 80, 80], [80, 140, 235]], np.uint8)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _렌(n, s):
    im = Image.open(R + "빛_r%s.png" % n).convert("RGB").crop((130, 110, 770, 750)).resize((s, s)); m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).rounded_rectangle((3, 3, s - 3, s - 3), 22, fill=255); im = im.convert("RGBA"); im.putalpha(m); return im
def _선(x, s): return Image.fromarray((255 - x * 225).astype(np.uint8)).resize((s, s), Image.NEAREST).convert("RGB")
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _둘(c, a, b, 왼, 오, 색왼=먹, 색오=먹, s=430):
    d = ImageDraw.Draw(c); c.alpha_composite(a, (50, 150)); c.alpha_composite(b, (520, 150)); d.text((265, 100), 왼, font=F(36), fill=색왼, anchor="mm"); d.text((735, 100), 오, font=F(36), fill=색오, anchor="mm")
def _막대(c, 줄, 기준=None):
    d = ImageDraw.Draw(c)
    for i, (t, v, col) in enumerate(줄):
        y = 150 + i * 130; d.text((40, y + 30), t, font=F(32), fill=먹); w = int((v - .5) / .12 * 560); d.rounded_rectangle((330, y, 330 + w, y + 70), 14, fill=col); d.text((318 + w, y + 35), "%.3f" % v, font=F(32), fill=(255, 255, 255), anchor="rm")
    if 기준: x = 330 + int((기준[0] - .5) / .12 * 560); d.line((x, 120, x, 150 + len(줄) * 130), fill=금, width=5); d.text((x, 105), 기준[1], font=F(28), fill=금, anchor="mm")
def 판(키, p):
    c = _카드(빨 if 키 in ("그대로", "사라짐", "버림", "범인") else 초 if 키 in ("다시", "ㄱ판", "원통", "세장") else 금 if 키 in ("53바깥선", "숫자") else 파); d = ImageDraw.Draw(c)
    if 키 == "세장":
        for i, (k, t) in enumerate((("X", "위"), ("F", "앞"), ("S", "옆"))):
            if p > i * .2: c.paste(_선(Z[k][0], 290), (25 + i * 330, 170)); d.text((170 + i * 330, 130), t, font=F(38), fill=먹, anchor="mm")
        d.text((500, 560), "세 장을 같이 보여 줌", font=F(38), fill=초, anchor="mm"); return c
    if 키 == "그대로":
        _막대(c, [("위 한 장", .593, (150, 160, 180)), ("위 · 앞 · 옆", .592, (230, 80, 80))]); d.text((500, 560), "옆 그림을 줬는데 그대로", font=F(38), fill=빨, anchor="mm"); return c
    if 키 == "사라짐":
        _둘(c, _렌("31_3_정답", 430), _렌("31_3_2b", 430), "정답", "지은 것", 초, 빨)
        if p > .4: d.text((735, 640), "몸통이 없다", font=F(36), fill=빨, anchor="mm")
        return c
    if 키 == "범인":
        for i, (t, s) in enumerate((("모델이 지웠다?", "모델이 칠한 지도"), ("짓는 코드가 버렸다?", "꼬인 선 검사"))):
            x = 60 + i * 450; d.rounded_rectangle((x, 170, x + 420, 520), 30, fill=(250, 240, 240, 255), outline=빨, width=5); d.text((x + 210, 280), t, font=F(36), fill=빨, anchor="mm"); d.text((x + 210, 400), s, font=F(32), fill=먹, anchor="mm")
        return c
    if 키 == "버림":   # 꼬인 윤곽(나비 모양) → 버림 → 0 점
        d.polygon([(90, 200), (360, 470), (360, 200), (90, 470)], outline=먹, width=6); e = _쉬움(p * 2)
        d.ellipse((190, 300, 260, 370), outline=빨, width=6); d.text((225, 540), "선이 꼬임", font=F(34), fill=빨, anchor="mm")
        if p > .3: d.text((500, 335), "→", font=F(90), fill=회, anchor="mm")
        if p > .45:
            d.rounded_rectangle((600, 200, 940, 470), 30, fill=(250, 235, 235, 255), outline=빨, width=6); d.text((770, 290), "버림", font=F(60), fill=빨, anchor="mm"); d.text((770, 390), "몸통이면 0 점", font=F(36), fill=먹, anchor="mm")
        d.text((500, 640), "구멍 선 · 몸통 선 구분 없이", font=F(32), fill=회, anchor="mm"); return c
    if 키 == "53바깥선":
        c.paste(Image.fromarray(색[Z["P"][1]]).resize((400, 400), Image.NEAREST), (60, 160)); c.paste(_선(Z["X"][1], 400), (540, 160))
        d.text((260, 110), "모델이 칠한 지도", font=F(34), fill=빨, anchor="mm"); d.text((740, 110), "그림 바깥 선(53 편)", font=F(34), fill=초, anchor="mm")
        d.text((260, 610), "경계가 지글지글", font=F(32), fill=빨, anchor="mm"); d.text((740, 610), "있었는데 안 씀", font=F(32), fill=금, anchor="mm"); return c
    if 키 == "다시":
        c.paste(_선(Z["X"][0], 300), (40, 200)); d.text((500, 350), "→", font=F(80), fill=회, anchor="mm"); c.alpha_composite(_렌("33_120_바탕", 400), (570, 150))
        d.text((190, 150), "그림 바깥 선", font=F(32), fill=먹, anchor="mm"); d.text((770, 110), "몸통", font=F(34), fill=초, anchor="mm"); d.text((500, 620), "200 개 전부 몸통이 섬", font=F(36), fill=초, anchor="mm"); return c
    if 키 == "ㄱ판":
        _둘(c, _렌("31_3_2b", 430), _렌("33_3_2b", 430), "전 · 0.00", "다시 · 0.98", 빨, 초); return c
    if 키 == "원통":
        _둘(c, _렌("33_120_2a", 430), _렌("33_120_2b", 430), "위 한 장 · 0.33", "위 · 앞 · 옆 · 0.70", 빨, 초); return c
    if 키 == "숫자":
        _막대(c, [("바탕만", .565, (150, 160, 180)), ("위 한 장", .584, (230, 80, 80)), ("위 · 앞 · 옆", .599, (80, 190, 120))], (.604, "기준 +0.02"))
        d.text((500, 620), "효과는 보이는데 기준엔 조금 못 미침", font=F(34), fill=금, anchor="mm"); return c
    raise KeyError(키)
