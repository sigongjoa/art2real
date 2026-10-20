# 판정기준120 모델의 어려운 것 — 처음 보는 생성 시험 200 전부를 입력과 같은 시점에서 정답 · 예측 렌더 → 실루엣 IoU 낮은 순 12 · 특징 많은 것 · 10-20
# 사용(cadrille venv): 어려운120.py → out/설명/캐드부품/모델120/어려운.png · 어려운.json
import json, numpy as np, cv2, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 설계116 as S, 데이터117 as Q, 모델120 as M
plt.rcParams["font.family"] = "Malgun Gothic"; D = M.D; j = json.load(open(D + "학습.json", encoding="utf-8")); 줄 = []
def 특글(s): return " · ".join(f["종류"] for f in s["특징"]) or "없음"
for n, p, g in zip(j["시험"]["번호"], j["시험"]["예측"], j["시험"]["정답"]):
    g = json.loads(g); rng = np.random.default_rng(120000 + n); S.무작위(rng); a, e = float(rng.uniform(0, 360)), float(rng.uniform(15, 35))
    ig, sg = Q.렌더(S.메시(S.짓기(g))[0], a, e)
    try: ip, sp = Q.렌더(S.메시(S.짓기(p))[0], a, e)
    except Exception: ip, sp = np.full_like(ig, 255), np.zeros_like(sg)
    iou = (sg & sp).sum() / max((sg | sp).sum(), 1); 특맞 = sorted(f["종류"] for f in g["특징"]) == sorted(f["종류"] for f in p["특징"])
    줄.append((iou, n, g, p, ig, ip, 특맞))
줄.sort(key=lambda x: x[0]); ious = np.array([x[0] for x in 줄])
요 = {"IoU 중앙": float(np.median(ious)), "IoU < 0.9 몫": float((ious < .9).mean()), "특징 종류 다 맞음": float(np.mean([x[6] for x in 줄])), "특징 ≥ 2 인 것 특징 맞음": float(np.mean([x[6] for x in 줄 if len([f for f in x[2]["특징"] if f["종류"] != "필렛"]) >= 2] or [0])), "기울임 있는 것 IoU 중앙": float(np.median([x[0] for x in 줄 if x[2]["기울임"]]))}
json.dump({"요약": 요, "낮은 순": [{"번호": x[1], "IoU": round(float(x[0]), 3), "정답": x[2], "예측": x[3]} for x in 줄[:20]]}, open(D + "어려운.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(요)
fig, ax = plt.subplots(4, 9, figsize=(20, 10.5))
for k, (iou, n, g, p, ig, ip, _) in enumerate(줄[:12]):
    for t, (im, lab) in enumerate(((cv2.imdecode(np.fromfile(D + f"렌더/{n:05d}.png", np.uint8), 1)[..., ::-1], f"입력 #{n}"), (ig, f"정답 {g['바탕']['종류']} · {특글(g)}" + (f" · 기움 {g['기울임']:.0f}°" if g["기울임"] else "")), (ip, f"예측 {p['바탕']['종류']} · {특글(p)} · IoU {iou:.2f}"))):
        x = ax[k // 3, (k % 3) * 3 + t]; x.imshow(im); x.axis("off"); x.set_title(lab, fontsize=8.5, color="#d8262b" if t == 2 else "#333")
fig.suptitle(f"모델120 이 가장 못한 12 (처음 보는 생성 부품 200 중 · 같은 시점) — IoU 중앙 {요['IoU 중앙']:.2f} · 0.9 아래 {요['IoU < 0.9 몫']:.0%} · 특징 종류 다 맞음 {요['특징 종류 다 맞음']:.0%} · 특징 둘 이상이면 {요['특징 ≥ 2 인 것 특징 맞음']:.0%}", fontsize=13)
plt.tight_layout(); plt.savefig(D + "어려운.png", dpi=72); print("저장")
