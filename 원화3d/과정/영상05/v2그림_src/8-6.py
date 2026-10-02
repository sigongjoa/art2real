# -*- coding: utf-8 -*-
"""8-6 코는 네 면의 쐐기: 콧등 면(따뜻한 색)은 끝으로 넓어지고, 옆면 둘(파랑)도 끝으로 넓어지며,
밑면(회색)은 얼굴 쪽이 넓고 가운데 연골이 콧구멍 면 둘을 가른다. 3/4 위 · 아래에서 · 옆."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _블록 as B, _머리 as M
B.scene(line=2.2); B.sun(45, 0, -50, 3.0); B.bpy.data.worlds[0].node_tree.nodes["Background"].inputs[1].default_value = 0.25
TOP, SIDE, BOT = (0.95, 0.60, 0.32), (0.42, 0.60, 0.86), (0.48, 0.48, 0.50)

def nose(g):
    P = [(s * 0.08, -0.86, 0.24) for s in (-1, 1)] + [(s * 0.16, -1.16, -0.27) for s in (-1, 1)] +         [(s * 0.22, -0.86, -0.36) for s in (-1, 1)] + [(0, -0.86, -0.42), (0, -1.17, -0.33)]
    o = B.hull(P, "코", parent=g, merge=4)
    o.data.materials.clear()
    for c in (TOP, SIDE, BOT): o.data.materials.append(B.mat(c))
    for p in o.data.polygons:
        n = p.normal
        p.material_index = 1 if abs(n.x) > 0.75 else (2 if n.z < -0.35 else 0)
    # 얼굴 판: 눈구멍 아래 ~ 윗입술 (얼굴 덩어리의 앞 조각)
    B.hull(B.cbox(-0.42, 0.42, -0.87, -0.80, -0.50, 0.36), "얼굴판", (0.95, 0.95, 0.94), parent=g)
    return o

for loc, rot in (((-4.0, 0, 0.0), (20, 0, -38)), ((0, 0, 0.4), (-32, 0, -28)), ((3.9, 0, 0.0), (0, 0, -90))):
    g = B.empty(loc=loc, rot=rot, scale=(3.4, 3.4, 3.4)); B.bpy.context.view_layer.update()
    nose(g); g.location -= g.matrix_world @ B.Vector((0, -0.95, -0.05)) - g.location
    if loc[0] < 0:
        B.bpy.context.view_layer.update(); W = lambda p: g.matrix_world @ B.Vector(p) + B.Vector((0, -5, 0))
        B.label("콧등", W((0.0, -1.02, 0.02)), color="#6b3000"); B.label("옆면", W((0.24, -0.92, -0.16)), color="#132f55")
        B.label("밑면", W((0.02, -1.0, -0.52)), color="#555")
B.look((-0.4, 0, 0), 0, 0, ortho=12.5)
B.shot("8-6")
