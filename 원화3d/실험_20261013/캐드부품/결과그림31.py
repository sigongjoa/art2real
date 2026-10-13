# 판정기준31 결과 한 장 — 로드맵 2a → ① → 2b 숫자 + 부품 넷(입력 · 정답 · 2a · 2b) · 10-13
import json, numpy as np
from PIL import Image, ImageDraw, ImageFont
O = "G:/art2real/out/설명/캐드부품/"; A = "G:/art2real/out/설명/구멍/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
a, b = json.load(open(O + "결과31a.json", encoding="utf-8")), json.load(open(O + "결과31b.json", encoding="utf-8")); Ra, Rb = np.load(O + "부피IoU_31a.npy"), np.load(O + "부피IoU_31b.npy")
고른 = [171, 120, 3, 142]; X = np.load(O + "비교31_입력.npy"); e = np.load(O + "데이터_앞옆.npz"); te = np.nonzero(np.load(O + "데이터.npz")["시험"])[0][:200]
W, H = 1800, 1700; c = Image.new("RGB", (W, H), (10, 15, 30)); d = ImageDraw.Draw(c); 흰, 초, 빨, 파, 회 = (236, 242, 250), (110, 220, 140), (255, 100, 100), (64, 196, 255), (150, 160, 180)
d.text((40, 30), "로드맵 2단계 · 판정기준31 — ① 통과 · ② 실패", font=F(48), fill=흰)
표 = [("", "덩어리(중앙)", "깊이 오차", "부피 IoU", "판정"), ("바탕만(윤곽 밀기)", "—", "—", "%.3f" % a["바탕만"], ""), ("2a 위 한 장 · 0.1 층", "17", "0.095", "0.576", "실패"),
     ("① 덩어리마다 깊이 하나", "%d" % a["덩어리_중앙"], "0.095", "%.3f" % a["부피IoU"], "통과"), ("② 2b 위 · 앞 · 옆", "—", "%.3f" % b["깊이오차중앙"], "%.3f" % b["부피IoU"], "실패")]
for i, r in enumerate(표):
    for k, t in enumerate(r): d.text((60 + [0, 520, 820, 1100, 1380][k], 120 + i * 52), t, font=F(32), fill=파 if i == 0 else (초 if t == "통과" else 빨 if t == "실패" else 흰))
d.text((60, 400), "② 기준: 깊이 오차 ≤ 0.066 · 부피 ≥ ① + 0.02 → 깊이는 0.068 까지 줄었지만 부피는 그대로. 부품별로 2b 이김 %d · 짐 %d · 같음 %d" % ((Rb[:, 0] - Ra[:, 0] > .01).sum(), (Rb[:, 0] - Ra[:, 0] < -.01).sum(), (abs(Rb[:, 0] - Ra[:, 0]) <= .01).sum()), font=F(28), fill=흰)
for j, t in enumerate(("입력 그림(위 · 앞 · 옆)", "정답", "2a+① (위 한 장)", "2b+① (세 장)")): d.text((40 + [0, 520, 900, 1300][j], 470), t, font=F(30), fill=파)
s = 300
for r, k in enumerate(고른):
    y = 520 + r * 290; i = te[k]
    for q, im in enumerate((X[r], e["F"][i], e["S"][i])): c.paste(Image.fromarray((255 - im * 225).astype(np.uint8)).resize((150, 150)).convert("RGB"), (40 + q * 160, y + 30))
    for q, t in enumerate(("정답", "2a", "2b")): c.paste(Image.open(A + "빛_r31_%d_%s.png" % (k, t)).convert("RGB").crop((130, 110, 770, 750)).resize((270, 270)), (520 + q * 400, y))
    d.text((1580, y + 100), "%.2f" % Ra[k, 0], font=F(32), fill=흰); d.text((1580, y + 150), "→ %.2f" % Rb[k, 0], font=F(32), fill=초 if Rb[k, 0] > Ra[k, 0] else 빨)
d.text((1580, 490), "부피 IoU", font=F(26), fill=회)
c.save(O + "결과31.png"); print("ok")
