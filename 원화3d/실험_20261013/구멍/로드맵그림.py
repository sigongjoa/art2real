# 로드맵 한 장 그림 — 위: 원칙(입구 하나 흐름) · 가운데: 계단 6 개(예시 형태 · 기준 · 상태) · 아래: 위험 · 10-13
from PIL import Image, ImageDraw, ImageFont, ImageFilter
A = "G:/art2real/out/설명/구멍/"; J = "G:/art2real/out/영상05/대화/49_진짜그림/자료/"; O = "G:/art2real/out/설명/로드맵_그림CAD.png"
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); 코 = lambda n: ImageFont.truetype("C:/Windows/Fonts/consola.ttf", n)
W, H = 1800, 2500; 바, 카, 테, 하, 흰, 회, 빨, 초, 금 = (10, 15, 30), (18, 26, 46), (44, 58, 90), (64, 196, 255), (236, 242, 250), (120, 134, 160), (255, 100, 100), (110, 220, 140), (255, 205, 70)
c = Image.new("RGBA", (W, H), 바 + (255,)); d = ImageDraw.Draw(c)
def 카드(xy, col=테, r=28, fill=카): d.rounded_rectangle(xy, r, fill=fill + (255,), outline=col, width=3)
def 빛테(xy, col, r=28):
    g = Image.new("RGBA", c.size); ImageDraw.Draw(g).rounded_rectangle(xy, r, outline=col + (255,), width=10); c.alpha_composite(g.filter(ImageFilter.GaussianBlur(14))); d.rounded_rectangle(xy, r, outline=col, width=4)
def 붙(p, xy, s, 둥글=True):
    im = Image.open(p).convert("RGBA"); k = s / max(im.size); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    if 둥글: m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((6, 6, im.width - 6, im.height - 6), 18, fill=255); im.putalpha(m.filter(ImageFilter.GaussianBlur(4)))
    c.alpha_composite(im, (int(xy[0] + (s - im.width) / 2), int(xy[1] + (s - im.height) / 2)))
def 화살(x0, y, x1, col=회): d.line((x0, y, x1 - 14, y), fill=col, width=6); d.polygon([(x1, y), (x1 - 22, y - 13), (x1 - 22, y + 13)], fill=col)

