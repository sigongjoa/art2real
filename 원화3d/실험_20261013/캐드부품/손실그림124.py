# 손실그림124 — 124 손실이 어떻게 계산되는지(칸 6 × 41 · 부피 순 정렬 · 항목 11) + 항목별 크기 학습 300 대 시험 300 · 학습 없음 · 10-22
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 모델124 as B, 조립124 as C
항 = ["있음", "종류", "치수", "축", "자리", "특징 있음", "특징 종류", "특징 수치", "필렛 있음", "필렛 크기"]
def 항목(o, Y, 쓰):   # 모델124.학습.손실 과 같은 식 · 항목마다 따로(가중치 곱한 값)
    import torch, torch.nn as nn
    bce = nn.functional.binary_cross_entropy_with_logits; ce = nn.functional.cross_entropy
    y = Y; 있 = y[..., 0]; n = 있.sum().clamp(min=1); 있f = 있.reshape(-1); L = {}
    L["있음"] = bce(o[..., 0], 있)
    L["종류"] = (ce(o[..., 1:8].reshape(-1, 7), y[..., 1:8].argmax(-1).reshape(-1), reduction="none") * 있f).sum() / n
    L["치수"] = ((o[..., 8:17] - y[..., 8:17]).abs() * 쓰).sum() / n * 4
    L["축"] = (ce(o[..., 17:20].reshape(-1, 3), y[..., 17:20].argmax(-1).reshape(-1), reduction="none") * 있f).sum() / n
    L["자리"] = ((o[..., 20:23] - y[..., 20:23]).abs().sum(-1) * 있).sum() / n * 4
    f, g = o[..., 23:39].reshape(-1, C.K, 2, 8), y[..., 23:39].reshape(-1, C.K, 2, 8); g있 = g[..., 0] * 있[..., None]
    L["특징 있음"] = (bce(f[..., 0], g[..., 0], reduction="none") * 있[..., None]).sum() / n
    L["특징 종류"] = (ce(f[..., 1:4].reshape(-1, 3), g[..., 1:4].argmax(-1).reshape(-1), reduction="none") * g있.reshape(-1)).sum() / n
    L["특징 수치"] = ((f[..., 4:] - g[..., 4:]).abs().sum(-1) * g있).sum() / n * 2
    L["필렛 있음"] = (bce(o[..., 39], y[..., 39], reduction="none") * 있).sum() / n
    L["필렛 크기"] = ((o[..., 40] - y[..., 40]).abs() * y[..., 39] * 있).sum() / n
    return L   # 텐서 · 모델125 학습이 합을 loss 로 씀
