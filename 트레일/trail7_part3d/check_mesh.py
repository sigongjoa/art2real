# -*- coding: utf-8 -*-
"""작업대 메시의 **구멍과 성질**을 잰다. 채우기 전에 뭐가 얼마나 있는지 안다.

    blender -b --python check_mesh.py -- out/omega.blend

경계 엣지(면 1개만 붙은 엣지) = 구멍의 가장자리. 그 개수와 고리 수를 센다.
비다양체 엣지(면 3개 이상)도 같이 본다 — 채우기가 실패하는 자리다.
"""
import bpy, os, sys
import bmesh

A = sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(A[0]))

print("%-9s %8s %8s %9s %9s %7s" % ("이름", "정점", "면", "경계엣지", "비다양체", "고리"))
for o in [x for x in bpy.context.scene.objects if x.type == 'MESH']:
    bm = bmesh.new(); bm.from_mesh(o.data)
    bnd = [e for e in bm.edges if len(e.link_faces) == 1]
    nm = [e for e in bm.edges if len(e.link_faces) > 2]

    # 경계 엣지를 고리로 묶는다
    left = set(bnd); loops = 0
    while left:
        e = left.pop(); stack = [e]; loops += 1
        while stack:
            cur = stack.pop()
            for v in cur.verts:
                for ne in v.link_edges:
                    if ne in left:
                        left.discard(ne); stack.append(ne)
    print("%-9s %8d %8d %9d %9d %7d" % (o.name, len(bm.verts), len(bm.faces), len(bnd), len(nm), loops))
    bm.free()
