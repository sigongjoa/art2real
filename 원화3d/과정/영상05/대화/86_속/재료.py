# 86 편 위쪽 카드 재료 — 118b 실제 렌더: 그릇 셋(입력 · 고른 후보 · 정답) · 맞힌 부품 · 점수 카드 · 반 자른 그릇 · 동점 목록(반 자름 쌍) · 10-20
# 사용(cadrille venv · 캐드부품 폴더에서): python ../../과정/영상05/대화/86_속/재료.py
import sys, os, json, numpy as np, cv2, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, "G:/art2real/원화3d/실험_20261013/캐드부품"); os.chdir("G:/art2real/원화3d/실험_20261013/캐드부품")
plt.rcParams["font.family"] = "Malgun Gothic"
import 렌더118 as T
A = "G:/art2real/out/영상05/대화/86_속/자료/"; os.makedirs(A, exist_ok=True)
진, 강, 빨, 초 = "#6b7078", "#e0a020", "#d8262b", "#28a050"
def 판(): fig = plt.figure(figsize=(10, 7), dpi=100); fig.patch.set_alpha(0); return fig
def 저장(fig, nm): fig.savefig(A + nm, transparent=True); plt.close(fig)
def 줄들(조건, n):
    out = []
    for r, s in zip(T.색, T.점):
        if len(out) >= n: break
        칸, 동, 엄 = T.줄(r, s)
        if 조건(r, 동, 엄): out.append((r, 칸))
    return out
그릇 = 줄들(lambda r, 동, 엄: 동 and r["정답"]["종류"] == "그릇", 1)[0][1]
동점 = 줄들(lambda r, 동, 엄: 동, 6); 맞 = 줄들(lambda r, 동, 엄: 엄 and r["정답"]["종류"] in ("컵", "상자", "원뿔"), 2)
def 줄그림(ims, 이름, 강조=None):
    fig = 판(); n = len(ims)
    for j, im in enumerate(ims):
        ax = fig.add_axes([.02 + j * (.96 / n), .08, .96 / n - .02, .84]); ax.imshow(im); ax.axis("off")
        if 강조 is not None and j == 강조: ax.add_patch(plt.Rectangle((2, 2), im.shape[1] - 4, im.shape[0] - 4, fill=False, ec=빨, lw=5))
    저장(fig, 이름)
줄그림([그릇[0][0], 그릇[1][0], 그릇[2][0]], "그릇셋.png")
fig = 판()
for i, (r, 칸) in enumerate(맞):
    for j in range(2): ax = fig.add_axes([.06 + j * .46, .52 - i * .48, .42, .44]); ax.imshow(칸[j][0]); ax.axis("off")
ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.annotate("", xy=(.55, .5), xytext=(.47, .5), arrowprops=dict(arrowstyle="-|>", color=초, lw=5)); 저장(fig, "맞힘.png")
fig = 판(); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 7)
ax.text(2.6, 3.6, "0.95", fontsize=110, color=진, ha="center", va="center"); ax.plot([1.0, 4.2], [2.8, 4.4], color=빨, lw=9); ax.annotate("", xy=(6.0, 3.6), xytext=(4.7, 3.6), arrowprops=dict(arrowstyle="-|>", color="#333", lw=5)); ax.text(7.9, 3.6, "0.62", fontsize=110, color=빨, ha="center", va="center"); 저장(fig, "점수.png")
줄그림([그릇[3][0], 그릇[4][0]], "그릇자름.png")
fig = 판()
for i, (r, 칸) in enumerate(동점):
    for j in range(2): ax = fig.add_axes([.02 + (i % 3) * .33 + j * .16, .52 - (i // 3) * .48, .15, .44]); ax.imshow(칸[3 + j][0]); ax.axis("off")
저장(fig, "동점들.png"); print("저장")
