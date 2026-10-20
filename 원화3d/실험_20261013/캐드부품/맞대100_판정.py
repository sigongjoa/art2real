# 판정기준96 재기 — 맞대100 R · R* · 판0 같은 시험 300: 층 맞음 · 속 깎임 층 맞음 · F@1 · 울퉁(평가69.하나)
import json, numpy as np
from multiprocessing import Pool
import 평가69 as E
O = "G:/art2real/out/설명/캐드부품/"; D = O + "맞대100/"
if __name__ == "__main__":
    부 = np.load(D + "부품.npy"); 층 = np.load(O + "층32.npy", mmap_mode="r"); 껍 = np.load(O + "껍질32.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r")
    z = dict(np.load(O + "데이터51.npz")); L = json.load(open(O + "목록.json", encoding="utf-8")); 판0 = np.load(O + "학습69_판0/예측.npy", mmap_mode="r"); 판부 = list(np.load(O + "학습69_판0/예측부품.npy"))
    팔 = {"R": np.load(D + "R.npy"), "R*": np.load(D + "R별.npy"), "판0": np.stack([판0[판부.index(i)] for i in 부])}; 결 = {}
    for n, P in 팔.items():
        a = np.zeros(4)
        for j, i in enumerate(부):
            g = 층[i].astype(int); s = 껍[i].astype(int); 안 = (입[i, :, 1] > 0) & (g < 32); 깎 = 안 & (g >= s + 2); p = P[j].astype(int)
            a += [안.sum(), ((p == g) & 안).sum(), 깎.sum(), ((p == g) & 깎).sum()]
        with Pool(4, maxtasksperchild=20) as pool: 출 = pool.map(E.하나, [(0, L[i], P[j], z["반"][i], z["틀"][i], z["정답"][i]) for j, i in enumerate(부)], chunksize=2)
        m = np.array([o[0] for o in 출], float); 결[n] = {"층 맞음": round(a[1] / a[0], 4), "속 깎임 층 맞음": round(a[3] / a[2], 4), "F@1": round(float(np.nanmean(m[:, 0])), 4), "IoU": round(float(np.nanmean(m[:, 1])), 4), "울퉁": round(float(np.nanmean(m[:, 2])), 4)}
        print(n, 결[n], flush=True)
    json.dump(결, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
