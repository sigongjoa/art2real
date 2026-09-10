# -*- coding: utf-8 -*-
"""**표면으로 보는 눈.** 정답 메시를 복셀로 채우지 않고 표면에서 바로 잰다.

    python 표면.py            자가검사 (답을 아는 도형으로)

## 왜 필요한가 — 부피 IoU 하나로는 안 보이는 것

`정답.grid` 는 메시를 복셀로 굽고 **바깥에서 홍수채우기**로 속을 채운다. 벤치 12장이
전부 non-watertight 라, 격자를 96/128/192 로 바꾸면 **정답 부피가 중앙 22% 흔들린다**
(최대 36%). 케이스 하나짜리 판정은 0.005 수준에서 격자에 따라 뒤집힌다 (실측:
avatarsample_d 는 깊이 승 -> 균일 승 -> 깊이 승).

그리고 IoU 는 한 숫자라 **뚱뚱해서 지는 건지 덜 덮어서 지는 건지**를 안 가른다.
더 나쁜 건, 부피가 맞아가면서 형태가 망가지는 걸 못 잡는다 — 실측으로 깊이 깎기는
base_male 다리 단면을 정답 1.049 에서 **1.682** 로 각지게 만드는데 IoU 는 올라갔다.

## 재는 것 셋 (전부 정답을 안 채운다)

    챔퍼    양방향 최근접 거리 평균. 단위는 **키** (0.02 = 키의 2%, 사람이면 약 3.4 cm)
    F(τ)    τ 안에 든 점의 비율. 정밀도(우리->정답)와 재현율(정답->우리)의 조화평균
            **정밀도가 낮으면 없는 걸 만든 것 · 재현율이 낮으면 있는 걸 빠뜨린 것**
            (균일하게 부푼 것으로는 안 갈린다 — 오프셋이 대칭이라 둘이 같이 떨어진다)
    각짐    단면 둘레² / (4π·면적).  원 1.000 · 정사각형 1.273 (= 4/π)
            hull 은 단면이 항상 축정렬 직사각형이라 여기 박힌다. 사람 단면은 1.05~1.08

## 눈금을 왜 이렇게 잡았나

**점↔점이 아니라 점↔면이다.** 처음엔 두 표면에서 점을 뽑아 최근접 점끼리 쟀는데,
자가검사가 잡았다 — **같은 상자를 두 번 표본해도 챔퍼가 0.0088** 나온다. 표본 간격
(4만점·넓이 3.12 면 0.0044)이 그대로 바닥이 되고, base_male 의 실제 오차가 0.022 이라
바닥이 신호의 40% 였다. `_p2m` 이 점에서 **삼각형까지** 정확히 재서 바닥을 없앤다.

**N = 40,000 고정.** 점-면이라 바닥은 없지만 평균값은 여전히 표본에 따라 조금 움직인다.
비교하려면 고정하고 기록에 적어야 하는 값이다.

**TAU = 0.02** = 키의 2%. 사람 키 170 cm 면 3.4 cm — 굿즈에서 「닮았다」의 경계쯤이다.

`각짐` 은 표본이 없다 — 기하에서 바로 나오므로 이 문제가 아예 없다.
"""
import os
import sys

import numpy as np
import trimesh
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

TAU = 0.02                                       # 키의 2%. 자의 바닥(0.0091)의 두 배
N = 40000                                        # 표본 수. **고정값이다** — 위 참조
FLOOR = 0.0                                      # 점-면이라 바닥이 없다. 점↔점이면 0.0088 이었다
CIRCLE, SQUARE = 1.0, 4 / np.pi                  # 각짐의 두 기준점
CHUNK = 4096                                     # 점-면 거리를 한 번에 푸는 점 수. 메모리


