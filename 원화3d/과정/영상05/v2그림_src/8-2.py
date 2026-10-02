# -*- coding: utf-8 -*-
"""8-2 상자 속 머리: 정면 · 올려다봄 · 내려다봄 + 위에서 본 머리. 옆은 정사각, 앞은 긴 직사각."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B, _머리 as M
B.scene()
BOX = (-0.80, 0.80, -1.22, 1.12, -1.12, 1.12)
for loc, rot in (((-3.0, 0, 2.0), (0, 0, -22)), ((3.0, 0, 2.0), (-38, 0, 20)), ((-3.0, 0, -2.0), (30, 0, -18))):
    g = B.empty(loc=loc, rot=rot); M.head(g, neck=False); B.cage(*BOX, parent=g)
g = B.empty(loc=(3.0, 0, -2.0), rot=(90, 0, 0)); M.head(g, neck=False); B.cage(*BOX, parent=g, mids=False)
B.look((0, 0, 0), 0, 0, ortho=16.5)
B.shot("8-2")
