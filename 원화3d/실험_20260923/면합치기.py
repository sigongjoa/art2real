# -*- coding: utf-8 -*-
"""**면 합치기** — 잔 면을 넓은 판으로 (2026-09-23).

    python 면합치기.py        -> out/면합치기.png · out/기록/면합치기_<때>.json

사용자(09-23): 「면을 합치는 알고리즘이 있으면 좋겠다 지금은 면이 너무 작아서」.

    합치기(m)  영역 성장 -> 영역마다 최소제곱 평면 -> 정점을 닿은 평면들의 교차로 옮김
    다듬기(m)  대조군. 라플라시안 — 같은 거리만큼 움직이지만 판을 만들지는 않는다
"""
import json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
from collections import deque
import numpy as np
import trimesh, cv2, fast_simplification
from PIL import Image, ImageDraw, ImageFont

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921",
                r"G:\art2real\원화3d\실험_20260922", r"G:\art2real\원화3d\실험_20260923"]
import hull as H, 정답 as JD, 부품분할 as BB, 도면벤치_천장 as DC
import 지표 as Z, 깊이추정 as GC, 평면조각 as PJ
from 평면조각 import _이웃, 영역


def 합치기(m, 차례=((55, 26), (40, 20), (26, 14), (16, 9)), 늘어짐=0.12, 잔조각=2e-4, 정리=0.0):
    m = m.copy(); m.merge_vertices()
    v0 = np.asarray(m.vertices, float)
    v = v0.copy()
    for 국소, 전체 in 차례:
        m = trimesh.Trimesh(v, m.faces, process=False)
        시작, 이웃 = _이웃(m)
        라벨, L = 영역(m, 시작, 이웃, 국소, 전체)
        fa = m.area_faces; 몫 = np.bincount(라벨, weights=fa, minlength=L) / fa.sum()
        fc = m.triangles_center; fn = np.asarray(m.face_normals)
        # 영역마다 면적 가중 최소제곱 평면 (법선의 2차 모멘트 대신 점의 공분산)
        C = np.zeros((L, 3)); W = np.zeros(L)
        np.add.at(C, 라벨, fc * fa[:, None]); np.add.at(W, 라벨, fa)
        C /= np.maximum(W, 1e-12)[:, None]
        N = np.zeros((L, 3)); np.add.at(N, 라벨, fn * fa[:, None])
        N /= np.maximum(np.linalg.norm(N, axis=1), 1e-12)[:, None]
        # 정점마다: 닿은 영역들의 평면을 모아 3x3 을 푼다 (1·2·3 개면 면·모서리·꼭짓점)
        A = np.zeros((len(v), 3, 3)); b = np.zeros((len(v), 3)); k = np.zeros(len(v))
        f = np.asarray(m.faces)
        본 = [set() for _ in range(len(v))]
        for fi in range(len(f)):
            l = 라벨[fi]
            if 몫[l] < 잔조각: continue           # 부스러기 영역은 정점을 붙들지 않는다
            n = N[l]; d = n @ C[l]
            P = np.outer(n, n); q = n * d
            for vi in f[fi]:
                if l in 본[vi]: continue
                본[vi].add(l); A[vi] += P; b[vi] += q; k[vi] += 1
        λ = 늘어짐 * np.maximum(k, 1)
        A += λ[:, None, None] * np.eye(3)
        b += λ[:, None] * v
        v = np.linalg.solve(A, b[:, :, None])[:, :, 0]
    g = trimesh.Trimesh(v, m.faces, process=False)
    g.merge_vertices(digits_vertex=5)
    g.update_faces(g.nondegenerate_faces())
    g.remove_unreferenced_vertices()
    if 정리:
        # 판 안쪽은 이미 평평하다 -> 감면(quadric)이 공짜로 접는다. 판 사이에 남은 바늘 삼각형이 이걸로 사라진다.
        vv, ff = fast_simplification.simplify(np.asarray(g.vertices, np.float32),
                                              np.asarray(g.faces, np.int32), 정리)
        g = trimesh.Trimesh(vv, ff, process=False)
        g.update_faces(g.nondegenerate_faces()); g.remove_unreferenced_vertices()
    return g, float(np.linalg.norm(v - v0, axis=1).mean())