def _p2m(P, mesh, k=24):
    """점 -> **면** 최근접 거리. 점↔점이 아니다.

    `trimesh.proximity.closest_point` 는 `rtree` 가 있어야 도는데 이 환경엔 없다.
    삼각형 무게중심 KD트리로 후보 k 개를 고르고 **정확한 점-삼각형 거리**를 잰다
    (Ericson, Real-Time Collision Detection 의 영역 판정).

    **왜 점↔점을 안 쓰나.** 같은 상자를 두 번 표본하면 챔퍼가 0.0088 나온다 — 표본
    간격(4만점·넓이 3.12 면 0.0044)이 그대로 바닥이 된다. base_male 의 실제 오차가
    0.022 이라 바닥이 신호의 40% 다. 자가검사가 이걸 잡았다."""
    T = mesh.triangles
    if not len(T):
        return np.full(len(P), np.inf)
    tree = cKDTree(T.mean(1))
    # **덩어리로 나눠 푼다.** (n, k, 3) 중간배열이 여럿이라 4만점을 한 번에 하면
    # 350 MB 쯤 든다 — 오늘 이것 때문에 백그라운드 작업이 두 번 죽었다
    if len(P) > CHUNK:
        return np.concatenate([_p2m(P[i:i + CHUNK], mesh, k) for i in range(0, len(P), CHUNK)])
    _, idx = tree.query(P, k=min(k, len(T)))
    idx = np.atleast_2d(idx.T).T if idx.ndim > 1 else idx[:, None]
    A, B, C = T[idx, 0], T[idx, 1], T[idx, 2]        # (n, k, 3)
    p = P[:, None, :]
    ab, ac, ap = B - A, C - A, p - A
    d1 = (ab * ap).sum(-1); d2 = (ac * ap).sum(-1)
    bp = p - B; d3 = (ab * bp).sum(-1); d4 = (ac * bp).sum(-1)
    cp = p - C; d5 = (ab * cp).sum(-1); d6 = (ac * cp).sum(-1)
    vc = d1 * d4 - d3 * d2
    vb = d5 * d2 - d1 * d6
    va = d3 * d6 - d5 * d4
    den = np.where(np.abs(va + vb + vc) < 1e-20, 1e-20, va + vb + vc)
    v, w = vb / den, vc / den
    q = A + v[..., None] * ab + w[..., None] * ac        # 면 안쪽일 때
    # 꼭짓점·모서리 영역
    q = np.where(((d1 <= 0) & (d2 <= 0))[..., None], A, q)
    q = np.where(((d3 >= 0) & (d4 <= d3))[..., None], B, q)
    q = np.where(((d6 >= 0) & (d5 <= d6))[..., None], C, q)
    def edge(cond, P0, D, t):
        t = np.clip(t, 0, 1)[..., None]
        return cond[..., None], P0 + t * D
    for cond, P0, D, t in (
            ((vc <= 0) & (d1 >= 0) & (d3 <= 0), A, ab, d1 / np.where(d1 - d3 == 0, 1e-20, d1 - d3)),
            ((vb <= 0) & (d2 >= 0) & (d6 <= 0), A, ac, d2 / np.where(d2 - d6 == 0, 1e-20, d2 - d6)),
            ((va <= 0) & (d4 - d3 >= 0) & (d5 - d6 >= 0), B, C - B,
             (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1e-20, (d4 - d3) + (d5 - d6)))):
        c2, qq = edge(cond, P0, D, t)
        q = np.where(c2, qq, q)
    return np.linalg.norm(q - p, axis=-1).min(1)


def chamfer(truth, mesh, n=N, tau=TAU, seed=0):
    """양방향 최근접 **점-면** 거리와 F(τ).

    da = 정답 -> 우리 (못 덮은 만큼 커진다 = 재현율)
    db = 우리 -> 정답 (튀어나온 만큼 커진다 = 정밀도)"""
    if not len(mesh.faces) or not len(truth.faces):
        return {"챔퍼": float("nan"), "F": 0.0, "정밀도": 0.0, "재현율": 0.0}
    da = _p2m(truth.sample(n), mesh)
    db = _p2m(mesh.sample(n), truth)
    rec, pre = float((da < tau).mean()), float((db < tau).mean())
    return {"챔퍼": float(da.mean() + db.mean()), "정밀도": pre, "재현율": rec,
            "F": 2 * pre * rec / max(pre + rec, 1e-9)}


def angularity(mesh, nz=12):
    """높이마다 단면의 **둘레²/(4π·면적)** 중앙값. 원 1.000 · 정사각형 1.273.

    `shapely` 가 이 환경에 없어서 trimesh 의 polygon 경로를 못 쓴다 — 끈에서 직접 잰다.
    절단면이 z=const 라 x·y 만 있으면 신발끈 공식으로 면적이 나온다.

    **닫힌 고리만 센다.** 옷자락 같은 열린 껍질은 단면이 열려서 면적이 뜻이 없다 —
    이게 non-watertight 정답에서도 이 지표가 성립하는 이유다."""
    lo, hi = float(mesh.bounds[0][2]), float(mesh.bounds[1][2])
    out = []
    for z in np.linspace(lo + 0.15 * (hi - lo), lo + 0.85 * (hi - lo), nz):
        try:
            sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        except Exception:
            continue
        if sec is None:
            continue
        V = np.asarray(sec.vertices)[:, :2]
        for e in sec.entities:
            idx = np.asarray(e.points)
            if len(idx) < 4 or idx[0] != idx[-1]:
                continue
            P = V[idx[:-1]]
            per = float(np.linalg.norm(np.diff(V[idx], axis=0), axis=1).sum())
            ar = 0.5 * abs(float(np.dot(P[:, 0], np.roll(P[:, 1], -1))
                                 - np.dot(P[:, 1], np.roll(P[:, 0], -1))))
            if ar > 1e-5 and per > 1e-4:
                out.append(per * per / (4 * np.pi * ar))
    return float(np.median(out)) if out else float("nan")


