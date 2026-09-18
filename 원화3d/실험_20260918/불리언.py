# -*- coding: utf-8 -*-
"""**∩hull 을 복셀 말고 메시 불리언으로** (2026-09-18).

    python 불리언.py 검사       자가검사 (답을 아는 도형)
    python 불리언.py [n]        아직 안 한 장 n 개 -> out/기록/불리언_진행.jsonl
    python 불리언.py 판정       -> out/기록/불리언_<때>.json
    python 불리언.py 그림 [케이스] -> out/불리언.png

09-18 측정(`면.py`): 계단 몫이 TripoSG 생 0.015 인데 우리 `생성∩hull+보충` 은 0.196 이다 —
**우리가 복셀 격자에서 다시 구우면서 계단을 넣는다.** 그래서 깎는 방식을 바꾼다.

    복셀 길 (지금)   생 메시 -> 256³ 복셀 -> & hull -> 마칭큐브        면이 격자에 다시 눕는다
    불리언 길 (이것) 생 메시 ∩ 기둥(front) ∩ 기둥(side) ∩ 기둥(back)   잘리는 자리 말고는 생 메시 면 그대로

기둥은 판 마스크의 윤곽선을 그 시점 축으로 밀어 세운 것이다. 실루엣 교집합의 정의 그대로라
**hull 이 상한이라는 성질이 유지된다** — 복셀 반올림이 없어 오히려 더 정확하다.
"""
import json
import os
import sys
import time

