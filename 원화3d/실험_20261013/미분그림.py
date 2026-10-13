# -*- coding: utf-8 -*-
"""「CadQuery 는 왜 미분이 안 되나 · 어떻게 배우나」 설명 그림 — 블렌더 헤드리스 · 10-13
"C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b -P 미분그림.py  →  out/설명/미분/*.png
판 1 딱딱한 CAD: 상자 폭 3.0 → 3.4 로 바꿔도 켜진 화소가 같다(기울기 0)
판 2 부드러운 근사: 같은 폭 변화에 화소 밝기가 조금씩 변한다(기울기 있음)
판 3 보상 학습: 후보 CAD 넷 → 렌더 IoU 막대 → 가장 높은 것
판 4 숫자 다듬기: 구멍 반지름을 목표(유령)에 맞춰 네 걸음"""
import bpy, math, os, sys
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O = r"G:\art2real\out\설명\미분"; os.makedirs(O, exist_ok=True)
CAD, 켜짐, 꺼짐, 목표 = (0.35, 0.55, 0.95, 1), (1.0, 0.85, 0.25, 1), (0.16, 0.17, 0.2, 1), (0.95, 0.95, 0.97, 1)

def 상자(name, sx, sy, sz, loc, col):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = (sx, sy, sz); o.color = col; return o
def 원기둥(name, r, h, loc, col, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=48); o = bpy.context.object; o.name = name; o.color = col; return o
def 빼기(a, b):
    m = a.modifiers.new("b", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = b; bpy.context.view_layer.objects.active = a; bpy.ops.object.modifier_apply(modifier="b"); bpy.data.objects.remove(b)
def 더하기(a, b):
    m = a.modifiers.new("b", "BOOLEAN"); m.operation = "UNION"; m.object = b; bpy.context.view_layer.objects.active = a; bpy.ops.object.modifier_apply(modifier="b"); bpy.data.objects.remove(b)

def 화소판(폭, 부드럽게, 이름):   # 7×5 화소 격자 위에 폭 × 2 상자 · 화소 중심이 안이면 켬(딱딱) / 경계에서 거리로 밝기(부드럽게)
    H.scene(res=(900, 700), transparent=False, cavity=True)
    for i in range(7):
        for j in range(5):
            x, y = i - 3, j - 2
            if 부드럽게:
                d = max(abs(x) - 폭 / 2, abs(y) - 1.5)                       # 상자 SDF(화소 중심)
                a = 1 / (1 + math.exp(d / 0.18))                              # 시그모이드 → 0~1
            else:
                a = 1.0 if (abs(x) < 폭 / 2 and abs(y) < 1.5) else 0.0
            c = tuple(꺼짐[k] + (켜짐[k] - 꺼짐[k]) * a for k in range(3)) + (1,)
            상자("p%d%d" % (i, j), .92, .92, .12 + .5 * a, (x, y, (.12 + .5 * a) / 2), c)
    b = 상자("cad", 폭, 3.0, .05, (0, 0, .8), CAD); b.display_type = "WIRE"; b.show_in_front = True
    m = b.modifiers.new("w", "WIREFRAME"); m.thickness = .07
    H.look(center=(0, 0, 0), yaw=0, pitch=89.9, ortho=8.2, dist=40); H.shot(os.path.join(O, 이름 + ".png"))

for 폭, 이름 in ((3.0, "1_딱딱_30"), (3.4, "1_딱딱_34")): 화소판(폭, False, 이름)
for 폭, 이름 in ((3.0, "2_부드_30"), (3.4, "2_부드_34")): 화소판(폭, True, 이름)

# 판 3 — 목표(구멍 뚫린 블록 · 흰 유령) · 후보 넷(상자 · 원기둥 · 구멍 블록 · ㄱ자) + IoU 막대
H.scene(res=(1400, 700), transparent=False, cavity=True)
후보 = []
a = 상자("c0", 2, 2, 2, (-6, 0, 1), CAD); 후보.append((a, .55))
a = 원기둥("c1", 1.1, 2, (-2, 0, 1), CAD); 후보.append((a, .48))
a = 상자("c2", 2, 2, 2, (2, 0, 1), (0.35, 0.8, 0.45, 1)); 빼기(a, 원기둥("h", .5, 3, (2, 0, 1), CAD)); 후보.append((a, .93))
a = 상자("c3", 2, 2, 1, (6, 0, .5), CAD); 더하기(a, 상자("c3b", 1, 2, 1, (6.5, 0, 1.5), CAD)); 후보.append((a, .41))
for k, (o, s) in enumerate(후보):
    x = -6 + 4 * k; 상자("bar%d" % k, .5, .5, 3 * s, (x + 1.55, .6, 1.5 * s), (0.35, 0.8, 0.45, 1) if s > .9 else (0.95, 0.6, 0.25, 1))
H.look(center=(0, -1, 1.2), yaw=0, pitch=28, ortho=15.5, dist=60); H.shot(os.path.join(O, "3_보상.png"))

# 판 4 — 숫자 다듬기: 구멍 반지름 .15 → .3 → .42 → .5 (목표 .5 · 흰 유령 테)
for k, r in enumerate((.15, .3, .42, .5)):
    H.scene(res=(600, 600), transparent=False, cavity=True)
    a = 상자("b", 2, 2, 2, (0, 0, 1), (0.35, 0.8, 0.45, 1) if k == 3 else CAD); 빼기(a, 원기둥("h", r, 3, (0, 0, 1), CAD))
    g = 원기둥("ghost", .5, 2.06, (0, 0, 1), 목표); m = g.modifiers.new("w", "WIREFRAME"); m.thickness = .03; g.show_in_front = True
    H.look(center=(0, 0, 1), yaw=0, pitch=60, ortho=3.4, dist=30); H.shot(os.path.join(O, "4_다듬기_%d.png" % k))
print("ok")
