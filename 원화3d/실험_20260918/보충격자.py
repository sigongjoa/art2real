# -*- coding: utf-8 -*-
"""**보충도 격자 없이** — 배포 구성 전체를 메시 영역에서 (2026-09-18).

    python 보충격자.py 검사      자가검사 · 배관
    python 보충격자.py [n]       아직 안 한 장 n 개 -> out/기록/보충격자_진행.jsonl
    python 보충격자.py 판정      -> out/기록/보충격자_<때>.json
    python 보충격자.py 그림      -> out/보충격자.png · out/보충격자_장별.png

판정은 `claudedocs/plan_보충격자_20260918.md` 「Q」 절 그대로다 — 돌리기 전에 적었다.

    A 복셀+보충          현행 배포 구성
    B 불리언+복셀보충     09-18 제안 (∩hull 만 메시)
    C 불리언+hull보충     빈 자리를 기둥 교집합 메시로        격자 없음 · 타원 깎기 못 씀
    D 불리언+높이장보충   빈 자리를 타원 깊이 높이장 메시로    격자 없음 + 타원 깎기 유지 (목표)
    C→복셀 · D→복셀      같은 결과를 256 격자에 다시 굽기     해상도 대조군
"""
import json
import os
import sys
import gc
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
import 표면 as SF
import 대조 as C_
import 정답 as J
from 겉면채점 import bench_cases, fill_slices
from 생성깎기 import build as gen_build, voxelize, fill_gaps, sil_fit
from 면 import dihedral, roughness
from 불리언 import boolean_hull, fitted, gen_manifold, prism, to_trimesh, flip, P192

PROG = os.path.join(HERE, "out", "기록", "보충격자_진행.jsonl")
TAG = "보충격자 v2 · 실물22 · A~D + D→복셀 대조 · 거칠기 · 규약 채점 · 판본 하나씩 (2026-09-18)"
VARS = ("A 복셀+보충", "B 불리언+복셀보충", "C 불리언+hull보충", "D 불리언+높이장보충", "D→복셀")
NPT = 60000                       # 거칠기 표본점 — 쌍 수가 제곱으로 늘어 메모리 봉우리를 만든다


# ── 빈 자리 ──────────────────────────────────────────────────────────────────

def 빈자리(mesh, masks, bs, open_px=3):
    """원화 실루엣 중 이 메시의 투영이 못 덮은 곳 (1024²). 1 화소 테는 열기로 버린다."""
    V, F = np.asarray(mesh.vertices), np.asarray(mesh.faces)
    out = {}
    for v in W.VIEWS:
        s = np.asarray(W.silhouette(V, F, v, bs if v == "back" else None)).astype(bool)
        gap = masks[v] & ~s
        k = np.ones((open_px, open_px), np.uint8)
        out[v] = cv2.morphologyEx(gap.astype(np.uint8), cv2.MORPH_OPEN, k).astype(bool)
    return out


# ── 높이장 솔리드 ────────────────────────────────────────────────────────────

