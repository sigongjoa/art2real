"""`buildspec.json` **만** 읽어서 블렌더로 조립한다. 상수를 여기 적지 않는다.

    blender -b --python build_blender.py -- <buildspec.json> [출력.blend]

이 파일에 치수가 하나도 없다는 게 핵심이다. 스펙에 없는 값은 **아직 존재하지 않는 값**
이므로 만들 수 없다 — 그래서 눈으로 고치는 경로가 막힌다.

읽는 것:
    conventions   사각면 100% · 미러 원점 (0,0,0) · rotation_euler 금지 · flat 셰이딩
    envelope      z별 반폭(정면)과 앞뒤(측면) -> 부모 표면
    parts[].poly  윤곽 (월드 좌표)
    parts[].ops   make / protrusion / modifiers / shade / skip
    build_order   만드는 순서
    checks        조립 후 점검
"""
import json
import math
import os
import sys

import bmesh
import bpy

SEG = 12          # 판 하나의 격자. 스펙의 윤곽 점 수와 무관한 **메시 밀도**다


def _at(rows, z, i):
    """rows = [[z, v...]] 를 z 에서 선형보간."""
    if z <= rows[0][0]:
        return rows[0][i]
    for a, b in zip(rows, rows[1:]):
        if z <= b[0]:
            t = (z - a[0]) / max(1e-9, b[0] - a[0])
            return a[i] + (b[i] - a[i]) * t
    return rows[-1][i]


def make_surface(spec):
    """외형 -> 부모 표면 y(x, z). 깊이 rows 가 있으면 그걸, 없으면 반폭으로 근사."""
    hw = spec["envelope"]["halfwidth"]["rows"]
    dp = spec["envelope"]["depth"]["rows"]

    def surf(x, z):
        rx = max(_at(hw, z, 1), 1e-5)
        if dp:
            y0, y1 = _at(dp, z, 1), _at(dp, z, 2)
            cy, ry = (y0 + y1) / 2, max((y1 - y0) / 2, 1e-5)
        else:
            cy, ry = 0.0, rx
        u = min(1.0, abs(x) / rx)
        return cy - ry * math.sqrt(max(0.0, 1 - u * u))
    return surf


def radius(poly, c, th):
    dx, dz = math.cos(th), math.sin(th)
    best, n = 0.0, len(poly)
    for k in range(n):
        ax, az = poly[k][0] - c[0], poly[k][1] - c[1]
        bx, bz = poly[(k + 1) % n][0] - c[0], poly[(k + 1) % n][1] - c[1]
        ex, ez = bx - ax, bz - az
        den = ex * dz - dx * ez
        if abs(den) < 1e-12:
            continue
        t = (ex * az - ax * ez) / den
        s = (dx * az - dz * ax) / den
        if t > best and -1e-9 <= s <= 1 + 1e-9:
            best = t
    return best


