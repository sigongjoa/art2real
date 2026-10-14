# 판정기준34 — 천장 올리기: 정답 메시에 여섯 방향 광선 → 방향 조합별로 깎은 복셀의 부피 IoU · 학습 없음 · CAD 안 지음 · 10-14
# venv python 천장34.py → out/설명/캐드부품/결과34.json · 부피IoU_34.npy
import json, numpy as np
from multiprocessing import Pool
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"
판들 = ["①바탕", "①", "②", "③", "④"]
def 깎기(sc, n, 축, 부호):   # 축 방향 광선(부호 쪽에서 들어옴) → 첫 맞음보다 안쪽 복셀만 True · 안 맞은 줄은 전부 False
    import open3d as o3d
    g = (np.arange(n) + .5) / n * 1.1 - .55; 나머지 = [a for a in range(3) if a != 축]
    A, B = np.meshgrid(g, g, indexing="ij"); r = np.zeros((n, n, 6), np.float32)
    r[..., 나머지[0]], r[..., 나머지[1]], r[..., 축], r[..., 3 + 축] = A, B, 2.0 * 부호, -부호
    t = sc.cast_rays(o3d.core.Tensor(r.reshape(-1, 6)))["t_hit"].numpy().reshape(n, n); 맞 = 2.0 * 부호 - 부호 * t   # 맞은 좌표
    c = g.reshape([n if a == 축 else 1 for a in range(3)])
    맞 = np.expand_dims(맞, 축); ok = np.expand_dims(np.isfinite(t), 축)
    return ok & ((c <= 맞) if 부호 > 0 else (c >= 맞))
def 복셀(sc, v, f, H, n):   # → (정답 점유, {판: 점유})
    정 = J.점유_메시(v, f, n); g = (np.arange(n) + .5) / n * 1.1 - .55
    띠 = (np.abs(g) <= H / 2 + .5 * 1.1 / n).reshape(1, 1, n)   # 부품 높이 안(위 · 아래 면)
    위, 아래 = 깎기(sc, n, 2, 1), 깎기(sc, n, 2, -1); 앞, 뒤 = 깎기(sc, n, 1, 1), 깎기(sc, n, 1, -1); 옆, 반옆 = 깎기(sc, n, 0, 1), 깎기(sc, n, 0, -1)
    실 = lambda m, a: np.broadcast_to(m.any(axis=a, keepdims=True), m.shape)
    return 정, {"①바탕": 실(위, 2) & 띠, "①": 위 & 띠, "②": 실(위, 2) & 실(앞, 1) & 실(옆, 0) & 띠, "③": 위 & 앞 & 옆 & 띠, "④": 위 & 아래 & 앞 & 뒤 & 옆 & 반옆}
def 장면(p):
    import open3d as o3d
    v, f, H = J.정규메시(p); sc = o3d.t.geometry.RaycastingScene(); sc.add_triangles(o3d.core.Tensor(np.asarray(v, np.float32)), o3d.core.Tensor(np.asarray(f, np.uint32)))
    return sc, v, f, H
def 하나(p):
    out = []
    try:
        sc, v, f, H = 장면(p)
        for n in (48, 96):
            정, 판 = 복셀(sc, v, f, H, n); out += [float((판[k] & 정).sum() / max((판[k] | 정).sum(), 1)) for k in 판들]
        return out
    except Exception: return [0.0] * 10
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; del d
    L = json.load(open(O + "목록.json", encoding="utf-8"))
    with Pool(2, maxtasksperchild=20) as pool: R = np.array(pool.map(하나, [L[i] for i in te], chunksize=4))
    np.save(O + "부피IoU_34.npy", R); 결과 = {}
    for gi, n in enumerate((48, 96)):
        결과[n] = {k: float(R[:, gi * 5 + i].mean()) for i, k in enumerate(판들)}; 결과[n]["0점(①)"] = int((R[:, gi * 5 + 1] == 0).sum())
    a = 결과[48]; 결과["판정"] = {"A": a["③"] >= a["①"] + .08, "B": a["②"] >= a["①바탕"] + .04}; 결과["CAD 천장33"] = 0.6465
    json.dump(결과, open(O + "결과34.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(결과, ensure_ascii=False, indent=1))