def height_solid(jf, jb, on, axes):
    """앞뒤 높이장 (x, z) -> 닫힌 메시. **y 가 실수라 깊이 방향에 계단이 없다.**

    칸 모서리에 정점을 두고(이웃 켜진 칸의 평균 높이), 켜진 칸마다 윗면 · 아랫면 두 장,
    이웃이 꺼진 변마다 옆벽을 세운다. 경계 변이 모두 벽을 얻으므로 닫힌다."""
    u, _, z = axes
    n = len(u)
    du, dz = u[1] - u[0], z[1] - z[0]
    y_of = lambda a: u[0] + a * du                          # 칸 번호(실수) -> 세계 y
    pad = lambda a: np.pad(a, 1)
    ON = pad(on)
    cnt = ON[:-1, :-1].astype(np.float32) + ON[1:, :-1] + ON[:-1, 1:] + ON[1:, 1:]   # 모서리마다 켜진 이웃 수
    acc = lambda a: (pad(np.where(on, a, 0.0))[:-1, :-1] + pad(np.where(on, a, 0.0))[1:, :-1]
                     + pad(np.where(on, a, 0.0))[:-1, 1:] + pad(np.where(on, a, 0.0))[1:, 1:])
    with np.errstate(invalid="ignore"):
        Yf = np.where(cnt > 0, acc(jf) / np.maximum(cnt, 1), 0.0)
        Yb = np.where(cnt > 0, acc(jb) / np.maximum(cnt, 1), 0.0)
    gx = np.concatenate([u - du / 2, [u[-1] + du / 2]])       # (n+1,)
    gz = np.concatenate([z - dz / 2, [z[-1] + dz / 2]])
    X, Z = np.meshgrid(gx, gz, indexing="ij")
    top = np.stack([X.ravel(), y_of(Yb).ravel(), Z.ravel()], 1)
    bot = np.stack([X.ravel(), y_of(Yf).ravel(), Z.ravel()], 1)
    Vv = np.vstack([top, bot])
    m = (n + 1)
    idx = lambda i, k: i * m + k
    off = len(top)
    i, k = np.nonzero(on)
    a, b, c, d = idx(i, k), idx(i + 1, k), idx(i + 1, k + 1), idx(i, k + 1)
    tris = [np.stack([a, b, c], 1), np.stack([a, c, d], 1),                    # 뒷면(y 큰 쪽)
            np.stack([a + off, c + off, b + off], 1), np.stack([a + off, d + off, c + off], 1)]
    P = np.pad(on, 1)
    for di, dk, (p, q) in ((-1, 0, (0, 3)), (1, 0, (1, 2)), (0, -1, (0, 1)), (0, 1, (3, 2))):
        nb = P[1 + i + di, 1 + k + dk]
        sel = ~nb
        if not sel.any():
            continue
        corners = np.stack([a, b, c, d], 1)[sel]
        e0, e1 = corners[:, p], corners[:, q]
        tris += [np.stack([e0, e1, e1 + off], 1), np.stack([e0, e1 + off, e0 + off], 1)]
    Ff = np.vstack(tris)
    mesh = trimesh.Trimesh(Vv, Ff, process=True)
    mesh.remove_unreferenced_vertices()
    # 옆벽 네 방향의 감김을 손으로 맞추면 틀리기 쉽다 (부피가 0 으로 상쇄됐다) — 닫힌 뒤 한 번에 맞춘다
    trimesh.repair.fix_normals(mesh)
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def 기본_높이장(masks, bs):
    """`hull.carve_depth` 와 같은 규칙으로 앞뒤 높이장을 뽑아 메시로 세운다 (타원 단면)."""
    keep, axes = H.carve(masks, back_sign=bs)
    deps = H.ellipse_depths(keep, axes, bs)
    lam = H.DEPTH_LAM
    u, _, z = axes
    X2, Z2 = np.meshgrid(u, z, indexing="ij")
    j = np.arange(H.N)[None, :, None]
    lo = np.where(keep, j, H.N).min(1).astype(np.float32)
    hi = np.where(keep, j, -1).max(1).astype(np.float32)
    D = np.maximum(hi - lo, 0.0)

    def sample(v):
        a, sign = W.VIEW_AXIS[v]
        py, px = W.topix((bs if v == "back" else sign) * X2, Z2)
        return deps[v][py, px]
    on = keep.any(1)
    def norm(h):
        top = np.where(on, h, 0.0).max(0, keepdims=True)
        return np.where(on, h / np.maximum(top, 1e-6), 0.0)
    jf = lo + (1.0 - norm(sample("front"))) * lam * D
    jb = hi - (1.0 - norm(sample("back"))) * lam * D
    return height_solid(jf, jb, on, axes), axes


# ── 판본 ─────────────────────────────────────────────────────────────────────

def 기둥합(gaps, bs, views=("front", "side")):
    """빈 자리 기둥들의 합집합 (Manifold)."""
    import manifold3d as m3
    ps = [prism(gaps[v], v, bs) for v in views if gaps[v].any()]
    ps = [p for p in ps if p is not None]
    if not ps:
        return None
    return m3.Manifold.batch_boolean(ps, m3.OpType.Add)


