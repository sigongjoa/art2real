# -*- coding: utf-8 -*-
"""오메가몬 PG 얼굴 2 차 (2026-09-28) — 틀부터 다시: 건담식(창 + 속 얼굴판 · 귀 블록 · 가로 테) → 가면 투구 한 덩어리.

    python 얼굴2.py            -> out/출력/오메가몬_PG/디자인_얼굴2/*.stl · 부품.json(검사) · 멋/얼굴2_컨투어.jpg
    python 얼굴2.py --렌더     -> 위 + Blender 2 차 렌더 → 멋/얼굴2_전후.jpg (옛 · 1 차 렌더는 디자인_얼굴/_렌더 것 재사용)

치수 = 얼굴_컨투어.json 의 원화 · FRA 윤곽(정규화: 돔 꼭대기 0 · 턱 끝 1)을 반폭 표로 · 모양 = 키트 문법(모따기 능선 · 틀 + 메움판 · 덧판).
원본(디자인_머리어깨.py · 얼굴.py)은 안 고친다. 뿔은 1 차 테이퍼 뿔(소켓 뿌리 같음) · 안테나 · 투구뒤 다보 · 목 격벽은 옛 것.
"""
import os, sys, json, subprocess
import numpy as np, trimesh, manifold3d as M
from scipy.spatial.transform import Rotation as Rot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 얼굴 as F1                                   # 옛 부품 · 1 차 뿔 · 도우미(볼록 · 밀기 · 검사)
from 얼굴 import 볼록, 밀기, 메, 얇은곳, 읽기, ROOT, DES, 멋, J, 틈

