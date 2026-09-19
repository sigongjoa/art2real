# -*- coding: utf-8 -*-
"""**2 차 — 광원을 추정하고, 1 차 영역 안을 밝기로 쪼갠다** (2026-09-19).

    python 알베도광원.py 검사   자가검사 (합성 구·상자로 광원 되찾기 · 분할 거동)
    python 알베도광원.py [n]    아직 안 한 (장 × 광원) n 개 -> out/기록/알베도광원_진행.jsonl
    python 알베도광원.py 판정   -> out/기록/알베도광원_<때>.json
    python 알베도광원.py 그림   -> out/알베도광원.png

사용자 (09-19): 「빛이 고정되어 있으니까 각도 차이가 생겨서 밝기 변화가 생긴다는 거지?
**좌상단이 고정이 아니라 빛의 위치를 추정해야지?** 광원의 위치겠네」

판정은 `claudedocs/plan_알베도면_20260919.md` 「12 Q」 그대로다 — 돌리기 전에 적었다.
1 차 코드는 `알베도면.py` 를 그대로 쓴다 (`cut` · `cc` · `marks` · `voronoi` · `albedo_regions`).

## 이 파일이 재는 것

    조건 R   우리가 빛을 넣어 관측을 만든다. I = 알베도 · clamp(n·l,0,1) · 8 비트.
             **진짜 l 을 알므로 광원 추정이 채점된다**
    조건 B   드릴처럼 텍스처에 음영이 이미 박힌 장 — 진짜 l 이 없다. 적합도만 본다 (곁가지)

**2 차 분할 자체에는 l 이 안 들어간다** (1 차 영역 안에서 ρ 가 상수라 밝기 상수 = n·l 상수).
l 이 필요한 자리는 조각을 3D 로 세울 때와, 이 광원에서 **원리적으로 못 갈리는 평면쌍**을 아는 것이다.
"""
import json
import os
import sys
import time

import cv2
import numpy as np
import trimesh
from scipy import ndimage

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260913"))
sys.path.insert(0, os.path.join(HERE, "실험_20260919"))
os.chdir(HERE)
import 알베도면 as A1

PROG = os.path.join(HERE, "out", "기록", "알베도광원_진행.jsonl")
TAG = "알베도광원 v1 · 조건R 3장×광원2 · 윤곽음영 광원추정 · 1차영역 안 밝기분할 (2026-09-19)"

# 광원 둘. **L_A 가 조율자가 고정하자던 좌상단 45° 다.**
# 카메라 쪽은 **+y** 다 — `win.py` 규약은 「앞이 −y」지만 `시트.main`(과 `cut`)이 glTF 모델의
# 깊이를 한 번 뒤집으므로, 이 창에서 보이는 면의 법선은 n_y > 0 이다 (자가검사가 박는다).
LIGHTS = {"L_A 좌상단": np.array([-1.0, 1.0, 1.0]) / np.sqrt(3),
          "L_B 우하단": np.array([0.80, 0.40, -0.45]) / np.linalg.norm([0.80, 0.40, -0.45])}
FIXED = LIGHTS["L_A 좌상단"]          # 「좌상단 45° 고정」 대조군이 늘 내놓는 답
QS = 12                                # 2 차 밝기 양자화 단계
BAND = (2.0, 6.0)                      # 윤곽 띠 (실루엣 안쪽 거리, 화소)
DEGEN = 0.02                           # 이 광원에서 「못 가른다」고 보는 |Δ(n·l)|


# ------------------------------------------------------------------ 관측 만들기

def normals_at(Vw, F, ident):
    """화소마다 면 법선. 방향은 **부피 부호로 한 번에** 맞춘다.

    처음엔 「보이는 면은 n_y < 0」으로 화소마다 뒤집었는데, **가림 윤곽에서는 n_y ≈ 0 이라
    부호가 잡음으로 뒤집혀** 윤곽 법선이 통째로 반대가 됐다 (자가검사 구: 169.3°).
    감김은 메시 전체의 성질이므로 전역으로 한 번만 맞춘다."""
    m = trimesh.Trimesh(Vw, F, process=False)
    n = np.asarray(m.face_normals, np.float64)
    if m.volume < 0:
        n = -n
    return n[np.clip(ident, 0, None)]


