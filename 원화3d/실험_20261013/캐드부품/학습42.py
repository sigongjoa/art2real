# 판정기준42 — 학습39 + 부피 벌점(칸마다 재료 기둥 · 부품마다 부드러운 부피 IoU) · 나머지 같음 · 10-14
import os, json, time, numpy as np
import 학습 as T
def 부피벌점(lo, dp, y, dd):   # 칸마다 재료 기둥(윗면 1 · 뚫음 0 · 들어감 1 − 깊이) → 부품마다 1 − 겹침/합침 · 없는 구멍은 기둥 통째 손해
    import torch
    p = torch.softmax(lo, 1); p1, p2, p3 = p[:, 1], p[:, 2], p[:, 3]; 안 = (y > 0).float(); t1, t2, t3 = (y == 1).float(), (y == 2).float(), (y == 3).float()
    겹 = t1 * (p1 + p3 * (1 - dp)) + t3 * (p1 * (1 - dd) + p3 * (1 - torch.maximum(dd, dp)))
    합 = t1 * 1 + t2 * (p1 + p3 * (1 - dp)) + t3 * (p1 + p3 * (1 - torch.minimum(dd, dp)) + p2 * (1 - dd))
    return (1 - (겹 * 안).sum((1, 2)) / ((합 * 안).sum((1, 2)) + 1e-6)).mean()
O = "G:/art2real/out/설명/캐드부품/학습42/"; os.makedirs(O, exist_ok=True); 에폭 = 15
if __name__ == "__main__":
    import torch, torch.nn.functional as Fn
    torch.manual_seed(31); dev = "cuda"; d = np.load("G:/art2real/out/설명/캐드부품/데이터.npz"); e = np.load("G:/art2real/out/설명/캐드부품/데이터_앞옆.npz"); R = np.load("G:/art2real/out/설명/캐드부품/데이터_회전.npz")["R"]
    X = np.concatenate([np.stack([d["X"], e["F"], e["S"]], 1).astype(np.float16), R], 1); Y, D, 시 = d["Y"], d["D"].astype(np.float32), d["시험"]; del e, R
    tr, te = np.nonzero(~시)[0], np.nonzero(시)[0]
    m = T.U만들기(5)().to(dev); opt = torch.optim.Adam(m.parameters(), 1e-3); w = torch.tensor([1., 1., 3., 1.5], device=dev); 기록 = []; t0 = time.time()
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
            l = Fn.cross_entropy(lo, y, weight=w) + 2 * (((dp - dd).abs()) * (y == 3)).sum() / max(int((y == 3).sum()), 1) + 부피벌점(lo, dp, y, dd); opt.zero_grad(); l.backward(); opt.step()
    torch.save(m.state_dict(), O + "망.pt"); np.savez_compressed(O + "시험예측.npz", P=P, D=Dp.astype(np.float16)); print("끝")
