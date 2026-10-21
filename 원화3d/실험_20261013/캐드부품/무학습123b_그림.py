# 123b G2: 정답 | 학습한 모델 | 7종류 평균 중 가장 겹치는 것 | 학습 없음(늘 같은 답) — 확인/무학습.json 을 그림으로 · 10-21
# 사용(cadrille venv · ART_CL=0): 무학습123b_그림.py → out/설명/캐드부품/모델123b/확인/무학습.png
import os, json, numpy as np
os.environ["ART_CL"] = "0"
import 모델123 as T, 모델120 as M, 설계116 as S, 데이터117 as Q
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
색 = json.load(open(M.D + "색인.json", encoding="utf-8")); 과 = [M.과녁(json.loads(r["코드"])) for r in 색 if r["i"] < M.NT]
k = np.array([g["k"] for g in 과]); 치 = np.stack([g["치"] for g in 과]); 종류들 = [M.사양(kk, 치[k == kk].mean(0), np.zeros((2, 8)), [0., 0.], [0., 0.])["바탕"]["종류"] for kk in range(7)]
def 평균(이름): kk = 종류들.index(이름); return Q.렌더(S.메시(S.짓기(M.사양(kk, 치[k == kk].mean(0), np.zeros((2, 8)), [0., 0.], [0., 0.])))[0])[0]
줄 = json.load(open(T.D + "확인/무학습.json", encoding="utf-8")); 상수종류 = 종류들[int(np.bincount(k).argmax())]; 상수그림 = 평균(상수종류)
열 = ("정답", "학습한 모델", "7종류 중 최선", "학습 없음")
fig, ax = plt.subplots(10, 8, figsize=(16, 21))
for t, r in enumerate(줄):
    칸 = [(M.읽(T.D + f"렌더/{r['이름']}_정답.png"), r["이름"][3:][:14]), (M.읽(T.D + f"렌더/{r['이름']}_셋.png"), f"{r['예측 종류']} {r['학습']:.2f}"),
         (평균(r["최선 종류"]), f"{r['최선 종류']} {r['종류별 최선']:.2f}"), (상수그림, f"{상수종류} {r['상수']:.2f}")]
    for c, (im, 글) in enumerate(칸):
        a = ax[t // 2, (t % 2) * 4 + c]; a.imshow(im); a.set_xticks([]); a.set_yticks([]); a.set_xlabel(글, fontsize=10)
        if t < 2: a.set_title(열[c], fontsize=12)
        if c == 1: [s.set_color("green" if r["학습"] > r["상수"] else "red") or s.set_linewidth(2) for s in a.spines.values()]
fig.suptitle(f"G2 실제 CAD 20 · 3/4 IoU 중앙 — 학습 없음 {np.median([r['상수'] for r in 줄]):.3f} · 학습한 모델 {np.median([r['학습'] for r in 줄]):.3f} · 7종류 중 최선 {np.median([r['종류별 최선'] for r in 줄]):.3f}\n초록 테두리 = 학습한 모델이 학습 없음보다 나음", fontsize=14)
fig.tight_layout(rect=(0, 0, 1, .965)); fig.savefig(T.D + "확인/무학습.png", dpi=80); print("끝")
