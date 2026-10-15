# 판정기준54 판정 — 평가51나(평가머리=학습54나_) 결과에서 A · B · C · D · 얼린 B 112 목록(묶음54_B112.json) · 10-15
import json, numpy as np
O = "G:/art2real/out/설명/캐드부품/"; D = O + "학습54나_판0/"
a = np.load(D + "부피IoU.npy"); r = json.load(open(D + "결과.json", encoding="utf-8")); B = json.load(open("묶음54_B112.json", encoding="utf-8"))
판0 = np.load(O + "학습51나_판0전체/부피IoU.npy")[:, 0]; k = B["자리"]
결과 = {"712 CAD 평균": float(a[:, 0].mean()), "판0": float(판0.mean()), "B 112 평균": float(a[k, 0].mean()), "B 112 판0": float(판0[k].mean()), "망침": r["망침"], "CAD 유효": r["CAD 유효"], "크게망침": r["크게망침"], "168 개": r["칠 천장 < 0.5 인 168"], "조각내기": r["조각내기"]}
결과["판정54"] = {"A ≥ 0.706": 결과["712 CAD 평균"] >= .706, "B 112 + 0.05": 결과["B 112 평균"] >= 결과["B 112 판0"] + .05, "C 망침 ≤ 124": r["망침"] <= 124, "D 유효 ≥ 710": r["CAD 유효"] >= 710}
json.dump(결과, open(D + "결과54.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
