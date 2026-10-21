# 판정기준123 그림 — ① 셋 머리 에폭별 예측(고정 6) ② 줄마다 3면도 위 · 앞 · 옆 | 정답 3/4 | 120(그림 한 장) | 123(3면도) · 나아진 것 · 나빠진 것 ③ G2
# 사용(cadrille venv): 모델123_그림.py → out/설명/캐드부품/모델123/과정.png · 비교.png · 비교_G2.png
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 모델123 as T, 모델120 as M
plt.rcParams["font.family"] = "Malgun Gothic"; D = T.D; j = json.load(open(D + "학습.json", encoding="utf-8")); 결 = json.load(open(D + "결과.json", encoding="utf-8")); 요 = 결["요약"]
흰 = np.full((256, 256, 3), 255, np.uint8)
def 읽(p):
    try: return M.읽(p)
    except Exception: return 흰
에 = sorted(int(e) for e in j["셋"]["과정"]); fig, ax = plt.subplots(6, len(에) + 3, figsize=(2 * (len(에) + 3), 12.5))
for t, n in enumerate(j["고정"]):
    for k, nm in enumerate(T.뷰): ax[t, k].imshow(읽(D + f"도면/{n:05d}_{nm}.png")); ax[t, k].set_title(nm if t == 0 else "", fontsize=10)
    for c, ep in enumerate(에):
        ax[t, c + 3].imshow(읽(D + f"렌더/과정_{ep:02d}_{t}.png"))
        if t == 0: ax[t, c + 3].set_title(f"에폭 {ep}", fontsize=10)
for a in ax.ravel(): a.axis("off")
fig.suptitle("123 3면도 머리 — 에폭마다 같은 시험 6 개 예측(3/4 시점 렌더)", fontsize=13); plt.tight_layout(rect=(0, 0, 1, .96)); plt.savefig(D + "과정.png", dpi=70); plt.close(fig)
def 특글(s): return " · ".join(f["종류"] for f in s["특징"]) or "없음"
def 시트(줄들, 제목, 파일):
    fig, ax = plt.subplots(len(줄들), 6, figsize=(6 * 2.2, len(줄들) * 2.4), squeeze=False)
    for i, (n, a, b, 정글, 예글) in enumerate(줄들):
        칸 = [(읽(D + f"도면/{n}_{nm}.png"), f"{nm}" + (f" · {n}" if k == 0 else "")) for k, nm in enumerate(T.뷰)] + [(읽(D + f"렌더/{n}_정답.png"), 정글), (읽(D + f"렌더/{n}_120.png"), f"120 그림 한 장 · {a['IoU']:.2f}"), (읽(D + f"렌더/{n}_셋.png"), f"123 · {예글} · {b['IoU']:.2f}")]
        for t, (im, lab) in enumerate(칸): x = ax[i, t]; x.imshow(im); x.axis("off"); x.set_title(lab, fontsize=8.5, color=("#28a050" if b["IoU"] > a["IoU"] + .005 else "#d8262b") if t == 5 else "#333")
    fig.suptitle(제목, fontsize=10.5); plt.tight_layout(rect=(0, 0, 1, 1 - 1.2 / len(줄들) / 2.4)); plt.savefig(D + 파일, dpi=72); plt.close(fig)
가, 나 = {x["번호"]: x for x in 결["부품"]["120"]["시험"]}, {x["번호"]: x for x in 결["부품"]["셋"]["시험"]}; 정 = dict(zip(j["번호"], j["정답"])); 예 = dict(zip(j["번호"], j["셋"]["시험"]))
차 = sorted(나, key=lambda n: 나[n]["IoU"] - 가[n]["IoU"]); 고 = 차[::-1][:6] + 차[:3]
줄 = [(f"{n:05d}", 가[n], 나[n], "정답 " + json.loads(정[n])["바탕"]["종류"] + " · " + 특글(json.loads(정[n])), 특글(예[n])) for n in 고]
for n in 고:   # 렌더 파일 이름이 번호(0 채움 없음)라 맞춰 복사
    for 팔 in ("정답", "120", "셋"):
        try: M.저장(D + f"렌더/{n:05d}_{팔}.png", M.읽(D + f"렌더/{n}_{팔}.png"))
        except Exception: pass
s = lambda 팔: f"3/4 IoU {요[팔]['3/4 IoU 중앙']:.3f} · 특징 다 맞음 {요[팔]['특징 종류 다 맞음']:.0%} · 둘 이상 {요[팔]['특징 ≥ 2 맞음']:.0%} · 구멍 자리 {요[팔]['구멍 자리 오차 중앙']:.3f}"
시트(줄, f"생성 시험 200 — 위 6 줄 나아진 것 · 아래 3 줄 나빠진 것\n120(그림 한 장) {s('120')}\n123(3면도) {s('셋')}", "비교.png")
g가, g나 = {x["이름"]: x for x in 결["부품"]["120"]["G"]}, {x["이름"]: x for x in 결["부품"]["셋"]["G"]}; gp = dict(zip(j["G 이름"], j["셋"]["G"]))
g2 = sorted([n for n in g나 if n.startswith("G2")], key=lambda n: g나[n]["IoU"] - g가[n]["IoU"]); 고 = g2[::-1][:4] + g2[:3]
시트([(n, g가[n], g나[n], "정답(실제 CAD)", 특글(gp[n])) for n in 고], f"G2 실제 CAD — 3/4 IoU 중앙 120 {요['120']['G2 3/4 IoU 중앙']:.2f} → 123 {요['셋']['G2 3/4 IoU 중앙']:.2f} (위 4 나아짐 · 아래 3 나빠짐)", "비교_G2.png")
print("저장")
