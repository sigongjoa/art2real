# -*- coding: utf-8 -*-
"""더미 5판 — 선파츠 칸에서 지은 머리 (준비: 더미머리5_칸.py → 더미머리5_칸.out.json).
부품 = 정면 윤곽을 앞뒤로 민 판 ∩ 같은 이름 옆 윤곽을 좌우로 민 판(정면 높이로 늘임). 윤곽은 차이킨 곡선 · 110° 보다 뾰족한 꼭짓점만 각.
blender -b -P 더미머리5.py -- <흔들기씨앗(0 = 그대로)> ...   흔들기 = 부품 크기 ±8 % (칸 값 둘레만)."""
import bpy, bmesh, math, random, os, sys, json
from mathutils import Vector
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
HERE = os.path.dirname(os.path.abspath(__file__)); J = json.load(open(os.path.join(HERE, "더미머리5_칸.out.json"), encoding="utf-8"))
O = r"G:\art2real\원화3d\out\오메가몬2\지표\더미머리5"; os.makedirs(O, exist_ok=True)
S = 0.02; CX = J["정면가운데"]
def X(u): return (u - CX) * S
def Z(v): return (60 - v) * S

def 곡선(pts, n=2, 각도=110):
    P = [Vector(p) for p in pts]; m = len(P); 각 = set()
    for i in range(m):
        a, b = P[i - 1] - P[i], P[(i + 1) % m] - P[i]
        if a.length and b.length and math.degrees(a.angle(b)) < 각도: 각.add(i)
    Q = [(p, i in 각) for i, p in enumerate(P)]
    for _ in range(n):
        R = []
        for i, (a, sa) in enumerate(Q):
            b, sb = Q[(i + 1) % len(Q)]
            R.append((a, True) if sa else (a * 0.75 + b * 0.25, False))
            if not sb: R.append((a * 0.25 + b * 0.75, False))
        Q = R
    return [tuple(p) for p, _ in Q]
def 프리즘(이름, prof, 축, lo, hi):
    """prof: 2D 점. 축 'y' = (x,z) 윤곽을 y 로 민다 · 'x' = (y,z) 윤곽을 x 로 민다."""
    bm = bmesh.new(); mk = (lambda a, b, d: (a, d, b)) if 축 == "y" else (lambda a, b, d: (d, a, b))
    f = bm.faces.new([bm.verts.new(mk(a, b, lo)) for a, b in prof])
    ex = bmesh.ops.extrude_face_region(bm, geom=[f]); dv = (0, hi - lo, 0) if 축 == "y" else (hi - lo, 0, 0)
    bmesh.ops.translate(bm, vec=dv, verts=[e for e in ex["geom"] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.triangulate(bm, faces=[g for g in bm.faces if len(g.verts) > 4], ngon_method="BEAUTY"); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(이름); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(이름, me); bpy.context.scene.collection.objects.link(o); return o
def 색(h): h = h.lstrip("#"); return tuple(((int(h[i:i + 2], 16) / 255) ** 2.2) for i in (0, 2, 4))

def 짓기(seed):
    R = random.Random(seed); P = []
    for p in J["부품"]:
        k = 1 + (R.uniform(-0.08, 0.08) if seed else 0)
        zlo, zhi = p["z범위"]; zc = (zlo + zhi) / 2
        if p["옆"]: ylo, yhi = p["옆"]["y범위"]
        else: ylo, yhi = -2, 2
        yc = (ylo + yhi) / 2
        조각 = []
        for c in p["앞윤곽"]:
            xs = [q[0] for q in c]; prof = 곡선([(X(cx_ + (q[0] - cx_) * k) if False else X(q[0]), Z(zc + (q[1] - zc) * k)) for q in c for cx_ in [sum(xs) / len(xs)]])
            o = 프리즘(p["이름"], prof, "y", (ylo - 0.5) * S, (yhi + 0.5) * S)
            if p["옆"]:
                side = 곡선([((yc + (y - yc) * k) * S, Z(zhi - t * (zhi - zlo))) for y, t in p["옆"]["yt"]])
                x0, x1 = X(min(xs)) - 0.05, X(max(xs)) + 0.05; cut = 프리즘("자르개", side, "x", x0, x1)
                m = o.modifiers.new("옆", "BOOLEAN"); m.operation = "INTERSECT"; m.object = cut; m.solver = "EXACT"
                bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=m.name); bpy.data.objects.remove(cut)
                if len(o.data.polygons) == 0: o.data = 프리즘(p["이름"], prof, "y", (yc - 1) * S, (yc + 1) * S).data; o["빈교집합"] = 1
            조각.append(o)
        if len(조각) > 1:
            bpy.ops.object.select_all(action="DESELECT")
            for o in 조각: o.select_set(True)
            bpy.context.view_layer.objects.active = 조각[0]; bpy.ops.object.join()
        o = 조각[0]; o["부품"] = p["이름"]; o.color = 색(p["색"]) + (1,)
        for f in o.data.polygons: f.use_smooth = True
        o.data.use_auto_smooth = True; o.data.auto_smooth_angle = math.radians(40)
        조인트 = "핀" if p["이름"].startswith(("뿔", "안테나")) else ("힌지" if p["이름"].startswith(("미늘", "볼날개")) else "고정")
        bx, bz = p.get("붙는자리", [CX, zc])
        P.append(dict(o=o, 이름=p["이름"], 쪽=p["쪽"], 부모=p["부모"], 조인트=조인트, 중심=Vector((X(sum(q[0] for c in p["앞윤곽"] for q in c) / sum(len(c) for c in p["앞윤곽"])), yc * S, Z(zc)))))
        P[-1]["위치"] = Vector((X(bx), 0, Z(bz)))
    for p in P:
        p["위치"].y = (p["중심"].y + (P[p["부모"]]["중심"].y if p["부모"] >= 0 else p["중심"].y)) / 2
    return P

def 재질(툰):
    m = bpy.data.materials.new("툰" if 툰 else "흰"); m.use_nodes = True; nt = m.node_tree
    for x in list(nt.nodes): nt.nodes.remove(x)
    e = nt.nodes.new("ShaderNodeEmission"); out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], out.inputs[0])
    if not 툰: e.inputs[0].default_value = (1, 1, 1, 1); return m
    d = nt.nodes.new("ShaderNodeBsdfDiffuse"); s2r = nt.nodes.new("ShaderNodeShaderToRGB"); cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"
    cr.color_ramp.elements[0].color = (0.6, 0.6, 0.65, 1); cr.color_ramp.elements[1].position = 0.12; cr.color_ramp.elements[1].color = (1, 1, 1, 1)
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
def 막대(a, b, r, col, 이름):
    v = b - a
    if v.length < 1e-3: return None
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=r, depth=v.length, location=(a + b) / 2); o = bpy.context.active_object
    o.rotation_euler = v.to_track_quat("Z", "Y").to_euler(); o["부품"] = 이름; o.color = col + (1,); return o

