# -*- coding: utf-8 -*-
"""오메가몬 PG 얼굴 — 눈 고침 4 바탕에 턱만 새로(2026-09-28). 「지금 턱이 없어, 턱이」.

    python 얼굴3_턱.py --빠른 N   -> 디자인_얼굴3턱/*.stl + _바퀴/N/{정면,반옆}.png + _바퀴/바퀴N.jpg
    python 얼굴3_턱.py --검사     -> 위 + 닫힘 · 이웃 겹침 · 목 끄덕임(−25~+20°) 겹침 → 부품.json
    python 얼굴3_턱.py --렌더 N   -> 전신 렌더 + 멋/얼굴_턱.jpg

바꾼 것(눈 · 이마 · 뿔 · 볼 날개 그대로):
 ① 부리 + 턱 두 덩이 → 한 덩이 쐐기「주둥이턱」: 코끝(가장 앞) → 턱 끝 곧은 능선 · 정면 V · 턱 끝 z = 눈 중심 − (돔 − 눈 중심)
 ② 턱 밑면은 턱 끝에서 뒤로 비스듬히 올라감(y 8 에서 z 267.6) — 수평 절단 없음
 ③ 머리막의 아래막(피벗 z 아래 수평 절단)을 y < 8 앞쪽에서 뺌 — 목 쓸기 · 머리뼈 · 관절 여유는 그대로
 ④ 송곳니 = 턱 옆면에 솟은 세로 돌기 둘(홈 → 덧살, 아래 끝 뾰족)
"""
import os, sys, json, subprocess
import numpy as np, manifold3d as M
from scipy.spatial.transform import Rotation as Rot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 얼굴3_눈4 as E
F3 = E.F3; F2 = F3.F2; F1 = F3.F1
from 얼굴3 import 덩이, 속, 볼록, 메, 틈, 색, 멋, FRA, V홈

