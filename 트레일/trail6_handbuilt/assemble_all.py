# -*- coding: utf-8 -*-
"""부품별 생성물을 각각 IoU 로 정렬해 **전신으로 조립**하고 잰다.

    blender -b --python assemble_all.py

부품마다 **축정렬 회전 24가지** x 배율기준 2 를 훑어 배치를 고른다.

첫 판은 z 회전 4가지만 훑고 깊이 중심을 0 에 못박았다 — 정면 (x,z) 만 쓴 것이고,
trail2 가 "판 부조는 40도부터 무너진다"로 끝낸 그 방식이었다. 깊이 방향으로 누운
막대는 z 를 아무리 돌려도 안 세워져서 p19 는 깊이가 기준의 38배(4.756)가 됐다.

깊이 자는 **전신 생성 메시**가 준다 (122번: 전신 생성은 상대 위치·깊이를 공짜로
갖고 있다). 부품 마스크에 투영되는 전신 메시 정점의 y 2~98% 범위가 그 부품의
깊이 기준이다 (out/all/depth_ref.json).

깊이는 **목적함수가 아니라 가능성 필터**다. 곱으로 점수를 만들면 실루엣을 깊이와
맞바꿔서 오히려 나빠진다 (0.589 -> 0.477, p13 은 IoU 0.898 -> 0.123).

    깊이비가 [1/TOL, TOL] 안인 배치 중 **정면 IoU 최대**. 하나도 없으면 IoU 최대 + 표시

그리고 전부 한 씬에 넣어 전신 실루엣을 원화와 비교한다.

비교 대상: trail4 의 **전신 한 장 생성** 정면 IoU 0.827.
부품별로 나눠 만든 게 그걸 넘는지가 이 실험의 전부다.

산출: out/all/assembled.blend · out/all/assembled_{front,side,q}.png · out/all/report.json
"""
import bpy, os, sys, math, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ALL = os.path.join(HERE, "out", "all")
RES = 1024
U0, U1, Z0, Z1 = -0.6, 0.6, -0.1, 1.1
MODES = ("width", "height")
SWEEP_RES = 384        # 훑을 때만 작게. 최종은 RES
TOL = 2.5              # 깊이가 기준의 이 배를 넘으면 그 배치는 못 쓴다


def rots24():
    """정육면체 회전군 24개. 깊이로 누운 막대를 세우려면 z 회전만으론 안 된다."""
    import itertools
    out = []
    for perm in itertools.permutations(range(3)):
        for sx, sy, sz in itertools.product((1, -1), repeat=3):
            M = np.zeros((3, 3))
            sg = (sx, sy, sz)
            for i, j in enumerate(perm):
                M[i, j] = sg[i]
            if abs(np.linalg.det(M) - 1) < 1e-9:
                out.append(M)
    return out


ROTS = rots24()


def img(path, res=RES):
    im = bpy.data.images.load(path)
    a = np.array(im.pixels[:]).reshape(res, res, 4)[::-1]
    bpy.data.images.remove(im)
    return a


def shrink(m, res):
    """마스크를 res 로 줄인다 (훑을 때만). 최근접."""
    idx = (np.arange(res) * (m.shape[0] / res)).astype(int)
    return m[np.ix_(idx, idx)]


def load_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in set(bpy.data.objects) - before if o.type == 'MESH']
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = new[0]
    for o in new:
        o.select_set(True)
    if len(new) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o, np.array([v.co[:] for v in o.data.vertices])


def box_of(mask):
    ys, xs = np.nonzero(mask)
    wx = lambda c: U0 + c * (U1 - U0) / (RES - 1)
    wz = lambda r: Z1 - r * (Z1 - Z0) / (RES - 1)
    return wx(xs.min()), wx(xs.max()), wz(ys.max()), wz(ys.min())


def place(o, base, ri, mode, box, yref):
    """yref = (y0, y1) 깊이 기준. 깊이 중심을 0 에 못박지 않는다."""
    x0, x1, z0, z1 = box
    p = base @ ROTS[ri].T
    k = ((x1 - x0) / max(p[:, 0].max() - p[:, 0].min(), 1e-9) if mode == "width"
         else (z1 - z0) / max(p[:, 2].max() - p[:, 2].min(), 1e-9))
    p = p * k
    p[:, 0] += (x0 + x1) / 2 - (p[:, 0].min() + p[:, 0].max()) / 2
    p[:, 2] += (z0 + z1) / 2 - (p[:, 2].min() + p[:, 2].max()) / 2
    p[:, 1] += (yref[0] + yref[1]) / 2 - (p[:, 1].min() + p[:, 1].max()) / 2
    o.data.vertices.foreach_set("co", p.ravel())
    o.data.update()
    return k, float(p[:, 1].max() - p[:, 1].min())


