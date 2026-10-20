# 조사 10-20 한 장 그림 — 같은 3면도(원 셋)에 맞는 두 입체(공 · 원기둥 셋 교집합) / 사람이 공을 짓는 방법(반원 회전) / 선택지 셋 · 10-20
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
fig = plt.figure(figsize=(18, 9)); 회, 강, 빨, 초 = "#9aa3ad", "#e0a020", "#d8262b", "#28a050"
g = np.linspace(-1, 1, 41); X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
for k, (m, nm) in enumerate(((X**2 + Y**2 + Z**2 <= 1, "공"), ((X**2 + Y**2 <= 1) & (Y**2 + Z**2 <= 1) & (X**2 + Z**2 <= 1), "원기둥 셋 교집합"))):
    ax = fig.add_axes([.01 + k * .16, .42, .16, .45], projection="3d"); from scipy.ndimage import binary_erosion; s = m & ~binary_erosion(m); p = np.argwhere(s)
    ax.scatter(p[:, 0], p[:, 1], p[:, 2], s=2, c=회 if k == 0 else 강); ax.set_axis_off(); ax.set_box_aspect((1, 1, 1)); ax.set_title(nm, fontsize=16)
ax = fig.add_axes([.04, .08, .26, .3]); t = np.linspace(0, 2 * np.pi, 200)
for j in range(3): ax.plot(np.cos(t) + j * 2.4, np.sin(t), "k", lw=2); ax.text(j * 2.4, -1.4, "위 앞 옆".split()[j], ha="center", fontsize=13)
ax.set_aspect("equal"); ax.axis("off"); ax.set_title("① 둘 다 윤곽은 원 셋 — 도면에서 공을 확정하는 건 SØ 기호", fontsize=14)
ax = fig.add_axes([.36, .12, .26, .72]); 
th = np.linspace(-np.pi / 2, np.pi / 2, 50); ax.fill(np.r_[0, np.cos(th), 0], np.r_[-1, np.sin(th), 1], color=초, alpha=.35); ax.plot([0, 0], [-1.3, 1.3], "--", color="k")
ax.annotate("", xy=(-.9, .3), xytext=(.9, .3), arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.5", lw=2, color=강))
ax.text(.0, -1.6, "반원 프로파일 + 축 → 회전 = 공\n삼각형 → 회전 = 원뿔", ha="center", fontsize=14); ax.set_xlim(-1.4, 1.4); ax.set_ylim(-1.9, 1.5); ax.set_aspect("equal"); ax.axis("off")
ax.set_title("② 설계자는 도면이 아니라 스케치 → 돌출 · 회전으로 짓는다\n도면은 다 지은 3D 에서 나중에 뽑는다", fontsize=14)
ax = fig.add_axes([.65, .08, .34, .8]); ax.axis("off"); ax.set_title("우리 선택지 (사용자 결정)", fontsize=16)
줄 = [("가. 코드 후보에 곡면 · 회전 넣기", "투영 패턴(원+사각=원기둥 · 원 셋=구)\n· 실루엣 = 곡면 경계 · 학습 데이터 불필요\n· 지금 구조 그대로 · 가장 쌈", 초),
      ("나. 입력에 정보 더하기", "중심선 · 원 종류(Ø/SØ) · 실루엣/모서리 구분\n· 제도 표준이 메우는 방식\n· 실제 원화에 있을지가 문제", 강),
      ("다. 출력을 형상 프로그램으로", "3면도 → 돌출 · 회전 시퀀스 학습(PlankAssembly ·\nOrtho2CAD) · 회전 든 공개 데이터 없음\n· 연구 수준 IoU 0.56~0.79", 회)]
for j, (h, b, c) in enumerate(줄):
    y = .82 - j * .32; ax.add_patch(plt.Rectangle((0, y - .2), 1, .27, fc=c, alpha=.18, ec=c, lw=2)); ax.text(.03, y + .03, h, fontsize=15, weight="bold"); ax.text(.03, y - .03, b, fontsize=12, va="top")
fig.suptitle("조사 10-20: 선만 그린 3면도는 둥근 면을 정하지 못한다 — 사람은 치수 기호로 메우고, 설계는 돌출 · 회전으로 한다", fontsize=17)
plt.savefig("G:/art2real/out/설명/캐드부품/조사112.png", dpi=75); print("저장")
