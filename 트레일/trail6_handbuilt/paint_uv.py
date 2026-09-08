# -*- coding: utf-8 -*-
"""판 라벨을 **손으로 지은 견갑의 진짜 UV** 에 굽는다.

    blender -b --python paint_uv.py

129 번이 "화소가 아니라 판을 찍어라" 였고, 그건 생성 메시에서 색을 18개로 줄였다.
하지만 그 메시는 **펼 수가 없다** — 마칭큐브 덩어리라 이음선 놓을 구조가 없어서
smart_project 가 섬을 잘게 부수고 채움이 45.4% 다 (67 번 계단 잡음).
언랩기 탓이 아니다. 언랩기에 줄 게 없는 것이다.

`out/pauldron.blend` 는 그 문제가 없다. UV 를 언랩기에 안 맡기고 **지을 때 같이 냈다**
(build.py 의 layout(), 72 번). 캡 254면 + 뿔 4개가 한 0~1 판에 앉아 있다.

    캡    u 0.010..0.806  v 0.010..0.681     로프트 = 원기둥이라 띠 하나
    뿔4   v 0.681..0.961 에 부채꼴 넷

그리고 부품이 **오브젝트로 이미 갈려 있다** — 생성 메시에서 두께·단면모양으로 힘들게
찾아낸 "뿔 넷"이 여기서는 `sh_horn0..3` 이라는 이름이다. 계급 투표가 필요 없다.
(그래도 표는 세서 찍는다 — 이름과 원화가 어긋나면 그게 알아야 할 일이다.)

산출: out/pad_uv_col.png (텍스처) · out/pad_uv_prov.png (출처) · out/pad_uv.blend
"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mask2d
import tri_paint                                  # labels()/SCORE/VIEWS/sample 재사용
import tri_uv                                     # rasterize()/save() 재사용

OUT = os.path.join(HERE, "out")
SRC = os.path.join(OUT, "pauldron.blend")


def adjacency(me):
    """엣지를 공유하는 면 쌍 (tri_seg 와 같은 것. 여기선 메시가 작아 그대로 짠다)."""
    e2f = {}
    for pi, p in enumerate(me.polygons):
        v = p.vertices[:]
        for k in range(len(v)):
            a, b = v[k], v[(k + 1) % len(v)]
            e2f.setdefault((min(a, b), max(a, b)), []).append(pi)
    return np.array([(f[i], f[j]) for f in e2f.values() if len(f) > 1
                     for i in range(len(f)) for j in range(i + 1, len(f))], np.int32).reshape(-1, 2)


def assign_labels(obs, LBL):
    """면마다 판 라벨 하나. 가림은 **씬 전체**로 본다 — 캡이 뿔을 가린다."""
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for o in obs:
        me = o.data
        nf = len(me.polygons)
        ctr = np.empty(nf * 3); me.polygons.foreach_get("center", ctr); ctr = ctr.reshape(-1, 3)
        nrm = np.empty(nf * 3); me.polygons.foreach_get("normal", nrm); nrm = nrm.reshape(-1, 3)
        M = np.array(o.matrix_world)
        ctr = ctr @ M[:3, :3].T + M[:3, 3]                # 월드로 (조립본이라 변환이 있다)
        nrm = nrm @ M[:3, :3].T
        nrm /= np.clip(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9, None)

        sc = tri_paint.SCORE(nrm)
        order = np.argsort(-sc, 1)
        seen = [mask2d.lookup(LBL[n], ctr[:, mask2d.UAX[n]], ctr[:, 2])
                for n, _ in tri_paint.VIEWS]
        lid = np.full(nf, -1, np.int32)
        for i in range(nf):
            c = Vector(ctr[i])
            for slot in range(3):
                v = int(order[i, slot])
                if sc[i, v] <= 0.05:
                    break
                dv = tri_paint.VIEWS[v][1]
                hit, loc, _, _, _, _ = bpy.context.scene.ray_cast(dg, c - dv * 4.0, dv)
                if not (hit and (loc - c).length <= 0.004):
                    continue                              # 남이 가렸다 (캡이 뿔 뒤를 가린다)
                if seen[v][i] < 0:
                    continue
                lid[i] = seen[v][i]
                break
        out[o.name] = (lid, ctr, nrm)
    return out


def fill(o, lid, hue, meta):
    """오브젝트 = 부품이다. 못 받은 면은 **그 부품 안에서** 라벨을 옮긴다."""
    pairs = adjacency(o.data)
    und = np.concatenate([pairs, pairs[:, ::-1]]) if len(pairs) else pairs
    for _ in range(200):
        if not len(und) or (lid >= 0).all():
            break
        m = (lid < 0)[und[:, 0]] & (lid >= 0)[und[:, 1]]
        if not m.any():
            break
        t, s = und[m, 0], und[m, 1]
        k = np.argsort(-s, kind="stable")
        pick = np.full(len(lid), -1, np.int64); pick[t[k]] = s[k]
        g = pick >= 0
        lid[g] = lid[pick[g]]

    # 부품 표 — 이름이 뿔인데 원화가 금이라고 안 하면 그게 알아야 할 일이다
    front = np.array([meta[j].startswith("front/") for j in np.clip(lid, 0, None)]) & (lid >= 0)
    if front.any():
        h, n = np.unique(hue[lid[front]], return_counts=True)
        vote = " ".join("%s %.0f%%" % (h[j], n[j] / n.sum() * 100) for j in np.argsort(-n))
    else:
        vote = "정면 표 없음"
    return lid, vote


def main():
    bpy.ops.wm.open_mainfile(filepath=SRC)
    POLY = mask2d.fitted()
    LBL, COLS, meta = tri_paint.labels(POLY)
    hue = np.array([t.split("/")[1].rstrip("0123456789") for t in meta])
    gold = [j for j, t in enumerate(meta) if hue[j] == "gold"]
    obs = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.data.uv_layers]
    print("부품 %d개: %s" % (len(obs), " ".join(o.name for o in obs)))

    got = assign_labels(obs, LBL)
    allcol, allprov, tot = [], [], 0
    for o in obs:
        lid, ctr, nrm = got[o.name]
        direct = lid >= 0
        lid, vote = fill(o, lid, hue, meta)
        # **뿔은 이름이 이미 말해준다.** 생성 메시에서 두께·단면으로 찾아내야 했던 걸
        # 손으로 지은 것은 공짜로 준다. 표는 그래도 세서 어긋나면 찍는다
        forced = np.zeros(len(lid), bool)
        if "horn" in o.name:
            v = lid[direct]
            v = v[np.array([meta[j].startswith("front/") for j in v], bool)] if len(v) else v
            pick = (np.bincount(v[np.isin(v, gold)]).argmax() if np.isin(v, gold).any()
                    else max(gold, key=lambda j: (lid == j).sum()))
            forced = ~direct | ~np.isin(lid, gold)
            lid[forced] = pick
        print("  %-20s 면 %4d  직접 %3d (%.0f%%)  표: %-28s -> %s"
              % (o.name, len(lid), direct.sum(), direct.mean() * 100, vote,
                 "금 %s 강제 %d면" % (meta[lid[0]], forced.sum()) if "horn" in o.name else "판별"))
        allcol.append(COLS[np.clip(lid, 0, None)])
        allprov.append(np.where(forced, 2, np.where(direct, 0, 1)).astype(np.int8))
        tot += len(lid)

    # 한 판에 굽는다 — 부품들이 이미 같은 0~1 UV 를 나눠 쓰고 있다 (layout(), 72)
    img = np.zeros((tri_uv.ATLAS, tri_uv.ATLAS, 3), np.float32)
    prv = np.zeros_like(img)
    hit = np.zeros((tri_uv.ATLAS, tri_uv.ATLAS), bool)
    for o, c, p in zip(obs, allcol, allprov):
        a, h1 = tri_uv.rasterize(o.data, c, tri_uv.ATLAS)
        b, _ = tri_uv.rasterize(o.data, tri_uv.PROVCOL[p], tri_uv.ATLAS)
        img[h1] = a[h1]; prv[h1] = b[h1]; hit |= h1
    # UV 선 자체를 얹어 본다 — "UV map" 은 구운 색이 아니라 이 배치다
    A = tri_uv.ATLAS
    wire = img.copy()
    for o in obs:
        me = o.data
        uv = np.empty(len(me.loops) * 2); me.uv_layers[0].data.foreach_get("uv", uv)
        uv = uv.reshape(-1, 2)
        ls = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get("loop_start", ls)
        lt = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get("loop_total", lt)
        for i in range(len(me.polygons)):
            U = uv[ls[i]:ls[i] + lt[i]]
            for k in range(len(U)):
                a, b = U[k], U[(k + 1) % len(U)]
                n = max(int(np.hypot(*(b - a)) * A) + 1, 2)
                t = np.linspace(0, 1, n)[:, None]
                q = a[None] * (1 - t) + b[None] * t
                x = np.clip((q[:, 0] * (A - 1)).astype(int), 0, A - 1)
                y = np.clip(((1 - q[:, 1]) * (A - 1)).astype(int), 0, A - 1)
                wire[y, x] = (255, 255, 255)
    tri_uv.save(wire, hit | (wire.sum(2) > 700), "pad_uv_wire.png")

    tri_uv.save(img, hit, "pad_uv_col.png")
    tri_uv.save(prv, hit, "pad_uv_prov.png")

    pr = np.concatenate(allprov)
    print("면 %d — 직접 %.1f%% · 전파 %.1f%% · 금 강제 %.1f%%   색 %d개"
          % (tot, (pr == 0).mean() * 100, (pr == 1).mean() * 100, (pr == 2).mean() * 100,
             len(np.unique(np.concatenate(allcol).round().astype(int), axis=0))))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "pad_uv.blend"))


main()
