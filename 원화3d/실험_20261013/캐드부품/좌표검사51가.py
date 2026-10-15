# 학습51가 좌표 검사 — 채운 윤곽 셋을 학습51가.늘림 으로 48³ 에 포갠 「입력 껍질」이 정답 칸을 덮는가(정답 ⊂ 껍질 ≥ 0.95) · 축을 일부러 틀린 판과 나란히 · 10-15
# 사용(venv): 좌표검사51가.py [부품 수 20]
import sys, numpy as np, torch, torch.nn.functional as Fn
import 학습51가 as A
O = A.O; k = int(sys.argv[1]) if len(sys.argv) > 1 else 20
z = np.load(O + "데이터51.npz"); ok = z["ok"]; d = np.load(O + "데이터.npz"); X = d["X"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]
idx = np.nonzero(d["시험"] & ok)[0][:k]; 정 = A.풀기(z["정답"][idx]); 틀 = A.풀기(z["틀"][idx])
g = torch.tensor(A.그림들(X, F, S, idx)[:, :, 1]).float()   # 채운 윤곽 (B, 3, 128, 128)
줄 = lambda a: Fn.adaptive_max_pool2d(a[:, None], A.n)   # 128 → 48 · 조금이라도 채우면 1
빈 = 정.sum((1, 2, 3)) == 0; print("부품 %d · 정답 빈 부품 %d 개는 뺌(10-14 감사의 「빈」)" % (k, 빈.sum()))
def 덮음(껍): return ((껍 & 정).sum((1, 2, 3)) / np.maximum(정.sum((1, 2, 3)), 1))[~빈]
판 = {"맞는 축": A.늘림(줄(g[:, 0]), 줄(g[:, 1]), 줄(g[:, 2])),
      "뒤집기 없음": A.늘림(*(줄(g[:, i]).flip(2) for i in range(3))),
      "앞 ↔ 옆 바꿈": A.늘림(줄(g[:, 0]), 줄(g[:, 2]), 줄(g[:, 1]))}
for 이름, t in 판.items():
    껍 = (t > .5).all(1).numpy(); r = 덮음(껍); print("%-8s 정답 ⊂ 껍질 평균 %.3f · 최소 %.3f · 껍질 / 정답 칸 %.2f" % (이름, r.mean(), r.min(), 껍[~빈].sum() / max(정.sum(), 1)))
print("참고 · 정답 ⊂ 틀 평균 %.3f" % 덮음(틀).mean())
