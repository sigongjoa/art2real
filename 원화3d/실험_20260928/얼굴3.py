# -*- coding: utf-8 -*-
"""오메가몬 PG 얼굴 3 차 (2026-09-28) — 각진 면(하드서피스). 꼭짓점 표 → 볼록 덩이(면 꺾임) 합 → 껍질.

    python 얼굴3.py              -> out/출력/오메가몬_PG/디자인_얼굴3/*.stl · 부품.json(검사)
    python 얼굴3.py --빠른 N     -> 위 + 머리만 빠른 렌더(mh_12 와 같은 틀) → _바퀴/바퀴N.jpg (사진과 나란히)
    python 얼굴3.py --렌더       -> 위 + 전신 렌더(옛 · 2 차는 재사용) → 멋/얼굴3_전후.jpg

판정은 실루엣 IoU 가 아니라 안쪽 선(능선 · 눈두덩 · 주둥이 쐐기 · 볼 날개 경계)의 자리.
로프트 · 구 · 스무딩 없음. 덩이 하나 = 꼭짓점 표의 볼록 껍질(면은 전부 평면), 덩이 사이 단차가 꺾임선.
ponytail: 닫힌 껍질을 면 목록으로 손수 잇지 않고 볼록 덩이 합으로 닫는다(늘 닫힘). 오목 곡면이 필요해지면 면 목록으로.
좌표 mm · x 옆 · y 작은 쪽이 앞 · z 높이. mh_12 1 px = 0.155 mm(돔 꼭대기 py 222 = z 293.3 · 가운데 px 229).
"""
import os, sys, json, subprocess
import numpy as np, manifold3d as M
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 얼굴2 as F2
import 얼굴 as F1
from 얼굴 import 볼록, 밀기, 메, 얇은곳, ROOT, DES, 멋, 틈, V홈

