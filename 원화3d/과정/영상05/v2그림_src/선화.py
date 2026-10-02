# -*- coding: utf-8 -*-
"""v2 그림 공통: 흰 면 + 검은 Freestyle 선(비더만 교재 선화 느낌). blender -b -P <장면>.py 안에서 import.
   S = scene(res) · white(o) · look(...) · shot(path) · px(points) → 화면 픽셀(라벨을 CeTZ 에서 얹을 때)."""
import bpy, math, mathutils, os, sys, json
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
from bpy_extras.object_utils import world_to_camera_view
R = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(R, "_렌더")
_W = None
def scene(res=(1920, 1080), thick=2.4):
    global _W
    bpy.ops.wm.read_homefile(use_empty=True); sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"; sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.world = bpy.data.worlds.new("w"); sc.world.color = (1, 1, 1); sc.render.film_transparent = False
    sc.render.use_freestyle = True; sc.render.line_thickness_mode = "ABSOLUTE"; sc.render.line_thickness = thick
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = "ORTHO"; cam.data.clip_end = 1000
    fs = sc.view_layers[0].freestyle_settings; fs.crease_angle = math.radians(140)
    ls = fs.linesets[0]; ls.select_by_visibility = True
    for k in ("silhouette", "border", "crease", "external_contour", "contour"): setattr(ls, "select_" + k, True)
    ls.linestyle = ls.linestyle or bpy.data.linestyles.new("ln"); ls.linestyle.color = (0, 0, 0)
    _W = None
    return sc
def flat(color=(1, 1, 1)):
    m = bpy.data.materials.new("f"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (*color, 1); o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0]); return m
def white(o, smooth=True):
    global _W
    if _W is None: _W = flat()
    if o.type == "MESH":
        o.data.materials.clear(); o.data.materials.append(_W)
        for p in o.data.polygons: p.use_smooth = smooth
    else:
        o.data.materials.clear(); o.data.materials.append(_W)
    return o
def look(center, yaw, pitch, ortho, dist=60): H.look(center, yaw, pitch, ortho, dist)
def shot(name):
    p = os.path.join(OUT, name); bpy.context.scene.render.filepath = p; bpy.ops.render.render(write_still=True); return p
def px(points):
    sc = bpy.context.scene; W, Hh = sc.render.resolution_x, sc.render.resolution_y; out = {}
    for k, p in points.items():
        c = world_to_camera_view(sc, sc.camera, mathutils.Vector(p)); out[k] = (round(c.x * W, 1), round((1 - c.y) * Hh, 1))
    return out
def save_json(name, d): json.dump(d, open(os.path.join(OUT, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
