# -*- coding: utf-8 -*-
"""EG RX-78-2 — 부품 낱개가 아니라 조립 · 가동 · 포징으로 검증 (2026-09-27).

    python EG_조립.py           -> out/키트/EG_RX78/조립/  (조립.json · 조립_사진대조.png · 가동한계.png · 포징.png)

몸 좌표(체계 척도 mm): X = 로봇 왼쪽(정면에서 보면 오른쪽) · Y = 로봇 등 쪽 · Z = 위 · 바닥 Z = 0.
부품 파일은 안 고친다 — 부품마다 회전(지역 축 → 몸 축) + 이동만. 오른쪽(X<0) 팔다리를 놓고 왼쪽은 X 거울.
지역 좌표: 사진 부품(j1) 은 x 오른쪽 · y 위 · z 사진 쪽(두께). 발 52/53/54 · 정강이 44/45 · 방패 · 라이플은 이미 짝 좌표.

검사
 ① 그래프: 모든 부품이 몸통 10 까지 이어진다.
 ② 연결: 볼/핀 관절은 자식의 볼(자동 검출)이나 핀 반지름으로 부모 속 「받침(소켓 · 구멍)」을 찾는다 —
    부모 부피를 복셀로 바꿔 바깥 거리장(EDT) · 둘레 감쌈 비율로. 감쌈 ≥ 0.5 · 틈 0.05~0.3 이면 받침 있음.
    놓인 자리에서 부피 겹침(≤ 0.5 mm³) · 최소 틈(≤ 0.3)도 잰다.
 ③ 가동: 관절 아래 부품 전부를 축으로 3° 씩 돌려 나머지와 겹침이 0° 때보다 0.5 mm³ 넘게 늘면 한계.
 ④ 포징: 부피 × PLA 1.24 g/cm³ → 무게중심 · 발바닥 지지 다각형 · 관절 토크(N·mm). 체계 · ×1.9 둘 다.
"""
import os, sys, re, glob, json, numpy as np, trimesh, manifold3d as M
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from scipy.spatial import ConvexHull
from matplotlib.path import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 발3 as F3, 정강이 as S1, 정강이3 as S3

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, "..", "out", "키트", "EG_RX78"); SRC = os.path.join(KIT, "2단계"); OUT = os.path.join(KIT, "조립")
os.makedirs(OUT, exist_ok=True)
글꼴 = ImageFont.truetype("malgun.ttf", 15); 작은 = ImageFont.truetype("malgun.ttf", 12)
K = 1.9; RHO = 1.24e-3          # g/mm³
겹침문턱 = 0.5                  # mm³

# ======================= 부품 읽기 (가장 새 판) =======================
후 = "후" in sys.argv                                   # 고친 부품(부품_NN_조립.stl, EG_조립고침.py)으로 다시 잰다
꼬리 = "_후" if 후 else ("_전" if "전" in sys.argv else "")   # 「전」 = 고친 검사기로 원본을 다시
def 최신():
    best = {}
    for f in glob.glob(os.path.join(SRC, "부품_*.stl")):
        if f.endswith("_조립.stl"): continue
        m = re.match(r"부품_(\d+)(?:_(v\d|무기4))?\.stl", os.path.basename(f)); n = int(m.group(1)); v = m.group(2) or "v2"
        r = {"v2": 2, "v3": 3, "v4": 4, "무기4": 0}[v]
        if n not in best or r > best[n][0]: best[n] = (r, f)
    return {n: trimesh.load(f) for n, (r, f) in best.items()}, {n: os.path.basename(f) for n, (r, f) in best.items()}
P, 파일 = 최신()

# ======================= 놓기 =======================
AX = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}
def 축(s):
    """'X Z -Y' = 지역 x→X · y→Z · z→−Y. 오른손 좌표만(거울은 따로)."""
    cols = [np.array(AX[a[-1]]) * (-1 if a[0] == "-" else 1) for a in s.split()]
    R = np.array(cols, float).T; assert abs(np.linalg.det(R) - 1) < 1e-9, s; return R
F_ = "X Z -Y"      # 앞을 보고 찍힌 부품(z = 앞)
B_ = "-X Z Y"      # 뒤(안쪽)를 보고 찍힌 부품
S_out = "-Y Z -X"  # 옆모습: x = 앞 · z = 바깥(오른쪽)
S_in = "Y Z X"     # 옆모습: z = 안쪽(몸 가운데), x = 뒤

부품들 = {}   # 이름 → dict(n, T 4x4, 무리, 색)
def 놓기(이름, n, R, 중심=None, t=None, 색=(0.88, 0.9, 0.9)):
    R = 축(R) if isinstance(R, str) else np.asarray(R, float)
    if t is None:
        c = P[n].bounds.mean(0); t = np.asarray(중심, float) - R @ c
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = t; 부품들[이름] = dict(n=n, T=T, 색=색); return T
def 점(이름, p):   # 지역 점 → 몸
    T = 부품들[이름]["T"]; return T[:3, :3] @ np.asarray(p, float) + T[:3, 3]

흰, 파, 빨, 노, 회 = (0.9, 0.92, 0.9), (0.2, 0.35, 0.8), (0.8, 0.15, 0.15), (0.95, 0.78, 0.2), (0.45, 0.47, 0.52)
xl = 5.8                                           # 다리 X (오른쪽 = −xl)

# ---- 발 (발3 좌표: x = 발끝 쪽 · y = 폭 · z = 위) · 볼 중심 (Xb, 0, Zb)
Rf = 축("-Y X Z"); Xb, Zb = 9.82, 3.44
tf = np.array([-xl, 0, 0]) - Rf @ np.array([Xb, 0, 0])
for n, c in ((52, 빨), (53, 흰), (54, 회)): 놓기("R%d" % n, n, Rf, t=tf, 색=c)
# 54 요람(U) 속 중심: y = 0 단면에서 복셀 EDT 로 가장 큰 빈 원 (z > 5)
def 요람중심():
    v = P[54]; 표 = trimesh.voxel.creation.voxelize(v, 0.05).fill(); d = 표.matrix; T = 표.transform
    j = int(round((0 - T[1, 3]) / 0.05)); sl = d[:, j, :]
    edt = ndimage.distance_transform_edt(~sl) * 0.05
    xs = np.arange(sl.shape[0]) * 0.05 + T[0, 3]; zs = np.arange(sl.shape[1]) * 0.05 + T[2, 3]
    X_, Z_ = np.meshgrid(xs, zs, indexing="ij"); ok = (Z_ > 5.3) & (Z_ < 7.8) & (X_ < 6.5)
    # U 안: 위로 열렸으니 좌우 벽 사이 · 위로 새지 않는 점 — 좌우 x 방향 양쪽에 벽
    L_ = np.maximum.accumulate(sl, 0); R_ = np.maximum.accumulate(sl[::-1], 0)[::-1]; B_ = np.maximum.accumulate(sl, 1)
    안 = ok & L_ & R_ & B_ & ~sl; e = np.where(안, edt, 0); i = np.unravel_index(e.argmax(), e.shape)
    return np.array([xs[i[0]], 0.0, zs[i[1]]]), float(e.max())
