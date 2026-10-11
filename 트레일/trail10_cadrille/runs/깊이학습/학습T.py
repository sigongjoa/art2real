# -*- coding: utf-8 -*-
"""깊이학습 T — 같은 망 · 목표만 「정리된 깊이」(기능0/정답T.py) · 모델.pt 에서 이어 학습 · 10-11
python runs/깊이학습/학습T.py [에폭=6]  →  모델T.pt · 학습T.log · 스냅T/NNNNN.npz"""
import os, sys, time, numpy as np, torch
from 학습 import 망, 손실
H = os.path.dirname(os.path.abspath(__file__)); torch.manual_seed(0); dev = "cuda"
E = int(sys.argv[1]) if len(sys.argv) > 1 else 6; B = 32
X = np.load(os.path.join(H, "학습.npy"), mmap_mode="r"); TX = np.load(os.path.join(H, "정답T_학습.npy"), mmap_mode="r")
S_ = np.load(os.path.join(H, "시험.npz"))["X"]; ST = np.load(os.path.join(H, "정답T_시험.npy"))
rng = np.random.default_rng(0); 순 = rng.permutation(len(X)); V, TR = 순[:150], 순[150:]
꼬리 = "_검증뺌" if os.environ.get("VAL") else ""   # VAL=1: 검증목록.json 의 20 모델(150 부품)을 학습 · 검증에서 통째로 뺌
if 꼬리: 뺄 = set(__import__("json").load(open(os.path.join(H, "검증목록.json"), encoding="utf-8"))["학습빼기"]); V, TR = np.array([i for i in V if i not in 뺄]), np.array([i for i in TR if i not in 뺄])
쌍 = lambda idx: np.array([(i, v) for i in idx for v in range(6)])
PT, PV = 쌍(TR), 쌍(V); SN = [0, 5, 17, 18, 31, 35]
def 묶음(A, Tt, P):
    i = np.sort(np.unique(P[:, 0])); x = torch.from_numpy(np.stack([np.asarray(A[a, :3, b]) for a, b in P]).astype(np.float32)).to(dev)
    d = torch.from_numpy(np.stack([np.asarray(Tt[a, b]) for a, b in P]).astype(np.float32)[:, None]).to(dev); return x, d
m = 망().to(dev); m.load_state_dict(torch.load(os.path.join(H, "모델%s.pt" % 꼬리))); opt = torch.optim.AdamW(m.parameters(), 3e-4, weight_decay=1e-4); nb = len(PT) // B
sch = torch.optim.lr_scheduler.OneCycleLR(opt, 3e-4, total_steps=E * nb, pct_start=.05)
os.makedirs(os.path.join(H, "스냅T" + 꼬리), exist_ok=True); log = open(os.path.join(H, "학습T%s.log" % 꼬리), "w", encoding="utf-8"); st = 0; t0 = time.time(); best = 9e9
def 찍기(l):
    m.eval()
    with torch.no_grad():
        x, d = 묶음(S_, ST, 쌍(SN)); p = m(x)
        np.savez_compressed(os.path.join(H, "스냅T" + 꼬리, "%05d.npz" % st), P=p[:, 0].half().cpu().numpy(), 손실=np.float32(np.nan if l is None else l), 에폭=st / nb)
    m.train()
찍기(None)
for ep in range(E):
    rng.shuffle(PT); tl = []
    for i in range(nb):
        x, d = 묶음(X, TX, PT[i * B:(i + 1) * B])
        if rng.random() < .5: x, d = x.flip(-1), d.flip(-1)
        k = int(rng.integers(4)); x, d = x.rot90(k, (-2, -1)), d.rot90(k, (-2, -1))
        l = 손실(m(x), d, x[:, :1]); opt.zero_grad(); l.backward(); opt.step(); sch.step(); st += 1; tl.append(l.item())
        if st % 200 == 0: 찍기(tl[-1])
    m.eval(); vl, tt, bb = [], [], []
    with torch.no_grad():
        for A, Tt, P, o in ((X, TX, PV, vl), (S_, ST, 쌍(range(len(S_))), tt)):
            for j in range(0, len(P), 64):
                x, d = 묶음(A, Tt, P[j:j + 64]); o.append(손실(m(x), d, x[:, :1]).item())
                if o is tt: bb.append(손실(x[:, 2:3], d, x[:, :1]).item())
    msg = "에폭 %d 학습 %.4f 검증 %.4f 시험 %.4f (교차 그대로 %.4f) %.0f 초" % (ep, np.mean(tl), np.mean(vl), np.mean(tt), np.mean(bb), time.time() - t0)
    print(msg, flush=True); log.write(msg + "\n"); log.flush()
    if np.mean(vl) < best: best = np.mean(vl); torch.save(m.state_dict(), os.path.join(H, "모델T%s.pt" % 꼬리))
print("ok 최저 검증", best)
