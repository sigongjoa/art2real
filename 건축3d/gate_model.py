# -*- coding: utf-8 -*-
"""**딴 윤곽선을 그대로 세운다.** 커브로 넣고 두께를 준다.

    python gate_trace.py D:/imggen/blades6/r6_gate_front.png gate_front.json
    blender -b --factory-startup --python gate_model.py -- gate_front.json gate_front.blend [--probe]

## 커브로 넣는 이유 — 구멍

첨두아치는 **금색 덩어리에 뚫린 구멍**이다. 메시 면으로 만들면 구멍을 못 뚫어
아치가 막힌 판이 되는데, 블렌더의 2D 커브는 스플라인을 여럿 주면 짝홀 규칙으로
알아서 뚫는다. `gate_trace.py` 가 바깥선과 구멍선을 나눠 주는 게 그래서다.

## 처음 판이 왜 색종이였나

`art3d.py` 의 판 310개를 그대로 세웠었다. 그건 **톤 분할**이라 같은 기둥이
밝은 면·어두운 면으로 쪼개지고 하늘 조각을 버리면 그 자리가 구멍이 된다.
형태를 원하면 **형태의 경계**를 따야 한다 — 그게 이 파일의 입력이다.

## 값의 출처

    높이 11 m        사람이 준 절대값 **하나**. 화소당 m 은 여기서 나온다
    앞뒤 기복        `art3d_front/depth.npy` (크리스 인플레이션) 의 덩어리 안쪽 평균 — 잰 값
    두께             짐작. 옆모습 원화가 없다
"""
import json
import os
import sys

import bpy
import numpy as np

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = ARGV[0] if ARGV else "gate_front.json"
DST = os.path.abspath(ARGV[1]) if len(ARGV) > 1 else "gate_front.blend"
HERE = os.path.dirname(os.path.abspath(__file__))

M = 2.435 / 1.7                 # 1 m = 1.43 (채널 축척)
GATE_H = 11.0                   # **measured 아님 — 사람이 정한 절대값 하나**
THICK = 0.35                    # 판 두께(m). 짐작
RELIEF = 1.8                    # 제일 앞과 제일 뒤의 거리(m). depth.npy 로 나눈다
DEPTH_NPY = "art3d_front/depth.npy"


def mat(name, rgb, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = tuple(rgb) + (1.0,)
    p.inputs["Roughness"].default_value = rough
    return m


def shape(name, outer, holes, material, thick):
    """바깥선 하나 + 구멍선 여럿 -> **구멍 뚫린 두께 있는 판.**

    2D 커브는 제 로컬 XY 에 눕는다. 정면으로 세우려고 물체를 X 로 90도 돌린다."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '2D'
    cu.fill_mode = 'BOTH'
    cu.extrude = thick / 2.0
    cu.resolution_u = 1
    for ring in [outer] + list(holes):
        sp = cu.splines.new('POLY')
        sp.points.add(len(ring) - 1)
        for i, (x, y) in enumerate(ring):
            sp.points[i].co = (x, y, 0.0, 1.0)
        sp.use_cyclic_u = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = (1.5707963, 0.0, 0.0)
    cu.materials.append(material)
    return ob


def main():
    js = json.load(open(os.path.join(HERE, SRC), encoding="utf-8"))
    W, H = js["size"]
    wpp = GATE_H / float(H)                     # 화소당 m
    cx = W / 2.0
    dep = None
    p = os.path.join(HERE, DEPTH_NPY)
    if os.path.exists(p):
        dep = np.load(p)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    gold = mat("gold", (0.94, 0.82, 0.26), 0.35)

    def w(pt):
        return ((pt[0] - cx) * wpp * M, (H - pt[1]) * wpp * M)

    n = 0
    for i, s in enumerate(js["shapes"]):
        o = [w(p) for p in s["outer"]]
        hs = [[w(p) for p in h] for h in s["holes"]]
        y = 0.0
        if dep is not None:                     # **잰 기복** — 덩어리 안쪽 평균
            ys = [int(pt[1] * dep.shape[0] / H) for pt in s["outer"]]
            xs = [int(pt[0] * dep.shape[1] / W) for pt in s["outer"]]
            ys = np.clip(ys, 0, dep.shape[0] - 1)
            xs = np.clip(xs, 0, dep.shape[1] - 1)
            d = float(np.nanmean(dep[ys, xs]))
            lo, hi = float(np.nanmin(dep)), float(np.nanmax(dep))
            y = -(d - lo) / max(hi - lo, 1e-6) * RELIEF * M
        ob = shape("gate%02d" % i, o, hs, gold, THICK * M)
        ob.location.y = y
        n += 1
    print("GATE_MODEL %d덩어리 · 구멍 %d · 높이 %.1fm · 화소당 %.4fm"
          % (n, sum(len(s["holes"]) for s in js["shapes"]), GATE_H, wpp))
    bpy.ops.wm.save_as_mainfile(filepath=DST)
    print("SAVED " + DST)
    if "--probe" in ARGV:
        probe()


def probe():
    """정면에서 한 장 굽는다. **지어놓고 안 보면 또 눈으로 고치게 된다.**"""
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 405, 720
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (
        0.028, 0.032, 0.070, 1.0)
    bpy.ops.object.light_add(type='SUN', location=(6 * M, -20 * M, 18 * M))
    s = bpy.context.object
    s.data.energy = 2.8
    s.data.color = (1.0, 0.92, 0.72)
    s.rotation_euler = (0.80, 0.0, 0.35)
    cd = bpy.data.cameras.new("cam")
    cd.lens = 34
    cd.sensor_fit = 'VERTICAL'
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = (0.0, -26.0 * M, 5.5 * M)
    cam.rotation_euler = (1.5707963, 0.0, 0.0)
    src = open(os.path.join(os.path.dirname(HERE), "cel.py"), encoding="utf-8").read()
    ns = {"__file__": "cel.py", "__name__": "cel"}
    exec(src.split("\ndef main():")[0], ns)
    ns["cel"](sc)
    sc.render.filepath = os.path.join(HERE, "out", "gate_front.png")
    bpy.ops.render.render(write_still=True)
    print("PROBE " + sc.render.filepath)


main()
