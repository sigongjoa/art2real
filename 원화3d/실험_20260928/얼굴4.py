# -*- coding: utf-8 -*-
"""오메가몬 PG 얼굴 4 차 — 비율 고침(2026-09-28). 눈 모양(눈 고침 4)은 그대로, 크기 · 위치만. 치수는 얼굴_점수표.json 의 FRA 손 좌표.

    python 얼굴4.py --빠른 N   -> 디자인_얼굴4/*.stl + _바퀴/바퀴N.jpg (FRA | 눈4 | 얼굴4 정면 · 반옆)
    python 얼굴4.py --검사     -> 위 + 닫힘 · 겹침(가면 얇은살 검사는 안 함 — 메모리)
    python 얼굴4.py --점수     -> 모델 기하에서 점수표 좌표를 뽑아(눈4 · 얼굴4 같은 방식) 점수표 식으로 잼 → _바퀴/점수.json
    python 얼굴4.py --렌더     -> 전신 렌더 + 멋/얼굴4_전후.jpg

바꾼 것: ① z 사상 f(돔 꼭대기 · 턱 끝 고정, 눈두덩 · 능선 · 뿔 밑동을 위로) ② 주둥이 = 가로로 넓은 윗입술 판(코 쐐기) ③ 턱 = 판 뒤 한 단 들어간 넓은 아래 얼굴
④ 눈 = 눈4 윤곽 그대로 0.8 배(홍채 · 눈동자는 0.8 × 0.85) → FRA 눈구멍 중심 ⑤ 뿔 밑동 반폭 3.4 → 2.6 ⑥ 볼 날개 · 금 뿔 뿌리 = FRA 좌표.
ponytail: 돔 윤곽(이음 점)은 안 건드린다 — 투구뒤와 이어짐 유지. 「돔을 낮춤」= 안쪽 구조를 올려 같은 효과.
"""
import os, sys, json, subprocess
import numpy as np, manifold3d as M
from shapely.geometry import Polygon, MultiPoint, LineString, box as sbox
from shapely import affinity
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 얼굴3_눈4 as E4                       # (얼굴3 · 얼굴3_눈 도 같이 지어짐)
import 얼굴3 as F3
from 얼굴3 import 덩이, 속, 볼록, 메, 틈, 벽, 색, 멋, FRA, V홈, 대칭

OUT = os.path.join(F3.ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴4"); os.makedirs(OUT, exist_ok=True)
바퀴D = os.path.join(OUT, "_바퀴"); os.makedirs(바퀴D, exist_ok=True)
SJ = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "얼굴_점수표.json"), encoding="utf-8"))["좌표"]

# ════════ FRA 손 좌표 → mm (눈4 정면 렌더와 같은 정규화: 돔 꼭대기 293.29 · 턱 끝 263.37 · 머리 반폭(날개 끝) 17.42) ════════
_F = SJ["FRA"]; _H = 293.29 - 263.37; _W = 17.42 / (_F["axis"] - min(x for x, _ in _F["부위"]["머리외곽"]))
def mm(p): return ((_F["axis"] - p[0]) * _W, 293.29 - (p[1] - _F["top"]) * _H / (_F["chin"] - _F["top"]))
FRA눈 = Polygon([mm(p) for p in _F["부위"]["눈구멍"]])

# ════════ ① z 사상 ════════
사상 = ([262.0, 263.3, 277.0, 285.5, 293.3], [262.0, 263.3, 279.0, 288.8, 293.3])
def f(z): return float(np.interp(z, *사상))
def 올림(P): return [(x, y, f(z)) for x, y, z in P]

