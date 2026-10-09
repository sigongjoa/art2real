# -*- coding: utf-8 -*-
"""조각0 학습 — 얼린 인코더 토큰 → 칸 디코더(12 칸 · 한 번에) → SDF 점유 → 6 방향 실루엣 · 깊이 · 깊이 모서리 = 컨투어 loss
정답 조각 목록은 loss 에 안 쓴다(정답 그림만). 검증 loss 를 매 에폭 적고 가장 낮은 판을 남긴다.
python runs/조각0/학습.py [에폭=30]  →  runs/조각0/디코더.pt · 학습.log"""
import os, sys, json, glob, time, numpy as np, torch, torch.nn as nn
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from 조각 import 이름, 점유, 격자, 보기, 모서리, 정답칸
torch.manual_seed(0); dev = "cuda"; O = os.environ.get("OUT", H); PEN = float(os.environ.get("PEN", 0)); ST = os.environ.get("ST") == "1"   # 조각1: 창 밖 벌점 · 하나 고르기
K, N3, NTR = 12, int(os.environ.get("N3", 32)), int(os.environ.get("NTR", 3600)); AUX = float(os.environ.get("AUX", 0)); B = int(os.environ.get("B", 16))   # 조각2: 칸별 정답 보조 · 격자

class 디코더(nn.Module):
    def __init__(s, d=256, L=4):
        super().__init__()
        s.proj = nn.Sequential(nn.Linear(1536, d), nn.LayerNorm(d)); s.q = nn.Parameter(torch.randn(K, d) * .02)
        s.dec = nn.TransformerDecoder(nn.TransformerDecoderLayer(d, 8, 4 * d, 0.1, batch_first=True, norm_first=True), L)
        s.head = nn.Linear(d, len(이름) + 6)
    def forward(s, x):
        h = s.dec(s.q.expand(len(x), -1, -1), s.proj(x)); o = s.head(h)
        return o[..., :len(이름)], torch.sigmoid(o[..., -6:-3]) * 1.1 - .05, torch.sigmoid(o[..., -3:]) * 2   # 종류 · 중심 · 크기

def 그림(prob, c, s, tau, g):
    Sil, D = 보기(점유(g, prob, c, s, tau), N3); return Sil, D, 모서리(D)

def 짝손실(lg, c, s, gts):
    """합성 정답 조각과 칸을 짝지어(헝가리안 · 순서 없음) 종류 교차 엔트로피 + 중심·크기 L1 · 짝 없는 칸은 빈칸으로"""
    from scipy.optimize import linear_sum_assignment
    lp = lg.log_softmax(-1); tot = 0
    for b, (P, C, S, n) in enumerate(gts):
        tgt = torch.zeros(len(lp[b]), dtype=torch.long, device=lp.device)
        if n:
            cost = -lp[b][:, P[:n]] + (c[b][:, None] - C[None, :n]).abs().sum(-1) + (s[b][:, None] - S[None, :n]).clamp(-2, 2).abs().sum(-1) * .5
            r, q = linear_sum_assignment(cost.detach().cpu().numpy()); r, q = torch.as_tensor(r, device=lp.device), torch.as_tensor(q, device=lp.device)
            tgt[r] = P[q]; tot = tot + (c[b][r] - C[q]).abs().mean() + (s[b][r] - S[q].clamp(max=2)).abs().mean() * .5
        tot = tot + nn.functional.nll_loss(lp[b], tgt)
    return tot / len(gts)

def 손실(a, b):
    return sum(w * (x - y).abs().mean() for w, x, y in zip((1, 1, 0.5), a, b))

