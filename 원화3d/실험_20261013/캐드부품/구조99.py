# 우리 구조 그림(논문 Fig. 1 꼴) — 사용자 10-19 「원화 → 기하 처리 → 코드 → 기하 처리 → 원화」 · 「논문처럼 우리 구조를 이미지로」 · 부품 59 실제 데이터 · 10-19
# (a) 도면 셋 → (b) 기하 처리: 닫힌 영역 · 다른 도면 수평선의 깊이 후보 → (c) 코드: 영역마다 피처 가설 → (d) 다시 투영(앞 도면 실선 · 점선) → (e) 원래 도면과 맞대 고름
# 사용(venv · ART_MEM_GB=8): 구조99.py [부품=59] → out/설명/캐드부품/구조99.png · (b) 후보는 후보95 · 깎기는 평가69 · 다시 투영은 48³ 칸에서
import sys, json, numpy as np, cv2, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import 후보95 as H, 평가69 as E, 울퉁67 as U
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"; i = int(sys.argv[1]) if len(sys.argv) > 1 else 59; N = 128
X, F, S, HX, HF, HS = H.X[i], H.F[i], H.S[i], H.h88["HX"][i], H.h88["HF"][i], H.h88["HS"][i]; 층 = np.array(H.층[i]); z = np.load(O + "데이터51.npz"); L = json.load(open(O + "목록.json", encoding="utf-8"))
# (b) 위 도면 닫힌 영역 · 가장 큰 안쪽 영역의 후보
n, lab = cv2.connectedComponents(((X == 0) & (H.입[i, 0, 1] > 0)).astype(np.uint8), connectivity=4); 크 = np.bincount(lab.ravel()); 크[0] = 0
영 = np.argsort(크)[::-1][:2]; 안영 = 영[np.argmin([np.abs(np.argwhere(lab == r).mean(0) - 63.5).sum() for r in 영])]; m = lab == 안영
앞, 옆 = H.후보(i); Y, Xx = np.nonzero(m); c = (앞[Xx] & 옆[N - 1 - Y]).mean(0) > .5; 후 = list(np.nonzero(c)[0])
# (c) 가설마다 위 방향 원 영역 층만 바꿔 깎음 → 48³
def 깎기(값):
    t = 층.copy(); t[0][m] = 값; (f1, *_), b = E.하나((0, L[i], t, z["반"][i], z["틀"][i], z["정답"][i])); return U.풀(b), f1
가설 = [(v, *깎기(v)) for v in 후 if v > 0] + [(32, *깎기(32))]
# (d) 다시 투영 — 앞(+y 에서 −y 로) · 칸 [x, y, z] · 면 = 점유 바뀜 · 보이면 실선 · 가리면 점선
def 투영(v, 뛰=2):   # 앞에서 본 (x, z) 줄마다 재료 구간 · 구간 수가 바뀌거나 경계가 뛰= 칸 넘게 뛰면 선 · 첫 경계가 바뀌면 실선(보임) · 나머지 점선
    n = v.shape[0]; d = np.diff(np.pad(v, ((0, 0), (1, 1), (0, 0))).astype(int), axis=1)   # [x, y+1, z] 들어감 +1 · 나옴 −1
    수 = (d == 1).sum(1); 경 = np.full((n, n, 6), -99); 
    for x in range(n):
        for zz in range(n):
            e = np.nonzero(d[x, :, zz])[0][::-1][:6]; 경[x, zz, :len(e)] = e   # 앞(+y)부터
    실 = np.zeros((n, n), bool); 점 = np.zeros((n, n), bool)
    for 축 in (0, 1):
        A, B = (slice(1, None), slice(None, -1)); s1 = (A, slice(None)) if 축 == 0 else (slice(None), A); s0 = (B, slice(None)) if 축 == 0 else (slice(None), B)
        바뀜 = (수[s1] != 수[s0]) | (np.abs(경[s1] - 경[s0]) > 뛰).any(-1); 첫 = (수[s1] != 수[s0]) & ((수[s1] == 0) | (수[s0] == 0)) | (np.abs(경[s1][..., 0] - 경[s0][..., 0]) > 뛰)
        실[s1] |= 첫; 점[s1] |= 바뀜 & ~첫
    점 &= ~실; return 실.T[::-1], 점.T[::-1]   # 행 = −z · 열 = x
