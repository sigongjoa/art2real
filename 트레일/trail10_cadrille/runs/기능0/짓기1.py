# -*- coding: utf-8 -*-
"""기능0 1 판 — 쉬운 6 부품 손 짓기 (#24 #8 #32 #22 #13 #10) · 숫자는 256 실루엣 화소 줄표에서 읽음 · 10-11
python runs/기능0/짓기1.py [번호…]  →  결과/NN.step · NN.stl · NN.json (+ 순서)"""
import os, sys, json
from 도구 import *

def 짓24():   # 휜 띠 · 세 방향 윤곽 교차가 곧 기능 (휜 단면을 Y 로 밀고 옆 · 위 윤곽으로 다듬기)
    return 돌출(24, 1).intersect(돌출(24, 0)).intersect(돌출(24, 2)), ["돌출 Y(단면)", "교차 X", "교차 Z"]

def 짓8():   # 팔 갑주 · 옆(X) 집 모양 × 앞(Y) 둥근 고리 = 관 · 위(Z)에서 Y 106 화소 뒤로 뚫림 = 그 세 윤곽 그대로
    return 돌출(8, 0).intersect(돌출(8, 1)).intersect(돌출(8, 2)), ["돌출 X(집 모양)", "교차 Y(고리 = 관)", "교차 Z(창)"]

def 짓32():   # 손잡이 · ㄷ 단면(Y 에서 봄)을 Y 두께 113~142 로 밀기 → 팔 끝 둥글게 → 핀 구멍(X 방향 · Z 187.5 · 반지름 3 화소)
    s = 돌출(32, 1).intersect(상자(-10, 110, c(112.5), c(142.5), -10, 110))
    s = s.edges("|X").edges(">Z").fillet(13.5 * 화)
    s = s.cut(원기둥(0, (c(127.5), c(187.5)), 3 * 화, -10, 110))
    return s, ["돌출 Y(ㄷ 단면)", "필렛 팔 끝", "구멍 X"]

def 짓22():   # 팔꿈치 관절 · X 자 윤곽(Z 에서 봄)을 Z 99~156 으로 밀기 → 앞뒤 면 모따기 4 화소
    s = 돌출(22, 2).intersect(상자(-10, 110, -10, 110, c(98.5), c(156.5)))
    try: s = s.faces(">Z or <Z").edges().chamfer(1.6)
    except Exception as e: print("모따기 실패", str(e)[:50])
    return s, ["돌출 Z(X 자)", "모따기 앞뒤 면"]

def 짓13():   # 어깨 날개 틀 · 공 + 몸통(위 윤곽 밀기) + 축 + 원판
    공 = 구((c(54), c(183), c(127.5)), 44 * 화)
    몸 = 돌출(13, 2).intersect(상자(c(100), c(243.5), c(102.5), c(219), c(83.5), c(163.5)))
    축 = 원기둥(1, (c(171), c(123.5)), 22 * 화, c(59), c(104))
    판 = 원기둥(1, (c(171), c(127.5)), 44 * 화, c(23.5), c(60.5))
    return 몸.union(공).union(축).union(판), ["구(공)", "돌출 Z(몸통 · 소켓)", "원기둥 Y(축)", "원기둥 Y(원판)"]

def 짓10():   # 엉덩이 관절 · Y 방향 원기둥(Z 85~170 납작) + 홈 셋 + 끝 슬릿 · 포크(위 윤곽 밀기)
    봉 = 원기둥(1, (c(128), c(127.5)), 48 * 화, c(11.5), c(132)).intersect(상자(-10, 110, -10, 110, c(84.5), c(170.5)))
    for a, b in ((33, 41), (93, 101), (115, 131)):
        봉 = 봉.cut(원기둥(1, (c(128), c(127.5)), 60 * 화, c(a), c(b)).cut(원기둥(1, (c(128), c(127.5)), 43 * 화, c(a) - 1, c(b) + 1)))
    포크 = 돌출(10, 2).intersect(상자(-10, 110, c(131.5), 110, c(84.5), c(170.5)))
    s = 봉.union(포크).cut(상자(c(124.5), c(131.5), -10, c(85.5), -10, 110))
    return s, ["원기둥 Y(봉)", "납작 자르기 Z", "홈 셋", "돌출 Z(포크)", "합치기", "슬릿"]

if __name__ == "__main__":
    from 윤곽 import 메시로
    from 모양자 import 재기
    from s0 import unit
    O = os.path.join(H, "결과"); os.makedirs(O, exist_ok=True)
    for i in [int(a) for a in sys.argv[1:]] or (24, 8, 32, 22, 13, 10):
        s, 순서 = globals()["짓%d" % i]()
        gt = unit(trimesh.load(W.RR + str(부[i]), force="mesh")); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
        pm = 메시로(s); r = 재기(pm, gt); pm.export(os.path.join(O, "%02d.stl" % i)); cq.exporters.export(s, os.path.join(O, "%02d.step" % i))
        j = {"부품": str(부[i]), "순서": 순서, "edge_f1": r["edge_f1"], "iou": r["iou"], "조각": len(s.solids().vals()) - 1}; print(i, j, flush=True)
        json.dump(j, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
