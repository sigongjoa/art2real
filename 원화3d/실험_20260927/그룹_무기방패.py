# -*- coding: utf-8 -*-
"""EG RX-78-2 2 단계(하위 도형 분해) — 무기 · 방패 묶음: 부품 3(흰 방패 뒤판) · 4(빨강 앞판) · 25(노랑 십자) · 37 · 38(회색 라이플 반쪽 둘) (2026-09-27).

    python 그룹_무기방패.py
      -> out/키트/EG_RX78/2단계/부품_03·04·25·37·38.stl · 갤러리_무기방패.png · 무기방패.json

치수 출처: d_egx01_j1.jpg 를 0.17 mm/px 로 확대 · mm 격자에 대고 눈으로 읽음(흰 판은 4.8° 돌려 세움). 4 는 방패.py 의 짓기()를 35/70 로 줄여 그대로 씀.
좌표(방패 셋 공통 · 조립 상태): X 좌우 · Y 길이(좁은 끝 0 → 창 끝) · Z 앞(+, 빨강 쪽) / 뒤(−).
좌표(라이플 둘 공통 · 조립 상태): X 축(뒤 0 → 총구) · Y 위(+) · Z 폭 — 37 은 Z ≥ 0, 38 은 Z ≤ 0 (사진은 둘 다 바깥 면).
깊이(Z)는 사진에 없다 — 아래 「가정」 값은 설명서 등각도 · 완성 사진 04/05 눈대중."""
import os, sys, json, numpy as np, trimesh, manifold3d as M
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260925")
import 방패 as B
import 디테일대조 as DD
from 메시출력 import 부채나누기

D = r"G:\art2real\원화3d\out\키트\EG_RX78"; OUT = os.path.join(D, "2단계"); os.makedirs(OUT, exist_ok=True)
MM = 0.17
글꼴 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 15)
가정 = dict(흰판두께=0.8, 테두리높이=1.0, 테두리안쪽들임=0.4, 빨강틈=0.15, 뒤고원깊이=0.8, 고원꺾임x=5.0, 고원가장자리올림=0.6,
          등뼈높이=2.0, 등뼈윗블록높이=3.0, 핀반지름=0.5, 핀틈=0.1, 십자바닥=0.35, 십자능선=0.75, 라이플반폭=1.8, 손잡이반폭=1.1)
G = 가정