d.text((W // 2, 70), "로드맵 — 그림 → CadQuery 신경망", font=F(70), fill=흰, anchor="mm"); d.text((W // 2, 140), "초안 · 10-13 · 사용자 확인 전", font=F(32), fill=회, anchor="mm")
# ── 원칙: 입구 하나 ──
카드((40, 190, W - 40, 830)); d.text((80, 215), "원칙 — 입구는 하나, 모델만 바꿔 끼운다", font=F(44), fill=하)
y0 = 300; 붙(J + "머리_앞그림.png", (90, y0), 220); d.text((200, y0 + 240), "진짜 그림", font=F(30), fill=흰, anchor="mm")
화살(330, y0 + 110, 420, 하)
d.rounded_rectangle((430, y0 + 20, 720, y0 + 200), 26, fill=(20, 40, 70, 255)); 빛테((430, y0 + 20, 720, y0 + 200), 하); d.text((575, y0 + 80), "학습 모델", font=F(44), fill=흰, anchor="mm"); d.text((575, y0 + 140), "계단마다 교체", font=F(28), fill=하, anchor="mm")
화살(730, y0 + 110, 820, 하)
d.rounded_rectangle((830, y0 + 30, 1250, y0 + 190), 18, fill=(24, 26, 34, 255)); d.text((850, y0 + 60), "cq.Workplane()", font=코(30), fill=(200, 210, 230)); d.text((850, y0 + 100), "  .box(...)", font=코(30), fill=(200, 210, 230)); d.text((850, y0 + 140), "  .hole(...)", font=코(30), fill=(200, 210, 230))
d.text((1040, y0 + 240), "CadQuery 코드", font=F(30), fill=흰, anchor="mm")
화살(1260, y0 + 110, 1350, 하); 붙(A + "빛_r로드1.png", (1360, y0 - 10), 260); d.text((1490, y0 + 240), "CAD", font=F(30), fill=흰, anchor="mm")
# 대조군 가지
d.line((200, y0 + 270, 200, y0 + 330), fill=회, width=4); d.line((200, y0 + 330, 300, y0 + 330), fill=회, width=4)
d.rounded_rectangle((310, y0 + 300, 760, y0 + 360), 18, outline=회, width=3); d.text((535, y0 + 330), "겹치기 = 옆에 놓는 대조군", font=F(30), fill=회, anchor="mm")
d.text((800, y0 + 330), "→ 같은 그림 결과를 나란히 비교만 · 모델이 지면 「졌다」 보고", font=F(28), fill=회, anchor="lm")
for k, (t, col) in enumerate((("판마다 진짜 그림에 돌려 결과를 그대로", 초), ("계단 바꾸기 · 건너뛰기는 사용자가", 금), ("보고 첫 줄 = 「로드맵 N 단계」", 하))):
    x = 80 + k * 555; d.rounded_rectangle((x, 730, x + 530, 800), 35, fill=(14, 22, 40, 255), outline=col, width=3); d.text((x + 265, 765), t, font=F(28), fill=col, anchor="mm")
# ── 계단 ──
d.text((80, 870), "계단", font=F(48), fill=흰)
계 = [("0", "구멍 하나", "위 그림 1 장 → 반지름 · 위치", "시험 IoU ≥ 0.95", A + "빛_r5.png", True),
      ("1", "어휘 늘리기", "상자 크기 + 구멍 0~3 + 돌기", "합성 IoU ≥ 0.95 · 개수 80 %", A + "빛_r로드1.png", False),
      ("2", "앞 · 옆 두 장", "두 장 → 3D 숫자", "합성 부피 IoU ≥ 0.90", None, False),
      ("3", "합성 문법", "복잡한 합성 · 한 줄씩 짓기", "합성 ≥ 0.90", A + "빛_r로드3.png", False),
      ("4", "실물 점수 학습", "사람이 나눈 부품 렌더로", "처음 보는 실물 · 겹치기 + 0.05", "실물", False),
      ("5", "분할 · 병합", "진짜 그림을 덩어리로 나눠 짓기", "사용자 눈", "분할", False)]
cw, ch = 520, 470
for k, (n, t, s, g, im, 됨) in enumerate(계):
    col, row = k % 3, k // 3; x = 60 + col * 575; y = 960 + row * 560 + (2 - col) * 0
    d.rounded_rectangle((x, y, x + cw, y + ch), 30, fill=카 + (255,), outline=테, width=3)
    if 됨: 빛테((x, y, x + cw, y + ch), 초, 30)
    d.ellipse((x + 24, y + 22, x + 94, y + 92), fill=초 if 됨 else 테); d.text((x + 59, y + 57), n, font=F(42), fill=바 if 됨 else 흰, anchor="mm")
    d.text((x + 115, y + 35), t, font=F(42), fill=흰); d.text((x + 115, y + 90), s, font=F(26), fill=회)
    if im == "실물":
        sh = Image.open("G:/art2real/트레일/trail10_cadrille/runs/깊이학습/검증5_한눈.jpg").crop((6 * 256, 2 * 280 + 24, 7 * 256, 3 * 280)).convert("RGBA"); sh.save(A + "_실물예.png"); 붙(A + "_실물예.png", (x + 140, y + 130), 240)
    elif im == "분할":
        붙(J + "머리_앞그림.png", (x + 140, y + 130), 240)
        for bx in ((x + 235, y + 135, x + 285, y + 205), (x + 175, y + 205, x + 225, y + 290), (x + 300, y + 205, x + 350, y + 290), (x + 210, y + 215, x + 320, y + 345)): d.rounded_rectangle(bx, 8, outline=금, width=4)
    elif im is None:
        붙(J + "머리_앞그림.png", (x + 40, y + 150), 190); 붙(J + "머리_옆그림.png", (x + 220, y + 150), 190); d.text((x + 450, y + 245), "?", font=F(90), fill=회, anchor="mm")
    else: 붙(im, (x + 130, y + 120), 260)
    d.rounded_rectangle((x + 24, y + ch - 92, x + cw - 24, y + ch - 24), 20, fill=(12, 20, 36, 255)); d.text((x + 44, y + ch - 58), "기준 " + g, font=F(26), fill=흰, anchor="lm")
    d.text((x + cw - 40, y + 50), "통과 0.968" if 됨 else "대기", font=F(32), fill=초 if 됨 else 회, anchor="rm")
    if col < 2: 화살(x + cw + 6, y + ch // 2, x + 570, 회)
d.line((60 + 2 * 575 + cw // 2, 960 + ch + 5, 60 + 2 * 575 + cw // 2, 960 + ch + 40), fill=회, width=5); d.line((60 + cw // 2, 960 + ch + 40, 60 + 2 * 575 + cw // 2, 960 + ch + 40), fill=회, width=5); d.line((60 + cw // 2, 960 + ch + 40, 60 + cw // 2, 960 + 560 - 14), fill=회, width=5)
d.polygon([(60 + cw // 2, 960 + 560), (60 + cw // 2 - 13, 960 + 560 - 22), (60 + cw // 2 + 13, 960 + 560 - 22)], fill=회)
# ── 위험 ──
y = 2090; 카드((40, y, W - 40, y + 360), 빨); d.text((80, y + 25), "미리 적는 위험", font=F(44), fill=빨)
for k, t in enumerate(("실물 데이터가 적어 외우기만 할 수 있다 (10-08 정답 코드 36 개 → 외움)", "얼굴 · 곡면 갑주처럼 어휘 밖 모양은 끝까지 안 될 수 있다 → 방향은 사용자가", "점수 빈틈(상자 하나로 때우기 · 부스러기) → 판마다 형태를 눈으로")):
    d.text((90, y + 110 + k * 75), "•  " + t, font=F(32), fill=흰)
c.convert("RGB").save(O); print("ok")
