"""3-13 슈뢰더 계단 — 기둥 위 얇은 계단 판 · 위에서는 안쪽 모서리(빨강)로 칸이 나뉘고 고양이가 오른다 · 밑에서 보면 처마 · 오목 모서리(파랑)가 반 칸 밀린 자리."""
import bpy, bmesh, math
from 장난감_공용 import *

T = 시작(); 무대(ARGS[1])
TR, RI, N, Z0, X0, HW, TH = 0.4, 0.25, 5, 0.9, -1.0, 0.5, 0.06
prof = [(X0, Z0)]
for k in range(N):
    x = X0 + TR * (k + 1); z = Z0 + RI * k; prof.append((x, z))
    if k < N - 1: prof.append((x, z + RI))
me = bpy.data.meshes.new("계단"); bm = bmesh.new()
L = [bm.verts.new((x, -HW, z)) for x, z in prof]; Rr = [bm.verts.new((x, HW, z)) for x, z in prof]
for i in range(len(prof) - 1): bm.faces.new((L[i], L[i + 1], Rr[i + 1], Rr[i]))
bm.to_mesh(me); bm.free()
st = bpy.data.objects.new("계단", me); bpy.context.scene.collection.objects.link(st)
st.data.materials.append(mat("판", (0.95, 0.85, 0.65), 0.6)); s = st.modifiers.new("두께", "SOLIDIFY"); s.thickness = TH; s.offset = 0
post = mat("기둥", (0.55, 0.45, 0.4), 0.8)
for x, z in ((X0 + 0.15, Z0), (X0 + TR * N - 0.15, Z0 + RI * (N - 1))):
    for y in (-0.42, 0.42): cyl(0.03, z - TH / 2, post, loc=(x, y, (z - TH / 2) / 2))
red, blue = mat("빨강", (1, 0.15, 0.12), 0.4, emit=1.5), mat("파랑", (0.15, 0.45, 1), 0.4, emit=1.5)
o = 0.04
reds = [bar((X0 + TR * (k + 1) - o, -HW, Z0 + RI * k + o), (X0 + TR * (k + 1) - o, HW, Z0 + RI * k + o), 0.02, red) for k in range(N - 1)]
blues = [bar((X0 + TR * (k + 1) + o, -HW, Z0 + RI * (k + 1) - o), (X0 + TR * (k + 1) + o, HW, Z0 + RI * (k + 1) - o), 0.02, blue) for k in range(N - 1)]
cat = 고양이("고양이", (X0 - 0.6, -0.1, 0)); cat[0].scale = (0.75, 0.75, 0.75)

cams = {"front": camera("front", (0.2, -4.2, 2.6), (0.0, 0, 1.25), 30),
        "close": camera("close", (-0.1, -2.6, 2.4), (-0.1, 0, 1.3), 30),
        "top": camera("top", (-1.6, -2.4, 3.4), (0.0, 0, 1.3), 28),
        "cat": camera("cat", (-0.9, -1.9, 1.9), (-0.3, 0, 1.3), 28),
        "side": camera("side", (2.6, -2.2, 1.1), (0, 0, 1.1), 28),
        "under": camera("under", (1.1, -1.7, 0.2), (-0.1, 0, 1.4), 22),
        "under2": camera("under2", (-1.2, -1.4, 0.15), (0.2, 0, 1.45), 22)}

def 위치(fr):                                         # 고양이: 땅 → 첫 칸 → 한 칸씩
    if fr < T.lines[1][0]: u = T.u(0, 0.1, 0.9, fr); return X0 - 0.6 + 0.2 * u, 0.0, 0 < u < 1
    if fr < T.lines[2][0]: return X0 - 0.4, 0.0, False
    u = T.u(2, 0.0, 1.0, fr) * N if fr < T.lines[3][0] else N - 0.001
    k = min(int(u), N - 1); f = u - int(u) if u < N else 1.0
    def spot(j): return (X0 - 0.4, 0.0) if j < 0 else (X0 + TR * j + TR / 2, Z0 + RI * j + TH / 2)
    (xa, za), (xb, zb) = spot(k - 1), spot(k); g = 0.5 - 0.5 * math.cos(math.pi * min(f * 1.4, 1))
    return xa + (xb - xa) * g, za + (zb - za) * g + 0.18 * math.sin(math.pi * min(f * 1.4, 1)), False
for fr in range(1, T.end + 1):
    on = lambda i, a=0, b=1: T.u(i, a, b, fr) if fr >= T.lines[i][0] else 0
    x, z, wk = 위치(fr); cat[0].location = (x, 0.0, z); cat[0].keyframe_insert("location", frame=fr)
    cat[1].rotation_euler = (0, -0.3, 0.2 * math.sin(fr / 9)); cat[1].keyframe_insert("rotation_euler", frame=fr)
    고양이_키(cat, fr, wk)
    for k, b in enumerate(reds):
        v = on(1, 0.3 + 0.12 * k, 0.45 + 0.12 * k) * (1 + 0.2 * math.sin(fr / 2.5)); b.scale = (max(v, 1e-3), max(v, 1e-3), 1); b.keyframe_insert("scale", frame=fr)
    for k, b in enumerate(blues):
        v = on(5, 0.1 + 0.12 * k, 0.25 + 0.12 * k) * (1 + 0.2 * math.sin(fr / 2.5)); b.scale = (max(v, 1e-3), max(v, 1e-3), 1); b.keyframe_insert("scale", frame=fr)
    for n, base in (("under", (1.1, -1.7, 0.2)), ("under2", (-1.2, -1.4, 0.15))):
        c = cams[n][0]; c.location.x = base[0] + 0.3 * math.sin(fr / 30); c.keyframe_insert("location", frame=fr)
    c = cams["side"][0]; u = on(3, 0, 1); c.location = (2.6 - 1.0 * u, -2.2 + 0.3 * u, 1.1 - 0.8 * u); c.keyframe_insert("location", frame=fr)
끝(T, cams)
