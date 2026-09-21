# -*- coding: utf-8 -*-
"""**장에서 높이 방향으로만 편다** (2026-09-21) — `매끈.py`(정점 y 만 펴기)가 눈에 띄게 못 고쳐서 원인 쪽으로 갔다.

    python 매끈장.py [케이스=오메가몬] [격자=384]   -> out/결과물/<케이스>/장매끈_*.ply · out/매끈장_<케이스>.png

울퉁불퉁 = 타원 장 g 가 **높이(z)마다 따로 풀려** z 방향으로 뚝뚝 끊기는 것. 그래서 g 를 **z 로만** 가우시안으로 편다.
    g' = min( max( smooth_z(g, σ), g − δ ), f )
      · max(…, g − δ)  어디서도 표면이 δ 칸 넘게 물러나지 않는다 — 가는 것(칼끝 · 가시)이 안 먹힌다
      · min(…, f)      f = 이진 hull 의 연속 장. **실루엣 밖으로는 못 나간다** (hull 은 상한)
"""
import os, subprocess, sys
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np, trimesh
from scipy import ndimage
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import 결과물 as RS, 세우기 as SE, 장타원 as JT, 연속hull as CH
H, W, HERE = RS.H, RS.W, RS.HERE
판본 = (("원본", 0.0), ("σ2", 2.0), ("σ4", 4.0), ("σ8", 8.0))
DELTA = 1.0


def main(case="오메가몬", N=384):
    from PIL import Image
    d = os.path.join(HERE, "out", "결과물", case); os.makedirs(d, exist_ok=True)
    _, masks, p, bs, raw = SE.껍질(case)
    g, ax = JT.타원장(masks, bs, N=N)
    f, _ = CH.연속장(masks, bs, N=N)
    f = f / ((W.U1 - W.U0) / N)
    open(RS.렌더py, "w", encoding="utf-8").write(RS.렌더소스)
    tags = []
    for 이름, s in 판본:
        gg = g if s == 0 else np.minimum(np.maximum(ndimage.gaussian_filter1d(g, s, axis=2), g - DELTA), f)
        m = RS.큰덩어리(JT.메시(gg, ax))
        fn = "장매끈_%s.ply" % 이름
        m.export(os.path.join(d, fn))
        print("  %-3s 못덮음 앞·옆·뒤 %s · 면 %d · 닫힘 %s" % (이름, SE.못덮음(m, masks, bs), len(m.faces), m.is_watertight), flush=True)
        tag = "장" + 이름
        subprocess.run([RS.BLENDER, "-b", "--python", RS.렌더py, "--", os.path.join(d, fn), d, tag], capture_output=True, timeout=1500)
        tags.append(tag)
    rows = [[Image.open(os.path.join(d, "렌더_%s_%s.png" % (t, n))).convert("RGB").resize((600, 600)) for n in ("앞", "사선", "옆", "뒤")] for t in tags]
    sheet = Image.new("RGB", (4 * 610 - 10, len(rows) * 610 - 10), "white")
    for i, ims in enumerate(rows):
        for j, im in enumerate(ims):
            sheet.paste(im, (j * 610, i * 610))
    out = os.path.join(HERE, "out", "매끈장_%s.png" % case); sheet.save(out); print("  ->", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬", int(sys.argv[2]) if len(sys.argv) > 2 else 384)
