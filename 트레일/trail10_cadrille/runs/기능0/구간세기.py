# 판정기준25 싼 확인: 검증2 40 에서 H 가 통째로 안 건 부품 중 구간이 걸리는 부품 · 10-13
import os, sys, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from 도구 import 입력, 실루엣
import 회전 as RV, 회전2 as R2
out = {}
for i in range(40):
    if RV.찾기(실루엣(i))["걸림"]: out[i] = "옛 회전(그대로)"; continue
    f = R2.찾기(R2.학생부피(입력(i)))
    if f is None: out[i] = "없음"; continue
    if f["걸림"]: out[i] = "H 통째(그대로)"; continue
    out[i] = f["구간"]
    print(i, f["대칭"], f["칸"], f["구간"], flush=True)
json.dump({str(k): v for k, v in out.items()}, open(os.path.join(H, "판정25_구간.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("구간 걸림", sum(1 for v in out.values() if isinstance(v, list) and v))
