# 학습 타임랩스 쇼츠 프레임 — ChatGPT 디자인 시안(out/설명/구멍/GPT_디자인.png)을 우리 렌더로 옮김 · 10-13
# 남색 바탕 + 옅은 격자 · 하늘색 빛 · 왼쪽 시간축 카드(지금 = 빛나는 테 · 앞으로 = 점선 ?) · 가운데 큰 형태 + 그림 카드 · 판정 알약 · 겹침 카드 · 아래 대사 자리
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
A = "G:/art2real/out/설명/구멍/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
W, H = 1080, 1920
바탕0, 바탕1, 카드, 테, 하늘, 흰, 회, 빨 = (8, 13, 26), (14, 22, 42), (16, 24, 42), (40, 54, 84), (64, 196, 255), (236, 242, 250), (120, 132, 156), (255, 96, 96)
에폭 = ["0", "1", "2", "4엇", "3", "4", "6", "5"]
판정 = ["구멍 없음", "작다", "작다", "옆으로 샘", "작다", "거의", "너무 큼", "맞음"]

def 둥근(d, xy, r, **k): d.rounded_rectangle(xy, r, **k)
def 빛테(c, xy, r, col, 굵기=5, 퍼짐=18):   # 바깥으로 번지는 빛 + 선명한 테
    g = Image.new("RGBA", c.size, (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle(xy, r, outline=col + (255,), width=굵기 + 6)
    c.alpha_composite(g.filter(ImageFilter.GaussianBlur(퍼짐))); ImageDraw.Draw(c).rounded_rectangle(xy, r, outline=col + (255,), width=굵기)
def 점선테(d, xy, r, col, 간=14):
    x0, y0, x1, y1 = xy
    for x in range(x0 + r, x1 - r, 간 * 2): d.line((x, y0, x + 간, y0), fill=col, width=3); d.line((x, y1, x + 간, y1), fill=col, width=3)
    for y in range(y0 + r, y1 - r, 간 * 2): d.line((x0, y, x0, y + 간), fill=col, width=3); d.line((x1, y, x1, y + 간), fill=col, width=3)
def 형태(p, s, 알파=255):
    im = Image.open(A + p).convert("RGBA").resize((s, s), Image.LANCZOS)
    if 알파 < 255: im.putalpha(im.split()[3].point(lambda v: v * 알파 // 255))
    return im
def 바탕():
    c = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(c)
    for y in range(H): t = y / H; d.line((0, y, W, y), fill=tuple(int(바탕0[k] + (바탕1[k] - 바탕0[k]) * math.sin(math.pi * t)) for k in range(3)) + (255,))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); e = ImageDraw.Draw(g)   # 옅은 격자는 따로 그려 겹침(같은 판에 그리면 알파가 덮어써짐)
    for x in range(0, W, 60): e.line((x, 0, x, H), fill=(120, 160, 230, 14))
    for y in range(0, H, 60): e.line((0, y, W, y), fill=(120, 160, 230, 14))
    c.alpha_composite(g); return c
def 바닥격자(c, xy):   # 큰 형태 아래 원근 격자
    x0, y0, x1, y1 = xy; g = Image.new("RGBA", c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(g); cx = (x0 + x1) / 2; hy = y0 + (y1 - y0) * .42
    for k in range(-10, 11): d.line((cx + k * 18, hy, cx + k * 120, y1), fill=(90, 140, 220, 40), width=2)
    for j in range(1, 9): y = hy + (y1 - hy) * (j / 8) ** 1.6; d.line((x0, y, x1, y), fill=(90, 140, 220, 34), width=2)
    m = Image.new("L", c.size, 0); ImageDraw.Draw(m).rounded_rectangle(xy, 36, fill=255); c.alpha_composite(Image.composite(g, Image.new("RGBA", c.size), m))

def 프레임(k):
    c = 바탕(); d = ImageDraw.Draw(c)
    # 제목: 「AI」 하늘색 빛 + 흰 글 · 양옆 /// · 아래 빛줄
    t1, t2 = "AI", "가 구멍을 맞춰 가는 중"; f = F(64); w1, w2 = d.textlength(t1, font=f), d.textlength(t2, font=f); x = (W - w1 - w2) / 2
    g = Image.new("RGBA", c.size); ImageDraw.Draw(g).text((x, 70), t1, font=f, fill=하늘 + (255,)); c.alpha_composite(g.filter(ImageFilter.GaussianBlur(10))); d.text((x, 70), t1, font=f, fill=하늘); d.text((x + w1, 70), t2, font=f, fill=흰)
    d.text((x - 90, 78), "///", font=F(44), fill=(70, 90, 130)); d.text((x + w1 + w2 + 30, 78), "///", font=F(44), fill=(70, 90, 130))
    g = Image.new("RGBA", c.size); ImageDraw.Draw(g).line((240, 172, 840, 172), fill=하늘 + (255,), width=4); c.alpha_composite(g.filter(ImageFilter.GaussianBlur(6))); d.line((340, 172, 740, 172), fill=하늘, width=3)
    # 왼쪽 시간축: 점선 줄 + 마디 점 + 카드
    x0, y0, 칸 = 40, 215, 150; cx = x0 + 70
    for y in range(y0, y0 + 칸 * 8, 16): d.line((cx, y, cx, y + 8), fill=(60, 78, 112), width=4)
    d.line((cx, y0, cx, y0 + 칸 * (k - 1) + 60), fill=하늘, width=4)
    for j in range(8):
        y = y0 + 칸 * j; box = (x0, y + 8, x0 + 140, y + 128)
        if j < k:
            둥근(d, box, 22, fill=카드 + (255,), outline=테, width=3)
            if j == k - 1: 빛테(c, box, 22, 하늘, 5, 14)
            c.alpha_composite(형태("비스듬_r%s.png" % 에폭[j], 116, 255 if j == k - 1 else 190), (x0 + 12, y + 10))
        else:
            점선테(d, box, 22, (64, 80, 112)); d.text((x0 + 70, y + 68), "?", font=F(52), fill=(64, 80, 112), anchor="mm")
        d.ellipse((cx - 7, y + 136, cx + 7, y + 150), fill=하늘 if j < k else (60, 78, 112))
    # 가운데 큰 형태 카드
    mb = (200, 205, 1050, 1000); 둥근(d, mb, 36, fill=카드 + (230,), outline=테, width=2); 바닥격자(c, mb)
    c.alpha_composite(형태("비스듬_r%s.png" % 에폭[k - 1], 640), (300, 270))
    d.text((240, 240), "에폭 %d" % k, font=F(46), fill=하늘)
    둥근(d, (810, 230, 1025, 450), 24, fill=(244, 246, 250, 255)); c.alpha_composite(형태("그림_목표.png", 170).convert("RGBA"), (832, 242)); d.text((917, 428), "그림", font=F(28), fill=(40, 44, 56), anchor="mm")
    # 판정 알약
    맞 = 판정[k - 1] == "맞음"; col = 하늘 if 맞 else 빨; 글 = 판정[k - 1]; pw = d.textlength(글, font=F(50)) + 150; px = (200 + 1050 - pw) / 2; pb = (px, 900, px + pw, 980)
    둥근(d, pb, 40, fill=(12, 20, 36, 255)); 빛테(c, pb, 40, col, 4, 12)
    ix, iy = px + 50, 940; d.ellipse((ix - 24, iy - 24, ix + 24, iy + 24), fill=col)
    if 맞: d.line((ix - 11, iy, ix - 3, iy + 9, ix + 12, iy - 9), fill=(12, 20, 36), width=6)
    else: d.line((ix - 9, iy - 9, ix + 9, iy + 9), fill=(12, 20, 36), width=6); d.line((ix - 9, iy + 9, ix + 9, iy - 9), fill=(12, 20, 36), width=6)
    d.text((px + 90, 940), 글, font=F(50), fill=흰, anchor="lm")
    # 겹침 카드
    cb = (200, 1030, 1050, 1440); 둥근(d, cb, 36, fill=카드 + (230,), outline=테, width=2); d.text((240, 1060), "위에서 본 모양  ↔  그림", font=F(38), fill=흰)
    둥근(d, (240, 1125, 540, 1425), 14, fill=(244, 246, 250, 255)); c.alpha_composite(형태("겹침_r%s.png" % 에폭[k - 1], 280).convert("RGBA"), (250, 1135))
    for j, (t, sw) in enumerate((("파랑 = AI", (100, 150, 245)), ("빨강 = 그림", 빨))):
        y = 1230 + j * 80; 둥근(d, (600, y - 22, 644, y + 22), 8, fill=sw); d.text((664, y), t, font=F(38), fill=흰, anchor="lm")
    # 아래 대사 자리(대화 쇼츠의 인물 · 대사창이 들어감)
    둥근(d, (300, 1560, 1040, 1860), 40, fill=(12, 20, 36, 200)); 빛테(c, (300, 1560, 1040, 1860), 40, (70, 150, 230), 3, 10)
    d.text((670, 1710), "대사 자리", font=F(40), fill=(80, 96, 128), anchor="mm"); d.text((150, 1710), "인물", font=F(40), fill=(80, 96, 128), anchor="mm")
    return c.convert("RGB")

if __name__ == "__main__":
    fs = [프레임(k) for k in (2, 5, 8)]
    s = Image.new("RGB", (3 * 540 + 40, 960 + 70), (30, 32, 40)); d = ImageDraw.Draw(s)
    for j, (f, k) in enumerate(zip(fs, (2, 5, 8))): s.paste(f.resize((540, 960), Image.LANCZOS), (10 + j * 550, 60)); d.text((10 + j * 550 + 270, 30), "에폭 %d" % k, font=F(30), fill=(236, 242, 250), anchor="mm")
    s.save(A + "프레임디자인.png"); fs[2].save(A + "프레임디자인_한장.png"); print("ok")
