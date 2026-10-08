# -*- coding: utf-8 -*-
"""지금(cadrille) vs 새 구조(얼린 인코더 + 동작 디코더) vs 인코더 시험 — 한 장 그림 (10-08)"""
import os
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__)); S0 = os.path.join(D, "..", "사전0")
F = lambda s, b=True: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf" if b else "C:/Windows/Fonts/malgun.ttf", s)
W, H = 2600, 1560; im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
src = Image.open(os.path.join(S0, "0_05.png")); gt, pr = src.crop((0, 0, 260, 260)), src.crop((0, 260, 260, 520))
GR, BL, OR, RD, GN, IC = (120, 120, 120), (60, 110, 220), (240, 150, 40), (220, 60, 60), (40, 160, 70), (235, 240, 250)

def box(x, y, w, h, t, sub="", c=BL, fill=IC, lock=False):
    d.rounded_rectangle((x, y, x + w, y + h), 18, fill=fill, outline=c, width=5)
    d.text((x + w / 2, y + h / 2 - (16 if sub else 0)), t, font=F(30), fill="black", anchor="mm")
    if sub: d.text((x + w / 2, y + h / 2 + 24), sub, font=F(22, False), fill=(60, 60, 60), anchor="mm")
    if lock: d.text((x + w - 14, y + 10), "얼림", font=F(22), fill=BL, anchor="ra")
def arr(x1, x2, y):
    d.line((x1, y, x2 - 14, y), fill=GR, width=6); d.polygon([(x2, y), (x2 - 22, y - 13), (x2 - 22, y + 13)], fill=GR)
def row(y, title, c):
    d.text((40, y), title, font=F(40), fill=c)

# 1 지금
y = 60; row(y, "① 지금 — cadrille: 「sketch」라는 글자를 쓴다", RD); y += 80
im.paste(gt.resize((200, 200)), (40, y)); arr(250, 330, y + 100)
box(330, y + 20, 300, 160, "그림 읽기", "인코더 6.75 억", lock=False)
arr(630, 710, y + 100)
box(710, y - 10, 620, 220, "언어 디코더 15 억", "영어 · 파이썬 · 문장까지 다 아는 모델 · 어휘 15 만", c=RD, fill=(253, 236, 236))
arr(1330, 1410, y + 100)
d.rounded_rectangle((1410, y + 10, 2140, y + 190), 12, fill=(30, 30, 30))
for i, (t, col) in enumerate([("r = w.sketch().segment((", "white"), ("  -87,39),(-83,-41)).segment((", (255, 200, 80)),
                               ("  -83,-41),(52,-40))...  ← 40 % 가 숫자", (255, 200, 80))]):
    d.text((1430, y + 30 + i * 48), t, font=F(28, False), fill=col)
arr(2140, 2200, y + 100); im.paste(pr.resize((200, 200)), (2210, y))
d.text((2310, y + 215), "실행해야 모양", font=F(22, False), fill=GR, anchor="ma")
d.text((710, y + 230), "글자 조각 하나씩 고름 · 37 대신 38 이나 92 나 똑같이 틀림 · 학습 부품 67 % 외우고 시험 27 % (바탕 34 %)", font=F(26, False), fill=RD)

