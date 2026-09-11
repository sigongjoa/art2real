# -*- coding: utf-8 -*-
"""벤치2격자.jsonl -> 판정. **두 격자 모두에서** 타원0.20 이 균일을 평균으로 이기고 과반을
이겨야 통과 (돌리기 전에 정한 기준)."""
import json
import sys

import numpy as np

rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
n = len(rows)
KEYS = ["파이프", "타원0.20", "타원0.35", "타원0.50", "오라클0.20", "오라클0.35", "오라클0.50"]
print("  %d 장\n" % n)
print("  %-11s %s" % ("균일 대비", "   ".join("격자%s 평균 (승)" % g for g in ("128", "192"))))
verdict = {}
for k in KEYS:
    cells = []
    for g in ("128", "192"):
        d = np.array([r[g][k] - r[g]["균일"] for r in rows])
        cells.append("%+.4f (%2d/%d)" % (d.mean(), (d > 0).sum(), n))
        verdict.setdefault(k, []).append(bool(d.mean() > 0 and (d > 0).sum() > n / 2))
    print("  %-11s %s" % (k, "      ".join(cells)))
cp, ce = (np.array([r["상관_" + k] for r in rows]) for k in ("파이프", "타원"))
print("\n  깊이맵 상관 (오라클과 · 중앙)  파이프 %.3f · 타원 %.3f · 타원이 높은 장 %d/%d"
      % (np.nanmedian(cp), np.nanmedian(ce), int(np.nansum(ce > cp)), n))
for g in ("128", "192"):
    d = np.array([r[g]["타원0.20"] - r[g]["파이프"] for r in rows])
    print("  격자%s 타원0.20 - 파이프  %+.4f (%d/%d)" % (g, d.mean(), (d > 0).sum(), n))
print("\n  판정 (두 격자 모두 평균>0 이고 과반 승):")
for k in KEYS:
    print("    %-11s %s" % (k, "통과" if all(verdict[k]) else "불통과  %s" % verdict[k]))
w = sorted(rows, key=lambda r: r["128"]["타원0.20"] - r["128"]["균일"])
print("\n  타원0.20 - 균일 (격자128) 가장 나쁜 셋 · 좋은 셋")
for r in w[:3] + w[-3:]:
    print("    %-34s %+.4f  (192 %+.4f)" % (r["case"][:34], r["128"]["타원0.20"] - r["128"]["균일"],
                                           r["192"]["타원0.20"] - r["192"]["균일"]))
print("  최대 메모리 %.2f GB · 합계 %.0f 분" % (max(r["최대GB"] for r in rows), sum(r["초"] for r in rows) / 60))
