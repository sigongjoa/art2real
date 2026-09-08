# -*- coding: utf-8 -*-
"""메시에 선을 **실제로 달아서** 찍는다. 뷰포트 오버레이는 F12 에 안 나온다.

    blender -b out/workbench.blend --python wire.py

    out/wire_all.png    모든 엣지 (Wireframe 모디파이어 -> 진짜 기하)
    out/wire_crease.png 판 선만 (crease_edge >= 0.5 -> 커브 베벨)

"판 선을 메시 모서리로 박았다"가 사실인지 눈으로 확인하려고 만든 것.
"""
import bpy, os, math, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
RES = 1024
W_ALL = float(os.environ.get("W_ALL", 0.00035))
W_CR = float(os.environ.get("W_CR", 0.00075))


def blackmat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs[0].default_value = (0, 0, 0, 1)
    nt.links.new(e.outputs[0], o.inputs['Surface'])
    return m


def parts():
    return [o for o in bpy.context.scene.objects
            if o.type == 'MESH' and not o.name.startswith("REF_") and "_W" not in o.name]


def wire_all():
    """면이 있는 메시엔 Wireframe 모디파이어가 제일 싸다."""
    made = []
    for o in list(parts()):
        d = o.copy(); d.data = o.data.copy(); d.name = o.name + "_W"
        bpy.context.scene.collection.objects.link(d)
        d.data.materials.clear(); d.data.materials.append(blackmat("m_wire"))
        w = d.modifiers.new("w", 'WIREFRAME')
        w.thickness = W_ALL
        w.use_replace = True
        made.append(d)
    return made


def wire_crease():
    """crease_edge >= 0.5 인 엣지만 뽑아 커브로 굵힌다 (엣지엔 Wireframe 이 안 먹는다)."""
    made = []
    for o in list(parts()):
        me = o.data
        at = me.attributes.get("crease_edge")
        if at is None:
            continue
        idx = [i for i, v in enumerate(at.data) if v.value >= 0.5]
        if not idx:
            continue
        vs = [v.co[:] for v in me.vertices]
        es = [me.edges[i].vertices[:] for i in idx]
        nm = bpy.data.meshes.new(o.name + "_Cm")
        nm.from_pydata(vs, es, [])
        nm.validate()
        ob = bpy.data.objects.new(o.name + "_W", nm)
        bpy.context.scene.collection.objects.link(ob)
        bpy.context.view_layer.objects.active = ob
        for x in bpy.context.selected_objects:
            x.select_set(False)
        ob.select_set(True)
        bpy.ops.object.convert(target='CURVE')
        cu = ob.data
        cu.bevel_depth = W_CR
        cu.bevel_resolution = 1
        cu.materials.clear() if hasattr(cu, "materials") else None
        cu.materials.append(blackmat("m_crease"))
        made.append(ob)
        print("  %s 판 선 엣지 %d개" % (o.name, len(idx)))
    return made


def setup():
    sc = bpy.context.scene
    for o in bpy.data.objects:
        if o.name.startswith("REF_"):
            o.hide_render = True
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.view_settings.view_transform = 'Standard'
    for o in parts():                       # 바탕은 옅은 평면색 — 선이 읽히게
        o.data.materials.clear()
        m = bpy.data.materials.new("f")
        m.use_nodes = True
        nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        e = nt.nodes.new('ShaderNodeEmission')
        e.inputs[0].default_value = (0.72, 0.72, 0.80, 1)
        nt.links.new(e.outputs[0], out.inputs['Surface'])
        o.data.materials.append(m)
    return sc


def shoot(sc, tag):
    for v in ("front", "side"):
        sc.camera = bpy.data.objects["CAM_" + v]
        sc.render.filepath = os.path.join(OUT, "wire_%s_%s.png" % (tag, v))
        bpy.ops.render.render(write_still=True)
        print("WIRE", tag, v)


def main():
    which = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "both"
    sc = setup()
    if which in ("both", "crease"):
        made = wire_crease()
        shoot(sc, "crease")
        for o in made:
            bpy.data.objects.remove(o, do_unlink=True)
    if which in ("both", "all"):
        wire_all()
        shoot(sc, "all")


main()