# ---------- 도형 도우미 ----------
def 판(poly, z0, z1): return B.기둥z(np.asarray(poly, float), min(z0, z1), max(z0, z1))
def 상자(x0, y0, x1, y1, z0, z1): return 판([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)
def 대칭(반): P = np.asarray(반, float); return np.vstack([P, (P * [-1, 1])[::-1]])
def 들임(poly, d): return np.asarray(M.CrossSection([B.반시계(poly).tolist()]).offset(-d, M.JoinType.Miter).to_polygons()[0])
def 모따기(p0, z0, p1, z1): return M.Manifold.hull_points(np.array([(x, y, z0) for x, y in p0] + [(x, y, z1) for x, y in p1], float))
def 둥근네모(x0, y0, x1, y1, r, z0, z1):
    return M.CrossSection.square([x1 - x0 - 2 * r, y1 - y0 - 2 * r]).translate([x0 + r, y0 + r]).offset(r, M.JoinType.Round, 2.0, 24).extrude(z1 - z0).translate([0, 0, z0])
def 축원뿔(x0, x1, r0, r1, y=0.0, z=0.0, n=40):
    """X 축 방향 원뿔대 (라이플 좌표)."""
    return M.Manifold.cylinder(x1 - x0, r0, r1, n).rotate([0, 90, 0]).translate([x0, y, z])
def 반공간Z(양):  # Z ≥ 0 (양=True) 또는 Z ≤ 0
    return M.Manifold.cube([200, 200, 100]).translate([-100, -100, 0 if 양 else -100])

# ---------- 4 빨강 앞판 (방패.py 그대로 · 35/70 로 축소 · 창을 흰 판 창에 맞춰 Y 로 민다) ----------
빨강길이 = 35.0                                         # j1 상자 206 px × 0.17
빨강Y = 2.85                                            # 두 창 중심을 맞춘 값: 흰 창 중심 Y 34.95 − 빨강 창 중심 0.9175 × 35
def 빨강():
    m, P = B.짓기(); k = 빨강길이 / B.L
    m = m.scale([k, k, k]); dz = 0.05 - m.bounding_box()[2]      # 가장 낮은 곳(옆 면 가장자리)이 흰 바닥 0.05 위
    윤곽 = np.vstack([P, (P * [-1, 1])[::-1]]) * 빨강길이 + [0, 빨강Y]
    return m.translate([0, 빨강Y, dz]), 윤곽

# ---------- 3 흰 뒤판 ----------
# 바깥 윤곽(반폭, Y): 사진 g03r — 윗 모서리 y 4.8 반폭 5.0 · 가장 넓은 곳 y 17.5 반폭 8.4 · 좁은 끝 y 42.5 반폭 5.0 → Y = 42.5 − y
흰윤곽 = 대칭([(5.0, 37.7), (8.4, 25.0), (5.0, 0.0)])
def 흰판(빨윤곽, 빨mesh):
    t = G["흰판두께"]
    바닥 = 판(흰윤곽, -t, 0) + 상자(-4.3, 37.0, 4.3, 39.8, -1.5, G["테두리높이"])            # ① 바닥판 + 윗 탭(빨강 윗 끝을 덮는 턱)
    # ② 앞 테두리 벽: 바깥은 모따기 · 안은 빨강 윤곽 + 틈 → 빨강이 꼭 들어간다
    주머니 = M.CrossSection([B.반시계(빨윤곽).tolist()]).offset(G["빨강틈"], M.JoinType.Miter).extrude(10).translate([0, 0, 0])
    테 = 모따기(흰윤곽, 0, 들임(흰윤곽, G["테두리안쪽들임"]), G["테두리높이"]) - 주머니
    바닥 = 바닥 - 주머니
    # ③ 뒤 고원: 바깥 0.9 들인 모따기 판 ∩ 꺾임 쐐기(|x| < 5 평평 · 바깥으로 올라감 — 빨강 앞판의 꺾임과 같은 문법)
    zp = -t - G["뒤고원깊이"]; 기울 = G["고원가장자리올림"] / 3.0
    고원 = 모따기(들임(흰윤곽, 0.9), -t + 0.01, 들임(흰윤곽, 1.6), zp)
    a = G["고원꺾임x"]; 쐐기 = M.CrossSection([B.반시계(np.array([(-12, zp + 기울 * 7), (-a, zp), (a, zp), (12, zp + 기울 * 7), (12, 0), (-12, 0)])).tolist()])
    고원 = 고원 ^ 쐐기.extrude(60).rotate([90, 0, 0]).translate([0, 55, 0])
    # ④ 창 틀(뒤로 0.4 솟은 둥근 네모 테) + 창 구멍(관통)
    창틀 = 둥근네모(-4.0, 32.8, 4.0, 36.9, 0.8, zp - 0.4, zp + 0.1)
    창 = 둥근네모(-2.55, 33.7, 2.55, 36.2, 0.4, -10, 10)
    # ⑤ 등뼈: 낮은 상자 + 윗 블록 + 팔 연결 핀 · 손잡이 구멍
    등 = 상자(-1.5, 18.0, 1.5, 31.3, zp + 0.2, zp - G["등뼈높이"]) + 상자(-1.5, 25.0, 1.5, 31.3, zp + 0.2, zp - G["등뼈윗블록높이"])
    등 += M.Manifold.cylinder(0.9, 0.7, 0.7, 32).translate([0, 28.8, zp - G["등뼈윗블록높이"] - 0.8])
    등 -= 상자(-0.8, 19.5, 0.8, 23.0, zp - G["등뼈높이"] - 1, zp - G["등뼈높이"] + 1.0)
    # ⑥ 혀: 등뼈 아래로 가늘어지며 낮아지는 판(hull)
    혀 = M.Manifold.hull_points(np.array([(sx * 1.5, 16.0, zp + 0.2) for sx in (-1, 1)] + [(sx * 1.5, 16.0, zp - 1.0) for sx in (-1, 1)] +
                                          [(sx * 1.3, 7.0, zp + 0.2) for sx in (-1, 1)] + [(sx * 1.3, 7.0, zp - 0.3) for sx in (-1, 1)], float))
    # ⑦ 좁은 끝 블록 + 가운데 홈
    끝 = 상자(-3.8, 0.3, 3.8, 3.6, -t + 0.01, zp - 0.3) - 상자(-0.3, 2.2, 0.3, 3.0, zp - 1, zp + 0.05)
    # ⑧ 가로 패널선 두 줄 · 둥근 자국 여섯
    선 = [상자(sx * 1.5, y0, sx * 6.8, y0 + 0.25, zp - 1, zp + 0.2) for sx in (-1, 1) for y0 in (22.8, 25.1)]
    자국 = [M.Manifold.cylinder(0.3, 0.4, 0.4, 20).translate([sx * x, y, zp - 0.15]) for sx in (-1, 1) for x, y in ((3.1, 31.9), (3.9, 23.9), (2.6, 5.3))]
    m = 바닥 + 테 + 고원 + 창틀 + 등 + 혀 + 끝 + M.Manifold.batch_boolean(자국, M.OpType.Add)
    m = m - M.Manifold.batch_boolean(선, M.OpType.Add) - 창
    # ⑨ 앞 핀 넷: 위 둘은 빨강 앞판 보스(방패.py ±0.128 L · v 0.805) 바로 밑 · 아래 둘은 뒤 둥근 자국 자리. 높이는 빨강 밑면까지 − 틈
    핀자리 = [(sx * 0.128 * 빨강길이, 빨강Y + 0.805 * 빨강길이) for sx in (-1, 1)] + [(sx * 2.6, 5.3) for sx in (-1, 1)]
    밑면 = 빨mesh.ray.intersects_location(np.array([(x, y, -5.0) for x, y in 핀자리]), np.tile([0, 0, 1.0], (4, 1)))
    핀정보 = []
    for i, (x, y) in enumerate(핀자리):
        zs = 밑면[0][밑면[1] == i][:, 2]; z밑 = float(zs.min()) if len(zs) else 1.0
        h = z밑 - G["핀틈"]; m = m + M.Manifold.cylinder(h + 0.2, G["핀반지름"], G["핀반지름"] * 0.85, 24).translate([x, y, -0.2])
        핀정보.append(dict(x=round(x, 2), y=round(y, 2), 빨강밑면z=round(z밑, 2), 핀높이=round(h, 2)))
    return m, 핀정보

# ---------- 25 노랑 십자 ----------
def 팔(방향, 길이, w0, w1):
    """중심에서 방향(단위 2D)으로 가늘어지는 능선 팔: 바닥 네모 → 능선 한 줄 (hull)."""
    d = np.array(방향, float); n = np.array([-d[1], d[0]]); b, r = G["십자바닥"], G["십자능선"]
    pts = []
    for s in (-1, 1):
        pts += [(*(s * n * w0 / 2), 0), (*(s * n * w0 / 2), b), (*(d * 길이 + s * n * w1 / 2), 0), (*(d * 길이 + s * n * w1 / 2), b * 0.8)]
    pts += [(0, 0, r), (*(d * 길이), r * 0.6), (*(d * (길이 + w1 * 0.6)), b * 0.5), (*(d * (길이 + w1 * 0.6)), 0)]
    return M.Manifold.hull_points(np.array(pts, float))
def 십자():
    # 사진 g25: 중심에서 위 7.7 · 아래 12.3(맨 끝 0.5 는 게이트 자국으로 봄) · 좌우 3.75 · 세로 팔 폭 1.5 → 0.7 · 가로 팔 1.3 → 0.45
    m = 팔((0, 1), 7.7, 1.5, 0.7) + 팔((0, -1), 12.3, 1.5, 0.7) + 팔((1, 0), 3.75, 1.3, 0.45) + 팔((-1, 0), 3.75, 1.3, 0.45)
    m += M.Manifold.hull_points(np.array([(1.0, 0, 0), (-1.0, 0, 0), (0, 1.1, 0), (0, -1.1, 0), (0.9, 0, 0.3), (-0.9, 0, 0.3), (0, 1.0, 0.3), (0, -1.0, 0.3), (0, 0, 0.95)], float))   # 가운데 마름모
    m += 상자(-0.2, 3.8, 0.2, 4.2, -0.3, 0.05) + 상자(-0.2, -6.2, 0.2, -5.8, -0.3, 0.05)      # 빨강 십자 홈에 꽂히는 핀 둘 (0.4 각 · 홈 폭 0.455)
    return m

# ---------- 37 · 38 라이플 반쪽 ----------
# 사진 좌표(x, y mm · 부품 상자 왼위 기준) → 라이플 좌표. 38: X = y, Y = 4.55 − x. 37(뒤집힌 짝): X = y + 1.2, Y = x − 4.6 (총열 축 · 몸통 뒤 끝 · 띠를 맞춤)
def 몸38(p): p = np.asarray(p, float); return np.c_[p[:, 1], 4.55 - p[:, 0]]
def 몸37(p): p = np.asarray(p, float); return np.c_[p[:, 1] + 1.2, p[:, 0] - 4.6]
총열 = dict(x0=21.4, x1=31.4, r0=1.3, r1=0.72)
def 라이플38():
    hw = G["라이플반폭"]
    몸 = 판(몸38([(1.2, 5.0), (2.6, 2.6), (5.0, 2.4), (6.2, 3.2), (6.5, 6.6), (6.3, 6.9), (6.3, 14.4), (7.9, 14.4), (8.2, 15.3), (8.4, 19.0), (8.4, 21.4),
                  (3.0, 21.4), (3.0, 19.3), (2.6, 18.3), (2.0, 15.5), (1.2, 14.4)]), -hw, 0)
    몸 -= 판(몸38([(2.1, 7.0), (3.0, 7.0), (3.0, 13.5), (2.1, 13.5)]), -hw - 1, -hw + 1.0)                   # 윗 슬롯(깊이 1.0)
    몸 -= 판(몸38([(4.4, 20.0), (5.4, 20.0), (5.4, 20.8), (4.4, 20.8)]), -5, 5)                              # 조준기(A3-26) 끼움 틈
    손 = 판(몸38([(8.0, 15.4), (12.9, 16.6), (13.25, 18.6), (12.8, 19.3), (12.45, 18.7), (8.4, 18.6)]), -G["손잡이반폭"], G["손잡이반폭"])
    손 -= M.Manifold.batch_boolean([판(몸38([(x, 14), (x + 0.3, 14), (x + 0.3, 20), (x, 20)]), -5, -G["손잡이반폭"] + 0.25) + 판(몸38([(x, 14), (x + 0.3, 14), (x + 0.3, 20), (x, 20)]), G["손잡이반폭"] - 0.25, 5) for x in (10.0, 10.9, 11.8)], M.OpType.Add)
    막대 = 판(몸38([(6.0, 10.9), (11.5, 10.9), (11.5, 12.2), (6.0, 12.2)]), -0.8, 0.8)
    꼭지 = 축원뿔(0.4, 2.45, 0.7, 0.8, y=4.55 - 3.2)                                                         # 뒤 끝 원통
    관 = 축원뿔(21.2, 25.2, 0.45, 0.45, y=4.55 - 7.15) + M.Manifold.sphere(0.45, 20).translate([25.2, 4.55 - 7.15, 0])   # 총열 밑 작은 관
    반총열 = 축원뿔(총열["x0"] - 0.2, 총열["x1"], 총열["r0"], 총열["r1"]) ^ 반공간Z(False)
    총구 = 축원뿔(총열["x1"] - 0.05, 33.25, 0.6, 0.6) + 축원뿔(33.2, 33.95, 0.8, 0.8) + 축원뿔(33.9, 38.6, 0.75, 0.45)
    return 몸 + 손 + 막대 + 꼭지 + 관 + 반총열 + 총구
def 라이플37():
    hw = G["라이플반폭"]
    몸 = 판(몸37([(4.0, 1.3), (7.3, 1.3), (8.6, 3.2), (8.6, 5.8), (7.2, 5.8), (7.2, 12.3), (8.2, 12.4), (8.2, 13.6), (7.2, 13.8), (6.4, 17.6), (6.5, 17.7), (6.5, 20.2),
                  (1.1, 20.2), (1.1, 17.7), (2.0, 17.7), (2.0, 13.8), (3.3, 13.6), (3.3, 1.8)]), 0, hw)
    몸 -= 판(몸37([(3.3, 18.9), (6.2, 18.9), (6.2, 19.5), (3.3, 19.5)]), -5, 5)                             # 조준기 끼움 틈
    몸 -= M.Manifold.batch_boolean([판(몸37([(4.8, y), (6.3, y), (6.3, y + 0.22), (4.8, y + 0.22)]), hw - 0.3, hw + 1) for y in (1.9, 2.45, 3.0)], M.OpType.Add)   # 뒤 환기 홈 셋
    반총열 = 축원뿔(총열["x0"] - 0.2, 총열["x1"], 총열["r0"], 0.62) ^ 반공간Z(True)
    return 몸 + 반총열

# ---------- 내보내기 · 그림 ----------
def 내보내기(m, 번호):
    fn = os.path.join(OUT, "부품_%02d.stl" % 번호); g = m.to_mesh()
    trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False).export(fn)
    닫힘 = bool(trimesh.load(fn).is_watertight)
    for 양 in (0.02, 0.04, 0.08):
        if 닫힘: break
        부채나누기(m, 양).export(fn); 닫힘 = bool(trimesh.load(fn).is_watertight)
    tm = trimesh.load(fn)
    return tm, dict(닫힘=닫힘, 부피mm3=round(m.volume(), 1), 크기mm=np.round(tm.extents, 1).tolist(), 무게g=round(m.volume() * 1.05e-3, 2))
