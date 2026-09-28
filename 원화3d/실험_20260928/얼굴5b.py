# -*- coding: utf-8 -*-
"""오메가몬 PG 얼굴 5b (2026-09-28) — 얼굴 5 의 턱 가리개만 뒤로. 「턱 구조가 너무 돌출됐다」.

    python 얼굴5b.py            -> 디자인_얼굴5b/*.stl (가면 · 눈바탕만 새로, 나머지는 얼굴 5 STL 복사)
    python 얼굴5b.py --검사     -> + 이웃 겹침 · 끄덕 −25~+20° 5° 간격(몸통 부품 전부 + 깃 + 목) → 부품.json
    python 얼굴5b.py --렌더 N   -> 정면 · 옆 · 3/4 빠른 렌더(얼굴 5 와 같이) + 멋/얼굴5b.jpg

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
OUT = os.path.join(F3.ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴5b"); os.makedirs(OUT, exist_ok=True)
원화 = os.path.join(os.path.dirname(F3.ROOT), "트레일", "trail7_part3d", "in", "omega_front_clean.png")

# ════════ 손잡이(mm) ════════
턱z = T.턱z
기울 = 0.55                     # 옆으로 가며 뒤로(얼굴 5 그대로)
두께 = 4.5
z0 = 273.4                      # 누움 기준 높이(1 단 윗변)
누움 = 0.15                     # 아래로 1 mm 갈 때 뒤로 0.15 mm (옆모습 얼굴선이 뒤로 기움)
단차 = 0.35                     # 얼굴 5: 0.9
y1 = -6.5                       # 바퀴 3: −7.2 는 옆에서 아직 이마 능선(−6.4)보다 0.9 앞 → 1 단 가운데 앞면(z0) — 코 쐐기 끝(부리 z 273.2 에서 y −7.74) · 콧등 점(−7.6) 보다 뒤. 얼굴 5: −9.6
#      윗변 반폭 · 윗변 z · 옆 모서리 반폭 · 옆 모서리 z · 가운데 V 끝 z (얼굴 5 그대로)
단 = [(8.8, 273.4, 8.6, 272.4, 270.4), (8.4, 272.0, 8.0, 269.0, 266.4), (7.6, 269.0, 6.2, 265.8, 턱z)]
def 면y(x, z, k=0): return y1 + k * 단차 + 기울 * abs(x) + 누움 * (z0 - z)
날개 = [(8.6, 276.4), (11.6, 277.2), (13.8, 272.5), (13.0, 266.4), (10.6, 268.4), (8.6, 271.0)]
날개점 = [(x, 1.5 + 0.6 * (x - 9), z) for x, z in 날개] + [(x, 14.0, z) for x, z in 날개]
날개덩이 = 덩이(날개점) + 덩이([(-x, y, z) for x, y, z in 날개점])
코 = [(0, -6.9, 275.2), (2.6, -5.4, 274.0)]      # 바퀴 3: 콧등 점도 이마 능선 선에 맞춰 뒤로(얼굴 5: −7.6 · −5.8)

def 미늘(k, wt, zt, ws, zs, zc, 위=()):
    앞 = [(x, 면y(x, z, k), z) for x, z in ((0, zt), (wt, zt), (ws, zs), (0, zc))]
    return 덩이(앞 + [(x, y + 두께, z) for x, y, z in 앞] + list(위))
미늘들 = [미늘(0, *단[0], 위=코)] + [미늘(k, *d) for k, d in enumerate(단) if k]

# 속심: 옛 주둥이턱의 코끝(0, −9.4, 270.4) · 턱 끝을 미늘 면 뒤 1.0 으로
표 = dict(T.표)
#   바퀴 2: 앞 점 전부(V 아래 모서리 · 코 옆 꺾임이 3 단 옆면을 뚫었다)를 가장 깊은 3 단 면보다 1.0 뒤로
_턱 = [(0, T.턱y - 0.8 + 1.2, 턱z + 0.6) if p == (0, T.턱y, 턱z) else p for p in T.표["주둥이턱"]]
표["주둥이턱"] = [(x, max(y, 면y(x, z, 2) + 1.0), z) if y < 5 else (x, y, z) for x, y, z in _턱]
#   바퀴 2: 부리를 273.2 에서 자르면 1 단 윗변 위에 0.5 선반(정면 점)이 남는다 → 274.5 에서 자르고 콧등은 코 점 → 1 단으로
부리 = 덩이(표.pop("부리")).trim_by_plane([0, 0, 1], 274.5)
새겉 = M.Manifold.batch_boolean([덩이(p) for p in 표.values()] + [부리, 덩이(T.능선), 날개덩이] + 미늘들, M.OpType.Add) ^ F3.앞반
새속 = M.Manifold.batch_boolean([T.속(표[k]) for k in ("두개", "눈면", "주둥이턱")], M.OpType.Add)
껍질 = (새겉 - 새속) + ((F3.옛["투구앞"] ^ 새속) ^ F3.앞반)
가면 = V홈(껍질 - T.머리막 - F3.꽂는것, (0, -3.9, 285.0), (0, -6.2, 277.2), (0, -1, 0.3), 폭=0.6, 깊=0.5)
가면 = max((가면 - E.창L - E.창R).decompose(), key=lambda p: p.volume())
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

# 앞 끄덕: +20° 에서 가면이 몸과 겹치나(깎기 전)
def 끄덕겹(m, d): return (돌(m, d) ^ 몸전부).volume()
겹20 = {d: round(끄덕겹(가면, d), 3) for d in (10, 15, 20)}; print("깎기 전 가면 끄덕 겹침", 겹20, flush=True)
끄덕앞 = 20.0 if 겹20[20] < 0.005 else 10.0
if 끄덕앞 == 10.0:   # 얼굴 5 와 같이 가슴앞을 거꾸로 돌려 +10° 까지 깎는다
    _가슴 = F2.부풀(F1.읽기(os.path.join(몸D, "가슴앞.stl")) ^ 목상자, 틈 + 0.15)
    _거꾸로 = M.Manifold.batch_boolean([돌(_가슴, -d) for d in np.arange(10, 끄덕앞 + 0.1, 1.25)], M.OpType.Add)
    if (가면 ^ _거꾸로).volume() > 0.001: 가면 = max((가면 - _거꾸로).decompose(), key=lambda p: p.volume())
가면부풀 = F2.부풀(가면, 틈)
바탕L, 바탕R = [max((e - 가면부풀).decompose(), key=lambda p: p.volume()) for e in (E.새["눈바탕L_v5"][0], E.새["눈바탕R_v5"][0])]
머리 = dict(가면투구=가면, 눈바탕L=바탕L, 눈바탕R=바탕R, **머리그대로)
때("끄덕앞 %.0f°" % 끄덕앞)

def 내보내기():
    for n in ("가면투구", "눈바탕L", "눈바탕R"):
        t = 메(머리[n]); assert t.is_watertight and len(머리[n].decompose()) == 1, n; t.export(os.path.join(OUT, n + ".stl"))
    for n in 그대로 + ["목깃옆L", "목깃옆R", "목깃안검정"]: shutil.copy(os.path.join(D5, n + ".stl"), OUT)
    V = np.asarray(가면.to_mesh().vert_properties)[:, :3]
    ys = [T.앞면y(가면, 1.5, z) for z in (272.0, 268.0, 264.5)]
    def 앞끝(z1, z2): return float((가면 ^ M.Manifold.cube([30, 60, z2 - z1]).translate([-15, -30, z1])).bounding_box()[1])
    코y = 앞끝(274.0, 277.0)
    print("앞면 y (x 1.5 · 1 · 2 · 3 단)", np.round(ys, 2), "· 코 쐐기 가장 앞(z 274~277) %.2f · 턱 끝 z %.2f" % (코y, V[:, 2].min()))
    assert 0.25 < ys[1] - ys[0] < 1.2 and 0.25 < ys[2] - ys[1] < 1.2, ys       # 계단이 남고(아래로 갈수록 뒤) 너무 깊지 않다
    가운데1 = 앞끝(262.0, 273.9); print("턱 가리개 가장 앞(z < 273.9) %.2f" % 가운데1)
    assert 가운데1 > 코y, "1 단이 코 쐐기보다 앞"
    assert V[:, 2].min() < 턱z + 0.8, "턱 끝 잘림"
    if "--검사" not in sys.argv: return
    이웃 = {k: v for k, v in F1.이웃읽기().items() if k not in F3.대체}; 이웃.update({"몸_" + k: v for k, v in 몸.items()})
    겹 = {}
    for a in ("가면투구", "눈바탕L", "눈바탕R"):
        for b, m in list(이웃.items()) + [(k, v) for k, v in 머리.items() if k != a]:
            v = (머리[a] ^ m).volume()
            if v > 0.005: 겹["%s∩%s" % (a, b)] = round(v, 3)
    머리합 = M.Manifold.batch_boolean(list(머리.values()), M.OpType.Add)
    끄덕 = {d: round((돌(머리합, d) ^ 몸전부).volume(), 3) for d in range(-25, 21, 5)}
    끄덕틈 = {d: round(float(돌(머리합, d).min_gap(몸전부, 3.0)), 2) for d in (-25, 0, 10, 15, 20)}
    결과 = dict(설명="얼굴 5b — 턱 가리개 뒤로(단차 0.35 · 누움 0.15 · 1 단 y −6.5 · 콧등 −6.9) (09-28)", 끄덕범위도=[-25, 끄덕앞],
              앞면y_1_2_3단=ys, 코쐐기y=코y, 얼굴5_앞면y=[-8.76, -7.86, -6.96], 겹침=겹, 끄덕_겹침mm3=끄덕, 끄덕_최소틈mm=끄덕틈, 깎기전_가면끄덕=겹20)
    json.dump(결과, open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps(결과, ensure_ascii=False, default=float))

컷 = [("정면", 0, 0, 70.0, 280.0), ("옆", 90, 0, 70.0, 280.0), ("반옆", 62, 8, 70.0, 288.0)]
def 빠른그림(OUTd, d):
    os.makedirs(d, exist_ok=True); jf, pf = os.path.join(d, "빠른.json"), os.path.join(d, "빠른.py")
    P = json.load(open(os.path.join(D5, "부품.json"), encoding="utf-8"))["부품"]
    부품 = [(os.path.join(OUTd, n + ".stl"), v["색"]) for n, v in P.items()] + [(os.path.join(F1.DES, "몸통", n + ".stl"), 색["흰"]) for n in ("가슴앞", "목깃")]
    json.dump(dict(부품=부품, out=d.replace("\\", "/"), 컷=컷), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    open(pf, "w", encoding="utf-8").write(F3.빠른.replace("line_thickness = 1.6", "line_thickness = 1.0"))
    r = subprocess.run([F1.BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
def 렌더(바퀴):
    from PIL import Image, ImageDraw, ImageFont
    a, b = os.path.join(OUT, "_바퀴", "5"), os.path.join(OUT, "_바퀴", "5b_" + 바퀴)
    if not os.path.exists(os.path.join(a, "옆.png")): 빠른그림(D5, a)
    빠른그림(OUT, b); 때("블렌더")
    mmpx = 0.39; cy = 181.7 - (280.0 - 턱z) / mmpx; h = 70.0 / mmpx / 2
    원 = Image.open(원화).convert("RGB").crop((int(536 - h), int(cy - h), int(536 + h), int(cy + h)))
    빠 = lambda d, c: Image.open(os.path.join(d, c + ".png")).convert("RGB")
    fra = Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT)
    줄 = [[("원화 확대", 원), ("얼굴 5 정면", 빠(a, "정면")), ("얼굴 5b 정면", 빠(b, "정면"))],
          [("얼굴 5 옆(순수 측면 · 왼쪽이 앞)", 빠(a, "옆")), ("얼굴 5b 옆", 빠(b, "옆"))],
          [("FRA mh_13 (뒤집음)", fra), ("얼굴 5 3/4", 빠(a, "반옆")), ("얼굴 5b 3/4", 빠(b, "반옆"))]]
    f_ = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26); W, h = 1990, 620
    S = Image.new("RGB", (W, 3 * (h + 45) + 10), (245, 245, 243)); dr = ImageDraw.Draw(S); y = 45
    for 칸 in 줄:
        x = 10
        for t, im in 칸:
            im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
            if x + im.width > W: im = im.crop((0, 0, W - 10 - x, h))
            S.paste(im, (x, y)); dr.text((x + 6, y - 36), t, font=f_, fill=(30, 30, 30)); x += im.width + 10
        y += h + 45
    p = os.path.join(멋, "얼굴5b.jpg"); S.save(p, quality=90); print("시트", p, S.size)

if __name__ == "__main__":
    내보내기()
    if "--렌더" in sys.argv: 렌더(sys.argv[sys.argv.index("--렌더") + 1])
