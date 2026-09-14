# -*- coding: utf-8 -*-
"""**오메가몬 옆면의 가로 띠(찢김)를 잡는다** — 깊이색에서 앨리어싱보다 크게 보인 결.

    python 찢김.py     -> out/깊이색_찢김.png · out/찢김_<판본>.glb · out/기록/찢김_<날짜>.json

`깊이색_오메가몬.png` 에서 줄마다 색이 뚝 바뀌는 가로 띠가 기준 · ITK · ITK국소 · 가우시안 **넷 다 그대로**였다.
높이마다 깊이를 따로 정규화해 줄끼리 앞면 깊이가 튀는 찢김이다 (README 09-11 「스무딩 시험」). 이미 있는 두 수를 켠다.

## 판본 — 돌리기 전에 적는다 (2026-09-13 밤)

    기준            파이프 깊이맵 · lam 0.20 · ZSMOOTH 0          (지금 hull.py)
    Z2              기준 + ZSMOOTH σ 2 칸 (앞·뒷면 깊이만 높이 방향으로 민다 — 실루엣 안 건드림)
    타원1.00         타원 깊이맵(hull 단면 내접 타원) · lam 1.00    (09-12 벤치 셋 45장을 지난 후보)
    타원1.00+Z2      위 + ZSMOOTH σ 2
    전부            타원1.00+Z2 위에 ITK국소 (두꺼운 곳만 한 칸 구속 스무딩)

메시는 전부 `앨리어싱.variant` 의 위생(제일 큰 덩어리 · 법선)을 거친다.

## 판정 — 판본마다 넷을 다 지켜야 「통과」

    되받아 재기   세 판 못 덮음 < 6% (hull.THRESH)
    가는 곳       폭 약 12 화소 미만 화소 덮음이 기준보다 1%p 넘게 안 떨어진다 (세 판)
    hull 상한     결과 칸 중 이진 hull 밖 ≤ 2%
    찢김          `표면.tear` (앞면이 위아래 줄끼리 3 칸 넘게 튄 쌍 비율 — 09-11 자가검사 지난 지표) 가 **기준보다 낮다**

결은 깊이색 + 등깊이선 그림으로 본다 (관찰). 오메가몬은 정답 메시가 없다 — 모양이 **맞는지**는 이 시험이 못 잰다.
타원 lam1.00 은 많이 깎는 판본이라 부피가 줄어드는데, 그게 맞는지는 벤치(45장)가 잰 것이지 여기서 재는 게 아니다.
"""
import json
import os
import sys
import time

import numpy as np

HERE = r"G:\art2real\원화3d"
SCR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, SCR)
os.chdir(HERE)
import hull as H
import win as W
import 표면 as SF
import 앨리어싱 as AL

VARIANTS = ("기준", "Z2", "타원1.00", "타원1.00+Z2", "전부")


def carve(masks, plain, axes, deps_pipe, bs, depth, lam, z):
    import 오라클 as O
    H.ZSMOOTH = z
    try:
        deps = deps_pipe if depth == "파이프" else O.ellipse_depths(plain, axes, bs)
        vox, _ = H.carve_depth(masks, deps, lam=lam, back_sign=bs)
    finally:
        H.ZSMOOTH = 0.0
    return vox


def main():
    t0 = time.time()
    masks, plain, _, axes, bs, deps = AL.build()
    print("  준비 %.0f초" % (time.time() - t0), flush=True)
    spec = {"기준": ("파이프", 0.20, 0.0), "Z2": ("파이프", 0.20, 2.0),
            "타원1.00": ("타원", 1.00, 0.0), "타원1.00+Z2": ("타원", 1.00, 2.0), "전부": ("타원", 1.00, 2.0)}
    meshes, res = {}, {}
    for name in VARIANTS:
        t = time.time()
        vox = carve(masks, plain, axes, deps, bs, *spec[name])
        mesh, occ = AL.variant("ITK국소" if name == "전부" else "기준", vox, axes)
        meshes[name] = mesh
        mesh.export(os.path.join(HERE, "out", "찢김_%s.glb" % name))
        res[name] = {"재기": AL.reproject(mesh, masks, bs), "hull밖": float((occ & ~plain).sum() / max(occ.sum(), 1)),
                     "찢김": SF.tear(occ), "덩어리": SF.pieces(occ), "부피": float(mesh.volume), "초": time.time() - t}
        r = res[name]
        print("  %-11s %3.0f초 · 부피 %.4f · 찢김 %.1f%% · 덩어리 %d · hull 밖 %.2f%% · 못 덮음 %s · 가는 곳 %s" % (
            name, r["초"], r["부피"], 100 * r["찢김"], r["덩어리"], 100 * r["hull밖"],
            " ".join("%.2f" % (100 * r["재기"][v]["miss"]) for v in W.VIEWS),
            " ".join("%.1f" % (100 * r["재기"][v]["thin"]) for v in W.VIEWS)), flush=True)
    b = res["기준"]
    verdict = {}
    for name in VARIANTS[1:]:
        r = res[name]
        ok = {"되받아 재기": all(r["재기"][v]["miss"] < H.THRESH for v in W.VIEWS),
              "가는 곳": all(r["재기"][v]["thin"] >= b["재기"][v]["thin"] - AL.THIN_DROP for v in W.VIEWS),
              "hull 상한": r["hull밖"] <= AL.OUTSIDE,
              "찢김": r["찢김"] < b["찢김"]}
        verdict[name] = {**ok, "통과": all(ok.values())}
        print("  판정 %-11s %s · **%s**" % (name, " · ".join("%s %s" % (k, "O" if x else "X") for k, x in ok.items()),
                                          "통과" if all(ok.values()) else "짐"))
    p = os.path.join(HERE, "out", "기록", "찢김_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"때": time.strftime("%Y-%m-%d %H:%M"), "판정": verdict, "결과": res}, open(p, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("  기록 -> %s" % os.path.relpath(p, HERE))
    figure(meshes)


def figure(meshes):
    import 깊이색 as DC
    views = (-90, 45)
    fr = {az: AL.frame_of(meshes["기준"], az) for az in views}
    dr = {az: DC.depth_range(meshes["기준"], az) for az in views}
    (x0, z0), span = fr[-90]
    zoom = ((x0 + 0.30 * span, z0 + 0.45 * span), 0.35 * span)
    rows = []
    for n in VARIANTS:
        tiles = [DC.colorize(DC.zbuffer(meshes[n], az, fr[az], 400), dr[az]) for az in views]
        tiles.append(DC.colorize(DC.zbuffer(meshes[n], -90, zoom, 400), dr[-90]))
        rows.append((n, tiles))
        print("  %s 그림" % n, flush=True)
    DC.grid(rows, ["옆 (az −90)", "45도", "옆 가슴 확대"], "오메가몬 — 찢김 잡기 · 깊이색 + 등깊이선 (z 버퍼)",
            "빨강 = 가깝다 · 검은 선 = 같은 깊이. 가로 띠(줄마다 색이 뚝 바뀜)가 찢김이다. 같은 열은 틀 · 깊이 범위가 같다 (기준에 맞춤)",
            os.path.join(HERE, "out", "깊이색_찢김.png"))


if __name__ == "__main__":
    main()
