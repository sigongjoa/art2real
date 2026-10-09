# -*- coding: utf-8 -*-
"""실물학습 v2 — 어휘 v2(회전) 디코더 · 합성(정답 조각 있음: 컨투어 + 짝 보조) + 실물(윤곽만: 컨투어) 섞어 학습 · 조각2 가중치에서 이어서
스냅: 실물 시험 부품 6 개(사전0 의 0·2·6·8·14·32)를 300 스텝마다 → 타임랩스
python runs/실물학습/학습v2.py [에폭=12]"""
import os, sys, json, glob, time, numpy as np, torch, torch.nn as nn
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); sys.path[:0] = [os.path.join(R, "조각0")]
os.environ.setdefault("N3", "48")
from 조각 import 이름, 점유, 격자, 보기, 모서리, 정답칸r
from 학습 import 디코더, 손실, K, N3
torch.manual_seed(0); dev = "cuda"; B = 8; RSC = 2.0

class 디코더v2(디코더):   # 머리에 회전 3 칸 더함 · 회전 = tanh × π/2
    def __init__(s):
        super().__init__(); h = s.head; s.head = nn.Linear(h.in_features, len(이름) + 9)
        with torch.no_grad(): s.head.weight.zero_(); s.head.bias.zero_(); s.head.weight[:len(이름) + 6] = h.weight; s.head.bias[:len(이름) + 6] = h.bias
    def forward(s, x):
        h = s.dec(s.q.expand(len(x), -1, -1), s.proj(x)); o = s.head(h); T = len(이름)
        return o[..., :T], torch.sigmoid(o[..., T:T + 3]) * 1.1 - .05, torch.sigmoid(o[..., T + 3:T + 6]) * 2, torch.tanh(o[..., T + 6:]) * (np.pi / 2)

def 그림(prob, c, s, r, tau, g):
    Sil, D = 보기(점유(g, prob, c, s, tau, r), N3); return Sil, D, 모서리(D)

def 짝손실(lg, c, s, gts):   # 학습.짝손실 과 같음(회전은 컨투어에 맡김 — 대칭 조각은 회전 정답이 여럿)
    from scipy.optimize import linear_sum_assignment
    lp = lg.log_softmax(-1); tot = 0
    for b, (P, C, S, n) in enumerate(gts):
        tgt = torch.zeros(len(lp[b]), dtype=torch.long, device=lp.device)
        if n:
            cost = -lp[b][:, P[:n]] + (c[b][:, None] - C[None, :n]).abs().sum(-1) + (s[b][:, None] - S[None, :n]).clamp(-2, 2).abs().sum(-1) * .5
            r_, q = linear_sum_assignment(cost.detach().cpu().numpy()); r_, q = torch.as_tensor(r_, device=lp.device), torch.as_tensor(q, device=lp.device)
            tgt[r_] = P[q]; tot = tot + (c[b][r_] - C[q]).abs().mean() + (s[b][r_] - S[q].clamp(max=2)).abs().mean() * .5
        tot = tot + nn.functional.nll_loss(lp[b], tgt)
    return tot / len(gts)

