# 판정기준129 — 모델127 + 헝가리안 짝(a) · + 입력 4 채널 · 첫 보폭 1(b) · 기준은 판정기준129.json · 10-22
# 사용(cadrille): 모델129.py 학습 a|b → 모델129.py 평가 a|b → out/설명/캐드부품/모델129a|b/
import sys, os, json, time, numpy as np
import 모델124 as B, 조립124 as C, 모델127 as M7, 모델125 as T5
저장점 = M7.저장점
def 경로(판): d = f"G:/art2real/out/설명/캐드부품/모델129{판}/"; os.makedirs(d + "렌더", exist_ok=True); os.makedirs(d + "점검", exist_ok=True); return d
def 망(판):
    import torch, torch.nn as nn
    net = M7.망()
    if 판 in ("b", "c"):   # c = b 의 입력만 · loss 는 127 그대로(부피 순 짝) — 10-22 사용자 「convolution 문제만 풀라고 했는데」 · 실선 · 숨은선 · 좌표 x · y = 4 채널 · 첫 합성곱 보폭 1 · 끝 평균 풀(토큰 8×8 유지)
        torch.manual_seed(0); net.cnn[0][0] = nn.Conv2d(4, 32, 3, 1, 1); net.cnn.append(nn.AvgPool2d(2))
        def 전처리(x):
            b = len(x); x = x.reshape(b * 3, 1, M7.S, M7.S); 실 = (x == 255).float(); 숨 = ((x > 0) & (x < 255)).float()
            g = torch.linspace(-1, 1, M7.S, device=x.device); yy, xx = torch.meshgrid(g, g, indexing="ij")
            return torch.cat([실, 숨, xx.expand(b * 3, 1, -1, -1), yy.expand(b * 3, 1, -1, -1)], 1)
        net.전처리 = 전처리
        def forward(x, s=net):
            b = len(x); f = s.cnn(s.전처리(x)); m = (f.flatten(2).transpose(1, 2).reshape(b, 3, 64, -1) + s.자리 + s.시점).reshape(b, 192, -1)
            return s.출(s.dec(s.칸.expand(b, -1, -1), m)).reshape(b, -1)
        net.forward = forward
    return net
def 짝(o, Y):   # 헝가리안: 배치마다 칸 6 × 덩어리 비용 → 짝 받은 칸 = 그 덩어리 과녁 · 못 받은 칸 = 0(없음) · 반환 (과녁 순서 바꿈 인덱스, 있음 가리개)
    import torch
    from scipy.optimize import linear_sum_assignment as H
    with torch.no_grad():
        lp = o[..., 1:8].log_softmax(-1); la = o[..., 17:20].log_softmax(-1)   # (b, 6, ·)
        종 = -(lp[:, :, None] * Y[:, None, :, 1:8]).sum(-1); 축 = -(la[:, :, None] * Y[:, None, :, 17:20]).sum(-1)
        치 = ((o[:, :, None, 8:17] - Y[:, None, :, 8:17]).abs() * (Y[:, None, :, 8:17] != 0)).sum(-1) * 4; 자 = (o[:, :, None, 20:23] - Y[:, None, :, 20:23]).abs().sum(-1) * 4
        비 = (종 + 축 + 치 + 자).cpu().numpy(); 있 = (Y[..., 0] > 0).cpu().numpy()
    순 = np.zeros((len(o), 6), np.int64); 가 = np.zeros((len(o), 6), bool)
    for b in range(len(o)):
        t = np.nonzero(있[b])[0]; r_, c_ = H(비[b][:, t]); 순[b, r_] = t[c_]; 가[b, r_] = True
    return torch.tensor(순, device=o.device), torch.tensor(가, device=o.device)
def 바꾼과녁(o, Y, 쓰):
    import torch
    순, 가 = 짝(o, Y); ar = torch.arange(len(Y), device=Y.device)[:, None]
    return Y[ar, 순] * 가[..., None], 쓰[ar, 순] * 가[..., None]
