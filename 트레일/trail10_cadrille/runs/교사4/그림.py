# 교사4: 학습 부품(외움) 2 + 시험 부품(못 옮김) 2 — 사람 | 바탕 | 교사4 (모서리 최고 답)
import os, sys, json, numpy as np, trimesh, tempfile
from PIL import Image, ImageDraw, ImageFont
sys.path[:0] = [".", "s0", "s0/stub"]
import cadquery as cq, s0 as S
from render import render
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
L = lambda p: {r["부품"]: r for r in json.load(open(p, encoding="utf-8"))["부품별"]}
TR, TE, BA = L("runs/교사4/평가_학습부품.json"), L("runs/교사4/평가67e.json"), L("runs/자가3/평가67e_바탕.json")
def mesh(c):
    try:
        ns = {"cq": cq}; exec(c, ns); o = ns.get("r") or next(v for v in ns.values() if isinstance(v, cq.Workplane))
        p = os.path.join(tempfile.gettempdir(), "교사4그림.stl"); cq.exporters.export(o, p); return S.unit(trimesh.load(p))
    except Exception: return None
def best(r):
    i = int(np.argmax(r["모서리"])); return (mesh(r["코드"][i]) if r["모서리"][i] >= 0 else None), r["모서리"][i]
tr = sorted(TR, key=lambda k: -TR[k]["최고모서리"])[:2]; te = sorted(TE, key=lambda k: BA[k]["최고모서리"] - TE[k]["최고모서리"])[-2:]
F = ImageFont.truetype("malgun.ttf", 16); C = 220; rows = []
for k, kind in [(k, "학습") for k in tr] + [(k, "시험") for k in te]:
    cells = [(S.unit(trimesh.load(R + k, force="mesh")), f"사람 ({kind} 부품)")]
    if kind == "시험": m, e = best(BA[k]); cells.append((m, "바탕 %.2f" % e))
    m, e = best((TR if kind == "학습" else TE)[k]); cells.append((m, "교사4 %.2f%s" % (e, " O" if e >= 0.42 else " X")))
    row = Image.new("RGB", (C * 3, C + 22), "white"); d = ImageDraw.Draw(row)
    for j, (mm, t) in enumerate(cells):
        if mm is not None: row.paste(render(np.asarray(mm.vertices), np.asarray(mm.faces), [1, 1, 1], img_size=C), (j * C, 22))
        d.text((j * C + 6, 2), t, font=F, fill="black")
    rows.append(row)
out = Image.new("RGB", (C * 3, sum(r.height for r in rows)), "white"); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height
out.save("runs/그림/교사4_외움대시험.png"); print("ok")
