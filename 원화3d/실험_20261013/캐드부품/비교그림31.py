# 판정기준31 ② 보고 그림 — 같은 부품을 정답 · 2a(위 한 장)+① · 2b(위 · 앞 · 옆)+① 로 지어 EEVEE · 2b 가 크게 이긴 둘 · 크게 진 둘 · 10-13
import json, subprocess, numpy as np, trimesh, cadquery as cq
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"; A = "G:/art2real/out/설명/구멍/"; K = 30; 고른 = [171, 120, 3, 142]
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; X = d["X"][te]; del d
pa, pb = np.load(O + "학습/시험예측.npz"), np.load(O + "학습2b/시험예측.npz"); L = json.load(open(O + "목록.json", encoding="utf-8")); 이름 = []
for j in 고른:
    v, f, H = J.정규메시(L[te[j]]); trimesh.Trimesh(v * K, f).export(A + "r31_%d_정답.stl" % j); 이름.append("31_%d_정답" % j)
    for t, p in (("2a", pa), ("2b", pb)):
        s = J.짓기(p["P"][j], p["D"][j].astype(np.float32), H, True)
        cq.exporters.export(s.val().scale(K), A + "r31_%d_%s.stl" % (j, t), tolerance=.01, angularTolerance=.05); 이름.append("31_%d_%s" % (j, t))
np.save(O + "비교31_입력.npy", X[고른])
subprocess.run(["C:/Program Files/Blender Foundation/Blender 4.0/blender.exe", "-b", "-P", "G:/art2real/원화3d/실험_20261013/구멍/렌더_빛.py", "--"] + 이름, check=True, stdout=subprocess.DEVNULL); print("ok")
