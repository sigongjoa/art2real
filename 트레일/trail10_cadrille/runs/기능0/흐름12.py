# I 판(구간 회전) 흐름도 · 10-13
import os
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
W_ = 1440; im = Image.new("RGB", (W_, 1560), "white"); d = ImageDraw.Draw(im)
d.text((30, 20), "I 판 — 회전을 부품 통째가 아니라 구간에만 (판정기준25 · 10-13)", font=F(34), fill="black")
def 상자(x, y, w, h, 제목, 줄, 색):
    d.rounded_rectangle((x, y, x + w, y + h), 14, outline=색, width=4)
    d.text((x + 16, y + 10), 제목, font=F(26), fill=색)
    for k, t in enumerate(줄): d.text((x + 16, y + 52 + k * 32), t, font=F(21), fill="black")
def 화살(x, y0, y1): d.line((x, y0, x, y1), fill="gray", width=5); d.polygon([(x - 12, y1 - 16), (x + 12, y1 - 16), (x, y1)], fill="gray")
파, 빨, 초, 회 = (30, 90, 200), (200, 40, 40), (20, 140, 60), (110, 110, 110)
상자(30, 80, 860, 120, "1) 입력 (H 와 같음)", ["선 그림 3 장 → 3D 학생 부피 64³ ∩ 세 윤곽 교차 (회전2.학생부피 그대로)"], 파)
화살(460, 200, 240)
상자(30, 240, 860, 190, "2) 찾기 — 여기만 바뀜", ["주축을 따라 단면 64 칸마다 「둥근가」(H 와 같은 규칙 · 같은 문턱)",
                                          "H: 전체 칸의 80 % 가 둥글어야 부품 통째로 회전",
                                          "I: 둥근 칸이 10 칸 이상 이어진 구간마다 따로 회전"], 빨)
화살(460, 430, 470)
상자(30, 470, 860, 190, "3) 짓기", ["구간마다 반쪽 윤곽 회전(기운 축 그대로)",
                                 "교차 - (구간 판 - 회전체) = 그 구간만 둥글게 깎기",
                                 "조각이 늘거나 부피가 30 % 넘게 줄면 그 구간은 버림 · 다음 공 관절은 그대로"], 파)
# 오른쪽 그림: 교차(각짐) → H(통째로 안 걸림) → I(가운데 구간만 둥글게)
def 부품(x, y, 둥근):
    d.rectangle((x + 30, y, x + 110, y + 60), outline="black", width=3, fill=(220, 220, 220))          # 머리 상자
    if 둥근: d.rounded_rectangle((x + 40, y + 60, x + 100, y + 200), 30, outline=빨, width=4, fill=(250, 210, 210))
    else: d.rectangle((x + 40, y + 60, x + 100, y + 200), outline="black", width=3, fill=(220, 220, 220))
    d.rectangle((x, y + 200, x + 140, y + 240), outline="black", width=3, fill=(220, 220, 220))          # 받침
for k, (t, r) in enumerate([("교차", 0), ("H", 0), ("I", 1)]):
    부품(930 + k * 165, 130, r); d.text((970 + k * 165, 380), t, font=F(26), fill=빨 if r else "black")
d.text((930, 430), "H: 상자 · 받침 때문에 80 % 미달 → 안 걸림", font=F(19), fill=회)
d.text((930, 460), "I: 가운데 원기둥 구간만 둥글게", font=F(19), fill=빨)
y = 700
for t, c in [("대조: H (지금 기본 · 짓기C.py HREV=1) · 같은 부품 같은 학생(부피학생G)", "black"),
             ("세트: 개발 검증2 40 부품 — H 가 통째로 회전한 부품은 I 도 똑같음 · 처음 보는 4 모델(검증4)은 아끼고 통과하면 그때 씀", "black"),
             ("싼 확인 먼저: 구간이 걸리는 부품 수를 세고 썸네일로 보여 드림 → 0~2 개면 짓지 않고 멈춤", 초),
             ("판정: 가린 시트 · 맥락 없는 판사 둘(서브 에이전트) · 판사 대조 ≥ 9/10", 빨),
             ("        기준 I - H ≥ +0.05 (40 중 2 개 더 통과) · 짓기 실패 ≤ 2 · 5 분 넘으면 실패 · 8 GB 상한", 빨),
             ("        눈 판정 1 순위 — 바뀐 부품 나란히 썸네일 보냄", 빨),
             ("가져가는 것: 3D 학생 G · 회전2 의 단면 둥근 규칙과 문턱 · 공 관절 · 판사 시트(가린시트3.py)", 초),
             ("안 하는 것: 새 학습 · 필렛 · 홈 파기 · 처음 보는 검증 소모 · 문턱 바꾸기", 회),
             ("미리 적는 한계: 축은 부품 전체의 주축 하나 — 옆으로 뻗은 원기둥(팔 · 핀)의 구간은 못 잡음", 회)]:
    d.text((30, y), t, font=F(23), fill=c); y += 52
im = im.crop((0, 0, W_, y + 30)); im.save(os.path.join(H, "판정기준25_흐름.png")); print("ok")
