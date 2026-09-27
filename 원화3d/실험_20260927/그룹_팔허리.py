# -*- coding: utf-8 -*-
"""EG RX-78-2 2 단계 — 팔 · 허리 무리(23 24 28 30 31 33 34 35 36 39 40 41 42 43)를 하위 도형의 합으로 (2026-09-27).

    python 그룹_팔허리.py -> out/키트/EG_RX78/2단계/부품_NN.stl · 갤러리_팔허리.png · 팔허리.json

좌표: mm, 원점 = 목록.json 상자 왼쪽 아래(사진 화소 × 0.17). x 오른쪽 · y 위 · z = 사진 쪽으로 솟는 두께(뒷면 z = 0).
도형 치수는 10 배 확대 + 1 mm 격자 사진에서 눈으로 읽었다(정강이2 방식 — 윤곽 따오기 대신 곧은 변 · 원 · 팔각).
모든 도형은 볼록 → 「둥판」 = 볼록 다각형을 민 판 + 윗모서리 둥글림(hull). 구멍 · 홈은 합친 다음 뺀다(휘기 없음).
깊이(z) 값은 전부 가정 — 사진에 없다. 설명서(3 팔 · 5 허리) 그림과 완성 사진 07(앞치마 + 노란 블록)으로 어림.
부품 16 은 이미 조립된 팔(뼈 + 장갑 여러 개)이라 뺐다."""
import os, sys, json, numpy as np, trimesh, manifold3d as M
from PIL import Image, ImageDraw
from scipy import ndimage
from matplotlib.path import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260925")
import 전부품 as J
from 메시출력 import 부채나누기

D = J.D; MM = J.MM; OUT = os.path.join(D, "2단계"); os.makedirs(OUT, exist_ok=True)
목록 = {e["번호"]: e for e in json.load(open(os.path.join(J.OUT, "목록.json"), encoding="utf-8"))}

# ---------- 하위 도형 ----------
def CS(poly): return M.CrossSection([np.asarray(poly, float).tolist()], M.FillRule.NonZero)
def 점들(cs, z): return [(x, y, z) for p in cs.to_polygons() for x, y in p]
def 둥판(poly, z0, z1, r=0.3, n=5):
    """볼록 다각형 판: 바닥 z0 은 날카롭게, 윗모서리는 반지름 r 로 둥글게."""
    cs = CS(poly) if not isinstance(poly, M.CrossSection) else poly; r = min(r, 0.49 * (z1 - z0)); P = 점들(cs, z0) + 점들(cs, z1 - r)
    for t in np.linspace(0, np.pi / 2, n)[1:]:
        P += 점들(cs.offset(-r * (1 - np.cos(t)), M.JoinType.Round, circular_segments=24), z1 - r + r * np.sin(t))
    return M.Manifold.hull_points(np.array(P))
def 층(*쌍):
    """(다각형, z) 여러 층의 hull — 볏 · 비탈면 도형."""
    return M.Manifold.hull_points(np.array([q for poly, z in 쌍 for q in 점들(CS(poly), z)]))
def 사각(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
def 둥사각(x0, y0, x1, y1, r):
    return M.CrossSection.square([x1 - x0 - 2 * r, y1 - y0 - 2 * r]).translate([x0 + r, y0 + r]).offset(r, M.JoinType.Round, circular_segments=32)
def 원(cx, cy, R, n=48): a = np.linspace(0, 2 * np.pi, n, endpoint=False); return np.c_[cx + R * np.cos(a), cy + R * np.sin(a)]
def 팔각(cx, cy, w, h, c):
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]
def 기둥(poly, z0, z1): return CS(poly).extrude(z1 - z0).translate([0, 0, z0])      # 날카로운 뺄 도형
def 원통y(cx, zc, y0, y1, R):                                                        # y 축으로 누운 원통
    return M.Manifold.cylinder(y1 - y0, R, circular_segments=40).rotate([-90, 0, 0]).translate([cx, y0, zc])
