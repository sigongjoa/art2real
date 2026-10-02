# -*- coding: utf-8 -*-
"""메카 머리 더미 3판 — 도형 낱말 늘리기 + 연결 구조 · 조인트 (10-02 사용자 「여러 도형으로 · 연결 구조랑 조인트도 고려」).
blender -b -P 더미머리3.py -- <시작씨앗> <개수>
도형: 모서리 깎은 상자 · 쐐기 · 좁아지는 판 · 윤곽 판(무작위 다각형) · 홈 판(불리언 슬릿) · 원뿔 · 칼날 뿔.
연결: 부품마다 부모 · 붙는 자리 · 조인트(볼 · 핀 · 힌지 · 고정). 뿌리 = 속머리, 목은 볼.
렌더: 조립 툰 · 조립 선 정답 · 조립 부품 정답 · 분해도(부품을 부모에서 띄우고 조인트 · 이음선 표시). 정답 `d###_연결.json`."""
import bpy, bmesh, math, random, os, sys, json
from mathutils import Vector
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
O = os.path.join(r"G:\art2real\원화3d\out\오메가몬2\지표", "더미머리3"); os.makedirs(O, exist_ok=True)
부품 = ["속머리", "투구 돔", "차양", "눈구멍 판", "눈", "미늘", "볼날개", "뿔", "안테나"]
흰 = (0.9, 0.91, 0.96)
색 = {"속머리": (0.12, 0.12, 0.15), "투구 돔": 흰, "차양": 흰, "눈구멍 판": (0.08, 0.08, 0.1), "눈": (0.25, 0.55, 0.95),
     "미늘": 흰, "볼날개": 흰, "뿔": (0.9, 0.82, 0.35), "안테나": (0.85, 0.75, 0.3), "조인트": (1.0, 0.45, 0.1), "이음": (0.45, 0.45, 0.5)}

def _obj(mesh, 이름):
    o = bpy.data.objects.new(이름, mesh); bpy.context.scene.collection.objects.link(o); o["부품"] = 이름; return o
def 프리즘(이름, prof, t, loc, rot=(0, 0, 0)):
    """x-z 평면 윤곽을 y 로 t 만큼 민 판."""
    bm = bmesh.new(); vs = [bm.verts.new((u, -t / 2, v)) for u, v in prof]; f = bm.faces.new(vs)
    ex = bmesh.ops.extrude_face_region(bm, geom=[f]); bmesh.ops.translate(bm, vec=(0, t, 0), verts=[e for e in ex["geom"] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(이름); bm.to_mesh(me); bm.free()
    o = _obj(me, 이름); o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]; return o
def 사다리(w, h, k): return [(-w / 2, -h / 2), (w / 2, -h / 2), (w * k / 2, h / 2), (-w * k / 2, h / 2)]
def 쐐기(w, h): return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2)]
def 윤곽(R, w, h, n):
    a = sorted(R.uniform(0, 2 * math.pi) for _ in range(n)); return [(math.cos(t) * w / 2 * R.uniform(0.7, 1), math.sin(t) * h / 2 * R.uniform(0.7, 1)) for t in a]
def 깎은상자(이름, 크기, loc, rot=(0, 0, 0), 깎기=0.04):
    bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.active_object; o.name = 이름; o["부품"] = 이름; o.scale = 크기; o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]
    bpy.ops.object.transform_apply(scale=True); b = o.modifiers.new("깎기", "BEVEL"); b.width = 깎기; b.segments = 1; return o
def 슬릿(o, 개수, 폭, 높이):
    """판에 가로 홈을 판다(적용 후 자르개 삭제)."""
    bpy.context.view_layer.update(); c = o.matrix_world.translation
    for i in range(개수):
        bpy.ops.mesh.primitive_cube_add(size=1); k = bpy.context.active_object; k.scale = (폭, 1, 높이); k.rotation_euler = o.rotation_euler; k.location = c + Vector((0, 0, (i - (개수 - 1) / 2) * 높이 * 2.5))
        m = o.modifiers.new("홈", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = k; m.solver = "EXACT"
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=m.name); bpy.data.objects.remove(k)

