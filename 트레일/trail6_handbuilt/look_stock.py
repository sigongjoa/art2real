# -*- coding: utf-8 -*-
"""블렌더 **기본 제공**만으로 견갑을 찍는다. 손으로 만든 노드 조합 없음.

    blender -b out/workbench.blend --python look_stock.py

- 셰이더: 내장 BSDF 노드를 하나씩 그대로. 파라미터는 기본값 아니면 한두 개만
- 조명: 번들 스튜디오 HDRI (4.0/datafiles/studiolights/world/studio.exr)
- 엔진: Cycles. Toon BSDF 와 Glass 는 EEVEE 에서 가짜로 나온다

out/stock_<이름>.png
"""
import bpy, os, math, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
RES, SAMPLES = 560, 64
HDRI = os.path.join(os.path.dirname(bpy.app.binary_path), "4.0", "datafiles",
                    "studiolights", "world", "studio.exr")
SHELL = (89, 93, 126)
GOLD = (198, 158, 62)


def lin(c):
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)


def stage():
    sc = bpy.context.scene
    for o in bpy.data.objects:
        if o.name.startswith("REF_"):
            o.hide_render = True
    for o in [x for x in bpy.data.objects if x.type == 'LIGHT']:
        bpy.data.objects.remove(o, do_unlink=True)

    tgt = (0.181, 0.029, 0.867)
    emp = bpy.data.objects.new("t", None)
    emp.location = tgt
    sc.collection.objects.link(emp)
    cd = bpy.data.cameras.new("look")
    cd.lens = 85
    cam = bpy.data.objects.new("look", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    d, a, e = 0.62, math.radians(38), math.radians(16)
    cam.location = (tgt[0] + d * math.sin(a), tgt[1] - d * math.cos(a), tgt[2] + d * math.sin(e))
    ct = cam.constraints.new('TRACK_TO')
    ct.target = emp
    ct.track_axis = 'TRACK_NEGATIVE_Z'
    ct.up_axis = 'UP_Y'

    w = bpy.data.worlds.new("w")          # 번들 HDRI 를 월드로
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    o_ = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = 1.0
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(HDRI)
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value[2] = math.radians(150)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
    nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs[0], o_.inputs['Surface'])

    sc.render.engine = 'CYCLES'
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Filmic'
    return sc


def parts():
    return [o for o in bpy.context.scene.objects
            if o.type == 'MESH' and not o.name.startswith("REF_")]


def apply(name, build):
    """build(nt, base) -> 셰이더 출력 소켓. base 는 그 부품의 실측 색."""
    for o in parts():
        base = lin(GOLD if o.name.startswith("horn") else SHELL)
        o.data.materials.clear()
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        o.data.materials.append(m)
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(build(nt, base), out.inputs['Surface'])


# ------------------------------------------------ 내장 BSDF 를 하나씩, 그대로

def s_default(nt, base):
    """블렌더가 새 재질에 주는 **그 기본값**. 색도 안 바꾼다."""
    return nt.nodes.new('ShaderNodeBsdfPrincipled').outputs[0]


def s_principled(nt, base):
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = base
    return b.outputs[0]


def s_metal(nt, base):
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = base
    b.inputs['Metallic'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.25
    return b.outputs[0]


def s_diffuse(nt, base):
    b = nt.nodes.new('ShaderNodeBsdfDiffuse')
    b.inputs['Color'].default_value = base
    return b.outputs[0]


def s_glossy(nt, base):
    b = nt.nodes.new('ShaderNodeBsdfAnisotropic')   # 4.0 의 Glossy BSDF
    b.inputs['Color'].default_value = base
    b.inputs['Roughness'].default_value = 0.15
    return b.outputs[0]


def s_toon(nt, base):
    """블렌더 **내장 셀 셰이더**. Cycles 전용이라 EEVEE 에선 디퓨즈로 떨어진다."""
    b = nt.nodes.new('ShaderNodeBsdfToon')
    b.component = 'DIFFUSE'
    b.inputs['Color'].default_value = base
    b.inputs['Size'].default_value = 0.5
    b.inputs['Smooth'].default_value = 0.0
    return b.outputs[0]


def s_glass(nt, base):
    b = nt.nodes.new('ShaderNodeBsdfGlass')
    b.inputs['Color'].default_value = base
    b.inputs['Roughness'].default_value = 0.05
    return b.outputs[0]


def s_sss(nt, base):
    b = nt.nodes.new('ShaderNodeSubsurfaceScattering')
    b.inputs['Color'].default_value = base
    return b.outputs[0]


VARIANTS = [
    ("1default", "Principled 기본값 (손 안 댐)", s_default),
    ("2principled", "Principled + 실측색", s_principled),
    ("3metal", "Principled metallic 1.0", s_metal),
    ("4diffuse", "Diffuse BSDF", s_diffuse),
    ("5glossy", "Glossy BSDF", s_glossy),
    ("6toon", "Toon BSDF (내장 셀)", s_toon),
    ("7glass", "Glass BSDF", s_glass),
    ("8sss", "Subsurface Scattering", s_sss),
]


def main():
    which = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
    sc = stage()
    for k, _, fn in VARIANTS:
        if which and k != which:
            continue
        apply(k, fn)
        sc.render.filepath = os.path.join(OUT, "stock_%s.png" % k)
        bpy.ops.render.render(write_still=True)
        print("STOCK", k, sc.render.filepath)


main()
