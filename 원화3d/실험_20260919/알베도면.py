# -*- coding: utf-8 -*-
"""**알베도 한 컷에서 면 가르기 — 1차(컨투어)만** (2026-09-19).

    python 알베도면.py 검사     자가검사 (몫의 거동 · 배관)
    python 알베도면.py [n]      아직 안 한 장 n 개 -> out/기록/알베도면_진행.jsonl
    python 알베도면.py 판정     -> out/기록/알베도면_<때>.json
    python 알베도면.py 그림     -> out/알베도면.png

사용자 (09-19): 「알베도 기반의 방법 · 그림자를 추정하면 면을 추정할 수 있을 거거든?」
→ 「GT 에서 찍은 **한 컷**에서 보라」 → 「알베도랑 **컨투어로 외곽선** 따봐라, 외곽선 안의
면적에서의 알베도를 기반으로」.

3D 로 풀지 않는다. 원화와 같은 정사영 카메라로 **알베도 한 컷**을 찍고 (`시트.draw`, 선 없이),
그 컷의 **색만** 보고 영역을 나눈다. 원본 메시는 **정답지로만** 쓴다.

판정은 `claudedocs/plan_알베도면_20260919.md` 「5 Q」 그대로다 — 돌리기 전에 적었다.
**2 차(영역 안에서 음영으로 쪼개기)는 이 스크립트에 없다.** 빛을 어디 둘지는 사람이 정한다.
"""
import json
import os
import sys
import time

import cv2
import numpy as np
import trimesh
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260913"))
os.chdir(HERE)
import win as W
import 시트 as SH

PROG = os.path.join(HERE, "out", "기록", "알베도면_진행.jsonl")
TAG = "알베도면 v2 · 1차 컨투어만 · 궤짝·드릴·모자 · front 한 컷 · 512² (2026-09-19)"
CASES = ("cloak_Chest_Closed_AngpV0HxD8", "mech_Drill_8uBbH7Dvmb", "cape_Hat_Stylised_lNN3PlrjSa")
NICK = {CASES[0]: "닫힌 궤짝", CASES[1]: "드릴", CASES[2]: "모자"}

R = 512                       # 채점 해상도 (렌더는 1024, 2 배 줄인다)
QS = (6, 12, 24, 0)           # 색 양자화 단계 (채널마다). 0 = 정확색 (알베도를 정답으로 준 천장)
AMIN = 30                     # 최소 영역 화소 (512² 기준). 민감도는 AMIN2 로 같이 잰다
AMIN2 = 200
DIHED = (10.0, 15.0, 25.0)    # 정답 평면 그룹의 이면각 문턱. 15 가 주, 나머지는 민감도


# ------------------------------------------------------------------ 한 컷

def cut(case):
    """원본 모델 -> (알베도 RGB, 삼각형 번호, 월드 정점, 면). **`시트.py` 규약 그대로** —
    축 xyz · 깊이 뒤집기 · `normalize`. 선은 안 긋는다 (선은 알베도가 아니다)."""
    sc = trimesh.load(os.path.join(HERE, "out", "모델", "%s.glb" % case))
    V, F, col, mat = SH.faces_with_color(sc)
    Vw = W.to_world(V, "xyz")
    Vw[:, 1] *= -1
    Vw = W.normalize(Vw)
    rgb, ident = SH.draw(Vw, F, col, mat, "front", line=False)
    return rgb[::2, ::2], ident[::2, ::2], Vw, F


# ------------------------------------------------------------------ 정답지

def plane_faces(Vw, F, deg):
    """삼각형 -> 평면 그룹 번호. 이면각이 `deg` 미만인 이웃끼리 잇는다."""
    m = trimesh.Trimesh(Vw, F, process=False)
    m.merge_vertices()
    p, a = m.face_adjacency, m.face_adjacency_angles
    k = p[a < np.radians(deg)]
    g = coo_matrix((np.ones(len(k)), (k[:, 0], k[:, 1])), shape=(len(F), len(F)))
    return connected_components(g, directed=False)[1]


def cc(lab, mask, amin):
    """라벨 그림 -> **연결성분으로 다시 자른 라벨**. 배경 -1. `amin` 미만 조각은 제일 가까운
    남은 조각에 붙인다 (버리면 실루엣에 구멍이 나 판본끼리 분모가 달라진다).

    가림으로 한 평면이 화면에서 두 덩이로 보이면 2D 에서는 두 조각이다 — 정답도 판본도 같은
    함수를 탄다."""
    out = np.full(lab.shape, -1, np.int32)
    nxt = 0
    for v in np.unique(lab[mask]):
        c, n = ndimage.label((lab == v) & mask)
        out[c > 0] = c[c > 0] - 1 + nxt
        nxt += n
    big = np.bincount(out[mask]) >= amin
    keep = mask & big[out]
    if not keep.any():
        return out                                   # 다 작으면 그대로 둔다 (배관이 잡는다)
    _, (iy, ix) = ndimage.distance_transform_edt(~keep, return_indices=True)
    out = np.where(mask, np.where(keep, out, out[iy, ix]), -1)
    u, inv = np.unique(out[mask], return_inverse=True)
    res = np.full(lab.shape, -1, np.int32)
    res[mask] = inv
    return res


