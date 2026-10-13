# 쇼츠 54 재료 — 1d 스냅의 지켜볼 6 × 에폭(0 · 1 · 2 · 4 · 10 · 20) 지도 → 다각형 깎기 STL → EEVEE · 정답 렌더 · 10-13
import os, sys, json, subprocess, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 캐드점수2 as K, 학습3 as T, 학습4 as U
A = "G:/art2real/out/설명/구멍/"; L = A + "학습4/"; 에 = [0, 1, 2, 4, 10, 20]
if __name__ == "__main__":
    import cadquery as cq
    S = json.load(open(L + "스냅.json", encoding="utf-8")); 이름 = []
    for e in 에:
        for k, w in enumerate(S["스냅"][e]["지켜볼"]):
            지도 = (np.asarray(Image.open(L + "지도_e%02d_%d.png" % (e, k))) // 120).astype(np.uint8); 바 = w["바탕"]; 바 = (바[0], [tuple(p) for p in 바[1]]) if 바[0] == "다각" else tuple(바)
            n = "54_e%02d_%d" % (e, k); cq.exporters.export(U.다각깎기(바, 지도), A + "r%s.stl" % n, tolerance=0.01, angularTolerance=0.05); 이름.append(n)
    for k, p in enumerate(S["정답"]): n = "54_정답_%d" % k; cq.exporters.export(K.짓기(p), A + "r%s.stl" % n, tolerance=0.01, angularTolerance=0.05); 이름.append(n)
    for i in range(0, len(이름), 22): subprocess.run(["C:/Program Files/Blender Foundation/Blender 4.0/blender.exe", "-b", "-P", "렌더_빛.py", "--"] + 이름[i:i + 22], check=True, stdout=subprocess.DEVNULL)
    print("ok", len(이름))
