# 기능0 2 판 흐름도 — 기능 바탕 위에 선 고리 판 얹기 · 10-11
import os
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 260
a = Image.open(os.path.join(H, "결과1.png")); w = 3 * C + 20
im = Image.new("RGB", (130 + 2 * w + 700, 100 + 2 * (C + 50) + 200), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "기능 2 판: 손으로 지은 기능 바탕 위에 선 고리(홈 · 턱 파기)를 그대로 얹는다", font=F(30), fill="black")
d.text((130 + w // 2, 75), "지금 최선: 꺾은선 → 모 바탕 + 선 고리", font=F(20), fill=(31, 95, 173), anchor="mm"); d.text((130 + w + w // 2, 75), "바꿀 것: 기능 바탕(손) + 선 고리", font=F(20), fill=(200, 40, 40), anchor="mm")
for r_, row in enumerate((3, 4)):
    y0 = 100 + row * (C + 50)
    for j, col in enumerate((1, 2)): im.paste(a.crop((130 + col * w, y0, 130 + col * w + w, y0 + C + 45)), (130 + j * w, 100 + r_ * (C + 50)))
    d.text((20, 100 + r_ * (C + 50) + C // 2), ("#22", "#13")[r_], font=F(30), fill="black")
x = 130 + 2 * w + 30
for q, t in enumerate(["바탕만 바꿔 끼움 (BASE=_기능)", "선 고리 설정은 5 판 그대로", "LINES=mesh MINA=4 CHECK=1", "SHELLOP=1 WALLMAX=6", "", "대상 8 부품: #4 #21 #24 #8", "#32 #22 #13 #10 (손으로 지은 것)", "", "기대: 모양은 기능 바탕(깔끔)", "선 점수는 홈 · 턱이 채움"]):
    d.text((x, 130 + q * 38), t, font=F(21), fill="black")
y = im.height - 170; d.rectangle((15, y, im.width - 15, im.height - 15), outline=(31, 95, 173), width=2)
for q, t in enumerate(["대조: 같은 8 부품의 모 판 선 고리 (A 판 · 정답 깊이) · 기능 바탕만(손)",
                       "판정: 8 중 5 이상이 모 판 선 고리 점수 이상 · 조각 합 ≤ 모 판 조각 합 · 눈으로 기능 바탕 모양이 안 깨짐",
                       "안 함: 새 부품 손 짓기 — 이 판이 되면 그다음에 늘림"]):
    d.text((30, y + 15 + q * 45), t, font=F(21), fill=(200, 40, 40) if q == 1 else "black")
im.save(os.path.join(H, "흐름2.png")); print("ok")
