# -*- coding: utf-8 -*-
"""기능0 6 판 — 남은 부품 + 약했던 넷: 교차(직선 + 원호) → 자동이 짚은 홈 중 큰 것만 CAD 로(평평한 바닥 다각형) · 부스러기 생기는 홈은 버림 · 10-11"""
import os, sys, json
from 도구 import *
from 윤곽 import 메시로
from 모양자 import 재기
from s0 import unit
O = os.path.join(H, "결과6"); os.makedirs(O, exist_ok=True)
for i in [int(a) for a in sys.argv[1:]]:
    s = 돌출(i, 0).intersect(돌출(i, 1)).intersect(돌출(i, 2)); n0 = len(s.solids().vals()); 순서 = ["교차"]
    for 이름, 칼 in 홈들(i, int(os.environ.get("MIN", 150))):
        try:
            t = s.cut(칼)
            if len(t.solids().vals()) > n0 or t.val().Volume() < .3 * s.val().Volume(): print(i, "버림", 이름); continue
            s = t; 순서.append(이름)
        except Exception as e: print(i, "실패", 이름, str(e)[:40])
    gt = unit(trimesh.load(W.RR + str(부[i]), force="mesh")); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
    pm = 메시로(s); r = 재기(pm, gt); pm.export(os.path.join(O, "%02d.stl" % i)); cq.exporters.export(s, os.path.join(O, "%02d.step" % i))
    j = {"부품": str(부[i]), "순서": 순서, "edge_f1": r["edge_f1"], "iou": r["iou"], "조각": len(s.solids().vals()) - n0}; print(i, j["순서"], flush=True)
    json.dump(j, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
