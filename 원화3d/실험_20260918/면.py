# -*- coding: utf-8 -*-
"""**면이 없다 — 어디서 잃나** (2026-09-18).

    python 면.py 검사        자가검사 (답을 아는 도형)
    python 면.py [n]         아직 안 한 장 n 개 -> out/기록/면_진행.jsonl
    python 면.py 판정        -> out/기록/면_<때>.json
    python 면.py 그림 [케이스] -> out/면.png

사용자 (09-18, 짝 그림을 보고): 「기존의 꺼는 면을 잘 표현하는데 우리꺼는 면 자체가 없어 매끄럽지 않다」.

**「면이 없다」를 이웃 면 사이 각(dihedral)의 면적 가중 분포로 잰다.** 가정이 없다.

    평평    이웃 각 < 5°     한 평면 위에 있는 몫. 저폴리 정답은 여기가 크다
    계단    30° ~ 60°        마칭큐브가 복셀 격자에서 만드는 각. **우리 것의 특징**
    능선    > 60°            일부러 꺾은 모서리

물음: TripoSG 원본 메시에는 면이 있나. 있다면 **우리가 ∩hull 을 복셀로 하면서 잃는 것**이다
(그러면 고칠 자리는 후처리가 아니라 메시 불리언이다).
"""
import json
import os
import sys
import time

