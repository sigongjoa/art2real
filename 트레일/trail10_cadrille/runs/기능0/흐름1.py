# 기능0 1 판 흐름도 — 쉬운 6 부품 · 입력 선 그림 + 기능 순서 · 10-11
import os
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
줄 = [(24, "휜 껍질", "단면(Y) 밀기 → 옆 · 위 윤곽으로 다듬기", .68), (8, "속 빈 상자", "집 모양(X) 밀기 → 고리(Y) 교차 = 관 → 위(Z) 창", .66),
      (32, "돌출", "ㄷ 단면(Y) 두께만큼 밀기 → 팔 끝 필렛 → 핀 구멍", .417), (22, "돌출", "X 자 윤곽(Z) 밀기 → 앞뒤 면 모따기", .516),
      (13, "회전체 + 블록", "공 + 몸통(Z 윤곽) + 축 원기둥 + 원판", .626), (10, "회전체 + 블록", "Y 봉(납작) + 홈 셋 + 포크(Z 윤곽) + 끝 슬릿", .631)]
a = Image.open(os.path.join(H, "입력_1판.png")); a = a.resize((1200, 1200)); h = 200
im = Image.new("RGB", (2300, 130 + 6 * h + 170), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "기능 짓기 1 판: 쉬운 6 부품을 손으로 — 기능 순서는 제가 정하고 숫자는 그림에서", font=F(30), fill="black")
d.text((20, 62), "왼쪽 = 입력 여섯 방향 선 그림 + 깊이 · 오른쪽 = 고른 기본 형태와 기능 순서 · 순서는 학습 데이터로 남김(결과/NN.json)", font=F(19), fill=(90, 90, 90))
im.paste(a, (20, 110))
for q, (i, 형, 순, 모) in enumerate(줄):
    y = 110 + q * h + 50; d.text((1250, y), "#%d  %s" % (i, 형), font=F(26), fill="black"); d.text((1250, y + 40), 순, font=F(21), fill=(31, 95, 173)); d.text((1250, y + 75), "대조: 모 판 선 고리 %.2f" % 모, font=F(18), fill=(90, 90, 90))
y = im.height - 160; d.rectangle((15, y, im.width - 15, im.height - 15), outline=(31, 95, 173), width=2)
for q, t in enumerate(["판정: 6 중 4 이상이 모 판 점수 이상 · 조각 0 · 눈으로 지느러미 · 부스러기 없음",
                       "안 함: 작은 무늬(#32 손잡이 줄 · #10 나사 결) · 자동화 — 이번은 손으로 순서를 쌓는 판",
                       "#24 #8 은 세 윤곽 교차가 곧 기능 순서(바탕과 같음) — 「교차로 충분한 부품」이라는 표식도 데이터"]):
    d.text((30, y + 15 + q * 45), t, font=F(21), fill=(200, 40, 40) if q == 0 else "black")
im.save(os.path.join(H, "흐름1.png")); print("ok")
