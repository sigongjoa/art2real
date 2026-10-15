# 판정기준51 — 여섯 방향 깎기: 방향마다 깊이 지도(128²) → 틀에서 CadQuery 로 깎는다 · 같은 깊이로 칸만 깎는 검사판 · 10-15
# 방향마다 「지역 틀」: 지역 +w 가 그 면의 바깥 법선 · 깎기는 위(+w)에서 아래로(지금 짓기의 위 깎기와 같은 꼴) · 지역 → 세계는 회전 R
import numpy as np, cv2
import 짓기 as J
N = J.N; 칸 = J.칸; 층수 = 16
방향 = {"위": ("X", 0), "아래": ("X", 180), "앞": ("X", -90), "뒤": ("X", 90), "옆": ("Y", 90), "반옆": ("Y", -90)}   # (축, 도) · 오른손 회전 · 앞 = 지역 +w → 세계 +y
def R(축, 도):
    c, s = np.cos(np.radians(도)), np.sin(np.radians(도))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]]) if 축 == "X" else np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
g = (np.arange(N) + .5) * 칸 - .55   # 화소 가운데(지역 u · v) — J.화 와 같다: u = g[x] · v = -g[y]
def 깊이지도(v, f):   # 정답 메시 → {방향: 지역 w 의 첫 맞음(N × N · 안 맞으면 nan)}
    import open3d as o3d
    sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(np.asarray(v, np.float32)), o3d.core.Tensor(np.asarray(f, np.uint32))); out = {}
    U, V = np.meshgrid(g, -g)   # [y, x]
    for k, (축, 도) in 방향.items():
        r = R(축, 도); o = np.stack([U, V, np.full_like(U, 2.0)], -1) @ r.T; dvec = np.array([0, 0, -1.0]) @ r.T
        ray = np.concatenate([o.reshape(-1, 3), np.broadcast_to(dvec, (N * N, 3))], 1).astype(np.float32)
        t = sc.cast_rays(o3d.core.Tensor(ray))["t_hit"].numpy().reshape(N, N); out[k] = np.where(np.isfinite(t), 2.0 - t, np.nan)
    return out
def 반높이(몸, r):   # 틀 상자 꼭짓점을 지역 틀로 → 지역 w 의 위 끝
    b = 몸.val().BoundingBox(); 꼭 = np.array([[x, y, z] for x in (b.xmin, b.xmax) for y in (b.ymin, b.ymax) for z in (b.zmin, b.zmax)]); return float((꼭 @ r)[:, 2].max())
def 층(w, h):   # 깊이(h − w)를 층수 단계로 내림 → 깎을 깊이 · 안 맞음 = 통째(2h)
    d = np.where(np.isnan(w), 2 * h + .1, h - w); 단 = 2 * h / 층수; return np.floor(np.clip(d, 0, None) / 단 + 1e-6) * 단
def 깎기(몸, 지도, 마감=None, 다각=None):   # 다각: 깎을 마스크 → [(바깥, [섬…])] · 기본 J.다각섬(10-15 감사 뒤 J.다각섬4)
    다각 = 다각 or J.다각섬   # 몸 = CadQuery 틀 · 지도 = 깊이지도 → (고체, 버린 수) · 마감(time.time 기준)을 넘기면 TimeoutError(10-15 한 부품에 CPU 900 초)
    import time
    s = 몸; J.버린.clear()
    for k, (축, 도) in 방향.items():
        r = R(축, 도); h = 반높이(몸, r); 깊 = 층(지도[k], h); 단 = 2 * h / 층수
        for i in range(1, 층수 + 2):
            dz = i * 단 if i <= 층수 else 2 * h + .1; m = 깊 >= dz - 1e-6
            if not m.any(): break
            for q, 구 in 다각(m):
                if 마감 and time.time() > 마감: raise TimeoutError("여섯 깎기 %s 층 %d" % (k, i))
                try:
                    t = J._도구(q, 구, h + .05 - (h - dz), h - dz)   # 지역 w ∈ [h − dz, h + .05]
                    t = t.rotate((0, 0, 0), (1, 0, 0) if 축 == "X" else (0, 1, 0), 도) if 도 else t; s = s.cut(t)
                except Exception: J.버린["여섯 깎기"] += 1
    return s, sum(J.버린.values())
def 칸깎기(틀칸, 몸, 지도, n=48):   # 검사판 — 같은 깊이 · 같은 층으로 칸만 깎는다(CAD 안 지음)
    G = (np.arange(n) + .5) / n * 1.1 - .55; P = np.stack(np.meshgrid(G, G, G, indexing="ij"), -1).reshape(-1, 3); q = 틀칸.reshape(-1).copy()
    for k, (축, 도) in 방향.items():
        r = R(축, 도); h = 반높이(몸, r); 깊 = 층(지도[k], h); L = P @ r   # 세계 → 지역(r 은 직교)
        x = np.clip(np.round((L[:, 0] + .55) / 칸 - .5).astype(int), 0, N - 1); y = np.clip(np.round((-L[:, 1] + .55) / 칸 - .5).astype(int), 0, N - 1)
        q &= ~(L[:, 2] > h - 깊[y, x])
    return q.reshape(n, n, n)
