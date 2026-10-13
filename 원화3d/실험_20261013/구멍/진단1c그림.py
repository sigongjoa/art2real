# 1c 근본 원인 그림 · 10-13
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); O = "G:/art2real/out/설명/구멍/진단_1c.png"
W, H = 1700, 1250; 바, 카, 테, 하, 흰, 회, 빨, 초, 금 = (10, 15, 30), (18, 26, 46), (44, 58, 90), (64, 196, 255), (236, 242, 250), (120, 134, 160), (255, 100, 100), (110, 220, 140), (255, 205, 70)
c = Image.new("RGB", (W, H), 바); d = ImageDraw.Draw(c); d.text((W // 2, 55), "왜 아무것도 안 깎았나 — 깎으면 대부분 손해였다", font=F(50), fill=흰, anchor="mm")
막 = [("정답 자리 · 정답 크기로 깎기", 100, 초, "점수기 정상 0.838 → 0.990"), ("정답 자리 ± 0.3 mm", 98.7, 초, ""), ("정답 자리 ± 1.0 mm", 66.5, 금, ""),
      ("정답 자리 ± 1.65 mm (처음 흔들 폭)", 41.3, 빨, "평균 −0.009"), ("아무 데나 한 칸", 4.3, 빨, "평균 −0.103")]
d.text((60, 120), "깎았을 때 「바탕만」보다 점수가 오른 비율", font=F(34), fill=하)
for i, (t, v, col, 주) in enumerate(막):
    y = 190 + i * 120; d.text((60, y + 25), t, font=F(30), fill=흰); d.rounded_rectangle((640, y, 640 + 800, y + 70), 14, fill=(30, 40, 62)); d.rounded_rectangle((640, y, 640 + int(8 * v) + 2, y + 70), 14, fill=col)
    d.text((1460, y + 35), "%.1f%%" % v, font=F(32), fill=흰, anchor="lm"); d.text((660, y + 90), 주, font=F(22), fill=회)
d.rounded_rectangle((40, 820, W - 40, 1210), 26, fill=카, outline=금, width=3)
d.multiline_text((80, 850), "처음 모델은 그림과 상관없이 늘 가운데를 찍고(흩어짐 0.3 mm), 1.65 mm 로 크게 흔든다\n→ 「깎기」를 고른 후보는 평균 손해 · 「없음」만 손해가 없다 → 학습이 「없음」으로 무너짐\n\n코드 버그 아님 — 깎을 자리를 1 mm 안으로 찾아갈 길이 없는 탐색 구조의 문제\n가설: 깎을 자리가 처음부터 맞으면 학습이 된다 → 시험: 안쪽 칸 위치를 CV 로 주고 「깎나 · 무엇으로」만 배우기", font=F(30), fill=흰, spacing=14)
c.save(O); print("ok")
