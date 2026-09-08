# -*- coding: utf-8 -*-
"""견갑에 재질을 입혀 **보는** 스크립트. 재지 않는다, 찍는다.

    blender -b out/workbench.blend --python look.py

out/look_<변형>.png
변형: 1flat(지금) / 2cel(3단+아웃라인) / 3metal(PBR 금속) / 4worn(닳은 금속)
"""
import bpy, os, math, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
RES = 900
SHELL = (89, 93, 126)   # 원화 실측 중앙값 (LESSONS 69)
GOLD = (198, 158, 62)   # 뿔


def lin(c):
    """sRGB 0~255 -> 리니어. 이거 안 하면 전부 뿌옇게 뜬다."""
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


def stage():
    """참조판을 끄고, 3/4 투시 카메라와 3점 광원을 세운다."""
    sc = bpy.context.scene
    for o in bpy.data.objects:
        if o.name.startswith("REF_"):
            o.hide_render = True
    cd = bpy.data.cameras.new("look")
    cd.lens = 85
    cam = bpy.data.objects.new("look", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    tgt = (0.181, 0.029, 0.867)   # parts/sh_pauldron.json 실측 상자의 가운데
    emp = bpy.data.objects.new("t", None)
    emp.location = tgt
    sc.collection.objects.link(emp)
    d = 0.62
    a, e = math.radians(38), math.radians(16)
    cam.location = (tgt[0] + d * math.sin(a), tgt[1] - d * math.cos(a), tgt[2] + d * math.sin(e))
    ct = cam.constraints.new('TRACK_TO')
    ct.target = emp
    ct.track_axis = 'TRACK_NEGATIVE_Z'
    ct.up_axis = 'UP_Y'

    def light(name, loc, energy, size, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy, ld.size, ld.color = energy, size, color
        o = bpy.data.objects.new(name, ld)
        o.location = loc
        sc.collection.objects.link(o)
        c = o.constraints.new('TRACK_TO')
        c.target = emp
        c.track_axis = 'TRACK_NEGATIVE_Z'
        c.up_axis = 'UP_Y'
        return o

    light("key", (0.9, -0.8, 1.7), 220, 0.9)
    light("fill", (-0.8, -0.7, 0.9), 40, 1.2, (0.75, 0.80, 1.0))
    light("rim", (0.2, 1.0, 1.5), 160, 0.5, (1.0, 0.93, 0.8))

    sc.render.engine = 'BLENDER_EEVEE'
    sc.eevee.use_gtao = True
    sc.eevee.use_ssr = True
    sc.eevee.taa_render_samples = 96
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.06, 1)
    return sc


def parts():
    return [o for o in bpy.context.scene.objects
            if o.type == 'MESH' and not o.name.startswith("REF_") and not o.name.endswith("_OL")]


def is_gold(o):
    return o.name.startswith("horn")


def mat(o, name):
    o.data.materials.clear()
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    o.data.materials.append(m)
    nt = m.node_tree
    nt.nodes.clear()
    return m, nt, nt.nodes.new('ShaderNodeOutputMaterial')


# ---------------------------------------------------------------- 변형 4개

def v_flat():
    """지금 상태. Emission 평면색 — 빛이 없다."""
    for o in parts():
        m, nt, out = mat(o, "flat")
        e = nt.nodes.new('ShaderNodeEmission')
        e.inputs[0].default_value = lin(GOLD if is_gold(o) else SHELL)
        nt.links.new(e.outputs[0], out.inputs[0])


def v_cel():
    """닷 프로덕트 셀 (ep02). Shader to RGB 를 안 쓴다 — 라이트 세기에 안 흔들린다."""
    key = bpy.data.objects["key"]
    tgt = bpy.data.objects["t"]
    v = (key.matrix_world.translation - tgt.location).normalized()
    for o in parts():
        base = lin(GOLD if is_gold(o) else SHELL)
        m, nt, out = mat(o, "cel")
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        dot = nt.nodes.new('ShaderNodeVectorMath')
        dot.operation = 'DOT_PRODUCT'
        ldir = nt.nodes.new('ShaderNodeCombineXYZ')
        ldir.inputs[0].default_value = v.x
        ldir.inputs[1].default_value = v.y
        ldir.inputs[2].default_value = v.z
        nt.links.new(geo.outputs['Normal'], dot.inputs[0])
        nt.links.new(ldir.outputs[0], dot.inputs[1])
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        # Vector Math 의 outputs[0] 은 'Vector' 다. 닷 프로덕트 값은 'Value' 쪽
        nt.links.new(dot.outputs['Value'], ramp.inputs['Fac'])
        ramp.color_ramp.interpolation = 'CONSTANT'
        e0 = ramp.color_ramp.elements[0]
        e0.position = 0.0
        e0.color = (0.30, 0.32, 0.42, 1)          # 그늘 단
        e1 = ramp.color_ramp.elements[1]
        e1.position = 0.42
        e1.color = (0.80, 0.80, 0.86, 1)          # 중간 단
        e2 = ramp.color_ramp.elements.new(0.78)
        e2.color = (1.12, 1.10, 1.05, 1)          # 하이라이트 단
        mixv = nt.nodes.new('ShaderNodeMixRGB')
        mixv.blend_type = 'MULTIPLY'
        mixv.inputs[0].default_value = 1.0
        mixv.inputs[1].default_value = base
        nt.links.new(ramp.outputs[0], mixv.inputs[2])
        fres = nt.nodes.new('ShaderNodeFresnel')       # 림 = dot(노멀, 시선)
        fres.inputs[0].default_value = 1.45
        gt = nt.nodes.new('ShaderNodeMath')
        gt.operation = 'GREATER_THAN'
        gt.inputs[1].default_value = 0.62
        nt.links.new(fres.outputs[0], gt.inputs[0])
        rim = nt.nodes.new('ShaderNodeMixRGB')
        rim.blend_type = 'SCREEN'
        rim.inputs[2].default_value = (0.55, 0.52, 0.42, 1)
        nt.links.new(gt.outputs[0], rim.inputs[0])
        nt.links.new(mixv.outputs[0], rim.inputs[1])
        emi = nt.nodes.new('ShaderNodeEmission')
        nt.links.new(rim.outputs[0], emi.inputs[0])
        nt.links.new(emi.outputs[0], out.inputs[0])
    if not os.environ.get('NOOUT'):
        outline()


def outline():
    """인버티드 헐 — 메시를 복제하고 뒤집어 부풀린다 (ep02 1절)."""
    om = bpy.data.materials.new("m_outline")
    om.use_nodes = True
    nt = om.node_tree
    nt.nodes.clear()
    o_ = nt.nodes.new('ShaderNodeOutputMaterial')
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs[0].default_value = (0, 0, 0, 1)
    # use_backface_culling 은 EEVEE 에서 안 먹었다 (헐이 통째로 덮었다).
    # Backfacing 으로 직접 가른다 — 앞면은 투명, 뒷면만 검게
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(geo.outputs['Backfacing'], mx.inputs[0])
    # 뒤집은 헐에서 **카메라 쪽 면이 backfacing** 이다. 그쪽을 지워야 속이 보인다
    nt.links.new(e.outputs[0], mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], o_.inputs[0])
    om.blend_method = 'BLEND'
    om.shadow_method = 'NONE'
    om.show_transparent_back = False
    for o in list(parts()):
        d = o.copy()
        d.data = o.data.copy()
        d.name = o.name + "_OL"
        bpy.context.scene.collection.objects.link(d)
        d.data.materials.clear()
        d.data.materials.append(om)
        s = d.modifiers.new("s", 'SOLIDIFY')
        s.thickness = 0.0045
        s.offset = 1.0
        s.use_flip_normals = True
        s.use_rim = False
        s.use_even_offset = False   # 뿔 끝에서 1/cos 가 발산한다 (LESSONS 105)


