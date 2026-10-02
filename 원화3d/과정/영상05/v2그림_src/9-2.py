# -*- coding: utf-8 -*-
"""9-2 쐐기 몸통: 어깨가 밑변, 배 끝이 꼭짓점인 길쭉한 쐐기(주황) — 그 아래쪽을 양옆의 엉덩이 · 골반 덩어리(파랑)가
버팀벽처럼 받친다. 정면 · 3/4 · 옆."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B, _몸 as Y
from mathutils import Vector
B.scene(line=1.8)

def torso(g):
    W = [(sx * 1.35, sy * 0.6, 7.0) for sx in (-1, 1) for sy in (-1, 1)] + [(sx * 1.2, sy * 0.55, 7.35) for sx in (-1, 1) for sy in (-1, 1)] + \
        [(sx * 0.12, -0.35, 3.55) for sx in (-1, 1)] + [(sx * 0.12, 0.25, 3.7) for sx in (-1, 1)]
    B.hull(W, "쐐기", B.WARM, g)
    for s in (-1, 1):   # 버팀벽: 안쪽 면이 쐐기 옆면에 기대고, 바깥은 엉덩이로 떨어진다
        P = [(s * 0.55, -0.45, 5.3), (s * 0.55, 0.5, 5.3), (s * 1.25, -0.4, 5.0), (s * 1.3, 0.55, 5.0),
             (s * 1.45, -0.35, 3.6), (s * 1.45, 0.6, 3.5), (s * 0.15, -0.5, 3.1), (s * 0.15, 0.55, 3.2), (s * 0.9, -0.3, 2.9), (s * 0.9, 0.6, 2.9)]
        B.hull(P, "버팀벽", B.COOL, g)
        Y.seg(Vector((s * 0.8, 0.1, 3.1)), Vector((s * 0.65, 0.0, 1.6)), 0.9, 0.7, parent=g)   # 넓적다리 그루터기
    Y.seg(Vector((0, 0.1, 7.3)), Vector((0, 0.05, 7.75)), 0.5, 0.45, parent=g)
    B.hull([(x, y, z + 8.25) for x, y, z in B.cbox(-0.42, 0.42, -0.5, 0.5, -0.55, 0.55, c=0.12)], "머리", parent=g)

for x, yaw in ((-5.2, 0), (0, -35), (5.0, -90)):
    torso(B.empty(loc=(x, 0, 0), rot=(0, 0, yaw)))
B.look((0, 0, 4.9), 0, 6, ortho=17.5)
B.shot("9-2")
