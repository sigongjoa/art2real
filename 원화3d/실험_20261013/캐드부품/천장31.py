# 천장 — 정답 지도 · 정답 깊이를 덩어리 깊이로 지은 부피 IoU(같은 시험 앞 200) · 2.5D(위에서 파 들어가기) 표현이 낼 수 있는 최대 · 10-13
import json, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; Y = d["Y"][te]; D = d["D"][te].astype(np.float32); del d
    L = json.load(open(O + "목록.json", encoding="utf-8"))
    with Pool(2, maxtasksperchild=20) as pool: R = np.array(pool.map(J.부피IoU, [(L[te[j]], Y[j], D[j], True) for j in range(200)], chunksize=4))
    np.save(O + "부피IoU_천장31.npy", R); print("천장 %.3f · 0 점 %d · 바탕만(정답 윤곽) %.3f" % (R[:, 0].mean(), (R[:, 0] == 0).sum(), R[:, 1].mean()))
