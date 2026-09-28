# -*- coding: utf-8 -*-
"""오메가몬 정강이 한 짝 — 디테일 네 단계, 2 판 (2026-09-28).

    python 정강이_단계.py  -> out/오메가몬2/정강이/단계N/*.stl · out/오메가몬2/정강이_단계.png
1 판(종 모양 통 + 일반 메카 패널 선)은 「개판」. 2 판은 **원화에 실제로 있는 것만** 짓는다:
  윤곽 = 원화 px 단면 8 개를 이은 마디(무릎 밑 부풂 → 가운데 조임 → 바깥으로만 벌어짐) · 앞 능선 = 원화의 세로 꺾임 선
  특징 = 무릎 V 홈과 거기 꽂히는 허벅지 끝 · V 홈 테 · 발목 단(테) · 검은 발목 · 안쪽 복사뼈 덮개
전부 기본 도형(볼록 마디 · 쐐기 · 상자). 세계 좌표 · 앞 = −y · 원화의 그림 오른쪽 다리(뒤집지 않음).
"""
import os, sys, json, subprocess
import numpy as np, manifold3d as M
R = os.path.dirname(os.path.abspath(__file__)); 원화3d = os.path.dirname(R)
sys.path.insert(0, os.path.join(원화3d, "소체"))
from 낱말 import 링크, 경첩, 볼
from 생성기 import 블, BLENDER
from 골격들 import stl
OUT = os.path.join(원화3d, "out", "오메가몬2"); 원화 = os.path.join(os.path.dirname(원화3d), "트레일", "trail7_part3d", "in", "omega_front_clean.png")
k = 300.0 / 860.0
X = lambda px: (px - 537) * k
Z = lambda py: (960 - py) * k
흰, 검, 회 = (0.93, 0.93, 0.95), (0.10, 0.10, 0.12), (0.70, 0.72, 0.78)
무릎, 발목 = (X(615), 1, Z(603)), (X(640), 2, Z(886))

# 원화 단면: py · 왼쪽(안) px · 오른쪽(밖) px · 앞 능선 px · 깊이 배(종아리가 뒤로 부풂)
단면표 = [(608, 582, 650, 630, 1.00), (630, 574, 657, 633, 1.08), (655, 569, 660, 636, 1.15), (700, 584, 656, 638, 1.05),
          (745, 595, 660, 640, 0.98), (790, 599, 668, 647, 0.98), (830, 600, 686, 655, 1.00), (850, 600, 695, 658, 1.02)]
def 단면(py, xl, xr, 능, 깊, 불=0.0):
    """z = Z(py) 의 볼록 단면 — 둥근 통(점 24) + 앞 능선 한 점. 매끈하게 읽히도록 각을 잘게. 불 = 바깥으로 부풀림(mm)."""
    w = (xr - xl) * k; d = 0.92 * w * 깊; cx = (X(xl) + X(xr)) / 2; rx, ry = w / 2 + 불, d / 2 + 불
    P = [(cx + rx * np.sign(np.cos(t)) * abs(np.cos(t)) ** 0.8, ry * np.sign(np.sin(t)) * abs(np.sin(t)) ** 0.8 * (0.9 if np.sin(t) < 0 else 1.0), Z(py)) for t in np.linspace(0, 2 * np.pi, 24, endpoint=False)]
    return P + [(X(능), -d / 2 - 불, Z(py))]
def 마디(표, 불=0.0):
    return M.Manifold.batch_boolean([M.Manifold.hull_points(단면(*a, 불=불) + 단면(*b, 불=불)) for a, b in zip(표[:-1], 표[1:])], M.OpType.Add)
def 앞y(py):   # 능선의 앞면 y
    i = np.interp(py, [s[0] for s in 단면표], range(len(단면표))); a = 단면표[int(np.floor(i))]; b = 단면표[int(np.ceil(i))]; t = i - np.floor(i)
    return -0.46 * ((a[2] - a[1]) * a[4] * (1 - t) + (b[2] - b[1]) * b[4] * t) * k
