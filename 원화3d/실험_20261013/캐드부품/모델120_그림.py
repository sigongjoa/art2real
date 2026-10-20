# 판정기준120 그림 — ① 학습 과정: 고정 시험 6 개 입력 | 에폭별 예측 코드 렌더 · loss 곡선 ② G1 · G2: 입력 | 모델 예측 | 119 라이브러리 고르기 · 10-20
# 사용: python 모델120_그림.py → out/설명/캐드부품/모델120/과정.png · 비교_G1.png · 비교_G2.png
import json, numpy as np, cv2, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
D = "G:/art2real/out/설명/캐드부품/모델120/"; D119 = "G:/art2real/out/설명/캐드부품/어려움119/"
읽 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), 1)[..., ::-1]
j = json.load(open(D + "학습.json", encoding="utf-8")); 결 = json.load(open(D + "결과.json", encoding="utf-8")); 에 = sorted(int(e) for e in j["과정"])
fig = plt.figure(figsize=(2 * (len(에) + 1), 2 * 6 + 2.6))
for t, n in enumerate(j["고정"]):
    ax = fig.add_axes([0, 1 - (t + 1) / 6.9, 1 / (len(에) + 1), 1 / 7.2]); ax.imshow(읽(D + f"렌더/{n:05d}.png")); ax.axis("off"); ax.set_title("입력" if t == 0 else "", fontsize=10)
    for c, ep in enumerate(에):
        ax = fig.add_axes([(c + 1) / (len(에) + 1), 1 - (t + 1) / 6.9, 1 / (len(에) + 1), 1 / 7.2]); ax.axis("off")
        try: ax.imshow(읽(D + f"렌더/과정_{ep:02d}_{t}.png"))
        except Exception: ax.text(.5, .5, "짓기 실패", ha="center", color="#d8262b")
        if t == 0: ax.set_title(f"에폭 {ep}", fontsize=10)
ax = fig.add_axes([.06, .03, .9, .1]); 기 = j["기록"]; ax.plot([r["학습"] for r in 기], label="학습 loss"); ax.plot([r["시험"] for r in 기], label="시험 loss"); ax2 = ax.twinx(); ax2.plot([r["시험 종류"] for r in 기], color="#28a050", label="시험 종류 맞음"); ax2.set_ylim(0, 1); ax.legend(loc="upper center", fontsize=8); ax2.legend(loc="upper right", fontsize=8)
plt.savefig(D + "과정.png", dpi=70); plt.close(fig)
요 = 결["요약"]
for g in ("G1", "G2"):
    rs = 결["부품"][g]; c = 5; fig, ax = plt.subplots(4, c * 3, figsize=(c * 3 * 1.9, 4 * 2.3))
    for a in ax.ravel(): a.axis("off")
    for k, r in enumerate(rs):
        i, jj = divmod(k, c)
        for t, (p, lab) in enumerate(((D119 + f"렌더/{r['이름']}.png", "입력" + (f" · {r['정답 종류']}" if g == "G1" else "")), (D + f"렌더/{r['이름']}_모델.png", f"모델 · {r['종류']} · {r['IoU']:.2f}"), (D119 + f"렌더/{r['이름']}_찾기.png", f"119 고르기 · {r['119 IoU']:.2f}"))):
            a = ax[i, jj * 3 + t]
            try: a.imshow(읽(p))
            except Exception: a.text(.5, .5, "짓기 실패", ha="center", color="#d8262b")
            a.set_title(lab, fontsize=8, color="#28a050" if t == 1 else "#333")
    fig.suptitle(f"{g} — IoU 중앙 모델 {요[f'{g} IoU 중앙(IoU)']:.2f} · 119 고르기 {요[f'{g} IoU 중앙(119 IoU)']:.2f} · 대조②(종류 + 평균 치수) {요[f'{g} IoU 중앙(대조② IoU)']:.2f}" + (f" · 종류 {요['G1 종류']:.2f}" if g == "G1" else ""), fontsize=13)
    plt.tight_layout(); plt.savefig(D + f"비교_{g}.png", dpi=80); plt.close(fig)
print("저장")