if __name__ == "__main__":
    import torch
    plt.rcParams["font.family"] = "Malgun Gothic"
    net = B.망(); net.load_state_dict(torch.load(B.D + "머리.pt")); net.eval()
    z = np.load(B.D + "임베딩.npz"); 색 = {f"{r['i']:05d}": r for r in B.색인()}; 이 = list(z["이름"])
    확 = json.load(open(B.D + "확인124.json", encoding="utf-8")); 값 = {}
    for 이름 in ("학습", "시험"):
        ns = 확[이름]["이름"]; 과 = [B.과녁(색[n]) for n in ns]
        Y = torch.tensor(np.stack([a for a, _ in 과])); 쓰 = torch.tensor(np.stack([b for _, b in 과]))
        with torch.no_grad(): o = net(torch.tensor(z["E"][[이.index(n) for n in ns]]).reshape(len(ns), -1)).reshape(-1, C.K, B.W)
        값[이름] = {k: float(v) for k, v in 항목(o, Y, 쓰).items()}
    # 예시 부품 하나(학습 · 몸 5): 정답 칸 vs 예측 칸의 종류 · 자리
    n = "08342"; Y0, _ = B.과녁(색[n])
    with torch.no_grad(): o0 = net(torch.tensor(z["E"][이.index(n)]).reshape(1, -1)).reshape(C.K, B.W).numpy()
    import 모델120 as M; 종 = M.종류들
    fig = plt.figure(figsize=(20, 11.5)); fig.patch.set_facecolor("white")
    fig.suptitle("모델124 의 손실(loss) 계산 — 부품 하나 = 덩어리 칸 6 개 × 41 숫자", fontsize=22, weight="bold", y=.985)
    # ① 흐름
    ax = fig.add_axes([.01, .70, .98, .23]); ax.axis("off"); ax.set_xlim(0, 20); ax.set_ylim(0, 4)
    def 상자(x, y, w, h, 글, fc="#eef2f7", ec="#555", fs=14): ax.add_patch(plt.Rectangle((x, y), w, h, fc=fc, ec=ec, lw=2)); ax.text(x + w / 2, y + h / 2, 글, ha="center", va="center", fontsize=fs)
    def 화(x0, x1, y=2): ax.annotate("", xy=(x1, y), xytext=(x0, y), arrowprops=dict(arrowstyle="-|>", lw=2.5, color="#333"))
    상자(0, 1.2, 2.6, 1.6, "3면도 세 장"); 화(2.7, 3.3); 상자(3.3, 1.2, 2.6, 1.6, "얼린 Gemma\n768 × 3 = 2304"); 화(6.0, 6.6)
    상자(6.6, 1.2, 2.4, 1.6, "MLP 머리\n(학습하는 곳)", "#e3f4e6", "#28a050"); 화(9.1, 9.7)
    상자(9.7, 1.2, 3.2, 1.6, "예측 칸 6 × 41", "#fff4dc", "#d9a020"); 상자(9.7, -.2, 3.2, 1.2, "정답 칸 6 × 41\n부피 큰 순서로 줄 세움", "#fdf0f0", "#d8262b", 12)
    화(13.0, 13.6); 상자(13.6, .5, 6.3, 3.0, "칸 t 끼리만 비교 (예측 1번 ↔ 정답 1번 …)\n\n항목 10 개를 더한 값 = loss\n없는 칸은 「있음」만 셈 · 나머지는 0", "#ffffff", "#333", 14)
    # ② 41 숫자 띠
    ax = fig.add_axes([.03, .55, .94, .12]); ax.axis("off"); ax.set_xlim(0, 41); ax.set_ylim(0, 2)
    띠 = [("있음", 0, 1, "#888", "BCE"), ("종류 7", 1, 8, "#4a7bd1", "CE"), ("치수 9", 8, 17, "#28a050", "L1 × 4"), ("축 3", 17, 20, "#9b59b6", "CE"),
          ("자리 xyz", 20, 23, "#d8262b", "L1 × 4"), ("특징 2 × 8 (구멍 · 홈)", 23, 39, "#d9a020", "BCE · CE · L1×2"), ("필렛", 39, 41, "#16a2b8", "BCE · L1")]
    for 글, a, b, c, 식 in 띠:
        ax.add_patch(plt.Rectangle((a, .7), b - a, .9, fc=c, ec="white", lw=2, alpha=.85)); ax.text((a + b) / 2, 1.15, 글, ha="center", va="center", fontsize=12 if b - a > 2 else 9, color="white", weight="bold"); ax.text((a + b) / 2, .35, 식, ha="center", fontsize=11, color=c)
    ax.text(0, 1.8, "칸 하나 = 숫자 41 개", fontsize=14, weight="bold")
    # ③ 예시: 칸 짝
    ax = fig.add_axes([.03, .04, .45, .45]); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 7.6)
    ax.text(0, 7.2, f"예시: 학습 부품 {n} (덩어리 5) — 칸 t 끼리 비교", fontsize=15, weight="bold")
    ax.text(.2, 6.5, "칸", fontsize=13, weight="bold"); ax.text(1.0, 6.5, "정답(부피 순)", fontsize=13, weight="bold"); ax.text(5.4, 6.5, "예측", fontsize=13, weight="bold")
    for t in range(C.K):
        y = 5.8 - t * .95; 있g = Y0[t, 0] > 0; 있p = o0[t, 0] > 0
        g = f"{종[int(np.argmax(Y0[t, 1:8]))]} · 자리 ({', '.join(f'{v:+.2f}' for v in Y0[t, 20:23])})" if 있g else "(없음)"
        p = f"{종[int(np.argmax(o0[t, 1:8]))]} · 자리 ({', '.join(f'{v:+.2f}' for v in o0[t, 20:23])})" if 있p else "(없음)"
        맞 = (not 있g and not 있p) or (있g and 있p and np.argmax(Y0[t, 1:8]) == np.argmax(o0[t, 1:8]))
        ax.text(.3, y, str(t + 1), fontsize=13); ax.text(1.0, y, g, fontsize=12); ax.text(5.4, y, p, fontsize=12, color="#28a050" if 맞 else "#d8262b")
        if 있g and 있p: ax.text(9.6, y, f"{np.abs(o0[t, 20:23] - Y0[t, 20:23]).sum():.2f}", fontsize=12, ha="right", color="#d8262b")
    ax.text(9.6, 6.5, "자리 차", fontsize=13, weight="bold", ha="right")
    ax.text(0, -.1, "자리 = 부품 가운데에서 덩어리까지 · 부품 크기로 나눔", fontsize=11, color="#666")
    # ④ 항목별 크기
    ax = fig.add_axes([.56, .07, .42, .40]); k = np.arange(len(항)); w = .38
    a = [값["학습"][h] for h in 항]; b = [값["시험"][h] for h in 항]
    ax.barh(k - w / 2, a, w, color="#4a7bd1", label=f"학습 때 본 300 (합 {sum(a):.2f})"); ax.barh(k + w / 2, b, w, color="#d8262b", label=f"처음 보는 300 (합 {sum(b):.2f})")
    for i in range(len(항)): ax.text(max(a[i], b[i]) + .03, i, f"{a[i]:.2f} / {b[i]:.2f}", va="center", fontsize=11)
    ax.set_yticks(k); ax.set_yticklabels(항, fontsize=13); ax.invert_yaxis(); ax.legend(fontsize=12, loc="lower right"); ax.set_xlim(0, max(a + b) * 1.35)
    ax.set_title("60 에폭 뒤 항목별 loss (가중치 곱한 값)", fontsize=15); ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(B.D + "그림_손실124.png", dpi=72); json.dump(값, open(B.D + "손실항목124.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(값, ensure_ascii=False))