OUT = os.path.join(F3.ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴3턱"); os.makedirs(OUT, exist_ok=True)
바퀴D = os.path.join(OUT, "_바퀴"); os.makedirs(바퀴D, exist_ok=True)

# ════════ 손잡이(mm) ════════
돔 = 293.3
눈z = float(E.구멍.centroid.y)
턱비 = 0.85                                # 눈 → 턱 끝 / 돔 → 눈. mh_12 에서 잼: 돔 225 · 눈 329 · 턱 끝 418 px → 0.85 (1.0 은 바퀴 1 에서 FRA 보다 길었음)
턱z = 눈z - 턱비 * (돔 - 눈z)
턱y = -6.0                                 # 턱 끝 앞뒤(코끝 y −9.4 보다 3.4 뒤 → 능선이 뒤로 22° 누움)
뒤y = 8.0                                  # 밑면이 여기서 z 267.6 까지 올라가고, 이보다 뒤는 옛 절단 그대로
for i, a in enumerate(sys.argv):
    if a in ("--턱z", "--턱y"): globals()[a[2:]] = float(sys.argv[i + 1])

표 = {k: v for k, v in F3.점.items() if k != "턱"}                     # 부리(윗면 · 코끝)는 그대로
# ① 주둥이턱(오른쪽 반) — 부리와 코끝 · 코 옆 꺾임을 같이 써서 단차 없이 이어지고, 코끝 → 턱 끝이 곧은 능선
표["주둥이턱"] = [
    (0, -9.4, 270.4), (5.4, -3.2, 269.0),                                # 코끝(가장 앞) · 코 옆 꺾임 = 부리와 같은 점
    (0, -3.0, 273.6), (8.6, -0.8, 272.4), (8.8, -0.4, 270.6),             # 볼 쪽 옆 모서리(옛 턱 윗변을 눈 밑으로 내림)
    (4.4, 턱y + 2.6, 턱z + 4.3), (0, 턱y, 턱z),                            # V 아래 모서리 · 턱 끝
    (0, 뒤y, 267.6), (8.8, 뒤y, 269.2),                                   # ② 밑면: 뒤로 비스듬히 올라감
    (8.8, 15.0, 272.4), (8.8, 15.0, 270.6), (0, 15.0, 273.6), (0, 15.0, 269.0),
]
능선 = F3.능선
날개점 = [(x, 1.5 + 0.6 * (x - 9), z) for x, z in F3.날개] + [(x, 14.0, z) for x, z in F3.날개]
날개덩이 = 덩이(날개점) + 덩이([(-x, y, z) for x, y, z in 날개점])
새겉 = M.Manifold.batch_boolean([덩이(p) for p in 표.values()] + [덩이(능선), 날개덩이], M.OpType.Add) ^ F3.앞반
새속 = M.Manifold.batch_boolean([속(표[k]) for k in ("두개", "눈면", "주둥이턱")], M.OpType.Add)

# ③ 머리막: 아래막의 앞쪽(y < 뒤y)만 뺌
def 있으면(f): return F1.읽기(f) if os.path.exists(f) else M.Manifold()
앞빼기 = M.Manifold.cube([80, 30, 40]).translate([-40, 뒤y - 30, 230.0])
머리막 = F2.목쓸기 + (F2.아래막 - 앞빼기) + 있으면(os.path.join(F2.프레임D, "머리.stl")) + 있으면(os.path.join(F2.조립D, "관절_목위_자식.stl"))

# ④ 송곳니: 턱 옆면 위로 솟은 세로 돌기(위 폭 1.2 · 아래 끝 뾰족 · 앞으로 0.9)
def 앞면y(m, x, z):
    b = (m ^ M.Manifold.cube([0.1, 60, 0.1]).translate([x - 0.05, -30, z - 0.05])).bounding_box(); return b[1]
송 = dict(x=4.6, 위=271.6, 아래=턱z + 4.4)      # FRA: 코 옆에서 아래로 · 턱 끝보다 4.4 위에서 뾰족하게 끝남
def 송곳니(s):
    P = []
    for z, 반 in ((송["위"], 0.6), (송["아래"] + 1.4, 0.4)):
        for dx in (-반, 반):
            y0 = 앞면y(새겉, s * (송["x"] + dx), z); assert np.isfinite(y0), (dx, z)
            P += [(s * (송["x"] + dx), y0 - 0.9, z), (s * (송["x"] + dx), y0 + 1.2, z)]
    y0 = 앞면y(새겉, s * 송["x"], 송["아래"] + 0.2); assert np.isfinite(y0)
    P += [(s * 송["x"], y0 - 0.5, 송["아래"]), (s * 송["x"], y0 + 1.2, 송["아래"])]
    m = 볼록(P); assert m.volume() > 3, m.volume(); return m

껍질 = (새겉 - 새속) + ((F3.옛["투구앞"] ^ 새속) ^ F3.앞반)
가면 = V홈(껍질 - 머리막 - F3.꽂는것, (0, -3.9, 285.0), (0, -6.2, 277.2), (0, -1, 0.3), 폭=0.6, 깊=0.5)
가면 = 가면 + ((송곳니(1) + 송곳니(-1)) - 머리막)
가면 = max((가면 - E.창L - E.창R).decompose(), key=lambda p: p.volume())
가면부풀 = F2.부풀(가면, 틈)
바탕L, 바탕R = [max((e - 가면부풀).decompose(), key=lambda p: p.volume()) for e in (E.새["눈바탕L_v5"][0], E.새["눈바탕R_v5"][0])]

새 = {"가면투구": (가면, 색["흰"], "눈 고침 4 가면 + 한 덩이 주둥이턱 쐐기 · 턱 끝 z %.1f · 밑면 뒤로 올라감 · 송곳니 덧살" % 턱z),
      "투구뒤": F3.새["투구뒤"],
      "눈바탕L": (바탕L, 색["검"], "눈 고침 4 눈바탕"), "눈바탕R": (바탕R, 색["검"], "눈 고침 4 눈바탕"),
      "눈L": E.새["눈L_v5"], "눈R": E.새["눈R_v5"],
      "V안테나L": (F3.안L, 색["금"], "금 뿔"), "V안테나R": (F3.안R, 색["금"], "금 뿔"),
      "뿔": F3.새["뿔"]}

def 돌(m, d):
    R = Rot.from_rotvec([np.radians(d), 0, 0]).as_matrix(); return m.transform(np.hstack([R, (F2.Pn - R @ F2.Pn).reshape(3, 1)]))
def 내보내기():
    for n, (m, _, _) in 새.items():
        t = 메(m); assert t.is_watertight and len(m.decompose()) == 1, n + " 안 닫힘/조각 %d" % len(m.decompose())
        t.export(os.path.join(OUT, n + ".stl"))
    V = np.asarray(가면.to_mesh().vert_properties)[:, :3]
    print("턱 끝 z %.2f (목표 %.2f) · 눈 중심 z %.2f · 가장 앞 %s" % (V[:, 2].min(), 턱z, 눈z, np.round(V[V[:, 1].argmin()], 2)))
    if "--검사" not in sys.argv: return
    이웃 = {k: v for k, v in F1.이웃읽기().items() if k not in F3.대체}
    겹 = {}; ns = list(새)
    for i, a in enumerate(ns):
        for b in ns[i + 1:] + list(이웃):
            v = (새[a][0] ^ (새[b][0] if b in 새 else 이웃[b])).volume()
            if v > 0.005: 겹["%s∩%s" % (a, b)] = round(v, 3)
    몸 = 이웃["가슴앞"] + 이웃["목깃"]
    머리새 = M.Manifold.batch_boolean([m for m, _, _ in 새.values()], M.OpType.Add)
    머리눈4 = M.Manifold.batch_boolean([E.가면] + [F3.새[n][0] for n in ("투구뒤", "뿔")] + [F3.안L, F3.안R], M.OpType.Add)
    끄덕 = {d: dict(눈4=round((돌(머리눈4, d) ^ 몸).volume(), 3), 턱=round((돌(머리새, d) ^ 몸).volume(), 3)) for d in range(-25, 21, 5)}
    # 턱 끝과 목깃 · 가슴앞 사이 최소 거리(끄덕 끝에서)
    거리 = {d: round(float(돌(가면, d).min_gap(몸, 5.0)), 2) for d in (-25, 0, 20)}
    검 = {n: dict(닫힘=True, 조각=1, 부피mm3=round(m.volume(), 1), 크기mm=np.round(메(m).extents, 1).tolist()) for n, (m, _, _) in 새.items()}
    결과 = dict(설명="눈 고침 4 + 턱(09-28)", 턱끝z=round(float(V[:, 2].min()), 2), 눈중심z=round(눈z, 2), 돔=돔, 주둥이턱=표["주둥이턱"],
              겹침=겹, 끄덕_겹침mm3_가슴목깃=끄덕, 가면_몸_최소틈mm=거리, 부품={n: dict(파일=n + ".stl", 색=c, 비고=b, **검[n]) for n, (m, c, b) in 새.items()})
    json.dump(결과, open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: 결과[k] for k in ("겹침", "끄덕_겹침mm3_가슴목깃", "가면_몸_최소틈mm")}, ensure_ascii=False, default=float))

