# 판정기준90 눈 시트 — 어려움 20 중 8 개 · 정답 · 판0(이전) · 넓은(B) · 넓은숨은(A) 모델 곡면 맞춤 메시 · 10-19
# 사용(venv): 시트90.py → out/설명/캐드부품/시트90.png · B 메시가 아직 없으면 그 열은 뺀다
import os, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection; import 짓기 as J
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"; 빛 = matplotlib.colors.LightSource(315, 40)
시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 예부 = te[json.load(open(O + "범위46.json"))]; L = json.load(open(O + "목록.json", encoding="utf-8"))
열 = [(제, O + "곡면79_어려움%s/" % 꼬, 색) for 제, 꼬, 색 in (("판0 (이전)", "", "#e8c06a"), ("넓은 망", "_넓은", "#7fb3e8"), ("넓은 망 + 숨은선 (지금)", "_넓은숨은", "#b07ad0")) if os.path.exists(O + "곡면79_어려움%s/결과.json" % 꼬)]
R = [json.load(open(d + "결과.json", encoding="utf-8")) for _, d, _ in 열]; ks = R[0]["요약"]["부품"][:8]; n = len(열) + 1
f = plt.figure(figsize=(3.2 * n, 3.2 * len(ks)))
for i, k in enumerate(ks):
    for j in range(n):
        if j == 0: v, fc, _ = J.정규메시(L[예부[k]]); v, fc, 제, 색 = np.asarray(v), np.asarray(fc), "정답", "#9bd3a8"
        else: 제, d, 색 = 열[j - 1]; z = np.load(d + "판0맞춤_%d.npz" % k); v, fc = z["v"], z["f"]; 제 = "%s · F½ %.2f" % (제, R[j - 1]["부품별"][str(k)]["판0맞춤"][1])
        a = f.add_subplot(len(ks), n, i * n + j + 1, projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1)); a.set_xlim(-.5, .5); a.set_ylim(-.5, .5); a.set_zlim(-.5, .5); a.view_init(28, -50)
        a.add_collection3d(Poly3DCollection(v[fc], facecolors=색, edgecolors=색, linewidths=0, shade=True, lightsource=빛)); a.set_title(제, fontsize=11)
plt.tight_layout(); f.savefig(O + "시트90.png", dpi=60); print(O + "시트90.png", [c[0] for c in 열])
