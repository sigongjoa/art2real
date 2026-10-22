# 판정기준127 그림 — 처음 보는 조립 부품 6: 정답 | Gemma(125) | 3면도 직접(127) · 10-22
import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 모델120 as M
plt.rcParams["font.family"] = "Malgun Gothic"
R = "G:/art2real/out/설명/캐드부품/"; a = json.load(open(R + "모델127/결과.json", encoding="utf-8")); b = json.load(open(R + "모델125/결과.json", encoding="utf-8"))
ns = [f"{12000 + i:05d}" for i in range(6)]; 아 = dict(zip(a["시험"]["이름"], a["시험"]["IoU"])); 비 = dict(zip(b["시험"]["이름"], b["시험"]["IoU"]))
fig, ax = plt.subplots(3, 6, figsize=(21, 11))
for c, n in enumerate(ns):
    for r, (p, 글) in enumerate(((R + f"모델124/렌더/{n}_정답.png", f"{n} 정답"), (R + f"모델125/렌더/{n}_125.png", f"Gemma 입력 {비[n]:.2f}"), (R + f"모델127/렌더/{n}_예측.png", f"3면도 직접 {아[n]:.2f}"))):
        try: ax[r, c].imshow(M.읽(p))
        except Exception: pass
        ax[r, c].set_title(글, fontsize=15); ax[r, c].axis("off")
fig.suptitle(f"판정기준127 — Gemma 빼고 3면도를 직접 · 처음 보는 부품 IoU {a['시험']['IoU 중앙']:.3f} (Gemma {b['시험']['IoU 중앙']:.3f}) · 학습 {a['학습']['IoU 중앙']:.3f} ({b['학습']['IoU 중앙']:.3f}) · 자리 오차 {a['시험']['항목 loss']['자리'] / 4:.3f} (평균 0.323)", fontsize=15)
fig.tight_layout(); fig.savefig(R + "모델127/그림_비교127.png", dpi=60); print("끝")
