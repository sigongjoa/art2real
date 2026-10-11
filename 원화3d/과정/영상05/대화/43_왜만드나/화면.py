# 43 편 위쪽 화면 판 (42 편 재료 재사용 + 시험지 · 처음) — 판(키, 진행 0~1) → RGBA (≤ 1000 × 760) · 재료는 out/영상05/대화/42_각진덩어리/자료 (트레일 기능0/자료42.py)
# 화면 부품은 변형 허용 라이선스만: #4 · #5 만달로리안/RX78(BY-NC-SA) · #13 EVA00(BY-NC-SA) · #21 Robot Head(BY-NC-SA) · #33 메가트론(BY) · 격자 18
import json
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/42_각진덩어리/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
def _카드(w, h, 테=(255, 255, 255)):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _넣(c, im, box):   # 흰 여백을 잘라 내고 칸에 꽉 차게
    import numpy as np
    a = np.asarray(im.convert("RGB")); ys, xs = np.nonzero((a < 240).any(-1))
    if len(xs): im = im.crop((max(xs.min() - 12, 0), max(ys.min() - 12, 0), xs.max() + 12, ys.max() + 12))
    im = im.convert("RGBA"); s = min(box[2] / im.width, box[3] / im.height); im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS); c.alpha_composite(im, (box[0] + (box[2] - im.width) // 2, box[1] + (box[3] - im.height) // 2))
def _둘(a, b, ta, tb, ca, cb, t, 화살=True):   # 돌림판 둘 나란히 (같은 각)
    c = Image.new("RGBA", (1000, 640), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    for j, (n, tt, col) in enumerate(((a, ta, ca), (b, tb, cb))):
        k = _카드(470, 560, col); _넣(k, Image.open(A + "%s_%02d.png" % (n, t)), (20, 20, 430, 450)); ImageDraw.Draw(k).text((235, 515), tt, font=F(42), fill=col, anchor="mm"); c.alpha_composite(k, (j * 530, 40))
    if 화살: d.text((500, 330), "→", font=F(80), fill="white", stroke_width=6, stroke_fill=(10, 10, 20), anchor="mm")
    return c
노, 파, 주, 초, 빨 = (190, 150, 30), (60, 120, 220), (220, 110, 40), (60, 160, 80), (220, 50, 50)
def 판(키, p):
    t = int(p * 11.99) % 12
    if 키 == "각짐": c = _카드(1000, 700, 파); ImageDraw.Draw(c).text((500, 55), "세 방향 그림자를 겹친 덩어리", font=F(46), fill=파, anchor="mm"); _넣(c, Image.open(A + "21교차_%02d.png" % t), (60, 100, 880, 580)); return c
    if 키 == "교차": return _둘("21사람", "21교차", "사람이 만든 것", "그림자 겹치기", 노, 파, t, False)
    if 키 == "계단": return _둘("21사람", "21계단", "사람이 만든 것", "점수 0.94", 노, 빨, t, False)
    if 키 == "기능": return _둘("21교차", "21기능", "겹치기", "껍질 + 창", 파, 주, t)
    if 키 == "공": return _둘("5교차", "5기능", "겹치기", "공 + 원기둥", 파, 주, t)
    if 키 == "민짜": return _둘("33사람", "33전", "사람이 만든 것", "홈 없음", 노, 주, t, False)
    if 키 == "디테일": return _둘("33전", "33후", "닫힌 선 전", "닫힌 선 판 뒤", 주, 주, t)
    if 키 == "격자":
        ok = json.load(open(A + "격자.json")); c = _카드(1000, 760); d = ImageDraw.Draw(c); d.text((500, 42), "노랑 = 사람 · 주황 = 우리", font=F(40), fill=(40, 40, 50), anchor="mm")
        n = min(len(ok), 2 + int(p * 1.4 * len(ok)))
        for q, i in enumerate(ok[:n]):
            x, y = 15 + (q % 4) * 245, 80 + (q // 4) * 136
            for j, nm in enumerate(("격사", "격후")): c.alpha_composite(Image.open(A + "%s_%02d.png" % (nm, i)).convert("RGBA").resize((118, 118)), (x + j * 112, y))
        return c
    if 키 == "선깊이":
        c = Image.new("RGBA", (1000, 600), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
        for j, (n, tt) in enumerate((("선_2.png", "선 그림만"), ("깊이_2.png", "AI가 맞힌 깊이"))):
            k = _카드(450, 520, (255, 255, 255) if j == 0 else 초); _넣(k, Image.open(A + n), (20, 20, 410, 410)); ImageDraw.Draw(k).text((225, 475), tt, font=F(40), fill=(40, 40, 50) if j == 0 else 초, anchor="mm"); c.alpha_composite(k, (j * 550, 40))
        d.text((500, 300), "→", font=F(80), fill="white", stroke_width=6, stroke_fill=(10, 10, 20), anchor="mm"); return c
    if 키 == "옛새": return _둘("17옛", "17새", "예전 AI 깊이", "다시 배운 AI", 파, 초, t)
    if 키 == "공없음": return _둘("13사람", "13새", "사람이 만든 것", "공이 없다", 노, 빨, t, False)
    if 키 == "통짜":   # 생성 AI 결과물 그림은 안 씀(생성 3D 금지) — 글 카드 둘
        c = Image.new("RGBA", (1000, 640), (0, 0, 0, 0)); n = min(3, int(p * 8))
        for j, (머리, 줄, col) in enumerate((("생성 AI", ["메시 한 덩어리", "구멍 옮기기 어려움", "다시 뽑기"], 빨), ("우리", ["1 겹치기", "2 껍질", "3 창 뚫기"], 초))):
            k = _카드(470, 560, col); d = ImageDraw.Draw(k); d.text((235, 70), 머리, font=F(64), fill=col, anchor="mm")
            for q, t in enumerate(줄[:n if j else 3]): d.text((235, 210 + q * 110), t, font=F(50), fill=(40, 40, 50), anchor="mm")
            c.alpha_composite(k, (j * 530, 40))
        return c
    if 키 in ("시험지", "처음"):   # 격자 위에 도장 · 처음 = 실루엣만 남기고 물음표
        import numpy as np
        c = 판("격자", 1.0)
        if 키 == "처음":
            a = np.asarray(c).copy(); 칸 = (a[..., :3] < 235).all(-1) & (a[..., 3] > 0) & (np.arange(a.shape[0])[:, None] > 70)
            a[칸, :3] = (70, 70, 85); c = Image.fromarray(a); d = ImageDraw.Draw(c); d.rectangle((0, 0, 999, 75), fill=(250, 250, 252, 255))
            d.text((500, 42), "한 번도 안 본 부품", font=F(40), fill=(40, 40, 50), anchor="mm")
            d.text((500, 420), "?", font=F(int(300 + 40 * np.sin(p * 6.28))), fill=(255, 220, 60), stroke_width=10, stroke_fill=(10, 10, 20), anchor="mm")
        else:
            d = ImageDraw.Draw(c); s_ = 1 + 0.15 * max(0, 1 - p * 4)
            d.rounded_rectangle((180, 300, 820, 520), 30, fill=(255, 255, 255, 235), outline=(220, 50, 50, 255), width=int(14 * s_)); d.text((500, 410), "다 본 부품", font=F(int(110 * s_)), fill=(220, 50, 50), anchor="mm")
        return c
    raise KeyError(키)
