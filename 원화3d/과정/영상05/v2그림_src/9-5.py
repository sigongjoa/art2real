# -*- coding: utf-8 -*-
"""9-5 팔과 어깨 덩어리의 쐐기 · 맞물림: 어깨 덩어리(진한 주황)는 아래 바깥으로 기울어 위팔 위에 비스듬히 겹치고,
아래팔(쐐기 둘 + 심)은 위팔 끝의 뒤에서 시작해 비스듬히 가로지른다. 끝과 끝이 아니라 겹쳐 물린다. 자세 셋."""
import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B, _몸 as Y
B.scene(line=1.8)
POSES = [((-5.6, 0, 3.0), (0, -8, -35), 5, -5, 15), ((-0.8, 0, 3.0), (0, -20, -25), 75, 15, 40), ((3.4, 0, 1.4), (0, -55, -20), 50, -20, -20)]
for loc, rot, el, wr, tw in POSES:
    body = B.empty(loc=loc, rot=(0, 0, rot[2]))
    B.hull([(x, y, z) for x in (-1.4, -0.35) for y in (-0.7, 0.7) for z in (-1.9, 0.5)], "가슴", (0.9, 0.9, 0.88), body)
    g = B.empty(loc=(0.15, 0, 0), rot=(0, rot[1], 0), parent=body)
    Y.arm(g, elbow=el, wrist=wr, twist=tw)
B.look((0, 0, 0), 0, 6, ortho=19.5)
B.shot("9-5")
