# -*- coding: utf-8 -*-
"""EG RX-78-2 2 단계 「하위 도형 분해」 — 다리 · 발 무리(부품 44~54) (2026-09-27).

    python 그룹_다리발.py -> out/키트/EG_RX78/2단계/부품_NN.stl · 갤러리_다리발.png · 다리발.json

32(조립된 다리 통째)는 건너뜀 — 낱 부품이 아니다.
좌표: 부품 나열 사진(d_egx01_j1.jpg) 상자 −4 px 을 원점으로 u(오른쪽) · w(아래) mm, 척도 0.17 mm/px.
모델 좌표 = (u, −w, z) · z = 사진 쪽(겉면) 높이. 윤곽은 사진 마스크에서, 안쪽 도형 위치는 mm 격자 확대본에서 읽었다.
깊이(z 값: 판 두께 · 단차 · 홈 깊이 · 원기둥 반지름 중 사진 면에 수직인 것)는 모두 가정 — 사진에 깊이가 없다.
설명서 6 단계로 읽은 이름: 44/45 정강이 반쪽(B 16/17) · 46 무릎 관절(A 22) · 52 발바닥(A4 25, 빨강 쟁반) · 53 발등(B 19)
· 54 발목 관절(A 24, 공 + 요람) · 그 밖(47/49 빔사벨 손잡이 · 48 U 틀 · 50 백팩 · 51 갈래+원판)은 모양으로만 읽음."""
import os, sys, json, numpy as np, trimesh, manifold3d as M
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage import measure
from scipy.spatial.transform import Rotation as Rot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260925")
import 전부품 as J, 정강이2 as S2, 방패 as B
import 디테일대조 as DD
from 메시출력 import 부채나누기

D = J.D; OUT = os.path.join(D, "2단계"); os.makedirs(OUT, exist_ok=True)
MM = J.MM; 여백 = 4; 번호들 = [44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54]
IM = np.array(Image.open(os.path.join(D, "d_egx01_j1.jpg")).convert("RGB")).astype(float)
목록 = {e["번호"]: e for e in json.load(open(os.path.join(D, "전부품", "목록.json"), encoding="utf-8"))}
_lab = ndimage.label(J.전경(IM))[0]

# ---------- 도형 ----------
def 상자틀(n):
    x0, y0, x1, y1 = 목록[n]["상자"]; return x0 - 여백, y0 - 여백, x1 + 여백, y1 + 여백
def 마스크(n):
    x0, y0, x1, y1 = 상자틀(n); L = _lab[y0:y1, x0:x1]; ids, c = np.unique(L[L > 0], return_counts=True)
    return ndimage.binary_fill_holes(L == ids[c.argmax()])
def 윤곽(mask, 매끈=2.0):
    """마스크 → CrossSection (u, −w) mm. 4 배 올림 + 둘레 가우스 + RDP (전부품.짓기 와 같은 길)."""
    big = ndimage.gaussian_filter(ndimage.zoom(mask.astype(float), 4, order=1), 2.0) > 0.5; polys = []
    for c in measure.find_contours(np.pad(big, 1).astype(float), 0.5):
        if len(c) < 12: continue
        c = ndimage.gaussian_filter1d(c[:-1] - 1, 매끈, axis=0, mode="wrap"); P = np.c_[c[:, 1], -c[:, 0]] / 4 * MM
        P = B.rdp(np.vstack([P, P[:1]]), 0.04)[:-1]
        if len(P) >= 3: polys.append(P.tolist())
    return M.CrossSection(polys, M.FillRule.EvenOdd)
def 판(cs, z0, z1): return cs.extrude(z1 - z0).translate([0, 0, z0])
def 다각(pts): return M.CrossSection([B.반시계(np.c_[np.asarray(pts, float)[:, 0], -np.asarray(pts, float)[:, 1]]).tolist()])
def 상자(u0, w0, u1, w1, z0, z1): return 판(다각([(u0, w0), (u1, w0), (u1, w1), (u0, w1)]), z0, z1)
def 원(u, w, r, n=48): return 다각([(u + r * np.cos(t), w + r * np.sin(t)) for t in np.linspace(0, 2 * np.pi, n, endpoint=False)])
def 원기둥(u, w, r, z0, z1): return 판(원(u, w, r), z0, z1)
def 공(u, w, z, r): return M.Manifold.sphere(r, 48).translate([u, -w, z])
def 돌림(윤, u, w0, z, 방향=(0, 1)):
    """축 대칭 도형: 윤 = [(축 위치 mm, 반지름)] · 축은 사진 면에 누움(방향 (du, dw)) · 시작점 (u, w0) · 축 높이 z."""
    윤 = np.asarray(윤, float); pts = [(0, 윤[0, 0])] + [(r, s) for s, r in 윤] + [(0, 윤[-1, 0])]
    m = M.CrossSection([B.반시계(np.array(pts)).tolist()]).revolve(48)       # 축 = z
    du, dw = 방향; a = np.degrees(np.arctan2(du, dw))
    R = (Rot.from_euler("z", a, degrees=True) * Rot.from_euler("x", 90, degrees=True)).as_matrix()   # z → (du, −dw)
    return m.transform(np.c_[R, [u, -w0, z]])
