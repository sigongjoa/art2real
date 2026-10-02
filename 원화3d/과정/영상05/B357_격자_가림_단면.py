import bpy, bmesh, sys, os, math, mathutils
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
OUT = r"G:\art2real\out\영상05\B357"
def sgn_pow(x, e): return math.copysign(abs(x) ** e, x)
def superq(name, e1, e2, a=(1,1,1), n=48, loc=(0,0,0), color=(0.85,0.85,0.88,1)):
    vs, fs = [], []
    for i in range(n + 1):
        eta = -math.pi/2 + math.pi * i / n
        for j in range(n):
            w = -math.pi + 2*math.pi * j / n
            ce, se, cw, sw = math.cos(eta), math.sin(eta), math.cos(w), math.sin(w)
            vs.append((a[0]*sgn_pow(ce,e1)*sgn_pow(cw,e2), a[1]*sgn_pow(ce,e1)*sgn_pow(sw,e2), a[2]*sgn_pow(se,e1)))
    for i in range(n):
        for j in range(n):
            p = i*n + j; q = i*n + (j+1) % n
            fs.append((p, q, q+n, p+n))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.location = loc; o.color = color
    for p in me.polygons: p.use_smooth = True
    return o
def wb(sc):
    sc.render.engine = "BLENDER_WORKBENCH"; sc.view_settings.view_transform = "Standard"
    sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_cavity = True
# ---------- B3 초이차 격자 ----------
sc = H.scene(res=(1200, 1200)); wb(sc)
E = [0.2, 0.5, 1.0, 1.5, 2.0]
for i, e1 in enumerate(E):
    for j, e2 in enumerate(E):
        superq("sq%d%d" % (i, j), e1, e2, loc=(j*2.6 - 5.2, 0, -(i*2.6 - 5.2)))
H.look((0,0,0), 25, 20, ortho=14); H.shot(os.path.join(OUT, "B3_grid.png"))
# ---------- B5 가림 뒤 세 가지 ----------
sc = H.scene(res=(1500, 700)); wb(sc)
def arm(x0, kind):
    # 팔 = z 축 따라 반지름 r(z): 가운데(가림 뒤)만 kind 에 따라 다름
    n, m = 64, 40; vs = []; fs = []
    for i in range(n + 1):
        z = -3 + 6 * i / n; t = max(0.0, 1 - abs(z) / 1.0)   # |z|<1 가림 구간
        r = 0.6 + {"곧게": 0, "가늘게": -0.38, "굵게": 0.55}[kind] * math.sin(t * math.pi / 2) ** 2
        for j in range(m):
            a = 2 * math.pi * j / m; vs.append((x0 + r * math.cos(a), r * math.sin(a), z))
    for i in range(n):
        for j in range(m):
            p = i*m + j; q = i*m + (j+1) % m; fs.append((p, q, q+m, p+m))
    me = bpy.data.meshes.new(kind); me.from_pydata(vs, [], fs); me.update()
    o = bpy.data.objects.new(kind, me); sc.collection.objects.link(o); o.color = (0.85,0.85,0.88,1)
    for p in me.polygons: p.use_smooth = True
    return o
plates = []
for k, kind in enumerate(["곧게", "가늘게", "굵게"]):
    x0 = (k - 1) * 4.5; arm(x0, kind)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x0, -1.6, 0)); p = bpy.context.object; p.scale = (3.2, 0.15, 2.3); p.color = (0.25,0.45,0.85,1); plates.append(p)
H.look((0,0,0), 0, 0, ortho=14.5); H.shot(os.path.join(OUT, "B5_가림.png"))
for p in plates: p.hide_render = True
H.shot(os.path.join(OUT, "B5_걷음.png"))
# ---------- B7 수평 단면 ----------
bpy.ops.wm.open_mainfile(filepath=r"G:\art2real\out\영상05\B1\head60k.blend")
sc = bpy.context.scene; wb(sc); sc.render.resolution_x = sc.render.resolution_y = 900; sc.render.film_transparent = True
head = [x for x in sc.objects if x.type == "MESH"][0]; head.scale = (1,1,1); head.color = (0.85,0.85,0.88,0.25)
zs = [-30 + 6 * k for k in range(13)]
for k, z in enumerate(zs):
    bm = bmesh.new(); bm.from_mesh(head.data)
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0,0,z), plane_no=(0,0,1))
    cut = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    vs = {}; ed = []
    for e in cut:
        ids = []
        for v in e.verts:
            if v.index not in vs: vs[v.index] = len(vs)
            ids.append(vs[v.index])
        ed.append(tuple(ids))
    co = [None] * len(vs)
    for v in bm.verts:
        if v.index in vs: co[vs[v.index]] = v.co.copy()
    bm.free()
    me = bpy.data.meshes.new("cut%d" % k); me.from_pydata(co, ed, []); me.update()
    o = bpy.data.objects.new("cut%d" % k, me); sc.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    for x in sc.objects: x.select_set(x == o)
    bpy.ops.object.convert(target="CURVE"); o.data.bevel_depth = 0.45
    hue = k / len(zs); c = mathutils.Color(); c.hsv = (0.66 * (1 - hue), 0.8, 1.0); o.color = (c.r, c.g, c.b, 1)
sh = sc.display.shading; sh.show_xray = False
H.look((0,0,0), 0, 0, ortho=120); H.shot(os.path.join(OUT, "B7_정면.png"))
H.look((0,0,0), 0, 89.5, ortho=120); H.shot(os.path.join(OUT, "B7_위.png"))
head.hide_render = True
H.look((0,0,0), 35, 25, ortho=120); H.shot(os.path.join(OUT, "B7_단면만.png"))
