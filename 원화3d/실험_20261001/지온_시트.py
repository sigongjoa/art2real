# -*- coding: utf-8 -*-
"""지온 그래프 한 장: 위 = 조립 · 분해(조인트 · 붙음 선) / 아래 왼 = 부품 카드(지온 4 칸 그림 + 3D 에서 읽은 근거) / 아래 오른 = 붙음 나무.
python 지온_시트.py <지온 폴더> — 폴더에 그래프.json · 자리.json · 조립_34.png · 분해_34.png"""
import os, sys, json, math
from PIL import Image, ImageDraw, ImageFont
O = sys.argv[1] if len(sys.argv) > 1 else r"G:\art2real\원화3d\out\샘플\메크머리_CC0\지온"
g = json.load(open(os.path.join(O, "그래프.json"), encoding="utf-8")); 자리 = json.load(open(os.path.join(O, "자리.json"), encoding="utf-8"))
F = lambda s, b=True: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf" if b else "C:/Windows/Fonts/malgun.ttf", s)
색 = {"투구": (140, 190, 255), "총": (255, 165, 75), "핀": (240, 80, 80)}
관계색 = {"안에-듦": (215, 25, 25), "끝-가운데": (25, 125, 40), "끝-끝": (125, 50, 180), "위에-얹힘": (25, 75, 200)}
K = (40, 40, 40)

def 칸(d, x, y, s, 종류, 값):
    """지온 속성 하나를 s×s 그림으로."""
    d.rectangle([x, y, x + s, y + s], outline=(190, 190, 190), width=2); m = s * 0.2; a, b, c_ = x + m, y + m, s - 2 * m
    if 종류 == "단면":
        if 값 == "둥": d.ellipse([a, b, a + c_, b + c_], outline=K, width=4)
        else: d.rectangle([a, b, a + c_, b + c_], outline=K, width=4)
    elif 종류 == "축":
        if 값 == "곧": d.line([a, b + c_, a + c_, b], fill=K, width=5)
        else: d.arc([a, b, a + 2 * c_, b + 2 * c_], 180, 270, fill=K, width=5)
    elif 종류 == "크기":
        mx = x + s / 2
        poly = {"일정": [(mx - c_ / 4, b), (mx + c_ / 4, b), (mx + c_ / 4, b + c_), (mx - c_ / 4, b + c_)],
                "좁아짐": [(mx - c_ / 12, b), (mx + c_ / 12, b), (mx + c_ / 3, b + c_), (mx - c_ / 3, b + c_)],
                "불룩": [(mx - c_ / 8, b), (mx + c_ / 8, b), (mx + c_ / 2.5, b + c_ / 2), (mx + c_ / 8, b + c_), (mx - c_ / 8, b + c_), (mx - c_ / 2.5, b + c_ / 2)],
                "잘록": [(mx - c_ / 3, b), (mx + c_ / 3, b), (mx + c_ / 10, b + c_ / 2), (mx + c_ / 3, b + c_), (mx - c_ / 3, b + c_), (mx - c_ / 10, b + c_ / 2)]}[값]
        d.polygon(poly, outline=K, width=4)
    else:
        mx = x + s / 2; d.line([mx - c_ / 4, b + c_, mx - c_ / 4, b + c_ / 2], fill=K, width=4); d.line([mx + c_ / 4, b + c_, mx + c_ / 4, b + c_ / 2], fill=K, width=4)
        if 값 == "잘림": d.line([mx - c_ / 4, b + c_ / 2, mx + c_ / 4, b + c_ / 2], fill=K, width=4)
        elif 값 == "뾰족": d.line([mx - c_ / 4, b + c_ / 2, mx, b], fill=K, width=4); d.line([mx + c_ / 4, b + c_ / 2, mx, b], fill=K, width=4)
        else: d.arc([mx - c_ / 4, b + c_ / 4, mx + c_ / 4, b + 3 * c_ / 4], 180, 360, fill=K, width=4)
    d.text((x + 4, y + s + 2), f"{종류} {값}", font=F(15, False), fill=K)

