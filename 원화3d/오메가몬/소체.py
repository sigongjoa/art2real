# -*- coding: utf-8 -*-
"""오메가몬 PG 다시 시작 1 — 전신 소체를 원화 옆에 (2026-09-28).

    python 소체.py  -> out/오메가몬2/소체/소체.stl · 관절.json · out/오메가몬2/소체_원화.png
위키: 지식/작업흐름.md ② 레퍼런스 → ③ 소체. 베이스 = 이족 · 비율 「오메가몬」(소체/생성기.py 비율표 · 원화 px).
갑주 · 짐승 머리 · 망토는 아직 없다 — 비율만 본다.
"""
import os, sys, json, subprocess
import numpy as np
R = os.path.dirname(os.path.abspath(__file__)); 원화3d = os.path.dirname(R)
sys.path.insert(0, os.path.join(원화3d, "소체"))
from 생성기 import 이족, 재기, 뼈대, 블, 색, 비율표, BLENDER
from 골격들 import stl
OUT = os.path.join(원화3d, "out", "오메가몬2"); os.makedirs(os.path.join(OUT, "소체"), exist_ok=True)
원화 = os.path.join(os.path.dirname(원화3d), "트레일", "trail7_part3d", "in", "omega_front_clean.png")
돔, 발바닥, 가운데 = 100, 960, 537          # 원화 px: 투구 돔 꼭대기(뿔 뺌) · 발바닥 · 몸 가운데 x
키 = 300.0

if __name__ == "__main__":
    from PIL import Image, ImageDraw, ImageFont
    몸, 관, 뼈 = 이족("오메가몬", "남", 키); 검 = 재기(몸, 관, 뼈, 키, 비율표["오메가몬"]["n"]); print(검)
    f = stl(몸, os.path.join(OUT, "소체", "소체.stl"))
    json.dump(dict(골격="이족", 비율="오메가몬", 키=키, 관절=관, 검사=검, 고친값={}), open(os.path.join(OUT, "소체", "관절.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    뼈m, 볼m, 경m = 뼈대(관, 뼈, 2.0); T = os.path.join(OUT, "소체", "_그림"); os.makedirs(T, exist_ok=True)
    mmpx = 키 / (발바닥 - 돔); 폭 = 1024 * mmpx; cz = 키 - (512 - 돔) * mmpx     # 원화와 같은 틀(1024 px = 폭 mm)
    판 = [dict(부품=[(f, 색["몸"])], 폭=폭, 해상=(1024, 1024), 중심=(0, 0, cz), out=os.path.join(T, "정면.png")),
         dict(부품=[(stl(m, os.path.join(T, n + ".stl")), 색[n]) for m, n in ((뼈m, "뼈"), (볼m, "볼"), (경m, "경첩"))], 폭=폭, 해상=(1024, 1024), 중심=(0, 0, cz), out=os.path.join(T, "뼈.png")),
         dict(부품=[(stl(몸.rotate([0, 0, -90]), os.path.join(T, "옆.stl")), 색["몸"])], 폭=폭, 해상=(1024, 1024), 중심=(0, 0, cz), out=os.path.join(T, "옆.png"))]
    jf = os.path.join(T, "판.json"); json.dump(dict(판=판), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    pf = os.path.join(T, "블.py"); open(pf, "w", encoding="utf-8").write(블)
    r = subprocess.run([BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    _a = Image.open(원화).convert("RGBA"); 원 = Image.new("RGB", _a.size, (255, 255, 255)); 원.paste(_a, mask=_a.split()[3]); 원 = 원.transform(원.size, Image.AFFINE, (1, 0, 가운데 - 512, 0, 1, 0), fillcolor=(255, 255, 255))   # 몸 가운데를 그림 가운데로
    정, 뼈그, 옆 = [Image.open(os.path.join(T, n + ".png")).convert("RGB") for n in ("정면", "뼈", "옆")]
    겹 = Image.blend(원, 정, 0.45); 겹뼈 = Image.composite(뼈그, 원, Image.eval(뼈그.convert("L"), lambda v: 255 if v < 150 or v > 200 else 0))
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 30); S = Image.new("RGB", (4 * 1034 + 10, 1100), (245, 245, 243)); d = ImageDraw.Draw(S)
    for i, (t, im) in enumerate((("원화", 원), ("원화 + 소체 겹침", 겹), ("원화 + 관절", 겹뼈), ("소체 정면(같은 축척)", 정))):
        S.paste(im, (10 + i * 1034, 66)); d.text((16 + i * 1034, 16), t, font=ft, fill=(20, 20, 20))
    for y, 글 in ((돔, "돔"), (182, "턱"), (480, "샅"), (발바닥, "발바닥")):
        d.line([(10, 66 + y), (4 * 1034, 66 + y)], fill=(220, 40, 40), width=2); d.text((14, 66 + y - 34), 글, font=ft, fill=(220, 40, 40))
    p = os.path.join(OUT, "소체_원화.png"); S.save(p); print("시트", p, S.size)
