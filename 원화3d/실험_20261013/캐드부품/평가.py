# 로드맵 2 평가만(학습.py 의 끝 단계가 메모리 상한에 걸려 따로) — 시험 1,003 예측 → 부피 IoU · 바탕만 · 일꾼 4 · 10-13
import json, numpy as np
from multiprocessing import Pool
import 짓기 as J, 학습 as T
O = "G:/art2real/out/설명/캐드부품/학습/"
if __name__ == "__main__":
    import torch
    d = np.load("G:/art2real/out/설명/캐드부품/데이터.npz"); 시 = d["시험"]; te = np.nonzero(시)[0][:200];   # 10-13 메모리로 두 번 멈춤 → 시험 앞 200 만(사용자 「ㄱㄱ」)
    X = d["X"][te].astype(np.float32); Y = d["Y"][te]; del d
    L = json.load(open("G:/art2real/out/설명/캐드부품/목록.json", encoding="utf-8"))
    m = T.U만들기()().cuda(); m.load_state_dict(torch.load(O + "망.pt")); m.eval(); P, Dp = [], []
    with torch.no_grad():
        for k in range(0, len(X), 64): lo, dp = m(torch.tensor(X[k:k + 64]).cuda()); P.append(lo.argmax(1).cpu().numpy().astype(np.uint8)); Dp.append(dp.cpu().numpy().astype(np.float16))
    P, Dp = np.concatenate(P), np.concatenate(Dp); del X, m; torch.cuda.empty_cache(); np.savez_compressed(O + "시험예측.npz", P=P, D=Dp)
    mi = float(np.mean([((P == c) & (Y == c)).sum() / max(((P == c) | (Y == c)).sum(), 1) for c in (1, 2, 3)]))
    with Pool(2, maxtasksperchild=20) as pool: R = np.array(pool.map(J.부피IoU, [(L[i], P[j], Dp[j].astype(np.float32)) for j, i in enumerate(te)], chunksize=4))
    결과 = {"부피IoU": float(R[:, 0].mean()), "바탕만": float(R[:, 1].mean()), "차": float((R[:, 0] - R[:, 1]).mean()), "화소mIoU": mi, "부품": len(te), "나아진비율": float((R[:, 0] > R[:, 1] + .01).mean()), "나빠진비율": float((R[:, 0] < R[:, 1] - .01).mean())}
    결과["통과"] = 결과["차"] >= .04 and mi >= .6; json.dump(결과, open(O + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); np.save(O + "부피IoU.npy", R)
    print("끝 · 시험 %d 부피 IoU %.3f · 바탕만 %.3f · 차 %+.3f · 나아짐 %.0f%% 나빠짐 %.0f%% · 화소 mIoU %.3f · 통과 %s" % (len(te), 결과["부피IoU"], 결과["바탕만"], 결과["차"], 100 * 결과["나아진비율"], 100 * 결과["나빠진비율"], mi, 결과["통과"]))
