# -*- coding: utf-8 -*-
"""합성 복잡 도형 — CAD 로 바탕 + 연산 3~8 · 입력(실물보기 128 · 3D 학생 꼴 3×3×128²)과 정답 점유 64³ · 판정기준24 · 10-12
python 합성.py 조각 <k> [개수=250]   → 합성/k.npz (X float16 (n,3,3,128,128) · Y packbits · 이름)
python 합성.py 모음                  → 합성.npz (조각 모두)
python 합성.py 보기 <k>              → 합성/k.png (처음 16 개 렌더)"""
import os, sys, glob, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(R, "조각0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub"), H]
O = os.path.join(H, "합성"); 씨 = 20261024

def 도형(rng):
    import cadquery as cq
    V = cq.Vector; u = lambda a, b: float(rng.uniform(a, b))
    def 원기둥(r, h, p, d): return cq.Workplane().add(cq.Solid.makeCylinder(r, h, V(*p), V(*d)))
    def 상자(x, y, z, p): return cq.Workplane().add(cq.Solid.makeBox(x, y, z, V(*p)))
    def 기운방향():
        d = np.zeros(3); d[rng.integers(3)] = 1; d += rng.normal(0, .35, 3); return d / np.linalg.norm(d)
    종 = rng.choice(["상자", "상자", "원기둥", "기운원기둥", "쐐기", "회전체"])
    if 종 == "상자": s = 상자(u(30, 70), u(30, 70), u(30, 70), (0, 0, 0))
    elif 종 == "원기둥": d = [0, 0, 0]; d[rng.integers(3)] = 1; h = u(30, 80); s = 원기둥(u(12, 30), h, [-h / 2 * x for x in d], d)
    elif 종 == "기운원기둥": d = 기운방향(); h = u(40, 80); s = 원기둥(u(10, 25), h, list(-d * h / 2), list(d))
    elif 종 == "쐐기":
        a, b, c = u(30, 70), u(30, 70), u(20, 60); t = u(.1, .6)
        s = cq.Workplane("XY").polyline([(0, 0), (a, 0), (a, b * t), (0, b)]).close().extrude(c)
    else:
        n = rng.integers(3, 7); zs = np.sort(rng.uniform(0, 70, n)); zs[0], zs[-1] = 0, max(zs[-1], 30); rs = rng.uniform(6, 28, n)
        s = cq.Workplane("XZ").polyline([(0, 0)] + [(float(r), float(z)) for r, z in zip(rs, zs)] + [(0, float(zs[-1]))]).close().revolve(360, (0, 0, 0), (0, 1, 0))
    한 = []
    for _ in range(rng.integers(3, 9)):
        bb = s.val().BoundingBox(); lo = np.array([bb.xmin, bb.ymin, bb.zmin]); hi = np.array([bb.xmax, bb.ymax, bb.zmax]); L = hi - lo
        연 = rng.choice(["단차", "포켓", "구멍", "필렛", "모따기", "공", "기운돌기", "패널홈", "덧상자"]); ax = int(rng.integers(3)); 쪽 = int(rng.integers(2))
        try:
            if 연 in ("단차", "포켓", "패널홈", "덧상자"):
                w = L * np.array([u(.2, .6), u(.2, .6), u(.2, .6)]); p = lo + (L - w) * rng.uniform(0, 1, 3)
                if 연 == "단차": p = np.where(rng.random(3) < .5, lo - 1, hi - w + 1); p[ax] = (hi[ax] - w[ax] * .5) if 쪽 else (lo[ax] - w[ax] * .5)
                if 연 == "포켓": w[ax] = L[ax] * u(.1, .35); p[ax] = hi[ax] - w[ax] if 쪽 else lo[ax]
                if 연 == "패널홈": o = [j for j in range(3) if j != ax]; w[o[rng.integers(2)]] = max(L.min() * u(.03, .07), .8); w[ax] = L[ax] * u(.04, .1); p[ax] = hi[ax] - w[ax] if 쪽 else lo[ax]
                if 연 == "덧상자": w[ax] = L[ax] * u(.1, .3); p[ax] = hi[ax] - w[ax] * .3 if 쪽 else lo[ax] - w[ax] * .7
                t = 상자(*w, tuple(p)); s2 = s.union(t) if 연 == "덧상자" else s.cut(t)
            elif 연 == "구멍":
                o = [j for j in range(3) if j != ax]; c = lo + L * rng.uniform(.3, .7, 3); r = min(L[o]) * u(.08, .25); d = [0, 0, 0]; d[ax] = 1; c[ax] = lo[ax] - 5
                s2 = s.cut(원기둥(r, L[ax] + 10, list(c), d))
            elif 연 in ("필렛", "모따기"):
                sel = rng.choice(["|X", "|Y", "|Z", ">Z", "<Z", ">X", "<Y"]); r = float(L.min() * u(.04, .15))
                s2 = s.edges(sel).fillet(r) if 연 == "필렛" else s.edges(sel).chamfer(r)
            elif 연 == "공":
                c = (lo + hi) / 2; c[ax] = hi[ax] if 쪽 else lo[ax]; r = L.min() * u(.15, .3); d = np.zeros(3); d[ax] = 1 if 쪽 else -1
                s2 = s.union(원기둥(r * .45, r * 1.3, list(c - d * r * .3), list(d))).union(cq.Workplane().add(cq.Solid.makeSphere(r, V(*(c + d * r * 1.2)), angleDegrees1=-90)))
            else:
                c = lo + L * rng.uniform(.3, .7, 3); d = 기운방향(); r = L.min() * u(.08, .2); h = L.max() * u(.4, .8)
                s2 = s.union(원기둥(r, h, list(c), list(d)) if rng.random() < .6 else cq.Workplane().add(cq.Solid.makeCone(r, r * u(.2, .7), h, V(*c), V(*d))))
            v = s2.val()
            if v.isValid() and v.Volume() > .05 * s.val().Volume(): s = s2; 한.append(연)
        except Exception: pass
    return s, 종 + ":" + ",".join(한)

