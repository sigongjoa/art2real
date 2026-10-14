# 182 번 3D — 정답 · 세 방향 틀 · 틀 + 모델 깊이 (채점하는 48³ 칸 그대로) · 10-14
import sys, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 짓기 as J
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"; j = int(sys.argv[1]) if len(sys.argv) > 1 else 182
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; X = d["X"][te[j]]; Y = d["Y"][te[j]]; D = d["D"][te[j]].astype(np.float32)
e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te[j]]; S = e["S"][te[j]]; L = json.load(open(O + "목록.json", encoding="utf-8"))
B = np.load(O + "학습2b/시험예측.npz"); P = B["P"][j]; PD = B["D"][j].astype(np.float32)
v, f, H = J.정규메시(L[te[j]]); 정 = J.점유_메시(v, f); 몸, _ = J.몸통37((X, F, S), H)
판 = [("정답 부품", 정), ("세 방향 틀로 찍은 모양", J.점유_캐드(몸)), ("틀 + 정답 깊이로 깎음", J.점유_캐드(J.깎기(몸, Y, D, H, True))), ("틀 + 모델 깊이로 깎음", J.점유_캐드(J.깎기(몸, P, PD, H, True)))]
ix = np.argwhere(정); lo, hi = ix.min(0), ix.max(0)
fig = plt.figure(figsize=(20, 11))
for i, (t, q) in enumerate(판):
    iou = (q & 정).sum() / max((q | 정).sum(), 1)
    for r, (el, az) in enumerate([(25, -60), (5, -90)]):
        a = fig.add_subplot(2, 4, r * 4 + i + 1, projection="3d"); a.voxels(q, facecolors="tab:green" if i == 0 else "tab:orange", edgecolor="k", linewidth=.1)
        a.view_init(el, az); [getattr(a, "set_%slim" % k)(lo[i_] - 1, hi[i_] + 2) for i_, k in enumerate("xyz")]; a.set_box_aspect(tuple(hi - lo + 3)); a.set_axis_off()
        if r == 0: a.set_title("%s\n점수 %.2f · 칸 %d" % (t, iou, q.sum()), fontsize=15)
fig.suptitle("%d 번 · 위 줄 = 비스듬히 · 아래 줄 = 앞에서 (채점 칸 48³ 그대로)" % j, fontsize=17)
plt.savefig(O + "3d_%d.png" % j, dpi=70, bbox_inches="tight"); print("ok", q.shape)
