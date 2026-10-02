# -*- coding: utf-8 -*-
"""8-1 머리의 블록 구성: 여러 방향의 상자 머리 + 같은 덩어리를 녹인 「얼굴」 하나."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B, _머리 as M
B.scene()
# 윗줄: 상자 머리 셋(내려다봄 · 옆 · 올려다봄)
for x, rot in ((-4.9, (-18, 0, -35)), (0, (0, 0, -80)), (4.9, (22, 0, 30))):
    M.head(B.empty(loc=(x, 0, 2.05), rot=rot))
# 아랫줄: 같은 각도의 상자 머리와 녹인 머리
g = B.empty(loc=(-2.5, 0, -2.0), rot=(8, 0, -28)); parts = M.head(g)
bpy = B.bpy; bpy.context.view_layer.update()
sm = B.smooth_copy(parts, voxel=0.035, iters=10); sm.location.x += 5.0
B.look((0, 0, 0), 0, 0, ortho=16.5)
B.shot("8-1")
