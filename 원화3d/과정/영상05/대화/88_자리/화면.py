# 88 편 위쪽 화면 판 — 재료 out/영상05/대화/88_자리/자료/*.png(재료.py · 124 실제 렌더)
from PIL import Image, ImageDraw
A = "G:/art2real/out/영상05/대화/88_자리/자료/"
초, 빨, 금 = (40, 160, 80), (220, 50, 50), (220, 160, 30)
카드 = {"뭉침": 빨, "과정": 초, "본부품": 빨, "본것": 금, "몸수": 금, "잊음": 빨}
def 판(키, p):
    c = Image.new("RGBA", (1000, 700), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, 999, 699), 36, fill=(250, 250, 252, 255), outline=카드[키] + (255,), width=8)
    c.alpha_composite(Image.open(A + 키 + ".png").convert("RGBA").resize((1000, 700))); return c
