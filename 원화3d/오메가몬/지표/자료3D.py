# -*- coding: utf-8 -*-
"""자료 3D 1 단계 — 캡처 자료만으로(우리 모델 없음): 정면 면 33 개 = 판 33 개(키트 1 단계 · 실루엣 평판) · 깊이 = 옆 실루엣의 앞 윤곽 (09-29 「3d ㄱㄱ」).
    python 자료3D.py -> out/오메가몬2/자료/3D/<번호>.stl (머리 높이 100 단위 · x 오른쪽 · y 아래 · z 앞) · 자료3D.png (정면 · 3/4 · 옆 렌더, 판 색 = 자료영역 색) · 자료3D.json
깊이 규칙: 정면 판의 꼭짓점 (x, y) → z = 옆 실루엣 앞 윤곽 z_front(y) (같은 높이에서 가장 앞). 판은 두께 3 단위로 뒤로. 옆 실루엣의 목(y > 100)은 뺀다.
한계: 판마다 깊이가 y 만의 함수라 좌우로 기운 판(볼 날개)은 아직 평평 · 뒤통수 없음 · 옆에서만 보이는 판 없음.
"""
import os, sys, json
import numpy as np, cv2, trimesh, manifold3d as M
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
D = J(OUT, "..", "자료"); D3 = J(D, "3D"); os.makedirs(D3, exist_ok=True); 기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); S = 3; 두께 = 3.0
읽기 = lambda p, f=cv2.IMREAD_COLOR: cv2.imdecode(np.fromfile(p, np.uint8), f)
def 틀(sil):
    ys, xs = np.nonzero(sil); return ys.min(), ys.max(), (xs.min() + xs.max()) / 2
def 앞윤곽(태그):
    """옆 실루엣 → y(단위 0..100) 마다 가장 앞 x(단위 · 앞 = 그림 왼쪽이면 음수 x 가 앞). 반환: z_front(y) 보간 함수 (z 앞 +)."""
    sil = 읽기(J(D, 태그 + "_실루엣.png"), cv2.IMREAD_GRAYSCALE) > 0; y0, y1, cx = 틀(sil); h = y1 - y0
    ys = np.arange(y0, y1 + 1); front = np.array([np.nonzero(sil[y])[0].min() for y in ys], float)      # 옆 캡처는 코가 왼쪽 → 가장 앞 = 최소 x
    z = (cx - front) / h * 100; u = (ys - y0) / h * 100                                                  # 가운데 x 기준 앞쪽 거리(단위)
    return lambda yy: float(np.interp(yy, u, z))
if __name__ == "__main__":
    n = "02_정면"; 라벨 = np.load(J(D, n + "_영역.npz"))["라벨"]; sil = 읽기(J(D, n + "_실루엣.png"), cv2.IMREAD_GRAYSCALE) > 0; y0, y1, cx = 틀(sil); h = y1 - y0
    zf = 앞윤곽("02_옆"); ids = [i for i in np.unique(라벨) if i > 0]; rng = np.random.RandomState(5); 색 = {i: tuple(int(x) for x in rng.randint(60, 240, 3)) for i in ids}
    부품 = {}; 표 = {}
    for i in ids:
        m = (라벨 == i).astype(np.uint8); cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); c = max(cs, key=cv2.contourArea); poly = cv2.approxPolyDP(c, 1.5, True).reshape(-1, 2).astype(float)
        if len(poly) < 3: continue
        P = np.stack([(poly[:, 0] / S - cx) / h * 100, (poly[:, 1] / S - y0) / h * 100], 1)               # px(3 배) → 단위
        if P[:, 1].max() > 108 or P[:, 1].min() < -5: continue                                            # 목 · 깃(머리 밖)은 뺀다
        cs_ = M.CrossSection([P.tolist()]); cs_ = cs_ if cs_.area() > 0 else M.CrossSection([P[::-1].tolist()])
        if cs_.area() < 1: continue
        mesh = cs_.extrude(두께).warp(lambda v: [v[0], v[1], v[2] + zf(v[1]) - 두께])                   # 판을 앞 윤곽 깊이에 얹고 뒤로 두께만큼
        mm_ = mesh.to_mesh(); V = np.array(mm_.vert_properties)[:, :3]; F = np.array(mm_.tri_verts)
        t = trimesh.Trimesh(V, F, process=False)
        if t.volume < 0: t.invert()
        t.export(J(D3, "%02d.stl" % i)); 부품[i] = t; 표[int(i)] = dict(꼭짓점=len(P), 깊이=round(zf(float(P[:, 1].mean())), 1), 넓이=round(float(cs_.area()), 1))
    print("판", len(부품), "· 닫힘", all(t.is_watertight for t in 부품.values()))
    # 렌더: 정면 · 3/4(yaw −35°) · 옆(yaw −90°) 정사영 · 화가 알고리즘
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 22); 판들 = []
    for 이름, yaw in (("정면", 0), ("3/4", -35), ("옆", -90)):
        th = np.radians(yaw); R = np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]]); W, H, s = 700, 700, 5.0; 삼 = []
        for i, t in 부품.items():
            V = np.asarray(t.vertices) @ R.T; uv = np.stack([V[:, 0] * s + W / 2, V[:, 1] * s + 60], 1); z = V[:, 2]
            for tri in t.faces: 삼.append((z[tri].mean(), i, uv[tri]))
        삼.sort(key=lambda a: a[0]); im = np.full((H, W, 3), 245, np.uint8)                                # z 앞 + → 작은 z(뒤)부터
        for _, i, q in 삼: cv2.fillPoly(im, [np.round(q).astype(np.int32)], 색[i][::-1])
        ID = np.zeros((H, W), np.int32)
        for _, i, q in 삼: cv2.fillPoly(ID, [np.round(q).astype(np.int32)], int(i))
        im[cv2.Laplacian(ID.astype(np.float32), cv2.CV_32F) != 0] = (0, 0, 0)
        p = Image.fromarray(im[:, :, ::-1]); ImageDraw.Draw(p).text((8, 6), "자료 3D 1단계 · %s (yaw %d°)" % (이름, yaw), font=ft, fill=(0, 0, 0)); 판들.append(p)
    캡 = Image.open(J(D, "자료영역_셋.png")).convert("RGB"); 캡 = 캡.crop((0, 0, 캡.width // 2, 캡.height // 3)); 캡 = 캡.resize((int(캡.width * 700 / 캡.height), 700))
    시트 = Image.new("RGB", (캡.width + sum(p.width for p in 판들) + 40, 700), (250, 250, 248)); 시트.paste(캡, (0, 0)); x = 캡.width + 10
    for p in 판들: 시트.paste(p, (x, 0)); x += p.width + 10
    시트.save(J(D, "자료3D.png")); json.dump(표, open(J(D, "자료3D.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(J(D, "자료3D.png"))
