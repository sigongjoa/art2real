# 69 편(골라 학습) 위쪽 화면 판 — 재료 out/영상05/대화/69_골라학습/자료/(Anatomy 난이도 선별기 150 프레임 · difficulty.mjs · Remotion 결과 카드 Ep69) · 숫자는 결과_난이도57 · 결과판정57_가
# Anatomy 구간: 소개 0–14 · 틀자 15–54 · 천장자 55–94 · 갈림 95–119 · 배합 120–130(못 배움 ✕ · 34:66 — 실제로 돌린 구성 가 · 131 뒤는 안 돌린 비율이라 안 씀)
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/69_골라학습/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 40, 50), (130, 130, 140), (220, 160, 30)
자름 = (157, 37, 843, 700)   # 0–130 프레임 공통 bbox
잘라 = {"틀자": (130, 15, 640, 420), "천장자": (130, 15, 640, 420), "갈림": (400, 280, 850, 690), "배합": (400, 280, 850, 690)}   # 10-16 기계가 카드에서 작아 계기 숫자가 안 읽힘 → 구간마다 그 부분만 크게(계측소 · 통)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _프레임(c, 폴, i, box, crop=None):
    im = Image.open(A + "%s/프레임_%03d.png" % (폴, i)).convert("RGBA"); im = im.crop(crop) if crop else im
    x0, y0, x1, y1 = box; s = min((x1 - x0) / im.width, (y1 - y0) / im.height); im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS); c.alpha_composite(im, (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2))
구간 = {"틀자": (15, 54, 금, "실루엣만 눌러 본 점수", "판 0.95 · 컵 0.60 · 속 빈 상자 0.30"), "천장자": (55, 94, 금, "정답 깊이로 깎은 최고점", "판 0.95 · 컵 0.92 · 속 빈 상자 0.43"),
       "갈림": (95, 119, 초, "세 통으로 가른다", "쉬움 2,347 · 배울 것 4,584 · 못 배움 1,890"), "배합": (120, 130, 빨, "못 배움을 잠그고 학습", "쉬움 : 배울 것 = 34 : 66 그대로")}
def 판(키, p):
    q = min(max(p, 0), 1)
    if 키 in 구간 or 키.rstrip("끝") in 구간:
        a, b, 테, 제, 아래 = 구간[키.rstrip("끝")]; i = b if 키.endswith("끝") else min(b, a + int(q * (b - a + 1)))
        c = _카드(테); d = ImageDraw.Draw(c); _프레임(c, "난이도", i, (40, 110, 960, 630), 잘라[키.rstrip("끝")]); d.text((500, 72), 제, font=F(42), fill=테, anchor="mm"); d.text((500, 662), 아래, font=F(28), fill=회, anchor="mm"); return c
    if 키 in ("결과", "결과끝"):
        i = 149 if 키 == "결과끝" else min(149, int(q * 150)); c = _카드(빨); d = ImageDraw.Draw(c); c.alpha_composite(Image.open(A + "결과모션/프레임_%03d.png" % i).convert("RGBA")); d.text((500, 78), "못 배움을 빼고 다시 학습", font=F(42), fill=먹, anchor="mm"); return c
    raise KeyError(키)
