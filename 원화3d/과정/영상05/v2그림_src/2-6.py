# -*- coding: utf-8 -*-
"""2-6 부품을 덜 그린 판과 다 그린 판: 펭귄(9 부품 중 3 · 9) · 와인잔(3 중 2 · 3) · 손전등(3 중 2 · 3).
blender -b -P 2-6.py → _렌더/2-6.png + 2-6.json(이름표 자리) → 2-6.typ"""
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import 선화 as S
sc = S.scene(thick=2.4)
def ell(loc, sc_, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1, location=loc, rotation=rot); o = bpy.context.object; o.scale = sc_; return S.white(o)
def cone(loc, r1, r2, h, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=h, location=loc, rotation=rot); return S.white(bpy.context.object)
def lathe(prof, loc):
    """(r, z) 단면을 z 축으로 돌린 면(위가 열린 그릇)"""
    bm = bmesh.new(); vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), steps=64, angle=2 * math.pi, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    me = bpy.data.meshes.new("l"); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new("l", me); sc.collection.objects.link(o); o.location = loc; return S.white(o)
LAB = {}
def penguin(x, z, full):
    ell((x, 0, z + 1.35), (0.72, 0.62, 1.35))                       # 몸
    ell((x - 0.18, 0, z + 2.85), (0.42, 0.4, 0.42))                  # 머리
    cone((x - 0.78, 0, z + 2.82), 0.13, 0.0, 0.55, rot=(0, -math.pi / 2, 0))   # 부리
    if full:
        ell((x - 0.3, -0.36, z + 2.97), (0.06, 0.03, 0.06))           # 눈
        ell((x + 0.05, -0.62, z + 1.6), (0.22, 0.08, 0.85), rot=(0, math.radians(-12), 0))   # 앞 날개
        ell((x + 0.05, 0.62, z + 1.6), (0.22, 0.08, 0.85), rot=(0, math.radians(-12), 0))    # 뒤 날개
        ell((x - 0.25, -0.25, z + 0.04), (0.32, 0.13, 0.06))         # 발 둘
        ell((x - 0.2, 0.25, z + 0.04), (0.32, 0.13, 0.06))
        cone((x + 0.72, 0, z + 0.3), 0.14, 0.0, 0.45, rot=(0, math.radians(120), 0))         # 꼬리
def _bowl(n=28):
    out = []
    for i in range(n + 1):
        t = i / n
        r = 0.66 * math.sqrt(max(0, 1 - ((t - 0.6) / 0.6) ** 2)) if t < 0.6 else 0.66 - 0.12 * ((t - 0.6) / 0.4) ** 2
        out.append((r, 1.2 * t))
    return out
BOWL = _bowl()
def glass(x, z, full):
    lathe(BOWL, (x, 0, z + 1.25))   # 잔
    cone((x, 0, z + 0.65), 0.06, 0.06, 1.25, verts=24)                                            # 대
    if full: cone((x, 0, z + 0.03), 0.6, 0.6, 0.06)                                               # 받침
def torch(x, z, full):
    rz = math.radians(-18); c, s = math.cos(rz), math.sin(rz)
    def L(t, h=0): return (x + t * c, t * s, z + 0.6 + h)
    cone(L(-0.35), 0.35, 0.35, 2.6, rot=(0, math.pi / 2, rz))         # 몸통
    cone(L(1.25), 0.35, 0.62, 0.6, rot=(0, math.pi / 2, rz))          # 머리(넓어짐)
    if full:
        q = L(0.1, 0.22); q = (q[0] - 0.24 * s, q[1] - 0.24 * c, q[2])   # 몸통 위 · 앞쪽(보는 쪽)으로 기운 자리
        bpy.ops.mesh.primitive_cube_add(size=1, location=q, rotation=(math.radians(-45), 0, rz)); b = bpy.context.object; b.scale = (0.6, 0.3, 0.22); S.white(b, smooth=False)
TOP, BOT = 0.6, -3.4
penguin(-2.0, TOP, False); LAB["3/9"] = (-2.0, 0, TOP - 0.3)
penguin(2.0, TOP, True); LAB["9/9"] = (2.0, 0, TOP - 0.3)
glass(-6.4, BOT, False); LAB["2/3 "] = (-6.4, 0, BOT - 0.3)
glass(-3.9, BOT, True); LAB["3/3 "] = (-3.9, 0, BOT - 0.3)
torch(1.0, BOT, False); LAB["2/3"] = (1.4, 0, BOT - 0.3)
torch(5.3, BOT, True); LAB["3/3"] = (5.7, 0, BOT - 0.3)
S.look((-0.3, 0, 0.0), 0, 10, ortho=19)
S.shot("2-6.png"); S.save_json("2-6.json", S.px(LAB))
