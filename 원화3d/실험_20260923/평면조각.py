# -*- coding: utf-8 -*-
"""**평면 조각** — 면이 넓게 나오나, 잘게 나오나 (2026-09-23).

    python 평면조각.py       -> out/기록/평면조각_<때>.json · out/평면조각.png

사용자(09-23): 「지금 보면 면이 크게 안 나오고 짧게 짧게 나오는데?」
법선이 비슷한 이웃 면을 이어 붙여(영역 성장) **평면 조각**으로 묶고, 그 조각이 얼마나 큰지 잰다.

    조각 수                 적을수록 넓은 판이다
    가장 큰 조각의 면적 몫
    큰 조각(전체 면적의 1% 이상)이 덮는 몫   ← 「판이 있나」를 한 숫자로
"""
import json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
import cv2
from collections import deque
from PIL import Image, ImageDraw, ImageFont

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922", r"G:\art2real\원화3d\실험_20260923"]
import hull as H
import 정답 as JD
import 부품분할 as BB
import 면자르기 as MJ
import 도면벤치_천장 as DC
import 지표 as Z
import 색대응 as CC
import 깊이칸 as K
import 깊이추정 as GC

문턱도 = 8.0            # 이웃 면 사이 각이 이보다 작으면 같은 판으로 본다


def _이웃(m):
    a = m.face_adjacency
    n = len(m.faces)
    cnt = np.bincount(a[:, 0], minlength=n) + np.bincount(a[:, 1], minlength=n)
    시작 = np.zeros(n + 1, np.int64); np.cumsum(cnt, out=시작[1:])
    끝 = 시작[:-1].copy()
    이웃 = np.empty(시작[-1], np.int64)
    for x, y in ((a[:, 0], a[:, 1]), (a[:, 1], a[:, 0])):
        for i, j in zip(x, y):
            이웃[끝[i]] = j; 끝[i] += 1
    return 시작, 이웃


def 영역(m, 시작, 이웃, 국소, 전체):
    """**영역 성장** — 이웃 면과의 각 < 국소 이고 영역 평균 법선과의 각 < 전체 일 때만 붙인다.
    국소만 보면 굽은 면이 통째로 한 판이 되어 공으로 눌린다. 둘 다 본다."""
    fn = np.asarray(m.face_normals); fa = m.area_faces
    c국, c전 = np.cos(np.radians(국소)), np.cos(np.radians(전체))
    라벨 = np.full(len(fn), -1, np.int64)
    L = 0
    for s in np.argsort(fa)[::-1]:
        if 라벨[s] >= 0: continue
        라벨[s] = L; 합 = fn[s] * fa[s]; q = deque([s])
        while q:
            i = q.popleft()
            평 = 합 / max(np.linalg.norm(합), 1e-12)
            for k in range(시작[i], 시작[i + 1]):
                j = 이웃[k]
                if 라벨[j] >= 0: continue
                if fn[i] @ fn[j] < c국 or 평 @ fn[j] < c전: continue
                라벨[j] = L; 합 = 합 + fn[j] * fa[j]; q.append(j)
        L += 1
    return 라벨, L


def 조각내기(m, 문턱=문턱도, 전체=None):
    """법선이 비슷한 이웃 면을 이어 붙인다. 면 라벨을 돌려준다.

    `전체` 를 주면 **영역 평균 법선과의 각**도 함께 본다 — 이걸 안 보면 매끈한 공이 통째로 한 판이 되어
    라플라시안 다듬기가 「큰 판 0.96」으로 1 위를 한다(09-23 대조군이 자를 깨뜨렸다). 판은 **평평해야** 판이다."""
    m = m.copy(); m.merge_vertices()
    if 전체 is not None:
        시작, 이웃 = _이웃(m)
        라벨, _ = 영역(m, 시작, 이웃, 문턱, 전체)
        return 라벨, m
    adj = m.face_adjacency
    ang = np.degrees(m.face_adjacency_angles)
    붙 = adj[ang < 문턱]
    n = len(m.faces)
    부모 = np.arange(n)

    def 찾기(a):
        while 부모[a] != a:
            부모[a] = 부모[부모[a]]; a = 부모[a]
        return a
    for a, b in 붙:
        ra, rb = 찾기(a), 찾기(b)
        if ra != rb: 부모[ra] = rb
    라벨 = np.array([찾기(i) for i in range(n)])
    _, 라벨 = np.unique(라벨, return_inverse=True)
    return 라벨, m


