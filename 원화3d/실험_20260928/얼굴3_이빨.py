# -*- coding: utf-8 -*-
"""오메가몬 PG 얼굴 — 턱 판 위에 이빨 턱(A) + 검은 두건(B) (2026-09-28). 사용자가 A+B 를 골랐다.

    python 얼굴3_이빨.py --빠른 N   -> 디자인_얼굴3이빨/*.stl + _바퀴/N/{정면,반옆}.png + _바퀴/바퀴N.jpg
    python 얼굴3_이빨.py --검사     -> 닫힘 · 이웃 겹침 · 끼움 틈 · 이빨 판 얇은살 · 목 끄덕임 → 부품.json
    python 얼굴3_이빨.py --렌더 N   -> 전신 렌더 + 멋/얼굴_이빨.jpg

A. 코 쐐기 밑을 입으로 연다(가면에서 입 구멍) → 앞에서부터 위 이빨 판(흰) · 아래 이빨 판(흰) · 입 안 판(검) 세 겹.
   세 판 모두 정면 V(가운데 앞 · 옆 뒤) 를 따르는 쐐기 판. 틈 0.12. 옛 송곳니 덧살은 위 이빨 줄 바깥 큰 이빨로 흡수.
   아래턱 V 모서리를 조금 내려(턱 끝은 그대로) 입 옆에 이빨 자리를 만든다.
B. 검은 두건: 몸(가슴) 쪽 부품. 머리 뒤 · 옆 · 턱 밑 공간을 채우는 덩이 − 끄덕 −25~+20° 로 쓴 머리 − 몸 부품(틈 0.12).
"""
import os, sys, json
import numpy as np, manifold3d as M
from shapely.geometry import Polygon, box
import 얼굴3_턱 as T
E, F3, F2, F1 = T.E, T.F3, T.F2, T.F1
from 얼굴3 import 덩이, 볼록, 메, 틈, 색, 멋, FRA, V홈

