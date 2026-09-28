# -*- coding: utf-8 -*-
"""오메가몬 정강이 한 짝 — 디테일 네 단계를 단계마다 그림으로 (2026-09-28).

    python 정강이_단계.py  -> out/오메가몬2/정강이/단계N/*.stl · out/오메가몬2/정강이_단계.png
1 큰 덩어리(통 하나) → 2 나누기(색 경계 · 꺾임) → 3 겹치기(덧판 · 단차 · 능선) → 4 작은 것(홈 · 벤트 · 패널 선).
전부 기본 도형(소체/낱말.py). 로컬 좌표: z = 무릎 → 발목 · x = 폭 · +y = 앞.
"""
import os, sys, json, subprocess
import numpy as np, manifold3d as M
R = os.path.dirname(os.path.abspath(__file__)); 원화3d = os.path.dirname(R)
sys.path.insert(0, os.path.join(원화3d, "소체"))
from 낱말 import 뿔대, 링크, 경첩, 볼, 쐐기, _틀
from 생성기 import 블, BLENDER
from 골격들 import stl
OUT = os.path.join(원화3d, "out", "오메가몬2"); 원화 = os.path.join(os.path.dirname(원화3d), "트레일", "trail7_part3d", "in", "omega_front_clean.png")
k = 300.0 / 860.0
W = lambda px: px * k
Z = lambda py: (960 - py) * k
무릎, 발목 = np.array((W(72), -3, Z(615))), np.array((W(98), 0, Z(890))); L = float(np.linalg.norm(발목 - 무릎)); T = _틀(무릎, 발목)
흰, 검, 회 = (0.93, 0.93, 0.95), (0.10, 0.10, 0.12), (0.62, 0.64, 0.70)

def 통(t0, t1, w0, w1, d0, d1, 앞=0.0, 모=1.0):
    """링크의 t0 ~ t1 구간을 감싸는 뿔대. 폭 w · 깊이 d · 앞 = +y 로 민 양."""
    return 뿔대(w0, d0, w1, d1, (t1 - t0) * L, 모, t0 * L).translate([0, 앞, 0])
def 앞반(m, g=0.0): return m.trim_by_plane([0, 1, 0], g)
def 뒤반(m, g=0.0): return m.trim_by_plane([0, -1, 0], g)
def 상(x0, x1, y0, y1, z0, z1): return M.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])
프 = 링크((0, 0, 0), (0, 0, L), 7, 7) + 경첩((0, 0, 0), 4.2, 12) + 볼((0, 0, L), 4.5)
속 = 링크((0, 0, 0), (0, 0, L), 7, 7, 여유=0.4) + 경첩((0, 0, 0), 4.2, 12, 여유=0.4) + 볼((0, 0, L), 4.5, 여유=0.4)
# 원화 정강이 윤곽(정면 폭 px → mm): 무릎 밑 78 · 가운데 92 · 아래 118 (아래로 갈수록 빨리 벌어짐)
곡 = [(0.06, W(76)), (0.35, W(84)), (0.62, W(98)), (0.80, W(114)), (0.88, W(120))]
깊 = lambda w: 0.95 * w + 4

def 단계1():
    return {"정강이": (통(0.05, 0.95, W(78), W(118), 깊(W(78)), 깊(W(118))), 흰)}
def 단계2():
    """나누기: 앞판 · 뒤판(종아리) 을 세 마디 곡선으로 · 무릎 덮개 · 무릎 가시 · 발목 고리(검정)."""
    P = {}; 마디 = [통(a[0], b[0], a[1], b[1], 깊(a[1]), 깊(b[1])) for a, b in zip(곡[:-1], 곡[1:])]
    몸 = M.Manifold.batch_boolean(마디, M.OpType.Add)
    P["앞판"] = (앞반(몸, 0.2), 흰); P["뒤판"] = (뒤반(몸, 0.2), 흰)
    P["무릎덮개"] = (뿔대(W(60), 9, W(70), 12, 13, 1.2, -8).translate([0, 깊(W(76)) / 2 - 1, 0]), 흰)
    P["무릎가시"] = (쐐기([(-W(20), 깊(W(76)) / 2 + 1, 6), (W(20), 깊(W(76)) / 2 + 1, 6), (-W(14), 깊(W(76)) / 2 - 7, 2), (W(14), 깊(W(76)) / 2 - 7, 2)], (0, 깊(W(76)) / 2 + 3, -W(62))), 흰)
    P["발목고리"] = (통(0.89, 0.985, W(84), W(88), 깊(W(84)), 깊(W(88)), 모=2.0), 검)
    return P