def 둥글(m, mask, r, z위, 아래=None):
    """가장자리 둥글림: 윤곽 가까운(거리 < r) 윗면 정점을 사분원으로 내린다(정강이2 와 같은 방식). 아래 = 이 높이 아래 정점은 두지 않음."""
    거리 = ndimage.distance_transform_edt(np.pad(mask, 2)) * MM; 아래 = z위 * 0.5 if 아래 is None else 아래
    def f(V):
        rr = np.clip(-V[:, 1] / MM + 2 - 0.5, 0, 거리.shape[0] - 1); cc = np.clip(V[:, 0] / MM + 2 - 0.5, 0, 거리.shape[1] - 1)
        d = ndimage.map_coordinates(거리, [rr, cc], order=1); 위 = np.clip((V[:, 2] - 아래) / max(z위 - 아래, 1e-6), 0, 1)
        return np.c_[V[:, 0], V[:, 1], V[:, 2] - 위 * r * (1 - np.sqrt(np.clip(1 - (1 - np.clip(d / r, 0, 1)) ** 2, 0, 1)))]
    return m.refine_to_length(0.25).warp_batch(f)

# ---------- 부품 ----------
가정 = {}
def 정강이(n):
    """정강이2.짓기(L=60 정규 · x=두께 y=u z=v) 를 실제 크기(마스크 136 px × 0.17)로 줄이고 (u, v, 두께) 로 돌린다. 45 = 거울."""
    m, _ = S2.짓기(); k = 136 * MM / S2.L; s = -1.0 if n == 45 else 1.0
    가정[n] = dict(방법="정강이2.py 그대로(바닥판·돔·무릎원판·발목탭·브래킷)", 축척=round(k, 4), 거울=(n == 45), 반두께mm=round(S2.반두께 * 136 * MM, 2))
    return m.transform(np.array([[0, s, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]], float) * np.array([[k], [k], [k]]))

def p46(mask):
    """무릎 관절(A 22, 회색 H 토막): 바닥판 2.6 + 가운데 등뼈 3.4 + 팔 위 가로 홈 둘 + 가운데 옆 홈."""
    t, 등 = 2.6, 3.4; 가정[46] = dict(판=t, 등뼈=등, 홈깊이=0.4)
    m = 판(윤곽(mask), 0, t) + 상자(3.9, 1.1, 5.9, 8.0, t - 0.2, 등)
    for w in (2.5, 6.3): m = m - 상자(0.8, w - 0.2, 3.9, w + 0.2, t - 0.4, 등 + 1)
    for w in (2.2, 3.4, 5.4, 6.6): m = m - 상자(4.1, w - 0.12, 5.7, w + 0.12, 등 - 0.3, 등 + 1)   # 등뼈 가로 골(사진 줄무늬)
    m = m - 상자(0.5, 4.3, 2.2, 5.0, -1, t + 1)                                                   # 왼쪽 가운데 틈(관통)
    return 둥글(m, mask, 0.4, 등)

def 손잡이(mask, n):
    """빔사벨 손잡이(47/49): 축 대칭. 윤곽 반지름은 사진 폭에서, 나머지는 원기둥."""
    ys, xs = np.nonzero(mask); w0, w1 = ys.min() * MM, (ys.max() + 1) * MM; u = (xs.mean() + 0.5) * MM; L = w1 - w0
    r몸 = 0.68      # 47 확대본 몸통 폭 8 px(1.36 mm) — 같은 부품인 49 는 마스크가 번져 1.02 로 읽혔다(첫 판) → 한 값으로
    윤 = [(0, 0.2), (0.25, r몸 * 0.8), (0.6, r몸), (0.12 * L, r몸), (0.12 * L, r몸 * 1.15), (0.17 * L, r몸 * 1.15), (0.17 * L, r몸),
                     (0.72 * L, r몸), (0.72 * L, r몸 * 1.45), (0.78 * L, r몸 * 1.45), (0.78 * L, r몸 * 1.25), (0.83 * L, r몸 * 1.25), (0.83 * L, r몸 * 1.45),
                     (0.86 * L, r몸 * 1.45), (0.86 * L, r몸 * 0.9), (L - 0.3, r몸 * 0.9), (L, 0.2)]
    가정[n] = dict(방법="회전체(길이는 마스크 · 몸 반지름 0.68 고정 · 고리 위치는 길이 비)", 몸반지름=round(r몸, 2))
    return 돌림(윤, u, w0, r몸 * 1.45)

