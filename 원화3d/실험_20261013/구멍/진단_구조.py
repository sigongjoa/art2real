# 구조 문제냐 신호 문제냐 가르기 — 1c 와 같은 신경망(학습3.망만들기)을 정답 위치로 직접 가르쳐(지도 · CAD 안 지음) 구멍 · 홈 중심을 몇 mm 로 맞히나 · 10-13
# 판정(미리): 시험 위치 오차 중앙 ≤ 1.0 mm 면 「구조는 그림에서 위치를 읽을 수 있다 → 원인은 점수 신호가 드문 것」 · 아니면 구조 문제
import numpy as np, json
import 캐드점수2 as K, 학습3 as T
if __name__ == "__main__":
    import torch
    torch.manual_seed(1); dev = "cuda"
    def 묶음(n, 씨):
        g = np.random.default_rng(씨); P = [K.무작위(g) for _ in range(n)]; P = [p for p in P if any(c[0] for c in p["칸"])]
        X = np.stack([K.그림(p) for p in P]); Y = np.zeros((len(P), 3, 2), np.float32); 유 = np.zeros((len(P), 3), np.float32)
        for i, p in enumerate(P):
            for j, c in enumerate(p["칸"]):
                if c[0]: Y[i, j] = c[1:3]; 유[i, j] = 1
        return X, Y, 유
    Xtr, Ytr, Utr = 묶음(3000, 27); Xte, Yte, Ute = 묶음(200, 2027)
    m = T.망만들기()().to(dev); opt = torch.optim.Adam(m.parameters(), 1e-3)
    def 손실(pred, Y, U):   # 정답 특징마다 가장 가까운 예측 칸까지 거리(순서 무관) — 있는 특징만
        d = ((pred[:, None, :, :] - Y[:, :, None, :]) ** 2).sum(-1)   # (배치, 정답 3, 예측 3)
        return (d.min(-1).values.clamp(min=0).sqrt() * U).sum() / U.sum()
    Xt, Yt, Ut = [torch.tensor(a, device=dev) for a in (Xtr, Ytr, Utr)]; Xv, Yv, Uv = [torch.tensor(a, device=dev) for a in (Xte, Yte, Ute)]
    for ep in range(40):
        perm = torch.randperm(len(Xt), device=dev); m.train()
        for k in range(0, len(Xt), 64):
            i = perm[k:k + 64]; _, cv = m(Xt[i]); l = 손실(cv[..., :2], Yt[i], Ut[i]); opt.zero_grad(); l.backward(); opt.step()
        if ep % 5 == 4 or ep == 0:
            m.eval()
            with torch.no_grad():
                _, cv = m(Xv); d = ((cv[:, None, :, :2] - Yv[:, :, None, :]) ** 2).sum(-1).min(-1).values.sqrt(); e = d[Uv > 0].cpu().numpy()
            print("에폭 %2d · 시험 위치 오차 중앙 %.2f mm · 1 mm 안 %.0f%% · 2 mm 안 %.0f%%" % (ep + 1, np.median(e), 100 * (e < 1).mean(), 100 * (e < 2).mean()), flush=True)
    가운데 = np.sqrt((Yte ** 2).sum(-1))[Ute > 0]; print("대조(늘 가운데 찍기) 오차 중앙 %.2f mm" % np.median(가운데))
