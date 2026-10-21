# 판정기준121 그림 — 줄마다: 입력 | 120 · 121(입력 시점) | 정답 · 120 · 121(+90° 다른 시점) · 많이 나아진 것 · 나빠진 것 · G2 · 10-21
# 사용(cadrille venv): 다듬기121_그림.py → out/설명/캐드부품/다듬기121/비교.png · 비교_G2.png
import json, numpy as np, trimesh, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 다듬기121 as T, 데이터117 as Q, 모델120 as M
plt.rcParams["font.family"] = "Malgun Gothic"; 결 = json.load(open(T.D + "결과.json", encoding="utf-8")); 일 = {r["이름"]: r for r in json.load(open(T.D + "일감.json", encoding="utf-8"))}; 요 = 결["요약"]
def 그림(s, a, e):
    try: return Q.렌더(T._메시(s), a, e)[0]
    except Exception: return np.full((256, 256, 3), 255, np.uint8)
def 시트(rs, 제목, 파일):
    fig, ax = plt.subplots(len(rs), 6, figsize=(6 * 2.1, len(rs) * 2.3), squeeze=False)
    for i, r in enumerate(rs):
        w = 일[r["이름"]]; 진 = w["정답"]; mt = T._메시(json.loads(진["코드"])) if "코드" in 진 else trimesh.load(진["stl"], force="mesh")
        a1, e1 = r["120 시점"]; a2, e2 = r["121 시점"]
        칸 = [(M.읽(w["그림"]), f"입력 {r['이름']}"), (그림(r["120"], a1, e1), f"120 · {r['120 입력']:.2f}"), (그림(r["121"], a2, e2), f"121 다듬기 · {r['121 입력']:.2f}"),
             (Q.렌더(mt, (w["방위"] + 90) % 360, w["고도"])[0], "정답 · 다른 시점"), (그림(r["120"], (a1 + 90) % 360, e1), f"120 · {r['120 다른']:.2f}"), (그림(r["121"], (a2 + 90) % 360, e2), f"121 · {r['121 다른']:.2f}")]
        for t, (im, lab) in enumerate(칸):
            x = ax[i, t]; x.imshow(im); x.axis("off"); 좋 = t in (2, 5) and r["121 " + ("입력" if t == 2 else "다른")] > r["120 " + ("입력" if t == 2 else "다른")] + .005
            x.set_title(lab, fontsize=9, color="#28a050" if 좋 else "#d8262b" if t in (2, 5) else "#333")
    fig.suptitle(제목, fontsize=12); plt.tight_layout(rect=(0, 0, 1, 1 - .9 / len(rs) / 2.3)); plt.savefig(T.D + 파일, dpi=72); plt.close(fig)
rs = [r for r in 결["부품"] if r["무리"] in ("G1", "시험")]; 차 = lambda r: r["121 다른"] - r["120 다른"]; rs.sort(key=차)
시트(rs[::-1][:6] + rs[:3], f"121 다듬기 — 위 6 줄: 가장 나아진 것 · 아래 3 줄: 나빠진 것 (G1 · 생성 시험)\n다른 시점 IoU 중앙 G1 {요['G1 120 다른']:.3f} → {요['G1 121 다른']:.3f} · 생성 시험 {요['시험 120 다른']:.3f} → {요['시험 121 다른']:.3f} (평균 치수에서 시작 ③ {요['시험 ③ 다른']:.3f})", "비교.png")
g2 = sorted([r for r in 결["부품"] if r["무리"] == "G2"], key=차); 시트(g2[::-1][:4] + g2[:3], f"G2 실제 CAD — 다듬기 입력 시점 {요['G2 120 입력']:.2f} → {요['G2 121 입력']:.2f} · 다른 시점 {요['G2 120 다른']:.2f} → {요['G2 121 다른']:.2f} (위 4 나아짐 · 아래 3 나빠짐)", "비교_G2.png")
print("저장")
