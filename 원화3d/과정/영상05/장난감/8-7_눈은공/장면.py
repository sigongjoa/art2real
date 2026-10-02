"""8-7 눈은 공 — Speed 1913 Diagram VI. 큰 달걀 머리 앞에 납작한 아몬드 둘 → 떨어지고 눈알 공이 굴러 들어와 박힌다 · 눈꺼풀 띠가 공을 감싼다 · 눈알이 두리번 · 머리가 기울면 안내선 띠가 휜다 · 끝에 깜빡."""
import bpy, bmesh, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
def key(o, fr, *what):
    for w in what: o.keyframe_insert(w, frame=fr)
def cap(name, r, keep, m, parent, loc):            # 공 껍질에서 keep(x,y,z) 인 곳만 남긴 띠(눈꺼풀)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=r)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep(*v.co)], context="VERTS")
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    s = o.modifiers.new("두께", "SOLIDIFY"); s.thickness = 0.02; o.modifiers.new("매끈", "SUBSURF").levels = 1
    for p in me.polygons: p.use_smooth = True
    return put(o, m, parent, loc)

skin, lid = mat("살", (0.98, 0.76, 0.62), 0.7), mat("눈꺼풀", (0.95, 0.62, 0.55), 0.6)
white, iris, pupil = mat("흰자", (0.97, 0.97, 0.95), 0.3), mat("홍채", (0.3, 0.55, 0.85), 0.4), mat("동공", (0.03, 0.03, 0.04), 0.2)
cyl(0.35, 0.6, skin, loc=(0, 0.05, 0.3))
H = empty("머리", loc=(0, 0, 1.4))
ball(0.8, skin, H, (0, 0, 0), (0.8, 0.9, 1.1))
nm = bpy.data.meshes.new("코"); nm.from_pydata([(0, 0, 0.1), (-0.08, 0, -0.16), (0.08, 0, -0.16), (0, -0.16, -0.16)], [], [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)])
n = bpy.data.objects.new("코", nm); bpy.context.scene.collection.objects.link(n); put(n, skin, H, (0, -0.66, -0.05))
R = 0.11
eyes, uppers, lowers, alms = [], [], [], []
for s in (-1, 1):
    E = empty("눈", H, (s * 0.24, -0.6, 0.12))
    ball_ = empty("눈알", E); ball(R, white, ball_); cyl(0.05, 0.02, iris, ball_, (0, -R + 0.004, 0), (math.pi / 2, 0, 0)); cyl(0.024, 0.024, pupil, ball_, (0, -R - 0.002, 0), (math.pi / 2, 0, 0))
    up = empty("윗꺼풀", E); cap("윗", R + 0.012, lambda x, y, z: z > 0.025 and y < 0.06, lid, up, (0, 0, 0))
    lo = empty("아랫꺼풀", E); cap("아래", R + 0.01, lambda x, y, z: z < -0.06 and y < 0.03, lid, lo, (0, 0, 0))
    eyes.append(ball_); uppers.append(up); lowers.append(lo)
    # 납작한 아몬드(훅): 앞에 붙은 판
    am = bpy.data.meshes.new("아몬드"); pts = [(0.16 * math.cos(a), 0, 0.07 * math.sin(a) * abs(math.sin(a)) ** -0.3 if math.sin(a) else 0) for a in [2 * math.pi * k / 40 for k in range(40)]]
    am.from_pydata(pts, [], [list(range(40))]); A = bpy.data.objects.new("아몬드", am); bpy.context.scene.collection.objects.link(A)
    put(A, mat("아몬드%d" % s, (0.15, 0.12, 0.2), 0.5), H, (s * 0.24, -0.73, 0.12)); A.modifiers.new("t", "SOLIDIFY").thickness = 0.01
    alms.append(A)
