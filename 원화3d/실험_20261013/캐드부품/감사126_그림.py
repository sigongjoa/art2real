# 감사126 결과 한 장 — S1 · S5(버그 없음) · S3 자리 오차 막대 · S4 거리 · S6 주의 · S2 그림 · 10-22
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from PIL import Image
plt.rcParams["font.family"] = "Malgun Gothic"
D = "G:/art2real/out/설명/캐드부품/"; j = json.load(open(D + "감사126/결과.json", encoding="utf-8"))
a124 = json.load(open(D + "모델124/손실항목124.json", encoding="utf-8")); a125 = json.load(open(D + "모델125/결과.json", encoding="utf-8"))
초, 빨, 금, 회 = "#28a050", "#d8262b", "#d9a020", "#888"
fig = plt.figure(figsize=(20, 12)); fig.suptitle("감사126 — 파이프라인 단계마다 비교 · 버그는 없고, 덩어리 자리는 어떤 입력에서도 「평균」보다 못 나음", fontsize=19, weight="bold")
ax = fig.add_axes([.03, .55, .3, .36]); ax.axis("off")
줄 = [("S1 라벨 왕복", f"덩어리 2+ IoU {j['S1 왕복']['몸 2+']:.2f} · 다시 짓기 실패 {j['S1 왕복']['다시 짓기 실패']}/299", 초, "통과"),
      ("S2 입력 그림", "칸 자리가 3면도 덩어리 위에 맞게 찍힘", 초, "통과"),
      ("S5 채점 자", "정답 1.00 · 10 % 옮김 0.88 · 20 % 0.78", 초, "통과"),
      ("S3 탐침", "Gemma · 화소 모두 평균과 같음(아래 막대)", 빨, "자리 안 풀림"),
      ("S4 하나 옮긴 짝", f"거리 비 {j['S4 옮긴 짝']['비']:.2f} (기준 < 0.5) · 20/20 은 남보다 가까움", 금, "경계"),
      ("S6 모델 안", "칸 6 개 모두 세 그림을 거의 고르게(0.26~0.48)", 금, "칸이 그림을 안 나눠 봄")]
for k, (이, 설, c, 판) in enumerate(줄):
    y = .92 - k * .16; ax.text(0, y, 이, fontsize=15, weight="bold", color=c); ax.text(0, y - .065, 설, fontsize=12); ax.text(1.0, y, 판, fontsize=14, color=c, ha="right", weight="bold")
ax = fig.add_axes([.40, .58, .27, .31]); 이름 = ["늘 평균", "Gemma\n선형", "3면도 화소\n선형", "MLP 124\n(학습)", "트랜스포머 125\n(학습)"]
s3 = j["S3 탐침"]; v = [s3["늘 평균"]["자리 오차(칸 평균)"], s3["Gemma 벡터"]["자리 오차(칸 평균)"], s3["3면도 화소"]["자리 오차(칸 평균)"], a124["시험"]["자리"] / 4, a125["시험"]["항목 loss"]["자리"] / 4]
ax.bar(이름, v, color=[회, 빨, 빨, 빨, 빨]); [ax.text(i, x + .005, f"{x:.3f}", ha="center", fontsize=12) for i, x in enumerate(v)]; ax.set_ylim(0, .4)
ax.set_title("S3 처음 보는 부품 299 · 덩어리 자리 오차(부품 크기 비 · 낮을수록 좋음)", fontsize=13); ax.spines[["top", "right"]].set_visible(False)
ax = fig.add_axes([.71, .58, .27, .31]); 종 = [s3["늘 평균"]["종류 맞음"], s3["Gemma 벡터"]["종류 맞음"], s3["3면도 화소"]["종류 맞음"], .47, a125["시험"]["종류 맞음"]]
ax.bar(이름, 종, color=[회, 초, 초, 초, 초]); [ax.text(i, x + .01, f"{x:.2f}", ha="center", fontsize=12) for i, x in enumerate(종)]; ax.set_ylim(0, 1)
ax.set_title("같은 부품 · 덩어리 종류 맞음(높을수록 좋음)", fontsize=13); ax.spines[["top", "right"]].set_visible(False)
ax = fig.add_axes([.02, .02, .45, .47]); ax.imshow(Image.open(D + "감사126/S2_입력그림.png").crop((0, 0, 900, 470))); ax.axis("off"); ax.set_title("S2 — 모델이 받는 3면도 + 정답 칸 자리(번호 = 부피 순)", fontsize=13)
ax = fig.add_axes([.53, .07, .2, .36]); s4 = j["S4 옮긴 짝"]; ax.bar(["덩어리 하나\n반대 면으로", "가장 가까운\n다른 부품"], [s4["옮긴 짝 거리 중앙"], s4["다른 부품 중 가장 가까운 거리 중앙"]], color=[금, 회])
ax.set_title("S4 Gemma 벡터 거리(중앙 · 20 부품)", fontsize=13); ax.spines[["top", "right"]].set_visible(False)
ax = fig.add_axes([.79, .07, .19, .36]); w = np.array(j["S6 주의(칸 × 위 앞 옆)"]["층 4"]); im = ax.imshow(w, cmap="viridis", vmin=0, vmax=.6)
ax.set_xticks(range(3)); ax.set_xticklabels(["위", "앞", "옆"], fontsize=12); ax.set_yticks(range(6)); ax.set_yticklabels([f"칸{t + 1}" for t in range(6)], fontsize=12)
[ax.text(c, r, f"{w[r, c]:.2f}", ha="center", va="center", color="white", fontsize=11) for r in range(6) for c in range(3)]; ax.set_title("S6 트랜스포머 마지막 층 주의", fontsize=13)
fig.savefig(D + "감사126/그림_감사126.png", dpi=62); print("끝")
