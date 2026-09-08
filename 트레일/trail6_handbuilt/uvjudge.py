# -*- coding: utf-8 -*-
"""표면 위에서 잰다 — 화면이 아니라. 시점·셰이딩 편향이 없는 판정.

    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b --python uvjudge.py

두 가지를 낸다.

1. **날카로운 엣지 사슬** — 이면각이 큰 엣지를 잇고 사슬 길이별로 나눈다.
   마칭큐브 계단 잡음은 **짧은 사슬 수천 개**로, 패널선은 **긴 사슬 몇 개**로 나온다.
   57번의 "선 밀도는 방향을 안 가리니 계단과 디테일을 구별 못 한다" 를 사슬 길이로 가른다.
2. **UV 품질** — 섬 수 / 왜곡 / 채움. 후보를 다 돌려 왜곡 <= 2.0 중 섬이 최소인 것 (32번).
"""
import json
import math
import os

import numpy as np

try:
    import bmesh
    import bpy
except ImportError:
    bpy = None

HERE = os.path.dirname(os.path.abspath(__file__))
T4 = os.path.join(HERE, "..", "trail4_gen3d")
BASE = os.path.join(T4, "out", "nd_baked.blend")
PART = os.path.join(HERE, "out", "pauldron.blend")
SHARP = math.radians(25)          # 이 이면각 넘으면 "날카롭다"
BUCKETS = (0.010, 0.030)          # 사슬 길이 구간 경계 (전신 높이 = 1)
CAND = [("smart89", "smart", 89), ("sharp40", "unwrap", 40),
        ("sharp55", "unwrap", 55), ("smart66", "smart", 66)]
MAXD = 2.0


def chains(me):
    """날카로운 엣지를 이어 사슬로 만들고 길이별로 센다."""
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.edges.ensure_lookup_table()
    sharp = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > SHARP]
    area = sum(f.calc_area() for f in bm.faces)
    adj = {}
    for e in sharp:
        for v in e.verts:
            adj.setdefault(v.index, []).append(e)
    seen, out = set(), []
    for e0 in sharp:
        if e0.index in seen:
            continue
        st, comp = [e0], []
        seen.add(e0.index)
        while st:
            e = st.pop()
            comp.append(e)
            for v in e.verts:
                for g in adj[v.index]:
                    if g.index not in seen:
                        seen.add(g.index)
                        st.append(g)
        out.append(sum(e.calc_length() for e in comp))
    bm.free()
    # 이면각 히스토그램 (엣지 길이 가중). 구(球)는 작은 각에만 몰리고,
    # 하드서피스는 **0도 근처(판 안쪽)와 큰 각(능선)에 동시에** 몰린다 — 쌍봉이 형태의 서명이다.
    bm2 = bmesh.new()
    bm2.from_mesh(me)
    ang = np.array([e.calc_face_angle(0.0) for e in bm2.edges if len(e.link_faces) == 2])
    ln = np.array([e.calc_length() for e in bm2.edges if len(e.link_faces) == 2])
    bm2.free()
    deg = np.degrees(ang)
    edges = [0, 5, 15, 25, 45, 181]
    hist = [float(ln[(deg >= edges[i]) & (deg < edges[i + 1])].sum() / max(ln.sum(), 1e-9))
            for i in range(len(edges) - 1)]
    out = np.array(out) if out else np.zeros(0)
    lo, hi = BUCKETS
    return {
        "area": float(area),
        "sharp_edges": len(sharp),
        "chains": int(len(out)),
        "len_total": float(out.sum()),
        "len_per_area": float(out.sum() / area) if area else 0.0,
        "short": [int((out < lo).sum()), float(out[out < lo].sum())],
        "mid": [int(((out >= lo) & (out < hi)).sum()), float(out[(out >= lo) & (out < hi)].sum())],
        "long": [int((out >= hi).sum()), float(out[out >= hi].sum())],
        "longest": float(out.max()) if len(out) else 0.0,
        "hist": hist,          # <5, 5~15, 15~25, 25~45, >=45 도 (길이 비율)
    }


