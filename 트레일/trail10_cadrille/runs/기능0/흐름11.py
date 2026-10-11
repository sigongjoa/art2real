# 둥근 학습 흐름도 · 10-11
import os
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
a = Image.open(os.path.join(H, "둥근흐름.png")); a = a.resize((1400, int(a.height * 1400 / a.width)))
im = Image.new("RGB", (1440, a.height + 560), "white"); d = ImageDraw.Draw(im); im.paste(a, (20, 20))
y = a.height + 40
for q, t in enumerate(["2) 학습 정답: 학습 부품 2,883 개에 둥근 찾기(깊이에서 그린 30° 꺾임 선) → 방향마다 칸 지도 0 없음 · 1 공 · 2 소켓 · 3 볼록 원기둥 · 4 오목 원기둥",
                       "3) 학생: 같은 작은 U-Net · 입력 선 · 실루엣 · 교차 깊이 → 칸 지도 5 갈래 (6 에폭)",
                       "4) 짓기(B 판): 학생 칸 지도의 덩이마다 새 학생 깊이로 구 · 원기둥을 맞춤 → 공은 붙이고 소켓은 빼고 원기둥은 둥글게 깎음",
                       "대조: 지난 B 판(둥근 없음) · 통과된 한 벌",
                       "판정: 사용자 썸네일 1 순위 · Claude 눈 — #5 #13 #34 공 · #29 소켓 4 곳 중 3 이상 생김 · #3 #7 #16 #18 #31 에 잘못 생긴 공 0 · 조각 안 늘기",
                       "안 함: #4 기운 원뿔 · 껍질 두께(휜 판은 겉만 둥글게)"]):
    d.text((20, y + q * 70), t, font=F(22), fill=(200, 40, 40) if q == 4 else "black")
im.save(os.path.join(H, "흐름11.png")); print("ok")