OUT = os.path.join(ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴2"); os.makedirs(OUT, exist_ok=True)
옛 = F1.옛
벽 = 1.6

# ── 1. 정면 윤곽(반폭 표) · 앞 가운데 y · 옆으로 휘어 들어가는 깊이 D ──
ZT, ZC = 293.3, 263.0; H = ZT - ZC                  # 돔 꼭대기(옛 투구뒤와 같음) · 턱 끝(옛 얼굴보다 1.4 아래)
def zv(v): return ZT - H * v
#        v     반폭w  앞y    D      (w/H: 원화 0.42 · FRA 0.40 최대 → 0.42 · 턱은 V)
표 = [(0.03, 4.0, 8.0, 3.0), (0.08, 7.2, 4.5, 4.0), (0.15, 9.6, 1.5, 5.0), (0.25, 11.4, -0.6, 5.5),
      (0.35, 12.4, -1.8, 6.0), (0.45, 12.7, -2.2, 6.0), (0.55, 12.5, -2.2, 6.0), (0.65, 11.6, -2.0, 5.5),
      (0.75, 9.8, -1.8, 5.0), (0.85, 7.2, -1.5, 4.0), (0.93, 4.2, -1.2, 2.8), (1.00, 0.8, -0.8, 1.2)]
# 볼 가드(FRA 번역: 아래 옆으로 조금 벌림) — 정면 (x, z)
가드 = [(10.4, 273.8), (14.4, 273.2), (15.2, 270.6), (13.2, 267.6), (9.6, 266.4)]

def 윤곽(가드포함=True):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    반 = [(0.0, ZT + 0.2), (3.2, ZT + 0.2)] + [(w, zv(v)) for v, w, _, _ in 표] + [(0.0, ZC)]
    P = [Polygon(반 + [(-x, z) for x, z in 반[::-1]])]
    if 가드포함: P += [Polygon([(s * x, z) for x, z in 가드]) for s in (1, -1)]
    from shapely.geometry.polygon import orient
    g = orient(unary_union(P).buffer(0), 1.0)              # 반시계(CrossSection 채움 규칙)
    return [list(g.exterior.coords)[:-1]]
def 기둥(poly2d, 안=0.0):
    """정면 (x,z) 윤곽을 y −20..40 로 민 기둥(안 > 0 이면 그만큼 안으로)."""
    cs = M.CrossSection(poly2d)
    if 안: cs = cs.offset(-안, M.JoinType.Miter)
    return cs.extrude(60.0).rotate([90, 0, 0]).translate([0, 40.0, 0])

# 이음선(y = 15) 단면 = 옛 투구뒤 앞면 — 가면 hull 의 뒤끝이 여기 딱 맞는다
tb = 메(옛["투구뒤"]); sec = tb.section([0, 1, 0], [0, 15.02, 0])
이음 = np.array([(x, 15.0, z) for x, _, z in sec.vertices])
이음 = 이음[np.abs(이음[:, 0]) <= 11.3]              # 옛 귀(볼 가리개) 뺌
면점 = []
for v, w, y0, D in 표:
    for x in np.linspace(-w, w, 11): 면점.append((x, y0 + D * (x / w) ** 2, zv(v)))
    for s in (-1, 1): 면점.append((s * w, 11.5 if v > 0.1 else y0 + D + 2.0, zv(v)))
P겉 = np.vstack([면점, 이음])
기둥겉, 기둥속 = 기둥(윤곽()), 기둥(윤곽(), 벽)
앞반 = M.Manifold.cube([80, 60, 80]).translate([-40, -45, 240])     # y < 15
새겉 = 볼록(P겉) ^ 기둥겉 ^ 앞반
새속 = 볼록(밀기(P겉, -벽)) ^ 기둥속

def y앞(x, z, m=새겉):   # (x, z) 에서 겉면 y
    b = (m ^ M.Manifold.cube([0.1, 60, 0.1]).translate([x - 0.05, -30, z - 0.05])).bounding_box()
    return b[1]

# ── 2. 목 · 머리 뼈 여유(디자인_머리어깨.py 와 같은 식) ──
조립D = os.path.join(ROOT, "out", "가동", "관절배치"); 프레임D = os.path.join(ROOT, "out", "가동", "프레임")
def 있으면(f): return 읽기(f) if os.path.exists(f) else M.Manifold()
Pn = np.array(J["목위"]["피벗mm"])
목뼈 = 볼록(밀기(np.asarray((있으면(os.path.join(프레임D, "목.stl")) + 있으면(os.path.join(조립D, "관절_목위_부모.stl"))
                   + 있으면(os.path.join(조립D, "관절_목아래_자식.stl"))).hull().to_mesh().vert_properties)[:, :3], 0.3))
쓸 = []
for rx in (-25, -12, 0, 10, 20):
    for ry in (-15, 0, 15):
        ps = [목뼈.transform(np.hstack([R, (Pn - R @ Pn).reshape(3, 1)])) for R in
              [Rot.from_euler("xyz", [rx, ry, rz], degrees=True).inv().as_matrix() for rz in range(-45, 46, 15)]]
        쓸 += [(a + b).hull() for a, b in zip(ps[:-1], ps[1:])]
목쓸기 = M.Manifold.batch_boolean(쓸, M.OpType.Add)
def 구(p, r): return M.Manifold.sphere(r, 64).translate(list(map(float, p)))
쐐기 = 볼록([(0, Pn[1], z) for z in (230.0, Pn[2])] + [(sx * 40 * np.sin(np.radians(28)), Pn[1] - 40 * np.cos(np.radians(28)), z)
                                                   for sx in (-1, 1) for z in (230.0, Pn[2])])
아래막 = M.Manifold.cube([80, 80, Pn[2] - 230.0]).translate([-40, -20, 230.0]) - 구(Pn, 11.2) - (쐐기 ^ 구(Pn, 21.8))
머리막 = 목쓸기 + 아래막 + 있으면(os.path.join(프레임D, "머리.stl")) + 있으면(os.path.join(조립D, "관절_목위_자식.stl"))

_d = [np.array(v, float) / np.linalg.norm(v) for v in [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)] + [(i, j, k) for i in (-1, 1) for j in (-1, 1) for k in (-1, 1)]]
def 부풀(m, r): return M.Manifold.batch_boolean([m] + [m.translate(list(r * v)) for v in _d], M.OpType.Add)

뿔 = F1.뿔; 안L, 안R = 옛["V안테나L"], 옛["V안테나R"]
꽂는것 = 부풀(뿔 + 안L + 안R, 틈)