표 = {k: 올림(F3.표[k]) for k in ("두개", "눈두덩", "눈면")}
# ② 주둥이: 윗입술 판(앞 = 코 쐐기, 가로 ±8.4 · z 273.0~278.0 · 윗변 가운데가 눈두덩 V 에 닿고 눈구멍 아래 0.35 띄움 — 바퀴 2) — FRA 주둥이 (0,277.8)(7.8,278.1)(8.1,276.4)(4.8,274.6)(0,272.9) 에서 윗변만 눈구멍 밑으로 내림
표["주둥이"] = [(0, -6.4, 278.0), (0, -6.9, 273.0), (3.6, -4.6, 277.3), (7.8, -2.0, 277.0), (8.4, -1.6, 275.8), (4.8, -3.8, 274.2),
               (0, 4.0, 278.0), (8.2, 4.0, 277.0), (8.2, 4.0, 275.4), (0, 4.0, 272.8)]
# ③ 턱: 판 뒤 한 단(앞 y 가 판보다 1.4 뒤) · FRA 턱 (10.05,276.4)(10.8,270.0)(9.0,268.6)(6.6,266.5)(3.3,264.5)(0,263.3)
표["턱"] = [(0, -5.3, 272.8), (4.6, -3.6, 273.8), (9.8, -0.7, 275.8), (10.6, -0.1, 270.0), (9.0, -1.2, 268.4), (6.6, -2.2, 266.3),
           (3.3, -3.2, 264.4), (0, -3.6, 263.3)]
뒤 = {"눈면": [(x, f(z)) for x, z in F3.뒤["눈면"]], "턱": [(10.6, 275.8), (10.6, 270.0), (9.0, 268.4), (6.6, 266.3), (0, 264.0)]}
# ⑥ 볼 날개(정면 x, z) — FRA (12.3,278.8)(14.1,275.2)(17.4,269.7)(13.8,269.7)(10.8,270)(10.05,276.4)
날개 = [(10.0, 276.6), (12.3, 278.6), (17.4, 269.7), (13.8, 269.5), (10.6, 270.2)]
송곳니 = dict(x=4.4, 위=273.2, 아래=269.8)       # FRA 송곳니: 판 아래 끝에서 내려옴(x ≈ 4~4.8)
# ⑤ 뿔: 밑동 반폭 2.6(능선과 같음) · 밑동 z = f(285.5)
zb = f(285.5)
뿔단 = [(zb, [(0, -3.8), (2.6, -0.6), (2.6, 5.0), (0, 9.0)]), (299.0, [(0, 0.6), (1.6, 2.6), (1.6, 6.6), (0, 9.4)]), (324.0, [(0, 11.4), (0.4, 11.8), (0, 12.4)])]
능선 = [(0, -3.8, zb), (2.6, -0.6, zb), (2.6, 3.0, zb), (0, -6.4, f(276.6)), (0.7, -5.9, f(276.6)), (0.7, 0.0, f(276.6))]

점 = {k: list(v) + [(x, 15.0, z) for x, z in 뒤.get(k, [])] for k, v in 표.items()}
점["두개"] += F3.이음
날개점 = [(x, 1.5 + 0.6 * (x - 9), z) for x, z in 날개] + [(x, 14.0, z) for x, z in 날개]
날개덩이 = 덩이(날개점) + 덩이([(-x, y, z) for x, y, z in 날개점])
새겉 = M.Manifold.batch_boolean([덩이(p) for p in 점.values()] + [덩이(능선), 날개덩이], M.OpType.Add) ^ F3.앞반
새속 = M.Manifold.batch_boolean([속(점[k]) for k in ("두개", "눈면", "턱")], M.OpType.Add)

def 단(z, P): return [(x, y, z) for x, y in P] + [(-x, y, z) for x, y in P if x > 0]
뿔 = M.Manifold.batch_boolean([볼록(단(*a) + 단(*b)) for a, b in zip(뿔단[:-1], 뿔단[1:])], M.OpType.Add) \
     + (F3.F1.뿔 ^ F3.F1.상자((-10, -10, 270), (10, 20, zb + 1.0)))
