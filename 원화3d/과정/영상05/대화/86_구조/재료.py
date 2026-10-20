# 86 편(구조) 위쪽 카드 — 실제 렌더 · 설계도: 입력 셋(그림 · 3D 턴테이블 · 글) · 인코더 하나 · 종류 고르기(117 실제 후보) · 숫자 · 코드 → 3D → 설계도 · 두께 다른 그릇(3면도 같음 · 단면 다름) · 결과 · 10-20
# 사용(cadrille venv · 캐드부품 폴더에서): python ../../과정/영상05/대화/86_구조/재료.py
import sys, os, json, copy, numpy as np, cv2, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, "G:/art2real/원화3d/실험_20261013/캐드부품"); os.chdir("G:/art2real/원화3d/실험_20261013/캐드부품")
plt.rcParams["font.family"] = "Malgun Gothic"
import 설계116 as S, 데이터117 as Q
A = "G:/art2real/out/영상05/대화/86_구조/자료/"; os.makedirs(A, exist_ok=True); E = Q.D
진, 강, 빨, 초 = "#6b7078", "#e0a020", "#d8262b", "#28a050"
def 판(): fig = plt.figure(figsize=(10, 7), dpi=100); fig.patch.set_alpha(0); return fig
def 저장(fig, nm): fig.savefig(A + nm, transparent=True); plt.close(fig)
읽 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), 1)[..., ::-1]
색 = json.load(open(E + "색인.json", encoding="utf-8")); r = 색[2]; p = r["정답"]["이름"]   # 그릇
# 1 입력 셋
fig = 판()
for j, (im, t) in enumerate(((읽(E + "렌더/" + p + ".png"), "그림"), (읽(E + "렌더/" + p + "_155.png"), "3D(돌려 본 영상)"))):
    ax = fig.add_axes([.03 + j * .32, .2, .3, .6]); ax.imshow(im); ax.axis("off"); ax.set_title(t, fontsize=26, color=진)
