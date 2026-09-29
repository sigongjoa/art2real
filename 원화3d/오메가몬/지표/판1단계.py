# -*- coding: utf-8 -*-
"""판 1 단계 — 캡처 면(영역.py)을 키트 부품 사진처럼 다뤄 실루엣 평판으로 짓는다 (09-27 전부품.py 방식 · 09-29 「건담 파츠 방식 응용」).
    python 판1단계.py -> out/오메가몬2/판/정면/<이름>.stl (mm · 6 판 부품과 같은 좌표) · 판1단계_정면.png(정면 겹침) · 판1단계_3-4.png(held-out 3/4 에 투영) · 판1단계.json
방법: 정면 면 → 다각형(px) → 6 판 부품 투영과 겹침으로 이름 · 정면향 부품만 남김 → 그 부품의 카메라 깊이에 **화면과 나란한 평판**(두께 3 단위)으로 놓고 자세 역변환으로 모델 좌표로.
1 단계는 키트 때처럼 「실루엣을 민 평판」이다. 기울기 · 두께 · 오목은 2 단계(하위 도형).
"""
import os, sys, json, glob
import numpy as np, cv2, trimesh, manifold3d as M
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
from 부품투영 import 단위, 찍기 as 찍기N, 머리mm, cx_mm, top_mm, 읽기
F = json.load(open(J(OUT, "랜드마크3D.json"), encoding="utf-8")); 자세 = F["자세"]
정면향 = ("눈썹", "눈구멍", "코", "부리2", "부리3", "번개", "뿔", "홍채", "동공"); 두께 = 3.0; 최소 = 300
D6 = J(OUT, "..", "머리", "단계4"); 이름표 = [os.path.basename(f)[:-4] for f in sorted(glob.glob(J(D6, "*.stl"))) if os.path.basename(f) != "프레임.stl"]
def mm(U): return np.stack([U[:, 0] / 100 * 머리mm + cx_mm, -U[:, 2] / 100 * 머리mm, top_mm - U[:, 1] / 100 * 머리mm], 1)
def 카메라깊이(부품id, ID, 자):
    """6 판 부품의 카메라 z (단위): 그 부품 STL 꼭짓점을 자세로 찍은 z 의 중앙값"""
    m = trimesh.load(J(D6, 이름표[부품id - 1] + ".stl"), process=False); _, z = 찍기N(단위(np.asarray(m.vertices, float)), 자); return float(np.median(z))
def 평판(poly_px, z_cam, 자):
    """정면 px 다각형 → 카메라 좌표(단위)에서 z_cam 에 놓인 평판 → 모델 좌표(단위)"""
    R, _ = cv2.Rodrigues(np.asarray(자["r"], float)); s = 자["s"]; t = np.asarray(자["t"])
    c2 = (np.asarray(poly_px, float) - t) / s; cs = M.CrossSection([c2.tolist()])
    if cs.area() <= 0: cs = M.CrossSection([c2[::-1].tolist()])            # 시계 방향이면 빈 단면이 된다(면적 0) → 뒤집는다
    m = cs.extrude(두께).translate([0, 0, z_cam - 두께 / 2]); T = np.zeros((3, 4)); T[:, :3] = R.T; m = m.transform(T)    # 카메라 → 모델(X̃)
    return m.transform(np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0]], float))                              # X̃ → X (z 뒤집기)
if __name__ == "__main__":
    n = "정면 yt_172"; 자 = 자세[n]; 라벨 = np.load(J(OUT, "영역_정면.npz"))["라벨"]; ID = cv2.imdecode(np.fromfile(J(OUT, "부품투영_정면_yt_172_id.png"), np.uint8), cv2.IMREAD_GRAYSCALE)
    im = 읽기(J(장면, "yt_172.0_얼굴_정면.jpg")); H, W = ID.shape; 라벨1 = cv2.resize(라벨.astype(np.int32).astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST).astype(np.int32)
    DO = J(OUT, "판", "정면"); os.makedirs(DO, exist_ok=True); [os.remove(f) for f in glob.glob(J(DO, "*.stl"))]; 기록 = []; 셈 = {}
    for i in [v for v in np.unique(라벨1) if v > 0]:
        m = (라벨1 == i); a = int(m.sum())
        if a < 최소: continue
        ids = ID[m]; ids = ids[ids > 0]
        if ids.size < 0.5 * a: continue
        pid = int(np.bincount(ids).argmax()); pname = 이름표[pid - 1]
        if not pname.startswith(정면향): continue
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); c = max(cs, key=cv2.contourArea); poly = cv2.approxPolyDP(c, 1.2, True).reshape(-1, 2)
        if len(poly) < 3: continue
        셈[pname] = 셈.get(pname, 0) + 1; nm = "%s_%d" % (pname, 셈[pname]); mesh = 평판(poly, 카메라깊이(pid, ID, 자), 자)
        mm_ = mesh.to_mesh(); V = mm(np.array(mm_.vert_properties)[:, :3]); Fc = np.array(mm_.tri_verts)[:, ::-1]; trimesh.Trimesh(V, Fc, process=False).export(J(DO, nm + ".stl"))   # z 뒤집기(행렬식 −1)로 면이 안쪽을 보므로 삼각형 순서를 되돌린다
        기록.append(dict(이름=nm, 면=int(i), 넓이px=a, 꼭짓점=len(poly), 부품=pname));
    print("판", len(기록), "→", DO); json.dump(기록, open(J(OUT, "판1단계.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 겹침 그림: 정면(항등) · 3/4(held-out)
    from 자세 import 캡처 as 캡처2D
    rng = np.random.RandomState(9); 색 = {r["이름"]: tuple(int(c) for c in rng.randint(60, 240, 3)) for r in 기록}
    for 장이름, 파일, out in (("정면 yt_172", "yt_172.0_얼굴_정면.jpg", "판1단계_정면.png"), ("3/4 M04", "wk_Omegamon_M04.jpg", "판1단계_3-4.png")):
        자2 = 자세[장이름]; im = 읽기(J(장면, 파일)); ov = im.copy()
        for r in 기록:
            t = trimesh.load(J(DO, r["이름"] + ".stl"), process=False, force="mesh"); uv, z = 찍기N(단위(np.asarray(t.vertices, float)), 자2)
            for tri in t.faces: cv2.fillPoly(ov, [np.round(uv[tri]).astype(np.int32)], 색[r["이름"]])
        vis = cv2.addWeighted(im, 0.5, ov, 0.5, 0); cv2.imencode(".png", vis)[1].tofile(J(OUT, out)); print(J(OUT, out))