# ── 3. 이마 V 능선(가면과 한 몸 · 모따기 두 면): 뿔 앞 밑동(z 288.5) → 눈 사이(z 277.2) ──
능위, 능아래 = 288.5, 277.2
능 = []
for z, 반폭, 솟음 in ((능위, 3.4, 1.9), (능아래, 0.5, 0.5)):
    yc = y앞(0.0, z); 능.append((0, yc - 솟음, z))
    for s in (-1, 1): 능 += [(s * 반폭, y앞(s * 반폭, z) + 0.8, z), (s * 반폭, y앞(s * 반폭, z) - 0.01, z)]
이마능 = 볼록(능)

# ── 4. 눈: 이마 밑 · 바깥이 치켜 오른 육각 창(틀) + 뒤에서 끼우는 초록 메움판(틈 0.12 · 앞 0.5 들어감) ──
눈반 = [(1.5, 277.0), (2.6, 278.3), (7.6, 279.9), (8.9, 279.1), (7.5, 277.5), (2.8, 276.1)]
def 눈조각(s):
    from shapely.geometry import Polygon
    P = [(s * x, z) for x, z in 눈반]; pg = Polygon(P)
    작 = list(pg.buffer(-틈, join_style=2).exterior.coords)[:-1]; 큰 = list(pg.buffer(0.9, join_style=2).exterior.coords)[:-1]
    창 = 볼록([(x, -10.0, z) for x, z in P] + [(x, y앞(x, z) + 벽 + 0.6, z) for x, z in P])
    마개 = 볼록([(x, y앞(x, z) + 0.5, z) for x, z in 작] + [(x, y앞(x, z) + 벽 + 0.5, z) for x, z in 작])
    테 = 볼록([(x, y앞(x, z) + 벽 + 틈, z) for x, z in 큰] + [(x, y앞(x, z) + 벽 + 틈 + 0.9, z) for x, z in 큰])
    return 창, 마개 + 테
창L, 눈L = 눈조각(-1); 창R, 눈R = 눈조각(1)

# ── 5. 볼 가드(흰 덧판 · 따로) : 가면 옆 아래에 얹혀 폭을 조금 벌린다 · 앞 모서리 0.6 모따기 ──
가드들 = {}
for s, 이름 in ((1, "볼가드R"), (-1, "볼가드L")):
    P = [(s * x, z) for x, z in 가드]
    from shapely.geometry import Polygon
    안P = list(Polygon(P).buffer(-0.6, join_style=2).exterior.coords)[:-1]
    가드들[이름] = 볼록([(x, 3.2, z) for x, z in P] + [(x, 2.6, z) for x, z in 안P] + [(x, 13.0, z) for x, z in P]) ^ 기둥겉

# ── 6. 조립: 가면 투구 = 껍질 + 능선 + (옛 투구앞 속 격벽 · 소켓 · 다보 ∩ 새 속) − 창 − 뼈/목 여유 − 꽂는 것 − 가드 자리 ──
껍질 = (새겉 - 새속) + 이마능 + ((옛["투구앞"] ^ 새속) ^ 앞반)
가면 = 껍질 - 창L - 창R - 머리막 - 꽂는것 - 부풀(가드들["볼가드L"] + 가드들["볼가드R"], 틈)
가면 = max(가면.decompose(), key=lambda p: p.volume())      # 옛 속 조각의 부피 0 부스러기 · 뒤집힌 빈 방울 버림
눈L, 눈R = [max((e - 부풀(가면, 틈)).decompose(), key=lambda p: p.volume()) for e in (눈L, 눈R)]   # 옛 속 격벽이 테 귀퉁이를 떼어 낸 부스러기 버림
투구뒤 = 옛["투구뒤"] ^ 기둥겉                               # 옛 귀 · 넓은 아랫단을 새 윤곽으로 잘라 V 턱이 뒤에서 안 비치게
색 = dict(흰=[0.93, 0.93, 0.95], 은=[0.80, 0.82, 0.86], 초록=[0.15, 0.72, 0.35])
새 = {"가면투구": (가면, 색["흰"], "투구 앞 + 얼굴 한 판 · 둥근 돔 → V 턱 로프트 · 이마 V 능선 한 몸 · 육각 눈 창 · 벽 1.6"),
      "투구뒤": (투구뒤, 색["흰"], "옛 투구뒤 ∩ 새 정면 윤곽(귀 · 넓은 아랫단 없앰) · 다보 그대로"),
      "눈L": (눈L, 색["초록"], "눈 메움판 — 뒤에서 끼움 · 틈 0.12 · 테 0.9"),
      "눈R": (눈R, 색["초록"], "눈 메움판"),
      "볼가드L": (가드들["볼가드L"], 색["흰"], "볼 가드 덧판 — 가면 옆 자리에 끼워 붙임(틈 0.12)"),
      "볼가드R": (가드들["볼가드R"], 색["흰"], "볼 가드 덧판"),
      "뿔": (뿔, 색["은"], "1 차 테이퍼 뿔 그대로(소켓 뿌리 옛과 같음)")}
