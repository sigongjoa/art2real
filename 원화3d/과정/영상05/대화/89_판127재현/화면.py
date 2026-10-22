# 89_판127재현 위쪽 화면 판 — 재료 out/영상05/대화/89_판127재현/자료/*.png(하네스/쇼츠.py · 판 127재현 보고서)
from PIL import Image, ImageDraw
A = "G:/art2real/out/영상05/대화/89_판127재현/자료/"
초, 빨, 금 = (40, 160, 80), (220, 50, 50), (220, 160, 30)
카드 = {"명제": 금, "시트": 초, "특징": 빨, "주의": 빨}
def 판(키, p):
    c = Image.new("RGBA", (1000, 700), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, 999, 699), 36, fill=(250, 250, 252, 255), outline=카드[키] + (255,), width=8)
    c.alpha_composite(Image.open(A + 키 + ".png").convert("RGBA").resize((1000, 700))); return c
