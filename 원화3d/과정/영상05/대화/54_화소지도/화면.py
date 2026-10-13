# 54 편 위쪽 화면 판 — 재료 out/설명/구멍(빛_r54_* · 학습4/지도_* · 학습4/스냅.json) · 사실 숫자는 결과판정28 · 29 · 진단_1c · 진단_구조
import json, math, numpy as np
from PIL import Image, ImageDraw, ImageFont
R = "G:/art2real/out/설명/구멍/"; L = R + "학습4/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 파, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 110, 220), (40, 40, 50), (130, 130, 140), (220, 160, 30)
S = json.load(open(L + "스냅.json", encoding="utf-8")); 에 = [0, 1, 2, 4, 10, 20]
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _렌더(p, s):
    im = Image.open(R + p).convert("RGB").crop((180, 160, 720, 700)).resize((s, s)); m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).rounded_rectangle((4, 4, s - 4, s - 4), 22, fill=255); im = im.convert("RGBA"); im.putalpha(m); return im
def _지도(p, s):   # 0 안 깎음(옅은 회색) · 1 구멍(빨강) · 2 홈(파랑)
    a = np.asarray(Image.open(p)) // 120; c = np.full(a.shape + (3,), 235, np.uint8); c[a == 1] = (230, 80, 80); c[a == 2] = (80, 140, 235); return Image.fromarray(c).resize((s, s), Image.NEAREST)
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _막대(d, x, y, w, 글, v, col, 글자=None):
    d.text((x, y + 22), 글, font=F(32), fill=먹); d.rounded_rectangle((x + 230, y, x + 230 + w, y + 50), 12, fill=(225, 228, 235)); d.rounded_rectangle((x + 230, y, x + 230 + max(int(w * v), 4), y + 50), 12, fill=col)
    d.text((x + 240 + w, y + 25), 글자 if 글자 else "%d%%" % round(v * 100), font=F(30), fill=먹, anchor="lm")