대체 = ["투구앞", "투구뒤", "얼굴", "뿔"]

# ════════════ 컨투어 재측정: 정면 정사영 실루엣(뿔 · 안테나 뺌) → 얼굴_컨투어.py 와 같은 정규화 · 격자 ════════════
def 실루엣(ms, N=600):
    from PIL import Image, ImageDraw
    V = [],
    tris = []
    for m in ms:
        t = m.to_mesh(); v = np.asarray(t.vert_properties)[:, :3]; tris.append(v[np.asarray(t.tri_verts)])
    T = np.vstack(tris); zt, zc = T[:, :, 2].max(), T[:, :, 2].min(); s = zt - zc
    im = Image.new("L", (N, N)); dr = ImageDraw.Draw(im); sc = N / 2.6
    for tri in T: dr.polygon([((x / s + 1.3) * sc, ((zt - z) / s + 1.4) * sc) for x, _, z in tri], fill=1)
    a = np.array(im, bool); cols = np.nonzero(a.any(0))[0]
    return a, dict(폭=round((cols.max() - cols.min() + 1) / sc, 3), 높이mm=round(s, 1))
def 컨투어():
    import 얼굴_컨투어 as C
    from PIL import Image, ImageDraw, ImageFont
    판들 = {"옛": [옛[n] for n in ("투구앞", "투구뒤", "얼굴")],
           "1차": [F1.새[n][0] for n in ("투구앞", "얼굴", "얼굴이마V", "얼굴눈L", "얼굴눈R", "얼굴볼판L", "얼굴볼판R", "얼굴턱")] + [옛["투구뒤"]],
           "2차": [새[n][0] for n in 새 if n != "뿔"]}
    R = {}
    for k, ms in 판들.items():
        a, st = 실루엣(ms); R[k] = dict(마스크=a, 원화IoU=round(C.iou(a, C.M0["원화"]), 3), FRA_IoU=round(C.iou(a, C.M0["FRA"]), 3), **st)
    기준 = round(C.iou(C.M0["원화"], C.M0["FRA"]), 3)
    # 그림: 칸 셋(옛 · 1 차 · 2 차) — 각 칸 = 원화 윤곽(빨강 선) · FRA(파랑 선) · 우리(초록 채움)
    f = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 26); P = 600
    img = Image.new("RGB", (3 * P + 40, P + 120), "white"); dr = ImageDraw.Draw(img); sc = P / 2.6
    def px(p): return [((x + 1.3) * sc, (y + 1.4) * sc) for x, y in p]
    for i, k in enumerate(("옛", "1차", "2차")):
        ox = 10 + i * (P + 10); a = R[k]["마스크"]
        rgb = np.full(a.shape + (3,), 255, np.uint8); rgb[a] = (170, 225, 180)
        img.paste(Image.fromarray(rgb), (ox, 60)); d2 = ImageDraw.Draw(img)
        for n, c in (("원화", (220, 30, 30)), ("FRA", (20, 120, 230))):
            b = C.S[n][0]; d2.line([(x + ox, y + 60) for x, y in px(b + b[:1])], fill=c, width=3)
        d2.text((ox + 6, 8), "③ %s  원화 IoU %.2f · FRA %.2f · 폭/높이 %.2f" % (k, R[k]["원화IoU"], R[k]["FRA_IoU"], R[k]["폭"]), fill="black", font=f)
    dr.text((10, P + 75), "뿔 뺌 · 정면 정사영(메시) · 정규화 돔 꼭대기 0 → 가장 아래 1 · 빨강 원화 · 파랑 FRA · 초록 우리 · 기준선 원화↔FRA %.2f" % 기준, fill="black", font=f)
    img.save(os.path.join(멋, "얼굴2_컨투어.jpg"), quality=90)
    return {k: {kk: vv for kk, vv in v.items() if kk != "마스크"} for k, v in R.items()}, 기준