def dump(me, tag, store):
    """사슬 선분(월드 좌표 + 그 사슬 길이) 과 UV 폴리곤을 그림용으로 뽑아 둔다."""
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.edges.ensure_lookup_table()
    sharp = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > SHARP]
    adj = {}
    for e in sharp:
        for v in e.verts:
            adj.setdefault(v.index, []).append(e)
    seen, segs, lens = set(), [], []
    for e0 in sharp:
        if e0.index in seen:
            continue
        st, comp = [e0], []
        seen.add(e0.index)
        while st:
            e = st.pop()
            comp.append(e)
            for v in e.verts:
                for g in adj[v.index]:
                    if g.index not in seen:
                        seen.add(g.index)
                        st.append(g)
        L = sum(e.calc_length() for e in comp)
        for e in comp:
            segs.append([list(e.verts[0].co), list(e.verts[1].co)])
            lens.append(L)
    bm.free()
    store[tag + "_seg"] = np.array(segs, np.float32) if segs else np.zeros((0, 2, 3), np.float32)
    store[tag + "_len"] = np.array(lens, np.float32)
    n, lab = islands(me, labels=True)
    uv = np.empty(len(me.loops) * 2)
    me.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    ls = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get("loop_total", lt)
    store[tag + "_uv"] = uv.astype(np.float32)
    store[tag + "_ls"] = ls
    store[tag + "_lt"] = lt
    store[tag + "_lab"] = lab


def islands(me, labels=False):
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv.active
    bm.faces.ensure_lookup_table()
    lab = np.full(len(bm.faces), -1, np.int32)
    seen, n = set(), 0
    for f in bm.faces:
        if f.index in seen:
            continue
        n += 1
        lab[f.index] = n - 1
        st = [f]
        seen.add(f.index)
        while st:
            c = st.pop()
            for lp in c.loops:
                lr = lp.link_loop_radial_next
                g = lr.face
                if g.index in seen:
                    continue
                if (lp[uvl].uv - lr.link_loop_next[uvl].uv).length < 1e-5 and \
                   (lp.link_loop_next[uvl].uv - lr[uvl].uv).length < 1e-5:
                    seen.add(g.index)
                    lab[g.index] = n - 1
                    st.append(g)
    bm.free()
    return (n, lab) if labels else n


def stretch(o):
    """UV 면적 / 3D 면적 비의 p95/p5. 1.0 이면 균일 (trail4 uv_quality.py 재사용)."""
    m = o.data
    nf = len(m.polygons)
    uv = np.empty(len(m.loops) * 2)
    m.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    ls = np.empty(nf, np.int32)
    m.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32)
    m.polygons.foreach_get("loop_total", lt)
    a3 = np.empty(nf)
    m.polygons.foreach_get("area", a3)
    a2 = np.array([0.5 * abs(np.dot(uv[s:s + t, 0], np.roll(uv[s:s + t, 1], -1)) -
                             np.dot(uv[s:s + t, 1], np.roll(uv[s:s + t, 0], -1)))
                   for s, t in zip(ls, lt)])
    ok = (a3 > 1e-12) & (a2 > 1e-14)
    sc = np.sqrt(a2 / np.maximum(a3, 1e-12))
    # 왜곡을 둘로 가른다. 섞어서 재면 "재배치로 없앨 수 있는 것"과 "곡률 때문에 못 없애는 것"이
    # 한 수에 섞인다 (LESSONS 34: 파츠 사이 밀도차 32.9배는 배분 선택일 뿐이었다)
    n, lab = islands(m, labels=True)
    med = np.array([np.median(sc[ok & (lab == i)]) if (ok & (lab == i)).any() else 1.0
                    for i in range(n)])
    intra = sc[ok] / np.maximum(med[lab[ok]], 1e-12)
    p = lambda a, q: float(np.percentile(a, q))
    return (p(intra, 95) / max(p(intra, 5), 1e-12),          # 섬 **안**의 왜곡 — 못 없앤다
            float(med.max() / max(med.min(), 1e-12)),        # 섬 **끼리** 밀도차 — 재배치로 없앤다
            float(a2.sum()))


