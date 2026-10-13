# ② 실패 가르기 — 2b 가 크게 진 부품: 0 점(짓기 · 채점 예외)인지 · 모양이 실제로 나쁜지 · 10-13
import json, traceback, numpy as np
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; del d
A = np.load(O + "학습/시험예측.npz"); B = np.load(O + "학습2b/시험예측.npz"); L = json.load(open(O + "목록.json", encoding="utf-8"))
Ra, Rb = np.load(O + "부피IoU_31a.npy"), np.load(O + "부피IoU_31b.npy")
영 = (Ra[:, 0] == 0) | (Rb[:, 0] == 0); print("둘 중 하나라도 0 점:", 영.sum(), "· 그것 빼면 2a %.3f 2b %.3f (%d 개)" % (Ra[~영, 0].mean(), Rb[~영, 0].mean(), (~영).sum()))
for j in np.nonzero(Rb[:, 0] == 0)[0]:
    try:
        v, f, H = J.정규메시(L[te[j]]); s = J.짓기(B["P"][j], B["D"][j].astype(np.float32), H, True)
        if s is None: print(j, "몸통 없음(윤곽 버림)"); continue
        q = J.점유_캐드(s); print(j, "지어짐 · 부피 칸", int(q.sum()), "· 2a %.2f" % Ra[j, 0])
    except Exception as e: print(j, "예외:", type(e).__name__, str(e)[:80], "· 2a %.2f" % Ra[j, 0])