요람, 요람r = 요람중심()
# ---- 정강이 (정강이3 좌표: x = 앞(+u) · y = 위 · z = 두께(45 는 조립R 로 뒤집음))
k3 = S3.k; L1 = S1.L
발목 = np.array([S1.발목구멍[0] * L1 * k3, S1.발목구멍[1] * L1 * k3, 0.0]); 무릎 = np.array([S1.무릎원[0] * L1 * k3, S1.무릎원[1] * L1 * k3, 0.0])
Rs = 축("-Y Z -X")                                  # 정강이 x(앞) → −Y · z → X
요람몸 = Rf @ 요람 + tf
ts = 요람몸 - Rs @ 발목
놓기("R44", 44, Rs, t=ts, 색=흰)
R45 = Rs @ np.array(S3.조립R)[:, :3]; 놓기("R45", 45, R45, t=ts, 색=흰)
무릎몸 = Rs @ 무릎 + ts
# ---- 무릎 관절 46 (j1: y = −w · C 집게 입 (2.55, −2.0) 위 · (2.4, −6.3) 아래 · 축 = z)
R46 = 축("-Y Z -X"); c46 = np.array([2.4, -6.3, 1.4])
놓기("R46", 46, R46, t=무릎몸 - R46 @ c46, 색=회)
무릎위 = 점("R46", [2.55, -2.0, 1.4])
놓기("R43", 43, "Y Z X", 중심=무릎몸 + [0, 2.4, 0.5], 색=회)
# ---- 발목 가드 48 (귀 허브 축 = 지역 x · 중심 w 2.9 → y −2.9) : 54 앞 작은 볼 막대 둘레
놓기("R48", 48, F_, 중심=요람몸 + [0, -2.6, 0.4], 색=흰)
# ---- 허벅지: 30 앞 껍데기 · 33 뒤 판 · 35 · 39 옆 판(역할 추정) · 31 고관절 축
허벅지아래 = 무릎위[2] - 0.6; 고관절 = np.array([-4.3, 0.2, 무릎위[2] + 9.2])
zc = (허벅지아래 + 고관절[2]) / 2
놓기("R30", 30, F_, 중심=[-xl, -1.3, zc], 색=흰)
놓기("R33", 33, B_, 중심=[-xl, 1.5, zc - 1.8], 색=흰)
놓기("R35", 35, S_out, 중심=[-xl - 2.6, 0.1, zc - 1.0], 색=흰)
놓기("R39", 39, S_in, 중심=[-xl + 2.4, 0.1, zc], 색=흰)
놓기("R31", 31, "Y Z X", 중심=[-xl + 0.2, 0.2, 고관절[2] - 2.6], 색=회)
# ---- 허리 · 사타구니
놓기("29", 29, F_, 중심=[0, 0.2, 고관절[2] - 0.8], 색=빨)
놓기("27", 27, "X -Y -Z", 중심=[0, 0.3, 고관절[2] + 2.4], 색=노)
놓기("36", 36, F_, 중심=[0, -1.4, 고관절[2] - 1.0], 색=흰)
놓기("34", 34, F_, 중심=[0, -3.4, 고관절[2] - 3.6], 색=흰)
놓기("41", 41, F_, 중심=[-3.4, -4.5, 고관절[2] - 3.2], 색=노); 놓기("42", 42, F_, 중심=[3.4, -4.5, 고관절[2] - 3.2], 색=노)
놓기("40", 40, B_, 중심=[0, 3.0, 고관절[2] - 0.5], 색=흰)
# ---- 몸통 (배 21 볼 → 허리 27 가운데 고리)
z배 = 고관절[2] + 4.2
놓기("21", 21, "X -Y -Z", 중심=[0, 0.3, z배], 색=빨)
놓기("20", 20, F_, 중심=[0, -3.0, z배 + 0.8], 색=빨)
z가슴 = z배 + 7.5
놓기("10", 10, F_, 중심=[0, 0.3, z가슴], 색=파)
놓기("14", 14, B_, 중심=[0, -0.6, z가슴 + 1.2], 색=파)
놓기("13", 13, F_, 중심=[0, -3.8, z가슴 + 2.0], 색=노)
놓기("22", 22, F_, 중심=[0, 1.6, z가슴 - 2.5], 색=회)
놓기("50", 50, B_, 중심=[0, 5.0, z가슴 + 1.0], 색=회)
놓기("47", 47, F_, 중심=[-2.6, 7.6, z가슴 + 4.0], 색=흰); 놓기("49", 49, F_, 중심=[2.6, 7.6, z가슴 + 4.0], 색=흰)
# ---- 머리
z목 = z가슴 + 6.8
놓기("06", 6, F_, 중심=[0, 0.3, z목], 색=회)
놓기("07", 7, F_, 중심=[0, -0.2, z목 + 3.6], 색=빨)
놓기("08", 8, F_, 중심=[0, 0.3, z목 + 4.6], 색=흰)
놓기("09", 9, F_, 중심=[0, -3.3, z목 + 2.4], 색=흰)
놓기("05", 5, F_, 중심=[0, -3.2, z목 + 6.4], 색=노)
놓기("02", 2, F_, 중심=[0, -2.9, z목 + 8.4], 색=흰)
놓기("01", 1, F_, 중심=[0, -2.2, z목 + 7.2], 색=빨)
# ---- 팔 (오른쪽) — 15 집게가 10 팔 끝 기둥을 문다 · 15 볼이 바깥
어깨 = np.array([-8.2, 0.3, z가슴 + 1.6])
놓기("R15", 15, F_, 중심=어깨 + [-1.2, 0, 0], 색=회)
팔X = 어깨[0] - 4.8
놓기("R12", 12, F_, 중심=[팔X, 0.3, 어깨[2] - 1.5], 색=흰)
놓기("R11", 11, S_out, 중심=[팔X - 2.5, 0.3, 어깨[2] - 0.6], 색=흰)
놓기("R18", 18, S_out, 중심=[팔X, 0.3, 어깨[2] - 6.3], 색=흰)
놓기("R17", 17, S_out, 중심=[팔X, 0.3, 어깨[2] - 10.0], 색=회)
놓기("R19", 19, S_out, 중심=[팔X, 1.8, 어깨[2] - 9.0], 색=회)
팔꿈치 = np.array([팔X, 0.3, 어깨[2] - 10.8])
놓기("R23", 23, S_out, 중심=[팔X - 1.7, 0.3, 팔꿈치[2] - 4.4], 색=흰)
놓기("R24", 24, "Y Z X", 중심=[팔X + 1.7, 0.3, 팔꿈치[2] - 4.4], 색=흰)
손목 = np.array([팔X, 0.3, 팔꿈치[2] - 10.4])
놓기("R26", 26, S_out, 중심=손목 + [0, 0, -2.8], 색=회)

