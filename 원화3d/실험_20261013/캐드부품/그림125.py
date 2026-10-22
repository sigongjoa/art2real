# 판정기준125 그림 — 처음 보는 조립 부품 6: 정답 | MLP(124) | 트랜스포머(125) + 숫자 · 10-22
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 모델120 as M
plt.rcParams["font.family"] = "Malgun Gothic"
A, B5 = "G:/art2real/out/설명/캐드부품/모델124/", "G:/art2real/out/설명/캐드부품/모델125/"
a = json.load(open(B5 + "결과.json", encoding="utf-8")); b = json.load(open(A + "확인124.json", encoding="utf-8"))
ns = [f"{12000 + i:05d}" for i in range(6)]; 아 = dict(zip(a["시험"]["이름"], a["시험"]["IoU"])); 비 = dict(zip(b["시험"]["이름"], b["시험"]["IoU"]))
fig, ax = plt.subplots(3, 6, figsize=(21, 11))
for c, n in enumerate(ns):
    for r, (p, 글) in enumerate(((A + f"렌더/{n}_정답.png", f"{n} 정답"), (A + f"렌더/{n}_124.png", f"MLP {비[n]:.2f}"), (B5 + f"렌더/{n}_125.png", f"트랜스포머 {아[n]:.2f}"))):
        try: ax[r, c].imshow(M.읽(p))
        except Exception: pass
        ax[r, c].set_title(글, fontsize=15); ax[r, c].axis("off")
fig.suptitle(f"판정기준125 실패 — 머리를 트랜스포머로 바꿔도 같음 · 시험 IoU {a['시험']['IoU 중앙']:.3f} (MLP {b['시험']['IoU 중앙']:.3f}) · 학습 {a['학습']['IoU 중앙']:.3f} (MLP {b['학습']['IoU 중앙']:.3f}) · 자리 loss 시험 {a['시험']['항목 loss']['자리']:.2f} (MLP 1.33)", fontsize=16)
fig.tight_layout(); fig.savefig(B5 + "그림_비교125.png", dpi=60); print("끝")
