# 1c 학습(판정기준28) — 바탕 = 그림의 바깥 윤곽(학습 없음) · 모델 = 칸 3 개 디테일 → 후보 8 → CadQuery 실제로 짓고 윗면 IoU → GRPO 식 · 10-13
# venv python 학습3.py → out/설명/구멍/학습3/스냅.json · 결과.json · 망.pt
import os, json, time, numpy as np
from multiprocessing import Pool
import 캐드점수2 as K, 윤곽바탕 as B   # 일꾼은 이 파일 맨 위만 다시 읽는다 — torch 는 main · 망만들기 안에서만
O = "G:/art2real/out/설명/구멍/학습3/"; os.makedirs(O, exist_ok=True)
걸음, 배치, 후보, 스냅간격 = 1000, 16, 8, 100
범주 = ["상자+구멍1", "상자+구멍여럿", "상자+홈", "원기둥+구멍", "원기둥+홈", "상자+섞임"]

def 바탕맞춤(그림):   # 그림 → 바탕 설계(피클 가능): ("원", x, y, r) | ("다각", [(x, y)…]) · mm
    _, c = B.바깥(그림); f = B.맞추기(c)
    if f[0] == "원": (x, y), r = f[1], f[2]; return ("원", float(B.화소mm(x)), float(-B.화소mm(y)), float(r / K.N * 2 * K.반))
    return ("다각", [(float(B.화소mm(x)), float(-B.화소mm(y))) for x, y in f[1]])   # json 에 넣으려고 float
def 짓기(바, 칸):
    import cadquery as cq
    s = cq.Workplane("XY").center(바[1], 바[2]).circle(바[3]).extrude(K.높) if 바[0] == "원" else cq.Workplane("XY").polyline(바[1]).close().extrude(K.높)
    for t, x, y, a, b in 칸:
        try:
            if t == 1: s = s.cut(cq.Workplane("XY").center(x, y).circle(max(a, .3)).extrude(K.높 + 2).translate((0, 0, -1)))
            elif t in (2, 3):
                w, h = (max(a, .5), max(b, .5)) if t == 2 else (max(b, .5), max(a, .5))
                s = s.cut(cq.Workplane("XY").center(x, y).rect(w, h).extrude(K.홈깊이 + 1).translate((0, 0, K.높 - K.홈깊이)))
        except Exception: pass
    return s
def 점수(job):
    바, 칸, m = job
    try: c = K.윗면(짓기(바, 칸))
    except Exception: return 0.0
    return float((c & m).sum() / max((c | m).sum(), 1))
def 묶음(pool, n, 씨):
    g = np.random.default_rng(씨); P = [K.무작위(g) for _ in range(n)]; M = pool.map(K.정답, P); keep = [i for i, m in enumerate(M) if m is not None]
    P = [P[i] for i in keep]; M = [M[i] for i in keep]; X = np.stack([K.그림(p) for p in P]); 바 = [바탕맞춤(x) for x in X]; return P, X, M, 바
def 범주of(p):
    t = [c[0] for c in p["칸"] if c[0]]; h = t.count(1); s = len(t) - h
    if p["바탕"] == 1: return "원기둥+구멍" if h and not s else "원기둥+홈" if s and not h else None
    return "상자+구멍1" if h == 1 and not s else "상자+구멍여럿" if h >= 2 and not s else "상자+홈" if s and not h else "상자+섞임" if h and s else None
def 개수(칸): return sum(1 for c in 칸 if c[0])
def 망만들기():
    import torch, torch.nn as nn
    class 망(nn.Module):
        def __init__(s):
            super().__init__(); c = lambda i, o: nn.Sequential(nn.Conv2d(i, o, 3, 2, 1), nn.BatchNorm2d(o), nn.ReLU())
            s.f = nn.Sequential(c(1, 32), c(32, 64), c(64, 96), c(96, 128), c(128, 128), nn.Flatten(), nn.Linear(128 * 16, 256), nn.ReLU())
            s.칸종 = nn.Linear(256, 3 * 4); s.칸수 = nn.Linear(256, 3 * 4); s.로그폭칸 = nn.Parameter(torch.full((4,), .5))
            nn.init.zeros_(s.칸종.weight); nn.init.zeros_(s.칸종.bias)   # 시작은 네 종류 똑같이(쏠림 없이)
        def forward(s, x):
            h = s.f(x[:, None]); q = s.칸수(h).view(-1, 3, 4)
            return s.칸종(h).view(-1, 3, 4), torch.stack([9 * torch.tanh(q[..., 0]), 9 * torch.tanh(q[..., 1]), 6.5 + 5.5 * torch.tanh(q[..., 2]), 3 + 1.5 * torch.tanh(q[..., 3])], -1)
    return 망