def 짓기(seed):
    R = random.Random(seed); P = []   # P[i] = {o, 이름, 부모, 조인트, 위치, 축, 펼침}
    def 붙이기(o, 부모, 조인트, 위치, 축=(0, 0, 1), 펼침=(0, 0, 0)):
        P.append(dict(o=o, 이름=o["부품"], 부모=부모, 조인트=조인트, 위치=Vector(위치), 축=Vector(축).normalized(), 펼침=Vector(펼침))); return len(P) - 1
    W = R.uniform(0.85, 1.05); Hh = R.uniform(0.95, 1.1); D = R.uniform(0.95, 1.15)
    root = 붙이기(깎은상자("속머리", (W * 0.78, D * 0.8, Hh * 0.55), (0, 0.12, 0), 깎기=0.06), -1, "볼", (0, 0.15, -Hh * 0.3), (0, 0, 1))
    # 투구 돔: 다각 반구 껍질 · 속머리 위에 다보 핀
    bpy.ops.mesh.primitive_uv_sphere_add(segments=R.choice([8, 10, 12]), ring_count=R.choice([5, 6]), radius=1); d = bpy.context.active_object; d.name = "투구 돔"; d["부품"] = "투구 돔"
    bm = bmesh.new(); bm.from_mesh(d.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.55 or (v.co.y < -0.5 and v.co.z < 0.3)], context="VERTS"); bm.to_mesh(d.data); bm.free()
    d.scale = (W * 0.66, D * 0.75, Hh * 0.66); d.location = (0, 0.1, 0.1); d.modifiers.new("두께", "SOLIDIFY").thickness = 0.07
    dome = 붙이기(d, root, "핀", (0, 0.12, Hh * 0.27), (0, 0, 1), (0, 0.15, 0.45))
    # 차양: 쐐기 · 좁아지는 판 · 깎은 상자 중 하나 · 돔 앞 테에 핀
    va = R.uniform(15, 32); vz = R.uniform(0.2, 0.3); vy = -D * 0.6; 형 = R.choice(["쐐기", "사다리", "깎은"]); visors = []
    for s in (-1, 1):
        loc = (s * W * 0.17, vy, vz); rot = (R.uniform(20, 40), 0, -s * va)
        o = 프리즘("차양", 쐐기(W * 0.38, 0.16) if 형 == "쐐기" else 사다리(W * 0.38, 0.14, 0.6), 0.16, loc, rot) if 형 != "깎은" else 깎은상자("차양", (W * 0.36, 0.16, 0.13), loc, rot)
        if 형 == "쐐기" and s < 0: o.scale.x = -1
        visors.append(붙이기(o, dome, "핀", (s * W * 0.12, vy + 0.08, vz), (0, 1, 0), (s * 0.15, -0.35, 0.1)))
    # 눈구멍 판(홈 판 가능) + 눈
    ez = vz - R.uniform(0.15, 0.2); ew = R.uniform(0.2, 0.28)
    for s in (-1, 1):
        o = 프리즘("눈구멍 판", 사다리(ew, 0.16, R.uniform(0.7, 1.0)), 0.05, (s * W * 0.2, vy + 0.12, ez), (0, 0, -s * R.uniform(10, 25)))
        ep = 붙이기(o, root, "고정", (s * W * 0.2, vy + 0.15, ez), (0, 1, 0), (0, -0.3, 0))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.05); e = bpy.context.active_object; e.name = "눈"; e["부품"] = "눈"; e.location = (s * W * 0.2, vy + 0.08, ez)
        붙이기(e, ep, "고정", e.location, (0, 1, 0), (0, -0.12, 0))
    # 미늘: 좁아지는 V 판 사슬 · 위 테에 힌지(x 축) · 아래로 갈수록 앞
    n = R.randint(2, 4); z = ez - 0.13; fw = W * 0.46; ang = R.uniform(28, 42); fwd = vy + 0.05; step = R.uniform(0.05, 0.1); par = root; 홈 = R.random() < 0.5
    for i in range(n):
        h = R.uniform(0.12, 0.17); fwd -= step; cur = []
        for s in (-1, 1):
            o = 프리즘("미늘", 사다리(fw * 0.55, h, R.uniform(0.75, 1.0)), 0.07, (s * fw * 0.23, fwd, z), (R.uniform(-20, 0), 0, -s * ang))
            if 홈 and i == 0: 슬릿(o, 2, fw * 0.35, 0.018)
            cur.append(붙이기(o, par, "힌지", (s * fw * 0.23, fwd + 0.03, z + h / 2), (1, 0, 0), (0, -0.22, -0.12)))
        par = cur[0]; z -= h * 0.75; fw *= R.uniform(0.62, 0.8)
    # 볼날개: 윤곽 판 · 돔 옆 앞쪽 힌지(z 축) · 뒤로 벌어짐
    wp = 윤곽(R, D * R.uniform(0.55, 0.75), Hh * R.uniform(0.4, 0.55), R.randint(5, 7)); wa = R.uniform(12, 30); wt = R.uniform(-20, -5)
    for s in (-1, 1):
        o = 프리즘("볼날개", wp, 0.08, (s * W * 0.64, -D * 0.05, ez - 0.1), (wt, 0, -s * wa)); o.rotation_euler.z += math.radians(s * 90)  # 판을 옆면으로 세움
        if s < 0: o.scale.x = -1
        붙이기(o, dome, "힌지", (s * W * 0.6, -D * 0.3, ez - 0.05), (0, 0, 1), (s * 0.4, 0, 0))
    # 뿔: 원뿔 또는 칼날(얇은 쐐기) · 차양 사이에 꽂는 핀
    k = R.choice([1, 1, 3]); 칼 = R.random() < 0.5
    for j in range(k):
        x = 0 if j == 0 else (W * 0.28 if j == 1 else -W * 0.28); L = R.uniform(0.7, 1.2) * (1 if j == 0 else 0.6); tilt = R.uniform(-30, -10)
        base = Vector((x, vy + 0.1, vz + 0.1)); dirv = Vector((0, math.sin(math.radians(tilt)), math.cos(math.radians(tilt))))
        if 칼: o = 프리즘("뿔", [(-0.08, 0), (0.08, 0), (0.0, L)], 0.05, base, (0, 0, 90)); o.rotation_euler = (math.radians(tilt), 0, math.radians(90 - x * 30))
        else:
            bpy.ops.mesh.primitive_cone_add(vertices=R.choice([4, 6]), radius1=0.09, depth=L); o = bpy.context.active_object; o.name = "뿔"; o["부품"] = "뿔"
            o.location = base + dirv * L / 2; o.rotation_euler = (math.radians(tilt), 0, math.radians(-x * 30))
        붙이기(o, visors[0] if j == 0 else dome, "핀", base, dirv, dirv * 0.35)
    if R.random() < 0.6:
        for s in (-1, 1):
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.03, depth=R.uniform(0.6, 1.0)); a_ = bpy.context.active_object; a_.name = "안테나"; a_["부품"] = "안테나"
            a_.location = (s * W * 0.42, -0.1, vz + 0.4); a_.rotation_euler = (0, math.radians(s * R.uniform(25, 45)), 0)
            붙이기(a_, dome, "볼", (s * W * 0.32, -0.1, vz + 0.18), (0, 0, 1), (s * 0.2, 0, 0.25))
    for p in P:
        p["o"].color = 색[p["이름"]] + (1,)
        for f in p["o"].data.polygons: f.use_smooth = False
    return P

