# -*- coding: utf-8 -*-
"""생성 메시를 **두께로** 부품으로 가른다.

    blender -b --python tri_seg.py

뿔은 얇고 캡은 두껍다. 면마다 안쪽으로 광선을 쏘아 반대편까지의 거리를 재면
(shape diameter function) 그 둘이 갈린다. 곡률은 마칭큐브 계단에 묻히는데
(LESSONS 67: 사슬 40개 전부 짧음) 두께는 안 묻힌다.

    1) 면마다 SDF — -법선 둘레 원뿔로 5줄기, 중앙값
    2) 문턱은 Otsu (눈으로 찍지 않는다)
    3) 같은 부류끼리 엣지로 이어진 덩어리 = 부품

산출: out/tri_seg.blend (부품마다 별개 오브젝트) + out/tri_seg_*.png
"""
import bpy, os, sys, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tri_look

NRAY = 5
CONE = math.radians(20)
MINF = int(os.environ.get("MINF", 200))     # 이보다 작은 덩어리는 부스러기


def sdf(me):
    nf = len(me.polygons)
    ctr = np.empty(nf * 3); me.polygons.foreach_get("center", ctr); ctr = ctr.reshape(-1, 3)
    nrm = np.empty(nf * 3); me.polygons.foreach_get("normal", nrm); nrm = nrm.reshape(-1, 3)
    vs = [v.co for v in me.vertices]
    ps = [p.vertices[:] for p in me.polygons]
    bvh = BVHTree.FromPolygons(vs, ps, all_triangles=False)
    eps = 1e-5
    out = np.zeros(nf)
    rs = np.random.RandomState(0)
    for i in range(nf):
        n = Vector(-nrm[i])
        o = Vector(ctr[i]) + n * eps
        d = []
        for j in range(NRAY):
            if j == 0:
                v = n
            else:                                   # -법선 둘레 원뿔
                a = rs.normal(size=3); a = Vector(a); a -= n * a.dot(n)
                if a.length < 1e-9:
                    continue
                v = (n + a.normalized() * math.tan(CONE)).normalized()
            hit = bvh.ray_cast(o, v)
            if hit[0] is not None:
                d.append(hit[3])
        out[i] = np.median(d) if d else 0.0
    return out, ctr, nrm


def otsu(x, bins=128):
    """문턱을 눈으로 찍지 않는다. 두께는 로그로 봐야 두 봉우리가 갈린다."""
    v = np.log(np.clip(x, 1e-6, None))
    h, e = np.histogram(v, bins=bins)
    p = h / h.sum()
    w0 = np.cumsum(p); w1 = 1 - w0
    m = (e[:-1] + e[1:]) / 2
    mu0 = np.cumsum(p * m) / np.clip(w0, 1e-12, None)
    mu1 = (np.cumsum((p * m)[::-1])[::-1]) / np.clip(w1, 1e-12, None)
    var = w0 * w1 * (mu0 - mu1) ** 2
    return float(np.exp(m[int(np.nanargmax(var))]))


def adjacency(me):
    """엣지를 공유하는 면 쌍. **부품 그래프의 뼈대다** — tri_paint 가 색 전파에 다시 쓴다."""
    e2f = {}
    for pi, p in enumerate(me.polygons):
        vt = p.vertices[:]
        for k in range(len(vt)):
            a, b = vt[k], vt[(k + 1) % len(vt)]
            e2f.setdefault((min(a, b), max(a, b)), []).append(pi)
    pairs = [(f[i], f[j]) for f in e2f.values() if len(f) > 1
             for i in range(len(f)) for j in range(i + 1, len(f))]
    return np.array(pairs, np.int32).reshape(-1, 2)


def components(pairs, nf, mask):
    """같은 부류끼리 엣지로 이어진 면 덩어리. union-find."""
    par = list(range(nf))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a

    for a, b in pairs:
        if mask[a] != mask[b]:
            continue
        ra, rb = find(int(a)), find(int(b))
        if ra != rb:
            par[rb] = ra
    lab = np.array([find(i) for i in range(nf)])
    _, lab = np.unique(lab, return_inverse=True)
    return lab


