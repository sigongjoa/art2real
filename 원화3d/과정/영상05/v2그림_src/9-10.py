# -*- coding: utf-8 -*-
"""9-10 손과 손목 덩어리의 돌기: 손목(회색)과 손(주황)을 각기둥 둘로. 두 덩어리가 꺾인 각도와 아래팔의 비틀림이 바뀌면서 손이 돌아간다.
곧게 · 손바닥 쪽으로 · 손등 쪽으로 · 엄지 쪽으로 · 엎친 채 꺾음. 아래 줄은 같은 각도의 손."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B, _몸 as Y
B.scene(line=1.8)
POSES = [(0, 0, 0), (45, 0, 0), (-40, 0, 0), (0, 30, 0), (35, 0, 80)]   # (굽힘, 엄지쪽 꺾임, 아래팔 비틀림)
for k, (fl, dev, tw) in enumerate(POSES):
    h = B.empty(loc=((k - 2) * 3.3, 0, -1.3), rot=(0, 0, -30 + tw))   # 아래 줄: 같은 각도의 손
    B.hull(B.tbox(-0.05, 1.6, 0.9, 0.62, 1.0, 0.7), "손목", B.CLAY, h)
    Y.hand(B.empty(rot=(-fl, dev, 0), parent=h), curls=(15, 20, 25, 30), thumb=(15, 15))
    g = B.empty(loc=((k - 2) * 3.3, 0, 3.4), rot=(0, 0, -30 + tw))
    B.hull(B.tbox(-0.05, 1.6, 0.9, 0.62, 1.0, 0.7), "손목", B.CLAY, g)
    w = B.empty("꺾임", rot=(-fl, dev, 0), parent=g)
    B.hull(B.tbox(-2.0, -0.05, 0.95, 0.26, 0.9, 0.42), "손", B.WARM, w)
    B.hull([(0.45, -0.1, -0.15), (0.45, 0.15, -0.15), (0.75, -0.3, -0.9), (0.62, -0.32, -1.25), (0.48, -0.05, -0.8)], "엄지", B.WARM, w)
B.look((0, 0, 0.75), 0, 12, ortho=21)
B.shot("9-10")
