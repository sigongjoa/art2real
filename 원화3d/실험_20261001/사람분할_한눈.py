# -*- coding: utf-8 -*-
"""받은 사람 분할 모델을 받은 그대로(부품 색 다르게) 정면 · 위 두 방향 그림 — 「조립 위치로 저장됐나」는 숫자 말고 눈으로 (2026-10-05)"""
import os, glob, json, colorsys, numpy as np, trimesh, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
plt.rcParams["font.family"] = "Malgun Gothic"
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; ds = sorted(glob.glob(R + "*/"))
fig, axs = plt.subplots(len(ds), 2, figsize=(10, 4.2 * len(ds)))
rng = np.random.default_rng(0)
for r, d in enumerate(ds):
    fs = [f for f in glob.glob(d + "**/*", recursive=True) if f.lower().endswith((".stl", ".obj"))][:120]
    ps = []
    for i, f in enumerate(fs):
        try:
            m = trimesh.load(f, force="mesh")
            if not len(m.faces): continue
            k = min(len(m.faces), 4000); idx = rng.choice(len(m.faces), k, replace=False)
            ps.append((m.triangles[idx], m.face_normals[idx], colorsys.hsv_to_rgb((i * 0.618) % 1, 0.65, 0.95)))
        except Exception: pass
    for c, (a, b) in enumerate(((0, 2), (0, 1))):
        ax = axs[r, c]
        for T, N, col in ps:
            sh = 0.35 + 0.65 * np.clip(np.abs(N[:, 3 - a - b]), 0, 1)
            ax.add_collection(PolyCollection(T[:, :, [a, b]], facecolors=np.array(col)[None] * sh[:, None], edgecolors="none"))
        ax.autoscale(); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(f"{os.path.basename(d[:-1])} · {len(ps)} 부품 · {'정면(x,z)' if c == 0 else '위(x,y)'}", fontsize=10)
fig.tight_layout(); fig.savefig(R + "한눈.png", dpi=55)