def uv_best(o):
    """후보를 다 돌려 왜곡 <= MAXD 중 섬이 최소인 것. 한 설정이 전부에 맞는 일은 없다 (32번)."""
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    rows = []
    keep = None
    if o.data.uv_layers:
        # 후보 스윕은 **원본 UV 를 덮어쓴다.** 이긴 게 원본이면 되돌려 놔야 한다.
        # 안 그러면 마지막 후보가 남아서 그림도 저장본도 딴 UV 가 된다.
        keep = np.empty(len(o.data.loops) * 2)
        o.data.uv_layers[0].data.foreach_get("uv", keep)
        # 지을 때 같이 쓴 UV. 언랩기를 부르기 전에 먼저 잰다
        d, dens, f = stretch(o)
        rows.append(("built", islands(o.data), round(d, 2), round(dens, 1), round(f, 4)))
    for tag, how, ang in CAND:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        if how == "smart":
            bpy.ops.uv.smart_project(angle_limit=math.radians(ang), island_margin=0.003)
        else:
            bpy.ops.mesh.mark_seam(clear=True)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_mode(type='EDGE')
            bpy.ops.mesh.edges_select_sharp(sharpness=math.radians(ang))
            bpy.ops.mesh.mark_seam()
            bpy.ops.mesh.select_mode(type='FACE')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.003)
        bpy.ops.object.mode_set(mode='OBJECT')
        d, dens, f = stretch(o)
        rows.append((tag, islands(o.data), round(d, 2), round(dens, 1), round(f, 4)))
    ok = [r for r in rows if r[2] <= MAXD] or rows
    best = min(ok, key=lambda r: r[1])
    if best[0] == "built":
        o.data.uv_layers[0].data.foreach_set("uv", keep)   # 스윕이 덮어쓴 걸 되돌린다
        o.data.update()
        return best, rows
    # 채택안을 실제로 다시 걸어 둔다 (마지막 후보가 남아 있으면 굽기가 엉뚱한 UV 를 쓴다)
    tag, how, ang = next(c for c in CAND if c[0] == best[0])
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    if how == "smart":
        bpy.ops.uv.smart_project(angle_limit=math.radians(ang), island_margin=0.003)
    else:
        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.003)
    bpy.ops.object.mode_set(mode='OBJECT')
    return best, rows


def join(obs):
    obs = [o for o in obs if o.type == 'MESH']
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    if len(obs) > 1:
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def region_of_base(lo, hi):
    bpy.ops.wm.open_mainfile(filepath=BASE)
    for o in [x for x in bpy.context.scene.objects if x.type == 'MESH']:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces
                                   if not all(lo[i] <= f.calc_center_median()[i] <= hi[i]
                                              for i in range(3))], context='FACES')
        bm.to_mesh(o.data)
        bm.free()
    for o in [x for x in bpy.context.scene.objects if x.type == 'MESH']:
        if not len(o.data.polygons):
            bpy.data.objects.remove(o)
    return join(list(bpy.context.scene.objects))


