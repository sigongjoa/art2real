# 로드맵 1 단계 흐름도 — 여러 부품에서도 되나 · 10-13
from PIL import Image, ImageDraw, ImageFont, ImageFilter
A = "G:/art2real/out/설명/구멍/"; O = A + "흐름_여러부품.png"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); 코 = lambda n: ImageFont.truetype("C:/Windows/Fonts/consola.ttf", n)
W, H = 1800, 2150; 바, 카, 테, 하, 흰, 회, 빨, 초, 금 = (10, 15, 30), (18, 26, 46), (44, 58, 90), (64, 196, 255), (236, 242, 250), (120, 134, 160), (255, 100, 100), (110, 220, 140), (255, 205, 70)
c = Image.new("RGBA", (W, H), 바 + (255,)); d = ImageDraw.Draw(c)
def 붙(p, xy, s):
    im = Image.open(A + p).convert("RGBA").resize((s, s), Image.LANCZOS); m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((6, 6, s - 6, s - 6), 20, fill=255); im.putalpha(m.filter(ImageFilter.GaussianBlur(5))); c.alpha_composite(im, xy)
d.text((W // 2, 65), "로드맵 1 단계 — 여러 부품에서도 되나", font=F(64), fill=흰, anchor="mm"); d.text((W // 2, 130), "흐름도 · 10-13 · 승인 전", font=F(30), fill=회, anchor="mm")
# 부품 종류
d.rounded_rectangle((40, 180, W - 40, 900), 30, fill=카 + (255,), outline=테, width=3); d.text((80, 205), "부품 종류 — 위에서 본 그림 한 장으로 되는 것만 이번 판", font=F(40), fill=하)
이번 = [("빛_r예_판구멍.png", "구멍 여러 개"), ("빛_r예_홈.png", "홈"), ("빛_r예_원기둥구멍.png", "원기둥 + 구멍"), ("빛_r5.png", "구멍 하나(0 단계)")]
다음 = [("빛_r예_돌기.png", "돌기"), ("빛_r예_기역.png", "ㄱ자"), ("빛_r예_계단.png", "계단")]
for k, (p, t) in enumerate(이번): x = 70 + k * 300; 붙(p, (x, 280), 270); d.text((x + 135, 575), t, font=F(30), fill=흰, anchor="mm")
d.rounded_rectangle((60, 270, 1260, 610), 26, outline=초, width=4); d.text((1240, 640), "이번 판(1 단계)", font=F(30), fill=초, anchor="rm")
for k, (p, t) in enumerate(다음): x = 1290 + (k % 2) * 230; y = 270 + (k // 2) * 200; 붙(p, (x if k < 2 else 1405, y), 160); d.text(((x if k < 2 else 1405) + 80, y + 165), t, font=F(24), fill=회, anchor="mm")
d.text((1290, 680), "높이가 필요 → 2 단계", font=F(26), fill=회)
d.text((80, 700), "합성: 상자 또는 원기둥 바탕 + 특징 0~3 개(구멍 · 홈) · 크기 · 위치 무작위 · 학습 3,000 · 시험 200(학습에 안 씀)", font=F(28), fill=흰)
d.text((80, 760), "지켜볼 부품 6 개(종류마다) → 쇼츠에서 6 칸이 동시에 맞춰지는 타임랩스", font=F(28), fill=금)
# 신경망이 내는 코드
d.rounded_rectangle((40, 940, W - 40, 1400), 30, fill=카 + (255,), outline=테, width=3); d.text((80, 965), "신경망이 내는 것 = CadQuery 한 줄씩(칸 4 개)", font=F(40), fill=하)
줄 = ["1  바탕   상자(가로, 세로) | 원기둥(반지름)", "2  특징   없음 | 구멍(x, y, 반지름) | 홈(x, y, 길이, 폭, 각도)", "3  특징   …", "4  특징   …"]
d.rounded_rectangle((80, 1040, 1100, 1360), 18, fill=(24, 26, 34, 255))
for k, t in enumerate(줄): d.text((110, 1065 + k * 72), t, font=F(30), fill=(200, 210, 230))
d.multiline_text((1150, 1050), "칸마다 「무엇」(고르기)\n+ 숫자(흔들어 뽑기)\n\n후보 8 벌 → 실제로 짓고\n위에서 본 모양과 그림 겹침\n→ 좋은 후보 쪽으로", font=F(32), fill=흰, spacing=12)
# 판정 · 대조 · 진짜 그림
d.rounded_rectangle((40, 1440, W - 40, 1830), 30, fill=카 + (255,), outline=빨, width=3); d.text((80, 1465), "판정(미리 적음)", font=F(40), fill=빨)
for k, (t, col) in enumerate((("시험 200 평균 IoU ≥ 0.95  ·  특징 개수 맞힘 ≥ 80 %", 흰), ("대조: ⓐ 학습 전 ⓑ 평균 맞히기(늘 같은 답) — 둘보다 +0.05", 흰), ("판마다 진짜 그림 묶음(메카2 머리 · 발)도 입구에 넣어 결과를 그대로 보여 줌 — 위 그림이 없어 형편없을 것", 금), ("실패해도 고쳐 다시 돌리지 않음 · 결과 그대로 쇼츠", 회))):
    d.text((80, 1545 + k * 68), t, font=F(30), fill=col)
d.rounded_rectangle((40, 1870, W - 40, 2110), 30, fill=카 + (255,), outline=테, width=3); d.text((80, 1895), "쇼츠", font=F(40), fill=하)
d.text((80, 1965), "51 편 「부품 하나」 다음 → 「여러 부품에서도 되나」 · 6 칸 타임랩스 + 시간축 템플릿 · 끝은 결과로(다음 약속 없음)", font=F(28), fill=흰)
d.text((80, 2030), "안 하는 것: 높이 · ㄱ자 · 계단(2 단계) · 겹치기 바탕 · 실물 부품", font=F(28), fill=회)
c.convert("RGB").save(O); print("ok")