W = 1800; top = 560
조 = Image.open(os.path.join(O, "조립_34.png")).convert("RGB"); 분 = Image.open(os.path.join(O, "분해_34.png")).convert("RGB")
def 자르기(im):
    import numpy as np
    a = np.asarray(im).astype(int); bg = a[5, 5]; m = (abs(a - bg).sum(2) > 20); ys, xs = m.nonzero(); p = 20
    im = im.crop((max(0, xs.min() - p), max(0, ys.min() - p), xs.max() + p, ys.max() + p)); s = min((W / 2 - 20) / im.width, (top - 60) / im.height); return im.resize((int(im.width * s), int(im.height * s)))
조, 분 = 자르기(조), 자르기(분)
cards = [p for p in g["부품들"] if p["쪽"] in ("가운데", "왼")]   # 좌우 짝은 한 장(검사가 짝 지온 같음을 보장)
S = 70; ch = 250; H_ = top + 40 + ch * len(cards) + 40
im = Image.new("RGB", (W, H_), (255, 255, 255)); d = ImageDraw.Draw(im)
d.text((20, 10), "조립", font=F(28), fill=K); d.text((W // 2 + 10, 10), "분해 · 조인트(공) · 붙음 선(관계 색)", font=F(28), fill=K)
im.paste(조, (20, 50)); im.paste(분, (W // 2 + 10, 50))
y = top + 20; d.line([20, y - 10, W - 20, y - 10], fill=(220, 220, 220), width=2)
for p in cards:
    obs = json.loads(p["관찰들"][0]["근거"]) if p["관찰들"] else {}; j = p["지온"]
    d.rectangle([20, y, 44, y + 24], fill=색[p["이름"]]); 짝 = " (왼 · 오른 짝)" if p["쪽"] == "왼" else ""
    d.text((54, y - 4), f'{p["이름"]}{짝} · 층 {p["층"]}', font=F(26), fill=K)
    for i, (k, v) in enumerate([("단면", j["단면"]), ("축", j["축"]), ("크기", j["크기"]), ("끝", j["끝"])]): 칸(d, 30 + i * (S + 28), y + 40, S, k, v)
    t = f'3D 에서 읽은 근거: 원형도 {obs.get("원형도중앙")} · 중심선 휨/길이 {obs.get("중심선휨/길이")} · 넓이 변화 {obs.get("넓이변화")} · 끝 넓이비 {obs.get("끝넓이비")} · 길이 {obs.get("길이mm")} mm'
    d.text((30, y + 40 + S + 30), t, font=F(15, False), fill=(90, 90, 90))
    dim = p["관찰들"][0]["치수"] if p["관찰들"] else {}; d.text((30, y + 40 + S + 52), "주 뷰 치수(mm): " + " · ".join(f"{k} {v}" for k, v in dim.items()), font=F(15, False), fill=(90, 90, 90))
    y += ch
# 나무
x0 = 860; y0 = top + 30; d.text((x0, y0 - 6), "붙음 나무 (자식 → 부모 · 관계 · 조인트)", font=F(24), fill=K)
kids = {}
for e in g["붙음들"]: kids.setdefault(e["부모"], []).append(e)
def 그리기(k, x, y, 깊이=0):
    이름 = k.split("/")[0]; d.rounded_rectangle([x, y, x + 170, y + 40], 8, fill=색.get(이름, (220, 220, 220)), outline=K, width=2); d.text((x + 10, y + 7), k, font=F(19), fill=K)
    yy = y
    for e in kids.get(k, []):
        yy += 0 if yy == y and False else 0
        cy = yy + (70 if 깊이 == 0 else 0); nx = x + 300
        d.line([x + 170, y + 20, nx, cy + 20], fill=관계색[e["관계"]], width=4)
        d.text(((x + 170 + nx) / 2 - 50, (y + cy) / 2 + 2), f'{e["관계"]} · {e["조인트"]}', font=F(15), fill=관계색[e["관계"]])
        yy = 그리기(e["자식"], nx, cy, 깊이 + 1) + 80
    return max(yy - 80, y)
그리기("투구/가운데", x0, y0 + 60)
d.text((x0, H_ - 70), "검사 경보: " + ("없음 (나무 · 부모 하나 · 좌우 짝 지온 같음)" if not 자리["경보"] else " / ".join(자리["경보"])), font=F(18), fill=(0, 120, 0) if not 자리["경보"] else (180, 0, 0))
im.save(os.path.join(O, "지온_시트.png")); print(im.size)
