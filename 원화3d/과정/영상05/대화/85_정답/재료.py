# 85 편 위쪽 카드 재료 — 안 되는 88(84 재료 재사용) · 회전 후보 점수 막대 · 교과서(SØ 기호 · 반단면 회전) · 설계 순서(3D → 도면) · 학습 장치 영상 프레임(anatomy115) · 10-20
# 사용: python 재료.py → out/영상05/대화/85_정답/자료/
import os, shutil, glob, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from PIL import Image
plt.rcParams["font.family"] = "Malgun Gothic"
A = "G:/art2real/out/영상05/대화/85_정답/자료/"; os.makedirs(A + "장치", exist_ok=True)
회, 진, 강, 빨, 초 = "#c9ccd1", "#6b7078", "#e0a020", "#d8262b", "#28a050"
def 판(): fig = plt.figure(figsize=(10, 7), dpi=100); fig.patch.set_alpha(0); return fig
def 저장(fig, nm): fig.savefig(A + nm, transparent=True); plt.close(fig)
shutil.copy("G:/art2real/out/영상05/대화/84_곡면/자료/안됨.png", A + "안됨.png")
# 회전: 점수 막대 · 목표선
fig = 판(); ax = fig.add_axes([.18, .14, .74, .7]); 값 = [(0.928, "회전 후보 전", 회), (0.935, "회전 후보 넣음", 강)]
ax.barh([1, 0], [v for v, _, _ in 값], color=[c for _, _, c in 값], height=.55)
for y, (v, nm, c) in zip([1, 0], 값): ax.text(v + .002, y, f"{v:.3f}", va="center", fontsize=34, color=진); ax.text(.899, y + .42, nm, fontsize=26, color=진)
ax.axvline(.95, color=빨, lw=4, ls="--"); ax.text(.951, 1.45, "목표 0.95", fontsize=26, color=빨); ax.set_xlim(.9, .97); ax.set_ylim(-.5, 1.75); ax.axis("off")
저장(fig, "회전.png")
# 교과서: 공 = 원 + SØ 기호 / 회전체 = 중심선 + 반단면
fig = 판(); ax = fig.add_axes([.02, .05, .96, .9]); ax.set_xlim(0, 10); ax.set_ylim(0, 7); ax.set_aspect("equal"); ax.axis("off")
t = np.linspace(0, 2 * np.pi, 200); ax.plot(2.6 + 1.8 * np.cos(t), 3.6 + 1.8 * np.sin(t), color="#222", lw=4)
ax.annotate("", xy=(2.6 + 1.27, 3.6 + 1.27), xytext=(5.0, 5.9), arrowprops=dict(arrowstyle="-|>", color=강, lw=3)); ax.text(5.05, 5.85, "SØ 36", fontsize=40, color=강, va="center")
th = np.linspace(-np.pi / 2, np.pi / 2, 80); ax.fill(np.r_[7.4, 7.4 + 1.8 * np.cos(th), 7.4], np.r_[1.8, 3.6 + 1.8 * np.sin(th), 5.4], color=초, alpha=.35, lw=0)
ax.plot(7.4 + 1.8 * np.cos(th), 3.6 + 1.8 * np.sin(th), color="#222", lw=4); ax.plot([7.4, 7.4], [1.2, 6.0], color="#222", lw=2.5, ls=(0, (8, 3, 2, 3)))
ax.annotate("", xy=(6.2, 1.0), xytext=(8.6, 1.0), arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=.45", color=강, lw=3))
저장(fig, "교과서.png")
# 교과서2: 설계 순서 — 3D(상자 + 원기둥) → 도면 석 장
fig = 판(); ax = fig.add_axes([.02, .05, .96, .9]); ax.set_xlim(0, 10); ax.set_ylim(0, 7); ax.set_aspect("equal"); ax.axis("off")
def 상자(x, y, w, h, d):
    for poly, c in (([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], "#eef0f2"), ([(x, y + h), (x + w, y + h), (x + w + d, y + h + d * .6), (x + d, y + h + d * .6)], "#ffffff"), ([(x + w, y), (x + w + d, y + d * .6), (x + w + d, y + h + d * .6), (x + w, y + h)], "#d5d8dc")):
        ax.add_patch(plt.Polygon(poly, fc=c, ec="#222", lw=3))
상자(.6, 2.2, 2.4, 1.8, 1.2); ax.add_patch(plt.matplotlib.patches.Ellipse((2.4, 4.85), 1.2, .55, fc="#ffffff", ec="#222", lw=3))
ax.annotate("", xy=(5.6, 3.6), xytext=(4.4, 3.6), arrowprops=dict(arrowstyle="-|>", color=강, lw=5))
for (x, y) in ((6.0, 4.0), (8.1, 4.0), (6.0, 1.4)):
    ax.add_patch(plt.Rectangle((x, y), 1.8, 1.8, fc="#ffffff", ec="#222", lw=2.5)); ax.add_patch(plt.Rectangle((x + .4, y + .4), 1.0, .8, fc="none", ec="#222", lw=2))
저장(fig, "교과서2.png")
# 장치: anatomy115 프레임 → 1000 × 700 (그림 칸만 잘라)
fs = sorted(glob.glob("G:/art2real/out/설명/캐드부품/학습115_프레임/f*.png"))
for j, f in enumerate(fs[::2]):
    im = Image.open(f).convert("RGBA"); W, H = im.size; im = im.crop((210, 120, 1130, 764)).resize((1000, 700), Image.LANCZOS); im.save(A + "장치/%04d.png" % j)
print("장치 프레임", len(fs[::2]))
