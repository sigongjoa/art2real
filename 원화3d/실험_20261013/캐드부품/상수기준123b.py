# 123b: 생성 시험 200 에서도 「늘 같은 답」이 얼마 나오나 — 학습 손실이 떨어진 게 진짜 입력을 읽어서인지 · 10-21
# 사용(cadrille venv · ART_CL=0): 상수기준123b.py → out/설명/캐드부품/모델123b/확인/상수기준.json · 상수기준.png
import os, json, numpy as np
os.environ["ART_CL"] = "0"
import 모델123 as T, 모델120 as M, 설계116 as S, 데이터117 as Q, 회전118 as R
from collections import Counter
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
색 = json.load(open(M.D + "색인.json", encoding="utf-8")); 과 = [M.과녁(json.loads(r["코드"])) for r in 색 if r["i"] < M.NT]
k = np.array([g["k"] for g in 과]); 치 = np.stack([g["치"] for g in 과])
평 = [Q.렌더(S.메시(S.짓기(M.사양(kk, 치[k == kk].mean(0), np.zeros((2, 8)), [0., 0.], [0., 0.])))[0])[1] for kk in range(7)]; 최빈 = int(np.bincount(k).argmax())
j = json.load(open(T.D + "학습.json", encoding="utf-8")); 결과 = json.load(open(T.D + "결과.json", encoding="utf-8"))["부품"]["셋"]["시험"]
iou = lambda a, b: float((a & b).sum() / max((a | b).sum(), 1))
줄 = []
for r, p in zip(결과, j["셋"]["시험"]):
    sg = R.실루엣(M.읽(T.D + f"렌더/{r['번호']}_정답.png")); 종 = [iou(s, sg) for s in 평]
    줄.append({"번호": r["번호"], "학습": r["IoU"], "상수": 종[최빈], "종류별 최선": max(종), "예측 종류": p["바탕"]["종류"]})
중 = lambda key: round(float(np.median([x[key] for x in 줄])), 4)
요 = {"수": len(줄), "학습 IoU 중앙": 중("학습"), "늘 같은 답 IoU 중앙": 중("상수"), "7종류 평균 중 최선 IoU 중앙": 중("종류별 최선"),
     "학습 > 늘 같은 답 몫": float(np.mean([x["학습"] > x["상수"] for x in 줄])), "예측 종류 분포": Counter(x["예측 종류"] for x in 줄), "서로 다른 예측 사양 수": len({json.dumps(p, sort_keys=True) for p in j["셋"]["시험"]})}
json.dump({"요약": 요, "부품": 줄}, open(T.D + "확인/상수기준.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(요, ensure_ascii=False, indent=1))
# 그림: 생성 시험 앞 12 — 위 · 앞 · 옆 입력 | 정답 | 예측
fig, ax = plt.subplots(6, 10, figsize=(20, 13))
for t, x in enumerate(줄[:12]):
    n = x["번호"]; 칸 = [M.읽(T.D + f"도면/{n:05d}_{v}.png") for v in T.뷰] + [M.읽(T.D + f"렌더/{n}_정답.png"), M.읽(T.D + f"렌더/{n}_셋.png")]
    for c, im in enumerate(칸):
        a = ax[t // 2, (t % 2) * 5 + c]; a.imshow(im); a.set_xticks([]); a.set_yticks([])
        if t < 2: a.set_title(("위", "앞", "옆", "정답", "예측")[c], fontsize=12)
        if c == 4: a.set_xlabel(f"{x['예측 종류']} {x['학습']:.2f}", fontsize=10)
fig.suptitle(f"생성 시험 — 입력마다 출력이 다르다 · IoU 중앙 학습 {요['학습 IoU 중앙']} · 늘 같은 답 {요['늘 같은 답 IoU 중앙']} · 서로 다른 예측 {요['서로 다른 예측 사양 수']}/{len(줄)}", fontsize=14)
fig.tight_layout(rect=(0, 0, 1, .96)); fig.savefig(T.D + "확인/상수기준.png", dpi=75); print("끝")
