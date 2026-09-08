# -*- coding: utf-8 -*-
"""원화 3판을 UV 아틀라스에 굽는다.

    blender -b --python bake_art.py -- out/atlas.blend out/baked

절차
  1) 면마다 법선으로 판을 고르고 **광선으로 가려짐 검사** (앞에 딴 면 있으면 탈락)
  2) 면의 UV 삼각형을 아틀라스에 래스터화, 텍셀마다 무게중심으로 3D 점을 복원
  3) 그 점을 고른 판에 투영해 원화 색을 읽는다
  4) 어느 판도 못 본 면은 재질 클래스 색으로 채운다 (표면의 21.2%)
  5) 시임 틈은 팽창으로 메운다 — 안 하면 UV 경계에 검은 실선이 생긴다
"""
import math
import os
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, PRE = os.path.abspath(argv[0]), os.path.abspath(argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = 2048
RES, U0, U1, Z0, Z1 = 1024, -0.6, 0.6, -0.1, 1.1
CLSCOL = {0: (150, 150, 155), 1: (238, 238, 242), 2: (26, 26, 32), 3: (217, 179, 71)}
# 부품 하나만 구울 땐 그 부품의 실측색으로 덮는다 (전신 팔레트는 armor = 흰색이라
# 라벤더 견갑이 하얗게 나온다). 안 주면 기본값 그대로.
if os.environ.get("BAKE_CLSCOL"):
    import json as _j
    CLSCOL.update({int(k): tuple(v) for k, v in _j.loads(os.environ["BAKE_CLSCOL"]).items()})

RGB = {k: np.load(os.path.join(HERE, f"rgb_{k}.npy")) for k in ("front", "side", "back")}
CLS = {k: np.load(os.path.join(HERE, f"cls_{k}.npy")) for k in ("front", "side", "back")}
SNAP = {k: np.load(os.path.join(HERE, f"snap_{k}.npy")) for k in ("front", "side", "back")}
SNAP_MAX = 45          # 이보다 멀면 스냅하지 않고 클래스 단색 (전신 1024 창 기준 4.4%)

bpy.ops.wm.open_mainfile(filepath=SRC)
o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
me = o.data
nf = len(me.polygons)
print(f"면 {nf:,}  UV {me.uv_layers[0].name}")

cen = np.empty(nf * 3); me.polygons.foreach_get("center", cen); cen = cen.reshape(-1, 3)
nor = np.empty(nf * 3); me.polygons.foreach_get("normal", nor); nor = nor.reshape(-1, 3)
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
uv = np.empty(len(me.loops) * 2); me.uv_layers[0].data.foreach_get("uv", uv)
uv = uv.reshape(-1, 2)
ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", lv)

VIEWS = [("front", np.array([0., 1., 0.])), ("sidep", np.array([-1., 0., 0.])),
         ("siden", np.array([1., 0., 0.])), ("back", np.array([0., -1., 0.]))]
MAPKEY = {"front": "front", "sidep": "side", "siden": "side", "back": "back"}
score = np.stack([-nor[:, 1], nor[:, 0], -nor[:, 0], nor[:, 1]], 1)
order = np.argsort(-score, 1)

t0 = time.time()
# 가려짐만 통과하면 그 판으로 확정하면 안 된다. 원화 측면 판에는 검이 아예 없어서
# 검 면은 "안 가려졌는데 판에는 없는" 상태가 되고, 45px 밖이라 스냅도 못 해
# 단색 회색으로 떨어진다(측면 회색의 대부분이 검이었다).
# 그래서 **색이 실제로 나오는 판**을 찾을 때까지 우선순위대로 계속 본다.
def usable(v, c):
    name = VIEWS[v][0]; key = MAPKEY[name]
    u = c.x if name == "front" else (-c.x if name == "back" else c.y)
    px = int(np.clip((u - U0) / (U1 - U0) * RES, 0, RES - 1))
    py = int(np.clip((Z1 - c.z) / (Z1 - Z0) * RES, 0, RES - 1))
    return RGB[key][py, px, 3] >= 128 or SNAP[key][py, px, 2] <= SNAP_MAX

fview = np.full(nf, -1, np.int8)
rescued = 0
for i in range(nf):
    c = Vector(cen[i])
    first = -1
    for slot in range(4):
        v = order[i, slot]
        if score[i, v] <= 0.05:
            break
        dv = Vector(VIEWS[v][1])
        hit, loc, _, _ = o.ray_cast(c - dv * 4.0, dv)
        if not (hit and (loc - c).length <= 0.004):
            continue
        if first < 0:
            first = v
        if usable(v, c):
            fview[i] = v
            if v != first:
                rescued += 1
            break
    if fview[i] < 0:
        fview[i] = first          # 어느 판에서도 색이 안 나오면 1순위로 (단색이 된다)
print(f"  다음 판으로 넘겨 살린 면 {rescued:,}")
seenf = int((fview >= 0).sum())
print(f"판 배정 {time.time()-t0:.0f}s  {seenf:,}/{nf:,} 면 ({seenf/nf*100:.1f}%)")


def sample(key, P, mirror):
    """측면 판은 화면 x 가 **월드 y** 로 고정 매핑돼 있다. -x 쪽 면도 깊이 y 는
    같은 좌표다. 좌우 대칭 가정으로 (-x,y,z) 를 (+x,y,z) 의 색으로 칠하는 것이므로
    **뒤집으면 안 된다**. 뒤집었더니 발톱(y -0.17)이 뒷꿈치(y +0.17)를 읽었다."""
    u = P[:, 0] if key == "front" else (-P[:, 0] if key == "back" else P[:, 1])
    px = np.clip(((u - U0) / (U1 - U0) * RES).astype(int), 0, RES - 1)
    py = np.clip(((Z1 - P[:, 2]) / (Z1 - Z0) * RES).astype(int), 0, RES - 1)
    # 실루엣 밖이면 가까운 유효 화소로 스냅. 너무 멀면 그대로 두고 대체색이 되게 한다
    sn = SNAP[key][py, px]
    far = sn[:, 2] > SNAP_MAX
    py2 = np.where(far, py, sn[:, 0]); px2 = np.where(far, px, sn[:, 1])
    # 색은 45px 안에서만 당겨온다(멀면 거짓말이 된다). 다만 **클래스는 거리와
    # 무관하게 항상 스냅 위치**에서 읽는다 — 안 그러면 실루엣 밖에서 배경 0 을
    # 읽어 대체색이 회색이 된다. 검이 그 경우였다(측면 판에 검이 없다).
    return RGB[key][py2, px2], CLS[key][sn[:, 0], sn[:, 1]]


img = np.zeros((ATLAS, ATLAS, 3), np.float32)
hit = np.zeros((ATLAS, ATLAS), bool)
t0 = time.time()
for i in range(nf):
    n = lt[i]
    idx = lv[ls[i]:ls[i] + n]
    U = uv[ls[i]:ls[i] + n]
    P3 = co[idx]
    tris = [(0, j, j + 1) for j in range(1, n - 1)]
    for a, b, c in tris:
        t_uv = U[[a, b, c]]
        t_p3 = P3[[a, b, c]]
        sx = t_uv[:, 0] * (ATLAS - 1)
        sy = (1.0 - t_uv[:, 1]) * (ATLAS - 1)
        x0 = max(int(np.floor(sx.min())), 0); x1 = min(int(np.ceil(sx.max())) + 1, ATLAS)
        y0 = max(int(np.floor(sy.min())), 0); y1 = min(int(np.ceil(sy.max())) + 1, ATLAS)
        if x1 <= x0 or y1 <= y0:
            continue
        gy, gx = np.mgrid[y0:y1, x0:x1]
        px = gx + 0.5; py = gy + 0.5
        d = ((sy[1] - sy[2]) * (sx[0] - sx[2]) + (sx[2] - sx[1]) * (sy[0] - sy[2]))
        if abs(d) < 1e-9:
            continue
        w0 = ((sy[1] - sy[2]) * (px - sx[2]) + (sx[2] - sx[1]) * (py - sy[2])) / d
        w1 = ((sy[2] - sy[0]) * (px - sx[2]) + (sx[0] - sx[2]) * (py - sy[2])) / d
        w2 = 1.0 - w0 - w1
        m = (w0 >= -0.002) & (w1 >= -0.002) & (w2 >= -0.002)
        if not m.any():
            continue
        pts = (w0[m][:, None] * t_p3[0] + w1[m][:, None] * t_p3[1] + w2[m][:, None] * t_p3[2])
        v = fview[i]
        if v >= 0:
            name = VIEWS[v][0]
            rgba, cls = sample(MAPKEY[name], pts, False)
            col = rgba[:, :3].astype(np.float32)
            bad = rgba[:, 3] < 128                     # 판 밖으로 나간 텍셀
            if bad.any():
                col[bad] = [CLSCOL[1]] * int(bad.sum()) if False else np.array(
                    [CLSCOL[int(x)] for x in cls[bad]], np.float32)
        else:
            _, cls = sample("front", pts, False)
            col = np.array([CLSCOL[int(x)] for x in cls], np.float32)
        img[gy[m], gx[m]] = col
        hit[gy[m], gx[m]] = True
print(f"래스터화 {time.time()-t0:.0f}s  채워진 텍셀 {int(hit.sum()):,} "
      f"({hit.mean()*100:.1f}%)")

# 시임 틈 메우기 — 안 하면 UV 경계에 검은 실선이 생긴다
for _ in range(6):
    e = ~hit
    if not e.any():
        break
    acc = np.zeros_like(img); cnt = np.zeros(hit.shape)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        s_ = np.roll(np.roll(img, dy, 0), dx, 1)
        h_ = np.roll(np.roll(hit, dy, 0), dx, 1)
        acc += s_ * h_[..., None]; cnt += h_
    f = e & (cnt > 0)
    img[f] = acc[f] / cnt[f][:, None]
    hit |= f
img[~hit] = CLSCOL[0]

out = np.clip(img, 0, 255).astype(np.uint8)
np.save(PRE + "_atlas.npy", out)
bi = bpy.data.images.new("baked", ATLAS, ATLAS)
# 감마를 손으로 걸지 않는다. 픽셀에 sRGB 값을 그대로 넣고 colorspace 를 sRGB 로
# 두면 저장/로드가 왕복한다. 2.2 를 미리 걸었더니 저장 때 한 번 더 변환돼
# 전신이 새까맣게 나왔다.
buf = np.zeros((ATLAS, ATLAS, 4), np.float32)
buf[..., :3] = out[::-1] / 255.0
buf[..., 3] = 1.0
bi.pixels = buf.ravel()
bi.filepath_raw = PRE + "_atlas.png"
bi.file_format = 'PNG'
bi.save()
print("SAVED " + PRE + "_atlas.png")

m = bpy.data.materials.new("baked")
m.use_nodes = True
nt = m.node_tree
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bi
tex.image.colorspace_settings.name = 'sRGB'
# 셀 원화를 그대로 보려면 셰이딩을 얹지 않는다 — Emission 으로 색만 낸다
em = nt.nodes.new("ShaderNodeEmission")
nt.links.new(tex.outputs["Color"], em.inputs["Color"])
nt.links.new(em.outputs["Emission"], nt.nodes["Material Output"].inputs["Surface"])
me.materials.clear(); me.materials.append(m)
bpy.ops.wm.save_as_mainfile(filepath=PRE + ".blend")
print("SAVED " + PRE + ".blend")
