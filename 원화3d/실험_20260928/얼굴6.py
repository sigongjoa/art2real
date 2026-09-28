# -*- coding: utf-8 -*-
"""오메가몬 PG 얼굴 5c (2026-09-28) — 턱을 사선으로. 「물고기도 아니고 · 턱이 사선이어야지 · 지금은 턱이 돌출」.

    python 얼굴5c.py [--각 40 --턱z 265]  -> 디자인_얼굴5d/*.stl
    python 얼굴5c.py --검사 / --렌더 N      -> 5b 와 같음 · 멋/얼굴5d.jpg
바꾼 것(5b 대비): 턱 가리개 앞면을 수직에서 「각」 뒤로 누운 한 평면(미늘 3 단은 그 위 0.3 계단) · 폭 8.8→7.0 ·
  미늘 두께는 면 법선 방향 · 속심은 3 단 면 뒤 0.3 과 「턱 끝 → 뒤로 올라가는 밑면」에서 잘림(수평 밑면 없음).
(아래 5b 설명은 이력)

얼굴 5 는 import 하지 않는다(모듈 몸통이 쓴 머리 부풀림을 다시 돈다 · 메모리). 가면 만드는 12 줄만 옮기고,
깃 · 목 · 눈 · 뿔 등은 디자인_얼굴5 의 STL 을 그대로 쓴다.
바꾼 것: 미늘 앞면 = 한 평면 y = yc + 기울·|x| + 누움·(z0 − z) → 옆에서 이마→코→턱 끝이 뒤로 기우는 한 줄.
         단차 0.9 → 0.35. 옛 주둥이턱 속심의 앞 점(코끝 · 턱 끝)을 미늘 면 뒤 1.0 으로 물림.
"""
import os, sys, json, shutil, subprocess, time
import numpy as np, manifold3d as M
_t0 = time.time()
def 때(s): print("  [%5.1f s] %s" % (time.time() - _t0, s), flush=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 얼굴3_턱 as T
E, F3, F2, F1 = T.E, T.F3, T.F2, T.F1
from 얼굴3 import 덩이, 메, 틈, 색, 멋, FRA, V홈
from 얼굴3_턱 import 돌, 있으면

D5 = os.path.join(F3.ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴5")
D5c = os.path.join(F3.ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴5c")
안 = sys.argv[sys.argv.index("--안") + 1] if "--안" in sys.argv else "A"   # A: 눈 = 투구와 마스크 사이 틈(검은 속머리) · B: 흰 얼굴에 눈구멍(FRA 식)
OUT = os.path.join(F3.ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴6" + 안); os.makedirs(OUT, exist_ok=True)
원화 = os.path.join(os.path.dirname(F3.ROOT), "트레일", "trail7_part3d", "in", "omega_front_clean.png")

# ════════ 손잡이(mm) ════════
각 = float(sys.argv[sys.argv.index("--각") + 1]) if "--각" in sys.argv else 40.0   # 턱 앞면이 수직에서 뒤로 누운 각
턱z = float(sys.argv[sys.argv.index("--턱z") + 1]) if "--턱z" in sys.argv else 261.5  # 5d: 264 는 정면에서 턱이 짧다 → 261.5(끄덕 +10° 까지) · 5b: 262.1 (T.턱z). 265 는 턱이 없어 보임 · 262.1 은 끄덕 +15° 겹침 · 264 = +20° 까지 0
기울 = float(sys.argv[sys.argv.index("--기울") + 1]) if "--기울" in sys.argv else 0.8   # 5d: 뱃머리꼴 — x 10.5 에서 눈면(y 1.9)과 한 면 (5c: 0.55 = 앞에 붙은 상자)
두께 = 3.5                      # 면에 수직으로
z0 = 273.4                      # 누움 기준 높이(1 단 윗변 = 코 쐐기 바로 아래)
누움 = float(np.tan(np.radians(각)))   # 5b: 0.15 (8.5°)
단차 = 0.3
y1 = -5.2   # 6b: 마스크는 차양 밑으로 물러남(5d: −6.5 = 눈 아래가 가장 앞 → 주둥이)                       # 1 단 가운데 앞면(z0) — 코 쐐기(−6.79)보다 살짝 뒤
#      윗변 반폭 · 윗변 z · 옆 모서리 반폭 · 옆 모서리 z · 가운데 V 끝 z — 5b 보다 좁고(8.8→7.0) 짧게(턱z 까지 비례)
_s = (z0 - 턱z) / (273.4 - 262.1)
def _z(z): return z0 - (273.4 - z) * _s
# 5d: 얼굴 폭 전체 방패꼴(원화 · FRA) — 정면 (x, z) 반쪽 볼록 다각형. 윗변은 가운데 → 바깥 볼(눈 밑)로 올라가 가로 띠가 없다
윗 = 1.8 if 안 == "A" else 0.0   # A: 마스크 윗변이 눈 아래를 덮어 눈이 좁은 틈이 된다
단 = [[(0, 273.4 + 윗), (10.8, 274.4 + 윗), (10.4, _z(272.6)), (0, _z(269.4))],
      [(0, _z(272.0)), (10.4, _z(273.0)), (9.0, _z(270.0)), (0, _z(266.0))],
      [(0, _z(269.0)), (9.0, _z(270.4)), (6.0, _z(267.6)), (0, 턱z)]]
def 면y(x, z, k=0): return y1 + k * 단차 + 기울 * abs(x) + 누움 * max(z0 - z, 0.0)   # z0 위는 수직(코 쐐기 앞으로 안 나감)
_n = np.array([0, 1.0, 누움]) / np.hypot(1, 누움)     # 면 법선(뒤-위)
밑기울 = 0.75                   # 턱 끝에서 뒤로 1 mm 갈 때 위로 0.45 — 목 앞까지 올라가는 밑면
턱끝y = 면y(0, 턱z, 2)
def 앞자르개(d, W=16.0, zt=z0):   # 3 단 면 + d 보다 앞(zt 아래) — V 라 반쪽 둘(볼록)
    h = []
    for sx in (1, -1):
        P = [(sx * x, y, z) for x in (0, W) for z in (zt, 240.0) for y in (-40.0, 면y(x, z, 2) + d)]
        h.append(M.Manifold.hull_points(P))
    return h[0] + h[1]
def 밑자르개(d, yb=8.0):         # 턱 끝(+d 위) 에서 뒤로 올라가는 면 아래, y < yb
    P = [(x, y, z) for x in (-20, 20) for y in (-40.0, yb) for z in (230.0, 턱z + d + 밑기울 * (y - 턱끝y))]
    return M.Manifold.hull_points(P)
날개 = [(8.6, 276.4), (11.6, 277.2), (13.8, 272.5), (13.0, 266.4), (10.6, 268.4), (8.6, 271.0)]
날개점 = [(x, 1.5 + 0.6 * (x - 9), z) for x, z in 날개] + [(x, 14.0, z) for x, z in 날개]
날개덩이 = 덩이(날개점) + 덩이([(-x, y, z) for x, y, z in 날개점])
코 = [(0, -5.8, 275.2), (2.6, -4.4, 274.0)]      # 바퀴 3: 콧등 점도 이마 능선 선에 맞춰 뒤로(얼굴 5: −7.6 · −5.8)

def 미늘(k, pg, 위=()):
    앞 = [(x, 면y(x, z, k), z) for x, z in pg]
    위 = list(위) + [(x + 1.4, 면y(x, z, k) + 4.5, z) for x, z in pg if x > 8]   # 볼 옆으로 감싸는 껍질(앞판이 아니라)
    return 덩이(앞 + [tuple(np.add(p, 두께 * _n)) for p in 앞] + list(위))
미늘들 = [미늘(0, 단[0], 위=코)] + [미늘(k, d) for k, d in enumerate(단) if k]

# 속심: 옛 주둥이턱 — 앞은 3 단 면 뒤 0.3 에서, 밑은 턱 끝에서 뒤로 올라가는 면에서 자른다(수평 밑면 · 상자 모서리 없음)
표 = dict(T.표)
부리 = 덩이(표.pop("부리")).trim_by_plane([0, 0, 1], 274.5).trim_by_plane([0, 1, 0], -6.0)
# 6b: 가장 앞은 눈 위 차양(FRA 옆모습) — 차양 앞변을 앞으로, 눈은 그 밑 깊이
_차양 = {(0, -3.0, 281.0): (0, -6.8, 280.6), (6.0, -2.0, 282.4): (6.0, -4.4, 282.4), (10.6, 0.2, 281.0): (10.6, -1.0, 281.0)}
assert all(p in 표["눈두덩"] for p in _차양); 표["눈두덩"] = [_차양.get(p, p) for p in 표["눈두덩"]]
_자름 = 앞자르개(0.3) + 밑자르개(0.0)
속심 = M.Manifold.batch_boolean([덩이(p) for p in 표.values()] + [부리, 덩이(T.능선)], M.OpType.Add) - _자름
눈안 = 2.5   # 6b: 눈을 가운데로(눈 사이가 넓으면 물개) — 눈 면이 x 따라 뒤로 가므로 y 도 같이
def 안으로(m):
    b = m.bounding_box(); s = np.sign(b[0] + b[3]); return m.translate([-s * 눈안, -눈안 * 5.0 / 11.0, 0])
창L, 창R = 안으로(E.창L), 안으로(E.창R)
미늘합 = M.Manifold.batch_boolean(미늘들, M.OpType.Add) - 밑자르개(0.0)
마스크 = 미늘합 ^ F3.앞반                                   # 6: 마스크는 따로 한 부품(투구 밑으로 들어감)
새겉 = M.Manifold.batch_boolean([속심, 날개덩이], M.OpType.Add) ^ F3.앞반
새속 = M.Manifold.batch_boolean([T.속(표[k]) for k in ("두개", "눈면", "주둥이턱")], M.OpType.Add) - 앞자르개(2.3) - 밑자르개(2.0)
껍질 = (새겉 - 새속) + ((F3.옛["투구앞"] ^ 새속) ^ F3.앞반)
가면 = V홈(껍질 - T.머리막 - F3.꽂는것, (0, -3.9, 285.0), (0, -6.2, 277.2), (0, -1, 0.3), 폭=0.6, 깊=0.5)
가면 = max((가면 - 창L - 창R - 마스크).decompose(), key=lambda p: p.volume())
마스크 = 마스크 - 창L - 창R - T.머리막 - F3.꽂는것
때("가면")

# 몸(목 둘레만) — 얼굴 5 와 같은 부품 · 깃 · 목은 얼굴 5 STL
몸D = os.path.join(F1.DES, "몸통"); 목상자 = M.Manifold.cube([70, 70, 70]).translate([-35, -20, 235.0])
몸 = {n[:-4]: F1.읽기(os.path.join(몸D, n)) ^ 목상자 for n in sorted(os.listdir(몸D)) if n.endswith(".stl")}
몸["돌출가슴앞"] = F1.읽기(os.path.join(F1.DES, "돌출", "돌출03_가슴앞.stl")) ^ 목상자
몸 = {k: v for k, v in 몸.items() if v.volume() > 0.01}
for n in ("목깃옆L", "목깃옆R", "목깃안검정"): 몸[n] = F1.읽기(os.path.join(D5, n + ".stl"))
몸전부 = M.Manifold.batch_boolean(list(몸.values()), M.OpType.Add)
그대로 = ["투구뒤", "눈L", "눈R", "V안테나L", "V안테나R", "뿔"]
머리그대로 = {n: F1.읽기(os.path.join(D5, n + ".stl")) for n in 그대로}


# ════════ 6: 부품 나눔(썸네일 단계 — 끄덕 · 틈 · 속 비움 검사는 고른 안만 나중에) ════════
from 얼굴3 import 눈면y
눈 = {n: 안으로(F1.읽기(os.path.join(D5, n + ".stl"))) for n in ("눈L", "눈R")}
바탕 = {"눈바탕L": 안으로(E.새["눈바탕L_v5"][0]), "눈바탕R": 안으로(E.새["눈바탕R_v5"][0])}
부품 = {}
if 안 == "A":   # 눈 면(흰 얼굴)을 떼어 검은 속머리로 · 1 mm 뒤로 물려 투구와 마스크 사이 틈으로 보이게
    띠영역 = M.Manifold()
    for sx in (1, -1):
        띠영역 += M.Manifold.hull_points([(sx * x, 눈면y(x) + d, z) for x in (0, 10.9) for z in (272.0, 281.5) for d in (-0.4, 2.6)])
    속띠 = (가면 ^ 띠영역).translate([0, 1.0, 0]); 가면 = 가면 - 띠영역
    눈 = {k: v.translate([0, 1.0, 0]) for k, v in 눈.items()}; 바탕 = {k: v.translate([0, 1.0, 0]) for k, v in 바탕.items()}
    부품["속머리띠"] = (속띠, 색["검"])
부품.update({"투구앞": (가면, 색["흰"]), "마스크": (마스크, 색["흰"]), **{k: (v, 색["검"]) for k, v in 바탕.items()}, **{k: (v, 색["초록"]) for k, v in 눈.items()}})
for n in ("투구뒤", "뿔"): 부품[n] = (F1.읽기(os.path.join(D5, n + ".stl")), 색["흰"])
for n in ("V안테나L", "V안테나R"): 부품[n] = (F1.읽기(os.path.join(D5, n + ".stl")), 색["금"])
for n, c in (("목깃옆L", "흰"), ("목깃옆R", "흰"), ("목깃안검정", "검")): 부품[n] = (F1.읽기(os.path.join(D5, n + ".stl")), 색[c])
V = np.asarray(마스크.to_mesh().vert_properties)[:, :3]
print("안 %s · 마스크 x ±%.1f · y %.1f~%.1f · z %.1f~%.1f" % (안, V[:, 0].max(), V[:, 1].min(), V[:, 1].max(), V[:, 2].min(), V[:, 2].max()))
assert V[:, 2].min() < 턱z + 0.8 and 마스크.volume() > 100 and 가면.volume() > 500

컷 = [("정면", 0, 0, 70.0, 280.0), ("옆", 90, 0, 70.0, 280.0), ("반옆", 62, 8, 70.0, 288.0)]
def 그림():
    d = os.path.join(OUT, "_그림"); os.makedirs(d, exist_ok=True); jf, pf = os.path.join(d, "빠른.json"), os.path.join(d, "빠른.py")
    L = []
    for n, (m, c) in 부품.items(): 메(m).export(os.path.join(OUT, n + ".stl")); L.append((os.path.join(OUT, n + ".stl"), c))
    if "--머리만" in sys.argv: L = [l for l in L if "목깃" not in l[0]]
    else: L += [(os.path.join(F1.DES, "몸통", n + ".stl"), 색["흰"]) for n in ("가슴앞", "목깃")]
    json.dump(dict(부품=L, out=d.replace("\\", "/"), 컷=컷), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    open(pf, "w", encoding="utf-8").write(F3.빠른.replace("line_thickness = 1.6", "line_thickness = 1.0"))
    r = subprocess.run([F1.BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    때("블렌더")
def 시트():
    from PIL import Image, ImageDraw, ImageFont
    R = os.path.dirname(OUT); h = 560
    def 빠(a, c):
        im = Image.open(os.path.join(R, "디자인_얼굴6" + a, "_그림", c + ".png")).convert("RGB"); w, H = im.size
        return im.crop((int(w * .2), int(H * .3), int(w * .8), int(H * .9)))
    참 = [Image.open(os.path.join(멋, "원화_얼굴_확대.png")).convert("RGB").crop((230, 60, 700, 660)),
          Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT), Image.open(os.path.join(FRA, "mh_12.jpg"))]
    줄 = [[("원화", 참[0]), ("A 정면 — 눈 = 틈", 빠("A", "정면")), ("B 정면 — 눈구멍", 빠("B", "정면"))],
          [("FRA 옆(뒤집음)", 참[1]), ("A 옆", 빠("A", "옆")), ("B 옆", 빠("B", "옆"))],
          [("FRA 정면", 참[2]), ("A 3/4", 빠("A", "반옆")), ("B 3/4", 빠("B", "반옆"))]]
    f_ = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26); W = 1700
    S = Image.new("RGB", (W, 3 * (h + 45) + 10), (245, 245, 243)); dr = ImageDraw.Draw(S); y = 45
    for 칸 in 줄:
        x = 10
        for t, im in 칸:
            im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
            if x + im.width > W: im = im.crop((0, 0, W - 10 - x, h))
            S.paste(im, (x, y)); dr.text((x + 6, y - 36), t, font=f_, fill=(30, 30, 30)); x += im.width + 10
        y += h + 45
    p = os.path.join(멋, "얼굴6_AB.jpg"); S.save(p, quality=90); print("시트", p, S.size)

if __name__ == "__main__":
    그림()
    if "--시트" in sys.argv: 시트()


