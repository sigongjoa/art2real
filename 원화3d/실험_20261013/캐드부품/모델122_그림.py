# 판정기준122 그림 — ① 시점 준 머리의 에폭별 예측 렌더(고정 6) ② 줄마다 입력 | 정답 | 시점 없음 | 시점 줌 (같은 시점 · 차이 큰 순)
# 사용(cadrille venv): 모델122_그림.py → out/설명/캐드부품/모델122/과정.png · 비교.png
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 모델122 as P, 모델120 as M, 설계116 as S, 데이터117 as Q
plt.rcParams["font.family"] = "Malgun Gothic"; D = P.D; j = json.load(open(D + "학습.json", encoding="utf-8")); 결 = json.load(open(D + "결과.json", encoding="utf-8")); 요 = 결["요약"]
에 = sorted(int(e) for e in j["시점"]["과정"]); fig, ax = plt.subplots(6, len(에) + 1, figsize=(2 * (len(에) + 1), 12.5))
for t, n in enumerate(j["고정"]):
    ax[t, 0].imshow(M.읽(M.D + f"렌더/{n:05d}.png")); ax[t, 0].set_title("입력" if t == 0 else "", fontsize=10)
    for c, ep in enumerate(에):
        try: ax[t, c + 1].imshow(M.읽(D + f"렌더/과정_{ep:02d}_{t}.png"))
        except Exception: ax[t, c + 1].text(.5, .5, "짓기 실패", ha="center", color="#d8262b")
        if t == 0: ax[t, c + 1].set_title(f"에폭 {ep}", fontsize=10)
for a in ax.ravel(): a.axis("off")
fig.suptitle("122 시점 준 머리 — 에폭마다 같은 시험 6 개 예측(입력과 같은 시점 렌더)", fontsize=13); plt.tight_layout(rect=(0, 0, 1, .96)); plt.savefig(D + "과정.png", dpi=70); plt.close(fig)
없, 시 = {x["번호"]: x for x in 결["부품"]["없음"]["시험"]}, {x["번호"]: x for x in 결["부품"]["시점"]["시험"]}
def 특글(s): return " · ".join(f["종류"] for f in s["특징"]) or "없음"
차 = sorted(시, key=lambda n: 시[n]["IoU"] - 없[n]["IoU"]); 고른 = 차[::-1][:5] + 차[:4]; 정 = dict(zip(j["번호"], j["정답"])); 예 = {팔: dict(zip(j["번호"], j[팔]["시험"])) for 팔 in ("없음", "시점")}
fig, ax = plt.subplots(len(고른), 4, figsize=(4 * 2.4, len(고른) * 2.5))
for i, n in enumerate(고른):
    g = json.loads(정[n]); a, e = P.시점(n)
    칸 = [(M.읽(M.D + f"렌더/{n:05d}.png"), f"입력 #{n} · 방위 {a:.0f}°"), (Q.렌더(S.메시(S.짓기(g))[0], a, e)[0], f"정답 {g['바탕']['종류']} · {특글(g)}")]
    for 팔 in ("없음", "시점"):
        try: im = M.읽(D + f"렌더/{n}_{팔}.png")
        except Exception: im = np.full((256, 256, 3), 255, np.uint8)
        칸.append((im, f"시점 {팔} · {특글(예[팔][n])} · {(없 if 팔 == '없음' else 시)[n]['IoU']:.2f}"))
    for t, (im, lab) in enumerate(칸): ax[i, t].imshow(im); ax[i, t].axis("off"); ax[i, t].set_title(lab, fontsize=8.5, color="#28a050" if t == 3 and 시[n]["IoU"] > 없[n]["IoU"] + .005 else "#d8262b" if t == 3 else "#333")
s = lambda 팔: f"IoU {요[팔]['같은 시점 IoU 중앙']:.3f} · 특징 다 맞음 {요[팔]['특징 종류 다 맞음']:.0%} · 구멍 자리 오차 {요[팔]['구멍 자리 오차 중앙']:.3f}"
fig.suptitle(f"생성 시험 200 (같은 시점) — 위 5 줄 시점 주어 나아진 것 · 아래 4 줄 나빠진 것\n없음 {s('없음')}\n시점 {s('시점')}\n섞음 {s('섞음')}", fontsize=10.5); plt.tight_layout(rect=(0, 0, 1, .92)); plt.savefig(D + "비교.png", dpi=72); print("저장")
