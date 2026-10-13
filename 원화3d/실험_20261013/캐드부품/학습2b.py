# 판정기준31 ② — 2b: 위 · 앞 · 옆 선 그림 3 채널 → 같은 U-Net(입력만 3) · 15 에폭 · 끝에 시험 예측 저장(부피는 평가31b.py) · 10-13
import os, json, time, numpy as np
import 학습 as T
O = "G:/art2real/out/설명/캐드부품/학습2b/"; os.makedirs(O, exist_ok=True); 에폭 = 15
if __name__ == "__main__":
    import torch, torch.nn.functional as Fn
    torch.manual_seed(31); dev = "cuda"; d = np.load("G:/art2real/out/설명/캐드부품/데이터.npz"); e = np.load("G:/art2real/out/설명/캐드부품/데이터_앞옆.npz")
    X = np.stack([d["X"], e["F"], e["S"]], 1); Y, D, 시 = d["Y"], d["D"].astype(np.float32), d["시험"]; del e
    tr, te = np.nonzero(~시)[0], np.nonzero(시)[0]
    m = T.U만들기(3)().to(dev); opt = torch.optim.Adam(m.parameters(), 1e-3); w = torch.tensor([1., 1., 3., 1.5], device=dev); 기록 = []; t0 = time.time()
    def 예측(idx):
        m.eval(); C, Dp = [], []
        with torch.no_grad():
            for k in range(0, len(idx), 64):
                lo, dp = m(torch.tensor(X[idx[k:k + 64]], dtype=torch.float32, device=dev)); C.append(lo.argmax(1).cpu().numpy().astype(np.uint8)); Dp.append(dp.cpu().numpy())
        m.train(); return np.concatenate(C), np.concatenate(Dp)
    def mIoU(P, Tt): return float(np.mean([((P == c) & (Tt == c)).sum() / max(((P == c) | (Tt == c)).sum(), 1) for c in (1, 2, 3)]))
    for ep in range(에폭 + 1):
        P, Dp = 예측(te); Yt = Y[te]; mm = Yt == 3; 오차 = float(np.median(np.abs(Dp[mm] - D[te][mm]))); mi = mIoU(P, Yt); 기록.append({"에폭": ep, "mIoU": mi, "깊이오차중앙": 오차})
        print("에폭 %2d · 시험 화소 mIoU %.3f · 들어감 깊이 오차 중앙 %.3f · %.0f 초" % (ep, mi, 오차, time.time() - t0), flush=True); json.dump(기록, open(O + "기록.json", "w"))
        if ep == 에폭: break
        perm = np.random.default_rng(ep).permutation(tr)
        for k in range(0, len(perm), 32):
            i = perm[k:k + 32]; x = torch.tensor(X[i], dtype=torch.float32, device=dev); dd = torch.tensor(D[i], device=dev); y = torch.tensor(Y[i], device=dev).long(); lo, dp = m(x)
            l = Fn.cross_entropy(lo, y, weight=w) + 2 * (((dp - dd).abs()) * (y == 3)).sum() / max(int((y == 3).sum()), 1); opt.zero_grad(); l.backward(); opt.step()
    torch.save(m.state_dict(), O + "망.pt"); np.savez_compressed(O + "시험예측.npz", P=P, D=Dp.astype(np.float16)); print("끝")
