# -*- coding: utf-8 -*-
"""사전0 판정 — 판정기준.json 대로 결과0~2 합산 + 36 장 시트(위 사람 · 아래 구조 문장 · 초록 = 둘 다 통과)"""
import json, os, statistics as st
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__))
R = [r for i in range(3) for r in json.load(open(f"{D}/결과{i}.json", encoding="utf-8"))]
assert len(R) == 36, len(R)
ok = lambda r: r["edge_f1"] >= 0.42 and str(r["눈판정"]).startswith("O")
n = sum(map(ok, R)); 판 = {"자": sum(r["edge_f1"] >= 0.42 for r in R), "눈O": sum(str(r["눈판정"]).startswith("O") for r in R),
     "둘다": n, "비율": round(n / 36, 3), "기준": 29, "통과": n >= 29,
     "줄수중앙": st.median(r["낱말수"] for r in R), "윤곽판의존": sum(r["윤곽판수"] >= 1 for r in R),
     "모서리중앙": round(st.median(r["edge_f1"] for r in R), 3)}
json.dump(판, open(f"{D}/판정.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(판)
f = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 22); W, H = 390, 260; S = Image.new("RGB", (W * 6, H * 6), "white")
for k, r in enumerate(R):
    im = Image.open(f"{D}/{k // 12}_{k % 12:02d}.png").resize((W, H)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=(40, 170, 60) if ok(r) else (220, 50, 50), width=6)
    d.text((10, 8), "%d_%02d  %.2f  %s" % (k // 12, k % 12, r["edge_f1"], str(r["눈판정"])[0]), font=f, fill="black")
    S.paste(im, ((k % 6) * W, (k // 6) * H))
S.save(f"{D}/../그림/사전0_36.jpg", quality=85)