def 메시(s):
    import trimesh
    v, f = s.val().tessellate(.2, .3); return trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in v]), np.array(f))

def 하나(rng):
    import trimesh
    from s0 import unit
    from 실물보기 import 실물보기
    from 모양자 import _occ, _닫힘
    from 준비 import 선, 교차깊이
    from 부피학생 import 입력, n
    s, 이름 = 도형(rng); m = unit(메시(s))
    if not _닫힘(m) or len(m.faces) < 12: return None
    S, D = 실물보기(m, 128); X = np.stack([S, 선(S, D), 교차깊이(S), D]).astype(np.float32)
    g = (np.indices((n, n, n)).reshape(3, -1).T + .5) / n; Y = _occ(m, g)
    if Y.mean() < .01: return None
    return 입력(X).astype(np.float16), np.packbits(Y), 이름, m

if __name__ == "__main__":
    os.makedirs(O, exist_ok=True)
    if sys.argv[1] == "조각":
        k = int(sys.argv[2]); N = int(sys.argv[3]) if len(sys.argv) > 3 else 250; rng = np.random.default_rng([씨, k]); X, Y, 이 = [], [], []
        while len(X) < N:
            r = 하나(rng)
            if r: X.append(r[0]); Y.append(r[1]); 이.append(r[2])
        np.savez(os.path.join(O, "%03d.npz" % k), X=np.stack(X), Y=np.stack(Y), 이름=np.array(이)); print("ok", k, len(X), flush=True)
    elif sys.argv[1] == "모음":
        fs = sorted(glob.glob(os.path.join(O, "*.npz"))); d = [np.load(f) for f in fs]
        np.save(os.path.join(H, "합성X.npy"), np.concatenate([q["X"] for q in d])); np.save(os.path.join(H, "합성Y.npy"), np.concatenate([q["Y"] for q in d])); print("ok", sum(len(q["X"]) for q in d))
    elif sys.argv[1] == "보기":   # 처음 16 개 렌더 — 눈으로 먼저 본다
        from render import render
        from PIL import Image, ImageDraw, ImageFont
        rng = np.random.default_rng([씨, int(sys.argv[2])]); im = Image.new("RGB", (4 * 220, 4 * 240), "white"); dr = ImageDraw.Draw(im); F = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 12); j = 0
        while j < 16:
            r = 하나(rng)
            if not r: continue
            m = r[3]; im.paste(Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), [1, .6, .8], img_size=220))), ((j % 4) * 220, (j // 4) * 240 + 20)); dr.text(((j % 4) * 220 + 4, (j // 4) * 240 + 4), r[2][:40], font=F, fill="black"); j += 1
        im.save(os.path.join(O, "보기.png")); print("ok")