def 다듬기(m, 목표, 회=60):
    """**대조군** — 라플라시안. 합치기와 같은 평균 이동 거리가 될 때까지만 돌린다."""
    m = m.copy(); m.merge_vertices()
    v0 = np.asarray(m.vertices, float); v = v0.copy()
    e = m.edges_unique
    n = len(v)
    for _ in range(회):
        s = np.zeros((n, 3)); c = np.zeros(n)
        for a, b in ((e[:, 0], e[:, 1]), (e[:, 1], e[:, 0])):
            np.add.at(s, a, v[b]); np.add.at(c, a, 1)
        v = v + 0.5 * (s / np.maximum(c, 1)[:, None] - v)
        if np.linalg.norm(v - v0, axis=1).mean() >= 목표: break
    return trimesh.Trimesh(v, m.faces, process=False), float(np.linalg.norm(v - v0, axis=1).mean())


def 격자로(m, ux, uy, z):
    A, o = JD.grid(m, 봉합=1)
    return DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0


def iou(a, b):
    return float((a & b).sum() / max((a | b).sum(), 1))


def main():
    F = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", s)
    기록, 줄들, 이름줄 = {}, [], None
    for c in [GC.케이스들[i] for i in (0, 4, 9)]:
        raw, masks, bs, p = BB.판(c)
        g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
        ux, uy, z = [np.asarray(a) for a in ax]
        O = g > 0
        tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
        A, o = JD.grid(tm, 봉합=1)
        T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
        원 = Z.메시로(O, (ux, uy, z))
        합, 거리 = 합치기(원)
        정, _ = 합치기(원, 정리=0.93)
        대, 거리2 = 다듬기(원, 거리)
        결, 타 = {}, []
        for 이름, m in (("타원(지금)", 원), ("면 합치기", 합), ("합치기+정리", 정), ("대조: 라플라시안", 대), ("정답", tm)):
            r, 라벨, mm = PJ.재기(m, 전체=10)
            G = 격자로(m, ux, uy, z)
            r["부피 IoU"] = round(iou(G, T), 3)
            r["실루엣 IoU"] = round(float(np.mean([iou(G.any(a), O.any(a)) for a in (0, 1, 2)])), 3)
            결[이름] = r
            im = PJ.칠하기(mm, 라벨)
            pim = Image.fromarray(im)
            ImageDraw.Draw(pim).text((4, 3), "조각 %d · 큰것 %.0f%% · IoU %.2f" % (
                r["조각 수"], 100 * r["1% 이상이 덮는 몫"], r["부피 IoU"]), fill=(40, 40, 40), font=F(12))
            타.append(np.asarray(pim))
        결["_움직인 거리"] = [round(거리, 4), round(거리2, 4)]
        기록[c] = 결
        이름줄 = ["타원(지금)", "면 합치기", "합치기+정리", "대조: 라플라시안", "정답"]
        row = np.hstack(타)
        band = np.full((22, row.shape[1], 3), 255, np.uint8)
        pim = Image.fromarray(np.vstack([band, row]))
        ImageDraw.Draw(pim).text((5, 3), c[:34], fill=(80, 80, 80), font=F(14))
        줄들.append(np.asarray(pim))
        print("  " + c[:26], " | ".join("%s 조각%5d 큰것%.2f IoU%.3f 실루엣%.3f" % (
            k, v["조각 수"], v["1% 이상이 덮는 몫"], v["부피 IoU"], v["실루엣 IoU"])
            for k, v in 결.items() if k[0] != "_"), flush=True)
    머리 = Image.fromarray(np.full((28, 줄들[0].shape[1], 3), 255, np.uint8))
    d = ImageDraw.Draw(머리)
    for i, n in enumerate(이름줄):
        d.text((i * 230 + 6, 5), n, fill=(25, 25, 25), font=F(15))
    out = np.vstack([np.asarray(머리)] + 줄들)
    cv2.imencode(".png", out[:, :, ::-1])[1].tofile(os.path.join(H.OUT, "면합치기.png"))
    pth = os.path.join(H.OUT, "기록", "면합치기_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(기록, open(pth, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    중 = lambda k, n: float(np.median([기록[c][n][k] for c in 기록]))
    print("중앙값:", {n: (int(중("조각 수", n)), round(중("1% 이상이 덮는 몫", n), 3),
                        round(중("부피 IoU", n), 3), round(중("실루엣 IoU", n), 3)) for n in 이름줄})
    print(pth)


if __name__ == "__main__":
    main()