def p48(mask):
    """U 틀: 아래 가로대(칸 셋 오목) + 옆벽 둘 + 위 귀 둘(둥근 머리). 가운데는 뚫림(사진에서 바닥이 보인다)."""
    t대, t벽, t귀 = 2.4, 3.0, 3.6; 가정[48] = dict(가로대=t대, 옆벽=t벽, 귀=t귀, 칸깊이=0.9)
    m = 판(윤곽(mask), 0, t대) - 상자(3.6, 0.0, 9.8, 7.0, -1, t대 + 1)
    for u0, u1 in ((4.0, 5.9), (6.1, 7.9), (8.1, 9.9)): m = m - 상자(u0, 7.3, u1, 9.5, t대 - 0.9, t대 + 1)
    for u0, u1 in ((2.6, 3.6), (9.8, 10.8)): m = m + (상자(u0, 3.0, u1, 7.6, 0, t벽) ^ 판(윤곽(mask), -1, 9))
    for u0, u1 in ((1.9, 3.5), (9.9, 11.4)):
        c = (u0 + u1) / 2; h = (u1 - u0) / 2
        귀 = 상자(u0, 2.2, u1, 4.6, 0, t귀) + 원기둥(c, 2.2, h, 0, t귀)
        m = m + (귀 ^ 판(윤곽(mask), -1, 9))
    return 둥글(m, mask, 0.4, t귀, 1.0)

def p50(mask):
    """백팩: 몸통 토막 4.2 + 어깨 날개(얇게 2.4) + 둥근 무늬 홈 둘 + 가운데 구멍 + 아래 세로 홈 + 추진기 노즐 둘(회전체, 아래로)."""
    t, 날개 = 4.2, 2.4; 가정[50] = dict(몸통=t, 날개=날개, 노즐축높이=2.0, 무늬홈=0.35)
    몸 = 판(윤곽(mask), 0, t) - 상자(0, 9.7, 20, 20, -1, t + 1)                                 # 노즐 자리는 회전체로
    m = 몸 - (상자(0, 3.1, 3.6, 12, t - (t - 날개), t + 1) + 상자(13.2, 3.1, 20, 12, 날개, t + 1))   # 날개 낮춤
    m = m - (상자(3.6, 0, 13.2, 1.8, t - 0.5, t + 1))                                            # 윗면 턱
    for u in (5.0, 10.4):
        m = m - (원기둥(u, 4.6, 1.05, t - 0.35, t + 1) - 원기둥(u, 4.6, 0.75, t - 1, t + 2))      # 둥근 무늬(고리 홈)
    m = m - 원기둥(7.7, 4.9, 0.5, t - 2.0, t + 1) - 상자(7.1, 6.8, 8.3, 9.8, t - 0.6, t + 1)
    for u in (5.1, 10.0):
        m = m + 돌림([(0, 1.1), (0.4, 1.2), (1.4, 1.35), (2.4, 1.45), (2.8, 1.25), (3.0, 0.6)], u, 9.5, 2.0)
    return 둥글(m, mask, 0.45, t, 1.5)

def p51(mask):
    """갈래 + 원판: 갈래 · 줄기 판 1.4 + 원판 원기둥 2.4(가운데 구멍 · 둘레 턱)."""
    t, 원t = 1.4, 2.4; 가정[51] = dict(판=t, 원판=원t)
    m = 판(윤곽(mask), 0, t) + 원기둥(3.3, 6.9, 1.85, 0, 원t) - 원기둥(3.3, 6.9, 0.45, -1, 원t + 1)
    m = m - (원기둥(3.3, 6.9, 1.3, 원t - 0.3, 원t + 1) - 원기둥(3.3, 6.9, 0.8, 원t - 1, 원t + 2))
    return 둥글(m, mask, 0.35, t, 0.4)