def 원통x(x0, x1, y, zc, R): return M.Manifold.cylinder(x1 - x0, R, circular_segments=40).rotate([0, 90, 0]).translate([x0, y, zc])
def 거울x(poly, xc): return [(2 * xc - x, y) for x, y in poly][::-1]
def 고리(cx, cy, r0, r1, z0, z1): return 기둥(원(cx, cy, r1), z0, z1) - 기둥(원(cx, cy, r0), z0 - 1, z1 + 1)
def 비스듬홈(cx, cy, 길이, 폭, 각, z0, z1):
    a = np.radians(각); u, v = np.array([np.cos(a), np.sin(a)]), np.array([-np.sin(a), np.cos(a)]); c = np.array([cx, cy])
    return 기둥([c - u * 길이 / 2 - v * 폭 / 2, c + u * 길이 / 2 - v * 폭 / 2, c + u * 길이 / 2 + v * 폭 / 2, c - u * 길이 / 2 + v * 폭 / 2], z0, z1)

# ---------- 부품별 짓기 (반환: 모델, 가정 설명) ----------
def 팔뚝(몸, 원판, 구멍, 띠y, 두께=3.0):
    """23 · 24 = 설명서 B-9 팔뚝 껍데기를 옆으로 눕힌 것: 오각 몸통 + 팔꿈치 원판(고리 홈 + 빗금 홈) + 옆 구멍 고리 + 아래 띠 단차."""
    cx, cy, R = 원판; m = 둥판(몸, 0, 두께, 0.7) + 둥판(원(cx, cy, R), 0, 두께 + 0.3, 0.25)
    m = m - 고리(cx, cy, R - 0.38, R - 0.2, 두께 + 0.1, 두께 + 1) - 비스듬홈(cx, cy, 2 * R - 0.8, 0.32, 55, 두께 + 0.05, 두께 + 1)
    hx, hy, hR = 구멍; m = m - 기둥(원(hx, hy, hR), 두께 - 0.5, 두께 + 1) + 둥판(원(hx, hy, hR - 0.3), 두께 - 0.6, 두께 - 0.15, 0.1)
    m = m - 기둥(사각(-1, -1, 9, 띠y), 두께 - 0.35, 두께 + 1)
    return m, "두께 3.0(팔뚝 반폭) · 원판 +0.3 · 구멍 고리 깊이 0.5 · 아래 띠 −0.35"
def p23(): return 팔뚝([(0.3, 0.3), (5.1, 0.3), (5.2, 7.3), (4.4, 9.3), (1.9, 9.3), (0.4, 7.0)], (3.0, 10.3, 1.35), (2.9, 6.4, 0.8), 1.0)
def p24(): return 팔뚝([(1.0, 0.9), (5.4, 0.9), (5.4, 8.4), (4.3, 9.5), (2.2, 9.5), (1.0, 8.2)], (2.8, 11.0, 1.4), (2.9, 6.6, 0.8), 1.5)

def p28():
    """회색 ㄷ자 틀: 윗막대 둘(오른쪽이 약간 높음) + 다리 둘(속이 파인 U 채널)."""
    T = 3.0; m = 둥판(사각(1.1, 5.1, 4.2, 6.3), 0, T, 0.3) + 둥판([(4.0, 5.0), (8.2, 5.0), (8.2, 6.4), (4.4, 6.6), (4.0, 6.4)], 0, T, 0.3)
    for x0, y0, x1, y1 in ((1.1, 1.3, 3.4, 5.4), (6.0, 0.6, 8.0, 5.4)):
        m = m + 둥판(사각(x0, y0, x1, y1), 0, T, 0.3) - 기둥(사각(x0 + 0.4, y0 + 0.4, x1 - 0.4, y1 - 0.2), T - 1.2, T + 1)
    return m, "두께 3.0 · 다리 채널 깊이 1.2 · 벽 0.4"

def p30():
    """흰 둥근 판: 가로로 불룩한 윗면(층 hull) + 아래 턱 단차."""
    b = 둥사각(1.0, 0.3, 5.5, 11.0, 0.9); sx = lambda dx, dy: 둥사각(1.0 + dx, 0.3 + dy, 5.5 - dx, 11.0 - dy, max(0.9 - dx, 0.3))
    m = M.Manifold.hull_points(np.array(점들(b, 0) + 점들(b, 1.4) + 점들(sx(0.5, 0.15), 2.1) + 점들(sx(1.3, 0.3), 2.5)))
    m = m - 기둥(사각(-1, -1, 8, 1.0), 1.7, 5)
    return m, "두께 2.5 · 옆 비탈 1.4→2.5 · 아래 턱 y<1.0 은 1.7"

