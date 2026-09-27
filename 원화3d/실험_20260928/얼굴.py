# -*- coding: utf-8 -*-
"""오메가몬 PG 얼굴 디테일 (2026-09-28) — 키트 문법(틀 + 메움판 · 덧판 겹 · 모따기 · 따로 꽂는 작은 부품).

    python 얼굴.py            -> out/출력/오메가몬_PG/디자인_얼굴/*.stl · 부품.json(색 · 대체 · 검사)
    python 얼굴.py --렌더     -> 위 + Blender(멋_변형.py 같은 조명 · 카메라) 전/후 → 멋/얼굴_전후.jpg

원본(디자인_머리어깨.py · 디자인/머리어깨/*.stl)은 안 고친다. 옛 STL 을 읽어 깎고 덧댄다.
좌표 = 관절.json(mm · y 작은 쪽이 앞). 얼굴 앞면 y = -0.4 + 0.22|x| (옛 얼굴과 같다).
"""
import os, sys, json, subprocess
import numpy as np, trimesh, manifold3d as M
from scipy.spatial import ConvexHull, HalfspaceIntersection
from scipy.spatial.transform import Rotation as Rot

ROOT = r"G:\art2real\원화3d"
DES = os.path.join(ROOT, "out", "출력", "오메가몬_PG", "디자인")
OLD = os.path.join(DES, "머리어깨")
OUT = os.path.join(ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴"); os.makedirs(OUT, exist_ok=True)
멋 = os.path.join(ROOT, "out", "출력", "오메가몬_PG", "멋")
J = {j["이름"]: j for j in json.load(open(os.path.join(ROOT, "out", "가동", "관절.json"), encoding="utf-8"))["관절"]}
틈 = 0.12

def 읽기(fn):
    t = trimesh.load(fn, force="mesh")
    return M.Manifold(M.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
def 볼록(P): return M.Manifold.hull_points(np.asarray(P, float))
def 밀기(P, t):  # 볼록 hull 의 정확한 평면 오프셋 (디자인_머리어깨.py 와 같음)
    P = np.asarray(P, float); h = ConvexHull(P); eq = h.equations.copy(); eq[:, 3] -= t
    return HalfspaceIntersection(eq, P[h.vertices].mean(0)).intersections
def yf(x): return -0.4 + 0.22 * abs(x)
def 상자(lo, hi): return M.Manifold.cube(list(np.subtract(hi, lo))).translate(list(lo))
def 판(poly, 뒤, 앞, 앞poly=None):
    """(x,z) 볼록 다각형 → 얼굴 앞면에서 뒤(+)/앞(−) 오프셋 사이의 판. x 부호가 바뀌면 반쪽씩(V 앞면 때문)."""
    앞poly = 앞poly or poly
    pts = [(x, yf(x) + 뒤, z) for x, z in poly] + [(x, yf(x) - 앞, z) for x, z in 앞poly]
    return 볼록(pts)
def 안쪽(poly, d):  # 볼록 다각형을 d 만큼 안으로 (모따기 앞면)
    from shapely.geometry import Polygon
    return list(Polygon(poly).buffer(-d, join_style=2).exterior.coords)[:-1]
def V홈(m, p0, p1, n, 폭=0.8, 깊=0.5):
    p0, p1, n = np.array(p0, float), np.array(p1, float), np.array(n, float) / np.linalg.norm(n)
    w = np.cross(n, (p1 - p0) / np.linalg.norm(p1 - p0)); w /= np.linalg.norm(w)
    pts = [p + s * (폭 / 2) * w + 0.3 * n for p in (p0, p1) for s in (-1, 1)] + [p - 깊 * n for p in (p0, p1)]
    return m - 볼록(pts)
def 거울(poly): return [(-x, z) for x, z in poly][::-1]

# ── 옛 부품 ──
옛 = {n: 읽기(os.path.join(OLD, n + ".stl")) for n in ("투구앞", "투구뒤", "얼굴", "뿔", "V안테나L", "V안테나R")}
얼굴 = 옛["얼굴"]

# 옛 얼굴 앞면의 짧은 V 홈 넷(눈 · 입 줄)을 메운다: 앞 1 mm 층을 다시 채움
외곽 = [(0.0, 264.4), (7.8, 268.2), (8.0, 278.6), (-8.0, 278.6), (-7.8, 268.2)]
얼굴 = 얼굴 + 볼록([(x, y_, z) for x, z in 외곽 for y_ in (yf(x), yf(x) + 1.0)])

# ── 1. V 이마 덧판(흰) — 위 z 278.5 · 아래 V 끝 z 272.6(코) · 1.2 튀어나옴 · 아래 모서리 0.8 모따기 ──
def V선(x): return 272.6 + 0.55 * abs(x)
V반 = [(0.0, 278.5), (7.9, 278.5), (7.9, V선(7.9)), (0.0, V선(0))]
V반앞 = [(0.0, 278.5), (7.9, 278.5), (7.9, V선(7.9) + 0.8), (0.0, V선(0) + 0.8)]
def 덧판(반, 반앞, 앞, 박힘=0.3):
    """반쪽 다각형(x ≥ 0) 을 좌우로 — 판 · 얼굴 자리 홈(판 + 틈)."""
    ms, 홈 = [], []
    for s in (1, -1):
        P = [(s * x, z) for x, z in 반]; Q = [(s * x, z) for x, z in 반앞]
        ms.append(판(P, 박힘, 앞, Q))
        홈.append(볼록(밀기([(x, yf(x) + 박힘, z) for x, z in P] + [(x, yf(x) - 2.0, z) for x, z in P], 틈)))
    return ms[0] + ms[1], 홈[0] + 홈[1]
이마V, 이마홈 = 덧판(V반, V반앞, 1.2)
이마V = V홈(이마V, (0, yf(0) - 1.2, 278.8), (0, yf(0) - 1.2, 273.6), (0, -1, 0))      # 3. 세로 V 홈(뿔 밑~코)
얼굴 = 얼굴 - 이마홈

# ── 2. 치켜 올라간 눈: 얼굴(틀)에 사선 눈 구멍 1.5 · 초록 메움판을 끼움 ──
눈P = [(1.6, V선(1.6) - 0.3), (6.6, V선(6.6) - 0.3), (6.6, V선(6.6) - 2.0), (1.6, V선(1.6) - 1.7)]
눈들, 눈구멍 = {}, M.Manifold()
for s, 이름 in ((1, "눈R"), (-1, "눈L")):
    P = [(s * x, z) for x, z in 눈P]
    구멍 = 볼록([(x, yf(x) - 2.0, z) for x, z in P] + [(x, yf(x) + 1.5, z) for x, z in P])
    눈구멍 = 눈구멍 + 구멍
    눈들[이름] = 볼록(밀기([(x, yf(x) + 0.3, z) for x, z in P] + [(x, yf(x) + 1.5, z) for x, z in P], -틈))   # 앞 0.42 들어감
얼굴 = 얼굴 - 눈구멍

# ── 5. 볼 판(흰 덧판) · 아래로 좁아지는 쐐기 · 앞 0.5 모따기 ──
볼반 = [(4.2, 272.3), (8.0, 274.4), (8.0, 270.6), (6.0, 270.6)]
볼판, 볼홈 = M.Manifold(), M.Manifold()
for s in (1, -1):
    P = [(s * x, z) for x, z in 볼반]
    볼판 = 볼판 + 판(P, 0.3, 0.7, 안쪽(P, 0.5))
    볼홈 = 볼홈 + 볼록(밀기([(x, yf(x) + 0.3, z) for x, z in P] + [(x, yf(x) - 2.0, z) for x, z in P], 틈))
얼굴 = 얼굴 - 볼홈
볼판L = 볼판 ^ 상자((-20, -20, 200), (0, 40, 300)); 볼판R = 볼판 ^ 상자((0, -20, 200), (20, 40, 300))

# ── 4. 턱(회색 · 따로 꽂는 작은 부품) · 가로 홈 셋 · 앞 모서리 모따기 · 뒤 핀 Ø1.6 ──
턱영역 = 상자((-10, -5, 250), (10, 3.4, 269.6))
턱 = 얼굴 ^ 턱영역
얼굴 = 얼굴 - 상자((-10, -5, 250), (10, 3.4 + 틈, 269.6 + 틈))
턱외곽 = [(0.0, 264.4), (7.8, 268.2), (7.9, 269.6), (-7.9, 269.6), (-7.8, 268.2)]
턱 = 턱 ^ 볼록([(x, yf(x) + 0.7, z) for x, z in 턱외곽] + [(x, yf(x) - 0.01, z) for x, z in 안쪽(턱외곽, 0.7)] + [(x, 5.0, z) for x, z in 턱외곽])
for z in (265.9, 267.0, 268.1):
    for s in (1, -1):
        턱 = V홈(턱, (s * 7.5, yf(7.5), z), (0, yf(0), z), (s * 0.22, -1, 0), 폭=0.6, 깊=0.4)
핀 = M.Manifold.cylinder(2.2, 0.8, 0.8, 24).rotate([-90, 0, 0]).translate([0, 3.3, 267.3])
핀구멍 = M.Manifold.cylinder(2.4, 0.8 + 0.15, 0.8 + 0.15, 24).rotate([-90, 0, 0]).translate([0, 3.3, 267.3])
턱 = 턱 + 핀
얼굴 = 얼굴 - 핀구멍

# ── 6. 금뿔 → 끝이 뾰족한 테이퍼(뿌리는 옛 뿔과 같아 소켓 그대로) ──
HZ = 2.0
def 단z(z, P): return [(a, b, z + HZ) for a, b in P]
뿔밑 = 단z(281.0, [(0, 0.8), (3.2, 3.2), (3.2, 7.6), (0, 10.0), (-3.2, 7.6), (-3.2, 3.2)])
뿔중 = 단z(290.6, [(0, -1.4), (2.4, 0.4), (2.4, 4.4), (0, 6.2), (-2.4, 4.4), (-2.4, 0.4)])
뿔위 = 단z(299.0, [(0, -4.6), (1.3, -3.6), (1.3, -1.4), (0, -0.4), (-1.3, -1.4), (-1.3, -3.6)])
t_ = np.linspace(0, 2 * np.pi, 8, endpoint=False)
뿔끝 = [(0.45 * np.cos(a), -7.0 + 0.45 * np.sin(a), 309.2 + HZ) for a in t_]
뿔 = 볼록(np.vstack([뿔밑, 뿔중])) + 볼록(np.vstack([뿔중, 뿔위])) + 볼록(np.vstack([뿔위, 뿔끝]))
# 뿔 앞 능선 세우기: 가운데 앞 모서리 양옆 얕은 V 홈
for s in (1, -1):
    뿔 = V홈(뿔, (s * 1.0, -1.0 + 0.15, 290.6 + HZ), (s * 0.55, -4.0, 299.0 + HZ), (s * 0.6, -1, 0), 폭=0.5, 깊=0.3)

# ── 3. 투구앞 차양 가운데 세로 V 홈(뿔 밑 → 이마 V 로 이어짐) ──
투구앞 = V홈(옛["투구앞"], (0, -3.0, 284.4), (0, -3.0, 281.4), (0, -1, 0))
투구앞 = V홈(투구앞, (0, -3.0, 281.4), (0, -1.4, 279.6), (0, -1, 0.9))

색 = dict(흰=[0.93, 0.93, 0.95], 은=[0.80, 0.82, 0.86], 회=[0.45, 0.46, 0.50], 초록=[0.15, 0.72, 0.35])
새 = {"투구앞": (투구앞, 색["흰"], "옛 투구앞 + 차양 세로 V 홈"),
      "얼굴": (얼굴, 색["은"], "틀: 사선 눈 구멍 · 이마/볼 덧판 자리 0.3 · 턱 자리 · 핀 구멍 Ø1.9"),
      "얼굴이마V": (이마V, 색["흰"], "V 이마 덧판 1.5 · 아래 0.8 모따기 · 세로 V 홈 — 얼굴 자리에 끼워 붙임(틈 0.12)"),
      "얼굴눈L": (눈들["눈L"], 색["초록"], "눈 메움판 — 얼굴 눈 구멍에 앞에서 끼움(틈 0.12 · 0.42 들어감)"),
      "얼굴눈R": (눈들["눈R"], 색["초록"], "눈 메움판"),
      "얼굴볼판L": (볼판L, 색["흰"], "볼 덧판 1.0 · 앞 0.5 모따기"),
      "얼굴볼판R": (볼판R, 색["흰"], "볼 덧판"),
      "얼굴턱": (턱, 색["회"], "턱 · 가로 V 홈 3 · 앞 0.7 모따기 · 뒤 핀 Ø1.6×2.2 → 얼굴 구멍 Ø1.9"),
      "뿔": (뿔, 색["은"], "끝 Ø0.9 테이퍼 · 앞 능선 · 뿌리는 옛 뿔과 같음")}
대체 = ["투구앞", "얼굴", "뿔"]

# ════════════════ 검사 ════════════════
def 메(m):
    t = m.to_mesh(); return trimesh.Trimesh(np.asarray(t.vert_properties)[:, :3], np.asarray(t.tri_verts), process=False)
_dirs = [np.array(v, float) / np.linalg.norm(v) for v in [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)] + [(i, j, k) for i in (-1, 1) for j in (-1, 1) for k in (-1, 1)]]
def 얇은곳(m, r=0.4):
    """r 침식 → r 팽창(14 방향) 뒤 사라진 부피 ≈ 두께 < ~0.65–0.8 인 살."""
    core = m
    for v in _dirs: core = core ^ m.translate(list(-r * v))
    열림 = M.Manifold.batch_boolean([core] + [core.translate(list(r * v)) for v in _dirs], M.OpType.Add) ^ m
    return round((m - 열림).volume(), 2)
def 이웃읽기():
    d = {n: 옛[n] for n in ("투구뒤", "V안테나L", "V안테나R")}
    d["가슴앞"] = 읽기(os.path.join(DES, "돌출", "돌출03_가슴앞.stl")) if os.path.exists(os.path.join(DES, "돌출", "돌출03_가슴앞.stl")) else 읽기(os.path.join(DES, "몸통", "가슴앞.stl"))
    d["목깃"] = 읽기(os.path.join(DES, "몸통", "목깃.stl"))
    d["목뼈"] = 읽기(os.path.join(ROOT, "out", "가동", "프레임", "목.stl"))
    d["머리뼈"] = 읽기(os.path.join(ROOT, "out", "가동", "프레임", "머리.stl"))
    return d
if __name__ == "__main__":
    이웃 = 이웃읽기()
    검사 = {}
    for n, (m, c, 비고) in 새.items():
        tm = 메(m)
        검사[n] = dict(닫힘=bool(tm.is_watertight), 조각=len(m.decompose()), 부피mm3=round(m.volume(), 1), 얇은곳mm3=얇은곳(m),
                     크기mm=np.round(tm.extents, 1).tolist())
    # 겹침: 새 부품끼리 · 이웃(목 · 가슴 · 투구뒤 · 안테나 · 뼈)
    겹 = {}
    ns = list(새)
    for i, a in enumerate(ns):
        for b in ns[i + 1:] + list(이웃):
            B = 새[b][0] if b in 새 else 이웃[b]
            v = (새[a][0] ^ B).volume()
            if v > 0.005: 겹["%s∩%s" % (a, b)] = round(v, 3)
    # 옛 얼굴 기준 같은 값(대조)
    옛겹 = {}
    for a in ("투구앞", "얼굴", "뿔"):
        for b in 이웃:
            v = (옛[a] ^ 이웃[b]).volume()
            if v > 0.005: 옛겹["%s∩%s" % (a, b)] = round(v, 3)
    # 목위 끄덕: 머리 전체(투구뒤 · 안테나 포함)를 목위 피벗 x 축으로 돌려 가슴앞 · 목깃과 겹침
    Pn = np.array(J["목위"]["피벗mm"])
    def 돌(m, d):
        R = Rot.from_rotvec([np.radians(d), 0, 0]).as_matrix(); return m.transform(np.hstack([R, (Pn - R @ Pn).reshape(3, 1)]))
    몸 = 이웃["가슴앞"] + 이웃["목깃"]
    머리옛 = M.Manifold.batch_boolean([옛[n] for n in 옛], M.OpType.Add)
    머리새 = M.Manifold.batch_boolean([m for m, _, _ in 새.values()] + [옛[n] for n in ("투구뒤", "V안테나L", "V안테나R")], M.OpType.Add)
    끄덕 = {}
    for d in range(-25, 21, 5):
        끄덕[d] = dict(옛=round((돌(머리옛, d) ^ 몸).volume(), 2), 새=round((돌(머리새, d) ^ 몸).volume(), 2))
    for n, (m, c, 비고) in 새.items(): 메(m).export(os.path.join(OUT, n + ".stl"))
    json.dump(dict(설명="얼굴 디테일(09-28) — 머리어깨 부품 중 「대체」를 이 폴더 것으로 바꾼다. 나머지 새 부품은 더한다.",
                   대체=대체, 부품={n: dict(파일=n + ".stl", 색=c, 비고=비고, **검사[n]) for n, (m, c, 비고) in 새.items()},
                   겹침_새=겹, 겹침_옛=옛겹, 끄덕_겹침mm3_가슴목깃=끄덕),
              open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(dict(검사=검사, 겹침_새=겹, 겹침_옛=옛겹, 끄덕=끄덕), ensure_ascii=False, indent=1))

# ════════════════ 렌더(--렌더): 멋_변형.py 의 조명 · 카메라 그대로 · 큰 해상도로 찍고 얼굴은 잘라 낸다 ════════════════
BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
TMP = os.path.join(OUT, "_렌더")
구동 = r'''
import sys, os
sys.path.insert(0, r"{src}")
import 멋_변형 as MV
MV.DES = sys.argv[-2]; MV.REN = sys.argv[-1]
MV.컷.update({{"얼굴정면": (False, 0, 0.30, 85, 2000, 2000), "영웅큰": (False, 32, 0.22, 70, 1500, 1950)}})
MV.blender_main(["A", "얼굴정면", "영웅큰"])
'''
def 렌더():
    from PIL import Image, ImageDraw, ImageFont
    for 판 in ("전", "후"):
        d = os.path.join(TMP, 판, "DES")
        for 폴더 in ("몸통", "다리", "머리어깨", "색분할", "돌출"):
            P = json.load(open(os.path.join(DES, 폴더, "부품.json"), encoding="utf-8"))
            P = dict(부품={n: dict(v, 파일=os.path.join(DES, 폴더, v.get("파일", n + ".stl"))) for n, v in P["부품"].items()}, 대체=P.get("대체"))
            if 폴더 == "머리어깨" and 판 == "후":
                for n, (m, c, _) in 새.items(): P["부품"][n] = dict(파일=os.path.join(OUT, n + ".stl"), 색=c)
            os.makedirs(os.path.join(d, 폴더), exist_ok=True)
            json.dump(P, open(os.path.join(d, 폴더, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False)
        open(os.path.join(TMP, "구동.py"), "w", encoding="utf-8").write(구동.format(src=os.path.join(ROOT, "실험_20260927")))
        r = subprocess.run([BLENDER, "-b", "-P", os.path.join(TMP, "구동.py"), "--", d, os.path.join(TMP, 판)]); assert r.returncode == 0
    시트()
def 시트():
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 30)
    def 판(판, c): 
        im = Image.open(os.path.join(TMP, 판, "A_%s.png" % c)).convert("RGBA"); g = Image.new("RGBA", im.size, (205, 207, 212, 255)); g.alpha_composite(im); return g.convert("RGB")
    def 머리상자(im, 여유):
        a = np.asarray(Image.open(os.path.join(TMP, "전", "A_%s.png" % im)).split()[-1]) > 20
        ys, xs = np.nonzero(a); top = ys.min(); H = ys.max() - top
        cx = int(np.median(xs[ys < top + 0.12 * H]))
        s = int(여유 * H); return (cx - s // 2, top, cx + s // 2, top + s)
    칸 = []
    원 = Image.open(os.path.join(멋, "디테일비교.jpg")); 칸.append(("원화", 원.crop((335, 54, 709, 486))))
    칸.append(("FRA", 원.crop((1049, 54, 1478, 486))))
    b1 = 머리상자("얼굴정면", 0.16); b2 = 머리상자("영웅큰", 0.16)
    for 이름, c, b in (("정면", "얼굴정면", b1), ("영웅 3/4", "영웅큰", b2)):
        for 판_ in ("전", "후"): 칸.append(("%s %s" % (이름, 판_), 판(판_, c).crop(b)))
    전신 = [("전신 전", 판("전", "영웅큰")), ("전신 후", 판("후", "영웅큰"))]
    h = 480; row1 = [(t, im.resize((int(im.width * h / im.height), h), Image.LANCZOS)) for t, im in 칸]
    h2 = 900; row2 = [(t, im.resize((int(im.width * h2 / im.height), h2), Image.LANCZOS)) for t, im in 전신]
    W = min(2400, max(sum(i.width for _, i in row1), sum(i.width for _, i in row2)) + 10 * 8)
    S = Image.new("RGB", (max(sum(i.width for _, i in row1) + 70, sum(i.width for _, i in row2) + 30), h + h2 + 110), (245, 245, 243))
    d = ImageDraw.Draw(S); x = 10
    for t, im in row1: S.paste(im, (x, 45)); d.text((x + 6, 5), t, font=f, fill=(30, 30, 30)); x += im.width + 10
    x = 10
    for t, im in row2: S.paste(im, (x, h + 100)); d.text((x + 6, h + 58), t, font=f, fill=(30, 30, 30)); x += im.width + 10
    if S.width > 2400: S = S.resize((2400, int(S.height * 2400 / S.width)), Image.LANCZOS)
    S.save(os.path.join(멋, "얼굴_전후.jpg"), quality=90); print("시트", os.path.join(멋, "얼굴_전후.jpg"), S.size)
if __name__ == "__main__" and "--렌더" in sys.argv: 렌더()
if __name__ == "__main__" and "--시트만" in sys.argv: 시트()
