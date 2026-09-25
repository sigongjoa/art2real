# -*- coding: utf-8 -*-
"""**공차 쿠폰** — 다보 틈을 실물로 정한다 (2026-09-25).

09-24 오메가몬 키트는 부품이 **하나도 안 들어갔다**. 다보 틈 한쪽 0.15 mm 는 레진 값이었고
FDM(A1 · 0.4 노즐 · PLA) 시작값은 0.20~0.30 이다(원형사 교본 5 장). 추정하지 말고 뽑아서 고른다.

    python 공차쿠폰.py  ->  out/출력/공차쿠폰/구멍판.stl · 시험막대.stl · 쿠폰.json

  구멍판   핀 지름 1.8 (키트 다보) · 3.0 두 줄 × 한쪽 틈 0.05 ~ 0.35 (0.05 간격) — 구멍 깊이 3 mm, 위로 열림
           칸마다 틈을 1/100 mm 로 새김 (5 = 0.05 · 35 = 0.35) · 줄 머리에 핀 지름
  시험막대 양 끝에 핀 (1.8 · 3.0, 길이 2.5, 지름은 설계값 그대로) — 판에 눕혀 뽑으면 핀이 위를 본다
쓰는 법: 막대 핀을 구멍마다 꽂아 「꽉(안 들어감) · 알맞음(손으로 끼워지고 안 빠짐) · 헐거움(뒤집으면 빠짐)」을 적는다.
알맞음 칸의 틈이 키트 다보 틈이 된다. 키트 핀은 이 쿠폰과 같은 방향(세로)으로 뽑히는 것이 가장 좋다."""
import json, os, subprocess, sys
import numpy as np, trimesh
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from shapely.geometry import Polygon
from shapely.ops import unary_union

OUT = r"G:\art2real\원화3d\out\출력\공차쿠폰"
틈들 = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35]
핀들 = [1.8, 3.0]
간격, 판두께, 구멍깊이, 새김깊이, 핀길이 = 8.0, 4.0, 3.0, 0.4, 2.5
BBL = r"C:\Program Files\OrcaSlicer\resources\profiles\BBL"
ORCA = r"C:\Program Files\OrcaSlicer\orca-slicer.exe"


def 글자(s, 높이, 중심xy):
    """글자를 윤곽 다각형으로 (matplotlib TextPath · 짝홀 규칙으로 구멍 처리)."""
    tp = TextPath((0, 0), s, size=높이, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    링 = [Polygon(p) for p in tp.to_polygons() if len(p) >= 3]
    링 = [r.buffer(0) for r in 링 if r.area > 1e-6]
    모양 = None
    for r in sorted(링, key=lambda r: -r.area):                 # 큰 것부터: 안에 들어가면 빼고, 아니면 더한다
        모양 = r if 모양 is None else (모양.difference(r) if 모양.contains(r) else 모양.union(r))
    minx, miny, maxx, maxy = 모양.bounds
    from shapely import affinity
    return affinity.translate(모양, 중심xy[0] - (minx + maxx) / 2, 중심xy[1] - (miny + maxy) / 2)


def 새김(판, 모양, 윗면z):
    polys = list(모양.geoms) if hasattr(모양, "geoms") else [모양]
    칼 = trimesh.util.concatenate([trimesh.creation.extrude_polygon(p, 새김깊이 + 0.2) for p in polys])
    칼.apply_translation([0, 0, 윗면z - 새김깊이])
    return trimesh.boolean.difference([판, 칼], engine="manifold")


def 구멍판():
    n = len(틈들); 폭 = 12 + n * 간격; 깊 = 8 + len(핀들) * 12
    판 = trimesh.creation.box([폭, 깊, 판두께]); 판.apply_translation([폭 / 2, 깊 / 2, 판두께 / 2])
    칼들 = []
    for j, d in enumerate(핀들):
        y = 깊 - 7 - j * 12
        for i, c in enumerate(틈들):
            x = 12 + i * 간격
            h = trimesh.creation.cylinder(radius=d / 2 + c, height=구멍깊이 + 0.2, sections=64)
            h.apply_translation([x, y, 판두께 - (구멍깊이 + 0.2) / 2 + 0.2]); 칼들.append(h)
    판 = trimesh.boolean.difference([판] + 칼들, engine="manifold")
    for j, d in enumerate(핀들):
        y = 깊 - 7 - j * 12
        판 = 새김(판, 글자("%.1f" % d, 3.0, (5.0, y)), 판두께)
        for i, c in enumerate(틈들):
            판 = 새김(판, 글자("%d" % round(c * 100), 2.6, (12 + i * 간격, y - 4.6)), 판두께)
    return 판


def 시험막대():
    길 = 40.0; 막대 = trimesh.creation.box([길, 8, 3]); 막대.apply_translation([길 / 2, 4, 1.5])
    핀 = []
    for x, d in ((5, 핀들[0]), (길 - 5, 핀들[1])):
        p = trimesh.creation.cylinder(radius=d / 2, height=핀길이, sections=64); p.apply_translation([x, 4, 3 + 핀길이 / 2]); 핀.append(p)
    막대 = trimesh.boolean.union([막대] + 핀, engine="manifold")
    막대 = 새김(막대, 글자("1.8", 3.0, (13, 4)), 3.0)
    return 새김(막대, 글자("3.0", 3.0, (길 - 13, 4)), 3.0)


def main():
    os.makedirs(OUT, exist_ok=True)
    판, 막대 = 구멍판(), 시험막대()
    막대.apply_translation([0, -14, 0])                             # 한 판에 나란히
    낼 = {}
    for 이름, m in (("구멍판", 판), ("시험막대", 막대)):
        assert m.is_watertight, 이름 + " 이 닫혀 있지 않다"
        p = os.path.join(OUT, 이름 + ".stl"); m.export(p)
        낼[이름] = {"닫힘": True, "치수mm": [round(float(v), 1) for v in m.extents], "부피cm3": round(float(m.volume) / 1000, 2)}
        print("  %s  %s mm · %.2f cm³ · 닫힘" % (이름, 낼[이름]["치수mm"], 낼[이름]["부피cm3"]))
    낼["틈(한쪽 mm)"] = 틈들; 낼["핀 지름 mm"] = 핀들; 낼["구멍 지름 = 핀 + 2×틈"] = True
    # 슬라이서 견적 (A1 · 0.2 mm · PLA Basic · 서포트 없음)
    if os.path.exists(ORCA):
        설정 = ";".join([os.path.join(BBL, "machine", "Bambu Lab A1 0.4 nozzle.json"), os.path.join(BBL, "process", "0.20mm Standard @BBL A1.json")])
        r = subprocess.run([ORCA, "--load-settings", 설정, "--load-filaments", os.path.join(BBL, "filament", "Bambu PLA Basic @BBL A1.json"),
                            "--arrange", "1", "--slice", "0", "--outputdir", OUT, os.path.join(OUT, "구멍판.stl"), os.path.join(OUT, "시험막대.stl")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        낼["슬라이스 종료코드"] = r.returncode
        g = [f for f in os.listdir(OUT) if f.endswith(".gcode")]
        for f in g:
            t = open(os.path.join(OUT, f), encoding="utf-8", errors="replace").read()
            for 줄 in t.splitlines():
                if "printing time" in 줄 or "filament used [g]" in 줄 or "total filament weight" in 줄:
                    낼.setdefault("견적", []).append(줄.strip("; ").strip())
        print("  슬라이스", r.returncode, 낼.get("견적"))
    json.dump(낼, open(os.path.join(OUT, "쿠폰.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
