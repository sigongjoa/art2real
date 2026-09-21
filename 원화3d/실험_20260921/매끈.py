# -*- coding: utf-8 -*-
"""**깊이 방향으로만 편다** — 앞 · 뒤 실루엣을 한 화소도 안 건드리는 스무딩 (2026-09-21).

    python 매끈.py [케이스=오메가몬]   -> out/결과물/<케이스>/매끈_<세기>.ply · out/매끈_<케이스>.png

사용자(09-21): 「좋은 부분은 shape 정보는 어느 정도 한단 말이야. 그런데 **울퉁불퉁한 것만** 어떻게 하면 좋겠는데?」

울퉁불퉁의 정체는 **깊이(y)가 높이마다 들쭉날쭉한 것**이다 — 높이마다 단면 타원을 따로 풀어서다.
09-11 에 3D 가우시안 스무딩(`SMOOTH_OUT`)은 껐다: 칼끝 · 가시를 먹어 못덮음이 4.07 → 7.45% 가 됐다.

여기서는 **정점의 y 좌표만** 편다 (Taubin λ/μ · 메시 라플라시안). x · z 를 안 건드리니
**앞 · 뒤 실루엣은 구조적으로 그대로**다. 바뀔 수 있는 것은 옆 실루엣뿐이라 그것만 잰다.
"""
import os
import subprocess
import sys

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import 결과물 as RS
import 세우기 as SE
H, W = RS.H, RS.W
HERE = RS.HERE
세기들 = (("약", 30), ("중", 120), ("강", 400))
LAM, MU = 0.5, -0.53


def y만펴기(m, it):
    L = trimesh.smoothing.laplacian_calculation(m, equal_weight=True)     # 이웃 평균 (희소 행렬)
    V = np.asarray(m.vertices, float).copy()
    y = V[:, 1].copy()
    for _ in range(it):
        y = y + LAM * (L @ y - y)
        y = y + MU * (L @ y - y)                                           # Taubin — 쪼그라들지 않게
    V[:, 1] = y
    return trimesh.Trimesh(V, np.asarray(m.faces), process=False)


def main(case="오메가몬"):
    from PIL import Image
    d = os.path.join(HERE, "out", "결과물", case)
    src = os.path.join(d, "결과.ply")
    if not os.path.exists(src):
        RS.main(case)
    m = trimesh.load(src, force="mesh", process=False)
    _, masks, p, bs, raw = SE.껍질(case)
    print("  못덮음 앞·옆·뒤   원본 %s" % SE.못덮음(m, masks, bs), flush=True)
    open(RS.렌더py, "w", encoding="utf-8").write(RS.렌더소스)
    tags = [("결과", "결과.ply")]
    for 이름, it in 세기들:
        s = y만펴기(m, it)
        f = "매끈_%s.ply" % 이름
        s.export(os.path.join(d, f))
        print("  %-2s (%3d 회)      %s · 닫힘 %s" % (이름, it, SE.못덮음(s, masks, bs), s.is_watertight), flush=True)
        tags.append(("매끈" + 이름, f))
    for tag, f in tags:
        subprocess.run([RS.BLENDER, "-b", "--python", RS.렌더py, "--", os.path.join(d, f), d, tag],
                       capture_output=True, timeout=1500)
    rows = []
    for tag, _ in tags:
        rows.append([Image.open(os.path.join(d, "렌더_%s_%s.png" % (tag, n))).convert("RGB").resize((600, 600))
                     for n in ("앞", "사선", "옆", "뒤")])
    sheet = Image.new("RGB", (4 * 610 - 10, len(rows) * 610 - 10), "white")
    for i, ims in enumerate(rows):
        for j, im in enumerate(ims):
            sheet.paste(im, (j * 610, i * 610))
    out = os.path.join(HERE, "out", "매끈_%s.png" % case)
    sheet.save(out)
    print("  ->", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")
