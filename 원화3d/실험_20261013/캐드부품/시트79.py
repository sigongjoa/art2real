# 판정기준79 눈 판정 시트 — 곡면79 메시(정답 · 칸32 · 단32맞춤 · 판0칸 · 판0맞춤) 부품 6 개 · 10-18
# 사용(venv): 시트79.py → out/설명/캐드부품/곡면79/시트.png · 시트79.py 기대 → 곡면79_기대/시트.png(판정기준82)
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection; import 짓기 as J
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"; D = O + ("곡면79_%s/" % __import__("os").environ["SET"] if __import__("os").environ.get("SET") else "곡면79/"); 빛 = matplotlib.colors.LightSource(315, 40)
r = json.load(open(D + "결과.json", encoding="utf-8")); 시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 예부 = te[json.load(open(O + "범위46.json"))]; L = json.load(open(O + "목록.json", encoding="utf-8")); 곡 = np.load(O + "곡선77.npy")
import sys; 기 = len(sys.argv) > 1 and sys.argv[1] == "기대"
ks = r["요약"]["부품"][:6] if __import__("os").environ.get("SET") else sorted(r["요약"]["부품"], key=lambda k: -곡[k])[:6]; 열 = [("정답", None, "#9bd3a8"), ("판0칸", "판0칸", "#e8c06a"), ("판0맞춤", "판0맞춤", "#d09a30"), ("기대장", "판0기대장", "#b07ad0"), ("기대맞춤", "판0기대맞춤", "#8a5ab8")] if 기 else [("정답", None, "#9bd3a8"), ("칸32", "칸32", "#7fb3e8"), ("단32맞춤", "단32맞춤", "#5a8fd0"), ("판0칸", "판0칸", "#e8c06a"), ("판0맞춤", "판0맞춤", "#d09a30")]
f = plt.figure(figsize=(3 * len(열), 3 * len(ks)))
for i, k in enumerate(ks):
    for j, (제, 팔, 색) in enumerate(열):
        if 팔 is None: v, fc, _ = J.정규메시(L[예부[k]]); v, fc = np.asarray(v), np.asarray(fc)
        else: z = np.load((O + "곡면79_기대/" if 팔.startswith("판0기대") else D) + "%s_%d.npz" % (팔, k)); v, fc = z["v"], z["f"]
        a = f.add_subplot(len(ks), len(열), i * len(열) + j + 1, projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1)); a.set_xlim(-.5, .5); a.set_ylim(-.5, .5); a.set_zlim(-.5, .5); a.view_init(28, -50)
        a.add_collection3d(Poly3DCollection(v[fc], facecolors=색, edgecolors=색, linewidths=0, shade=True, lightsource=빛))
        a.set_title(제 if 팔 is None or 팔.startswith("판0기대") else "%s · F½ %.2f" % (제, r["부품별"][str(k)][팔][1]), fontsize=11)
plt.tight_layout(); f.savefig((O + "곡면79_기대/" if 기 else D) + "시트.png", dpi=60)
