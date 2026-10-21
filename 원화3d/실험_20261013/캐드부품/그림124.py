# 판정기준124 결과 그림 — 과정(에폭마다 고정 시험 6) · 조립 시험(나쁨 · 중간 · 좋음) · 실물 12 · G2 20 · 렌더는 모델124.py 평가가 남긴 것 · 10-21
# 사용(cadrille venv): 그림124.py → out/설명/캐드부품/모델124/그림_{과정,조립,실물,G2}.png
import json, numpy as np, 모델120 as M
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
D = "G:/art2real/out/설명/캐드부품/모델124/"; R = D + "렌더/"
결 = json.load(open(D + "결과.json", encoding="utf-8")); j = json.load(open(D + "학습.json", encoding="utf-8")); 요 = 결["요약"]
흰 = np.full((256, 256, 3), 255, np.uint8)
def 읽(p):
    try: return M.읽(p)
    except Exception: return 흰
def 칸(a, im, 위=None, 아래=None, 색="black"):
    a.imshow(im); a.set_xticks([]); a.set_yticks([])
    if 위: a.set_title(위, fontsize=11)
    if 아래: a.set_xlabel(아래, fontsize=10, color=색)
# 1 과정
에 = sorted(int(e) for e in j["과정"]); 기 = {r["에폭"]: r for r in j["기록"]}; 고 = j["고정"]
fig, ax = plt.subplots(len(고), len(에) + 1, figsize=(2.2 * (len(에) + 1), 2.3 * len(고)))
for t, n in enumerate(고):
    칸(ax[t, 0], 읽(R + f"{n}_정답.png"), "정답" if t == 0 else None, f"{n} · 몸 {len(json.load(open(D + f'사양/{n}.json', encoding='utf-8'))['코드']['몸'])}")
    for c, e in enumerate(에): 칸(ax[t, c + 1], 읽(R + f"과정_{e:02d}_{t}.png"), f"에폭 {e}\n시험 loss {기[e]['시험']:.2f}" if t == 0 else None)
fig.suptitle("124 학습 과정 — 고정 시험 부품 6 · 시험 loss 는 21 에폭 6.56 이 최저, 60 에폭 7.13(과적합)", fontsize=14); fig.tight_layout(rect=(0, 0, 1, .96)); fig.savefig(D + "그림_과정.png", dpi=70); plt.close()
# 2 조립 시험: 나쁨 4 · 중간 4 · 좋음 4
줄 = sorted(결["부품"]["조립 시험"], key=lambda x: x["124"]); k = len(줄); 뽑 = 줄[:4] + 줄[k // 2 - 2:k // 2 + 2] + 줄[-4:]
fig, ax = plt.subplots(6, 4, figsize=(10, 15))
for t, x in enumerate(뽑):
    r, c = (t // 4) * 2, t % 4
    칸(ax[r, c], 읽(R + f"{x['이름']}_정답.png"), ("나쁨", "", "", "", "중간", "", "", "", "좋음", "", "", "")[t] or None, f"정답 몸 {x['몸 수']}")
    칸(ax[r + 1, c], 읽(R + f"{x['이름']}_124.png"), None, f"124 몸 {x['예측 몸 수']} · {x['124']:.2f} (123b {x['123b']:.2f})", "red" if x["124"] < .5 else "black")
fig.suptitle(f"조립 시험 {k} — 3/4 IoU 중앙 124 {요['조립 시험 124']:.3f} · 123b {요['조립 시험 123b']:.3f} · 몸 수 맞음 {요['조립 몸 수 맞음']:.0%}\n(위 = 정답, 아래 = 124 답)", fontsize=13)
fig.tight_layout(rect=(0, 0, 1, .95)); fig.savefig(D + "그림_조립.png", dpi=70); plt.close()
# 3 실물 12 · 4 G2 20
def 짝판(줄, 파일, 제목, 열=6):
    n = len(줄); 행 = (n + 열 - 1) // 열; fig, ax = plt.subplots(행 * 2, 열, figsize=(2.6 * 열, 2.7 * 행 * 2))
    for a in ax.ravel(): a.axis("off")
    for t, x in enumerate(줄):
        r, c = (t // 열) * 2, t % 열; ax[r, c].axis("on"); ax[r + 1, c].axis("on")
        칸(ax[r, c], 읽(R + f"{x['이름']}_정답.png"), None, x["이름"].replace("실물_", ""))
        칸(ax[r + 1, c], 읽(R + f"{x['이름']}_124.png"), None, f"124 {x['124']:.2f} · 123b {x['123b']:.2f}", "red" if x["124"] < x["123b"] else "green")
    fig.suptitle(제목, fontsize=13); fig.tight_layout(rect=(0, 0, 1, .95)); fig.savefig(D + 파일, dpi=70); plt.close()
짝판(결["부품"]["실물"], "그림_실물.png", f"복잡 실물 12 — 중앙 124 {요['실물 124']:.3f} · 123b {요['실물 123b']:.3f} (기준 0.60) · 위 정답 · 아래 124 답 · 초록 = 123b 보다 나음")
짝판([x for x in 결["부품"]["G"] if x["무리"] == "G2"], "그림_G2.png", f"G2 실제 부품 20 — 중앙 124 {요['G2 124']:.3f} · 123b {요['G2 123b']:.3f} (기준 0.55) · 위 정답 · 아래 124 답")
print("끝")
