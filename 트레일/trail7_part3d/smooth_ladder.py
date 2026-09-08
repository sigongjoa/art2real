# -*- coding: utf-8 -*-
"""생성 메시를 곡면으로 다듬는다. 단계를 하나씩 얹고 **같은 카메라로 전/후**를 뽑는다.

    blender -b --python smooth_ladder.py -- out/omega8.glb out/sm [zoom]

LESSONS 4: 스무스 셰이딩부터 확인한다 — 각진 면이 만드는 계단이 다른 증상을 덮는다.
LESSONS 9: 손으로 굽지 말고 모디파이어. 파괴적이지 않고 되돌릴 수 있다.
LESSONS 2: "좋아진 것 같다"는 판정이 아니다. 같은 카메라·같은 빛으로 나란히.

마칭큐브 출력이라 면이 27만이다. 데시메이트로 먼저 줄이고 다듬는 게 순서다 —
계단이 남은 채로 섭디비전을 걸면 계단이 매끈해질 뿐 사라지지 않는다.
"""
import bpy, os, sys, math
import numpy as np

A = sys.argv[sys.argv.index("--")+1:]
GLB, TAG = A[0], A[1]
ZOOM = "zoom" in A[2:]
HERE = os.path.dirname(os.path.abspath(__file__))

# 각짐의 원인이 둘이다 — 플랫 셰이딩과 기하. 셰이딩부터 끄고 봐야 기하 문제가 보인다.
# 스무스 모디파이어는 라플라시안이라 **판 이음선과 뿔 끝을 같이 지운다.** 마지막 수단이다.
VARIANTS = [
    ("0_raw",        "받은 그대로 (플랫 셰이딩)",            []),
    ("1_shade",      "스무스 셰이딩만 — 기하는 그대로",       ["shade"]),
    ("2_dec50",      "+ 데시메이트 0.50",                  ["shade", ("DECIMATE", 0.50)]),
    ("3_dec25",      "+ 데시메이트 0.25",                  ["shade", ("DECIMATE", 0.25)]),
    ("4_corr",       "+ 코렉티브 스무스 (0.5 x 5)",         ["shade", ("DECIMATE", 0.25), ("CORRECTIVE_SMOOTH", 0.5)]),
    ("5_lap",        "+ 라플라시안 스무스 (0.5 x 12) — 대조군", ["shade", ("DECIMATE", 0.15), ("SMOOTH", 0.5)]),
]


def load():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(GLB))
    obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in obs:
        o.data.transform(o.matrix_world)
        o.matrix_world.identity()
    bpy.context.view_layer.objects.active = obs[0]
    for o in obs:
        o.select_set(True)
    if len(obs) > 1:
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def camera(o, name, ang):
    co = np.array([v.co[:] for v in o.data.vertices])
    lo, hi = co.min(0), co.max(0)
    if ZOOM:
        lo = lo.copy(); lo[2] = hi[2] - (hi[2]-lo[2])*0.35
    ctr, size = (lo+hi)/2, float((hi-lo).max())
    r = math.radians(ang)
    cd = bpy.data.cameras.new(name); cd.type = 'ORTHO'; cd.ortho_scale = size*1.25
    c = bpy.data.objects.new(name, cd)
    c.location = (ctr[0] + 3*size*math.sin(r), ctr[1] - 3*size*math.cos(r), ctr[2])
    c.rotation_euler = (math.radians(90), 0, r)
    bpy.context.scene.collection.objects.link(c)
    return c


def shoot(o, tag):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (0.62, 0.62, 0.66)
    sc.display.shading.show_cavity = True      # 계단이 남았으면 여기서 드러난다
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = 512
    sc.view_settings.view_transform = 'Standard'
    for n, ang in (("a000", 0.0), ("a090", 90.0)):
        sc.camera = camera(o, "%s_%s" % (tag, n), ang)
        sc.render.filepath = os.path.join(HERE, "%s_%s_%s.png" % (TAG, tag, n))
        bpy.ops.render.render(write_still=True)


for tag, desc, steps in VARIANTS:
    o = load()
    for st in steps:
        if st == "shade":
            bpy.ops.object.shade_smooth(); continue
        kind, val = st
        m = o.modifiers.new(kind.lower(), kind)
        if kind == 'DECIMATE':
            m.ratio = val
        elif kind == 'SMOOTH':
            m.factor, m.iterations = val, 12
        elif kind == 'CORRECTIVE_SMOOTH':
            m.factor, m.iterations, m.use_only_smooth = val, 5, True
    bpy.context.view_layer.update()
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    print("%-10s %-38s 면 %8d" % (tag, desc, len(ev.data.polygons)))
    shoot(o, tag)