def p31():
    """회색 축: 팔각판 + 솟은 원면(세로 홈) + 목 + 누운 원통 축(끝 고리 홈)."""
    m = 둥판(팔각(2.75, 6.4, 3.7, 4.0, 0.85), 0, 2.0, 0.25) + 둥판(원(2.75, 6.4, 1.55), 0, 2.4, 0.15)
    m = m - 기둥(사각(2.65, 6.3, 2.85, 7.8), 2.1, 3)
    m = m + 둥판(사각(1.9, 3.5, 3.6, 4.6), 0, 1.8, 0.2) + 원통y(2.7, 0.75, 1.1, 3.7, 0.7) + 원통y(2.7, 0.75, 0.9, 1.1, 0.55) + 원통y(2.7, 0.75, 0.35, 0.9, 0.65)
    return m, "팔각판 2.0 · 원면 2.4 · 축 반지름 0.7(폭에서) 바닥에 닿게 누움"

def p33():
    """흰 껍데기(허리 뒤 B1-11 로 추정, 속 쪽이 보이게 놓임): 몸통 + 오목한 안쪽 + 솟은 윗 테 + 아래 경첩 마디 둘."""
    m = 둥판([(1.0, 0.4), (6.2, 0.4), (6.4, 6.0), (0.9, 6.0)], 0, 3.5, 0.4) - 기둥(사각(1.5, 2.5, 5.9, 5.3), 2.0, 5)
    m = m + 둥판(사각(2.2, 5.3, 6.5, 6.9), 0, 3.9, 0.5)                                 # 윗 테(밝은 띠 둘 = 둥근 테)
    m = m - 기둥(사각(2.4, 0.8, 5.1, 2.3), 2.6, 5)                                        # 경첩 자리
    for x0, x1 in ((2.6, 3.3), (3.6, 5.0)): m = m + 원통x(x0, x1, 1.6, 2.6, 0.6)             # 경첩 마디(사진 아래 밝은 원통 둘)
    return m, "껍데기 3.5 · 안쪽 오목 1.5 · 윗 테 3.9 · 경첩 원통 r 0.6 — 형태 자체가 추정(가장 불확실)"

def p34():
    """앞치마 한 쌍(B2-13): 오각판 둘 + 노란 블록 자리(오목 창 + 둘레 홈) + 가로 슬롯 관통 + 가운데 경첩(마디 셋)."""
    T = 1.3; 왼 = [(0.9, 1.9), (6.1, 0.05), (6.1, 7.7), (1.3, 7.9), (0.9, 7.5)]; 오 = 거울x(왼, 7.95)
    m = 둥판(왼, 0, T, 0.35) + 둥판(오, 0, T, 0.35)
    for s in (1, -1):
        f = (lambda x: x) if s == 1 else (lambda x: 15.9 - x)
        a, b = sorted((f(1.9), f(5.1)))
        m = m - 기둥(사각(a, 2.9, b, 6.0), T - 0.45, T + 1)                                         # 블록 자리
        m = m - (기둥(사각(a - 0.45, 2.45, b + 0.45, 6.45), T - 0.2, T + 1) - 기둥(사각(a - 0.3, 2.6, b + 0.3, 6.3), -1, T + 2))   # 둘레 홈
        a2, b2, y2 = (2.4, 4.4, 4.35) if s == 1 else (11.0, 12.9, 4.65)                          # 슬롯(오른쪽은 사진대로 약간 위 · 안쪽)
        m = m - 기둥(사각(a2, y2, b2, y2 + 0.4), -1, T + 1)
    m = m + 둥판(사각(6.0, 6.0, 9.9, 7.4), 0, 0.9, 0.2)
    for x0, x1 in ((6.1, 6.9), (7.55, 8.35), (9.0, 9.8)): m = m + 원통x(x0, x1, 6.8, 0.9, 0.9)
    return m, "판 1.3 · 블록 자리 0.45 · 경첩 원통 반지름 0.9"

def 판넬판(바깥, 안, T, 솟음):
    """35 · 36 왼쪽: 판 + 솟은 안쪽 판넬 + 둘레 홈."""
    m = 둥판(바깥, 0, T, 0.35) + 둥판(사각(*안), 0, T + 솟음, 0.15)
    x0, y0, x1, y1 = 안; return m - (기둥(사각(x0 - 0.25, y0 - 0.25, x1 + 0.25, min(y1, 99) + 0.25), T - 0.3, T + 1) - 기둥(사각(x0, y0, x1, y1), -1, T + 5))