def main():
    store = {}
    spec = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
    x0, x1 = spec["front"]["u"]
    z0, z1 = spec["front"]["z"]
    y0, y1 = spec["side"]["y"]
    p = 0.012
    lo, hi = (x0 - p, y0 - p, z0 - p), (x1 + p, y1 + p, z1 + p)

    out = {}
    a = region_of_base(lo, hi)
    out["A"] = {"faces": len(a.data.polygons), **chains(a.data)}
    best, rows = uv_best(a)
    out["A"]["uv"] = {"pick": best[0], "islands": best[1], "distortion": best[2],
                      "density": best[3], "fill": best[4], "all": rows}
    dump(a.data, "A", store)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "out", "A_uv.blend"))

    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(PART) as (src, dst):
        dst.objects = src.objects
    for o in dst.objects:
        bpy.context.scene.collection.objects.link(o)
    b = join(list(bpy.context.scene.objects))
    out["B"] = {"faces": len(b.data.polygons), **chains(b.data)}
    best, rows = uv_best(b)
    out["B"]["uv"] = {"pick": best[0], "islands": best[1], "distortion": best[2],
                      "density": best[3], "fill": best[4], "all": rows}
    dump(b.data, "B", store)
    np.savez(os.path.join(HERE, "out", "uvdump.npz"), **store)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "out", "B_uv.blend"))

    json.dump(out, open(os.path.join(HERE, "out", "uvjudge.json"), "w"), indent=1)
    print("\nRESULT")
    print("=== 날카로운 엣지 사슬 (이면각 > 25도) ===")
    print(f"{'':4}{'면':>8}{'표면적':>9}{'사슬':>7}{'총길이':>9}{'길이/면적':>10}"
          f"{'짧음<0.01':>16}{'0.01~0.03':>16}{'김>=0.03':>16}{'최장':>8}")
    for t in ("A", "B"):
        d = out[t]
        print(f"{t:<4}{d['faces']:>8,}{d['area']:>9.4f}{d['chains']:>7,}{d['len_total']:>9.3f}"
              f"{d['len_per_area']:>10.1f}"
              f"{d['short'][0]:>9,}개 {d['short'][1]:>5.2f}"
              f"{d['mid'][0]:>9,}개 {d['mid'][1]:>5.2f}"
              f"{d['long'][0]:>9,}개 {d['long'][1]:>5.2f}"
              f"{d['longest']:>8.3f}")
    print("\n=== UV 품질 (왜곡 <= 2.0 중 섬 최소) ===")
    for t in ("A", "B"):
        u = out[t]["uv"]
        print(f"{t:<4}채택 {u['pick']:<9} 섬 {u['islands']:>5,}  섬안왜곡 {u['distortion']:>5.2f}  "
              f"섬끼리밀도차 {u['density']:>6.1f}배  채움 {u['fill']:.4f}")
        for r in u["all"]:
            print(f"{'':9}{r[0]:<9} 섬 {r[1]:>5,}  {r[2]:>9.2f}  {r[3]:>14.1f}배  {r[4]:>10.4f}")


