"""11-7 점토 개 → 블록 템플릿(지온18 Princeton p29) — 한 덩어리 점토 개 → 부위마다 반투명 상자가 끼워지며 점토가 부품 색으로 나뉨 → 점토를 빼면 블록 개 · 고양이가 다가가자 블록 꼬리 흔들기."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

def mball(name, elems, m, alpha_mat=False):
    mb = bpy.data.metaballs.new(name); mb.resolution = 0.05; mb.render_resolution = 0.03; mb.threshold = 0.6
    for p, q, r in elems:
        p, q = Vector(p), Vector(q); d = q - p; e = mb.elements.new()
        if d.length < 1e-4: e.type = "BALL"; e.co = p; e.radius = r
        else: e.type = "CAPSULE"; e.co = (p + q) / 2; e.radius = r; e.size_x = d.length / 2; e.rotation = Vector((1, 0, 0)).rotation_difference(d)
    o = bpy.data.objects.new(name, mb); bpy.context.scene.collection.objects.link(o); o.data.materials.append(m); return o

T = 시작(); 무대(ARGS[1])
PARTS = {  # 부위: 메타볼 요소들, 상자(크기, 중심), 색
    "몸통": ([((-0.45, 0, 0.78), (0.45, 0, 0.82), 0.3)], ((1.25, 0.5, 0.5), (0, 0, 0.8)), (0.6, 0.75, 0.95)),
    "머리": ([((0.78, 0, 1.18), (0.78, 0, 1.18), 0.27), ((0.92, 0, 1.1), (1.1, 0, 1.08), 0.12)], ((0.62, 0.42, 0.42), (0.88, 0, 1.15)), (0.98, 0.6, 0.45)),
    "앞다리1": ([((0.35, -0.17, 0.65), (0.37, -0.17, 0.1), 0.1)], ((0.17, 0.17, 0.62), (0.36, -0.17, 0.36)), (0.45, 0.78, 0.6)),
    "앞다리2": ([((0.35, 0.17, 0.65), (0.37, 0.17, 0.1), 0.1)], ((0.17, 0.17, 0.62), (0.36, 0.17, 0.36)), (0.45, 0.78, 0.6)),
    "뒷다리1": ([((-0.35, -0.17, 0.65), (-0.37, -0.17, 0.1), 0.1)], ((0.17, 0.17, 0.62), (-0.36, -0.17, 0.36)), (0.7, 0.55, 0.9)),
    "뒷다리2": ([((-0.35, 0.17, 0.65), (-0.37, 0.17, 0.1), 0.1)], ((0.17, 0.17, 0.62), (-0.36, 0.17, 0.36)), (0.7, 0.55, 0.9)),
    "꼬리": ([((-0.6, 0, 0.88), (-0.85, 0, 1.2), 0.07)], ((0.36, 0.12, 0.12), (-0.72, 0, 1.04)), (0.98, 0.72, 0.3)),
}
clay_m = mat("점토", (0.9, 0.72, 0.55), 0.75)
clay = mball("한덩어리", [e for v in PARTS.values() for e in v[0]], clay_m)
seg, boxes = [], []
boxm = mat("상자틀", (1.0, 0.55, 0.15), 0.4, alpha=True); BA = alpha_of(boxm)
if hasattr(boxm, "show_transparent_back"): boxm.show_transparent_back = False
tail_piv = empty("꼬리축", loc=(-0.6, 0, 0.88))
for k, (name, (el, (sz, c), col)) in enumerate(PARTS.items()):
    seg.append(mball("부품%d" % k, el, mat(name, col, 0.7)))                 # 이름이 달라 서로 안 붙음 → 부품별 덩어리
    b = box(sz, boxm, loc=c, bevel=0.02)
    blk = box(sz, mat("블록" + name, col, 0.55), loc=c, bevel=0.03)
    if name == "꼬리":
        b.rotation_euler.y = blk.rotation_euler.y = -math.atan2(0.32, 0.25)
        blk.parent = tail_piv; blk.location = Vector(c) - tail_piv.location
    boxes.append((b, blk, Vector(c)))
cat = 고양이("고양이", (2.6, -0.4, 0)); cat[0].rotation_euler.z = math.pi

cams = {"front": camera("front", (0.4, -5.4, 1.1), (0.3, 0, 0.9), 25),
        "close": camera("close", (1.2, -2.8, 1.3), (0.2, 0, 0.85), 26),
        "low": camera("low", (1.6, -2.0, 0.2), (0, 0, 0.8), 21),
        "top": camera("top", (-1.4, -2.6, 3.6), (0.1, 0, 0.7), 24),
        "orbit": camera("orbit", (0.3, -5.4, 1.2), (0.2, 0, 0.8), 25),
        "catcam": camera("catcam", (3.2, -1.4, 0.55), (1.0, 0, 0.7), 24)}

def u_(li, a, b, fr): return T.u(li, a, b, fr) if fr >= T.lines[li][0] else 0.0
n = len(boxes)
for fr in range(1, T.end + 1):
    split = u_(2, 0.5, 0.6, fr) > 0.5; tmpl = u_(3, 0.1, 0.3, fr) > 0.5
    clay.hide_render = split; clay.keyframe_insert("hide_render", frame=fr)
    for o in seg: o.hide_render = not split or tmpl; o.keyframe_insert("hide_render", frame=fr)
    for k, (b, blk, c) in enumerate(boxes):
        g = u_(2, k / n * 0.5, k / n * 0.5 + 0.15, fr)
        b.location = c + Vector((0, 0, 1.8 * (1 - g))); b.hide_render = g <= 0 or tmpl
        blk.hide_render = not tmpl
        b.keyframe_insert("location", frame=fr); b.keyframe_insert("hide_render", frame=fr); blk.keyframe_insert("hide_render", frame=fr)
    wag = u_(4, 0.4, 0.5, fr)
    tail_piv.rotation_euler.z = 0.6 * math.sin(fr / 2.5) * wag; tail_piv.keyframe_insert("rotation_euler", frame=fr)
    w = u_(4, 0, 0.4, fr)
    cat[0].location = (2.6 - 0.9 * w, -0.4, 0); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.2, 0.3 * math.sin(fr / 13)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, 0 < w < 1)
    oc, _ = cams["orbit"]; v = u_(3, 0, 1, fr)
    ang = math.radians(-90 + 60 * v); oc.location = (5.4 * math.cos(ang), 5.4 * math.sin(ang), 1.2 + 1.0 * v); oc.keyframe_insert("location", frame=fr)
    tc, _ = cams["top"]; tc.location.x = -1.4 + 1.2 * math.sin(fr / 40); tc.keyframe_insert("location", frame=fr)
끝(T, cams)