if __name__ == "__main__":
    이웃 = F1.이웃읽기(); 이웃.pop("투구뒤"); 이웃["목깃"] = 이웃["목깃"]
    for n in ("V안테나L", "V안테나R"): 이웃[n] = 옛[n]
    검사 = {}
    for n, (m, c, _) in 새.items():
        tm = 메(m); 검사[n] = dict(닫힘=bool(tm.is_watertight), 조각=len(m.decompose()), 부피mm3=round(m.volume(), 1),
                                 얇은곳mm3=얇은곳(m), 크기mm=np.round(tm.extents, 1).tolist())
    겹 = {}; ns = list(새)
    for i, a in enumerate(ns):
        for b in ns[i + 1:] + [k for k in 이웃 if not k.startswith("V안테나")] + ["V안테나L", "V안테나R"]:
            B = 새[b][0] if b in 새 else 이웃[b]; v = (새[a][0] ^ B).volume()
            if v > 0.005: 겹["%s∩%s" % (a, b)] = round(v, 3)
    몸 = 이웃["가슴앞"] + 이웃["목깃"]
    def 돌(m, d):
        R = Rot.from_rotvec([np.radians(d), 0, 0]).as_matrix(); return m.transform(np.hstack([R, (Pn - R @ Pn).reshape(3, 1)]))
    머리옛 = M.Manifold.batch_boolean(list(옛.values()), M.OpType.Add)
    머리새 = M.Manifold.batch_boolean([m for m, _, _ in 새.values()] + [안L, 안R], M.OpType.Add)
    끄덕 = {d: dict(옛=round((돌(머리옛, d) ^ 몸).volume(), 2), 새=round((돌(머리새, d) ^ 몸).volume(), 2)) for d in range(-25, 21, 5)}
    for n, (m, c, _) in 새.items(): 메(m).export(os.path.join(OUT, n + ".stl"))
    컨, 기준 = 컨투어()
    결과 = dict(검사=검사, 겹침=겹, 끄덕_겹침mm3_가슴목깃=끄덕, 컨투어=컨, 기준선_원화FRA=기준,
              눈높이v=[round((ZT - max(z for _, z in 눈반)) / H, 3), round((ZT - min(z for _, z in 눈반)) / H, 3)],
              눈폭_정규=round((8.9 - 1.5) / H, 3))
    json.dump(dict(설명="얼굴 2 차(09-28) — 머리어깨 부품 중 「대체」를 이 폴더 것으로 바꾼다.", 대체=대체,
                   부품={n: dict(파일=n + ".stl", 색=c, 비고=b, **검사[n]) for n, (m, c, b) in 새.items()}, **{k: v for k, v in 결과.items() if k != "검사"}),
              open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps(결과, ensure_ascii=False, indent=1, default=float))
    assert 0 < 컨["2차"]["원화IoU"] <= 1

