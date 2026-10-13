# 쇼츠 57(샘플 · 다섯 칸) 재료 — 시험 0 플랜지 · 2a 모델 예측 · 덩어리 깊이로 깎은 것(판정기준31 ① 방식) EEVEE + 덩어리 지도 · 10-14
import json, subprocess, numpy as np, cv2, cadquery as cq
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"; A = "G:/art2real/out/설명/구멍/"; Z = "G:/art2real/out/영상05/대화/57_덩어리/자료/"
import os; os.makedirs(Z, exist_ok=True)
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0]; j = 0; X = d["X"][te[j]]; del d
p = np.load(O + "학습/시험예측.npz"); P, Dp = p["P"][j], p["D"][j].astype(np.float32); L = json.load(open(O + "목록.json", encoding="utf-8"))
v, f, H = J.정규메시(L[te[j]]); s = J.짓기(P, Dp, H, True); cq.exporters.export(s.val().scale(30), A + "r57_덩어리.stl", tolerance=.01, angularTolerance=.05)
n, lab = cv2.connectedComponents((P == 3).astype(np.uint8), connectivity=4); 깊 = np.zeros_like(Dp)
for i in range(1, n): m = lab == i; 깊[m] = np.median(Dp[m])
np.savez_compressed(Z + "지도.npz", X=X, P=P, Dp=Dp, 덩깊=깊, lab=lab)
층 = np.clip(np.round(np.where(P == 3, Dp, 0) / .1), 0, 10).astype(int); 층수 = sum(cv2.connectedComponents(((P == 3) & (층 == k)).astype(np.uint8), connectivity=4)[0] - 1 for k in range(1, 11))
print("들어감 덩어리(덩어리 깊이)", n - 1, "· 층으로 쪼갠 조각", 층수)
subprocess.run(["C:/Program Files/Blender Foundation/Blender 4.0/blender.exe", "-b", "-P", "G:/art2real/원화3d/실험_20261013/구멍/렌더_빛.py", "--", "57_덩어리"], check=True, stdout=subprocess.DEVNULL); print("ok")
