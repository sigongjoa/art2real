# -*- coding: utf-8 -*-
"""가린 판정 시트 — 쌍(사람 / 후보) 그림을 섞어 번호만 붙인다 · 후보는 우리 · 교차 · 양성 대조(같은 사람 부품) · 음성 대조(다른 부품의 우리 결과) · 모두 같은 색 · 10-12
python runs/기능0/가린시트.py <출력 폴더> <대응표.json>   → 쌍NNN.png · 대응표는 판정자가 읽는 폴더 밖에 둔다"""
import os, sys, json, random, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
from render import render
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); C = 256; RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
우 = os.environ.get("OURS", "B_모델T_검증뺌")   # 10-12 C 판 = OURS=B_C
폴더 = {("시험", "우리"): 우, ("검증", "우리"): 우 + "_검증", ("검증2", "우리"): 우 + "_검증2", ("시험", "교차"): "B_교차", ("검증", "교차"): "B_교차_검증", ("검증2", "교차"): "B_교차_검증2"}
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 그(m, 색, v): return Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), v, img_size=C, cols=None if 색 is None else np.tile(색, (len(m.faces), 1)))))
def 쌍그림(사람, 후보):
    c = Image.new("RGB", (4 * C + 30, C + 40), "white"); d = ImageDraw.Draw(c); d.text((C, 18), "사람", font=F(24), fill="black", anchor="mm"); d.text((3 * C + 30, 18), "후보", font=F(24), fill="black", anchor="mm")
    for j, v in enumerate(([1, .6, .8], [-1, -.6, .8])):
        c.paste(그(사람, None, v), (j * C, 40))
        if 후보 is None: d.text((2 * C + 30 + j * C + C // 2, 40 + C // 2), "없음", font=F(30), fill=(200, 50, 50), anchor="mm")
        else: c.paste(그(후보, (0.55, 0.8, 0.5), v), (2 * C + 30 + j * C, 40))
    return c
if __name__ == "__main__":
    O, 표 = sys.argv[1], sys.argv[2]; os.makedirs(O, exist_ok=True); L = json.load(open(os.path.join(H, "라벨.json"), encoding="utf-8"))["부품"]
    세트들 = os.environ.get("SETS", "시험,검증").split(","); 키 = sorted(k for k in L if k.split("/")[0] in 세트들); rng = random.Random(int(os.environ.get("SEED", 20261012))); 항목 = [(k, 방) for k in 키 for 방 in ("우리", "교차")]
    for k in rng.sample(키, 10): 항목.append((k, "양성"))
    for k in rng.sample(키, 10): 항목.append((k, "음성:" + rng.choice([q for q in 키 if q != k])))
    rng.shuffle(항목); 대응 = {}
    for n, (k, 방) in enumerate(항목):
        세트, i = k.split("/"); 사람 = 정(trimesh.load(RR + L[k]["부품"], force="mesh"))
        if 방 == "양성": 후보 = 사람
        else:
            src = k if not 방.startswith("음성") else 방.split(":")[1]; s2, i2 = src.split("/"); p = os.path.join(H, 폴더[(s2, "우리" if 방.startswith("음성") else 방)], "%s.stl" % i2)
            후보 = 정(trimesh.load(p)) if os.path.exists(p) else None
        쌍그림(사람, 후보).save(os.path.join(O, "쌍%03d.png" % n)); 대응["쌍%03d" % n] = {"부품": k, "후보": 방}; print(n, flush=True)
    json.dump(대응, open(표, "w", encoding="utf-8"), ensure_ascii=False, indent=0); print("ok", len(대응))
