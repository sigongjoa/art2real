# 끄트러기 원인 가르기(systematic-debugging) — 종류 지도 · 깊이 지도를 정답/모델로 바꿔 끼움 · 고치지 않고 잰다 · 10-13
# A 정답 · 정답 | B 모델 종류 · 정답 깊이 | C 정답 종류 · 모델 깊이 | D 모델 · 모델(지금)
# 잰 것: 깎은 덩어리 수(시험 200 전부 · CAD 안 지음) · 20 화소 미만 조각 수 · 부피 IoU(앞 60 · CAD 지음)
import json, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
def 덩어리(Y, D):
    import cv2
    층 = np.clip(np.round(np.where(Y == 3, D, 0) / .1), 0, 10).astype(int); 개, 작 = 0, 0
    for m in [(Y == 3) & (층 == k) for k in range(1, 11)] + [Y == 2]:
        n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=4)
        for i in range(1, n):
            if st[i, 4] >= 3: 개 += 1; 작 += st[i, 4] < 20
    return 개, 작
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; Yg = d["Y"][te]; Dg = d["D"][te].astype(np.float32); del d
    p = np.load(O + "학습/시험예측.npz"); P, Dp = p["P"][:200], p["D"][:200].astype(np.float32); L = json.load(open(O + "목록.json", encoding="utf-8"))
    판 = {"A 정답·정답": (Yg, Dg), "B 모델종류·정답깊이": (P, Dg), "C 정답종류·모델깊이": (Yg, Dp), "D 모델·모델": (P, Dp)}
    결과 = {}
    for 이름, (Y, D) in 판.items():
        c = np.array([덩어리(Y[j], D[j]) for j in range(200)]); 결과[이름] = {"덩어리_중앙": float(np.median(c[:, 0])), "작은조각_중앙": float(np.median(c[:, 1])), "작은조각_평균": float(c[:, 1].mean())}
    with Pool(2, maxtasksperchild=20) as pool:
        for 이름, (Y, D) in 판.items():
            R = np.array(pool.map(J.부피IoU, [(L[te[j]], Y[j], D[j]) for j in range(60)], chunksize=3)); 결과[이름]["부피IoU_60"] = float(R[:, 0].mean()); 결과[이름]["바탕만_60"] = float(R[:, 1].mean())
            print(이름, 결과[이름], flush=True)
    json.dump(결과, open(O + "진단_끄트러기.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
