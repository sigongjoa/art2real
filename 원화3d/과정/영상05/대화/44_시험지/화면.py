# 44 편 위쪽 화면 판 — 판(키, 진행 0~1) → RGBA (≤ 1000 × 760) · 재료 out/영상05/대화/44_시험지/자료 (트레일 기능0/자료44.py)
# 화면 부품은 변형 허용 라이선스만: 검증 32(ND · 표준 8 개 뺌) · 개발은 42 편 격자 18 · 캐릭터는 자체 디자인
import json, random, math
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/44_시험지/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
노, 파, 주, 초, 빨, 먹 = (190, 150, 30), (60, 120, 220), (220, 110, 40), (60, 160, 80), (220, 50, 50), (40, 40, 50)
목 = json.load(open(A + "목록.json"))
def _카드(w, h, 테=(255, 255, 255)):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _붙(c, p, xy, s):
    im = Image.open(A + p).convert("RGBA").resize((s, s)); c.alpha_composite(im, xy)
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def 판(키, p):
    t = int(p * 11.99) % 12
    if 키 == "모델째":   # 402 칸 중 20 칸이 아래 빨간 상자로 빠져나감
        c = _카드(1000, 700, 파); d = ImageDraw.Draw(c); d.text((500, 45), "배우던 로봇 모델 402개", font=F(44), fill=파, anchor="mm")
        rng = random.Random(3); 뺌 = sorted(rng.sample(range(402), 20)); e = _쉬움(p * 1.6)
        d.rounded_rectangle((60, 545, 940, 680), 24, outline=빨 + (255,) if e > .05 else (0, 0, 0, 0), width=6)
        for j in range(402):
            x, y = 42 + (j % 30) * 31, 90 + (j // 30) * 32
            if j in 뺌:
                q = 뺌.index(j); tx, ty = 95 + (q % 10) * 82, 562 + (q // 10) * 44; x, y = int(x + (tx - x) * e), int(y + (ty - y) * e); d.rounded_rectangle((x, y, x + 60 if e > .5 else x + 25, y + 30 if e > .5 else y + 24), 6, fill=빨)
            else: d.rounded_rectangle((x, y, x + 25, y + 24), 5, fill=(200, 205, 215))
        if e > .9: d.text((500, 520), "↓ 학습에서 통째로 뺌", font=F(32), fill=빨, anchor="mm")
        return c
    if 키 == "같은로봇":   # 같은 로봇의 두 부품(Duck Mecha 어깨 · 팔뚝 · CC BY)
        c = _카드(1000, 640, 주); d = ImageDraw.Draw(c); d.text((500, 50), "같은 로봇의 다른 부품", font=F(44), fill=주, anchor="mm")
        _붙(c, "검_04.png", (60, 110), 400); _붙(c, "검_05.png", (540, 110), 400); d.text((500, 330), "=", font=F(90), fill=주, anchor="mm")
        d.text((500, 580), "같은 디자이너 · 같은 버릇", font=F(36), fill=먹, anchor="mm"); return c
    if 키 == "검증격자":
        c = _카드(1000, 760, 초); d = ImageDraw.Draw(c); d.text((500, 42), "처음 보는 부품 (화면 허용 32개)", font=F(38), fill=초, anchor="mm"); n = min(32, 2 + int(p * 1.5 * 32))
        for q, i in enumerate(목["검"][:n]): _붙(c, "검_%02d.png" % i, (28 + (q % 8) * 118, 80 + (q // 8) * 165), 120)
        return c
    if 키 == "회전체":
        c = Image.new("RGBA", (1000, 640), (0, 0, 0, 0))
        for j, (nm, tt) in enumerate((("터빈", "제트 엔진 터빈"), ("바퀴", "바퀴"))):
            k = _카드(470, 560, 빨); _붙(k, "%s_%02d.png" % (nm, t), (25, 20), 420); ImageDraw.Draw(k).text((235, 505), tt, font=F(40), fill=빨, anchor="mm"); c.alpha_composite(k, (j * 530, 40))
        return c
    if 키 == "라벨":
        c = _카드(1000, 700, 파); d = ImageDraw.Draw(c); d.text((500, 45), "부품마다 이름표", font=F(44), fill=파, anchor="mm")
        for j, (p_, tag, col) in enumerate((("개_13.png", "공 관절", 주), ("개_04.png", "휜 껍질", 초), ("검_30.png", "회전체", 빨), ("개_32.png", "각진 판", 파))):
            x = 30 + (j % 2) * 480; y = 100 + (j // 2) * 300; _붙(c, p_, (x, y), 250)
            if p * 4 > j: d.rounded_rectangle((x + 250, y + 100, x + 460, y + 160), 18, fill=col); d.text((x + 355, y + 130), tag, font=F(36), fill="white", anchor="mm")
        return c
    if 키 == "가림":   # 번호만 붙은 쌍 — 무엇으로 만든 건지 안 보임
        c = _카드(1000, 700, 먹); d = ImageDraw.Draw(c)
        for j, (i, src) in enumerate(((21, "쌍우"), (33, "쌍교"))):
            y = 40 + j * 330; d.text((60, y + 10), "쌍 %03d" % (17 + j * 88), font=F(36), fill=먹); _붙(c, "쌍사_%02d.png" % i, (230, y), 280); _붙(c, "%s_%02d.png" % (src, i), (560, y), 280)
            d.text((370, y + 300), "사람", font=F(28), fill=먹, anchor="mm"); d.text((700, y + 300), "후보 = ?", font=F(28), fill=먹, anchor="mm")
        return c
    if 키 == "대조":
        c = _카드(1000, 700, 먹); d = ImageDraw.Draw(c)
        for j, (a, b, 말, col) in enumerate((("쌍사_13.png", "쌍사_13.png", "똑같은 쌍 → 통과여야", 초), ("쌍사_21.png", "쌍우_33.png", "엉뚱한 쌍 → 실패여야", 빨))):
            y = 30 + j * 335; _붙(c, a, (80, y), 270); _붙(c, b, (400, y), 270)
            if p * 2 > j * .9: d.rounded_rectangle((690, y + 100, 980, y + 180), 20, outline=col, width=8); d.text((835, y + 140), 말.split(" → ")[1], font=F(40), fill=col, anchor="mm")
            d.text((335, y + 285), 말.split(" → ")[0], font=F(28), fill=먹, anchor="mm")
        return c
    if 키 == "교차":
        c = _카드(1000, 640, 주); d = ImageDraw.Draw(c); d.text((500, 45), "같이 채점하는 대조군", font=F(40), fill=주, anchor="mm")
        for j, (src, tt, col) in enumerate((("쌍사_21.png", "사람", 노), ("쌍교_21.png", "그림자 3개 겹침", 파), ("쌍우_21.png", "우리", 초))):
            _붙(c, src, (25 + j * 325, 120), 300); d.text((175 + j * 325, 470), tt, font=F(32), fill=col, anchor="mm")
        return c
    if 키 == "다음":
        c = _카드(1000, 640, 초); d = ImageDraw.Draw(c); b = 0.5 + 0.5 * math.sin(p * 12)
        d.text((500, 250), "학습 중…", font=F(110), fill=초, anchor="mm"); d.rounded_rectangle((150, 400, 850, 460), 30, outline=초, width=6); d.rounded_rectangle((158, 408, 158 + int(684 * min(p * 1.2, 1)), 452), 24, fill=초)
        return c
    if 키 == "자랑":   # 우리 결과 하나 크게 — 살짝 커지며 등장
        c = _카드(1000, 700, 초); k = int(520 + 60 * _쉬움(p * 3)); _붙(c, "쌍우_21.png", ((1000 - k) // 2, (700 - k) // 2 + 20), k)
        ImageDraw.Draw(c).text((500, 50), "우리가 지은 부품", font=F(44), fill=초, anchor="mm"); return c
    if 키 in ("비교", "비교같다"):
        c = Image.new("RGBA", (1000, 700), (0, 0, 0, 0))
        for j, (src, tt, col) in enumerate((("쌍교_21.png", "그림자 3개 겹침", 파), ("쌍우_21.png", "일주일 걸려 지음", 초))):
            k = _카드(470, 600, col); _붙(k, src, (25, 30), 420); ImageDraw.Draw(k).text((235, 540), tt, font=F(38), fill=col, anchor="mm"); c.alpha_composite(k, (j * 530, 40))
        if 키 == "비교같다":
            d = ImageDraw.Draw(c); s_ = 1 + 0.3 * max(0, 1 - p * 5); d.text((500, 330), "=", font=F(int(200 * s_)), fill=(255, 220, 60), stroke_width=12, stroke_fill=(10, 10, 20), anchor="mm")
        return c
    raise KeyError(키)
