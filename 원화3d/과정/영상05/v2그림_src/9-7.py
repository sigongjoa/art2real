# -*- coding: utf-8 -*-
"""9-7 아래로 가늘어지는 사각 기둥 마디: 팔 전체도 어깨→손목으로 가늘어지고, 마디마다 위→아래로 가늘어진다.
어깨 단면은 모서리 둥근 정사각(빨강), 팔꿈치에서 위팔(넓고 얇게)과 아래팔(좁고 두껍게)의 너비 · 두께가 뒤바뀐다(빨강 둘).
정면 · 옆 · 3/4."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B
B.scene(line=1.8)

def ring(z, w, d, c):
    return [(sx * (w / 2 - c), sy * d / 2, z) for sx in (-1, 1) for sy in (-1, 1)] + [(sx * w / 2, sy * (d / 2 - c), z) for sx in (-1, 1) for sy in (-1, 1)]

def arm(g):
    up = B.hull(ring(0, 1.05, 1.05, 0.25) + ring(-3.0, 1.0, 0.62, 0.12), "위팔", parent=g)
    fo = B.hull(ring(-3.0, 0.66, 0.92, 0.12) + ring(-5.7, 0.62, 0.42, 0.08), "아래팔", parent=g)
    B.hull(ring(-5.7, 0.84, 0.36, 0.06) + ring(-7.0, 0.74, 0.26, 0.05), "손", parent=g)
    B.section_lines(up, [((0, 0, -0.35), (0, 0, 1)), ((0, 0, -2.85), (0, 0, 1))], t=0.035, lift=1.04)
    B.section_lines(fo, [((0, 0, -3.15), (0, 0, 1))], t=0.035, lift=1.06)

for x, rz in ((-4.2, 0), (0, 90), (4.2, 35)):
    arm(B.empty(loc=(x, 0, 3.4), rot=(0, 0, rz)))
B.look((0, 0, -0.3), 0, 12, ortho=17.5)
B.label("정면", (-4.2, 0, -4.05)); B.label("옆", (0, 0, -4.05))
B.shot("9-7")
