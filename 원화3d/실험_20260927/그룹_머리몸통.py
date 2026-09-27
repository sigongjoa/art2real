# -*- coding: utf-8 -*-
"""EG RX-78-2 2 단계 — 머리 · 몸통 무리 22 부품을 하위 도형의 합으로 (2026-09-27).

    python 그룹_머리몸통.py -> out/키트/EG_RX78/2단계/부품_NN.stl · 갤러리_머리몸통.png · 머리몸통.json

좌표: 부품 나열 사진(d_egx01_j1.jpg) 속 상자(목록.json) 안의 화소 (x 오른쪽 · y 아래) 로 도형을 적고 × 0.17 mm 로 바꾼다.
      X = x·MM · Y = (H − y)·MM · Z = 책상에서 위(사진에 없는 축). 1 단계 STL(전부품/) 과 같은 틀이라 같은 화면에 그린다.
도형: 실루엣판(사진 윤곽을 민 평판) · 판(다각형) · 상자 · 원판 · 구(볼 조인트) · 봉(누운 원기둥) · 돔(거리장으로 부푼 윗면) · 띠(선을 굵힌 판).
      구멍 · 홈은 휘기 전에 뺀다(정강이2 방식). 가장자리 둥글림은 판마다 윗면만 거리장으로 내린다.
**Z 쪽 값(두께 · 단차 · 돔 높이 · 볼 중심 높이)은 모두 가정** — 사진은 위에서 한 장뿐. 조립 사진 · 설명서 등각도로 어림했을 뿐 잰 값이 아니다."""
import os, sys, json, numpy as np, trimesh, manifold3d as M
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage import measure
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260925")
import 방패 as B
import 디테일대조 as DD
import 전부품 as P1
from 메시출력 import 부채나누기

D = r"G:\art2real\원화3d\out\키트\EG_RX78"; OUT = os.path.join(D, "2단계"); os.makedirs(OUT, exist_ok=True)
MM = P1.MM; SEG = 40
목록 = {e["번호"]: e for e in json.load(open(os.path.join(D, "전부품", "목록.json"), encoding="utf-8"))}
사진 = np.array(Image.open(os.path.join(D, "d_egx01_j1.jpg")).convert("RGB")).astype(float)
_lab, _ = ndimage.label(P1.전경(사진))

def 이동(m, x, y, z): return m.translate([float(x), float(y), float(z)])

