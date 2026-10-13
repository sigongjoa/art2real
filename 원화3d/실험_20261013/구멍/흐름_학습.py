# 구멍 학습 판 흐름도 · 10-13
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); O = "G:/art2real/out/설명/구멍/흐름_학습.png"
im = Image.new("RGB", (1500, 1500), "white"); d = ImageDraw.Draw(im); 파, 빨, 초, 회 = (30, 90, 200), (200, 40, 40), (20, 140, 60), (110, 110, 110)
d.text((30, 20), "구멍 학습 판 — 그림 → CadQuery 숫자 · 점수로 배우기 (판정기준26 · 10-13)", font=F(36), fill="black")
d.text((30, 75), "목표 줄 확인: 「그림 → CadQuery」 신경망 줄기의 가장 작은 첫걸음 (어휘 = 상자 1 + 구멍 1) · 겹치기 바탕 없음", font=F(24), fill=초)
칸 = [("① 그림", "위에서 본 선 그림 128²\n정육면체 20 mm + 구멍\n반지름 1.5~7 · 위치 ±4 무작위"), ("② 신경망", "작은 CNN\n→ 반지름 · x · y 평균\n+ 흔들 폭"), ("③ 후보 8 개", "평균 주변에서 뽑은\n숫자 8 벌 → CadQuery 코드"),
     ("④ 실제 CAD", "CadQuery 로 짓고\n윗면을 래스터 렌더"), ("⑤ 점수", "그림과 겹친 IoU"), ("⑥ 고침", "그 그림의 후보 평균보다\n높은 후보 쪽으로 (GRPO 식)")]
for k, (t, b) in enumerate(칸):
    x, y = 30 + (k % 3) * 490, 140 + (k // 3) * 260; d.rounded_rectangle((x, y, x + 460, y + 220), 18, outline=파 if k != 4 else 빨, width=4); d.text((x + 20, y + 15), t, font=F(30), fill=파 if k != 4 else 빨); d.multiline_text((x + 20, y + 65), b, font=F(24), fill="black", spacing=8)
    if k % 3 != 2: d.text((x + 465, y + 90), "→", font=F(40), fill=회)
d.text((1100, 630), "③~⑥ 400 걸음 반복", font=F(28), fill=회)
y = 700
for t, c in [("데이터: 학습 그림 600 · 시험 그림 100(학습에 안 씀) · 지켜볼 그림 4(시험에서 고정)", "black"),
             ("대조: ⓐ 학습 전 신경망(무작위) ⓑ 「평균 맞히기」 — 늘 반지름 4.25 · 가운데 (그림을 안 보는 답)", "black"),
             ("판정(미리 적음): 시험 100 평균 IoU ≥ 0.95 · 그리고 평균 맞히기보다 +0.05 이상", 빨),
             ("        실패해도 그대로 쇼츠로(평평한 시간축) — 다시 돌려 고치지 않음", 빨),
             ("스냅: 매 25 걸음 · 지켜볼 그림 4 의 숫자 → CadQuery STL → 끝나고 블렌더 EEVEE 렌더 → 템플릿 프레임", "black"),
             ("쇼츠: 템플릿.json 의 에폭 목록을 스냅으로 채움 · 대화 쇼츠 51 편 · 공개로 올림", "black"),
             ("가져가는 것: CadQuery · 50 편 IoU 재기 · 프레임 템플릿 · 상한.py 8 GB", 초),
             ("안 하는 것: 미분 근사(SDF) · 겹치기 · 생성 3D · 실물 부품(다음 판)", 회),
             ("미리 적는 한계: 장난감 문제 — 어휘 2 개 · 위에서 본 그림 한 장 · 숫자 3 개. 실물 부품으로 가는 건 다음 판", 회)]:
    d.text((30, y), t, font=F(25), fill=c); y += 62
im.save(O); print("ok")
