# 기능0 4 판 흐름도 — 6 부품 · 판정은 눈(썸네일) 먼저 · 입력 선 그림 + 기능 순서 · 10-11
import os
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
줄 = [(3, "다면 덩어리", "교차 → 포켓 Y(왼쪽 깊은 칸)", 0), (15, "다면 덩어리", "교차 → 포켓 Z(아치 굴) · 포켓 X(구멍 턱)", 0),
      (16, "다면 덩어리", "교차로 충분(두 벽 사이 틈)", 0), (18, "다면 덩어리", "교차 → 포켓 Z(가운데 칸)", 0),
      (26, "다면 덩어리", "교차 → 포켓 X(ㄴ 자 굴)", 0), (31, "다면 덩어리", "교차로 충분 · 육각 자리는 안 함", 0)]
a = Image.open(os.path.join(H, "입력_4판.png")); a = a.resize((1200, 1200)); h = 200
im = Image.new("RGB", (2300, 130 + 6 * h + 170), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "기능 짓기 4 판: 다면 덩어리 6 + #23 #29 고치기 — 홈은 「포켓」(고른 네모 안 깊은 곳을 바닥까지)", font=F(30), fill="black")
d.text((20, 62), "왼쪽 = 입력 여섯 방향 선 그림 + 깊이 · 오른쪽 = 고른 기본 형태와 기능 순서 · 순서는 학습 데이터로 남김(결과/NN.json)", font=F(19), fill=(90, 90, 90))
im.paste(a, (20, 110))
for q, (i, 형, 순, 모) in enumerate(줄):
    y = 110 + q * h + 50; d.text((1250, y), "#%d  %s" % (i, 형), font=F(26), fill="black"); d.text((1250, y + 40), 순, font=F(21), fill=(31, 95, 173)); 
y = im.height - 160; d.rectangle((15, y, im.width - 15, im.height - 15), outline=(31, 95, 173), width=2)
for q, t in enumerate(["판정: 사용자 썸네일 고르기 1 순위 · Claude 눈 6 중 4 이상 모 판보다 같거나 가까움 · 조각 0 · 부피 IoU 보조",
                       "고치기: #23 앞면 = 원기둥(잔차 0.3) 두께 3.1 껍질 · #29 앞 접시 = 구 R 23.5 둘 빼기 (둘 다 깊이 맞춤)",
                       "대조: 모 판 + 선 고리 · 사람 부품 · 3 판 #23 #29(부피 1.5 배 · 1.58 배)"]):
    d.text((30, y + 15 + q * 45), t, font=F(21), fill=(200, 40, 40) if q == 0 else "black")
im.save(os.path.join(H, "흐름4.png")); print("ok")
