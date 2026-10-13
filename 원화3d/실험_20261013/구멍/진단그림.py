# 원기둥 쏠림 진단 그림 · 10-13
import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
A = "G:/art2real/out/설명/구멍/"; D = json.load(open(A + "학습2/진단_원기둥.json", encoding="utf-8")); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
W, H = 1600, 1150; 바, 카, 테, 하, 흰, 회, 빨, 초, 금 = (10, 15, 30), (18, 26, 46), (44, 58, 90), (64, 196, 255), (236, 242, 250), (120, 134, 160), (255, 100, 100), (110, 220, 140), (255, 205, 70)
c = Image.new("RGB", (W, H), 바); d = ImageDraw.Draw(c)
d.text((W // 2, 55), "왜 처음부터 다 직사각형이었나 — 50 걸음 진단", font=F(50), fill=흰, anchor="mm")
# 왼쪽: 걸음 0 화면(6 칸 모두 상자)
im = Image.open(A + "빛_r52_s0000_3.png").convert("RGB").crop((180, 160, 720, 700)).resize((300, 300)); g = Image.open(A + "학습2/그림_3.png").resize((110, 110))
d.rounded_rectangle((40, 120, 520, 560), 26, fill=카, outline=테, width=3); c.paste(im, (60, 150)); c.paste(g, (380, 150)); d.text((280, 480), "원기둥 문제인데 걸음 0 부터 상자", font=F(28), fill=빨, anchor="mm")
d.text((280, 525), "처음 원기둥 확률 평균 %.2f → 고르면 상자 %d %%" % (D["처음_원기둥확률_평균"], round(100 * (1 - D["처음_원기둥으로_고른_비율(argmax)"]))), font=F(24), fill=흰, anchor="mm")
# 오른쪽: 걸음마다 원기둥이 후보로 뽑힌 비율 막대
x0, y0, w, h = 600, 150, 950, 380; d.rounded_rectangle((x0 - 30, 120, x0 + w + 20, 560), 26, fill=카, outline=테, width=3)
d.text((x0, 135), "후보 중 원기둥이 뽑힌 비율(걸음마다)", font=F(30), fill=하)
for i, g_ in enumerate(D["걸음"]):
    v = g_["원기둥_뽑힌비율"]; bx = x0 + i * (w / 50); d.rectangle((bx, y0 + 40 + h - 20 - v * (h - 60) / .5, bx + w / 50 - 3, y0 + 40 + h - 20), fill=금 if v > 0 else 빨)
d.line((x0, y0 + 40 + h - 20, x0 + w, y0 + 40 + h - 20), fill=회, width=2); d.text((x0, y0 + h + 30), "0", font=F(24), fill=회); d.text((x0 + w, y0 + h + 30), "50 걸음", font=F(24), fill=회, anchor="ra")
d.text((x0 + 380, y0 + 200), "20 걸음부터 0 % — 원기둥이 사라짐", font=F(30), fill=빨)
# 아래: 읽기 · 고칠 것
d.rounded_rectangle((40, 600, W - 40, 1110), 26, fill=카, outline=초, width=3); d.text((80, 625), "읽기", font=F(38), fill=초)
g0 = D["걸음"][:10]; 원 = [x["원기둥문제_원기둥후보점수"] for x in g0 if x["원기둥문제_원기둥후보점수"] is not None]; 상 = [x["원기둥문제_상자후보점수"] for x in g0 if x["원기둥문제_상자후보점수"] is not None]
for k, t in enumerate(("① 시작부터 상자 쪽으로 기울어 있었다(원기둥 확률 0.41) — 화면엔 6 칸 모두 상자로 보임",
                       "② 처음 10 걸음 원기둥 문제에서 원기둥 후보 %.2f · 상자 후보 %.2f — 점수 차이가 거의 없음(구멍 · 홈이 아무렇게나라)" % (sum(원) / len(원), sum(상) / len(상)),
                       "③ 그 상태에서 몇 걸음 만에 원기둥 확률이 0 으로 무너짐 → 그 뒤엔 시도조차 안 함",
                       "고칠 것: 시작을 50 : 50 으로 · 학습 중에도 원기둥을 일정 비율 이상 계속 뽑게(탐색 바닥)")):
    d.text((80, 700 + k * 95), t, font=F(29), fill=금 if k == 3 else 흰)
c.save(A + "진단_원기둥.png"); print("ok")