def score(truth, mesh):
    """한 판본의 표면 점수 전부."""
    r = chamfer(truth, mesh)
    r["각짐"] = angularity(mesh)
    return r


def selfcheck():
    """**답을 아는 도형으로 자를 검사한다.** `계단` 이 떨어졌던 그 문이다."""
    cyl = trimesh.creation.cylinder(radius=0.3, height=1.0, sections=256)
    box = trimesh.creation.box((0.6, 0.6, 1.0))
    ac, ab = angularity(cyl), angularity(box)
    assert abs(ac - CIRCLE) < 0.02, "원기둥 단면이 1.000 이 아니다 (%.3f)" % ac
    assert abs(ab - SQUARE) < 0.02, "정사각 단면이 %.3f 이 아니다 (%.3f)" % (SQUARE, ab)

    # 같은 물건이면 챔퍼 ~0 · F ~1. **점↔점이면 여기서 0.0088 이 나온다**
    same = chamfer(box, box.copy())
    assert same["챔퍼"] < 1e-4, "같은 물건인데 챔퍼가 %.6f" % same["챔퍼"]
    assert same["F"] > 0.999, "같은 물건인데 F 가 %.4f" % same["F"]

    # **거리가 실제 거리인가.** 반지름 0.02 만큼 부푼 구는 챔퍼가 0.04 (양방향) 여야 한다
    s1 = trimesh.creation.icosphere(subdivisions=4, radius=0.50)
    s2 = trimesh.creation.icosphere(subdivisions=4, radius=0.52)
    gap = chamfer(s1, s2)["챔퍼"]
    assert abs(gap - 0.04) < 0.004, "0.02 벌린 구인데 챔퍼가 %.4f (답 0.04)" % gap

    # **정밀도와 재현율이 갈리나.** 균일하게 부풀린 물건으로는 안 갈린다 (오프셋이
    # 대칭이라 둘이 같이 떨어진다) — 처음 쓴 시험이 그래서 틀렸다. 가르는 건
    # **부품을 빠뜨렸나 / 없는 걸 만들었나** 다.
    arm = trimesh.creation.box((0.8, 0.3, 0.3)); arm.apply_translation([0.6, 0, 0.2])
    blob = trimesh.creation.box((0.45, 0.45, 0.45)); blob.apply_translation([-0.8, 0, 0.7])
    whole = trimesh.util.concatenate([box, arm])
    miss = chamfer(whole, box)                               # 팔을 빠뜨림
    extra = chamfer(whole, trimesh.util.concatenate([box, arm, blob]))   # 없는 걸 만듦
    assert miss["재현율"] < miss["정밀도"] - 0.15,         "팔을 빠뜨렸는데 재현율이 안 떨어진다 (%.3f vs %.3f)" % (miss["재현율"], miss["정밀도"])
    assert extra["정밀도"] < extra["재현율"] - 0.15,         "없는 걸 만들었는데 정밀도가 안 떨어진다 (%.3f vs %.3f)" % (extra["정밀도"], extra["재현율"])

    # **각짐이 방향을 맞나.** 원기둥을 x 로 눌러도 원이 아니게 되면 커져야 한다
    sq = trimesh.creation.cylinder(radius=0.3, height=1.0, sections=4)   # 정사각(회전) 단면
    asq = angularity(sq)
    assert asq > ac + 0.2, "사각 단면인데 각짐이 안 커진다 (%.3f vs %.3f)" % (asq, ac)

    print("  표면 자가검사 통과")
    print("    각짐   원 %.3f (답 %.3f) · 정사각 %.3f (답 %.3f) · 4각기둥 %.3f"
          % (ac, CIRCLE, ab, SQUARE, asq))
    print("    챔퍼   같은 물건 %.6f · F %.4f · 0.02 벌린 구 %.4f (답 0.0400)"
          % (same["챔퍼"], same["F"], gap))
    print("    갈림   없는 걸 만듦: 정밀도 %.3f < 재현율 %.3f · 빠뜨림: 재현율 %.3f < 정밀도 %.3f"
          % (extra["정밀도"], extra["재현율"], miss["재현율"], miss["정밀도"]))
    print("    눈금   TAU %.3f (키의 2%%) · 표본 %s 고정 · 점-면이라 바닥 없음" % (TAU, format(N, ",")))


if __name__ == "__main__":
    selfcheck()
