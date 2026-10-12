# -*- coding: utf-8 -*-
"""깊이학습 — 실루엣 · 선 · 교차 깊이 → 실물 깊이 (작은 U-Net) · 10-10
python runs/깊이학습/학습.py [에폭=15]  →  모델.pt · 학습.log · 스냅/NNNNN.npz"""
import os, sys, time, json, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
H = os.path.dirname(os.path.abspath(__file__)); torch.manual_seed(0); dev = "cuda"

def 블록(a, b): return nn.Sequential(nn.Conv2d(a, b, 3, padding=1), nn.GroupNorm(8, b), nn.SiLU(), nn.Conv2d(b, b, 3, padding=1), nn.GroupNorm(8, b), nn.SiLU())
class 망(nn.Module):
    def __init__(s, c=(32, 64, 128, 256)):
        super().__init__(); s.d = nn.ModuleList([블록(3 if i == 0 else c[i - 1], c[i]) for i in range(len(c))])
        s.u = nn.ModuleList([블록(c[i] + c[i - 1], c[i - 1]) for i in range(len(c) - 1, 0, -1)]); s.o = nn.Conv2d(c[0], 1, 1)
    def forward(s, x):   # x (B,3,N,N) = S, L, Dh → D
        S, Dh = x[:, :1], x[:, 2:3]; h = []; y = x
        for i, b in enumerate(s.d):
            y = b(y if i == 0 else F.max_pool2d(y, 2)); h.append(y)
        for b in s.u:
            y = b(torch.cat([F.interpolate(y, scale_factor=2), h[-2]], 1)); h.pop()
        return (Dh + F.softplus(s.o(y) - 6) * S).clamp(max=.999) * S + (1 - S)   # 실루엣 밖은 1

def 모서리(D):
    k = torch.tensor([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], device=D.device, dtype=D.dtype)[None, None]
    return F.conv2d(D, k, padding=1).abs() + F.conv2d(D, k.transpose(-1, -2), padding=1).abs()
def 손실(P, D, S):
    m = S.sum().clamp(min=1); return ((P - D).abs() * S).sum() / m + .5 * ((모서리(P) - 모서리(D)).abs() * S).sum() / m

if __name__ == "__main__":
    E = int(sys.argv[1]) if len(sys.argv) > 1 else 15; B = 32
    XP = os.path.join(H, "학습.npy")                     # 10-10 메모리 부족으로 꺼짐 → 메모리 맵(통째로 안 올림)
    if not os.path.exists(XP): np.save(XP, np.load(os.path.join(H, "학습.npz"))["X"])
    X = np.load(XP, mmap_mode="r"); T = np.load(os.path.join(H, "시험.npz"))["X"]   # (n,4,6,N,N) f16
    rng = np.random.default_rng(0); 순 = rng.permutation(len(X)); V, TR = 순[:150], 순[150:]
    꼬리 = ("_검증뺌" + ("" if os.environ.get("VAL") == "1" else os.environ.get("VAL"))) if os.environ.get("VAL") else ""   # VAL=2 → 검증목록2 · _검증뺌2   # VAL=1: 검증목록.json 의 20 모델(150 부품)을 학습 · 검증에서 통째로 뺌
    if 꼬리: 뺄 = set(__import__("json").load(open(os.path.join(H, "검증목록%s.json" % ("" if os.environ.get("VAL") == "1" else os.environ.get("VAL"))), encoding="utf-8"))["학습빼기"]); V, TR = np.array([i for i in V if i not in 뺄]), np.array([i for i in TR if i not in 뺄])
    쌍 = lambda idx: np.array([(i, v) for i in idx for v in range(6)])
    PT, PV = 쌍(TR), 쌍(V); SN = [0, 5, 17, 18, 31, 35]
    def 묶음(A, P):
        x = torch.from_numpy(A[P[:, 0], :, P[:, 1]].astype(np.float32)).to(dev); return x[:, :3], x[:, 3:4]
    m = 망().to(dev); opt = torch.optim.AdamW(m.parameters(), 1e-3, weight_decay=1e-4); nb = len(PT) // B
    sch = torch.optim.lr_scheduler.OneCycleLR(opt, 1e-3, total_steps=E * nb, pct_start=.05)
    # 이어 하기: 에폭 A 부터 C 까지(이번 호출) · 일정은 전체 E 기준 · 상태는 마지막.pt
    A, C = int(os.environ.get("FROM", 0)), int(os.environ.get("UPTO", E)); CK = os.path.join(H, "마지막%s.pt" % 꼬리); best = 9e9
    if A:
        if os.path.exists(CK): ck = torch.load(CK); m.load_state_dict(ck["m"]); opt.load_state_dict(ck["opt"]); sch.load_state_dict(ck["sch"]); best = ck["best"]
        else:   # 처음 이어 할 때: 최고 모델만 있음 → 옵티마이저는 새로, 일정은 그 자리까지 돌림
            m.load_state_dict(torch.load(os.path.join(H, "모델%s.pt" % 꼬리)))
            for _ in range(A * nb): sch.step()
        rng = np.random.default_rng(A)
    os.makedirs(os.path.join(H, "스냅" + 꼬리), exist_ok=True); log = open(os.path.join(H, "학습%s.log" % 꼬리), "a" if A else "w", encoding="utf-8"); st = A * nb; t0 = time.time()
    def 찍기(l):
        m.eval()
        with torch.no_grad():
            P = 쌍(SN); x, d = 묶음(T, P); p = m(x)
            np.savez_compressed(os.path.join(H, "스냅" + 꼬리, "%05d.npz" % st), P=p[:, 0].half().cpu().numpy(), 손실=np.float32(l if l is not None else np.nan), 에폭=st / nb)
        m.train()
    if not A: 찍기(None)
    for ep in range(A, C):
        rng.shuffle(PT); tl = []
        for i in range(nb):
            x, d = 묶음(X, PT[i * B:(i + 1) * B])
            if rng.random() < .5: x, d = x.flip(-1), d.flip(-1)       # 화면 안 뒤집기 · 돌리기는 깊이 뜻이 그대로
            k = int(rng.integers(4)); x, d = x.rot90(k, (-2, -1)), d.rot90(k, (-2, -1))
            l = 손실(m(x), d, x[:, :1]); opt.zero_grad(); l.backward(); opt.step(); sch.step(); st += 1; tl.append(l.item())
            if st % 200 == 0: 찍기(tl[-1])
        m.eval(); vl, tt, bb = [], [], []
        with torch.no_grad():
            for A, P, o in ((X, PV, vl), (T, 쌍(range(len(T))), tt)):
                for j in range(0, len(P), 64):
                    x, d = 묶음(A, P[j:j + 64]); o.append(손실(m(x), d, x[:, :1]).item())
                    if o is tt: bb.append(손실(x[:, 2:3], d, x[:, :1]).item())
            바 = np.mean(bb)
        msg = "에폭 %d 학습 %.4f 검증 %.4f 시험 %.4f (교차 그대로 %.4f) %.0f 초" % (ep, np.mean(tl), np.mean(vl), np.mean(tt), 바, time.time() - t0)
        print(msg, flush=True); log.write(msg + "\n"); log.flush()
        if np.mean(vl) < best: best = np.mean(vl); torch.save(m.state_dict(), os.path.join(H, "모델%s.pt" % 꼬리))
        torch.save({"m": m.state_dict(), "opt": opt.state_dict(), "sch": sch.state_dict(), "best": best}, CK)
    if C >= E: 찍기(tl[-1])
    print("ok 에폭", C, "최저 검증", best)
