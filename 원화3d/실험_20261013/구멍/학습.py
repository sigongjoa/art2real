# 구멍 학습(판정기준26) — 그림 → CNN → 숫자(반지름 · x · y) → 후보 8 → CadQuery 실제로 짓고 윗면 렌더 → IoU → GRPO 식 고침 · 10-13
# venv python 학습.py  →  out/설명/구멍/학습/스냅.json (0 · 25 · 50 … 걸음마다 지켜볼 4 의 숫자 · 시험 IoU) · 결과.json
import os, json, time, numpy as np
from multiprocessing import Pool
import 캐드점수 as K   # 일꾼(spawn)은 이 파일 맨 위만 다시 읽는다 — torch 는 아래 main 안에서만(일꾼마다 CUDA 를 올려 페이징 파일이 바닥남 · 10-13)
O = "G:/art2real/out/설명/구멍/학습/"; os.makedirs(O, exist_ok=True)
걸음, 배치, 후보, 스냅간격 = 400, 16, 8, 25

def 묶음(n, 씨):
    g = np.random.default_rng(씨); P = np.stack([g.uniform(1.5, 7, n), g.uniform(-4, 4, n), g.uniform(-4, 4, n)], 1)
    G = [K.그림(*p) for p in P]; return P, np.stack([a for a, _ in G]), [m for _, m in G]
def 평가(pool, m, X, M):   # 평균 숫자로 지은 CAD 의 IoU
    import torch
    with torch.no_grad(): mu = m(torch.tensor(X)).numpy()
    return mu, pool.map(K.점수, [(*p, mm) for p, mm in zip(mu, M)])

if __name__ == "__main__":
    import torch, torch.nn as nn
    class 망(nn.Module):
        def __init__(s):
            super().__init__(); c = lambda i, o: nn.Sequential(nn.Conv2d(i, o, 3, 2, 1), nn.ReLU())
            s.f = nn.Sequential(c(1, 16), c(16, 32), c(32, 64), c(64, 64), c(64, 64), nn.Flatten(), nn.Linear(64 * 16, 128), nn.ReLU(), nn.Linear(128, 3))
            s.로그폭 = nn.Parameter(torch.tensor([0.4, 0.6, 0.6]))   # 처음 흔들 폭 ≈ 1.5 · 1.8 mm
        def forward(s, x):
            o = s.f(x[:, None]); return torch.stack([4.25 + 2.5 * torch.tanh(o[:, 0]), 6 * torch.tanh(o[:, 1]), 6 * torch.tanh(o[:, 2])], 1)
    torch.manual_seed(26); Ptr, Xtr, Mtr = 묶음(600, 26); Pte, Xte, Mte = 묶음(100, 2026); 지 = list(range(4))
    m = 망(); opt = torch.optim.Adam(m.parameters(), 2e-3); 스냅 = []
    with Pool(6) as pool:
        평균맞히기 = float(np.mean(pool.map(K.점수, [(4.25, 0, 0, mm) for mm in Mte])))
        t0 = time.time()
        for st in range(걸음 + 1):
            if st % 스냅간격 == 0:
                mu, s = 평가(pool, m, Xte, Mte)
                스냅.append({"걸음": st, "시험IoU": float(np.mean(s)), "지켜볼": [{"r": float(mu[i, 0]), "x": float(mu[i, 1]), "y": float(mu[i, 2]), "IoU": s[i]} for i in 지],
                           "폭": [float(v) for v in torch.exp(m.로그폭).detach()]})
                json.dump({"평균맞히기": 평균맞히기, "정답": [Pte[i].tolist() for i in 지], "스냅": 스냅}, open(O + "스냅.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
                print("걸음 %3d  시험 IoU %.3f  (평균 맞히기 %.3f)  폭 %s  %.0f 초" % (st, 스냅[-1]["시험IoU"], 평균맞히기, np.round(스냅[-1]["폭"], 2), time.time() - t0), flush=True)
            if st == 걸음: break
            b = np.random.default_rng(st).choice(600, 배치, replace=False); mu = m(torch.tensor(Xtr[b])); 폭 = torch.exp(m.로그폭)
            d = torch.distributions.Normal(mu[:, None, :].expand(-1, 후보, -1), 폭.expand(배치, 후보, 3)); 뽑 = d.sample()
            R = np.array(pool.map(K.점수, [(*뽑[i, j].tolist(), Mtr[b[i]]) for i in range(배치) for j in range(후보)])).reshape(배치, 후보)
            이득 = torch.tensor((R - R.mean(1, keepdims=True)) / (R.std(1, keepdims=True) + 1e-4), dtype=torch.float32)   # 같은 그림 후보끼리 비교
            loss = -(이득 * d.log_prob(뽑).sum(-1)).mean(); opt.zero_grad(); loss.backward(); opt.step()
    끝 = 스냅[-1]["시험IoU"]; 통과 = 끝 >= .95 and 끝 >= 평균맞히기 + .05
    json.dump({"시험IoU_처음": 스냅[0]["시험IoU"], "시험IoU_끝": 끝, "평균맞히기": 평균맞히기, "통과": 통과}, open(O + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    torch.save(m.state_dict(), O + "망.pt"); print("끝 · 처음 %.3f → 끝 %.3f · 평균 맞히기 %.3f · 통과 %s" % (스냅[0]["시험IoU"], 끝, 평균맞히기, 통과))
