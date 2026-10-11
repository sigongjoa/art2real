# 기능0 흐름도 — 천장 시험: #4 #21 을 CAD 기능(돌출 · 로프트 · 필렛 · 셸 · 자르기)으로 손 짓기 · 10-11
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
글 = {4: ["읽은 것 (위 · 옆 · 앞 선 + 깊이)",
          "· 앞에서 C 자 → 원뿔 껍질 (반지름 116→107, 축 조금 기움)",
          "· 앞뒤 깊이 차 → 두께 약 3.5 mm",
          "· 옆에서 윗변 비스듬 → 비스듬한 평면 자르기",
          "· 아래 끝 띠 두 줄 → 바깥 2 화소 두꺼운 띠",
          "짓기: 원뿔 로프트 빼기 안쪽 원뿔 → 반 자르기 → 윗면 자르기 → 띠 더하기",
          "안 함: 겉의 네모 판 무늬(작은 디테일)"],
      21: ["읽은 것",
          "· 뒤에서 둥근 네모 테 + 창 → 몸통 + 창 뚫기",
          "· 옆에서 D 자(위 둥근 모서리 · 아래 큰 휨) → 옆 윤곽 돌출로 깎기",
          "· 위에서 뒤쪽 모서리 둥긂 → 위 윤곽으로 깎기",
          "· 앞에서 테 폭 5 화소 · 안 깊음 → 앞이 열린 셸 6 mm",
          "· 위에서 줄 셋 → 환기 구멍 3 개",
          "짓기: 몸통 → 필렛 → 셸(앞 열림) → 창 → 구멍 3",
          "안 함: 안쪽 바닥 비탈(선에 안 보임)"]}
im = Image.new("RGB", (2340, 1260), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "기능 짓기 천장 시험: 실루엣 겹치기 대신 CAD 설계자처럼 기능 순서로 · #4 #21 손으로", font=F(32), fill="black")
d.text((20, 65), "입력 = 선 고리와 같은 여섯 방향 선 그림(빨강) + 깊이(회색, A 판) · 숫자는 이 그림에서만 읽는다 · 지어낸 치수 없음", font=F(20), fill=(90, 90, 90))
for r_, i in enumerate((4, 21)):
    y = 110 + r_ * 480; d.text((20, y), "#%d %s" % (i, "휜 등판" if i == 4 else "로봇 아래 머리"), font=F(28), fill="black")
    a = Image.open(os.path.join(H, "입력_%d.png" % i)); a = a.resize((1400, int(a.height * 1400 / a.width))); im.paste(a, (20, y + 45))
    for q, t in enumerate(("앞(X)", "뒤", "위(Y)", "아래", "뒤(Z)", "앞")): d.text((20 + q * 233 + 116, y + 45 + a.height + 15), t, font=F(18), fill=(90, 90, 90), anchor="mm")
    for q, t in enumerate(글[i]): d.text((1450, y + 45 + q * 40), t, font=F(20), fill=(200, 40, 40) if t.startswith("안 함") else (31, 95, 173) if t.startswith("짓기") else "black")
y = 1080; d.rectangle((15, y, im.width - 15, im.height - 15), outline=(31, 95, 173), width=2)
for q, t in enumerate(["대조: 같은 부품의 모 판 결과(#4 0.41 · #21 0.45) · 사람 부품",
                       "판정: 눈 — #4 얇은 휜 껍질 · 지느러미 없음 / #21 매끈한 둥근 테 · 앞 열림 · 창 · 구멍 셋 · 점수 둘 다 모 판보다 높음 · 조각 0",
                       "되면: 이 읽기를 규칙으로 옮겨 35 부품 자동 · 안 되면: 이 방향 접음"]):
    d.text((30, y + 15 + q * 50), t, font=F(22), fill=(200, 40, 40) if q == 1 else "black")
im.save(os.path.join(H, "흐름.png")); print("ok")
