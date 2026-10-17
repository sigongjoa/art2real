# 74 편 위쪽 화면 판 — 재료 out/영상05/대화/74_면맞춤/자료/ · 핀/ = Anatomy 면맞춤(face_fit.mjs · 180 장: 기운 판 0–59 · 관 60–119 · ㄱ자 120–179) · 판 · 막대 = 턴테이블(300 장 · 키 뒤 「2」 = 뒤 150) · 평균(150) · 숫자는 결과판정65 · 66
from PIL import Image, ImageDraw
A = "G:/art2real/out/영상05/대화/74_면맞춤/자료/"
초, 빨, 금, 파 = (40, 160, 80), (220, 50, 50), (220, 160, 30), (60, 120, 200)
핀구간 = {"핀소개": (0, 24, 금), "핀누름": (24, 59, 파), "관핀": (66, 85, 빨), "ㄱ다리": (128, 143, 초), "ㄱ누름": (144, 179, 빨)}   # 관은 잠금(65 규칙) 전까지만 — 66 엔 잠금이 없다
카드 = {"판": 파, "막대": 파, "평균": 빨, "사라짐": 빨}   # 사라짐 = 73 편 판후 카드(칸마다 깊이 하나로 기운 판이 사라짐)
def 판(키, p):
    끝 = 키.endswith("끝"); k = 키[:-1] if 끝 else 키; 뒤 = k.endswith("2"); k = k[:-1] if 뒤 else k
    c = Image.new("RGBA", (1000, 700), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    if k in 핀구간:
        a, b, 테 = 핀구간[k]; i = b if 끝 else min(b, a + int(max(p, 0) * (b - a + 1))); d.rounded_rectangle((0, 0, 999, 699), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8)
        im = Image.open(A + "핀/프레임_%03d.png" % i).convert("RGBA").crop((110, 60, 830, 564)).resize((1000, 700)); c.alpha_composite(im); return c
    i = 149 if 끝 else min(149, int(max(p, 0) * 150)); i += 150 if 뒤 else 0
    d.rounded_rectangle((0, 0, 999, 699), 36, fill=(250, 250, 252, 255), outline=카드[k] + (255,), width=8); c.alpha_composite(Image.open(A + "%s/element-%03d.png" % (k, i)).convert("RGBA")); return c