def 회전(오른, 위, 앞, 기울=0.0, 돌림=0.0):
    R = np.array([오른, 위, 앞], float)
    c, s = np.cos(np.radians(돌림)), np.sin(np.radians(돌림)); R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]) @ R
    c, s = np.cos(np.radians(기울)), np.sin(np.radians(기울)); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]]) @ R
def 렌더(조각, R, W=300):
    V = np.vstack([t.vertices for t, _ in 조각]); o = np.cumsum([0] + [len(t.vertices) for t, _ in 조각])
    F = np.vstack([t.faces + o[i] for i, (t, _) in enumerate(조각)]); C = np.vstack([np.tile(c, (len(t.faces), 1)) for t, c in 조각])
    Nf = np.vstack([t.face_normals for t, _ in 조각]) @ R.T; Vs = V @ R.T
    lo, hi = Vs[:, :2].min(0), Vs[:, :2].max(0); s = (hi - lo).max() / (W - 16); Vs = Vs - np.r_[(lo + hi) / 2, 0]
    zb, tid = DD.래스터(Vs, F, W / 2, W / 2, s, W)
    img = np.ones((W, W, 3)); A = tid >= 0; Lt = np.array([-0.45, 0.5, 0.74]); Lt /= np.linalg.norm(Lt)
    img[A] = C[tid[A]] * (np.clip(Nf[tid[A]] @ Lt, 0, 1) * 0.7 + 0.3)[:, None]
    nb = np.zeros((W, W, 3)); nb[A] = Nf[tid[A]]; z = np.where(A, zb, 0.0); 선 = np.zeros((W, W), bool)
    for ax in (0, 1):
        z2, n2, A2 = np.roll(z, 1, ax), np.roll(nb, 1, ax), np.roll(A, 1, ax)
        선 |= (A != A2) | (A & A2 & ((np.abs(z - z2) > 0.25) | ((nb * n2).sum(-1) < np.cos(np.radians(20)))))
    img[선] *= 0.35
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