class 틀:
    """한 부품의 좌표 틀 — 사진 상자 화소 → mm."""
    def __init__(s, n):
        x0, y0, x1, y1 = 목록[n]["상자"]; s.W, s.H = x1 - x0, y1 - y0
        lab = _lab[y0:y1, x0:x1]; ids, cnt = np.unique(lab[lab > 0], return_counts=True)
        s.mask = lab == ids[np.argmax(cnt)]
    def xy(s, pts): p = np.asarray(pts, float).reshape(-1, 2); return np.c_[p[:, 0] * MM, (s.H - p[:, 1]) * MM]
    def cs(s, pts): return M.CrossSection([B.반시계(s.xy(pts)).tolist()])
    def 네모(s, x0, y0, x1, y1, 모=0.0):
        c = s.cs([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        return c.offset(-모 * MM, M.JoinType.Round).offset(모 * MM, M.JoinType.Round) if 모 else c
    def 원cs(s, x, y, r, n=SEG): a = np.linspace(0, 2 * np.pi, n, endpoint=False); return s.cs(np.c_[x + r * np.cos(a), y + r * np.sin(a)])
    def 고리cs(s, x, y, r0, r1): return s.원cs(x, y, r1) - s.원cs(x, y, r0)
    def 실루엣cs(s, 깎=0.0):
        big = ndimage.gaussian_filter(ndimage.zoom(s.mask.astype(float), 4, order=1), 2.0) > 0.5; polys = []
        for c in measure.find_contours(np.pad(big, 1).astype(float), 0.5):
            if len(c) <= 12: continue
            c = ndimage.gaussian_filter1d(c[:-1] - 1, 2.0, axis=0, mode="wrap"); p = np.c_[c[:, 1], big.shape[0] - c[:, 0]] / 4 * MM
            p = B.rdp(np.vstack([p, p[:1]]), 0.08)[:-1]
            if len(p) >= 3: polys.append(p.tolist())
        c = M.CrossSection(polys, M.FillRule.EvenOdd)
        return c.offset(-깎 * MM, M.JoinType.Round) if 깎 else c
    def 띠cs(s, pts, w):
        pts = np.asarray(pts, float); c = M.CrossSection()
        for a, b in zip(pts[:-1], pts[1:]):
            d = b - a; n = np.array([-d[1], d[0]]) / np.linalg.norm(d) * w / 2
            c = c + s.cs([a + n, b + n, b - n, a - n])
        for p in pts: c = c + s.원cs(p[0], p[1], w / 2, 20)
        return c
    # --- 입체 ---
    def 판(s, c, z0, z1, r=0.0):
        """단면 c 를 z0..z1 로 민다. r>0 이면 윗면 가장자리를 r mm 로 둥글린다(거리장 · 윗면만)."""
        m = c.extrude(z1 - z0).translate([0, 0, z0])
        if r <= 0: return m
        r = min(r, 0.9 * (z1 - z0)); 해 = 0.02
        polys = c.to_polygons(); lo = np.concatenate(polys).min(0) - 0.2; hi = np.concatenate(polys).max(0) + 0.2
        Wd, Hd = np.ceil((hi - lo) / 해).astype(int) + 1; acc = np.zeros((Hd, Wd), bool)
        for p in polys:
            im = Image.new("1", (Wd, Hd)); ImageDraw.Draw(im).polygon([tuple(q) for q in (np.asarray(p) - lo) / 해], fill=1); acc ^= np.array(im)
        거리 = ndimage.distance_transform_edt(acc) * 해
        def f(V):
            d = ndimage.map_coordinates(거리, [(V[:, 1] - lo[1]) / 해, (V[:, 0] - lo[0]) / 해], order=1)
            w = np.clip((V[:, 2] - (z1 - r)) / r, 0, 1)
            return np.c_[V[:, 0], V[:, 1], V[:, 2] - w * r * (1 - np.sqrt(np.clip(1 - (1 - np.clip(d / r, 0, 1)) ** 2, 0, 1)))]
        return m.refine_to_length(max(r / 2, 0.08)).warp_batch(f)
    def 상자(s, x0, y0, x1, y1, z0, z1, r=0.0, 모=0.0): return s.판(s.네모(x0, y0, x1, y1, 모), z0, z1, r)
    def 원판(s, x, y, rr, z0, z1, r=0.0): return s.판(s.원cs(x, y, rr), z0, z1, r)
    def 구(s, x, y, rr, zc=None):
        rr *= MM; X, Y = s.xy([(x, y)])[0]; return 이동(M.Manifold.sphere(rr, SEG), X, Y, rr if zc is None else zc)
    def 봉(s, a, b, rr, zc):
        """a→b (화소) 로 누운 원기둥, 반지름 rr 화소, 중심 높이 zc mm."""
        A_, B_ = s.xy([a, b]); d = B_ - A_; L = float(np.linalg.norm(d)); ang = np.degrees(np.arctan2(d[1], d[0]))
        m = M.Manifold.cylinder(L, rr * MM, rr * MM, SEG).rotate([0, 90, 0]).rotate([0, 0, ang])
        return 이동(m, A_[0], A_[1], zc)
    def 뚫기(s, c): return s.판(c, -1, 20)
    def 돔(s, m, 영역, h, z_top, 덧=0.0):
        """z ≥ z_top 인 정점을 영역(단면) 안쪽 거리에 따라 h mm 부풀린다(+덧: 고른 추가 높이)."""
        k = s._장(영역)
        def f(V):
            top = V[:, 2] >= z_top - 1e-6
            return np.c_[V[:, 0], V[:, 1], V[:, 2] + top * (h * k(V[:, 0], V[:, 1]) + 덧)]
        return m.refine_to_length(0.12).warp_batch(f)
    def _장(s, 영역):
        해 = 0.02; polys = 영역.to_polygons(); lo = np.concatenate(polys).min(0) - 0.2; hi = np.concatenate(polys).max(0) + 0.2
        Wd, Hd = np.ceil((hi - lo) / 해).astype(int) + 1; acc = np.zeros((Hd, Wd), bool)
        for p in polys:
            im = Image.new("1", (Wd, Hd)); ImageDraw.Draw(im).polygon([tuple(q) for q in (np.asarray(p) - lo) / 해], fill=1); acc ^= np.array(im)
        dd = ndimage.gaussian_filter(ndimage.distance_transform_edt(acc) * 해, 4); dmax = float(dd.max())
        def k(X, Y):
            d = ndimage.map_coordinates(dd, [(Y - lo[1]) / 해, (X - lo[0]) / 해], order=1, cval=0.0)
            return np.sqrt(np.clip(1 - (1 - np.clip(d / dmax, 0, 1)) ** 2, 0, 1))
        return k

# ---------------- 부품 22 (도형 이름은 설명서 · 조립 사진으로 어림한 역할) ----------------
def p01(t):   # 빨강 번개 띠(작은 장식판): 굵은 띠 + 가운데 등줄
    pts = [(5, 4), (5, 13), (12, 17.5), (7, 21), (6, 24), (11.5, 31)]
    return t.판(t.띠cs(pts, 4.2), 0, 0.9, 0.25) + t.판(t.띠cs(pts, 1.6), 0, 1.25, 0.15)
def p02(t):   # V 안테나: 얇은 팔(실루엣) + 가운데 몸통(홈 파인 상자)
    몸 = t.cs([(19, 0), (30, 0), (30, 24), (27, 33), (22, 33), (19, 24)])
    팔 = [(0, 13), (0, 4), (3, 2), (19.5, 19), (24.5, 21), (24.5, 37), (22, 37)]      # 흰 바탕 위 흰 부품이라 자동 윤곽 대신 손으로 잰 V
    팔 = t.cs(팔) + t.cs([(49 - x, y) for x, y in 팔])
    m = t.판(팔 - 몸, 0, 0.7, 0.2) + t.판(몸, 0, 2.3, 0.35)
    return m - t.상자(21.5, 14, 27.5, 29, 1.3, 5)
def p05(t):   # 노랑 방패꼴 판: 바닥판 + 한 단 솟은 돔 판 + 열쇠구멍 관통 + 위 탭
    m = t.판(t.실루엣cs(), 0, 0.9, 0.25) + t.돔(t.판(t.실루엣cs(2.5), 0.5, 1.2), t.실루엣cs(2.5), 0.5, 1.2) + t.상자(10, 5, 14, 9, 0, 1.6, 0.2)
    return m - t.뚫기(t.원cs(12, 22, 2.8) + t.네모(10.8, 22, 13.3, 28.5))
def p06(t):   # 목 관절: 볼 둘 + 가운데 블록 + 목 봉 둘
    rb = 5.3 * MM
    return (t.구(10, 8.5, 5.3) + t.구(12.5, 30, 5.3) + t.판(t.cs([(3, 15), (16, 13), (17.5, 23.5), (4, 25)]), 0, 2 * rb, 0.3)
            + t.봉((10, 8.5), (11, 16), 2.6, rb) + t.봉((11, 22), (12.5, 30), 2.6, rb))
def p07(t):   # 빨강 육각 돔 판 + 아래 핀
    hx = [(12, 3), (18, 6), (20, 11), (20, 21), (17, 27), (12, 30), (7, 27), (4, 21), (4, 10), (7, 5)]
    안 = t.cs(hx).offset(-1.0 * MM, M.JoinType.Round)
    return t.판(t.cs(hx), 0, 0.7, 0.2) + t.돔(t.판(안, 0.4, 0.9), 안, 1.2, 0.9) + t.봉((12, 28), (12, 38.5), 1.7, 0.35)
def p08(t):   # 흰 투구: 원 윤곽 돔(속 참) + 가운데 등줄(같은 돔 위로 0.35) + 가로 홈 + 앞 얼굴 구멍
    겉 = t.원cs(20, 19, 18.3, 64) ^ t.네모(0, 0.5, 40, 37); h = 2.7      # 흰 바탕 위 흰 부품이라 자동 윤곽이 들쭉날쭉 → 원으로
    m = t.돔(t.판(겉, 0, 0.6, 0), 겉, h, 0.6)
    m = m + t.돔(t.판(t.네모(12.5, 3, 23.5, 37) ^ 겉, 0, 0.6), 겉, h, 0.6, 덧=0.35)
    k = t._장(겉); X, Y = t.xy([(18, 21)])[0]; z = 0.6 + h * float(k(np.array([X]), np.array([Y]))[0])
    m = m - t.상자(12, 20.3, 24, 22, z - 0.05, 9)
    return m - t.상자(13.5, 30.5, 23.5, 40, 0.35, 9)       # 얼굴 들어갈 자리(바닥 0.35 남김)
def p09(t):   # 흰 작은 U 블록
    return t.상자(1, 3, 15, 13, 0, 1.3, 0.3, 모=1) - t.뚫기(t.네모(7, 7.5, 11, 14) + t.원cs(9, 7.5, 2))
def p10(t):   # 파랑 몸통 골격(십자): 기둥 상자 + 위 탭 + 좌우 팔 + 끝 기둥 + 창(오목) + 가로 홈
    m = t.상자(32, 18, 55, 73, 0, 3.2, 0.45, 모=2) + t.상자(37.5, 4, 48.5, 19, 0, 1.4, 0.2)
    for a, b in ((5, 33), (54, 82)): m = m + t.상자(a, 23, b, 40, 0, 1.8, 0.3)
    for a, b in ((5, 11.5), (75.5, 82)): m = m + t.상자(a, 21, b, 40.5, 0, 2.6, 0.3, 모=1)
    for a, b in ((12, 19), (68, 75)): m = m - t.상자(a, 27, b, 36, 0.6, 5)
    for y in (34.5, 55): m = m - t.상자(31, y, 56, y + 1.3, 2.95, 5)
    return m - t.상자(40, 13.5, 46, 14.5, 1.2, 5)
def p11(t):   # 흰 판 상자 + 솟은 앞판
    return t.상자(5, 6, 48, 43, 0, 2.4, 0.35, 모=3) + t.상자(10.5, 7, 46.5, 39, 0, 2.8, 0.2, 모=2)
def p12(t):   # 흰 주사위 + 아래 핀
    return (t.상자(6, 3, 30, 27, 0, 3.4, 0.4, 모=2) - t.상자(14, 7.5, 22, 10.5, 3.15, 5)) + t.봉((17.5, 26), (17.5, 44), 3.6, 0.62)
def p13(t):   # 노랑 가슴 덕트: 바닥판 + 기둥 둘(반원 등) + 가운데 블록 + 아래 띠 + 호 갈빗대 둘 + 스터드 + 발 둘
    m = t.판(t.실루엣cs(), 0, 1.2, 0.2)
    for a, b in ((13, 24.5), (44, 57)): m = m + t.상자(a, 2, b, 46, 0, 2.9, 0.9, 모=2)
    m = m + t.상자(24.5, 25, 44, 37, 0, 1.8, 0.3) + t.상자(3, 40, 72, 56, 0, 2.0, 0.4, 모=3)
    for r0, r1 in ((30, 31.6), (33.2, 34.8)): m = m + t.판(t.고리cs(37.5, 17, r0, r1) ^ t.네모(14, 43, 61, 57), 1.8, 2.45, 0.15)
    for x, y in ((7, 44), (67, 46)): m = m + t.원판(x, y, 2.3, 0, 2.7, 0.25)
    for a, b in ((3, 22), (51, 70)): m = m + t.상자(a, 54, b, 66, 0, 2.5, 0.3, 모=1)
    return m
def p14(t):   # 파랑 가슴 겉 틀(안쪽이 보이게 엎어 놓임): 바깥 윤곽 − 창 + 아래 비탈 + 위 홈 + 목깃 블록(구멍) + 어깨 축 둘
    겉 = t.cs([(10, 8), (13, 5), (93, 5), (95, 8), (95, 45), (92, 72), (88, 76), (15, 76), (11, 72), (10, 45)])
    창 = t.cs([(18, 18), (86, 18), (86, 46), (72, 66), (31, 66), (18, 46)])
    m = t.판(겉 - 창, 0, 4.5, 0.4)
    Y0, Y1 = (t.H - 45) * MM, (t.H - 80) * MM           # 아래 비탈: y 45 → 76 에서 4.5 → 2.2 mm
    쐐기 = M.CrossSection([B.반시계(np.array([[Y0, 4.5], [Y1, 4.5 - 2.3 * 35 / 31], [Y1, 9], [Y0, 9]])).tolist()]).extrude(t.W * MM + 2)
    m = m - 쐐기.transform(np.array([[0, 0, 1, -1.0], [1, 0, 0, 0], [0, 1, 0, 0]], float))
    for a in (32.5, 66): m = m - t.상자(a, 4, a + 2, 18.5, 4.1, 6)
    깃 = t.cs([(35, 10), (68, 10), (68, 38), (62, 45), (41, 45), (35, 38)])
    m = m + t.판(깃, 0, 4.0, 0.4) - t.상자(40, 20, 64, 22, 3.75, 6)
    m = m - t.뚫기(t.원cs(51.5, 32, 6))
    for x in (19.5, 84.5): m = m + t.봉((x, 17), (x, 47), 3.0, 2.3) + t.봉((x, 23), (x, 26), 4.3, 2.3) + t.봉((x, 38), (x, 41), 4.3, 2.3)
    return m
def p15(t):   # 회색 볼 + 목 + 턱(칼라) + C 브래킷(홈)
    rb = 7.5 * MM
    m = t.구(8, 18, 7.5) + t.봉((13, 18), (26, 18), 3.0, rb) + t.봉((17, 18.5), (21, 18.5), 8.0, rb)
    m = m + t.판(t.실루엣cs() ^ t.네모(24, 0, 60, 60), 0, 2.4, 0.3)
    return m - t.판(t.cs([(28, 13), (35, 13), (35, 23), (29, 25)]), 1.3, 4)
def p17(t):   # 회색 세로 틀: 실루엣판 + 윗단 + 창(관통) + U 홈
    m = t.판(t.실루엣cs(), 0, 2.2, 0.25) + t.상자(4, 3, 21.5, 18, 0, 2.6, 0.25, 모=1)
    m = m - t.뚫기(t.네모(7, 7, 10.5, 13) + t.네모(12, 7, 17, 13))
    U = (t.고리cs(13, 31, 3.2, 5.2) ^ t.네모(0, 31, 30, 45)) + t.네모(7.8, 31, 9.8, 40) + t.네모(16.2, 31, 18.2, 40)
    return m - t.판(U, 1.2, 4)
def p18(t):   # 흰 ㄷ 브래킷: 상자 + 앞 홈 + 다리 사이 틈
    return t.상자(4, 3, 27, 28, 0, 2.3, 0.3, 모=1) - t.상자(9, 17, 23, 30, 0.7, 4) - t.뚫기(t.네모(9.5, 23.5, 22.5, 30))
def p19(t):   # 회색 블록 + 솟은 판 + 가로 홈
    return t.상자(5, 2, 20, 23, 0, 2.2, 0.3, 모=1) + t.상자(7, 4, 19, 19.5, 0, 2.5, 0.15) - t.상자(6, 9.5, 20, 10.5, 2.3, 4)
def p20(t):   # 빨강 ㄷ 판: 바닥판 + 가장자리 테 남기고 얕은 골 + 패드 둘 + 안쪽 턱 둘
    m = t.판(t.실루엣cs(), 0, 1.5, 0.3)
    패드 = t.네모(10, 8, 19, 38, 2) + t.네모(44, 8, 53, 38, 2)
    m = m - t.판(t.실루엣cs(3) - 패드.offset(0.6 * MM, M.JoinType.Round), 1.2, 3)
    m = m + t.판(패드, 0, 2.2, 0.25)
    for a, b in ((19, 24), (39, 44)): m = m + t.상자(a, 10, b, 26, 0, 1.8, 0.2)
    return m
def p21(t):   # 빨강 C 고리 틀(단면 ㄷ: 바깥 테 + 얕은 골) + 가운데 줄기 + 볼
    틀cs = t.실루엣cs() - t.네모(27, 11.5, 41, 31)
    m = t.판(틀cs, 0, 1.9, 0.3) - t.판(t.실루엣cs(2.2) - t.실루엣cs(6.5) - t.네모(27, 0, 41, 31), 1.5, 3)
    return m + t.상자(30.5, 3, 37.5, 17, 0, 1.5, 0.25) + t.구(34, 22, 5.5)
def p22(t):   # 회색 어깨 블록: 상자(오목 창) + 위 턱 + 볼 둘(핀 구멍)
    m = t.판(t.cs([(6, 7), (27, 6), (28, 30), (7, 31)]), 0, 2.8, 0.3) - t.상자(11, 11, 22, 26, 1.4, 4)
    m = m + t.상자(4, 5, 26, 10, 0, 3.1, 0.3) + t.구(32, 12, 8.5) + t.구(19, 39, 8.5) + t.봉((30, 14), (25, 17), 3.5, 1.45) + t.봉((19, 38), (18.5, 28), 3.5, 1.45)
    for x, y in ((37, 8), (32, 15.5), (24, 35), (18, 43)): m = m - t.원판(x, y, 1.1, 1.8, 4)
    return m
def p26(t):   # 회색 주먹꼴 블록(깎은 모서리) + 목 + 작은 볼 + 옆 홈
    몸 = t.cs([(10, 15), (30, 13), (35, 20), (35, 36), (28, 43), (12, 43), (5, 36), (5, 22)])
    m = t.판(몸, 0, 4.0, 0.7) + t.봉((15, 10), (15, 16), 2.6, 2.0) + t.구(15, 10, 5, 2.0)
    return m - t.상자(7, 24, 12, 39, 1.2, 6)
def p27(t):   # 노랑 허리 틀: 몸판 + 위 집게 + 탭 + 가운데 구멍(테) + 가로 홈 + 팔 봉 · 볼 둘 + 발 셋(십자 홈)
    몸 = t.cs([(19, 31), (38, 27), (55, 27), (71, 31), (71, 51), (19, 51)])
    m = t.판(몸, 0, 1.6, 0.3) + t.상자(40, 10, 52, 28, 0, 2.2, 0.3) + t.상자(43, 2, 50, 11, 0, 1.4, 0.2) + t.판(t.고리cs(46, 37, 8, 9.8), 0, 2.0, 0.25)
    for a, b in ((19, 37.5), (55, 71)):
        for y in (42, 47.5): m = m - t.상자(a, y, b, y + 1, 1.35, 3)
    rb = 5.5 * MM
    m = m + t.봉((9, 34), (20, 35), 2.8, rb) + t.봉((70, 38), (83, 39), 2.8, rb) + t.봉((13, 34), (15.5, 34), 4.2, rb) + t.구(6, 34, 5.5) + t.구(86, 39, 5.5)
    m = m + t.상자(11, 51, 31, 63, 0, 2.6, 0.3) + t.상자(60, 51, 80, 65, 0, 2.6, 0.3) + t.상자(41, 50, 51, 62, 0, 1.6, 0.2)
    m = m - t.판(t.네모(44.5, 53, 47.5, 60) + t.네모(42, 55.5, 50, 57.5), 1.0, 3)
    return m - t.뚫기(t.원cs(46, 37, 8))
def p29(t):   # 빨강 T 틀: 가로대 + 볼 둘 + 십자 음각 + 줄기(홈 둘) + 아래 블록(단)
    rb = 7.5 * MM
    m = t.상자(13, 7, 52, 18, 0, 1.6, 0.3) + t.구(10, 12, 7.5) + t.구(56, 13, 7.5)
    for x in (21, 44): m = m - t.판(t.네모(x - 2, 11.4, x + 2, 12.6) + t.네모(x - 0.6, 10, x + 0.6, 14), 1.35, 3)
    m = m + t.상자(24, 7, 35, 42, 0, 2.0, 0.55) + t.상자(22, 39, 36, 51, 0, 2.4, 0.3)
    for x in (27.5, 31.5): m = m - t.상자(x, 10, x + 1, 39, 1.75, 3)
    return m - t.상자(21, 45, 37, 52, 2.1, 4)

부품들 = {1: p01, 2: p02, 5: p05, 6: p06, 7: p07, 8: p08, 9: p09, 10: p10, 11: p11, 12: p12, 13: p13, 14: p14, 15: p15,
        17: p17, 18: p18, 19: p19, 20: p20, 21: p21, 22: p22, 26: p26, 27: p27, 29: p29}

# ---------------- 그림 ----------------
def 그림(tm, 색, 중심, s, T=240):
    a, b = np.radians(30), np.radians(-20)
    Rz = np.array([[np.cos(b), -np.sin(b), 0], [np.sin(b), np.cos(b), 0], [0, 0, 1]]); Rx = np.array([[1, 0, 0], [0, np.cos(a), np.sin(a)], [0, -np.sin(a), np.cos(a)]])
    R = Rx @ Rz; V = (tm.vertices - 중심) @ R.T; N = tm.face_normals @ R.T
    zb, tid = DD.래스터(V, tm.faces, T / 2, T / 2, s, T)
    zb, tid = zb.reshape(T, T) if zb.ndim == 1 else zb, tid.reshape(T, T) if tid.ndim == 1 else tid
    img = np.ones((T, T, 3)) * 0.93; A = tid >= 0; Lt = np.array([-0.45, 0.5, 0.74]); Lt /= np.linalg.norm(Lt)
    img[A] = np.array(색) * (np.clip(N[tid[A]] @ Lt, 0, 1) * 0.7 + 0.35)[:, None]
    nb = np.zeros((T, T, 3)); nb[A] = N[tid[A]]; z = np.where(A, zb, 0.0); 선 = np.zeros((T, T), bool)
    for ax in (0, 1):
        선 |= A & np.roll(A, 1, ax) & ((np.abs(z - np.roll(z, 1, ax)) > 0.25) | ((nb * np.roll(nb, 1, ax)).sum(-1) < np.cos(np.radians(25))))
    선 |= A ^ np.roll(A, 1, 0) | A ^ np.roll(A, 1, 1)
    img[선] *= 0.5
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)

def 저장(m, fn):
    g = m.to_mesh(); tm = trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False); tm.export(fn)
    닫힘 = bool(trimesh.load(fn).is_watertight)
    for 양 in (0.02, 0.04, 0.08):
        if 닫힘: break
        부채나누기(m, 양).export(fn); 닫힘 = bool(trimesh.load(fn).is_watertight)
    return 닫힘

