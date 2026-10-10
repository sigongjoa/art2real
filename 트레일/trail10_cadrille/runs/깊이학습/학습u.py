# -*- coding: utf-8 -*-
"""깊이학습 2 판 — 불확실성까지 (10-10) · 1 판 모델.pt 에서 이어 머리만 2 칸(깊이 · 퍼짐 b)
손실 = 실루엣 안 라플라스 NLL(|P−D|/b + log b) + 0.5 × 깊이 모서리 L1 · 깎을 때 「잔차 > k·b」 인 곳만 믿는다
python runs/깊이학습/학습u.py [에폭=8]  (FROM · UPTO 로 나눠 돌림)  →  모델u.pt · 마지막u.pt · 학습u.log · 스냅u/"""
import os, sys, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from 학습 import 망, 모서리
torch.manual_seed(1); dev = "cuda"

class 망u(망):
    def __init__(s):
        super().__init__(); o = s.o; s.o = nn.Conv2d(o.in_channels, 2, 1)
        with torch.no_grad(): s.o.weight.zero_(); s.o.bias.zero_(); s.o.weight[:1] = o.weight; s.o.bias[:1] = o.bias; s.o.bias[1] = -4.0   # 처음 b ≈ 0.018
    def forward(s, x):
        S, Dh = x[:, :1], x[:, 2:3]; h = []; y = x
        for i, b in enumerate(s.d):
            y = b(y if i == 0 else F.max_pool2d(y, 2)); h.append(y)
        for b in s.u:
            y = b(torch.cat([F.interpolate(y, scale_factor=2), h[-2]], 1)); h.pop()
        o = s.o(y); r = F.softplus(o[:, :1] - 6) * S
        D = (Dh + r).clamp(max=.999) * S + (1 - S); bb = F.softplus(o[:, 1:2]) + 2e-3
        return torch.cat([D, bb, r], 1)          # 깊이 · 퍼짐 · 잔차(교차보다 깊은 만큼)

def 손실(Y, D, S):
    P, b = Y[:, :1], Y[:, 1:2]; m = S.sum().clamp(min=1)
    return (((P - D).abs() / b + b.log()) * S).sum() / m * .02 + .5 * ((모서리(P) - 모서리(D)).abs() * S).sum() / m   # NLL 은 크기가 달라 0.02 로 맞춤

if __name__ == "__main__":
    E = int(sys.argv[1]) if len(sys.argv) > 1 else 8; B = 32
    X = np.load(os.path.join(H, "학습.npy"), mmap_mode="r"); T = np.load(os.path.join(H, "시험.npz"))["X"]
    rng = np.random.default_rng(0); 순 = rng.permutation(len(X)); V, TR = 순[:150], 순[150:]      # 1 판과 같은 검증 150
    쌍 = lambda idx: np.array([(i, v) for i in idx for v in range(6)]); PT, PV = 쌍(TR), 쌍(V); SN = [0, 5, 17, 18, 31, 35]
    def 묶음(A, P):
        x = torch.from_numpy(A[P[:, 0], :, P[:, 1]].astype(np.float32)).to(dev); return x[:, :3], x[:, 3:4]
    m = 망u().to(dev); nb = len(PT) // B
    opt = torch.optim.AdamW(m.parameters(), 3e-4, weight_decay=1e-4); sch = torch.optim.lr_scheduler.OneCycleLR(opt, 3e-4, total_steps=E * nb, pct_start=.05)
    A, C = int(os.environ.get("FROM", 0)), int(os.environ.get("UPTO", E)); CK = os.path.join(H, "마지막u.pt"); best = 9e9
    if A:
        ck = torch.load(CK); m.load_state_dict(ck["m"]); opt.load_state_dict(ck["opt"]); sch.load_state_dict(ck["sch"]); best = ck["best"]; rng = np.random.default_rng(100 + A)
    else:
        sd = torch.load(os.path.join(H, "모델.pt")); w, b = sd.pop("o.weight"), sd.pop("o.bias"); m.load_state_dict(sd, strict=False)
        with torch.no_grad(): m.o.weight[:1] = w; m.o.bias[:1] = b
    os.makedirs(os.path.join(H, "스냅u"), exist_ok=True); log = open(os.path.join(H, "학습u.log"), "a" if A else "w", encoding="utf-8"); st = A * nb; t0 = time.time()
    def 찍기(l):
        m.eval()
        with torch.no_grad():
            x, d = 묶음(T, 쌍(SN)); y = m(x)
            np.savez_compressed(os.path.join(H, "스냅u", "%05d.npz" % st), P=y[:, 0].half().cpu().numpy(), Bq=y[:, 1].half().cpu().numpy(), 손실=np.float32(l if l is not None else np.nan), 에폭=st / nb)
        m.train()
    if not A: 찍기(None)
    for ep in range(A, C):
        rng.shuffle(PT); tl = []
        for i in range(nb):
            x, d = 묶음(X, PT[i * B:(i + 1) * B])
            if rng.random() < .5: x, d = x.flip(-1), d.flip(-1)
            k = int(rng.integers(4)); x, d = x.rot90(k, (-2, -1)), d.rot90(k, (-2, -1))
            l = 손실(m(x), d, x[:, :1]); opt.zero_grad(); l.backward(); nn.utils.clip_grad_norm_(m.parameters(), 1.0); opt.step(); sch.step(); st += 1; tl.append(l.item())
            if st % 200 == 0: 찍기(tl[-1])
        m.eval(); vl, l1, cal = [], [], []
        with torch.no_grad():
            for j in range(0, len(PV), 64):
                x, d = 묶음(X, PV[j:j + 64]); y = m(x); S = x[:, :1]; vl.append(손실(y, d, S).item())
                e = (y[:, :1] - d).abs(); l1.append(((e * S).sum() / S.sum()).item())
                cal.append((((e < y[:, 1:2]).float() * S).sum() / S.sum()).item())     # |오차| < b 비율 — 라플라스면 63 % 근처가 맞음
        msg = "에폭 %d 학습 %.4f 검증 %.4f 깊이 L1 %.4f |오차|<b %.0f%% %.0f 초" % (ep, np.mean(tl), np.mean(vl), np.mean(l1), 100 * np.mean(cal), time.time() - t0)
        print(msg, flush=True); log.write(msg + "\n"); log.flush()
        if np.mean(vl) < best: best = np.mean(vl); torch.save(m.state_dict(), os.path.join(H, "모델u.pt"))
        torch.save({"m": m.state_dict(), "opt": opt.state_dict(), "sch": sch.state_dict(), "best": best}, CK)
    if C >= E: 찍기(tl[-1])
    print("ok 에폭", C, "최저 검증", best)
