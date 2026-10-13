# 쇼츠 프레임용 조명 렌더(EEVEE) — 금속 질감 · 조명 셋 · 부드러운 그림자 · 빛나는 바닥 격자 · 블룸 · 10-13
# "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b -P 렌더_빛.py  →  out/설명/구멍/빛_r*.png
import bpy, math, mathutils, sys
O = "G:/art2real/out/설명/구멍/"; 형태들 = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["0", "1", "2", "3", "4엇", "4", "5", "6"]
바탕 = (0.010, 0.017, 0.040)

def 재질(name, col, metal=0.0, rough=0.4, emit=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = col + (1,); b.inputs["Metallic"].default_value = metal; b.inputs["Roughness"].default_value = rough
    if emit: b.inputs["Emission Color"].default_value = emit + (1,); b.inputs["Emission Strength"].default_value = strength
    return m
def 빛(kind, loc, energy, col=(1, 1, 1), size=6.0, aim=(0, 0, 0)):
    l = bpy.data.lights.new(kind, kind); l.energy = energy; l.color = col
    if kind == "AREA": l.size = size
    o = bpy.data.objects.new(kind, l); bpy.context.scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (mathutils.Vector(aim) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()

def 장면():
    bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene
    try: sc.render.engine = "BLENDER_EEVEE"
    except TypeError: sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.render.resolution_x = sc.render.resolution_y = 900; sc.render.film_transparent = False
    ee = sc.eevee; ee.use_bloom = True; ee.bloom_intensity = 0.06; ee.use_soft_shadows = True; ee.use_gtao = True; ee.taa_render_samples = 64
    sc.view_settings.view_transform = "Filmic"; sc.view_settings.look = "Medium High Contrast"
    sc.world = bpy.data.worlds.new("w"); sc.world.use_nodes = True; sc.world.node_tree.nodes["Background"].inputs[0].default_value = 바탕 + (1,); sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    # 바닥: 어두운 판 + 빛나는 격자 선
    bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, -10.02)); f = bpy.context.object; f.data.materials.append(재질("바닥", 바탕, rough=0.7))
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=24, size=120, location=(0, 0, -10.0)); g = bpy.context.object
    w = g.modifiers.new("w", "WIREFRAME"); w.thickness = 0.05; g.data.materials.append(재질("격자", (0.02, 0.06, 0.12), emit=(0.15, 0.55, 1.0), strength=0.18))
    # 빛: 키(왼 위 흰) · 채움(오른 약하게) · 뒤 테두리(하늘)
    빛("AREA", (-30, -25, 40), 16000, (1.0, 0.97, 0.94), 22); 빛("AREA", (35, -30, 10), 5000, (0.75, 0.85, 1.0), 18); 빛("AREA", (-5, 40, 18), 5000, (0.3, 0.7, 1.0), 8, (0, 0, 5))
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 85
    y, p, dist = math.radians(35), math.radians(32), 120
    d = mathutils.Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p))); cam.location = d * dist + mathutils.Vector((0, 0, -1.5))
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler(); return sc

sc = 장면(); 몸 = 재질("몸", (0.62, 0.72, 0.88), metal=0.15, rough=0.35)
for r in 형태들:
    for o in [o for o in sc.objects if o.name.startswith("r")]: bpy.data.objects.remove(o)
    bpy.ops.import_mesh.stl(filepath=O + "r%s.stl" % r); o = bpy.context.selected_objects[0]; o.name = "r" + r; o.data.materials.append(몸)
    bpy.ops.object.shade_smooth(); o.data.use_auto_smooth = True; o.data.auto_smooth_angle = math.radians(35)
    sc.render.filepath = O + "빛_r%s.png" % r; bpy.ops.render.render(write_still=True)
print("ok")