색 = {3: (0.9, 0.92, 0.9), 4: (0.82, 0.18, 0.15), 25: (0.96, 0.76, 0.2), 37: (0.4, 0.43, 0.48), 38: (0.4, 0.43, 0.48)}
앞, 뒤 = ((1, 0, 0), (0, 1, 0), (0, 0, 1)), ((-1, 0, 0), (0, 1, 0), (0, 0, -1))
보기 = {3: 뒤, 4: 앞, 25: 앞, 37: ((0, 1, 0), (-1, 0, 0), (0, 0, 1)), 38: ((0, -1, 0), (-1, 0, 0), (0, 0, -1))}   # 사진과 같은 면 · 같은 세움

if __name__ == "__main__":
    빨m, 빨윤곽 = 빨강(); 빨tm = trimesh.Trimesh(np.asarray(빨m.to_mesh().vert_properties)[:, :3], np.asarray(빨m.to_mesh().tri_verts), process=False)
    흰m, 핀정보 = 흰판(빨윤곽, 빨tm)
    # 십자: 빨강 십자 홈 중심(v 0.352) 위 · 빨강 겉면 높이에 앉힌다
    yc = 빨강Y + 0.352 * 빨강길이; hit = 빨tm.ray.intersects_location(np.array([[1.5, yc + 1.5, 20.0]]), np.array([[0, 0, -1.0]]))[0]
    십m = 십자().translate([0, yc, float(hit[:, 2].max())])
    부품 = {3: 흰m, 4: 빨m, 25: 십m, 37: 라이플37(), 38: 라이플38()}
    결과 = dict(가정=가정, 척도="0.17 mm/px (어림)", 핀=핀정보)
    tms = {}
    for k, m in 부품.items(): tms[k], 결과["부품_%02d" % k] = 내보내기(m, k)
    # 맞춤 검사: 빨강 윤곽이 흰 바깥 윤곽 안에 드는가(넘친 넓이 = 0 이어야) · 핀이 빨강 윤곽 안인가 · 라이플 반쪽 겹침
    cs0 = lambda p: M.CrossSection([B.반시계(np.asarray(p, float)).tolist()]); 흰전체 = cs0(흰윤곽) + cs0([(-4.3, 37), (4.3, 37), (4.3, 39.8), (-4.3, 39.8)])
    cs = lambda p: 흰전체 if p is 흰윤곽 else cs0(p)
    결과["맞춤"] = dict(빨강이_흰윤곽_넘친넓이mm2=round((cs(빨윤곽) - cs(흰윤곽)).area(), 3),
                     흰윤곽_여유최소mm=next((round(float(d), 2) for d in np.arange(0.05, 3, 0.05) if (cs(빨윤곽) - cs(흰윤곽).offset(-d, M.JoinType.Miter)).area() > 0.01), None),
                     라이플_반쪽겹침mm3=round((부품[37] ^ 부품[38]).volume(), 3), 흰_빨강겹침mm3=round((흰m ^ 빨m).volume(), 3), 십자_빨강겹침mm3=round((십m ^ 빨m).volume(), 3))
    json.dump(결과, open(os.path.join(OUT, "무기방패.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(결과, ensure_ascii=False, indent=1))
    # 갤러리
    im = Image.open(os.path.join(D, "d_egx01_j1.jpg")).convert("RGB"); 목록 = {e["번호"]: e for e in json.load(open(os.path.join(D, "전부품", "목록.json"), encoding="utf-8"))}
    T = 300; 줄 = []
    for k in (3, 4, 25, 37, 38):
        x0, y0, x1, y1 = 목록[k]["상자"]; ph = im.crop((x0 - 4, y0 - 4, x1 + 4, y1 + 4)); k_ = (T - 10) / max(ph.size); ph = ph.resize((int(ph.size[0] * k_), int(ph.size[1] * k_)), Image.LANCZOS)
        a = Image.new("RGB", (T, T), "white"); a.paste(ph, ((T - ph.size[0]) // 2, (T - ph.size[1]) // 2))
        s1 = 렌더([(trimesh.load(os.path.join(D, "전부품", "부품_%02d.stl" % k)), np.array(색[k]))], 회전(*앞, 기울=-30), T)
        s2 = 렌더([(tms[k], np.array(색[k]))], 회전(*보기[k], 기울=-30), T)
        s0 = 렌더([(tms[k], np.array(색[k]))], 회전(*보기[k]), T)
        extra = 렌더([(tms[k], np.array(색[k]))], 회전(*앞, 기울=-35, 돌림=20), T) if k == 3 else 렌더([(tms[k], np.array(색[k]))], 회전(*(앞 if k in (4, 25) else 보기[k]), 기울=-60, 돌림=25), T)
        row = Image.new("RGB", (T * 5, T + 22), "white"); dr = ImageDraw.Draw(row)
        for j, (t, 이름) in enumerate(((a, "사진 j1"), (s1, "1단계(평판)"), (s0, "2단계 · 사진과 같은 면"), (s2, "2단계 · 30° 비스듬"), (extra, "2단계 · 앞면" if k == 3 else "2단계 · 다른 각"))):
            row.paste(t, (j * T, 22)); dr.text((j * T + 4, 4), "부품 %02d  %s" % (k, 이름) if j == 0 else 이름, fill=(0, 0, 0), font=글꼴)
        줄.append(row)
    조 = [(tms[3], np.array(색[3])), (tms[4], np.array(색[4])), (tms[25], np.array(색[25]))]
    W2 = 560
    for 사진, 상자_, R_, 이름 in (("d_egx01_04.jpg", (25, 30, 490, 420), 회전(*앞, 기울=-35, 돌림=115), ("완성 사진 04 (앞)", "조립 3+4+25 · 앞")),
                               ("d_egx01_05.jpg", (10, 30, 660, 360), 회전(*뒤, 기울=-45, 돌림=-95), ("완성 사진 05 (뒤 · 참고)", "조립 · 뒤 (손잡이 A4-29 는 이 묶음 밖)"))):
        p = Image.open(os.path.join(D, 사진)).convert("RGB").crop(상자_); p.thumbnail((W2, W2), Image.LANCZOS)
        r = Image.new("RGB", (T * 5, W2 + 22), "white"); dr = ImageDraw.Draw(r)
        r.paste(p, (0, 22)); r.paste(렌더(조, R_, W2), (W2 + 20, 22)); dr.text((4, 4), 이름[0], fill=(0, 0, 0), font=글꼴); dr.text((W2 + 24, 4), 이름[1], fill=(0, 0, 0), font=글꼴)
        줄.append(r)
    갤 = Image.new("RGB", (T * 5, sum(r.size[1] for r in 줄)), "white"); y = 0
    for r in 줄: 갤.paste(r, (0, y)); y += r.size[1]
    갤.save(os.path.join(OUT, "갤러리_무기방패.png")); print("갤러리", 갤.size)
