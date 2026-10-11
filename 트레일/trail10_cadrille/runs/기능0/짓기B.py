# -*- coding: utf-8 -*-
"""기능0 B 판 — 정답 깊이 대신 학생 깊이로 같은 짓기: 교차 → 큰 홈(학생 − 교차 > 3 칸 · 150 칸 이상 · 평평 바닥) → 선 고리 디테일 · 10-11
python runs/기능0/짓기B.py 모델T|모델 번호…  →  B_모델T/NN.*"""
import os, sys, json, numpy as np, cv2, torch
from scipy import ndimage
from 도구 import *
import 디테일 as DT
sys.path.insert(0, os.path.join(R, "깊이학습"))
from 학습 import 망
이름 = sys.argv[1]; ids = [int(a) for a in sys.argv[2:]]; O = os.path.join(H, "B_" + 이름); os.makedirs(O, exist_ok=True)
m = 망().cuda(); m.load_state_dict(torch.load(os.path.join(R, "깊이학습", 이름 + ".pt"))); m.eval()
def 홈칼(i, k, c, 바닥):
    ax = k // 2; o = [j for j in range(3) if j != ax]
    cs, _ = cv2.findContours(c.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); p = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 1.5, True)[:, 0, :]
    a = (1 - 바닥) * 110 - 5 if k % 2 else 바닥 * 110 - 5; 끝 = 120.0 if k % 2 else -20.0; pts = []
    for cc, rr in p:
        q = [0.0, 0.0, 0.0]; q[o[0]] = c8(rr); q[o[1]] = c8(cc); q[ax] = a; pts.append(V(*q))
    d_ = [0, 0, 0]; d_[ax] = 끝 - a
    return cq.Workplane().add(cq.Solid.extrudeLinear(cq.Face.makeFromWires(cq.Wire.makePolygon(pts, close=True)), V(*d_)))
from 윤곽 import 메시로
from 모양자 import 재기
from s0 import unit
for i in ids:
    X = 입력(i); S = X[0] > .5; Dh = X[2]
    with torch.no_grad(): Z = m(torch.from_numpy(X[:3]).permute(1, 0, 2, 3).cuda())[:, 0].cpu().numpy()
    s = 돌출(i, 0).intersect(돌출(i, 1)).intersect(돌출(i, 2)); n0 = len(s.solids().vals()); 순서 = ["교차"]
    for k in range(6):
        lab, nl = ndimage.label(S[k] & (Z[k] - Dh[k] > 3 / 128))
        for j in range(1, nl + 1):
            c = lab == j
            if c.sum() < 150: continue
            try:
                t = s.cut(홈칼(i, k, c, float(np.median(Z[k][c]))))
                if len(t.solids().vals()) > n0 or t.val().Volume() < .3 * s.val().Volume(): continue
                s = t; 순서.append("홈 %d · %d칸" % (k, c.sum()))
            except Exception: pass
    s, 됨 = DT.얹기(s, DT.고리찾기(i, s, Z)); 순서 += ["%s %d" % (f["종"], f["쪽"]) for f in 됨]
    gt = unit(trimesh.load(W.RR + str(부[i]), force="mesh")); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
    pm = 메시로(s); e = 재기(pm, gt); pm.export(os.path.join(O, "%02d.stl" % i)); cq.exporters.export(s, os.path.join(O, "%02d.step" % i))
    json.dump({"부품": str(부[i]), "순서": 순서, "edge_f1": e["edge_f1"], "iou": e["iou"], "조각": len(s.solids().vals()) - n0}, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
    print(i, len(순서), flush=True)
