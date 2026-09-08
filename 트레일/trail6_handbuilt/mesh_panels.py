# -*- coding: utf-8 -*-
"""푼 평면 + 공유 경계망 -> 실제 3D 껍질.

    blender -b --python mesh_panels.py -- out/cap_panels.blend

정점 깊이는 **그 정점에 모이는 판들의 평면 평균**이다. 두 판이 만나는 호 위에서는
두 평면의 평균, 접합점에서는 세 평면 이상의 평균 — 다면체 꼭짓점이 저절로 닫힌다.
따로 윤곽을 뽑아 거리로 꿰매려던 앞판은 홀 엣지가 513개 남았다.
"""
import json
import math
import os
import sys
from collections import defaultdict

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.geometry import tessellate_polygon

HERE = os.path.dirname(os.path.abspath(__file__))
THICK = float(os.environ.get("THICK", 0.008))
# 판마다 제 평면으로 들어올리면 표면이 울퉁불퉁해진다. 그런데 밑바탕 돔이 판별 평면을
# 오차 0.0023 으로 맞춘다 — 판들이 서로 크게 다른 방향을 보는 게 아니라는 뜻이다.
# 판 선은 별개 플레이트가 아니라 **돔 위의 홈**이다. MODE=surface 가 그 해석이다.
MODE = os.environ.get("MODE", "plates")        # plates | surface
GROOVE = float(os.environ.get("GROOVE", 0.004))  # 판 경계를 안쪽으로 이만큼 눌러 홈을 판다
LEAN = float(os.environ.get("LEAN", 1.0))      # 뿔이 화면 밖으로 기우는 최대 (1 = 45도)
BACK = float(os.environ.get("BACK", 0.060))    # 테두리를 뒤로 이만큼 밀어 닫는다 (0 = 껍질)
# 밑바탕(어깨 돔)이 **절대 깊이**를 주므로 기본은 재중심화 안 함.
# 예전엔 여기서 다시 앉혔는데, 그러면 밑바탕을 쓴 의미가 없어진다
Y_MID = float(os.environ["Y_MID"]) if "Y_MID" in os.environ else None
LAV = (0.52, 0.52, 0.70, 1)


def loops(arcs):
    """호(정점열)들을 끝점끼리 이어 닫힌 고리로. 여러 고리가 나올 수 있다."""
    left = list(arcs)
    out = []
    while left:
        cur = list(left.pop(0))
        while True:
            for k, a in enumerate(left):
                if a[0] == cur[-1]:
                    cur += a[1:]; left.pop(k); break
                if a[-1] == cur[-1]:
                    cur += a[::-1][1:]; left.pop(k); break
                if a[-1] == cur[0]:
                    cur = a[:-1] + cur; left.pop(k); break
                if a[0] == cur[0]:
                    cur = a[::-1][:-1] + cur; left.pop(k); break
            else:
                break
            if cur[0] == cur[-1]:
                break
        if cur[0] == cur[-1]:
            cur = cur[:-1]
        if len(cur) >= 3:
            out.append(cur)
    return out


