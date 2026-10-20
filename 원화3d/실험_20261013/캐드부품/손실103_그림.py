# 손실103 그림 — 갈래별 손실 몫 대 화소 몫(시험) · 학습 대 시험 화소당 손실 · 손실 큰 시험 부품 넷의 화소 손실 지도 · 10-20
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
O = "G:/art2real/out/설명/캐드부품/"; D = O + "손실103/"; d = json.load(open(D + "결과.json", encoding="utf-8")); 화 = np.load(D + "화소손실.npy", mmap_mode="r"); 부손 = np.load(D + "부품손실.npy")
시부 = np.nonzero(np.load(O + "데이터.npz")["시험"])[0][:300]; 입 = np.load(O + "입력51.npy", mmap_mode="r")
묶 = [["영역: 윤곽 밖", "영역: 안 · 통째(32)", "영역: 안 · 껍질 그대로", "영역: 안 · 껍질 + 1", "영역: 안 · 깎인 속(≥ 껍질+2)"],
      ["면: 평평(7×7 창 한 층)", "면: 비탈(창 1~3 층)", "면: 벽 옆 · 급한 면(창 > 3 층)"], ["선에서 거리 0~0.5", "선에서 거리 0.5~2.5", "선에서 거리 2.5~5.5", "선에서 거리 5.5~999"],
      ["방향: 위", "방향: 아래", "방향: 앞", "방향: 뒤", "방향: 옆", "방향: 반옆"]]
fig = plt.figure(figsize=(20, 13)); gs = fig.add_gridspec(2, 4, height_ratios=[1.1, 1])
for j, ks in enumerate(묶):
    ax = fig.add_subplot(gs[0, j]); y = np.arange(len(ks)); s = [d["시험"][k] for k in ks]
    ax.barh(y + .2, [v["손실 몫"] for v in s], .4, color="#d8262b", label="손실 몫"); ax.barh(y - .2, [v["화소 몫"] for v in s], .4, color="#bbbbbb", label="화소 몫")
    for yy, v in zip(y, s): ax.text(v["손실 몫"] + .01, yy + .2, f"{v['손실 몫']:.2f} · 맞음 {v['층 맞음']:.2f} (학습 {d['학습'][ks[list(y).index(yy)]]['층 맞음']:.2f})", va="center", fontsize=8)
    ax.set_yticks(y); ax.set_yticklabels([k.split(": ")[-1] for k in ks], fontsize=9); ax.invert_yaxis(); ax.set_xlim(0, 1.05); ax.legend(fontsize=8, loc="lower right")
    ax.set_title(["어느 영역에서", "어떤 면에서 (윤곽 안 · 깊이 있음)", "선에서 얼마나 떨어진 곳에서 (윤곽 안)", "어느 방향에서"][j], fontsize=12)
top = np.argsort(-부손)[:4]
for j, t in enumerate(top):
    n = int(np.argmax(화[t].reshape(6, -1).sum(1))); ax = fig.add_subplot(gs[1, j]); 안 = 입[시부[t], n, 1] > 0
    ax.imshow(np.where(입[시부[t], n, 0] > 0, 0, 1), cmap="gray", vmin=0, vmax=1.4); m = ax.imshow(np.where(안, 화[t, n].astype(float), np.nan), cmap="inferno", vmin=0, vmax=6, alpha=.85)
    plt.colorbar(m, ax=ax, fraction=.046); ax.axis("off"); ax.set_title(f"손실 {j + 1} 위 시험 부품 {시부[t]} · 방향 {n}\n부품 손실 몫 {부손[t] / 부손.sum():.3f}", fontsize=11)
fig.suptitle(f"판0 손실은 어디서 나오나 (시험 300 · 화소당 {d['시험']['전체']['화소당 손실']:.3f} · 학습 300 {d['학습']['전체']['화소당 손실']:.3f}) — 깎인 속은 화소 4 % 인데 손실 47 % · 학습 부품에서도 맞음 0.16", fontsize=15)
plt.tight_layout(); plt.savefig(D + "그림.png", dpi=72); print("저장")
