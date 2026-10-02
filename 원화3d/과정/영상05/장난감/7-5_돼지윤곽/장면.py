"""7-5 돼지 윤곽 = 앞/뒤 경계(Bénard & Hertzmann 2019 그림 1.1) — 정면에선 테두리 선, 돌려 보면 몸통을 두른 띠. 고양이가 돼지 둘레를 걸으면 띠가 고양이 쪽 시선에 맞춰 미끄러진다."""
import bpy, math
from mathutils import Vector
from 장난감_공용 import *

def 키(o, fr, *props):
    for q in props: o.keyframe_insert(q, frame=fr)

_dot = []
def 점(m):
    if not _dot:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=12, ring_count=6); u = bpy.context.object
        for f in u.data.polygons: f.use_smooth = True
        u.data.materials.append(m); _dot.append(u.data); bpy.data.objects.remove(u)
    o = bpy.data.objects.new("윤곽", _dot[0]); bpy.context.scene.collection.objects.link(o); o.scale = (0.03,) * 3; return o

def 윤곽점들(c, a, b, cc, d, n, grow=1.025):     # 타원체(축 a,b,cc · 중심 c)의 시선 d(수평) 윤곽 고리
    u = Vector((a * a * d.y, -b * b * d.x, 0)); lam = 1 / math.sqrt((u.x / a) ** 2 + (u.y / b) ** 2); u *= lam
    return [c + (u * math.cos(t) + Vector((0, 0, cc)) * math.sin(t)) * grow for t in (2 * math.pi * k / n for k in range(n))]

T = 시작(); 무대(ARGS[1])
pink, dpink, ink = mat("돼지", (0.98, 0.68, 0.72), 0.6), mat("코", (0.9, 0.5, 0.58), 0.6), mat("선", (0.06, 0.06, 0.12), 0.4)
BC, BA, BB, BCC = Vector((0, 0, 0.78)), 0.65, 0.4, 0.4
HC, HR = Vector((0.72, 0, 0.9)), 0.3
ball(1, pink, loc=BC, scale=(BA, BB, BCC)); ball(HR, pink, loc=HC)
cyl(0.12, 0.14, dpink, loc=(1.04, 0, 0.85), rot=(0, math.pi / 2, 0))
for s in (-1, 1):
    cone(0.09, 0.16, pink, loc=(0.66, s * 0.17, 1.2), rot=(s * 0.3, -0.3, 0))
    ball(0.035, mat("눈", (0.05, 0.05, 0.05), 0.2), loc=(0.95, s * 0.12, 0.98))
    for x in (-0.38, 0.38): cyl(0.08, 0.5, pink, loc=(x, s * 0.2, 0.25))
for k in range(4): ball(0.035, pink, loc=(-0.66 - 0.05 * k, 0.03 * math.sin(k * 2), 0.85 + 0.05 * math.cos(k * 2)))
NB, NH = 110, 60
body = [점(ink) for _ in range(NB)]; head = [점(ink) for _ in range(NH)]
cat = 고양이("고양이", (0.0, -1.8, 0)); cat[0].rotation_euler.z = math.pi / 2
cams = {"front": camera("front", (0.15, -9.5, 0.85), (0.15, 0, 0.8), 62),
        "close": camera("close", (0.3, -7.0, 0.9), (0.3, 0, 0.85), 80),
        "orbit": camera("orbit", (0.15, -3.2, 0.85), (0.15, 0, 0.8), 30),
        "top": camera("top", (0.4, -1.9, 3.3), (0.1, 0, 0.6), 26),
        "side2": camera("side2", (2.0, -1.5, 1.6), (0.1, 0, 0.8), 28),
        "close2": camera("close2", (0.9, -1.3, 1.5), (0.0, 0, 0.8), 30),
        "catcam": camera("catcam", (0.0, -2.6, 0.5), (0.1, 0, 0.8), 24)}
L = T.lines
for fr in range(1, T.end + 1):
    # 시선: 0-4 줄은 정면(카메라) · 5 줄은 고양이가 앞 → 오른쪽(주둥이 쪽)으로 돌며 본다 · 6 줄은 정면으로 돌아옴
    g = T.u(5, 0.05, 0.85, fr) * (1 - T.u(6, 0.0, 0.5, fr)); phi = math.radians(-90 + 80 * g)
    cp = Vector((0.1 + 1.8 * math.cos(phi), 1.8 * math.sin(phi), 0))
    cat[0].location = cp; cat[0].rotation_euler.z = phi + math.pi; 키(cat[0], fr, "location", "rotation_euler")
    cat[1].rotation_euler = (0, -0.35, 0); 키(cat[1], fr, "rotation_euler")
    고양이_키(cat, fr, 0 < T.u(5, 0.05, 0.85, fr) < 1 or 0 < T.u(6, 0, 0.5, fr) < 1)
    d = -Vector((math.cos(phi), math.sin(phi), 0))
    for o, p in zip(body, 윤곽점들(BC, BA, BB, BCC, d, NB)): o.location = p; 키(o, fr, "location")
    for o, p in zip(head, 윤곽점들(HC, HR, HR, HR, d, NH, 1.04)): o.location = p; 키(o, fr, "location")
    a = math.radians(-90 + 60 * T.u(2, 0, 1, fr)); oc = cams["orbit"][0]
    oc.location = (0.15 + 3.2 * math.cos(a), 3.2 * math.sin(a), 0.85 + 1.5 * T.u(2, 0, 1, fr)); 키(oc, fr, "location")
    c = cams["top"][0]; c.location.x = 0.4 - 0.5 * math.sin(fr / 45); 키(c, fr, "location")
    c = cams["catcam"][0]; c.location = cp * 1.45 + Vector((0, 0, 0.5)); 키(c, fr, "location")
끝(T, cams)
