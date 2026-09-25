# -*- coding: utf-8 -*-
"""PG 디자인 판 전체(장갑 3 블록 + 뼈 + 관절 부품)를 부품 속 보기 HTML 로 (2026-09-26).

    python PG보기.py  ->  out/부품속_PG디자인.html  (설계/부품속.src.html 템플릿 · __DATA__ 치환)

층: 장갑(블록 색) · 뼈(파랑) · 관절(회색). 벌림 방향 = 몸 중심에서 부품 중심으로.
삼각형은 부품마다 6000 이하로 줄여 16 MB 아래로."""
import base64, glob, json, os, sys
import numpy as np, trimesh
sys.path.insert(0, r"G:\art2real\원화3d")
import hull as H  # noqa

ROOT = r"G:\art2real\원화3d\out\출력\오메가몬_PG"
색표 = {"몸통": "#e8590c", "다리": "#ae3ec9", "머리어깨": "#1c7ed6", "뼈": "#4c6ef5", "관절": "#9a9a92"}

def 읽기(p, 최대=2200):
    m = trimesh.load(p, force="mesh", process=False)
    닫힘 = bool(trimesh.load(p, force="mesh").is_watertight)
    if len(m.faces) > 최대:
        try:
            s = m.simplify_quadric_decimation(face_count=최대)
            if len(s.faces) > 0: m = s
        except Exception: pass
    return m, 닫힘

데, 전체 = [], []
목록 = []
for 블록 in ("몸통", "다리", "머리어깨"):
    for p in sorted(glob.glob(os.path.join(ROOT, "디자인", 블록, "*.stl"))):
        목록.append((블록, os.path.basename(p)[:-4], p, "장갑"))
for p in sorted(glob.glob(r"G:\art2real\원화3d\out\가동\프레임\*.stl")):
    목록.append(("뼈", os.path.basename(p)[:-4], p, "뼈"))
for p in sorted(glob.glob(r"G:\art2real\원화3d\out\가동\관절배치\관절_*.stl")):
    목록.append(("관절", os.path.basename(p)[3:-4], p, "관절"))

메시 = []
for 블록, 이름, p, 종류 in 목록:
    try: m, 닫힘 = 읽기(p, 2200 if 종류 == "장갑" else 900)
    except Exception as e: print("  못 읽음", 이름, e); continue
    메시.append((블록, 이름, 종류, m, 닫힘))
중심 = np.mean([m.bounds.mean(0) for *_, m, _ in 메시], axis=0)
for 블록, 이름, 종류, m, 닫힘 in 메시:
    m = m.copy(); m.apply_translation(-중심)
    c = m.bounds.mean(0); d = c / max(np.linalg.norm(c), 1e-6)
    부품이름 = 이름.replace("_", " ")
    데.append({"부품": 블록 if 종류 != "장갑" else 이름, "조각": (블록 + " · " if 종류 != "장갑" else "") + 부품이름,
               "블록": 블록, "종류": "관절" if 종류 == "관절" else ("뼈" if 종류 == "뼈" else "통"),
               "벌림": [float(x) for x in d] if 종류 == "장갑" else None,
               "색": 색표[블록], "치수": [round(float(x), 1) for x in m.extents], "닫힘": 닫힘,
               "부피": round(float(abs(m.volume)) / 1000, 2),
               "v": base64.b64encode(m.vertices.astype(np.float32).tobytes()).decode(),
               "f": base64.b64encode(m.faces.astype(np.uint32).tobytes()).decode()})
n장갑 = sum(1 for x in 데 if x["블록"] in 색표 and x["블록"] not in ("뼈", "관절"))
print("장갑 %d · 뼈 %d · 관절 %d · 닫힘 %d/%d · 삼각형 %d" % (
    n장갑, sum(1 for x in 데 if x["블록"] == "뼈"), sum(1 for x in 데 if x["블록"] == "관절"),
    sum(x["닫힘"] for x in 데), len(데), sum(len(m.faces) for *_, m, _ in 메시)))
t = open(r"G:\art2real\원화3d\설계\부품속.src.html", encoding="utf-8").read()
t = t.replace("<title>오메가몬 부품 속</title>", "<title>오메가몬 PG 디자인 판</title>")
t = t.replace("부품 속 — 오메가몬", "오메가몬 PG 디자인 판 · 3바퀴")
t = t.replace("색 = 블록 · 회색 = 관절 부품(볼 · 폴리캡 · 플러그) · 반쪽은 속이 빈 컵(벽 1.2 mm)이고 속 기둥(보스) 두 개 — 한쪽 보스에 핀, 다른 쪽에 구멍 · 전고 125 mm",
              "주황 = 몸통 · 보라 = 다리 · 파랑 = 머리어깨 · 남색 = 뼈 · 회색 = 관절 부품 · 벽 2 mm 껍질 · 전고 300 mm · 관절 32 · 아직 원화 디테일 25~40% 빠짐")
t = t.replace("__DATA__", json.dumps(데, ensure_ascii=False))
out = os.path.join(H.OUT, "부품속_PG디자인.html"); open(out, "w", encoding="utf-8").write(t)
print(out, "%.1f MB" % (os.path.getsize(out) / 2 ** 20))
