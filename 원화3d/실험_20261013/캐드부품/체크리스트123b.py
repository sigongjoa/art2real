# 123b 머리에 ml-training-recipes 디버깅 체크리스트 돌리기 — 배치 하나 외우기 · 기울기 크기 · 죽은 뉴런 · 라벨 왕복 · 10-21
# 사용(cadrille venv · ART_CL=0): 체크리스트123b.py → out/설명/캐드부품/모델123b/확인/체크리스트.json
import os, json, numpy as np, torch, torch.nn as nn
os.environ["ART_CL"] = "0"
import 모델123 as T, 모델120 as M
색 = json.load(open(M.D + "색인.json", encoding="utf-8")); z = np.load(T.D + "임베딩.npz"); 번 = {n: k for k, n in enumerate(z["이름"])}
E = torch.tensor(z["E"][[번[f"{r['i']:05d}"] for r in 색]]).reshape(len(색), -1); 과 = [M.과녁(json.loads(r["코드"])) for r in 색]
tr = np.array([r["i"] < M.NT for r in 색]); idx = torch.tensor(np.nonzero(tr)[0]); 시 = lambda key: torch.tensor(np.stack([np.array(g[key]) for g in 과]))
K, 치, 칸쓰, 특, 필, 기 = 시("k").long(), 시("치"), 시("칸쓰"), 시("특"), 시("필"), 시("기")
def 망(): torch.manual_seed(0); return nn.Sequential(nn.Linear(2304, 512), nn.GELU(), nn.Dropout(.1), nn.Linear(512, 512), nn.GELU(), nn.Linear(512, 36))
def 손실(o, ix):   # 모델123 학습() 과 같음
    k, c, f, fi, ti = o[:, :7], o[:, 7:16], o[:, 16:32].reshape(-1, 2, 8), o[:, 32:34], o[:, 34:36]; bce = nn.functional.binary_cross_entropy_with_logits
    L = nn.functional.cross_entropy(k, K[ix]) + ((c - 치[ix]).abs() * 칸쓰[ix]).sum(1).mean() * 4
    L = L + bce(f[..., 0], 특[ix][..., 0]) + (nn.functional.cross_entropy(f[..., 1:4].reshape(-1, 3), 특[ix][..., 1:4].argmax(-1).reshape(-1), reduction="none") * 특[ix][..., 0].reshape(-1)).mean() + ((f[..., 4:] - 특[ix][..., 4:]).abs().sum(-1) * 특[ix][..., 0]).mean() * 2
    return L + bce(fi[:, 0], 필[ix][:, 0]) + bce(ti[:, 0], 기[ix][:, 0]) + ((ti[:, 1] - 기[ix][:, 1]).abs() * 기[ix][:, 0]).mean() * 2 + ((fi[:, 1] - 필[ix][:, 1]).abs() * 필[ix][:, 0]).mean()
결 = {}
# 1 배치 하나 외우기(드롭아웃 끔) — 못 외우면 버그
net = 망(); net.eval(); b = idx[:128]; opt = torch.optim.AdamW(net.parameters(), 1e-3, weight_decay=0); 줄 = []
for s in range(1500):
    opt.zero_grad(); l = 손실(net(E[b]), b); l.backward(); opt.step()
    if s in (0, 99, 499, 1499): 줄.append(round(float(l), 4))
with torch.no_grad(): o = net(E[b])
결["1 배치 하나 외우기"] = {"손실(0·100·500·1500 스텝)": 줄, "종류 맞음": float((o[:, :7].argmax(1) == K[b]).float().mean()), "치수 L1 평균": float(((o[:, 7:16] - 치[b]).abs() * 칸쓰[b]).sum() / 칸쓰[b].sum())}
# 2 원래 학습 그대로 돌리며 기울기 크기 · LR 기록
net = 망(); opt = torch.optim.AdamW(net.parameters(), 1e-3, weight_decay=1e-4); gn = []
for ep in range(60):
    perm = idx[torch.randperm(len(idx))]; g = []
    for i in range(0, len(perm), 128):
        ix = perm[i:i + 128]; opt.zero_grad(); 손실(net(E[ix]), ix).backward(); g.append(float(torch.nn.utils.clip_grad_norm_(net.parameters(), 1e9))); opt.step()
    gn.append((ep + 1, round(float(np.median(g)), 3), round(float(np.max(g)), 3)))
결["2 기울기 크기(에폭 · 중앙 · 최대)"] = [x for x in gn if x[0] in (1, 2, 3, 5, 10, 20, 40, 60)]; 결["2 LR"] = "1e-3 고정(스케줄 없음)"
# 3 죽은 뉴런(학습 집합에서 GELU 출력이 늘 ≤ 0)
net.eval(); h = {}
for j in (1, 4): net[j].register_forward_hook(lambda m, i, o, j=j: h.__setitem__(j, o))
with torch.no_grad(): net(E[idx])
결["3 죽은 뉴런 몫(층1 · 층2)"] = [round(float((h[j] <= 0).all(0).float().mean()), 3) for j in (1, 4)]
# 4 라벨 왕복: 과녁 → 사양 → 과녁 이 같은가(라벨 오류)
다름 = 0
for g in 과[:1000]:
    s = M.사양(g["k"], g["치"], g["특"], g["필"], g["기"]); g2 = M.과녁(s); 다름 += int(g2["k"] != g["k"] or not np.allclose(np.array(g2["치"]) * np.array(g["칸쓰"]), np.array(g["치"]) * np.array(g["칸쓰"]), atol=1e-4))
결["4 라벨 왕복 다름(1000 중)"] = 다름
json.dump(결, open(T.D + "확인/체크리스트.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결, ensure_ascii=False, indent=1))
