# -*- coding: utf-8 -*-
"""오메가몬 PG — 부위 스크립트가 같이 쓰는 것 (2026-09-28). 방법: 지식/부위/정강이.md · 지식/규칙/윤곽은-원화-단면으로-짓는다.md

  좌표   원화 px → mm: X(px) · Z(py) · 1 px = k mm. **뒤집지 않는다**: 그림 오른쪽 = +x · 앞 = −y · 위 = +z.
  격자   격자(이름, (x0, y0, x1, y1), 배=3) → out/오메가몬2/_격자/이름.png — 원화를 확대 + px 격자. 단면을 읽기 전에 먼저 본다.
  도형   단면 · 마디(원화 단면표를 이은 볼록 마디) · 기둥(정면 px 다각형을 앞뒤로 민 볼록 판) · 상 · 띠 + 소체/낱말.py
  그림   단계시트(이름, 단계들, 프레임, 속, 중심px, 높이mm) → 부품 STL + 단계마다 정면 · 3/4 · 옆 + 원화 크롭 · 겹침
"""
import os, sys, json, subprocess
import numpy as np, manifold3d as M
R = os.path.dirname(os.path.abspath(__file__)); 원화3d = os.path.dirname(R)
sys.path.insert(0, os.path.join(원화3d, "소체"))
from 낱말 import 링크, 경첩, 볼, 쐐기, 뿔대, 덧판      # noqa: F401 (부위 스크립트가 여기서 가져간다)
from 생성기 import 블, BLENDER
from 골격들 import stl
OUT = os.path.join(원화3d, "out", "오메가몬2"); 원화 = os.path.join(os.path.dirname(원화3d), "트레일", "trail7_part3d", "in", "omega_front_clean.png")
k = 300.0 / 860.0                      # 키 300 mm = 돔(py 100) … 발바닥(py 960)
가운데 = 537
X = lambda px: (px - 가운데) * k
Z = lambda py: (960 - py) * k
흰, 검, 회, 파랑, 주황, 금, 빨강, 은 = (0.93, 0.93, 0.95), (0.10, 0.10, 0.12), (0.70, 0.72, 0.78), (0.42, 0.44, 0.72), (0.95, 0.55, 0.15), (0.85, 0.68, 0.2), (0.75, 0.15, 0.12), (0.75, 0.78, 0.82)
색들 = (흰, 검, 회, 파랑, 주황, 금, 빨강, 은)

def 원화그림():
    from PIL import Image
    a = Image.open(원화).convert("RGBA"); w = Image.new("RGB", a.size, (255, 255, 255)); w.paste(a, mask=a.split()[3]); return w
def 격자(이름, 상자px, 배=3, 간격=20):
    from PIL import ImageDraw
    x0, y0, x1, y1 = 상자px; c = 원화그림().crop(상자px); c = c.resize((c.width * 배, c.height * 배)); d = ImageDraw.Draw(c)
    for y in range(y0 - y0 % 간격 + 간격, y1, 간격): d.line([(0, (y - y0) * 배), (c.width, (y - y0) * 배)], fill=(255, 0, 0) if y % 100 == 0 else (255, 180, 180)); d.text((2, (y - y0) * 배 + 1), str(y), fill=(200, 0, 0))
    for x in range(x0 - x0 % 간격 + 간격, x1, 간격): d.line([((x - x0) * 배, 0), ((x - x0) * 배, c.height)], fill=(0, 0, 255) if x % 100 == 0 else (180, 180, 255)); d.text(((x - x0) * 배 + 1, 2), str(x), fill=(0, 0, 200))
    p = os.path.join(OUT, "_격자"); os.makedirs(p, exist_ok=True); p = os.path.join(p, 이름 + ".png"); c.save(p); return p

# ── 도형 ──
def 단면(py, xl, xr, 능, 깊, 불=0.0, 깊이비=0.92, 밀=0.0, 각=0.8):
    """z = Z(py) 의 볼록 단면: 둥근 통(점 24 · 각 = 1 이면 타원, 작을수록 네모) + 앞 능선 한 점(능 = px). 깊 = 깊이 배 · 밀 = 앞뒤로 민 양(mm) · 불 = 부풀림(mm)."""
    w = (xr - xl) * k; d = 깊이비 * w * 깊; cx = (X(xl) + X(xr)) / 2; rx, ry = w / 2 + 불, d / 2 + 불
    P = [(cx + rx * np.sign(np.cos(t)) * abs(np.cos(t)) ** 각, 밀 + ry * np.sign(np.sin(t)) * abs(np.sin(t)) ** 각 * (0.9 if np.sin(t) < 0 else 1.0), Z(py)) for t in np.linspace(0, 2 * np.pi, 24, endpoint=False)]
    return P + [(X(능), 밀 - d / 2 - 불, Z(py))]
def 마디(표, 불=0.0, **kw):
    """단면표 [(py, 안 px, 밖 px, 능선 px, 깊이 배), …] 를 위에서 아래로 이은 볼록 마디들의 합."""
    return M.Manifold.batch_boolean([M.Manifold.hull_points(단면(*a, 불=불, **kw) + 단면(*b, 불=불, **kw)) for a, b in zip(표[:-1], 표[1:])], M.OpType.Add)
def 앞y(표, py, 깊이비=0.92, 밀=0.0):
    """단면표의 py 높이에서 앞 능선의 y(mm)."""
    i = np.interp(py, [s[0] for s in 표], range(len(표))); a = 표[int(np.floor(i))]; b = 표[int(np.ceil(i))]; t = i - np.floor(i)
    return 밀 - 깊이비 / 2 * ((a[2] - a[1]) * a[4] * (1 - t) + (b[2] - b[1]) * b[4] * t) * k
