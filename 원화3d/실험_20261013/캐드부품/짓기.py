# 로드맵 2 — 지도(0 바깥 · 1 윗면 · 2 관통 · 3 들어감 + 깊이 비율) → CadQuery: 바깥 윤곽을 높이 H 로 밀고 · 관통은 뚫고 · 들어감은 깊이 층(0.1 단위)마다 덩어리째 깎음 · 부피 IoU(48³) · 10-13
import numpy as np, cv2
N = 128; 칸 = 1.1 / N
def 화(x, y): return (-.55 + (x + .5) * 칸, .55 - (y + .5) * 칸)   # 화소 → 세계(데이터.py 의 광선 격자와 같음)
def 꼬임(q):   # 닫힌 다각형의 변끼리 건너는 곳 수 — 0 이어야 CAD 면이 된다(기능0/도구.py 와 같음 · 꼬인 윤곽은 OCC 불리언이 메모리를 끝없이 잡음 10-11)
    n = len(q); o = lambda u, v, w: (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    return sum(o(q[i], q[(i + 1) % n], q[j]) * o(q[i], q[(i + 1) % n], q[(j + 1) % n]) < 0 and o(q[j], q[(j + 1) % n], q[i]) * o(q[j], q[(j + 1) % n], q[(i + 1) % n]) < 0
               for i in range(n) for j in range(i + 2, n) if not (i == 0 and j == n - 1))
def 면유효(q):   # 판정기준44 — 꼬임 검사는 변이 「건너는」 것만 센다 · 꼭짓점이 다른 변에 「닿는」 다각형(787 번)도 OCC 면이 무효 → 깎는 도구가 깨지고 칸이 틀 밖으로 튐 · OCC 에 직접 묻는다
    import cadquery as cq
    try: return cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(x, y, 0) for x, y in q], close=True)).isValid()
    except Exception: return False
def 다각(mask):
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); out = []
    for c in cs:
        if cv2.contourArea(c) < 3: continue
        for e in (.8, .5, .3, 1.2, 2, 3):   # 꼬이면 버리지 않고 줄임 정도를 바꿔 다시(판정기준32) — 0.8 에서 되던 것은 그대로
            p = cv2.approxPolyDP(c, e, True)[:, 0, :]
            if 3 <= len(p) <= 200:
                q = [화(x, y) for x, y in p]
                if not 꼬임(q) and 면유효(q): out.append(q); break   # 끝까지 꼬이거나 꼭짓점 200 넘으면 버림
    return out
def 몸통53(그림, H):   # 판정기준33 — 몸통은 53 편 윤곽바탕(그림 물붓기 · 가장 큰 바깥 윤곽 · 원 판정 · 1.5 줄이기) · → (고체, 경로)
    import sys, cadquery as cq
    sys.path.insert(0, "G:/art2real/원화3d/실험_20261013/구멍"); import 윤곽바탕 as W
    _, c = W.바깥(그림); f = W.맞추기(c)
    if f[0] == "원": (x, y), r = f[1], f[2]; cx, cy = 화(x, y); return cq.Workplane("XY").center(cx, cy).circle(r * 칸).extrude(H).translate((0, 0, -H / 2)), "원"
    for i, e in enumerate((1.5, 1.0, .5, 2.5, 4)):   # 꼬이면 줄임 정도를 바꿔 다시 — 끝까지 꼬이면 볼록 껍질(경로를 세어 찍는다)
        p = cv2.approxPolyDP(c.reshape(-1, 1, 2).astype(np.float32), e, True)[:, 0, :]; q = [화(x, y) for x, y in p]
        if 3 <= len(q) <= 300 and not 꼬임(q): return cq.Workplane("XY").polyline(q).close().extrude(H).translate((0, 0, -H / 2)), "다각" if i == 0 else "다시 줄임"
    q = [화(x, y) for x, y in cv2.convexHull(c.astype(np.float32))[:, 0, :]]; return cq.Workplane("XY").polyline(q).close().extrude(H).translate((0, 0, -H / 2)), "볼록 껍질"