OUT = os.path.join(F3.ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴3이빨"); os.makedirs(OUT, exist_ok=True)
바퀴D = os.path.join(OUT, "_바퀴"); os.makedirs(바퀴D, exist_ok=True)

# ════════ 손잡이(mm) ════════
V모 = (5.2, T.턱y + 3.0, T.턱z + 3.0)      # 아래턱 V 모서리(턱 판 4.4, z +4.3 → 옆으로 · 아래로: 입 옆에 이빨 자리)
입 = [(-4.6, 269.0), (4.6, 269.0), (4.6, 266.2), (0, 263.4), (-4.6, 266.2)]      # 정면 입 구멍(x, z)
def f(x): return -7.2 + 0.9 * abs(x)       # 위 이빨 앞면 y — 정면 V 를 따라 옆이 뒤로
층 = dict(위=(0.0, 1.0), 아래=(1.0 + 틈, 2.0 + 틈), 입안=(2.0 + 2 * 틈, 3.2 + 2 * 틈))
구멍뒤 = 3.2 + 3 * 틈
위띠 = 268.4                               # 위 이빨 띠 아래 끝
위이 = [(0, 267.0), (1.8, 267.0), (-1.8, 267.0), (3.6, 266.2), (-3.6, 266.2)]     # (중심 x, 끝 z) — ±3.6 = 송곳니
아래이 = [(0.9, 266.0), (-0.9, 266.0), (2.7, 266.7), (-2.7, 266.7)]   # 바퀴 2: 끝이 위 이빨과 겹쳐 입 안이 가는 삼각뿐 → 벌린 입으로 낮춤               # 위와 반 칸 엇갈림 → W
이폭, 끝폭, 띠 = 1.8, 0.8, 0.8
def 아래선(x): return 263.4 + (266.2 - 263.4) * abs(x) / 4.6

# ① 가면: 턱 판의 표에서 V 모서리만 옮기고, 송곳니 덧살 없이 다시 짓는다
표 = dict(T.표); 표["주둥이턱"] = [V모 if p == (4.4, T.턱y + 2.6, T.턱z + 4.3) else p for p in T.표["주둥이턱"]]
assert V모 in 표["주둥이턱"]
새겉 = M.Manifold.batch_boolean([덩이(p) for p in 표.values()] + [덩이(T.능선), T.날개덩이], M.OpType.Add) ^ F3.앞반
새속 = M.Manifold.batch_boolean([T.속(표[k]) for k in ("두개", "눈면", "주둥이턱")], M.OpType.Add)

def 쐐기판(pg, a, b):
    """정면 볼록 다각형 pg(x, z) 를 y = f(x)+a … f(x)+b 로 민 판. x=0 에서 V 로 꺾이므로 좌우 반을 따로 볼록으로."""
    out = []
    for s in (1, -1):
        q = pg.intersection(box(0, 200, 30, 300) if s > 0 else box(-30, 200, 0, 300))
        if q.area < 1e-4: continue
        xs = list(q.exterior.coords)[:-1]
        out.append(볼록([(x, f(x) + a, z) for x, z in xs] + [(x, f(x) + b, z) for x, z in xs]))
    return M.Manifold.batch_boolean(out, M.OpType.Add)
입pg = Polygon(입); 안pg = 입pg.buffer(-틈, join_style=2)
def 이빨판(이들, 위쪽):
    조각 = []
    for cx, tz in 이들:
        if 위쪽: bz, P = 위띠, [(cx - 이폭 / 2, 269.5), (cx + 이폭 / 2, 269.5), (cx + 이폭 / 2, 위띠), (cx + 끝폭 / 2, tz), (cx - 끝폭 / 2, tz), (cx - 이폭 / 2, 위띠)]
        else:
            l, r = cx - 이폭 / 2, cx + 이폭 / 2
            P = [(l, 262.0), (r, 262.0), (r, 아래선(r) + 띠), (cx + 끝폭 / 2, tz), (cx - 끝폭 / 2, tz), (l, 아래선(l) + 띠)]
        조각.append(Polygon(P).intersection(안pg))
    if 위쪽: 조각.append(box(-4.6, 위띠, 4.6, 269.5).intersection(안pg))          # 띠(이빨 사이 · 바깥 끝까지)
    else: 조각 += [Polygon([(0, 262.0), (s * 3.6, 262.0), (s * 3.6, 아래선(3.6) + 띠), (0, 아래선(0) + 띠)]).intersection(안pg) for s in (1, -1)]   # V 띠(이빨을 한 판으로)
    return M.Manifold.batch_boolean([쐐기판(q, *층["위" if 위쪽 else "아래"]) for q in 조각], M.OpType.Add)

구멍 = M.Manifold.batch_boolean([볼록([(x, -20, z) for x, z in list(q.exterior.coords)[:-1]] + [(x, f(x) + 구멍뒤, z) for x, z in list(q.exterior.coords)[:-1]])
                                for q in (입pg.intersection(box(0, 200, 30, 300)), 입pg.intersection(box(-30, 200, 0, 300)))], M.OpType.Add)
껍질 = (새겉 - 새속) + ((F3.옛["투구앞"] ^ 새속) ^ F3.앞반)
가면 = V홈(껍질 - T.머리막 - F3.꽂는것, (0, -3.9, 285.0), (0, -6.2, 277.2), (0, -1, 0.3), 폭=0.6, 깊=0.5)
가면 = max((가면 - E.창L - E.창R - 구멍).decompose(), key=lambda p: p.volume())
가면부풀 = F2.부풀(가면, 틈)
바탕L, 바탕R = [max((e - 가면부풀).decompose(), key=lambda p: p.volume()) for e in (E.새["눈바탕L_v5"][0], E.새["눈바탕R_v5"][0])]
머막부풀 = F2.부풀(T.머리막, 틈)
def 한덩이(m): return max(m.decompose(), key=lambda p: p.volume())
위판 = 한덩이(이빨판(위이, True) - 머막부풀)
아래판 = 한덩이(이빨판(아래이, False) - 머막부풀)
입안 = 한덩이(쐐기판(안pg, *층["입안"]) - 머막부풀)

머리 = {"가면투구": (가면, 색["흰"], "턱 판 가면 − 입 구멍 · 아래턱 V 모서리 %s · 송곳니 덧살 없앰" % (V모,)),
       "투구뒤": F3.새["투구뒤"],
       "눈바탕L": (바탕L, 색["검"], "눈 고침 4 눈바탕"), "눈바탕R": (바탕R, 색["검"], "눈 고침 4 눈바탕"),
       "눈L": E.새["눈L_v5"], "눈R": E.새["눈R_v5"],
       "위이빨": (위판, 색["흰"], "위 이빨 판 — 이 5(가운데 3 + 바깥 송곳니 2) · 폭 1.8 · 끝 0.8 · 두께 1.0 · 입 구멍 윗면에 틈 0.12 로 닿고 아래 이빨 판 앞에 붙임"),
       "아래이빨": (아래판, 색["흰"], "아래 이빨 판 — 이 4 · 위와 반 칸 엇갈림(W) · 두께 1.0 · 입 구멍 아랫면에 틈 0.12"),
       "입안": (입안, 색["검"], "검은 입 안 판 — 입 구멍 전체를 뒤에서 막음 · 두께 1.2 · 틈 0.12"),
       "V안테나L": (F3.안L, 색["금"], "금 뿔"), "V안테나R": (F3.안R, 색["금"], "금 뿔"),
       "뿔": F3.새["뿔"]}

# ② 검은 두건(몸 쪽) — 끄덕 1° 간격으로 쓴 머리 + 틈 을 뺀다
from 얼굴3_턱 import 돌, 있으면
몸D = os.path.join(F1.DES, "몸통")
몸 = {n: F1.읽기(os.path.join(몸D, n + ".stl")) for n in ("가슴앞", "가슴뒤", "목깃")}
몸["돌출가슴앞"] = F1.이웃읽기()["가슴앞"]; 몸["목뼈"] = F1.이웃읽기()["목뼈"]
머리전부 = M.Manifold.batch_boolean([m for m, _, _ in 머리.values()] + [있으면(os.path.join(F2.프레임D, "머리.stl")), 있으면(os.path.join(F2.조립D, "관절_목위_자식.stl"))], M.OpType.Add)
쓴머리 = M.Manifold.batch_boolean([돌(머리전부, d) for d in range(-25, 21)], M.OpType.Add)
두건틀 = 볼록([(sx * x, y, z) for sx in (1, -1) for x, y, z in
              [(9.0, 2.0, 255.0), (15.5, 7.0, 257.0), (15.5, 7.0, 281.0), (12.0, 9.0, 285.0), (15.5, 26.0, 257.0), (14.0, 24.0, 280.0), (9.0, 26.0, 255.0)]])
두건 = 두건틀 - F2.부풀(쓴머리, 틈 + 0.2) - F2.부풀(M.Manifold.batch_boolean(list(몸.values()), M.OpType.Add), 틈)
두건조각 = sorted(두건.decompose(), key=lambda p: -p.volume())
두건 = 두건조각[0]
몸새 = {"두건": (두건, 색["검"], "검은 두건 — 가슴 목 구멍 · 목깃 앞을 채움 · 끄덕 −25~+20° 쓴 머리 + 0.32 · 몸 부품 + 0.12 를 뺌 · 가슴에 접착")}
새 = dict(머리, **몸새)

def 내보내기():
    for n, (m, _, _) in 새.items():
        t = 메(m); assert t.is_watertight and len(m.decompose()) == 1, n + " 안 닫힘/조각 %d" % len(m.decompose())
        t.export(os.path.join(OUT, n + ".stl"))
    print("두건 조각 부피", [round(p.volume(), 1) for p in 두건조각[:4]], "· 위/아래/입안 부피", round(위판.volume(), 1), round(아래판.volume(), 1), round(입안.volume(), 1))
    # 이빨 수: 이빨 높이 한가운데 가로 단면의 조각 수와 폭
    for n, m, z in (("위", 위판, 267.6), ("아래", 아래판, 265.6)):
        ps = m.slice(z).to_polygons(); assert len(ps) == (5 if n == "위" else 4), (n, len(ps)); print(n, "이빨 단면 z %.1f: %d 조각 · x 폭" % (z, len(ps)), sorted(round(np.ptp(np.array(p)[:, 0]), 2) for p in ps))
    if "--검사" not in sys.argv: return
    이웃 = {k: v for k, v in F1.이웃읽기().items() if k not in F3.대체}
    이웃.update({"몸_" + k: v for k, v in 몸.items() if k in ("가슴앞", "가슴뒤")})
    겹 = {}; ns = list(새)
    for i, a in enumerate(ns):
        for b in ns[i + 1:] + list(이웃):
            v = (새[a][0] ^ (새[b][0] if b in 새 else 이웃[b])).volume()
            if v > 0.005: 겹["%s∩%s" % (a, b)] = round(v, 3)
    틈재 = {"%s-%s" % (a, b): round(float(새[a][0].min_gap(새[b][0], 2.0)), 3) for a, b in
           (("위이빨", "가면투구"), ("아래이빨", "가면투구"), ("입안", "가면투구"), ("위이빨", "아래이빨"), ("아래이빨", "입안"), ("두건", "가면투구"))}
    몸합 = M.Manifold.batch_boolean(list(몸.values()) + [두건], M.OpType.Add)
    머리합 = M.Manifold.batch_boolean([m for m, _, _ in 머리.values()], M.OpType.Add)
    끄덕 = {d: round((돌(머리합, d) ^ 몸합).volume(), 3) for d in range(-25, 21, 5)}
    끄덕틈 = {d: round(float(돌(머리합, d).min_gap(두건, 3.0)), 2) for d in (-25, -10, 0, 10, 20)}
    얇 = {n: F1.얇은곳(새[n][0]) for n in ("위이빨", "아래이빨", "입안")}
    검 = {n: dict(닫힘=True, 조각=1, 부피mm3=round(m.volume(), 1), 크기mm=np.round(메(m).extents, 1).tolist()) for n, (m, _, _) in 새.items()}
    결과 = dict(설명="턱 판 + 이빨 턱(A) + 검은 두건(B) (09-28)", 입=입, 위이=위이, 아래이=아래이, V모=V모, 층=층,
              대체=dict(머리어깨=["투구앞", "투구뒤", "얼굴", "뿔", "V안테나L", "V안테나R"], 몸통_추가=["두건"]),
              겹침=겹, 끼움틈mm=틈재, 끄덕_겹침mm3_몸두건=끄덕, 끄덕_두건최소틈mm=끄덕틈, 얇은살mm3_r04=얇,
              부품={n: dict(파일=n + ".stl", 색=c, 비고=b, **검[n]) for n, (m, c, b) in 새.items()})
    json.dump(결과, open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: 결과[k] for k in ("겹침", "끼움틈mm", "끄덕_겹침mm3_몸두건", "끄덕_두건최소틈mm", "얇은살mm3_r04")}, ensure_ascii=False, default=float))

