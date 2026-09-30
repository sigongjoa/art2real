"""눈구멍 — 상자로 투구를 파낸다(좌우 거울)
상자 추가 → 정면 영역 10(왼 눈) 상자 x −33 ~ −18 · y 33 ~ 55(측정) · 깊이: 투구 앞에서 8 들어감(손) → 미러 모디파이어(X) → 투구에 불리언(차) 모디파이어 「눈구멍」."""
x0, x1, y0, y1 = 값["눈구멍L_상자"]
bpy.ops.mesh.primitive_cube_add(size=1.0, location=((x0 + x1) / 2, -2.0, -(y0 + y1) / 2))
칼 = bpy.context.active_object; 칼.name = "눈구멍_칼"; 칼.scale = (x1 - x0, 24.0, y1 - y0); 칼["칼"] = True
mm = 칼.modifiers.new("좌우 거울", "MIRROR"); mm.use_axis[0] = True
b = bpy.data.objects["투구"].modifiers.new("눈구멍", "BOOLEAN"); b.operation = "DIFFERENCE"; b.object = 칼; b.solver = "EXACT"