금이동 = (0.8, 3.2)                          # 금 뿔 뿌리: 안쪽 0.8 · 위 3.2 (FRA 금뿔뿌리 쪽으로)
안L = F3.안L.translate([금이동[0], 0, 금이동[1]]); 안R = F3.안R.translate([-금이동[0], 0, 금이동[1]])
if F3.안L.bounding_box()[0] > 0: 안L, 안R = F3.안L.translate([-금이동[0], 0, 금이동[1]]), F3.안R.translate([금이동[0], 0, 금이동[1]])
뿔 = max((뿔 - F3.F2.부풀(안L + 안R, 틈)).decompose(), key=lambda p: p.volume())   # 올린 금 뿔 뿌리가 옛 뿔 뿌리를 파고듦 → 뿔 쪽을 비움
꽂는것 = F3.F2.부풀(뿔 + 안L + 안R, 틈)

# ════════ ④ 눈: 눈4 윤곽을 0.8 배 · 홍채/눈동자는 추가 0.85 배 → FRA 눈구멍 중심 ════════
눈배, 홍배 = 0.8, 0.85
def 옮(g, c0, c1): return affinity.translate(affinity.scale(g, 눈배, 눈배, origin=c0), c1[0] - c0[0], c1[1] - c0[1])
_눈4 = (E4.구멍, E4.홍채, E4.동자)            # 눈4 원본(점수 전/후용)
c0 = E4.구멍.centroid.coords[0]; c1 = FRA눈.centroid.coords[0]
구멍 = 옮(E4.구멍, c0, c1); 홍채 = 옮(E4.홍채, c0, c1); 동자 = 옮(E4.동자, c0, c1)
ci = 홍채.centroid; 홍채 = affinity.scale(홍채, 홍배, 홍배, origin=ci); 동자 = affinity.scale(동자, 홍배, 홍배, origin=ci)
assert 구멍.contains(홍채) and 홍채.contains(동자.buffer(0.3)), "홍채/눈동자 자리"
E4.구멍, E4.홍채, E4.동자 = 구멍, 홍채, 동자          # 눈조각() 은 E4 의 전역을 읽는다
창L, 바탕L, 눈L = E4.눈조각(-1); 창R, 바탕R, 눈R = E4.눈조각(1)

껍질 = (새겉 - 새속) + ((F3.옛["투구앞"] ^ 새속) ^ F3.앞반)
가면 = V홈(껍질 - F3.F2.머리막 - 꽂는것, (0, -3.9, f(285.0)), (0, -6.2, f(277.2)), (0, -1, 0.3), 폭=0.6, 깊=0.5)
for s in (1, -1):
    가면 = 가면 - 볼록([(s * x, y, z) for x in (송곳니["x"] - 0.45, 송곳니["x"] + 0.45) for y in (-7, -2.0)
                     for z in (송곳니["위"], 송곳니["아래"] + 1.5)] + [(s * 송곳니["x"], y, 송곳니["아래"]) for y in (-7, -2.2)])
가면 = max((가면 - 창L - 창R).decompose(), key=lambda p: p.volume())
가면부풀 = F3.F2.부풀(가면, 틈)
바탕L, 바탕R = [max((e - 가면부풀).decompose(), key=lambda p: p.volume()) for e in (바탕L, 바탕R)]
윤곽기둥 = 새겉.rotate([-90, 0, 0]).project().extrude(60.0).rotate([90, 0, 0]).translate([0, 40.0, 0])
투구뒤 = (F3.옛["투구뒤"] ^ 윤곽기둥) - F3.F2.부풀(안L + 안R, 틈)