def 조인트도형(p):
    """조인트를 실물 모양으로: 볼 = 구 · 핀 = 막대 · 힌지 = 축 막대 · 고정 = 없음."""
    if p["조인트"] == "고정": return None
    if p["조인트"] == "볼": bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.065, location=p["위치"])
    else:
        L, r = (0.22, 0.025) if p["조인트"] == "힌지" else (0.14, 0.03)
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=r, depth=L, location=p["위치"]); bpy.context.active_object.rotation_euler = p["축"].to_track_quat("Z", "Y").to_euler()
    j = bpy.context.active_object; j["부품"] = "조인트"; j.color = 색["조인트"] + (1,); return j
def 이음선(a, b):
    v = b - a
    if v.length < 1e-3: return None
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.008, depth=v.length, location=(a + b) / 2); o = bpy.context.active_object
    o.rotation_euler = v.to_track_quat("Z", "Y").to_euler(); o["부품"] = "이음"; o.color = 색["이음"] + (1,); return o

def 재질(툰):
    m = bpy.data.materials.new("툰" if 툰 else "흰"); m.use_nodes = True; nt = m.node_tree
    for x in list(nt.nodes): nt.nodes.remove(x)
    e = nt.nodes.new("ShaderNodeEmission"); out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], out.inputs[0])
    if not 툰: e.inputs[0].default_value = (1, 1, 1, 1); return m
    d = nt.nodes.new("ShaderNodeBsdfDiffuse"); s2r = nt.nodes.new("ShaderNodeShaderToRGB"); cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"
    cr.color_ramp.elements[0].color = (0.55, 0.55, 0.6, 1); cr.color_ramp.elements[1].position = 0.12; cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    oi = nt.nodes.new("ShaderNodeObjectInfo"); mul = nt.nodes.new("ShaderNodeMixRGB"); mul.blend_type = "MULTIPLY"; mul.inputs[0].default_value = 1
    nt.links.new(d.outputs[0], s2r.inputs[0]); nt.links.new(s2r.outputs[0], cr.inputs[0]); nt.links.new(cr.outputs[0], mul.inputs[1]); nt.links.new(oi.outputs["Color"], mul.inputs[2]); nt.links.new(mul.outputs[0], e.inputs[0]); return m