def draw():
    """지표가 무엇을 보고 있는지 그린다 — 사슬과 UV 배치."""
    import cv2
    RES2, U0, U1, Z0, Z1 = 1024, -0.6, 0.6, -0.1, 1.1
    d = np.load(os.path.join(HERE, "out", "uvdump.npz"))
    col = lambda u: ((u - U0) / (U1 - U0) * (RES2 - 1))
    row = lambda z: ((Z1 - z) / (Z1 - Z0) * (RES2 - 1))
    # cv2.putText 는 한글을 못 그린다 (?????? 로 나온다). 라벨은 ASCII 로.
    BUCK = ((0.010, (60, 60, 235), "noise  chain < 0.01"),
            (0.030, (40, 150, 240), "0.01 ~ 0.03"),
            (1e9, (220, 120, 40), "structure  chain >= 0.03"))
    st = json.load(open(os.path.join(HERE, "out", "uvjudge.json"), encoding="utf-8"))

    def project(seg, view, alpha):
        """측면 화면 가로가 +y 인지 -y 인지 렌더 알파에 얼마나 얹히는지로 정한다 (LESSONS 39)."""
        if view == "front":
            return np.stack([col(seg[..., 0]), row(seg[..., 2])], -1)
        best, bp = -1, None
        for sgn in (1, -1):
            pj = np.stack([col(sgn * seg[..., 1]), row(seg[..., 2])], -1)
            q = np.clip(pj.reshape(-1, 2).astype(int), 0, RES2 - 1)
            sc = alpha[q[:, 1], q[:, 0]].mean()
            if sc > best:
                best, bp = sc, pj
        return bp

    rows = []
    for view in ("front", "side"):
        tiles = []
        for tag, iso in (("A", "Aiso"), ("B", "Biso")):
            im = cv2.imread(os.path.join(HERE, "out", f"j_{iso}_{view}.png"), cv2.IMREAD_UNCHANGED)
            bg = im[..., :3].astype(np.float32)
            al = im[..., 3] > 0
            bg[~al] = 255
            bg = (bg * 0.35 + 255 * 0.65).astype(np.uint8)     # 배경은 흐리게, 선이 주인공
            seg, ln = d[tag + "_seg"], d[tag + "_len"]
            pj = project(seg, view, al.astype(np.float32))
            order = np.argsort(ln)                              # 긴 사슬을 위에 그린다
            for i in order:
                c = next(cc for lim, cc, _ in BUCK if ln[i] < lim)
                p0 = tuple(np.round(pj[i, 0]).astype(int))
                p1 = tuple(np.round(pj[i, 1]).astype(int))
                cv2.line(bg, p0, p1, c, 2, cv2.LINE_AA)
            r, c_ = np.nonzero(al)
            pd = 30
            t = bg[max(r.min() - pd, 0):r.max() + pd, max(c_.min() - pd, 0):c_.max() + pd]
            t = cv2.resize(t, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
            t = cv2.copyMakeBorder(t, 30, 6, 6, 6, cv2.BORDER_CONSTANT, value=(255, 255, 255))
            q = st[tag]
            cv2.putText(t, f"{tag} {view}   faces {q['faces']:,}   chains {q['chains']}"
                           f"   longest {q['longest']:.3f}   len/area {q['len_per_area']:.1f}",
                        (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 0, 0), 1, cv2.LINE_AA)
            tiles.append(t)
        h = max(t.shape[0] for t in tiles)
        w = max(t.shape[1] for t in tiles)
        tiles = [cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, w - t.shape[1],
                                    cv2.BORDER_CONSTANT, value=(255, 255, 255)) for t in tiles]
        rows.append(np.hstack(tiles))
    W = max(r.shape[1] for r in rows)
    rows = [cv2.copyMakeBorder(r, 0, 0, 0, W - r.shape[1], cv2.BORDER_CONSTANT,
                               value=(255, 255, 255)) for r in rows]
    sheet = np.vstack(rows)
    y = sheet.shape[0] - 14
    for k, (_, c, name) in enumerate(BUCK):
        cv2.rectangle(sheet, (10 + k * 300, y - 12), (30 + k * 300, y), c, -1)
        cv2.putText(sheet, name, (36 + k * 300, y - 1), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 0, 0), 1, cv2.LINE_AA)
    cv2.imwrite(os.path.join(HERE, "out", "proof_chains.png"), sheet)

    # UV 배치 — 섬마다 다른 색
    tiles = []
    for tag in ("A", "B"):
        uv, ls, lt, lab = d[tag + "_uv"], d[tag + "_ls"], d[tag + "_lt"], d[tag + "_lab"]
        S = 900
        cv = np.full((S, S, 3), 255, np.uint8)
        rng = np.random.default_rng(0)
        cols = rng.integers(60, 235, (int(lab.max()) + 1, 3))
        for f in range(len(ls)):
            pts = uv[ls[f]:ls[f] + lt[f]].copy()
            pts[:, 1] = 1 - pts[:, 1]
            q = np.round(np.clip(pts, 0, 1) * (S - 1)).astype(np.int32)
            cv2.fillPoly(cv, [q], [int(x) for x in cols[lab[f]]])
            cv2.polylines(cv, [q], True, (40, 40, 40), 1, cv2.LINE_AA)
        cv = cv2.copyMakeBorder(cv, 30, 6, 6, 6, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        cv2.putText(cv, f"{tag} UV   faces {len(ls):,}   islands {int(lab.max()) + 1}",
                    (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
        tiles.append(cv)
    cv2.imwrite(os.path.join(HERE, "out", "proof_uv.png"), np.hstack(tiles))
    print("proof_chains.png / proof_uv.png")


if __name__ == "__main__":
    if bpy is not None:
        main()
    else:
        import subprocess
        subprocess.run([r"C:/Program Files/Blender Foundation/Blender 4.0/blender.exe",
                        "-b", "--python", __file__], check=True)
        draw()
