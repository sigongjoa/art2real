# -*- coding: utf-8 -*-
"""8-3 원근 속 머리 구성선: 머리를 여러 방향으로 돌리고, 얼굴 자리를 정하는 선(가운데 · 눈썹 · 코밑 · 귀 앞)이 덩어리를 따라 휜다."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B, _머리 as M
B.scene()
PL = [((0, 0, 0), (1, 0, 0)), ((0, 0, 0.25), (0, 0, 1)), ((0, 0, -0.36), (0, 0, 1)), ((0, 0, -0.62), (0, 0, 1)), ((0, 0.25, 0), (0, 1, 0))]
ROT = [(-20, 0, -30), (10, 0, 0), (-10, 0, 55), (30, 0, -50), (-35, 0, 15), (25, 0, 35)]
for k, rot in enumerate(ROT):
    g = B.empty(loc=((k % 3 - 1) * 4.3, 0, 1.95 if k < 3 else -1.95), rot=rot)
    parts = M.head(g, neck=False)
    B.section_lines(parts[0], PL)
B.look((0, 0, 0), 0, 0, ortho=16)
B.shot("8-3")
