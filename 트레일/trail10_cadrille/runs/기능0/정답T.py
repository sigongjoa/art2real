# -*- coding: utf-8 -*-
"""기능0 학습 정답 — 통과된 짓기 방식을 깊이 그림 위에서 그대로: 교차 깊이에서 시작 → 큰 홈(실물 − 교차 > 3 칸 · 150 칸 이상)은 평평한 바닥 하나 →
선 고리 중 안쪽이 고르고(IQR ≤ 3 칸) 0.8 칸 넘게 다르면 그 깊이 하나 · 나머지는 교차 그대로 (= 학생이 맞힐 「정리된 깊이」) · 10-11
python runs/기능0/정답T.py 학습|시험  →  깊이학습/정답T_학습.npy (n,6,N,N) f16"""
import os, sys, numpy as np, cv2
from scipy import ndimage
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); n = 128
def 정리(S, L, Dh, D):
    T = Dh.copy(); s = S > .5
    lab, nl = ndimage.label(s & (D - Dh > 3 / n))
    for j in range(1, nl + 1):
        c = lab == j
        if c.sum() >= 150: T[c] = np.median(D[c])
    안 = (s & (L < .5)).astype(np.uint8); nn_, lb = cv2.connectedComponents(안, connectivity=4)
    for j in range(1, nn_):
        m = cv2.dilate((lb == j).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & s
        if m.sum() < 6 or m.sum() > .4 * s.sum(): continue
        d = D[m]
        if np.percentile(d, 75) - np.percentile(d, 25) > 3 / n: continue
        if abs(np.median(d) - np.median(T[m])) >= .8 / n: T[m] = np.median(d)
    return np.where(s, np.maximum(T, Dh), 1.0)   # 교차보다 앞으로는 못 나옴(실루엣 안)
if __name__ == "__main__":
    판 = sys.argv[1]; XP = os.path.join(R, "깊이학습", "학습.npy" if 판 == "학습" else "시험.npz")
    X = np.load(XP, mmap_mode="r") if 판 == "학습" else np.load(XP)["X"]; out = np.zeros((len(X), 6, n, n), np.float16)
    for i in range(len(X)):
        x = np.asarray(X[i]).astype(np.float32)
        for k in range(6): out[i, k] = 정리(x[0, k], x[1, k], x[2, k], x[3, k])
        if i % 200 == 0: print(i, flush=True)
    np.save(os.path.join(R, "깊이학습", "정답T_%s.npy" % 판), out); print("ok", out.shape)