# ════════════ 렌더(--렌더): 2 차만 새로 · 옛(전) · 1 차(후) 는 디자인_얼굴/_렌더 재사용 ════════════
TMP = os.path.join(OUT, "_렌더"); TMP1 = os.path.join(F1.OUT, "_렌더")
def 렌더():
    d = os.path.join(TMP, "DES")
    for 폴더 in ("몸통", "다리", "머리어깨", "색분할", "돌출"):
        P = json.load(open(os.path.join(DES, 폴더, "부품.json"), encoding="utf-8"))
        P = dict(부품={n: dict(v, 파일=os.path.join(DES, 폴더, v.get("파일", n + ".stl"))) for n, v in P["부품"].items()}, 대체=P.get("대체"))
        if 폴더 == "머리어깨":
            for n in ("투구앞", "얼굴"): P["부품"].pop(n, None)
            for n, (m, c, _) in 새.items(): P["부품"][n] = dict(파일=os.path.join(OUT, n + ".stl"), 색=c)
        os.makedirs(os.path.join(d, 폴더), exist_ok=True)
        json.dump(P, open(os.path.join(d, 폴더, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False)
    open(os.path.join(TMP, "구동.py"), "w", encoding="utf-8").write(F1.구동.format(src=os.path.join(ROOT, "실험_20260927")))
    r = subprocess.run([F1.BLENDER, "-b", "-P", os.path.join(TMP, "구동.py"), "--", d, TMP]); assert r.returncode == 0
    시트()
def 시트():
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 30)
    def 판(p, c):
        im = Image.open(os.path.join(p, "A_%s.png" % c)).convert("RGBA"); g = Image.new("RGBA", im.size, (205, 207, 212, 255)); g.alpha_composite(im); return g.convert("RGB")
    def 머리상자(c, 여유=0.16):
        a = np.asarray(Image.open(os.path.join(TMP1, "전", "A_%s.png" % c)).split()[-1]) > 20
        ys, xs = np.nonzero(a); top = ys.min(); Hh = ys.max() - top
        cx = int(np.median(xs[ys < top + 0.12 * Hh])); s = int(여유 * Hh); return (cx - s // 2, top, cx + s // 2, top + s)
    원 = Image.open(os.path.join(멋, "디테일비교.jpg"))
    판경로 = [("옛", os.path.join(TMP1, "전")), ("1차", os.path.join(TMP1, "후")), ("2차", TMP)]
    줄 = []
    for 이름, c in (("정면", "얼굴정면"), ("3/4", "영웅큰")):
        b = 머리상자(c); 칸 = [("원화", 원.crop((335, 54, 709, 486))), ("FRA", 원.crop((1049, 54, 1478, 486)))] if 이름 == "정면" else [("", None), ("", None)]
        칸 += [("%s %s" % (k, 이름), 판(p, c).crop(b)) for k, p in 판경로]; 줄.append(칸)
    h = 430; 전신 = [("전신 옛", 판(판경로[0][1], "영웅큰")), ("전신 2차", 판(TMP, "영웅큰"))]; h2 = 900
    def rs(im, hh): return im.resize((int(im.width * hh / im.height), hh), Image.LANCZOS)
    W = 5 * (h + 10) + 10
    S = Image.new("RGB", (max(W, 2 * int(h2 * 1500 / 1950) + 30), 2 * (h + 45) + h2 + 60), (245, 245, 243)); d = ImageDraw.Draw(S)
    for r, 칸 in enumerate(줄):
        x = 10; y = 45 + r * (h + 45)
        for t, im in 칸:
            if im is not None: im = rs(im, h); S.paste(im.crop((0, 0, h, h)) if im.width > h else im, (x, y)); d.text((x + 6, y - 38), t, font=f, fill=(30, 30, 30))
            x += h + 10
    x = 10; y = 2 * (h + 45) + 50
    for t, im in 전신: im = rs(im, h2); S.paste(im, (x, y)); d.text((x + 6, y - 40), t, font=f, fill=(30, 30, 30)); x += im.width + 10
    if S.width > 2400: S = S.resize((2400, int(S.height * 2400 / S.width)), Image.LANCZOS)
    S.save(os.path.join(멋, "얼굴2_전후.jpg"), quality=90); print("시트", os.path.join(멋, "얼굴2_전후.jpg"), S.size)
if __name__ == "__main__" and "--렌더" in sys.argv: 렌더()
if __name__ == "__main__" and "--시트만" in sys.argv: 시트()