def prepare(case):
    """장 하나의 공통 재료. **판본 메시는 여기서 안 만든다** — 여섯을 동시에 들고 있으면 봉우리가 20GB 를 넘는다
    (cape_Hat 실측 20.92GB). 판본은 `make` 로 하나씩 만들고 재고 바로 버린다."""
    import manifold3d as m3
    masks, bs, plain, base, axes = gen_build(case)
    gen = fitted(case, masks)
    vox = voxelize(gen, axes) & plain
    m_bool = boolean_hull(gen, masks, bs)
    del gen
    patch_vox = fill_gaps(vox, base, plain) & ~vox
    gaps = 빈자리(m_bool, masks, bs)
    ctx = {"masks": masks, "bs": bs, "axes": axes, "vox": vox, "patch": patch_vox, "gaps": gaps,
           "bool": m_bool, "B": gen_manifold(m_bool)}
    ctx["gp"] = 기둥합(gaps, bs)
    ctx["hull"] = m3.Manifold.batch_boolean([prism(masks[v], v, bs) for v in W.VIEWS], m3.OpType.Intersect)
    hf_mesh, _ = 기본_높이장(masks, bs)
    ctx["hf"] = gen_manifold(hf_mesh)
    del hf_mesh
    gc.collect()
    return ctx


def make(ctx, name, cache=None):
    """판본 하나를 만든다. `D→복셀` 은 D 를 다시 굽는 것이라 cache 로 받는다."""
    import manifold3d as m3
    axes = ctx["axes"]
    if name == "A 복셀+보충":
        return C_.to_mesh(ctx["vox"] | ctx["patch"], axes)
    if name == "B 불리언+복셀보충":
        if not ctx["patch"].any():
            return ctx["bool"]
        pm = gen_manifold(C_.to_mesh(ctx["patch"], axes))
        return to_trimesh(m3.Manifold.batch_boolean([ctx["B"], pm], m3.OpType.Add))
    if name in ("C 불리언+hull보충", "D 불리언+높이장보충"):
        if ctx["gp"] is None:
            return ctx["bool"]
        src = ctx["hull"] if name.startswith("C") else ctx["hf"]
        pat = m3.Manifold.batch_boolean([src, ctx["gp"]], m3.OpType.Intersect)
        return to_trimesh(m3.Manifold.batch_boolean([ctx["B"], pat], m3.OpType.Add))
    if name == "D→복셀":
        return C_.to_mesh(voxelize(cache, axes), axes)
    raise KeyError(name)


def variants(case, only=None):
    """그림용 — 필요한 판본만 만든다."""
    ctx = prepare(case)
    out, d = {}, None
    for n in (only or VARS):
        if n == "D→복셀" and d is None:
            d = make(ctx, "D 불리언+높이장보충")
        out[n] = make(ctx, n, cache=d)
        if n.startswith("D 불리언"):
            d = out[n]
    return out, ctx


# ── 채점 ─────────────────────────────────────────────────────────────────────

def score(truth, mesh, pitch):
    T, ot = J.grid(truth, pitch)
    Fg, og = J.grid(mesh, pitch)
    A, B = J.common(fill_slices(T), ot, fill_slices(Fg), og)
    return round(float((A & B).sum() / max((A | B).sum(), 1)), 5)


def one(case):
    t0 = time.time()
    ctx = prepare(case)
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    masks, bs, axes = ctx["masks"], ctx["bs"], ctx["axes"]
    out = {"case": case, "판": TAG,
           "빈자리": {v: round(float(ctx["gaps"][v].sum() / max(masks[v].sum(), 1)), 4) for v in W.VIEWS}}
    dmesh = None
    for n in VARS:
        m = make(ctx, n, cache=dmesh)
        vx = voxelize(m, axes)
        sf = sil_fit(vx, masks, bs, axes)
        rec = {"거칠기": roughness(m, n=NPT)["거칠기"], "면": int(len(m.faces)),
               "부피": round(float(abs(m.volume)), 6),
               "iou": score(truth, m, J.PITCH),
               "못덮음": round(max(sf["못덮음_front"], sf["못덮음_side"]), 4),
               "조각": SF.pieces(vx), "닫힘": bool(m.is_watertight)}
        if n != "D→복셀":                                  # 대조군은 128 하나면 된다
            rec["iou192"] = score(truth, m, P192)
        out[n] = rec
        dmesh = m if n.startswith("D 불리언") else dmesh
        if not n.startswith("D 불리언"):
            del m
        del vx
        gc.collect()
    out["초"] = round(time.time() - t0, 1)
    return out


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                assert r["case"] not in out, "%s 가 같은 판으로 두 번 적혔다" % r["case"]
                out[r["case"]] = r
    return out


