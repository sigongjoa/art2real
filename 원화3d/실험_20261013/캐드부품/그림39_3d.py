# 판정기준39 실제 결과 3D — 정답 · 틀만 · 예전 모델(2b) · 회전 넣은 모델(39) · 채점 칸 48³ · 10-14
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 짓기 as J
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; X = d["X"][te]; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te]; S = e["S"][te]; L = json.load(open(O + "목록.json", encoding="utf-8"))
A = np.load(O + "학습2b/시험예측.npz"); B = np.load(O + "학습39/시험예측.npz"); b = np.load(O + "부피IoU_39_39.npy")
나쁜 = [int(i) for i in np.argsort(b[:, 0] - b[:, 1])[:2]]; 부품 = [182, 0, 131] + 나쁜
fig = plt.figure(figsize=(20, 4.6 * len(부품)))
for r, j in enumerate(부품):
    v, f, H = J.정규메시(L[te[j]]); 정 = J.점유_메시(v, f); 몸, _ = J.몸통37((X[j], F[j], S[j]), H)
    판 = [("정답", 정), ("틀만", J.점유_캐드(몸)), ("예전 모델(포갬)", J.점유_캐드(J.깎기(몸, A["P"][j], A["D"][j].astype(np.float32), H, True)) ), ("회전 넣은 모델", J.점유_캐드(J.깎기(몸, B["P"][j], B["D"][j].astype(np.float32), H, True)))]
    ix = np.argwhere(정); lo, hi = ix.min(0), ix.max(0)
    for c, (t, q) in enumerate(판):
        a = fig.add_subplot(len(부품), 4, r * 4 + c + 1, projection="3d"); a.voxels(q, facecolors="tab:green" if c == 0 else "tab:orange", edgecolor="k", linewidth=.06)
        [getattr(a, "set_%slim" % k)(lo[i] - 1, hi[i] + 2) for i, k in enumerate("xyz")]; a.set_box_aspect(tuple(np.maximum(hi - lo + 3, 4))); a.view_init(30, -58); a.set_axis_off()
        s = (q & 정).sum() / max((q | 정).sum(), 1); a.set_title(("%d 번 · " % j if c == 0 else "") + "%s %.2f" % (t, s), fontsize=16, color="k" if c < 2 else ("tab:red" if s < 판_틀 - .01 else "tab:green" if s > 판_틀 + .01 else "k")) if c >= 2 else a.set_title(("%d 번 · " % j if c == 0 else "") + "%s %.2f" % (t, s), fontsize=16)
        if c == 1: 판_틀 = s
fig.suptitle("실제 지은 모양 (채점 칸 48³) — 위 셋은 앞에서 본 부품 · 아래 둘은 회전 넣은 모델이 가장 많이 망친 부품\n빨강 = 틀보다 나빠짐 · 초록 = 좋아짐", fontsize=19)
plt.savefig(O + "결과39_3d.png", dpi=60, bbox_inches="tight"); print("ok", 부품)