def p35():
    m = 판넬판([(0.6, 0.4), (6.0, 0.4), (6.1, 7.2), (0.7, 7.2)], (1.6, 2.0, 4.9, 7.2), 1.6, 0.5)
    return m - 기둥(사각(-1, -1, 8, 1.0), 1.3, 5), "판 1.6 · 판넬 +0.5 · 홈 0.3 · 아래 띠 −0.3"

def p36():
    """허리 앞 틀(B2-12 + 옆 판): 옆 판넬판 + 창틀 둘(오목 창) + 가운데 기둥(슬롯 둘) + 사타구니 끝."""
    m = 판넬판([(0.3, 3.1), (5.9, 3.1), (5.9, 10.2), (0.4, 10.2)], (1.4, 5.0, 4.6, 10.2), 1.8, 0.5)
    틀 = [(6.2, 3.3), (11.4, 1.8), (11.6, 9.3), (6.4, 9.3)]
    for poly, 창 in ((틀, (7.2, 5.2, 11.0, 8.4)), (거울x(틀, 13.2), (15.4, 5.2, 19.2, 8.4))):
        m = m + 둥판(poly, 0, 2.2, 0.35) - 기둥(사각(*창), 1.2, 3)
    m = m + 둥판(사각(11.6, 1.0, 14.8, 10.5), 0, 3.0, 0.3) + 둥판([(12.0, 0.1), (14.3, 0.1), (14.6, 1.2), (11.8, 1.2)], 0, 2.2, 0.2)
    for y0, y1 in ((4.1, 5.9), (2.0, 3.3)): m = m - 기둥(사각(12.3, y0, 13.9, y1), 1.8, 4)
    return m, "옆판 1.8 · 창틀 2.2(창 깊이 1.0) · 가운데 3.0(슬롯 1.2) — 사진 한 덩어리를 부품 셋으로 읽음"

def p39():
    """흰 잎 모양: 윗몸 = 바닥 윤곽 → 평평한 윗 깎은면으로 가는 층 hull, 아래 끝 = 낮은 쐐기."""
    아래0 = [(0.9, 3.7), (4.1, 3.6), (5.0, 6.0), (5.0, 10.0), (4.7, 12.6), (1.9, 12.6), (0.7, 10.0), (0.7, 6.0)]
    위 = 층((아래0, 0), (아래0, 1.2), ([(1.6, 4.0), (3.9, 4.0), (4.5, 6.5), (4.5, 12.2), (2.1, 12.2), (1.4, 9.5)], 2.3), ([(2.3, 4.3), (3.8, 4.3), (4.1, 9.5), (4.1, 12.0), (2.4, 12.0)], 2.7))
    끝 = 층(([(1.7, 0.2), (3.7, 0.2), (4.0, 3.9), (1.2, 3.9)], 0), ([(2.1, 0.5), (3.3, 0.5), (3.5, 3.9), (1.7, 3.9)], 1.7))
    return 위 + 끝, "윗몸 2.7(볏) · 아래 끝 1.7 — 단면 모양 추정"

def p40():
    m = 둥판(사각(0.7, 0.6, 3.8, 5.4), 0, 3.0, 0.3) - 기둥(사각(-1, -1, 5, 1.3), 2.6, 5) - 기둥(사각(1.1, 4.9, 3.1, 6), 2.0, 5)
    return m, "블록 3.0 · 아래 띠 −0.4 · 위 홈 1.0"

def 노랑(x0, y0, x1, y1):
    """41 · 42 노란 블록: 둥근 상자 + 아래쪽 비탈(사진 아래 어두운 띠)."""
    b = 둥사각(x0, y0, x1, y1, 0.45); t = 둥사각(x0 + 0.2, y0 + 0.5, x1 - 0.2, y1 - 0.15, 0.3)
    return M.Manifold.hull_points(np.array(점들(b, 0) + 점들(b, 1.1) + 점들(t, 1.8))), "두께 1.8 · 아래 비탈 0.5"
def p41(): return 노랑(0.4, 0.7, 4.0, 4.1)
def p42(): return 노랑(0.4, 0.7, 4.0, 4.1)

def p43():
    """회색 둥근 판: 테 + 오목 안쪽 + 가로 갈비 넷."""
    m = 둥판(둥사각(0.6, 0.4, 3.0, 7.6, 0.45), 0, 2.0, 0.3) - 기둥(사각(0.95, 0.8, 2.65, 7.2), 1.7, 3)
    for y in (1.9, 3.3, 4.7, 6.1): m = m + 기둥(사각(0.9, y - 0.12, 2.7, y + 0.12), 1.0, 1.9)
    for x in (0.6, 3.0): m = m - 기둥(원(x, 4.4, 0.25, 16), -1, 3)                        # 양옆 작은 파임(사진 가운데 높이)
    return m, "판 2.0 · 안쪽 오목 0.3 · 갈비 · 옆 파임 — 사진에서 흐릿"