def 단계3():
    """겹치기: 앞 능선 · 아랫단(한 단 두꺼운 테) · 옆 덧판 · 뒤 종아리 덧판 · 무릎 덮개 받침."""
    P = 단계2(); y앞 = lambda t: 깊(np.interp(t, [c[0] for c in 곡], [c[1] for c in 곡])) / 2
    P["앞능선"] = (M.Manifold.hull_points([(x, y앞(t) + h, t * L) for t in (0.10, 0.45, 0.78) for x, h in ((-W(9) - 4 * t, -0.5), (0, 1.6), (W(9) + 4 * t, -0.5))]), 흰)
    P["아랫단"] = (앞반(통(0.80, 0.885, W(116), W(124), 깊(W(116)) + 2, 깊(W(124)) + 2, 모=1.4) - 통(0.79, 0.90, W(112), W(118), 깊(W(112)) - 1.5, 깊(W(118)) - 1.5), 0.2), 흰)
    for s, 쪽 in ((1, "밖"), (-1, "안")):
        w = lambda t: np.interp(t, [c[0] for c in 곡], [c[1] for c in 곡]) / 2
        P["옆덧판" + 쪽] = (M.Manifold.hull_points([(s * (w(t) + e), y, t * L) for t, y0, y1 in ((0.18, -4, 5), (0.5, -6, 7), (0.72, -7, 8)) for y in (y0, y1) for e in (-0.5, 0.9)]), 회)
    P["종아리덧판"] = (M.Manifold.hull_points([(x, -y앞(t) - h, t * L) for t, ww in ((0.12, W(26)), (0.40, W(34)), (0.60, W(30))) for x, h in ((-ww, -0.4), (0, 1.4), (ww, -0.4))]), 흰)
    P["무릎받침"] = (뿔대(W(74), 5, W(80), 6, 5, 0.8, 4).translate([0, y앞(0.06) - 1.5, 0]), 회)
    return P
def 단계4():
    """작은 것: 발목 고리 홈 셋 · 옆 덧판 패널 선 · 종아리 벤트 둘 · 아랫단 가운데 V 노치 · 앞판 가로 이음 선."""
    P = 단계3(); g = lambda n, m: P.__setitem__(n, (P[n][0] - m, P[n][1]))
    for i in range(3): g("발목고리", 상(-30, 30, -30, 30, (0.905 + 0.025 * i) * L, (0.905 + 0.025 * i) * L + 0.8) - 통(0.88, 0.99, W(80), W(84), 깊(W(80)) - 1, 깊(W(84)) - 1))
    for 쪽 in ("밖", "안"): g("옆덧판" + 쪽, 상(-40, 40, -0.35, 0.35, 0.22 * L, 0.70 * L) + 상(-40, 40, -9, 9, 0.46 * L, 0.46 * L + 0.6))
    for i in range(2): g("종아리덧판", 상(-W(14), W(14), -40, -깊(W(84)) / 2 + 0.2, (0.20 + 0.05 * i) * L, (0.20 + 0.05 * i) * L + 1.6))
    g("아랫단", M.Manifold.hull_points([(-W(10), y, 0.90 * L) for y in (0, 40)] + [(W(10), y, 0.90 * L) for y in (0, 40)] + [(0, y, 0.835 * L) for y in (0, 40)]))
    g("앞판", 상(-40, 40, 깊(W(98)) / 2 - 0.5, 40, 0.615 * L, 0.615 * L + 0.6) + 상(-40, 40, 깊(W(84)) / 2 - 0.5, 40, 0.30 * L, 0.30 * L + 0.6))
    return P