def todo_cases():
    """얼린 집합 = 불리언 v6 이 돈 22장. **가벼운 장부터** 돈다 —
    무거운 장(궤짝 · 광장: 불리언 면 100만 이상)은 한 장에 600초를 넘겨 백그라운드로 밀리고,
    시스템 메모리가 빠듯할 때 거기서 죽는다. 순서만 바꿔 가벼운 것을 먼저 확보한다."""
    import 불리언 as BL
    r = BL.rows()
    cs = [c for c in bench_cases() if c != "소체" and c in r]
    return sorted(cs, key=lambda c: r[c]["불리언∩hull"]["면"])


def run(n):
    done = rows()
    for c in [x for x in todo_cases() if x not in done][:n]:
        r = one(c)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  %-30s 거칠기 A %.3f · B %.3f · C %.3f · D %.3f (D→복셀 %.3f) · IoU A %.3f D %.3f · %.0f초"
              % (c, r["A 복셀+보충"]["거칠기"], r["B 불리언+복셀보충"]["거칠기"], r["C 불리언+hull보충"]["거칠기"],
                 r["D 불리언+높이장보충"]["거칠기"], r["D→복셀"]["거칠기"],
                 r["A 복셀+보충"]["iou"], r["D 불리언+높이장보충"]["iou"], r["초"]), flush=True)


def verdict():
    rs = list(rows().values())
    full = todo_cases()
    미룬 = [c for c in full if c not in rows()]
    assert len(rs) >= 15, "%d 장만 돌았다" % len(rs)   # 목표 22 · 무거운 장은 미루고 기록에 남긴다
    med = lambda n, k: round(float(np.median([r[n][k] for r in rs])), 4)
    keys = ("거칠기", "iou", "못덮음", "조각", "면", "부피")
    dif = lambda a, b, k: (round(float(np.median([r[a][k] - r[b][k] for r in rs])), 5),
                           int(sum(r[a][k] > r[b][k] for r in rs)))
    A, B, C, D = VARS[0], VARS[1], VARS[2], VARS[3]
    q = {}
    m, w = dif(D, B, "거칠기"); q["Q1 거칠기 D<B"] = {"중앙": m, "우세(D큼)": w, "통과": bool(m < 0 and w < len(rs) / 2)}
    m1, _ = dif(D, A, "iou")
    m2 = round(float(np.median([r[D]["iou192"] - r[A]["iou192"] for r in rs])), 5)
    q["Q2 형상 D≥A−0.005"] = {"128": m1, "192": m2, "통과": bool(m1 >= -0.005 and m2 >= -0.005)}
    mm, _ = dif(D, A, "못덮음"); pc, _ = dif(D, A, "조각")
    q["Q3 약속"] = {"못덮음차": mm, "조각차": pc, "통과": bool(mm <= 0 and pc <= 0)}
    m4, _ = dif("D→복셀", D, "거칠기"); q["Q4 격자 회피"] = {"중앙": m4, "통과": bool(m4 > 0.1)}
    q["Q5 C 대 D"] = {"거칠기차": dif(C, D, "거칠기")[0], "iou차": dif(C, D, "iou")[0]}
    v = {"판": TAG, "n": len(rs), "목표n": len(full), "미룬장": 미룬, "케이스": [r["case"] for r in rs],
         "중앙": {n: {k: med(n, k) for k in keys} for n in VARS},
         "빈자리중앙": {x: round(float(np.median([r["빈자리"][x] for r in rs])), 4) for x in W.VIEWS},
         "닫힘": {n: int(sum(r[n]["닫힘"] for r in rs)) for n in VARS}, "Q": q}
    p = os.path.join(HERE, "out", "기록", "보충격자_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %-18s %8s %8s %8s %7s %9s" % ("판본", "거칠기", "IoU128", "못덮음", "조각", "면"))
    for n in VARS:
        d = v["중앙"][n]
        print("  %-18s %8.3f %8.3f %8.4f %7.1f %9d" % (n, d["거칠기"], d["iou"], d["못덮음"], d["조각"], d["면"]))
    print("  Q", json.dumps(q, ensure_ascii=False))
    print("  ->", p)
    return v


