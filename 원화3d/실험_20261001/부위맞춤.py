# -*- coding: utf-8 -*-
"""부위 맞춤 F 판 (10-05 · 외부 LLM 2 회 채택: 부위 닮음 변환 + 공유 경계 제약 + 그래프 라플라시안 + 적게 바꾸기)
python 부위맞춤.py <판 이름> [w경계=20] [w매끈=2] [w적게=1]
  바탕: 트리포_T6 + 부위 라벨 20(PartField) · 「지움」 부위는 버림
  부위 i 변환 θi = (회전 벡터 3 · 이동 3 · log 배율 1), 중심 = 부위 무게중심
  비용 = 정면 실루엣(모델 점이 원화 마스크 밖이면 거리², 원화 테두리 점이 모델 점에서 멀면 거리²)
       + w경계 · Σ 공유 경계점 |Ai(v) − Aj(v)|²  + w매끈 · Σ 이웃 (θi − θj)² · 경계 길이  + w적게 · Σ |θi|²
  적용: 꼭짓점마다 그 꼭짓점을 쓰는 부위 변환의 평균(경계에서 이어 붙음)
출력: 블렌더/<판>.ply · 변환표 json"""
import sys, json, numpy as np, trimesh
from scipy.optimize import minimize
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot
from scipy import ndimage
B = "G:/art2real/원화3d/out/오메가몬2/블렌더/"; O = "G:/art2real/원화3d/out/오메가몬2/지표/트리포분할/"; A = "G:/art2real/원화3d/out/오메가몬2/지표/각도데이터/"
nm = sys.argv[1]; WE, WS, WP = [float(x) for x in (sys.argv[2:5] + ["20", "2", "1"][len(sys.argv[2:5]):])]
m = trimesh.load(B + "트리포_T6.ply", process=False); m = trimesh.Trimesh(m.vertices, m.faces, process=False)
lab = np.load(O + "트리포_T6_라벨20.npy"); G = json.load(open(O + "트리포_T6_그래프20.json", encoding="utf-8"))
drop = {d["id"] for d in G["노드"] if "지움" in d["이름(눈)"]}
keepf = ~np.isin(lab, list(drop)); m = trimesh.Trimesh(m.vertices, m.faces[keepf], process=False); lab = lab[keepf]
ids = sorted(set(lab.tolist())); K = len(ids); ix = {p: i for i, p in enumerate(ids)}; L = np.array([ix[p] for p in lab])
V = m.vertices.copy()
# 꼭짓점 → 부위들
vp = [set() for _ in range(len(V))]
for f, l in zip(m.faces, L):
    for v in f: vp[v].add(l)
cen = np.array([V[np.unique(m.faces[L == i])].mean(0) for i in range(K)])
# 표본 점(부위마다 ≤ 200)
rng = np.random.default_rng(0); S = []
for i in range(K):
    vs = np.unique(m.faces[L == i]); S.append(vs if len(vs) <= 200 else rng.choice(vs, 200, replace=False))
# 공유 경계점
bnd = [(v, sorted(p)) for v, p in enumerate(vp) if len(p) > 1]
BE = [(v, a, b) for v, p in bnd for a in p for b in p if a < b]
bv = np.array([e[0] for e in BE]); ba = np.array([e[1] for e in BE]); bb = np.array([e[2] for e in BE])
# 이웃 · 경계 길이
NB = {}
for e in G["간선"]:
    if e["a"] in ix and e["b"] in ix: NB[(ix[e["a"]], ix[e["b"]])] = e["경계"]
nbl = np.array(list(NB.keys())); nbw = np.array(list(NB.values())); nbw = nbw / nbw.mean()
# 원화 정면 마스크 · 거리장 (레퍼런스정렬과 같은 틀: u = x + cu, 행 = −z)
mk = np.load(A + "판_1_Z.npz")["m"].astype(bool); cu = (np.nonzero(mk)[1].min() + np.nonzero(mk)[1].max()) / 2
dout = ndimage.distance_transform_edt(~mk)   # 마스크 밖 거리
edge = mk & ~ndimage.binary_erosion(mk); er, ec = np.nonzero(edge); EP = np.c_[ec - cu, -er.astype(float)]   # 테두리 점 (x, z)
def 변환(th, i, P):
    r = Rot.from_rotvec(th[i, :3]); s = np.exp(th[i, 6])
    return r.apply((P - cen[i]) * s) + cen[i] + th[i, 3:6]
