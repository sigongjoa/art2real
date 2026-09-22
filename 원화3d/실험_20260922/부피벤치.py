# -*- coding: utf-8 -*-
"""**부피 벤치** — 나누기와 떼어서 부피 복원만 잰다 (2026-09-22).

    python 부피벤치.py      얼린 10 케이스 -> out/기록/부피벤치_<때>.json

외부 평가 3 회 + 천장 검산: 표면 자는 부피를 못 본다(상자로도 짝 162). 그래서 부피를 따로 잰다.
정답 부피는 `정답.grid(봉합=1)` — k=0 은 knight_Matt 에서 새서 껍데기만 남았다(채움/껍질 1.02 -> 4.41).

    판 둘   타원   `hull.field_default` (제품 기본 · 연속 장 타원)
            hull   `hull.field_hull` (이진 visual hull) — 대조군. 상한이라 재현율 ≈ 1 · 정밀도가 낮아야 한다
    자      우리 격자 위 IoU · 정밀도(우리 중 정답 안) · 재현율(정답 중 우리 안) · 부피 비(우리/정답)

돌리기 전 예상 (틀리면 자나 정답이 이상한 것):  hull 재현율 중앙 ≥ 0.9  ·  타원 정밀도 > hull 정밀도
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260922")
import hull as H
import 정답 as JD
import 부품분할 as BB
import 도면벤치_천장 as DC
import 깊이추정 as GC

OUT = H.OUT


def 재기(O, T):
    교 = (O & T).sum()
    return {"IoU": float(교 / max((O | T).sum(), 1)), "정밀도": float(교 / max(O.sum(), 1)),
            "재현율": float(교 / max(T.sum(), 1)), "부피 비": float(O.sum() / max(T.sum(), 1))}


def 한케이스(c):
    raw, masks, bs, p = BB.판(c)
    tm = trimesh.load(os.path.join(OUT, "시트", c, "truth.glb"), force="mesh")
    A, o = JD.grid(tm, 봉합=1)
    r = {}
    for k, f in (("타원", H.field_default), ("hull", H.field_hull)):
        g, ax = f(masks, back_sign=bs, n=BB.N)
        ux, uy, z = [np.asarray(a) for a in ax]
        T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
        r[k] = 재기(g > 0, T)
    return r


def main():
    기록 = {}
    for c in GC.케이스들:
        t0 = time.time()
        기록[c] = r = 한케이스(c)
        print("  %-38s " % c + " | ".join("%s IoU %.2f 정밀 %.2f 재현 %.2f 비 %.2f" % (k, v["IoU"], v["정밀도"], v["재현율"], v["부피 비"])
                                          for k, v in r.items()) + "  %.0f초" % (time.time() - t0), flush=True)
    요약 = {k: {m: float(np.median([r[k][m] for r in 기록.values()])) for m in ("IoU", "정밀도", "재현율", "부피 비")}
          for k in ("타원", "hull")}
    요약["예상 맞음"] = {"hull 재현율 ≥ 0.9": 요약["hull"]["재현율"] >= 0.9,
                     "타원 정밀도 > hull": 요약["타원"]["정밀도"] > 요약["hull"]["정밀도"]}
    print("\n" + json.dumps(요약, ensure_ascii=False, indent=1))
    p = os.path.join(OUT, "기록", "부피벤치_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(p)


if __name__ == "__main__":
    main()