def v_metal(worn=False):
    """PBR 도장 금속. 갑주는 칠한 강판이라 완전 금속이 아니다 — 라벤더는 도장, 뿔만 금속."""
    for o in parts():
        g = is_gold(o)
        m, nt, out = mat(o, "worn" if worn else "metal")
        b = nt.nodes.new('ShaderNodeBsdfPrincipled')
        b.inputs['Base Color'].default_value = lin(GOLD if g else SHELL)
        b.inputs['Metallic'].default_value = 1.0 if g else 0.35
        b.inputs['Roughness'].default_value = 0.28 if g else 0.42
        nt.links.new(b.outputs[0], out.inputs[0])
        if not worn:
            continue
        # 닳음: 절차적 노이즈만으로. 텍스처 파일 없다
        tc = nt.nodes.new('ShaderNodeTexCoord')
        n1 = nt.nodes.new('ShaderNodeTexNoise')
        n1.inputs['Scale'].default_value = 42.0
        n1.inputs['Detail'].default_value = 8.0
        nt.links.new(tc.outputs['Object'], n1.inputs['Vector'])
        rr = nt.nodes.new('ShaderNodeMapRange')
        rr.inputs['To Min'].default_value = 0.22 if g else 0.30
        rr.inputs['To Max'].default_value = 0.62 if g else 0.72
        nt.links.new(n1.outputs['Fac'], rr.inputs['Value'])
        nt.links.new(rr.outputs[0], b.inputs['Roughness'])
        n2 = nt.nodes.new('ShaderNodeTexNoise')
        n2.inputs['Scale'].default_value = 180.0
        n2.inputs['Detail'].default_value = 6.0
        nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
        bump = nt.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.22
        bump.inputs['Distance'].default_value = 0.0008
        nt.links.new(n2.outputs['Fac'], bump.inputs['Height'])
        nt.links.new(bump.outputs[0], b.inputs['Normal'])
        # 모서리 벗겨짐: 볼록한 데만 강이 드러난다
        ao = nt.nodes.new('ShaderNodeAmbientOcclusion')
        ao.inside = True
        ed = nt.nodes.new('ShaderNodeMath')
        ed.operation = 'GREATER_THAN'
        ed.inputs[1].default_value = 0.72
        nt.links.new(ao.outputs['AO'], ed.inputs[0])   # 'Fac' 아니다
        mixc = nt.nodes.new('ShaderNodeMixRGB')
        mixc.inputs[1].default_value = lin(GOLD if g else SHELL)
        mixc.inputs[2].default_value = lin((150, 148, 152))
        nt.links.new(ed.outputs[0], mixc.inputs[0])
        nt.links.new(mixc.outputs[0], b.inputs['Base Color'])


VARIANTS = {
    "1flat": v_flat,
    "2cel": v_cel,
    "3metal": lambda: v_metal(False),
    "4worn": lambda: v_metal(True),
}


def main():
    which = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
    sc = stage()
    keys = [which] if which else list(VARIANTS)
    for k in keys:
        for o in [x for x in bpy.context.scene.objects if x.name.endswith("_OL")]:
            bpy.data.objects.remove(o, do_unlink=True)   # 앞 변형이 만든 아웃라인 복제본
        VARIANTS[k]()
        sc.view_settings.view_transform = 'Standard' if k == "2cel" else 'Filmic'
        sc.render.filepath = os.path.join(OUT, "look_%s.png" % k)
        bpy.ops.render.render(write_still=True)
        print("LOOK", k, sc.render.filepath)


if __name__ == "__main__":       # tri_look.py 가 재질만 가져다 쓴다
    main()
