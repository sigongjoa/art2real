# ② 실패 가르기 한 장 — 천장 막대 + 0 점 원인 · 10-13
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); 흰, 초, 빨, 파, 회, 금 = (236, 242, 250), (110, 220, 140), (255, 100, 100), (64, 196, 255), (150, 160, 180), (240, 190, 60)
c = Image.new("RGB", (1800, 1150), (10, 15, 30)); d = ImageDraw.Draw(c); d.text((40, 30), "로드맵 2단계 · ② 는 왜 안 올랐나 — 같은 시험 200 · 부피 IoU", font=F(46), fill=흰)
막 = [("바탕만(모델 윤곽 밀기)", .548, 회), ("2a 위 한 장 · 0.1 층", .576, 빨), ("① 덩어리 깊이", .593, 초), ("② 2b 위 · 앞 · 옆", .592, 빨), ("천장: 정답 지도 + 정답 깊이", .654, 금), ("완벽", 1.0, 회)]
x0, sc = 560, 1150
for i, (t, v, col) in enumerate(막):
    y = 130 + i * 78; d.text((40, y + 10), t, font=F(32), fill=흰); d.rounded_rectangle((x0, y, x0 + int(sc * v), y + 56), 12, fill=col); d.text((x0 + int(sc * v) - 12, y + 28), "%.3f" % v, font=F(30), fill=(10, 15, 30), anchor="rm")
d.line((x0 + int(sc * .654), 120, x0 + int(sc * .654), 600), fill=금, width=3)
글 = [("① 표현 천장", 금, "위에서만 파 들어가는 방식은 정답을 그대로 줘도 0.654. 옆 구멍 · 세운 벽 · 아래쪽 홈은 못 만든다.\n   ① 에서 천장까지 남은 건 0.06 뿐 — ② 기준 +0.02 는 그 1/3 을 요구했다."),
     ("② 짓기가 부서진다", 빨, "몸통 윤곽이 「꼬였다」고 통째로 버려지거나 깎고 나니 빈 것 → 0 점. 정답 지도도 5 개, 2b 는 10 개.\n   0 점 부품을 빼면 2a 0.617 · 2b 0.623 (+0.006)."),
     ("③ 깊이는 좋아졌다", 초, "깊이 오차 0.095 → 0.068 · 화소 mIoU 0.657 → 0.751. 모델은 나아졌지만 부피 점수로는 거의 안 옮겨진다.")]
for i, (t, col, s) in enumerate(글): y = 640 + i * 165; d.text((40, y), t, font=F(36), fill=col); d.multiline_text((60, y + 52), s, font=F(28), fill=흰, spacing=10)
c.save("G:/art2real/out/설명/캐드부품/진단31.png"); print("ok")
