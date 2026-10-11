# 둥근 학습 정답 — 부품마다 둥근 찾기(깊이 꺾임 선) → 방향별 칸 지도 0 없음 · 1 공 · 2 소켓 · 3 볼록 원기둥 · 4 오목 원기둥 · 10-11
# python runs/기능0/둥근라벨.py 학습|시험  →  깊이학습/둥근라벨_<판>.npy (n,6,N,N) uint8
import os, sys, numpy as np
import 둥근찾기 as G
from 도구 import R
판 = sys.argv[1]; XP = os.path.join(R, "깊이학습", "학습.npy" if 판 == "학습" else "시험.npz")
X = np.load(XP, mmap_mode="r") if 판 == "학습" else np.load(XP)["X"]; out = np.zeros((len(X), 6, 128, 128), np.uint8)
for i in range(len(X)):
    x = np.asarray(X[i]).astype(np.float32)
    try: _, 낱 = G.찾기(i, x, 깊선=True)
    except Exception as e: print(i, "실패", str(e)[:50]); continue
    for f in 낱: out[i, f["쪽"]][f["_m"]] = (1 if not f["오목"] else 2) if f["종류"] == "구" else (3 if not f["오목"] else 4)
    if i % 200 == 0: print(i, flush=True)
np.save(os.path.join(R, "깊이학습", "둥근라벨_%s.npy" % 판), out); print("ok", (out > 0).mean())
