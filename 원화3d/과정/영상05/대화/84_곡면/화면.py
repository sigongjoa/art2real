# 84 편 위쪽 화면 판 — 재료 out/영상05/대화/84_곡면/자료/*.png(재료.py) · 공3d = 48 장 돌림(공3d 앞 24 · 공3d2 뒤 24)
from PIL import Image, ImageDraw
A = "G:/art2real/out/영상05/대화/84_곡면/자료/"
초, 빨, 금 = (40, 160, 80), (220, 50, 50), (220, 160, 30)
카드 = {"공": 빨, "공3d": 빨, "공3d2": 빨, "공2": 금, "틀": 금, "안됨": 빨, "안됨2": 금}
def 판(키, p):
    p = min(max(p, 0), 1); 색 = 카드[키]
    if 키 == "공3d": f = "공3d_%02d.png" % min(23, int(p * 24))
    elif 키 == "공3d2": f = "공3d_%02d.png" % (24 + min(23, int(p * 24)))
    else: f = 키 + ".png"
    c = Image.new("RGBA", (1000, 700), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, 999, 699), 36, fill=(250, 250, 252, 255), outline=색 + (255,), width=8)
    c.alpha_composite(Image.open(A + f).convert("RGBA").resize((1000, 700))); return c