def p52(mask):
    """발바닥(빨강 쟁반 · 사진은 안쪽이 위): 바깥 경사벽(아래 넓게) + 안 주머니 + 안 바닥 판 테두리 + コ 갈비 + 꽂이 기둥."""
    h, 벽, 깊 = 3.6, 1.1, 2.4; 가정[52] = dict(높이=h, 벽=벽, 주머니깊이=깊, 경사=0.7)
    cs = 윤곽(mask, 4.0)
    # 경사벽: 바닥 윤곽과 0.7 mm 안으로 당긴 윗 윤곽의 볼록 껍질 (첫 판은 층층 오프셋 → 계단 줄이 보였다).
    # ponytail: 볼록 껍질이라 윤곽의 작은 오목(오른쪽 아래 턱)은 사라진다 — 오목을 살리려면 거리장 warp 로.
    m = (판(cs, 0, 0.01) + 판(cs.offset(-0.7, M.JoinType.Round), h - 0.01, h)).hull()
    안 = cs.offset(-벽, M.JoinType.Round)
    m = m - 판(안, h - 깊, h + 1)
    m = m + (상자(3.0, 3.0, 11.8, 8.0, h - 깊 - 0.1, h - 깊 + 0.6) - 상자(3.6, 3.6, 11.2, 7.4, h - 깊, h))      # 안 바닥 테 판
    m = m + 상자(8.6, 4.0, 11.0, 4.6, h - 깊 - 0.1, h - 깊 + 0.9) + 상자(8.6, 6.4, 11.0, 7.0, h - 깊 - 0.1, h - 깊 + 0.9) + 상자(8.6, 4.0, 9.2, 7.0, h - 깊 - 0.1, h - 깊 + 0.9)
    m = m + (원기둥(12.9, 5.9, 0.8, h - 깊 - 0.1, h - 0.4) - 원기둥(12.9, 5.9, 0.4, h - 깊, h))
    m = m + (상자(14.4, 1.0, 16.2, 12, h - 깊 - 0.1, h - 1.0) ^ 판(안, -1, 9))                       # 뒤꿈치 턱
    return m

def p53(mask):
    """발등(흰 · 사진은 아래에서 본 면): 바닥판 + 발목 쪽 오목 틀(구멍 둘 · 창) + 발끝 덩이(높고 끝을 깎음)."""
    t, 끝 = 2.0, 4.2; 가정[53] = dict(판=t, 발끝=끝, 오목=0.8)
    cs = 윤곽(mask, 3.0); m = 판(cs, 0, t)
    m = m - (판(cs.offset(-1.0, M.JoinType.Round), t - 0.8, t + 1) ^ 상자(0, 0, 9.2, 12, -2, t + 2))
    m = m - 원기둥(3.3, 3.6, 0.4, -1, t + 1) - 원기둥(3.3, 6.3, 0.4, -1, t + 1) - 상자(7.4, 4.0, 8.9, 6.8, -1, t + 1)
    발끝 = 판(cs, 0, 끝) ^ 상자(9.2, 0, 20, 12, -1, 끝 + 1) + (판(cs, 0, 끝) ^ 판(다각([(6.2, 0.8), (9.3, 0.8), (9.3, 3.8), (6.2, 3.0)]), -1, 9))
    m = m + 발끝
    def 깎(V):                                                                                   # 발끝 윗면: 오른쪽 끝으로 1.2 mm 낮춤
        k = np.clip((V[:, 0] - 11.0) / 2.4, 0, 1) * np.clip((V[:, 2] - t) / (끝 - t), 0, 1); return np.c_[V[:, 0], V[:, 1], V[:, 2] - 1.2 * k]
    return 둥글(m.refine_to_length(0.3).warp_batch(깎), mask, 0.4, 끝, 1.0)

def p54(mask):
    """발목 관절(A 24): 요람 토막(U 파임 · 호 홈) + 공 관절 + 옆 막대 + 막대 끝 공."""
    t = 3.0; 가정[54] = dict(토막=t, 공r=1.45, 막대r=0.45)
    토막 = 판(윤곽(mask), 0, t) - 상자(6.6, 0, 20, 20, -1, t + 1)
    토막 = 토막 - 원기둥(4.6, 2.0, 1.25, -1, t + 1) - 상자(3.35, 0, 5.85, 2.0, -1, t + 1)             # U 파임
    토막 = 토막 - ((원기둥(4.6, 2.0, 2.45, t - 0.35, t + 1) - 원기둥(4.6, 2.0, 2.1, t - 1, t + 2)) ^ 상자(0, 2.0, 20, 20, -2, t + 2))
    m = 둥글(토막, mask, 0.35, t, 0.8)
    m = m + 공(7.9, 5.8, 1.5, 1.45) - 원기둥(7.9, 5.8, 0.3, 2.3, 4)
    m = m + 돌림([(0, 0.45), (3.0, 0.45)], 6.2, 2.85, 1.5, (1, 0)) + 공(9.6, 2.85, 1.5, 0.55)
    return m

