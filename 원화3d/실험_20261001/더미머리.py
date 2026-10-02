# -*- coding: utf-8 -*-
"""메카 머리 더미 생성기 + 툰 렌더 (10-02 사용자 「더미 가져오는 건 이해된다」 → 받지 말고 우리 낱말로 짓자).
blender -b -P 더미머리.py -- <시작씨앗> <개수>
머리 = 우리 부품 낱말: 속머리(상자) · 투구 돔(팔각 반구 껍질) · 차양(V 쐐기 둘) · 눈구멍 판(검정) · 눈(파랑) · 미늘(포갠 V 판 2~4) · 볼날개(판 둘) · 뿔(원뿔 1~3) · 안테나(막대 0/2).
씨앗마다 치수 · 각도 · 개수 무작위. 렌더 3 종 × 두 각도: 툰 입력 · 선 종류 정답(빨강 외곽·가림 / 파랑 꺾임) · 부품 이름 지도(평면색 = 부품 번호).
모든 부품이 우리가 지은 것이라 이름 · 선 정답이 정확하다. 받은 3D 없음."""
import bpy, bmesh, math, random, os, sys, json, mathutils
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O = r"G:\art2real\원화3d\out\오메가몬2\지표\더미머리"; os.makedirs(O, exist_ok=True)
부품 = ["속머리", "투구 돔", "차양", "눈구멍 판", "눈", "미늘", "볼날개", "뿔", "안테나"]
색 = {"속머리": (0.12, 0.12, 0.15), "투구 돔": (0.9, 0.91, 0.96), "차양": (0.9, 0.91, 0.96), "눈구멍 판": (0.08, 0.08, 0.1), "눈": (0.25, 0.55, 0.95),
     "미늘": (0.9, 0.91, 0.96), "볼날개": (0.9, 0.91, 0.96), "뿔": (0.9, 0.82, 0.35), "안테나": (0.85, 0.75, 0.3)}

def 상자(이름, 크기, 위치, 회전=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.active_object; o.scale = 크기; o.location = 위치; o.rotation_euler = [math.radians(a) for a in 회전]; o["부품"] = 이름; return o
def 판(이름, 폭, 높이, 두께, 위치, 회전): return 상자(이름, (폭, 두께, 높이), 위치, 회전)

def 짓기(seed):
    R = random.Random(seed); objs = []
    W = R.uniform(0.75, 1.0); Hh = R.uniform(0.8, 1.0); D = R.uniform(0.85, 1.1)
    objs.append(상자("속머리", (W * 1.2, D * 1.3, Hh * 1.3), (0, 0.1, -0.15)))
    # 투구 돔: 팔각 반구 껍질
    seg = R.choice([8, 8, 10, 12]); bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=R.choice([4, 5, 6]), radius=1)
    d = bpy.context.active_object; bm = bmesh.new(); bm.from_mesh(d.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.05], context="VERTS"); bm.to_mesh(d.data); bm.free()
    d.scale = (W * 0.75, D * 0.85, Hh * 0.7); d.location = (0, 0.12, 0.25); sd = d.modifiers.new("두께", "SOLIDIFY"); sd.thickness = 0.06; d["부품"] = "투구 돔"; objs.append(d)
    # 차양: V 쐐기 둘
    va = R.uniform(10, 28); vz = R.uniform(0.18, 0.3)
    for s in (-1, 1): objs.append(판("차양", W * 0.42, 0.14, 0.12, (s * W * 0.2, -D * 0.72, vz), (R.uniform(15, 35), 0, -s * va)))
    # 눈구멍 판 + 눈
    ez = vz - R.uniform(0.18, 0.26); ew = R.uniform(0.22, 0.32)
    for s in (-1, 1):
        objs.append(판("눈구멍 판", ew, 0.16, 0.05, (s * W * 0.25, -D * 0.62, ez), (0, 0, -s * R.uniform(5, 20))))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.055); e = bpy.context.active_object; e.location = (s * W * 0.25, -D * 0.66, ez); e["부품"] = "눈"; objs.append(e)
    # 미늘: 포갠 V 판 2~4
    n = R.randint(2, 4); z = ez - 0.14; fw = W * 0.5; ang = R.uniform(25, 40); fwd = -D * 0.66
    for i in range(n):
        h = R.uniform(0.12, 0.18)
        for s in (-1, 1): objs.append(판("미늘", fw * 0.55, h, 0.07, (s * fw * 0.25, fwd - i * R.uniform(0.04, 0.09), z), (R.uniform(-10, 15), 0, -s * ang)))
        z -= h * 0.8; fw *= R.uniform(0.7, 0.85)
    # 볼날개
    for s in (-1, 1): objs.append(판("볼날개", 0.12, Hh * R.uniform(0.45, 0.7), D * R.uniform(0.5, 0.8), (s * W * 0.68, -D * 0.05, ez - 0.1), (R.uniform(-15, 10), 0, s * R.uniform(5, 25))))
    # 뿔
    k = R.choice([1, 1, 3])
    for j in range(k):
        x = 0 if j == 0 else (W * 0.3 if j == 1 else -W * 0.3); L = R.uniform(0.6, 1.1) * (1 if j == 0 else 0.7)
        bpy.ops.mesh.primitive_cone_add(vertices=R.choice([4, 6, 8]), radius1=0.09, depth=L); c = bpy.context.active_object; c.location = (x, -D * 0.45, vz + L * 0.45); c.rotation_euler = (math.radians(R.uniform(-25, -5)), 0, math.radians(-x * 30)); c["부품"] = "뿔"; objs.append(c)
    if R.random() < 0.6:
        for s in (-1, 1): bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.03, depth=R.uniform(0.6, 1.0)); a = bpy.context.active_object; a.location = (s * W * 0.5, 0, vz + 0.45); a.rotation_euler = (0, math.radians(s * R.uniform(25, 45)), 0); a["부품"] = "안테나"; objs.append(a)
    for o in objs:
        o.color = 색[o["부품"]] + (1,)
        for p in o.data.polygons: p.use_smooth = False
    return objs

