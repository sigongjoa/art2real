# -*- coding: utf-8 -*-
"""오메가몬 PG 얼굴 5 (2026-09-28) — 이빨 없음. 원화대로 닫힌 턱 가리개(V 미늘 3 단) + 높이 선 흰 깃 + 검은 목.

    python 얼굴5.py --빠른 N   -> 디자인_얼굴5/*.stl + _바퀴/N/{정면,반옆}.png + _바퀴/바퀴N.jpg (원화 확대와 같은 틀)
    python 얼굴5.py --검사     -> 닫힘 · 이웃 겹침 · 끼움 틈 · 목 끄덕임(몸통 부품 전부) → 부품.json · 대체.json
    python 얼굴5.py --렌더 N   -> 전신 렌더 + 멋/얼굴5.jpg

바탕 = 얼굴3_턱(눈 고침 4 + 주둥이턱). 주둥이턱 쐐기는 속심으로만 남기고(코끝을 뒤로 물림) 겉은 평면 판 3 단.
각 단: 정면 오각형(윗변 수평 · 아랫변 V) × 앞면 두 평면(가운데 능선). 위 단이 아래 단보다 `단차` 만큼 앞.
"""
import os, sys, json, subprocess
import numpy as np, manifold3d as M, time
_t0 = time.time()
def 때(s): print("  [%5.1f s] %s" % (time.time() - _t0, s), flush=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 얼굴3_턱 as T
E, F3, F2, F1 = T.E, T.F3, T.F2, T.F1
from 얼굴3 import 덩이, 볼록, 메, 틈, 색, 멋, FRA, V홈
from 얼굴3_턱 import 돌, 있으면

OUT = os.path.join(F3.ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴5"); os.makedirs(OUT, exist_ok=True)
바퀴D = os.path.join(OUT, "_바퀴"); os.makedirs(바퀴D, exist_ok=True)
원화 = os.path.join(os.path.dirname(F3.ROOT), "트레일", "trail7_part3d", "in", "omega_front_clean.png")

# ════════ 손잡이(mm) ════════
턱z = T.턱z
기울 = 0.55                                  # 앞면이 옆으로 가며 뒤로 물러나는 비(y / x)
두께 = 4.5                                   # 판 앞뒤(속심에 묻힘)
#      윗변 반폭 · 윗변 z · 옆 모서리 반폭 · 옆 모서리 z · 가운데 V 끝 z · 가운데 앞면 y
단 = [(8.8, 273.4, 8.6, 272.4, 270.4, -9.6),
      (8.4, 272.0, 8.0, 269.0, 266.4, -8.7),          # 바퀴 2: 2 · 3 단을 넓혀 방패꼴(원화는 아래 2/3 까지 넓다가 V)
      (7.6, 269.0, 6.2, 265.8, 턱z, -7.8)]
# 볼 가리개(바퀴 2): 옛 날개는 옆으로 벌어진 삼각(끝 x 17.6). 원화는 얼굴 옆에 아래로 늘어진 판 → 끝이 아래를 봄
날개 = [(8.6, 276.4), (11.6, 277.2), (13.8, 272.5), (13.0, 266.4), (10.6, 268.4), (8.6, 271.0)]
날개점 = [(x, 1.5 + 0.6 * (x - 9), z) for x, z in 날개] + [(x, 14.0, z) for x, z in 날개]
날개덩이 = 덩이(날개점) + 덩이([(-x, y, z) for x, y, z in 날개점])
코 = [(0, -7.6, 275.2), (2.6, -5.8, 274.0)]    # 1 단 윗면을 콧등으로 비스듬히 잇는 점

def 미늘(wt, zt, ws, zs, zc, yc, 위=()):
    앞 = [(0, yc, zt), (wt, yc + 기울 * wt, zt), (ws, yc + 기울 * ws, zs), (0, yc, zc)]
    return 덩이(앞 + [(x, y + 두께, z) for x, y, z in 앞] + list(위))
미늘들 = [미늘(*단[0], 위=코)] + [미늘(*d) for d in 단[1:]]

# ① 가면: 속심(주둥이턱 코끝을 뒤로) + 부리는 눈 사이 콧등만 + 미늘 3 단
표 = dict(T.표)
표["주둥이턱"] = [(0, -8.4, 270.4) if p == (0, -9.4, 270.4) else (0, T.턱y - 0.8 + 1.2, 턱z + 0.6) if p == (0, T.턱y, 턱z) else p for p in T.표["주둥이턱"]]
부리 = 덩이(표.pop("부리")).trim_by_plane([0, 0, 1], 273.2)
새겉 = M.Manifold.batch_boolean([덩이(p) for p in 표.values()] + [부리, 덩이(T.능선), 날개덩이] + 미늘들, M.OpType.Add) ^ F3.앞반
새속 = M.Manifold.batch_boolean([T.속(표[k]) for k in ("두개", "눈면", "주둥이턱")], M.OpType.Add)
껍질 = (새겉 - 새속) + ((F3.옛["투구앞"] ^ 새속) ^ F3.앞반)
가면 = V홈(껍질 - T.머리막 - F3.꽂는것, (0, -3.9, 285.0), (0, -6.2, 277.2), (0, -1, 0.3), 폭=0.6, 깊=0.5)
가면 = max((가면 - E.창L - E.창R).decompose(), key=lambda p: p.volume())
가면부풀 = F2.부풀(가면, 틈)
바탕L, 바탕R = [max((e - 가면부풀).decompose(), key=lambda p: p.volume()) for e in (E.새["눈바탕L_v5"][0], E.새["눈바탕R_v5"][0])]

때("가면")
머리 = {"가면투구": (가면, 색["흰"], "눈 고침 4 가면 + 턱 가리개 V 미늘 3 단(평면 판 · 단차 0.9 · 가운데 능선) · 이빨 · 입 없음"),
       "투구뒤": F3.새["투구뒤"],
       "눈바탕L": (바탕L, 색["검"], "눈 고침 4 눈바탕"), "눈바탕R": (바탕R, 색["검"], "눈 고침 4 눈바탕"),
       "눈L": E.새["눈L_v5"], "눈R": E.새["눈R_v5"],
       "V안테나L": (F3.안L, 색["금"], "금 뿔"), "V안테나R": (F3.안R, 색["금"], "금 뿔"),
       "뿔": F3.새["뿔"]}

끄덕앞 = 10.0      # +20° 까지 깎으면 턱 끝 2.3 mm · 3 단이 사라지고(바퀴 4) +15° 도 턱 끝 1.0 mm 가 잘린다(바퀴 5) → 앞 끄덕을 +10° 로 줄인다(턱 끝을 지킴)
# ①½ 끄덕 +15~20° 에서 실제 가슴앞과 겹친다(옛 검사는 돌출 부품만 봐서 놓침) → 가슴을 거꾸로 돌려 머리에서 깎는다
_가슴 = F2.부풀(F1.읽기(os.path.join(F1.DES, "몸통", "가슴앞.stl")) ^ M.Manifold.cube([70, 70, 70]).translate([-35, -20, 235.0]), 틈 + 0.15)
_거꾸로 = M.Manifold.batch_boolean([돌(_가슴, -d) for d in np.arange(10, 끄덕앞 + 0.1, 1.25)], M.OpType.Add)
for n in list(머리):
    m, c, b = 머리[n]; v = (m ^ _거꾸로).volume()
    if v > 0.001:
        머리[n] = (max((m - _거꾸로).decompose(), key=lambda p: p.volume()), c, b + " · 끄덕 +20° 가슴앞 비킴 %.1f mm³ 깎음" % v); print("가슴 비킴", n, round(v, 1), flush=True)
가면 = 머리["가면투구"][0]
# ② 몸 쪽: 높이 선 흰 깃(옆 날개 둘 · 옛 목깃 옆에 이어 앞으로) + 검은 목 채움(깃 안쪽 · 턱 밑)
몸D = os.path.join(F1.DES, "몸통")
목상자 = M.Manifold.cube([70, 70, 70]).translate([-35, -20, 235.0])     # 머리가 닿을 수 있는 곳만(몸 전체 부풀림은 메모리 15 GB 로 터졌다)
몸 = {n[:-4]: F1.읽기(os.path.join(몸D, n)) ^ 목상자 for n in sorted(os.listdir(몸D)) if n.endswith(".stl")}       # 실제 몸통 부품 전부
몸["돌출가슴앞"] = F1.읽기(os.path.join(F1.DES, "돌출", "돌출03_가슴앞.stl")) ^ 목상자
몸 = {k: v for k, v in 몸.items() if v.volume() > 0.01}; print("목 둘레 몸 부품", list(몸), flush=True)
몸합 = M.Manifold.batch_boolean(list(몸.values()), M.OpType.Add)
머리전부 = M.Manifold.batch_boolean([m for m, _, _ in 머리.values()] + [있으면(os.path.join(F2.프레임D, "머리.stl")), 있으면(os.path.join(F2.조립D, "관절_목위_자식.stl"))], M.OpType.Add)
# ponytail: 부풀린 머리(목 둘레만)를 3° 간격으로 쓴다(여유 0.6 = 틈 0.12 + 3° 사이 호 처짐). 1° × 쓴 뒤 부풀림은 100 만 면 · 메모리 터짐. 검사는 5° 마다 실제 머리로 따로.
머리아래 = F2.부풀(머리전부 ^ M.Manifold.cube([60, 80, 60]).translate([-30, -30, 230.0]), 0.6)
쓴부풀 = M.Manifold.batch_boolean([돌(머리아래, d) for d in np.arange(-25, 20.1, 3)], M.OpType.Add); 때("쓴 면 %d" % 쓴부풀.num_tri())
몸부풀 = F2.부풀(몸합, 틈); 때("몸 면 %d" % 몸부풀.num_tri())
# 깃(바퀴 2): 앞섶(라펠) 판 + 옆벽. 앞섶 = 정면에서 넓게 보이는 흰 면(안쪽 아래 → 바깥 위), 옆벽 = 옛 목깃까지 뒤로 이음
깃 = dict(안아래=(9.5, -4.5, 263.0), 밖아래=(22.0, -1.0, 263.0), 밖위=(20.6, 7.0, 276.6), 안위=(15.6, 7.0, 275.4), 두께=2.4, 뒤y=19.0, 뒤위=277.5)
def 깃날개(s):
    g = 깃; 앞 = [g[k] for k in ("안아래", "밖아래", "밖위", "안위")]
    섶 = 볼록([(s * x, y, z) for x, y, z in 앞] + [(s * (x + 0.6), y + g["두께"], z) for x, y, z in 앞])
    벽 = 볼록([(s * x, y, z) for x, z in ((g["안위"][0], g["안위"][2]), (g["밖위"][0], g["밖위"][2]), (22.4, 263.0), (19.6, 263.0)) for y in (g["밖위"][1], g["뒤y"])]
             + [(s * x, g["뒤y"], g["뒤위"]) for x in (16.0, 20.6)])
    return max(((섶 + 벽) - 쓴부풀 - 몸부풀).decompose(), key=lambda p: p.volume())
깃L, 깃R = 깃날개(-1), 깃날개(1); 때("깃 %d" % 깃L.num_tri())
목틀 = 볼록([(sx * x, y, z) for sx in (1, -1) for x, y, z in
            [(17.5, 1.5, 259.0), (17.5, 19.0, 259.0), (17.5, 1.5, 266.0), (17.5, 8.0, 270.0), (17.5, 19.0, 270.0), (6.0, -3.0, 259.0), (6.0, -3.0, 264.0)]])
# 깃과는 평면으로 가른다(깃 안쪽 모서리 선을 y 로 민 면 − 틈). 부풀린 깃을 빼는 불리언은 메모리 25 GB 로 터졌다
_a, _b = np.array(깃["안아래"])[[0, 2]], np.array(깃["안위"])[[0, 2]]; _n = np.array([-(_b - _a)[1], (_b - _a)[0]]); _n /= np.linalg.norm(_n)
for sx in (1, -1): 목틀 = 목틀.trim_by_plane([sx * _n[0], 0, _n[1]], float(_n @ _a) + 틈)
목검 = 목틀 - 쓴부풀; 때("목1 %d" % 목검.num_tri())
목검 = 목검 - 몸부풀 - F2.부풀(F1.이웃읽기()["목뼈"] ^ 목상자, 틈); 때("목2 %d" % 목검.num_tri())
목조각 = sorted(목검.decompose(), key=lambda p: -p.volume()); 목검 = 목조각[0]
때("깃 · 목")
몸새 = {"목깃옆L": (깃L, 색["흰"], "높이 선 흰 깃 옆 날개 — 옛 목깃 옆에서 앞으로 · 윗변이 앞으로 내려감 · 가슴에 접착"),
       "목깃옆R": (깃R, 색["흰"], "높이 선 흰 깃 옆 날개"),
       "목깃안검정": (목검, 색["검"], "검은 목 · 깃 안쪽 채움 — 끄덕 −25~+20° 쓴 머리 + 0.32 · 몸 + 0.12 뺌 · 가슴에 접착")}
새 = dict(머리, **몸새)

def 내보내기():
    for n, (m, _, _) in 새.items():
        t = 메(m); assert t.is_watertight and len(m.decompose()) == 1, n + " 안 닫힘/조각 %d" % len(m.decompose())
        t.export(os.path.join(OUT, n + ".stl"))
    때("STL")
    V = np.asarray(가면.to_mesh().vert_properties)[:, :3]
    print("턱 끝 z %.2f · 가장 앞 %s · 목 조각 부피 %s" % (V[:, 2].min(), np.round(V[V[:, 1].argmin()], 2), [round(p.volume(), 1) for p in 목조각[:4]]))
    # 미늘 계단: 가운데(x 1.5) 세로 줄에서 앞면 y 가 단마다 뒤로 물러나야 한다(질 수 있는 검사)
    ys = [T.앞면y(가면, 1.5, z) for z in (272.0, 268.0, 264.5)]; print("앞면 y (1 · 2 · 3 단)", np.round(ys, 2))
    assert 0.5 < ys[1] - ys[0] < 1.5 and 0.5 < ys[2] - ys[1] < 1.5, ys          # 위 한계: 바퀴 4 에서 3 단이 깎여 없어져도(−0.34) 통과했다
    assert V[:, 2].min() < 턱z + 0.8, "턱 끝이 잘림 %.2f" % V[:, 2].min()
    if "--검사" not in sys.argv: return
    이웃 = {k: v for k, v in F1.이웃읽기().items() if k not in F3.대체}; 이웃.update({"몸_" + k: v for k, v in 몸.items()})
    겹 = {}; ns = list(새)
    for i, a in enumerate(ns):
        for b in ns[i + 1:] + list(이웃):
            v = (새[a][0] ^ (새[b][0] if b in 새 else 이웃[b])).volume()
            if v > 0.005: 겹["%s∩%s" % (a, b)] = round(v, 3)
    틈재 = {"%s-%s" % (a, b): round(float(새[a][0].min_gap(새[b][0] if b in 새 else 몸합, 3.0)), 3) for a, b in
           (("눈바탕L", "가면투구"), ("목깃옆L", "가면투구"), ("목깃안검정", "가면투구"), ("목깃옆L", "목깃안검정"), ("목깃옆L", "몸"), ("목깃안검정", "몸"))}
    몸전부 = 몸합 + 깃L + 깃R + 목검
    머리합 = M.Manifold.batch_boolean([m for m, _, _ in 머리.values()], M.OpType.Add)
    끄덕 = {d: round((돌(머리합, d) ^ 몸전부).volume(), 3) for d in range(-25, 21, 5)}; 끄덕[끄덕앞] = round((돌(머리합, 끄덕앞) ^ 몸전부).volume(), 3)
    끄덕부품 = {d: {k: round(v, 3) for k, v in ((k, (돌(머리합, d) ^ m).volume()) for k, m in 몸.items()) if v > 0.005} for d in (-25, 15, 20)}
    끄덕틈 = {d: round(float(돌(머리합, d).min_gap(몸전부, 3.0)), 2) for d in (-25, -10, 0, 10, 20)}
    검 = {n: dict(닫힘=True, 조각=1, 부피mm3=round(m.volume(), 1), 크기mm=np.round(메(m).extents, 1).tolist()) for n, (m, _, _) in 새.items()}
    결과 = dict(설명="얼굴 5 — 턱 가리개 V 미늘 3 단 + 흰 깃 + 검은 목 (09-28)", 끄덕범위도=[-25, 끄덕앞], 단=단, 기울=기울, 깃=깃,
              겹침=겹, 끼움틈mm=틈재, 끄덕_겹침mm3_몸전부=끄덕, 끄덕_겹친부품=끄덕부품, 끄덕_최소틈mm=끄덕틈,
              부품={n: dict(파일=n + ".stl", 색=c, 비고=b, **검[n]) for n, (m, c, b) in 새.items()})
    json.dump(결과, open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    json.dump(dict(머리어깨_대체=["투구앞", "투구뒤", "얼굴", "뿔", "V안테나L", "V안테나R"], 몸통_추가=list(몸새), 몸통_대체=[],
                   안씀=["디자인_얼굴3이빨/위이빨", "아래이빨", "입안", "두건"]), open(os.path.join(OUT, "대체.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: 결과[k] for k in ("겹침", "끼움틈mm", "끄덕_겹침mm3_몸전부", "끄덕_겹친부품", "끄덕_최소틈mm")}, ensure_ascii=False, default=float))

# 원화 확대 틀: 1 px = 0.39 mm(돔 폭 57.5 px = 22.4 mm) · 가운데 x 536 · 턱 끝 y 181.7 = z 턱z
mmpx = 0.39
def 원화틀(cz, 폭=70.0, 크기=600):
    from PIL import Image
    cy = 181.7 - (cz - 턱z) / mmpx; h = 폭 / mmpx / 2
    return Image.open(원화).convert("RGB").crop((int(536 - h), int(cy - h), int(536 + h), int(cy + h))).resize((크기, 크기), Image.LANCZOS)
컷 = [("정면", 0, 0, 70.0, 280.0), ("반옆", 62, 8, 70.0, 288.0)]
def 빠른그림(OUTd, 부품들, d):
    os.makedirs(d, exist_ok=True)
    jf, pf = os.path.join(d, "빠른.json"), os.path.join(d, "빠른.py")
    몸파일 = [(os.path.join(몸D, n + ".stl"), 색["흰"]) for n in ("가슴앞", "목깃")]
    json.dump(dict(부품=[(os.path.join(OUTd, n + ".stl"), c) for n, c in 부품들] + 몸파일, out=d.replace("\\", "/"), 컷=컷), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    open(pf, "w", encoding="utf-8").write(F3.빠른.replace("line_thickness = 1.6", "line_thickness = 1.0"))
    r = subprocess.run([F1.BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
def 빠른렌더(N):
    from PIL import Image, ImageDraw, ImageFont
    d = os.path.join(바퀴D, str(N)); 빠른그림(OUT, [(n, c) for n, (m, c, _) in 새.items()], d)
    때("블렌더")
    f_ = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 24)
    칸 = [("원화 (같은 틀)", 원화틀(280.0)), ("얼굴 5 정면 (바퀴 %s)" % N, Image.open(os.path.join(d, "정면.png")).convert("RGB").resize((600, 600))),
          ("FRA mh_13", Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT).resize((714, 600)).crop((60, 0, 660, 600))),
          ("얼굴 5 반옆", Image.open(os.path.join(d, "반옆.png")).convert("RGB").resize((600, 600)))]
    S = Image.new("RGB", (4 * 610 + 10, 650), "white"); dr = ImageDraw.Draw(S)
    for i, (t, im) in enumerate(칸): S.paste(im, (10 + i * 610, 45)); dr.text((14 + i * 610, 8), t, font=f_, fill="black")
    p = os.path.join(바퀴D, "바퀴%s.jpg" % N); S.save(p, quality=88); print(p)

def 렌더(N):
    from PIL import Image, ImageDraw, ImageFont
    Tt = os.path.join(OUT, "_렌더"); os.makedirs(Tt, exist_ok=True)
    if "--시트만" not in sys.argv: T.전신(Tt, {n: (os.path.join(OUT, n + ".stl"), c) for n, (m, c, _) in 새.items()})
    이빨D = os.path.join(F3.ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴3이빨"); 이d = os.path.join(바퀴D, "이빨판")
    if not os.path.exists(os.path.join(이d, "정면.png")):
        P = json.load(open(os.path.join(이빨D, "부품.json"), encoding="utf-8"))["부품"]; 빠른그림(이빨D, [(n, v["색"]) for n, v in P.items()], 이d)
    f_ = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
    def 판(p, c): im = Image.open(os.path.join(p, "A_%s.png" % c)).convert("RGBA"); g = Image.new("RGBA", im.size, (205, 207, 212, 255)); g.alpha_composite(im); return g.convert("RGB")
    빠 = lambda n, c: Image.open(os.path.join(n, c + ".png")).convert("RGB")
    D5 = os.path.join(바퀴D, str(N))
    줄 = [[("원화 확대 (같은 틀)", 원화틀(280.0)), ("이빨 판 (틀린 것)", 빠(이d, "정면")), ("얼굴 5", 빠(D5, "정면"))],
          [("FRA 3/4 (mh_13 뒤집음 · 깊이 참고)", Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT)), ("얼굴 5 3/4", 빠(D5, "반옆"))],
          [("원화 전신", Image.open(원화).convert("RGB")), ("얼굴 5 전신 (같은 정면 카메라)", 판(Tt, "얼굴정면"))]]
    hs = [640, 560, 900]; W = 1990
    S = Image.new("RGB", (W, sum(hs) + 3 * 45 + 10), (245, 245, 243)); dr = ImageDraw.Draw(S); y = 45
    for 칸, h in zip(줄, hs):
        x = 10
        for t, im in 칸:
            im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
            if x + im.width > W: im = im.crop((0, 0, W - 10 - x, h))
            S.paste(im, (x, y)); dr.text((x + 6, y - 36), t, font=f_, fill=(30, 30, 30)); x += im.width + 10
        y += h + 45
    p = os.path.join(멋, "얼굴5.jpg"); S.save(p, quality=90); print("시트", p, S.size)

if __name__ == "__main__":
    내보내기()
    if "--빠른" in sys.argv: 빠른렌더(sys.argv[sys.argv.index("--빠른") + 1])
    if "--렌더" in sys.argv: 렌더(sys.argv[sys.argv.index("--렌더") + 1])
