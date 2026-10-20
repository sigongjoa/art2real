# 판정기준117 그림 — 입력 × 후보 표현별 1 등 맞힘(T1 범주 · T2 미세) · 찍기선 · 예시 부품 한 개의 입력 셋 · 10-20
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, cv2
plt.rcParams["font.family"] = "Malgun Gothic"
D = "G:/art2real/out/설명/캐드부품/임베딩117/"; R = json.load(open(D + "결과.json", encoding="utf-8")); 색 = json.load(open(D + "색인.json", encoding="utf-8"))
fig = plt.figure(figsize=(18, 9)); 입 = ["이미지(다른 시점)", "영상", "글"]; 표 = ["렌더", "코드"]
for k, 과 in enumerate(("T1", "T2")):
    ax = fig.add_axes([.36 + k * .33, .14, .29, .7]); x = np.arange(3)
    for j, t in enumerate(표): v = [R[과][f"{i}→{t}"] for i in 입]; b = ax.bar(x + (j - .5) * .36, v, .34, color=["#28a050", "#e0a020"][j], label="후보 = " + t); [ax.text(xx + (j - .5) * .36, vv + .02, f"{vv:.2f}", ha="center", fontsize=11) for xx, vv in zip(x, v)]
    ax.axhline(1 / 6, color="#888", ls=":"); ax.text(2.55, 1 / 6 + .02, "찍기 0.167", color="#666", fontsize=10, ha="right")
    if 과 == "T1": ax.axhline(.8, color="#d8262b", ls="--"); ax.text(2.55, .82, "기준 0.8", color="#d8262b", fontsize=10, ha="right")
    ax.set_xticks(x); ax.set_xticklabels(["이미지\n(다른 시점)", "턴테이블\n영상(3D)", "글 설명"]); ax.set_ylim(0, 1.12); ax.legend(loc="upper left", fontsize=10)
    ax.set_title(["T1 범주: 정답 + 다른 종류 5 → 통과", "T2 미세: 정답 + 수치 변형 5 → 비교기 몫"][k], fontsize=13)
r = 색[3]; p = r["정답"]["이름"]
for j, (f, t) in enumerate(((D + "렌더/" + p + "_155.png", "입력: 이미지(155°)"), (D + "렌더/" + p + ".png", "후보 렌더(35°)"))):
    ax = fig.add_axes([.02, .55 - j * .4, .14, .34]); ax.imshow(cv2.imdecode(np.fromfile(f, np.uint8), 1)[..., ::-1]); ax.set_title(t); ax.axis("off")
ax = fig.add_axes([.17, .15, .17, .7]); ax.axis("off"); ax.text(0, 1, "입력: 글\n" + "\n".join([r["정답"]["글"][i:i + 22] for i in range(0, len(r["정답"]["글"]), 22)]) + "\n\n후보: 코드\n" + "\n".join([r["정답"]["코드"][i:i + 26] for i in range(0, min(len(r["정답"]["코드"]), 208), 26)]) + " …", va="top", fontsize=9, family="Malgun Gothic")
fig.suptitle("판정기준117 통과 — EmbeddingGemma 2(학습 없음)가 이미지 · 턴테이블 영상 · 글 어느 입력에서도 부품 종류는 고른다(0.98 · 1.00 · 1.00) · 수치 차이는 못 가린다(0.13~0.37)", fontsize=14)
plt.savefig(D + "판정117.png", dpi=70); print("저장")
