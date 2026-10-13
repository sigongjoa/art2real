# 55 편 위쪽 화면 판 — 재료 out/영상05/대화/55_끄트러기/자료/지도.npz(시험 앞 0 플랜지 · 5 너트) · 렌더 out/설명/구멍/빛_r2a_* · 빛_r55_* · 숫자는 결과판정30 · 진단_끄트러기 · 다섯 화소 숫자는 예시
import math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
R = "G:/art2real/out/설명/구멍/"; Z = np.load("G:/art2real/out/영상05/대화/55_끄트러기/자료/지도.npz"); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 파, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 110, 220), (40, 40, 50), (130, 130, 140), (220, 160, 30)
색 = np.array([[245, 245, 245], [205, 215, 230], [230, 80, 80], [80, 140, 235]], np.uint8)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _렌(p, s, 잘=(130, 110, 770, 750)):
    im = Image.open(R + p).convert("RGB").crop(잘).resize((s, s)); m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).rounded_rectangle((3, 3, s - 3, s - 3), 22, fill=255); im = im.convert("RGBA"); im.putalpha(m); return im
def _선(x, s): return Image.fromarray((255 - x * 225).astype(np.uint8)).resize((s, s), Image.NEAREST).convert("RGB")
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _층(Y, D):
    층 = np.clip(np.round(np.where(Y == 3, D, 0) / .1), 0, 10).astype(int); v = 색[Y].copy()
    for k in range(1, 11): v[(Y == 3) & (층 == k)] = cv2.applyColorMap(np.uint8([[k * 25]]), cv2.COLORMAP_TURBO)[0, 0][::-1]
    return v
def _다섯(c, 숫자, y, 색들, 제목):
    d = ImageDraw.Draw(c); d.text((500, y - 40), 제목, font=F(34), fill=먹, anchor="mm")
    for i, (v, col) in enumerate(zip(숫자, 색들)): x = 120 + i * 160; d.rounded_rectangle((x, y, x + 140, y + 110), 16, fill=col + (255,), outline=먹, width=3); d.text((x + 70, y + 55), v, font=F(40), fill=먹, anchor="mm")