def 비용(x, 자세=False):
    th = x.reshape(K, 7)
    pts = np.vstack([변환(th, i, V[S[i]]) for i in range(K)])
    u = np.clip(np.round(pts[:, 0] + cu).astype(int), 0, mk.shape[1] - 1); r = np.clip(np.round(-pts[:, 2]).astype(int), 0, mk.shape[0] - 1)
    out = (dout[r, u] ** 2).mean()
    d, _ = cKDTree(pts[:, [0, 2]]).query(EP); cov = (np.minimum(d, 15) ** 2).mean()   # F2: 15 화소에서 자름 — 원화 마스크의 어깨 · 깃까지 덮으려 키우지 않게
    pa = np.vstack([변환(th, a, V[[v]]) for v, a in zip(bv, ba)]) if False else None
    ea = np.zeros((len(bv), 3)); eb = np.zeros((len(bv), 3))
    for i in range(K):
        sa = ba == i; sb = bb == i
        if sa.any(): ea[sa] = 변환(th, i, V[bv[sa]])
        if sb.any(): eb[sb] = 변환(th, i, V[bv[sb]])
    eg = ((ea - eb) ** 2).sum(1).mean()
    sm = (((th[nbl[:, 0]] - th[nbl[:, 1]]) ** 2).sum(1) * nbw).mean()
    pr = (th[:, :3] ** 2).sum() * 100 + (th[:, 3:6] ** 2).sum() * 0.05 + (th[:, 6] ** 2).sum() * (400 if VW else 100)   # F2: 부위 배율은 더 아낌(전체가 맡음)
    sv = sum(옆비용(pts, w) for w in VW) if VW else 0.0
    tot = out + cov + WE * eg + WS * sm + WP * pr + WV * sv
    return (tot, dict(밖=out, 덮음=cov, 경계=eg, 매끈=sm, 적게=pr, 옆34=sv)) if 자세 else tot
# F2: 옆 · 3/4 — 렌더와 같은 yaw(옆 80 · 3/4 35, 피치 10) 투영 → 원화 마스크 높이 · 위치에 맞춰(모양만) 밖 · 덮음
VW = []
for k, yaw, pit in ((2, 80, 0), (3, 35, 10)):
    mk2 = np.load(A + f"판_{k}_Z.npz")["m"].astype(bool); d2 = ndimage.distance_transform_edt(~mk2)
    e2 = mk2 & ~ndimage.binary_erosion(mk2); r2, c2 = np.nonzero(e2); ys, xs = np.nonzero(mk2)
    VW.append(dict(mk=mk2, d=d2, E=np.c_[c2, r2].astype(float), yaw=np.radians(yaw), pit=np.radians(pit), box=(ys.min(), ys.max(), xs.min(), xs.max()), flip=1))
def 투영(P, w):
    c, s_ = np.cos(w["yaw"]), np.sin(w["yaw"]); u = P[:, 0] * c + P[:, 1] * s_ * w["flip"]; dep = -P[:, 0] * s_ + P[:, 1] * c
    z = P[:, 2] * np.cos(w["pit"]) + dep * np.sin(w["pit"]); return u, z
def 옆비용(pts, w):
    u, z = 투영(pts, w); y0, y1, x0_, x1_ = w["box"]; h = z.max() - z.min(); s_ = (y1 - y0) / max(h, 1e-6)
    col = (u - u.min()) * s_ + x0_; row = (z.max() - z) * s_ + y0
    cc = np.clip(np.round(col).astype(int), 0, w["mk"].shape[1] - 1); rr = np.clip(np.round(row).astype(int), 0, w["mk"].shape[0] - 1)
    o_ = (np.minimum(w["d"][rr, cc], 15) ** 2).mean(); dd, _ = cKDTree(np.c_[col, row]).query(w["E"]); return (o_ + (np.minimum(dd, 15) ** 2).mean()) / s_ ** 2
