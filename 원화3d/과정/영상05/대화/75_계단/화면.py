# 75 편 위쪽 화면 판 — 재료 out/영상05/대화/75_계단/자료/<카드>/element-NNN.png(Remotion Ep75 · 투명) · 턴테이블 카드는 300 프레임(키 뒤 「2」 = 뒤 150) · 숫자는 결과판정69 · 69_천장32 · Anatomy 없음
from PIL import Image, ImageDraw
A = "G:/art2real/out/영상05/대화/75_계단/자료/"
초, 빨, 금, 파 = (40, 160, 80), (220, 50, 50), (220, 160, 30), (60, 120, 200)
카드 = {"관전": 금, "계단": 금, "잘게": 파, "관비교": 파, "판비교": 빨, "숫자": 초}
def 판(키, p):
    끝 = 키.endswith("끝"); k = 키[:-1] if 끝 else 키; 뒤 = k.endswith("2"); k = k[:-1] if 뒤 else k
    i = 149 if 끝 else min(149, int(max(p, 0) * 150)); i += 150 if 뒤 else 0
    c = Image.new("RGBA", (1000, 700), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, 999, 699), 36, fill=(250, 250, 252, 255), outline=카드[k] + (255,), width=8)
    c.alpha_composite(Image.open(A + "%s/element-%03d.png" % (k, i)).convert("RGBA")); return c
