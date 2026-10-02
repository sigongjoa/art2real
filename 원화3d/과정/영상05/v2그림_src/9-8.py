# -*- coding: utf-8 -*-
"""9-8 다리의 띠: 넓적다리 · 무릎뼈 · 종아리 · 정강이 · 발목 · 발을 각진 덩어리로, 면이 꺾이는 자리마다 띠(빨강).
넓적다리 앞은 무릎뼈를 거쳐 정강이로 내려가고, 뒤쪽 종아리(파랑)는 무릎뼈 윗선 높이까지 파고든다. 옆 · 정면 · 3/4."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B
B.scene(line=1.8)

def ring(z, y0, y1, w, c=0.15):
    return [(sx * (w / 2 - c), y, z) for sx in (-1, 1) for y in (y0, y1)] + [(sx * w / 2, y, z) for sx in (-1, 1) for y in (y0 + c, y1 - c)]

def leg(g):
    th = B.hull(ring(8.0, -0.85, 0.9, 1.6, 0.35) + ring(6.4, -0.8, 0.75, 1.45, 0.3) + ring(4.6, -0.55, 0.5, 1.05, 0.15), "넓적다리", parent=g)
    B.hull(B.cbox(-0.3, 0.3, -0.72, -0.4, 3.95, 4.75, c=0.08), "무릎뼈", B.WARM, g)
    sh = B.hull(ring(4.6, -0.55, 0.3, 1.0) + ring(3.9, -0.55, 0.2, 0.9) + ring(0.95, -0.3, 0.15, 0.55, 0.1), "정강이", parent=g)
    B.hull(ring(4.75, 0.0, 0.62, 0.95) + ring(3.3, -0.05, 0.85, 1.05) + ring(1.5, -0.05, 0.38, 0.6, 0.1), "종아리", B.COOL, g)
    B.hull(ring(0.95, -0.3, 0.2, 0.6, 0.1) + ring(0.45, -0.35, 0.35, 0.68, 0.1), "발목", parent=g)
    B.hull([(sx * w, y, z) for sx in (-1, 1) for w, y, z in ((0.33, 0.4, 0.0), (0.33, 0.4, 0.5), (0.3, -0.3, 0.65), (0.45, -2.2, 0.0), (0.4, -2.2, 0.25))], "발", parent=g)
    B.section_lines(th, [((0, 0, z), (0, 0.22, 1)) for z in (7.2, 5.5)], t=0.035, lift=1.02)
    B.section_lines(sh, [((0, 0, z), (0, -0.2, 1)) for z in (2.6, 1.5)], t=0.035, lift=1.03)

for x, rz in ((-3.6, 90), (0, 0), (3.6, 40)):
    leg(B.empty(loc=(x, 0, -4.0), rot=(0, 0, rz)))
B.look((0, 0, -0.3), 0, 6, ortho=20)
B.label("옆", (-3.6, 0, -4.55)); B.label("정면", (0, 0, -4.55))
B.shot("9-8")