def 상(x0, x1, y0, y1, z0, z1): return M.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])
def 띠(P, 굵=1.6, 돋=0.8):
    """정면 px 꺾은선 P 를 따라 앞면에 얹는 가는 띠."""
    점 = lambda px, py: [(X(px) + dx, 앞y(py) + dy, Z(py) + dz) for dx in (-굵 / 2, 굵 / 2) for dz in (-굵 / 2, 굵 / 2) for dy in (-돋, 6)]
    return M.Manifold.batch_boolean([M.Manifold.hull_points(점(*a) + 점(*b)) for a, b in zip(P[:-1], P[1:])], M.OpType.Add)

프 = 링크(무릎, 발목, 7, 7) + 경첩(무릎, 4.2, 12) + 볼(발목, 4.5)
속 = 링크(무릎, 발목, 7, 7, 여유=0.4) + 경첩(무릎, 4.2, 12, 여유=0.4) + 볼(발목, 4.5, 여유=0.4)
V = [(585, 606), (658, 606), (630, 648)]                       # 무릎 V 홈(정면 px): 윗변 둘 · 꼭짓점
V홈 = M.Manifold.hull_points([(X(px), y, Z(py)) for px, py in V + [(585, 590), (658, 590)] for y in (-40, 앞y(630) + 5.0)])
허벅지끝 = M.Manifold.hull_points([(X(px), y, Z(py)) for px, py in ((589, 588), (654, 588), (589, 607), (654, 607), (630, 643)) for y in (앞y(630) - 1.2, 앞y(630) + 4.4)])
몸통 = 마디(단면표)
아치 = M.Manifold.cylinder(40, 1, 1, 48).scale([46 * k, 58 * k, 1]).rotate([90, 0, 0]).translate([X(650), 0, Z(902)])     # 발등 위로 파인 아치(앞쪽만) — 원화의 발목 단 곡선

def 단계1(): return {"정강이": (몸통, 흰)}
def 단계2():
    """나누기 — 원화의 부품 경계: 무릎 V 홈 + 허벅지 끝 · 발목 단 · 검은 발목 · 안쪽 복사뼈 덮개."""
    P = {"정강이": (마디(단면표[:-1] + [(838, 600, 690, 656, 1.0)]) - V홈 - 아치, 흰), "허벅지끝": (허벅지끝, 흰)}
    P["발목단"] = (마디([(832, 598, 690, 656, 1.0), (872, 598, 705, 660, 1.02)], 불=0.9) - 아치.scale([1, 1, 1]).translate([0, 0, -2.2]), 흰)
    P["검은발목"] = (마디([(866, 604, 694, 658, 0.95), (892, 610, 684, 655, 0.9)]), 검)
    P["복사뼈덮개"] = (M.Manifold.hull_points([(X(px), y, Z(py)) for px, py in ((600, 866), (640, 872), (644, 906), (612, 914), (600, 900)) for y in (-11, 5)]), 흰)
    return P
def 단계3():
    """겹치기 — 원화의 겹 선: V 홈을 따라 도는 테(두 줄 선) · 발목 아치를 따라 도는 회색 테."""
    P = 단계2()
    P["V테"] = (띠([(583, 612), (630, 654), (660, 612)], 2.0, 0.9) - V홈, 흰)
    P["발목덧단"] = ((마디([(820, 599, 683, 654, 1.0), (872, 598, 705, 660, 1.02)], 불=1.5) ^ 아치.translate([0, 0, 1.6])) - 아치.translate([0, 0, -2.2]) - 상(-100, 100, 0, 100, 0, 400), 회)
    return P
def 단계4():
    """작은 것 — 원화에는 거의 없다. 키트 문법에서 둘만: 앞뒤 반쪽 이음 홈 · 복사뼈 덮개 핀 자국. 큰 면은 비운다."""
    P = 단계3(); g = lambda n, m: P.__setitem__(n, (P[n][0] - m, P[n][1]))
    이음 = 마디(단면표, 불=0.5) - 마디(단면표, 불=-0.45)
    g("정강이", (이음 ^ 상(-100, 100, 1.2, 1.9, 0, 400)))
    g("복사뼈덮개", M.Manifold.cylinder(3, 1.3, 1.3, 24).rotate([90, 0, 0]).translate([X(622), -9.0, Z(890)]))
    return P

