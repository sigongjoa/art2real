# 판정기준120 짝 확인 — ① 학습에 들어간 (입력 그림, 정답 코드) 가 같은 부품인가: 그림 파일 | 정답 코드를 같은 시점으로 다시 렌더 | 모델 예측(같은 시점) ② 정답을 섞어 학습하면 시험 종류가 찍기(≈ 0.2)로 떨어지는가 · 10-20
# 사용: (gemma venv) 확인120.py 섞기 → (cadrille venv) 확인120.py 그림 → out/설명/캐드부품/모델120/짝확인.png
import sys, json, numpy as np
import 모델120 as M
D = M.D
def 섞기():
    import torch, torch.nn as nn
    색 = json.load(open(D + "색인.json", encoding="utf-8")); E = torch.tensor(np.load(D + "임베딩.npz")["E"]); K = torch.tensor([M.과녁(json.loads(r["코드"]))["k"] for r in 색])
    시 = torch.tensor([r["i"] >= M.NT for r in 색]); out = {}
    for 판 in ("제대로", "섞음"):
        torch.manual_seed(0); Kt = K.clone(); tr = torch.nonzero(~시).ravel()
        if 판 == "섞음": Kt[tr] = K[tr][torch.randperm(len(tr))]
        net = nn.Sequential(nn.Linear(768, 512), nn.GELU(), nn.Linear(512, 7)); opt = torch.optim.AdamW(net.parameters(), 1e-3)
        for ep in range(20):
            p = tr[torch.randperm(len(tr))]
            for b in range(0, len(p), 128): ix = p[b:b + 128]; opt.zero_grad(); nn.functional.cross_entropy(net(E[ix]), Kt[ix]).backward(); opt.step()
        vx = torch.nonzero(시).ravel(); out[판] = float((net(E[vx]).argmax(1) == K[vx]).float().mean())
    print(out); json.dump(out, open(D + "섞기.json", "w"), ensure_ascii=False)
def 그림():
    import cv2, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    import 설계116 as S, 데이터117 as Q
    plt.rcParams["font.family"] = "Malgun Gothic"; j = json.load(open(D + "학습.json", encoding="utf-8")); 섞 = json.load(open(D + "섞기.json"))
    fig, ax = plt.subplots(4, 6, figsize=(16, 11))
    for k in range(8):
        n, p, g = j["시험"]["번호"][k * 7], j["시험"]["예측"][k * 7], json.loads(j["시험"]["정답"][k * 7])
        rng = np.random.default_rng(120000 + n); s = S.무작위(rng); assert M.사양(**{}) if False else True; assert json.dumps(s, sort_keys=True, ensure_ascii=False) == json.dumps(g, sort_keys=True, ensure_ascii=False), "색인 코드 ≠ 시드로 다시 만든 코드"
        a, e = float(rng.uniform(0, 360)), float(rng.uniform(15, 35))   # 짓기 때와 같은 시점
        ims = [cv2.imdecode(np.fromfile(D + f"렌더/{n:05d}.png", np.uint8), 1)[..., ::-1], Q.렌더(S.메시(S.짓기(g))[0], a, e)[0], Q.렌더(S.메시(S.짓기(p))[0], a, e)[0]]
        for t, (im, lab) in enumerate(zip(ims, (f"입력 그림 #{n}", f"정답 코드 · {g['바탕']['종류']}", f"예측 코드 · {p['바탕']['종류']}"))):
            x = ax[k // 2, (k % 2) * 3 + t]; x.imshow(im); x.axis("off"); x.set_title(lab, fontsize=10, color="#28a050" if t == 2 else "#333")
    fig.suptitle(f"학습 짝 확인 — 처음 보는 시험 부품 · 세 칸 모두 입력과 같은 시점 · 정답을 섞어 학습하면 시험 종류 {섞['섞음']:.2f} (제대로 {섞['제대로']:.2f})", fontsize=13)
    plt.tight_layout(); plt.savefig(D + "짝확인.png", dpi=70); print("저장")
if __name__ == "__main__": {"섞기": 섞기, "그림": 그림}[sys.argv[1]]()
