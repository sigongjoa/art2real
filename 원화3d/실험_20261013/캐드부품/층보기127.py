# 층보기127 — 모델127 체크포인트(에폭 1 · 2 · 3 · 5 · 8 · 12 · 20 · 30 · 45 · 60)마다 층별 입력 · 출력 · 학습 없음 · 10-22
# ① 통계(시험 64 부품): CNN 블록 값 크기 · 죽은 비율 · 토큰 크기 · 층마다 칸끼리 코사인 닮음 · 교차 주의 엔트로피(1 = 고르게) · 자리 출력 퍼짐
# ② 부품 시트(시험 12003 · 12005 · 학습 하나): 행 = 에폭 · 열 = 입력+자리 · CNN 블록 1~4 · 토큰 크기 · 4 층 칸 1 · 2 · 3 주의(앞 그림 위)
# 사용(cadrille): 층보기127.py → out/설명/캐드부품/모델127/층보기/
import os, sys, json, glob, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 모델124 as B, 조립124 as C, 모델127 as M7
D = M7.D + "층보기/"; os.makedirs(D, exist_ok=True); 색칸 = ["#d8262b", "#28a050", "#4a7bd1", "#d9a020", "#9b59b6", "#16a2b8"]
def 펼침(net, x):   # 모델127.망.forward 를 손으로 펼쳐 층마다 담음 · 끝에 모델 출력과 같은지 확인
    import torch
    b = len(x); 담 = {}; h = net.전처리(x) if hasattr(net, "전처리") else x.reshape(b * 3, 1, M7.S, M7.S).float() / 255.   # 모델129b 는 4 채널
    for i, 블 in enumerate(net.cnn): h = 블(h); 담[f"CNN{i + 1}"] = h.reshape(b, 3, *h.shape[1:])
    m = (h.flatten(2).transpose(1, 2).reshape(b, 3, 64, -1) + net.자리 + net.시점).reshape(b, 192, -1); 담["토큰"] = m; q = net.칸.expand(b, -1, -1)
    for i, L in enumerate(net.dec.layers):
        a = L.norm1(q); q = q + L.self_attn(a, a, a, need_weights=False)[0]
        a = L.norm2(q); o, w = L.multihead_attn(a, m, m, need_weights=True, average_attn_weights=True); q = q + o
        q = q + L.linear2(L.activation(L.linear1(L.norm3(q)))); 담[f"층{i + 1}"] = q; 담[f"주의{i + 1}"] = w   # w (b, 6, 192)
    o = net.출(q); 담["출력"] = o
    assert torch.allclose(o.reshape(b, -1), net(x), atol=1e-4), "손 펼침 ≠ 모델"
    return 담
def 통계(담, Y, 빈=None):   # 빈 = (부품, 192) 선 없는 조각
    import torch
    s = {}
    for i in range(1, 5): f = 담[f"CNN{i}"]; s[f"CNN{i} 크기"] = float(f.abs().mean()); s[f"CNN{i} 죽음"] = float((f.amax((3, 4)) <= 0).float().mean())   # 그림 전체에서 한 번도 안 켜진 채널
    s["토큰 크기"] = float(담["토큰"].norm(dim=-1).mean())
    for i in range(1, 5):
        q = torch.nn.functional.normalize(담[f"층{i}"], dim=-1); c = q @ q.transpose(1, 2); s[f"층{i} 칸 닮음"] = float((c.sum((1, 2)) - 6).mean() / 30)
        w = 담[f"주의{i}"].clamp_min(1e-9); s[f"층{i} 주의 엔트로피"] = float((-(w * w.log()).sum(-1) / np.log(192)).mean())
    if 빈 is not None:
        for i in range(1, 5): s[f"층{i} 빈 조각 몫"] = float((담[f"주의{i}"] * 빈[:, None, :]).sum(-1).mean())
    o = 담["출력"].reshape(-1, 6, B.W)[..., 20:23]; 있 = torch.tensor(Y[..., 0] > 0); s["출력 자리 퍼짐"] = float(o[있].std(0).mean()); s["정답 자리 퍼짐"] = float(torch.tensor(Y[..., 20:23])[있].std(0).mean())
    s["출력 자리 오차"] = float((o - torch.tensor(Y[..., 20:23])).abs().sum(-1)[있].mean()); return s
