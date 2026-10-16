# 로드맵 2 학습(판정기준30) — U-Net: 선 그림 → 화소 4 갈래(바깥 · 윗면 · 관통 · 들어감) + 깊이 · 에폭마다 화소 mIoU · 끝에 시험 1,003 부피 IoU · 10-13
# venv python 학습.py → out/설명/캐드부품/학습/망.pt · 기록.json · 결과.json · 지켜볼 지도
import os, json, time, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/학습/"; os.makedirs(O, exist_ok=True); 에폭 = 15
def U만들기(ch=1, k=1):   # ch = 입력 채널(1 위 · 3 위 · 앞 · 옆 — 판정기준31 ②) · k = 폭 배수(10-16 진단59 · 기본 1 은 예전과 같음)
    import torch, torch.nn as nn
    class U(nn.Module):
        def __init__(s):
            super().__init__(); b = lambda i, o: nn.Sequential(nn.Conv2d(i, o, 3, 1, 1), nn.BatchNorm2d(o), nn.ReLU(), nn.Conv2d(o, o, 3, 1, 1), nn.BatchNorm2d(o), nn.ReLU())
            s.e1, s.e2, s.e3, s.e4 = b(ch, 32 * k), b(32 * k, 64 * k), b(64 * k, 128 * k), b(128 * k, 192 * k); s.p = nn.MaxPool2d(2)
            s.u3, s.d3 = nn.ConvTranspose2d(192 * k, 128 * k, 2, 2), b(256 * k, 128 * k); s.u2, s.d2 = nn.ConvTranspose2d(128 * k, 64 * k, 2, 2), b(128 * k, 64 * k); s.u1, s.d1 = nn.ConvTranspose2d(64 * k, 32 * k, 2, 2), b(64 * k, 32 * k); s.o = nn.Conv2d(32 * k, 5, 1)
        def forward(s, x):
            x = x[:, None] if x.dim() == 3 else x; a = s.e1(x); b_ = s.e2(s.p(a)); c = s.e3(s.p(b_)); d = s.e4(s.p(c))
            c2 = s.d3(torch.cat([s.u3(d), c], 1)); b2 = s.d2(torch.cat([s.u2(c2), b_], 1)); a2 = s.d1(torch.cat([s.u1(b2), a], 1)); o = s.o(a2)
            return o[:, :4], torch.sigmoid(o[:, 4])   # 갈래 4 · 깊이 비율 0~1
    return U
if __name__ == "__main__":
    import torch, torch.nn.functional as Fn
    torch.manual_seed(30); dev = "cuda"; d = np.load("G:/art2real/out/설명/캐드부품/데이터.npz"); X, Y, D, 시 = d["X"].astype(np.float32), d["Y"], d["D"].astype(np.float32), d["시험"]   # Y 는 uint8 로 두고 배치마다 long
    L = json.load(open("G:/art2real/out/설명/캐드부품/목록.json", encoding="utf-8")); tr, te = np.nonzero(~시)[0], np.nonzero(시)[0]
    m = U만들기()().to(dev); opt = torch.optim.Adam(m.parameters(), 1e-3); w = torch.tensor([1., 1., 3., 1.5], device=dev); 기록 = []; t0 = time.time()
    def 예측(idx):
        m.eval(); C, Dp = [], []
        with torch.no_grad():
            for k in range(0, len(idx), 64):
                lo, dp = m(torch.tensor(X[idx[k:k + 64]], device=dev)); C.append(lo.argmax(1).cpu().numpy().astype(np.uint8)); Dp.append(dp.cpu().numpy())
        m.train(); return np.concatenate(C), np.concatenate(Dp)
    def mIoU(P, T): return float(np.mean([((P == c) & (T == c)).sum() / max(((P == c) | (T == c)).sum(), 1) for c in (1, 2, 3)]))
    지 = te[:6]
    for ep in range(에폭 + 1):
        P, Dp = 예측(te); mi = mIoU(P, Y[te]); 기록.append({"에폭": ep, "mIoU": mi}); print("에폭 %2d · 시험 화소 mIoU %.3f · %.0f 초" % (ep, mi, time.time() - t0), flush=True)
        np.save(O + "지켜볼_e%02d.npy" % ep, np.stack([P[:6], (Dp[:6] * 255).astype(np.uint8)])); json.dump(기록, open(O + "기록.json", "w"))
        if ep == 에폭: break
        perm = np.random.default_rng(ep).permutation(tr)
        for k in range(0, len(perm), 32):
            i = perm[k:k + 32]; x, dd = torch.tensor(X[i], device=dev), torch.tensor(D[i], device=dev); y = torch.tensor(Y[i], device=dev).long(); lo, dp = m(x)
            l = Fn.cross_entropy(lo, y, weight=w) + 2 * (((dp - dd).abs()) * (y == 3)).sum() / max(int((y == 3).sum()), 1); opt.zero_grad(); l.backward(); opt.step()
    torch.save(m.state_dict(), O + "망.pt")
    with Pool(6) as pool: R = np.array(pool.map(J.부피IoU, [(L[i], P[j], Dp[j]) for j, i in enumerate(te)], chunksize=8))
    결과 = {"부피IoU": float(R[:, 0].mean()), "바탕만": float(R[:, 1].mean()), "차": float((R[:, 0] - R[:, 1]).mean()), "화소mIoU": 기록[-1]["mIoU"], "부품": len(te)}
    결과["통과"] = 결과["차"] >= .04 and 결과["화소mIoU"] >= .6; json.dump(결과, open(O + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); np.save(O + "부피IoU.npy", R)
    print("끝 · 시험 %d 부피 IoU %.3f · 바탕만 %.3f · 차 %+.3f · 화소 mIoU %.3f · 통과 %s" % (len(te), 결과["부피IoU"], 결과["바탕만"], 결과["차"], 결과["화소mIoU"], 결과["통과"]))
