# 판정기준32 — 짓기 고친 뒤 같은 시험 앞 200 · 천장(정답 지도) · 2a+① · 2b+① · 고치기 전(31a · 31b · 천장31)과 부품별 비교 · 10-13
import json, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; Y = d["Y"][te]; D = d["D"][te].astype(np.float32); del d
    A = np.load(O + "학습/시험예측.npz"); B = np.load(O + "학습2b/시험예측.npz"); L = json.load(open(O + "목록.json", encoding="utf-8"))
    판 = {"천장": (Y, D, "부피IoU_천장31.npy"), "2a": (A["P"][:200], A["D"][:200].astype(np.float32), "부피IoU_31a.npy"), "2b": (B["P"][:200], B["D"][:200].astype(np.float32), "부피IoU_31b.npy")}; 결과 = {}
    with Pool(2, maxtasksperchild=20) as pool:
        for k, (YY, DD, 전) in 판.items():
            R = np.array(pool.map(J.부피IoU, [(L[te[j]], YY[j], DD[j], True) for j in range(200)], chunksize=4)); np.save(O + "부피IoU_32_%s.npy" % k, R); R0 = np.load(O + 전)
            같 = (R0[:, 0] > 0) & (R[:, 0] > 0); 결과[k] = {"부피IoU": float(R[:, 0].mean()), "전": float(R0[:, 0].mean()), "0점": int((R[:, 0] == 0).sum()), "0점_전": int((R0[:, 0] == 0).sum()), "나머지_최대변화": float(np.abs(R[같, 0] - R0[같, 0]).max())}
            print(k, 결과[k], flush=True)
    결과["통과"] = 결과["천장"]["0점"] <= 1 and 결과["2b"]["0점"] <= 3 and 결과["천장"]["부피IoU"] >= .654 and max(결과[k]["나머지_최대변화"] for k in 판) <= .005
    json.dump(결과, open(O + "결과32.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과["통과"])
