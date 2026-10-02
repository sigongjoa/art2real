"""11-2 Marr–Nishihara(1978) 원기둥 모델 — 말랑한 점토 인형(메타볼) → 부위마다 축 따라 원기둥이 끼워짐 → 점토가 걷히면 원기둥 묶음 · 빛나는 축."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
SEG = [  # 시작, 끝, 굵기
    ((0, 0, 1.22), (0, 0, 1.95), 0.27), ((0, 0, 2.18), (0, 0, 2.5), 0.2),
    ((-0.36, 0, 1.9), (-0.6, 0, 1.45), 0.085), ((-0.6, 0, 1.45), (-0.74, 0, 1.0), 0.075),
    ((0.36, 0, 1.9), (0.62, 0, 2.3), 0.085), ((0.62, 0, 2.3), (0.72, 0, 2.75), 0.075),     # 오른팔은 들어 인사
    ((-0.15, 0, 1.18), (-0.18, 0, 0.64), 0.12), ((-0.18, 0, 0.64), (-0.2, 0, 0.1), 0.095),
    ((0.15, 0, 1.18), (0.18, 0, 0.64), 0.12), ((0.18, 0, 0.64), (0.2, 0, 0.1), 0.095)]
root = empty("인형", loc=(0, 0, 0))
clay = mat("점토", (0.95, 0.72, 0.55), 0.7, alpha=True); ca = alpha_of(clay)
if hasattr(clay, "show_transparent_back"): clay.show_transparent_back = False
mb = bpy.data.metaballs.new("점토"); mb.resolution = 0.05; mb.render_resolution = 0.03; mb.threshold = 0.5
for p, q, r in SEG:
    p, q = Vector(p), Vector(q); d = q - p
    e = mb.elements.new(); e.type = "CAPSULE"; e.co = (p + q) / 2; e.radius = r * 1.5; e.size_x = d.length / 2
    e.rotation = Vector((1, 0, 0)).rotation_difference(d)
e = mb.elements.new(); e.co = (0, 0, 2.05); e.radius = 0.16                                         # 목
mo = bpy.data.objects.new("점토", mb); bpy.context.scene.collection.objects.link(mo); mo.data.materials.append(clay); mo.parent = root
cols = [(0.6, 0.75, 0.95), (0.98, 0.6, 0.45), (0.45, 0.78, 0.6), (0.98, 0.72, 0.3), (0.7, 0.55, 0.9)]
glow = mat("축", (1.0, 0.45, 0.08), 0.5, emit=2.5)
cyls, axes = [], []
for i, (p, q, r) in enumerate(SEG):
    c = bar(p, q, r, mat("원기둥%d" % i, cols[i % 5], 0.55)); c.parent = root; cyls.append(c)
    p, q = Vector(p), Vector(q); d = (q - p).normalized()
    a = bar(p - d * 0.12, q + d * 0.12, 0.018, glow); a.parent = root; axes.append(a)
cat = 고양이("고양이", (1.2, -0.7, 0)); cat[0].rotation_euler.z = math.radians(150)

cams = {"front": camera("front", (0, -5.0, 1.5), (0, 0, 1.45), 26),
        "close": camera("close", (0.5, -3.6, 2.0), (0, 0, 1.75), 28),
        "low": camera("low", (1.3, -2.6, 0.25), (0, 0, 1.5), 21),
        "top": camera("top", (-1.6, -3.0, 4.4), (0, 0, 1.4), 24),
        "orbit": camera("orbit", (0, -6.0, 1.7), (0, 0, 1.4), 26)}

n = len(SEG)
for fr in range(1, T.end + 1):
    root.rotation_euler.z = 0.12 * math.sin(fr / 25); root.keyframe_insert("rotation_euler", frame=fr)
    a = 1.0 - 0.55 * (T.u(2, 0, 0.12, fr) if fr >= T.lines[2][0] else 0) - 0.42 * (T.u(3, 0.05, 0.5, fr) if fr >= T.lines[3][0] else 0)
    ca.default_value = a; ca.keyframe_insert("default_value", frame=fr)
    mo.hide_render = a < 0.06; mo.keyframe_insert("hide_render", frame=fr)
    for k, (c, ax) in enumerate(zip(cyls, axes)):
        g = T.u(2, k / n * 0.85, k / n * 0.85 + 0.15, fr) if fr >= T.lines[2][0] else 0     # 하나씩 끼워짐
        c.scale = (g, g, max(g, 0.001)); c.hide_render = g < 0.01
        ax.hide_render = not (T.lines[2][0] <= fr and g > 0.5 and (fr < T.lines[4][0] or fr >= T.lines[4][0]))
        c.keyframe_insert("scale", frame=fr); c.keyframe_insert("hide_render", frame=fr); ax.keyframe_insert("hide_render", frame=fr)
    hop = 0.3 * math.sin(math.pi * T.u(3, 0.1, 0.3, fr)) if fr >= T.lines[3][0] else 0
    cat[0].location.z = hop; cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.6 + 0.15 * math.sin(fr / 9), 0.3 * math.sin(fr / 13)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, False)
    oc, _ = cams["orbit"]; u = T.u(3, 0, 1, fr) if fr >= T.lines[3][0] else 0
    ang = math.radians(-90 + 60 * u); oc.location = (6.0 * math.cos(ang), 6.0 * math.sin(ang), 1.7 + 0.8 * u); oc.keyframe_insert("location", frame=fr)
    tc, _ = cams["top"]; tc.location.x = -1.6 + 1.4 * math.sin(fr / 40); tc.keyframe_insert("location", frame=fr)
끝(T, cams)
