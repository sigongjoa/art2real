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

# ════════ 손잡이(mm) — 2 판: 원화식 과장(좁은 두개 · 긴 얼굴 · 뾰족한 V 턱 · 눈두덩 밑 깊은 눈) ════════
Pn = np.asarray(F3.F2.Pn, float); print("목 끄덕 축(기존 관절)", np.round(Pn, 2))
정수리, 턱z, 눈z = 290.5, 262.0, 277.3
반폭 = 8.0                       # 사람 비율 9.4(높이 28.5 × 0.66 / 2) 보다 좁게
앞y, 뒤y = -2.0, 26.0          # 기존 목 관절(y 21.4)이 뒤통수 안에 오게 — 깊이 28 (사람 0.85 보다 긴 1.0 · 투구형)
눈두덩y, 코y, 턱y = -3.6, -3.2, 0.2   # 옆얼굴: 눈두덩이 가장 앞 → 눈은 1.6 들어감 → 코 → 턱 끝은 3.8 뒤(사선)
목 = dict(r=4.4, y=float(Pn[1]), 위=273.0, 아래=255.0)

cy, ry = (앞y + 뒤y) / 2, (뒤y - 앞y) / 2
def 짝(P): return list(P) + [(-x, y, z) for x, y, z in P if x]
두개 = M.Manifold.sphere(1.0, 64).scale([반폭, ry, 정수리 - 눈z + 2.0]).translate([0, cy, 눈z - 2.0]).trim_by_plane([0, 0, 1], 눈z + 1.6)
눈두덩 = M.Manifold.hull_points(짝([(0, 눈두덩y, 279.4), (5.0, 눈두덩y + 0.9, 280.6), (7.8, 앞y + 3.0, 280.0), (0, 앞y + 1.0, 284.0), (7.0, 앞y + 4.0, 283.0), (0, 앞y + 4.0, 278.9), (7.8, 앞y + 5.0, 278.9)]))
# 얼굴: 눈 면(들어감) → 광대 → 턱 모서리 → 뾰족한 턱 끝. 앞면은 코에서 턱 끝으로 뒤로 누움
얼굴 = M.Manifold.hull_points(짝([(0, 앞y, 눈z + 1.7), (7.6, 앞y + 3.2, 눈z + 1.7), (0, 코y, 274.2), (7.7, 앞y + 3.6, 274.0),      # 눈 면 · 광대
                                 (5.2, 턱y + 2.6, 267.4), (1.1, 턱y, 턱z), (4.6, 턱y + 7.0, 266.6),                                 # 턱선 · 턱 끝
                                 (7.6, cy + 1.0, 눈z + 1.7), (7.4, cy + 1.0, 271.0), (4.4, cy + 1.0, 266.8)]))                       # 귀 앞(뒤 경계)
뒤통수 = M.Manifold.sphere(1.0, 64).scale([반폭, ry, 정수리 - 눈z + 2.0]).translate([0, cy, 눈z - 2.0]).trim_by_plane([0, 1, 0], cy).trim_by_plane([0, 0, 1], 269.0)
목기둥 = M.Manifold.cylinder(목["위"] - 목["아래"], 목["r"], 목["r"] * 0.9, 48).translate([0, 목["y"], 목["아래"]])
소체 = M.Manifold.batch_boolean([두개, 눈두덩, 얼굴, 뒤통수, 목기둥], M.OpType.Add)
assert len(소체.decompose()) == 1
def 눈알(s):   # 소체에 붙은 눈: 눈 면 위 가로 타원 5.2 × 2.4 · 바깥이 올라감 18°
    from scipy.spatial.transform import Rotation as Rot
    e = M.Manifold.cylinder(0.8, 1.0, 1.0, 48).scale([2.6, 1.2, 1.0]).rotate([90, 0, 0])
    x = 4.0; return e.rotate([0, -s * 18.0, 0]).rotate([0, 0, s * 22.0]).translate([s * x, 앞y + 0.42 * x + 0.1, 눈z])
눈L, 눈R = 눈알(-1), 눈알(1)
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
    눈 = []
    for n, m in (("소체눈L", 눈L), ("소체눈R", 눈R)): q = os.path.join(OUT, n + ".stl"); 메(m).export(q); 눈.append((q, 색["초록"]))
    a = 그림("소체", [(f, [0.30, 0.31, 0.35])] + 눈)
    h = 520
    def 빠(d, k):
        im = Image.open(os.path.join(d, k + ".png")).convert("RGB"); w, H = im.size
        return im.crop((int(w * .2), int(H * .25), int(w * .8), int(H * .9)))
    참 = [Image.open(os.path.join(멋, "원화_얼굴_확대.png")).convert("RGB").crop((230, 60, 700, 660)),
          Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT).crop((100, 120, 400, 400)), Image.open(os.path.join(FRA, "mh_12.jpg")).crop((60, 0, 390, 450))]
    줄 = [[("소체 정면", 빠(a, "정면")), ("소체 옆", 빠(a, "옆")), ("소체 3/4", 빠(a, "반옆"))],
          [("원화", 참[0]), ("FRA 옆(뒤집음)", 참[1]), ("FRA 정면", 참[2])]]
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
    W = 10 + sum(int(im.width * h / im.height) + 10 for _, im in 줄[0])
    S = Image.new("RGB", (W, 2 * (h + 45) + 10), (245, 245, 243)); dr = ImageDraw.Draw(S); y = 45
    for 칸 in 줄:
        x = 10
        for t, im in 칸:
            im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS); S.paste(im, (x, y)); dr.text((x + 6, y - 36), t, font=ft, fill=(30, 30, 30)); x += im.width + 10
        y += h + 45
    p = os.path.join(멋, "소체머리.jpg"); S.save(p, quality=90); print("시트", p, S.size)


