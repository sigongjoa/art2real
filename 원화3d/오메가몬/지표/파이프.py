# -*- coding: utf-8 -*-
"""한 장 파이프라인 — 그 장의 ROI(실루엣) → 선 → 면 → 판 1 단계, 전부 **그 장의 자세**로 (09-29 「각도가 다른데 이전 이미지에 맞추려 하니 안 되잖아 · ROI 다시 따서 파이프라인 다시 돌려야지」).
    python 파이프.py "3/4 M04"  -> out/오메가몬2/지표/파이프_<장>_{실루엣,영역}.png · 영역_<장>.npz · 판/<장>/*.stl · 파이프_<장>_판.png(자기 장에 항등 겹침)
실루엣 = 자세2.씨앗실루엣(6 판 투영 씨앗 GrabCut) · 선 · 면 = 선화 · 영역 · 판 = 판1단계(면 → 그 장 카메라와 나란한 평판, 이름은 그 장의 부품투영 겹침).
장마다 따로 판이 나온다. 장끼리 합치는 건 다음 단계(같은 이름 판끼리 평면 맞춤).
"""
import os, sys, json, glob
import numpy as np, cv2, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
from 자세 import 캡처 as 캡처2D
import 자세2, 영역 as 영역모듈, 판1단계 as P
from 부품투영 import 단위, 찍기 as 찍기N, 읽기
def 돌리기(n):
    태그 = n.replace("/", "-").replace(" ", "_"); f, _ = 캡처2D[n]; im = 읽기(J(장면, f)); 자 = P.자세[n]
    p0 = 자세2.초기(n); full = 자세2.씨앗실루엣(im, p0)                                   # 1 ROI
    im3, 라벨, 선, 검면 = 영역모듈.영역(im, full); ids = [i for i in np.unique(라벨) if i > 0]     # 2 선 → 3 면
    np.savez_compressed(J(OUT, "영역_%s.npz" % 태그), 라벨=라벨)
    rng = np.random.RandomState(5); 면 = np.full(im3.shape, 255, np.uint8)
    for i in ids: 면[라벨 == i] = tuple(int(c) for c in rng.randint(60, 240, 3))
    면[라벨 == -1] = (30, 30, 30); 면[선 & (라벨 != 0)] = (0, 0, 0); cv2.imencode(".png", cv2.addWeighted(im3, 0.4, 면, 0.6, 0))[1].tofile(J(OUT, "파이프_%s_영역.png" % 태그))
    # 4 판: 이름은 이 장의 부품투영 id 지도(새 자세로 다시 만든 것)
    ID = cv2.imdecode(np.fromfile(J(OUT, "부품투영_%s_id.png" % 태그), np.uint8), cv2.IMREAD_GRAYSCALE); H, W = ID.shape
    라벨1 = cv2.resize(라벨.astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST).astype(np.int32)
    DO = J(OUT, "판", 태그); os.makedirs(DO, exist_ok=True); [os.remove(g) for g in glob.glob(J(DO, "*.stl"))]; 기록 = []; 셈 = {}
    for i in ids:
        m = (라벨1 == i); a = int(m.sum())
        if a < P.최소: continue
        v = ID[m]; v = v[v > 0]
        if v.size < 0.5 * a: continue
        pid = int(np.bincount(v).argmax()); pname = P.이름표[pid - 1]
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); c = max(cs, key=cv2.contourArea); poly = cv2.approxPolyDP(c, 1.2, True).reshape(-1, 2)
        if len(poly) < 3: continue
        셈[pname] = 셈.get(pname, 0) + 1; nm = "%s_%d" % (pname, 셈[pname]); mesh = P.평판(poly, P.카메라깊이(pid, ID, 자), 자)
        mm_ = mesh.to_mesh(); V = P.mm(np.array(mm_.vert_properties)[:, :3]); trimesh.Trimesh(V, np.array(mm_.tri_verts)[:, ::-1], process=False).export(J(DO, nm + ".stl")); 기록.append(dict(이름=nm, 면=int(i), 넓이px=a, 부품=pname))
    json.dump(기록, open(J(OUT, "파이프_%s_판.json" % 태그), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ov = im.copy(); rng = np.random.RandomState(9)
    for r in 기록:
        t = trimesh.load(J(DO, r["이름"] + ".stl"), process=False, force="mesh"); uv, z = 찍기N(단위(np.asarray(t.vertices, float)), 자); c = tuple(int(x) for x in rng.randint(60, 240, 3))
        for tri in t.faces: cv2.fillPoly(ov, [np.round(uv[tri]).astype(np.int32)], c)
    cv2.imencode(".png", cv2.addWeighted(im, 0.5, ov, 0.5, 0))[1].tofile(J(OUT, "파이프_%s_판.png" % 태그)); print(n, "면", len(ids), "판", len(기록), "→", DO)
if __name__ == "__main__":
    for n in (sys.argv[1:] or ["3/4 M04"]): 돌리기(n)
