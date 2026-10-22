# 판정기준127 — Gemma 빼고 3면도 그림을 직접: 작은 CNN(그림마다 8×8 조각 64 토큰 · 위치 남김) → 모델125 와 같은 트랜스포머 디코더(칸 쿼리 6) · 데이터 · loss · 평가 그대로 · 10-22
# 사용: (cadrille) 모델127.py 그림 → 학습 → 평가 → out/설명/캐드부품/모델127/
import sys, os, json, time, numpy as np
import 모델124 as B, 조립124 as C, 모델125 as T5
D = "G:/art2real/out/설명/캐드부품/모델127/"; os.makedirs(D + "렌더", exist_ok=True); os.makedirs(D + "점검", exist_ok=True); S = 128; 저장점 = (1, 2, 3, 5, 8, 12, 20, 30, 45, 60)
def 그림():   # 3면도 256 RGB → 회색 반전(선 = 1) 128 · uint8 한 파일
    import cv2
    이 = [f"{r['i']:05d}" for r in B.색인()]; X = np.zeros((len(이), 3, S, S), np.uint8)
    for k, n in enumerate(이):
        for v, nm in enumerate(B.뷰): X[k, v] = 255 - cv2.resize(cv2.imdecode(np.fromfile(B.D + f"도면/{n}_{nm}.png", np.uint8), 0), (S, S), interpolation=cv2.INTER_AREA)
    np.savez(D + "그림.npz", X=X, 이름=np.array(이)); print("끝", X.shape)
def 망():
    import torch, torch.nn as nn
    torch.manual_seed(0)
    def 블(a, b): return nn.Sequential(nn.Conv2d(a, b, 3, 2, 1), nn.GroupNorm(8, b), nn.GELU(), nn.Conv2d(b, b, 3, 1, 1), nn.GroupNorm(8, b), nn.GELU())
    class 머리(nn.Module):   # 입력 (배치, 3, 128, 128) uint8 → (배치, 6 × 41)
        def __init__(s, d=256):
            super().__init__(); s.cnn = nn.Sequential(블(1, 32), 블(32, 64), 블(64, 128), 블(128, d))   # 128 → 8
            s.자리 = nn.Parameter(torch.randn(64, d) * .02); s.시점 = nn.Parameter(torch.randn(3, 1, d) * .02); s.칸 = nn.Parameter(torch.randn(C.K, d) * .02)
            s.dec = nn.TransformerDecoder(nn.TransformerDecoderLayer(d, 8, 1024, .1, batch_first=True, norm_first=True), 4); s.출 = nn.Linear(d, B.W)
        def forward(s, x):
            b = len(x); f = s.cnn(x.reshape(b * 3, 1, S, S).float() / 255.)   # (b·3, d, 8, 8)
            m = (f.flatten(2).transpose(1, 2).reshape(b, 3, 64, -1) + s.자리 + s.시점).reshape(b, 192, -1)
            return s.출(s.dec(s.칸.expand(b, -1, -1), m)).reshape(b, -1)
    return 머리()
def 학습():
    import torch, 손실그림124 as L
    dev = "cuda"; z = np.load(D + "그림.npz"); 이 = list(z["이름"]); 색 = {f"{r['i']:05d}": r for r in B.색인()}
    X = torch.tensor(z["X"]).to(dev); 과 = [B.과녁(색[n]) for n in 이]
    Y = torch.tensor(np.stack([a for a, _ in 과])).to(dev); 쓰 = torch.tensor(np.stack([b for _, b in 과])).to(dev)
    시험 = np.array([int(n) >= B.NT for n in 이]); idx = torch.tensor(np.nonzero(~시험)[0]); vx = torch.tensor(np.nonzero(시험)[0]); 고정 = vx[:6]
    net = 망().to(dev); opt = torch.optim.AdamW(net.parameters(), 3e-4, weight_decay=1e-4)
    손실 = lambda o, ix: sum(L.항목(o.reshape(-1, C.K, B.W), Y[ix], 쓰[ix]).values())
    기록 = []; 과정 = {}; t0 = time.time()
    for ep in range(60):
        net.train(); perm = idx[torch.randperm(len(idx))]; ls = []
        for b in range(0, len(perm), 128): ix = perm[b:b + 128]; opt.zero_grad(); l = 손실(net(X[ix]), ix); l.backward(); opt.step(); ls.append(float(l))
        net.eval()
        with torch.no_grad(): ov = net(X[vx]); lv = float(손실(ov, vx)); 수 = float(((ov.reshape(-1, C.K, B.W)[..., 0] > 0).sum(1) == Y[vx][..., 0].sum(1)).float().mean())
        기록.append({"에폭": ep + 1, "학습": float(np.mean(ls)), "시험": lv, "몸 수 맞음": 수, "초": round(time.time() - t0)}); print(기록[-1], flush=True)
        if ep in (0, 2, 5, 10, 20, 40, 59):
            with torch.no_grad(): 과정[ep + 1] = net(X[고정]).reshape(-1, C.K, B.W).cpu().numpy().tolist()
        if ep + 1 in 저장점: torch.save(net.state_dict(), D + f"점검/{ep + 1:02d}.pt")   # 층별 보기(층보기127.py)용
    torch.save(net.state_dict(), D + "머리.pt")
    json.dump({"기록": 기록, "과정": 과정, "고정": [이[int(i)] for i in 고정]}, open(D + "학습.json", "w", encoding="utf-8"), ensure_ascii=False); print("저장")
def 평가():
    import torch
    z = np.load(D + "그림.npz"); 이 = list(z["이름"]); net = 망(); net.load_state_dict(torch.load(D + "머리.pt"))
    T5.평가(net, lambda ns: torch.tensor(z["X"][[이.index(n) for n in ns]]), D)
if __name__ == "__main__":
    {"그림": 그림, "학습": 학습, "평가": 평가}[sys.argv[1]]()