def cams(sc):
    for n, loc, rot in (("front", (0, -2, 0.5), (math.radians(90), 0, 0)),
                        ("side", (2, 0, 0.5), (math.radians(90), 0, math.radians(90))),
                        ("q", (1.4 * math.sin(math.radians(40)),
                               -1.4 * math.cos(math.radians(40)), 0.5),
                         (math.radians(90), 0, math.radians(40)))):
        cd = bpy.data.cameras.new(n); cd.type = 'ORTHO'; cd.ortho_scale = 1.2
        c = bpy.data.objects.new(n, cd); c.location = loc; c.rotation_euler = rot
        sc.collection.objects.link(c)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'FLAT'
    sc.display.shading.color_type = 'MATERIAL'
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = RES
    sc.view_settings.view_transform = 'Standard'
    cams(sc)
    tmp = os.path.join(ALL, "_tmp.png")
    pids = json.load(open(os.path.join(ALL, "pids.json")))
    globals()["DREF"] = json.load(open(os.path.join(ALL, "depth_ref.json")))
    rep = []
    for pid in pids:
        glb = os.path.join(ALL, "p%d.glb" % pid)
        mp = os.path.join(ALL, "p%d_mask.png" % pid)
        if not os.path.exists(glb):
            print("MISS p%d" % pid); continue
        ref = img(mp)[..., 0] > 0.5
        box = box_of(ref)
        o, base = load_glb(glb)
        o.name = "p%d" % pid
        m = bpy.data.materials.new("m%d" % pid)
        m.diffuse_color = (0.55, 0.57, 0.72, 1)
        o.data.materials.clear(); o.data.materials.append(m)
        for x in bpy.context.scene.objects:
            x.hide_render = (x.type == 'MESH' and x is not o)
        sc.camera = bpy.data.objects["front"]
        yref = DREF.get(str(pid))
        if yref is None:
            print("MISS depth p%d" % pid); continue
        yr = (yref["y0"], yref["y1"])
        dref = yr[1] - yr[0]
        sc.render.resolution_x = sc.render.resolution_y = SWEEP_RES
        rs = shrink(ref, SWEEP_RES)
        best = None
        for ri in range(len(ROTS)):
            for mode in MODES:
                k, d = place(o, base, ri, mode, box, yr)
                sc.render.filepath = tmp
                bpy.ops.render.render(write_still=True)
                a = img(tmp, SWEEP_RES)[..., 3] > 0.5
                iou = (a & rs).sum() / max((a | rs).sum(), 1)
                dep = min(d, dref) / max(d, dref, 1e-9)     # 깊이 일치도
                ok = dep >= 1.0 / TOL                        # 필터. 점수에 안 곱한다
                cand = (ok, float(iou), float(dep), ri, mode, float(d))
                if best is None or cand[:2] > best[:2]:      # 통과한 것 우선, 그 안에서 IoU
                    best = cand
        sc.render.resolution_x = sc.render.resolution_y = RES
        place(o, base, best[3], best[4], box, yr)
        rep.append(dict(pid=pid, pass_depth=bool(best[0]), iou=best[1], depth_fit=best[2],
                        rot=best[3], mode=best[4], depth=best[5], depth_ref=float(dref),
                        faces=len(o.data.polygons), px=int(ref.sum())))
        print("FIT p%-3d %s IoU %.3f  깊이 %.3f/기준 %.3f (%.1f배)  rot%-2d %-6s  면 %7d"
              % (pid, "OK " if best[0] else "깊이X", best[1], best[5], dref,
                 max(best[5], dref) / max(min(best[5], dref), 1e-9),
                 best[3], best[4], len(o.data.polygons)))

    for x in bpy.context.scene.objects:
        x.hide_render = False
    # 전신 판정
    whole = np.load(os.path.join(HERE, "..", "trail4_gen3d", "pid_front.npy")) > 0
    for n in ("front", "side", "q"):
        sc.camera = bpy.data.objects[n]
        sc.render.filepath = os.path.join(ALL, "assembled_%s.png" % n)
        bpy.ops.render.render(write_still=True)
    a = img(os.path.join(ALL, "assembled_front.png"))[..., 3] > 0.5
    iou = (a & whole).sum() / (a | whole).sum()
    faces = sum(len(o.data.polygons) for o in bpy.context.scene.objects if o.type == 'MESH')
    npass = sum(1 for r in rep if r["pass_depth"])
    print("WHOLE 부품 %d개 (깊이 통과 %d개)  전신 정면 IoU %.3f  (전신 한 장 생성은 0.827)  총 면 %d"
          % (len(rep), npass, iou, faces))
    json.dump(dict(parts=rep, whole_iou=float(iou), faces=faces),
              open(os.path.join(ALL, "report.json"), "w"), indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ALL, "assembled.blend"))


main()
