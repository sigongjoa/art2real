"""투구 돔 — 구 하나를 투구 크기로
구 추가(UV 구) → 크기: 폭 ±39.7(정면 실루엣 · 측정) · 앞뒤 −5 ~ −62(옆 실루엣 앞 · 측정 / 뒤는 손) · 높이 0 ~ 56(돔 꼭대기 ~ 눈 밑)."""
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0, location=(0, 33.5, -28))
o = bpy.context.active_object; o.name = "투구"; o.scale = (39.7, 28.5, 28.0); bpy.ops.object.shade_smooth()
m = bpy.data.materials.new("흰 갑주"); m.diffuse_color = (0.9, 0.9, 0.93, 1); o.data.materials.append(m)
