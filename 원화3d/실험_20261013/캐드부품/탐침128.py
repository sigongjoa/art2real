# 탐침128 — 모델127 CNN 블록 1~4 가 곡률 · 접합 · 교차를 가르는가 · 합성 그림 · 선형 탐침 · 학습 없음 · 기준은 판정기준128.json · 10-22
# 사용(cadrille): 탐침128.py → out/설명/캐드부품/탐침128/
import os, json, numpy as np, cv2
D = "G:/art2real/out/설명/캐드부품/탐침128/"; os.makedirs(D, exist_ok=True)
종들 = ["직선", "곡선", "모서리", "T 접합", "교차", "실선×숨은선"]; 실, 숨 = 255, 115
def 점선(im, p, q, v):   # 숨은선 = 회색 점선(3 화소 그림 · 3 화소 빔)
    n = int(np.hypot(*(np.subtract(q, p)))) + 1
    for t in range(n):
        if (t // 3) % 2 == 0: x, y = np.round(np.add(p, np.subtract(q, p) * t / max(n - 1, 1))).astype(int); 0 <= x < im.shape[1] and 0 <= y < im.shape[0] and im.__setitem__((y, x), v)
def 한장(종, rng, S=128):   # 가운데 c 에 구조 하나 + 멀리 방해 선 둘 · 반환 (그림, 가운데, 반지름)
    k = S / 128; im = np.zeros((S, S), np.uint8); c = rng.uniform(40, 88, 2) * k; a = rng.uniform(0, np.pi); L = rng.uniform(18, 30) * k; r = 0.
    u = np.array([np.cos(a), np.sin(a)]); v = np.array([-u[1], u[0]]); P = lambda x: tuple(np.round(x).astype(int))
    if 종 == "직선": cv2.line(im, P(c - L * u), P(c + L * u), 실, max(1, int(k)))
    elif 종 == "곡선":
        r = float(np.exp(rng.uniform(np.log(6), np.log(120)))) * k; o = c + r * v; 각 = np.degrees(np.arctan2(-v[1], -v[0])); 폭 = np.degrees(min(L / r, np.pi * .9))
        cv2.ellipse(im, P(o), (int(round(r)), int(round(r))), 0, 각 - 폭, 각 + 폭, 실, max(1, int(k)))
    elif 종 == "모서리": b = a + np.radians(rng.uniform(45, 135)); w = np.array([np.cos(b), np.sin(b)]); cv2.line(im, P(c), P(c + L * u), 실, max(1, int(k))); cv2.line(im, P(c), P(c + L * w), 실, max(1, int(k)))
    elif 종 == "T 접합": cv2.line(im, P(c - L * u), P(c + L * u), 실, max(1, int(k))); cv2.line(im, P(c), P(c + L * v), 실, max(1, int(k)))
    elif 종 == "교차": b = a + np.radians(rng.uniform(40, 140)); w = np.array([np.cos(b), np.sin(b)]); cv2.line(im, P(c - L * u), P(c + L * u), 실, max(1, int(k))); cv2.line(im, P(c - L * w), P(c + L * w), 실, max(1, int(k)))
    else: b = a + np.radians(rng.uniform(40, 140)); w = np.array([np.cos(b), np.sin(b)]); cv2.line(im, P(c - L * u), P(c + L * u), 실, max(1, int(k))); 점선(im, c - L * w, c + L * w, 숨)
    for _ in range(2):   # 방해 선: 가운데에서 40 화소(128 기준) 넘게 떨어진 곳
        while True:
            p = rng.uniform(0, S, 2)
            if np.linalg.norm(p - c) > 40 * k: break
        q = p + rng.uniform(-20, 20, 2) * k; cv2.line(im, P(p), P(q), 실, max(1, int(k)))
    return im, c, r
def 특징(net, ims, cs, S, 묶=256):   # 블록마다 구조 가운데가 든 칸의 특징 · 256 장씩(256 화소 그림 3600 장 한 번에 7.5 GB)
    import torch
    out = {}; 묶 = 묶 if net.cnn[0][0].stride[0] == 2 else 64   # 보폭 1(모델129b · c)은 중간 값 4 배
    with torch.no_grad():
        for s in range(0, len(ims), 묶):
            x = torch.tensor(np.stack(ims[s:s + 묶]))[:, None]; c = np.array(cs[s:s + 묶])
            if net.cnn[0][0].in_channels == 4:   # 모델129c · b: 실선 · 숨은선 · 좌표 x · y (모델129.망 의 전처리와 같은 꼴 · 그림 크기 S 에 맞춤)
                g = torch.linspace(-1, 1, S); yy, xx = torch.meshgrid(g, g, indexing="ij")
                h = torch.cat([(x == 255).float(), ((x > 0) & (x < 255)).float(), xx.expand(len(x), 1, -1, -1), yy.expand(len(x), 1, -1, -1)], 1)
            else: h = x.float() / 255.
            for i, 블 in enumerate(net.cnn):
                h = 블(h); st = S // h.shape[-1]; ix = torch.tensor((c // st).astype(int)).clamp(0, h.shape[-1] - 1)
                out.setdefault(f"블록 {i + 1}", []).append(h[torch.arange(len(h)), :, ix[:, 1], ix[:, 0]].numpy())
    return {k: np.concatenate(v) for k, v in out.items()}
def 릿지(X, y, 학, 시, 분류):
    mu, sd = X[학].mean(0), X[학].std(0) + 1e-6; X = np.c_[(X - mu) / sd, np.ones(len(X))]; 최 = None; 검 = 학[-len(학) // 5:]; 맞 = 학[:-len(학) // 5]
    T = np.eye(int(y.max()) + 1)[y] if 분류 else y[:, None]
    def 점(W, ix): p = X[ix] @ W; return float((p.argmax(1) == y[ix]).mean()) if 분류 else float(1 - ((p[:, 0] - y[ix]) ** 2).sum() / ((y[ix] - y[ix].mean()) ** 2).sum())
    for lam in (1e-1, 1e0, 1e1, 1e2, 1e3):
        W = np.linalg.solve(X[맞].T @ X[맞] + lam * np.eye(X.shape[1]), X[맞].T @ T[맞]); s = 점(W, 검)
        if 최 is None or s > 최[0]: 최 = (s, lam)
    W = np.linalg.solve(X[학].T @ X[학] + 최[1] * np.eye(X.shape[1]), X[학].T @ T[학]); return round(점(W, 시), 4)
if __name__ == "__main__":
    import torch, 모델127 as M7
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; plt.rcParams["font.family"] = "Malgun Gothic"
    # 인자 없으면 10-22 첫 판(127 60 에폭 · 무작위) · 있으면 「이름=판:에폭」 여럿(판 127 | a | b | c · 에폭 2 자리 점검 · 0 = 무작위 초기) → 결과_<이름들>.json
    def 불러(판, ep):
        import 모델129 as M9
        net = M7.망() if 판 == "127" else M9.망(판); 경 = M7.D if 판 == "127" else M9.경로(판)
        if ep: net.load_state_dict(torch.load(경 + (f"점검/{ep:02d}.pt" if ep < 60 or 판 != "127" else "머리.pt")))
        return net
    import sys
    인자 = sys.argv[1:] or ["127 CNN(학습)=127:60", "무작위 CNN=127:0"]
    nets = {k: 불러(v.split(":")[0], int(v.split(":")[1])) for k, v in (a.split("=") for a in 인자)}
    for n in nets.values(): n.eval()
    결 = {}
    for S in (128, 256):
        rng = np.random.default_rng(128); 자료 = [(k, *한장(종, rng, S)) for k, 종 in enumerate(종들) for _ in range(600)]
        y = np.array([a[0] for a in 자료]); ims = [a[1] for a in 자료]; cs = [a[2] for a in 자료]; rr = np.array([a[3] for a in 자료])
        idx = np.random.default_rng(0).permutation(len(y)); 학, 시 = idx[:2400], idx[2400:]; 곡 = y == 1; 학곡, 시곡 = 학[곡[학]], 시[곡[시]]
        if S == 128:
            fig, ax = plt.subplots(3, 6, figsize=(18, 9))
            for k in range(6):
                for j in range(3): t = np.nonzero(y == k)[0][j]; ax[j, k].imshow(ims[t], cmap="gray"); ax[j, k].plot(*cs[t], "r+", ms=14); ax[j, k].axis("off"); j == 0 and ax[j, k].set_title(종들[k], fontsize=15)
            fig.tight_layout(); fig.savefig(D + "예시.png", dpi=55); plt.close(fig)
            패치 = np.stack([np.pad(im, 8)[int(c[1]):int(c[1]) + 15, int(c[0]):int(c[0]) + 15].ravel() for im, c in zip(ims, cs)]).astype(float)   # 가운데 15×15
            결["가운데 15×15 화소"] = {"128": {"구조 6 종": 릿지(패치, y, 학, 시, True), "곡률 R²": 릿지(패치, np.log(rr), 학곡, 시곡, False)}}
        for 이름, net in nets.items():
            F = 특징(net, ims, cs, S)
            for b, X in F.items():
                결.setdefault(이름 + " " + b, {})[str(S)] = {"구조 6 종": 릿지(X, y, 학, 시, True), "곡률 R²": 릿지(X, np.log(rr / (S / 128)), 학곡, 시곡, False)}
        print(S, "끝", flush=True)
    json.dump(결, open(D + ("결과.json" if not sys.argv[1:] else "결과_" + "_".join(k.split("=")[0] for k in 인자).replace(" ", "") + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in 결.items(): print(k, v)
