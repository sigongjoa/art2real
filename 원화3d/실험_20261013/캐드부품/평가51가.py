# 판정기준51 (가) 평가 — 예측 칸 48³ 대 정답 칸(데이터51 「정답」 = 짓기.점유_메시) · 712 개(범위46) · 판정기준51 의 A · B · C · D · 대조는 결과52대조 · 10-15
# 사용(venv): 평가51가.py <이름>
import sys, json, numpy as np
from scipy.ndimage import label
O = "G:/art2real/out/설명/캐드부품/"; 이름 = sys.argv[1]; D = O + "학습51가_%s/" % 이름
z = np.load(O + "데이터51.npz"); 정, 틀 = z["정답"], z["틀"]; te = np.nonzero(np.load(O + "데이터.npz")["시험"])[0]; 범 = json.load(open(O + "범위46.json"))
P = np.load(D + "예측.npy"); 자 = {int(i): n for n, i in enumerate(np.load(D + "예측부품.npy"))}; 풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
r = lambda a, b: float((a & b).sum() / max((a | b).sum(), 1)); K = np.ones((3, 3, 3)); 줄 = []
for k in range(len(범)):
    i = int(te[범[k]]); g, t, p = 풀(정[i]), 풀(틀[i]), 풀(P[자[i]]); 줄.append((r(p, g), r(t, g), int(label(g, K)[1]), int(label(p, K)[1]), int(g.sum() == 0)))
a = np.array(줄); 칠천장 = np.load(O + "부피IoU_52대조.npy")[:, 1]; 낮 = 칠천장 < .5; 대 = json.load(open(O + "결과52대조.json", encoding="utf-8"))["42"]
결과 = {"부품": len(a), "가 평균": float(a[:, 0].mean()), "틀": float(a[:, 1].mean()), "대조 42 + 고친 짓기": 대["새"], "망침": int((a[:, 0] < a[:, 1] - .01).sum()), "크게망침": int((a[:, 0] < a[:, 1] - .1).sum()),
      "칠 천장 < 0.5 인 부품": int(낮.sum()), "그 부품 평균": float(a[낮, 0].mean()), "조각내기(정답 1 덩어리 → 여럿)": int(((a[:, 2] == 1) & (a[:, 3] > 1)).sum()), "빈 정답 뺀 평균": float(a[a[:, 4] == 0, 0].mean())}
결과["판정(첫 판 · 가)"] = {"A ≥ 0.683": 결과["가 평균"] >= .683, "B 망침 ≤ 213": 결과["망침"] <= 213, "C 168 ≥ 0.30": 결과["그 부품 평균"] >= .3}
np.save(D + "부피IoU.npy", a); json.dump(결과, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
