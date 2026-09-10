# -*- coding: utf-8 -*-
"""**잰 치수로 성당 문을 짓는다.** 윤곽선을 밀어내는 게 아니라 부피를 만든다.

    python gate_measure.py gate_front.json gate_spec.json
    blender -b --factory-startup --python gate_build.py -- gate_spec.json gate.blend [--probe]

**이 스크립트는 `gate_spec.json` 만 읽는다. 치수 상수를 여기 안 적는다**
(스킬 `art-to-3d-maps` 의 규율). 여기 있는 숫자는 전부 spec 값에서 나온 비율이다.

## 윤곽선을 밀면 왜 안 되나

`gate_model.py` 로 딴 선을 그대로 밀어봤더니 **종이 오린 것**이었다.
아치가 두께 0.35 m 짜리 판이라 옆에서 보면 없다. 성당의 아치는 **깊이가 있는 통로**고,
기둥은 원기둥이며, 열주는 **뒤로 물러나면서 작아진다.** 그건 원화에 안 적혀 있고
(원근으로 그려져 있으니) 3D 로 지어야 나온다.

## 짓는 것 여섯

    아치 리본   잰 프로필(행별 반너비) 안쪽 선 + 바깥 선 -> 닫힌 띠 -> Y 로 두껍게
    기둥        잰 x·폭으로 원기둥. 밑동과 주두를 붙인다
    첨탑        기둥 위 사각 축 + 원뿔
    십자가      잰 상자 안에 세로 기둥 + 가로 팔
    바닥        잰 행에서 시작하는 슬래브
    열주        칸 하나를 지어 **뒤로 물리며 반복** — 원화의 원근이 이것이다
"""
import json
import math
import os
import sys

import bmesh
import bpy

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SPEC = ARGV[0] if ARGV else "gate_spec.json"
DST = os.path.abspath(ARGV[1]) if len(ARGV) > 1 else "gate.blend"
HERE = os.path.dirname(os.path.abspath(__file__))
M = 2.435 / 1.7                                   # 1 m = 1.43 (채널 축척)


