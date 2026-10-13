# 로드맵 1 단계 다시(1b) 흐름도 — 정답 코드로 먼저 따라 배우고, 점수 학습으로 잇기 · 10-13
from PIL import Image, ImageDraw, ImageFont, ImageFilter
A = "G:/art2real/out/설명/구멍/"; O = A + "흐름_1b.png"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
W, H = 1800, 1900; 바, 카, 테, 하, 흰, 회, 빨, 초, 금 = (10, 15, 30), (18, 26, 46), (44, 58, 90), (64, 196, 255), (236, 242, 250), (120, 134, 160), (255, 100, 100), (110, 220, 140), (255, 205, 70)
c = Image.new("RGBA", (W, H), 바 + (255,)); d = ImageDraw.Draw(c)
def 붙(p, xy, s, crop=True):
    im = Image.open(A + p).convert("RGBA")
    if crop: im = im.crop((180, 160, 720, 700))
    im = im.resize((s, s), Image.LANCZOS); m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((6, 6, s - 6, s - 6), 20, fill=255); im.putalpha(m.filter(ImageFilter.GaussianBlur(5))); c.alpha_composite(im, xy)
def 화살(x0, y, x1, col=회): d.line((x0, y, x1 - 14, y), fill=col, width=6); d.polygon([(x1, y), (x1 - 22, y - 13), (x1 - 22, y + 13)], fill=col)
d.text((W // 2, 60), "로드맵 1 단계 다시(1b) — 정답 코드로 먼저 따라 배우기", font=F(56), fill=흰, anchor="mm"); d.text((W // 2, 120), "흐름도 · 10-13 · 승인 전", font=F(30), fill=회, anchor="mm")
# 1단계 실패 요약
d.rounded_rectangle((40, 170, W - 40, 620), 30, fill=카 + (255,), outline=빨, width=3); d.text((80, 195), "1 단계(52 편)에서 본 것", font=F(40), fill=빨)
for k, j in enumerate((0, 3, 4)):
    x = 80 + k * 300; 붙("빛_r52_s1500_%d.png" % j, (x, 270), 220); 붙("../구멍/학습2/그림_%d.png" % j if False else "학습2/그림_%d.png" % j, (x + 150, 260), 90, False)
d.multiline_text((1000, 280), "바깥 크기만 배움\n원기둥은 한 번도 안 고름\n구멍 · 홈은 그림과 무관\n\n짐작: 처음부터 점수로만 배우니\n「무엇을 고를지」를 우연히 찾아야 함", font=F(32), fill=흰, spacing=14)
# 바꾸는 것 하나
d.rounded_rectangle((40, 660, W - 40, 1270), 30, fill=카 + (255,), outline=초, width=3); d.text((80, 685), "바꾸는 것 하나 — 학습을 두 마디로", font=F(40), fill=초)
d.rounded_rectangle((80, 770, 820, 1220), 24, fill=(14, 22, 40, 255), outline=하, width=3); d.text((110, 790), "① 따라 배우기 (지도 학습)", font=F(36), fill=하)
d.multiline_text((110, 860), "합성 부품은 정답 코드를 안다\n그림 → 「바탕 원기둥 · 구멍 · 세로 홈」\n종류와 숫자를 정답에 맞춰 바로 배움\n(실제 CAD 안 지음 · 빠름)", font=F(30), fill=흰, spacing=12)
화살(830, 995, 960, 하)
d.rounded_rectangle((970, 770, 1720, 1220), 24, fill=(14, 22, 40, 255), outline=금, width=3); d.text((1000, 790), "② 점수로 이어 배우기 (1 단계와 같음)", font=F(36), fill=금)
d.multiline_text((1000, 860), "후보 8 벌을 CadQuery 로 실제로 짓고\n그림과 겹쳐 본 점수로 다듬기\n\n← 실물 부품(정답 코드 없음)으로\n가는 길도 이 두 마디(로드맵 3 · 4)", font=F(30), fill=흰, spacing=12)
# 그대로 두는 것 · 판정
d.rounded_rectangle((40, 1310, W - 40, 1860), 30, fill=카 + (255,), outline=테, width=3); d.text((80, 1335), "그대로 두는 것 · 판정(미리 적음)", font=F(40), fill=하)
for k, (t, col) in enumerate((("같은 합성 3,000 / 시험 200 · 같은 6 칸 · 같은 신경망 · 같은 칸 3 개 — 학습 순서만 바뀜", 흰),
                              ("① 따라 배우기 30 에폭 → ② 점수 학습 1,000 걸음", 흰),
                              ("판정: 시험 200 IoU ≥ 0.95 · 개수 맞힘 ≥ 80 % (1 단계 기준 그대로) · 대조 = 1 단계 결과(0.830 · 0.23)", 빨),
                              ("따로 적음: ①만 끝낸 판의 점수도 기록 — 점수 학습이 보태는 몫을 가르기 위해", 금),
                              ("판마다 진짜 그림(메카2 머리 · 발) 결과 그대로 · 실패해도 다시 안 돌림 · 쇼츠 53", 회))):
    d.text((80, 1420 + k * 80), t, font=F(30), fill=col)
c.convert("RGB").save(O); print("ok")
