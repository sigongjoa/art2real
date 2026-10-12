# -*- coding: utf-8 -*-
"""학생이 고르고 규칙이 짓는 회전체 — 3D 학생 부피(증거)에서 주축 · 대칭을 보고, 맞으면 그 축으로 CAD 회전 ∩ 교차 · 판정기준22 · 10-12
SET=시험|검증2 python 회전2.py 찾기 번호…   → 축 · 기운 각 · 대칭 점수 · 걸림"""
import os, sys, numpy as np, torch
H = os.path.dirname(os.path.abspath(__file__)); 깊 = os.path.join(os.path.dirname(H), "깊이학습")
대칭문턱, 칸문턱, 비율문턱 = 0.8, 10, 0.15   # 판정기준22 에 얼림
_m = None
def 학생부피(X):   # X (4, 6, 128, 128) → 점유 확률 64³ ∩ 교차
    global _m
    sys.path.insert(0, 깊); import 부피학생 as 부
    if _m is None: _m = 부.부피망().cuda(); _m.load_state_dict(torch.load(os.path.join(깊, os.environ.get("STUDENT", "부피학생G.pt")))); _m.eval()
    with torch.no_grad():
        with torch.autocast("cuda", dtype=torch.float16): p = torch.sigmoid(_m(torch.tensor(부.입력(X.astype(np.float32))[None]).cuda()).float())[0].cpu().numpy()
    s = [np.asarray(X[0][2 * a] > .5).reshape(64, 2, 64, 2).max((1, 3)) for a in range(3)]; return p * (s[0][None] & s[1][:, None] & s[2][:, :, None])
def 찾기(P):
    idx = np.argwhere(P > .5)
    if len(idx) < 200: return None
    u = (idx + .5) / 64; c = u.mean(0); w, V = np.linalg.eigh(np.cov((u - c).T)); a = V[:, np.argmax(w)]   # 주축 = 가장 긴 방향
    e1 = np.cross(a, [1, 0, 0] if abs(a[0]) < .9 else [0, 1, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(a, e1)
    d = u - c; t = d @ a; r = np.hypot(d @ e1, d @ e2); th = np.arctan2(d @ e2, d @ e1); tb = np.floor((t - t.min()) * 64).astype(int); ab = ((th + np.pi) / (2 * np.pi) * 16).astype(int) % 16
    R, Rin, ok = {}, {}, []
    for b in np.unique(tb):
        m = tb == b
        if m.sum() < 8: continue
        mx = np.zeros(16); mn = np.full(16, np.inf)
        np.maximum.at(mx, ab[m], r[m]); np.minimum.at(mn, ab[m], r[m])
        if (mx > 0).sum() < 12: ok.append(False); continue
        ok.append(mx.std() / max(mx.mean(), 1e-6) <= 비율문턱); R[b] = float(np.median(mx)); 안 = np.median(mn[np.isfinite(mn)]); Rin[b] = float(안) if 안 > 2.5 / 64 else 0.0
    점 = float(np.mean(ok)) if ok else 0.0; 기움 = float(np.degrees(np.arccos(min(1.0, np.abs(a).max()))))
    return {"축": a, "중심": c, "e1": e1, "R": R, "Rin": Rin, "t0": float(t.min()), "대칭": round(점, 3), "칸": len(ok), "기움": round(기움, 1), "걸림": 점 >= 대칭문턱 and len(ok) >= 칸문턱}
def 짓기(f, 교):   # 반쪽 윤곽(바깥 R · 안 Rin) → 임의 축 회전 → ∩ 교차 · CAD = 110 u − 5
    import cadquery as cq, cv2
    from 도구 import 꼬임
    from scipy.ndimage import median_filter
    bs = sorted(f["R"]); T = lambda b: f["t0"] + (b + .5) / 64
    for k in ("R", "Rin"):   # 칸마다 반지름이 들쭉날쭉 → 5 칸 중앙값으로 고름(판정 전 고침 · #8 #23 고리 줄)
        v = median_filter(np.array([f[k][b] for b in bs]), size=5, mode="nearest"); f[k] = dict(zip(bs, v.tolist()))
    밖 = [(f["R"][b], T(b)) for b in bs]; 안 = [(f["Rin"][b], T(b)) for b in reversed(bs)]
    poly = [(0.0, T(bs[0]) - .5 / 64)] + 밖 + [(0.0, T(bs[-1]) + .5 / 64)] + ([q for q in 안 if q[0] > 0] if any(q[0] > 0 for q in 안) else [])
    p = cv2.approxPolyDP(np.array(poly, np.float32).reshape(-1, 1, 2) * 1000, 8, True)[:, 0, :] / 1000
    if len(p) < 3 or 꼬임([list(q) for q in p]): raise ValueError("윤곽")
    C_ = lambda v: cq.Vector(*(110 * np.asarray(v) - 5))
    pts = [C_(f["중심"] + t_ * f["축"] + r_ * f["e1"]) for r_, t_ in p]
    면 = cq.Face.makeFromWires(cq.Wire.makePolygon(pts, close=True)); s = cq.Workplane().add(cq.Solid.revolve(면, 360, C_(f["중심"] - f["축"]), C_(f["중심"] + f["축"])))
    t = s.intersect(교); return t if t.val().Volume() > .3 * s.val().Volume() else None
if __name__ == "__main__":
    sys.path.insert(0, H); from 도구 import 입력, 세트
    for i in [int(x) for x in sys.argv[2:]]:
        f = 찾기(학생부피(입력(i)))
        print(세트, i, "없음" if f is None else "대칭 %.2f 칸 %d 기움 %.0f° %s" % (f["대칭"], f["칸"], f["기움"], "걸림" if f["걸림"] else ""), flush=True)
