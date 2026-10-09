# -*- coding: utf-8 -*-
"""실물 학습 데이터 — 시험 36 부품이 나온 모델(23 개)은 통째로 빼고 · 모델마다 최대 8 개 · 렌더(모델 입력) + 6 방향 실루엣·깊이(정답 그림)
python runs/실물학습/준비.py [일꾼=6]  →  그림/NNNN.png · 보기/NNNN.npz · 목록.json"""
import os, sys, json, glob, random
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(R, "조각0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub"), T0]
RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"

def 일(a):
    i, p = a
    import numpy as np, trimesh
    from s0 import unit, item_img
    from 실물보기 import 실물보기
    try:
        if os.path.getsize(RR + p) > 8e6: return None
        m = unit(trimesh.load(RR + p, force="mesh"))
        if len(m.faces) < 12 or min(m.extents) < 0.01: return None   # 납작한 0 두께 · 부스러기
        _, g = item_img(m); g.save(os.path.join(H, "그림", "%04d.png" % i))
        S, D = 실물보기(m, 48); np.savez_compressed(os.path.join(H, "보기", "%04d.npz" % i), S=S.astype(np.float16), D=D.astype(np.float16))
        return i, p
    except Exception: return None

if __name__ == "__main__":
    from multiprocessing import Pool
    for d in ("그림", "보기"): os.makedirs(os.path.join(H, d), exist_ok=True)
    시험 = {r["부품"].split("/")[0] for k in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % k), encoding="utf-8"))}
    모델 = {}
    for q in glob.glob(RR + "*/**/*.stl", recursive=True) + glob.glob(RR + "*/**/*.STL", recursive=True):
        q = os.path.relpath(q, RR).replace("\\", "/"); mo = q.split("/")[0]
        if mo not in 시험: 모델.setdefault(mo, set()).add(q)
    rng = random.Random(0); 고름 = []
    for mo in sorted(모델): 고름 += rng.sample(sorted(모델[mo]), min(8, len(모델[mo])))
    print("모델", len(모델), "고른 부품", len(고름), flush=True)
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 6) as pool: out = [x for x in pool.imap(일, list(enumerate(고름)), chunksize=8) if x]
    json.dump({"%04d" % i: p for i, p in out}, open(os.path.join(H, "목록.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0); print("ok", len(out))