import cv2
import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
for d in ("실험_20260913", "실험_20260915", "실험_20260916", "실험_20260918"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import hull as H
import win as W
import 대조 as C
import 정답 as J
import 생성3D as G3
from 겉면채점 import bench_cases, fill_slices
import 표면 as SF
from 생성깎기 import build as gen_build, voxelize, fill_gaps, sil_fit
from 면 import dihedral, roughness

PROG = os.path.join(HERE, "out", "기록", "불리언_진행.jsonl")
TAG = "불리언 v6 · 실물28 · 판본 5 · 규약대로 채점(양쪽 속채움 · 128·192) · 거칠기 · 못덮음 · 조각 (2026-09-18)"
VARS = ("복셀∩hull", "불리언∩hull", "불리언→복셀", "복셀+보충", "불리언+보충")
PAIRS = {"거칠기": ("불리언∩hull", "복셀∩hull"), "iou": ("불리언∩hull", "복셀∩hull"),
         "거칠기(보충)": ("불리언+보충", "복셀+보충"), "iou(보충)": ("불리언+보충", "복셀+보충"),
         "해상도대조": ("불리언→복셀", "복셀∩hull")}
P192 = (W.U1 - W.U0) / 192.0
EPS_PX = 0.8                                          # 윤곽 단순화 (화소). 격자 256 의 1/5 이라 실루엣에 영향 없다


def unpix(px, py):
    """화소 -> 월드 (u, z). `win.topix` 의 역 — 화소 가운데를 쓴다."""
    u = W.U0 + (np.asarray(px, float) + 0.5) * (W.U1 - W.U0) / W.RES
    z = W.Z1 - (np.asarray(py, float) + 0.5) * (W.Z1 - W.Z0) / W.RES
    return u, z


def polys(mask):
    """마스크 -> [(바깥 고리, [구멍…])] (월드 (u, z) 좌표)."""
    m = mask.astype(np.uint8)
    cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hier is None:
        return []
    hier = hier[0]
    out = []
    for i, c in enumerate(cs):
        if hier[i][3] != -1:                          # 구멍은 부모 차례에 붙인다
            continue
        shell = cv2.approxPolyDP(c, EPS_PX, True)[:, 0, :]
        if len(shell) < 3:
            continue
        holes = []
        j = hier[i][2]
        while j != -1:
            h = cv2.approxPolyDP(cs[j], EPS_PX, True)[:, 0, :]
            if len(h) >= 3:
                holes.append(np.stack(unpix(h[:, 0], h[:, 1]), 1))
            j = hier[j][0]
        out.append((np.stack(unpix(shell[:, 0], shell[:, 1]), 1), holes))
    return out


def prism(mask, view, bs):
    """한 판의 실루엣을 그 시점 축으로 밀어 세운 기둥. 창 전체 깊이([U0, U1])로 민다.

    **trimesh 의 `extrude_polygon` 을 안 쓴다** — 구멍이 여럿인 다각형에서 닫히지 않은 메시가 나온다
    (avatarsample_d 정면: 구멍 11개 · watertight False). manifold3d 의 `CrossSection` 은 홀짝 규칙으로 구멍을 제대로 판다."""
    import manifold3d as m3
    a, sign = W.VIEW_AXIS[view]
    if view == "back":
        sign = bs
    cont = []
    for shell, holes in polys(mask):
        cont.append(np.asarray(shell, np.float64))
        cont += [np.asarray(h, np.float64) for h in holes]
    if not cont:
        return None
    cs = m3.CrossSection(cont, m3.FillRule.EvenOdd)
    ex = cs.extrude(W.U1 - W.U0).translate([0, 0, W.U0])          # 국소 (u, z, 두께)
    # 국소 -> 월드: front·back 은 (sign·u, 두께, z) · side 는 (두께, u, z)
    # 부호를 두 갈래 **모두**에 넣는다 — side 만 하드코딩이면 언젠가 좌우가 뒤집힌 채 조용히 깎는다 (검토 지적)
    M = ([[sign, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]] if a == 0
         else [[0, 0, 1, 0], [sign, 0, 0, 0], [0, 1, 0, 0]])
    out = ex.transform(np.asarray(M, np.float64))
    if out.volume() < 0:                                          # 뒤집힌 감김을 바로 세운다
        out = flip(out)
    return out


def flip(man):
    """감김을 뒤집는다 (부피 부호가 음수일 때)."""
    import manifold3d as m3
    if man.is_empty():
        return man
    msh = man.to_mesh()
    # **`to_mesh()` 는 읽기 전용 배열을 준다** — nanobind 는 쓰기 가능한 것만 받으므로 반드시 복사한다
    V = np.array(np.asarray(msh.vert_properties)[:, :3], np.float32, order="C")
    tv = np.array(np.asarray(msh.tri_verts)[:, ::-1], np.uint32, order="C")
    return m3.Manifold(m3.Mesh(V, tv))


def to_trimesh(man):
    msh = man.to_mesh()
    return trimesh.Trimesh(np.asarray(msh.vert_properties)[:, :3], np.asarray(msh.tri_verts), process=False)


def gen_manifold(mesh):
    """생 메시 -> Manifold. 통째로 안 들어가는 장이 있다 (avatarsample_f: 부피 0) — 그때만 닫힌 덩어리를 골라 합집합한다.
    **쪼개기를 먼저 하면 안 된다** — 통째로 되는 장에서 `split(only_watertight=True)` 조각을 manifold3d 가 대부분 버려
    IoU 가 0.45 -> 0.00 으로 무너진다 (avatarsample_d_darkness, v2 에서 실측)."""
    import manifold3d as m3
    make = lambda m: m3.Manifold(m3.Mesh(np.ascontiguousarray(np.asarray(m.vertices, np.float32)),
                                         np.ascontiguousarray(np.asarray(m.faces, np.uint32))))
    whole = make(mesh)
    # **`is_empty()` 만으로는 못 거른다** — manifold3d 는 비-manifold 입력에서 「비어 있지 않은 쓰레기」를 낸다
    # (cloak_Chest_O72u4Drp8k 면 80 · hairsample_female 면 1,912 로 실제로 났다). 부피를 원본과 대 본다
    if not whole.is_empty() and abs(abs(whole.volume()) - abs(mesh.volume)) < 0.35 * abs(mesh.volume):
        # **3판맞춤이 좌우를 뒤집은 장은 감김이 뒤집혀 부피가 음수다** (28장 중 여럿). 복셀 길은 감김을 안 보지만
        # 불리언은 뒤집힌 것을 「바깥」으로 읽어 교집합이 엉뚱해진다 — 바로 세우고 쓴다
        return whole if whole.volume() > 0 else flip(whole)
    ms = []
    for part in mesh.split(only_watertight=False):
        q = part.copy()
        q.merge_vertices()
        q.update_faces(q.nondegenerate_faces())
        q.update_faces(q.unique_faces())
        q.remove_unreferenced_vertices()
        if not q.is_watertight:
            trimesh.repair.fill_holes(q)
        trimesh.repair.fix_normals(q)
        if len(q.faces) < 4:
            continue
        x = make(q)
        if x.is_empty():
            continue
        if x.volume() < 0:
            x = flip(x)
        if x.volume() > 0:
            ms.append(x)
    assert ms, "닫힌 덩어리가 하나도 없다"
    return m3.Manifold.batch_boolean(ms, m3.OpType.Add)


def boolean_hull(gen_mesh, masks, bs):
    """생 메시 ∩ 기둥 셋. 실루엣 교집합의 정의 그대로다 — 복셀 반올림이 없다."""
    import manifold3d as m3
    parts = [gen_manifold(gen_mesh)] + [prism(masks[v], v, bs) for v in W.VIEWS]
    assert all(p is not None for p in parts), "빈 기둥이 있다"
    return to_trimesh(m3.Manifold.batch_boolean(parts, m3.OpType.Intersect))


def fitted(case, masks):
    g = trimesh.load(os.path.join(G3.GEN, G3.MODEL, case + ".glb"), force="mesh")
    _, V, yaw, mir = G3.orient(g.vertices, masks)
    V = G3.fit_to_art(V, masks)
    return trimesh.Trimesh(V, np.asarray(g.faces), process=False)


def score(truth, mesh, pitch):
    """**규약대로** — 정답과 후보 **둘 다** z 층 속채움 (`생성깎기.py:127` 과 같은 자)."""
    T, ot = J.grid(truth, pitch)
    F = fill_slices(T)
    G, og = J.grid(mesh, pitch)
    Gf = fill_slices(G)
    A, B = J.common(F, ot, Gf, og)
    return round(float((A & B).sum() / max((A | B).sum(), 1)), 5)


def one(case):
    t0 = time.time()
    masks, bs, plain, base, axes = gen_build(case)
    gen = fitted(case, masks)
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    vox = voxelize(gen, axes) & plain
    m_bool = boolean_hull(gen, masks, bs)
    # **해상도 대조군** — 같은 불리언 결과를 복셀 길과 똑같은 256 격자에 다시 구운 것.
    # 「메시로 깎아서 좋아진 몫」과 「더 얇게 · 더 곱게 깎아서 좋아진 몫」을 가른다 (검토 지적)
    vox_of_bool = voxelize(m_bool, axes)
    patch = fill_gaps(vox, base, plain) & ~vox                 # 보충이 더하는 칸
    meshes = {"복셀∩hull": C.to_mesh(vox, axes),
              "불리언∩hull": m_bool,
              "불리언→복셀": C.to_mesh(vox_of_bool, axes),
              "복셀+보충": C.to_mesh(vox | patch, axes),
              "불리언+보충": union_patch(m_bool, patch, axes)}
    voxels = {"복셀∩hull": vox, "불리언∩hull": vox_of_bool, "불리언→복셀": vox_of_bool,
              "복셀+보충": vox | patch, "불리언+보충": vox_of_bool | patch}
    out = {"case": case, "판": TAG, "생": roughness(gen)["거칠기"], "면_생": int(len(gen.faces))}
    for n, m in meshes.items():
        d = dihedral(m)
        sf = sil_fit(voxels[n], masks, bs, axes)
        out[n] = {"거칠기": roughness(m)["거칠기"], "계단": d["계단"], "능선": d["능선"], "면": d["면"],
                  "iou": score(truth, m, J.PITCH), "iou192": score(truth, m, P192),
                  "못덮음": round(max(sf["못덮음_front"], sf["못덮음_side"]), 4),
                  "조각": SF.pieces(voxels[n]), "닫힘": bool(m.is_watertight)}
    out["초"] = round(time.time() - t0, 1)
    return out


def union_patch(m_bool, patch, axes):
    """불리언 결과에 보충 칸을 더한다. 보충은 복셀이라 그 자리만 마칭큐브 면이 된다 (계단이 부분적으로 돌아온다)."""
    import manifold3d as m3
    if not patch.any():
        return m_bool
    pm = C.to_mesh(patch, axes)
    a = gen_manifold(m_bool)
    b = gen_manifold(pm)
    return to_trimesh(m3.Manifold.batch_boolean([a, b], m3.OpType.Add))


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                assert r["case"] not in out, "%s 가 같은 판으로 두 번 적혔다 — 코드가 바뀌었으면 TAG 를 올려라" % r["case"]
                out[r["case"]] = r
    return out


def run(n):
    done = rows()
    todo = [c for c in bench_cases() if c != "소체" and c not in done][:n]
    for c in todo:
        r = one(c)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  %-30s 거칠기 %.3f -> %.3f (생 %.3f · 재샘플 %.3f) · IoU %.3f -> %.3f · 못덮음 %.3f -> %.3f · %.0f초"
              % (c, r["복셀∩hull"]["거칠기"], r["불리언∩hull"]["거칠기"], r["생"], r["불리언→복셀"]["거칠기"],
                 r["복셀∩hull"]["iou"], r["불리언∩hull"]["iou"],
                 r["복셀∩hull"]["못덮음"], r["불리언∩hull"]["못덮음"], r["초"]), flush=True)


