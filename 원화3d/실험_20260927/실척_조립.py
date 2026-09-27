# -*- coding: utf-8 -*-
"""조립 고친 EG 한 벌(부품_NN_조립.stl 우선 · 왼쪽은 오른쪽 거울 · 무기 포함)을 실척 ×1.9 로 슬라이스해 시간 · 무게만 본다 (2026-09-27).

    python 실척_조립.py   -> out/키트/EG_RX78/출력/판/EG실척_N/ (3mf · 견적.json) · 조립/실척견적.json
프린터로 보내지 않는다. 눕히기 없음(지역 z = 사진 두께 = 판 수직). 판 넓이 합 ≤ 256² × 0.45 씩 나눈다.
"""
import os, sys, re, json, numpy as np
sys.argv = [sys.argv[0], "후"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "실험_20260925"))
import EG_조립 as A, 출력판
출력판.ROOT = os.path.join(A.KIT, "출력")
낱 = os.path.join(A.KIT, "출력", "실척낱개"); os.makedirs(낱, exist_ok=True)
경로 = []
for k, d in A.부품들.items():
    m = A.P[d["n"]].copy(); m.apply_scale(A.K)
    if d.get("거울"): m.apply_transform(np.diag([-1.0, 1, 1, 1]))
    m.apply_translation(-m.bounds[0]); p = os.path.join(낱, "부품_%02d_%s.stl" % (d["n"], k)); m.export(p); 경로.append((m.extents[0] * m.extents[1], p))
판들, 지금, 넓이 = [], [], 0
for a, p in sorted(경로, reverse=True):
    if 넓이 + a > 256 * 256 * 0.45 and 지금: 판들.append(지금); 지금, 넓이 = [], 0
    지금.append(p); 넓이 += a
판들.append(지금)
합 = []
for i, 판 in enumerate(판들):
    출력판.main("EG실척_%d" % i, 판, 눕히기=False)
    j = json.load(open(os.path.join(출력판.ROOT, "판", "EG실척_%d" % i, "견적.json"), encoding="utf-8")); 합.append(dict(판=i, 부품수=len(판), 종료코드=j["종료코드"], 줄=j["줄"]))
json.dump(dict(부품수=len(경로), 판=합), open(os.path.join(A.OUT, "실척견적.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(합, ensure_ascii=False, indent=1))
