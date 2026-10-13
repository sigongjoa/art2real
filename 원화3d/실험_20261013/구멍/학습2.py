# 로드맵 1 단계 학습(판정기준27) — 그림 → CNN → 바탕 + 칸 3 → 후보 8 → CadQuery 실제로 짓고 윗면 IoU → GRPO 식 · 10-13
# venv python 학습2.py → out/설명/구멍/학습2/스냅.json · 결과.json · 망.pt
import os, json, time, numpy as np
from multiprocessing import Pool
import 캐드점수2 as K   # 일꾼은 이 파일 맨 위만 다시 읽는다 — torch 는 main 안에서만
O = "G:/art2real/out/설명/구멍/학습2/"; os.makedirs(O, exist_ok=True)
걸음, 배치, 후보, 스냅간격 = 1500, 16, 8, 100
범주 = ["상자+구멍1", "상자+구멍여럿", "상자+홈", "원기둥+구멍", "원기둥+홈", "상자+섞임"]
def 범주of(p):
    t = [c[0] for c in p["칸"] if c[0]]; h = t.count(1); s = len(t) - h
    if p["바탕"] == 1: return "원기둥+구멍" if h and not s else "원기둥+홈" if s and not h else None
    return "상자+구멍1" if h == 1 and not s else "상자+구멍여럿" if h >= 2 and not s else "상자+홈" if s and not h else "상자+섞임" if h and s else None
def 묶음(pool, n, 씨):
    g = np.random.default_rng(씨); P = [K.무작위(g) for _ in range(n)]; M = pool.map(K.정답, P); keep = [i for i, m in enumerate(M) if m is not None]
    P = [P[i] for i in keep]; M = [M[i] for i in keep]; return P, np.stack([K.그림(p) for p in P]), M
def 개수(p): return sum(1 for c in p["칸"] if c[0])

def 망만들기():   # torch 는 여기서만 올린다(일꾼 spawn 은 안 부름)
    import torch, torch.nn as nn
    class 망(nn.Module):
        def __init__(s):
            super().__init__(); c = lambda i, o: nn.Sequential(nn.Conv2d(i, o, 3, 2, 1), nn.BatchNorm2d(o), nn.ReLU())
            s.f = nn.Sequential(c(1, 32), c(32, 64), c(64, 96), c(96, 128), c(128, 128), nn.Flatten(), nn.Linear(128 * 16, 256), nn.ReLU())
            s.바탕 = nn.Linear(256, 2); s.b = nn.Linear(256, 3); s.칸종 = nn.Linear(256, 3 * 4); s.칸수 = nn.Linear(256, 3 * 4)
            s.로그폭b = nn.Parameter(torch.full((3,), .5)); s.로그폭칸 = nn.Parameter(torch.full((4,), .5))
        def forward(s, x):
            h = s.f(x[:, None]); b = torch.stack([18 + 4 * torch.tanh(s.b(h)[:, 0]), 15 + 5 * torch.tanh(s.b(h)[:, 1]), 8 + 2 * torch.tanh(s.b(h)[:, 2])], 1)
            q = s.칸수(h).view(-1, 3, 4); 칸 = torch.stack([9 * torch.tanh(q[..., 0]), 9 * torch.tanh(q[..., 1]), 6.5 + 5.5 * torch.tanh(q[..., 2]), 3 + 1.5 * torch.tanh(q[..., 3])], -1)
            return s.바탕(h), b, s.칸종(h).view(-1, 3, 4), 칸
    return 망
def 프로그램(bt, b, ct, cv):
    칸 = []
    for j in range(3):
        t = int(ct[j]); x, y, a, bb = [float(v) for v in cv[j]]
        if t == 1: a = 1 + (a - 1) / 11 * 2.5   # 구멍 반지름 1~3.5 로 다시 맞춤(같은 숫자 칸을 길이 4~12 와 같이 씀)
        칸.append((t, x, y, a, bb))
    return {"바탕": int(bt), "b": [float(v) for v in b], "칸": 칸}