작 = lambda a: cv2.resize(a.astype(np.uint8), (48, 48), interpolation=cv2.INTER_AREA) > 0
원앞 = (작(F > 0), 작((HF > 0) & ~(F > 0)))
def 맞대(실, 점):   # 원래 앞 도면 선(실 ∪ 점) 대비 다시 그린 선 F
    a = 원앞[0] | 원앞[1]; b = 실 | 점; k = np.ones((3, 3), np.uint8); ad, bd = cv2.dilate(a.astype(np.uint8), k) > 0, cv2.dilate(b.astype(np.uint8), k) > 0
    p = (b & ad).sum() / max(b.sum(), 1); r = (a & bd).sum() / max(a.sum(), 1); return 2 * p * r / max(p + r, 1e-9), a & ~bd
# 그림
f = plt.figure(figsize=(26, 15)); 
def 칸(x, y, w, h, 제, 색):
    a = f.add_axes([x, y, w, h]); a.set_axis_off(); a.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.0,rounding_size=0.02", fc=색, ec="#666", lw=1.4, transform=a.transAxes)); a.text(.02, .97, 제, va="top", fontsize=15, weight="bold", transform=a.transAxes); return a
def 판(x, y, w, h, v, 제="", **kw):
    a = f.add_axes([x, y, w, h]); a.imshow(v, **kw); a.set_xticks([]); a.set_yticks([]); [s.set_color("#999") for s in a.spines.values()]; a.set_title(제, fontsize=11.5); return a
