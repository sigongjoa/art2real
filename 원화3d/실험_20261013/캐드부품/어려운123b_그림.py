# 123b 생성 시험 중 IoU 가장 낮은 12 — 위 · 앞 · 옆 입력 | 정답 | 예측 · 확인/상수기준.json 을 씀 · 10-21
# 사용(cadrille venv · ART_CL=0): 어려운123b_그림.py → out/설명/캐드부품/모델123b/확인/어려운.png
import os, json
os.environ["ART_CL"] = "0"
import 모델123 as T, 모델120 as M
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
j = json.load(open(T.D + "학습.json", encoding="utf-8")); 정 = {n: json.loads(g)["바탕"]["종류"] for n, g in zip(j["번호"], j["정답"])}
줄 = sorted(json.load(open(T.D + "확인/상수기준.json", encoding="utf-8"))["부품"], key=lambda x: x["학습"])[:12]
fig, ax = plt.subplots(6, 10, figsize=(20, 13))
for t, x in enumerate(줄):
    n = x["번호"]; 칸 = [M.읽(T.D + f"도면/{n:05d}_{v}.png") for v in T.뷰] + [M.읽(T.D + f"렌더/{n}_정답.png"), M.읽(T.D + f"렌더/{n}_셋.png")]
    for c, im in enumerate(칸):
        a = ax[t // 2, (t % 2) * 5 + c]; a.imshow(im); a.set_xticks([]); a.set_yticks([])
        if t < 2: a.set_title(("위", "앞", "옆", "정답", "예측")[c], fontsize=12)
        if c == 3: a.set_xlabel(f"{n} {정[n]}", fontsize=10)
        if c == 4: a.set_xlabel(f"{x['예측 종류']} {x['학습']:.2f}", fontsize=10, color="red" if x["예측 종류"] != 정[n] else "black")
fig.suptitle("생성 시험 200 중 IoU 가장 낮은 12 (빨간 글씨 = 종류 틀림)", fontsize=14)
fig.tight_layout(rect=(0, 0, 1, .96)); fig.savefig(T.D + "확인/어려운.png", dpi=75); print([(x["번호"], x["학습"]) for x in 줄])