# 2 새 구조
y = 560; row(y, "② 새 구조 — 「sketch」라는 동작만 고른다 (뜻은 CAD 프로그램이 이미 안다)", GN); y += 80
im.paste(gt.resize((200, 200)), (40, y)); arr(250, 330, y + 100)
box(330, y + 20, 300, 160, "그림 읽기", "인코더 · 빌려 옴", lock=True)
arr(630, 710, y + 100)
box(710, y + 45, 240, 110, "동작 디코더", "수천만 · 어휘 300", c=GN, fill=(232, 247, 235))
arr(950, 1030, y + 100)
for i, (t, c) in enumerate([("스케치", BL), ("밀기 · 칸 37", BL), ("공관절 · 칸 12", BL), ("구멍 ×2", BL), ("모따기", OR), ("끝", GR)]):
    x = 1030 + (i % 3) * 210; yy = y + 30 + (i // 3) * 80
    d.rounded_rectangle((x, yy, x + 195, yy + 62), 30, fill=c); d.text((x + 97, yy + 31), t, font=F(26), fill="white", anchor="mm")
arr(1670, 1740, y + 100)
box(1740, y + 30, 220, 140, "CadQuery", "실행 · 미분 안 됨", c=GR, fill=(245, 245, 245))
arr(1960, 2030, y + 100)
box(2030, y + 30, 160, 140, "컨투어", "숫자 다듬기", c=OR, fill=(253, 243, 228))
arr(2190, 2210, y + 100); im.paste(pr.resize((200, 200)), (2210, y))
d.text((710, y + 230), "디코더 크기 비교:", font=F(26), fill="black")
d.rectangle((960, y + 236, 960 + 900, y + 262), fill=(253, 200, 200)); d.text((1870, y + 249), "언어 디코더 15 억", font=F(22), fill=RD, anchor="lm")
d.rectangle((960, y + 272, 960 + 18, y + 298), fill=GN); d.text((990, y + 285), "동작 디코더 약 3 천만 (1/50)", font=F(22), fill=GN, anchor="lm")
d.text((710, y + 315), "상한을 정하는 건 모델 크기가 아니라 동작 목록 — 사전0 에서 빠진 것: 아무 방향 모따기 · 껍질/휜 판 · 쐐기", font=F(26, False), fill=OR)

# 3 인코더 시험
y = 1080; row(y, "③ 먼저 할 시험 — 얼린 인코더가 CAD 에 필요한 것을 이미 보고 있나 (디코더 만들기 전)", BL); y += 80
im.paste(gt.resize((200, 200)), (40, y)); arr(250, 330, y + 100)
for i, (t, s) in enumerate([("cadrille 인코더", "CAD 렌더로 학습됨"), ("Qwen2-VL 원본", "일반 그림"), ("DINOv2", "그림 전용 · 작음")]):
    box(330, y - 10 + i * 82, 330, 72, t, ""); d.text((680, y + 26 + i * 82), s, font=F(20, False), fill=GR, anchor="lm")
arr(900, 980, y + 100); d.text((495, y - 30), "셋 다 얼림 · 같은 시험", font=F(22), fill=BL, anchor="mm")
box(980, y + 50, 200, 100, "선형층 하나", "학습은 이것만", c=GN, fill=(232, 247, 235))
arr(1180, 1260, y + 100)
qs = ["구멍 있나 · 몇 개", "모따기 있나", "회전체 · 판", "대칭인가", "크기 비율"]
for i, q in enumerate(qs):
    d.rounded_rectangle((1260, y - 10 + i * 46, 1600, y + 30 + i * 46), 14, fill=(240, 240, 240), outline=GR, width=2)
    d.text((1430, y + 10 + i * 46), q, font=F(23), fill="black", anchor="mm")
arr(1600, 1680, y + 100)
for i, (t, c) in enumerate([("≥ 90 %  얼려서 그대로", GN), ("80~90 %  마지막 층만 조금 풂", OR), ("< 80 %  그 인코더 버림", RD)]):
    d.rounded_rectangle((1680, y + 10 + i * 64, 2380, y + 64 + i * 64), 14, fill=c)
    d.text((1700, y + 37 + i * 64), t, font=F(28), fill="white", anchor="lm")
d.text((40, y + 330), "합성 부품(정답 앎) + 사람 부품 36 · 선형층만 학습이라 GPU 한 시간 안 · 통과한 인코더 위에 ② 디코더를 올리면 실패 원인이 인코더/디코더로 갈린다", font=F(26, False), fill=(60, 60, 60))
im.save(os.path.join(D, "구조_인코더시험.png")); print("ok")