def main():
    out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "out/cap_panels.blend"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    G = json.load(open(os.path.join(HERE, "parts", "graph.json")))
    PL = {p["id"]: p for p in json.load(open(os.path.join(HERE, "parts", "planes.json")))["planes"]}
    V2 = G["verts"]

    at = defaultdict(set)                       # 정점 -> 그 정점에 모이는 판
    byp = defaultdict(list)
    for a in G["arcs"]:
        for lab in a["pair"]:
            if lab in PL:
                byp[lab].append(a["v"])
                for v in a["v"]:
                    at[v].add(lab)

    B = json.load(open(os.path.join(HERE, "parts", "base.json")))

    def dome_y(x, z):
        t = ((x - B["cx"]) / B["ax"]) ** 2 + ((z - B["cz"]) / B["az"]) ** 2
        return B["cy"] - B["ay"] * max(1.0 - t, 0.02) ** 0.5

    # 정점 깊이
    Y = {}
    for v, labs in at.items():
        x, z = V2[v]
        if MODE == "surface":
            # 돔 표면 그대로. 판 경계 정점만 GROOVE 만큼 안으로 눌러 홈을 만든다
            Y[v] = dome_y(x, z) + (GROOVE if len(labs) >= 2 else 0.0)
        else:
            Y[v] = float(np.mean([PL[l]["a"] * x + PL[l]["b"] * z + PL[l]["c"] for l in labs]))
    if Y_MID is not None:
        ymid = float(np.mean(list(Y.values())))
        for v in Y:
            Y[v] += Y_MID - ymid
    print("정점 %d개   모이는 판 수 분포 %s"
          % (len(Y), {k: sum(1 for s in at.values() if len(s) == k) for k in (1, 2, 3, 4)}))

    bm = bmesh.new()
    bv = {v: bm.verts.new((V2[v][0], Y[v], V2[v][1])) for v in sorted(Y)}
    nf = 0
    for lab in sorted(PL):
        for lp in loops(byp[lab]):
            pts2 = [Vector((V2[v][0], V2[v][1], 0.0)) for v in lp]
            for tri in tessellate_polygon([pts2]):
                try:
                    bm.faces.new([bv[lp[i]] for i in tri])
                    nf += 1
                except ValueError:
                    pass
    bm.verts.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if sum(f.normal.y * f.calc_area() for f in bm.faces) > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    # 면에 안 붙은 정점·엣지를 solidify 에 넘기면 좌표가 튄다 (x -0.29, z 1.40 이 나왔다)
    loose_e = [e for e in bm.edges if not e.link_faces]
    bmesh.ops.delete(bm, geom=loose_e, context="EDGES")
    loose_v = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose_v, context="VERTS")
    gap = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    print("면 %d   홀 엣지 %d (바깥 테두리만 남아야 정상)   떠 있던 정점 %d 엣지 %d 버림"
          % (nf, gap, len(loose_v), len(loose_e)))
    # 앞면 셸만 있으면 옆에서 보면 판때기다. **바깥 테두리를 뒤로 밀어 닫는다.**
    # 홀 엣지 175개는 전부 바깥 테두리였다 (안쪽은 이미 다 꿰매졌다)
    if BACK > 0:
        bnd = [e for e in bm.edges if len(e.link_faces) == 1]
        ret = bmesh.ops.extrude_edge_only(bm, edges=bnd)
        yb = max(v.co.y for v in bm.verts) + BACK
        nv = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)]
        for v in nv:
            # surface 모드는 뒤도 타원체다 — 평평한 슬래브 대신 뒤 반쪽을 만든다
            v.co.y = (2 * B["cy"] - dome_y(v.co.x, v.co.z)) if MODE == "surface" else yb
        ne = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMEdge) and len(g.link_faces) == 1]
        bmesh.ops.holes_fill(bm, edges=ne, sides=0)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        left = sum(1 for e in bm.edges if len(e.link_faces) == 1)
        print("뒤로 %.3f 밀어 닫음   측벽 %d면   남은 홀 엣지 %d (0 이어야 닫힌 입체)"
              % (BACK, len(ne), left))

    me = bpy.data.meshes.new("cap_panels")
    bm.to_mesh(me); bm.free()
    mat = bpy.data.materials.new("lav"); mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = LAV
    me.materials.append(mat)
    me.use_auto_smooth = True; me.auto_smooth_angle = math.radians(15)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("cap_panels", me)
    bpy.context.scene.collection.objects.link(ob)
    # bmesh.ops.solidify 는 급한 접힘에서 균등두께 보정(1/cos)이 발산한다 —
    # 깊이 0.120 에서 x 가 -0.45, z 가 2.57 로 튀었다. 모디파이어의 단순 오프셋을 쓴다
    if BACK > 0:
        THICK2 = 0.0
    sd = ob.modifiers.new("solid", "SOLIDIFY")
    sd.thickness = 0.0 if BACK > 0 else THICK
    sd.use_even_offset = False
    sd.offset = -1
    bpy.context.view_layer.objects.active = ob
    if BACK > 0:
        ob.modifiers.remove(sd)
    else:
        bpy.ops.object.modifier_apply(modifier="solid")

    with bpy.data.libraries.load(os.path.join(HERE, "out", "horns.blend")) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith("horn")]
    for o in dst.objects:
        bpy.context.scene.collection.objects.link(o)
    # 뿔도 **어깨 돔 위에 세운다**. 뿌리는 돔 표면에 앉히고, 화면 방향(원화가 준 것)은
    # 그대로 두되 깊이 방향 기울기를 돔 법선에서 가져온다.
    # 옛 y 는 다른 계측에서 온 것이라 캡보다 0.08 뒤에 파묻혔다 (101번의 잔재)
    B = json.load(open(os.path.join(HERE, "parts", "base.json")))
    def dome(x, z):
        t = ((x - B["cx"]) / B["ax"]) ** 2 + ((z - B["cz"]) / B["az"]) ** 2
        k = max(1.0 - t, 0.02) ** 0.5
        y = B["cy"] - B["ay"] * k
        n = Vector(((x - B["cx"]) / B["ax"] ** 2, -k / B["ay"], (z - B["cz"]) / B["az"] ** 2))
        n.normalize()
        return y, n
    for o in dst.objects:
        co = np.array([v.co[:] for v in o.data.vertices])
        lo = co[:, 2] <= co[:, 2].min() + 1e-4
        root = Vector(co[lo].mean(0))
        tip = Vector(co[co[:, 2] >= co[:, 2].max() - 1e-4].mean(0))
        yd, n = dome(root.x, root.z)
        d = tip - root
        scr = math.hypot(d.x, d.z)
        nscr = math.hypot(n.x, n.z)
        # 돔 법선을 그대로 따르면 정수리 뿔이 카메라를 정면으로 찌른다 (lean -7).
        # 원화는 위로 뻗는다 — 화면 방향은 원화가 맞으니 깊이 기울기만 제한한다
        lean = max(-LEAN, min(LEAN, n.y / nscr)) if nscr > 1e-3 else -LEAN
        tgt = Vector((d.x, scr * lean, d.z))
        if d.length > 1e-6 and tgt.length > 1e-6:
            q = d.rotation_difference(tgt)
            M = (Matrix.Translation(root) @ q.to_matrix().to_4x4()
                 @ Matrix.Translation(-root))
            o.data.transform(M)
        o.data.transform(Matrix.Translation(Vector((0, yd - root.y, 0))))
        print("  %-6s 뿌리 y %+.4f -> 돔 %+.4f   기울기 %+.2f" % (o.name, root.y, yd, lean))

    co = np.array([v.co[:] for v in me.vertices])
    print("캡 x %+.4f..%+.4f  y %+.4f..%+.4f  z %.4f..%.4f"
          % (co[:, 0].min(), co[:, 0].max(), co[:, 1].min(), co[:, 1].max(), co[:, 2].min(), co[:, 2].max()))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
    print("PANELS OK objects=%d faces=%d -> %s"
          % (len(bpy.context.scene.objects), len(me.polygons), out))


if __name__ == "__main__":
    main()
