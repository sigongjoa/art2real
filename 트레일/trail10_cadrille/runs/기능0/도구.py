# -*- coding: utf-8 -*-
"""기능0 도구 — 기능 짓기에 쓰는 낱말 · 숫자는 그림(256 실루엣 화소)에서 읽어 넘긴다 · 10-11"""
import os, sys, json, numpy as np, trimesh, cadquery as cq
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(R, "윤곽0"), os.path.join(R, "조각0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
os.environ["ARC"] = "2"
import 윤곽 as W
V = cq.Vector; 부 = np.load(os.path.join(R, "깊이학습", "시험.npz"))["부품"]
c = lambda p: ((p + .5) / 256 * 1.1 - .05) * 100   # 256 화소 → CAD (단위 상자 × 100)
c8 = lambda p: ((p + .5) / 128 * 1.1 - .05) * 100
화 = 1.1 / 256 * 100   # 화소 하나 길이
_S = {}
def 실루엣(i):
    if i not in _S:
        from 실물보기 import 실물보기
        from s0 import unit
        _S[i] = 실물보기(unit(trimesh.load(W.RR + str(부[i]), force="mesh")), W.N)[0]
    return _S[i]
def 상자(x0, x1, y0, y1, z0, z1): return cq.Workplane().add(cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0)))
def 돌출(i, ax):   # 그 축 방향 실루엣(직선 + 원호 · 모서리 끊기)을 밀어낸 판 · 축 ax: 0 X · 1 Y · 2 Z
    return W.판(ax, 실루엣(i)[2 * ax], True)
def 원기둥(ax, 중심, r, a, b):   # 축 ax 방향 · 중심 = 나머지 두 좌표(CAD) · a~b
    d = [0, 0, 0]; d[ax] = 1; p = list(중심); p.insert(ax, a)
    return cq.Workplane().add(cq.Solid.makeCylinder(r, b - a, V(*p), V(*d)))
def 구(중심, r): return cq.Workplane().add(cq.Solid.makeSphere(r, V(*중심), angleDegrees1=-90))
