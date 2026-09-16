# -*- coding: utf-8 -*-
"""**머리만 떼서 정제하고 되돌린다** (2026-09-17). 계획 `claudedocs/plan_DetailGen3D_20260916.md` 「머리 게이트」.

    python 머리정제.py 준비     머리 메시 · 얼굴 크롭 · 빈 이미지 -> 스크래치 dg_head/
    (DetailGen3D 를 imggen venv 에서 두 번 — 크롭 · 빈 이미지)
    python 머리정제.py 합침     정제된 머리를 원좌표로 되돌려 목에서 잇고 재고 그린다

**왜 머리만.** DetailGen3D 는 이미지를 224×224 로 본다. 전신이면 인물 키 187화소 · 눈 1.3화소라 눈이 인코더에 안 걸린다 (09-16 실측).
얼굴을 크롭하면 눈이 수십 화소가 된다. 메시도 같은 머리만 줘야 이미지와 짝이 맞는다.
09-16 조각생성(짐)과 다른 점: 머리를 **새로 생성하지 않고 같은 머리를 다듬는다** — 자리 · 크기는 원 메시가 정한다.
"""
import os
import sys

import cv2
import numpy as np
import trimesh

S = r"C:\Users\zesky\AppData\Local\Temp\claude\G--art2real\612c5d2a-3321-47b1-8ebf-c897df4a0801\scratchpad"
OUT = os.path.join(S, "dg_head")
RAW = os.path.join(S, "hermit", "hermit.glb")          # TripoSG 원출력 (y 위 · 원좌표)
IMG = os.path.join(S, "hermit", "hermit_prep.png")     # TripoSG 가 본 판
# 머리 상자 (원좌표) — 09-17 탐침: 키 1.904 · 지팡이는 x < -0.38 · 꼭대기 14% 안의 머리 x -0.03..0.14
BOX = dict(y0=0.66, x0=-0.30, x1=0.32)
NECK = 0.72                                           # 이 높이 위만 정제본으로 바꾼다 (상자 아래 0.06 은 겹침 여유)


def head_mesh(m):
    c = m.triangles_center
    keep = (c[:, 1] > BOX["y0"]) & (c[:, 0] > BOX["x0"]) & (c[:, 0] < BOX["x1"])
    return m.submesh([np.nonzero(keep)[0]], append=True)


def face_crop(m, head):
    """원좌표 머리 상자를 입력 판 화소로 옮겨 정사각으로 자른다. 판의 인물 bbox ↔ 메시 bbox 를 선형으로 맞춘다 (지팡이 · 손이 둘 다에 있다)."""
    im = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
    ys, xs = np.nonzero(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) < 247)
    V = np.asarray(m.vertices)
    (mx0, my0), (mx1, my1) = V[:, :2].min(0), V[:, :2].max(0)
    px = lambda x: xs.min() + (x - mx0) / (mx1 - mx0) * (xs.max() - xs.min())
    py = lambda y: ys.min() + (my1 - y) / (my1 - my0) * (ys.max() - ys.min())
    (hx0, hy0), (hx1, hy1) = head.vertices[:, :2].min(0), head.vertices[:, :2].max(0)   # 머리 메시 bbox 로 — 지팡이 꼭대기가 전체 bbox 를 끌어올린다
    x0, x1, y0, y1 = px(hx0), px(hx1), py(hy1), py(hy0)
    side = int(max(x1 - x0, y1 - y0) * 1.12)
    cx, cy = int((x0 + x1) / 2), int((y0 + y1) / 2)
    pad = np.full((side, side, 3), 255, np.uint8)
    X0, Y0 = cx - side // 2, cy - side // 2
    a0, b0 = max(0, Y0), max(0, X0)
    a1, b1 = min(im.shape[0], Y0 + side), min(im.shape[1], X0 + side)
    pad[a0 - Y0:a1 - Y0, b0 - X0:b1 - X0] = im[a0:a1, b0:b1]
    return pad


def prepare():
    os.makedirs(OUT, exist_ok=True)
    m = trimesh.load(RAW, force="mesh")
    h = head_mesh(m)
    h.export(os.path.join(OUT, "head.glb"))
    crop = face_crop(m, h)
    cv2.imencode(".png", crop)[1].tofile(os.path.join(OUT, "face.png"))
    cv2.imencode(".png", np.full_like(crop, 255))[1].tofile(os.path.join(OUT, "blank.png"))
    print("  머리 메시 면 %d · 얼굴 크롭 %s -> %s" % (len(h.faces), crop.shape[:2], OUT))


def back_to_raw(refined, head):
    """DetailGen3D 는 입력을 bbox 중심 · 최대변 1.9 로 옮겨 풀고 그 좌표로 낸다 — 같은 변환을 거꾸로."""
    c = head.bounding_box.centroid
    s = 1.9 / max(head.bounding_box.extents)
    r = refined.copy()
    r.apply_scale(1.0 / s)
    r.apply_translation(c)
    return r


def merge(tag):
    m = trimesh.load(RAW, force="mesh")
    head = trimesh.load(os.path.join(OUT, "head.glb"), force="mesh")
    ref = back_to_raw(trimesh.load(os.path.join(OUT, tag, "head.glb"), force="mesh"), head)
    c = m.triangles_center
    inbox = (c[:, 1] > NECK) & (c[:, 0] > BOX["x0"]) & (c[:, 0] < BOX["x1"])
    body = m.submesh([np.nonzero(~inbox)[0]], append=True)
    rc = ref.triangles_center
    top = ref.submesh([np.nonzero(rc[:, 1] > NECK)[0]], append=True)
    # 이음매 — 목 높이 단면에서 원 메시 윤곽과 정제본 윤곽의 거리
    seam = None
    try:
        a = m.section(plane_origin=[0, NECK, 0], plane_normal=[0, 1, 0])
        b = ref.section(plane_origin=[0, NECK, 0], plane_normal=[0, 1, 0])
        if a is not None and b is not None:
            A = np.asarray(a.vertices); B = np.asarray(b.vertices)
            A = A[(A[:, 0] > BOX["x0"]) & (A[:, 0] < BOX["x1"])]
            B = B[(B[:, 0] > BOX["x0"]) & (B[:, 0] < BOX["x1"])]
            from scipy.spatial import cKDTree
            d1 = cKDTree(B).query(A)[0]; d2 = cKDTree(A).query(B)[0]
            seam = (float(np.median(d1)), float(np.percentile(np.r_[d1, d2], 95)))
    except Exception as e:
        print("  이음매 단면 실패:", e)
    out = trimesh.util.concatenate([body, top])
    out.export(os.path.join(OUT, "merged_%s.glb" % tag))
    return m, ref, out, seam


if __name__ == "__main__":
    a = sys.argv[1:] or ["준비"]
    if a[0] == "준비":
        prepare()