def 빠른렌더(N):
    from PIL import Image, ImageDraw, ImageFont
    d = os.path.join(바퀴D, str(N)); os.makedirs(d, exist_ok=True)
    jf, pf = os.path.join(d, "빠른.json"), os.path.join(d, "빠른.py")
    json.dump(dict(부품=[(os.path.join(OUT, n + ".stl"), c) for n, (m, c, _) in 새.items()], out=d.replace("\\", "/"),
                   컷=[("정면", 0, 0, 70.0, 292.9), ("반옆", 62, 8, 70.0, 288.0)]), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    open(pf, "w", encoding="utf-8").write(F3.빠른.replace("line_thickness = 1.6", "line_thickness = 1.0"))
    r = subprocess.run([F1.BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    f_ = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 24)
    D4 = os.path.join(F3.OUT, "_바퀴", "눈", "후4")
    칸 = [("FRA mh_12", Image.open(os.path.join(FRA, "mh_12.jpg")).resize((597, 600))),
          ("눈 고침 4", Image.open(os.path.join(D4, "정면.png")).convert("RGB").resize((597, 600))),
          ("턱 (바퀴 %s)" % N, Image.open(os.path.join(d, "정면.png")).convert("RGB").resize((597, 600))),
          ("FRA mh_13", Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT).resize((714, 600))),
          ("눈4 반옆", Image.open(os.path.join(D4, "반옆.png")).convert("RGB").resize((597, 600))),
          ("턱 반옆", Image.open(os.path.join(d, "반옆.png")).convert("RGB").resize((597, 600)))]
    S = Image.new("RGB", (3 * 607 + 10, 1300), "white"); dr = ImageDraw.Draw(S)
    for i, (t, im) in enumerate(칸):
        x, y = 10 + (i % 3) * 607, 45 + (i // 3) * 650
        S.paste(im.crop((0, 0, 597, 600)), (x, y)); dr.text((x + 4, y - 38), t, font=f_, fill="black")
        if i in (1, 2):                            # 렌더 틀: 돔 · 눈 중심 · 목표 턱 끝
            for z in (돔, 눈z, 턱z): py = (450 - (z - 292.9) * 12.8) * 600 / 900; dr.line([(x, y + py), (x + 597, y + py)], fill=(255, 0, 0), width=1)
    p = os.path.join(바퀴D, "바퀴%s.jpg" % N); S.save(p, quality=88); print(p)

def 전신(TMP, 부품):
    d = os.path.join(TMP, "DES")
    for 폴더 in ("몸통", "다리", "머리어깨", "색분할", "돌출"):
        P = json.load(open(os.path.join(F3.DES, 폴더, "부품.json"), encoding="utf-8"))
        P = dict(부품={n: dict(v, 파일=os.path.join(F3.DES, 폴더, v.get("파일", n + ".stl"))) for n, v in P["부품"].items()}, 대체=P.get("대체"))
        if 폴더 == "머리어깨":
            for n in ("투구앞", "얼굴"): P["부품"].pop(n, None)
            for n, (fp, c) in 부품.items(): P["부품"][n] = dict(파일=fp, 색=c)
        os.makedirs(os.path.join(d, 폴더), exist_ok=True)
        json.dump(P, open(os.path.join(d, 폴더, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False)
    open(os.path.join(TMP, "구동.py"), "w", encoding="utf-8").write(F1.구동.format(src=os.path.join(F3.ROOT, "실험_20260927")))
    r = subprocess.run([F1.BLENDER, "-b", "-P", os.path.join(TMP, "구동.py"), "--", d, TMP], capture_output=True); assert r.returncode == 0, r.stderr[-1500:]
def 렌더(N):
    from PIL import Image, ImageDraw, ImageFont
    T = os.path.join(OUT, "_렌더"); os.makedirs(T, exist_ok=True)
    if "--시트만" not in sys.argv: 전신(T, {n: (os.path.join(OUT, n + ".stl"), c) for n, (m, c, _) in 새.items()})
    T4 = os.path.join(F3.ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴4", "_렌더_눈4")
    f_ = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
    def 판(p, c): im = Image.open(os.path.join(p, "A_%s.png" % c)).convert("RGBA"); g = Image.new("RGBA", im.size, (205, 207, 212, 255)); g.alpha_composite(im); return g.convert("RGB")
    빠 = lambda n, c: Image.open(os.path.join(n, c + ".png")).convert("RGB")
    D4, D5 = os.path.join(F3.OUT, "_바퀴", "눈", "후4"), os.path.join(바퀴D, str(N))
    줄 = [[("FRA 정면 mh_12", Image.open(os.path.join(FRA, "mh_12.jpg"))), ("눈 고침 4", 빠(D4, "정면")), ("턱", 빠(D5, "정면"))],
          [("FRA 3/4 (mh_13 뒤집음)", Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT)), ("눈 고침 4 3/4", 빠(D4, "반옆")), ("턱 3/4", 빠(D5, "반옆"))],
          [("전신 영웅 3/4 — 눈 고침 4", 판(T4, "영웅큰")), ("전신 영웅 3/4 — 턱", 판(T, "영웅큰"))]]
    hs = [560, 560, 900]; W = 1990
    S = Image.new("RGB", (W, sum(hs) + 3 * 45 + 10), (245, 245, 243)); dr = ImageDraw.Draw(S); y = 45
    for 칸, h in zip(줄, hs):
        x = 10
        for t, im in 칸:
            im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
            if x + im.width > W: im = im.crop((0, 0, W - 10 - x, h))
            S.paste(im, (x, y)); dr.text((x + 6, y - 36), t, font=f_, fill=(30, 30, 30)); x += im.width + 10
        y += h + 45
    p = os.path.join(멋, "얼굴_턱.jpg"); S.save(p, quality=90); print("시트", p, S.size)

if __name__ == "__main__":
    내보내기()
    if "--빠른" in sys.argv: 빠른렌더(sys.argv[sys.argv.index("--빠른") + 1])
    if "--렌더" in sys.argv: 렌더(sys.argv[sys.argv.index("--렌더") + 1])
