# -*- coding: utf-8 -*-
"""**복셀을 안 거치는 hull** — 세 실루엣 기둥의 정확한 메시 교집합 (2026-09-21).

    python 기둥hull.py 검사
    python 기둥hull.py 짓기     -> out/정확hull_오메가몬.glb · out/기록/정확hull_<때>.json
    python 기둥hull.py 그림     -> out/정확hull_오메가몬.png

사용자(09-21): 「hull 이 문제인데? 면이 매끄럽지가 않아」.

까닭은 알려져 있다 — hull 을 **256 칸 복셀로 깎고 마칭큐브로 뜬다**. 계단 한 단 = 칸 = 키의 1/213.
09-16 에 후처리 넷(부화소 · ITK국소 · Z2 …)을 걸었고 **넷 다 눈으로는 못 고쳤다**(「계단은 격자 탓」).
그때 적어 두고 안 한 길이 「정확 hull 메시 불리언」이다 — 09-20 에 `manifold3d` 가 깔려 이제 된다.

    판마다  마스크 윤곽(구멍 포함) -> 다각형 -> 시선 방향으로 밀어낸 **기둥**
    hull  = 앞 기둥 ∩ 옆 기둥 ∩ 뒤 기둥        (복셀 없음 · 마칭큐브 없음)

표면은 **윤곽선을 곧게 민 면**이라 계단이 구조적으로 없다. 대신 이것은 **이진 hull** 이다 —
깊이 깎기(타원 단면)가 안 들어가 단면이 네모나다. 그건 이 바퀴가 안 푼다. 적어 둔다.

**문턱을 돌리기 전에 적는다.**

    Q1  세 판 **못덮음이 복셀 이진 hull 보다 0.5%p 넘게 나쁘지 않다** (상한이라는 약속)
    Q2  **거칠기가 복셀 hull 보다 낮다** (`면.roughness` · 같은 자)
    Q3  닫힌 메시 · 조각 1 (09-20 게이트 G1)
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
import 폴리싱 as PL
import manifold3d as m3
H, W, LR = SE.H, SE.W, SE.LR
HERE, OUT = SE.HERE, SE.OUT
윤곽오차 = 0.6                 # 화소. 다각형 단순화 (approxPolyDP)
문_여유 = 0.005


def 다각형(mask):
    """bool 마스크 -> [(N,2) 세계좌표 (u, z)] · 바깥 윤곽과 구멍 다. **한 화소 부풀려** 딴다 —
    윤곽은 화소 중심을 지나 반 화소 작게 나오는데, hull 은 상한이라 작게 뜨면 약속을 어긴다."""
    import cv2
    from scipy import ndimage
    m = ndimage.binary_dilation(mask).astype(np.uint8)
    cs, _ = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    out = []
    for c in cs:
        c = cv2.approxPolyDP(c, 윤곽오차, True)[:, 0, :].astype(np.float64)
        if len(c) < 3:
            continue
        u = W.U0 + (c[:, 0] + 0.5) / W.RES * (W.U1 - W.U0)
        z = W.Z1 - (c[:, 1] + 0.5) / W.RES * (W.Z1 - W.Z0)
        out.append(np.stack([u, z], 1))
    return out


def 기둥(mask, view, bs):
    """실루엣을 시선 방향으로 민 기둥. 창 깊이 [U0, U1] 을 다 덮는다."""
    polys = 다각형(mask)
    cs = m3.CrossSection([p.tolist() for p in polys], m3.FillRule.EvenOdd)
    L = W.U1 - W.U0
    s = cs.extrude(L)                                      # (u, z, 0..L)
    s = s.rotate([90, 0, 0]).translate([0, L / 2, 0])      # (u, y∈[−L/2, L/2], z)
    if view == "side":
        s = s.rotate([0, 0, 90])                           # u 가 세계 y 가 된다
    elif view == "back" and bs < 0:
        s = s.scale([-1, 1, 1])
    return s, sum(len(p) for p in polys), len(polys)


def tm(man):
    me = man.to_mesh()
    return trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3], np.asarray(me.tri_verts), process=False)


def 재다(m, masks, bs):
    from 면 import dihedral, roughness
    d = dihedral(m)
    return {"못덮음": SE.못덮음(m, masks, bs), "거칠기": roughness(m)["거칠기"],
            "평평": d["평평"], "계단": d["계단"], "면": int(len(m.faces)),
            "닫힘": bool(m.is_watertight),
            "조각": int(len(trimesh.graph.connected_components(m.face_adjacency, nodes=np.arange(len(m.faces))))),
            "부피": round(float(m.volume), 5)}


def 짓기(case="오메가몬"):
    t0 = time.time()
    _, masks, p, bs, raw = SE.껍질(case)                    # 마스크 · 정렬은 `hull.py` 배관 그대로
    keep, axes = H.carve(masks, back_sign=bs)               # 견줄 상대 = **복셀 이진 hull**
    Vv, F = H.mesh_from(keep, axes)
    복셀 = trimesh.Trimesh(Vv, F, process=True)
    기본, _, _, _, _ = SE.껍질(case)                          # 그리고 지금 기본(타원 깎기)
    t1 = time.time()
    hull, 점수 = None, {}
    for v in W.VIEWS:
        g, n, k = 기둥(masks[v], v, bs)
        점수[v] = {"꼭짓점": n, "윤곽": k}
        hull = g if hull is None else hull ^ g
    정 = tm(hull)
    초 = round(time.time() - t1, 1)
    r = {"판": "정확hull v1 · 세 기둥의 manifold 교집합 (2026-09-21)", "때": time.strftime("%Y%m%d_%H%M"),
         "case": case, "윤곽": 점수, "교집합초": 초,
         "복셀 이진 hull": 재다(복셀, masks, bs), "기본(타원 깎기)": 재다(기본, masks, bs),
         "정확 hull": 재다(정, masks, bs)}
    a, b = r["정확 hull"], r["복셀 이진 hull"]
    r["Q1"] = {"문턱": "못덮음이 복셀 이진 hull 보다 %g 넘게 나쁘지 않다" % 문_여유,
               "차": {v: round(a["못덮음"][v] - b["못덮음"][v], 5) for v in W.VIEWS},
               "통과": bool(all(a["못덮음"][v] - b["못덮음"][v] <= 문_여유 for v in W.VIEWS))}
    r["Q2"] = {"문턱": "거칠기가 복셀 hull 보다 낮다", "정확": a["거칠기"], "복셀": b["거칠기"],
               "통과": bool(a["거칠기"] < b["거칠기"])}
    r["Q3"] = {"문턱": "닫힘 · 조각 1", "통과": bool(a["닫힘"] and a["조각"] == 1), "조각": a["조각"]}
    정.export(os.path.join(HERE, "out", "정확hull_%s.glb" % case))
    복셀.export(os.path.join(HERE, "out", "정확hull_%s_복셀.glb" % case))
    r["초"] = round(time.time() - t0, 1)
    q = os.path.join(OUT, "정확hull_%s.json" % r["때"])
    json.dump(r, open(q, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %-16s %22s %8s %7s %7s %8s %5s %4s" % ("판본", "못덮음 앞·옆·뒤", "거칠기", "평평", "계단", "면", "닫힘", "조각"))
    for n in ("복셀 이진 hull", "기본(타원 깎기)", "정확 hull"):
        x = r[n]
        print("  %-16s %22s %8.4f %7.3f %7.3f %8d %5s %4d"
              % (n, " ".join("%.4f" % x["못덮음"][v] for v in W.VIEWS), x["거칠기"], x["평평"],
                 x["계단"], x["면"], x["닫힘"], x["조각"]))
    print("  교집합 %.1f초 · Q1 %s · Q2 %s · Q3 %s" % (초, *("통과" if r[k]["통과"] else "짐" for k in ("Q1", "Q2", "Q3"))))
    print("  ->", q)
    return r


def 그림(case="오메가몬"):
    from PIL import Image
    import 앨리어싱 as AL
    L = lambda n: trimesh.load(os.path.join(HERE, "out", n), force="mesh")
    src = np.asarray(Image.open(os.path.join(HERE, "out", "누끼", "오메가몬_front", "흰바탕.png"))
                     .convert("RGB").resize((700, 700)))
    가슴 = ((-0.19, 0.56), 0.38)
    R = []
    for 이름, f in (("복셀 hull (지금 기본)", "세우기_껍질.glb"), ("정확 hull (메시 교집합)", "정확hull_%s.glb" % case)):
        a = L(f)
        R.append((이름, [src, PL.shaded(a, 0, AL.frame_of(a, 0), S=700),
                        PL.shaded(a, 45, AL.frame_of(a, 45), S=700),
                        PL.shaded(a, 0, 가슴, S=700), PL.shaded(a, 45, ((-0.19, 0.56), 0.38), S=700)]))
    LR.DC.grid(R, ("원화", "앞", "45°", "가슴 확대 (앞)", "가슴 확대 (45°)"),
               "정확 hull — 복셀을 안 거치면 면이 매끄러운가 (같은 마스크 · 같은 정렬)",
               "위 = 256 칸 복셀 + 마칭큐브 · 아래 = 세 실루엣 기둥의 manifold 교집합. 아래는 이진 hull 이라 단면이 네모나다(깊이 깎기 없음)",
               os.path.join(HERE, "out", "정확hull_%s.png" % case), S=420)


def selfcheck():
    # 정사각 마스크 셋 -> 상자. 부피가 맞아야 한다
    m = np.zeros((W.RES, W.RES), bool)
    m[300:700, 400:600] = True
    hull = None
    for v in W.VIEWS:
        g, n, k = 기둥(m, v, +1)
        hull = g if hull is None else hull ^ g
    t = tm(hull)
    px = (W.U1 - W.U0) / W.RES
    기대 = (202 * px) ** 2 * (402 * px)                     # 한 화소 부풀린 몫 포함
    assert t.is_watertight and abs(t.volume - 기대) / 기대 < 0.02, (t.volume, 기대)
    print("  자가검사 통과 — 상자 부피 %.5f (기대 %.5f) · 면 %d" % (t.volume, 기대, len(t.faces)))


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "검사"
    {"검사": selfcheck, "짓기": 짓기, "그림": 그림}[a]()
