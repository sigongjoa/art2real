# 층보기127 세 장 — 같은 부품 · 위 · 앞 · 옆 모두: 입력 + ○ 정답 × 예측 자리 · 4 층 칸 1 · 칸 2 주의 · 행 = 에폭 · 10-22
import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 모델124 as B, 모델127 as M7, 층보기127 as V
if __name__ == "__main__":
    import torch
    plt.rcParams["font.family"] = "Malgun Gothic"; n = sys.argv[1] if len(sys.argv) > 1 else "12003"
    z = np.load(M7.D + "그림.npz"); 이 = list(z["이름"]); 색 = {f"{r['i']:05d}": r for r in B.색인()}; Y = B.과녁(색[n])[0]; x = torch.tensor(z["X"][[이.index(n)]])
    에 = (1, 8, 20, 60); 축 = ((0, 1), (0, 2), (1, 2)); fig, ax = plt.subplots(len(에), 9, figsize=(27, 3.3 * len(에)))
    for r, ep in enumerate(에):
        net = M7.망(); net.load_state_dict(torch.load(M7.D + f"점검/{ep:02d}.pt")); net.eval()
        with torch.no_grad(): d = {k: v.numpy() for k, v in V.펼침(net, x).items()}
        o = d["출력"][0].reshape(6, B.W)
        for v, (가, 세) in enumerate(축):
            im = z["X"][이.index(n), v]; a = ax[r, v * 3]; a.imshow(im, cmap="gray"); a.set_xticks([]); a.set_yticks([])
            for k in range(6):
                if Y[k, 0] > 0: p = Y[k, 20:23]; a.plot((p[가] + .55) / 1.1 * 128, (.55 - p[세]) / 1.1 * 128, "o", ms=11, mfc="none", mec=V.색칸[k], mew=2.5)
                if o[k, 0] > 0: p = o[k, 20:23]; a.plot((p[가] + .55) / 1.1 * 128, (.55 - p[세]) / 1.1 * 128, "x", ms=11, mec=V.색칸[k], mew=3)
            r == 0 and a.set_title(f"{B.뷰[v]} · ○ 정답 × 예측", fontsize=13); v == 0 and a.set_ylabel(f"에폭 {ep}", fontsize=15)
            for k in range(2):
                a = ax[r, v * 3 + 1 + k]; w = d["주의4"][0, k].reshape(3, 8, 8); a.imshow(im, cmap="gray"); a.imshow(np.kron(w[v] / w.max(), np.ones((16, 16))), cmap="viridis", alpha=.6, vmin=0, vmax=1); a.axis("off")
                r == 0 and a.set_title(f"{B.뷰[v]} · 칸{k + 1} 주의 (세 장 합 {w[v].sum():.2f})", fontsize=12, color=V.색칸[k])
                r > 0 and a.text(2, 10, f"{w[v].sum():.2f}", color="white", fontsize=12)
    fig.suptitle(f"{n} — 세 장 모두(위 · 앞 · 옆) · 4 층 칸 1 · 2 주의 · 숫자 = 그 그림에 준 주의 몫", fontsize=17); fig.tight_layout(); fig.savefig(M7.D + f"층보기/세장_{n}.png", dpi=50); print("끝")
