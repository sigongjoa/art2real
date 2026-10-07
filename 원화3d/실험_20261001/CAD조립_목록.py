"""CAD조립/parts/ 를 훑어 목록.json 을 쓴다 (10-07).

폴더 이름 = <source>_<assemblyid> · 항목 {"source","assembly","parts","folder"} · 끝에 합계.
"""
import json
from collections import Counter
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "out" / "레퍼런스" / "CAD조립" / "parts"
rows = []
for d in sorted(x for x in P.iterdir() if x.is_dir()):
    n = len(list(d.glob("*.stl")))
    if n:
        src, aid = d.name.split("_", 1)
        rows.append({"source": src, "assembly": aid, "parts": n, "folder": d.name})
(P / "목록.json").write_text(json.dumps(rows, ensure_ascii=False, indent=0), "utf-8")
for s in sorted({r["source"] for r in rows}):
    rs = [r for r in rows if r["source"] == s]
    print(f"{s}: 조립 {len(rs)} · 부품 {sum(r['parts'] for r in rs)} · 부품 수 분포 {dict(sorted(Counter(r['parts'] for r in rs).items()))}")
print(f"합계: 조립 {len(rows)} · 부품 {sum(r['parts'] for r in rows)}")
