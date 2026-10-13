# 왜 끄트러기가 생기나 — 모델 지도(화소마다 따로 판단) → 깊이 층(0.1 단위) → 덩어리마다 다각형 깎기 · 개수 세기 · 10-13
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"; A = "G:/art2real/out/설명/구멍/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:8]; Yg = d["Y"][te]; Dg = d["D"][te].astype(np.float32); del d
p = np.load(O + "학습/시험예측.npz"); P, Dp = p["P"][:8], p["D"][:8].astype(np.float32)
col = np.array([[245, 245, 245], [205, 215, 230], [230, 80, 80], [80, 140, 235]], np.uint8)
def 층그림(Y, D):
    층 = np.clip(np.round(np.where(Y == 3, D, 0) / .1), 0, 10).astype(int); v = np.full(Y.shape + (3,), 245, np.uint8); v[Y > 0] = (205, 215, 230)
    pal = [(255, 255, 255)] + [tuple(int(c) for c in np.array(cv2.applyColorMap(np.uint8([[k * 25]]), cv2.COLORMAP_TURBO)[0, 0][::-1])) for k in range(1, 11)]
    for k in range(1, 11): v[(Y == 3) & (층 == k)] = pal[k]
    v[Y == 2] = (30, 30, 30); return v, 층
def 세기(Y, 층):
    n = 0
    for k in range(1, 11): n += len(J.다각((Y == 3) & (층 == k)))
    return n + len(J.다각(Y == 2))
W, H = 1800, 1250; c = Image.new("RGB", (W, H), (10, 15, 30)); dr = ImageDraw.Draw(c); s = 300
dr.text((W // 2, 50), "왜 끄트러기가 생기나 — 화소마다 따로 정하고, 덩어리마다 따로 깎는다", font=F(44), fill=(236, 242, 250), anchor="mm")
for j, t in enumerate(("정답 지도", "모델 지도(화소마다)", "모델 깊이 층(0.1 단위)", "깎은 결과")): dr.text((190 + j * 380, 120), t, font=F(28), fill=(64, 196, 255), anchor="mm")
for r, k in enumerate((0, 7)):
    y = 160 + r * 420
    c.paste(Image.fromarray(col[Yg[k]]).resize((s, s), Image.NEAREST), (40, y)); c.paste(Image.fromarray(col[P[k]]).resize((s, s), Image.NEAREST), (420, y))
    v, 층 = 층그림(P[k], Dp[k]); c.paste(Image.fromarray(v).resize((s, s), Image.NEAREST), (800, y)); vg, 층g = 층그림(Yg[k], Dg[k])
    c.paste(Image.open(A + "빛_r2a_모델_%d.png" % k).convert("RGB").crop((130, 110, 770, 750)).resize((s, s)), (1180, y))
    dr.text((40, y + s + 15), "정답: 깎을 덩어리 %d 개" % 세기(Yg[k], 층g), font=F(26), fill=(110, 220, 140)); dr.text((800, y + s + 15), "모델: 깎을 덩어리 %d 개" % 세기(P[k], 층), font=F(26), fill=(255, 100, 100))
dr.multiline_text((40, 1010), "① 화소마다 따로 판단 → 경계가 지글지글 · 작은 섬이 생김(모델 지도의 점들)\n② 깊이를 0.1 층으로 나눔 → 비탈 · 둥근 바닥이 층마다 고리 · 띠로 쪼개짐(깊이 층 무지개)\n③ 층 · 섬마다 다각형 하나씩 따로 깎음 → 수십 개의 작은 홈 = 끄트러기", font=F(30), fill=(236, 242, 250), spacing=14)
c.save(O + "끄트러기.png"); print("ok")