새 = {"가면투구": (가면, 색["흰"], "얼굴 4 차 가면 — 넓은 윗입술 판 + 한 단 들어간 넓은 턱 · 눈두덩/능선/뿔 밑동 올림"),
      "투구뒤": (투구뒤, 색["흰"], "옛 투구뒤 ∩ 새 정면 윤곽"),
      "눈바탕L": (바탕L, 색["검"], "검은 눈바탕(눈4 모양 0.8 배)"), "눈바탕R": (바탕R, 색["검"], "검은 눈바탕"),
      "눈L": (눈L, 색["초록"], "초록 홍채(눈4 모양 0.68 배)"), "눈R": (눈R, 색["초록"], "초록 홍채"),
      "V안테나L": (안L, 색["금"], "금 뿔 — 뿌리 안쪽 0.8 · 위 3.2"), "V안테나R": (안R, 색["금"], "금 뿔"),
      "뿔": (뿔, 색["흰"], "넓은 날 뿔 · 밑동 반폭 2.6 · 이마 능선과 이어짐 · 뿌리는 옛 소켓")}

def 내보내기():
    for n, (m, _, _) in 새.items():
        t = 메(m); assert t.is_watertight and len(m.decompose()) == 1, n + " 안 닫힘/조각 %d" % len(m.decompose())
        t.export(os.path.join(OUT, n + ".stl"))
    if "--검사" not in sys.argv: return
    이웃 = {k: v for k, v in F3.F1.이웃읽기().items() if k not in F3.대체}
    겹 = {}; ns = list(새)
    for i, a in enumerate(ns):
        for b in ns[i + 1:] + list(이웃):
            v = (새[a][0] ^ (새[b][0] if b in 새 else 이웃[b])).volume()
            if v > 0.005: 겹["%s∩%s" % (a, b)] = round(v, 3)
    검 = {n: dict(닫힘=True, 조각=1, 부피mm3=round(m.volume(), 1), 크기mm=np.round(메(m).extents, 1).tolist()) for n, (m, _, _) in 새.items()}
    for n in ("눈바탕L", "눈L"): 검[n]["얇은곳mm3"] = F3.얇은곳(새[n][0])
    끼움 = dict(눈바탕_가면틈0_12=round((바탕L ^ 가면부풀).volume(), 4), 홍채_바탕_직접=round((눈L ^ 바탕L).volume(), 4),
              홍채_옆틈0_1=round((눈L ^ 바탕L.translate([0.1, 0, 0])).volume() + (눈L ^ 바탕L.translate([0, 0, 0.1])).volume(), 4))
    json.dump(dict(설명="얼굴 4 차(09-28) 비율 고침", 사상=사상, 꼭짓점표=표, 날개=날개, 뿔단=뿔단, 겹침=겹, 끼움틈_겹침mm3=끼움,
                   부품={n: dict(파일=n + ".stl", 색=c, 비고=b, **검[n]) for n, (m, c, b) in 새.items()}),
              open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps(dict(검사=검, 겹침=겹, 끼움=끼움), ensure_ascii=False, default=float))