짓개 = {23: p23, 24: p24, 28: p28, 30: p30, 31: p31, 33: p33, 34: p34, 35: p35, 36: p36, 39: p39, 40: p40, 41: p41, 42: p42, 43: p43}

# ---------- 검사 · 그림 ----------
def 마스크(n, im, lab):
    x0, y0, x1, y1 = 목록[n]["상자"]; sub = lab[y0:y1, x0:x1]; k = np.bincount(sub[sub > 0]).argmax(); return sub == k
def 윗IoU(m, mask):
    H, W = mask.shape; yy, xx = np.mgrid[0:H, 0:W]; P = np.c_[(xx.ravel() + 0.5) * MM, (H - yy.ravel() - 0.5) * MM]; c = np.zeros(len(P), int)
    for p in m.project().to_polygons(): c += Path(np.asarray(p)).contains_points(P)
    a = (c % 2 == 1).reshape(H, W); return float((a & mask).sum() / max((a | mask).sum(), 1))
def 저장(m, fn):
    g = m.to_mesh(); trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False).export(fn); 닫힘 = bool(trimesh.load(fn).is_watertight)
    for 양 in (0.02, 0.05):
        if 닫힘: break
        부채나누기(m, 양).export(fn); 닫힘 = bool(trimesh.load(fn).is_watertight)
    return 닫힘

if __name__ == "__main__":
    im = np.array(Image.open(os.path.join(D, "d_egx01_j1.jpg")).convert("RGB")).astype(float)
    lab, _ = ndimage.label(J.전경(im)); 결과 = {}; 타일 = []
    for n, f in 짓개.items():
        m, 가정 = f(); fn = os.path.join(OUT, "부품_%02d.stl" % n); 닫힘 = 저장(m, fn); iou = 윗IoU(m, 마스크(n, im, lab))
        결과[n] = dict(닫힘=닫힘, 윗실루엣IoU=round(iou, 3), 크기mm=np.round(trimesh.load(fn).extents, 1).tolist(), 가정=가정, 도형=f.__doc__ or 짓개[n].__doc__)
        print(n, 결과[n]["닫힘"], 결과[n]["윗실루엣IoU"], 결과[n]["크기mm"])
        x0, y0, x1, y1 = 목록[n]["상자"]; 색 = np.array(목록[n]["색rgb"]) if 목록[n]["색"] != "흰" else np.array([0.86, 0.89, 0.88])
        ph = Image.fromarray(im[y0:y1, x0:x1].astype(np.uint8)); s = 220 / max(ph.size); ph = ph.resize((max(1, int(ph.size[0] * s)), max(1, int(ph.size[1] * s))), Image.LANCZOS)
        pt = Image.new("RGB", (230, 230), (240, 240, 240)); pt.paste(ph, ((230 - ph.size[0]) // 2, (230 - ph.size[1]) // 2))
        t = Image.new("RGB", (690, 246), "white"); t.paste(pt, (0, 16))
        t.paste(Image.fromarray(J.그림(trimesh.load(os.path.join(J.OUT, "부품_%02d.stl" % n)), 색, 230)), (230, 16)); t.paste(Image.fromarray(J.그림(trimesh.load(fn), 색, 230)), (460, 16))
        ImageDraw.Draw(t).text((4, 2), "%02d  photo | stage1 | stage2   IoU %.2f  %s" % (n, iou, "closed" if 닫힘 else "OPEN"), fill=(0, 0, 0)); 타일.append(t)
    cols = 3; rows = (len(타일) + cols - 1) // cols; G = Image.new("RGB", (690 * cols + 8 * (cols - 1), 246 * rows), "white")
    for j, t in enumerate(타일): G.paste(t, ((j % cols) * 698, (j // cols) * 246))
    G.save(os.path.join(OUT, "갤러리_팔허리.png"))
    json.dump(dict(뺌={"16": "이미 조립된 팔(여러 부품) — 뺌"}, 부품={str(k): v for k, v in 결과.items()}), open(os.path.join(OUT, "팔허리.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
