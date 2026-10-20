# 84 편 위쪽 카드 재료 — 공 부품 3504: 3면도 · 돌아가는 3D(정답 대비 코드 천장 · 판0) · 앞 도면 · 가운데 단면(정답 대 틀) / 안 되는 88 부품 썸네일 · 둥근 윤곽 몫 · 10-20
# 사용(venv · 캐드부품 폴더에서): python ../../과정/영상05/대화/84_곡면/재료.py → out/영상05/대화/84_곡면/자료/*.png
import sys, os, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, "G:/art2real/원화3d/실험_20261013/캐드부품"); os.chdir("G:/art2real/원화3d/실험_20261013/캐드부품")
plt.rcParams["font.family"] = "Malgun Gothic"
import 천장쪼개기52 as CK, 울퉁67 as U, 여섯방향 as S6
O = "G:/art2real/out/설명/캐드부품/"; A = "G:/art2real/out/영상05/대화/84_곡면/자료/"; os.makedirs(A, exist_ok=True)
회, 진, 강, 빨, 초 = "#c9ccd1", "#6b7078", "#e0a020", "#d8262b", "#28a050"   # Anatomy 강조색: 회백 + 강조 하나
d = np.load(O + "데이터.npz"); X = d["X"]; te = np.nonzero(d["시험"])[0]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; h = np.load(O + "숨은선88.npz"); HX, HF, HS = h["HX"], h["HF"], h["HS"]
z = np.load(O + "데이터51.npz"); 반, 틀, 정 = z["반"], z["틀"], z["정답"]; 예 = list(te[json.load(open(O + "범위46.json"))])
i = 3504; k = 예.index(i); t = int(np.nonzero(te == i)[0][0])
def 판(): fig = plt.figure(figsize=(10, 7), dpi=100); fig.patch.set_alpha(0); return fig
def 저장(fig, nm): fig.savefig(A + nm, transparent=True); plt.close(fig)
def 도(a, b): img = np.ones((128, 128, 3)); img[b > 0] = (.45, .65, 1); img[a > 0] = .1; return img
# 공: 3면도
fig = 판()
for j, (a, b, nm) in enumerate(((X, HX, "위"), (F, HF, "앞"), (S, HS, "옆"))):
    ax = fig.add_axes([.03 + j * .325, .12, .3, .75]); ax.imshow(도(a[i], b[i])); ax.axis("off"); ax.set_title(nm, fontsize=40, color=진)
저장(fig, "공.png")
# 공3d: 정답 대비 코드 천장(왼쪽) · 판0(오른쪽) 돌림
def 깎(tt): hh = [float(x) for x in 반[i]]; w = {dd: np.where(tt[j] == 32, np.nan, hv - tt[j] * (2 * hv / 32)) for j, (dd, hv) in enumerate(zip(S6.방향, hh))}; return CK.깎(U.풀(틀[i]), w, 48, False, hh).astype(bool)
g = U.풀(정[i]).astype(bool); 코 = 깎(np.load(O + "코드110/층.npy", mmap_mode="r")[k]); 판0 = 깎(np.load(O + "학습69_판0/예측.npy", mmap_mode="r")[t])
def 겉(v):
    from scipy.ndimage import binary_erosion; return v & ~binary_erosion(v)
값 = {"코드": np.nan_to_num(np.load(O + "코드110/값.npy"))[k, 0], "모델": np.nan_to_num(np.load(O + "학습69_판0/값.npy"))[k, 0]}
for f in range(48):
    fig = 판()
    for j, (v, nm) in enumerate(((코, "코드"), (판0, "모델"))):
        ax = fig.add_axes([.01 + j * .5, .02, .48, .86], projection="3d"); ax.set_axis_off(); ax.view_init(20, f * 7.5)
        같 = 겉(v & g); 남 = 겉(v) & ~g; 모 = 겉(g) & ~v
        for m, c, s in ((같, 회, 3), (남, 강, 6), (모, 빨, 6)):
            p = np.argwhere(m); ax.scatter(p[:, 0], p[:, 1], p[:, 2], c=c, s=s, depthshade=True, lw=0)
        ax.set_box_aspect((1, 1, 1)); ax.set_title(f"{nm} {값[nm]:.2f}", fontsize=36, color=초 if 값[nm] > .9 else 빨, y=.97)
    저장(fig, "공3d_%02d.png" % f)
# 공2: 앞 도면 크게 + 가운데 세로 화살표(안쪽 선 없음)
fig = 판(); ax = fig.add_axes([.2, .05, .6, .86]); ax.imshow(도(F[i], HF[i])); ax.axis("off")
ax.annotate("", xy=(64, 18), xytext=(64, 110), arrowprops=dict(arrowstyle="<->", color=강, lw=5)); ax.text(70, 64, "?", fontsize=70, color=강, va="center")
저장(fig, "공2.png")
# 틀: 모서리 쪽 단면(가운데는 틀 = 공) — 정답(회) · 틀에만(강)
fig = 판(); ax = fig.add_axes([.2, .05, .6, .86]); c = 35; tg = U.풀(틀[i]).astype(bool)
im = np.ones((48, 48, 4)); im[..., 3] = 0; im[tg[:, :, c]] = [*plt.matplotlib.colors.to_rgb(강), 1]; im[g[:, :, c]] = [*plt.matplotlib.colors.to_rgb(회), 1]
ax.imshow(im, interpolation="nearest"); ax.axis("off")   # 맥락 없는 읽기: 「층」 단위가 안 읽힘 → 글자 뺌
저장(fig, "틀.png")
# 안됨: 안 되는 88 중 앞 12 의 위 · 앞 · 옆
안 = list(np.load(O + "코드110/안됨.npy")); fig = 판()
for q, j in enumerate(안[:12]):
    ax = fig.add_axes([(q % 4) * .25 + .005, .69 - (q // 4) * .33, .24, .3]); ax.imshow(np.concatenate([도(X[j], HX[j]), np.ones((128, 6, 3)), 도(F[j], HF[j])], 1)); ax.axis("off")
저장(fig, "안됨.png")
# 안됨2: 둥근 윤곽 몫 막대
fig = 판(); ax = fig.add_axes([.34, .15, .6, .72]); 값2 = [(0.51, "크게 틀림", 빨), (0.34, "잘 됨", 회)]   # 88 + 265 ≠ 450 으로 읽혀 개수 뺌
ax.barh([1, 0], [v for v, _, _ in 값2], color=[c for _, _, c in 값2], height=.6)
for y, (v, nm, c) in zip([1, 0], 값2): ax.text(v + .01, y, f"{v:.0%}", va="center", fontsize=40, color=진); ax.text(-.01, y, nm, va="center", ha="right", fontsize=32, color=진)
ax.set_xlim(0, .62); ax.axis("off"); ax.set_title("둥근 윤곽이 있는 부품", fontsize=36, color=진)
저장(fig, "안됨2.png"); print("저장", A)
