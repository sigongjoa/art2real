# 기능0 3 판 흐름도 — 6 부품 · 판정은 눈(썸네일) 먼저 · 입력 선 그림 + 기능 순서 · 10-11
import os
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
줄 = [(23, "휜 껍질", "휜 판(교차) + 뒤 혹 + 걸이(기둥 · 팔)", .0), (17, "속 빈 상자", "세 윤곽 교차로 충분(ㄴ 판)", .0),
      (29, "속 빈 상자", "세 윤곽 교차 · 오목 접시는 안 함", .0), (33, "회전체 + 블록", "세 윤곽 교차(관통 원통 구멍)", .0),
      (34, "회전체 + 블록", "포크(Z 윤곽) + 목 원기둥 + 공", .0), (11, "돌출", "세 윤곽 교차(비스듬 판)", .0)]
a = Image.open(os.path.join(H, "입력_3판.png")); a = a.resize((1200, 1200)); h = 200
im = Image.new("RGB", (2300, 130 + 6 * h + 170), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "기능 짓기 3 판: 6 부품 더 — 판정은 썸네일(눈) 먼저, 숫자는 보조", font=F(30), fill="black")
d.text((20, 62), "왼쪽 = 입력 여섯 방향 선 그림 + 깊이 · 오른쪽 = 고른 기본 형태와 기능 순서 · 순서는 학습 데이터로 남김(결과/NN.json)", font=F(19), fill=(90, 90, 90))
im.paste(a, (20, 110))
for q, (i, 형, 순, 모) in enumerate(줄):
    y = 110 + q * h + 50; d.text((1250, y), "#%d  %s" % (i, 형), font=F(26), fill="black"); d.text((1250, y + 40), 순, font=F(21), fill=(31, 95, 173)); 
y = im.height - 160; d.rectangle((15, y, im.width - 15, im.height - 15), outline=(31, 95, 173), width=2)
for q, t in enumerate(["판정: 사용자 썸네일 고르기 1 순위 · Claude 눈 6 중 4 이상 모 판보다 같거나 가까움 · 조각 0 · 부피 IoU 보조",
                       "안 함: #29 앞 오목 접시 · #33 옆 육각 · 선 고리 얹기(2 판에서 눈으로 더 나쁨)",
                       "대조: 모 판 + 선 고리 · 사람 부품 — 2 판에서 사용자가 「기능 바탕만」을 고름"]):
    d.text((30, y + 15 + q * 45), t, font=F(21), fill=(200, 40, 40) if q == 0 else "black")
im.save(os.path.join(H, "흐름3.png")); print("ok")