def 툰재질():
    m = bpy.data.materials.new("툰"); m.use_nodes = True; nt = m.node_tree
    for x in list(nt.nodes): nt.nodes.remove(x)
    d = nt.nodes.new("ShaderNodeBsdfDiffuse"); s2r = nt.nodes.new("ShaderNodeShaderToRGB"); cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"
    cr.color_ramp.elements[0].color = (0.55, 0.55, 0.6, 1); cr.color_ramp.elements[1].position = 0.12; cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    oi = nt.nodes.new("ShaderNodeObjectInfo"); mul = nt.nodes.new("ShaderNodeMixRGB"); mul.blend_type = "MULTIPLY"; mul.inputs[0].default_value = 1
    e = nt.nodes.new("ShaderNodeEmission"); out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(d.outputs[0], s2r.inputs[0]); nt.links.new(s2r.outputs[0], cr.inputs[0]); nt.links.new(cr.outputs[0], mul.inputs[1]); nt.links.new(oi.outputs["Color"], mul.inputs[2]); nt.links.new(mul.outputs[0], e.inputs[0]); nt.links.new(e.outputs[0], out.inputs[0]); return m
def 흰재질():
    m = bpy.data.materials.new("흰"); m.use_nodes = True; nt = m.node_tree
    for x in list(nt.nodes): nt.nodes.remove(x)
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (1, 1, 1, 1); out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], out.inputs[0]); return m

a = sys.argv[sys.argv.index("--") + 1:]; s0, cnt = int(a[0]), int(a[1]); 기록 = {}
for seed in range(s0, s0 + cnt):
    sc = H.scene(res=(640, 640), transparent=False)
    try: sc.render.engine = "BLENDER_EEVEE"
    except TypeError: sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.world.use_nodes = False; sc.world.color = (1, 1, 1); sc.view_settings.view_transform = "Standard"
    objs = 짓기(seed)
    sun = bpy.data.objects.new("해", bpy.data.lights.new("해", "SUN")); sc.collection.objects.link(sun); sun.rotation_euler = (math.radians(55), math.radians(-20), math.radians(-35)); sun.data.energy = 3
    tm, wm = 툰재질(), 흰재질()
    sc.render.use_freestyle = True; vl = sc.view_layers[0]; vl.use_freestyle = True; fs = vl.freestyle_settings; fs.crease_angle = math.radians(140)
    for 각, (yaw, pitch) in {"a": (25, 10), "b": (60, 5)}.items():
        H.look((0, 0, 0.05), yaw, pitch, 2.6, dist=10)
        for ls in list(fs.linesets): fs.linesets.remove(ls)
        ls = fs.linesets.new("선"); ls.select_silhouette = ls.select_border = ls.select_crease = ls.select_contour = ls.select_external_contour = True; ls.linestyle.color = (0.05, 0.05, 0.08); ls.linestyle.thickness = 2.0
        for o in objs: o.data.materials.clear(); o.data.materials.append(tm)
        H.shot(os.path.join(O, f"d{seed:03d}_{각}_입력.png"))
        for ls in list(fs.linesets): fs.linesets.remove(ls)
        l1 = fs.linesets.new("꺾임"); l1.select_silhouette = l1.select_border = l1.select_contour = l1.select_external_contour = False; l1.select_crease = True; l1.linestyle.color = (0.1, 0.4, 1.0); l1.linestyle.thickness = 2.4
        l2 = fs.linesets.new("외곽가림"); l2.select_crease = False; l2.select_silhouette = l2.select_border = l2.select_contour = l2.select_external_contour = True; l2.linestyle.color = (0.95, 0.15, 0.15); l2.linestyle.thickness = 2.4
        for o in objs: o.data.materials.clear(); o.data.materials.append(wm)
        H.shot(os.path.join(O, f"d{seed:03d}_{각}_선정답.png"))
        # 부품 이름 지도: Workbench 평면색
        sc.render.use_freestyle = False; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"; sh.color_type = "OBJECT"; sh.show_cavity = False
        sav = {o.name: tuple(o.color) for o in objs}
        for o in objs: i = 부품.index(o["부품"]); o.color = (((i + 1) * 24) / 255.0, 0.5, 0.5, 1)
        H.shot(os.path.join(O, f"d{seed:03d}_{각}_부품정답.png"))
        for o in objs: o.color = sav[o.name]
        try: sc.render.engine = "BLENDER_EEVEE"
        except TypeError: sc.render.engine = "BLENDER_EEVEE_NEXT"
        sc.render.use_freestyle = True
    기록[seed] = {p: sum(1 for o in objs if o["부품"] == p) for p in 부품}
    print("ok", seed, 기록[seed])
json.dump({"부품": 부품, "씨앗": 기록}, open(os.path.join(O, f"기록_{s0}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