오른쪽 = [k for k in 부품들 if k.startswith("R")]
Mx = np.diag([-1.0, 1, 1, 1])
for k in 오른쪽:
    d = 부품들[k]; 부품들["L" + k[1:]] = dict(n=d["n"], T=Mx @ d["T"], 색=d["색"], 거울=True)
# 거울 짝 없는 부품 목록(오른쪽 하나만 있던 것 → 왼쪽은 X 거울로 만듦)
거울로만듦 = sorted({부품들[k]["n"] for k in 부품들 if k.startswith("L")} - {44, 45, 41, 42})

# ---- 무기(포징 계산에선 뺌): 방패 → 왼 팔뚝 · 라이플 → 오른 주먹
def 무기놓기():
    c24 = 점("L24", P[24].bounds.mean(0))
    놓기("03", 3, "Y Z X", 중심=c24 + [4.4, 0, 2.0], 색=흰)
    T03 = 부품들["03"]["T"]
    for n, c in ((4, 빨), (25, 노)): 부품들["%02d" % n] = dict(n=n, T=T03.copy(), 색=c)
    놓기("28", 28, "Y Z X", 중심=c24 + [1.9, 0, 0], 색=회)
    c26 = 점("R26", P[26].bounds.mean(0))
    놓기("38", 38, "Y Z X", 중심=c26 + [0, -6.0, 0], 색=회)
    T38 = 부품들["38"]["T"]
    for n in (37, 51): 부품들["%02d" % n] = dict(n=n, T=T38.copy(), 색=회)
무기놓기()
무기 = {"03", "04", "25", "28", "37", "38", "51"}
# 놓기는 원본 모양으로 정했다(중심 = 원본 상자 중심) → 고친 부품은 놓은 뒤에 바꿔 끼운다
if 후:
    for f in glob.glob(os.path.join(SRC, "부품_*_조립.stl")):
        n = int(re.match(r"부품_(\d+)_조립\.stl", os.path.basename(f)).group(1)); P[n] = trimesh.load(f); 파일[n] = os.path.basename(f)

def 메시(이름, T=None):
    d = 부품들[이름]; m = P[d["n"]].copy(); m.apply_transform(d["T"] if T is None else T @ d["T"])
    return m
def 매니(tm): return M.Manifold(M.Mesh(np.ascontiguousarray(tm.vertices, np.float32), np.ascontiguousarray(tm.faces, np.uint32)))

# ======================= 그래프 =======================
# (자식, 부모, 방식, 비고). 방식: 볼 · 핀 · 축(힌지) · 집게 · 끼움. 설명서 단계 · 번호(역할 추정은 「?」)
def 편(측):
    s = 측
    return [
        (s+"52", s+"53", "끼움", "6 단계 A4-25 발바닥 ↔ B3-19 발등: 53 핀 둘 → 52 구멍(발3 에서 설계)"),
        (s+"53", s+"54", "볼", "6 단계 발목 볼(54) → 53 소켓(발3 설계 · 틈 0.15)"),
        (s+"54", s+"44", "축", "6 단계 A3-24 요람 ↔ 정강이 발목 핀(44 핀 · 45 구멍)"),
        (s+"48", s+"54", "볼", "6 단계 B3-20 발목 가드 ↔ 54 앞 작은 볼 막대"),
        (s+"45", s+"44", "핀", "6 단계 정강이 반쪽: 44 보스 핀 다섯 → 45 구멍(정강이3 설계)"),
        (s+"43", s+"44", "끼움", "6 단계 A3-23 무릎 뒤 덮개"),
        (s+"44", s+"46", "집게", "6 단계 A3-22 무릎 관절 아래 C 집게 ↔ 정강이 무릎 축"),
        (s+"46", s+"30", "집게", "6 단계 A3-22 위 C 집게 ↔ 허벅지 무릎 축"),
        (s+"33", s+"30", "끼움", "6 단계 B3-14 허벅지 뒤 ↔ B3-15 앞: 33 핀 둘"),
        (s+"35", s+"30", "끼움", "허벅지 옆 판(? 역할 추정 — B3-16?)"),
        (s+"39", s+"30", "끼움", "허벅지 안 판(? 역할 추정 — B3-17?)"),
        (s+"30", s+"31", "핀", "7 단계 A3-21 고관절 축(31 누운 원통 r 0.7) → 허벅지 구멍"),
        (s+"31", "29", "볼", "7 단계 사타구니 볼(29) → 31 팔각판 원면(소켓이어야 함)"),
        (s+"15", "10", "집게", "4 단계 A1-10 어깨 관절 C 집게 ↔ 몸통 10 팔 끝 기둥"),
        (s+"12", s+"15", "볼", "4 단계 어깨 볼(15 r 0.99) → 팔 윗 블록 12 소켓"),
        (s+"11", s+"12", "끼움", "4 단계 B1-6 어깨 갑주"),
        (s+"18", s+"12", "핀", "3 단계 12 아래 핀(r 0.62·MM px) → 위팔 18"),
        (s+"17", s+"18", "축", "3 단계 A1-11 팔꿈치 관절 ↔ 위팔"),
        (s+"19", s+"17", "끼움", "팔꿈치 덮개(? 역할 추정)"),
        (s+"23", s+"17", "축", "3 단계 B1-8 팔뚝 반쪽 원판(r 1.35) ↔ 팔꿈치 축"),
        (s+"24", s+"23", "핀", "3 단계 B1-9 팔뚝 반쪽 짝(보스)"),
        (s+"26", s+"23", "볼", "3 단계 A1-12 주먹 손목 볼 → 팔뚝 아래 소켓"),
    ]
