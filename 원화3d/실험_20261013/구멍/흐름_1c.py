# 로드맵 1 단계 다시(1c) 흐름도 — 바탕은 그림의 바깥 윤곽에서, 모델은 디테일만 깎는다(사용자 10-13) · 10-13
from PIL import Image, ImageDraw, ImageFont, ImageFilter
A = "G:/art2real/out/설명/구멍/"; O = A + "흐름_1c.png"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
W, H = 1800, 2000; 바, 카, 테, 하, 흰, 회, 빨, 초, 금 = (10, 15, 30), (18, 26, 46), (44, 58, 90), (64, 196, 255), (236, 242, 250), (120, 134, 160), (255, 100, 100), (110, 220, 140), (255, 205, 70)
c = Image.new("RGBA", (W, H), 바 + (255,)); d = ImageDraw.Draw(c)
def 붙(p, xy, s, crop=True):
    im = Image.open(A + p).convert("RGBA")
    if crop: im = im.crop((180, 160, 720, 700))
    im = im.resize((s, s), Image.LANCZOS); m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((6, 6, s - 6, s - 6), 20, fill=255); im.putalpha(m.filter(ImageFilter.GaussianBlur(5))); c.alpha_composite(im, xy)
def 화살(x0, y, x1, col=회): d.line((x0, y, x1 - 14, y), fill=col, width=6); d.polygon([(x1, y), (x1 - 22, y - 13), (x1 - 22, y + 13)], fill=col)
d.text((W // 2, 60), "로드맵 1 단계 다시(1c) — 바탕은 그림 윤곽에서, 모델은 디테일만", font=F(54), fill=흰, anchor="mm"); d.text((W // 2, 120), "흐름도 · 10-13 · 승인 전 · 사용자 「깎아 들어가는 건 맞다 · 앞의 형태 정보로 시작」", font=F(28), fill=회, anchor="mm")
# 흐름(예시 두 줄)
d.rounded_rectangle((40, 170, W - 40, 1000), 30, fill=카 + (255,), outline=초, width=3)
for r, k in enumerate((3, 5)):
    y = 230 + r * 380
    붙("학습2/그림_%d.png" % k, (80, y), 280, False); d.text((220, y + 300), "그림", font=F(28), fill=흰, anchor="mm")
    화살(375, y + 140, 470, 초); d.text((420, y + 95), "윤곽", font=F(24), fill=초, anchor="mm")
    붙("빛_r1c_바탕_%d.png" % k, (480, y - 10), 300); d.text((630, y + 300), "① 바탕 = 바깥 윤곽 밀기", font=F(26), fill=초, anchor="mm")
    화살(795, y + 140, 900, 하); d.text((850, y + 95), "모델", font=F(24), fill=하, anchor="mm")
    붙("빛_r1c_완성_%d.png" % k, (910, y - 10), 300); d.text((1060, y + 300), "② 디테일 깎기(구멍 · 홈)", font=F(26), fill=하, anchor="mm")
d.multiline_text((1260, 260), "① 학습 없음\n   그림의 바깥 윤곽을\n   CadQuery 로 밀어 바탕\n   → 상자 · 원기둥을\n      고를 필요가 없어짐\n\n② 학습 모델이 맡는 것\n   칸 3 개: 없음 · 구멍 ·\n   가로 홈 · 세로 홈 + 숫자\n   바탕에서 깎아 들어감", font=F(30), fill=흰, spacing=10)
# 점수 신호
d.rounded_rectangle((40, 1040, W - 40, 1380), 30, fill=카 + (255,), outline=하, width=3); d.text((80, 1065), "점수가 디테일만 보게 된다", font=F(40), fill=하)
d.multiline_text((80, 1135), "1 단계에선 바깥 크기만 맞춰도 0.8 이 나와 구멍 · 홈 신호가 묻혔다\n이번엔 바탕이 그림과 같으니 점수 차이는 전부 구멍 · 홈에서 난다\n학습 방식은 1 단계와 같음: 후보 8 벌 실제로 짓고 → 그림과 겹친 점수로", font=F(30), fill=흰, spacing=14)
# 판정 · 원칙 변경
d.rounded_rectangle((40, 1420, W - 40, 1960), 30, fill=카 + (255,), outline=빨, width=3); d.text((80, 1445), "판정(미리 적음) · 로드맵 원칙 고침", font=F(40), fill=빨)
for k, (t, col) in enumerate((("같은 합성 3,000 / 시험 200 · 같은 6 칸 · 1,000 걸음", 흰),
                              ("판정: 시험 200 IoU ≥ 0.95 · 구멍 · 홈 개수 맞힘 ≥ 80 % · 그리고 「윤곽 바탕만(디테일 없음)」보다 높을 것", 빨),
                              ("대조: 1 단계(0.830 · 23 %) · 윤곽 바탕만 · 진짜 그림(메카2 머리 · 발) 결과 그대로", 흰),
                              ("로드맵 원칙 1 고침: 「바탕 = 그림의 형태 정보(윤곽) · 학습 모델 = 디테일」(사용자 결정 10-13)", 금),
                              ("주의: 10-09~13 「교차 바탕 + 깊이로 홈 파기」와 비슷해 보이지만, 디테일을 깊이 지도가 아니라 CadQuery 칸으로 배운다", 회),
                              ("실패해도 다시 안 돌림 · 쇼츠 53 · 다음 약속 없음", 회))):
    d.text((80, 1530 + k * 70), t, font=F(28), fill=col)
c.convert("RGB").save(O); print("ok")
