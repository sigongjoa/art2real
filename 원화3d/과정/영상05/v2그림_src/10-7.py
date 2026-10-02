# -*- coding: utf-8 -*-
"""10-7 다모 외 LDI: 방 한 장 → 앞 겹(원래 색 + 깊이) · 뒤 겹(물건 지운 방 + 깊이) → 시점을 옮기면 한 겹은 구멍, 두 겹은 메움.
깊이는 ray_cast 로 직접 재고, 시점 이동은 그 깊이로 점을 옮겨 찍는다(numpy z-버퍼). blender -b -P 10-7.py"""
import bpy, sys, os, math, mathutils
import numpy as np
sys.path.insert(0, r"G:\art2real\원화3d\오메가몬\지표"); import 헤드리스 as H
D = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(D, "_r"); W, Hh = 480, 360
sc = H.scene(res=(W, Hh), transparent=False); sc.world.color = (0, 0, 0); sc.view_settings.view_transform = "Standard"
sh = sc.display.shading; sh.show_cavity = False; sh.show_shadows = True; sh.light = "STUDIO"
def box(name, loc, size, col):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = size; o.color = col; return o
WALL = (0.82, 0.82, 0.8, 1); FL = (0.68, 0.68, 0.66, 1); WOOD = (0.85, 0.62, 0.35, 1); RED = (0.8, 0.15, 0.1, 1)
box("바닥", (1.8, 1.0, -0.05), (8.0, 6.4, 0.1), FL); box("뒷벽", (1.8, 4.15, 1.4), (8.0, 0.1, 2.9), WALL); box("옆벽", (-2.15, 1.0, 1.4), (0.1, 6.4, 2.9), WALL)
box("선반", (-1.9, 2.2, 1.7), (0.4, 1.6, 0.08), (0.55, 0.3, 0.15, 1)); box("선반2", (-1.9, 2.2, 1.95), (0.4, 1.6, 0.08), (0.55, 0.3, 0.15, 1))
FG = []
cx, cy = 0.15, 1.2
FG.append(box("좌판", (cx, cy, 0.45), (0.5, 0.5, 0.05), WOOD))
for dx in (-0.22, 0.22):
    for dy in (-0.22, 0.22): FG.append(box("다리", (cx + dx, cy + dy, 0.22), (0.05, 0.05, 0.45), WOOD))
for k in range(5): FG.append(box("살", (cx - 0.2 + 0.1 * k, cy + 0.23, 0.75), (0.04, 0.04, 0.6), WOOD))
FG.append(box("등", (cx, cy + 0.23, 1.05), (0.5, 0.05, 0.06), WOOD))
o = box("상자", (0.75, 2.7, 0.15), (0.35, 0.6, 0.3), RED); o.rotation_euler.z = 0.5; FG.append(o)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(-0.6, 1.7, 0.1)); o = bpy.context.object; o.color = (0.95, 0.95, 0.95, 1); FG.append(o)
cam = sc.camera; cam.data.type = "PERSP"; cam.data.lens = 26; cam.data.sensor_width = 36; cam.data.clip_end = 100
def aim(pos, tgt):
    cam.location = pos; cam.rotation_euler = (mathutils.Vector(tgt) - mathutils.Vector(pos)).to_track_quat("-Z", "Y").to_euler(); bpy.context.view_layer.update()
A_POS, TGT = mathutils.Vector((1.3, -1.6, 2.3)), (-0.4, 2.6, 0.4)
aim(A_POS, TGT)
fx = W * cam.data.lens / 36.0
def rays():
    u, v = np.meshgrid(np.arange(W) + 0.5, np.arange(Hh) + 0.5)
    d = np.stack([(u - W / 2) / fx, -(v - Hh / 2) / fx, -np.ones_like(u)], -1)
    Rm = np.array(cam.matrix_world.to_3x3()); return d @ Rm.T
def depth_pts():
    dg = bpy.context.evaluated_depsgraph_get(); o = cam.matrix_world.translation.copy(); dirs = rays(); P = np.zeros((Hh, W, 3)); hit = np.zeros((Hh, W), bool)
    for i in range(Hh):
        for j in range(W):
            d = mathutils.Vector(dirs[i, j]).normalized(); ok, loc, *_ = sc.ray_cast(dg, o, d)
            if ok: P[i, j] = loc; hit[i, j] = True
    fwd = -np.array(cam.matrix_world.to_3x3())[:, 2]; z = (P - np.array(o)) @ fwd; return P, np.where(hit, z, np.nan)
def render(name):
    p = os.path.join(R, name); H.shot(p); im = bpy.data.images.load(p); a = np.array(im.pixels[:]).reshape(Hh, W, 4)[::-1, :, :3]; bpy.data.images.remove(im); return a
def save(a, name):
    im = bpy.data.images.new(name, W, Hh); rgba = np.concatenate([a, np.ones((Hh, W, 1))], -1)[::-1]; im.pixels = rgba.ravel().tolist()
    im.filepath_raw = os.path.join(R, name); im.file_format = "PNG"; im.save()
def cmap(z, lo, hi):
    t = np.clip((np.nan_to_num(z, nan=hi) - lo) / (hi - lo), 0, 1)[..., None]   # 가까움 = 보라 · 멂 = 노랑
    a, b, c = np.array([0.3, 0.05, 0.5]), np.array([0.9, 0.3, 0.4]), np.array([1.0, 0.9, 0.55])
    return np.where(t < 0.5, a + (b - a) * (t * 2), b + (c - b) * (t * 2 - 1))
fg_col = render("10-7_fg.png"); fg_P, fg_z = depth_pts()
for o in FG: bpy.data.objects.remove(o)
bg_col = render("10-7_bg.png"); bg_P, bg_z = depth_pts()
lo, hi = np.nanmin(fg_z), np.nanmax(bg_z); save(cmap(fg_z, lo, hi), "10-7_fgz.png"); save(cmap(bg_z, lo, hi), "10-7_bgz.png")
# 시점 옮기기: 카메라 오른쪽으로 0.7 m, 같은 곳을 본다
right = np.array(cam.matrix_world.to_3x3())[:, 0]; aim(A_POS + mathutils.Vector(right * 0.9), TGT)
Rb = np.array(cam.matrix_world.to_3x3()); ob = np.array(cam.matrix_world.translation)
def warp(layers):
    P = np.concatenate([l[0].reshape(-1, 3) for l in layers]); C = np.concatenate([l[1].reshape(-1, 3) for l in layers])
    q = (P - ob) @ Rb; z = -q[:, 2]; ok = z > 0.05; P, C, q, z = P[ok], C[ok], q[ok], z[ok]
    u = W / 2 + fx * q[:, 0] / z; v = Hh / 2 - fx * q[:, 1] / z
    out = np.zeros((Hh, W, 3)); zb = np.full((Hh, W), np.inf)
    order = np.argsort(-z)                     # 먼 것부터 찍고 가까운 것이 덮는다
    for du in (0, 1):
        for dv in (0, 1):
            iu = np.floor(u[order]).astype(int) + du; iv = np.floor(v[order]).astype(int) + dv; m = (iu >= 0) & (iu < W) & (iv >= 0) & (iv < Hh)
            out[iv[m], iu[m]] = C[order][m]
    return out
fh = ~np.isnan(fg_z); bh = ~np.isnan(bg_z)
save(warp([(fg_P[fh], fg_col[fh])]), "10-7_warp1.png")
save(warp([(bg_P[bh], bg_col[bh]), (fg_P[fh], fg_col[fh])]), "10-7_warp2.png")
