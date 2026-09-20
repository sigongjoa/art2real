"""**Knife Project 로 판 경계를 껍질에 새긴다.** GUI 블렌더에서 돌려야 한다.

    blender --python knife_gui.py -- <buildspec.json> [출력.blend]     ← `-b` 를 붙이지 않는다

왜 GUI 인가: `bpy.ops.mesh.knife_project()` 는 **화면 방향으로 투영**하므로 3D 뷰포트
컨텍스트가 필요하다. `-b` 에는 창이 없어 못 쓴다. 헤드리스 대안으로
`bpy.ops.mesh.intersect()` 를 써봤지만 **예외 없이 통과하면서 면을 하나도 안 늘렸다**
(9,216 -> 9,216). 그래서 GUI 로 온다.

순서는 영상(sUMDGjzSw_E)의 공정 그대로:
    껍질을 만든다 -> **판 경계를 새긴다(Knife Project)** -> 그 면을 법선으로 민다
자르기 전에 밀면 오프셋이 면을 가로질러 **가로 줄무늬로 찢어진다** (실측).
"""
import json
import math
import os
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _at(rows, z, i):
    if z <= rows[0][0]:
        return rows[0][i]
    for a, b in zip(rows, rows[1:]):
        if z <= b[0]:
            t = (z - a[0]) / max(1e-9, b[0] - a[0])
            return a[i] + (b[i] - a[i]) * t
    return rows[-1][i]


def inside(poly, x, z):
    c = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, zi = poly[i]
        xj, zj = poly[j]
        if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi + 1e-12) + xi:
            c = not c
        j = i
    return c


def find_view3d():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        return win, area, region
    return None, None, None


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    spec = json.load(open(argv[0], encoding="utf-8"))
    dst = os.path.abspath(argv[1] if len(argv) > 1
                          else os.path.join(os.path.dirname(argv[0]), "knife.blend"))
    hw = spec["envelope"]["halfwidth"]["rows"]
    dp = spec["envelope"]["depth"]["rows"]
    z0, z1 = min(r[0] for r in hw), max(r[0] for r in hw)

    def surf(x, z):
        rx = max(_at(hw, z, 1), 1e-5)
        if dp:
            y0, y1 = _at(dp, z, 1), _at(dp, z, 2)
            cy, ry = (y0 + y1) / 2, max((y1 - y0) / 2, 1e-5)
        else:
            cy, ry = 0.0, rx
        u = min(1.0, abs(x) / rx)
        return cy - ry * math.sqrt(max(0.0, 1 - u * u))

    panels = []
    for p in spec["parts"]:
        if p["ops"].get("skip") or not p.get("poly"):
            continue
        prot = p["ops"]["protrusion"]
        if p["ops"].get("make") == "recess":
            prot = -abs(prot) * 0.6
        for poly in p["poly"]:
            if len(poly) >= 3:
                panels.append((poly, prot))

    bpy.ops.wm.read_factory_settings(use_empty=True)

    # ── 껍질
    ncol, nrow = 96, 96
    bm = bmesh.new()
    grid = []
    for j in range(nrow + 1):
        z = z0 + (z1 - z0) * j / nrow
        rx = max(_at(hw, z, 1), 1e-5)
        row = []
        for i in range(ncol):
            a = 2 * math.pi * i / ncol - math.pi / 2
            x = rx * math.cos(a)
            y = surf(x, z)
            row.append(bm.verts.new((x, -y if math.sin(a) > 0 else y, z)))
        grid.append(row)
    for j in range(nrow):
        for i in range(ncol):
            k = (i + 1) % ncol
            bm.faces.new((grid[j][i], grid[j][k], grid[j + 1][k], grid[j + 1][i]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("shell")
    bm.to_mesh(me)
    bm.free()
    shell = bpy.data.objects.new("shell", me)
    bpy.context.scene.collection.objects.link(shell)

    # ── 절단자: 판 윤곽을 앞쪽 평면에 깐 **닫힌 폴리라인**
    cutters = []
    for n, (poly, _pr) in enumerate(panels):
        cm = bmesh.new()
        vs = [cm.verts.new((x, -0.5, z)) for x, z in poly]
        for k in range(len(vs)):
            try:
                cm.edges.new((vs[k], vs[(k + 1) % len(vs)]))
            except ValueError:
                pass
        # **면을 채워 '경계 엣지'를 만든다.** 와이어만 두면 knife_project 가
        # "No other selected objects have wire or boundary edges" 로 거부한다(실측)
        try:
            cm.faces.new(vs)
        except ValueError:
            pass
        m2 = bpy.data.meshes.new(f"cut{n}")
        cm.to_mesh(m2)
        cm.free()
        o2 = bpy.data.objects.new(f"cut{n}", m2)
        bpy.context.scene.collection.objects.link(o2)
        cutters.append(o2)

    win, area, region = find_view3d()
    if area is None:
        print("VIEW_3D 없음 — `-b` 로 돌렸다. GUI 로 실행해야 한다")
        return
    # 정면 정사영으로 맞춘다 — Knife Project 는 **화면 방향**으로 투영한다
    with bpy.context.temp_override(window=win, area=area, region=region):
        bpy.ops.view3d.view_axis(type='FRONT')
        area.spaces[0].region_3d.view_perspective = 'ORTHO'
        bpy.ops.view3d.view_all()

        before = len(shell.data.polygons)
        # **한 번에 49개를 넣으면 블렌더가 죽는다** (EXCEPTION_ACCESS_VIOLATION, 실측).
        # 사람도 하나씩 자른다 — 한 개씩 돌리고 각각 예외를 잡는다.
        ok = fail = 0
        for c in cutters:
            bpy.ops.object.select_all(action='DESELECT')
            c.select_set(True)
            shell.select_set(True)
            bpy.context.view_layer.objects.active = shell
            try:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.mesh.knife_project(cut_through=True)
                ok += 1
            except RuntimeError:
                fail += 1
            finally:
                if bpy.context.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
        after = len(shell.data.polygons)
    print(f"Knife Project: 성공 {ok} 실패 {fail} · 면 {before} -> {after} "
          f"(+{after - before})")

    for c in cutters:
        bpy.data.objects.remove(c, do_unlink=True)

    # ── 새겨진 면을 법선으로 민다
    bm2 = bmesh.new()
    bm2.from_mesh(shell.data)
    moved = {}
    for f in bm2.faces:
        c = f.calc_center_median()
        off = 0.0
        for poly, prot in panels:
            if inside(poly, c.x, c.z):
                off = max(off, prot) if prot > 0 else min(off, prot)
        if off:
            for v in f.verts:
                moved[v] = max(moved.get(v, 0.0), off, key=abs)
    for v, off in moved.items():
        if v.normal.length > 1e-6:
            v.co += v.normal.normalized() * off
    cl = (bm2.edges.layers.float.get('crease_edge')
          or bm2.edges.layers.float.new('crease_edge'))
    ncre = 0
    for e in bm2.edges:
        if (moved.get(e.verts[0]) is not None) != (moved.get(e.verts[1]) is not None):
            e[cl] = 1.0
            ncre += 1
    bm2.to_mesh(shell.data)
    bm2.free()
    shell.data.update()
    ng = sum(1 for f in shell.data.polygons if len(f.vertices) != 4)
    print(f"민 정점 {len(moved)} · 크리스 {ncre} · 면 {len(shell.data.polygons)} "
          f"· N각면 {ng}")
    bpy.ops.wm.save_as_mainfile(filepath=dst)
    print("SAVED", dst)
    bpy.ops.wm.quit_blender()


main()
