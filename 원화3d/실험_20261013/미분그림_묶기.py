# 미분그림 렌더 → 한 장(한글 설명) · 10-13
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/설명/미분/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
W = 1800; im = Image.new("RGB", (W, 3600), (14, 15, 20)); d = ImageDraw.Draw(im); y = 30
노, 초, 빨, 흰, 회 = (255, 220, 90), (110, 220, 130), (255, 110, 100), (240, 240, 245), (160, 165, 175)
def 줄(t, c=흰, n=40, x=40): global y; d.text((x, y), t, font=F(n), fill=c); y += int(n * 1.45)
def 붙(p, x, w): g = Image.open(A + p).convert("RGB"); g = g.resize((w, int(g.height * w / g.width))); im.paste(g, (x, y)); return g.height
줄("CadQuery 는 왜 미분이 안 되나 — 그리고 어떻게 배우나", 노, 54)
줄("파란 테 = 신경망이 낸 CAD 상자(위에서 봄) · 칸 = 렌더 화소 (노랑 = 켜짐) · ③ 주황 막대 = 점수", 회, 30); y += 10
줄("① 실제 CAD — 상자 폭 3.0 → 3.4 로 늘려도 켜진 화소가 똑같다 → IoU 그대로 → 기울기 0", 빨, 36)
h = 붙("1_딱딱_30.png", 40, 840); 붙("1_딱딱_34.png", 920, 840); d.text((60, y + 10), "폭 3.0", font=F(40), fill=흰); d.text((940, y + 10), "폭 3.4  (똑같음)", font=F(40), fill=빨); y += h + 30
줄("② 부드러운 근사(SDF) — 같은 변화에 경계 화소가 조금 밝아진다 → 기울기가 생김 → 학습 가능", 초, 36)
h = 붙("2_부드_30.png", 40, 840); 붙("2_부드_34.png", 920, 840); d.text((60, y + 10), "폭 3.0", font=F(40), fill=흰); d.text((940, y + 10), "폭 3.4  (가장자리 밝아짐)", font=F(40), fill=초); y += h + 10
줄("   대신 근사 ≠ 실제 CAD → 모서리가 무너지던 문제(조각 디코더)", 회, 30); y += 20
줄("③ 보상 학습 — 미분 없이: 후보 코드를 실제로 짓고 렌더 → IoU 점수 → 높은 코드를 더 자주 내게", 노, 36)
h = 붙("3_보상.png", 40, 1720)
for k, (t, s) in enumerate((("상자", ".55"), ("원기둥", ".48"), ("구멍 블록", ".93 최고"), ("ㄱ자", ".41"))): d.text((250 + k * 405, y + h - 70), "%s  %s" % (t, s), font=F(36), fill=초 if "최고" in s else 흰)
y += h + 30
줄("④ 숫자 다듬기 — 구조(구멍 블록)는 정해 두고, 실제 CAD 렌더를 보며 반지름만 찔러 맞춤 (흰 테 = 목표)", 노, 36)
for k in range(4):
    g = Image.open(A + "4_다듬기_%d.png" % k).convert("RGB").resize((400, 400)); im.paste(g, (40 + k * 430, y)); d.text((240 + k * 430, y + 410), ("r 0.15", "0.30", "0.42", "0.50 맞음")[k], font=F(34), fill=초 if k == 3 else 흰, anchor="ma")
    if k < 3: d.polygon([(443 + k * 430, y + 185), (465 + k * 430, y + 200), (443 + k * 430, y + 215)], fill=회)
y += 480
im.crop((0, 0, W, y + 20)).save(A + "미분_한장.png"); print(y)