def 학습(판, 끝=60):   # 10-22 사용자 「10 에폭으로 attention map 확인 · 괜찮으면 더」 → 끝 에폭까지만 · 점검/마지막.pt(모델 + 옵티마이저 + 기록)에서 이어 함 · 학습률 일정 없음이라 이어 해도 한 번에 돈 것과 같음
    import torch, 손실그림124 as L
    D = 경로(판); dev = "cuda"; z = np.load(M7.D + "그림.npz"); 이 = list(z["이름"]); 색 = {f"{r['i']:05d}": r for r in B.색인()}
    X = torch.tensor(z["X"]).to(dev); 과 = [B.과녁(색[n]) for n in 이]
    Y = torch.tensor(np.stack([a for a, _ in 과])).to(dev); 쓰 = torch.tensor(np.stack([b for _, b in 과])).to(dev)
    시험 = np.array([int(n) >= B.NT for n in 이]); idx = torch.tensor(np.nonzero(~시험)[0]); vx = torch.tensor(np.nonzero(시험)[0]); 고정 = vx[:6]
    net = 망(판).to(dev); opt = torch.optim.AdamW(net.parameters(), 3e-4, weight_decay=1e-4); 미세 = 128 if 판 == "a" else 32
    def 손실(o, ix):
        o = o.reshape(-1, C.K, B.W)
        if 판 == "c": return sum(L.항목(o, Y[ix], 쓰[ix]).values())   # 127 과 같은 짝
        y, s = 바꾼과녁(o, Y[ix], 쓰[ix]); return sum(L.항목(o, y, s).values())
    기록 = []; 과정 = {}; t0 = time.time(); 시작 = 0
    if os.path.exists(D + "점검/마지막.pt"):
        k = torch.load(D + "점검/마지막.pt"); net.load_state_dict(k["모델"]); opt.load_state_dict(k["옵티"]); 시작, 기록, 과정 = k["에폭"], k["기록"], k["과정"]; print("이어 함", 시작, flush=True)
    for ep in range(시작, 끝):
        net.train(); perm = idx[torch.randperm(len(idx))]; ls = []
        for b in range(0, len(perm), 128):   # b 판은 32 씩 나눠 기울기 누적(보폭 1 로 중간 값 4 배 · 8 GB) · 덩어리 수 정규화가 조각마다라 128 한 번과 아주 조금 다름
            ix = perm[b:b + 128]; opt.zero_grad(); lt = 0.
            for c in range(0, len(ix), 미세): jx = ix[c:c + 미세]; l = 손실(net(X[jx]), jx) * len(jx) / len(ix); l.backward(); lt += float(l)
            opt.step(); ls.append(lt)
        net.eval()
        with torch.no_grad(): ov = torch.cat([net(X[vx[i:i + 50]]) for i in range(0, len(vx), 50)]); lv = float(손실(ov, vx)); 수 = float(((ov.reshape(-1, C.K, B.W)[..., 0] > 0).sum(1) == Y[vx][..., 0].sum(1)).float().mean())
        기록.append({"에폭": ep + 1, "학습": float(np.mean(ls)), "시험": lv, "몸 수 맞음": 수, "초": round(time.time() - t0)}); print(기록[-1], flush=True)
        if ep in (0, 2, 5, 10, 20, 40, 59):
            with torch.no_grad(): 과정[ep + 1] = net(X[고정]).reshape(-1, C.K, B.W).cpu().numpy().tolist()
        torch.save(net.state_dict(), D + f"점검/{ep + 1:02d}.pt")
        torch.save({"모델": net.state_dict(), "옵티": opt.state_dict(), "에폭": ep + 1, "기록": 기록, "과정": 과정}, D + "점검/마지막.pt")
    torch.save(net.state_dict(), D + "머리.pt")
    json.dump({"기록": 기록, "과정": 과정, "고정": [이[int(i)] for i in 고정]}, open(D + "학습.json", "w", encoding="utf-8"), ensure_ascii=False); print("저장")
def 짝재기(net, X, Y):   # 헝가리안 짝으로 자리 오차 · 종류 맞음(시험) — 127 · 129a · 129b 같은 자
    import torch
    with torch.no_grad(): o = torch.cat([net(torch.tensor(X[i:i + 64])) for i in range(0, len(X), 64)]).reshape(-1, C.K, B.W)
    Yt = torch.tensor(Y); 순, 가 = 짝(o, Yt); ar = torch.arange(len(Y))[:, None]; y = Yt[ar, 순]
    자 = (o[..., 20:23] - y[..., 20:23]).abs().sum(-1)[가]; 종 = (o[..., 1:8].argmax(-1) == y[..., 1:8].argmax(-1))[가]
    return {"짝 자리 오차": round(float(자.mean()), 4), "짝 종류 맞음": round(float(종.float().mean()), 4)}
def 평가(판):
    import torch
    D = 경로(판); z = np.load(M7.D + "그림.npz"); 이 = list(z["이름"]); 색 = {f"{r['i']:05d}": r for r in B.색인()}
    net = 망(판); net.load_state_dict(torch.load(D + "머리.pt")); net.eval(); 시 = [n for n in 이 if int(n) >= B.NT]
    Xs = z["X"][[이.index(n) for n in 시]]; Ys = np.stack([B.과녁(색[n])[0] for n in 시]); 짝값 = 짝재기(net, Xs, Ys)
    n7 = M7.망(); n7.load_state_dict(torch.load(M7.D + "머리.pt")); n7.eval(); 짝값["127 같은 자"] = 짝재기(n7, Xs, Ys); print(짝값, flush=True)
    json.dump(짝값, open(D + "짝재기.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); del Xs
    T5.평가(net, lambda ns: torch.tensor(z["X"][[이.index(n) for n in ns]]), D)
if __name__ == "__main__":
    {"학습": 학습, "평가": 평가}[sys.argv[1]](sys.argv[2], *[int(a) for a in sys.argv[3:]])
