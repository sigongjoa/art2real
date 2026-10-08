# -*- coding: utf-8 -*-
"""모션 그래픽 세 갈래 시안(10-08 · 조사 claudedocs/research_모션그래픽_20261008.md) — 공막대(컷 4) · 엉덩이(컷 8)
지금 | A 테크 미니멀 | B 손그림 마커 | C 장면 안 소품(블렌더 34_클로드코드C) → _갈래비교.jpg"""
import json, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
O = "G:/art2real/out/영상05/장난감/"; F = O + "34_클로드코드/frames/"; FC = O + "34_클로드코드C/frames/"
S = "C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/259f23f2-edc9-4277-85f4-fd324dc7cd8f/scratchpad/"
GD = lambda n: ImageFont.truetype(S + "GowunDodum.ttf", n); PEN = lambda n: ImageFont.truetype(S + "NanumPen.ttf", n)
KR = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
W, H = 1080, 1920; YEL = (255, 214, 64); WH = (245, 245, 245); SKY = (140, 200, 255)
A = {a["컷"]: a for a in json.load(open(F + "앵커.json", encoding="utf-8"))}
CAP = {4: "공 두 개 붙은 관절", 8: "안에 있던 관절 공이"}

def cap_thin(d, s):   # A 규칙 자막: 흰색 · 얇은 외곽선 · 한 줄
    d.text((W // 2, 1290), s, font=GD(64), fill=WH, anchor="mm", stroke_width=3, stroke_fill=(20, 20, 20))
def thin_label(d, p, s, col, dx, dy):
    x, y = p[0] * W, p[1] * H; d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=col)
    ex, ey = x + dx, y + dy; d.line((x, y, ex, ey), fill=col, width=3); d.line((ex, ey, ex + (110 if dx > 0 else -110), ey), fill=col, width=3)
    d.text((ex + (120 if dx > 0 else -120), ey), s, font=GD(54), fill=col, anchor="lm" if dx > 0 else "rm")
def corner_score(d, s):
    d.text((W - 60, 120), s, font=GD(58), fill=WH, anchor="rm"); d.line((W - 330, 160, W - 60, 160), fill=YEL, width=3)

def A_(k, im):
    d = ImageDraw.Draw(im); a = A[k]["점"]
    if k == 4:
        thin_label(d, a["공막대사람"], "사람", WH, 60, -300); thin_label(d, a["공막대클로드"], "Claude", YEL, -60, -300); corner_score(d, "Claude  1 / 10")
    else:
        thin_label(d, a["엉덩이사람"], "관절 공", WH, 60, -330); thin_label(d, a["엉덩이클로드"], "없음", YEL, -60, -330); corner_score(d, "Claude  3 / 10")
    cap_thin(d, CAP[k]); return im

def wob(d, pts, col, w):   # 손 떨림 있는 선(두 번 겹쳐 그은 마커)
    for rep in range(2):
        rnd = random.Random(rep * 7 + len(pts)); q = [(x + rnd.uniform(-4, 4), y + rnd.uniform(-4, 4)) for x, y in pts]; d.line(q, fill=col, width=w, joint="curve")
def marker_circle(d, p, r, col):
    cx, cy = p[0] * W, p[1] * H; rnd = random.Random(3)
    pts = [(cx + (r + rnd.uniform(-10, 10)) * math.cos(t) * 1.15, cy + (r + rnd.uniform(-10, 10)) * math.sin(t)) for t in [i / 40 * 2 * math.pi * 1.08 - 0.4 for i in range(41)]]
    wob(d, pts, col, 12)
def marker_arrow(d, a, b, col):
    wob(d, [a, ((a[0] + b[0]) / 2 + 30, (a[1] + b[1]) / 2 - 20), b], col, 10)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (2.6, -2.6): wob(d, [b, (b[0] + 45 * math.cos(ang + s), b[1] + 45 * math.sin(ang + s))], col, 10)
def B_(k, im):
    d = ImageDraw.Draw(im); a = A[k]["점"]
    if k == 4:
        p = a["공막대클로드"]; marker_circle(d, p, 150, YEL)
        d.text((p[0] * W - 40, p[1] * H - 330), "똑같다!", font=PEN(130), fill=YEL, anchor="mm")
        p0 = a["공막대사람"]; d.text((p0[0] * W, p0[1] * H - 250), "사람", font=PEN(90), fill=WH, anchor="mm")
    else:
        pc = a["엉덩이클로드"]; marker_circle(d, pc, 95, YEL); ph = a["엉덩이사람"]
        d.text((W // 2, ph[1] * H - 360), "관절 공이 없다", font=PEN(120), fill=YEL, anchor="mm")
        marker_arrow(d, (ph[0] * W + 40, ph[1] * H - 250), (ph[0] * W + 10, ph[1] * H - 60), WH)
    # 종이 결(아주 약한 그레인)
    g = Image.effect_noise((W, H), 18).convert("RGB"); im = Image.blend(im, g, 0.04); d = ImageDraw.Draw(im)
    cap_thin(d, CAP[k]); return im

def C_(k, im):
    d = ImageDraw.Draw(im); cap_thin(d, CAP[k]); return im

cols = []
for k in (4, 8):
    row = [Image.open(F + "mg_%02d.png" % k).convert("RGB"), A_(k, Image.open(F + "still_%02d.png" % k).convert("RGB")),
           B_(k, Image.open(F + "still_%02d.png" % k).convert("RGB")), C_(k, Image.open(FC + "still_%02d.png" % k).convert("RGB"))]
    cols.append(row)
w, h = 432, 768; sheet = Image.new("RGB", (w * 4 + 30, h * 2 + 70), (30, 30, 34)); d = ImageDraw.Draw(sheet)
for j, t in enumerate(("지금", "A 테크 미니멀", "B 손그림 마커", "C 장면 안 소품")): d.text((j * (w + 10) + w // 2, 35), t, font=KR(36), fill=WH, anchor="mm")
for i, row in enumerate(cols):
    for j, im in enumerate(row): sheet.paste(im.resize((w, h)), (j * (w + 10), 70 + i * h))
sheet.save(O + "34_클로드코드/_갈래비교.jpg"); print(sheet.size)