ax = fig.add_axes([.67, .2, .31, .6]); ax.axis("off"); ax.set_title("글", fontsize=26, color=진); ax.add_patch(plt.Rectangle((0, 0), 1, 1, fc="#ffffff", ec="#bbb", lw=2))
ax.text(.06, .8, "그릇\nr 30 mm\nh 14 mm\n두께 5 mm", fontsize=24, va="top", color="#333"); 저장(fig, "입력셋.png")
# 2 인코더 하나
fig = 판(); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 7)
for y, t in ((5.6, "그림"), (3.5, "3D"), (1.4, "글")): ax.add_patch(plt.matplotlib.patches.FancyBboxPatch((.4, y - .55), 2.0, 1.1, boxstyle="round,pad=.05", fc="#eef0f2", ec="#555", lw=2)); ax.text(1.4, y, t, fontsize=30, ha="center", va="center"); ax.annotate("", xy=(4.4, 3.5), xytext=(2.5, y), arrowprops=dict(arrowstyle="-|>", color="#333", lw=3))
ax.add_patch(plt.matplotlib.patches.FancyBboxPatch((4.5, 2.3), 2.4, 2.4, boxstyle="round,pad=.08", fc="#fef3c7", ec=강, lw=4)); ax.text(5.7, 3.5, "인코더\n하나", fontsize=30, ha="center", va="center")
ax.annotate("", xy=(8.0, 3.5), xytext=(7.0, 3.5), arrowprops=dict(arrowstyle="-|>", color="#333", lw=3))
rng = np.random.default_rng(1); ax.scatter(8.9 + rng.normal(0, .35, 40), 3.5 + rng.normal(0, .9, 40), s=40, c=[초] * 13 + [강] * 13 + [진] * 14); 저장(fig, "인코더.png")
# 3 종류 고르기: 입력(155°) + 후보 여섯(정답 + 다른 종류 5)
fig = 판(); ax = fig.add_axes([.02, .28, .28, .44]); ax.imshow(읽(E + "렌더/" + p + "_155.png")); ax.axis("off"); ax.set_title("입력", fontsize=22, color=진)
후 = [r["정답"]] + r["T1"]; 순 = [3, 0, 5, 1, 4, 2]
for k, j in enumerate(순):
    ax = fig.add_axes([.34 + (k % 3) * .22, .52 - (k // 3) * .46, .2, .42]); ax.imshow(읽(E + "렌더/" + 후[j]["이름"] + ".png")); ax.axis("off")
    if j == 0: ax.add_patch(plt.Rectangle((3, 3), 250, 250, fill=False, ec=초, lw=6))
저장(fig, "종류.png")
# 4 숫자
fig = 판(); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 7)
for x, (t, v) in zip((1.8, 5.0, 8.2), (("그림", "0.98"), ("3D", "1.00"), ("글", "1.00"))): ax.text(x, 4.3, v, fontsize=72, ha="center", va="center", color=초); ax.text(x, 2.4, t, fontsize=32, ha="center", color=진)
ax.text(5, .9, "찍으면 0.17", fontsize=24, ha="center", color="#999"); 저장(fig, "숫자.png")
# 5 코드 → 3D → 설계도 (컵)
s = {"바탕": {"종류": "컵", "r": 22.0, "h": 30.0, "안r": 16.0, "바닥": 8.0}, "특징": [{"종류": "관통", "x": 0.0, "y": 0.0, "크기": 0.12, "깊이": 0.5}], "기울임": 0.0}
d = S.설계도(s); m, *_ = S.메시(S.짓기(s)); 3 if False else None
fig = 판(); ax = fig.add_axes([.01, .3, .3, .4]); ax.axis("off"); ax.add_patch(plt.Rectangle((0, 0), 1, 1, fc="#1f2227", ec="#555"))
ax.text(.05, .9, "cup = revolve(\n  profile,\n  axis=Z)\ncup.hole(5.3)", fontsize=24, va="top", color="#e6e7e3", family="Consolas")
ax.annotate("", xy=(.33, .5), xytext=(.31, .5), xycoords="figure fraction", arrowprops=dict(arrowstyle="-|>", color="#333", lw=3))
ax = fig.add_axes([.33, .25, .3, .5]); ax.imshow(Q.렌더(m)[0]); ax.axis("off")
N = S.N
for j, (nm, t) in enumerate((("위", "위"), ("앞", "앞"))):
    im = np.ones((N, N, 3)); im[d[nm + "숨"]] = (.45, .65, 1); im[d[nm + "실"]] = 0; im[d[nm + "중심"]] = (.9, .5, .1); ax = fig.add_axes([.66, .52 - j * .46, .16, .42]); ax.imshow(im); ax.axis("off")
ax = fig.add_axes([.83, .3, .16, .42]); ax.imshow(d["단면"], cmap="Greys"); ax.axis("off"); 저장(fig, "코드도면.png")
# 6 두께 다른 그릇: 겉 렌더는 같아 보이고 반 자른 렌더는 다름
import 렌더118 as T
g = {"바탕": {"종류": "그릇", "r": 24.0, "h": 18.0, "두께": 2.5}, "특징": [], "기울임": 0.0}; v = copy.deepcopy(g); v["바탕"]["두께"] = 5.0
fig = 판()
for i, sp in enumerate((g, v)):
    m, *_ = S.메시(S.짓기(sp)); ax = fig.add_axes([.04, .52 - i * .48, .42, .44]); ax.imshow(Q.렌더(m)[0]); ax.axis("off")
    ax = fig.add_axes([.54, .52 - i * .48, .42, .44]); ax.imshow(T.반단면(sp, 35, 25)); ax.axis("off")
ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.annotate("", xy=(.55, .5), xytext=(.46, .5), arrowprops=dict(arrowstyle="-|>", color=강, lw=5))
저장(fig, "단면차.png")
# 7 결과
fig = 판(); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 7)
ax.text(5, 4.6, "849 → 3", fontsize=96, ha="center", va="center", color=초); ax.text(5, 2.5, "못 가린 후보", fontsize=32, ha="center", color=진); 저장(fig, "결과.png"); print("저장")