if __name__ == "__main__":
    E = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    X = torch.from_numpy(np.load(os.path.join(H, "특징.npy")))                  # (N, 토큰, 1536) fp16
    Qs = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(H, "정답", "*.json")))][:len(X)]
    assert len(Qs) == len(X), (len(Qs), len(X))
    g = 격자(N3, dev)[None]
    with torch.no_grad():   # 정답 그림(날카롭게 τ 0.005)을 한 번만
        Y = []
        for i in range(0, len(Qs), B):
            P, C, S = map(lambda t: torch.stack(t).to(dev), zip(*[정답칸(q, K) for q in Qs[i:i + B]]))
            Y.append([t.cpu() for t in 그림(P, C, S, 0.005, g)])
        Y = [torch.cat(t) for t in zip(*Y)]
    GT = []
    for q in Qs:   # 짝손실용 정답 조각(종류 번호 · 중심 · 크기 · 개수)
        q = q[:K]; GT.append((torch.tensor([이름.index(t) for t, _, _ in q] or [0], device=dev), torch.tensor([c for _, c, _ in q] or [[0, 0, 0]], device=dev), torch.tensor([s for _, _, s in q] or [[0, 0, 0]], device=dev), len(q)))
    m = 디코더().to(dev); npar = sum(p.numel() for p in m.parameters()); print("디코더 매개변수", npar, flush=True)
    opt = torch.optim.AdamW(m.parameters(), 3e-4, weight_decay=1e-4); best = 9e9; log = open(os.path.join(O, "학습.log"), "w", encoding="utf-8")
    steps = E * (NTR // B); sched = torch.optim.lr_scheduler.OneCycleLR(opt, 3e-4, total_steps=steps, pct_start=.05); st = 0; t0 = time.time()
    SNAP = int(os.environ.get("SNAP", 0)); SID = list(range(3600, 3606)); os.makedirs(os.path.join(O, "스냅"), exist_ok=True) if SNAP else None
    def 찍기(m, st, ep, l):   # 10-09 학습 타임랩스: 시험 부품 6 개의 그 순간 예측(한 종류)을 남긴다
        was = m.training; m.eval()
        with torch.no_grad():
            lg, c, s = m(X[SID].to(dev).float()); t_ = lg.argmax(-1)
            P = [[(이름[int(t_[b, q])], c[b, q].tolist(), s[b, q].tolist()) for q in range(K) if int(t_[b, q]) != 0] for b in range(len(SID))]
        json.dump({"스텝": st, "에폭": ep, "손실": l, "예측": P}, open(os.path.join(O, "스냅", "%05d.json" % st), "w", encoding="utf-8"), ensure_ascii=False)
        m.train(was)
    if SNAP: 찍기(m, 0, 0, None)
    for ep in range(E):
        tau = .05 + (.01 - .05) * ep / max(E - 1, 1); m.train(); perm = torch.randperm(NTR); tl = []
        for i in range(0, NTR - B + 1, B):
            j = perm[i:i + B]; lg, c, s = m(X[j].to(dev).float()); prob = nn.functional.gumbel_softmax(lg, tau=1.0, hard=True) if ST and ep >= E // 3 else lg.softmax(-1)
            ent = -(prob * prob.clamp_min(1e-8).log()).sum(-1).mean()
            loss = 손실(그림(prob, c, s, tau, g), [y[j].to(dev) for y in Y]) + 0.01 * (ep / E) * ent
            if AUX: loss = loss + AUX * 짝손실(lg, c, s, [GT[int(q)] for q in j])
            if PEN: add = prob[..., 1:6].sum(-1); out = (torch.relu(c + s / 2 - 1.05) + torch.relu(-0.05 - (c - s / 2))).sum(-1); loss = loss + PEN * (add * out).mean()   # 창 밖은 공짜가 아니다
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(m.parameters(), 1.0); opt.step(); sched.step(); st += 1; tl.append(loss.item())
            if SNAP and st % SNAP == 0: 찍기(m, st, ep, tl[-1])
        m.eval(); vl = []
        with torch.no_grad():
            for i in range(NTR, len(X), B):
                j = torch.arange(i, min(i + B, len(X))); lg, c, s = m(X[j].to(dev).float())
                vl.append(손실(그림(nn.functional.one_hot(lg.argmax(-1), len(이름)).float() if ST else lg.softmax(-1), c, s, .01, g), [y[j].to(dev) for y in Y]).item())
        v = float(np.mean(vl)); msg = "에폭 %d τ %.3f 학습 %.4f 검증 %.4f %.0f 초" % (ep, tau, np.mean(tl), v, time.time() - t0); print(msg, flush=True); log.write(msg + "\n"); log.flush()
        if v < best: best = v; torch.save(m.state_dict(), os.path.join(O, "디코더.pt"))
    print("ok 최저 검증", best)