# ════════ 빠른 렌더 (얼굴3 과 같은 틀) ════════
def 빠른렌더(N):
    from PIL import Image, ImageDraw, ImageFont
    d = os.path.join(바퀴D, str(N)); os.makedirs(d, exist_ok=True)
    jf, pf = os.path.join(d, "빠른.json"), os.path.join(d, "빠른.py")
    json.dump(dict(부품=[(os.path.join(OUT, n + ".stl"), c) for n, (m, c, _) in 새.items()], out=d.replace("\\", "/"),
                   컷=[("정면", 0, 0, 70.0, 292.9), ("반옆", 62, 8, 70.0, 288.0)]), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    open(pf, "w", encoding="utf-8").write(F3.빠른.replace("line_thickness = 1.6", "line_thickness = 1.0"))
    r = subprocess.run([F3.F1.BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    f_ = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 24)
    D4 = os.path.join(F3.OUT, "_바퀴", "눈", "후4")
    칸 = [("FRA mh_12", Image.open(os.path.join(FRA, "mh_12.jpg")).resize((597, 600))),
          ("눈 고침 4", Image.open(os.path.join(D4, "정면.png")).convert("RGB").resize((597, 600))),
          ("얼굴 4 (바퀴 %s)" % N, Image.open(os.path.join(d, "정면.png")).convert("RGB").resize((597, 600)))]
    S = Image.new("RGB", (3 * 607 + 10, 650), "white"); dr = ImageDraw.Draw(S); x = 10
    for t, im in 칸:
        S.paste(im, (x, 45)); dr.text((x + 4, 6), t, font=f_, fill="black")
        for z in (279.4, 273.2, 263.4):      # FRA 눈 중심 · 코끝 · 턱 끝 (mh_12 틀과 렌더 틀 각각)
            py = (235 + (293.29 - z) / _H * 207) * 600 / 450 if t.startswith("FRA") else (450 - (z - 292.9) * 12.8) * 600 / 900
            dr.line([(x, 45 + py), (x + 597, 45 + py)], fill=(255, 0, 0), width=1)
        x += 607
    p = os.path.join(바퀴D, "바퀴%s.jpg" % N); S.save(p, quality=88)
    Image.open(os.path.join(d, "반옆.png")).convert("RGB").save(os.path.join(바퀴D, "반옆%s.jpg" % N), quality=88); print(p)

# ════════ 점수: 모델 기하 → 점수표 좌표(렌더 px) — 눈4 와 얼굴4 를 같은 방식으로 ════════
def 좌표뽑기(겉, 덩, 구멍_, 홍채_, 동자_, 날개_, 뿔단_, 능선바닥, 안테나):
    def P(x, z): return [448 - x * 12.8, 450 - (z - 292.9) * 12.8]
    def 앞(m): return Polygon(MultiPoint([(v[0], v[2]) for v in np.asarray(m.to_mesh().vert_properties)[:, :3]]).convex_hull.exterior.coords)
    def 반(g): g = g.intersection(sbox(0, 0, 60, 400)); g = max(g.geoms, key=lambda q: q.area) if hasattr(g, "geoms") else g; return [P(x, z) for x, z in list(g.exterior.coords)[:-1]]
    V = np.asarray(겉.to_mesh().vert_properties)[:, :3]; top, chin = V[:, 2].max(), V[:, 2].min()
    실 = unary_union([Polygon(c) for c in 겉.rotate([-90, 0, 0]).project().to_polygons() if len(c) > 2])
    프 = [(0.0, top)]
    for z in np.linspace(top - 0.05, chin + 0.05, 120):
        s = 실.intersection(LineString([(0, z), (40, z)]))
        if not s.is_empty: 프.append((s.bounds[2], z))
    프.append((0.0, chin))
    주, 턱_, 눈두 = 앞(덩["주둥이"]), 앞(덩["턱"]), 앞(덩["눈두덩"])
    날 = Polygon(날개_); 턱보임 = 턱_.difference(주).difference(날)
    xs = np.linspace(0, 눈두.bounds[2] - 0.05, 12)
    눈두선 = [P(x, 눈두.intersection(LineString([(x, 0), (x, 400)])).bounds[1]) for x in xs[::-1]]
    wb, zb_ = 뿔단_[0][1][1][0], 뿔단_[0][0]
    뿔선 = [P(0, 뿔단_[-1][0]), P(뿔단_[1][1][1][0], 뿔단_[1][0]), P(wb, zb_), P(0, 능선바닥)]
    A = np.asarray(안테나.to_mesh().vert_properties)[:, :3]
    if A[:, 0].mean() < 0: A[:, 0] *= -1
    금 = MultiPoint([(x, z) for x, _, z in A]).convex_hull.difference(실)            # 보이는 몫만(머리에 묻힌 뿌리 뺌)
    금 = max(금.geoms, key=lambda q: q.area) if hasattr(금, "geoms") else 금
    gx = np.array(금.exterior.coords); 뿌 = gx[gx[:, 0] < gx[:, 0].min() + 1.5]; 뿌 = np.c_[뿌[:, 0], 뿌[:, 0] * 0, 뿌[:, 1]]
    ex = np.array(구멍_.exterior.coords); 코 = min((p for p in 주.exterior.coords if abs(p[0]) < 1e-6), key=lambda p: p[1])
    wt = max(날개_, key=lambda p: p[0])
    return dict(axis=448, top=round(P(0, top)[1], 1), chin=round(P(0, chin)[1], 1), flip=False,
                부위=dict(머리외곽=[P(x, z) for x, z in 프], 가운데뿔=뿔선, 금뿔=반(금), 눈구멍=반(구멍_), 홍채=반(홍채_), 눈동자=반(동자_), 눈두덩=눈두선,
                         주둥이=반(주), 턱=반(턱보임), 볼날개=반(날)),
                기준점=dict(눈안쪽=P(*ex[ex[:, 0].argmin()]), 눈꼬리=P(*ex[ex[:, 0].argmax()]), 눈동자=P(*동자_.centroid.coords[0]), 코끝=P(*코),
                          턱끝=P(0, chin), 뿔밑동=P(wb, zb_), 볼날개끝=P(*wt), 금뿔뿌리=P(뿌[:, 0].mean(), 뿌[:, 2].mean())))

def 점수():
    덩3 = {k: 덩이(v) for k, v in F3.점.items()}; 덩3["주둥이"] = 덩3["부리"]
    덩4 = {k: 덩이(v) for k, v in 점.items()}
    J = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "얼굴_점수표.json"), encoding="utf-8"))
    J.pop("결과", None)
    J["좌표"] = {k: J["좌표"][k] for k in ("FRA", "FRA2", "눈4")}
    J["좌표"]["눈4자동"] = dict(file=os.path.join(F3.OUT, "_바퀴", "눈", "후4", "정면.png"),
                           **좌표뽑기(F3.새겉, 덩3, _눈4[0], _눈4[1], _눈4[2], F3.날개, F3.뿔단, 276.6, F3.안R))
    J["좌표"]["얼굴4"] = dict(file=os.path.join(바퀴D, sys.argv[sys.argv.index("--점수") + 1], "정면.png"),
                          **좌표뽑기(새겉, 덩4, 구멍, 홍채, 동자, 날개, 뿔단, f(276.6), 안R))
    jp = os.path.join(바퀴D, "점수.json"); json.dump(J, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "얼굴_점수표.py"), encoding="utf-8").read()
    src = src.split("\nlose = {")[0]                          # 옛 얼굴 이름을 쓰는 단언은 뺌
    src = src.replace('JP = os.path.join(H_, "얼굴_점수표.json")', "JP = %r" % jp).replace('OUT = r"', 'OUT_ = r"') \
             .replace("img.save(OUT", "img.save(%r" % os.path.join(바퀴D, "점수표.jpg")).replace("W = 8 * (P + 4) + 4", "W = max(len(NAMES), 6) * (P + 4) + 4")
    exec(compile(src, "점수표", "exec"), dict(__name__="점수표", __file__=os.path.abspath("얼굴_점수표.py")))