def 빠른렌더(N):
    import subprocess
    from PIL import Image, ImageDraw, ImageFont
    d = os.path.join(바퀴D, str(N)); os.makedirs(d, exist_ok=True)
    jf, pf = os.path.join(d, "빠른.json"), os.path.join(d, "빠른.py")
    몸파일 = [(os.path.join(몸D, n + ".stl"), 색["흰"]) for n in ("가슴앞", "목깃")]
    json.dump(dict(부품=[(os.path.join(OUT, n + ".stl"), c) for n, (m, c, _) in 새.items()] + 몸파일, out=d.replace("\\", "/"),
                   컷=[("정면", 0, 0, 70.0, 292.9), ("반옆", 62, 8, 70.0, 288.0)]), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    open(pf, "w", encoding="utf-8").write(F3.빠른.replace("line_thickness = 1.6", "line_thickness = 1.0"))
    r = subprocess.run([F1.BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    f_ = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 24)
    D2 = os.path.join(T.바퀴D, "2")
    칸 = [("tri.", 얼굴자르기("tri")), ("턱 판", Image.open(os.path.join(D2, "정면.png")).convert("RGB").resize((597, 600))),
          ("이빨+두건 (바퀴 %s)" % N, Image.open(os.path.join(d, "정면.png")).convert("RGB").resize((597, 600))),
          ("설정화", 얼굴자르기("설정")), ("턱 판 반옆", Image.open(os.path.join(D2, "반옆.png")).convert("RGB").resize((597, 600))),
          ("이빨+두건 반옆", Image.open(os.path.join(d, "반옆.png")).convert("RGB").resize((597, 600)))]
    S = Image.new("RGB", (3 * 607 + 10, 1300), "white"); dr = ImageDraw.Draw(S)
    for i, (t, im) in enumerate(칸):
        x, y = 10 + (i % 3) * 607, 45 + (i // 3) * 650
        im = im.resize((597, 600)); S.paste(im, (x, y)); dr.text((x + 4, y - 38), t, font=f_, fill="black")
    p = os.path.join(바퀴D, "바퀴%s.jpg" % N); S.save(p, quality=88); print(p)

원작 = os.path.join(F3.ROOT, "out", "번역", "디지몬", "원작")
def 얼굴자르기(k):
    from PIL import Image
    if k == "tri": return Image.open(os.path.join(원작, "Omegamon_tri.png")).convert("RGB").crop((270, 0, 390, 130)).resize((597, 600))
    return Image.open(os.path.join(원작, "Omegamon1.png")).convert("RGB").crop((365, 105, 485, 235)).resize((597, 600))

def 렌더(N):
    from PIL import Image, ImageDraw, ImageFont
    Tt = os.path.join(OUT, "_렌더"); os.makedirs(Tt, exist_ok=True)
    if "--시트만" not in sys.argv: T.전신(Tt, {n: (os.path.join(OUT, n + ".stl"), c) for n, (m, c, _) in 새.items()})
    T턱 = os.path.join(T.OUT, "_렌더")
    f_ = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
    def 판(p, c): im = Image.open(os.path.join(p, "A_%s.png" % c)).convert("RGBA"); g = Image.new("RGBA", im.size, (205, 207, 212, 255)); g.alpha_composite(im); return g.convert("RGB")
    빠 = lambda n, c: Image.open(os.path.join(n, c + ".png")).convert("RGB")
    D2, D5 = os.path.join(T.바퀴D, "2"), os.path.join(바퀴D, str(N))
    줄 = [[("설정화 얼굴", 얼굴자르기("설정")), ("tri. 얼굴", 얼굴자르기("tri")), ("턱 판", 빠(D2, "정면")), ("이빨+두건", 빠(D5, "정면"))],
          [("FRA 3/4 (mh_13 뒤집음)", Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT)), ("턱 판 3/4", 빠(D2, "반옆")), ("이빨+두건 3/4", 빠(D5, "반옆"))],
          [("전신 영웅 3/4 — 턱 판", 판(T턱, "영웅큰")), ("전신 영웅 3/4 — 이빨+두건", 판(Tt, "영웅큰"))]]
    hs = [480, 560, 900]; W = 1990
    S = Image.new("RGB", (W, sum(hs) + 3 * 45 + 10), (245, 245, 243)); dr = ImageDraw.Draw(S); y = 45
    for 칸, h in zip(줄, hs):
        x = 10
        for t, im in 칸:
            im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
            if x + im.width > W: im = im.crop((0, 0, W - 10 - x, h))
            S.paste(im, (x, y)); dr.text((x + 6, y - 36), t, font=f_, fill=(30, 30, 30)); x += im.width + 10
        y += h + 45
    p = os.path.join(멋, "얼굴_이빨.jpg"); S.save(p, quality=90); print("시트", p, S.size)

if __name__ == "__main__":
    내보내기()
    if "--빠른" in sys.argv: 빠른렌더(sys.argv[sys.argv.index("--빠른") + 1])
    if "--렌더" in sys.argv: 렌더(sys.argv[sys.argv.index("--렌더") + 1])