for seed in [int(a) for a in sys.argv[sys.argv.index("--") + 1:]]:
    sc = H.scene(res=(700, 700), transparent=False); 이브(); sc.world.use_nodes = False; sc.world.color = (1, 1, 1); sc.view_settings.view_transform = "Standard"
    P = 짓기(seed); objs = [p["o"] for p in P]
    sun = bpy.data.objects.new("해", bpy.data.lights.new("해", "SUN")); sc.collection.objects.link(sun); sun.rotation_euler = (math.radians(55), math.radians(-20), math.radians(-35)); sun.data.energy = 3
    tm, wm = 재질(True), 재질(False); sc.render.use_freestyle = True; vl = sc.view_layers[0]; vl.use_freestyle = True; fs = vl.freestyle_settings; fs.crease_angle = math.radians(140)
    def 입힘(os_, m):
        for o in os_: o.data.materials.clear(); o.data.materials.append(m)
    ctr = Vector((0, 0, Z(55))); 입힘(objs, tm); 선(fs, False)
    for nm, (yaw, pitch) in {"정면": (0, 0), "옆": (-90, 0), "34": (30, 8)}.items():
        H.look(tuple(ctr), yaw, pitch, 2.4, dist=10); H.shot(os.path.join(O, f"s{seed}_{nm}_입력.png"))
    H.look(tuple(ctr), 30, 8, 2.4, dist=10); 선(fs, True); 입힘(objs, wm); H.shot(os.path.join(O, f"s{seed}_34_선정답.png"))
    # 분해도: 돔 중심에서 부품 중심 쪽으로 0.45 (누적 없음)
    c0 = P[[i for i, p in enumerate(P) if p["부모"] < 0][0]]["중심"]; extra = []
    for p in P:
        d = p["중심"] - c0; d = d.normalized() * 0.45 if d.length > 1e-3 else Vector((0, 0, 0)); p["o"].location += d; p["펼침"] = d
    for p in P:
        if p["부모"] < 0: continue
        a = p["위치"] + P[p["부모"]]["펼침"]; b = p["위치"] + p["펼침"]
        l = 막대(a, b, 0.006, (0.45, 0.45, 0.5), "이음")
        if l: extra.append(l)
        if p["조인트"] != "고정":
            j = 막대(b - Vector((0, 0.03, 0)), b + Vector((0, 0.03, 0)), 0.025, (1.0, 0.45, 0.1), "조인트"); extra.append(j)
    입힘(objs + extra, tm); 선(fs, False); H.look(tuple(ctr), 30, 8, 3.4, dist=12); H.shot(os.path.join(O, f"s{seed}_분해_입력.png"))
    json.dump([{"번호": i, "부품": p["이름"], "쪽": p["쪽"], "부모": p["부모"], "조인트": p["조인트"], "위치": [round(v, 3) for v in p["위치"]]} for i, p in enumerate(P)],
              open(os.path.join(O, f"s{seed}_연결.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("ok", seed, len(P), "부품 · 빈 교집합", [p["이름"] for p in P if p["o"].get("빈교집합")])
