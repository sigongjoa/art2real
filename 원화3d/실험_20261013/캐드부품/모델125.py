# 판정기준125 — 모델124 의 MLP 머리를 트랜스포머(칸 쿼리 6 · 3면도 토큰 3)로 · 입력 · 데이터 · loss 그대로 · 10-22
# 사용: (cadrille) 모델125.py 학습 → 모델125.py 평가 → out/설명/캐드부품/모델125/
import sys, os, json, time, numpy as np
import 모델124 as B, 조립124 as C
D = "G:/art2real/out/설명/캐드부품/모델125/"; os.makedirs(D + "렌더", exist_ok=True)
def 망():
    import torch, torch.nn as nn
    torch.manual_seed(0)
    class 머리(nn.Module):   # 입력 (배치, 2304) 그대로 받음 → 안에서 토큰 3 개 · 출력 (배치, 6 × 41) — 모델124 와 같은 꼴
        def __init__(s, d=256):
            super().__init__(); s.입 = nn.Linear(768, d); s.시점 = nn.Parameter(torch.randn(3, d) * .02); s.칸 = nn.Parameter(torch.randn(C.K, d) * .02)
            s.dec = nn.TransformerDecoder(nn.TransformerDecoderLayer(d, 8, 1024, .1, batch_first=True, norm_first=True), 4); s.출 = nn.Linear(d, B.W)
        def forward(s, x):
            m = s.입(x.reshape(-1, 3, 768)) + s.시점; q = s.칸.expand(len(x), -1, -1)
            return s.출(s.dec(q, m)).reshape(len(x), -1)
    return 머리()
def 학습():
    import torch, 손실그림124 as L
    dev = "cuda"; z = np.load(B.D + "임베딩.npz"); 색 = {f"{r['i']:05d}": r for r in B.색인()}; 이 = list(z["이름"])
    E = torch.tensor(z["E"]).reshape(len(이), -1).to(dev); 과 = [B.과녁(색[n]) for n in 이]
    Y = torch.tensor(np.stack([a for a, _ in 과])).to(dev); 쓰 = torch.tensor(np.stack([b for _, b in 과])).to(dev)
    시험 = np.array([int(n) >= B.NT for n in 이]); idx = torch.tensor(np.nonzero(~시험)[0]); vx = torch.tensor(np.nonzero(시험)[0]); 고정 = vx[:6]
    net = 망().to(dev); opt = torch.optim.AdamW(net.parameters(), 3e-4, weight_decay=1e-4)
    손실 = lambda o, ix: sum(L.항목(o.reshape(-1, C.K, B.W), Y[ix], 쓰[ix]).values())
    기록 = []; 과정 = {}; t0 = time.time()
    for ep in range(60):
        net.train(); perm = idx[torch.randperm(len(idx))]; ls = []
        for b in range(0, len(perm), 128): ix = perm[b:b + 128]; opt.zero_grad(); l = 손실(net(E[ix]), ix); l.backward(); opt.step(); ls.append(float(l))
        net.eval()
        with torch.no_grad(): ov = net(E[vx]); lv = float(손실(ov, vx)); 수 = float(((ov.reshape(-1, C.K, B.W)[..., 0] > 0).sum(1) == Y[vx][..., 0].sum(1)).float().mean())
        기록.append({"에폭": ep + 1, "학습": float(np.mean(ls)), "시험": lv, "몸 수 맞음": 수, "초": round(time.time() - t0)}); print(기록[-1], flush=True)
        if ep in (0, 2, 5, 10, 20, 40, 59):
            with torch.no_grad(): 과정[ep + 1] = net(E[고정]).reshape(-1, C.K, B.W).cpu().numpy().tolist()
    torch.save(net.state_dict(), D + "머리.pt")
    json.dump({"기록": 기록, "과정": 과정, "고정": [이[int(i)] for i in 고정]}, open(D + "학습.json", "w", encoding="utf-8"), ensure_ascii=False); print("저장")
def 평가(net=None, 입력=None, 출=D):   # 확인124 와 같은 학습 300 · 시험 299 · 같은 자 + 항목별 loss + 과정 렌더 · 모델127 은 net · 입력(이름들 → 텐서) · 출 을 넘김
    import torch, 손실그림124 as L
    z = np.load(B.D + "임베딩.npz"); 이 = list(z["이름"])
    if net is None: net = 망(); net.load_state_dict(torch.load(D + "머리.pt")); 입력 = lambda ns: torch.tensor(z["E"][[이.index(n) for n in ns]]).reshape(len(ns), -1)
    net.eval(); 색 = {f"{r['i']:05d}": r for r in B.색인()}; 이 = list(z["이름"]); 확 = json.load(open(B.D + "확인124.json", encoding="utf-8")); 결 = {}
    for 이름 in ("학습", "시험"):
        ns = 확[이름]["이름"]; 과 = [B.과녁(색[n]) for n in ns]; Y = torch.tensor(np.stack([a for a, _ in 과])); 쓰 = torch.tensor(np.stack([b for _, b in 과]))
        with torch.no_grad(): o = net(입력(ns)).reshape(-1, C.K, B.W).cpu()
        항 = {k: round(float(v), 4) for k, v in L.항목(o, Y, 쓰).items()}; o = o.numpy(); 있 = Y.numpy()[..., 0] > 0
        정 = B.병렬렌더([("조립", 색[n]["코드"]) for n in ns]); 예 = B.병렬렌더([("자리", B.사양(a)) for a in o])
        assert sum(g is None for g in 정) <= 5, "정답 렌더 실패 — 일꾼 문제부터"
        iou = np.array([0. if g is None or p is None else float((g[1] & p[1]).sum() / max((g[1] | p[1]).sum(), 1)) for g, p in zip(정, 예)]); 몸1 = 있.sum(1) == 1
        for n, p in list(zip(ns, 예))[:12]:
            if p is not None: B.M.저장(출 + f"렌더/{n}_예측.png", p[0])
        결[이름] = {"IoU 중앙": round(float(np.median(iou)), 4), "몸 1": round(float(np.median(iou[몸1])), 4), "몸 2+": round(float(np.median(iou[~몸1])), 4),
                   "몸 수 맞음": round(float(np.mean((o[..., 0] > 0).sum(1) == 있.sum(1))), 4), "종류 맞음": round(float((o[..., 1:8].argmax(-1) == Y.numpy()[..., 1:8].argmax(-1))[있].mean()), 4),
                   "항목 loss": 항, "IoU": [round(float(x), 4) for x in iou], "이름": ns}
        print(이름, {k: v for k, v in 결[이름].items() if k not in ("IoU", "이름")}, flush=True)
    j = json.load(open(출 + "학습.json", encoding="utf-8")); 키 = [(int(ep), t) for ep, os_ in j["과정"].items() for t in range(len(os_))]
    for (ep, t), r in zip(키, B.병렬렌더([("자리", B.사양(np.array(j["과정"][str(ep)][t]))) for ep, t in 키])):
        if r is not None: B.M.저장(출 + f"렌더/과정_{ep:02d}_{t}.png", r[0])
    json.dump(결, open(출 + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if __name__ == "__main__":
    {"학습": 학습, "평가": 평가}[sys.argv[1]]()