def render(rgb, N, mask, l):
    """관측 = 알베도 휘도 × clamp(n·l, 0, 1). 8 비트로 떨군다 (진짜 그림이 그렇다)."""
    rho = rgb.astype(np.float64) @ np.array([0.299, 0.587, 0.114])
    obs = np.where(mask, rho * np.clip(N @ l, 0, 1), 0)
    return np.clip(np.rint(obs), 0, 255).astype(np.uint8), rho


# ------------------------------------------------------------------ 광원 추정 (가림 윤곽)

def contour_band(mask):
    """실루엣 안쪽 띠와 그 자리의 **화면 바깥 방향**. 매끈한 면이면 그게 곧 표면 법선이다.

    front 창에서 화면 (열, 행) = 월드 (+x, −z) 다. 바깥 방향은 −∇(흐린 마스크)."""
    d = ndimage.distance_transform_edt(mask)
    band = mask & (d >= BAND[0]) & (d <= BAND[1])
    g = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 2.0)
    gy, gx = np.gradient(g.astype(np.float64))
    u = np.stack([-gx, -gy], -1)
    u /= np.linalg.norm(u, axis=-1, keepdims=True) + 1e-12
    return band, np.stack([u[:, :, 0], -u[:, :, 1]], -1)      # -> 월드 (x, z)


def estimate_light(obs, reg, mask):
    """윤곽 띠에서 l 을 푼다.

        I = ρ_r · (cx·lx + cz·lz)     영역 r 안에서 ρ_r 은 상수

    영역마다 최소제곱으로 v_r ∈ R² 를 얻고, **방향**만 모아 (lx, lz) 를 낸다 (ρ_r 이 크기를 먹는다).
    l_y(카메라 축)는 윤곽에서 **원리적으로 안 읽힌다** — 영역 최대 밝기를 ρ̂_r 로 보고
    s = |v_r|/ρ̂_r 로 되찾는다 (제일 밝은 화소가 빛을 정면으로 받는다는 가정)."""
    band, C = contour_band(mask)
    acc, ws, ss = np.zeros(2), 0.0, []
    for r in np.unique(reg[band]):
        m = band & (reg == r)
        if m.sum() < 30:
            continue
        lit = obs[m] > 3                                  # **밝은 쪽만 쓴다** — clamp(·,0) 이
        if lit.sum() < 20:                                # 어두운 쪽을 0 으로 눌러 최소제곱을 편향시킨다
            continue                                      # (자가검사 구: s 0.42 -> 0.80)
        c, i = C[m][lit], obs[m][lit].astype(np.float64)
        v, *_ = np.linalg.lstsq(c, i, rcond=None)
        nv = np.linalg.norm(v)
        if nv < 1e-6:
            continue
        w = float(m.sum())
        acc += w * v / nv
        ws += w
        rho = float(obs[mask & (reg == r)].max())
        if rho > 1:
            ss.append(min(nv / rho, 1.0))
    if ws == 0 or not ss:
        return np.array([0.0, 1.0, 0.0]), 0.0
    u = acc / np.linalg.norm(acc)
    s = float(np.median(ss))
    l = np.array([s * u[0], np.sqrt(max(1 - s * s, 0.0)), s * u[1]])   # 카메라 쪽이 +y
    return l / np.linalg.norm(l), s


def ang(a, b):
    return float(np.degrees(np.arccos(np.clip(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)), -1, 1))))


def azi(a, b):
    """화면 안(x, z) 방위 오차."""
    p, q = np.array([a[0], a[2]]), np.array([b[0], b[2]])
    if np.linalg.norm(p) < 1e-9 or np.linalg.norm(q) < 1e-9:
        return 180.0
    return ang(np.array([p[0], 0, p[1]]), np.array([q[0], 0, q[1]]))


# ------------------------------------------------------------------ 2 차 분할

