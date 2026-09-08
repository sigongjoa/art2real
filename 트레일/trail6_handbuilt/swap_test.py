# -*- coding: utf-8 -*-
"""선별 교체 시험 — 전신 생성 메시에서 견갑만 손으로 지은 것으로 갈아 끼운다.

    blender -b --python swap_test.py

122번의 결론(전량 교체가 아니라 선별 교체)을 실제로 재는 것. 그리고 이번엔
**정면만으로 판정하지 않는다** — 정면 IoU 는 판을 못 걸러낸다(123).

    바탕      trail4 out/nd_baked.blend (전신 한 장 생성)
    갈아낌    견갑 실측 상자 안의 생성 기하를 지우고 workbench 의 PAD + horn0~3 을 넣는다
    판정      정면 pid_front>0 · 측면 pid_side>0 두 실루엣과 IoU

부품 하나를 바꿔서 전신 지표가 움직이는지가 이 시험의 전부다.
1절에서 이미 겪었다 — 이웃이 부풀어 있으면 하나만 바꿔서는 안 움직인다.
"""
import bpy, os, sys, math, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
T4 = os.path.join(HERE, "..", "trail4_gen3d")
BASE = os.path.join(T4, "out", "nd_baked.blend")
WB = os.path.join(HERE, "out", "workbench.blend")
RES = 1024
U0, U1, Z0, Z1 = -0.6, 0.6, -0.1, 1.1
# 견갑 상자 (panels.json lav+gold 마스크에서 잰 것) + 여유
BOX = dict(x=(0.108, 0.260), z=(0.775, 0.995))


def cams(sc):
    for n, loc, rot in (("front", (0, -2, 0.5), (math.radians(90), 0, 0)),
                        ("side", (2, 0, 0.5), (math.radians(90), 0, math.radians(90)))):
        cd = bpy.data.cameras.new(n); cd.type = 'ORTHO'; cd.ortho_scale = 1.2
        c = bpy.data.objects.new(n, cd); c.location = loc; c.rotation_euler = rot
        sc.collection.objects.link(c)


def setup():
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'FLAT'
    sc.display.shading.color_type = 'SINGLE'
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.view_settings.view_transform = 'Standard'
    cams(sc)
    return sc


def alpha(path):
    im = bpy.data.images.load(path)
    a = np.array(im.pixels[:]).reshape(RES, RES, 4)[::-1, :, 3] > 0.5
    bpy.data.images.remove(im)
    return a


def shoot(sc, tag):
    out = {}
    for n in ("front", "side"):
        sc.camera = bpy.data.objects[n]
        sc.render.filepath = os.path.join(HERE, "out", "swap_%s_%s.png" % (tag, n))
        bpy.ops.render.render(write_still=True)
        out[n] = alpha(sc.render.filepath)
    return out


def carve():
    """견갑 상자 안의 생성 기하를 지운다. 지운 면 수를 돌려준다."""
    import bmesh
    n = 0
    for o in [x for x in bpy.context.scene.objects if x.type == 'MESH']:
        bm = bmesh.new(); bm.from_mesh(o.data)
        M = o.matrix_world
        kill = []
        for f in bm.faces:
            c = M @ f.calc_center_median()
            if BOX["x"][0] <= c.x <= BOX["x"][1] and BOX["z"][0] <= c.z <= BOX["z"][1]:
                kill.append(f)
        n += len(kill)
        if kill:
            bmesh.ops.delete(bm, geom=kill, context='FACES')
            bm.to_mesh(o.data)
        bm.free()
        o.data.update()
    return n


def bring_hand():
    with bpy.data.libraries.load(WB) as (s, d):
        d.objects = [x for x in s.objects if x == "PAD" or x.startswith("horn")]
    got = []
    for o in d.objects:
        if o is None:
            continue
        bpy.context.scene.collection.objects.link(o)
        got.append(o)
    return got


def iou(a, b):
    return float((a & b).sum() / max((a | b).sum(), 1))


def main():
    ref_f = np.load(os.path.join(T4, "pid_front.npy")) > 0
    ref_s = np.load(os.path.join(T4, "pid_side.npy")) > 0
    bpy.ops.wm.open_mainfile(filepath=BASE)
    sc = setup()
    base = shoot(sc, "base")
    b = (iou(base["front"], ref_f), iou(base["side"], ref_s))
    print("BASE  전신 생성        정면 %.3f  측면 %.3f" % b)

    killed = carve()
    only = shoot(sc, "carved")
    c = (iou(only["front"], ref_f), iou(only["side"], ref_s))
    print("CARVE 견갑 파냄 (면 %d)  정면 %.3f  측면 %.3f" % (killed, c[0], c[1]))

    got = bring_hand()
    print("HAND  가져온 오브젝트 %d개 (%s)" % (len(got), ", ".join(o.name for o in got)))
    sw = shoot(sc, "swapped")
    s = (iou(sw["front"], ref_f), iou(sw["side"], ref_s))
    print("SWAP  견갑 교체        정면 %.3f  측면 %.3f" % s)
    print("DELTA 정면 %+.3f  측면 %+.3f" % (s[0] - b[0], s[1] - b[1]))
    json.dump(dict(base=b, carved=c, swapped=s, killed=killed),
              open(os.path.join(HERE, "out", "swap_report.json"), "w"), indent=1)


main()