ring_m = mat("안내선", (1.0, 0.45, 0.2), 0.5, emit=1.0)
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.012, major_segments=96)
ring = put(bpy.context.object, ring_m, H, (0, 0, 0.12)); ring.scale = (0.64, 0.72, 1.4)
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.012, major_segments=96, rotation=(0, math.pi / 2, 0))
mer = put(bpy.context.object, ring_m, H, (0, 0, 0))

cams = {"front": camera("front", (0, -3.1, 1.4), (0, 0, 1.35), 30),
        "close": camera("close", (0.45, -1.7, 1.6), (0.12, -0.6, 1.5), 35),
        "side": camera("side", (2.2, -1.5, 1.5), (0, -0.4, 1.4), 32),
        "low": camera("low", (0.6, -1.9, 0.8), (0, -0.4, 1.45), 30),
        "top": camera("top", (0.5, -1.7, 2.6), (0, -0.5, 1.45), 32),
        "orbit": camera("orbit", (0, -2.0, 1.5), (0.2, -0.6, 1.5), 32)}

for fr in range(1, T.end + 1):
    t = fr / 24
    tilt = T.u(4, 0.1, 0.8, fr) * (1 - T.u(6, 0.3, 0.9, fr))
    H.rotation_euler = (0.3 * tilt, -0.35 * tilt, 0.15 * math.sin(t * 0.7)); key(H, fr, "rotation_euler")
    # 0 줄 아몬드 → 1 줄 툭 떨어진다
    for i, A in enumerate(alms):
        d = T.u(1, 0.0, 0.4, fr); A.location.z = 0.12 - 1.5 * d * d; A.location.y = -0.73 - 0.3 * d; A.rotation_euler.x = 2.5 * d
        A.hide_render = d > 0.95; key(A, fr, "location", "rotation_euler", "hide_render")
    for i, (b, up, lo) in enumerate(zip(eyes, uppers, lowers)):
        r = T.u(1, 0.3 + 0.15 * i, 0.75 + 0.15 * i, fr)            # 공이 옆에서 굴러 들어온다
        sgn = -1 if i == 0 else 1
        b.location = (sgn * 1.2 * (1 - r), -0.1 * (1 - r), 0); look = T.u(3, 0, 1, fr) * (1 - T.u(5, 0.5, 1, fr))
        b.rotation_euler = (0.25 * look * math.sin(t * 3), 6 * sgn * (1 - r), 0.6 * look * math.sin(t * 2.2))
        b.scale = (max(0.001, min(1, r * 3)),) * 3; key(b, fr, "location", "rotation_euler", "scale")
        k = T.u(2, 0.1 + 0.2 * i, 0.5 + 0.2 * i, fr)
        blink = math.sin(math.pi * T.u(6, 0.55, 0.8, fr))
        up.scale = (max(0.001, k),) * 3; up.rotation_euler.x = 1.2 * blink; key(up, fr, "scale", "rotation_euler")
        lo.scale = (max(0.001, T.u(2, 0.3 + 0.2 * i, 0.7 + 0.2 * i, fr)),) * 3; key(lo, fr, "scale")
    g = T.u(5, 0.0, 0.4, fr)
    ring.hide_render = mer.hide_render = g < 0.02
    ring.scale = (0.64 * max(g, 0.001), 0.72 * max(g, 0.001), 1.4); mer.scale = (0.89 * max(g, 0.001), 0.73 * max(g, 0.001), 1.4)
    key(ring, fr, "scale", "hide_render"); key(mer, fr, "scale", "hide_render")
    oc, _ = cams["orbit"]; a = math.radians(-90 + 70 * T.u(3, 0, 1, fr) - 70 * T.u(6, 0, 1, fr) + 10 * math.sin(t)); oc.location = (2.0 * math.cos(a), 2.0 * math.sin(a), 1.5); key(oc, fr, "location")
    cc, _ = cams["close"]; cc.location.x = 0.45 + 0.15 * math.sin(t * 0.6); key(cc, fr, "location")
끝(T, cams)
