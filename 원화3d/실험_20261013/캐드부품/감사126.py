# 감사126 — 124/125 파이프라인 단계 넘김 검사 · 학습 없음 · 기준은 판정기준126.json · 10-22
# 사용(cadrille · ART_MEM_GB=10): 감사126.py 왕복 | 자 | 그림 | 탐침 | 주의  ·  (gemma) 감사126.py 옮김임베딩  — 옮김은 (cadrille) 옮김도면 → (gemma) 옮김임베딩 → (cadrille) 옮김
import sys, os, json, copy, numpy as np
import 모델124 as B, 조립124 as C
D = "G:/art2real/out/설명/캐드부품/감사126/"; os.makedirs(D, exist_ok=True)
def 시험(): 색 = {f"{r['i']:05d}": r for r in B.색인()}; return 색, [n for n in sorted(색) if int(n) >= B.NT]
def 겹(g, p): return 0. if g is None or p is None else float((g[1] & p[1]).sum() / max((g[1] | p[1]).sum(), 1))
def 저(이름, 값):
    p = D + "결과.json"; j = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}; j[이름] = 값
    json.dump(j, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
def 왕복():   # S1 정답 칸 → 로짓처럼 바꿔 모델124.사양 → 짓기_자리 → 렌더 vs 정답 렌더
    색, ns = 시험(); o = []
    for n in ns:
        y = B.과녁(색[n])[0].copy(); 있 = y[:, 0] > 0
        y[:, 0] = np.where(있, 9., -9.); y[:, 23:39:8] = np.where(y[:, 23:39:8] > 0, 9., -9.); y[:, 39] = np.where(y[:, 39] > 0, 9., -9.)   # 있음 · 특징 있음 · 필렛 있음 = 시그모이드 들어가는 칸
        o.append(y)
    정 = B.병렬렌더([("조립", 색[n]["코드"]) for n in ns]); 예 = B.병렬렌더([("자리", B.사양(a)) for a in o])
    iou = np.array([겹(g, p) for g, p in zip(정, 예)]); 수 = np.array([len(색[n]["코드"]["몸"]) for n in ns]); 실 = int(sum(p is None for p in 예))
    줄 = {f"몸 {k}": round(float(np.median(iou[수 == k])), 4) for k in range(1, 7) if (수 == k).any()}
    값 = {"IoU 중앙 전체": round(float(np.median(iou)), 4), "몸 2+": round(float(np.median(iou[수 > 1])), 4), "몸 수별": 줄, "다시 짓기 실패": 실, "정답 렌더 실패": int(sum(g is None for g in 정)),
         "0.95 아래": [(n, round(float(i), 3)) for n, i in zip(ns, iou) if i < .95][:30]}
    for n, g, p, i in zip(ns, 정, 예, iou):
        if i < .95 and g is not None and p is not None: B.M.저장(D + f"왕복_{n}_정답.png", g[0]); B.M.저장(D + f"왕복_{n}_다시.png", p[0])
    print(json.dumps(값, ensure_ascii=False)); 저("S1 왕복", 값)
def 자():   # S5 정답 사양에서 덩어리 하나(마지막) 자리를 부품 크기의 5 · 10 · 20 % 옮김 → IoU
    색, ns = 시험(); ns = [n for n in ns if len(색[n]["코드"]["몸"]) > 1][:60]; 잡 = [("자리", 색[n]["코드"]) for n in ns]
    for f in (.05, .1, .2):
        for n in ns:
            c = copy.deepcopy(색[n]["코드"]); E = 색[n]["크기"]; c["몸"][-1]["자리"][0] += f * E; 잡.append(("자리", c))
    r = B.병렬렌더(잡); k = len(ns); 정 = B.병렬렌더([("조립", 색[n]["코드"]) for n in ns])
    값 = {"정답 = 정답(자리 그대로 다시 짓기)": round(float(np.median([겹(g, p) for g, p in zip(정, r[:k])])), 4)}
    for t, f in enumerate((.05, .1, .2)): 값[f"마지막 덩어리 x {int(f * 100)} % 옮김"] = round(float(np.median([겹(g, p) for g, p in zip(정, r[k * (t + 1):k * (t + 2)])])), 4)
    print(json.dumps(값, ensure_ascii=False)); 저("S5 자", 값)
def 탐침():   # S3 얼린 Gemma 벡터 vs 3면도 화소(세 장 32×32) vs 평균 → 칸별 자리(L1 · 크기 비) · 종류(맞음) · 릿지 · 학습 12000 에서 λ 고르고 시험 299
    import cv2
    z = np.load(B.D + "임베딩.npz"); 이 = list(z["이름"]); 색 = {f"{r['i']:05d}": r for r in B.색인()}
    Y = np.stack([B.과녁(색[n])[0] for n in 이]); 있 = Y[..., 0] > 0; 시 = np.array([int(n) >= B.NT for n in 이])
    def 화소(n): return np.concatenate([cv2.resize(cv2.imdecode(np.fromfile(B.D + f"도면/{n}_{v}.png", np.uint8), 0), (32, 32), interpolation=cv2.INTER_AREA).ravel() / 255. for v in B.뷰])
    Xs = {"Gemma 벡터": z["E"].reshape(len(이), -1).astype(np.float64), "3면도 화소": np.stack([화소(n) for n in 이])}
    T = np.concatenate([Y[..., 20:23].reshape(len(이), -1), Y[..., 1:8].reshape(len(이), -1)], 1)   # 칸 6 × 자리 3 = 18 · 칸 6 × 종류 7 = 42
    def 재기(P):
        p = P[:, :18].reshape(-1, 6, 3); k = P[:, 18:].reshape(-1, 6, 7); y = Y[시]; m = 있[시]
        오 = np.abs(p - y[..., 20:23]).sum(-1); 종 = k.argmax(-1) == y[..., 1:8].argmax(-1)
        return {"자리 오차(칸 평균)": round(float(오[m].mean()), 4), "칸별 자리 오차": [round(float(오[:, t][m[:, t]].mean()), 4) for t in range(6) if m[:, t].any()],
                "종류 맞음": round(float(종[m].mean()), 4), "칸1 종류 맞음": round(float(종[:, 0][m[:, 0]].mean()), 4)}
    학 = np.nonzero(~시)[0]; 검, 맞 = 학[-1000:], 학[:-1000]; 값 = {"늘 평균": 재기(np.broadcast_to(T[~시].mean(0), (int(시.sum()), T.shape[1])))}
    for 이름, X in Xs.items():
        mu, sd = X[~시].mean(0), X[~시].std(0) + 1e-6; X = (X - mu) / sd; X = np.concatenate([X, np.ones((len(X), 1))], 1); 최 = None
        for lam in (1e0, 1e1, 1e2, 1e3, 1e4):
            W = np.linalg.solve(X[맞].T @ X[맞] + lam * np.eye(X.shape[1]), X[맞].T @ T[맞]); e = np.abs(X[검] @ W - T[검])[:, :18].mean()
            if 최 is None or e < 최[0]: 최 = (e, lam)
        W = np.linalg.solve(X[학].T @ X[학] + 최[1] * np.eye(X.shape[1]), X[학].T @ T[학]); 값[이름] = {**재기(X[시] @ W), "λ": 최[1]}
    for k, v in 값.items(): print(k, v, flush=True)
    저("S3 탐침", 값)
def 그림():   # S2 3면도(모델 입력 그대로) 위에 정답 칸 자리(부피 순 1~6)를 숨은선88 투영 규칙으로 찍음 + 3/4 렌더
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; plt.rcParams["font.family"] = "Malgun Gothic"
    색, ns = 시험(); ns = [n for n in ns if len(색[n]["코드"]["몸"]) >= 4][:4]; 색칸 = ["#d8262b", "#28a050", "#4a7bd1", "#d9a020", "#9b59b6", "#16a2b8"]
    fig, ax = plt.subplots(4, 4, figsize=(16, 16.5))
    for r, n in enumerate(ns):
        Y = B.과녁(색[n])[0]
        for c, (v, (가, 세)) in enumerate(zip(B.뷰, ((0, 1), (0, 2), (1, 2)))):
            im = B.M.읽(B.D + f"도면/{n}_{v}.png"); N = im.shape[0]; ax[r, c].imshow(im)
            for t in range(6):
                if Y[t, 0] > 0: p = Y[t, 20:23]; ax[r, c].plot((p[가] + .55) / 1.1 * N, (.55 - p[세]) / 1.1 * N, "o", ms=16, mfc=색칸[t], mec="white", alpha=.85); ax[r, c].text((p[가] + .55) / 1.1 * N, (.55 - p[세]) / 1.1 * N, str(t + 1), color="white", ha="center", va="center", fontsize=11, weight="bold")
            ax[r, c].set_title(f"{n} {v}", fontsize=14); ax[r, c].axis("off")
        g = B.병렬렌더([("조립", 색[n]["코드"])])[0]; ax[r, 3].imshow(g[0]); ax[r, 3].axis("off"); ax[r, 3].set_title(f"3/4 렌더 · 덩어리 {int((Y[:, 0] > 0).sum())}", fontsize=14)
    fig.suptitle("S2 — 모델이 받는 3면도 위에 정답 칸 자리(번호 = 부피 순)", fontsize=18); fig.tight_layout(); fig.savefig(D + "S2_입력그림.png", dpi=55); print("끝")
def 옮김도면():   # S4-1 시험 부품(덩어리 2+) 20 개 · 마지막 덩어리를 다른 면에 붙여 다시 지음 → 3면도(모델123.도면 · 메시 경로)
    import 모델123 as T
    색, ns = 시험(); ns = [n for n in ns if len(색[n]["코드"]["몸"]) > 1][:20]; os.makedirs(D + "옮김", exist_ok=True); 줄 = []
    for n in ns:
        c = copy.deepcopy(색[n]["코드"]); s = c["몸"][-1]; j, f = s["붙임"]; s["붙임"] = [j, f ^ 1]   # 반대 면(+x ↔ −x …)
        try:
            m = C.메시(C.짓기(c))[0]
            for v, im in zip(B.뷰, T.도면(m=m)): B.M.저장(D + f"옮김/{n}_{v}.png", im)
            줄.append(n)
        except Exception as ex: print(n, "실패", str(ex)[:60])
    json.dump(줄, open(D + "옮김/목록.json", "w")); print("지음", len(줄))
def 옮김():   # S4-3 벡터 거리: 원래 ↔ 옮긴 것 vs 원래 ↔ 다른 시험 부품 중 가장 가까운 것 (세 장 코사인 거리 평균)
    z = np.load(B.D + "임베딩.npz"); 이 = list(z["이름"]); E = z["E"]; 옮 = np.load(D + "옮김/임베딩.npz"); ns = list(옮["이름"])
    시 = [k for k, n in enumerate(이) if int(n) >= B.NT]; 거 = lambda a, b: float(np.mean([1 - a[v] @ b[v] for v in range(3)]))
    짝 = [거(E[이.index(n)], 옮["E"][t]) for t, n in enumerate(ns)]; 이웃 = [min(거(E[이.index(n)], E[k]) for k in 시 if 이[k] != n) for n in ns]
    값 = {"옮긴 짝 거리 중앙": round(float(np.median(짝)), 4), "다른 부품 중 가장 가까운 거리 중앙": round(float(np.median(이웃)), 4), "비": round(float(np.median(짝) / np.median(이웃)), 3),
         "옮긴 짝이 가장 가까운 남보다 가까운 부품": f"{sum(a < b for a, b in zip(짝, 이웃))} / {len(ns)}", "부품별": [(n, round(a, 4), round(b, 4)) for n, a, b in zip(ns, 짝, 이웃)]}
    print(json.dumps({k: v for k, v in 값.items() if k != "부품별"}, ensure_ascii=False)); 저("S4 옮긴 짝", 값)
def 주의():   # S6 모델125 칸 6 개의 교차 주의(층별 · 위 · 앞 · 옆 비율) · 시험 299 평균 · norm_first 디코더 층을 손으로 펼쳐 가중치를 받음
    import torch, 모델125 as T5
    net = T5.망(); net.load_state_dict(torch.load(T5.D + "머리.pt")); net.eval(); z = np.load(B.D + "임베딩.npz"); 이 = list(z["이름"])
    x = torch.tensor(z["E"][[k for k, n in enumerate(이) if int(n) >= B.NT]]).reshape(-1, 2304); 층별 = []
    with torch.no_grad():
        m = net.입(x.reshape(-1, 3, 768)) + net.시점; h = net.칸.expand(len(x), -1, -1)
        for L in net.dec.layers:
            a = L.norm1(h); h = h + L.dropout1(L.self_attn(a, a, a, need_weights=False)[0])
            a = L.norm2(h); o, w = L.multihead_attn(a, m, m, need_weights=True, average_attn_weights=True); h = h + L.dropout2(o); 층별.append(w.mean(0).numpy())   # (칸 6, 그림 3)
            h = h + L.dropout3(L.linear2(L.dropout(L.activation(L.linear1(L.norm3(h))))))
        assert np.allclose(net.출(h).reshape(len(x), -1).numpy(), net(x).numpy(), atol=1e-4), "손 펼침 ≠ 모델"
    값 = {f"층 {i + 1}": [[round(float(v), 3) for v in row] for row in w] for i, w in enumerate(층별)}; print(json.dumps(값, ensure_ascii=False)); 저("S6 주의(칸 × 위 앞 옆)", 값)
if __name__ == "__main__":
    {"왕복": 왕복, "자": 자, "탐침": 탐침, "그림": 그림, "옮김도면": 옮김도면, "옮김": 옮김, "주의": 주의}[sys.argv[1]]()