도 = lambda 실, 점: np.where(실 > 0, 0, np.where(점 > 0, .6, 1))
# (a)
칸(.01, .52, .2, .44, "(a) 입력 도면 — 원화", "#f7f7f7")
for j, (실, 점, 제) in enumerate(((X, HX, "위"), (F, HF, "앞"), (S, HS, "옆"))): 판(.025 + (j % 2) * .095, .72 - (j // 2) * .2, .085, .16, 도(실, 점), 제, cmap="gray", vmin=0, vmax=1)
f.text(.12, .58, "실선 = 보이는 선\n점선(회색) = 가려진 선", fontsize=11, color="#555")
# (b)
칸(.23, .52, .3, .44, "(b) 기하 처리 — 학습 없음", "#eef4fb")
rgb = np.ones((N, N, 3)); rgb[lab == 영[0]] = [.80, .88, .97]; rgb[lab == 영[1]] = [.98, .86, .70]; rgb[X > 0] = 0
판(.245, .66, .085, .16, rgb, "① 닫힌 영역")
px, py = int(np.median(Xx)), int(np.median(Y)); a = 판(.34, .66, .085, .16, 도(F, HF), "② 앞 도면 같은 x 줄", cmap="gray", vmin=0, vmax=1); a.axvline(px, color="#d33", lw=1.2)
a = 판(.435, .66, .085, .16, 도(S, HS), "③ 옆 도면 같은 y 줄", cmap="gray", vmin=0, vmax=1); a.axvline(N - 1 - py, color="#d33", lw=1.2)
f.text(.245, .58, "④ 영역 깊이 후보 = 앞 ∩ 옆 수평선 높이 → 원 영역: %s 층\n    (시험 300: 정답이 후보 안 0.67 · 화소당 후보 3.2 · 속 깎임 0.35)" % ", ".join(map(str, 후)), fontsize=12.5)
# (c)
칸(.55, .52, .44, .44, "(c) 코드 — 영역마다 피처 가설", "#f4f9ee")
f.text(.565, .9, "body = extrude(위 윤곽 ∩ 앞 ∩ 옆)\n" + "\n".join("가설 %d: body.cut(원 영역, %s)" % (j + 1, ("깊이 %d 층 포켓" % v) if v < 32 else "관통") for j, (v, _, _) in enumerate(가설)), fontsize=13, va="top")
from skimage import measure; from mpl_toolkits.mplot3d.art3d import Poly3DCollection
for j, (v, 칸v, f1) in enumerate(가설[:4]):
    a = f.add_axes([.565 + j * .105, .56, .1, .17], projection="3d"); a.set_axis_off(); a.set_box_aspect((1, 1, 1)); a.view_init(35, -55)
    vv, ff, _, _ = measure.marching_cubes(np.pad(칸v, 1).astype(float), .5); a.add_collection3d(Poly3DCollection(vv[ff], facecolors="#c9c9c9", edgecolors="#c9c9c9", linewidths=0, shade=True, lightsource=matplotlib.colors.LightSource(315, 40))); [s(0, 50) for s in (a.set_xlim, a.set_ylim, a.set_zlim)]
    a.set_title("가설 %d" % (j + 1), fontsize=12)
f.text(.565, .52, "학습(망)은 여기만 — 기하로 하나로 안 정해지는 영역의 후보 고르기", fontsize=12, color="#2a7")
# (d) · (e)
칸(.23, .04, .76, .44, "(d) 다시 투영(기하 처리)  →  (e) 원래 도면과 맞대 고르기 — 정답 3D 없이", "#fbf3ee")
투 = [투영(g[1]) for g in 가설]; 모 = [a | b for a, b in 투]; 공통 = np.logical_and.reduce(모); k3 = np.ones((3, 3), np.uint8)
다름 = cv2.dilate((np.logical_or.reduce(모) & ~공통).astype(np.uint8), k3) > 0   # 가설끼리 다른 선 자리만 잰다(공통 윤곽은 빼고)
원 = 원앞[0] | 원앞[1]
def 맞대(실, 점):   # 다른 자리에서: 원래 선 재현율 · 다시 그린 선 정밀도 → F
    a = 원 & 다름; b = (실 | 점) & 다름; ad, bd = cv2.dilate(a.astype(np.uint8), k3) > 0, cv2.dilate(b.astype(np.uint8), k3) > 0
    p = (b & ad).sum() / max(b.sum(), 1); r = (a & bd).sum() / max(a.sum(), 1); return 2 * p * r / max(p + r, 1e-9), a & ~bd, b & ~ad
점수 = []
for j, (v, 칸v, f1) in enumerate(가설[:4]):
    실, 점 = 투[j]; 점수.append(맞대(실, 점)); fF, 빠, 넘 = 점수[-1]; x0 = .25 + j * .185
    판(x0, .14, .085, .22, 도(실, 점), "가설 %d 다시 그린 앞" % (j + 1), cmap="gray", vmin=0, vmax=1)
    ov = np.ones((48, 48, 3)); ov[원앞[0] | 원앞[1]] = [.7, .7, .7]; ov[실 | 점] = [.1, .55, .25]; ov[빠] = [.85, .1, .1]; ov[넘] = [.95, .6, .1]
    판(x0 + .09, .14, .085, .22, ov, "맞대기(가설끼리 다른 자리만) F %.2f\n초록 맞음 · 빨강 빠짐 · 주황 없는 선" % fF)
best = int(np.argmax([s[0] for s in 점수])); f.text(.25, .075, "▲ 가장 잘 맞음 = 가설 %d (%s) · 정답 3D 와 F %.2f" % (best + 1, ("포켓 %d 층" % 가설[best][0]) if 가설[best][0] < 32 else "관통", 가설[best][2]), fontsize=13, color="#d33", weight="bold")
칸(.01, .04, .2, .44, "한 바퀴", "#ffffff")
f.text(.025, .40, "원화(도면)  (a)\n  ↓ 기하 처리  (b)\n코드  (c)\n  ↓ 기하 처리  (d)\n원화(다시 그림)\n  ↑ 원래 도면과 맞대기  (e)", fontsize=16, va="top", linespacing=1.6)
f.text(.025, .1, "기존 판0: 날 화소 → U-Net → 화소마다 층\n(원 안 0 층 / 뚫림 반반 · 바닥 16 층 확률 0.01)", fontsize=11, color="#888")
for (x1, y1, x2, y2) in ((.21, .74, .23, .74), (.53, .74, .55, .74)):
    f.add_artist(FancyArrowPatch((x1, y1), (x2, y2), transform=f.transFigure, arrowstyle="-|>", mutation_scale=25, lw=2, color="#444"))
f.add_artist(FancyArrowPatch((.77, .52), (.77, .48), transform=f.transFigure, arrowstyle="-|>", mutation_scale=25, lw=2, color="#444"))
f.suptitle("Fig. 1  도면 → 기하 처리 → 코드 → 기하 처리 → 도면  (부품 %d 실제 데이터)" % i, fontsize=20, y=.995)
f.savefig(O + "구조99.png", dpi=60); print(O + "구조99.png", 후, [(g[0], round(g[2], 3), round(s[0], 3)) for g, s in zip(가설, 점수)])