def shade_split(obs, reg, mask, qs=QS, amin=A1.AMIN):
    """**1 차 영역 안에서 밝기로 쪼갠다.** ρ 가 영역 안에서 상수이므로 밝기 상수 = n·l 상수다.
    l 은 여기 안 들어간다."""
    q = np.minimum(obs.astype(np.int32) * qs // 256, qs - 1)
    return A1.cc(reg.astype(np.int64) * qs + q, mask, amin)


def split_control(reg, mask, k, seed=0):
    """**자유도 대조군** — 1 차 영역을 무작위로 더 쪼개 조각 수만 2 차와 맞춘 것.
    2 차의 이득이 「조각이 늘어서」가 아님을 본다."""
    extra = max(k - int(reg[mask].max() + 1), 0)
    if extra == 0:
        return reg
    vor = A1.voronoi(mask, extra + 1, seed=seed)
    return A1.cc(reg.astype(np.int64) * (extra + 1) + np.clip(vor, 0, None), mask, 1)


def degeneracy(Vw, F, ident, mask, l):
    """이 광원에서 **원리적으로 못 가르는** 인접 정답 평면쌍의 몫."""
    lab = A1.plane_faces(Vw, F, 15.0)
    g = A1.cc(lab[np.clip(ident, 0, None)], mask, A1.AMIN)
    n = normals_at(Vw, F, ident)
    sh = np.clip(n @ l, 0, 1)
    v = {int(k): float(np.median(sh[mask & (g == k)])) for k in np.unique(g[mask])}
    a, b = g[:, :-1][mask[:, :-1] & mask[:, 1:]], g[:, 1:][mask[:, :-1] & mask[:, 1:]]
    c, d = g[:-1][mask[:-1] & mask[1:]], g[1:][mask[:-1] & mask[1:]]
    p = set(map(tuple, map(sorted, zip(np.r_[a, c].tolist(), np.r_[b, d].tolist()))))
    p = [x for x in p if x[0] != x[1]]
    if not p:
        return {"인접쌍": 0, "못가르는몫": 0.0}
    bad = sum(1 for i, j in p if abs(v[i] - v[j]) < DEGEN)
    return {"인접쌍": len(p), "못가르는몫": round(bad / len(p), 4)}


# ------------------------------------------------------------------ 한 판 (장 × 광원)

def one(case, lname):
    t0 = time.time()
    l = LIGHTS[lname]
    rgb, ident, Vw, F = A1.cut(case)
    mask = ident >= 0
    N = normals_at(Vw, F, ident)
    obs, _ = render(rgb, N, mask, l)
    reg = A1.albedo_regions(rgb, mask, 12, A1.AMIN)
    gt = A1.cc(A1.plane_faces(Vw, F, 15.0)[np.clip(ident, 0, None)], mask, A1.AMIN)

    out = {"case": case, "광원": lname, "판": TAG}
    # ⓪ 윤곽 법선 가정의 입력 검사 — 매끈한 면에서만 맞는다
    band, C = contour_band(mask)
    tn = N[band]
    cn = np.stack([C[band][:, 0], np.zeros(band.sum()), C[band][:, 1]], 1)
    out["⓪윤곽법선오차"] = {"중앙": round(float(np.median([ang(a, b) for a, b in zip(tn[::7], cn[::7])])), 1),
                            "띠화소": int(band.sum())}

    lh, s = estimate_light(obs, reg, mask)
    out["광원추정"] = {"l참": [round(float(x), 4) for x in l], "l추정": [round(float(x), 4) for x in lh],
                       "s": round(s, 4),
                       "방위오차": round(azi(lh, l), 1), "3D각도오차": round(ang(lh, l), 1),
                       "고정_방위오차": round(azi(FIXED, l), 1), "고정_3D각도오차": round(ang(FIXED, l), 1)}
    rng = np.random.default_rng(0)
    rr = rng.normal(size=(100, 3)); rr[:, 1] = np.abs(rr[:, 1])       # 카메라 쪽 반구
    rr /= np.linalg.norm(rr, axis=1, keepdims=True)
    out["광원추정"]["무작위_방위오차중앙"] = round(float(np.median([azi(x, l) for x in rr])), 1)
    out["광원추정"]["무작위_3D각도오차중앙"] = round(float(np.median([ang(x, l) for x in rr])), 1)

    seg = shade_split(obs, reg, mask)
    out["1차"] = A1.marks(gt, reg, mask)
    out["2차"] = A1.marks(gt, seg, mask)
    k = out["2차"]["조각"]
    out["C1 보로노이@2차"] = A1.marks(gt, A1.voronoi(mask, k), mask)
    out["C2 1차@같은조각수"] = A1.marks(gt, split_control(reg, mask, k), mask)
    out["L3"] = degeneracy(Vw, F, ident, mask, l)
    out["초"] = round(time.time() - t0, 1)
    return out


def baked_fit(case="mech_Drill_8uBbH7Dvmb"):
    """**조건 B (곁가지).** 구워진 팔레트 밝기가 한 광원의 램버시안인가.
    GT 법선을 쓰는 **오라클 적합**이다 — 진짜 l 이 없으므로 채점이 아니라 적합도만 본다."""
    import 시트 as SH
    import win as W
    sc = trimesh.load(os.path.join(HERE, "out", "모델", "%s.glb" % case))
    V, F, col, mat = SH.faces_with_color(sc)
    Vw = W.to_world(V, "xyz"); Vw[:, 1] *= -1; Vw = W.normalize(Vw)
    n = np.asarray(trimesh.Trimesh(Vw, F, process=False).face_normals, np.float64)
    lum = col.astype(np.float64) @ np.array([0.299, 0.587, 0.114])

    def fit(sel):
        X = np.c_[n[sel], np.ones(int(sel.sum()))]
        b, *_ = np.linalg.lstsq(X, lum[sel], rcond=None)
        y = lum[sel]
        return {"면": int(sel.sum()), "R²": round(float(1 - ((y - X @ b) ** 2).sum() / max(((y - y.mean()) ** 2).sum(), 1e-9)), 4),
                "맞은 l": [round(float(x), 3) for x in b[:3] / (np.linalg.norm(b[:3]) + 1e-12)],
                "밝기": [round(float(y.min()), 0), round(float(y.max()), 0)]}

    return {"case": case, "전체": fit(np.ones(len(F), bool)),
            "재질별": {"재질%d" % m: fit(mat == m) for m in np.unique(mat)}}


# ------------------------------------------------------------------ 진행 · 판정

JOBS = [(c, n) for c in A1.CASES for n in LIGHTS]


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[(r["case"], r["광원"])] = r
    return out


def run(n):
    done = rows()
    for c, ln in [j for j in JOBS if j not in done][:n]:
        r = one(c, ln)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        e = r["광원추정"]
        print("  %-10s %-10s 방위 %5.1f° (고정 %5.1f° · 무작위 %4.1f°) · 3D %5.1f° · 윤곽법선오차 %4.1f° · "
              "1차 %.3f -> 2차 %.3f (조각 %d) · C1 %.3f · C2 %.3f"
              % (A1.NICK[c], ln, e["방위오차"], e["고정_방위오차"], e["무작위_방위오차중앙"],
                 e["3D각도오차"], r["⓪윤곽법선오차"]["중앙"], r["1차"]["매칭IoU"], r["2차"]["매칭IoU"],
                 r["2차"]["조각"], r["C1 보로노이@2차"]["매칭IoU"], r["C2 1차@같은조각수"]["매칭IoU"]),
              flush=True)


JUDGE = ("cloak_Chest_Closed_AngpV0HxD8",)     # L2 판정에 쓰는 장 (계획 12절) — 모자·드릴은 뺀다


def verdict():
    rs = rows()
    assert len(rs) == len(JOBS), "%d/%d 판만 돌았다" % (len(rs), len(JOBS))
    v = {"판": TAG, "n": len(rs),
         "정정": ["조율자가 1차 단계에서 낸 정답 평면 수(44·97·101)는 「법선 6단계 양자화」로 잡은 값이라 틀렸다. "
                  "옳은 정의(이면각 15° 연결 + 화면 연결성분)로는 88·131·5 다 — 모자가 101 이 아니라 5 인 까닭.",
                  "「좌상단 45° 로 고정」 제안은 관측에서 읽을 수 있는 값을 가정으로 바꾸는 것이라 철회하고, 이 바퀴에서 대조군으로 내렸다."],
         "광원": {k: [round(float(x), 4) for x in w] for k, w in LIGHTS.items()},
         "광원사이각": round(ang(*LIGHTS.values()), 1),
         "판": TAG, "조건B 드릴 구워진음영 오라클적합": baked_fit(), "판별": {}}
    for (c, ln), r in rs.items():
        v["판별"]["%s · %s" % (A1.NICK[c], ln)] = {k: r[k] for k in r if k not in ("case", "광원", "판")}

    e = lambda c, ln: rs[(c, ln)]["광원추정"]
    L1a = {"%s·%s" % (A1.NICK[c], ln): e(c, ln)["방위오차"] for c, ln in JOBS}
    L1b = {"%s·%s" % (A1.NICK[c], ln): e(c, ln)["3D각도오차"] for c, ln in JOBS}
    L1c = {"%s" % A1.NICK[c]: {"추정": e(c, "L_B 우하단")["방위오차"], "고정": e(c, "L_B 우하단")["고정_방위오차"],
                               "추정이김": bool(e(c, "L_B 우하단")["방위오차"] < e(c, "L_B 우하단")["고정_방위오차"])}
           for c in A1.CASES}
    L2 = {}
    for c, ln in JOBS:
        r = rs[(c, ln)]
        L2["%s·%s" % (A1.NICK[c], ln)] = {
            "1차": r["1차"]["매칭IoU"], "2차": r["2차"]["매칭IoU"],
            "차": round(r["2차"]["매칭IoU"] - r["1차"]["매칭IoU"], 4),
            "−C1": round(r["2차"]["매칭IoU"] - r["C1 보로노이@2차"]["매칭IoU"], 4),
            "−C2": round(r["2차"]["매칭IoU"] - r["C2 1차@같은조각수"]["매칭IoU"], 4),
            "잘림": r["2차"]["잘림"], "순도": r["2차"]["순도"], "조각": r["2차"]["조각"],
            "정답조각": r["2차"]["정답조각"]}
    ok2 = all(L2["%s·%s" % (A1.NICK[c], ln)]["차"] >= 0.10 for c in JUDGE for ln in LIGHTS) \
        and all(x["차"] >= -0.05 for x in L2.values()) \
        and all(L2["%s·%s" % (A1.NICK[c], ln)]["−C1"] >= 0.10 and L2["%s·%s" % (A1.NICK[c], ln)]["−C2"] >= 0.05
                for c in JUDGE for ln in LIGHTS)
    v["L1a 방위오차 ≤ 20°"] = L1a
    v["L1b 3D각도오차 ≤ 30°"] = L1b
    v["L1c L_B 에서 고정을 이기나"] = L1c
    v["L2 2차가 1차보다 (판정장 = 궤짝)"] = L2
    v["L3 광원이 정한 상한"] = {"%s·%s" % (A1.NICK[c], ln): rs[(c, ln)]["L3"] for c, ln in JOBS}
    v["판정"] = {"L1a": all(x <= 20 for x in L1a.values()), "L1b": all(x <= 30 for x in L1b.values()),
                 "L1c": all(x["추정이김"] for x in L1c.values()), "L2": bool(ok2)}
    p = os.path.join(HERE, "out", "기록", "알베도광원_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("\n  %-22s %8s %8s %8s %9s %8s %8s %7s" % ("장 · 광원", "방위°", "고정°", "3D°", "1차", "2차", "−C1", "−C2"))
    for c, ln in JOBS:
        k = "%s·%s" % (A1.NICK[c], ln)
        print("  %-22s %8.1f %8.1f %8.1f %9.3f %8.3f %8.3f %7.3f"
              % (k, L1a[k], e(c, ln)["고정_방위오차"], L1b[k], L2[k]["1차"], L2[k]["2차"], L2[k]["−C1"], L2[k]["−C2"]))
    print("\n  판정 %s" % json.dumps(v["판정"], ensure_ascii=False))
    print("  ->", p)
    return v


# ------------------------------------------------------------------ 그림

def 그림():
    from 깊이색 import grid
    rws = []
    for case in A1.CASES:
        rgb, ident, Vw, F = A1.cut(case)
        mask = ident >= 0
        N = normals_at(Vw, F, ident)
        reg = A1.albedo_regions(rgb, mask, 12, A1.AMIN)
        gt = A1.cc(A1.plane_faces(Vw, F, 15.0)[np.clip(ident, 0, None)], mask, A1.AMIN)
        tiles = [A1.tint(reg, mask)]
        for ln in LIGHTS:
            obs, _ = render(rgb, N, mask, LIGHTS[ln])
            tiles.append(np.dstack([obs] * 3))
            tiles.append(A1.tint(shade_split(obs, reg, mask), mask))
        tiles.append(A1.tint(gt, mask))
        rws.append((A1.NICK[case], tiles))
    grid(rws, ["1차 알베도 영역", "관측 L_A(좌상단)", "2차 @L_A", "관측 L_B(우하단)", "2차 @L_B", "정답 평면"],
         "2차 — 광원을 추정하고 1차 영역 안을 밝기로 쪼갠다 · front 한 컷 (2026-09-19)",
         "관측 = 알베도 × clamp(n·l). 색은 조각 번호 무작위. **광원이 바뀌면 갈리는 면이 바뀐다** — 그게 L3 이다",
         os.path.join(HERE, "out", "알베도광원.png"))


# ------------------------------------------------------------------ 자가검사

def _tilted_box():
    """앞에서 **두 면이 보이는** 상자 — 2 차가 쪼갤 것이 있어야 검사가 뜻을 갖는다."""
    import trimesh.transformations as TT
    b = trimesh.creation.box((0.7, 0.7, 0.9))
    b.apply_transform(TT.rotation_matrix(np.radians(30), [0, 0, 1]))
    return b


def selfcheck():
    """합성 구 · 상자로 광원을 되찾는다. **윤곽 법선 가정은 매끈한 면에서만 맞는다** —
    구에서는 맞고 상자에서는 틀리는 것이 이 방법의 전제이자 한계다."""
    import win as W
    l = np.array([-0.5, 0.6, 0.62]); l /= np.linalg.norm(l)
    for nm, m, lim in (("구", trimesh.creation.icosphere(subdivisions=4, radius=0.45), 8.0),
                       ("상자", _tilted_box(), None)):
        Vw = W.normalize(np.asarray(m.vertices, np.float64))
        F = np.asarray(m.faces)
        col = np.full((len(F), 3), 200, np.uint8)
        import 시트 as SH
        rgb, ident = SH.draw(Vw, F, col, np.zeros(len(F), np.int32), "front", line=False)
        rgb, ident = rgb[::2, ::2], ident[::2, ::2]
        mask = ident >= 0
        N = normals_at(Vw, F, ident)
        # **카메라 축의 부호를 여기서 박는다** — 한 번 반대로 잡아 관측이 통째로 검게 나왔다
        assert N[mask][:, 1].mean() > 0.3, "보이는 면의 n_y 가 음수다 — 카메라 축 부호가 바뀌었다 (%.3f)" % N[mask][:, 1].mean()
        obs, _ = render(rgb, N, mask, l)
        assert obs[mask].mean() > 20, "관측이 거의 검다 — 광원이 카메라 반대쪽이다"
        reg = A1.albedo_regions(rgb, mask, 12, A1.AMIN)
        lh, s = estimate_light(obs, reg, mask)
        a = azi(lh, l)
        band, C = contour_band(mask)
        cn = np.stack([C[band][:, 0], np.zeros(band.sum()), C[band][:, 1]], 1)
        ce = float(np.median([ang(x, y) for x, y in zip(N[band][::5], cn[::5])]))
        print("  %s — 윤곽법선오차 %.1f° · 방위오차 %.1f° · 3D %.1f° (s=%.2f)" % (nm, ce, a, ang(lh, l), s))
        if lim is not None:
            assert ce < 12, "구의 윤곽 법선이 안 맞는다 (%.1f°) — 전제가 틀렸다" % ce
            assert a < lim, "구에서 광원 방위를 못 찾는다 (%.1f°)" % a
        else:
            assert ce > 15, "상자의 윤곽 법선이 맞아 버린다 (%.1f°) — 이 검사가 무엇도 못 가른다" % ce

    # 2 차 분할이 실제로 쪼개는가 — 기울인 상자는 앞에서 두 면이 보이고 밝기가 다르다
    seg = shade_split(obs, reg, mask)
    assert seg[mask].max() + 1 >= 2, "2차가 기울인 상자의 두 면을 안 쪼갠다"
    # 자유도 대조군은 조각 수를 맞춘다
    k = int(seg[mask].max() + 1)
    c2 = split_control(reg, mask, k)
    assert abs(int(c2[mask].max() + 1) - k) <= max(2, k // 3), "자유도 대조군 조각 수가 안 맞는다 (%d 대 %d)" % (c2[mask].max() + 1, k)
    print("  자가검사 통과 — 구에서 광원을 찾고 상자에서는 전제가 깨진다 · 2차 조각 %d" % k)


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        selfcheck()
    elif a == "판정":
        verdict()
    elif a == "그림":
        그림()
    else:
        run(int(a))


if __name__ == "__main__":
    main()
