# -*- coding: utf-8 -*-
"""기능0 3 판 — #23 #17 #29 #33 #34 #11 손 짓기 · 숫자는 256 실루엣 줄표 · 128 깊이에서 · 10-11
교차로 충분한 부품(#17 #29 #33 #11)은 세 윤곽 교차가 곧 기능 순서 — 그 표식도 데이터"""
import os, sys, json
from 도구 import *

def 교차(i): return 돌출(i, 0).intersect(돌출(i, 1)).intersect(돌출(i, 2))

def 짓23():   # 방패 · 휜 판(세 윤곽 교차 · X ≥ 136) + 뒤 혹(Y 27~51 · 구멍은 Y 윤곽에 있음) + 걸이(기둥 + 팔)
    판 = 교차(23).intersect(상자(c(135.5), 110, -10, 110, -10, 110))
    혹 = 돌출(23, 1).intersect(상자(c(125.5), c(152), c(26.5), c(51.5), c(93.5), c(161.5)))
    걸이 = 돌출(23, 1).intersect(돌출(23, 2)).intersect(상자(c(88), c(140), c(77), c(170), c(56), c(88)))
    return 판.union(혹).union(걸이), ["교차(휜 판)", "돌출 Y(뒤 혹 · 구멍)", "돌출 Y ∩ Z(걸이)"]

def 짓17(): return 교차(17), ["교차(ㄴ 판 = 벽 + 바닥)"]
def 짓29(): return 교차(29), ["교차(구멍 둘 · D 단면)"]   # 안 함: 앞 오목 접시 · 뒤 둥근 막대(깊이로만 보임)
def 짓33(): return 교차(33), ["교차(Z 관통 원통 구멍)"]   # 안 함: 옆 육각 · 긴 홈
def 짓11(): return 교차(11), ["교차(비스듬 판)"]

def 짓34():   # 허리 틀 · 포크(Z 윤곽 · Y ≤ 145 · Z 89~159) + 목 원기둥(Y) + 공
    포크 = 돌출(34, 2).intersect(상자(-10, 110, -10, c(145), c(88.5), c(159.5)))
    목 = 원기둥(1, (c(127.5), c(125.5)), 18 * 화, c(140), c(180))
    공 = 구((c(127.5), c(207.5), c(127.5)), 37 * 화)
    return 포크.union(목).union(공), ["돌출 Z(포크 · 소켓)", "원기둥 Y(목)", "구(공)"]

if __name__ == "__main__":
    from 윤곽 import 메시로
    from 모양자 import 재기
    from s0 import unit
    O = os.path.join(H, "결과"); os.makedirs(O, exist_ok=True)
    for i in [int(a) for a in sys.argv[1:]] or (23, 17, 29, 33, 34, 11):
        s, 순서 = globals()["짓%d" % i]()
        gt = unit(trimesh.load(W.RR + str(부[i]), force="mesh")); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
        pm = 메시로(s); r = 재기(pm, gt); pm.export(os.path.join(O, "%02d.stl" % i)); cq.exporters.export(s, os.path.join(O, "%02d.step" % i))
        j = {"부품": str(부[i]), "순서": 순서, "edge_f1": r["edge_f1"], "iou": r["iou"], "조각": len(s.solids().vals()) - 1}; print(i, j, flush=True)
        json.dump(j, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