if __name__ == "__main__":
    import torch
    망 = 망만들기()
    torch.manual_seed(27); dev = "cuda" if torch.cuda.is_available() else "cpu"
    with Pool(6) as pool:
        Ptr, Xtr, Mtr = 묶음(pool, 3000, 27); Pte, Xte, Mte = 묶음(pool, 200, 2027)
        지 = [next(i for i, p in enumerate(Pte) if 범주of(p) == c) for c in 범주]
        m = 망().to(dev); opt = torch.optim.Adam(m.parameters(), 1e-3); 스냅 = []
        고정 = {"바탕": 0, "b": [18, 15, 8], "칸": [(0, 0, 0, 0, 0)] * 3}; 평균맞히기 = float(np.mean(pool.map(K.점수, [(고정, mm) for mm in Mte])))
        def 평가():
            m.eval()
            with torch.no_grad():
                bl, b, cl, cv = m(torch.tensor(Xte, device=dev)); P = [프로그램(bl[i].argmax(), b[i], cl[i].argmax(-1), cv[i]) for i in range(len(Xte))]
            m.train(); s = pool.map(K.점수, [(p, mm) for p, mm in zip(P, Mte)]); return P, s
        t0 = time.time()
        for st in range(걸음 + 1):
            if st % 스냅간격 == 0:
                P, s = 평가(); 맞 = float(np.mean([개수(p) == 개수(q) for p, q in zip(P, Pte)]))
                스냅.append({"걸음": st, "시험IoU": float(np.mean(s)), "개수맞힘": 맞, "지켜볼": [{"범주": 범주[k], "프로그램": P[i], "IoU": s[i]} for k, i in enumerate(지)]})
                json.dump({"평균맞히기": 평균맞히기, "범주": 범주, "정답": [Pte[i] for i in 지], "스냅": 스냅}, open(O + "스냅.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
                print("걸음 %4d  시험 IoU %.3f  개수 %.2f  (평균 맞히기 %.3f)  %.0f 초" % (st, 스냅[-1]["시험IoU"], 맞, 평균맞히기, time.time() - t0), flush=True)
            if st == 걸음: break
            idx = np.random.default_rng(st).choice(len(Ptr), 배치, replace=False); bl, b, cl, cv = m(torch.tensor(Xtr[idx], device=dev))
            dB = torch.distributions.Categorical(logits=bl[:, None].expand(-1, 후보, -1)); db = torch.distributions.Normal(b[:, None].expand(-1, 후보, -1), torch.exp(m.로그폭b))
            dC = torch.distributions.Categorical(logits=cl[:, None].expand(-1, 후보, -1, -1)); dc = torch.distributions.Normal(cv[:, None].expand(-1, 후보, -1, -1), torch.exp(m.로그폭칸))
            sB, sb, sC, sc = dB.sample(), db.sample(), dC.sample(), dc.sample()
            jobs = [(프로그램(sB[i, k], sb[i, k], sC[i, k], sc[i, k]), Mtr[idx[i]]) for i in range(배치) for k in range(후보)]
            R = np.array(pool.map(K.점수, jobs)).reshape(배치, 후보); 이득 = torch.tensor((R - R.mean(1, keepdims=True)) / (R.std(1, keepdims=True) + 1e-4), dtype=torch.float32, device=dev)
            쓰임 = (sC > 0).float()   # 「없음」 칸의 숫자는 점수에 영향이 없으니 로그확률에서 뺀다
            bmask = torch.stack([(sB == 0).float(), (sB == 0).float(), (sB == 1).float()], -1)
            lp = dB.log_prob(sB) + (db.log_prob(sb) * bmask).sum(-1) + dC.log_prob(sC).sum(-1) + (dc.log_prob(sc).sum(-1) * 쓰임).sum(-1)
            loss = -(이득 * lp).mean(); opt.zero_grad(); loss.backward(); opt.step()
    끝 = 스냅[-1]; 통과 = 끝["시험IoU"] >= .95 and 끝["개수맞힘"] >= .8 and 끝["시험IoU"] >= max(평균맞히기, 스냅[0]["시험IoU"]) + .05
    json.dump({"시험IoU_처음": 스냅[0]["시험IoU"], "시험IoU_끝": 끝["시험IoU"], "개수맞힘_끝": 끝["개수맞힘"], "평균맞히기": 평균맞히기, "통과": 통과}, open(O + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    torch.save(m.state_dict(), O + "망.pt"); print("끝 · IoU %.3f → %.3f · 개수 %.2f · 평균 맞히기 %.3f · 통과 %s" % (스냅[0]["시험IoU"], 끝["시험IoU"], 끝["개수맞힘"], 평균맞히기, 통과))
