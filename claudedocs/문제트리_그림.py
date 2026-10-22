# 문제트리.md 그림 — 목표에서 가지로 · 상태 색 · 10-22
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
색 = {"해결": "#28a050", "열림": "#d8262b", "보류": "#d9a020", "안 봄": "#999999"}
가지 = {"A 입력": [("A1 임의 이미지까지", "열림", "실물 0.51 · G2 0.37"), ("A2 인코더가 자리를 남기나", "해결", "Gemma → CNN 0.63 → 0.74"), ("A3 CNN 곡률 · 접합 ★", "열림", "구조 0.59 · 곡률 0.43"), ("A4 선분 토큰", "안 봄", "A3 막히면")],
        "B 출력": [("B1 코드 어휘", "열림", "어휘 밖 부품(119)"), ("B2 칸 짝 · 붕괴", "보류", "0.27 → 0.17 · 129a 효과 없음"), ("B3 덩어리 수", "열림", "0.68 ~ 0.76"), ("B4 실행 · 결정성", "해결", "1.0 · 1.0")],
        "C 학습": [("C1 과적합", "열림", "시험 loss 6.6 → 10.1"), ("C2 단순한 것 잊음", "열림", "0.96 → 0.90"), ("C3 계산 몫 칸", "안 봄", "자리는 기하로?")],
        "D 평가 · 도구": [("D1 파이프라인 버그", "해결", "126 버그 없음"), ("D2 자가 보는 것", "보류", "10 % 옮김 0.88"), ("D3 판마다 같은 점검", "열림", "손으로 · 늦게")]}
fig = plt.figure(figsize=(22, 12)); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 22); ax.set_ylim(0, 12)
ax.add_patch(plt.Rectangle((6.5, 10.6), 9, 1.0, fc="#1d2733", ec="k")); ax.text(11, 11.1, "① 목표: 임의의 이미지로부터 CAD 코드를 만든다", ha="center", va="center", fontsize=19, color="white", weight="bold")
for i, (이, 잎들) in enumerate(가지.items()):
    x = .4 + i * 5.4; ax.plot([11, x + 2.4], [10.6, 9.6], color="#555", lw=2); ax.add_patch(plt.Rectangle((x, 9.0), 4.8, .7, fc="#eef2f7", ec="#555", lw=2)); ax.text(x + 2.4, 9.35, 이, ha="center", va="center", fontsize=16, weight="bold")
    for k, (잎, 상, 증) in enumerate(잎들):
        y = 7.6 - k * 1.85; c = 색[상]; ax.plot([x + 2.4, x + 2.4], [9.0, y + 1.4], color="#bbb", lw=1.5, zorder=0)
        ax.add_patch(plt.Rectangle((x, y), 4.8, 1.4, fc="white", ec=c, lw=4 if "★" in 잎 else 2.5)); ax.text(x + .15, y + 1.05, 잎, fontsize=13.5, weight="bold", va="center")
        ax.text(x + .15, y + .45, 증, fontsize=11.5, va="center", color="#444"); ax.text(x + 4.65, y + 1.05, 상, fontsize=12, va="center", ha="right", color=c, weight="bold")
for k, (상, c) in enumerate(색.items()): ax.add_patch(plt.Rectangle((.4 + k * 2.2, .3), .4, .3, fc=c)); ax.text(.9 + k * 2.2, .45, 상, va="center", fontsize=13)
ax.text(21.6, .45, "★ = 사용자가 고른 줄기 · 새 판은 가지 하나에서만", ha="right", va="center", fontsize=13)
fig.savefig("G:/art2real/out/설명/프레임워크/문제트리.png", dpi=60); print("끝")
