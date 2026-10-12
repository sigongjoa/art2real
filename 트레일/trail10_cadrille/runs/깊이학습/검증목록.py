# -*- coding: utf-8 -*-
"""검증 세트 — 학습 모델 중 20 개를 통째로 떼어 냄(고정 씨앗) · 모델마다 부품 2 개 · 하드서페이스는 규칙(평면 면 넓이 비율 ≥ 0.5)으로만 고름 · 사람 눈으로 안 고름 · 10-11
python runs/깊이학습/검증목록.py            →  검증목록.json · 검증.npz
python runs/깊이학습/검증목록.py 2          →  검증목록2.json · 검증2.npz (10-12 재심: 씨앗 20261012 · 1 차 20 모델은 뺌 — 이미 본 개발 세트)"""
import os, sys, json, glob, random, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); sys.path.insert(0, H)
from 준비 import RR, 일
목록 = json.load(open(os.path.join(R, "실물학습", "목록.json"), encoding="utf-8")); 키 = sorted(목록)
def 평면비(p):
    import trimesh
    from s0 import unit
    if os.path.getsize(RR + p) > 8e6: return 0
    m = unit(trimesh.load(RR + p, force="mesh"))
    if len(m.faces) < 12 or min(m.extents) < 0.01 or len(m.faces) > 200000: return 0
    return float(sum(m.area_faces[f].sum() for f in m.facets) / m.area)
if __name__ == "__main__":
    판 = sys.argv[1] if len(sys.argv) > 1 else ""; 씨 = 20261012 if 판 else 20261011
    본 = set(json.load(open(os.path.join(H, "검증목록.json"), encoding="utf-8"))["모델"]) if 판 else set()
    모델 = sorted({p.split("/")[0] for p in 목록.values()} - 본); rng = random.Random(씨); rng.shuffle(모델)
    고른모델, 부품 = [], []
    for mo in 모델:
        if len(고른모델) == 20: break
        후보 = sorted(os.path.relpath(q, RR).replace("\\", "/") for q in glob.glob(RR + mo + "/**/*.stl", recursive=True) + glob.glob(RR + mo + "/**/*.STL", recursive=True)); rng.shuffle(후보); 됨 = []
        for p in 후보:
            try: ok = 평면비(p) >= 0.5
            except Exception: ok = False
            if ok: 됨.append(p)
            if len(됨) == 2: break
        if 됨: 고른모델.append(mo); 부품 += 됨; print(mo, len(됨), flush=True)
    빼기 = [j for j, k in enumerate(키) if 목록[k].split("/")[0] in set(고른모델)]   # 학습.npy 번호(키 정렬 순 · 2883 = 2883 확인함)
    X = [일(p) for p in 부품]; ok = [j for j, x in enumerate(X) if x is not None]
    json.dump({"씨앗": 씨, "규칙": "평면 면 넓이 ≥ 0.5 · ≤ 8 MB · 면 12~20만", "모델": 고른모델, "부품": [부품[j] for j in ok], "학습빼기": 빼기},
              open(os.path.join(H, "검증목록%s.json" % 판), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    np.savez(os.path.join(H, "검증%s.npz" % 판), X=np.stack([X[j] for j in ok]), 부품=np.array([부품[j] for j in ok]))
    print("ok 모델", len(고른모델), "부품", len(ok), "학습에서 빼는 것", len(빼기))
