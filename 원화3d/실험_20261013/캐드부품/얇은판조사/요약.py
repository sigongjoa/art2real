import json, numpy as np
R = [r for r in json.load(open("결과.json", encoding="utf-8"))]; 실 = [r for r in R if "실패" in r]; R = [r for r in R if "실패" not in r]
print("실패", len(실), [r.get("실패") for r in 실][:5])
M = ["M0_48", "M1_부분", "M2_F", "M2_CD칸", "M3_96", "M3_192"]
for g in ("89", "100"):
    S = [r for r in R if r["무리"] == g]; print(f"\n== {g} 개 무리 (n={len(S)}) · 천장53 평균 {np.mean([r['천장53'] for r in S]):.3f} · 틀칸 다시 잰 천장 {np.mean([r['천장틀'] for r in S]):.3f} · 초 {np.mean([r['초'] for r in S]):.1f}")
    print("후보".ljust(10), *[c.rjust(8) for c in ("자기", "밀림x", "밀림z", "깎기")])
    for m in M: print(m.ljust(10), *[f"{np.nanmean([r[c][m] for r in S]):8.3f}" for c in ("자기", "밀림x", "밀림z", "깎기")])
    if g == "89":
        e = [r for r in S if r["칸48수"] == 0]; print("정답 48³ 칸 0 개:", len(e))
        c192 = np.array([r["깎기"]["M3_192"] for r in S]); F = np.array([r["깎기"]["M2_F"] for r in S]); 부 = np.array([r["깎기"]["M1_부분"] for r in S])
        print("깎기 192³ ≥ .5:", (c192 >= .5).sum(), " F ≥ .8:", (F >= .8).sum(), " 부분 ≥ .5:", (부 >= .5).sum())
        mz = np.array([r["밀림z"]["M3_192"] for r in S]); print("밀림z 192³ < .1 (판 두께 < 한 칸):", (mz < .1).sum())
        H = np.array([r["H"] for r in S]); print("H < 2 칸(0.046):", (H < .046).sum())