def 기둥(점px, y0, y1):
    """정면 px 다각형(볼록)을 y0 … y1 (mm) 로 민 판 · 덩어리."""
    return M.Manifold.hull_points([(X(px), y, Z(py)) for px, py in 점px for y in (y0, y1)])
def 상(x0, x1, y0, y1, z0, z1): return M.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])
def 띠(P, y면, 굵=1.6, 돋=0.8):
    """정면 px 꺾은선 P 를 따라 얹는 가는 띠. y면(py) = 그 높이의 앞면 y 를 주는 함수(또는 수)."""
    f = y면 if callable(y면) else (lambda py: y면)
    점 = lambda px, py: [(X(px) + dx, f(py) + dy, Z(py) + dz) for dx in (-굵 / 2, 굵 / 2) for dz in (-굵 / 2, 굵 / 2) for dy in (-돋, 6)]
    return M.Manifold.batch_boolean([M.Manifold.hull_points(점(*a) + 점(*b)) for a, b in zip(P[:-1], P[1:])], M.OpType.Add)
def 거울(m): return m.mirror([1, 0, 0])

# ── 검사 + 그림 ──
def 단계시트(이름, 단계, 프, 속, 중심px, 높이=135.0, 반옆각=38):
    """단계 = [("1 큰 덩어리", 함수), …] · 함수는 {부품 이름: (도형, 색)} 을 돌려준다. 프 = 프레임 · 속 = 프레임 + 틈 0.4(갑주에서 파냄).
    부품마다 프레임을 파내고 · 조각나면 가장 큰 것 · 겹치면 나중 부품에서 뺀다 · 프레임 파고듦 0 을 assert. 그림: out/오메가몬2/<이름>_단계.png"""
    from PIL import Image, ImageDraw, ImageFont
    G = os.path.join(OUT, 이름, "_그림"); os.makedirs(G, exist_ok=True); 판 = []; 수 = []
    c = np.array((X(중심px[0]), 0.0, Z(중심px[1])))
    for i, (제목, f) in enumerate(단계, 1):
        P = {"프레임": (프, 검)}
        for n, (m, 색) in f().items():
            m = m - 속; assert not m.is_empty(), n; P[n] = (max(m.decompose(), key=lambda q: q.volume()), 색)
            assert (P[n][0] ^ 프).volume() < 1e-3, (n, "프레임 파고듦")
        ns = [n for n in P if n != "프레임"]
        for a in range(len(ns)):
            for b in ns[a + 1:]:
                if (P[ns[a]][0] ^ P[b][0]).volume() > 0.5: P[b] = (max((P[b][0] - P[ns[a]][0]).decompose(), key=lambda q: q.volume()), P[b][1])
        D = os.path.join(OUT, 이름, "단계%d" % i); os.makedirs(D, exist_ok=True); 수.append(len(P) - 1)
        for f_ in os.listdir(D): os.remove(os.path.join(D, f_))
        for n, (m, 색) in P.items(): stl(m, os.path.join(D, n + ".stl"))
        json.dump({n: list(색) for n, (m, 색) in P.items()}, open(os.path.join(D, "색.json"), "w", encoding="utf-8"), ensure_ascii=False)
        for 각, 보기 in ((0, "정면"), (반옆각, "반옆"), (90, "옆")):
            Ls = []
            for j, 색 in enumerate(색들):
                ms = [m for m, cc in P.values() if cc == 색]
                if ms: Ls.append((stl(M.Manifold.batch_boolean(ms, M.OpType.Add).translate(list(-c)).rotate([0, 0, 각]).translate(list(c)), os.path.join(G, "%d_%s_%d.stl" % (i, 보기, j))), 색))
            판.append(dict(부품=Ls, 폭=높이, 해상=(560, 800), 중심=list(map(float, c)), out=os.path.join(G, "%d_%s.png" % (i, 보기))))
    jf = os.path.join(G, "판.json"); json.dump(dict(판=판), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    pf = os.path.join(G, "블.py"); open(pf, "w", encoding="utf-8").write(블.replace("line_thickness = 1.0", "line_thickness = 1.3"))
    r = subprocess.run([BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    px = 높이 / 800 / k; cx, cy = 중심px
    원 = 원화그림().crop((int(cx - 280 * px), int(cy - 400 * px), int(cx + 280 * px), int(cy + 400 * px))).resize((560, 800), Image.LANCZOS)
    n = len(단계); ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 28); S = Image.new("RGB", ((n + 1) * 570 + 10, 3 * 850 + 10), (245, 245, 243)); d = ImageDraw.Draw(S)
    for r_, 보기 in enumerate(("정면", "반옆", "옆")):
        y = 10 + r_ * 850
        if r_ == 0: S.paste(원, (10, y + 44)); d.text((16, y + 6), "원화(같은 축척)", font=ft, fill=(20, 20, 20))
        if r_ == 1: S.paste(Image.blend(원, Image.open(os.path.join(G, "%d_정면.png" % n)).convert("RGB"), 0.5), (10, y + 44)); d.text((16, y + 6), "원화 + %d 단계 겹침" % n, font=ft, fill=(20, 20, 20))
        for i, (제목, _) in enumerate(단계, 1):
            x = 10 + i * 570; S.paste(Image.open(os.path.join(G, "%d_%s.png" % (i, 보기))).convert("RGB"), (x, y + 44))
            d.text((x + 6, y + 6), "%s · %s · 부품 %d" % (제목, 보기, 수[i - 1]), font=ft, fill=(20, 20, 20))
    p = os.path.join(OUT, 이름 + "_단계.png"); S.save(p); print("부품 수", 수); print("시트", p, S.size); return p
