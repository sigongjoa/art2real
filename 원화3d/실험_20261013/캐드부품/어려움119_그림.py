# 판정기준119 시트 — 무리마다 줄: 입력(155°) | 찾기로 고른 코드(같은 시점 렌더) | 대조(무작위 8 중 1 등) · 10-20
# 사용: python 어려움119_그림.py → out/설명/캐드부품/어려움119/시트_G1.png · 시트_G2.png · 시트_G3.png
import json, numpy as np, cv2, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
D = "G:/art2real/out/설명/캐드부품/어려움119/"; 결 = json.load(open(D + "결과.json", encoding="utf-8"))
읽 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), 1)[..., ::-1]
for g, 제목 in (("G1", "생성기 어려운 부품(특징 ≥ 2 · 기울임)"), ("G2", "실제 CAD 부품"), ("G3", "피규어 부품")):
    rs = [r for r in 결["부품"] if r["무리"] == g]; n = len(rs); c = 5 if n > 5 else n
    fig, ax = plt.subplots((n + c - 1) // c * 1, c * 3, figsize=(c * 3 * 1.9, (n + c - 1) // c * 2.3), squeeze=False)
    for a in ax.ravel(): a.axis("off")
    for k, r in enumerate(rs):
        i, j = divmod(k, c)
        for t, (nm, lab) in enumerate(((r["이름"], "입력" + (f" · {r['정답 종류']}" if g == "G1" else "")), (r["이름"] + "_찾기", f"찾기 · {r['찾기']['종류']} · {r['찾기']['IoU']:.2f}"), (r["이름"] + "_대조", f"대조 · {r['대조']['IoU']:.2f}"))):
            a = ax[i, j * 3 + t]; a.imshow(읽(D + f"렌더/{nm}.png")); a.set_title(lab, fontsize=8, color="#28a050" if t == 1 else "#333")
    요 = 결["요약"]; fig.suptitle(f"{g} {제목} — IoU 중앙 찾기 {요[f'{g} IoU 중앙(찾기)']:.2f} · 대조 {요[f'{g} IoU 중앙(대조)']:.2f}" + (f" · 종류 맞음 {요['G1 종류 맞음']:.2f}" if g == "G1" else ""), fontsize=13)
    plt.tight_layout(); plt.savefig(D + f"시트_{g}.png", dpi=80); plt.close(fig); print(g)