import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
for d in ("실험_20260913", "실험_20260915", "실험_20260916"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import hull as H
import win as W
import 대조 as C
from 겉면채점 import bench_cases
from 생성깎기 import variants as gen_variants
import 생성3D as G3

PROG = os.path.join(HERE, "out", "기록", "면_진행.jsonl")
TAG = "면 v2 · 실물28 · 정답 · TripoSG생 · 생성∩hull+보충 · 지금 기본 · 이웃각 분포 (2026-09-18)"
VARS = ("정답", "TripoSG생", "생성∩hull+보충", "지금 기본")


def dihedral(mesh):
    """이웃 면 사이 각의 **면적 가중** 분포 -> (평평 <5° · 계단 30~60° · 능선 >60° · 중앙각)."""
    m = mesh.copy()
    m.merge_vertices()
    # **퇴화면을 먼저 버린다** — 면적 0 삼각형의 법선은 [0,0,0] 이라 cos 가 0 이 되고 90°(능선)로 잘못 집계된다 (검토 지적).
    # `nondegenerate_faces()` 는 길이 문턱이라 법선 0 을 다 못 걸러낸다 — 법선 길이로 직접 자른다
    ok = np.linalg.norm(np.asarray(m.face_normals), axis=1) > 0.5
    if not ok.all():
        m.update_faces(ok)
        m.remove_unreferenced_vertices()
    pairs = m.face_adjacency
    if len(pairs) == 0:
        return {"평평": 0.0, "계단": 0.0, "능선": 0.0, "중앙각": 0.0, "면": len(m.faces)}
    n = m.face_normals
    assert np.linalg.norm(n, axis=1).min() > 0.5, "법선이 0 인 면이 남았다"
    cos = np.clip((n[pairs[:, 0]] * n[pairs[:, 1]]).sum(1), -1, 1)
    ang = np.degrees(np.arccos(cos))
    a = m.area_faces
    w = (a[pairs[:, 0]] + a[pairs[:, 1]]) / 2                    # 이웃 쌍의 면적 몫
    w = w / w.sum()
    f = lambda sel: round(float(w[sel].sum()), 4)
    return {"평평": f(ang < 5), "계단": f((ang >= 30) & (ang < 60)), "능선": f(ang >= 60),
            "중앙각": round(float(np.median(ang)), 2), "면": int(len(m.faces))}


R_STEP = (W.U1 - W.U0) / 256.0          # 격자 한 칸 = 키의 1/213 (150mm 에 0.7mm)


def roughness(mesh, r=None, n=120000, seed=0):
    """**쪼개기에 안 흔들리는 거칠기.** 표면에서 면적 비례로 점을 뽑아, 반지름 r 안의 이웃 쌍 중
    법선 각이 30° 를 넘는 비율.

    이웃각(dihedral) 분포는 **면 수에 휘둘린다** — 같은 복셀 메시를 두 번 세분하면 기하는 그대로인데
    계단 몫이 0.236 -> 0.118 -> 0.059 로 떨어진다 (09-18 실측). 면을 잘게 쪼개면 0° 쌍이 늘어 계단이 희석돼서다.
    점을 뽑아 **공간 거리 r** 로 이웃을 잡으면 삼각형 나누기와 무관해진다. r 은 격자 한 칸으로 고정한다 —
    「격자 한 칸 거리에서 면이 얼마나 꺾이나」가 곧 계단이다."""
    from scipy.spatial import cKDTree
    r = r or R_STEP
    rng = np.random.default_rng(seed)
    pts, fid = trimesh.sample.sample_surface(mesh, n, seed=seed) if hasattr(trimesh.sample, "sample_surface") else (None, None)
    nrm = np.asarray(mesh.face_normals)[fid]
    tree = cKDTree(pts)
    pairs = tree.query_pairs(r, output_type="ndarray")
    if len(pairs) == 0:
        return {"거칠기": 0.0, "쌍": 0}
    if len(pairs) > 2_000_000:
        pairs = pairs[rng.choice(len(pairs), 2_000_000, replace=False)]
    cos = np.clip((nrm[pairs[:, 0]] * nrm[pairs[:, 1]]).sum(1), -1, 1)
    ang = np.degrees(np.arccos(np.abs(cos)))          # 감김 방향은 무시 (|cos|)
    return {"거칠기": round(float((ang > 30).mean()), 4), "쌍": int(len(pairs))}


def meshes(case):
    vs, plain, axes, masks, bs = gen_variants(case)
    out = {"정답": trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh"),
           "TripoSG생": trimesh.load(os.path.join(G3.GEN, G3.MODEL, "%s.glb" % case), force="mesh"),
           "생성∩hull+보충": C.to_mesh(vs["생성∩hull+보충"], axes),
           "지금 기본": C.to_mesh(vs["지금 기본"], axes)}
    return out


def one(case):
    t0 = time.time()
    out = {"case": case, "판": TAG}
    for n, m in meshes(case).items():
        out[n] = dihedral(m)
        out[n].update(roughness(m))
    out["초"] = round(time.time() - t0, 1)
    return out


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[r["case"]] = r
    return out


def run(n):
    done = rows()
    todo = [c for c in bench_cases() if c != "소체" and c not in done][:n]
    for c in todo:
        r = one(c)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  %-36s " % c + " · ".join("%s 평평 %.2f 계단 %.2f" % (n, r[n]["평평"], r[n]["계단"]) for n in VARS), flush=True)


def verdict():
    rs = list(rows().values())
    assert len(rs) >= 28, "%d 장만 돌았다" % len(rs)
    med = lambda n, k: round(float(np.median([r[n][k] for r in rs])), 4)
    v = {"판": TAG, "n": len(rs),
         "중앙": {n: {k: med(n, k) for k in ("거칠기", "평평", "계단", "능선", "중앙각", "면")} for n in VARS},
         "장별": {r["case"]: {n: r[n]["평평"] for n in VARS} for r in rs}}
    p = os.path.join(HERE, "out", "기록", "면_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %-16s %8s %7s %7s %7s %8s" % ("판본", "거칠기", "평평", "계단", "능선", "면"))
    for n in VARS:
        d = v["중앙"][n]
        print("  %-16s %8.3f %7.3f %7.3f %7.3f %8d" % (n, d["거칠기"], d["평평"], d["계단"], d["능선"], d["면"]))
    print("  ->", p)
    return v


def selfcheck():
    """답을 아는 도형 — 상자는 평평이 크고 계단이 0, 복셀로 구운 구는 계단이 크다."""
    box = trimesh.creation.box((1, 1, 1))
    d = dihedral(box)
    # 상자 12 삼각형: 면 안쪽 대각 6 쌍(0°) + 모서리 12 쌍(90°) -> 평평 1/3 · 능선 2/3 가 **맞는 값**이다
    assert 0.3 < d["평평"] < 0.4 and d["계단"] == 0 and d["능선"] > 0.6, "상자가 틀렸다 %s" % d
    sph = trimesh.creation.icosphere(subdivisions=3, radius=0.5)
    ds = dihedral(sph)
    # 세분 3 구는 이웃각 중앙이 5.4° 라 「평평(<5°)」에 절반쯤만 든다 — 문턱이 절대값이 아니라 판본 비교용이라는 뜻
    assert ds["평평"] > 0.3 and ds["능선"] == 0 and ds["중앙각"] < 10, "고운 구가 틀렸다 %s" % ds
    g = np.zeros((40, 40, 40), bool)
    z, y, x = np.mgrid[0:40, 0:40, 0:40]
    g[((z - 20) ** 2 + (y - 20) ** 2 + (x - 20) ** 2) < 14 ** 2] = True
    V, F = H.mesh_from(g, (np.arange(40) / 40.0,) * 3)
    dv = dihedral(trimesh.Trimesh(V, F, process=True))
    # **복셀 구는 평평도 더 크다** (계단은 평평 — 45° — 평평의 되풀이라서). 그래서 「면이 있나」를 평평으로 읽으면 안 된다.
    # 판본을 가르는 건 계단 몫이다 — 매끈한 구 0.00, 복셀 구 0.25
    assert dv["계단"] > 0.15 > ds["계단"] and dv["평평"] > ds["평평"], "복셀 구의 계단이 안 잡힌다 %s" % dv
    # **거칠기는 쪼개기에 안 흔들려야 한다** — 같은 복셀 메시를 두 번 세분해도 값이 그대로여야 자가 맞다
    vm = trimesh.Trimesh(V, F, process=True)
    r0 = roughness(vm)["거칠기"]
    sub = vm.copy()
    for _ in range(2):
        Vs, Fs = trimesh.remesh.subdivide(sub.vertices, sub.faces)
        sub = trimesh.Trimesh(Vs, Fs, process=False)
    r2, d2 = roughness(sub)["거칠기"], dihedral(sub)["계단"]
    assert abs(r2 - r0) < 0.03, "거칠기가 쪼개기에 흔들린다 (%.3f -> %.3f)" % (r0, r2)
    assert d2 < 0.6 * dv["계단"], "계단 지표가 쪼개기에 안 흔들렸다 — 자가검사 전제가 틀렸다"
    assert roughness(sph)["거칠기"] < 0.05 < r0, "매끈한 구와 복셀 구의 거칠기가 안 갈린다"
    print("  자가검사 통과 — 상자 평평 %.2f · 복셀 구 계단 %.2f(세분 %.2f) · 거칠기 %.3f(세분 %.3f) · 매끈 구 %.3f"
          % (d["평평"], dv["계단"], d2, r0, r2, roughness(sph)["거칠기"]))


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        selfcheck()
    elif a == "판정":
        verdict()
    elif a == "그림":
        import 면그림
        면그림.main(sys.argv[2:] or None)
    else:
        H.register_sheets()
        run(int(a))


if __name__ == "__main__":
    main()