def _판(그림, 면, 길, 넓힘=0.0):   # 넓힘 > 0: 채운 윤곽을 4 배로 키워 다시 딴다(화소 가운데 윤곽은 반 화소 안쪽 → 1/8 화소 · 판정기준37 · OCC offset2D 는 얇은 모양을 깨뜨려 버림)
    import sys, cadquery as cq
    sys.path.insert(0, "G:/art2real/원화3d/실험_20261013/구멍"); import 윤곽바탕 as W
    밀 = (lambda w: w.extrude(길).translate((0, 0, -길 / 2))) if 면 == "XY" else (lambda w: w.extrude(길, both=True))
    m, c = W.바깥(그림); f = W.맞추기(c); k = 4 if 넓힘 else 1
    if f[0] == "원": (x, y), r = f[1], f[2]; cx, cy = 화(x, y); return 밀(cq.Workplane(면).center(cx, cy).circle((r + (.5 if 넓힘 else 0)) * 칸)), "원"
    if 넓힘:
        큰 = cv2.resize(m.astype(np.uint8), None, fx=k, fy=k, interpolation=cv2.INTER_NEAREST); cs, _ = cv2.findContours(큰, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)[:, 0, :]
    원래 = lambda p: [화((x + .5) / k - .5, (y + .5) / k - .5) for x, y in p]
    for i, e in enumerate((1.5, 1.0, .5, 2.5, 4)):
        p = cv2.approxPolyDP(c.reshape(-1, 1, 2).astype(np.float32), e * k, True)[:, 0, :]; q = 원래(p)
        if 3 <= len(q) <= 300 and not 꼬임(q) and 면유효([(x, y) for x, y in q]): return 밀(cq.Workplane(면).polyline(q).close()), "다각" if i == 0 else "다시 줄임"
    q = 원래(cv2.convexHull(c.astype(np.float32))[:, 0, :]); return 밀(cq.Workplane(면).polyline(q).close()), "볼록 껍질"
def 몸통35(그림셋, H):   # 위 · 앞 · 옆 바깥 윤곽 교차(사용자 「해보자고」 10-14 · 판정기준34 B) · → (고체, 경로)
    X, Fr, S = 그림셋; t, a = _판(X, "XY", H); f, b = _판(Fr, "XZ", 1.2); s, c = _판(S, "YZ", 1.2)
    return t.intersect(f).intersect(s), "/".join((a, b, c))
def _폭(m, 축): i = np.nonzero(m.any(axis=축))[0]; return (i.max() - i.min() + 1) if len(i) else 0
def 몸통36(그림셋, H, 넓힘=0.0, 빈장건너뜀=False):   # 판정기준37: 넓힘 = 반 화소 · 빈 앞 · 옆 그림은 건너뜀   # 판정기준36 — 몸통35 + 두 안전장치(쓴 장을 경로에 찍는다) · → (고체, 경로)
    # ① 앞 · 옆 그림을 믿는 조건: 채운 윤곽의 가로 폭이 위 그림의 그 축 폭과 3 화소 안 · 세로 6 화소 이상(얇은 부품은 한 줄이라 조각만 잡힘 · 판정35)
    # ② 교차 결과가 재료보다 크거나 비면(OCC 순서 탈) 다른 순서 → 그래도 안 되면 그 장을 뺀다
    import sys; sys.path.insert(0, "G:/art2real/원화3d/실험_20261013/구멍"); import 윤곽바탕 as W
    X, Fr, S = 그림셋; mt = W.바깥(X)[0]; t, a = _판(X, "XY", H); 쓴 = [("위", t)]
    for 이름, g, 면, 축폭 in (("앞", Fr, "XZ", _폭(mt, 0)), ("옆", S, "YZ", _폭(mt, 1))):
        if 빈장건너뜀 and (g > .3).sum() < 3: continue
        m = W.바깥(g)[0]
        if abs(_폭(m, 0) - 축폭) <= 3 and _폭(m, 1) >= 6:
            for 넓 in ((넓힘, 0.0) if 넓힘 else (0.0,)):   # 넓히기가 OCC 에서 깨지면(빈 모양) 안 넓힌 것으로 · 그것도 깨지면 그 장을 뺀다
                try: q = _판(g, 면, 1.2, 넓)[0]; q.val().Volume(); 쓴.append((이름, q)); break
                except Exception: pass
    V = lambda q: q.val().Volume()
    for 판 in ([쓴[0], 쓴[1], 쓴[2]], [쓴[0], 쓴[2], 쓴[1]], 쓴[:2], [쓴[0], 쓴[-1]], 쓴[:1]) if len(쓴) == 3 else (쓴, 쓴[:1]):
        try:
            r = 판[0][1]
            for _, q in 판[1:]: r = r.intersect(q)
            if len(판) == 1: return r, "위 · " + a
            칸들 = [점유_캐드(q) for _, q in 판]; 기대 = np.logical_and.reduce(칸들); 얻 = 점유_캐드(r)   # 재료를 칸으로 겹친 것과 CAD 교차가 맞아야(정답 안 봄 · 판정37)
            if 기대.sum() and (기대 & 얻).sum() / max((기대 | 얻).sum(), 1) >= .9: return r, "+".join(n for n, _ in 판) + " · " + a
        except Exception: pass
    return t, "위 · " + a
