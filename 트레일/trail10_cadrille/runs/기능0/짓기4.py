# -*- coding: utf-8 -*-
"""기능0 4 판 — #23 #29 고치기(깊이 맞춤) + 다면 덩어리 6(#3 #15 #16 #18 #26 #31) · 10-11
홈은 「포켓」: 사람이(Claude) 고른 방향 · 네모 안에서 깊은 곳 윤곽을 바닥 깊이까지 판다"""
import os, sys, json
from 도구 import *
def 교차(i): return 돌출(i, 0).intersect(돌출(i, 1)).intersect(돌출(i, 2))
def 판다(s, i, *홈):
    for h in 홈:
        p = 포켓(i, *h)
        if p is not None: s = s.cut(p)
        else: print("포켓 없음", i, h)
    return s

def 짓23():   # 앞면 = 원기둥(축 Y · 중심 X -59.2 · Z 50 · R 124.4 · 잔차 0.3) · 두께 3.1(앞뒤 깊이 차) → 방패 윤곽(X) 으로 자르기 + 뒤 혹 + 걸이
    판 = 원기둥(1, (-59.23, 50.0), 124.41, -10, 110).cut(원기둥(1, (-59.23, 50.0), 124.41 - 3.1, -11, 111)).intersect(돌출(23, 0)).intersect(돌출(23, 2))
    안 = 원기둥(1, (-59.23, 50.0), 124.41 - 1.5, -10, 110)   # 혹 · 걸이는 판 두께 가운데까지 (판에 붙게)
    혹 = 돌출(23, 1).intersect(상자(c(125.5), 110, c(26.5), c(51.5), c(93.5), c(161.5))).intersect(안)
    걸이 = 돌출(23, 1).intersect(돌출(23, 2)).intersect(상자(c(88), 110, c(77), c(170), c(56), c(88))).intersect(안)
    return 판.union(혹).union(걸이), ["원기둥 껍질 Y(깊이 맞춤)", "교차 X · Z", "돌출 Y(뒤 혹)", "돌출 Y ∩ Z(걸이)"]

def 짓29():   # 교차 − 공 소켓 둘(앞 깊이 접시를 구로 맞춤 · R 23.5 · 잔차 2)
    s = 교차(29)
    for x in (16.8, 83.26): s = s.cut(구((x, 47.2, 59.5), 23.5))
    return s, ["교차", "구 빼기 ×2(공 소켓)"]

def 짓3(): return 판다(교차(3), 3, (2, 8, 115, 0, 36)), ["교차", "포켓 Y(왼쪽 깊은 칸)"]
def 짓15(): return 판다(교차(15), 15, (4, 50, 118, 20, 68), (1, 33, 81, 20, 70)), ["교차", "포켓 Z(아치 굴)", "포켓 X(구멍 둘레 턱)"]
def 짓16(): return 교차(16), ["교차(두 벽 사이 틈)"]
def 짓18(): return 판다(교차(18), 18, (4, 29, 62, 28, 87)), ["교차", "포켓 Z(가운데 칸)"]
def 짓26(): return 판다(교차(26), 26, (0, 20, 100, 20, 90)), ["교차", "포켓 X(ㄴ 자 굴)"]
def 짓31(): return 교차(31), ["교차"]   # 안 함: 육각 너트 자리(작음)

if __name__ == "__main__":
    from 윤곽 import 메시로
    from 모양자 import 재기
    from s0 import unit
    O = os.path.join(H, "결과"); os.makedirs(O, exist_ok=True)
    for i in [int(a) for a in sys.argv[1:]] or (23, 29, 3, 15, 16, 18, 26, 31):
        s, 순서 = globals()["짓%d" % i]()
        gt = unit(trimesh.load(W.RR + str(부[i]), force="mesh")); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
        pm = 메시로(s); r = 재기(pm, gt); pm.export(os.path.join(O, "%02d.stl" % i)); cq.exporters.export(s, os.path.join(O, "%02d.step" % i))
        j = {"부품": str(부[i]), "순서": 순서, "edge_f1": r["edge_f1"], "iou": r["iou"], "조각": len(s.solids().vals()) - 1, "부피비": round(pm.volume / gt.volume, 2)}; print(i, j, flush=True)
        json.dump(j, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