# ------------------------------------------------------------------ 1 차 — 알베도 컨투어

def albedo_regions(rgb, mask, q, amin):
    """**컨투어 안의 알베도 영역.** 색을 채널마다 q 단계로 양자화하고 4-연결 성분을 딴다.
    q=0 이면 양자화 없이 **정확히 같은 색** — 알베도를 정답으로 줬을 때의 천장이다."""
    a = rgb.astype(np.int32)
    if q:
        a = np.minimum(a * q // 256, q - 1)
    key = (a[:, :, 0] * 1024 + a[:, :, 1]) * 1024 + a[:, :, 2]
    return cc(key, mask, amin)


def voronoi(mask, k, seed=0):
    """**정보 0 대조군.** 색을 안 보고 실루엣 안에 씨앗 k 개를 뿌려 가장 가까운 씨앗에 붙인다.
    조각 수를 짝지은 판본과 맞춘다 — 순도는 조각을 잘게 낼수록 오르므로 수를 안 맞추면 못 가른다."""
    from scipy.spatial import cKDTree
    idx = np.argwhere(mask)
    rng = np.random.default_rng(seed)
    s = idx[rng.choice(len(idx), min(k, len(idx)), replace=False)]
    out = np.full(mask.shape, -1, np.int32)
    out[mask] = cKDTree(s).query(idx)[1]
    return out


# ------------------------------------------------------------------ 채점

def marks(gt, seg, mask):
    """정답 조각 g · 판본 조각 s.

        순도        Σ_s (|s|/N)·max_g |s∩g|/|s|   영역 하나가 평면 하나만 담나.
                    **화소 하나씩 쪼개면 1.0 이다 — 단독으로는 판정에 못 쓴다**
        덮음        Σ_g (|g|/N)·max_s |g∩s|/|g|   평면이 한 영역 안에 통째로 드나.
                    **전부 한 덩이로 두면 1.0 이다 — 역시 단독으로는 못 쓴다**
        잘림        1 − 덮음. 0 이면 알베도 경계가 평면을 안 자른다 = 1 차를 확정으로 쓸 수 있다
        매칭IoU     Σ_g (|g|/N)·max_s IoU(g,s)     **양쪽을 다 벌한다 — 판정은 이걸로 한다**
    """
    a, b = gt[mask], seg[mask]
    n = len(a)
    t = coo_matrix((np.ones(n), (a, b)), shape=(a.max() + 1, b.max() + 1)).toarray()
    ga, sa = t.sum(1), t.sum(0)
    pur = float((t.max(0) / n).sum())
    cov = float((t.max(1) / n).sum())
    iou = t / (ga[:, None] + sa[None, :] - t)
    mio = float(((t.sum(1) / n) * iou.max(1)).sum())
    return {"순도": round(pur, 4), "덮음": round(cov, 4), "잘림": round(1 - cov, 4),
            "매칭IoU": round(mio, 4), "조각": int((sa > 0).sum()), "정답조각": int((ga > 0).sum())}


# ------------------------------------------------------------------ 한 장

def one(case):
    t0 = time.time()
    rgb, ident, Vw, F = cut(case)
    mask = ident >= 0
    out = {"case": case, "판": TAG, "전경": round(float(mask.mean()), 4)}

    # 배관 — 내가 찍은 컷이 그 케이스의 truth.glb 와 같은 자리인가
    tp = os.path.join(HERE, "out", "시트", case, "truth.glb")
    t = trimesh.load(tp, force="mesh")
    sil = W.silhouette(np.asarray(t.vertices), np.asarray(t.faces), "front")[::2, ::2]
    out["배관_실루엣IoU"] = round(float((sil & mask).sum() / max((sil | mask).sum(), 1)), 4)

    main12 = albedo_regions(rgb, mask, 12, AMIN)
    for deg in DIHED:
        gt = cc(plane_faces(Vw, F, deg)[np.clip(ident, 0, None)], mask, AMIN)
        # 정답 정의(이면각)에 판정이 얼마나 달렸나 — 주 판본 q12·a30 을 그 정답으로 다시 채점
        out["정답@%g" % deg] = marks(gt, main12, mask)
        if deg != 15.0:
            continue
        out["배관_GT자신"] = marks(gt, gt, mask)
        for amin in (AMIN, AMIN2):
            for q in QS:
                seg = albedo_regions(rgb, mask, q, amin)
                nm = "q%s·a%d" % (q or "정확", amin)
                out[nm] = marks(gt, seg, mask)
                out["C@" + nm] = marks(gt, voronoi(mask, out[nm]["조각"]), mask)
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
    for c in [x for x in CASES if x not in done][:n]:
        r = one(c)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        m = r["q12·a30"]
        print("  %-14s 실루엣IoU %.3f · 정답평면 %3d · q12 조각 %3d · 순도 %.3f · 잘림 %.3f · 매칭IoU %.3f (%.0f초)"
              % (NICK[c], r["배관_실루엣IoU"], m["정답조각"], m["조각"], m["순도"], m["잘림"],
                 m["매칭IoU"], r["초"]), flush=True)


# ------------------------------------------------------------------ 판정

MAIN = "q12·a30"


def verdict():
    rs = [rows()[c] for c in CASES if c in rows()]
    assert len(rs) == 3, "%d 장만 돌았다" % len(rs)
    bad = [r["case"] for r in rs if r["배관_실루엣IoU"] < 0.98 or r["배관_GT자신"]["매칭IoU"] < 0.999]
    v = {"판": TAG, "n": len(rs), "배관불량": bad, "주판본": MAIN, "장별": {}}
    for r in rs:
        v["장별"][NICK[r["case"]]] = {k: r[k] for k in r if k not in ("case", "판")}

    # Q1 1 차를 확정으로 쓸 수 있나 — 알베도 경계가 평면을 자르지 않는가
    q1 = {NICK[r["case"]]: {"잘림": r[MAIN]["잘림"], "조각": r[MAIN]["조각"],
                            "정답조각": r[MAIN]["정답조각"],
                            "통과": bool(r[MAIN]["잘림"] <= 0.10 and r[MAIN]["조각"] <= r[MAIN]["정답조각"])}
          for r in rs}
    # Q2 1 차가 정보를 갖나 — 같은 조각 수 대조군 대비
    q2 = {NICK[r["case"]]: {"매칭IoU": r[MAIN]["매칭IoU"], "C": r["C@" + MAIN]["매칭IoU"],
                            "차": round(r[MAIN]["매칭IoU"] - r["C@" + MAIN]["매칭IoU"], 4),
                            "통과": bool(r[MAIN]["매칭IoU"] - r["C@" + MAIN]["매칭IoU"] >= 0.10)}
          for r in rs}
    # Q3 양자화 문턱에 판정이 뒤집히나
    q3 = {NICK[r["case"]]: {("q%s·a%d" % (q or "정확", a)): {"잘림": r["q%s·a%d" % (q or "정확", a)]["잘림"],
                                                            "조각": r["q%s·a%d" % (q or "정확", a)]["조각"],
                                                            "매칭IoU": r["q%s·a%d" % (q or "정확", a)]["매칭IoU"]}
                            for q in QS for a in (AMIN, AMIN2)} for r in rs}
    # Q4 음영이 구워진 장(드릴)이 안 구워진 둘보다 q정확에서 +0.15 이상인가
    ex = {NICK[r["case"]]: r["q정확·a30"]["매칭IoU"] for r in rs}
    q4 = {"q정확 매칭IoU": ex,
          "통과": bool(all(ex["드릴"] - ex[k] >= 0.15 for k in ex if k != "드릴"))}
    # 정답 정의(이면각)에 판정이 달렸나
    q5 = {NICK[r["case"]]: {k: r[k] for k in r if k.startswith("정답@")} for r in rs}
    v["Q1 1차를 확정으로 (잘림 ≤ 0.10 · 조각 ≤ 정답조각)"] = q1
    v["Q2 대조군 대비 (매칭IoU − C ≥ 0.10)"] = q2
    v["Q3 문턱 민감도"] = q3
    v["Q4 구워진 음영이 갈랐나 (드릴 − 나머지 ≥ 0.15)"] = q4
    v["정답 이면각 민감도 (주 판본 q12·a30 을 다시 채점)"] = q5
    v["판정"] = {"Q1": all(x["통과"] for x in q1.values()),
                 "Q2": all(x["통과"] for x in q2.values()), "Q4": q4["통과"]}
    p = os.path.join(HERE, "out", "기록", "알베도면_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("\n  %s · %s" % (MAIN, "배관 불량 %s" % bad if bad else "배관 통과"))
    print("  %-12s %8s %8s %7s %7s %7s %9s %7s" % ("장", "정답평면", "알베도영역", "순도", "덮음", "잘림", "매칭IoU", "대조C"))
    for r in rs:
        m, c = r[MAIN], r["C@" + MAIN]
        print("  %-12s %8d %10d %7.3f %7.3f %7.3f %9.3f %7.3f"
              % (NICK[r["case"]], m["정답조각"], m["조각"], m["순도"], m["덮음"], m["잘림"],
                 m["매칭IoU"], c["매칭IoU"]))
    print("\n  Q1 %s · Q2 %s" % (v["판정"]["Q1"], v["판정"]["Q2"]))
    print("  ->", p)
    return v


# ------------------------------------------------------------------ 그림

def 그림():
    from 깊이색 import grid
    rws = []
    for case in CASES:
        rgb, ident, Vw, F = cut(case)
        mask = ident >= 0
        gt = cc(plane_faces(Vw, F, 15.0)[np.clip(ident, 0, None)], mask, AMIN)
        seg = albedo_regions(rgb, mask, 12, AMIN)
        ex = albedo_regions(rgb, mask, 0, AMIN)
        con = np.zeros(mask.shape + (3,), np.uint8) + 255
        e = cv2.Canny(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), 40, 120) > 0
        con[e] = (20, 20, 20)
        rws.append((NICK[case], [rgb, con, tint(ex, mask), tint(seg, mask), tint(gt, mask)]))
    grid(rws, ["알베도 한 컷", "Canny 외곽선", "1차 · 정확색", "1차 · q12", "정답 평면 그룹"],
         "알베도 한 컷에서 면 가르기 — 1차(컨투어)만 · front · 3D 안 씀 (2026-09-19)",
         "색은 조각 번호를 무작위로 칠한 것 (같은 색 = 같은 조각). 정답 평면 = 이면각 15° 로 이은 삼각형 묶음 · 화면 연결성분",
         os.path.join(HERE, "out", "알베도면.png"))


def tint(lab, mask, seed=1):
    rng = np.random.default_rng(seed)
    c = rng.integers(40, 235, (max(lab.max() + 1, 1), 3)).astype(np.uint8)
    return np.where(mask[:, :, None], c[np.clip(lab, 0, None)], 255).astype(np.uint8)


# ------------------------------------------------------------------ 자가검사

def selfcheck():
    """**문턱이 낼 수 있는 값을 먼저 본다** (계획 3 절). 정답 = 같은 넓이 세 줄무늬."""
    m = np.ones((90, 90), bool)
    gt = np.repeat(np.arange(3), 30)[:, None] * np.ones((1, 90), np.int32)

    same = marks(gt, gt, m)
    assert same["매칭IoU"] == 1.0 and same["순도"] == 1.0 and same["잘림"] == 0.0, same
    # 줄마다 둘로 쪼갠다 — 순도는 그대로 1, 매칭IoU 는 반으로 떨어진다
    half = gt * 2 + (np.arange(90)[None, :] >= 45)
    h = marks(gt, half, m)
    assert h["순도"] == 1.0 and abs(h["매칭IoU"] - 0.5) < 0.02 and h["잘림"] > 0.45, h
    # 전부 한 덩이 — 잘림은 0 인데 매칭IoU 는 1/3
    o = marks(gt, np.zeros_like(gt), m)
    assert o["잘림"] == 0.0 and abs(o["매칭IoU"] - 1 / 3) < 0.02, o
    # **화소 하나씩** — 순도 1.0 · 잘림 ~1. 순도만 보면 제일 좋은 답이 된다
    px = np.arange(90 * 90).reshape(90, 90)
    p = marks(gt, px, m)
    assert p["순도"] == 1.0 and p["매칭IoU"] < 0.01, p
    # 대조군 바닥이 0 이 아니다 — 세 조각 보로노이
    c = marks(gt, voronoi(m, 3), m)
    assert 0.15 < c["매칭IoU"] < 0.75, "대조군 바닥 %s — 0 이나 1 에 붙으면 문턱을 다시 센다" % c

    # cc — 떨어진 두 덩이는 같은 라벨이어도 두 조각, 작은 조각은 이웃에 붙는다
    l = np.zeros((40, 40), np.int32); l[:, 20:] = 0; l[10:12, 10:12] = 1
    mm = np.ones((40, 40), bool); mm[:, 18:22] = False
    r = cc(l, mm, amin=5)
    assert r[mm].max() + 1 == 2, "떨어진 두 덩이가 안 갈렸다 (%d)" % (r[mm].max() + 1)
    assert (r[10:12, 10:12] == r[0, 0]).all(), "작은 조각이 이웃에 안 붙었다"

    print("  자가검사 통과 — 같음 %.3f · 쪼갬 %.3f(순도 %.2f) · 뭉침 %.3f(잘림 %.2f) · 화소 %.3f(순도 %.2f) · 대조군 %.3f"
          % (same["매칭IoU"], h["매칭IoU"], h["순도"], o["매칭IoU"], o["잘림"], p["매칭IoU"], p["순도"], c["매칭IoU"]))


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        selfcheck()
    elif a == "판정":
        verdict()
    elif a == "그림":
        그림()
    else:
        selfcheck()
        run(int(a))


if __name__ == "__main__":
    main()