def 몸통37(그림셋, H): return 몸통36(그림셋, H, 넓힘=.5 * 칸, 빈장건너뜀=True)
def 짓기(Y, D, H, 덩어리깊이=False, 그림=None):   # 그림: 주면 몸통은 몸통53(그림) · Y 는 관통 · 들어감에만   # 덩어리깊이: 들어감 덩어리(4 이웃)마다 깊이 하나(중앙값) — 판정기준31 ①
    import cadquery as cq
    if 그림 is not None: return 깎기(몸통53(그림, H)[0], Y, D, H, 덩어리깊이)
    밖 = Y > 0; ps = 다각(밖)
    if not ps: return None
    s = None
    for p in ps:
        try:
            b = cq.Workplane("XY").polyline(p).close().extrude(H).translate((0, 0, -H / 2)); s = b if s is None else s.union(b)
        except Exception: pass
    if s is None: return None
    return 깎기(s, Y, D, H, 덩어리깊이)
def 깎기(s, Y, D, H, 덩어리깊이):   # 몸통 s 에 관통 · 들어감을 깎는다
    import cadquery as cq
    for p in 다각(Y == 2):
        try: s = s.cut(cq.Workplane("XY").polyline(p).close().extrude(H + .2).translate((0, 0, -H / 2 - .1)))
        except Exception: pass
    if 덩어리깊이:
        n, lab = cv2.connectedComponents((Y == 3).astype(np.uint8), connectivity=4)
        for i in range(1, n):
            m = lab == i; dz = min(float(np.median(D[m])), .98) * H
            if dz < .01 * H: continue
            for p in 다각(m):
                try: s = s.cut(cq.Workplane("XY").polyline(p).close().extrude(dz + .05).translate((0, 0, H / 2 - dz)))
                except Exception: pass
        return s
    층 = np.clip(np.round(np.where(Y == 3, D, 0) / .1), 0, 10).astype(int)
    for k in range(1, 11):
        for p in 다각((Y == 3) & (층 == k)):
            dz = min(k * .1, .98) * H
            try: s = s.cut(cq.Workplane("XY").polyline(p).close().extrude(dz + .05).translate((0, 0, H / 2 - dz)))
            except Exception: pass
    return s
def 점유_메시(v, f, n=48):
    import open3d as o3d
    sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(np.asarray(v, np.float32)), o3d.core.Tensor(np.asarray(f, np.uint32)))
    g = (np.arange(n) + .5) / n * 1.1 - .55; P = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3).astype(np.float32)
    return sc.compute_occupancy(o3d.core.Tensor(P)).numpy().reshape(n, n, n) > .5
def 점유_캐드(s, n=48):
    vs, ts = s.val().tessellate(0.005, 0.2); return 점유_메시([(q.x, q.y, q.z) for q in vs], ts, n)
def 정규메시(p):   # 데이터.py 와 같은 변환
    import trimesh
    m = trimesh.load(p, force="mesh")
    if len(m.faces) > 150000: raise ValueError("면이 너무 많음")   # 10-13 평가 메모리 — 큰 메시는 건너뜀(0 점으로 셈)
    e = m.extents; ax = int(np.argmin(e)); order = [i for i in range(3) if i != ax] + [ax]
    return (m.vertices - m.bounds.mean(0))[:, order] / e.max(), m.faces, float(e[ax] / e.max())
def 부피IoU(job):   # (stl 경로, Y, D[, 덩어리깊이[, 그림]]) → (IoU, 바탕만 IoU) · 그림을 주면 (IoU, 바탕만, 몸통 경로)
    p, Y, D = job[:3]; 덩 = job[3] if len(job) > 3 else False; 그림 = job[4] if len(job) > 4 else None
    if 그림 is not None:
        try:
            v, f, H = 정규메시(p); 정 = 점유_메시(v, f); 몸, 길 = 몸통37(그림, H) if isinstance(그림, tuple) else 몸통53(그림, H); s = 깎기(몸, Y, D, H, 덩)
            r = lambda q: float((q & 정).sum() / max((q | 정).sum(), 1)); return (r(점유_캐드(s)), r(점유_캐드(몸)), 길)
        except Exception as e: return (0.0, 0.0, "실패 " + type(e).__name__)
    try:
        v, f, H = 정규메시(p); 정 = 점유_메시(v, f); s = 짓기(Y, D, H, 덩); s0 = 짓기(np.where(Y > 0, 1, 0), D * 0, H)
        r = lambda q: float((q & 정).sum() / max((q | 정).sum(), 1))
        return (r(점유_캐드(s)) if s is not None else 0.0, r(점유_캐드(s0)) if s0 is not None else 0.0)
    except Exception: return (0.0, 0.0)