def main():
    o = tri_look.bring()
    me = o.data
    d, ctr, nrm = sdf(me)
    t = otsu(d)
    thin = d < t
    print("SDF 중앙값 %.4f  문턱 %.4f (Otsu)  얇은 면 %d / %d"
          % (float(np.median(d)), t, int(thin.sum()), len(d)))
    pairs = adjacency(me)
    lab = components(pairs, len(me.polygons), thin)
    sizes = np.bincount(lab)
    keep = [i for i in np.argsort(-sizes) if sizes[i] >= MINF]
    print("덩어리 %d개 (>=%d면 %d개)" % (len(sizes), MINF, len(keep)))
    for i in keep[:12]:
        sel = lab == i
        z = ctr[sel, 2]
        print("  #%-3d %6d면  %s  z %.3f..%.3f  SDF 중앙 %.4f"
              % (i, sizes[i], "얇음(뿔?)" if thin[sel][0] else "두꺼움(캡?)",
                 z.min(), z.max(), float(np.median(d[sel]))))

    # 그래프를 남긴다. 어제는 오브젝트로 뜯고 라벨을 버려서 tri_paint 가 못 썼다
    od = os.path.join(HERE, "out")
    np.save(os.path.join(od, "tri_lab.npy"), lab.astype(np.int32))
    np.save(os.path.join(od, "tri_thin.npy"), thin)
    np.save(os.path.join(od, "tri_adj.npy"), pairs)
    print("그래프 저장: 면 %d  부품 %d  엣지쌍 %d" % (len(lab), lab.max() + 1, len(pairs)))

    # 부품마다 오브젝트로 뜯어낸다
    import bmesh
    src = bmesh.new(); src.from_mesh(me); src.faces.ensure_lookup_table()
    made = []
    rs = np.random.RandomState(3)
    for i in keep:
        bm = bmesh.new()
        vmap = {}
        for fi in np.nonzero(lab == i)[0]:
            f = src.faces[fi]
            vv = []
            for v in f.verts:
                if v.index not in vmap:
                    vmap[v.index] = bm.verts.new(v.co)
                vv.append(vmap[v.index])
            try:
                bm.faces.new(vv)
            except ValueError:
                pass
        nm = bpy.data.meshes.new("part%02d" % i)
        bm.to_mesh(nm); bm.free()
        ob = bpy.data.objects.new("part%02d_%s" % (i, "thin" if thin[lab == i][0] else "thick"), nm)
        bpy.context.scene.collection.objects.link(ob)
        m = bpy.data.materials.new("c%02d" % i)
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (
            *(rs.uniform(0.15, 0.95, 3)), 1)
        nm.materials.append(m)
        made.append(ob)
    src.free()
    bpy.data.objects.remove(o, do_unlink=True)
    print("부품 %d개 뜯음" % len(made))

    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'MATERIAL'
    sc.display.shading.show_cavity = True
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.view_settings.view_transform = 'Standard'
    cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = 0.30
    c = bpy.data.objects.new("c", cd); sc.collection.objects.link(c); sc.camera = c
    tgt = (0.184, 0.027, 0.885)
    for az in (0, 40, 90):
        r = math.radians(az)
        c.location = (tgt[0] + 1.2 * math.sin(r), tgt[1] - 1.2 * math.cos(r), tgt[2])
        c.rotation_euler = (math.radians(90), 0, r)
        sc.render.filepath = os.path.join(HERE, "out", "tri_seg_%03d.png" % az)
        bpy.ops.render.render(write_still=True)
        print("SEG", az)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "out", "tri_seg.blend"))


if __name__ == "__main__":       # tri_paint.py 가 adjacency() 만 가져다 쓴다
    main()