OUT = os.path.join(ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴3"); os.makedirs(OUT, exist_ok=True)
바퀴D = os.path.join(OUT, "_바퀴"); os.makedirs(바퀴D, exist_ok=True)
FRA = os.path.join(ROOT, "out", "키트", "FRA_오메가몬", "추가")
옛, 벽 = F1.옛, 1.6

# ════════ 꼭짓점 표(오른쪽 반 · x ≥ 0) — 덩이마다. 거울은 자동 ════════
표 = {
 # 두개(이마): 능선 양옆 기운 평면 둘 + 관자놀이 꺾임
 "두개": [(0, -1.2, 283.0), (0, 1.5, 288.5), (0, 6.5, 293.3), (3.5, 7.5, 292.6),
          (6.2, -1.6, 281.6), (5.6, 2.0, 289.0), (9.6, 1.6, 282.0), (8.8, 5.5, 287.6),
          (11.2, 6.0, 282.0), (10.2, 9.0, 286.0), (11.2, 6.0, 279.5)],
 # 눈두덩: 앞으로 튀어나온 두꺼운 테 · 아랫날이 안쪽 낮고 바깥 높음
 "눈두덩": [(0, -6.2, 276.4), (1.4, -5.9, 276.4), (0, -3.0, 281.0), (6.0, -2.0, 282.4),
            (10.6, 0.2, 281.0), (11.4, 1.8, 281.2), (10.6, 1.2, 283.2),
            (0, 4.0, 281.0), (11.2, 6.0, 282.4), (0, 4.0, 277.0)],
 # 눈 면: 눈두덩 밑 깊이 파인 면(눈구멍이 여기 뚫림)
 "눈면": [(0, -2.6, 280.0), (0, -2.6, 270.0), (11.0, 2.4, 281.0), (11.0, 2.4, 274.4)],
 # 주둥이 쐐기(부리): 가운데 능선 끝이 가장 앞
 "부리": [(0, -5.6, 276.8), (0, -9.4, 270.4), (0, -5.6, 264.6), (1.0, -4.6, 276.4),
          (5.4, -3.2, 269.0), (2.4, -3.8, 265.4), (0, 4.0, 277.0), (5.4, 4.0, 269.0), (0, 4.0, 265.0)],
 # 턱(아래 얼굴): 뾰족한 V
 "턱": [(0, -3.6, 263.0), (8.6, -0.8, 273.6), (8.8, -0.4, 270.6), (4.6, -2.4, 266.8),
        (0, -3.0, 273.6)],
}
뒤 = {  # 덩이 뒤끝(y 15 이음면) (x, z)
 "눈면": [(11.0, 281.0), (11.0, 274.4)],
 "턱": [(8.8, 273.6), (8.8, 270.6), (4.6, 266.8), (0, 264.0)],
}
# 볼 날개: 정면 (x, z) · 앞면 y = 1.5 + 0.6 (x − 9) · 뒤 y 14
날개 = [(8.6, 274.6), (11.4, 275.4), (17.6, 267.4), (11.6, 265.0), (8.4, 268.4)]
# 눈구멍(검은 육각 · 안쪽 낮고 바깥 높음) · 초록 눈(작은 육각)
눈반 = [(3.4, 274.6), (4.6, 276.8), (9.4, 279.3), (10.2, 278.5), (9.0, 276.3), (4.6, 273.8)]
송곳니 = dict(x=6.1, 위=272.0, 아래=267.4)      # 부리 옆 세로 홈
# 뿔(넓은 날): 단면 (x, y) — 밑동 z 285.5 가 이마 능선 윗끝과 같다
뿔단 = [(285.5, [(0, -3.8), (3.4, -0.6), (3.4, 5.0), (0, 9.0)]),
        (299.0, [(0, 0.6), (2.0, 2.6), (2.0, 6.6), (0, 9.4)]),
        (324.0, [(0, 11.4), (0.4, 11.8), (0, 12.4)])]
능선 = [(0, -3.8, 285.5), (3.4, -0.6, 285.5), (3.4, 3.0, 285.5), (0, -6.4, 276.6), (0.7, -5.9, 276.6), (0.7, 0.0, 276.6)]

def 눈면y(x): return -2.6 + 5.0 * abs(x) / 11.0
def 대칭(P): return list(P) + [(-x, y, z) for x, y, z in P if x > 0]
_팔 = np.array([(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)], float)
def 덩이(P, 모=0.3):
    """볼록 덩이 + 모서리 0.3 모따기(안으로 0.3 밀고 팔면체 0.3 을 더함 → 모서리만 깎임)."""
    P = np.asarray(대칭(P), float)
    if not 모: return 볼록(P)
    Q = 밀기(P, -모); return 볼록(np.vstack([Q + 모 * d for d in _팔]))
def 속(P):
    try: return 볼록(밀기(np.asarray(대칭(P), float), -벽))
    except Exception: return M.Manifold()          # 얇은 덩이는 속을 채운다

def 아치(z): return float(np.interp(z, [279, 284, 288, 291, 293.3], [11.2, 11.0, 9.6, 7.0, 3.0]))   # 둥근 돔 윤곽(꺾인 다각)
이음 = [(float(np.clip(p[0], -아치(p[2]), 아치(p[2]))), 15.0, p[2]) for p in F2.이음 if p[2] >= 279.0]
점 = {k: list(v) + [(x, 15.0, z) for x, z in 뒤.get(k, [])] for k, v in 표.items()}
점["두개"] += 이음
날개점 = [(x, 1.5 + 0.6 * (x - 9), z) for x, z in 날개] + [(x, 14.0, z) for x, z in 날개]
앞반 = F2.앞반
겉덩이 = [덩이(p) for p in 점.values()] + [덩이(능선)]
날개덩이 = 덩이(날개점) + 덩이([(-x, y, z) for x, y, z in 날개점])
새겉 = (M.Manifold.batch_boolean(겉덩이 + [날개덩이], M.OpType.Add)) ^ 앞반
새속 = M.Manifold.batch_boolean([속(점[k]) for k in ("두개", "눈면", "턱")], M.OpType.Add)

# 뿔: 넓은 날 + 옛 뿔 뿌리(소켓 그대로)
def 단(z, P): return [(x, y, z) for x, y in P] + [(-x, y, z) for x, y in P if x > 0]
뿔 = M.Manifold.batch_boolean([볼록(단(*a) + 단(*b)) for a, b in zip(뿔단[:-1], 뿔단[1:])], M.OpType.Add) \
     + (F1.뿔 ^ F1.상자((-10, -10, 270), (10, 20, 286.5)))
def 눕힘(m, 각=40.0):
    from scipy.spatial.transform import Rotation as Rot
    V = np.asarray(m.to_mesh().vert_properties)[:, :3]; 뿌리 = V[V[:, 2] < V[:, 2].min() + 1.5].mean(0); 끝 = V[V[:, 2].argmax()]
    d = 끝 - 뿌리; 지금 = np.degrees(np.arctan2(d[2], abs(d[0]))); R = Rot.from_euler("y", (지금 - 각) * np.sign(d[0]), degrees=True).as_matrix()
    return m.transform(np.hstack([R, (뿌리 - R @ 뿌리).reshape(3, 1)]))
안L, 안R = 눕힘(옛["V안테나L"]), 눕힘(옛["V안테나R"])
꽂는것 = F2.부풀(뿔 + 안L + 안R, 틈)

# 눈: 검은 바탕판(뒤에서 끼움 · 테) + 초록 눈(바탕 구멍에 꽂음)
def 눈조각(s):
    from shapely.geometry import Polygon
    P = [(s * x, z) for x, z in 눈반]; pg = Polygon(P)
    def 링(d): return list(pg.buffer(d, join_style=2).exterior.coords)[:-1]
    def 기둥(R, a, b): return 볼록([(x, 눈면y(x) + a, z) for x, z in R] + [(x, 눈면y(x) + b, z) for x, z in R])
    창 = 기둥(P, -1.0, 벽 + 0.6)
    바탕 = 기둥(링(-틈), 0.9, 벽 + 0.5) + 기둥(링(0.9), 벽 + 틈, 벽 + 틈 + 0.9)
    초록 = 기둥(링(-0.75), 0.5, 벽 + 틈 + 0.9)
    return 창, 바탕 - F2.부풀(초록, 틈), 초록
창L, 바탕L, 눈L = 눈조각(-1); 창R, 바탕R, 눈R = 눈조각(1)

껍질 = (새겉 - 새속) + ((옛["투구앞"] ^ 새속) ^ 앞반)
가면 = 껍질 - 창L - 창R - F2.머리막 - 꽂는것
가면 = V홈(가면, (0, -3.9, 285.0), (0, -6.2, 277.2), (0, -1, 0.3), 폭=0.6, 깊=0.5)             # 능선 가운데 세로 패널선
for s in (1, -1):                                                                          # 송곳니 세로 홈
    가면 = 가면 - 볼록([(s * x, y, z) for x in (송곳니["x"] - 0.45, 송곳니["x"] + 0.45) for y in (-6, -2.0)
                     for z in (송곳니["위"], 송곳니["아래"] + 1.5)] + [(s * 송곳니["x"], y, 송곳니["아래"]) for y in (-6, -2.2)])
가면 = max(가면.decompose(), key=lambda p: p.volume())
바탕L, 바탕R = [max((e - F2.부풀(가면, 틈)).decompose(), key=lambda p: p.volume()) for e in (바탕L, 바탕R)]
눈L, 눈R = [max((e - F2.부풀(가면, 틈)).decompose(), key=lambda p: p.volume()) for e in (눈L, 눈R)]
윤곽기둥 = 새겉.rotate([-90, 0, 0]).project().extrude(60.0).rotate([90, 0, 0]).translate([0, 40.0, 0])
투구뒤 = (옛["투구뒤"] ^ 윤곽기둥) - F2.부풀(안L + 안R, 틈)

색 = dict(흰=[0.93, 0.93, 0.95], 검=[0.04, 0.04, 0.05], 초록=[0.15, 0.72, 0.35], 금=[0.85, 0.62, 0.12])
새 = {"가면투구": (가면, 색["흰"], "각진 면 가면 한 판 · 두개 + 눈두덩 + 눈면 + 부리 + 턱 + 볼 날개 + 이마 능선 · 벽 1.6 · 모 0.3"),
      "투구뒤": (투구뒤, 색["흰"], "옛 투구뒤 ∩ 새 정면 윤곽"),
      "눈바탕L": (바탕L, 색["검"], "검은 눈구멍 바탕 — 뒤에서 끼움 · 틈 0.12"), "눈바탕R": (바탕R, 색["검"], "검은 눈구멍 바탕"),
      "눈L": (눈L, 색["초록"], "초록 눈 — 바탕 구멍에 꽂음 · 틈 0.12"), "눈R": (눈R, 색["초록"], "초록 눈"),
      "V안테나L": (안L, 색["금"], "금 뿔 — 뿌리 기준 32° 로 눕힘"), "V안테나R": (안R, 색["금"], "금 뿔"),
      "뿔": (뿔, 색["흰"], "넓은 날 뿔 · 밑동 폭 6.8(머리 폭 1/4) · 이마 능선과 이어짐 · 뿌리는 옛 소켓")}
대체 = ["투구앞", "투구뒤", "얼굴", "뿔", "V안테나L", "V안테나R"]

def 검사():
    이웃 = F1.이웃읽기(); 이웃.pop("투구뒤")
    검 = {n: dict(닫힘=bool(메(m).is_watertight), 조각=len(m.decompose()), 부피mm3=round(m.volume(), 1), 얇은곳mm3=얇은곳(m),
                 크기mm=np.round(메(m).extents, 1).tolist()) for n, (m, _, _) in 새.items()}
    겹 = {}; ns = list(새)
    for i, a in enumerate(ns):
        for b in ns[i + 1:] + list(이웃):
            v = (새[a][0] ^ (새[b][0] if b in 새 else 이웃[b])).volume()
            if v > 0.005: 겹["%s∩%s" % (a, b)] = round(v, 3)
    return 검, 겹
def 내보내기():
    for n, (m, _, _) in 새.items(): assert 메(m).is_watertight and len(m.decompose()) == 1, n + " 안 닫힘/조각"
    if "--검사" not in sys.argv:          # 바퀴 돌 때는 STL 만(검사는 분 단위)
        for n, (m, _, _) in 새.items(): 메(m).export(os.path.join(OUT, n + ".stl"))
        for n, m in (("V안테나L", 안L), ("V안테나R", 안R)): 메(m).export(os.path.join(바퀴D, n + ".stl"))
        return
    검, 겹 = 검사()
    for n, (m, _, _) in 새.items(): 메(m).export(os.path.join(OUT, n + ".stl"))
    for n, m in (("V안테나L", 안L), ("V안테나R", 안R)): 메(m).export(os.path.join(바퀴D, n + ".stl"))
    json.dump(dict(설명="얼굴 3 차(09-28) 각진 면", 대체=대체, 꼭짓점표=표, 겹침=겹,
                   부품={n: dict(파일=n + ".stl", 색=c, 비고=b, **검[n]) for n, (m, c, b) in 새.items()}),
              open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps(dict(검사=검, 겹침=겹), ensure_ascii=False, default=float))
    assert all(v["닫힘"] for v in 검.values()), "안 닫힌 부품"

# ════════ 빠른 렌더: 머리만 · 정사영 · mh_12 와 같은 틀(가로 70 mm · 가운데 z 292.9) ════════
빠른 = r'''
import bpy, sys, json, math
from mathutils import Vector
a = json.loads(open(sys.argv[-1], encoding="utf-8").read())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for f, c in a["부품"]:
    bpy.ops.import_mesh.stl(filepath=f); o = bpy.context.selected_objects[0]
    m = bpy.data.materials.new("m"); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Roughness"].default_value = 0.45
    o.data.materials.append(m)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.55, 0.57, 1)
def 빛(loc, e):
    d = bpy.data.lights.new("s", "SUN"); d.energy = e; d.angle = 0.3; o = bpy.data.objects.new("s", d); sc.collection.objects.link(o)
    o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
빛((-300, -400, 500), 3.5); 빛((400, -300, 100), 1.0)
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.clip_end = 5000
sc.render.engine = "BLENDER_EEVEE"; sc.render.resolution_x = 896; sc.render.resolution_y = 900
sc.render.use_freestyle = True; sc.render.line_thickness = 1.6
fs = sc.view_layers[0].freestyle_settings; fs.crease_angle = math.radians(150)
for l in list(fs.linesets): fs.linesets.remove(l)
l = fs.linesets.new("l"); l.linestyle = bpy.data.linestyles.new("ls"); l.select_silhouette = True; l.select_border = True; l.select_crease = True
for 이름, az, el, 폭, cz in a["컷"]:
    cam.data.ortho_scale = 폭 * 900 / 896
    t = Vector((0, 6, cz)); r = 600
    p = t + Vector((r * math.sin(math.radians(az)) * math.cos(math.radians(el)), -r * math.cos(math.radians(az)) * math.cos(math.radians(el)), r * math.sin(math.radians(el))))
    cam.location = p; cam.rotation_euler = (t - p).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = a["out"] + "/" + 이름 + ".png"; bpy.ops.render.render(write_still=True)
'''
def 빠른렌더(N):
    from PIL import Image, ImageDraw, ImageFont
    parts = [(os.path.join(OUT, n + ".stl"), c) for n, (m, c, _) in 새.items()] 
    jf = os.path.join(바퀴D, "빠른.json"); pf = os.path.join(바퀴D, "빠른.py")
    json.dump(dict(부품=parts, out=바퀴D.replace("\\", "/"), 컷=[("정면", 0, 0, 70.0, 292.9), ("반옆", 62, 8, 70.0, 288.0)]), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    open(pf, "w", encoding="utf-8").write(빠른)
    r = subprocess.run([F1.BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    f = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
    칸 = [("FRA mh_12", Image.open(os.path.join(FRA, "mh_12.jpg")).resize((597, 600))), ("3차 정면 (바퀴 %s)" % N, Image.open(os.path.join(바퀴D, "정면.png")).convert("RGB").resize((597, 600))),
          ("FRA mh_13", Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT).resize((714, 600))), ("3차 반옆", Image.open(os.path.join(바퀴D, "반옆.png")).convert("RGB").resize((597, 600)))]
    S = Image.new("RGB", (sum(i.width for _, i in 칸) + 50, 650), "white"); d = ImageDraw.Draw(S); x = 10
    for t, im in 칸:
        S.paste(im, (x, 45)); d.text((x + 4, 6), t, font=f, fill="black")
        if "정면" in t or "mh_12" in t:      # 같은 자리 눈금(눈 · 코끝 · 턱)
            for py in (318, 345, 417): d.line([(x, 45 + py * 600 / 450), (x + 597, 45 + py * 600 / 450)], fill=(255, 0, 0), width=1)
        x += im.width + 10
    S.save(os.path.join(바퀴D, "바퀴%s.jpg" % N), quality=88); print(os.path.join(바퀴D, "바퀴%s.jpg" % N))

# ════════ 전신 렌더 + 시트 ════════
TMP = os.path.join(OUT, "_렌더"); TMP1 = F2.TMP1; TMP2 = F2.TMP
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
    def 머리상자(c, 여유=0.16, p=os.path.join(TMP1, "전")):
        a = np.asarray(Image.open(os.path.join(p, "A_%s.png" % c)).split()[-1]) > 20
        ys, xs = np.nonzero(a); top = ys.min(); Hh = ys.max() - top
        cx = int(np.median(xs[ys < top + 0.12 * Hh])); s = int(여유 * Hh); return (cx - s // 2, top, cx + s // 2, top + s)
    원 = Image.open(os.path.join(멋, "디테일비교.jpg")).crop((335, 54, 709, 486))
    b1, b2 = 머리상자("얼굴정면"), 머리상자("영웅큰"); c1, c2 = 머리상자("얼굴정면", 0.2, TMP), 머리상자("영웅큰", 0.2, TMP)   # 3 차는 뿔이 길어 제 꼭대기 기준 · 틀 1.25 배
    줄1 = [("FRA 정면", Image.open(os.path.join(FRA, "mh_12.jpg"))), ("3차 정면", 판(TMP, "얼굴정면").crop(c1)),
           ("2차 정면", 판(TMP2, "얼굴정면").crop(b1)), ("옛 정면", 판(os.path.join(TMP1, "전"), "얼굴정면").crop(b1))]
    줄2 = [("FRA 3/4 (mh_13 좌우 뒤집음)", Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT)), ("3차 3/4", 판(TMP, "영웅큰").crop(c2)),
           ("3차 반옆(빠른 렌더)", Image.open(os.path.join(바퀴D, "반옆.png")).convert("RGB")), ("원화", 원)]
    줄3 = [("전신 옛", 판(os.path.join(TMP1, "전"), "영웅큰")), ("전신 3차", 판(TMP, "영웅큰"))]
    def rs(im, hh): return im.resize((int(im.width * hh / im.height), hh), Image.LANCZOS)
    h, h2 = 560, 1000
    S = Image.new("RGB", (2400, 2 * (h + 45) + h2 + 60), (245, 245, 243)); d = ImageDraw.Draw(S)
    for r, (칸, hh) in enumerate(((줄1, h), (줄2, h), (줄3, h2))):
        x = 10; y = 45 + r * (h + 45)
        for t, im in 칸: im = rs(im, hh); S.paste(im, (x, y)); d.text((x + 6, y - 38), t, font=f, fill=(30, 30, 30)); x += im.width + 10
    S.save(os.path.join(멋, "얼굴3_전후.jpg"), quality=90); print("시트", os.path.join(멋, "얼굴3_전후.jpg"), S.size)

if __name__ == "__main__":
    내보내기()
    if "--빠른" in sys.argv: 빠른렌더(sys.argv[sys.argv.index("--빠른") + 1])
    if "--렌더" in sys.argv: 렌더()
    if "--시트만" in sys.argv: 시트()