def 논문자료():
    """줄기 논문이 읽을 판정 json · 장별 csv 를 `논문/보충격자/` 에 둔다 (숫자를 손으로 안 박는다)."""
    import csv
    import glob
    import shutil
    d = os.path.join(HERE, "논문", "보충격자")
    os.makedirs(os.path.join(d, "그림"), exist_ok=True)
    shutil.copyfile(sorted(glob.glob(os.path.join(HERE, "out", "기록", "보충격자_2026*.json")))[-1],
                    os.path.join(d, "판정.json"))
    shutil.copyfile(os.path.join(HERE, "out", "기록", "보충입력.json"), os.path.join(d, "입력.json"))
    rs = rows()
    with open(os.path.join(d, "장별.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        짧 = {VARS[0]: "A", VARS[1]: "B", VARS[2]: "C", VARS[3]: "D", VARS[4]: "Dv"}
        w.writerow(["case", "빈front", "빈side"] + ["거칠기_%s" % 짧[n] for n in VARS] +
                   ["iou_A", "iou_D", "못덮음_A", "못덮음_D", "면_A", "면_D"])
        for c, r in sorted(rs.items()):
            w.writerow([c, "%.3f" % r["빈자리"]["front"], "%.3f" % r["빈자리"]["side"]]
                       + ["%.3f" % r[n]["거칠기"] for n in VARS]
                       + ["%.3f" % r[VARS[0]]["iou"], "%.3f" % r[VARS[3]]["iou"],
                          "%.4f" % r[VARS[0]]["못덮음"], "%.4f" % r[VARS[3]]["못덮음"],
                          r[VARS[0]]["면"], r[VARS[3]]["면"]])
    print("  -> %s" % d)


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def selfcheck():
    """높이장 솔리드가 닫히고 부피가 맞나 — 답을 아는 경사면."""
    n = 40
    u = np.linspace(-0.5, 0.5, n)
    z = np.linspace(0.0, 1.0, n)
    axes = (u, u, z)
    on = np.zeros((n, n), bool)
    on[8:32, 8:32] = True
    jf = np.full((n, n), 10.0)
    jb = np.full((n, n), 30.0)
    m = height_solid(jf, jb, on, axes)
    assert m.is_watertight, "높이장 솔리드가 안 닫혔다"
    du = u[1] - u[0]
    want = 24 * du * 24 * (z[1] - z[0]) * (20 * du)
    assert abs(m.volume - want) / want < 0.12, "부피가 틀렸다 %.5f 대 %.5f" % (m.volume, want)
    # 기울어진 앞면 — 계단이 없어야 한다 (거칠기 0 에 가깝다)
    jf2 = 10.0 + 12.0 * (np.arange(n)[:, None] / n) * np.ones((1, n))
    m2 = height_solid(jf2, jb, on, axes)
    r2 = roughness(m2, r=du)["거칠기"]
    assert m2.is_watertight and r2 < 0.12, "기울어진 높이장에 계단이 있다 (%.3f)" % r2
    print("  자가검사 통과 — 높이장 솔리드 닫힘 · 부피 %.5f (기대 %.5f) · 기울기 거칠기 %.3f"
          % (m.volume, want, r2))


def plumb(case=None):
    case = case or todo_cases()[0]
    vs, ctx = variants(case)
    masks, bs, gaps = ctx["masks"], ctx["bs"], ctx["gaps"]
    for n, m in vs.items():
        assert m.is_watertight, "%s 가 안 닫혔다" % n
    for v in W.VIEWS:
        assert not (gaps[v] & ~masks[v]).any(), "빈 자리가 원화 실루엣 밖으로 나갔다"
    vb = abs(vs["B 불리언+복셀보충"].volume)
    for n in ("C 불리언+hull보충", "D 불리언+높이장보충"):
        r = abs(vs[n].volume) / max(vb, 1e-9)
        assert 0.8 < r < 1.25, "%s 부피가 B 의 %.2f 배다" % (n, r)
    print("  배관 통과 — %s · 빈자리 f %.3f s %.3f · 부피비 C %.2f D %.2f"
          % (case, gaps["front"].sum() / max(masks["front"].sum(), 1),
             gaps["side"].sum() / max(masks["side"].sum(), 1),
             abs(vs["C 불리언+hull보충"].volume) / vb, abs(vs["D 불리언+높이장보충"].volume) / vb))


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        selfcheck()
        H.register_sheets()
        plumb()
    elif a == "판정":
        verdict()
    elif a == "논문자료":
        논문자료()
    elif a == "그림":
        import 보충격자그림
        보충격자그림.main(sys.argv[2:] or None)
    else:
        H.register_sheets()
        run(int(a))


if __name__ == "__main__":
    main()