def verdict():
    rs = list(rows().values())
    full = [c for c in bench_cases() if c != "소체"]
    missing = [c for c in full if c not in rows()]
    assert len(rs) >= 20, "%d 장만 돌았다" % len(rs)          # 28 장이 목표 · 모자라면 빠진 장을 기록에 남긴다
    med = lambda n, k: round(float(np.median([r[n][k] for r in rs])), 4)
    keys = ("거칠기", "계단", "능선", "면", "iou", "iou192", "못덮음", "조각")
    v = {"판": TAG, "n": len(rs), "목표n": len(full), "빠진장": missing,
         "생 거칠기 중앙": round(float(np.median([r["생"] for r in rs])), 4),
         "중앙": {n: {k: med(n, k) for k in keys} for n in VARS},
         "닫힘": {n: int(sum(r[n]["닫힘"] for r in rs)) for n in VARS}}
    v["차"] = {}
    for name, (a, b) in PAIRS.items():
        k = "iou" if name.startswith("iou") else "거칠기" if name.startswith("거칠기") else "거칠기"
        for kk in (("iou", "iou192") if name.startswith("iou") else (k,)):
            d = np.array([r[a][kk] - r[b][kk] for r in rs], float)
            v["차"]["%s·%s" % (name, kk)] = {"중앙": round(float(np.median(d)), 5),
                                            "승": int((d > 0).sum()), "n": len(rs)}
    p = os.path.join(HERE, "out", "기록", "불리언_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %-14s %8s %8s %8s %8s %8s %7s %6s" % ("판본", "거칠기", "계단", "IoU128", "IoU192", "못덮음", "조각", "면"))
    for n in VARS:
        d = v["중앙"][n]
        print("  %-14s %8.3f %8.3f %8.3f %8.3f %8.4f %7.1f %6d"
              % (n, d["거칠기"], d["계단"], d["iou"], d["iou192"], d["못덮음"], d["조각"], d["면"]))
    print("  생 거칠기", v["생 거칠기 중앙"])
    print("  차", json.dumps(v["차"], ensure_ascii=False))
    print("  ->", p)
    return v


