# 코드 결과 단면: python _단면코드.py idx code.py → _단면코드NN.png
import sys, os, numpy as np, trimesh, cadquery as cq, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
i = int(sys.argv[1]); sp = "G:/art2real/트레일/trail10_cadrille/runs/윤곽0/결과/%02d_교차.step" % i
ns = {"cq": cq, "바탕": cq.importers.importStep(sp) if os.path.exists(sp) else None}
exec(open(sys.argv[2], encoding="utf-8").read(), ns); p = os.path.join(os.environ.get("TEMP", "."), "_sc.stl")
cq.exporters.export(ns["r"], p, tolerance=0.1); m = trimesh.load(p); print("bounds", m.bounds.round(1).tolist())
fr = [15, 30, 50, 70, 85]; fig, ax = plt.subplots(3, 5, figsize=(16, 9.6))
for a in range(3):
    for j, f in enumerate(fr):
        n = np.zeros(3); n[a] = 1; o = np.full(3, 50.); o[a] = f; s = m.section(plane_origin=o, plane_normal=n); A = ax[a, j]; uv = [k for k in range(3) if k != a]
        if s is not None:
            for e in s.discrete: A.plot(e[:, uv[0]], e[:, uv[1]], "r-", lw=.8)
        A.set_xlim(0, 100); A.set_ylim(0, 100); A.set_aspect("equal"); A.grid(alpha=.4); A.set_title("%s=%g" % ("xyz"[a], f), fontsize=9)
plt.tight_layout(); plt.savefig(os.path.dirname(os.path.abspath(__file__)) + "/_단면코드%02d.png" % i, dpi=60)
