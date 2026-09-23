# -*- coding: utf-8 -*-
"""**최소 표면** — 실루엣을 지키면서 표면적을 줄여 유령을 깎는다 (2026-09-23).

    python 최소표면.py            얼린 10 케이스 -> out/기록/최소표면_<때>.json

조사(`claudedocs/research_의료영상_2D3D_20260923.md`): 적은 각도 CT 는 TV(총변동) 최소화로 유령을 지운다.
이진 부피에서 TV = **표면적**이다. 실루엣만으로는 유령이 원리적으로 안 지워지니 **규칙(정칙화)** 으로 고른다.

    판 A · 되돌림(POCS)   ① 지시 함수를 가우시안으로 뭉개고 문턱 -> 표면적이 준다
                          ② 세 실루엣을 다시 강제 — 어떤 광선의 화소가 실루엣에 있는데 비었으면 되돌린다
                          (적은 각도 CT 의 「TV 한 걸음 + 자료 일관성 한 걸음」과 같은 꼴)
    판 B · 최소 절단      그래프 컷(PyMaxflow) — 겉면 벌점(표면적) + 부피 벌점 λ,
                          **광선마다 가장 안쪽 복셀**(hull 거리장 최대)은 원천에 묶어 실루엣이 안 비게 한다

판정(외부 평가 4 회에서 미리 적음 · 중앙값): **부피 IoU ≥ 0.70 · 정밀도 ≥ 0.75 · 재현율 ≥ 0.85**
손잡이(σ · 되돌림 횟수 · λ)는 **홀수 5 장에서 고르고 짝수 5 장에서 잰다**(홀드아웃).
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922"]
import hull as H
import 정답 as JD
import 부품분할 as BB
import 도면벤치_천장 as DC
import 부피벤치 as PB
import 깊이추정 as GC

축들 = (0, 1)          # 앞 · 뒤는 y(1) 로, 옆은 x(0) 으로 누른다 — 위(z)는 판이 없다


def 실루엣(O):
    """세 판이 주는 것: y 로 누른 그림(앞 · 뒤)과 x 로 누른 그림(옆)."""
    return {a: O.any(axis=a) for a in 축들}


def 표면적(O):
    s = 0
    for a in range(3):
        s += int((np.diff(O.astype(np.int8), axis=a) != 0).sum())
    return s


def 되돌림(O, σ=1.2, 회=6):
    """TV 한 걸음(뭉개기+문턱) + 자료 일관성 한 걸음(실루엣 되돌리기)을 번갈아."""
    목표 = 실루엣(O)
    X = O.copy()
    for _ in range(회):
        f = ndimage.gaussian_filter(X.astype(np.float32), σ)
        새 = (f > 0.5) & O                                  # hull 밖으로는 못 나간다 (hull 은 상한)
        for a in 축들:                                      # 실루엣이 비면 그 광선에서 가장 두꺼웠던 자리를 되돌린다
            빈 = 목표[a] & ~새.any(axis=a)
            if 빈.any():
                되 = np.zeros_like(새)
                깊 = np.where(O, ndimage.distance_transform_edt(O), -1)
                idx = np.expand_dims(np.argmax(np.where(np.expand_dims(빈, a), 깊, -1), axis=a), a)
                np.put_along_axis(되, idx, True, a)
                새 |= 되 & O & np.expand_dims(빈, a)
        X = 새
    return X


def 최소절단(O, λ=1.0):
    """E = 표면적 − λ·부피 를 최소로 하는 절단. λ 가 크면 많이 남기고, 작으면 뼈대만 남는다.
    광선마다 가장 안쪽 복셀은 원천에 묶어 실루엣이 안 비게 한다."""
    import maxflow
    깊 = ndimage.distance_transform_edt(O).astype(np.float32)
    묶 = np.zeros_like(O)
    for a in 축들:
        있 = O.any(axis=a)
        idx = np.expand_dims(np.argmax(np.where(O, 깊, -1), axis=a), a)
        t = np.zeros_like(O)
        np.put_along_axis(t, idx, True, a)
        묶 |= t & O & np.expand_dims(있, a)
    g = maxflow.Graph[float]()
    nid = g.add_grid_nodes(O.shape)
    g.add_grid_edges(nid, 1.0)                              # 이웃이 다르면 1 (표면적)
    원천 = np.where(묶, 1e6, np.where(O, λ, 0.0))            # 남기면 λ 만큼 이득 · 묶인 것은 반드시 남는다
    싱크 = np.where(O, 0.0, 1e6)                             # hull 밖은 반드시 빈다
    g.add_grid_tedges(nid, 원천, 싱크)
    g.maxflow()
    return (~g.get_grid_segments(nid)) & O                    # PyMaxflow: True 는 싱크 쪽 — 남는 것은 그 반대


def 한케이스(c, 손잡이):
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    O = g > 0
    tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
    A, o = JD.grid(tm, 봉합=1)
    T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
    r = {"지금": dict(PB.재기(O, T), 표면적=표면적(O))}
    for 이름, X in 손잡이(O):
        r[이름] = dict(PB.재기(X, T), 표면적=표면적(X))
        for a in 축들:                                       # 실루엣을 깨지 않았나 (제약 검사)
            r[이름]["실루엣 깨짐(%d)" % a] = int((O.any(axis=a) & ~X.any(axis=a)).sum())
    return r


def 손잡이들(O):
    for σ, 회 in ((1.0, 4), (1.6, 6), (2.4, 8)):
        yield "되돌림 σ%.1f x%d" % (σ, 회), 되돌림(O, σ, 회)
    for λ in (0.25, 0.35, 0.5):
        yield "최소절단 λ%.1f" % λ, 최소절단(O, λ)


def main():
    기록 = {}
    for c in GC.케이스들:
        t0 = time.time()
        기록[c] = r = 한케이스(c, 손잡이들)
        print("  %-30s " % c[:30] + " | ".join("%s %.2f" % (k.replace("되돌림 ", "되").replace("최소절단 ", "컷"), v["IoU"]) for k, v in r.items()) + "  %.0f초" % (time.time() - t0), flush=True)
    판들 = list(기록[GC.케이스들[0]].keys())
    중앙 = lambda 판, m, 집합: float(np.median([기록[c][판][m] for c in 집합]))
    홀, 짝 = GC.케이스들[0::2], GC.케이스들[1::2]
    요약 = {"전체": {p: {m: round(중앙(p, m, GC.케이스들), 3) for m in ("IoU", "정밀도", "재현율", "부피 비")} for p in 판들}}
    고른 = max([p for p in 판들 if p != "지금"], key=lambda p: 중앙(p, "IoU", 홀))
    요약["고름(홀수 5 장)"] = 고른
    h = {m: 중앙(고른, m, 짝) for m in ("IoU", "정밀도", "재현율")}
    요약["홀드아웃(짝수 5 장)"] = {k: round(v, 3) for k, v in h.items()}
    요약["판정"] = {"IoU ≥ 0.70": h["IoU"] >= 0.70, "정밀도 ≥ 0.75": h["정밀도"] >= 0.75, "재현율 ≥ 0.85": h["재현율"] >= 0.85}
    요약["실루엣 깨짐 합"] = {p: int(sum(기록[c][p].get("실루엣 깨짐(0)", 0) + 기록[c][p].get("실루엣 깨짐(1)", 0) for c in GC.케이스들)) for p in 판들 if p != "지금"}
    print("\n" + json.dumps(요약, ensure_ascii=False, indent=1))
    pth = os.path.join(H.OUT, "기록", "최소표면_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(pth, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(pth)


if __name__ == "__main__":
    main()
