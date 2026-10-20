# 판정기준106 채점 — 학습69_<이름> 망으로 시험 300 · 학습 300: 층 맞음(정확 · ±1) · 깎인 속(정확 · ±1) · 판0 과 같은 자(손실103.손실 의 입력 · 예측) · 10-20
# 사용(venv · ART_MEM_GB=10): 판정106.py <이름> [<이름> ...] → out/설명/캐드부품/학습69_<이름>/판정106.json
import sys, json, numpy as np, torch, 손실103 as L
K = 32
for 이름 in sys.argv[1:]:
    L.m.load_state_dict(torch.load(L.O + f"학습69_{이름}/망.pt")); L.m.eval(); 결 = {}
    for 꼴, 부품 in (("시험", L.부[L.시][:300]), ("학습", L.tr[:300])):
        a = np.zeros(6)
        for i in 부품:
            _, p = L.손실(i); g = np.array(L.층[i]).astype(int); s = np.array(L.껍32[i]).astype(int); 안 = (np.array(L.입[i][:, 1]) > 0) & (g < K); 깎 = 안 & (g >= s + 2); e = np.abs(p.astype(int) - g)
            a += [안.sum(), (안 & (e == 0)).sum(), (안 & (e <= 1)).sum(), 깎.sum(), (깎 & (e == 0)).sum(), (깎 & (e <= 1)).sum()]
        결[꼴] = {"안 정확": round(a[1] / a[0], 4), "안 ±1": round(a[2] / a[0], 4), "깎인 속 정확": round(a[4] / a[3], 4), "깎인 속 ±1": round(a[5] / a[3], 4)}
    print(이름, 결, flush=True); json.dump(결, open(L.O + f"학습69_{이름}/판정106.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
