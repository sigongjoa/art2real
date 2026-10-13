# 로드맵 2 — 지도(0 바깥 · 1 윗면 · 2 관통 · 3 들어감 + 깊이 비율) → CadQuery: 바깥 윤곽을 높이 H 로 밀고 · 관통은 뚫고 · 들어감은 깊이 층(0.1 단위)마다 덩어리째 깎음 · 부피 IoU(48³) · 10-13
import numpy as np, cv2
N = 128; 칸 = 1.1 / N
def 화(x, y): return (-.55 + (x + .5) * 칸, .55 - (y + .5) * 칸)   # 화소 → 세계(데이터.py 의 광선 격자와 같음)
def 다각(mask):
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); out = []
    for c in cs:
        if cv2.contourArea(c) < 3: continue
        p = cv2.approxPolyDP(c, .8, True)[:, 0, :]
        if len(p) >= 3: out.append([화(x, y) for x, y in p])
    return out
def 짓기(Y, D, H):
    import cadquery as cq
    밖 = Y > 0; ps = 다각(밖)
    if not ps: return None
    s = None
    for p in ps:
        try:
            b = cq.Workplane("XY").polyline(p).close().extrude(H).translate((0, 0, -H / 2)); s = b if s is None else s.union(b)
        except Exception: pass
    if s is None: return None
    for p in 다각(Y == 2):
        try: s = s.cut(cq.Workplane("XY").polyline(p).close().extrude(H + .2).translate((0, 0, -H / 2 - .1)))
        except Exception: pass
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
    m = trimesh.load(p, force="mesh"); e = m.extents; ax = int(np.argmin(e)); order = [i for i in range(3) if i != ax] + [ax]
    return (m.vertices - m.bounds.mean(0))[:, order] / e.max(), m.faces, float(e[ax] / e.max())
def 부피IoU(job):   # (stl 경로, Y, D) → (IoU, 바탕만 IoU)
    p, Y, D = job
    try:
        v, f, H = 정규메시(p); 정 = 점유_메시(v, f); s = 짓기(Y, D, H); s0 = 짓기(np.where(Y > 0, 1, 0), D * 0, H)
        r = lambda q: float((q & 정).sum() / max((q | 정).sum(), 1))
        return (r(점유_캐드(s)) if s is not None else 0.0, r(점유_캐드(s0)) if s0 is not None else 0.0)
    except Exception: return (0.0, 0.0)
