# -*- coding: utf-8 -*-
"""무료 CC0 자산을 실제로 받아 견갑에 물려 본다.

    blender -b out/workbench.blend --python look_free.py

두 가지를 가른다.
    A) 환경이 문제인가   같은 금속 셰이더 · Poly Haven HDRI 4장
    B) 마스크가 문제인가  같은 HDRI · ambientCG roughness 맵으로 거칠기를 흔든다

자산은 `fetch_free.sh` 가 받는다 (out/hdri, out/acg — 둘 다 git 에 안 올린다).
UV 는 안 쓴다 — 이 부품의 UV 는 3D 거리 단위 배치라(LESSONS 72) 타일링 배율이 안 맞는다.
오브젝트 좌표 박스 투영으로 쏜다.
"""
import bpy, os, math, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
HDRI_DIR = os.path.join(OUT, "hdri")
ACG_DIR = os.path.join(OUT, "acg")
RES, SAMPLES = 560, 64
SHELL = (89, 93, 126)
GOLD = (198, 158, 62)

HDRIS = ["brown_photostudio_02", "kloofendal_43d_clear_puresky",
         "abandoned_factory_canteen_01", "dikhololo_night"]
ACG = ["Metal032", "Metal046B"]


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
    sc.render.engine = 'CYCLES'
    sc.render.film_transparent = False   # workbench.blend 에 켜져 있다. 끄지 않으면 HDRI 가 안 찍힌다
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.view_settings.view_transform = 'Filmic'
    return sc


def world(slug, rot_deg=150):
    w = bpy.data.worlds.get("w") or bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    o_ = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(os.path.join(HDRI_DIR, slug + ".hdr"))
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value[2] = math.radians(rot_deg)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
    nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs[0], o_.inputs['Surface'])


def parts():
    return [o for o in bpy.context.scene.objects
            if o.type == 'MESH' and not o.name.startswith("REF_")]


def metal(acg=None, scale=14.0):
    """Principled 금속. acg 를 주면 그 재질의 roughness/normal 을 물린다."""
    for o in parts():
        g = o.name.startswith("horn")
        o.data.materials.clear()
        m = bpy.data.materials.new("m")
        m.use_nodes = True
        o.data.materials.append(m)
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        b = nt.nodes.new('ShaderNodeBsdfPrincipled')
        b.inputs['Base Color'].default_value = lin(GOLD if g else SHELL)
        b.inputs['Metallic'].default_value = 1.0 if g else 0.55
        b.inputs['Roughness'].default_value = 0.25 if g else 0.40
        nt.links.new(b.outputs[0], out.inputs['Surface'])
        if not acg:
            continue
        # UV 말고 오브젝트 좌표로 쏜다 (박스 투영). 이음매는 blend 가 지운다
        tc = nt.nodes.new('ShaderNodeTexCoord')
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (scale, scale, scale)
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])

        def tex(suffix, non_color=True):
            p = os.path.join(ACG_DIR, acg, "%s_1K-PNG_%s.png" % (acg, suffix))
            if not os.path.exists(p):
                return None
            t = nt.nodes.new('ShaderNodeTexImage')
            t.image = bpy.data.images.load(p)
            t.projection = 'BOX'
            t.projection_blend = 0.3
            if non_color:
                t.image.colorspace_settings.name = 'Non-Color'
            nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
            return t

        r = tex("Roughness")
        if r:
            # 원화 색을 지키려고 Color 맵은 안 쓴다. **거칠기만** 빌려온다
            mr = nt.nodes.new('ShaderNodeMapRange')
            mr.inputs['To Min'].default_value = 0.18
            mr.inputs['To Max'].default_value = 0.75
            nt.links.new(r.outputs['Color'], mr.inputs['Value'])
            nt.links.new(mr.outputs[0], b.inputs['Roughness'])
        n = tex("NormalGL")
        if n:
            nm = nt.nodes.new('ShaderNodeNormalMap')
            nm.inputs['Strength'].default_value = 0.6
            nt.links.new(n.outputs['Color'], nm.inputs['Color'])
            nt.links.new(nm.outputs[0], b.inputs['Normal'])


def main():
    sc = stage()
    for s in HDRIS:                       # A) 환경만 바꾼다
        world(s)
        metal()
        sc.render.filepath = os.path.join(OUT, "free_env_%s.png" % s)
        bpy.ops.render.render(write_still=True)
        print("FREE env", s)
    world("brown_photostudio_02")         # B) 환경 고정, 거칠기 맵만 바꾼다
    for a in ACG:
        metal(acg=a)
        sc.render.filepath = os.path.join(OUT, "free_acg_%s.png" % a)
        bpy.ops.render.render(write_still=True)
        print("FREE acg", a)


main()
