# -*- coding: utf-8 -*-
"""**마칭큐브에 0/1 복셀 말고 연속 장을 준다** (2026-09-21).

    python 연속hull.py 검사
    python 연속hull.py 짓기     -> out/연속hull_오메가몬.glb · out/기록/연속hull_<때>.json
    python 연속hull.py 그림     -> out/연속hull_오메가몬.png

사용자(09-21): 「복셀 말고 마칭큐브로 해 볼래? 그러면 매끄러울 건데?」

**지금도 마칭큐브다** — 다만 `hull.mesh_from` 은 **0/1 복셀**에 수준 0.5 로 건다. 이진 장에서는
꼭짓점이 늘 칸 한가운데에 놓여 계단이 난다. 마칭큐브가 매끄러워지는 것은 **연속 장**을 받을 때다
(모서리를 따라 선형 보간). 09-11 의 `sdf_of(vox)` 는 이진 복셀의 거리 변환이라 경계에서 여전히 ±1 칸으로
양자화돼 있었다.

여기서는 복셀 이진화를 **아예 안 거친다**:

    판마다  1024² 마스크의 2D 부호거리장 (안 +, 밖 −, 세계 단위)      ← 격자(256)보다 4 배 촘촘
    3D 장   f(x, y, z) = min( 앞(x,z), 옆(y,z), 뒤(±x,z) )            ← 교집합 = 최솟값
    메시    `hull.mesh_from_field(f)` — 수준 0 의 마칭큐브 (같은 256 격자 · 같은 좌표 규약)

**문턱을 돌리기 전에 적는다.** 견줄 상대는 같은 마스크의 **복셀 이진 hull**(지금 방식)이다.

    Q1  세 판 못덮음이 복셀 이진 hull 보다 **0.5%p 넘게 나쁘지 않다**
    Q2  **계단 몫이 절반 아래로** 내려간다 (`면.dihedral` 의 「계단」 · 같은 자)
    Q3  닫힌 메시

**이 바퀴가 못 고치는 것을 먼저 적는다** — 앞면이 「옆 윤곽을 가로로 민 납작한 판」인 것은
hull 의 구조라 마칭큐브를 바꿔도 남는다(09-21 `정확hull`). 여기서 보는 것은 **계단**이다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260920")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260919")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260916")
import 세우기 as SE
import 기둥hull as EH
import 폴리싱 as PL
H, W, LR = SE.H, SE.W, SE.LR
HERE, OUT = SE.HERE, SE.OUT
문_여유 = 0.005


def 거리장2d(mask):
    """1024² 마스크 -> 부호거리장 (안 +, 세계 단위). 경계가 화소 **사이**에 놓이게 반 화소를 맞춘다."""
    from scipy import ndimage
    안 = ndimage.distance_transform_edt(mask) - 0.5
    밖 = ndimage.distance_transform_edt(~mask) - 0.5
    return np.where(mask, 안, -밖).astype(np.float32) * ((W.U1 - W.U0) / W.RES)


def 표본(S2, u, z):
    """2D 장을 세계 좌표 (u, z) 격자에서 쌍선형으로 읽는다 -> (len(u), len(z))."""
    from scipy import ndimage
    col = (u - W.U0) / (W.U1 - W.U0) * W.RES - 0.5
    row = (W.Z1 - z) / (W.Z1 - W.Z0) * W.RES - 0.5
    C, Rr = np.meshgrid(col, row, indexing="ij")
    return ndimage.map_coordinates(S2, [Rr, C], order=1, mode="nearest").astype(np.float32)


def 연속장(masks, bs, N=None):
    N = N or H.N
    u = W.U0 + (np.arange(N) + 0.5) / N * (W.U1 - W.U0)
    z = W.Z0 + (np.arange(N) + 0.5) / N * (W.Z1 - W.Z0)
    Sf = 표본(거리장2d(masks["front"]), u, z)               # (x, z)
    Ss = 표본(거리장2d(masks["side"]), u, z)                # (y, z)
    Sb = 표본(거리장2d(masks["back"]), bs * u, z)           # (x, z) — 뒤 판의 가로는 bs·x
    f = np.minimum(np.minimum(Sf[:, None, :], Ss[None, :, :]), Sb[:, None, :])
    return f, (u, u, z)


def 짓기(case="오메가몬"):
    t0 = time.time()
    _, masks, p, bs, raw = SE.껍질(case)
    keep, axes = H.carve(masks, back_sign=bs)
    Vv, F = H.mesh_from(keep, axes)
    복셀 = trimesh.Trimesh(Vv, F, process=True)
    t1 = time.time()
    f, ax = 연속장(masks, bs)
    cell = (W.U1 - W.U0) / H.N
    V2, F2 = H.mesh_from_field(f / cell, ax)                # 칸 단위로 (hull.py 의 장과 같은 눈금)
    # **process=False.** 마칭큐브 원출력은 닫혀 있는데, trimesh 가 가까운 정점을 합치면 넓이 0 인 면이
    # 2 만 개 생기고 메시가 열린다(닫힘 False · 조각 15,023 으로 나왔다). 장의 값이 격자점에서 0 에
    # 아주 가까운 자리가 많아서다. 정점을 안 합친다.
    연 = trimesh.Trimesh(V2, F2, process=False)
    초 = round(time.time() - t1, 1)
    r = {"판": "연속hull v1 · 2D 거리장 셋의 최솟값 -> 마칭큐브 (2026-09-21)",
         "때": time.strftime("%Y%m%d_%H%M"), "case": case, "격자": H.N, "장+메시 초": 초,
         "복셀 이진 + 마칭큐브": EH.재다(복셀, masks, bs), "연속 장 + 마칭큐브": EH.재다(연, masks, bs)}
    p정 = os.path.join(HERE, "out", "정확hull_%s.glb" % case)
    if os.path.exists(p정):
        r["정확 hull (메시 교집합)"] = EH.재다(trimesh.load(p정, force="mesh"), masks, bs)
    a, b = r["연속 장 + 마칭큐브"], r["복셀 이진 + 마칭큐브"]
    r["Q1"] = {"문턱": "못덮음 증가 <= %g" % 문_여유,
               "차": {v: round(a["못덮음"][v] - b["못덮음"][v], 5) for v in W.VIEWS},
               "통과": bool(all(a["못덮음"][v] - b["못덮음"][v] <= 문_여유 for v in W.VIEWS))}
    r["Q2"] = {"문턱": "계단 몫이 절반 아래", "연속": a["계단"], "복셀": b["계단"],
               "통과": bool(a["계단"] < 0.5 * b["계단"])}
    r["Q3"] = {"문턱": "닫힌 메시", "통과": bool(a["닫힘"])}
    연.export(os.path.join(HERE, "out", "연속hull_%s.glb" % case))
    r["초"] = round(time.time() - t0, 1)
    q = os.path.join(OUT, "연속hull_%s.json" % r["때"])
    json.dump(r, open(q, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %-22s %22s %8s %7s %7s %8s %5s %4s" % ("판본", "못덮음 앞·옆·뒤", "거칠기", "평평", "계단", "면", "닫힘", "조각"))
    for n in ("복셀 이진 + 마칭큐브", "연속 장 + 마칭큐브", "정확 hull (메시 교집합)"):
        if n not in r:
            continue
        x = r[n]
        print("  %-22s %22s %8.4f %7.3f %7.3f %8d %5s %4d"
              % (n, " ".join("%.4f" % x["못덮음"][v] for v in W.VIEWS), x["거칠기"], x["평평"],
                 x["계단"], x["면"], x["닫힘"], x["조각"]))
    print("  장+메시 %.1f초 · Q1 %s · Q2 %s · Q3 %s" % (초, *("통과" if r[k]["통과"] else "짐" for k in ("Q1", "Q2", "Q3"))))
    print("  ->", q)
    return r


def 그림(case="오메가몬"):
    from PIL import Image
    import 앨리어싱 as AL
    L = lambda n: trimesh.load(os.path.join(HERE, "out", n), force="mesh")
    가슴 = ((-0.19, 0.56), 0.38)
    R = []
    for 이름, f in (("복셀 이진 + 마칭큐브 (지금)", "정확hull_%s_복셀.glb" % case),
                  ("연속 장 + 마칭큐브", "연속hull_%s.glb" % case),
                  ("정확 hull (메시 교집합)", "정확hull_%s.glb" % case)):
        if not os.path.exists(os.path.join(HERE, "out", f)):
            continue
        a = L(f)
        R.append((이름, [PL.shaded(a, 0, AL.frame_of(a, 0), S=700), PL.shaded(a, 45, AL.frame_of(a, 45), S=700),
                        PL.shaded(a, 0, 가슴, S=700), PL.shaded(a, 45, 가슴, S=700)]))
    LR.DC.grid(R, ("앞", "45°", "가슴 확대 (앞)", "가슴 확대 (45°)"),
               "마칭큐브에 무엇을 주나 — 0/1 복셀 대 연속 장 (같은 마스크 · 같은 256 격자)",
               "셋 다 이진 hull(깊이 깎기 없음)이다. 보는 것은 계단이다 — 앞면이 납작한 것은 hull 의 구조라 셋 다 같다",
               os.path.join(HERE, "out", "연속hull_%s.png" % case), S=400)


def selfcheck():
    m = np.zeros((W.RES, W.RES), bool)
    m[300:700, 400:600] = True
    S2 = 거리장2d(m)
    px = (W.U1 - W.U0) / W.RES
    assert S2[500, 500] > 0 and S2[10, 10] < 0
    assert abs(S2[500, 400] - 0.5 * px) < 1e-6 and abs(S2[500, 399] + 0.5 * px) < 1e-6, "경계가 화소 사이에 안 놓였다"
    f, ax = 연속장({"front": m, "side": m, "back": m}, +1, N=64)
    assert f.shape == (64, 64, 64) and f.max() > 0 > f.min()
    V, F = H.mesh_from_field(f / ((W.U1 - W.U0) / 64), ax)
    t = trimesh.Trimesh(V, F, process=True)
    기대 = (200 * px) ** 2 * (400 * px)
    assert t.is_watertight and abs(abs(t.volume) - 기대) / 기대 < 0.03, (t.volume, 기대)
    print("  자가검사 통과 — 상자 부피 %.5f (기대 %.5f)" % (abs(t.volume), 기대))


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "검사"
    {"검사": selfcheck, "짓기": 짓기, "그림": 그림}[a]()
