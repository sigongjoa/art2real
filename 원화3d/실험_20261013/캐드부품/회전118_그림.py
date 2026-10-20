# 판정기준118b 그림 — T2(수치 변형 고르기) 세 판 맞대기: 117 임베딩 · 118 시점(실루엣만) · 118b 시점(실루엣 × 모서리 · 좁혀 찾기) · 종류별 · 원기둥 예시 · 10-20
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, cv2
plt.rcParams["font.family"] = "Malgun Gothic"
import 설계116 as S, 데이터117 as Q, 회전118 as R
D = Q.D; a = json.load(open(D + "회전118.json", encoding="utf-8")); b = json.load(open(D + "회전118b.json", encoding="utf-8")); e = json.load(open(D + "결과.json", encoding="utf-8"))
fig = plt.figure(figsize=(18, 9)); ax = fig.add_axes([.05, .12, .5, .72]); 종 = list(b["T2 종류별"]); x = np.arange(len(종) + 1)
for j, (v, nm, c) in enumerate(((a["T2 종류별"], "118 시점(실루엣만)", "#e0a020"), (b["T2 종류별"], "118b 시점(실루엣 × 모서리 · 5° 좁혀)", "#28a050"))):
    vals = [v[k] for k in 종] + [[a, b][j]["T2"]]; ax.bar(x + (j - .5) * .38, vals, .36, color=c, label=nm); [ax.text(xx + (j - .5) * .38, vv + .015, f"{vv:.2f}", ha="center", fontsize=10) for xx, vv in zip(x, vals)]
ax.axhline(.8, color="#d8262b", ls="--"); ax.axhline(e["T2"]["이미지(다른 시점)→렌더"], color="#888", ls=":"); ax.text(len(종) + .5, .82, "기준 0.8", color="#d8262b", ha="right"); ax.text(len(종) + .5, e["T2"]["이미지(다른 시점)→렌더"] + .02, "117 임베딩 0.33", color="#666", ha="right")
ax.set_xticks(x); ax.set_xticklabels(종 + ["전체"]); ax.set_ylim(0, 1.12); ax.legend(loc="lower left"); ax.set_title("T2: 정답 + 수치 변형 5 중 1 등 맞힘(부품 100)", fontsize=13)
색 = json.load(open(D + "색인.json", encoding="utf-8")); r = next(r for r in 색 if r["정답"]["종류"] == "원기둥" and json.loads(r["정답"]["코드"])["특징"])
입 = cv2.imdecode(np.fromfile(D + "렌더/" + r["정답"]["이름"] + "_155.png", np.uint8), 1)[..., ::-1].copy()
m, *_ = S.메시(S.짓기(json.loads(r["정답"]["코드"]))); sc, az, el, _ = R.맞추기(m, 입); 정img, _ = Q.렌더(m, az, el)
v = r["T2"][0]; mv, *_ = S.메시(S.짓기(json.loads(v["코드"]))); sv, azv, elv, _ = R.맞추기(mv, 입); 변img, _ = Q.렌더(mv, azv, elv)
for j, (im, t) in enumerate(((입, "입력(155° · 방법은 모름)"), (정img, f"정답 후보 · 찾은 시점 {az}° · 점수 {sc:.2f}"), (변img, f"변형({v['변형']}) · {azv}° · 점수 {sv:.2f}"))):
    ax = fig.add_axes([.6 + (j % 2) * .2, .5 - (j // 2) * .42, .19, .38]); ax.imshow(im); ax.set_title(t, fontsize=10); ax.axis("off")
b2 = json.load(open(D + "회전118b_재채점.json", encoding="utf-8")); fig.suptitle(f"판정기준118b 실패(재채점) — 시점은 맞췄지만(오차 중앙 0°) 동점을 빼면 T2 {b2['T2 엄격(동점 = 틀림)']:.2f} · 막대는 동점을 정답으로 센 값 · 예시처럼 막힌 구멍 깊이는 겉 그림에 안 보여 동점", fontsize=13)
plt.savefig(D + "판정118b.png", dpi=70); print("저장")