WV = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
allS = np.concatenate(S)
for w in VW:   # 앞 방향(좌우 뒤집힘) 고르기
    a = 옆비용(V[allS], w); w["flip"] = -1; b = 옆비용(V[allS], w); w["flip"] = 1 if a <= b else -1; print("옆 방향", w["flip"], round(a), round(b))
# F2: 원화 윤곽점은 처음 모델 실루엣 12 화소 안의 것만(원화 마스크엔 깃 · 어깨판까지 들어 있어 덮으려 키웠다)
_p0 = V[allS]; _t = cKDTree(_p0[:, [0, 2]]); EP = EP[_t.query(EP)[0] < 12]
for w in VW:
    u_, z_ = 투영(_p0, w); y0, y1, x0_, x1_ = w["box"]; s_ = (y1 - y0) / (z_.max() - z_.min())
    pc = np.c_[(u_ - u_.min()) * s_ + x0_, (z_.max() - z_) * s_ + y0]; w["E"] = w["E"][cKDTree(pc).query(w["E"])[0] < 12 * s_ / max(s_, 1)]
print("윤곽점", len(EP), [len(w["E"]) for w in VW])
# F2: 전체 닮음 변환 먼저(정면 항만) — F1 은 부위 변형이 대부분 「전체 키우기」였다
gc = V.mean(0)
def 전체(g, P): return Rot.from_rotvec(g[:3]).apply((P - gc) * np.exp(g[6])) + gc + g[3:6]
def 정면만(g):
    pts = 전체(g, V[allS]); u = np.clip(np.round(pts[:, 0] + cu).astype(int), 0, mk.shape[1] - 1); r = np.clip(np.round(-pts[:, 2]).astype(int), 0, mk.shape[0] - 1)
    d, _ = cKDTree(pts[:, [0, 2]]).query(EP); return (np.minimum(dout[r, u], 15) ** 2).mean() + (np.minimum(d, 15) ** 2).mean() + (g[:3] ** 2).sum() * 1000
import os
g = np.zeros(7) if os.environ.get("NOGLOBAL") else minimize(정면만, np.zeros(7), method="Powell", options=dict(maxiter=4000)).x   # F2b: 전체 정렬이 정면 밖으로 넘치게 키워(밖 53 → 82) 끄고 비교
print("전체", np.degrees(np.linalg.norm(g[:3])).round(1), g[3:6].round(1), round(float(np.exp(g[6])), 3))
V = 전체(g, V); cen = np.array([V[np.unique(m.faces[L == i])].mean(0) for i in range(K)])
x0 = np.zeros(K * 7); print("시작", {k: round(v, 2) for k, v in 비용(x0, True)[1].items()})
res = minimize(비용, x0, method="L-BFGS-B", options=dict(maxiter=300, maxfun=60000, eps=1e-3, ftol=1e-12, gtol=1e-8))   # F2: 화소 반올림이라 기본 간격(1e-8)이면 기울기 0
th = res.x.reshape(K, 7); print("끝", res.nit, {k: round(v, 2) for k, v in 비용(res.x, True)[1].items()})
# 꼭짓점 = 그 꼭짓점을 쓰는 부위 변환의 평균
NV = np.zeros_like(V); cnt = np.zeros(len(V))
for i in range(K):
    vs = np.unique(m.faces[L == i]); NV[vs] += 변환(th, i, V[vs]); cnt[vs] += 1
NV /= np.maximum(cnt, 1)[:, None]
out = trimesh.Trimesh(NV, m.faces, process=False); out.visual.vertex_colors = np.tile([228, 232, 240, 255], (len(NV), 1)).astype(np.uint8); out.export(B + nm + ".ply")
tab = {G["노드"][[d["id"] for d in G["노드"]].index(p)]["이름(눈)"]: dict(회전도=np.degrees(np.linalg.norm(th[i, :3])).round(1).item(), 이동=th[i, 3:6].round(1).tolist(), 배율=round(float(np.exp(th[i, 6])), 3)) for p, i in ix.items()}
json.dump(tab, open(O + nm + "_변환.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in sorted(tab.items(), key=lambda kv: -np.linalg.norm(kv[1]["이동"]))[:8]: print(k, v)
