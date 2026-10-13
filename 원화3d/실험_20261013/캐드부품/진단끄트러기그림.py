# 끄트러기 원인 가르기 그림 · 10-13
import json
from PIL import Image, ImageDraw, ImageFont
O = "G:/art2real/out/설명/캐드부품/"; R = json.load(open(O + "진단_끄트러기.json", encoding="utf-8")); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
W, H = 1800, 1350; 바, 카, 테, 하, 흰, 회, 빨, 초, 금 = (10, 15, 30), (18, 26, 46), (44, 58, 90), (64, 196, 255), (236, 242, 250), (120, 134, 160), (255, 100, 100), (110, 220, 140), (255, 205, 70)
c = Image.new("RGB", (W, H), 바); d = ImageDraw.Draw(c); d.text((W // 2, 55), "끄트러기는 어디서 오나 — 종류 · 깊이 지도를 정답/모델로 바꿔 끼움(시험 200)", font=F(42), fill=흰, anchor="mm")
행 = [("A 정답 종류 · 정답 깊이", "A 정답·정답", 초), ("B 모델 종류 · 정답 깊이", "B 모델종류·정답깊이", 금), ("C 정답 종류 · 모델 깊이", "C 정답종류·모델깊이", 빨), ("D 모델 · 모델 (지금)", "D 모델·모델", 빨)]
for j, (t, x0, w) in enumerate((("깎은 덩어리 수(중앙)", 560, 20), ("20 화소 미만 조각(평균)", 960, 14), ("부피 IoU(앞 60)", 1360, None))): d.text((x0 + 170, 140), t, font=F(28), fill=하, anchor="mm")
for i, (t, k, col) in enumerate(행):
    y = 200 + i * 130; r = R[k]; d.text((60, y + 30), t, font=F(32), fill=흰)
    for x0, v, mx, 글 in ((560, r["덩어리_중앙"], 20, "%.0f" % r["덩어리_중앙"]), (960, r["작은조각_평균"], 14, "%.1f" % r["작은조각_평균"]), (1360, (r["부피IoU_60"] - .55) / .15, 1, "%.3f" % r["부피IoU_60"])):
        d.rounded_rectangle((x0, y + 10, x0 + 300, y + 60), 10, fill=(30, 40, 62)); d.rounded_rectangle((x0, y + 10, x0 + max(int(300 * v / mx), 4), y + 60), 10, fill=col); d.text((x0 + 310, y + 35), 글, font=F(28), fill=흰, anchor="lm")
d.rounded_rectangle((40, 760, W - 40, H - 40), 26, fill=카, outline=금, width=3); d.text((80, 785), "읽기", font=F(38), fill=금)
d.multiline_text((80, 850), "① 깊이 흔들림이 주범 — 종류만 정답으로 두고 깊이만 모델로 바꿔도(C) 덩어리 8 → 15.5 · 작은 조각 6.5 → 10.1\n② 종류 흔들림은 조금 — 깊이를 정답으로 두면(B) 덩어리 9 · 작은 조각 7.7\n③ 둘이 겹치면 더 나빠짐 — 지금(D) 덩어리 17 · 부피 0.668 → 0.608\n④ 정답으로 지어도(A) 작은 조각이 평균 6.5 — 곡면 · 비탈을 0.1 층으로 자르면 정답도 띠로 쪼개짐(층 방식 자체의 한계)\n\n다음 시험(고치기 전 가설 하나): 「덩어리마다 깊이 하나(중앙값)」로 깎으면 C · D 의 덩어리 · 조각이 A 수준으로 줄어드나", font=F(29), fill=흰, spacing=14)
c.save(O + "진단_끄트러기.png"); print("ok")