if __name__ == "__main__":
    import torch
    plt.rcParams["font.family"] = "Malgun Gothic"
    판 = sys.argv[1] if len(sys.argv) > 1 else ""   # 비면 모델127 · a | b 면 모델129a | b
    if 판: import 모델129 as M9; 망 = lambda: M9.망(판); 점D = M9.경로(판)
    else: 망 = M7.망; 점D = M7.D
    D = 점D + "층보기/"; os.makedirs(D, exist_ok=True)
    z = np.load(M7.D + "그림.npz"); 이 = list(z["이름"]); 색 = {f"{r['i']:05d}": r for r in B.색인()}
    통ns = [n for n in 이 if int(n) >= B.NT][:64]; 부ns = ["12003", "12005", next(n for n in 이 if int(n) < B.NT and len(색[n]["코드"]["몸"]) >= 4)]
    X통 = torch.tensor(z["X"][[이.index(n) for n in 통ns]]); 빈통 = torch.tensor(z["X"][[이.index(n) for n in 통ns]].reshape(64, 3, 8, 16, 8, 16).max((3, 5)) < 40).reshape(64, 192).float(); Y통 = np.stack([B.과녁(색[n])[0] for n in 통ns]); X부 = torch.tensor(z["X"][[이.index(n) for n in 부ns]]); Y부 = np.stack([B.과녁(색[n])[0] for n in 부ns])
    점 = sorted(p for p in glob.glob(점D + "점검/*.pt") if os.path.basename(p)[:2].isdigit()); 에 = [int(os.path.basename(p)[:2]) for p in 점]; 표 = []; 부담 = {}
    for p, ep in zip(점, 에):
        net = 망(); net.load_state_dict(torch.load(p)); net.eval()
        with torch.no_grad(): 표.append(통계(펼침(net, X통), Y통, 빈통)); 부담[ep] = {k: v.numpy() for k, v in 펼침(net, X부).items()}
        print(ep, {k: round(v, 3) for k, v in 표[-1].items()}, flush=True)
    json.dump({"에폭": 에, "통계": 표}, open(D + "통계.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # ① 통계 곡선
    fig, ax = plt.subplots(2, 3, figsize=(20, 10)); fig.suptitle(f"층별 통계 {판 or 127} — 에폭마다 같은 시험 64 부품", fontsize=18)
    묶 = [("CNN 값 크기", [f"CNN{i} 크기" for i in range(1, 5)]), ("CNN 죽은 채널 비율", [f"CNN{i} 죽음" for i in range(1, 5)]), ("디코더 칸끼리 닮음(1 = 6 칸 같음)", [f"층{i} 칸 닮음" for i in range(1, 5)]),
         ("교차 주의 엔트로피(1 = 192 조각 고르게)", [f"층{i} 주의 엔트로피" for i in range(1, 5)]), ("자리: 출력 퍼짐 vs 정답 퍼짐", ["출력 자리 퍼짐", "정답 자리 퍼짐"]), ("빈 조각 주의 몫(선 없는 조각 54 %) · 자리 오차", [k for k in ("층1 빈 조각 몫", "층4 빈 조각 몫") if k in 표[0]] + ["출력 자리 오차"])]
    for a, (제, 키들) in zip(ax.ravel(), 묶):
        for k in 키들: a.plot(에, [t[k] for t in 표], "o-", label=k)
        a.set_title(제, fontsize=14); a.set_xlabel("에폭"); a.legend(fontsize=10); a.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(D + "통계.png", dpi=60)
    # ② 부품 시트 · 앞 그림(뷰 1) 기준 · 행 = 에폭 다섯
    행에 = [e for e in (1, 3, 8, 20, 60) if e in 부담] or 에[::max(1, len(에) // 4)][:5]
    for t, n in enumerate(부ns):
        fig, ax = plt.subplots(len(행에), 9, figsize=(27, 3.2 * len(행에))); fig.suptitle(f"{n} ({'시험' if int(n) >= B.NT else '학습'} · 덩어리 {int((Y부[t][:, 0] > 0).sum())}) — 앞 그림 · 행 = 에폭", fontsize=18)
        for r, ep in enumerate(행에):
            d = 부담[ep]; 앞 = z["X"][이.index(n), 1]; a = ax[r, 0]; a.imshow(앞, cmap="gray")
            o = d["출력"][t].reshape(6, B.W)
            for k in range(6):
                if Y부[t][k, 0] > 0: p = Y부[t][k, 20:23]; a.plot((p[0] + .55) / 1.1 * 128, (.55 - p[2]) / 1.1 * 128, "o", ms=11, mfc="none", mec=색칸[k], mew=2.5)
                if o[k, 0] > 0: p = o[k, 20:23]; a.plot((p[0] + .55) / 1.1 * 128, (.55 - p[2]) / 1.1 * 128, "x", ms=11, mec=색칸[k], mew=3)
            a.set_ylabel(f"에폭 {ep}", fontsize=15); a.set_xticks([]); a.set_yticks([])
            if r == 0: a.set_title("입력 · ○ 정답 × 예측 자리", fontsize=12)
            for i in range(4): a = ax[r, 1 + i]; a.imshow(np.abs(d[f"CNN{i + 1}"][t, 1]).mean(0), cmap="magma"); a.axis("off"); r == 0 and a.set_title(f"CNN 블록 {i + 1} 출력", fontsize=12)
            a = ax[r, 5]; a.imshow(np.linalg.norm(d["토큰"][t].reshape(3, 64, -1)[1], axis=-1).reshape(8, 8), cmap="magma"); a.axis("off"); r == 0 and a.set_title("토큰 크기(앞)", fontsize=12)
            for k in range(3):
                a = ax[r, 6 + k]; w = d["주의4"][t, k].reshape(3, 8, 8)[1]; a.imshow(앞, cmap="gray"); a.imshow(np.kron(w / w.max(), np.ones((16, 16))), cmap="viridis", alpha=.6); a.axis("off")
                r == 0 and a.set_title(f"4 층 칸{k + 1} 주의(앞)", fontsize=12, color=색칸[k])
        fig.tight_layout(); fig.savefig(D + f"부품_{n}.png", dpi=50); plt.close(fig)
    print("끝")
