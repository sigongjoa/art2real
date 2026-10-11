# -*- coding: utf-8 -*-
"""기능0 — #4 #21 을 CAD 기능 순서로 손 짓기 (치수는 흐름.png 의 여섯 방향 선 + 깊이에서 읽은 화소값) · 10-11
python runs/기능0/짓기.py  →  결과/NN.step · NN.stl · NN.json"""
import os, sys, json, numpy as np, trimesh, cadquery as cq
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(R, "윤곽0"), os.path.join(R, "조각0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
V = cq.Vector
c = lambda p: ((p + .5) / 256 * 1.1 - .05) * 100   # 256 화소 → CAD (단위 상자 × 100)
c8 = lambda p: ((p + .5) / 128 * 1.1 - .05) * 100  # 128 화소(선 그림) → CAD
상자 = lambda x0, x1, y0, y1, z0, z1: cq.Workplane().add(cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0)))

def 원뿔(y0, y1, r, zc, xc=50.0):   # Y 축 따라 반지름 · 중심 z 가 곧게 변하는 원뿔대 (r · zc 는 y 의 함수)
    w = [cq.Wire.makeCircle(r(y), V(xc, y, zc(y)), V(0, 1, 0)) for y in (y0, y1)]
    return cq.Workplane().add(cq.Solid.makeLoft(w, True))

def 짓기4():
    # 앞(Y) 그림 C 자 · 위 그림 X 폭 → Y 80 화소: R 116 · 중심 z 198 / Y 175: R 107.2 · z 193.2 (화소) · 두께 = 앞뒤 깊이 차 0.015
    ya, yb = c(80), c(175); k = lambda a, b: (lambda y: a + (b - a) * (y - ya) / (yb - ya))
    r = k(116 * .4297, 107.2 * .4297); zc = k(c(198), c(193.2)); t = 1.5; y0, y1 = c(50), c(205)
    겉 = 원뿔(y0, y1, r, zc); 속 = 원뿔(y0 - 1, y1 + 1, lambda y: r(y) - t, zc)
    s = 겉.cut(속).intersect(상자(-10, 110, c(54.5), c(200.5), -10, c(174.5)))   # C 의 끝 = z 174 평면 · 위아래 끝
    # 옆(X) 그림 윗변 비스듬: (Y 55, Z 174) → (Y 74.2, Z 82) 화소 · 이 선 위쪽을 잘라냄
    p0, p1 = np.array([c(55), c(174.5)]), np.array([c(74.2), c(82)]); d = p1 - p0
    칼 = cq.Workplane("YZ").polyline([(float((p0 - 3 * d)[0]), float((p0 - 3 * d)[1])), (float((p1 + 3 * d)[0]), float((p1 + 3 * d)[1])), (-40.0, float((p1 + 3 * d)[1])), (-40.0, float((p0 - 3 * d)[1]))]).close().extrude(120).translate((-10, 0, 0))
    s = s.cut(칼)
    # 아래 끝 띠: Y 181~197 화소 · 바깥 2 화소 두꺼움
    띠 = 원뿔(c(181), c(197), lambda y: r(y) + 2 * .4297, zc).cut(원뿔(c(180), c(198), lambda y: r(y) - .1, zc)).intersect(상자(-10, 110, 0, 100, -10, c(174.5)))
    return s.union(띠)

def 짓기21():
    x0, x1, y0, y1, z0, z1 = c(67.5), c(187.5), c(11.5), c(243.5), c(79.5), c(175.5)
    몸 = 상자(x0, x1, y0, y1, z0, z1).edges("|Z").fillet(5.2)   # 뒤 그림 둥근 네모 테 · 모서리 12 화소
    # 옆(X) 그림 D 자 (Y, Z) 화소
    P = lambda *q: (c(q[0]), c(q[1]))
    옆 = (cq.Workplane("YZ").moveTo(*P(13, 104)).threePointArc(P(20, 88), P(33, 81)).lineTo(*P(194, 81)).threePointArc(P(219, 102), P(232, 129))
          .lineTo(*P(241, 162)).lineTo(*P(243.5, 175.5)).lineTo(*P(11.5, 175.5)).close().extrude(120).translate((-10, 0, 0)))
    # 위(Y) 그림 뒤 모서리 둥긂 (X, Z) · 좌우 같게
    Q = lambda x, z: (c(x), c(z))
    위 = (cq.Workplane("XZ").moveTo(*Q(67.5, 175.5)).lineTo(*Q(67.5, 112)).threePointArc(Q(71.5, 90), Q(84, 80.5)).lineTo(*Q(171, 80.5))
          .threePointArc(Q(183.5, 90), Q(187.5, 112)).lineTo(*Q(187.5, 175.5)).close().extrude(-120).translate((0, -10, 0)))
    몸 = 몸.intersect(옆).intersect(위)
    t = 5 * 1.1 / 128 * 100   # 앞 그림 테 폭 5 화소
    try: 껍 = 몸.faces(">Z").shell(-t)
    except Exception as e: print("셸 실패", str(e)[:60]); 껍 = 몸
    창 = cq.Workplane("XY").center(c(127.5), c(112)).rect(c(171.5) - c(83.5), c(185.5) - c(38.5)).extrude(200).translate((0, 0, -50)).edges("|Z").fillet(20 * .4297)
    s = 껍.cut(창)
    for r0 in (50.5, 60.5, 70.5):   # 위 그림 줄 셋 (128 화소 · X 행 · Z 열 52~84)
        s = s.cut(상자(c8(r0), c8(r0 + 6), -5, 12, c8(51.5), c8(84.5)))
    return s

if __name__ == "__main__":
    from 윤곽 import 메시로, RR
    from 모양자 import 재기
    from s0 import unit
    부 = np.load(os.path.join(R, "깊이학습", "시험.npz"))["부품"]; O = os.path.join(H, "결과"); os.makedirs(O, exist_ok=True)
    for i, f in ((4, 짓기4), (21, 짓기21)):
        s = f(); v = s.val(); print(i, "valid", v.isValid(), "부피", round(v.Volume(), 1), "솔리드", len(s.solids().vals()))
        gt = unit(trimesh.load(RR + str(부[i]), force="mesh")); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
        pm = 메시로(s); r = 재기(pm, gt); pm.export(os.path.join(O, "%02d.stl" % i)); cq.exporters.export(s, os.path.join(O, "%02d.step" % i))
        j = {"부품": str(부[i]), "edge_f1": r["edge_f1"], "iou": r["iou"], "조각": len(s.solids().vals()) - 1}; print(j)
        json.dump(j, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
