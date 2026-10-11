# -*- coding: utf-8 -*-
"""기능0 둥근 찾기 — 선 그림(메시 모서리선)으로 나뉜 면마다 깊이 점을 평면 · 구 · 원기둥(축 X/Y/Z)에 맞춰 보고,
둥근 쪽이 평면보다 확실히 잘 맞으면 「공 · 소켓 · 휜 판」 후보 · 여러 방향에서 같은 구/원기둥은 하나로 · 10-11
python runs/기능0/둥근찾기.py 번호…  →  둥근/NN.json"""
import os, sys, json, numpy as np, trimesh
from 도구 import *
sys.path.insert(0, os.path.join(R, "선고리"))
import importlib.util
_s = importlib.util.spec_from_file_location("선고리", os.path.join(R, "선고리", "선고리.py")); 선 = importlib.util.module_from_spec(_s); _s.loader.exec_module(선); 선.MINA = 6
n = 128
def 점들(D, k, m):   # 깊이 화소 → 3D 점(칸 단위 0..128)
    r, c = np.nonzero(m); ax = k // 2; o = [j for j in range(3) if j != ax]; P = np.zeros((len(r), 3))
    P[:, o[0]] = r + .5; P[:, o[1]] = c + .5; d = D[k][r, c]; P[:, ax] = (1 - d if k % 2 else d) * n; return P
def 평면(P):
    c = P.mean(0); _, s, vt = np.linalg.svd(P - c); return float(np.median(np.abs((P - c) @ vt[2])))
def 구(P):
    A = np.c_[2 * P, np.ones(len(P))]; x = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]; o = x[:3]; Rr = float(np.sqrt(max(x[3] + o @ o, 1e-9)))
    return o, Rr, float(np.median(np.abs(np.linalg.norm(P - o, axis=1) - Rr)))
def 원기둥(P, a):
    jj = [j for j in range(3) if j != a]; q = P[:, jj]; A = np.c_[2 * q, np.ones(len(q))]; x = np.linalg.lstsq(A, (q ** 2).sum(1), rcond=None)[0]; o = x[:2]; Rr = float(np.sqrt(max(x[2] + o @ o, 1e-9)))
    return o, Rr, float(np.median(np.abs(np.linalg.norm(q - o, axis=1) - Rr)))
def 찾기(i):
    from s0 import unit
    X = 입력(i); D = X[3]; mu = unit(trimesh.load(W.RR + str(부[i]), force="mesh")); out = []
    for k in range(6):
        L = 선.모서리선(mu, D[k], X[0][k], k); ax = k // 2
        for 종, m in 선.면나누기(X[0][k], L):
            안 = m > 0
            if 종 != "고리" or 안.sum() < 60: continue
            P = 점들(D, k, 안); e0 = 평면(P); 크기 = float(np.ptp(P, 0).max())
            cand = []
            o, Rr, e = 구(P)
            if Rr < 1.5 * 크기 + 4: cand.append(("구", {"중심": o.round(2).tolist(), "R": round(Rr, 2)}, e, o[ax]))
            for a in range(3):
                if a == ax: continue
                o2, R2, e2 = 원기둥(P, a)
                if R2 < 1.5 * 크기 + 4:
                    jj = [j for j in range(3) if j != a]; 깊 = o2[jj.index(ax)] if ax in jj else None
                    cand.append(("원기둥", {"축": a, "중심": o2.round(2).tolist(), "R": round(R2, 2)}, e2, 깊))
            if not cand: continue
            종류, p, e, 깊 = min(cand, key=lambda t: t[2])
            if e < .45 and e0 > 2.5 * e + .25:   # 둥근 쪽이 평면보다 확실히 잘 맞음
                면깊 = float(np.median(P[:, ax])); 오목 = (깊 < 면깊) if k % 2 == 0 else (깊 > 면깊)   # 중심이 보는 쪽 = 오목(소켓)
                out.append({"쪽": k, "종류": 종류, **p, "잔차": round(e, 3), "평면잔차": round(e0, 3), "넓이": int(안.sum()), "오목": bool(오목), "_m": 안})
    # 같은 구 · 원기둥 하나로 (중심 4 칸 · R 15 % 안)
    합 = []
    for f in sorted(out, key=lambda f: -f["넓이"]):
        for g in 합:
            if g["종류"] == f["종류"] and g.get("축") == f.get("축") and np.linalg.norm(np.array(g["중심"]) - np.array(f["중심"])) < 4 and abs(g["R"] - f["R"]) < .15 * g["R"]:
                g["쪽들"].append(f["쪽"]); g["넓이"] += f["넓이"]; break
        else: 합.append({**f, "쪽들": [f["쪽"]]})
    return 합, out
if __name__ == "__main__":
    O = os.path.join(H, "둥근"); os.makedirs(O, exist_ok=True)
    for i in [int(a) for a in sys.argv[1:]]:
        r, _ = 찾기(i); r = [{k: v for k, v in f.items() if k != "_m"} for f in r]; json.dump(r, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
        print(i, [(f["종류"], "오목" if f["오목"] else "볼록", f["R"], f["쪽들"], f["잔차"]) for f in r], flush=True)
