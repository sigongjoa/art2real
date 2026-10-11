# 기능0 학습 흐름도 — 자동 정답 찾기 → 학습 → 시험 · 1 단계(찾기 맞춤 검사)만 이번 판 · 10-11
import os, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import 탐색 as T
H = os.path.dirname(os.path.abspath(__file__)); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
x = T.X_("시험")[23].astype(np.float32); S = x[0] > .5; D, Dh = x[3], x[2]
im = Image.new("RGB", (2300, 1180), "white"); d = ImageDraw.Draw(im)
d.text((20, 15), "학습으로 가는 길: 손 20 부품은 시험지 · 학습 정답은 학습 부품 2,883 개에서 자동으로 찾는다", font=F(30), fill="black")
d.text((20, 62), "예: #23 — 여섯 방향에서 「교차가 실물보다 튀어나온 곳」(실물 깊이 빼기 교차 깊이 > 3 칸) = 후보 홈 (빨강)", font=F(20), fill=(90, 90, 90))
for k in range(6):
    a = np.full((128, 128, 3), 255, np.uint8); a[S[k]] = (225, 228, 236); a[S[k] & (D[k] - Dh[k] > 3 / 128)] = (220, 60, 60)
    im.paste(Image.fromarray(cv2.resize(a, (300, 300), interpolation=cv2.INTER_NEAREST)), (20 + k * 315, 110))
    d.text((20 + k * 315 + 150, 425), ("앞 X-", "앞 X+", "위 Y-", "위 Y+", "옆 Z-", "옆 Z+")[k], font=F(18), fill=(90, 90, 90), anchor="mm")
단 = [("1 단계 (이번 판)", "자동 찾기: 교차(복셀)에서 시작 → 후보 기능 하나씩 더해 보고 정답 깊이 복셀과 IoU 가 제일 오르는 것을 고름 · 부스러기 생기면 버림 · 최대 6 개", (200, 40, 40)),
      ("", "후보 = 포켓(빨강 덩이 · 평평 바닥) · 구 빼기(오목 덩이가 구에 맞을 때) · 원기둥 껍질(한 면 깊이가 원기둥에 맞을 때) — 숫자는 깊이에서 맞춤", "black"),
      ("", "검사: 손으로 지은 20 부품에 돌려 「정답을 볼 때 손만큼 고르나」 — 못 하면 학습 정답이 틀린 것 → 학습 안 함", "black"),
      ("2 단계", "학습 부품 2,883 개에 자동 찾기 → 후보마다 「쓴다 / 안 쓴다」 정답 → 선 그림만 보고 고르는 작은 모델 학습", (90, 90, 90)),
      ("3 단계", "시험 35 부품: 모델이 고른 것 / 손 / 교차만 — 썸네일로 사용자가 판정 · IoU 보조", (90, 90, 90))]
for q, (h, t, c) in enumerate(단):
    y = 470 + q * 70
    if h: d.text((20, y), h, font=F(24), fill=c)
    d.text((220, y + 2), t, font=F(20), fill=c)
y = im.height - 190; d.rectangle((15, y, im.width - 15, im.height - 15), outline=(31, 95, 173), width=2)
for q, t in enumerate(["1 단계 판정: 20 부품 중 12 이상에서 자동 IoU ≥ 손 IoU (정답 깊이 복셀 기준) · 중앙 얻음(자동 빼기 교차) ≥ 0.05 · 조각 0",
                       "같이 볼 것: #23 #29 #15 처럼 손이 휜 면 · 구를 쓴 곳에서 자동도 그 기능을 고르나",
                       "안 함: 학습(2 단계) — 1 단계가 통과해야 시작 · 메시 정답 대신 「보이는 깊이로 깎은 복셀」을 정답으로 씀(손도 같은 자로 잼)"]):
    d.text((30, y + 15 + q * 52), t, font=F(21), fill=(200, 40, 40) if q == 0 else "black")
im.save(os.path.join(H, "흐름5.png")); print("ok")
