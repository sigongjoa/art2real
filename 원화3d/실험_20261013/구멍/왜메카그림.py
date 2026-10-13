# 왜 메카는 안 되나 — 모델이 받은 입력을 나란히: 합성(학습한 것) vs 메카2(진짜) · 지도 · 10-13
import json, numpy as np
from PIL import Image, ImageDraw, ImageFont
import 캐드점수2 as K
A = "G:/art2real/out/설명/구멍/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
S = json.load(open(A + "학습4/스냅.json", encoding="utf-8")); W, H = 1800, 1500
바, 카, 테, 하, 흰, 회, 빨, 초, 금 = (10, 15, 30), (18, 26, 46), (44, 58, 90), (64, 196, 255), (236, 242, 250), (120, 134, 160), (255, 100, 100), (110, 220, 140), (255, 205, 70)
c = Image.new("RGB", (W, H), 바); d = ImageDraw.Draw(c); s = 330
def 입력(a): return Image.fromarray((255 - a * 225).astype(np.uint8)).resize((s, s), Image.NEAREST).convert("RGB")
def 지도(p):
    a = np.asarray(Image.open(p)) // 120; v = np.full(a.shape + (3,), 235, np.uint8); v[a == 1] = (230, 80, 80); v[a == 2] = (80, 140, 235); return Image.fromarray(v).resize((s, s), Image.NEAREST)
d.text((W // 2, 55), "왜 메카는 안 되나 — 모델이 실제로 받은 그림", font=F(54), fill=흰, anchor="mm")
for j, t in enumerate(("원래 그림", "모델이 받은 선 그림", "모델 지도(빨강 구멍 · 파랑 홈)")): d.text((265 + j * 400, 130), t, font=F(30), fill=하, anchor="mm")
# 줄 1: 합성
g = K.그림(S["정답"][5]); c.paste(입력(g), (100, 170)); c.paste(입력(g), (500, 170)); c.paste(지도(A + "학습4/지도_e20_5.png"), (900, 170))
d.text((1260, 230), "학습한 그림", font=F(34), fill=초); d.multiline_text((1260, 290), "선이 몇 개뿐\n안쪽 닫힌 칸 = 전부 구멍 · 홈\n→ 「안쪽 칸이면 깎는다」를 배움", font=F(28), fill=흰, spacing=10)
# 줄 2: 메카
o = Image.open("G:/art2real/out/영상05/대화/49_진짜그림/자료/머리_앞그림.png").convert("RGB").resize((s, s)); c.paste(o, (100, 560))
x = np.asarray(Image.open(A + "학습2/진짜입력_머리.png")) / 255.0; c.paste(입력(x), (500, 560)); c.paste(지도(A + "학습4/진짜지도_머리.png"), (900, 560))
d.text((1260, 620), "메카2 머리", font=F(34), fill=빨); d.multiline_text((1260, 680), "선이 빽빽 — 패널 선 · 색 경계 ·\n그림자 · 눈 · 볏이 다 선으로\n→ 안쪽 칸이 수십 개 → 다 깎음", font=F(28), fill=흰, spacing=10)
# 원인
d.rounded_rectangle((40, 950, W - 40, H - 40), 26, fill=카, outline=금, width=3); d.text((80, 975), "안 되는 이유 셋", font=F(38), fill=금)
for k, t in enumerate(("① 선의 뜻이 다르다 — 합성에선 안쪽 선 = 구멍 · 홈뿐. 메카에선 대부분 패널 선 · 색 경계 · 겹친 부품(깎는 선이 아님).\n     모델은 「깎지 않는 안쪽 선」을 본 적이 없다",
                       "② 그림이 다르다 — 합성은 깨끗한 CAD 선 그림.\n     메카는 색칠된 그림에서 윤곽을 뽑은 것이라 굵은 검정 · 그림자까지 선이 된다",
                       "③ 형태가 다르다 — 모델은 「평평한 판을 위에서 본 그림 + 구멍 · 홈」만 안다.\n     메카 머리는 둥근 입체인데 앞 그림을 위 그림 자리에 넣었다")):
    d.multiline_text((80, 1050 + k * 135), t, font=F(27), fill=흰, spacing=8)
c.save(A + "왜메카.png"); print("ok")
