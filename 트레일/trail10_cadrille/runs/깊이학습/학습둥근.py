# -*- coding: utf-8 -*-
"""둥근 학생 — 선 · 실루엣 · 교차 깊이 → 칸 지도 5 갈래(없음 · 공 · 소켓 · 볼록 원기둥 · 오목 원기둥) · 같은 작은 U-Net 몸 · 10-11
python runs/깊이학습/학습둥근.py [에폭=6]  →  모델둥근.pt · 학습둥근.log"""
import os, sys, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from 학습 import 망
H = os.path.dirname(os.path.abspath(__file__)); torch.manual_seed(0); dev = "cuda"
class 둥근망(망):
    def __init__(s): super().__init__(); s.o = nn.Conv2d(32, 5, 1)
    def forward(s, x):
        h = []; y = x
        for i, b in enumerate(s.d):
            y = b(y if i == 0 else F.max_pool2d(y, 2)); h.append(y)
        for b in s.u:
            y = b(torch.cat([F.interpolate(y, scale_factor=2), h[-2]], 1)); h.pop()
        return s.o(y)
if __name__ == "__main__":
    E = int(sys.argv[1]) if len(sys.argv) > 1 else 6; B = 32
    X = np.load(os.path.join(H, "학습.npy"), mmap_mode="r"); Y = np.load(os.path.join(H, "둥근라벨_학습.npy"), mmap_mode="r")
    TX = np.load(os.path.join(H, "시험.npz"))["X"]; TY = np.load(os.path.join(H, "둥근라벨_시험.npy"))
    rng = np.random.default_rng(0); 순 = rng.permutation(len(X)); V, TR = 순[:150], 순[150:]
    쌍 = lambda idx: np.array([(i, v) for i in idx for v in range(6)]); PT, PV = 쌍(TR), 쌍(V)
    def 묶음(A, L, P):
        x = torch.from_numpy(np.stack([np.asarray(A[a, :3, b]) for a, b in P]).astype(np.float32)).to(dev); y = torch.from_numpy(np.stack([np.asarray(L[a, b]) for a, b in P]).astype(np.int64)).to(dev); return x, y
    w = torch.tensor([.2, 3, 3, 2, 2], device=dev)   # 둥근 칸이 1.7 % 뿐이라 무게
    m = 둥근망().to(dev); sd = torch.load(os.path.join(H, "모델T.pt")); m.load_state_dict({k: v for k, v in sd.items() if not k.startswith("o.")}, strict=False)
    opt = torch.optim.AdamW(m.parameters(), 5e-4, weight_decay=1e-4); nb = len(PT) // B; sch = torch.optim.lr_scheduler.OneCycleLR(opt, 5e-4, total_steps=E * nb, pct_start=.05)
    log = open(os.path.join(H, "학습둥근.log"), "w", encoding="utf-8"); best = 9e9; t0 = time.time()
    def 잼(A, L, P):
        m.eval(); ls, inter, uni = [], np.zeros(5), np.zeros(5)
        with torch.no_grad():
            for j in range(0, len(P), 64):
                x, y = 묶음(A, L, P[j:j + 64]); o = m(x); ls.append(F.cross_entropy(o, y, weight=w).item()); p = o.argmax(1)
                for c in range(1, 5): inter[c] += ((p == c) & (y == c)).sum().item(); uni[c] += ((p == c) | (y == c)).sum().item()
        m.train(); return np.mean(ls), inter[1:] / np.maximum(uni[1:], 1)
    for ep in range(E):
        rng.shuffle(PT); tl = []
        for i in range(nb):
            x, y = 묶음(X, Y, PT[i * B:(i + 1) * B])
            if rng.random() < .5: x, y = x.flip(-1), y.flip(-1)
            k = int(rng.integers(4)); x, y = x.rot90(k, (-2, -1)), y.rot90(k, (-2, -1))
            l = F.cross_entropy(m(x), y, weight=w); opt.zero_grad(); l.backward(); opt.step(); sch.step(); tl.append(l.item())
        vl, viou = 잼(X, Y, PV); tl_, tiou = 잼(TX, TY, 쌍(range(len(TX))))
        msg = "에폭 %d 학습 %.4f 검증 %.4f 시험 %.4f · 시험 IoU 공 %.2f 소켓 %.2f 볼록원기둥 %.2f 오목원기둥 %.2f · %.0f 초" % (ep, np.mean(tl), vl, tl_, *tiou, time.time() - t0)
        print(msg, flush=True); log.write(msg + "\n"); log.flush()
        if vl < best: best = vl; torch.save(m.state_dict(), os.path.join(H, "모델둥근.pt"))
    print("ok 최저 검증", best)
