# 디버그 베이스 한 부품의 전체 흐름 한 장 — 사용자 10-19 「전체 그림을 보여줘야지 · 베이스 이미지 · 디버그하면서 따라갈거야」 · 10-19
# ㉮ 원본 도면 셋(실선 검정 · 점선 회색) → ㉯ 방향 여섯: 모델 입력(제 선 · 껍질) · 정답 층 · 예측 층(틀림 빨강) → ㉰ 깎은 결과: 틀 · 정답 깊이로 깎음 · 예측으로 깎음 · 정답(3D + 가운데 자른 면)
# 사용(venv · ART_MEM_GB=8): 전체96.py <부품 번호=59> [예측 이름=판0] → out/설명/캐드부품/전체96_<부품>_<이름>.png
import sys, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 여섯방향 as S6
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
i = int(sys.argv[1]) if len(sys.argv) > 1 else 59; 이름 = sys.argv[2] if len(sys.argv) > 2 else "판0"
d = np.load(O + "데이터.npz"); X, 시 = d["X"], d["시험"]; e = np.load(O + "데이터_앞옆.npz"); h88 = np.load(O + "숨은선88.npz"); z = np.load(O + "데이터51.npz")
입 = np.load(O + "입력51.npy", mmap_mode="r"); 층 = np.load(O + "층32.npy", mmap_mode="r"); te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json"))
부 = list(np.load(O + "학습69_%s/예측부품.npy" % 이름)); 예 = np.load(O + "학습69_%s/예측.npy" % 이름, mmap_mode="r")[부.index(i)]
풀 = lambda b: np.unpackbits(b)[:48 ** 3].reshape(48, 48, 48).astype(bool)
import 울퉁67 as U; 틀, 정 = U.풀(z["틀"][i]), U.풀(z["정답"][i]); import 평가69 as E; L = json.load(open(O + "목록.json", encoding="utf-8"))   # 평가69 와 같은 깎기 · F@1 칸
(F천, *_), b천 = E.하나((0, L[i], np.array(층[i]), z["반"][i], z["틀"][i], z["정답"][i])); (F판, *_), b판 = E.하나((0, L[i], np.array(예), z["반"][i], z["틀"][i], z["정답"][i])); 천, 판 = 풀(b천), 풀(b판)
f = plt.figure(figsize=(24, 27)); gs = f.add_gridspec(7, 6, height_ratios=[1.15, .1, 1, 1, 1, 1, 1.25])
def 그(a, v, 제, **kw): a.imshow(v, **kw); a.set_title(제, fontsize=13); a.set_xticks([]); a.set_yticks([])
도 = lambda 실, 점: np.where(실 > 0, 0, np.where(점 > 0, .55, 1))
for c, (실, 점, 제) in enumerate(((X[i], h88["HX"][i], "㉮ 원본 위 도면"), (e["F"][i], h88["HF"][i], "㉮ 원본 앞 도면"), (e["S"][i], h88["HS"][i], "㉮ 원본 옆 도면"))):
    그(f.add_subplot(gs[0, 2 * c:2 * c + 2]), 도(실, 점), 제 + "  (실선 검정 · 점선 회색)", cmap="gray", vmin=0, vmax=1)
t = f.add_subplot(gs[1, :]); t.set_axis_off(); t.text(.5, .5, "↓ 방향마다 「제 도면 선 + 껍질(윤곽 셋 교집합 깊이)」만 모델에 들어간다 — 다른 도면의 선 높이는 껍질로 뭉개져 들어감 ↓", ha="center", va="center", fontsize=16, color="#b22", transform=t.transAxes)
줄 = ["모델 입력 · 제 선", "모델 입력 · 껍질 층", "정답 층", "%s 예측 층(틀림 빨강)" % 이름]
for c, 방 in enumerate(S6.방향):
    안 = 입[i, c, 1] > 0; g = 층[i, c].astype(float); p = 예[c].astype(float); 껍 = np.where(입[i, c, 2] == 17, 32, 입[i, c, 2] * 2.0)
    for r, (v, cm) in enumerate(((입[i, c, 0], "gray_r"), (np.where(안, 껍, np.nan), "viridis"), (np.where(안 | (g < 32), g, np.nan), "viridis"), (np.where(안 | (p < 32), p, np.nan), "viridis"))):
        a = f.add_subplot(gs[2 + r, c]); 맞 = np.mean((p == g)[안]) if 안.any() else np.nan
        그(a, v, ("%s 방향\n" % 방 if r == 0 else "") + 줄[r] + (" · 맞음 %.2f" % 맞 if r == 3 else ""), cmap=cm, vmin=0, vmax=1 if cm == "gray_r" else 32)
        if r == 3: 틀림 = 안 & (p != g); a.imshow(np.ma.masked_where(~틀림, 틀림), cmap="autumn", alpha=.55)
from skimage import measure
def 입체(a, v, 제, 색):
    a.set_axis_off(); a.set_box_aspect((1, 1, 1)); a.view_init(35, -55); a.set_title(제, fontsize=13)
    if v.sum() == 0: return
    vv, ff, _, _ = measure.marching_cubes(np.pad(v, 1).astype(float), .5); from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    a.add_collection3d(Poly3DCollection(vv[ff], facecolors=색, edgecolors=색, linewidths=0, shade=True, lightsource=matplotlib.colors.LightSource(315, 40))); [s(0, 50) for s in (a.set_xlim, a.set_ylim, a.set_zlim)]
for c, (v, 제, 색) in enumerate(((틀, "㉰ 틀(윤곽 셋 교집합)", "#bbbbbb"), (천, "정답 깊이로 깎음(천장) · F %.2f" % F천, "#7fb3e8"), (판, "%s 예측으로 깎음 · F %.2f" % (이름, F판), "#e8c06a"), (정, "정답", "#9bd3a8"))):
    입체(f.add_subplot(gs[6, c], projection="3d"), v, 제, 색)
a = f.add_subplot(gs[6, 4:]); m = 정.shape[1] // 2; 단 = np.concatenate([np.rot90(v[:, m, :]) for v in (틀, 천, 판, 정)], 1)
그(a, 단, "가운데 자른 면(앞에서) · 틀 | 천장 | %s | 정답" % 이름, cmap="Greys", vmin=0, vmax=1)
f.suptitle("부품 %d 전체 흐름 — 도면 → 방향별 깊이 → 깎기" % i, fontsize=20, y=.995); plt.tight_layout(rect=(0, 0, 1, .985))
쓸 = O + "전체96_%d_%s.png" % (i, 이름); f.savefig(쓸, dpi=55); print(쓸, "F 천장 %.3f · %s %.3f" % (F천, 이름, F판))
