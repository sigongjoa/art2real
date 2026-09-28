# -*- coding: utf-8 -*-
"""오메가몬 PG 머리 소체(기본 프레임) (2026-09-28) — 갑주를 짓기 전에 속 머리부터.

    python 소체머리.py  -> out/출력/오메가몬_PG/소체_머리/*.stl · 멋/소체머리.jpg
사람 머리 비율(폭 : 높이 : 깊이 ≈ 0.66 : 1 : 0.85 · 눈은 높이의 가운데)로 두개 + 턱 + 목.
갑주(투구 · 마스크)는 이 면에서 바깥으로 띄워 짓는다 — 갑주 치수는 여기서 나온다.
"""
import os, sys, json, subprocess
import numpy as np, manifold3d as M
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 얼굴3 as F3
from 얼굴3 import 메, 색, 멋, FRA
F1 = F3.F1
OUT = os.path.join(F3.ROOT, "out", "출력", "오메가몬_PG", "소체_머리"); os.makedirs(OUT, exist_ok=True)
갑주D = os.path.join(F3.ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴6A")

# ════════ 손잡이(mm) — 갑주 바깥(돔 293 · 턱 261.5 · 폭 ±11)에서 갑주 두께 + 틈 ≈ 2 를 뺀 속 ════════
정수리, 턱z, 눈z = 290.5, 264.0, 277.5
반폭 = 8.8                       # 높이 26.5 × 0.66 / 2
앞y, 뒤y = -2.6, 17.0             # 얼굴 앞(눈 면) · 뒤통수 — 깊이 19.6 (0.74)
턱y = 0.4                        # 턱 끝은 이마보다 3 뒤(사람 옆얼굴: 턱선이 목으로 들어감)
목 = dict(r=4.6, y=8.5, 위=268.0, 아래=252.0)

cy, ry = (앞y + 뒤y) / 2, (뒤y - 앞y) / 2
두개 = M.Manifold.sphere(1.0, 64).scale([반폭, ry, 정수리 - 눈z]).translate([0, cy, 눈z])
윗 = 두개.trim_by_plane([0, 0, 1], 눈z - 3.0)                     # 눈 밑 3 까지는 타원체
_고리 = [(반폭 * np.cos(t) * 0.97, cy - ry * np.sin(t) * 0.97, 눈z - 3.0) for t in np.linspace(0, np.pi, 13)]   # 앞 반쪽 둘레
_뒤 = [(s * 반폭 * 0.8, cy + 3.0, z) for s in (1, -1) for z in (눈z - 3.0, 269.0)]
턱 = M.Manifold.hull_points(_고리 + _뒤 + [(s * 2.2, 턱y, 턱z) for s in (1, -1)] + [(s * 6.0, 턱y + 5.0, 턱z + 3.0) for s in (1, -1)])
뒤통수 = 두개.trim_by_plane([0, 0, -1], -(눈z - 3.0)).trim_by_plane([0, 1, 0], cy + 3.0).trim_by_plane([0, 0, 1], 270.0)
목기둥 = M.Manifold.cylinder(목["위"] - 목["아래"] + 6, 목["r"], 목["r"], 48).translate([0, 목["y"], 목["아래"]])
소체 = M.Manifold.batch_boolean([윗, 턱, 뒤통수, 목기둥], M.OpType.Add)
assert len(소체.decompose()) == 1
b = 소체.bounding_box(); print("소체 x ±%.1f · y %.1f~%.1f · z %.1f~%.1f" % (b[3], b[1], b[4], b[2], b[5]))

# 갑주(얼굴 6A)와 띄움: 갑주 안쪽이 소체를 파고들면 갑주가 틀린 것
파고듦 = {}
if os.path.isdir(갑주D):
    for n in ("투구앞", "마스크", "투구뒤"):
        f = os.path.join(갑주D, n + ".stl")
        if os.path.exists(f): 파고듦[n] = round((F1.읽기(f) ^ 소체).volume(), 1)
    print("갑주 6A 가 소체를 파고든 부피 mm³", 파고듦)

컷 = [("정면", 0, 0, 70.0, 280.0), ("옆", 90, 0, 70.0, 280.0), ("반옆", 62, 8, 70.0, 288.0)]
def 그림(이름, L):
    d = os.path.join(OUT, "_그림", 이름); os.makedirs(d, exist_ok=True); jf, pf = os.path.join(d, "빠른.json"), os.path.join(d, "빠른.py")
    json.dump(dict(부품=L, out=d.replace("\\", "/"), 컷=컷), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    open(pf, "w", encoding="utf-8").write(F3.빠른.replace("line_thickness = 1.6", "line_thickness = 1.0"))
    r = subprocess.run([F1.BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    return d

if __name__ == "__main__":
    from PIL import Image, ImageDraw, ImageFont
    f = os.path.join(OUT, "소체머리.stl"); 메(소체).export(f)
    눈 = [(os.path.join(갑주D, n + ".stl"), 색["초록"]) for n in ("눈L", "눈R")]
    a = 그림("소체", [(f, [0.35, 0.36, 0.40])] + 눈)
    # 갑주 앞 반만 걸친 그림: 오른쪽 반(x > 0)은 소체, 왼쪽 반은 갑주 → 두께 · 띄움이 보인다
    반 = M.Manifold.cube([40, 80, 80]).translate([-40, -30, 240])
    L = [(f, [0.35, 0.36, 0.40])] + 눈
    for n in ("투구앞", "마스크", "투구뒤", "속머리띠"):
        p = os.path.join(갑주D, n + ".stl")
        if os.path.exists(p):
            q = os.path.join(OUT, "_반_" + n + ".stl"); 메(F1.읽기(p) ^ 반).export(q); L.append((q, 색["검"] if n == "속머리띠" else 색["흰"]))
    c = 그림("반갑주", L)
    h = 520
    def 빠(d, k):
        im = Image.open(os.path.join(d, k + ".png")).convert("RGB"); w, H = im.size
        return im.crop((int(w * .2), int(H * .25), int(w * .8), int(H * .9)))
    줄 = [[("소체 정면", 빠(a, "정면")), ("소체 옆", 빠(a, "옆")), ("소체 3/4", 빠(a, "반옆"))],
          [("반쪽 갑주(6A) 정면", 빠(c, "정면")), ("반쪽 갑주 옆(갑주 쪽)", 빠(c, "옆")), ("반쪽 갑주 3/4", 빠(c, "반옆"))]]
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
    W = 10 + sum(int(im.width * h / im.height) + 10 for _, im in 줄[0])
    S = Image.new("RGB", (W, 2 * (h + 45) + 10), (245, 245, 243)); dr = ImageDraw.Draw(S); y = 45
    for 칸 in 줄:
        x = 10
        for t, im in 칸:
            im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS); S.paste(im, (x, y)); dr.text((x + 6, y - 36), t, font=ft, fill=(30, 30, 30)); x += im.width + 10
        y += h + 45
    p = os.path.join(멋, "소체머리.jpg"); S.save(p, quality=90); print("시트", p, S.size)
