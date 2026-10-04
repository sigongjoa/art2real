# -*- coding: utf-8 -*-
"""블렌더 격자 변형용 값 (10-04 사용자 「블렌더 격자 변형」 · 행별 늘이기 세 판 실패 뒤).
행마다가 아니라 **높이 4 층**마다 하나씩: 그 층 띠의 원화 몸통 반폭 / 엑시아 몸통 반폭(중앙값 · 0.85~1.2) · 가운데 옮김 · 뒤 끝 비(뒤쪽만).
출력 out/오메가몬2/블렌더/격자값.json → 격자변형_bl.py 가 블렌더 래티스(3×3×4) 점을 옮긴다."""
import os, json, numpy as np, cv2, trimesh, contextlib, io
A = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
K = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "기준선.py")}
with contextlib.redirect_stdout(io.StringIO()): exec(open(K["__file__"], encoding="utf-8").read(), K)
m1 = np.load(os.path.join(A, "판_1_Z.npz"))["m"]; H, W = m1.shape; cu = (np.nonzero(m1)[1].min() + np.nonzero(m1)[1].max()) / 2
m2 = np.load(os.path.join(A, "판_2_Z.npz"))["m"]; D0, ND = -200, 400; k_, t_ = K["k"], K["t"]; ct, st_ = np.cos(t_), np.sin(t_)
Ma = np.array([[k_ * ct, -k_ * st_, -k_ * K["ex"] * ct + k_ * K["ey"] * st_ - D0], [k_ * st_, k_ * ct, K["c"] - k_ * K["xm"] * st_]], np.float32)
S2 = cv2.warpAffine(m2.astype(np.uint8), Ma, (ND, H), flags=cv2.INTER_NEAREST)
me = trimesh.load(os.path.join(B, "엑시아_정렬.ply"), process=False); v = me.vertices; f = me.faces
def 실루엣(u, shape):
    img = np.zeros(shape, np.uint8); r = -v[:, 2]
    cv2.fillPoly(img, [np.round(np.c_[u[t], r[t]]).astype(np.int32) for t in f], 1); return img
몸 = lambda m: cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
Fa, Fe = 몸(m1), 몸(실루엣(v[:, 0] + cu, (H, W))); Sa, Se = 몸(S2), 몸(실루엣(v[:, 1] - D0, (H, ND)))
z0, z1 = float(v[:, 2].min()), float(v[:, 2].max()); 층 = np.linspace(z0, z1, 4); 띠 = (z1 - z0) / 3
값 = []
for z in 층:
    rows = [r for r in range(H) if abs(-r - z) <= 띠 / 2]
    def 몫(fa, fe, fn):
        a = [fn(np.nonzero(fa[r])[0]) for r in rows if len(np.nonzero(fa[r])[0]) > 2 and len(np.nonzero(fe[r])[0]) > 2]
        e = [fn(np.nonzero(fe[r])[0]) for r in rows if len(np.nonzero(fa[r])[0]) > 2 and len(np.nonzero(fe[r])[0]) > 2]
        return (np.median(a), np.median(e)) if a else (np.nan, np.nan)
    wa, we = 몫(Fa, Fe, lambda x: (x.max() - x.min()) / 2); ca, ce = 몫(Fa, Fe, lambda x: (x.max() + x.min()) / 2)
    ba, be = 몫(Sa, Se, lambda x: x.max() + D0)
    값.append({"z": z, "sx": float(np.clip(wa / we, 0.85, 1.2)) if np.isfinite(wa) else 1.0, "c": float(ce - cu) if np.isfinite(ce) else 0.0,
              "dc": float(np.clip(ca - ce, -15, 15)) if np.isfinite(ca) else 0.0, "sy": float(np.clip(ba / be, 0.85, 1.2)) if np.isfinite(ba) and be > 5 else 1.0})
json.dump({"층": 값, "범위": [v.min(0).tolist(), v.max(0).tolist()]}, open(os.path.join(B, "격자값.json"), "w"), indent=1)
print(json.dumps(값, ensure_ascii=False))