def 판(키, p):
    if 키 == "안깎음":
        c = _카드(빨); d = ImageDraw.Draw(c); c.alpha_composite(_렌더("빛_r1c_완성_5.png", 420), (50, 100)); c.alpha_composite(_렌더("빛_r1c_바탕_5.png", 420), (530, 100))
        d.text((260, 60), "정답", font=F(40), fill=초, anchor="mm"); d.text((740, 60), "1c 모델", font=F(40), fill=빨, anchor="mm"); d.text((500, 610), "바탕은 맞았는데 구멍 · 홈이 없다", font=F(36), fill=먹, anchor="mm"); return c
    if 키 == "확률":
        c = _카드(빨); d = ImageDraw.Draw(c); e = _쉬움(p * 2); d.text((500, 70), "1c 모델이 칸마다 고르는 확률(끝)", font=F(38), fill=먹, anchor="mm")
        for i, (t, v) in enumerate((("안 깎음", 1.0), ("구멍", 0), ("가로 홈", 0), ("세로 홈", 0))): _막대(d, 80, 170 + i * 110, 520, t, v * e, 빨 if v else 회)
        return c
    if 키 == "손해":
        c = _카드(빨); d = ImageDraw.Draw(c); d.text((500, 70), "깎았을 때 점수가 오른 비율", font=F(38), fill=먹, anchor="mm"); e = _쉬움(p * 2)
        for i, (t, v, col) in enumerate((("정답 자리", 1.0, 초), ("± 1 mm", .665, 금), ("± 1.65 mm", .413, 빨), ("아무 데나", .043, 빨))): _막대(d, 60, 160 + i * 115, 520, t, v * e, col)
        d.text((500, 640), "아무 데나 깎으면 평균 -0.103", font=F(32), fill=빨, anchor="mm"); return c
    if 키 == "머리":
        c = _카드(초); d = ImageDraw.Draw(c); d.text((500, 70), "정답 위치를 직접 가르쳤더니", font=F(38), fill=먹, anchor="mm"); e = _쉬움(p * 2)
        _막대(d, 60, 200, 520, "늘 가운데", 3.73 / 4 * 1, 회, "3.73 mm"); _막대(d, 60, 330, 520, "직접 가르침", .82 / 4 * e + (1 - e) * 3.73 / 4, 초, "%.2f mm" % (.82 * e + 3.73 * (1 - e)))
        d.text((500, 520), "구멍 · 홈 위치 오차(작을수록 좋음)", font=F(30), fill=회, anchor="mm"); return c
    if 키 == "점수하나":
        c = _카드(금); d = ImageDraw.Draw(c); c.alpha_composite(_렌더("빛_r54_e00_5.png", 380), (60, 150)); d.text((600, 330), "→", font=F(80), fill=회, anchor="mm")
        d.rounded_rectangle((680, 260, 920, 400), 30, fill=(255, 240, 200, 255), outline=금, width=5); d.text((800, 330), "%.2f" % S["스냅"][0]["지켜볼"][5]["IoU"], font=F(72), fill=먹, anchor="mm"); d.text((500, 620), "다 짓고 나서 점수 하나 — 어디가 틀렸는지 모름", font=F(32), fill=먹, anchor="mm"); return c
    if 키 == "유넷":   # 줄였다가 키우는 네모들
        c = _카드(초); d = ImageDraw.Draw(c); 크기 = [200, 140, 90, 55, 90, 140, 200]; xs = [70 + i * 130 for i in range(7)]; n = int(1 + p * 7.5)
        for i in range(min(n, 7)):
            s = 크기[i]; x, y = xs[i], 330 - s // 2; d.rounded_rectangle((x, y, x + 100, y + s), 14, fill=(200, 220, 245, 255) if i < 3 else (205, 238, 210, 255) if i > 3 else (230, 230, 240, 255), outline=파 if i < 3 else 초 if i > 3 else 회, width=4)
            if i < 6 and i + 1 < n: d.line((x + 104, 330, xs[i + 1] - 4, 330), fill=회, width=4)
        d.text((300, 560), "줄이기", font=F(34), fill=파, anchor="mm"); d.text((780, 560), "다시 키우기", font=F(34), fill=초, anchor="mm"); d.text((500, 630), "화소마다 「깎는 자리인가」를 낸다", font=F(32), fill=먹, anchor="mm"); return c
    if 키 == "지도":
        c = _카드(초); d = ImageDraw.Draw(c); g = Image.open(L + "정답지도_5.png"); c.paste(_지도(L + "정답지도_5.png", 420), (60, 110)); c.paste(_지도(L + "지도_e20_5.png", 420), (520, 110))
        d.text((270, 70), "정답 지도", font=F(36), fill=먹, anchor="mm"); d.text((730, 70), "모델 지도", font=F(36), fill=초, anchor="mm"); d.text((500, 600), "빨강 = 구멍 · 파랑 = 홈 · 화소 128 × 128", font=F(30), fill=회, anchor="mm"); return c
    if 키 == "타임랩스":
        c = _카드(초); d = ImageDraw.Draw(c); j = min(len(에) - 1, int(p * len(에))); e = 에[j]
        for k in range(6): x0, y0 = 20 + (k % 3) * 323, 70 + (k // 3) * 300; c.alpha_composite(_렌더("빛_r54_e%02d_%d.png" % (e, k), 280), (x0 + 10, y0))
        d.text((500, 35), "에폭 %d · 처음 보는 200개 IoU %.3f" % (e, S["스냅"][e]["시험IoU"]), font=F(36), fill=초 if e else 먹, anchor="mm"); return c
    if 키 == "진짜":
        c = _카드(빨); d = ImageDraw.Draw(c)
        for j, n in enumerate(("머리", "발")):
            y = 30 + j * 320; g = Image.open("G:/art2real/out/영상05/대화/49_진짜그림/자료/%s_앞그림.png" % n).convert("RGB").resize((280, 280)); c.paste(g, (40, y)); c.paste(_지도(L + "진짜지도_%s.png" % n, 280), (360, y)); c.alpha_composite(_렌더("빛_r54_진짜_%s.png" % n, 290), (680, y - 5))
        d.text((180, 660), "그림", font=F(28), fill=먹, anchor="mm"); d.text((500, 660), "모델 지도", font=F(28), fill=먹, anchor="mm"); d.text((825, 660), "깎은 결과", font=F(28), fill=빨, anchor="mm"); return c
    raise KeyError(키)