def hull(poly):
    pts = sorted(set(map(tuple, poly)))
    if len(pts) < 3:
        return poly

    def half(ps):
        h = []
        for q in ps:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (q[1] - h[-2][1]) -
                                   (h[-1][1] - h[-2][1]) * (q[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(q)
        return h[:-1]
    return half(pts) + half(pts[::-1])


def build_plate(name, poly, prot, surf, rim=0.28):
    """윤곽을 부모 표면에 얹은 **평평한 갑판**. 격자를 원반으로 사상해 전부 사각면.

    **돔으로 부풀리면 안 된다.** 하드서피스 판은 평평하고 테두리에서만 꺾인다 —
    부풀리면 표면이 물집이 된다(실측: 첫 조립본이 통째로 그랬다, LESSON 83).
    그래서 윗면은 평탄(1.0)이고 테두리 rim 비율 안에서만 표면으로 내려간다.
    """
    c = (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))
    if min(radius(poly, c, 2 * math.pi * k / 24) for k in range(24)) <= 0:
        poly = hull(poly)                      # 중심에서 별모양이 아니면 볼록껍질
        c = (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))
    bm = bmesh.new()
    grid = {}
    for i in range(SEG + 1):
        for j in range(SEG + 1):
            u, v = -1 + 2 * i / SEG, -1 + 2 * j / SEG
            dx = u * math.sqrt(max(0.0, 1 - v * v / 2))
            dz = v * math.sqrt(max(0.0, 1 - u * u / 2))
            rr = math.hypot(dx, dz)
            x, z = c
            if rr > 1e-9:
                R = radius(poly, c, math.atan2(dz, dx))
                x, z = c[0] + R * dx, c[1] + R * dz
            bulge = min(1.0, max(0.0, (1.0 - min(1.0, rr)) / rim))   # 평탄 + 테두리 챔퍼
            base = surf(x, z)
            f = bm.verts.new((x, base - prot * bulge, z))
            grid[(i, j, 0)] = f
            grid[(i, j, 1)] = f if rr > 1 - 1e-9 else bm.verts.new((x, base + 0.02 * bulge, z))
    for side in (0, 1):
        for i in range(SEG):
            for j in range(SEG):
                q = [grid[(i, j, side)], grid[(i + 1, j, side)],
                     grid[(i + 1, j + 1, side)], grid[(i, j + 1, side)]]
                if len(set(q)) < 4:
                    continue
                bm.faces.new(q if side == 0 else q[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def build_blade(name, poly, prot, surf, n=8):
    """**뻗은 날** — 뿔. 주축을 따라 단면을 쌓고 끝으로 갈수록 얇아진다.
    갑판처럼 표면에 얹으면 뿔이 납작한 무늬가 된다 (실측: 첫 조립본이 그랬다)."""
    xs = [q[0] for q in poly]; zs = [q[1] for q in poly]
    cx, cz = sum(xs) / len(xs), sum(zs) / len(zs)
    # 주축 = 가장 먼 두 점
    far = max(poly, key=lambda q: (q[0] - cx) ** 2 + (q[1] - cz) ** 2)
    near = min(poly, key=lambda q: (q[0] - far[0]) ** 2 + (q[1] - far[1]) ** 2)
    ax, az = far[0] - near[0], far[1] - near[1]
    L = math.hypot(ax, az) or 1e-6
    ax, az = ax / L, az / L
    px_, pz_ = -az, ax                              # 수직
    t = [( (q[0]-near[0])*ax + (q[1]-near[1])*az,
           (q[0]-near[0])*px_ + (q[1]-near[1])*pz_ ) for q in poly]
    bm = bmesh.new()
    rings = []
    for k in range(n + 1):
        u = k / n
        seg = [w for tt, w in t if abs(tt - u * L) < L / n * 1.2]
        hw = (max(seg) - min(seg)) / 2 if len(seg) >= 2 else 0.0
        hw = max(hw * (1 - u) ** 0.35, L * 0.004)   # 끝으로 갈수록 얇게
        bx, bz = near[0] + ax * L * u, near[1] + az * L * u
        base = surf(bx, bz)
        dep = max(hw * 0.8, 0.002)
        rings.append([bm.verts.new((bx + px_ * hw * sx, base - prot - dep * sy,
                                    bz + pz_ * hw * sx))
                      for sx, sy in ((1, 1), (1, -1), (-1, -1), (-1, 1))])
    for a_, b_ in zip(rings, rings[1:]):
        for m in range(4):
            bm.faces.new((a_[m], a_[(m + 1) % 4], b_[(m + 1) % 4], b_[m]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def inside(poly, x, z):
    c = False; n = len(poly); j = n - 1
    for i in range(n):
        xi, zi = poly[i]; xj, zj = poly[j]
        if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi + 1e-12) + xi:
            c = not c
        j = i
    return c


def build_shell(spec, surf, ncol=96, nrow=96):
    """**한 껍질을 만들고, 판 경계를 그 메시에 새긴 뒤, 그 면들을 법선으로 민다.**

    영상(sUMDGjzSw_E)의 순서를 그대로 따른다. 앞서 **자르지 않고 밀었더니 가로
    줄무늬로 찢어졌다** — 오프셋이 면을 가로지르기 때문이다. 순서가 핵심이다.

    Knife Project 는 3D 뷰포트 컨텍스트가 필요해 `-b` 에선 못 쓴다.
    같은 일을 하는 **Knife Intersect**(`bpy.ops.mesh.intersect`)는 헤드리스에서 돈다:
    판 폴리곤을 y 방향으로 뽑은 **절단자 프리즘**을 같은 메시에 넣고 교차시키면
    껍질에 판 경계가 새겨진다. 그 뒤 절단자만 지우고 면을 민다.
    """
    hw = spec["envelope"]["halfwidth"]["rows"]
    z0, z1 = min(r[0] for r in hw), max(r[0] for r in hw)
    panels = []
    for p in spec["parts"]:
        if p["ops"].get("skip") or not p.get("poly"):
            continue
        mk = p["ops"].get("make", "plate")
        prot = p["ops"]["protrusion"]
        if mk == "recess":
            prot = -abs(prot) * 0.6
        for poly in p["poly"]:
            if len(poly) >= 3:
                panels.append((poly, prot, p["material"]))

    bm = bmesh.new()
    grid = []
    for j in range(nrow + 1):
        z = z0 + (z1 - z0) * j / nrow
        rx = max(_at(hw, z, 1), 1e-5)
        row = []
        for i in range(ncol):
            ang = 2 * math.pi * i / ncol - math.pi / 2
            x = rx * math.cos(ang)
            yb = surf(x, z)
            if math.sin(ang) > 0:
                yb = -yb
            row.append(bm.verts.new((x, yb, z)))
        grid.append(row)
    shell_faces = []
    for j in range(nrow):
        for i in range(ncol):
            a_, b_ = grid[j], grid[j + 1]
            k = (i + 1) % ncol
            shell_faces.append(bm.faces.new((a_[i], a_[k], b_[k], b_[i])))
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("shell")
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("shell", me)
    bpy.context.scene.collection.objects.link(ob)

    # ── 절단자 프리즘: 판 폴리곤을 y 로 길게 뽑는다
    cut = bmesh.new()
    YF, YB = -0.6, 0.6
    for poly, _pr, _m in panels:
        vs_f = [cut.verts.new((x, YF, z)) for x, z in poly]
        vs_b = [cut.verts.new((x, YB, z)) for x, z in poly]
        for k in range(len(poly)):
            j2 = (k + 1) % len(poly)
            try:
                cut.faces.new((vs_f[k], vs_f[j2], vs_b[j2], vs_b[k]))
            except ValueError:
                pass
    cme = bpy.data.meshes.new("cutter")
    cut.to_mesh(cme); cut.free()
    cob = bpy.data.objects.new("cutter", cme)
    bpy.context.scene.collection.objects.link(cob)

    # ── 합쳐서 Knife Intersect
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True); cob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.join()
    n_before = len(ob.data.polygons)

    # **선택은 편집모드에서 bmesh 로 넘겨야 한다.** 오브젝트 모드에서 `f.select` 를
    # 찍으면 오퍼레이터가 못 받는다 — 격리 테스트에서 확인했다(513->513 vs 513->577).
    # 그리고 `separate_mode` 기본은 'CUT' 이다. 'NONE' 은 교차만 계산하고 안 자른다.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    bmE = bmesh.from_edit_mesh(ob.data)
    bmE.faces.ensure_lookup_table()
    nsel = 0
    for f in bmE.faces:
        # **면 중심으로 판정하면 안 된다** — 프리즘 벽면의 중심은 y=0 이라 껍질과 구분이
        # 안 된다(실측: 선택 0개). 벽면은 **모든 정점**이 y=±0.6 이다.
        if all(abs(v.co.y) > 0.45 for v in f.verts):  # 절단자 면
            f.select_set(True); nsel += 1
    bmesh.update_edit_mesh(ob.data)
    try:
        bpy.ops.mesh.intersect(mode='SELECT_UNSELECT', separate_mode='CUT',
                               solver='EXACT')
        cutok = True
    except RuntimeError as e:
        print("  intersect 실패:", e); cutok = False
    bmE = bmesh.from_edit_mesh(ob.data)
    n_cut = len(bmE.faces)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # 절단자 **정점**을 지운다 (면만 지우면 엣지가 남아 정점이 살아남는다)
    for v in ob.data.vertices:
        v.select = abs(v.co.y) > 0.45
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"  Knife Intersect {'OK' if cutok else '실패'} · 절단자면 {nsel} · "
          f"교차직후 {n_cut} · 정리후 {len(ob.data.polygons)} (껍질 원래 {ncol*nrow})")

    # ── 새겨진 면을 법선으로 민다 (Alt+S 에 해당)
    bm2 = bmesh.new(); bm2.from_mesh(ob.data)
    bm2.faces.ensure_lookup_table()
    # **정점 자체가 판 안에 있을 때만 민다.** 면 중심으로 판정하고 그 면의 모든 정점을
    # 밀면 **경계 면의 바깥쪽 정점까지 딸려간다** — 판이 제 경계를 넘어 이웃을 부풀린다.
    # 실측: 밀린 정점 7,009 -> 17,790 으로 늘고 실루엣 과함이 19.9% 였다.
    moved = {}
    for v in bm2.verts:
        off = 0.0
        for poly, prot, _m in panels:
            if inside(poly, v.co.x, v.co.z):
                off = max(off, prot) if prot > 0 else min(off, prot)
        if off:
            moved[v] = off
    for v, off in moved.items():
        n = v.normal.copy()
        if n.length < 1e-6:
            continue
        v.co += n.normalized() * off
    # 판 경계에 크리스
    cl = bm2.edges.layers.float.get('crease_edge') or         bm2.edges.layers.float.new('crease_edge')
    ncre = 0
    for e in bm2.edges:
        a_in = moved.get(e.verts[0]) is not None
        b_in = moved.get(e.verts[1]) is not None
        if a_in != b_in:
            e[cl] = 1.0; ncre += 1
    bm2.to_mesh(ob.data); bm2.free()
    ob.data.update()
    print(f"  민 정점 {len(moved)} · 크리스 엣지 {ncre}")
    return ob, len(panels)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    spec = json.load(open(argv[0], encoding="utf-8"))
    dst = os.path.abspath(argv[1] if len(argv) > 1
                          else os.path.join(os.path.dirname(argv[0]), "build.blend"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    conv = spec["conventions"]
    surf = make_surface(spec)
    by_id = {p["id"]: p for p in spec["parts"]}

    mats = {}
    for nm, col in (("white", (.94, .94, .96, 1)), ("dark", (.05, .05, .07, 1)),
                    ("gold", (.85, .72, .35, 1)), ("steel", (.55, .60, .68, 1))):
        m = bpy.data.materials.new(nm)
        m.diffuse_color = col
        mats[nm] = m

    if os.environ.get("A3D_SHELL", "1") == "1":
        ob, npan = build_shell(spec, surf)
        ob.data.materials.append(mats["white"])
        for f in ob.data.polygons:
            f.use_smooth = True
        print(f"껍질 1개 · 판 {npan}개를 눌러 넣음 · 면 {len(ob.data.polygons)}")
        bpy.context.view_layer.update()
        bpy.ops.wm.save_as_mainfile(filepath=dst)
        print("SAVED", dst)
        return

    made = skipped = 0
    for pid in spec["build_order"]:
        p = by_id.get(pid)
        if not p:
            continue
        o = p["ops"]
        if o.get("skip") or not p.get("poly"):
            skipped += 1
            continue
        for i, poly in enumerate(p["poly"]):
            if len(poly) < 3:
                continue
            nm2 = pid + (f"_{i}" if len(p["poly"]) > 1 else "")
            mk = o.get("make", "plate")
            if mk == "blade":
                ob = build_blade(nm2, poly, o["protrusion"], surf)
            elif mk == "recess":
                # **안쪽으로 판다.** 눈·언더아머는 튀어나온 게 아니라 파인 것이다
                ob = build_plate(nm2, poly, -abs(o["protrusion"]) * 0.6, surf)
            else:
                ob = build_plate(nm2, poly, o["protrusion"], surf)
            ob.data.materials.append(mats.get(p["material"], mats["white"]))
            for f in ob.data.polygons:
                f.use_smooth = (o.get("shade") != "flat")
            for m in o["modifiers"]:
                if m["type"] == "MIRROR":
                    md = ob.modifiers.new("mir", 'MIRROR')
                    md.use_axis = (True, False, False)
                    md.use_mirror_merge = m.get("use_mirror_merge", False)
                elif m["type"] == "SOLIDIFY":
                    md = ob.modifiers.new("sol", 'SOLIDIFY')
                    md.thickness, md.offset = m["thickness"], m.get("offset", 1.0)
                elif m["type"] == "SUBSURF":
                    md = ob.modifiers.new("sub", 'SUBSURF')
                    md.levels = md.render_levels = m["levels"]
            assert tuple(ob.location) == (0.0, 0.0, 0.0), conv["mirror_origin"]
            made += 1
    bpy.context.view_layer.update()

    # ── 스펙의 checks 를 실제로 돌린다
    dg = bpy.context.evaluated_depsgraph_get()
    ngon = tot = 0
    zmax = -1e9
    for ob in [x for x in bpy.context.scene.objects if x.type == 'MESH']:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        ngon += sum(1 for f in me.polygons if len(f.vertices) != 4)
        tot += len(me.polygons)
        for v in me.vertices:
            zmax = max(zmax, (ev.matrix_world @ v.co).z)
        ev.to_mesh_clear()
    print(f"\n부품 {made} 생성 · {skipped} 건너뜀(미러 대체) · 면 {tot}")
    print(f"점검 사각면100%: {'OK' if ngon == 0 else f'실패 N각면 {ngon}'}")
    top = spec["envelope"]["halfwidth"]["rows"][-1][0]
    print(f"점검 정수리높이: {zmax:.4f} vs {top}  "
          f"{'OK' if abs(zmax - top) < 0.01 else '실패'}")
    bpy.ops.wm.save_as_mainfile(filepath=dst)
    print("SAVED", dst)


main()
