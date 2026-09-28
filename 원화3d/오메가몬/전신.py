# -*- coding: utf-8 -*-
"""오메가몬 PG — 부위별 마지막 단계를 한 몸으로 모아 원화 옆에 (2026-09-28).

    python 전신.py  -> out/오메가몬2/전신.png
부위 스크립트가 낸 out/오메가몬2/<부위>/단계4/*.stl + 색.json 을 읽는다. 다리는 그림 오른쪽 것을 거울로 왼쪽에도.
아직 없는 것: 아래팔(그레이 · 가루루 머리 · 칼 · 포) · 망토.
"""
import os, json, subprocess
import numpy as np, manifold3d as M, trimesh
from 공통 import OUT, X, Z, k, 원화그림, 블, BLENDER, stl

부위 = [("머리", False, ()), ("몸통", False, ()), ("어깨", False, ()), ("방패", False, ()),
        ("허벅지", True, ()), ("정강이", True, ("허벅지끝",)), ("발", True, ())]          # (이름, 거울로 반대쪽에도, 뺄 부품)
def 읽기(f):
    t = trimesh.load(f); return M.Manifold(M.Mesh(np.asarray(t.vertices, np.float32), np.asarray(t.faces, np.uint32)))

if __name__ == "__main__":
    from PIL import Image, ImageDraw, ImageFont
    묶음 = {}; 수 = 0
    for 이름, 거울, 뺌 in 부위:
        D = os.path.join(OUT, 이름, "단계4"); 색 = json.load(open(os.path.join(D, "색.json"), encoding="utf-8"))
        for n, c in 색.items():
            if n in 뺌: continue
            t = trimesh.load(os.path.join(D, n + ".stl")); 수 += 1 + 거울
            묶음.setdefault(tuple(c), []).append(t)
            if 거울: m = t.copy(); m.apply_scale([-1, 1, 1]); m.invert(); 묶음[tuple(c)].append(m)
    T = os.path.join(OUT, "_전신"); os.makedirs(T, exist_ok=True); 판 = []; 폭 = 1024 * k; c = np.array((0.0, 0.0, Z(512)))
    for 각, 보기 in ((0, "정면"), (35, "반옆"), (90, "옆")):
        L = []
        for i, (색, ts) in enumerate(묶음.items()):
            m = trimesh.util.concatenate(ts).copy(); m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(각), [0, 0, 1])); f = os.path.join(T, "%s_%d.stl" % (보기, i)); m.export(f); L.append((f, list(색)))
        판.append(dict(부품=L, 폭=폭, 해상=(1024, 1024), 중심=list(map(float, c)), out=os.path.join(T, 보기 + ".png")))
    jf = os.path.join(T, "판.json"); json.dump(dict(판=판), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    pf = os.path.join(T, "블.py"); open(pf, "w", encoding="utf-8").write(블.replace("line_thickness = 1.0", "line_thickness = 0.7")      # 굵은 선은 눈 같은 작은 부품을 덮는다)
    r = subprocess.run([BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    원 = 원화그림().transform((1024, 1024), Image.AFFINE, (1, 0, 537 - 512, 0, 1, 0), fillcolor=(255, 255, 255))
    im = {n: Image.open(os.path.join(T, n + ".png")).convert("RGB") for n in ("정면", "반옆", "옆")}
    칸 = [("원화", 원), ("전신 정면 (부품 %d · 아래팔 · 망토 없음)" % 수, im["정면"]), ("원화 + 전신 겹침", Image.blend(원, im["정면"], 0.5)), ("3/4", im["반옆"]), ("옆", im["옆"])]
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 30); S = Image.new("RGB", (3 * 1034 + 10, 2 * 1090 + 10), (245, 245, 243)); d = ImageDraw.Draw(S)
    for i, (t, g) in enumerate(칸):
        x, y = 10 + (i % 3) * 1034, 10 + (i // 3) * 1090; S.paste(g, (x, y + 56)); d.text((x + 6, y + 8), t, font=ft, fill=(20, 20, 20))
    p = os.path.join(OUT, "전신.png"); S.save(p); print("부품", 수); print("시트", p, S.size)
