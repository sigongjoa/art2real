# 0 점 부품이 어느 단계에서 부서지나 — 정답 지도 · 2b · 단계별 예외 문구 · 10-13
import json, sys, traceback, numpy as np, cv2
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; Y = d["Y"][te]; D = d["D"][te].astype(np.float32); del d
B = np.load(O + "학습2b/시험예측.npz"); L = json.load(open(O + "목록.json", encoding="utf-8"))
Rc, Rb = np.load(O + "부피IoU_천장31.npy"), np.load(O + "부피IoU_31b.npy")
for 이름, R, YY, DD in (("정답", Rc, Y, D), ("2b", Rb, B["P"][:200], B["D"][:200].astype(np.float32))):
    for j in np.nonzero(R[:, 0] == 0)[0]:
        단 = "메시"
        try:
            v, f, H = J.정규메시(L[te[j]]); 단 = "윤곽"; ps = J.다각(YY[j] > 0); cs, _ = cv2.findContours((YY[j] > 0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            단 = "짓기"; s = J.짓기(YY[j], DD[j], H, True)
            if s is None: print(이름, j, "몸통 없음 · 윤곽 %d 개 중 남은 다각형 %d" % (len(cs), len(ps))); continue
            단 = "부피"; print(이름, j, "지어짐 · 물체 수", len(s.vals()), "· 고체 수", len(s.val().Solids()), "· 부피 %.4f" % s.val().Volume(), "· 점유", int(J.점유_캐드(s).sum()), "· 높이 H %.3f" % H)
        except Exception as e: print(이름, j, 단, "에서 예외:", type(e).__name__, str(e)[:100])