def 재기(m, 전체=None):
    라벨, mm = 조각내기(m, 전체=전체)
    면적 = mm.area_faces
    합 = np.bincount(라벨, weights=면적)
    전체 = 면적.sum()
    몫 = np.sort(합)[::-1] / max(전체, 1e-9)
    큰 = 몫[몫 >= 0.01]
    return {"조각 수": int(len(합)), "가장 큰 조각 몫": round(float(몫[0]), 3),
            "1% 이상 조각 수": int(len(큰)), "1% 이상이 덮는 몫": round(float(큰.sum()), 3),
            "면당 면적 중앙": round(float(np.median(면적) / 전체 * 1000), 4)}, 라벨, mm


def 칠하기(m, 라벨, 크기=230, yaw=32, pitch=-72):
    rng = np.random.default_rng(3)
    pal = rng.integers(70, 235, (라벨.max() + 1, 3))
    v = np.asarray(m.vertices); v = v - v.mean(0)
    R = (trimesh.transformations.rotation_matrix(np.radians(yaw), [0, 0, 1])[:3, :3]
         @ trimesh.transformations.rotation_matrix(np.radians(pitch), [1, 0, 0])[:3, :3])
    p = v @ R.T
    tri = p[np.asarray(m.faces)]
    sc = 크기 * 0.40 / max(np.abs(p[:, [0, 2]]).max(), 1e-9)
    pts = np.stack([tri[:, :, 0] * sc + 크기 / 2, -tri[:, :, 2] * sc + 크기 / 2], -1).astype(np.int32)
    order = np.argsort(tri[:, :, 1].mean(1))[::-1]
    fn = np.asarray(m.face_normals) @ R.T
    L = np.array([0.35, -0.6, 0.72]); L /= np.linalg.norm(L)
    sh = np.clip(fn @ L, 0, 1) * 0.55 + 0.45
    im = np.full((크기, 크기, 3), 255, np.uint8)
    for i in order:
        c = tuple(int(x * sh[i]) for x in pal[라벨[i]])
        cv2.fillConvexPoly(im, pts[i], c)
    return im


def main():
    F = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", s)
    기록, 줄들, 이름줄 = {}, [], None
    for c in [GC.케이스들[i] for i in (0, 4, 9)]:
        raw, masks, bs, p = BB.판(c)
        g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
        gh, _ = H.field_hull(masks, back_sign=bs, n=BB.N)
        ux, uy, z = [np.asarray(a) for a in ax]
        O = g > 0
        tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
        A, o = JD.grid(tm, 봉합=1)
        T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
        격, _ = CC.판색(c, raw, masks, p, bs)
        판 = [("hull", Z.메시로(gh > 0, (ux, uy, z))), ("타원(지금)", Z.메시로(O, (ux, uy, z))),
             ("색 대응", Z.메시로(CC.깎기(O, 격, 6), (ux, uy, z))), ("정답", tm)]
        타, 결 = [], {}
        for 이름, m in 판:
            r, 라벨, mm = 재기(m)
            결[이름] = r
            im = 칠하기(mm, 라벨)
            pim = Image.fromarray(im)
            ImageDraw.Draw(pim).text((4, 3), "조각 %d · 큰것 %.0f%%" % (r["조각 수"], 100 * r["1% 이상이 덮는 몫"]),
                                     fill=(40, 40, 40), font=F(12))
            타.append((이름, np.asarray(pim)))
        기록[c] = 결
        이름줄 = [n for n, _ in 타]
        row = np.hstack([t for _, t in 타])
        band = np.full((22, row.shape[1], 3), 255, np.uint8)
        pim = Image.fromarray(np.vstack([band, row]))
        ImageDraw.Draw(pim).text((5, 3), c[:34], fill=(80, 80, 80), font=F(14))
        줄들.append(np.asarray(pim))
        print("  %-28s " % c[:28] + " | ".join("%s 조각 %4d 큰것 %.2f" % (k, v["조각 수"], v["1% 이상이 덮는 몫"]) for k, v in 결.items()), flush=True)
    머리 = Image.fromarray(np.full((28, 줄들[0].shape[1], 3), 255, np.uint8))
    d = ImageDraw.Draw(머리)
    for i, n in enumerate(이름줄):
        d.text((i * 230 + 6, 5), n, fill=(25, 25, 25), font=F(15))
    out = np.vstack([np.asarray(머리)] + 줄들)
    cv2.imencode(".png", out[:, :, ::-1])[1].tofile(os.path.join(H.OUT, "평면조각.png"))
    pth = os.path.join(H.OUT, "기록", "평면조각_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(기록, open(pth, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(pth, os.path.join(H.OUT, "평면조각.png"))


if __name__ == "__main__":
    main()
