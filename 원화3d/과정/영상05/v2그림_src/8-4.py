# -*- coding: utf-8 -*-
"""8-4 머리의 면: 옆 · 3/4 · 정면에서 평평한 조각으로 깎인 머리. 이마 면은 위로 넘어가 머리뼈, 옆은 관자 면으로 꺾이고 얼굴은 코 · 광대→윗입술 선으로 나뉜다."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B, _머리 as M
B.scene(line=2.0, crease=170)
B.sun(45, 0, -50, 4.5); B.bpy.data.worlds[0].node_tree.nodes["Background"].inputs[1].default_value = 0.18
for x, rot in ((-3.6, (0, 0, -90)), (0, (6, 0, -35)), (3.8, (-4, 0, 12))):
    M.head(B.empty(loc=(x, 0, 0), rot=rot), eyes=False)
B.look((0, 0, -0.35), 0, 0, ortho=13)
B.shot("8-4")
