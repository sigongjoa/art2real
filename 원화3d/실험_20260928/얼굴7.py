# -*- coding: utf-8 -*-
"""오메가몬 PG 얼굴 7 (2026-09-28) — 소체 위에 세 겹(속머리 → 마스크 → 투구). 「기존 시스템을 이용해서 만들어볼래?」

    python 얼굴7.py  -> out/출력/오메가몬_PG/디자인_얼굴7/*.stl · 부품.json · 멋/얼굴7.jpg
소체 = 소체머리3.py. 갑주는 전부 소체에서 나온다:
  속머리(검) = 소체 자체(눈이 여기 달림) · 틈으로 보이는 곳이 검은 눈 띠.
  마스크(흰) = 소체를 d_k 만큼 부풀린 면 ∩ 정면 V 띠 k (3 장, 아래로 갈수록 얇게 = 뒤로 물러나는 계단) − 소체 부풀림 0.3.
             턱 사선은 소체 턱선을 따른 결과(깎는 면 없음).
  투구(흰) = 6A 투구앞 중 z ≥ 차양밑 + 6A 투구뒤 − 소체 부풀림 0.3 − 마스크 틈.
ponytail: 부풀림은 F2.부풀(15 방향 평행이동 합) — 참 오프셋이 아니라 벽 ≥ 0.82·d − 0.3 (d_min 2.1 → ≥ 1.42). 곡면 오프셋이 필요해지면 SDF.
"""
import os, sys, json, shutil, subprocess, time
import numpy as np, manifold3d as M
_t0 = time.time()
def 때(s): print("  [%5.1f s] %s" % (time.time() - _t0, s), flush=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 소체머리3 as S
import 얼굴3_턱 as T
F3, F2, F1 = T.F3, T.F2, T.F1
from 얼굴3 import 메, 색, 멋, FRA, 틈
from 얼굴3_턱 import 돌
부풀 = F2.부풀
D6 = os.path.join(F3.ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴6A")
OUT = os.path.join(F3.ROOT, "out", "출력", "오메가몬_PG", "디자인_얼굴7"); os.makedirs(OUT, exist_ok=True)
때("import")

# ════════ 손잡이(mm) ════════
틈소체 = 0.3
d = [2.9, 2.5, 2.1]            # 마스크 미늘 1·2·3 장의 소체에서 겉까지 — 계단 0.4, 아래가 뒤
차양밑 = 278.7                  # 투구는 이 위만(눈 윗끝 278.5 바로 위)
뒤끝 = 12.0                     # 마스크가 볼 옆으로 감싸는 뒤 끝 y
# 정면 반쪽 (x, z): 윗변 = 가운데 콧등이 차양 밑까지 올라가고 눈 밑을 지나 바깥 볼에서 다시 투구에 닿음
윗변 = [(0, 278.2), (1.3, 275.9), (7.0, 275.7), (9.0, 278.6), (16.0, 278.6)]
V밑 = [[(16.0, 273.6), (0, 270.2)], [(16.0, 270.6), (0, 266.4)], [(16.0, 245.0), (0, 245.0)]]

def 띠(k):   # 정면 다각형을 y 로 뽑은 기둥(y < 뒤끝)
    P = [(-x, z) for x, z in reversed(윗변) if x] + 윗변 + V밑[k] + [(-x, z) for x, z in reversed(V밑[k]) if x]
    return M.CrossSection([P[::-1]]).extrude(60.0).rotate([90, 0, 0]).translate([0, 뒤끝, 0])

소체 = S.소체
소체틈 = 부풀(소체, 틈소체)
꽂는것 = F3.꽂는것
def 큰조각(m): return max(m.decompose(), key=lambda p: p.volume())

# ① 속머리(검) = 소체(목 기둥은 기존 목 관절이 맡음) · 눈 자리 오목
눈 = {"눈L": S.눈L, "눈R": S.눈R}
속머리 = 큰조각(소체 - T.머리막 - 꽂는것 - 눈["눈L"] - 눈["눈R"] - M.Manifold.cube([40, 40, 30]).translate([-20, 12.0, 240.0]))
# ② 마스크(흰)
마스크 = M.Manifold.batch_boolean([부풀(소체, d[k]) ^ 띠(k) for k in range(3)], M.OpType.Add) - 소체틈
마스크 = 큰조각(마스크 - T.머리막 - 꽂는것)
# 끄덕 +10° 여유: 5c 와 같이 가슴앞 · 검은 목깃을 거꾸로 돌려 쓸고 뺀다(턱 끝 밑 · 뒤통수 밑만 닿음)
몸D = os.path.join(F1.DES, "몸통"); 목상자 = M.Manifold.cube([70, 70, 70]).translate([-35, -20, 235.0])
_닿 = F2.부풀(M.Manifold.batch_boolean([F1.읽기(os.path.join(몸D, "가슴앞.stl")) ^ 목상자, F1.읽기(os.path.join(F1.DES, "돌출", "돌출03_가슴앞.stl")) ^ 목상자,
                                        F1.읽기(os.path.join(D6, "목깃안검정.stl"))], M.OpType.Add), 틈 + 0.15)
_거꾸로 = M.Manifold.batch_boolean([돌(_닿, -a) for a in np.arange(0, 10.01, 1.25)], M.OpType.Add)
마스크 = 큰조각(마스크 - _거꾸로); 속머리 = 큰조각(속머리 - _거꾸로)
때("마스크")
# ③ 투구(흰) = 6A 외형 재사용
위 = M.Manifold.cube([60, 80, 40]).translate([-30, -40, 차양밑])
마스크틈 = 부풀(마스크, 틈)
투구 = 큰조각((F1.읽기(os.path.join(D6, "투구앞.stl")) ^ 위) - 소체틈 - 마스크틈 - 꽂는것)
투구뒤 = 큰조각(F1.읽기(os.path.join(D6, "투구뒤.stl")) - 소체틈 - 마스크틈 - 부풀(투구, 틈))
때("투구")
부품 = {"속머리": (속머리, 색["검"]), **{k: (v, 색["초록"]) for k, v in 눈.items()}, "마스크": (마스크, 색["흰"]), "투구": (투구, 색["흰"]), "투구뒤": (투구뒤, 색["흰"])}
for n, c in (("뿔", "흰"), ("V안테나L", "금"), ("V안테나R", "금")): 부품[n] = (F1.읽기(os.path.join(D6, n + ".stl")), 색[c])
깃 = {n: (F1.읽기(os.path.join(D6, n + ".stl")), 색[c]) for n, c in (("목깃옆L", "흰"), ("목깃옆R", "흰"), ("목깃안검정", "검"))}

# ════════ 검사 ════════
결과 = {}
갑주 = ("마스크", "투구", "투구뒤")
결과["갑주∩소체_mm3"] = {n: round((부품[n][0] ^ 소체).volume(), 4) for n in 갑주}
print("갑주 ∩ 소체", 결과["갑주∩소체_mm3"])
assert all(v < 1e-3 for v in 결과["갑주∩소체_mm3"].values()), "갑주가 소체를 파고듦"
for n, (m, _) in 부품.items():
    assert len(m.decompose()) == 1 and 메(m).is_watertight, n + " 조각/안 닫힘"
겹 = {}
names = list(부품)
for i, a in enumerate(names):
    for b in names[i + 1:]:
        v = (부품[a][0] ^ 부품[b][0]).volume()
        if v > 0.005: 겹["%s∩%s" % (a, b)] = round(v, 3)
결과["부품겹침_mm3"] = 겹; print("부품끼리 겹침", 겹)
머리합 = M.Manifold.batch_boolean([m for n, (m, _) in 부품.items() if n not in ("뿔", "V안테나L", "V안테나R")], M.OpType.Add)
def 앞끝(m, z1, z2): return float((m ^ M.Manifold.cube([40, 80, z2 - z1]).translate([-20, -40, z1])).bounding_box()[1])
Vm = np.asarray(마스크.to_mesh().vert_properties)[:, :3]; 턱끝z = float(Vm[:, 2].min())
옆 = dict(차양=앞끝(머리합, 차양밑, 284.0), 코_마스크윗=앞끝(머리합, 273.0, 차양밑), 턱끝=앞끝(머리합, 턱끝z, 턱끝z + 2.0))
결과["옆_가장앞y"] = {k: round(v, 2) for k, v in 옆.items()}; 결과["턱끝z"] = round(턱끝z, 2)
print("옆 가장 앞 y", 결과["옆_가장앞y"], "턱 끝 z %.2f" % 턱끝z)
assert 옆["차양"] < 옆["코_마스크윗"] < 옆["턱끝"], "차양 < 코 < 턱 끝 아님"
# 마스크 벽: 앞에서 본 광선 두께(가운데 · 볼)
def 벽y(x, z):   # 앞에서 첫 조각의 y 두께
    b = min(((마스크 ^ M.Manifold.cube([0.1, 60, 0.1]).translate([x - 0.05, -30, z - 0.05])).decompose()), key=lambda q: q.bounding_box()[1]).bounding_box()
    return round(b[4] - b[1], 2)
결과["마스크_광선두께"] = {"%g,%g" % (x, z): 벽y(x, z) for x, z in ((0.5, 272), (0.5, 268), (3, 265), (6, 272), (9, 274))}
print("마스크 y 광선 두께", 결과["마스크_광선두께"])
# 턱 밑 수평면 없음(5c 와 같은 검사)
tm = 메(마스크); c = tm.triangles_center; nz = tm.face_normals[:, 2]; 턱끝y = float(Vm[Vm[:, 2] < 턱끝z + 0.3][:, 1].min())
밑 = (c[:, 2] < 턱끝z + 3) & (np.abs(c[:, 0]) < 3) & (c[:, 1] < 턱끝y + 3.0) & (nz < -0.3)
평 = float(tm.area_faces[밑 & (nz < -0.97)].sum()); 결과["턱밑수평_mm2"] = round(평, 3)
print("턱 밑 수평(<14°) 면적 %.2f mm² / 아래 보는 면 %.2f" % (평, tm.area_faces[밑].sum()))
assert 평 < 1.0, "턱 밑에 수평면"
# 끄덕 −25~+10°: 5c 와 같은 몸(목 둘레) + 6A 깃
몸 = {n[:-4]: F1.읽기(os.path.join(몸D, n)) ^ 목상자 for n in sorted(os.listdir(몸D)) if n.endswith(".stl")}
몸["돌출가슴앞"] = F1.읽기(os.path.join(F1.DES, "돌출", "돌출03_가슴앞.stl")) ^ 목상자
몸.update({k: v for k, (v, _) in 깃.items()})
몸전부 = M.Manifold.batch_boolean([v for v in 몸.values() if v.volume() > 0.01], M.OpType.Add)
머리전부 = M.Manifold.batch_boolean([m for m, _ in 부품.values()], M.OpType.Add)
결과["끄덕_겹침mm3"] = {a: round((돌(머리전부, a) ^ 몸전부).volume(), 3) for a in range(-25, 11, 5)}
print("끄덕 겹침", 결과["끄덕_겹침mm3"])
assert all(v < 0.005 for v in 결과["끄덕_겹침mm3"].values()), "끄덕 충돌"
결과["부피_mm3"] = {n: round(m.volume(), 1) for n, (m, _) in 부품.items()}
때("검사")

# ════════ 내보내기 · 렌더 ════════
for n, (m, _) in {**부품, **깃}.items(): 메(m).export(os.path.join(OUT, n + ".stl"))
json.dump(dict(설명="얼굴 7 — 소체 3 판 위 세 겹 (09-28)", 부품={n: dict(색=c) for n, (_, c) in 부품.items()}, **결과),
          open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
컷 = [("정면", 0, 0, 70.0, 280.0), ("옆", 90, 0, 70.0, 280.0), ("반옆", 62, 8, 70.0, 288.0)]
def 그림(이름, L):
    dd = os.path.join(OUT, "_그림", 이름); os.makedirs(dd, exist_ok=True); jf, pf = os.path.join(dd, "빠른.json"), os.path.join(dd, "빠른.py")
    json.dump(dict(부품=L, out=dd.replace("\\", "/"), 컷=컷), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    open(pf, "w", encoding="utf-8").write(F3.빠른.replace("line_thickness = 1.6", "line_thickness = 1.0"))
    r = subprocess.run([F1.BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    return dd
L = [(os.path.join(OUT, n + ".stl"), c) for n, (_, c) in 부품.items()]
a머리 = 그림("머리만", L)
a깃 = 그림("깃", L + [(os.path.join(OUT, n + ".stl"), c) for n, (_, c) in 깃.items()] + [(os.path.join(F1.DES, "몸통", n + ".stl"), 색["흰"]) for n in ("가슴앞", "목깃")])
때("블렌더")

from PIL import Image, ImageDraw, ImageFont
def 빠(dd, k):
    im = Image.open(os.path.join(dd, k + ".png")).convert("RGB"); w, H = im.size
    return im.crop((int(w * .2), int(H * .3), int(w * .8), int(H * .9)))
a6 = os.path.join(D6, "_그림")
참원 = Image.open(os.path.join(멋, "원화_얼굴_확대.png")).convert("RGB").crop((230, 60, 700, 660))
fra = Image.open(os.path.join(FRA, "mh_13.jpg")).transpose(Image.FLIP_LEFT_RIGHT)
줄 = [[("FRA mh_13 (뒤집음)", fra), ("6b 옆", 빠(a6, "옆")), ("7 옆", 빠(a깃, "옆"))],
      [("원화 확대", 참원), ("6b 정면", 빠(a6, "정면")), ("7 정면", 빠(a깃, "정면"))],
      [("6b 3/4", 빠(a6, "반옆")), ("7 3/4", 빠(a깃, "반옆"))],
      [("7 머리만 정면", 빠(a머리, "정면")), ("7 머리만 옆", 빠(a머리, "옆")), ("7 머리만 3/4", 빠(a머리, "반옆"))]]
f_ = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26); W, h = 1990, 560
Sh = Image.new("RGB", (W, len(줄) * (h + 45) + 10), (245, 245, 243)); dr = ImageDraw.Draw(Sh); y = 45
for 칸 in 줄:
    x = 10
    for t, im in 칸:
        im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
        if x + im.width > W: im = im.crop((0, 0, W - 10 - x, h))
        Sh.paste(im, (x, y)); dr.text((x + 6, y - 36), t, font=f_, fill=(30, 30, 30)); x += im.width + 10
    y += h + 45
p = os.path.join(멋, "얼굴7.jpg"); Sh.save(p, quality=90); print("시트", p, Sh.size)