def 판(키, p):
    c = _카드(빨 if 키 in ("끄트러기", "계단", "덩어리", "바꿔2", "깊이AI") else 초 if 키 in ("화소셋", "너트", "옆그림") else 금 if 키 in ("납작", "오차", "반올림") else 파); d = ImageDraw.Draw(c)
    if 키 == "끄트러기":
        t = _쉬움(p * 1.5); s = int(480 + 100 * t); c.alpha_composite(_렌("빛_r2a_모델_0.png", s), (500 - s // 2, 390 - s // 2)); d.text((500, 52), "플랜지 — 모델이 깎은 것", font=F(34), fill=빨, anchor="mm"); return c
    if 키 == "화소셋":
        im = _선(Z["X"][0], 520); dr = ImageDraw.Draw(im)
        for k in range(0, 520, 520 // 16): dr.line((k, 0, k, 520), fill=(200, 210, 230)); dr.line((0, k, 520, k), fill=(200, 210, 230))
        c.paste(im, (40, 90)); d.text((300, 50), "위에서 본 그림 + 화소 격자", font=F(30), fill=먹, anchor="mm")
        for i, (t, col) in enumerate((("그대로", (205, 215, 230)), ("뚫기", (230, 80, 80)), ("파기 · 깊이", (80, 140, 235)))):
            if p > .25 + .2 * i: d.rounded_rectangle((610, 170 + i * 150, 960, 280 + i * 150), 20, fill=col + (255,)); d.text((785, 225 + i * 150), t, font=F(44), fill=먹, anchor="mm")
        return c
    if 키 == "너트":
        c.paste(_선(Z["X"][1], 290), (25, 150)); c.paste(Image.fromarray(색[Z["P"][1]]).resize((290, 290), Image.NEAREST), (355, 150)); c.alpha_composite(_렌("빛_r2a_모델_5.png", 300), (680, 145))
        for x, t in ((170, "그림"), (500, "모델 지도"), (830, "깎은 CAD")): d.text((x, 110), t, font=F(32), fill=먹, anchor="mm")
        d.text((500, 520), "가운데 구멍 뚫음 · 바탕만보다 +0.20", font=F(38), fill=초, anchor="mm"); return c
    if 키 == "플랜지":
        c.alpha_composite(_렌("빛_r2a_정답_0.png", 430), (50, 140)); c.alpha_composite(_렌("빛_r2a_모델_0.png", 430), (520, 140)); d.text((265, 100), "정답", font=F(38), fill=초, anchor="mm"); d.text((735, 100), "모델", font=F(38), fill=빨, anchor="mm"); return c
    if 키 == "다섯화소":
        _다섯(c, ["0.40"] * 5, 160, [(220, 235, 250)] * 5, "정답 깊이(평평한 판 한 줄)")
        if p > .35: _다섯(c, ["0.38", "0.41", "0.44", "0.47", "0.43"], 430, [(250, 230, 210)] * 5, "모델이 짐작한 깊이")
        d.text((960, 680), "예시", font=F(26), fill=회, anchor="rb"); return c
    if 키 == "반올림":
        _다섯(c, ["0.38", "0.41", "0.44", "0.47", "0.43"], 160, [(250, 230, 210)] * 5, "모델이 짐작한 깊이")
        if p > .3:
            r = ["0.4", "0.4", "0.4", "0.5", "0.4"]; _다섯(c, r, 430, [(250, 120, 120) if v == "0.5" else (200, 225, 250) for v in r], "0.1 층으로 반올림")
            d.text((500, 340), "↓", font=F(60), fill=회, anchor="mm")
        d.text((960, 680), "예시", font=F(26), fill=회, anchor="rb"); return c
    if 키 == "계단":   # 단면: 평평한 바닥에 한 칸만 더 파임
        y0 = 160; d.text((500, 70), "옆에서 자른 모습(단면)", font=F(34), fill=먹, anchor="mm"); d.rectangle((100, y0, 900, y0 + 380), fill=(205, 215, 230, 255), outline=먹, width=4)
        for i in range(5):
            x = 150 + i * 140; 깊 = 160 if i == 3 else 120; d.rectangle((x, y0, x + 140, y0 + 깊), fill=(250, 250, 252, 255)); d.line((x, y0 + 깊, x + 140, y0 + 깊), fill=먹, width=4)
        if p > .4: d.ellipse((560, y0 + 100, 740, y0 + 210), outline=빨, width=6); d.text((650, y0 + 260), "작은 계단 = 끄트러기", font=F(36), fill=빨, anchor="mm")
        return c
    if 키 == "덩어리":
        Yg, Dg, P, Dp = Z["Yg"][0], Z["Dg"][0], Z["P"][0], Z["Dp"][0]
        c.paste(Image.fromarray(_층(Yg, Dg)).resize((400, 400), Image.NEAREST), (60, 120)); c.paste(Image.fromarray(_층(P, Dp)).resize((400, 400), Image.NEAREST), (540, 120))
        d.text((260, 80), "정답 — 깎을 덩어리 11 개", font=F(32), fill=초, anchor="mm"); d.text((740, 80), "모델 — 26 개로 쪼개짐", font=F(32), fill=빨, anchor="mm"); d.text((500, 600), "색 = 깊이 층", font=F(28), fill=회, anchor="mm"); return c
    if 키 == "범인":
        for i, (t, col) in enumerate((("범인 후보 ①", "구멍 자리를 틀렸다"), ("범인 후보 ②", "깊이를 틀렸다"))):
            x = 70 + i * 450; d.rounded_rectangle((x, 180, x + 410, 520), 30, fill=(240, 244, 250, 255), outline=파, width=5); d.text((x + 205, 260), t, font=F(36), fill=파, anchor="mm"); d.text((x + 205, 380), col, font=F(38), fill=먹, anchor="mm")
        return c
    if 키 in ("바꿔1", "바꿔2"):
        자리, 깊 = ("정답", "모델") if 키 == "바꿔1" else ("모델", "정답"); 값 = 15.5 if 키 == "바꿔1" else 9
        for i, (t, v) in enumerate((("구멍 자리", 자리), ("깊이", 깊))): x = 90 + i * 300; d.rounded_rectangle((x, 160, x + 260, 400), 24, fill=(240, 244, 250, 255), outline=초 if v == "정답" else 빨, width=6); d.text((x + 130, 220), t, font=F(34), fill=먹, anchor="mm"); d.text((x + 130, 320), v, font=F(48), fill=초 if v == "정답" else 빨, anchor="mm")
        d.text((750, 280), "→", font=F(70), fill=회, anchor="mm"); e = _쉬움(p * 2); 현 = 8 + (값 - 8) * e
        d.text((880, 230), "덩어리", font=F(32), fill=먹, anchor="mm"); d.text((880, 320), "%d" % int(현), font=F(90), fill=빨 if 값 > 10 else 초, anchor="mm"); d.text((500, 560), "정답대로 지으면 8 개", font=F(32), fill=회, anchor="mm"); return c
    if 키 == "납작":
        c.alpha_composite(_렌("빛_r55_얕은홈.png", 270), (60, 80)); c.alpha_composite(_렌("빛_r55_깊은구멍.png", 270), (60, 400)); d.text((195, 45), "얕은 홈", font=F(30), fill=먹, anchor="mm"); d.text((195, 380), "깊은 구멍", font=F(30), fill=먹, anchor="mm")
        if p > .3:
            d.text((450, 350), "→", font=F(80), fill=회, anchor="mm"); g = Image.new("RGB", (380, 380), "white"); dg = ImageDraw.Draw(g); dg.rectangle((40, 40, 340, 340), outline=먹, width=5); dg.ellipse((115, 115, 265, 265), outline=먹, width=5); c.paste(g, (560, 160)); d.text((750, 600), "위에서 보면 둘 다 이 그림", font=F(30), fill=금, anchor="mm")
        return c
    if 키 == "오차":
        d.text((500, 120), "모델이 짐작한 깊이 오차", font=F(38), fill=먹, anchor="mm"); e = _쉬움(p * 2)
        d.rounded_rectangle((120, 260, 880, 360), 20, fill=(230, 232, 238, 255)); d.rounded_rectangle((120, 260, 120 + int(760 * .095 / .2 * e), 360), 20, fill=금); d.text((500, 450), "부품 높이의 약 10 % (중앙 9.5 %)", font=F(40), fill=먹, anchor="mm"); return c
    if 키 == "음영":   # 같은 모양 · 다른 음영 두 판
        for i, (a, b) in enumerate(((60, 230), (200, 90))):
            x = 80 + i * 460; g = Image.new("RGB", (380, 380), "white"); dg = ImageDraw.Draw(g)
            for r in range(150, 0, -3): v = int(a + (b - a) * (1 - r / 150)); dg.ellipse((190 - r, 190 - r, 190 + r, 190 + r), fill=(v, v, v + 10))
            dg.ellipse((40, 40, 340, 340), outline=먹, width=5); c.paste(g, (x, 120))
        d.text((500, 580), "같은 모양 · 칠하기 나름", font=F(38), fill=먹, anchor="mm"); return c
    if 키 == "깊이AI":
        d.text((500, 90), "09-22 시험 · 부피 IoU", font=F(36), fill=먹, anchor="mm")
        for i, (t, v, col) in enumerate((("그림자 겹치기", .56, 회), ("깊이 추정 AI", .55, 빨))): y = 220 + i * 160; d.text((80, y + 30), t, font=F(34), fill=먹); d.rounded_rectangle((420, y, 420 + int(450 * v), y + 70), 16, fill=col); d.text((430 + int(450 * v), y + 35), "%.2f" % v, font=F(34), fill=먹, anchor="lm")
        d.text((500, 600), "색을 깊이로 읽음", font=F(34), fill=빨, anchor="mm"); return c
    if 키 == "옆그림":
        g = Image.new("RGB", (380, 300), "white"); dg = ImageDraw.Draw(g); dg.rectangle((40, 60, 340, 240), outline=먹, width=5); dg.line((150, 60, 150, 240), fill=먹, width=4); dg.line((260, 60, 260, 240), fill=먹, width=4); c.paste(g, (40, 150)); d.text((230, 120), "위에서 본 그림", font=F(30), fill=먹, anchor="mm")
        if p > .3:
            h = Image.new("RGB", (380, 300), "white"); dh = ImageDraw.Draw(h); dh.polygon([(40, 260), (340, 260), (340, 200), (190, 200), (190, 140), (110, 140), (110, 80), (40, 80)], outline=먹, width=5); c.paste(h, (560, 150)); d.text((750, 120), "옆에서 본 그림", font=F(30), fill=먹, anchor="mm")
            for y in (200, 140, 80): d.line((930, 150 + y, 960, 150 + y), fill=초, width=5)
            d.text((750, 500), "단차 높이가 선으로 보인다", font=F(34), fill=초, anchor="mm")
        c.alpha_composite(_렌("빛_r55_계단.png", 170), (415, 140)); return c
    if 키 == "가려짐":
        d.text((500, 70), "옆에서 본 모습", font=F(34), fill=먹, anchor="mm"); d.rectangle((150, 180, 850, 520), fill=(205, 215, 230, 255), outline=먹, width=5)
        for x in range(380, 620, 30): d.line((x, 180, x + 15, 180 + 0), fill=먹, width=0)
        d.rectangle((380, 180, 620, 360), outline=회, width=4); d.text((500, 270), "안쪽 구멍", font=F(32), fill=회, anchor="mm"); d.text((500, 600), "벽에 가려 옆에서도 안 보임", font=F(34), fill=파, anchor="mm"); return c
    raise KeyError(키)