def 이브():
    try: bpy.context.scene.render.engine = "BLENDER_EEVEE"
    except TypeError: bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
def 선(fs, 정답):
    for ls in list(fs.linesets): fs.linesets.remove(ls)
    if not 정답:
        ls = fs.linesets.new("선"); ls.select_silhouette = ls.select_border = ls.select_crease = ls.select_contour = ls.select_external_contour = True; ls.linestyle.color = (0.05, 0.05, 0.08); ls.linestyle.thickness = 2.0; return
    l1 = fs.linesets.new("꺾임"); l1.select_silhouette = l1.select_border = l1.select_contour = l1.select_external_contour = False; l1.select_crease = True; l1.linestyle.color = (0.1, 0.4, 1.0); l1.linestyle.thickness = 2.4
    l2 = fs.linesets.new("외곽가림"); l2.select_crease = False; l2.select_silhouette = l2.select_border = l2.select_contour = l2.select_external_contour = True; l2.linestyle.color = (0.95, 0.15, 0.15); l2.linestyle.thickness = 2.4

a = sys.argv[sys.argv.index("--") + 1:]; s0, cnt = int(a[0]), int(a[1])
for seed in range(s0, s0 + cnt):
    sc = H.scene(res=(640, 640), transparent=False); 이브(); sc.world.use_nodes = False; sc.world.color = (1, 1, 1); sc.view_settings.view_transform = "Standard"
    P = 짓기(seed)
    sun = bpy.data.objects.new("해", bpy.data.lights.new("해", "SUN")); sc.collection.objects.link(sun); sun.rotation_euler = (math.radians(55), math.radians(-20), math.radians(-35)); sun.data.energy = 3
    tm, wm = 재질(True), 재질(False); sc.render.use_freestyle = True; vl = sc.view_layers[0]; vl.use_freestyle = True; fs = vl.freestyle_settings; fs.crease_angle = math.radians(140)
    objs = [p["o"] for p in P]
    def 입힘(os_, m):
        for o in os_: o.data.materials.clear(); o.data.materials.append(m)
    H.look((0, 0, 0.05), 25, 10, 2.6, dist=10)
    선(fs, False); 입힘(objs, tm); H.shot(os.path.join(O, f"d{seed:03d}_조립_입력.png"))
    선(fs, True); 입힘(objs, wm); H.shot(os.path.join(O, f"d{seed:03d}_조립_선정답.png"))
    sc.render.use_freestyle = False; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"; sh.color_type = "OBJECT"; sh.show_cavity = False
    sav = {o.name: tuple(o.color) for o in objs}
    for p in P: i = 부품.index(p["이름"]); p["o"].color = (((i + 1) * 24) / 255.0, 0.5, 0.5, 1)
    H.shot(os.path.join(O, f"d{seed:03d}_조립_부품정답.png"))
    for o in objs: o.color = sav[o.name]
    # 분해도: 자식은 부모 펼침을 물려받는다
    tot = []
    for p in P: tot.append(p["펼침"] + (tot[p["부모"]] if p["부모"] >= 0 else Vector()))
    extra = []
    for i, p in enumerate(P):
        p["o"].location = p["o"].location + tot[i]; j = 조인트도형(p)
        if j: j.location = j.location + tot[i]; extra.append(j)
        if p["부모"] >= 0:
            l = 이음선(p["위치"] + tot[p["부모"]], p["위치"] + tot[i])
            if l: extra.append(l)
    이브(); sc.render.use_freestyle = True; 선(fs, False); 입힘(objs + extra, tm)
    H.look((0, -0.1, 0.25), 30, 12, 3.8, dist=12); H.shot(os.path.join(O, f"d{seed:03d}_분해_입력.png"))
    json.dump([{"번호": i, "부품": p["이름"], "부모": p["부모"], "조인트": p["조인트"], "위치": [round(v, 3) for v in p["위치"]], "축": [round(v, 3) for v in p["축"]]} for i, p in enumerate(P)],
              open(os.path.join(O, f"d{seed:03d}_연결.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("ok", seed, len(P), "부품", sum(1 for p in P if p["조인트"] != "고정"), "조인트")
