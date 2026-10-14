# 판정기준42 흐름도 · 10-14
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; f, a = plt.subplots(figsize=(15, 8)); a.axis("off"); a.set_xlim(0, 15); a.set_ylim(0, 8)
def 상자(x, y, w, h, t, c): a.add_patch(plt.Rectangle((x, y), w, h, fc=c, ec="k", lw=1.5)); a.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=13)
def 화(x0, y0, x1, y1): a.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="->", lw=2))
상자(.3, 5.6, 3, 1.4, "위 · 앞 · 옆 선 그림\n(지금 2b 입력)", "#ddd"); 상자(.3, 3.4, 3, 1.6, "앞 · 옆을 90° 세워\n위 칸에 맞춘 높이 2 장\n(새로 · 정답 안 봄)", "#bfe3bf")
상자(4.3, 4.4, 3, 1.6, "같은 모델 · 같은 학습\n15 에폭 · 씨앗 31\n입력만 3 → 5 장", "#ffe0a0"); 화(3.3, 6.3, 4.3, 5.4); 화(3.3, 4.2, 4.3, 5.0)
상자(8.3, 4.4, 3, 1.6, "칠 + 깊이\n→ 판정37 짓기 그대로\n(시험 200)", "#ffe0a0"); 화(7.3, 5.2, 8.3, 5.2)
상자(12, 3.2, 2.8, 4, "판정\nA 깊이 오차\n≤ 0.054(2b × 0.7)\nB 부피 ≥ 0.704\nC 나빠짐 < 97\nD 182 번 ≥ 0.80", "#fff"); 화(11.3, 5.2, 12, 5.2)
상자(.3, .5, 6.5, 2, "대조: 2b(같은 칸에 포갠 3 장)\n깊이 오차 0.077 · 부피 0.678 · 나빠짐 97 · 182 = 0.17", "#eee")
상자(7.3, .5, 7.5, 2, "가져가는 것: 2b 학습법 · 판정37 짓기 · 시험 200\n안 하는 것: 짓기 고치기 · 기준 바꾸기 · 깊이를 회전값으로 바로 쓰기", "#eee")
a.set_title("판정기준42 — 학습 목표를 채점과 맞춘다: 부피 벌점", fontsize=17)
plt.savefig("G:/art2real/out/설명/흐름42.png", dpi=80, bbox_inches="tight")
