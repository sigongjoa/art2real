# 판정기준110 흐름도 — 원화 → 기하 처리(영역 · 다른 두 도면에서 깊이) → 코드(영역마다 면 후보) → 학습(후보 고르기만) → 기하 처리(깎고 다시 그려 대조) → 원화 · 부품 59 를 예로 · 10-20
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, cv2
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams["font.family"] = "Malgun Gothic"
O = "G:/art2real/out/설명/캐드부품/"; i = 59
d = np.load(O + "데이터.npz"); X = d["X"]; e = np.load(O + "데이터_앞옆.npz"); F = e["F"]; h = np.load(O + "숨은선88.npz"); HX, HF = h["HX"], h["HF"]
층 = np.load(O + "층32.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r")
def 도(a, b): img = np.ones((128, 128, 3)); img[b > 0] = (.35, .6, 1); img[a > 0] = 0; return img
fig = plt.figure(figsize=(22, 12)); W = fig.add_axes([0, 0, 1, 1]); W.set_xlim(0, 22); W.set_ylim(0, 12); W.axis("off")
단 = [("① 원화", "위 · 앞 · 옆 3면도\n(실선 + 숨은선)", "#eeeeee"), ("② 기하 처리", "제 도면의 닫힌 영역\n+ 다른 두 도면 선에서\n영역의 깊이 읽기", "#dbeafe"), ("③ 코드", "영역마다 면 후보\n면(영역, 평면, 깊이)\n후보 몇 개", "#dcfce7"),
     ("④ 학습", "후보 중 하나 고르기만\n(영역 하나 = 답 하나)\n화소 argmax 없음", "#fef3c7"), ("⑤ 기하 처리", "코드로 깎기 →\n위 · 앞 · 옆 다시 그림 →\n원래 도면과 대조", "#dbeafe"), ("⑥ 원화", "다시 그린 3면도\n= 입력과 같아야 함", "#eeeeee")]
for k, (t, s, c) in enumerate(단):
    x = .4 + k * 3.6; W.add_patch(FancyBboxPatch((x, 9.2), 3.0, 2.3, boxstyle="round,pad=.05", fc=c, ec="#555")); W.text(x + 1.5, 11.05, t, ha="center", fontsize=15, weight="bold"); W.text(x + 1.5, 10.0, s, ha="center", va="center", fontsize=11)
    if k < 5: W.add_patch(FancyArrowPatch((x + 3.05, 10.35), (x + 3.55, 10.35), arrowstyle="-|>", mutation_scale=22, color="#333"))
W.text(11, 8.6, "부품 59 (컵) 로 따라가기", ha="center", fontsize=15, weight="bold")
a = fig.add_axes([.02, .33, .14, .33]); a.imshow(도(X[i], HX[i])); a.set_title("위 도면: 원 하나"); a.axis("off")
a = fig.add_axes([.02, .02, .14, .3]); a.imshow(도(F[i], HF[i])); a.set_title("앞 도면: 파랑 숨은선 = 바닥"); a.axis("off")
a = fig.add_axes([.19, .33, .14, .33]); 안 = 입[i, 0, 1] > 0; n, lab = cv2.connectedComponents(((입[i, 0, 0] == 0) & 안).astype(np.uint8), connectivity=4)
a.imshow(np.where(안, lab, np.nan), cmap="tab10"); a.set_title(f"영역 {n - 1} 개: 원 안 · 테두리"); a.axis("off")
a = fig.add_axes([.19, .02, .14, .3]); f = 도(F[i], HF[i]).copy(); ys = np.nonzero((HF[i] > 0).sum(1) > 40)[0]
for y in ys: f[y, :] = (1, .5, 0)
a.imshow(f); a.set_title(f"원 안 영역 아래로 지나는 수평 숨은선\n→ 깊이 후보 (행 {ys.min()}~{ys.max()})"); a.axis("off")
W.text(8.3, 6.6, "원 안 영역의 코드 후보\n\n  면(원 안, 평면, 층 0)   ← 위 윗면\n  면(원 안, 평면, 층 16)  ← 앞 · 옆 숨은선\n  면(원 안, 평면, 층 31)  ← 아래 바닥\n  관통", fontsize=12, va="top", family="Malgun Gothic", bbox=dict(fc="#dcfce7", ec="#555"))
W.text(12.2, 6.6, "고르기: 영역 하나에 답 하나\n정답 = 층 16\n\n화소마다 따로 안 고름\n→ 얼룩 · 부스러기가\n   구조상 생길 수 없음", fontsize=12, va="top", bbox=dict(fc="#fef3c7", ec="#555"))
gt = np.where(입[i, 0, 1] > 0, 층[i, 0].astype(float), np.nan); a = fig.add_axes([.75, .33, .14, .33]); a.imshow(gt, vmin=0, vmax=31); a.set_title("정답 깊이 (원 안 = 16)"); a.axis("off")
W.text(16.6, 2.6, "판정 전에 잼(학습 없이)\n· 천장: 코드 후보 중 정답에 가장 가까운 것을 골라 깎은 IoU · F\n  (판0 F 0.862 · 천장32 와 맞댐)\n· 영역 몫: 깎인 속 화소 중 「영역 하나 = 평면 하나」로\n  덮이는 몫(비탈 · 곡면은 기운 평면 후보까지)", fontsize=11, va="top", bbox=dict(fc="#f5f5f5", ec="#999"))
W.text(.4, 8.6, "가져가는 것: 후보101 넓은 선(세로선 뺀 실선 + 숨은선) · 맞대100 다시 그리기 · 평가69 채점\n안 하는 것: 화소 U-Net(판0) 을 바탕으로 쓰기 · 결과 보고 문턱 고치기", fontsize=11, va="top")
plt.savefig(O + "흐름110.png", dpi=72); print("저장")