def mat(name, rgb, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = tuple(rgb) + (1.0,)
    p.inputs["Roughness"].default_value = rough
    return m


def ribbon(name, loop, depth, material):
    """XZ 평면의 닫힌 띠 -> Y 로 두꺼운 덩어리. **아치가 통로가 되는 자리.**"""
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    vs = [bm.verts.new((p[0], -depth / 2.0, p[1])) for p in loop]
    f = bm.faces.new(vs)
    res = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0.0, depth, 0.0),
                        verts=[v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    return ob


def cyl(name, r, h, loc, material, verts=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(material)
    return o


def box(name, size, loc, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    o.data.materials.append(material)
    return o


def cone(name, r, h, loc, material, verts=8):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, depth=h, location=loc)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(material)
    return o


# 잰 「선 덩어리 수」를 부품 수로 옮기는 나눗수. 셀에서 작은 물체 하나는
# 선 덩어리를 서넛 낸다(윤곽 + 크리스). **이 값만 손잡이다** — 굽고 재서 맞춘다
PER_PART = 3.0


def n_of(spec, key):
    """띠에 깔 부품 수. `derived` — 잰 덩어리 수 ÷ PER_PART."""
    return max(1, int(round(spec["ornament"][key] / PER_PART)))


def crockets(name, a, b, n, r, material):
    """두 점 사이를 따라가며 **작은 뾰족이**를 심는다. 고딕의 크로켓."""
    import mathutils
    va, vb = mathutils.Vector(a), mathutils.Vector(b)
    d = vb - va
    for i in range(n):
        t = (i + 0.5) / n
        p = va + d * t
        o = cone("%s%02d" % (name, i), r, r * 2.4, tuple(p), material, 5)
        o.rotation_euler = (0.0, math.radians(90), math.atan2(d.y, d.x))


def colonnettes(name, cx, cy, z0, z1, r, n, material):
    """기둥 둘레에 **가는 부속 기둥**을 두른다. 성당 기둥은 통짜가 아니다."""
    for i in range(n):
        a = math.pi * (-0.5 + (i + 0.5) / n)          # 앞면 반 바퀴만
        cyl("%s%02d" % (name, i), r * 0.20, z1 - z0,
            (cx + r * 0.92 * math.cos(a), cy + r * 0.92 * math.sin(a), (z0 + z1) / 2.0),
            material, 6)


def bands(name, cx, cy, z0, z1, r, n, material):
    """샤프트를 가로지르는 **마디 띠**. 세로 기둥에 가로선을 준다."""
    for i in range(n):
        z = z0 + (z1 - z0) * (i + 0.5) / n
        cyl("%s%02d" % (name, i), r * 1.18, (z1 - z0) * 0.02 + r * 0.10,
            (cx, cy, z), material, 8)


def build(spec, gold):
    W, H = spec["size_px"]
    Hm = spec["height_m"]["v"]
    T = spec["thickness_m"]["v"]
    wpp = Hm / float(H)                            # 화소당 m — 높이 하나에서 나온다
    top_z = (1.0 - spec["arch"]["top"]) * Hm
    bot_z = (1.0 - spec["arch"]["bottom"]) * Hm
    prof = spec["arch"]["profile"]
    cols = spec["columns"]["v"]
    band = cols[0][1] * W * wpp * 0.75             # derived — 기둥 폭의 3/4 을 아치 폭으로

    def z_of(t):
        return top_z + (bot_z - top_z) * t

    def hw_of(k):
        return prof[k][1] * W * wpp

    inner = [(-hw_of(k), z_of(prof[k][0])) for k in range(len(prof) - 1, -1, -1)]
    inner += [(hw_of(k), z_of(prof[k][0])) for k in range(len(prof))]
    outer = [(-hw_of(k) - band, z_of(prof[k][0])) for k in range(len(prof) - 1, -1, -1)]
    outer += [(hw_of(k) + band, z_of(prof[k][0])) for k in range(len(prof))]
    ribbon("arch", inner + outer[::-1], T, gold)
    na = max(4, n_of(spec, "arch"))
    for k in range(len(prof) - 1):                 # 아치 띠를 따라 **쐐기돌 마디**
        for s_ in (-1.0, 1.0):
            z0_, z1_ = z_of(prof[k][0]), z_of(prof[k + 1][0])
            x0_ = s_ * (hw_of(k) + band * 0.5)
            x1_ = s_ * (hw_of(k + 1) + band * 0.5)
            m_ = max(1, na // (2 * (len(prof) - 1)))
            crockets("vou%d%d_" % (k, s_ > 0), (x0_, -T * 0.55, z0_),
                     (x1_, -T * 0.55, z1_), m_, band * 0.16, gold)

    # 기둥 — **원기둥이다.** 원화에서는 납작한 띠로 보이지만 성당의 기둥은 둥글다
    spring = z_of(0.37)                            # 반너비가 다 자란 높이 = 어깨
    for i, (cxn, cwn) in enumerate(cols):
        cx = (cxn - 0.5) * W * wpp
        r = cwn * W * wpp / 2.0
        cyl("col%d" % i, r, spring - bot_z, (cx, -T * 0.62, (spring + bot_z) / 2.0), gold)
        cyl("colbase%d" % i, r * 1.35, r * 0.7, (cx, -T * 0.62, bot_z + r * 0.35), gold)
        cyl("colcap%d" % i, r * 1.3, r * 0.6, (cx, -T * 0.62, spring - r * 0.3), gold)
        # **장식은 손으로 안 놓고 잰 수만큼 깐다** — 이게 「조촐함」의 해법이다
        nc = max(3, n_of(spec, "column") // 2)
        colonnettes("colnet%d_" % i, cx, -T * 0.62, bot_z + r * 0.7, spring - r * 0.6,
                    r, nc, gold)
        # 마디를 nc//3 로 뒀더니 **나사산**이 됐다. 고딕의 밀도는 균일한 반복이 아니라
        # 큰 것 -> 작은 것의 층위다 — 마디는 서넛만 두고 수는 콜로네트에 준다
        bands("colband%d_" % i, cx, -T * 0.62, bot_z + r, spring - r, r,
              max(2, nc // 8), gold)
        # 첨탑 — 기둥 위로 솟는다. 원화의 뾰족한 것들
        sh = (top_z - spring) * 0.55
        box("spshaft%d" % i, (r * 1.5, r * 1.5, sh), (cx, -T * 0.62, spring + sh / 2.0), gold)
        cone("sptip%d" % i, r * 1.05, sh * 0.9,
             (cx, -T * 0.62, spring + sh + sh * 0.45), gold)
        np_ = max(3, n_of(spec, "pinnacle") // 8)
        for s_ in (-1.0, 1.0):
            crockets("spcr%d%d_" % (i, s_ > 0),
                     (cx + s_ * r * 1.0, -T * 0.62, spring + sh),
                     (cx, -T * 0.62, spring + sh + sh * 0.9), np_, r * 0.22, gold)
        bands("spband%d_" % i, cx, -T * 0.62, spring + sh * 0.1, spring + sh * 0.9,
              r * 1.05, max(2, np_ // 4), gold)

    # 십자가 — 잰 상자 안에 세운다
    cb = spec["cross"]["v"]
    cw = (cb["x"][1] - cb["x"][0]) * W * wpp
    cz0 = (1.0 - cb["y"][1]) * Hm
    cz1 = (1.0 - cb["y"][0]) * Hm
    ch = cz1 - cz0
    box("cross_v", (cw * 0.13, T * 0.5, ch), (0.0, 0.0, cz0 + ch / 2.0), gold)
    box("cross_h", (cw, T * 0.5, ch * 0.10), (0.0, 0.0, cz0 + ch * 0.62), gold)

    # 바닥
    fz = (1.0 - spec["floor"]["v"]) * Hm
    box("floor", (W * wpp * 2.2, W * wpp * 2.2, Hm * 0.02), (0.0, -W * wpp * 0.6, fz), gold)
    # 바닥 문양 — 원화의 바닥은 민무늬가 아니라 **방사 무늬**다. 밀도의 절반이 여기 있다
    nf = max(6, n_of(spec, "colonnade") // 8)
    for j in range(nf):
        a = math.pi * (0.08 + 0.84 * j / (nf - 1.0))
        # **전부 광장 한 점에 두고 제자리에서 돌린다.** 위치를 cos/sin 으로 흩고
        # 나서 돌렸더니 막대가 사방으로 흩어졌다 — 회전은 제 원점 기준이다
        box("fray%02d" % j, (Hm * 1.6, Hm * 0.012, Hm * 0.004),
            (0.0, -Hm * 0.55, fz + Hm * 0.011), gold)
        bpy.context.object.rotation_euler = (0.0, 0.0, a)

    # 열주 — 칸 하나를 **뒤로 물리며** 반복한다. 원화의 원근이 이것이다
    bay = spec["bay"]
    pw = cols[0][1] * W * wpp * 1.5
    ph = (spring - bot_z) * 1.5
    for k in range(bay["n"]):
        y = -T - bay["spacing_m"] * (k + 1)
        for s in (-1.0, 1.0):
            # 아치 제일 넓은 곳 + 아치 폭 + 기둥 셋 만큼 밖으로. 3 m 에 뒀더니
            # 열주가 문보다 커 보였다 — **열주는 문 밖에 있어야 문이 주인공이다**
            # 3.6 은 화각(±5.5 m) 밖이라 열주가 아예 안 잡혔다 — 원화는 열주가
            # **화면 양옆을 채우는** 그림이다. 안으로 당긴다
            x = s * (max(hw_of(k) for k in range(len(prof))) + band + pw * 1.1)
            box("pier%d_%d" % (k, s > 0), (pw, pw, ph), (x, y, fz + ph / 2.0), gold)
            box("lintel%d_%d" % (k, s > 0), (pw * 2.6, pw * 0.8, ph * 0.12),
                (x, y, fz + ph * 1.03), gold)
            nl = max(3, n_of(spec, "colonnade") // (bay["n"] * 6))
            colonnettes("bnet%d%d_" % (k, s > 0), x, y, fz, fz + ph, pw * 0.5, nl, gold)
            bands("bband%d%d_" % (k, s > 0), x, y, fz + ph * 0.1, fz + ph * 0.95,
                  pw * 0.5, max(2, nl // 2), gold)
            for j in range(nl):                    # 난간 — 칸 사이를 잇는 작은 기둥들
                t_ = (j + 0.5) / nl
                cyl("bal%d%d_%02d" % (k, s > 0, j), pw * 0.10, ph * 0.22,
                    (x, y + bay["spacing_m"] * (t_ - 0.5), fz + ph * 0.30), gold, 6)
    return wpp


def probe():
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 405, 720
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (
        0.028, 0.032, 0.070, 1.0)
    bpy.ops.object.light_add(type='SUN', location=(6, -20, 18))
    s = bpy.context.object
    s.data.energy = 2.8
    s.data.color = (1.0, 0.92, 0.72)
    s.rotation_euler = (0.80, 0.0, 0.35)
    cd = bpy.data.cameras.new("cam")
    cd.lens = 22
    cd.sensor_fit = 'VERTICAL'
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    # 높이 11 m 를 30mm 세로에 담으려면 12 m 는 물러나야 한다. 21 m 에 뒀더니
    # 바닥이 화면 절반이었다 — **거리가 아니라 높이와 겨냥이 문제였다**
    cam.location = (0.8, -12.0, 1.7)
    # 90도가 수평이고 **키우면 위를 본다.** 77 로 뒀더니 바닥만 나왔다
    cam.rotation_euler = (math.radians(104), 0.0, math.radians(1.5))
    src = open(os.path.join(os.path.dirname(HERE), "cel.py"), encoding="utf-8").read()
    ns = {"__file__": "cel.py", "__name__": "cel"}
    exec(src.split("\ndef main():")[0], ns)
    ns["cel"](sc)
    sc.render.filepath = os.path.join(HERE, "out", "gate_build.png")
    bpy.ops.render.render(write_still=True)
    print("PROBE " + sc.render.filepath)


def main():
    spec = json.load(open(os.path.join(HERE, SPEC), encoding="utf-8"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    gold = mat("gold", (0.94, 0.82, 0.26), 0.35)
    wpp = build(spec, gold)
    print("GATE_BUILD 물체 %d개 · 높이 %.1fm · 화소당 %.4fm"
          % (len(bpy.data.objects), spec["height_m"]["v"], wpp))
    bpy.ops.wm.save_as_mainfile(filepath=DST)
    print("SAVED " + DST)
    if "--probe" in ARGV:
        probe()


main()
