# 설명128 — 헝가리안 짝 · CNN 곡선 탐지를 실제 데이터로 그림 두 장 · 학습 없음 · 10-22
# 사용(cadrille): 설명128.py → out/설명/캐드부품/탐침128/설명_헝가리안.png · 설명_CNN곡선.png
import numpy as np, cv2, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment as 헝가리안
import 모델124 as B, 모델127 as M7, 탐침128 as P
색칸 = ["#d8262b", "#28a050", "#4a7bd1", "#d9a020", "#9b59b6", "#16a2b8"]
def 픽(p, 가, 세): return (p[가] + .55) / 1.1 * 128, (.55 - p[세]) / 1.1 * 128
if __name__ == "__main__":
    import torch
    plt.rcParams["font.family"] = "Malgun Gothic"
    net = M7.망(); net.load_state_dict(torch.load(M7.D + "머리.pt")); net.eval()
    z = np.load(M7.D + "그림.npz"); 이 = list(z["이름"]); 색 = {f"{r['i']:05d}": r for r in B.색인()}
    # ── 1. 헝가리안 ──
    n = "12003"; Y = B.과녁(색[n])[0]; 있 = Y[:, 0] > 0; g = Y[있, 20:23]; m = len(g)
    with torch.no_grad(): o = net(torch.tensor(z["X"][[이.index(n)]])).reshape(6, B.W).numpy()
    p = o[:, 20:23]; C = np.abs(p[:, None] - g[None]).sum(-1); r_, c_ = 헝가리안(C)
    고정 = [(k, k) for k in range(m)]; 헝 = list(zip(r_, c_)); 앞 = 255 - z["X"][이.index(n), 1]
    fig, ax = plt.subplots(1, 3, figsize=(24, 10.5), gridspec_kw={"width_ratios": [1, 1, .9]})
    fig.suptitle(f"헝가리안 짝 — 처음 보는 부품 {n} (앞 그림) · ○ 정답 덩어리(번호 = 부피 순) · × 모델 칸 예측(번호 = 칸)", fontsize=18, weight="bold")
    for a, (짝, 제, 선색) in zip(ax[:2], ((고정, "지금: 부피 순 고정 짝 (칸 k ↔ 부피 k 번째)", "#d8262b"), (헝, "헝가리안: 거리 합이 가장 작은 1:1 짝", "#28a050"))):
        a.imshow(앞, cmap="gray", vmin=0, vmax=255)
        for k in range(m): x, y = 픽(g[k], 0, 2); a.plot(x, y, "o", ms=22, mfc="none", mec=색칸[k], mew=3.5); a.text(x + 5, y - 5, f"부피 {k + 1}", color=색칸[k], fontsize=13, weight="bold")
        for k in sorted({k for k, _ in 짝}):   # 이 짝에 쓰인 칸만 · 모델이 「없음」으로 낸 칸은 회색
            x, y = 픽(p[k], 0, 2); 없 = o[k, 0] <= 0; a.plot(x, y, "x", ms=16, mec="#999" if 없 else "k", mew=4); a.text(x - 4, y + 9, f"칸{k + 1}" + ("(없음)" if 없 else ""), fontsize=12, weight="bold", color="#999" if 없 else "k")
        합 = 0
        for k, t in 짝:
            (x0, y0), (x1, y1) = 픽(p[k], 0, 2), 픽(g[t], 0, 2); a.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=3, color=선색)); 합 += C[k, t]
        a.set_title(f"{제}\n거리 합 {합:.2f} (부피 덩어리 {m} 개)", fontsize=15, color=선색); a.axis("off")
    a = ax[2]; a.axis("off"); a.set_xlim(0, 1); a.set_ylim(0, 1)
    a.text(0, .95, "거리표 (칸 × 덩어리 · 3D 자리 차)", fontsize=15, weight="bold")
    for k in range(6):
        a.text(.02, .86 - k * .07, f"칸{k + 1}", fontsize=13, weight="bold")
        for t in range(m):
            굵 = (k, t) in 헝; 고 = k == t
            a.text(.18 + t * .2, .86 - k * .07, f"{C[k, t]:.2f}", fontsize=13, color="#28a050" if 굵 else ("#d8262b" if 고 else "#333"), weight="bold" if 굵 or 고 else "normal")
    for t in range(m): a.text(.18 + t * .2, .93 - .02, f"부피{t + 1}", fontsize=12, color=색칸[t], weight="bold")
    for k, s in enumerate(["빨강 = 지금 짝(대각선) · 초록 = 헝가리안 짝", "지금 loss: 칸1 은 꼭 부피 1(가장 큰 덩어리)을", "  맞혀야 함 → 덩어리 자리를 찾아도 칸 번호가", "  틀리면 벌을 받음 → 칸들이 가운데로 몰림", "헝가리안: 칸끼리 가까운 덩어리를 나눠 맡음", "  → 각 칸이 「내 덩어리」를 갖게 됨", "시험 299 전체: 고정 0.270 → 헝가리안 0.169"]):
        a.text(0, .38 - k * .055, s, fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, .94)); fig.savefig(P.D + "설명_헝가리안.png", dpi=55); plt.close(fig)
    # ── 2. CNN 곡선 ──
    fig = plt.figure(figsize=(24, 12)); fig.suptitle("CNN 이 곡선을 찾는 법 — 작은 틀(3×3)을 층마다 쌓아 보는 범위를 넓힘 (모델127 실제 가중치)", fontsize=18, weight="bold")
    im = np.zeros((128, 128), np.uint8); cv2.ellipse(im, (64, 64), (34, 34), 0, 200, 340, 255, 1); cv2.line(im, (20, 100), (108, 100), 255, 1)
    a = fig.add_axes([.02, .5, .3, .42]); a.imshow(im, cmap="gray"); a.set_title("입력: 곡선(반지름 34) + 직선", fontsize=15); a.axis("off")
    for (rr, 이름, c) in ((7, "블록 1 시야 7", "#d8262b"), (19, "블록 2 시야 19", "#d9a020"), (43, "블록 3 시야 43", "#28a050"), (91, "블록 4 시야 91", "#4a7bd1")):
        cx, cy = 64 - 34 * np.cos(np.radians(70)), 64 - 34 * np.sin(np.radians(70)); a.add_patch(plt.Rectangle((cx - rr / 2, cy - rr / 2), rr, rr, fill=False, ec=c, lw=2.5)); a.text(cx + rr / 2 + 1, cy - rr / 2 + 3, 이름, color=c, fontsize=11)
    for t, (rr, 제) in enumerate(((7, "블록 1 이 보는 7×7: 곡선이 거의 직선"), (19, "블록 2: 살짝 휨"), (43, "블록 3: 휜 게 보임"))):
        cx, cy = int(64 - 34 * np.cos(np.radians(70))), int(64 - 34 * np.sin(np.radians(70))); 조 = np.pad(im, 50)[cy + 50 - rr // 2:cy + 50 + rr // 2 + 1, cx + 50 - rr // 2:cx + 50 + rr // 2 + 1]
        a = fig.add_axes([.34 + t * .11, .62, .1, .25]); a.imshow(조, cmap="gray", interpolation="nearest"); a.set_title(제, fontsize=11); a.axis("off")
    W = net.cnn[0][0].weight.detach().numpy()[:, 0]; a = fig.add_axes([.69, .5, .29, .42]); a.axis("off"); a.set_title("첫 층 필터 32 개 (3×3 · 학습된 값) — 대부분 「이 방향 선」 틀", fontsize=14)
    for k in range(32): s = fig.add_axes([.70 + (k % 8) * .035, .84 - (k // 8) * .085, .03, .07]); s.imshow(W[k], cmap="RdBu_r", vmin=-np.abs(W).max(), vmax=np.abs(W).max(), interpolation="nearest"); s.axis("off")
    with torch.no_grad(): h1 = net.cnn[0](torch.tensor(im)[None, None].float() / 255.)[0].numpy()
    점 = h1.reshape(32, -1).std(1).argsort()[::-1][:4]
    for t, k in enumerate(점): a = fig.add_axes([.02 + t * .12, .06, .11, .32]); a.imshow(h1[k], cmap="magma"); a.set_title(f"블록 1 채널 {k} 반응", fontsize=12); a.axis("off")
    a = fig.add_axes([.52, .05, .46, .36]); a.axis("off")
    for k, s in enumerate(["① 3×3 틀은 「짧은 선분 + 방향」만 앎 → 채널마다 특정 방향 선에서 밝아짐(왼쪽 아래)", "② 곡선 = 방향이 조금씩 도는 선분들 → 다음 층이 「이웃 칸의 방향 차이」를 묶어야 곡률",
                           "③ 층마다 보폭 2 로 줄이며 시야 7 → 19 → 43 → 91 화소 → 큰 원의 휨은 블록 3 · 4 에서야 보임", "④ 탐침128: 블록 4 도 곡선 · 직선 · 접합 가르기 0.59 · 곡률 R² 0.43 → 이 묶기를 충분히 못 배움",
                           "⑤ 같은 CNN 에 256 그림(선이 두 배 굵고 길게) → 0.76 · 얇은 선은 보폭 2 에서 깨짐(앨리어싱)"]):
        a.text(0, .9 - k * .2, s, fontsize=13.5)
    fig.savefig(P.D + "설명_CNN곡선.png", dpi=55); print("끝", "고정", [round(C[k, k], 2) for k in range(m)], "헝가리안", [(int(a_), int(b_), round(C[a_, b_], 2)) for a_, b_ in 헝])
