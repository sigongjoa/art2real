# -*- coding: utf-8 -*-
"""기능0 7 판 — #5 공 발목(몸통 교차 + 목 원기둥 + 공) · #2 교차만(구 빼기 엉뚱) · 10-11"""
import os, sys, json
from 도구 import *
from 윤곽 import 메시로
from 모양자 import 재기
from s0 import unit
def 교차(i): return 돌출(i, 0).intersect(돌출(i, 1)).intersect(돌출(i, 2))
def 짓5():   # 옆(X) 줄표: 공 Y 126~183 · Z 62~135 → 중심 (X 128 · Y 147 · Z 98.5) R 35 · 목 Z 77~120 (R 21.5) Y 101~126
    몸 = 교차(5).cut(상자(-10, 110, c(125.5), 110, -10, 110)).cut(상자(-10, 110, c(100.5), 110, c(54), c(154)))
    목 = 원기둥(1, (c(128), c(98.5)), 21.5 * 화, c(95), c(135)); 공 = 구((c(128), c(147), c(98.5)), 35 * 화)
    return 몸.union(목).union(공), ["교차(몸통)", "자르기(공 자리)", "원기둥 Y(목)", "구(공)"]
def 짓2(): return 교차(2), ["교차(세 덩이)"]
O = os.path.join(H, "결과6")
for i in (5, 2):
    s, 순서 = globals()["짓%d" % i]()
    gt = unit(trimesh.load(W.RR + str(부[i]), force="mesh")); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
    pm = 메시로(s); r = 재기(pm, gt); pm.export(os.path.join(O, "%02d.stl" % i)); cq.exporters.export(s, os.path.join(O, "%02d.step" % i))
    j = {"부품": str(부[i]), "순서": 순서, "edge_f1": r["edge_f1"], "iou": r["iou"]}; print(i, j, flush=True)
    json.dump(j, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