if __name__ == "__main__":
    E = int(sys.argv[1]) if len(sys.argv) > 1 else 12; g = 격자(N3, dev)[None]
    # 합성: 조각0(축 정렬 4000) + 조각v2(회전 3000)
    XS, QS = [], []
    for d in ("조각0", "조각v2"):
        XS.append(torch.from_numpy(np.load(os.path.join(R, d, "특징.npy")))); QS += [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(os.path.join(R, d, "정답", "*.json")))]
    XS = torch.cat(XS); assert len(XS) == len(QS), (len(XS), len(QS))
    with torch.no_grad():
        YS = []
        for i in range(0, len(QS), B):
            P, C, S, Rr = map(lambda t: torch.stack(t).to(dev), zip(*[정답칸r(q, K) for q in QS[i:i + B]]))
            YS.append([t.half().cpu() for t in 그림(P, C, S, Rr, .005, g)])
        YS = [torch.cat(t) for t in zip(*YS)]
    GTS = [(torch.tensor([이름.index(q[0]) for q in Q[:K]] or [0], device=dev), torch.tensor([q[1] for q in Q[:K]] or [[0, 0, 0]], device=dev), torch.tensor([q[2] for q in Q[:K]] or [[0, 0, 0]], device=dev), len(Q[:K])) for Q in QS]
    # 실물: 윤곽만
    키 = sorted(json.load(open(os.path.join(H, "목록.json"), encoding="utf-8"))); XR = torch.from_numpy(np.load(os.path.join(H, "특징.npy"))); assert len(XR) == len(키)
    YR = []
    for k in 키:
        z = np.load(os.path.join(H, "보기", k + ".npz")); S_, D_ = torch.from_numpy(z["S"].astype(np.float32)), torch.from_numpy(z["D"].astype(np.float32))
        YR.append([S_.half(), D_.half(), 모서리(D_[None])[0].half()])
    YR = [torch.stack(t) for t in zip(*YR)]
    rng = np.random.default_rng(0); 순 = rng.permutation(len(XR)); RV, RT = 순[:150], 순[150:]     # 실물 검증 150 (학습에 안 씀)
    sp = rng.permutation(len(XS)); SV, ST = sp[:300], sp[300:]
    XT = torch.from_numpy(np.load(os.path.join(H, "시험특징.npy"))); SNAPI = [0, 2, 6, 8, 14, 32]
    m = 디코더v2().to(dev); sd = torch.load(os.path.join(R, "조각2", "디코더.pt")); h_w, h_b = sd.pop("head.weight"), sd.pop("head.bias")
    m.load_state_dict(sd, strict=False)
    with torch.no_grad(): m.head.weight.zero_(); m.head.bias.zero_(); m.head.weight[:len(이름) + 6] = h_w.to(dev); m.head.bias[:len(이름) + 6] = h_b.to(dev)
    opt = torch.optim.AdamW(m.parameters(), 1.5e-4, weight_decay=1e-4); nb = min(len(ST), len(RT)) // (B // 2)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, 1.5e-4, total_steps=E * nb, pct_start=.05); log = open(os.path.join(H, "학습.log"), "w", encoding="utf-8")
    os.makedirs(os.path.join(H, "스냅"), exist_ok=True); st = 0; best = 9e9; t0 = time.time()
    def 찍기(l):
        m.eval()
        with torch.no_grad():
            lg, c, s, r = m(XT[SNAPI].to(dev).float()); t_ = lg.argmax(-1)
            P = [[(이름[int(t_[b, q])], c[b, q].tolist(), s[b, q].tolist(), r[b, q].tolist()) for q in range(K) if int(t_[b, q]) != 0] for b in range(len(SNAPI))]
        json.dump({"스텝": st, "손실": l, "예측": P}, open(os.path.join(H, "스냅", "%05d.json" % st), "w", encoding="utf-8"), ensure_ascii=False); m.train()
    찍기(None)
    def 한판(j, 실물, tau, hard):
        X = (XR if 실물 else XS)[j].to(dev).float(); Y = [y[j].to(dev).float() for y in (YR if 실물 else YS)]
        lg, c, s, r = m(X); prob = nn.functional.gumbel_softmax(lg, tau=1.0, hard=True) if hard else lg.softmax(-1)
        L = 손실(그림(prob, c, s, r, tau, g), Y)
        add = prob[..., 1:6].sum(-1); out = (torch.relu(c + s / 2 - 1.05) + torch.relu(-0.05 - (c - s / 2))).sum(-1); L = L + 2 * (add * out).mean()
        if not 실물: L = L + 0.5 * 짝손실(lg, c, s, [GTS[int(q)] for q in j])
        return L
    for ep in range(E):
        tau = .03 + (.01 - .03) * ep / max(E - 1, 1); m.train(); a, b_ = rng.permutation(ST), rng.permutation(RT); tl = []
        for i in range(nb):
            js, jr = torch.as_tensor(a[i * B // 2:(i + 1) * B // 2]), torch.as_tensor(b_[i * B // 2:(i + 1) * B // 2])
            loss = 한판(js, False, tau, True) + RSC * 한판(jr, True, tau, True)
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(m.parameters(), 1.0); opt.step(); sched.step(); st += 1; tl.append(loss.item())
            if st % 300 == 0: 찍기(tl[-1])
        m.eval(); vr, vs = [], []
        with torch.no_grad():
            for i in range(0, len(RV), B):
                j = torch.as_tensor(RV[i:i + B]); lg, c, s, r = m(XR[j].to(dev).float())
                vr.append(손실(그림(nn.functional.one_hot(lg.argmax(-1), len(이름)).float(), c, s, r, .01, g), [y[j].to(dev).float() for y in YR]).item())
            for i in range(0, len(SV), B):
                j = torch.as_tensor(SV[i:i + B]); lg, c, s, r = m(XS[j].to(dev).float())
                vs.append(손실(그림(nn.functional.one_hot(lg.argmax(-1), len(이름)).float(), c, s, r, .01, g), [y[j].to(dev).float() for y in YS]).item())
        msg = "에폭 %d τ %.3f 학습 %.4f 검증 실물 %.4f 합성 %.4f %.0f 초" % (ep, tau, np.mean(tl), np.mean(vr), np.mean(vs), time.time() - t0); print(msg, flush=True); log.write(msg + "\n"); log.flush()
        if np.mean(vr) < best: best = np.mean(vr); torch.save(m.state_dict(), os.path.join(H, "디코더v2.pt"))
    print("ok 최저 실물 검증", best)
