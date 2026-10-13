# 1c 결과 그림 — 정답 vs 모델(아무것도 안 깎음) · 칸 확률 · 다음 후보(안쪽 닫힌 선도 CV 로) · 10-13
import json, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import 캐드점수2 as K
A = "G:/art2real/out/설명/구멍/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
S = json.load(open(A + "학습3/스냅.json", encoding="utf-8")); W, H = 1800, 2050
바, 카, 테, 하, 흰, 회, 빨, 초, 금 = (10, 15, 30), (18, 26, 46), (44, 58, 90), (64, 196, 255), (236, 242, 250), (120, 134, 160), (255, 100, 100), (110, 220, 140), (255, 205, 70)
c = Image.new("RGB", (W, H), 바); d = ImageDraw.Draw(c)
def 렌더(p, s): return Image.open(A + p).convert("RGB").crop((180, 160, 720, 700)).resize((s, s))
d.text((W // 2, 60), "1c 결과 — 바탕은 맞는데, 아무것도 안 깎았다", font=F(56), fill=흰, anchor="mm")
d.rounded_rectangle((40, 120, W - 40, 900), 30, fill=카, outline=빨, width=3)
for j, (k, 이름) in enumerate(((3, "원기둥 + 구멍"), (5, "상자 + 구멍 · 홈"))):
    y = 160 + j * 370; g = Image.fromarray((255 - K.그림(S["정답"][k]) * 225).astype(np.uint8)).resize((300, 300), Image.NEAREST).convert("RGB"); c.paste(g, (80, y))
    c.paste(렌더("빛_r1c_완성_%d.png" % k, 300), (420, y)); c.paste(렌더("빛_r1c_바탕_%d.png" % k, 300), (760, y))
    for x, t, col in ((230, "그림", 흰), (570, "정답", 초), (910, "모델이 지은 것", 빨)): d.text((x, y + 320), t if j == 0 else "", font=F(30), fill=col, anchor="mm")
    d.text((80, y - 30), 이름, font=F(26), fill=회)
# 칸 확률
d.text((1150, 180), "끝 모델이 칸마다 고르는 확률", font=F(32), fill=하)
for i, (t, v) in enumerate((("없음", 1.0), ("구멍", 0), ("가로 홈", 0), ("세로 홈", 0))):
    y = 250 + i * 90; d.text((1150, y + 20), t, font=F(30), fill=흰); d.rounded_rectangle((1310, y, 1310 + 380, y + 50), 12, fill=(30, 40, 62)); d.rounded_rectangle((1310, y, 1310 + int(380 * v) + 2, y + 50), 12, fill=빨 if v else 회); d.text((1700, y + 25), "%d%%" % (v * 100), font=F(28), fill=흰, anchor="ra")
d.multiline_text((1150, 640), "1,000 걸음 내내 0.875 그대로\n= 윤곽 바탕만 한 것과 같음\n\n아무 데나 깎은 후보는 점수를 깎아 먹음\n→ 「안 깎는 게 제일 안전」으로 무너짐", font=F(28), fill=흰, spacing=10)
# 다음 후보(사용자 결정)
d.rounded_rectangle((40, 940, W - 40, 2010), 30, fill=카, outline=금, width=3); d.text((80, 965), "다음 후보 — 고르는 건 사용자", font=F(40), fill=금)
# A: 안쪽 닫힌 선 CV
g = K.그림(S["정답"][5]); 선 = (g > .3).astype(np.uint8)
import 윤곽바탕 as B
m, _ = B.바깥(g); 안 = (m & (선 == 0)).astype(np.uint8); n, lab, st, _ = cv2.connectedComponentsWithStats(안, connectivity=4)
큰 = 1 + int(np.argmax(st[1:, 4]))   # 가장 큰 칸 = 바탕 윗면 · 나머지 = 선으로 둘러싸인 작은 칸(구멍 · 홈 자리 후보)
v = np.full((128, 128, 3), 245, np.uint8); v[선 > 0] = (190, 190, 200)
for i in range(1, n):
    if i != 큰 and st[i, 4] >= 3: v[lab == i] = (220, 60, 60)
c.paste(Image.fromarray(v).resize((320, 320), Image.NEAREST), (80, 1060)); d.text((240, 1400), "실제로 돌림: 선으로 둘러싸인 작은 칸(빨강)", font=F(24), fill=흰, anchor="mm")
d.multiline_text((440, 1070), "A. 깎을 자리도 그림에서 찾기 (CV · 53 편과 같은 방식)\n   바깥 선처럼 안쪽 닫힌 선을 찾으면 = 구멍 · 홈 자리 후보\n   모델은 「이 자리가 구멍인가 홈인가 · 얼마나 깊은가」만 고름\n   → 아무 데나 깎는 일이 없어짐", font=F(30), fill=흰, spacing=12)
d.multiline_text((80, 1470), "B. 정답 코드로 먼저 따라 배우기(1b)\n   합성은 정답 위치를 아니까 위치부터 가르치고 점수로 다듬기\n\nC. 점수 고치기 — 깎아서 나아진 만큼만 상\n   (위치를 아무 데나 고르는 문제는 그대로 남음)", font=F(30), fill=흰, spacing=12)
d.text((80, 1900), "주의: 진짜 그림의 안쪽 선은 구멍뿐 아니라 무늬 · 색 경계 · 겹친 부품도 있다 — A 는 합성에선 깨끗하지만 원화에선 고르는 일이 남음", font=F(26), fill=회)
c.save(A + "결과_1c.png"); print("ok")