def 칸들(ct, cv):
    out = []
    for j in range(3):
        t = int(ct[j]); x, y, a, b = [float(v) for v in cv[j]]
        if t == 1: a = 1 + (a - 1) / 11 * 2.5
        out.append((t, x, y, a, b))
    return out

if __name__ == "__main__":
    import torch
    torch.manual_seed(28); dev = "cuda" if torch.cuda.is_available() else "cpu"
    with Pool(6) as pool:
        Ptr, Xtr, Mtr, Btr = 묶음(pool, 3000, 27); Pte, Xte, Mte, Bte = 묶음(pool, 200, 2027)
        지 = [next(i for i, p in enumerate(Pte) if 범주of(p) == c) for c in 범주]
        바탕만 = float(np.mean(pool.map(점수, [(b, [(0, 0, 0, 0, 0)] * 3, m) for b, m in zip(Bte, Mte)])))
        m = 망만들기()().to(dev); opt = torch.optim.Adam(m.parameters(), 1e-3); 스냅 = []
        def 평가():
            m.eval()
            with torch.no_grad(): cl, cv = m(torch.tensor(Xte, device=dev)); C = [칸들(cl[i].argmax(-1), cv[i]) for i in range(len(Xte))]
            m.train(); return C, pool.map(점수, [(b, c, mm) for b, c, mm in zip(Bte, C, Mte)])
        t0 = time.time()
        for st in range(걸음 + 1):
            if st % 스냅간격 == 0:
                C, s = 평가(); 맞 = float(np.mean([개수(c) == 개수(p["칸"]) for c, p in zip(C, Pte)]))
                스냅.append({"걸음": st, "시험IoU": float(np.mean(s)), "개수맞힘": 맞, "지켜볼": [{"범주": 범주[k], "바탕": Bte[i], "칸": C[i], "IoU": s[i]} for k, i in enumerate(지)]})
                json.dump({"윤곽바탕만": 바탕만, "범주": 범주, "정답": [Pte[i] for i in 지], "스냅": 스냅}, open(O + "스냅.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
                print("걸음 %4d  시험 IoU %.3f  개수 %.2f  (윤곽 바탕만 %.3f)  %.0f 초" % (st, 스냅[-1]["시험IoU"], 맞, 바탕만, time.time() - t0), flush=True)
            if st == 걸음: break
            idx = np.random.default_rng(st).choice(len(Ptr), 배치, replace=False); cl, cv = m(torch.tensor(Xtr[idx], device=dev))
            dC = torch.distributions.Categorical(logits=cl[:, None].expand(-1, 후보, -1, -1)); dc = torch.distributions.Normal(cv[:, None].expand(-1, 후보, -1, -1), torch.exp(m.로그폭칸))
            sC, sc = dC.sample(), dc.sample()
            R = np.array(pool.map(점수, [(Btr[idx[i]], 칸들(sC[i, k], sc[i, k]), Mtr[idx[i]]) for i in range(배치) for k in range(후보)])).reshape(배치, 후보)
            이득 = torch.tensor((R - R.mean(1, keepdims=True)) / (R.std(1, keepdims=True) + 1e-4), dtype=torch.float32, device=dev)
            lp = dC.log_prob(sC).sum(-1) + (dc.log_prob(sc).sum(-1) * (sC > 0).float()).sum(-1)
            loss = -(이득 * lp).mean(); opt.zero_grad(); loss.backward(); opt.step()
    끝 = 스냅[-1]; 통과 = 끝["시험IoU"] >= .95 and 끝["개수맞힘"] >= .8 and 끝["시험IoU"] > 바탕만
    json.dump({"시험IoU_처음": 스냅[0]["시험IoU"], "시험IoU_끝": 끝["시험IoU"], "개수맞힘_끝": 끝["개수맞힘"], "윤곽바탕만": 바탕만, "통과": 통과}, open(O + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    torch.save(m.state_dict(), O + "망.pt"); print("끝 · IoU %.3f → %.3f · 개수 %.2f · 윤곽 바탕만 %.3f · 통과 %s" % (스냅[0]["시험IoU"], 끝["시험IoU"], 끝["개수맞힘"], 바탕만, 통과))