# ════════ 전신 렌더(눈4 · 얼굴4 둘 다 같은 구동) + 전후 시트 ════════
def 전신(TMP, 부품):
    DES = F3.DES; d = os.path.join(TMP, "DES")
    for 폴더 in ("몸통", "다리", "머리어깨", "색분할", "돌출"):
        P = json.load(open(os.path.join(DES, 폴더, "부품.json"), encoding="utf-8"))
        P = dict(부품={n: dict(v, 파일=os.path.join(DES, 폴더, v.get("파일", n + ".stl"))) for n, v in P["부품"].items()}, 대체=P.get("대체"))
        if 폴더 == "머리어깨":
            for n in ("투구앞", "얼굴"): P["부품"].pop(n, None)
            for n, (fp, c) in 부품.items(): P["부품"][n] = dict(파일=fp, 색=c)
        os.makedirs(os.path.join(d, 폴더), exist_ok=True)
        json.dump(P, open(os.path.join(d, 폴더, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False)
    open(os.path.join(TMP, "구동.py"), "w", encoding="utf-8").write(F3.F1.구동.format(src=os.path.join(F3.ROOT, "실험_20260927")))
    r = subprocess.run([F3.F1.BLENDER, "-b", "-P", os.path.join(TMP, "구동.py"), "--", d, TMP], capture_output=True); assert r.returncode == 0, r.stderr[-1500:]
def 렌더(N):
    v5 = {"가면투구", "눈바탕L", "눈바탕R", "눈L", "눈R"}
    눈4 = {n: (os.path.join(F3.OUT, n + ("_v5" if n in v5 else "") + ".stl"), c) for n, (m, c, _) in F3.새.items()}
    눈4["V안테나L"] = (os.path.join(F3.바퀴D, "V안테나L.stl"), 색["금"]); 눈4["V안테나R"] = (os.path.join(F3.바퀴D, "V안테나R.stl"), 색["금"])
    T4, T5 = os.path.join(OUT, "_렌더_눈4"), os.path.join(OUT, "_렌더")
    for t, b in ((T4, 눈4), (T5, {n: (os.path.join(OUT, n + ".stl"), c) for n, (m, c, _) in 새.items()})):
        os.makedirs(t, exist_ok=True)
        if "--시트만" not in sys.argv: 전신(t, b)
    from PIL import Image, ImageDraw, ImageFont
    f_ = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
    def 판(p, c): im = Image.open(os.path.join(p, "A_%s.png" % c)).convert("RGBA"); g = Image.new("RGBA", im.size, (205, 207, 212, 255)); g.alpha_composite(im); return g.convert("RGB")
    def 머리(p, c, k=0.2):
        a = np.asarray(Image.open(os.path.join(p, "A_%s.png" % c)).split()[-1]) > 20; ys, xs = np.nonzero(a); top = ys.min(); Hh = ys.max() - top
        cx = int(np.median(xs[ys < top + 0.12 * Hh])); s_ = int(k * Hh); return 판(p, c).crop((cx - s_ // 2, top, cx + s_ // 2, top + s_))
    빠 = lambda n, c: Image.open(os.path.join(n, c + ".png")).convert("RGB")
    D4, D5 = os.path.join(F3.OUT, "_바퀴", "눈", "후4"), os.path.join(바퀴D, str(N))
    줄 = [[("FRA 정면 mh_12", Image.open(os.path.join(FRA, "mh_12.jpg"))), ("눈 고침 4", 빠(D4, "정면")), ("얼굴 4", 빠(D5, "정면"))],
          [("FRA 3/4 (mh_13 뒤집음)", Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT)), ("눈 고침 4 3/4", 빠(D4, "반옆")), ("얼굴 4 3/4", 빠(D5, "반옆"))],
          [("전신 영웅 3/4 — 눈 고침 4", 판(T4, "영웅큰")), ("전신 영웅 3/4 — 얼굴 4", 판(T5, "영웅큰"))]]
    hs = [560, 560, 900]; W = 1990
    S = Image.new("RGB", (W, sum(hs) + 3 * 45 + 10), (245, 245, 243)); dr = ImageDraw.Draw(S); y = 45
    for 칸, h in zip(줄, hs):
        x = 10
        for t, im in 칸:
            im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
            if x + im.width > W: im = im.crop((0, 0, W - 10 - x, h))
            S.paste(im, (x, y)); dr.text((x + 6, y - 36), t, font=f_, fill=(30, 30, 30)); x += im.width + 10
        y += h + 45
    p = os.path.join(멋, "얼굴4_전후.jpg"); S.save(p, quality=90); print("시트", p, S.size)

if __name__ == "__main__":
    내보내기()
    if "--빠른" in sys.argv: 빠른렌더(sys.argv[sys.argv.index("--빠른") + 1])
    if "--점수" in sys.argv: 점수()
    if "--렌더" in sys.argv: 렌더(sys.argv[sys.argv.index("--렌더") + 1])
