# -*- coding: utf-8 -*-
"""기능0 B 판 + 둥근 — 선 그림만: 교차 → 둥근 학생 칸 지도 덩이마다 새 학생 깊이로 구 · 원기둥 맞춤(공 붙임 · 소켓 뺌 · 원기둥 둥글게) → 큰 홈 → 선 고리 디테일 · 10-11
python runs/기능0/짓기B둥근.py 번호…  →  B_둥근/NN.*"""
import os, sys, json, numpy as np, cv2, torch
from scipy import ndimage
from 도구 import *
import 디테일 as DT, 둥근찾기 as G
sys.path.insert(0, os.path.join(R, "깊이학습"))
from 학습 import 망
from 학습둥근 import 둥근망
def 홈칼(i, k, c, 바닥):
    ax = k // 2; o = [j for j in range(3) if j != ax]
    cs, _ = cv2.findContours(c.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); p = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 1.5, True)[:, 0, :]
    a = (1 - 바닥) * 110 - 5 if k % 2 else 바닥 * 110 - 5; 끝 = 120.0 if k % 2 else -20.0; pts = []
    for cc, rr in p:
        q = [0.0, 0.0, 0.0]; q[o[0]] = c8(rr); q[o[1]] = c8(cc); q[ax] = a; pts.append(V(*q))
    d_ = [0, 0, 0]; d_[ax] = 끝 - a
    return 다각기둥(pts, d_)
O = os.path.join(H, "B_둥근"); os.makedirs(O, exist_ok=True)
mT = 망().cuda(); mT.load_state_dict(torch.load(os.path.join(R, "깊이학습", "모델T.pt"))); mT.eval()
mR = 둥근망().cuda(); mR.load_state_dict(torch.load(os.path.join(R, "깊이학습", "모델둥근.pt"))); mR.eval()
v2c = lambda v: np.asarray(v) / 128 * 110 - 5; 칸 = 110 / 128
def 기둥칼(k, m, a=-30.0, b=130.0):   # 칸 지도 덩이 윤곽을 그 방향 축 전체로 민 기둥
    ax = k // 2; o = [j for j in range(3) if j != ax]
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); p = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 1.0, True)[:, 0, :]; pts = []
    for cc, rr in p:
        q = [0.0, 0.0, 0.0]; q[o[0]] = c8(rr); q[o[1]] = c8(cc); q[ax] = a; pts.append(V(*q))
    d_ = [0, 0, 0]; d_[ax] = b - a
    return 다각기둥(pts, d_)
def 둥근들(X, Z):
    with torch.no_grad(): C = mR(torch.from_numpy(X[:3]).permute(1, 0, 2, 3).cuda()).argmax(1).cpu().numpy()
    out = []
    for k in range(6):
        for c in range(1, 5):
            lab, nl = ndimage.label(C[k] == c)
            for j in range(1, nl + 1):
                m = lab == j
                if m.sum() < 60: continue
                P = G.점들(Z, k, m)
                if c <= 2:
                    o, Rr, e = G.구(P)
                    if e < 1.0 and 3 < Rr < 64: out.append({"종": "공" if c == 1 else "소켓", "쪽": k, "중심": o, "R": Rr, "m": m, "넓이": int(m.sum())})
                else:
                    best = min(((a,) + G.원기둥(P, a) for a in range(3) if a != k // 2), key=lambda t: t[3])
                    a, o, Rr, e = best
                    if e < 1.0 and 3 < Rr < 200: out.append({"종": "볼록원기둥" if c == 3 else "오목원기둥", "쪽": k, "축": a, "중심": o, "R": Rr, "m": m, "넓이": int(m.sum())})
    합 = []   # 같은 공 · 소켓은 하나로
    for f in sorted(out, key=lambda f: -f["넓이"]):
        if f["종"] in ("공", "소켓") and any(g["종"] == f["종"] and np.linalg.norm(g["중심"] - f["중심"]) < 5 for g in 합): continue
        합.append(f)
    return 합
def 둥근얹기(s, fs):
    n0 = len(s.solids().vals()); v0 = s.val().Volume(); 됨 = []
    for f in fs:
        try:
            if f["종"] in ("공", "소켓"):
                구_ = 구(tuple(v2c(f["중심"])), f["R"] * 칸)
                if f["종"] == "공":
                    c_ = v2c(f["중심"]); r_ = f["R"] * 칸; 박 = 상자(*[t for a in range(3) for t in (c_[a] - r_, c_[a] + r_)]); t = s.cut(박.cut(구_))
                else: t = s.cut(구_)
            else:
                a = f["축"]; jj = [j for j in range(3) if j != a]; 중 = v2c(f["중심"]); 원 = 원기둥(a, tuple(중), f["R"] * 칸, -30, 130); 기 = 기둥칼(f["쪽"], f["m"])
                t = s.cut(기.cut(원)) if f["종"] == "볼록원기둥" else s.cut(기.intersect(원))
            if len(t.solids().vals()) > n0 or t.val().Volume() < .5 * v0: continue
            s = t; 됨.append(f)
        except Exception: pass
    return s, 됨
if __name__ == "__main__":
    from 윤곽 import 메시로
    from 모양자 import 재기
    from s0 import unit
    for i in [int(a) for a in sys.argv[1:]]:
        X = 입력(i); S = X[0] > .5; Dh = X[2]
        with torch.no_grad(): Z = mT(torch.from_numpy(X[:3]).permute(1, 0, 2, 3).cuda())[:, 0].cpu().numpy()
        s = 돌출(i, 0).intersect(돌출(i, 1)).intersect(돌출(i, 2)); n0 = len(s.solids().vals())
        s, 됨 = 둥근얹기(s, 둥근들(X, Z)); 순서 = ["교차"] + ["%s %d R%.0f" % (f["종"], f["쪽"], f["R"]) for f in 됨]
        for k in range(6):
            lab, nl = ndimage.label(S[k] & (Z[k] - Dh[k] > 3 / 128))
            for j in range(1, nl + 1):
                c = lab == j
                if c.sum() < 150: continue
                try:
                    t = s.cut(홈칼(i, k, c, float(np.median(Z[k][c]))))
                    if len(t.solids().vals()) > n0 or t.val().Volume() < .3 * s.val().Volume(): continue
                    s = t; 순서.append("홈 %d" % k)
                except Exception: pass
        s, 디 = DT.얹기(s, DT.고리찾기(i, s, Z)); 순서 += ["%s %d" % (f["종"], f["쪽"]) for f in 디]
        gt = unit(trimesh.load(W.RR + str(부[i]), force="mesh")); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
        pm = 메시로(s); e = 재기(pm, gt); pm.export(os.path.join(O, "%02d.stl" % i)); cq.exporters.export(s, os.path.join(O, "%02d.step" % i))
        json.dump({"부품": str(부[i]), "순서": 순서, "edge_f1": e["edge_f1"], "iou": e["iou"], "조각": len(s.solids().vals()) - n0}, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
        print(i, [x for x in 순서 if x.split()[0] in ("공", "소켓", "볼록원기둥", "오목원기둥")], flush=True)