def 논문자료():
    """줄기 논문이 읽을 판정 json · 장별 csv · 그림을 `논문/표면계단/` 에 둔다 (숫자를 손으로 안 박는다)."""
    import csv
    import glob
    import shutil
    import 면 as MM
    d = os.path.join(HERE, "논문", "표면계단")
    os.makedirs(os.path.join(d, "그림"), exist_ok=True)
    for pat, name in (("불리언_2026*.json", "판정.json"), ("면_2026*.json", "면판정.json")):
        shutil.copyfile(sorted(glob.glob(os.path.join(HERE, "out", "기록", pat)))[-1], os.path.join(d, name))
    for f in ("불리언.png", "면.png", "불리언_장별.png"):
        shutil.copyfile(os.path.join(HERE, "out", f), os.path.join(d, "그림", f))
    br, mr = rows(), MM.rows()
    cs = [c for c in bench_cases() if c != "소체" and c in br and c in mr]
    with open(os.path.join(d, "장별.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case", "거칠기_정답", "거칠기_생", "거칠기_복셀", "거칠기_불리언",
                    "계단_복셀", "계단_불리언", "iou_복셀", "iou_불리언", "면_복셀", "면_불리언"])
        for c in cs:
            b, m = br[c], mr[c]
            w.writerow([c, "%.3f" % m["정답"]["거칠기"], "%.3f" % m["TripoSG생"]["거칠기"],
                        "%.3f" % b[VARS[0]]["거칠기"], "%.3f" % b[VARS[1]]["거칠기"],
                        "%.3f" % b[VARS[0]]["계단"], "%.3f" % b[VARS[1]]["계단"],
                        "%.3f" % b[VARS[0]]["iou"], "%.3f" % b[VARS[1]]["iou"],
                        b[VARS[0]]["면"], b[VARS[1]]["면"]])
    print("  -> %s" % d)


