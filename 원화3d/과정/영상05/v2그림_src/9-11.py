# -*- coding: utf-8 -*-
"""9-11 꺾인 직선만으로 잡은 손과 주먹: 손바닥(주황) 상자 + 손가락 각기둥 마디. 편 손 · 가리키는 손 · 주먹."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B, _몸 as Y
B.scene(line=1.8)
P = [((-4.6, 0, 1.4), (0, 0, -30), (12, 18, 25, 32), (30, 8)),
     ((0, 0, 1.4), (-20, 0, 40), (0, 85, 88, 90), (10, 50)),
     ((4.6, 0, 1.1), (15, 0, -20), (92, 94, 95, 96), (5, 55))]
for loc, rot, cu, th in P:
    g = B.empty(loc=loc, rot=rot)
    B.hull(B.tbox(0.0, 1.6, 0.9, 0.55, 1.0, 0.65), "팔", (0.93, 0.93, 0.92), g)
    Y.hand(g, curls=cu, thumb=th)
B.look((0, 0, 0.9), 0, 10, ortho=14.5)
B.shot("9-11")
