# -*- coding: utf-8 -*-
"""3 단계 첫 틀: 특징맞춤2 가 푼 카메라로 실루엣 헐 (10-03 · Gemini ③ 「틀 하나를 각 장에 맞춰」).
장합치기.py(눈짐작 각 → 뿔 · 얼굴이 지워진 덩어리)와 같은 투표인데 카메라만 특징점으로 푼 것(회전 · 크기 · 이동 · 정면 화소 틀).
투표: 복셀이 화면 안에 들어오는 장들 중 (그 수 − 1) 장 이상이 머리 안이면 남김 · 화면 안에 든 장이 3 장 미만이면 버림
       (뿔이 잘린 컷 · 목이 섞인 컷 때문에 「화면 밖 = 머리 밖」은 뿔을 지운다 → 화면 밖은 모름).
그다음 장마다 껍질 앞면보다 카메라 쪽 복셀을 깎음(껍질 깊이는 특징맞춤2 의 a · b 와 같은 맞춤). 출력 각도데이터/틀헐.ply · 틀헐.json"""
import os, json, numpy as np, trimesh
from skimage import measure
import importlib.util
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"
J = json.load(open(os.path.join(O, "특징맞춤2.json"), encoding="utf-8")); P = json.load(open(os.path.join(O, "특징점.json"), encoding="utf-8"))
spec = importlib.util.spec_from_file_location("fm2", os.path.join(os.path.dirname(os.path.abspath(__file__)), "특징맞춤2.py"))
def R_of(yaw, pitch, roll):
    t, p, r = np.radians([yaw, pitch, roll]); right = np.array([np.cos(t), -np.sin(t), 0]); toward = np.array([np.sin(t), np.cos(t), 0]); up0 = np.array([0, 0, 1.0])
    up = up0 * np.cos(p) - toward * np.sin(p); tw = toward * np.cos(p) + up0 * np.sin(p)
    r1 = right * np.cos(r) + up * np.sin(r); u1 = -right * np.sin(r) + up * np.cos(r); return np.array([r1, u1, tw])
깎기 = os.environ.get("CARVE", "1") == "1"
z1 = np.load(os.path.join(O, "판_1_Z.npz")); m1 = z1["m"]; ys, xs = np.nonzero(m1); cu, cv = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
X3 = {k: np.array(v) for k, v in J["특징점 3D"].items()}
뷰 = {}
for n in J["장"]:
    z = np.load(os.path.join(O, f"판_{n}_Z.npz")); m, Z = z["m"], z["Z"]
    if n == "1": R = np.eye(3)[[0, 2, 1]]; s, tx, ty = 1.0, cu, cv
    else:
        a = J["장별"][n]; R = R_of(*a["yaw · pitch · roll"]); s = a["크기"]
        # 이동은 json 에 없으니 특징점으로 다시(같은 R · s 에서 최소제곱)
        ks = list(P[n]); pr = np.array([[s * (R @ X3[k])[0], -s * (R @ X3[k])[1]] for k in ks]); ob = np.array([P[n][k] for k in ks], float); tx, ty = (ob - pr).mean(0)
    뷰[n] = dict(m=m, Z=Z, R=R, s=s, tx=tx, ty=ty)
G = 128; lo = np.array([-130, -130, -200]); hi = np.array([130, 130, 160]); ax = [np.linspace(lo[i], hi[i], G) for i in range(3)]
Xg, Yg, Zg = np.meshgrid(*ax, indexing="ij"); Pt = np.c_[Xg.ravel(), Yg.ravel(), Zg.ravel()]
보임 = np.zeros(len(Pt), int); 안 = np.zeros(len(Pt), int); proj = {}
for n, v in 뷰.items():
    c = Pt @ v["R"].T; px = np.round(v["s"] * c[:, 0] + v["tx"]).astype(int); py = np.round(-v["s"] * c[:, 1] + v["ty"]).astype(int); H, W = v["m"].shape
    ok = (px >= 0) & (px < W) & (py >= 0) & (py < H); ins = np.zeros(len(Pt), bool); ins[ok] = v["m"][py[ok], px[ok]]
    보임 += ok; 안 += ins; proj[n] = (ok, ins, px, py, c[:, 2])
keep = (보임 >= 3) & (안 >= 보임 - 1)
결과 = {"복셀(헐)": int(keep.sum())}
if 깎기:
    for n, v in 뷰.items():
        ok, ins, px, py, dep = proj[n]; q = keep & ok & ins; sZ = np.full(len(Pt), np.nan); sZ[q] = v["Z"][py[q], px[q]] / v["s"]
        sel = q & np.isfinite(sZ)
        if sel.sum() < 100: continue
        off = np.nanpercentile(dep[sel], 99) - np.nanpercentile(sZ[sel], 99)
        keep &= ~(sel & (dep > sZ + off + 4))
결과["복셀(깎은 뒤)"] = int(keep.sum())
V = keep.reshape(G, G, G); vt, fc, _, _ = measure.marching_cubes(np.pad(V, 1).astype(np.float32), 0.5); vt -= 1
vt = lo + vt * (hi - lo) / (G - 1); me = trimesh.Trimesh(np.c_[vt[:, 0], -vt[:, 1], vt[:, 2]], fc); trimesh.smoothing.filter_taubin(me, iterations=8)   # 블렌더: 앞 = −y
me.export(os.path.join(O, "틀헐.ply")); json.dump(결과, open(os.path.join(O, "틀헐.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(결과)
