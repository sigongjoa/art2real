# -*- coding: utf-8 -*-
"""리그 계획(json)만 읽어 **강체 리그**를 세우고, 포즈를 줘서 두 값을 잰다.

    blender -b --factory-startup --python rig_build.py -- out/st_doggy.glb out/st_doggy_rig.json \
        out/st_doggy_rigged.blend [--deg 25]

파트마다 본 하나, 가중치 1.0 짜리 그룹 하나. **섞이는 정점이 없다** —
`rigid_parts.py` 가 말한 대로 그러면 커튼이 원리적으로 안 생기고 늘어남이 1.000 이 된다.

## 재는 것 둘 (rigid_parts.py 와 같은 자)

    늘어남     포즈 뒤 모서리 길이 / 쉴 때. 강체면 1.000 이다. 아니면 뭔가 틀린 것
    이음매 틈  붙어 있던 두 파트 **사이의 최단거리**가 포즈 뒤 얼마나 되나 (span 대비 %)

처음엔 접촉점에서 제일 가까운 정점 하나씩을 골라 그 둘의 거리를 쟀다. 그건 틀린 자다 —
다리가 호를 그리면 붙어 있어도 두 점이 벌어져서, 강체로 딱 붙어 돌아가는 장식이
6.665% 벌어졌다고 나왔다(렌더는 멀쩡히 붙어 따라간다). **면을 점 하나로 줄이면 안 된다.**

**좌표 변환은 여기 한 곳뿐이다.** 계획은 GLB(Y-up), 블렌더는 Z-up: (x, -z, y).
"""
import json
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GLB, PLAN, OUT = argv[0], argv[1], argv[2]
DEG = float(argv[argv.index("--deg") + 1]) if "--deg" in argv else 25.0


def g2b(p):
    """GLB(Y-up) -> 블렌더(Z-up). 변환은 이 함수 하나뿐이다."""
    return Vector((p[0], -p[2], p[1]))


def main():
    plan = json.load(open(PLAN, encoding="utf-8"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(GLB))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes:
        o.parent = None
        o.matrix_world = o.matrix_world            # 임포트 계층을 떼고 월드로 굽는다
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # **정점 수로 짝짓는다** — 임포트 순서에 안 기댄다.
    # 면 수는 못 쓴다: 블렌더가 퇴화면을 버려서 파트 2·3 이 2개씩 어긋난다(267742->267740).
    byverts = {}
    for o in meshes:
        byverts.setdefault(len(o.data.vertices), []).append(o)
    obj = {}
    for p in plan["parts"]:
        c = byverts.get(p["verts"])
        assert c, "정점 %d 짜리 파트를 못 찾았다" % p["verts"]
        assert len(c) == 1, "정점 수가 겹치는 파트가 있다 — 다른 기준이 필요하다"
        obj[p["id"]] = c[0]

    arm_data = bpy.data.armatures.new("rig")
    arm = bpy.data.objects.new("rig", arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    for b in plan["bones"]:
        eb = arm_data.edit_bones.new(b["name"])
        eb.head, eb.tail = g2b(b["head"]), g2b(b["tail"])
        if (eb.tail - eb.head).length < 1e-4:
            eb.tail = eb.head + Vector((0, 0, 0.05))
    for b in plan["bones"]:
        if b["parent"]:
            arm_data.edit_bones[b["name"]].parent = arm_data.edit_bones[b["parent"]]
    bpy.ops.object.mode_set(mode='OBJECT')

    for b in plan["bones"]:
        o = obj[b["id"]]
        g = o.vertex_groups.new(name=b["name"])
        g.add(range(len(o.data.vertices)), 1.0, 'REPLACE')     # 한 본만, 가중치 1.0
        o.parent = arm
        m = o.modifiers.new("Armature", 'ARMATURE')
        m.object = arm

    dg = bpy.context.evaluated_depsgraph_get()

    def sample(o):
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        v = [me.vertices[i].co.copy() for i in range(len(me.vertices))]
        ed = [(a, b) for a, b in (ee.vertices for ee in me.edges)]
        e.to_mesh_clear()
        return v, ed

    rest = {i: sample(o) for i, o in obj.items()}

    for b in plan["bones"]:                                    # 다리를 벌린다
        if b["parent"] and b["parent"].endswith("_root") and b["name"] not in ("b03",):
            pb = arm.pose.bones[b["name"]]
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler = (0, 0, DEG * 3.14159265 / 180 * (1 if b["head"][0] > 0 else -1))
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    posed = {i: sample(o) for i, o in obj.items()}

    span = plan["datum"]["span"]
    worst, tot, n = 1.0, 0.0, 0
    for i in obj:
        (rv, ed), (pv, _) = rest[i], posed[i]
        for a, b in ed[:4000]:
            l0 = (rv[a] - rv[b]).length
            if l0 < 1e-9:
                continue
            r = (pv[a] - pv[b]).length / l0
            tot += r; n += 1
            worst = max(worst, r, 1 / r)
    print("늘어남  평균 %.5f · 최악 %.5f  (강체면 1.00000)" % (tot / max(n, 1), worst))

    import numpy as np

    def mindist(va, vb, n=2500):
        A = np.array([[v.x, v.y, v.z] for v in va])
        B = np.array([[v.x, v.y, v.z] for v in vb])
        r = np.random.default_rng(0)
        if len(A) > n:
            A = A[r.choice(len(A), n, replace=False)]
        if len(B) > n:
            B = B[r.choice(len(B), n, replace=False)]
        best = 1e18
        for k in range(0, len(A), 256):                    # 덩어리로 나눠 메모리를 아낀다
            d = np.linalg.norm(A[k:k + 256, None, :] - B[None, :, :], axis=2)
            best = min(best, float(d.min()))
        return best

    print("이음매 틈 = 두 파트 사이 최단거리 (span 대비 %):")
    for c in plan["contacts"]:
        r0 = mindist(rest[c["a"]][0], rest[c["b"]][0]) / span * 100
        r1 = mindist(posed[c["a"]][0], posed[c["b"]][0]) / span * 100
        flag = "  <- 벌어짐" if r1 > r0 + 0.5 else ""
        print("  %d-%d  쉴때 %.3f%%  ->  포즈 %.3f%%%s" % (c["a"], c["b"], r0, r1, flag))

    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT))
    print("저장 %s" % OUT)


main()
