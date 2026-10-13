# 1d 결과 한 장 — 지켜본 6: 그림 · 정답 · 모델 지도 · 모델 CAD · IoU / 에폭별 시험 IoU / 진짜 그림 · 10-13
import json, numpy as np
from PIL import Image, ImageDraw, ImageFont
import 캐드점수2 as K
A = "G:/art2real/out/설명/구멍/"; L = A + "학습4/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
S = json.load(open(L + "스냅.json", encoding="utf-8")); W, H = 1800, 2560
바, 카, 테, 하, 흰, 회, 빨, 초, 금 = (10, 15, 30), (18, 26, 46), (44, 58, 90), (64, 196, 255), (236, 242, 250), (120, 134, 160), (255, 100, 100), (110, 220, 140), (255, 205, 70)
c = Image.new("RGB", (W, H), 바); d = ImageDraw.Draw(c)
def 렌더(p, s): return Image.open(A + p).convert("RGB").crop((180, 160, 720, 700)).resize((s, s))
def 지도(p, s):
    a = np.asarray(Image.open(p)) // 120; v = np.full(a.shape + (3,), 235, np.uint8); v[a == 1] = (230, 80, 80); v[a == 2] = (80, 140, 235); return Image.fromarray(v).resize((s, s), Image.NEAREST)
d.text((W // 2, 55), "1d 결과 — U-Net 화소 지도로 구멍 · 홈을 깎았다", font=F(56), fill=흰, anchor="mm")
끝 = S["스냅"][-1]; d.text((W // 2, 125), "처음 보는 200 개: IoU 0.875 → %.3f (기준 0.95 · 통과) · 깎을 자리 화소 IoU %.3f · 20 에폭" % (끝["시험IoU"], 끝["화소IoU"]), font=F(32), fill=초, anchor="mm")
for j, t in enumerate(("그림", "정답", "모델 지도", "모델이 깎은 CAD")): d.text((215 + j * 300, 190), t, font=F(30), fill=(하 if j > 1 else 흰), anchor="mm")
for k in range(6):
    y = 220 + k * 270; s = 250
    g = Image.fromarray((255 - K.그림(S["정답"][k]) * 225).astype(np.uint8)).resize((s, s), Image.NEAREST).convert("RGB"); c.paste(g, (90, y))
    c.paste(렌더("빛_r54_정답_%d.png" % k, s), (390, y)); c.paste(지도(L + "지도_e20_%d.png" % k, s), (690, y)); c.paste(렌더("빛_r54_e20_%d.png" % k, s), (990, y))
    v = 끝["지켜볼"][k]["IoU"]; d.text((1290, y + 100), S["범주"][k].replace("+", " + "), font=F(28), fill=회); d.text((1290, y + 150), "IoU %.3f" % v, font=F(40), fill=초 if v >= .95 else 금)
# 에폭별 곡선
y0 = 1880; d.rounded_rectangle((40, y0, 880, H - 40), 26, fill=카, outline=테, width=3); d.text((70, y0 + 20), "에폭마다 처음 보는 200 개 IoU", font=F(30), fill=하)
xs = [100 + e * 36 for e in range(21)]; f = lambda v: y0 + 560 - (v - .85) / (.15) * 440
d.line((100, f(.875), 820, f(.875)), fill=회, width=2); d.text((830, f(.875)), "바탕만 0.875", font=F(20), fill=회, anchor="rm")
d.line((100, f(.95), 820, f(.95)), fill=금, width=2); d.text((830, f(.95) - 14), "기준 0.95", font=F(20), fill=금, anchor="rm")
pts = [(xs[i], f(s_["시험IoU"])) for i, s_ in enumerate(S["스냅"])]; d.line(pts, fill=초, width=5)
for p in pts: d.ellipse((p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6), fill=초)
d.text((100, y0 + 590), "0", font=F(22), fill=회); d.text((820, y0 + 590), "20 에폭", font=F(22), fill=회, anchor="ra")
# 진짜 그림
d.rounded_rectangle((920, y0, W - 40, H - 40), 26, fill=카, outline=빨, width=3); d.text((950, y0 + 20), "진짜 그림(메카2) — 아직 안 됨", font=F(30), fill=빨)
for j, n in enumerate(("머리", "발")):
    y = y0 + 80 + j * 290; g = Image.open("G:/art2real/out/영상05/대화/49_진짜그림/자료/%s_앞그림.png" % n).convert("RGB").resize((250, 250)); c.paste(g, (960, y)); c.paste(지도(L + "진짜지도_%s.png" % n, 250), (1230, y)); c.paste(렌더("빛_r54_진짜_%s.png" % n, 250), (1500, y))
c.save(A + "결과_1d.png"); print("ok")
