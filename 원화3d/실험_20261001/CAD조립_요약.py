"""AutoMate assemblies.parquet 요약 (10-07) — 고유 부품 수 분포.

돌리기: trail11_zerotocad venv(pyarrow 있음). 결과는 CAD조립/automate/요약.json.
"""
import json
from collections import Counter
from pathlib import Path
import pyarrow.parquet as pq

D = Path(__file__).resolve().parents[1] / "out" / "레퍼런스" / "CAD조립" / "automate"
t = pq.read_table(D / "assemblies.parquet", columns=["assemblyId", "n_parts", "n_step", "n_occurrences", "is_subassembly"]).to_pylist()
BINS = [(0, 0), (1, 1), (2, 3), (4, 6), (7, 12), (13, 25), (26, 50), (51, 100), (101, 10**9)]


def hist(key):
    c = Counter(r[key] for r in t)
    return {f"{a}-{b}" if a != b else str(a): sum(v for k, v in c.items() if a <= k <= b) for a, b in BINS}


ok = [r for r in t if r["n_step"] >= 4]
s = {
    "조립": len(t), "하위조립으로도쓰임": sum(r["is_subassembly"] for r in t),
    "고유부품수_분포": hist("n_parts"), "STEP부품수_분포": hist("n_step"),
    "STEP부품4이상": len(ok), "STEP다있고4이상": sum(r["n_step"] == r["n_parts"] for r in ok),
    "부품수_중앙": sorted(r["n_parts"] for r in t)[len(t) // 2],
    "4이상_부품수_중앙": sorted(r["n_step"] for r in ok)[len(ok) // 2],
}
(D / "요약.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), "utf-8")
print(json.dumps(s, ensure_ascii=False, indent=1))