if __name__ == "__main__":
    from PIL import Image, ImageDraw, ImageFont
    단계 = [("1 큰 덩어리", 단계1), ("2 나누기", 단계2), ("3 겹치기", 단계3), ("4 작은 것", 단계4)]
    G = os.path.join(OUT, "정강이", "_그림"); os.makedirs(G, exist_ok=True); 판 = []; c = np.array((X(632), 0.0, Z(750))); 수 = []; 높 = 135.0
    for i, (이름, f) in enumerate(단계, 1):
        P = {"프레임": (프, 검)}
        for n, (m, 색) in f().items():
            m = m - 속; assert not m.is_empty(), n; P[n] = (max(m.decompose(), key=lambda q: q.volume()), 색)
            assert (P[n][0] ^ 프).volume() < 1e-3, (n, "프레임 파고듦")
        ns = [n for n in P if n != "프레임"]
        for a in range(len(ns)):
            for b in ns[a + 1:]:
                v = (P[ns[a]][0] ^ P[b][0]).volume()
                if v > 0.5: P[b] = (max((P[b][0] - P[ns[a]][0]).decompose(), key=lambda q: q.volume()), P[b][1])     # 겹치면 나중 부품에서 뺀다
        D = os.path.join(OUT, "정강이", "단계%d" % i); os.makedirs(D, exist_ok=True); 수.append(len(P) - 1)
        for f_ in os.listdir(D): os.remove(os.path.join(D, f_))
        for n, (m, 색) in P.items(): stl(m, os.path.join(D, n + ".stl"))
        for 각, 보기 in ((0, "정면"), (38, "반옆"), (90, "옆")):
            Ls = []
            for j, 색 in enumerate((흰, 검, 회)):
                ms = [m for m, cc in P.values() if cc == 색]
                if ms: Ls.append((stl(M.Manifold.batch_boolean(ms, M.OpType.Add).translate(list(-c)).rotate([0, 0, 각]).translate(list(c)), os.path.join(G, "%d_%s_%d.stl" % (i, 보기, j))), 색))
            판.append(dict(부품=Ls, 폭=높, 해상=(560, 800), 중심=list(map(float, c)), out=os.path.join(G, "%d_%s.png" % (i, 보기))))
    jf = os.path.join(G, "판.json"); json.dump(dict(판=판), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    pf = os.path.join(G, "블.py"); open(pf, "w", encoding="utf-8").write(블.replace("line_thickness = 1.0", "line_thickness = 1.3"))
    r = subprocess.run([BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    _a = Image.open(원화).convert("RGBA"); 원 = Image.new("RGB", _a.size, (255, 255, 255)); 원.paste(_a, mask=_a.split()[3])
    px = 높 / 800 / k; cx, cy = 537 + c[0] / k, 960 - c[2] / k
    원 = 원.crop((int(cx - 280 * px), int(cy - 400 * px), int(cx + 280 * px), int(cy + 400 * px))).resize((560, 800), Image.LANCZOS)
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 28); S = Image.new("RGB", (5 * 570 + 10, 3 * 850 + 10), (245, 245, 243)); d = ImageDraw.Draw(S)
    for r_, 보기 in enumerate(("정면", "반옆", "옆")):
        y = 10 + r_ * 850
        if r_ == 0: S.paste(원, (10, y + 44)); d.text((16, y + 6), "원화(같은 축척)", font=ft, fill=(20, 20, 20))
        if r_ == 1:
            겹 = Image.blend(원, Image.open(os.path.join(G, "4_정면.png")).convert("RGB"), 0.5); S.paste(겹, (10, y + 44)); d.text((16, y + 6), "원화 + 4 단계 겹침", font=ft, fill=(20, 20, 20))
        for i, (이름, _) in enumerate(단계, 1):
            x = 10 + i * 570; S.paste(Image.open(os.path.join(G, "%d_%s.png" % (i, 보기))).convert("RGB"), (x, y + 44))
            d.text((x + 6, y + 6), "%s · %s · 부품 %d" % (이름, 보기, 수[i - 1]), font=ft, fill=(20, 20, 20))
    p = os.path.join(OUT, "정강이_단계.png"); S.save(p); print("부품 수", 수); print("시트", p, S.size)