def selfcheck():
    """**답을 아는 도형** — 상자 셋의 교집합은 상자다. 그리고 기둥이 마스크를 되찾나."""
    m = np.zeros((W.RES, W.RES), bool)
    (py0, px0), (py1, px1) = W.topix(-0.2, 0.8), W.topix(0.2, 0.2)
    m[int(py0):int(py1), int(px0):int(px1)] = True
    p = to_trimesh(prism(m, "front", +1))
    assert p.is_watertight, "기둥이 안 닫혔다"
    lo, hi = p.bounds
    assert abs(lo[0] + 0.2) < 0.01 and abs(hi[0] - 0.2) < 0.01, "기둥 x 범위가 틀렸다 %s %s" % (lo, hi)
    assert abs(lo[2] - 0.2) < 0.01 and abs(hi[2] - 0.8) < 0.01, "기둥 z 범위가 틀렸다 %s %s" % (lo, hi)
    box = trimesh.creation.box((0.3, 0.3, 0.3), trimesh.transformations.translation_matrix([0, 0, 0.5]))
    got = trimesh.boolean.intersection([box, p], engine="manifold")
    assert abs(got.volume - 0.3 ** 3) < 1e-4, "상자 ∩ 기둥이 상자가 아니다 (%.5f)" % got.volume
    # 구멍 있는 다각형도 닫힌 기둥이 나오나 (trimesh extrude_polygon 이 여기서 샌다)
    m2 = m.copy()
    m2[int(py0) + 120:int(py0) + 200, int(px0) + 60:int(px0) + 140] = False
    p2 = to_trimesh(prism(m2, "front", +1))
    assert p2.is_watertight and p2.volume < p.volume, "구멍 뚫린 기둥이 안 닫혔다"
    # 계단: 같은 구를 복셀로 구운 것과 그냥 둔 것
    sph = trimesh.creation.icosphere(subdivisions=4, radius=0.3)
    g = voxelize(sph, (np.linspace(W.U0, W.U1, 256), np.linspace(W.U0, W.U1, 256), np.linspace(W.Z0, W.Z1, 256)))
    vm = C.to_mesh(g, (np.linspace(W.U0, W.U1, 256), np.linspace(W.U0, W.U1, 256), np.linspace(W.Z0, W.Z1, 256)))
    assert dihedral(vm)["계단"] > 0.15 > dihedral(sph)["계단"], "복셀로 구우면 계단이 생겨야 한다"
    print("  자가검사 통과 — 기둥 범위 · 상자∩기둥 부피 %.5f · 복셀 구 계단 %.2f 대 생 구 %.2f"
          % (got.volume, dihedral(vm)["계단"], dihedral(sph)["계단"]))


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        selfcheck()
    elif a == "판정":
        verdict()
    elif a == "논문자료":
        논문자료()
    elif a == "그림":
        import 불리언그림
        불리언그림.main(sys.argv[2:] or None)
    else:
        H.register_sheets()
        run(int(a))


if __name__ == "__main__":
    main()
