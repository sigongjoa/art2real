# -*- coding: utf-8 -*-
"""한 판 출력 준비 — 부품 STL 을 눕히고 OrcaSlicer CLI 로 A1 · 0.2 mm · PLA Basic · 트리 서포트로 슬라이스 (2026-09-26).

    python 출력판.py <판이름> <STL 경로> ... [--그대로] [--자리]   (--그대로 = 이미 출력 방향 · --자리 = 판 좌표 그대로, 자동 배치 안 함)
      -> out/출력/오메가몬_PG/판/<판이름>/  눕힌 STL · <판이름>.3mf(슬라이스 포함) · 견적.json

눕히기: 반쪽 가름면(앞 반쪽 = y 최대면)이 판에 닿게 y → −z (x 축 −90°). 끼움 · 돌출 판도 두께 축이 y 라 같은 회전으로 눕는다.
프린터로 보내기는 CLI 가 못 한다 — 3mf 를 OrcaSlicer 에서 열어 「출력」."""
import os, sys, json, subprocess
import numpy as np, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 관절부품 import 평탄      # BBL inherits 풀기 — 안 풀면 판 200×200 · 속도/온도 기본값 (09-25)

ORCA = r"C:\Program Files\OrcaSlicer\orca-slicer.exe"
BBL = r"C:\Program Files\OrcaSlicer\resources\profiles\BBL"
ROOT = r"G:\art2real\원화3d\out\출력\오메가몬_PG"

def main(판, 파일들, 눕히기=True, 자리=False):
    OUT = os.path.join(ROOT, "판", 판); os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith((".gcode", ".stl", ".3mf")): os.remove(os.path.join(OUT, f))      # 지난 슬라이스 견적이 섞이지 않게
    풀린 = {}
    for 종류, 이름 in (("machine", "Bambu Lab A1 0.4 nozzle"), ("process", "0.20mm Standard @BBL A1"), ("filament", "Bambu PLA Basic @BBL A1")):
        d = 평탄(종류, 이름)
        if 종류 == "process": d.update(name="0.20mm 트리 @A1", enable_support="1", support_type="tree(auto)", curr_bed_type="Textured PEI Plate")   # CLI 기본은 Cool Plate 35 °C — 우리 판은 텍스처 PEI (09-26 첫 전송에서 잡음)
        풀린[종류] = os.path.join(OUT, "_%s.json" % 종류); json.dump(d, open(풀린[종류], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    눕힘 = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])      # y → −z
    stl = []
    for f in 파일들:
        m = trimesh.load(f, force="mesh")
        if 눕히기: m.apply_transform(눕힘)
        if not 자리: m.apply_translation(-m.bounds[0])
        p = os.path.join(OUT, os.path.basename(f)); m.export(p); stl.append(p)
    설정 = 풀린["machine"] + ";" + 풀린["process"]
    r = subprocess.run([ORCA, "--load-settings", 설정, "--load-filaments", 풀린["filament"],
                        "--arrange", "0" if 자리 else "1", "--orient", "0", "--slice", "0", "--export-3mf", 판 + ".3mf", "--outputdir", OUT] + stl,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    견적 = {"종료코드": r.returncode, "부품": [os.path.basename(p) for p in stl], "줄": []}
    for f in os.listdir(OUT):
        if f.endswith(".gcode"):
            for 줄 in open(os.path.join(OUT, f), encoding="utf-8", errors="replace"):
                if any(k in 줄 for k in ("total estimated time", "model printing time", "filament used [g]", "total filament weight", "enable_support =")) and 줄.startswith(";") and len(줄) < 200:
                    견적["줄"].append(줄.strip("; \n"))
    if r.returncode: 견적["stderr"] = r.stderr[-2000:]
    json.dump(견적, open(os.path.join(OUT, "견적.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(견적, ensure_ascii=False, indent=1)[:3000])

if __name__ == "__main__":
    a = [x for x in sys.argv[2:] if not x.startswith("--")]; main(sys.argv[1], a, 눕히기="--그대로" not in sys.argv, 자리="--자리" in sys.argv)