그래프 = 편("R") + 편("L") + [
    ("14", "10", "끼움", "2 단계 A1-5 가슴 겉 ↔ 골격"), ("13", "14", "끼움", "2 단계 가슴 덕트"),
    ("22", "10", "끼움", "2 단계 A2-6 속 블록(? 역할 추정)"), ("20", "21", "끼움", "2 단계 배 앞판"),
    ("21", "10", "끼움", "2 단계 배 틀 ↔ 골격"), ("50", "10", "핀", "2 단계 A2-9 백팩 ↔ 등"),
    ("47", "50", "핀", "2 단계 B3-21 빔 사벨 → 백팩"), ("49", "50", "핀", "2 단계 B4-21 빔 사벨 → 백팩"),
    ("06", "10", "볼", "2 단계 목 관절 아래 볼 → 몸통 목깃"), ("07", "06", "볼", "1 단계 목 위 볼 → 머리 속 07 (구 홈 r 0.8)"),
    ("08", "07", "끼움", "1 단계 투구"), ("09", "07", "끼움", "1 단계 얼굴(? B1-3)"),
    ("05", "08", "끼움", "1 단계 이마 캡"), ("02", "08", "끼움", "1 단계 V 안테나(아래 소켓)"), ("01", "02", "끼움", "1 단계 A2-15(? 붉은 조각)"),
    ("27", "21", "볼", "5 단계 배 볼(21) → 허리 틀 27 가운데 고리(허리 회전)"),
    ("29", "27", "끼움", "5 단계 A2-19 사타구니"), ("36", "27", "끼움", "5 단계 B2-12 앞 틀 + B1-10 옆치마"),
    ("34", "36", "축", "5 단계 B2-13 앞치마 경첩"), ("41", "34", "끼움", "5 단계 A1-4 노랑 블록"), ("42", "34", "끼움", "5 단계 A1-4 노랑 블록"),
    ("40", "27", "끼움", "5 단계 B1-11 허리 뒤"),
    ("28", "L24", "끼움", "1 쪽 A4-29 방패 손잡이 ↔ 팔뚝"), ("03", "28", "끼움", "방패 뒤판 ↔ 손잡이 소켓(무기4 설계)"),
    ("04", "03", "핀", "방패 앞판(무기4 설계)"), ("25", "04", "끼움", "방패 십자(무기4 설계)"),
    ("38", "R26", "끼움", "8 단계 라이플 손잡이 → 주먹 네모 구멍 1.2"), ("37", "38", "핀", "라이플 반쪽(무기4 설계)"), ("51", "38", "끼움", "조준기(무기4 설계)"),
]
뿌리 = "10"

def 떠있음():
    부 = {c: p for c, p, _, _ in 그래프}; 빠짐 = []
    for n in 부품들:
        x, seen = n, set()
        while x != 뿌리 and x in 부 and x not in seen: seen.add(x); x = 부[x]
        if x != 뿌리: 빠짐.append(n)
    return 빠짐

# ======================= 받침 찾기 (볼 · 핀) =======================
def 볼찾기(tm, rmin=0.4, rmax=2.2):
    """정점 − r·법선 이 한 점에 모이면 구. 모이는 정점이 가장 많은 (중심, r) 들."""
    v, n = tm.vertices, tm.vertex_normals; 결과 = []
    if len(v) > 40000: s_ = np.random.default_rng(0).choice(len(v), 40000, replace=False); v, n = v[s_], n[s_]
    for r in np.arange(rmin, rmax, 0.01):
        c = v - r * n; key = np.round(c / 0.04).astype(np.int64)
        u, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
        j = cnt.argmax()
        if cnt[j] >= 80: 결과.append((cnt[j], r, c[inv.ravel() == j].mean(0)))
    구들 = []
    for cnt, r, c in sorted(결과, key=lambda x: -x[0]):
        if all(np.linalg.norm(c - c2) > 0.5 for _, _, c2 in 구들): 구들.append((int(cnt), round(float(r), 2), c))
    return 구들[:3]

격자캐시 = {}
def 격자(n, pitch=0.08):
    """부품 n (지역 좌표) → 속 격자 S · 바깥 거리 EDT d · 원점. manifold 단면을 z 마다 래스터."""
    if n in 격자캐시: return 격자캐시[n]
    tm = P[n]; mf = M.Manifold(M.Mesh(np.ascontiguousarray(tm.vertices, np.float32), np.ascontiguousarray(tm.faces, np.uint32)))
    lo, hi = tm.bounds[0] - 1.2, tm.bounds[1] + 1.2
    xs, ys, zs = [np.arange(lo[i], hi[i], pitch) for i in range(3)]
    XX, YY = np.meshgrid(xs, ys, indexing="ij"); Q = np.c_[XX.ravel(), YY.ravel()]
    S = np.zeros((len(xs), len(ys), len(zs)), bool)
    for kz, z in enumerate(zs):
        if z <= tm.bounds[0][2] or z >= tm.bounds[1][2]: continue
        안 = np.zeros(len(Q), bool)
        for poly in mf.slice(float(z)).to_polygons():
            if len(poly) < 3: continue
            안 ^= Path(np.asarray(poly)).contains_points(Q)
        S[:, :, kz] = 안.reshape(XX.shape)
    d = ndimage.distance_transform_edt(~S) * pitch
    격자캐시[n] = (S, d, lo, pitch); return 격자캐시[n]

def 지역(이름, pts):
    T = 부품들[이름]["T"]; Ti = np.linalg.inv(T); return pts @ Ti[:3, :3].T + Ti[:3, 3]

def 거리(이름, pts):
    """몸 좌표 점 → 부품 표면 밖 거리(속이면 음수 대신 −1)."""
    S, d, lo, pitch = 격자(부품들[이름]["n"]); q = 지역(이름, pts)
    ii = np.round((q - lo) / pitch).astype(int); ok = np.all((ii >= 0) & (ii < S.shape), -1); ii = np.clip(ii, 0, np.array(S.shape) - 1)
    out = np.where(ok, d[ii[:, 0], ii[:, 1], ii[:, 2]], 9.0); 속 = ok & S[ii[:, 0], ii[:, 1], ii[:, 2]]
    return np.where(속, -1.0, out)