if __name__ == "__main__":
    고를 = [int(a) for a in sys.argv[1:]] or list(부품들)
    결과 = {}; 타일 = []; T = 240
    for n in 고를:
        t = 틀(n); m = 부품들[n](t)
        m = m ^ M.Manifold.cube([t.W * MM + 20, t.H * MM + 20, 30]).translate([-10, -10, 0])     # 책상 아래는 버림
        m = sum((p for p in m.decompose() if p.volume() > 0.01), M.Manifold())                  # 휘기가 남긴 부피 0 부스러기 버림
        fn = os.path.join(OUT, "부품_%02d.stl" % n); 닫힘 = 저장(m, fn); tm = trimesh.load(fn)
        결과[n] = dict(닫힘=닫힘, 조각=len(m.decompose()), 부피mm3=round(m.volume(), 2), 크기mm=np.round(tm.extents, 2).tolist())
        print(n, 결과[n])
        색 = 목록[n]["색rgb"]; 색 = [min(1.0, c * 1.15) for c in 색]
        중심 = np.array([t.W * MM / 2, t.H * MM / 2, 1.0]); s = max(t.W, t.H) * MM / (T * 0.62)
        x0, y0, x1, y1 = 목록[n]["상자"]; k = MM / s
        ph = Image.fromarray(사진[y0:y1, x0:x1].astype(np.uint8)).resize((max(1, int(t.W * k)), max(1, int(t.H * k))), Image.LANCZOS)
        pt = Image.new("RGB", (T, T), (237, 237, 237)); pt.paste(ph, ((T - ph.size[0]) // 2, (T - ph.size[1]) // 2))
        s1 = 그림(trimesh.load(os.path.join(D, "전부품", "부품_%02d.stl" % n)), 색, 중심, s, T); s2 = 그림(tm, 색, 중심, s, T)
        타 = Image.new("RGB", (3 * T + 8, T + 18), "white"); 타.paste(pt, (0, 18)); 타.paste(Image.fromarray(s1), (T + 4, 18)); 타.paste(Image.fromarray(s2), (2 * T + 8, 18))
        ImageDraw.Draw(타).text((4, 3), "#%02d  photo | stage1 | stage2   %.1fx%.1f mm  %s" % (n, t.W * MM, t.H * MM, "closed" if 닫힘 else "OPEN"), fill=(0, 0, 0)); 타일.append(타)
    if len(고를) == len(부품들):
        cols = 3; rows = (len(타일) + cols - 1) // cols; tw, th = 타일[0].size; G = Image.new("RGB", (cols * (tw + 12), rows * (th + 8)), "white")
        for j, 타 in enumerate(타일): G.paste(타, ((j % cols) * (tw + 12), (j // cols) * (th + 8)))
        G.save(os.path.join(OUT, "갤러리_머리몸통.png"))
        json.dump(dict(가정="Z 쪽 값(두께·단차·돔·볼 높이)은 모두 가정 · XY 는 사진 0.17 mm/px 어림", 부품=결과), open(os.path.join(OUT, "머리몸통.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    else:
        tw, th = 타일[0].size; G = Image.new("RGB", (tw, len(타일) * th), "white")
        for j, 타 in enumerate(타일): G.paste(타, (0, j * th))
        G.save(os.path.join(OUT, "시험_머리몸통.png"))
    print("닫힘 %d / %d" % (sum(v["닫힘"] for v in 결과.values()), len(결과)))
