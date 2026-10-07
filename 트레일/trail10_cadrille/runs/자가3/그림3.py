# 3 바퀴 비교 그림: 사람 / 바탕 최고 / LoRA3 최고 (모서리 F1 기준) · 갈린 부품 위주
import os, sys, json, numpy as np, trimesh, tempfile
from PIL import Image, ImageDraw, ImageFont
H = "s0"; sys.path[:0] = [".", H, os.path.join(H, "stub")]
import cadquery as cq, s0 as S
from render import render
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
B = {r["부품"]: r for r in json.load(open("runs/자가3/평가67e_바탕.json", encoding="utf-8"))["부품별"]}
L = {r["부품"]: r for r in json.load(open("runs/자가3/평가67e_3바퀴.json", encoding="utf-8"))["부품별"]}
d = sorted(B, key=lambda k: L[k]["최고모서리"] - B[k]["최고모서리"]); pick = d[:4] + d[-4:]   # 가장 나빠진 4 · 가장 나아진 4
def mesh(code):
    ns = {"cq": cq}; exec(code, ns); o = ns.get("r") or next(v for v in ns.values() if isinstance(v, cq.Workplane))
    p = os.path.join(tempfile.gettempdir(), "그림3.stl"); cq.exporters.export(o, p); return S.unit(trimesh.load(p))
def best(r):
    i = int(np.argmax(r["모서리"])); return (mesh(r["코드"][i]) if r["모서리"][i] >= 0 else None), r["모서리"][i]
F = ImageFont.truetype("malgun.ttf", 15); C = 220; rows = []
for k in pick:
    cells = [(S.unit(trimesh.load(R + k, force="mesh")), "사람")]
    for nm, D in (("바탕", B), ("LoRA3", L)):
        m, e = best(D[k]); cells.append((m, "%s 모서리 %.2f%s" % (nm, e, " O" if e >= 0.42 else " X")))
    row = Image.new("RGB", (C * 3, C + 22), "white"); dr = ImageDraw.Draw(row)
    for j, (m, t) in enumerate(cells):
        if m is not None: row.paste(render(np.asarray(m.vertices), np.asarray(m.faces), [1, 1, 1], img_size=C), (j * C, 22))
        dr.text((j * C + 6, 2), t, fill="black", font=F)
    dr.text((C * 3 - 200, C + 4), k.split("/")[-1][:28], fill="gray", font=F); rows.append(row)
out = Image.new("RGB", (C * 3, sum(r.height for r in rows)), "white"); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height
out.save("runs/그림/3바퀴_비교.png"); print("ok")
