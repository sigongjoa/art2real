# 72 편(실제 모양) 위쪽 화면 판 — 재료 out/영상05/대화/72_실제모양/자료/<카드>/element-NNN.png(Remotion Ep72 · 실제 부품 렌더(재료72) · 150 프레임 · 투명) · 숫자는 결과판정62 · 63 · 재료72 · Anatomy 없음(10-17 사용자)
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/72_실제모양/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 40, 50), (130, 130, 140), (220, 160, 30)
카드 = {"점수": (초, "채점만 바꿨다"), "자": (초, ""), "톱니": (초, "톱니 링"), "판": (빨, "모터 판"), "관": (빨, "얇은 관")}
def 판(키, p):
    k = 키[:-1] if 키.endswith("끝") else 키; 테, 제 = 카드[k]; i = 149 if 키.endswith("끝") else min(149, int(max(p, 0) * 150))
    c = Image.new("RGBA", (1000, 700), (0, 0, 0, 0)); d = ImageDraw.Draw(c); d.rounded_rectangle((0, 0, 999, 699), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8)
    c.alpha_composite(Image.open(A + "%s/element-%03d.png" % (k, i)).convert("RGBA")); d.text((500, 72), 제, font=F(42), fill=먹, anchor="mm"); return c
