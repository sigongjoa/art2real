# -*- coding: utf-8 -*-
"""9-6 위팔 · 아래팔 · 손목을 각진 마디로: 바깥 쐐기(주황)가 위팔 끝을 덮고 엄지 쪽을, 안 쐐기(파랑)는 새끼 쪽을 가리킨다.
어깨 근육도 쐐기(진한 주황) — 꼭짓점이 위팔 바깥 홈에 박힌다. 왼쪽 둘: 블록(바깥에서 · 안에서), 오른쪽 둘: 같은 팔을 녹인 둥근 윤곽."""
import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B, _몸 as Y
B.scene(line=1.8)
for k, rz in enumerate((-65, 115)):
    g = B.empty(loc=(-5.6 + 3.4 * k, 0, 3.4), rot=(0, 0, rz))
    ps = Y.arm(g, elbow=14, wrist=-10, twist=10)
    B.bpy.context.view_layer.update()
    sm = B.smooth_copy(ps, voxel=0.035, iters=30); sm.location.x += 6.8
B.look((0, 0, -0.15), 0, 4, ortho=19)
B.shot("9-6")
