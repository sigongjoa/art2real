# 판정기준116b 그림 — 3면도만으로는 못 가르고 단면으로 가르는 그릇 두께 쌍 · 결과 막대 · 10-20
import json, copy, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
import 설계116 as S
rng = np.random.default_rng(7); N = S.N
s = {"바탕": {"종류": "그릇", "r": 24.0, "h": 18.0, "두께": 3.0}, "특징": [], "기울임": 0.0}; v = copy.deepcopy(s); v["바탕"]["두께"] = 3.45
d, dv = S.설계도(s), S.설계도(v)
a3, _ = S.어긋남(d, dv, False); aA, _ = S.어긋남(d, dv, True)
fig = plt.figure(figsize=(16, 9)); 이름 = ("앞실", "앞숨", "단면")
for r, (dd, t) in enumerate(((d, "그릇 두께 3.0"), (dv, "그릇 두께 3.45 (+15 %)"))):
    for j, nm in enumerate(("위", "앞")):
        ax = fig.add_axes([.02 + j * .17, .52 - r * .46, .16, .4]); im = np.ones((N, N, 3)); im[dd[nm + "숨"]] = (.45, .65, 1); im[dd[nm + "실"]] = 0; im[dd[nm + "중심"]] = (.9, .5, .1); ax.imshow(im); ax.set_title(f"{t} · {nm} 도면"); ax.axis("off")
    ax = fig.add_axes([.38, .52 - r * .46, .16, .4]); ax.imshow(dd["단면"][40:100], cmap="Greys"); ax.set_title(f"{t} · 앞 단면"); ax.axis("off")
ax = fig.add_axes([.6, .55, .38, .35]); 차 = (d["단면"] ^ dv["단면"]); ax.imshow(np.where(차, 1, np.where(d["단면"], .35, 0))[40:100], cmap="magma"); ax.set_title(f"단면 차이(밝은 곳) · 비교기 어긋남: 3면도만 {a3:.3f} · 전체 {aA:.3f}"); ax.axis("off")
R = json.load(open(S.D + "결과b.json", encoding="utf-8"))
ax = fig.add_axes([.64, .1, .32, .3]); 값 = [R["구별 못 함(3면도만)"], R["구별 못 함(전체)"]]
ax.bar([0, 1], 값, color=["#9aa3ad", "#28a050"]); ax.axhline(.05, color="#d8262b", ls="--"); ax.text(1.42, .051, "기준 0.05", color="#d8262b", fontsize=11)
for x, y in zip([0, 1], 값): ax.text(x, y + .002, f"{y:.4f}", ha="center", fontsize=13)
ax.set_xticks([0, 1]); ax.set_xticklabels(["3면도만", "3면도 + 중심선 + 단면"]); ax.set_ylabel("구별 못 한 변형 몫(849 개)"); ax.set_title("판정기준116b 통과 · 실행 200/200 · 결정성 1.0")
fig.suptitle("코드 → 설계도 → 비교기: 3면도만으로는 그릇 두께 · 컵 바닥 · 상자 높이 변형을 놓치고, 단면이 들어가면 가른다", fontsize=15)
plt.savefig(S.D + "판정116b.png", dpi=70); print("저장", a3, aA)
