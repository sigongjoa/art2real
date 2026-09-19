# 방법 개념도 — 논문/코드기하/그림/방법.png. 숫자 없음(구조만).  python 방법.py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

plt.rcParams["font.family"] = "Malgun Gothic"
fig, ax = plt.subplots(figsize=(12, 4.6), dpi=200)
ax.set_xlim(0, 12); ax.set_ylim(0, 4.6); ax.axis("off")

def box(x, y, w, h, title, body, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.08", fc=fc, ec="#333", lw=1))
    ax.text(x + w / 2, y + h - 0.2, title, ha="center", va="top", fontsize=10, fontweight="bold")
    ax.text(x + w / 2, y + h - 0.55, body, ha="center", va="top", fontsize=8, linespacing=1.45)

def arrow(x0, y0, x1, y1, label=None, dashed=False):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", lw=1.2, color="#333", ls="--" if dashed else "-"))
    if label:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.12, label, ha="center", fontsize=7.5, color="#444")

box(0.1, 1.7, 1.5, 1.2, "3면 원화", "정면 · 후면 · 측면", "#f2f2f2")

box(2.2, 3.2, 2.7, 1.25, "① 생성 메시 증거", "부품 덩어리의 수 · 위치 · 크기\n평면 · 원통 영역 · 대칭면", "#dbe9f6")
box(2.2, 1.7, 2.7, 1.25, "② 음영 증거", "윤곽 내부의 알베도 면 영역\n광원 추정 → 면 법선의 서열\n법선이 꺾이는 경계 = 모서리", "#dbe9f6")
box(2.2, 0.2, 2.7, 1.25, "③ 실루엣 증거", "축 정렬 실루엣 3장\n(치수의 기준)", "#dbe9f6")

box(5.6, 2.45, 2.5, 1.9, "구조 프로그램 생성", "언어 모델이 증거 표를 읽고\n프리미티브 종류 · 개수 ·\n부착 관계 · 대칭을 선언\n→ build(θ)  (치수는 초기값)", "#fde9d0")
box(5.6, 0.2, 2.5, 1.7, "매개변수 추정", "무미분 최적화가 θ 를\n실루엣 일치 + 법선 서열에\n맞춘다 (언어 모델 아님)", "#e2f0d9")

box(8.9, 1.45, 2.9, 1.7, "닫힌 다양체 원형", "평면은 평면 · 모서리는 모서리\n다양체 불리언 커널이 닫힘을 보장", "#f2f2f2")

for y in (3.8, 2.3, 0.8):
    arrow(1.6, 2.3, 2.2, y)
arrow(4.9, 3.8, 5.6, 3.6); arrow(4.9, 2.3, 5.6, 3.1)
arrow(4.9, 0.8, 5.6, 0.9); arrow(4.9, 2.0, 5.6, 1.3)
arrow(6.85, 2.45, 6.85, 1.9, None)
ax.text(6.95, 2.17, "build(θ) 초기값", fontsize=7.5, color="#444")
arrow(8.1, 1.05, 8.9, 2.0)
ax.annotate("", xy=(8.1, 3.4), xytext=(8.1, 1.5),
            arrowprops=dict(arrowstyle="-|>", lw=1.1, color="#a33", ls="--", connectionstyle="arc3,rad=0.6"))
ax.text(9.75, 3.6, "잔차를 수치로 되돌림\n(구조 수정 · 최대 2회)", fontsize=7.5, color="#a33", ha="center")

fig.savefig(Path(__file__).with_name("방법.png"), bbox_inches="tight", facecolor="white")
