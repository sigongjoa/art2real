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
    """2판(10-02 「시작은 나쁘지 않아」 뒤): 머리 모양 언어 — 속머리는 숨기고 돔이 위·옆·뒤를 감쌈 · 차양은 돔 앞 테 · 미늘은 아래로 갈수록 앞(부리꼴) · 볼날개는 돔 옆에서 뒤로.
    ⚠ 비율 · 모양은 내가 지어낸 범위다(원화 칸에서 읽지 않았다 — 10-02 사용자 지적)."""
    R = random.Random(seed); objs = []
    W = R.uniform(0.85, 1.05); Hh = R.uniform(0.95, 1.1); D = R.uniform(0.95, 1.15)
    objs.append(상자("속머리", (W * 0.9, D * 0.9, Hh * 0.9), (0, 0.1, -0.2)))                       # 안에 숨김
    seg = R.choice([8, 10, 12]); bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=R.choice([5, 6]), radius=1)
    d = bpy.context.active_object; bm = bmesh.new(); bm.from_mesh(d.data)
    cut = R.uniform(-0.35, -0.15)                                                                      # 돔이 내려오는 깊이(옆·뒤)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < cut or (v.co.y < -0.55 and v.co.z < 0.25)], context="VERTS")   # 앞은 얼굴 자리 비움
    bm.to_mesh(d.data); bm.free(); d.scale = (W * 0.62, D * 0.7, Hh * 0.62); d.location = (0, 0.1, 0.12)
    sd = d.modifiers.new("두께", "SOLIDIFY"); sd.thickness = 0.07; d["부품"] = "투구 돔"; objs.append(d)
    va = R.uniform(15, 32); vz = R.uniform(0.2, 0.3); vy = -D * 0.6
    for s in (-1, 1): objs.append(판("차양", W * 0.36, 0.13, 0.16, (s * W * 0.17, vy, vz), (R.uniform(20, 40), 0, -s * va)))
    ez = vz - R.uniform(0.15, 0.2); ew = R.uniform(0.2, 0.28)
    for s in (-1, 1):
        objs.append(판("눈구멍 판", ew, 0.15, 0.05, (s * W * 0.2, vy + 0.12, ez), (0, 0, -s * R.uniform(10, 25))))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.05); e = bpy.context.active_object; e.location = (s * W * 0.2, vy + 0.08, ez); e["부품"] = "눈"; objs.append(e)
    n = R.randint(2, 4); z = ez - 0.13; fw = W * 0.46; ang = R.uniform(28, 42); fwd = vy + 0.05; step = R.uniform(0.05, 0.1)
    for i in range(n):
        h = R.uniform(0.11, 0.16); fwd -= step                                                         # 아래로 갈수록 앞으로
        for s in (-1, 1): objs.append(판("미늘", fw * 0.55, h, 0.07, (s * fw * 0.23, fwd, z), (R.uniform(-20, 0), 0, -s * ang)))
        z -= h * 0.75; fw *= R.uniform(0.62, 0.8)
    for s in (-1, 1):
        objs.append(판("볼날개", 0.08, Hh * R.uniform(0.35, 0.5), D * R.uniform(0.45, 0.7), (s * W * 0.62, -D * 0.2, ez - 0.12), (R.uniform(-25, -5), 0, s * R.uniform(15, 35))))
    k = R.choice([1, 1, 3])
    for j in range(k):
        x = 0 if j == 0 else (W * 0.28 if j == 1 else -W * 0.28); L = R.uniform(0.7, 1.2) * (1 if j == 0 else 0.6)
        bpy.ops.mesh.primitive_cone_add(vertices=R.choice([4, 6]), radius1=0.09, depth=L); c = bpy.context.active_object; c.location = (x, vy + 0.1, vz + 0.1 + L * 0.45); c.rotation_euler = (math.radians(R.uniform(-30, -10)), 0, math.radians(-x * 30)); c["부품"] = "뿔"; objs.append(c)
    if R.random() < 0.6:
        for s in (-1, 1): bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.03, depth=R.uniform(0.6, 1.0)); a_ = bpy.context.active_object; a_.location = (s * W * 0.42, -0.1, vz + 0.4); a_.rotation_euler = (0, math.radians(s * R.uniform(25, 45)), 0); a_["부품"] = "안테나"; objs.append(a_)
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
