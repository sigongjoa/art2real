# 68 편(숨은선) 위쪽 화면 판 — 재료 out/영상05/대화/68_숨은선/자료/(Anatomy 숨은선 96 프레임 · 재료68.py 실제 부품 선 그림 · Remotion 모션 카드 관문 · 결과) · 숫자는 결과판정56_G0 · 결과판정56
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/68_숨은선/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 40, 50), (130, 130, 140), (220, 160, 30)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _그림(c, n, box, crop=None):
    im = Image.open(A + n + ".png").convert("RGBA"); im = im.crop(crop) if crop else im.crop(im.getbbox())
    x0, y0, x1, y1 = box; s = min((x1 - x0) / im.width, (y1 - y0) / im.height); im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS); c.alpha_composite(im, (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2))
def _프레임(c, 폴, i, box, crop=None): _그림(c, "%s/프레임_%03d" % (폴, i), box, crop)
자름 = (180, 40, 819, 658)   # Anatomy 숨은선 96 장의 공통 bbox — 프레임마다 getbbox 면 크기가 흔들린다
def _선판(c, n, box, 제, 색):
    _그림(c, n, box); ImageDraw.Draw(c).text(((box[0] + box[2]) // 2, box[1] - 22), 제, font=F(30), fill=색, anchor="mm")
def 판(키, p):
    q = min(max(p, 0), 1)
    if 키 == "그릇":
        c = _카드(빨); d = ImageDraw.Draw(c); _프레임(c, "숨은선", 33, (60, 120, 940, 620), 자름); d.text((500, 78), "속 빈 부품 · 모델은 얕게 팠다", font=F(42), fill=빨, anchor="mm"); d.text((500, 655), "정답 깊이로 지으면 0.9 · 모델은 0.58 · 112 개", font=F(30), fill=회, anchor="mm"); return c
    if 키 in ("숨은선A", "숨은선B", "숨은선C"):   # Anatomy 구간: 소개 0–11 · 깊이찍기 12–35 · 광선 36–59 · 다시깎기 60–83 · 정지 84–95
        a, b, 테, 제, 아래 = {"숨은선A": (0, 35, 먹, "앞 · 옆 그림에는 깊이가 없다", "높이가 바뀌는 자리만 있다"), "숨은선B": (36, 59, 금, "광선이 벽 뒤 바닥에 닿는 자리", "도면의 점선 = 숨은선"), "숨은선C": (60, 95, 초, "숨은선 높이까지 깎는다", "안쪽 바닥이 맞는다")}[키]
        c = _카드(테); d = ImageDraw.Draw(c); _프레임(c, "숨은선", min(b, a + int(q * (b - a + 1))), (60, 120, 940, 620), 자름); d.text((500, 78), 제, font=F(42), fill=테, anchor="mm"); d.text((500, 655), 아래, font=F(30), fill=회, anchor="mm"); return c
    if 키 == "실물":
        c = _카드(금); d = ImageDraw.Draw(c); _그림(c, "9806_렌더", (60, 140, 480, 600)); _그림(c, "5926_렌더", (520, 140, 940, 600))
        d.text((500, 78), "실제 부품에 적용", font=F(42), fill=먹, anchor="mm"); d.text((270, 650), "나사 이음 9806", font=F(32), fill=회, anchor="mm"); d.text((730, 650), "컵 5926", font=F(32), fill=회, anchor="mm"); return c
    if 키 == "덩어리":
        c = _카드(빨); d = ImageDraw.Draw(c); _그림(c, "9806_렌더", (40, 200, 300, 520)); _선판(c, "9806_꺾임_앞", (340, 160, 640, 580), "앞", 먹); _선판(c, "9806_꺾임_옆", (670, 160, 970, 580), "옆", 먹)
        d.text((500, 78), "꺾임까지 선으로 잡으니 안쪽이 덩어리", font=F(42), fill=빨, anchor="mm"); d.text((500, 650), "빨강 = 숨은선 · 검정 = 보이는 선", font=F(30), fill=회, anchor="mm"); return c
    if 키 == "끊김":
        c = _카드(초); d = ImageDraw.Draw(c); _선판(c, "9806_끊김_앞", (40, 160, 340, 580), "나사 이음 · 앞", 먹); _선판(c, "9806_끊김_옆", (350, 160, 650, 580), "나사 이음 · 옆", 먹); _선판(c, "5926_끊김_앞", (660, 160, 960, 580), "컵 · 앞", 먹)
        d.text((500, 78), "높이 끊김만 남기니 선이 된다", font=F(42), fill=초, anchor="mm"); d.text((500, 650), "컵 안쪽 바닥 · 벽이 빨간 선으로", font=F(30), fill=회, anchor="mm"); return c
    if 키 in ("관문", "결과", "결과끝"):   # Remotion 모션 카드(투명 PNG 150 장) — 처음 줄은 p 로 움직이고 다시 나오면 마지막 프레임
        폴, 테, 제 = ("관문모션", 초, "속 빈 112 개 · 숨은선이 쓸 만한가") if 키 == "관문" else ("결과모션", 금, "숨은선을 넣고 다시 학습")
        i = 149 if 키.endswith("끝") else min(149, int(q * 150)); c = _카드(테); d = ImageDraw.Draw(c); c.alpha_composite(Image.open(A + "%s/프레임_%03d.png" % (폴, i)).convert("RGBA")); d.text((500, 80), 제, font=F(42), fill=먹, anchor="mm"); return c
    raise KeyError(키)
