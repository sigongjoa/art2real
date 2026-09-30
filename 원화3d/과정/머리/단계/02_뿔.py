"""뿔 — 네모 원뿔(칼날) 하나
원뿔 추가(꼭짓점 4) → 밑 = 정면 영역 1 의 아래 끝(측정) · 끝 = 영역 1 의 위 끝(측정) · 밑 폭 = 영역 1 아래 줄 폭(측정) · 앞으로 기울기 +14(손)."""
from mathutils import Vector
v = 값["뿔"]; x, y밑 = v["밑"]; y끝 = v["끝y"]; r = max(6.0, v["반지름"] * 2)
밑 = Vector((x, 10.0, -y밑)); 끝 = Vector((x, -4.0, -y끝)); d = 끝 - 밑
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=r, radius2=0.3, depth=d.length, location=(밑 + 끝) / 2)
o = bpy.context.active_object; o.name = "뿔"; o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
o.data.materials.append(bpy.data.materials["흰 갑주"])
