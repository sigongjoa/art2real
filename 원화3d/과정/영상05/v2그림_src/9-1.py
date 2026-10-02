# -*- coding: utf-8 -*-
"""9-1 기울고 비틀린 가슴 · 골반: 위는 서 있는 블록 사람 넷, 아래는 그 가슴(주황) · 골반(파랑) 상자 쌍만.
허리는 선 하나(말벌 허리)로만 잇는다."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B, _몸 as Y
B.scene(line=1.6)
POSES = [((0, 9, 0), (0, -10, 0), -0.15), ((0, -5, 28), (0, 6, -12), 0.1), ((-16, 0, 0), (14, 0, 0), 0.0), ((0, 13, -22), (0, -9, 16), -0.2)]
for k, (cr, pr, sh) in enumerate(POSES):
    x = (k - 1.5) * 5.4
    Y.figure(x, cr, pr, sh)
    Y.figure(x, cr, pr, sh, limbs=False, z=-8.4)
B.look((0, 0, 1.6), 22, 8, ortho=31)
B.shot("9-1")
