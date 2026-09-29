# -*- coding: utf-8 -*-
"""부품 투영 — 손으로 지어낸 판 다각형(투영.py · 「세그멘테이션이 개판」) 대신 **실제 3D 부품 STL** 을 캡처의 카메라 자세로 찍어 부품 마스크를 만든다.
    python 부품투영.py [판 폴더]  -> out/오메가몬2/지표/부품투영_<캡처>.png (부품 색 · 윤곽) · 부품투영_<캡처>_id.png(부품 번호 그림)
기본 판 = out/오메가몬2/머리/단계4 (6 판). 좌표: 모델 mm → 머리 단위(돔 py 100 = 0 · 턱 py 183 = 100 · 가운데 px 535 · 앞 −y → +z).
투영 = 맞춤.py 가 푼 약원근 자세(r · t · s). 화가 알고리즘(삼각형을 먼 것부터 칠함)으로 z 순서. 프레임 · 속머리(검정)는 그리지 않는다.
"""
import os, sys, json, glob
import numpy as np, cv2, trimesh
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))); import 공통
from 자세 import 캡처 as 캡처2D
읽기 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
F = json.load(open(J(OUT, "랜드마크3D.json"), encoding="utf-8"))
k = 0.349; 머리mm = 83 * k; cx_mm, top_mm = 공통.X(535), 공통.Z(100)
def 단위(V):
    """모델 mm (x 오른쪽 · y 뒤 + · z 위 +) → 머리 단위 (x 오른쪽 · y 아래 · z 앞)"""
    return np.stack([(V[:, 0] - cx_mm) / 머리mm * 100, (top_mm - V[:, 2]) / 머리mm * 100, -V[:, 1] / 머리mm * 100], 1)
def 찍기(U, 자):
    R, _ = cv2.Rodrigues(np.asarray(자["r"], float)); C = (U * (1, 1, -1)) @ R.T; return 자["s"] * C[:, :2] + np.asarray(자["t"]), C[:, 2]
if __name__ == "__main__":
    D = sys.argv[1] if len(sys.argv) > 1 else J(OUT, "..", "머리", "단계4"); ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 15)
    부품 = [(os.path.basename(f)[:-4], trimesh.load(f, process=False)) for f in sorted(glob.glob(J(D, "*.stl"))) if os.path.basename(f) not in ("프레임.stl",)]
    rng = np.random.RandomState(11); 색 = {n: tuple(int(c) for c in rng.randint(70, 240, 3)) for n, _ in 부품}
    for 이름, (f, _) in 캡처2D.items():
        자 = F["자세"][이름]; im = 읽기(J(장면, f)); H, W = im.shape[:2]; ID = np.zeros((H, W), np.int32); 삼 = []
        for i, (n, m) in enumerate(부품, 1):
            uv, z = 찍기(단위(np.asarray(m.vertices, float)), 자)
            for tri in m.faces: 삼.append((z[tri].mean(), i, uv[tri]))
        삼.sort(key=lambda t: -t[0])                                        # 카메라 z 큰 것(먼 것)부터
        for _, i, p in 삼: cv2.fillPoly(ID, [np.round(p).astype(np.int32)], int(i))
        ov = im.copy()
        for i, (n, _) in enumerate(부품, 1): ov[ID == i] = 색[n][::-1]
        vis = cv2.addWeighted(im, 0.45, ov, 0.55, 0)
        경계 = (cv2.Laplacian(ID.astype(np.float32), cv2.CV_32F) != 0); vis[경계] = (255, 255, 255)
        pil = Image.fromarray(vis[:, :, ::-1]); d = ImageDraw.Draw(pil)
        for i, (n, _) in enumerate(부품, 1):
            ys, xs = np.nonzero(ID == i)
            if len(xs) > 150: d.text((xs.mean() - 12, ys.mean() - 8), n, font=ft, fill=(0, 0, 0), stroke_width=2, stroke_fill=(255, 255, 255))
        p = J(OUT, "부품투영_%s.png" % 이름.replace("/", "-").replace(" ", "_")); pil.save(p); cv2.imencode(".png", ID.astype(np.uint8))[1].tofile(p[:-4] + "_id.png")
        print(p, "부품", len(부품), "보이는 부품", len(set(ID[ID > 0].tolist())))