짓개 = {46: p46, 48: p48, 50: p50, 51: p51, 52: p52, 53: p53, 54: p54}

# ---------- 그림 ----------
빛 = np.array([-0.45, 0.5, 0.74]); 빛 /= np.linalg.norm(빛)
R빗 = Rot.from_euler("zx", [20, -32], degrees=True).as_matrix()          # 비스듬히 ~30°
def 그림(tm, 색, W=240, R=R빗):
    V = tm.vertices @ R.T; N = tm.face_normals @ R.T
    x0, x1, y0, y1 = V[:, 0].min(), V[:, 0].max(), V[:, 1].min(), V[:, 1].max(); s = max(x1 - x0, y1 - y0) / (W - 16)
    zb, tid = DD.래스터(V - [(x0 + x1) / 2, (y0 + y1) / 2, 0], tm.faces, W / 2, W / 2, s, W)
    img = np.ones((W, W, 3)) * 0.93; A = tid >= 0
    img[A] = np.array(색) * (np.clip(N[tid[A]] @ 빛, 0, 1) * 0.7 + 0.3)[:, None]
    nb = np.zeros((W, W, 3)); nb[A] = N[tid[A]]; z = np.where(A, zb, 0.0); 선 = np.zeros((W, W), bool)
    for ax in (0, 1):
        선 |= A & np.roll(A, 1, ax) & ((np.abs(z - np.roll(z, 1, ax)) > 3 * s) | ((nb * np.roll(nb, 1, ax)).sum(-1) < np.cos(np.radians(30))))
    img[선] *= 0.55
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

def 내보내기(m, fn):
    g = m.to_mesh(); trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False).export(fn)
    닫힘 = bool(trimesh.load(fn).is_watertight)
    for 양 in (0.02, 0.04, 0.08):
        if 닫힘: break
        부채나누기(m, 양).export(fn); 닫힘 = bool(trimesh.load(fn).is_watertight)
    return 닫힘

if __name__ == "__main__":
    결과 = {}; 타일 = []
    for n in 번호들:
        mask = 마스크(n)
        m = 정강이(n) if n in (44, 45) else 손잡이(mask, n) if n in (47, 49) else 짓개[n](mask)
        fn = os.path.join(OUT, "부품_%02d.stl" % n); 닫힘 = 내보내기(m, fn); tm = trimesh.load(fn)
        결과[n] = dict(닫힘=닫힘, 크기mm=np.round(tm.extents, 1).tolist(), 부피mm3=round(m.volume(), 1), 가정=가정.get(n))
        print(n, 결과[n])
        색 = np.array(목록[n]["색rgb"]); 색 = np.clip(색 * 1.1, 0, 1) if 색.max() > 0.5 else np.clip(색 * 1.6, 0, 1)
        x0, y0, x1, y1 = 상자틀(n); ph = Image.fromarray(IM[y0:y1, x0:x1].astype(np.uint8)); k = 224 / max(ph.size)
        ph = ph.resize((max(1, int(ph.size[0] * k)), max(1, int(ph.size[1] * k))), Image.LANCZOS); pt = Image.new("RGB", (240, 240), (240, 240, 240)); pt.paste(ph, ((240 - ph.size[0]) // 2, (240 - ph.size[1]) // 2))
        t = Image.new("RGB", (720, 258), "white"); t.paste(pt, (0, 18)); t.paste(그림(trimesh.load(os.path.join(D, "전부품", "부품_%02d.stl" % n)), 색), (240, 18)); t.paste(그림(tm, 색), (480, 18))
        ImageDraw.Draw(t).text((4, 3), "%02d  photo | stage1 | stage2   %s  %s" % (n, "x".join("%.1f" % v for v in tm.extents), "closed" if 닫힘 else "OPEN"), fill=(0, 0, 0)); 타일.append(t)
    G = Image.new("RGB", (1440, 258 * ((len(타일) + 1) // 2)), "white")
    for j, t in enumerate(타일): G.paste(t, ((j % 2) * 720, (j // 2) * 258))
    G.save(os.path.join(OUT, "갤러리_다리발.png"))
    json.dump(dict(건너뜀={32: "조립된 다리 통째 — 낱 부품 아님"}, 척도_mm_px=MM, 부품=결과), open(os.path.join(OUT, "다리발.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("닫힘 %d / %d" % (sum(v["닫힘"] for v in 결과.values()), len(결과)))
