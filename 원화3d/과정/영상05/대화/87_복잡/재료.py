# 87 편 위쪽 카드 재료 — 123b 실제 렌더: 렉스 입력 · 예측 · 복잡 실물 6 짝 · 생성 시험 3 짝 · 점수 카드 · 학습 부품 12 · 10-21
# 사용(cadrille venv · ART_CL=0): python 재료.py
import sys, os, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, "G:/art2real/원화3d/실험_20261013/캐드부품"); os.chdir("G:/art2real/원화3d/실험_20261013/캐드부품"); os.environ["ART_CL"] = "0"
plt.rcParams["font.family"] = "Malgun Gothic"
import 모델123 as T, 모델120 as M, 설계116 as S, 데이터117 as Q, 복잡123b as C
A = "G:/art2real/out/영상05/대화/87_복잡/자료/"; os.makedirs(A, exist_ok=True)
진, 빨, 초 = "#6b7078", "#d8262b", "#28a050"
def 판(): fig = plt.figure(figsize=(10, 7), dpi=100); fig.patch.set_alpha(0); return fig
def 저장(fig, nm): fig.savefig(A + nm, transparent=True); plt.close(fig)
결 = {r["이름"]: r for r in json.load(open(C.D + "결과.json", encoding="utf-8"))}
def 짝(nm): return Q.렌더(C.메시(nm))[0], Q.렌더(S.메시(S.짓기(결[nm]["사양"]))[0])[0]
def 화살(fig, y=.5): ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.annotate("", xy=(.55, y), xytext=(.46, y), arrowprops=dict(arrowstyle="-|>", color="#333", lw=5)); return ax
# 렉스
fig = 판(); a, b = 짝("메기어렉스")
for j, im in enumerate((a, b)): ax = fig.add_axes([.02 + j * .52, .1, .46, .8]); ax.imshow(im); ax.axis("off")
ax = 화살(fig); ax.text(.79, .06, "믿는 정도 %.2f" % 결["메기어렉스"]["확신"], fontsize=34, color=빨, ha="center"); 저장(fig, "렉스.png")
def 짝판(짝들, nm, 열=3):   # 짝마다 왼 입력 · 오 모델 답, 위에 이름표
    fig = 판(); 행 = (len(짝들) + 열 - 1) // 열; h = .9 / 행
    for i, (a, b) in enumerate(짝들):
        x0 = .01 + (i % 열) * (.97 / 열); y0 = .9 - (i // 열 + 1) * h
        for j, im in enumerate((a, b)): ax = fig.add_axes([x0 + j * (.485 / 열), y0, .485 / 열 - .01, h - .02]); ax.imshow(im); ax.axis("off")
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    for c in range(열): ax.text(.01 + c / 열 + .25 / 열, .94, "입력", fontsize=22, color=진, ha="center"); ax.text(.01 + c / 열 + .75 / 열, .94, "모델 답", fontsize=22, color=빨, ha="center")
    저장(fig, nm)
# 실제 CAD 부품(G2) 4 짝 — 입력은 다른데 답은 상자 · 계단축
짝판([(M.읽(T.D + f"렌더/G2_{k}_정답.png"), M.읽(T.D + f"렌더/G2_{k}_셋.png")) for k in ("00", "02", "07", "13")], "실제부품.png", 2)
# 복잡 실물 6 짝
짝판([짝(nm) for nm in ("메기어렉스", "거미허리", "부엉이가슴", "매드캣몸통")], "복잡들.png", 2)
# 생성 시험 6 짝(정답 → 예측) — 입력마다 답이 다르다
fig = 판(); 번 = (6000, 6001, 6011, 6193, 6171, 6020)
for i, n in enumerate(번):
    for j, k in enumerate(("정답", "셋")): ax = fig.add_axes([.01 + i * .165, .47 - j * .44, .155, .4]); ax.imshow(M.읽(T.D + f"렌더/{n}_{k}.png")); ax.axis("off")
ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.text(.5, .91, "정답", fontsize=24, color=진, ha="center"); ax.text(.5, .47, "모델 답", fontsize=24, color=초, ha="center")
저장(fig, "생성맞힘.png")
# 점수
상 = json.load(open(T.D + "확인/상수기준.json", encoding="utf-8"))["요약"]; 실 = np.median([r["IoU"] for r in 결.values()]); 확 = np.median([r["확신"] for r in 결.values()])
fig = 판(); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 7)
ax.text(2.6, 4.0, f"{상['학습 IoU 중앙']:.2f}", fontsize=110, color=초, ha="center", va="center"); ax.text(2.6, 1.6, "학습한 모양", fontsize=34, color=진, ha="center")
ax.text(7.4, 4.0, f"{실:.2f}", fontsize=110, color=빨, ha="center", va="center"); ax.text(7.4, 1.6, "복잡한 실물", fontsize=34, color=진, ha="center"); 저장(fig, "점수.png")
# 학습 부품 12
fig = 판()
for i in range(12): ax = fig.add_axes([.01 + (i % 4) * .25, .67 - (i // 4) * .33, .23, .31]); ax.imshow(M.읽(M.D + f"렌더/{i * 37:05d}.png")); ax.axis("off")
저장(fig, "학습데이터.png")
색 = json.load(open(M.D + "색인.json", encoding="utf-8"))
print("저장 · 학습 수", sum(r["i"] < M.NT for r in 색), "· 생성 시험", 상["학습 IoU 중앙"], 상["서로 다른 예측 사양 수"], "· 실물 IoU", 실, "확신", 확)