def 받침찾기(이름, r, 핀=False, 근처=None, 반경=None):
    """부모(이름) 바깥 점 중 표면까지 거리 ∈ [r+0.05, r+0.3] 이고 둘레(r+0.4 구면) 가 부모 속에 드는 비율(감쌈)이 가장 큰 곳. 몸 좌표로 돌려준다."""
    S, d, lo, pitch = 격자(부품들[이름]["n"])
    idx = np.argwhere((~S) & (d >= r + 0.05) & (d <= r + 0.3))
    if len(idx) == 0: return dict(찾음=False, 감쌈=0.0)
    pts = idx * pitch + lo; T = 부품들[이름]["T"]; 몸pts = pts @ T[:3, :3].T + T[:3, 3]
    if 근처 is not None:
        sel = np.linalg.norm(몸pts - 근처, axis=1) < 반경; idx, pts, 몸pts = idx[sel], pts[sel], 몸pts[sel]
        if len(idx) == 0: return dict(찾음=False, 감쌈=0.0)
    if len(pts) > 6000: s_ = np.random.default_rng(0).choice(len(pts), 6000, replace=False); idx, pts, 몸pts = idx[s_], pts[s_], 몸pts[s_]
    g = np.random.default_rng(1).normal(size=(96, 3)); g /= np.linalg.norm(g, axis=1, keepdims=True)
    q = pts[:, None, :] + (r + 0.4) * g[None]
    ii = np.round((q - lo) / pitch).astype(int); ok = np.all((ii >= 0) & (ii < S.shape), -1)
    ii = np.clip(ii, 0, np.array(S.shape) - 1); 안 = S[ii[..., 0], ii[..., 1], ii[..., 2]] & ok
    감 = 안.mean(1)
    if 핀:   # 핀 구멍은 축 방향 두 끝이 열려도 된다 → 축(x/y/z) 에 수직인 방향만 본 감쌈 중 최대
        감 = np.max([안[:, np.abs(g[:, a]) < 0.35].mean(1) for a in range(3)], 0)
    j = int(감.argmax())
    return dict(찾음=bool(감[j] >= 0.5), 감쌈=round(float(감[j]), 2), 틈=round(float(d[tuple(idx[j])] - r), 2), 자리=np.round(몸pts[j], 2).tolist())

# ======================= 가동 =======================
def 자손(이름):
    아래 = {}
    for c, p, _, _ in 그래프: 아래.setdefault(p, []).append(c)
    out, st = [], [이름]
    while st:
        x = st.pop(); out.append(x); st += 아래.get(x, [])
    return out

def 회전(축v, 각, 중심):
    from scipy.spatial.transform import Rotation as Rot
    R = Rot.from_rotvec(np.radians(각) * np.asarray(축v, float) / np.linalg.norm(축v)).as_matrix()
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = 중심 - R @ 중심; return T

def 겹침합(움, 고정, 움T):
    """움 부품들을 움T 로 옮겼을 때 고정 부품들과의 겹침 (쌍별)."""
    out = {}
    for a in 움:
        ma = MM[a].transform(움T[:3, :].astype(np.float64))
        ba = ma.bounding_box() if hasattr(ma, "bounding_box") else None
        for b in 고정:
            v = (ma ^ MM[b]).volume()
            if v > 1e-4: out[(a, b)] = v
    return out

