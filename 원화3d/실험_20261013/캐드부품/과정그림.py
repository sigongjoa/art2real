# 한 부품이 지어지는 과정 그대로(짓기.몸통37 · 깎기) — 입력 → 세 판 밀기 → 교차 → 모델 칠 → 깎기 · 채점 칸 48³ · 10-14
import sys, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 짓기 as J
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍"); import 윤곽바탕 as W
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"; j = int(sys.argv[1]) if len(sys.argv) > 1 else 182
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; X = d["X"][te[j]]; Y = d["Y"][te[j]]; D = d["D"][te[j]].astype(np.float32)
e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te[j]]; S = e["S"][te[j]]; L = json.load(open(O + "목록.json", encoding="utf-8"))
B = np.load(O + "학습2b/시험예측.npz"); P = B["P"][j]; PD = B["D"][j].astype(np.float32)
v, f, H = J.정규메시(L[te[j]]); 정 = J.점유_메시(v, f); 칸 = J.점유_캐드
t = J._판(X, "XY", H, .5 * J.칸)[0]; fr = J._판(F, "XZ", 1.2, .5 * J.칸)[0]; sd = J._판(S, "YZ", 1.2, .5 * J.칸)[0]
몸, 길 = J.몸통37((X, F, S), H); 뚫 = J.깎기(몸, np.where(P == 3, 1, P), PD, H, True); 끝 = J.깎기(몸, P, PD, H, True)
점 = lambda q: (q & 정).sum() / max((q | 정).sum(), 1)
판3 = [("② 위 윤곽을 두께 H 로 밀기", 칸(t)), ("③ 앞 윤곽을 앞뒤로 밀기", 칸(fr)), ("④ 옆 윤곽을 좌우로 밀기", 칸(sd)), ("⑤ ②∩③∩④ = 세 방향 틀\n(실제 쓴 판: %s)" % 길, 칸(몸)),
      ("⑦ 모델 칠: 뚫는 곳(빨강)만 깎음", 칸(뚫)), ("⑧ 모델 칠: 들어감(파랑)을\n모델 깊이만큼 위에서 깎음 = 최종", 칸(끝)), ("정답 부품", 정)]
z = np.nonzero(칸(t).any((0, 1)))[0]; z0, z1 = max(z.min() - 2, 0), min(z.max() + 3, 48)
fig = plt.figure(figsize=(26, 17))
# 1 줄: 입력 선 그림과 채운 윤곽
for i, (g, n) in enumerate([(X, "위"), (F, "앞 (세로 = 높이)"), (S, "옆 (세로 = 높이)")]):
    a = fig.add_subplot(3, 6, i * 2 + 1); a.imshow(1 - g, cmap="gray"); a.set_title("① 입력 · %s 선 그림" % n, fontsize=15); a.axis("off")
    a = fig.add_subplot(3, 6, i * 2 + 2); a.imshow(W.바깥(g)[0], cmap="Greys"); a.set_title("%s 바깥 윤곽 채움" % n.split()[0], fontsize=15); a.axis("off")
def 입체(k, t_, q, 색="tab:orange"):
    a = fig.add_subplot(3, 6, k, projection="3d"); qq = q[:, :, z0:z1]; a.voxels(qq, facecolors=색, edgecolor="k", linewidth=.08)
    a.view_init(22, -62); a.set_box_aspect((48, 48, max(z1 - z0, 1) * 1.0)); a.set_axis_off(); a.set_title("%s\n칸 %d · 점수 %.2f" % (t_, q.sum(), 점(q)), fontsize=14)
for i, (t_, q) in enumerate(판3[:4]): 입체(7 + i, t_, q)
a = fig.add_subplot(3, 6, 11); 색 = np.array([[1, 1, 1], [.75, .75, .75], [.85, .2, .2], [.3, .5, .9]]); a.imshow(색[P]); a.set_title("⑥ 모델 칠 (위에서 본 칸마다)\n회색 윗면 · 빨강 뚫음 · 파랑 들어감", fontsize=14); a.axis("off")
a = fig.add_subplot(3, 6, 12); im = a.imshow(np.where(P == 3, PD, np.nan), cmap="magma_r", vmin=0, vmax=1); a.set_title("⑥ 모델 깊이 (파랑 칸만)\n어두울수록 깊게 · 정답 중앙 %.2f · 모델 %.2f" % (np.median(D[Y == 3]) if (Y == 3).any() else 0, np.median(PD[P == 3]) if (P == 3).any() else 0), fontsize=14); a.axis("off")
for i, (t_, q) in enumerate(판3[4:]): 입체(13 + i, t_, q, "tab:green" if t_ == "정답 부품" else "tab:orange")
a = fig.add_subplot(3, 6, 16, projection="3d"); a.voxels(칸(몸)[:, :, z0:z1] & ~칸(끝)[:, :, z0:z1], facecolors="tab:red", edgecolor="k", linewidth=.08); a.view_init(22, -62); a.set_box_aspect((48, 48, max(z1 - z0, 1))); a.set_axis_off(); a.set_title("⑤ 에서 ⑧ 로 가며 깎여 나간 칸", fontsize=14)
fig.suptitle("%d 번이 지어지는 과정 — 위 줄 입력 · 가운데 줄 세 방향 틀 · 아래 줄 모델이 깎기 (H = %.2f · 채점 칸 48³)" % (j, H), fontsize=19)
plt.savefig(O + "과정_%d.png" % j, dpi=62, bbox_inches="tight"); print("ok", 길)