if __name__ == "__main__":
    from PIL import Image, ImageDraw, ImageFont
    단계 = [("1 큰 덩어리", 단계1), ("2 나누기", 단계2), ("3 겹치기", 단계3), ("4 작은 것", 단계4)]
    G = os.path.join(OUT, "정강이", "_그림"); os.makedirs(G, exist_ok=True); 판 = []; c = (무릎 + 발목) / 2 + (0, 0, 6); 수 = []
    for i, (이름, f) in enumerate(단계, 1):
        P = {"프레임": (프, 검)}
        for n, (m, 색) in f().items():
            m = m - 속; assert not m.is_empty(), n; P[n] = (max(m.decompose(), key=lambda q: q.volume()), 색)
            assert (P[n][0] ^ 프).volume() < 1e-3, (n, "프레임 파고듦")
        D = os.path.join(OUT, "정강이", "단계%d" % i); os.makedirs(D, exist_ok=True); 수.append(len(P) - 1)
        for n, (m, 색) in P.items(): stl(m.transform(T), os.path.join(D, n + ".stl"))
        for 각, 보기 in ((0, "정면"), (-38, "반옆"), (-90, "옆")):
            Ls = []
            for j, 색 in enumerate((흰, 검, 회)):
                ms = [m for m, cc in P.values() if cc == 색]
                if ms: Ls.append((stl(M.Manifold.batch_boolean(ms, M.OpType.Add).transform(T).translate(list(-c)).rotate([0, 0, 각]).translate(list(c)), os.path.join(G, "%d_%s_%d.stl" % (i, 보기, j))), 색))
            판.append(dict(부품=Ls, 폭=135.0, 해상=(560, 800), 중심=list(map(float, c)), out=os.path.join(G, "%d_%s.png" % (i, 보기))))
    jf = os.path.join(G, "판.json"); json.dump(dict(판=판), open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    pf = os.path.join(G, "블.py"); open(pf, "w", encoding="utf-8").write(블.replace("line_thickness = 1.0", "line_thickness = 1.3"))
    r = subprocess.run([BLENDER, "-b", "-P", pf, "--", jf], capture_output=True); assert r.returncode == 0, r.stderr[-2000:]
    _a = Image.open(원화).convert("RGBA"); 원 = Image.new("RGB", _a.size, (255, 255, 255)); 원.paste(_a, mask=_a.split()[3])
    원 = 원.transform(원.size, Image.AFFINE, (1, 0, 537 - 512, 0, 1, 0), fillcolor=(255, 255, 255)).transpose(Image.FLIP_LEFT_RIGHT)
    px = 135.0 / 800 / k; cx, cy = 512 + c[0] / k, 960 - c[2] / k      # 렌더 1 px = 원화 px 몇
    원 = 원.crop((int(cx - 280 * px), int(cy - 400 * px), int(cx + 280 * px), int(cy + 400 * px))).resize((560, 800), Image.LANCZOS)
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 28); S = Image.new("RGB", (5 * 570 + 10, 3 * 850 + 10), (245, 245, 243)); d = ImageDraw.Draw(S)
    for r_, 보기 in enumerate(("정면", "반옆", "옆")):
        y = 10 + r_ * 850
        if r_ == 0: S.paste(원, (10, y + 44)); d.text((16, y + 6), "원화(같은 축척)", font=ft, fill=(20, 20, 20))
        for i, (이름, _) in enumerate(단계, 1):
            x = 10 + i * 570; S.paste(Image.open(os.path.join(G, "%d_%s.png" % (i, 보기))).convert("RGB"), (x, y + 44))
            d.text((x + 6, y + 6), "%s · %s · 부품 %d" % (이름, 보기, 수[i - 1]), font=ft, fill=(20, 20, 20))
    p = os.path.join(OUT, "정강이_단계.png"); S.save(p); print("부품 수", 수); print("시트", p, S.size)
