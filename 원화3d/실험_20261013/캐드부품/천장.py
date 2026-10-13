# 로드맵 2 천장 — 정답 지도를 그대로 지으면 부피 IoU 얼마 · 바탕만(윤곽 밀기) 얼마 · 시험 부품 앞 50 · 10-13
import json, time, numpy as np
from multiprocessing import Pool
import 짓기 as J
if __name__ == "__main__":
    d = np.load("G:/art2real/out/설명/캐드부품/데이터.npz"); L = json.load(open("G:/art2real/out/설명/캐드부품/목록.json", encoding="utf-8")); Y, D = d["Y"], d["D"]; idx = np.nonzero(d["시험"])[0][:50]; t = time.time()   # npz 는 꺼낼 때마다 다시 풂 → 한 번만
    with Pool(6) as p: R = np.array(p.map(J.부피IoU, [(L[i], Y[i], D[i].astype(np.float32)) for i in idx]))
    json.dump({"천장": float(R[:, 0].mean()), "바탕만": float(R[:, 1].mean()), "부품": len(idx)}, open("G:/art2real/out/설명/캐드부품/천장.json", "w"))
    print("천장(정답 지도 → CAD) 부피 IoU %.3f · 바탕만 %.3f · 차 %+.3f · 0 인 것 %d · %.0f 초" % (R[:, 0].mean(), R[:, 1].mean(), (R[:, 0] - R[:, 1]).mean(), (R[:, 0] == 0).sum(), time.time() - t))