# ======================= 실행 =======================
if __name__ == "__main__":
    결과 = {"척도": "체계(×1) · 실척 = ×1.9 (길이) · 부피 ×6.86 · 토크 ×13.0", "파일": {str(n): f for n, f in 파일.items()}}
    몸 = {k: 메시(k) for k in 부품들}
    MM = {k: 매니(m) for k, m in 몸.items()}
    몸통부 = [k for k in 부품들 if k not in 무기]
    전 = trimesh.util.concatenate([몸[k] for k in 몸통부]); print("전체 크기", np.round(전.extents, 2), "바닥", round(전.bounds[0][2], 2))
    결과["전체크기mm"] = np.round(전.extents, 2).tolist()

    # ---- ① 떠 있는 부품
    결과["떠있음"] = 떠있음(); 결과["거울로만듦"] = 거울로만듦; print("떠 있음", 결과["떠있음"])

    # ---- ② 연결
    연결 = []
    볼캐시 = {}
    for c, p, 방식, 비고 in 그래프:
        v = (MM[c] ^ MM[p]).volume()
        a, _ = trimesh.sample.sample_surface(몸[c], 4000, seed=0)
        gap = float(np.clip(거리(p, a), 0, None).min())
        줄 = dict(자식=c, 부모=p, 방식=방식, 비고=비고, 겹침mm3=round(v, 3), 최소틈mm=round(gap, 3))
        접점 = a[np.argmin(거리(p, a))]
        if 방식 == "볼":
            for x in (c, p):
                if x not in 볼캐시: 볼캐시[x] = [(cnt, r, 점(x, cc)) for cnt, r, cc in 볼찾기(P[부품들[x]["n"]])]
            후보 = [(c, p, b) for b in 볼캐시[c]] + [(p, c, b) for b in 볼캐시[p]]
            if not 후보:
                줄.update(판정="안 맞음", 원인="양쪽 다 볼 없음"); 연결.append(줄); print(c, p, 방식, 줄["판정"], flush=True); continue
            좋 = None
            for 볼쪽, 받침쪽, b in 후보:     # 볼마다 상대 쪽 받침을 찾고 가장 잘 감싼 것
                if np.clip(거리(받침쪽, b[2][None]), 0, None)[0] > 3.0: continue
                받 = 받침찾기(받침쪽, b[1], 근처=b[2], 반경=3.0)
                if 좋 is None or 받["감쌈"] > 좋[3]["감쌈"]: 좋 = (볼쪽, 받침쪽, b, 받)
            if 좋 is None:
                줄.update(판정="안 맞음", 원인="볼이 상대 부품에서 3 mm 넘게 떨어짐"); 연결.append(줄); print(c, p, 방식, 줄["판정"], flush=True); continue
            볼쪽, 받침쪽, b, 받 = 좋; r = b[1]
            줄.update(볼=dict(쪽=볼쪽, r=r, 중심=np.round(b[2], 2).tolist()), 받침=받)
            ok = 받["찾음"] and 0.05 <= 받["틈"] <= 0.3
            줄["판정"] = "맞음" if ok else "안 맞음"
            if not ok: 줄["원인"] = "%s 에 r %.2f 볼 소켓 없음(가장 잘 감싼 곳 %.2f)" % (받침쪽, r, 받["감쌈"])
            else: 줄["보정거리mm"] = round(float(np.linalg.norm(np.array(받["자리"]) - b[2])), 2)
        elif 방식 in ("핀", "축", "집게"):
            r = {"집게": 0.5, "축": 0.7, "핀": 0.35}[방식]
            받 = 받침찾기(p, r, 핀=True, 근처=접점, 반경=3.0); 받2 = 받침찾기(c, r, 핀=True, 근처=접점, 반경=3.0)
            줄.update(구멍_부모=받, 구멍_자식=받2)
            ok = 받["찾음"] or 받2["찾음"]
            줄["판정"] = ("구멍 있음(핀 짝 미확인)" if ok else "안 맞음")
            if not ok: 줄["원인"] = "맞닿는 곳 3 mm 안에 r %.2f 핀 구멍/집게 입 없음" % r
        else:
            ok = v <= 겹침문턱 and gap <= 0.3
            줄["판정"] = "맞닿음" if ok else ("겹침" if v > 겹침문턱 else "떨어짐")
            if not ok:   # 보는 사람이 오차를 보정한다: ±1.5 mm 밀어서 겹침 ≤ 0.5 · 틈 ≤ 0.3 되는 자리가 있나
                best = None
                for dx in np.arange(-1.5, 1.51, 0.75):
                    for dy in np.arange(-1.5, 1.51, 0.75):
                        for dz in np.arange(-1.5, 1.51, 0.75):
                            T = np.eye(4); T[:3, 3] = (dx, dy, dz); vv = (MM[c].transform(T[:3, :]) ^ MM[p]).volume()
                            gg = float(np.clip(거리(p, a + (dx, dy, dz)), 0, None).min())
                            sc = vv + 10 * max(gg - 0.3, 0)
                            if best is None or sc < best[0]: best = (sc, vv, gg, (dx, dy, dz))
                줄["밀기"] = dict(mm=[float(x) for x in best[3]], 겹침mm3=round(best[1], 2), 틈mm=round(best[2], 2))
                if best[1] <= 겹침문턱 and best[2] <= 0.3: 줄["판정"] = "맞닿음(밀어서 %.1f mm)" % np.linalg.norm(best[3])
                else: 줄["원인"] = "±1.5 mm 밀어도 겹침 %.1f · 틈 %.2f — 속 찬 부품끼리 자리 없음" % (best[1], best[2])
            v = 0.0 if 줄["판정"].startswith("맞닿음") else v
        if v > 겹침문턱: 줄["판정"] += " · 겹침 %.1f" % v
        연결.append(줄); print(c, p, 방식, 줄["판정"], 줄.get("원인", ""), flush=True)
    결과["연결"] = 연결

    json.dump(결과, open(os.path.join(OUT, "조립%s.json" % 꼬리), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))

    # ======================= ③ 가동 =======================
    몸부 = [k for k in 부품들 if k not in 무기]
    def 볼몸(이름, 참조):
        """부품의 볼 중 참조점에 가장 가까운 것 (몸 좌표)."""
        bs = 볼찾기(P[부품들[이름]["n"]]); c = [점(이름, b[2]) for b in bs]
        return min(c, key=lambda x: np.linalg.norm(x - 참조)) if c else np.asarray(참조, float)
    목볼 = 볼몸("06", [0, 0.3, z목 + 3]); 어깨볼 = 볼몸("R15", 어깨 + [-3, 0, 0]); 손목볼 = 볼몸("R26", 손목)
    엉볼 = 볼몸("29", [-4.5, 0, 고관절[2]]); 엉볼 = 엉볼 * [-1, 1, 1] if 엉볼[0] > 0 else 엉볼   # 09-27 고침: 원본 29 는 볼이 +X 에만 — 오른 다리를 왼 볼로 돌렸다
    배볼 = 볼몸("21", [0, 0, z배 - 2]); 발볼 = 점("R54", [Xb, 0, Zb])
    팔꿈치축 = 점("R23", [3.0, 10.3, 1.65])
    X_, Y_, Z_ = np.eye(3)
    관절 = [  # 이름, 움직이는 뿌리, 중심, 축, (+ 방향 이름, − 방향 이름)
        ("목", "07", 목볼, X_, ("숙임", "들기")), ("목", "07", 목볼, Z_, ("왼쪽 돌림", "오른쪽 돌림")),
        ("어깨(집게)", "R15", 어깨, X_, ("뒤로", "앞으로")), ("어깨(볼)", "R12", 어깨볼, Y_, ("옆 들기", "안으로(몸 쪽)")),
        ("팔꿈치", "R23", 팔꿈치축, X_, ("뒤로", "굽힘(앞)")), ("손목", "R26", 손목볼, X_, ("뒤", "앞")), ("손목", "R26", 손목볼, Y_, ("밖", "안")),
        ("허리", "27", 배볼, Z_, ("+", "−")),
        ("고관절", "R31", 엉볼, X_, ("뒤로", "앞차기")), ("고관절", "R31", 엉볼, Y_, ("벌리기", "안으로")),
        ("무릎", "R44", 무릎몸, X_, ("굽힘(뒤)", "앞")), ("발목", "R54", 요람몸, X_, ("발끝 내림", "발끝 올림")), ("발목", "R52", 발볼, Y_, ("발바닥 바깥쪽으로", "발바닥 안쪽으로")),
    ]
    자손_ = {}
    for c, p, _, _ in 그래프:
        if c in 무기 or p in 무기: continue
        자손_.setdefault(p, []).append(c)
    def 아래(뿌):
        out, st = [], [뿌]
        while st:
            x = st.pop(); out.append(x); st += 자손_.get(x, [])
        return out
    def 움직임(뿌):
        if 뿌[1:] == "52": return [뿌[0] + "52", 뿌[0] + "53"]
        return 아래(뿌)
    def 합(names):
        m = None
        for k in names: m = MM[k] if m is None else m + MM[k]
        return m
    가동 = []
    for 이름, 뿌, c0, ax, 방향 in 관절:
        움 = 움직임(뿌); 고 = [k for k in 몸부 if k not in 움]
        반경 = max(np.linalg.norm(몸[k].vertices - c0, axis=1).max() for k in 움) + 0.5
        고 = [k for k in 고 if np.linalg.norm(np.clip(c0, 몸[k].bounds[0], 몸[k].bounds[1]) - c0) < 반경]
        m움 = 합(움); m고 = 합(고); 기준 = (m움 ^ m고).volume()
        # 후: 앞치마 34(+41 · 42)는 36 경첩(34↔36 「축」)으로 따로 돈다 — 다리에 밀리면 0~80° 들어 올려 비키는지 본다
        연 = [k for k in ("34", "41", "42") if k in 고] if (후 and 이름 == "고관절") else []
        if 연:
            m고0 = 합([k for k in 고 if k not in 연]); m연 = 합(연); b34 = 몸["34"].bounds
            경첩 = np.array([0, b34.mean(0)[1], b34[1][2] - 0.3]); 연기준 = (m연 ^ m고0).volume()
        def 막힘(T):
            mT = m움.transform(T[:3, :])
            if (mT ^ m고).volume() - 기준 <= 겹침문턱: return False
            if not 연: return True
            v0 = (mT ^ m고0).volume()
            for b in range(10, 81, 10):
                for sb in (1, -1):
                    mb = m연.transform(회전(X_, sb * b, 경첩)[:3, :])
                    if v0 + (mT ^ mb).volume() + (mb ^ m고0).volume() - 연기준 - 기준 <= 겹침문턱: return False
            return True
        줄 = dict(관절=이름, 축=np.round(ax, 2).tolist(), 중심=np.round(c0, 2).tolist(), 기준겹침mm3=round(기준, 2))
        for sgn, 방 in ((+1, 방향[0]), (-1, 방향[1])):
            한계, 누구 = 180, None
            for a in range(3, 181, 3):
                T = 회전(ax, sgn * a, c0)
                if 막힘(T):
                    한계 = a - 3; 쌍 = {}
                    for u in 움:
                        mu = MM[u].transform(T[:3, :])
                        for g_ in 고:
                            v = (mu ^ MM[g_]).volume() - (MM[u] ^ MM[g_]).volume()
                            if v > 0.05: 쌍[(u, g_)] = v
                    누구 = max(쌍, key=쌍.get) if 쌍 else None; break
            줄[방] = dict(각=한계, 부딪힘=list(누구) if 누구 else None, 부호=sgn)
        가동.append(줄); print("가동", 이름, {k: v for k, v in 줄.items() if isinstance(v, dict)}, flush=True)
    결과["가동"] = 가동

    # ======================= ④ 포징 =======================
    무게 = {k: P[부품들[k]["n"]].volume * RHO for k in 몸부}
    결과["무게g_체계"] = round(sum(무게.values()), 3); 결과["무게g_실척"] = round(sum(무게.values()) * K ** 3, 2)
    def 자세(각들):
        """각들: [(관절 번호 i, 'R'/'L', 각)] 몸쪽부터. 돌린 뒤 바닥 z = 0."""
        T = {k: np.eye(4) for k in 몸부}
        for i, 측, a in 각들:
            이름, 뿌, c0, ax, _ = 관절[i]; c0 = np.array(c0, float); ax = np.array(ax, float)
            if 측 == "L" and 뿌[0] == "R":
                뿌 = "L" + 뿌[1:]; c0 = c0 * [-1, 1, 1]; ax = ax * [1, -1, -1]      # X 거울: 축벡터(유사벡터)는 Y · Z 성분 부호가 바뀐다
            움 = 움직임(뿌); Tp = T[뿌]; c = Tp[:3, :3] @ c0 + Tp[:3, 3]; axn = Tp[:3, :3] @ ax
            Rt = 회전(axn, a, c)
            for k in 움: T[k] = Rt @ T[k]
        z0 = min((몸[k].vertices @ T[k][:3, :3].T + T[k][:3, 3])[:, 2].min() for k in 몸부)
        for k in 몸부: T[k][2, 3] -= z0
        return T
    def 무게중심(T, names=None):
        names = names or 몸부; m = np.array([무게[k] for k in names])
        c = np.array([T[k][:3, :3] @ 몸[k].center_mass + T[k][:3, 3] for k in names]); return (m[:, None] * c).sum(0) / m.sum(), m.sum()
    def 지지(T):
        pts = []
        for k in ("R52", "L52"):
            v = 몸[k].vertices @ T[k][:3, :3].T + T[k][:3, 3]; pts.append(v[v[:, 2] < 0.3][:, :2])
        pts = np.vstack(pts); h = ConvexHull(pts); return pts[h.vertices]
    def 여유(poly, p):
        """무게중심 투영이 지지 다각형 안이면 +(가장 가까운 변까지), 밖이면 −."""
        n_ = len(poly); d = min(abs(np.cross(np.r_[poly[(i + 1) % n_] - poly[i], 0], np.r_[p - poly[i], 0])[2]) / np.linalg.norm(poly[(i + 1) % n_] - poly[i]) for i in range(n_))
        return d if Path(poly).contains_point(p) else -d
    # + 회전 방향(오른쪽 기준): X 축 + = 매달린 팔다리가 뒤로 · 머리는 앞으로 / Y 축 + = 매달린 팔다리가 바깥(−X)으로
    # 관절 번호: 0 목X 1 목Z 2 어깨집게X 3 어깨볼Y 4 팔꿈치 5,6 손목 7 허리 8 고관절X 9 고관절Y 10 무릎 11 발목X 12 발목Y
    자세들 = {
        "차렷": [],
        "한 발 앞": [(8, "R", -18), (11, "R", 18), (8, "L", 18), (11, "L", -18)],
        "무릎 30°": [(8, "R", -15), (10, "R", 30), (11, "R", -15), (8, "L", -15), (10, "L", 30), (11, "L", -15)],
        "팔 벌림": [(3, "R", 80), (3, "L", 80)],
        "한 발 앞 + 팔 앞": [(8, "R", -18), (11, "R", 18), (8, "L", 18), (11, "L", -18), (2, "R", -60), (4, "R", -60), (2, "L", -30)],
    }
    토크관절 = {"목": (0, "07", False), "어깨": (3, "R12", False), "팔꿈치": (4, "R23", False), "손목": (5, "R26", False), "허리": (7, "27", True),
               "고관절": (8, "R31", True), "무릎": (10, "R44", True), "발목": (11, "R54", True)}
    포징 = {}; 자세T = {}
    for 자, 각 in 자세들.items():
        T = 자세(각); 자세T[자] = T; g, m = 무게중심(T); poly = 지지(T); e = 여유(poly, g[:2])
        토 = {}
        for jn, (i, 뿌, 몸쪽) in 토크관절.items():
            for 측 in ("R", "L"):
                if 뿌[0] != "R" and 측 == "L": continue
                r_ = ("L" + 뿌[1:]) if (측 == "L" and 뿌[0] == "R") else 뿌
                움 = 움직임(r_)
                c0 = np.array(관절[i][2], float) * ([-1, 1, 1] if 측 == "L" else 1); Tp = T[r_]; c = Tp[:3, :3] @ c0 + Tp[:3, 3]
                if 몸쪽:   # 선 자세: 관절이 버티는 것은 발 반대쪽(몸쪽) 무게 — 두 발이면 반씩
                    남 = [k for k in 몸부 if k not in 움]; gg, mm_ = 무게중심(T, 남)
                    if 뿌[0] == "R": mm_ /= 2
                else:
                    gg, mm_ = 무게중심(T, 움)
                F = np.array([0, 0, -mm_ / 1000 * 9.81]); τ = np.linalg.norm(np.cross(gg - c, F))
                토[jn + ("" if 뿌[0] != "R" else ("(오른)" if 측 == "R" else "(왼)"))] = dict(체계Nmm=round(τ, 4), 실척Nmm=round(τ * K ** 4, 3))
        포징[자] = dict(무게중심mm=np.round(g, 2).tolist(), 무게g=round(m, 3), 지지안=bool(e > 0), 여유mm_체계=round(e, 2), 여유mm_실척=round(e * K, 2), 토크=토)
        print("포징", 자, 포징[자]["지지안"], 포징[자]["여유mm_체계"], flush=True)
    결과["포징"] = 포징

    # ======================= ⑤ 출력성: 실척(×1.9)에서 0.8 mm 보다 얇은 곳 =======================
    # 속 격자(0.08 체계 = 0.15 실척)를 반지름 0.4 실척 공으로 열기(opening) — 공이 못 들어가는 속 = 얇은 벽. ponytail: 격자 5 칸짜리 근사
    rv = 0.4 / K / 0.08; o = np.arange(-int(rv), int(rv) + 1); 공 = (o[:, None, None] ** 2 + o[None, :, None] ** 2 + o[None, None, :] ** 2) <= rv ** 2
    얇음 = {}
    for n in sorted({부품들[k]["n"] for k in 몸부}):
        S_ = 격자(n)[0]; 열 = ndimage.binary_opening(S_, 공); t_ = (S_ & ~열).sum() * 0.08 ** 3 * K ** 3
        얇음[str(n)] = dict(얇은mm3_실척=round(float(t_), 1), 비율=round(float((S_ & ~열).sum() / max(S_.sum(), 1)), 3))
    결과["출력성"] = dict(기준="실척 두께 < 0.8 mm (opening 공 r 0.4)", 부품=얇음, 합mm3=round(sum(v["얇은mm3_실척"] for v in 얇음.values()), 1))
    print("출력성 합", 결과["출력성"]["합mm3"], flush=True)
    json.dump(결과, open(os.path.join(OUT, "조립%s.json" % 꼬리), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))

    # ======================= 그림 =======================
    from shapely.geometry import Polygon
    def 그리기(T, 방향, W, 빨강=(), 덧=(), 무기도=False):
        이름들 = list(부품들) if 무기도 else 몸부
        L_ = [(몸[k].copy().apply_transform(T[k]) if T is not None else 몸[k], (1, 0.05, 0.05) if k in 빨강 else 부품들[k]["색"]) for k in 이름들]
        return F3.그림다색(L_ + list(덧), F3.시점(방향, up=(0, 0, 1)), W)
    W = 420
    사진칸 = [("d_egx01_21.jpg", (0, 0, 470, 700), (0, -1, 0.02), "앞 — d_egx01_21 왼쪽"), ("d_egx01_02.jpg", None, (-0.35, -1, 0.12), "3/4 — d_egx01_02"),
             ("d_egx01_03.jpg", None, (0, 1, 0.05), "뒤 — d_egx01_03"), ("d_egx01_08.jpg", None, (-1, -0.15, 0.05), "옆 — d_egx01_08(순수 옆 사진 없음)")]
    캔 = Image.new("RGB", (W * 4, W * 2 + 60), "white"); dr = ImageDraw.Draw(캔)
    for i, (f, box, d, 이름) in enumerate(사진칸):
        ph = Image.open(os.path.join(KIT, f)).convert("RGB"); ph = ph.crop(box) if box else ph; ph.thumbnail((W, W))
        캔.paste(ph, (i * W + (W - ph.size[0]) // 2, 26)); 캔.paste(그리기(None, d, W, 무기도=True), (i * W, W + 50))
        dr.text((i * W + 6, 4), 이름 + "  [위 사진 | 아래 조립]", fill=(0, 0, 0), font=글꼴)
    캔.save(os.path.join(OUT, "조립_사진대조%s.png" % 꼬리))
    칸 = []
    for j, 줄 in zip(관절, 가동):
        이름, 뿌, c0, ax, 방향 = j
        for 방 in 방향:
            r_ = 줄[방]; T = {k: np.eye(4) for k in 몸부}; Rt = 회전(ax, r_["부호"] * r_["각"], np.array(c0))
            for k in 움직임(뿌): T[k] = Rt
            보기 = (-1, -0.12, 0.1) if abs(ax[0]) > 0.5 else ((0, -1, 0.1) if abs(ax[1]) > 0.5 else (-0.4, -1, 0.9))
            im = 그리기(T, 보기, 300, 빨강=set(r_["부딪힘"] or ()))
            ImageDraw.Draw(im).text((4, 4), "%s %s %d°" % (이름, 방, r_["각"]), fill=(0, 0, 0), font=글꼴)
            ImageDraw.Draw(im).text((4, 24), "부딪힘: %s" % (" × ".join(r_["부딪힘"]) if r_["부딪힘"] else "180° 까지 없음"), fill=(160, 0, 0), font=작은)
            칸.append(im)
    열 = 6; 캔 = Image.new("RGB", (300 * 열, 300 * ((len(칸) + 열 - 1) // 열)), "white")
    for i, im in enumerate(칸): 캔.paste(im, ((i % 열) * 300, (i // 열) * 300))
    캔.save(os.path.join(OUT, "가동한계%s.png" % 꼬리))
    칸 = []
    for 자, T in 자세T.items():
        g = np.array(포징[자]["무게중심mm"]); poly = 지지(T)
        공 = trimesh.creation.icosphere(radius=1.2); 공.apply_translation(g)
        선 = trimesh.creation.cylinder(0.25, g[2], sections=12); 선.apply_translation([g[0], g[1], g[2] / 2])
        판 = trimesh.creation.extrude_polygon(Polygon(poly), 0.15)
        덧 = [(공, (0.9, 0, 0.9)), (선, (0.9, 0, 0.9)), (판, (0.1, 0.75, 0.2))]
        for d in ((0, -1, 0.15), (-1, 0, 0.15)):
            im = 그리기(T, d, 380, 덧=덧)
            ImageDraw.Draw(im).text((4, 4), "%s — %s (여유 %.1f mm 체계 · %.1f 실척)" % (자, "선다" if 포징[자]["지지안"] else "넘어짐", 포징[자]["여유mm_체계"], 포징[자]["여유mm_실척"]), fill=(0, 0, 0), font=작은)
            칸.append(im)
    캔 = Image.new("RGB", (380 * 2, 380 * len(자세T)), "white")
    for i, im in enumerate(칸): 캔.paste(im, ((i % 2) * 380, (i // 2) * 380))
    캔.save(os.path.join(OUT, "포징%s.png" % 꼬리)); print("그림 끝")
