# 판정 메커니즘 그림 — 부품 하나(5926 컵)로 채점 알고리즘을 단계별로: 선 그림 → 모델 예측 깊이 층(여섯 방향) → 틀(실루엣 교집합) → 깎기 → CAD → 48³ 칸 → 정답 칸과 겹침 → IoU · 10-16 사용자 「판정 메커니즘이랑 알고리즘을 보여 달라」
# 사용(venv · ART_MEM_GB=8): 판정그림57.py [부품 번호=5926] → out/설명/판정메커니즘_<번호>.png
import sys, json, numpy as np
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍")
import 짓기 as J, 여섯방향 as S6, 여섯방향_빠른 as S6빠, 평가51나 as E
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
O = "G:/art2real/out/설명/캐드부품/"; i = int(sys.argv[1]) if len(sys.argv) > 1 else 5926
L = json.load(open(O + "목록.json", encoding="utf-8")); d = np.load(O + "데이터.npz"); X = d["X"][i]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"][i], e["S"][i]
반 = np.load(O + "데이터51.npz")["반"][i]; D = O + "학습51나_판0전체/"; 자 = {int(a): n for n, a in enumerate(np.load(D + "예측부품.npy"))}; 층 = np.array(np.load(D + "예측.npy", mmap_mode="r")[자[i]])
v, f, H = J.정규메시(L[i]); 정 = J.점유_메시(v, f); 몸, _ = J.몸통37((X, F, S), H); 틀 = J.점유_캐드(몸); 지 = E.지도(층, 반); 칸 = S6.칸깎기(틀, 몸, 지)
s, 정보 = S6빠.지킴짓기(몸, 지); CAD = J.점유_캐드(s)
iou = lambda a, b: (a & b).sum() / (a | b).sum()
f_, ax = plt.subplots(2, 4, figsize=(22, 11)); ax = ax.ravel()
for a in ax: a.axis("off")
# ① 입력 선 그림
ax[0].imshow(np.concatenate([X, F, S], 1), cmap="gray_r"); ax[0].set_title("① 입력: 선 그림 위 · 앞 · 옆 (128²)", fontsize=15)
# ② 모델 예측 깊이 층(여섯 방향 · 0 얕음 ~ 16 깊음 · 17 = 뚫림)
g = np.concatenate([np.concatenate([층[k] for k in r], 1) for r in ((0, 1, 2), (3, 4, 5))], 0); im = ax[1].imshow(np.where(g == 17, np.nan, g), cmap="viridis", vmin=0, vmax=16); ax[1].set_title("② 모델이 낸 깊이 층 · 여섯 방향\n(위 아래 앞 / 뒤 옆 반옆 · 0 얕음 → 16 깊음 · 흰색 = 뚫림)", fontsize=14)
def 복셀(a, m, 색, 제):
    a.remove(); a = f_.add_subplot(2, 4, list(ax).index(a) + 1, projection="3d"); a.voxels(m, facecolors=색, edgecolor=(0, 0, 0, .05)); a.set_title(제, fontsize=14); a.set_axis_off(); a.view_init(28, -50); return a
회 = (.6, .6, .65, 1); 초 = (.16, .63, .31, 1); 빨 = (.86, .2, .2, 1); 파 = (.25, .45, .85, 1)
복셀(ax[2], 틀, 회, "③ 틀 = 세 실루엣을 겹친 덩어리\n정답과 IoU %.3f" % iou(틀, 정))
복셀(ax[3], CAD, 회, "④ 틀을 ②의 깊이만큼 여섯 방향에서 깎아 CAD 로 지음\n(지킴짓기 · 유효 %s)" % s.val().isValid())
복셀(ax[4], 정, 초, "⑤ 정답 메시를 같은 48³ 칸으로")
색 = np.empty(정.shape + (4,)); 색[...] = (0, 0, 0, 0); 색[CAD & 정] = 초; 색[CAD & ~정] = 빨; 색[~CAD & 정] = 파
복셀(ax[5], CAD | 정, 색, "⑥ 겹침: 초록 = 둘 다 · 빨강 = 모델만(더 남김) · 파랑 = 정답만(더 깎음)")
교, 합 = (CAD & 정).sum(), (CAD | 정).sum()
ax[6].text(0, .95, "⑦ 점수 = 부피 IoU = 둘 다 / 둘 중 하나라도\n\n  둘 다(초록) = %d 칸\n  하나라도(초록 + 빨강 + 파랑) = %d 칸\n  IoU = %d / %d = %.3f\n\n⑧ 712 개 부품마다 ①~⑦ 을 되풀이 → 평균이 「712 평균」\n   망침 = CAD IoU < 틀 IoU - 0.01 인 부품 수\n   (깎았더니 틀보다 나빠진 것)\n   유효 = CAD 가 닫힌 입체로 지어진 부품 수\n\n이 부품: 틀 %.3f → 모델 CAD %.3f → 정답 깊이로 깎은 천장 %.3f" % (교, 합, 교, 합, 교 / 합, iou(틀, 정), iou(CAD, 정), np.load(O + "영역53.npy")[json.load(open(O + "범위46.json")).index(int(np.where(np.nonzero(d["시험"])[0] == i)[0][0])), 0]), va="top", fontsize=15, linespacing=1.6, transform=ax[6].transAxes)
ax[7].imshow(np.concatenate([np.where(지[k] == 지[k], 1, 0) for k in ("위",)], 1) if False else np.zeros((1, 1)), cmap="gray"); ax[7].set_visible(False)
f_.suptitle("판정 메커니즘 — 부품 %d(컵) 하나를 채점하는 길" % i, fontsize=20); plt.tight_layout(); plt.savefig("G:/art2real/out/설명/판정메커니즘_%d.png" % i, dpi=72); print("ok", iou(틀, 정), iou(CAD, 정))
