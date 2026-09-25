# -*- coding: utf-8 -*-
r"""디자인 판 1바퀴 비평 — D1 몸통 + D2 다리 + D3 머리어깨 조립 렌더 · 블록 경계 · 주요 관절 가동.

    python 실험_20260925/비평_조립.py [--가동없이]
    -> out/출력/오메가몬_PG/디자인/조립_1바퀴.png · 조립_1바퀴.json

원화 → mm 는 골격(D2 · 관절.json)과 같은 창 좌표를 원화 픽셀에 맞춘 값(다리 창 마스크 IoU 0.992 / 0.987):
  정면 x = (열 − 534)·0.342 · z = (951 − 행)·0.342   /   옆 y = (열 − 462)·0.349 · z = (938 − 행)·0.349
가동: 자식 하위 트리 부품을 +0.3 부풀려 나머지 모든 외장과의 교집합 V(θ). 0° 에서 3° 씩 밖으로, V − V(0) ≥ 0.5 mm³ 에서 멈춤."""
import os, sys, json, glob, time
import numpy as np, trimesh, manifold3d as M
from scipy.spatial import cKDTree
from PIL import Image

ROOT = r"G:\art2real\원화3d"; D = os.path.join(ROOT, r"out\출력\오메가몬_PG\디자인")
ART = r"G:\art2real\트레일\trail7_part3d\in"
t0 = time.time()
def log(*a): print("[%4.0fs]" % (time.time() - t0), *a, flush=True)
관 = {a["이름"]: a for a in json.load(open(os.path.join(ROOT, r"out\가동\관절.json"), encoding="utf-8"))["관절"]}
FRONT = (534.0, 951.0, 0.342); SIDE = (462.0, 938.0, 0.349)

# ── 부품 · 뼈 배정 · 색 ──
def 뼈(blk, n):
    s = n[0] if n[0] in "LR" else ""
    if blk == "몸통": return "가슴" if n.startswith(("가슴", "목깃")) else "복부" if n.startswith(("복부", "엠블럼")) else "허리"
    if blk == "다리":
        return s + ("허벅지" if "허벅지" in n else "정강이" if ("정강이" in n or "무릎" in n) else "발끝" if ("발끝" in n or "발톱" in n) else "발")
    if n.startswith(("투구", "얼굴", "뿔", "V안테나")): return "머리"
    if n in ("방패빨강", "방패금"): return "L어깨블록"
    if n.startswith("가시"): return "R어깨블록"
    if "윗팔위" in n: return s + "윗팔위"
    if "윗팔" in n: return s + "윗팔"
    return s + "어깨블록"
def 색(blk, n, info):
    if "색" in info: return tuple(info["색"])
    if "파랑" in n or "엠블럼" in n: return (0.30, 0.38, 0.75)
    if n.startswith("복부") and "혀" not in n: return (0.22, 0.22, 0.25)
    if "발톱" in n: return (0.90, 0.72, 0.20)
    return (0.90, 0.90, 0.92)
부품 = {}   # 이름 → (블록, 뼈, trimesh, 색)
for blk in ("몸통", "다리", "머리어깨"):
    info = json.load(open(os.path.join(D, blk, "부품.json"), encoding="utf-8"))["부품"]
    for n, p in info.items():
        m = trimesh.load(os.path.join(D, blk, p.get("파일", n + ".stl")))
        부품[n] = (blk, 뼈(blk, n), m, 색(blk, n, p))
뼈메시 = {os.path.basename(f)[:-4]: trimesh.load(f) for f in glob.glob(os.path.join(ROOT, r"out\가동\프레임\*.stl"))}
log("부품", len(부품), "뼈", len(뼈메시))
def 만(tm): return M.Manifold(M.Mesh(vert_properties=np.asarray(tm.vertices, np.float32), tri_verts=np.asarray(tm.faces, np.uint32)))
MF = {n: 만(v[2]) for n, v in 부품.items()}
bad = [n for n, m in MF.items() if m.status() != M.Error.NoError or m.is_empty()]
log("manifold 실패", bad)

# ── 블록 경계: 차렷 겹침 · 최소 틈 ──
def 표본(tm, k=8000):
    p, _ = trimesh.sample.sample_surface_even(tm, k) if len(tm.faces) else (np.zeros((0, 3)), None); return p
표 = {n: 표본(v[2]) for n, v in 부품.items()}
블록쌍 = {("몸통", "다리"), ("몸통", "머리어깨"), ("다리", "머리어깨")}
겹침, 틈 = [], {}
names = list(부품)
for i, a in enumerate(names):
    for b in names[i + 1:]:
        ba, bb = 부품[a][0], 부품[b][0]
        if ba == bb: continue
        ma, mb = MF[a], MF[b]
        v = (ma ^ mb).volume()
        if v > 0.01: 겹침.append((a, b, round(v, 2)))
        d = cKDTree(표[b]).query(표[a])[0].min() if len(표[a]) and len(표[b]) else 99
        if d < 6: 틈[a + "↔" + b] = round(float(d), 2)
log("차렷 블록간 겹침", 겹침); log("블록간 가까운 짝(<6mm)", 틈)
# 외장 ∩ 뼈 (다른 뼈에 붙은 외장이 뼈를 먹는지)
뼈겹 = []
for n, (blk, b, tm, c) in 부품.items():
    for bn, btm in 뼈메시.items():
        if bn == b: continue
        try: v = (MF[n] ^ 만(btm)).volume()
        except Exception: continue
        if v > 0.5: 뼈겹.append((n, bn, round(v, 1)))
log("외장 ∩ 남의 뼈", 뼈겹)

# ── 가동 ──
def 회전행렬(a, θ):
    a = np.asarray(a, float); a = a / np.linalg.norm(a); K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]]); t = np.radians(θ)
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K
def 강체(R, p): p = np.asarray(p, float); return np.c_[R, p - R @ p]
def 합성(A, B): return np.c_[A[:, :3] @ B[:, :3], A[:, :3] @ B[:, 3] + A[:, 3]]
자식 = {}
for a in 관.values(): 자식.setdefault(a["부모뼈"], []).append(a["자식뼈"])
def 하위(b): out = {b}; [out.update(하위(c)) for c in 자식.get(b, [])]; return out
def 틀(j, 축, θ):
    if j["종류"] == "이중힌지":
        P2 = j["외피"]["둘째축피벗mm"]; return 합성(강체(회전행렬(축, θ / 2), j["피벗mm"]), 강체(회전행렬(축, θ / 2), P2))
    return 강체(회전행렬(축, θ), j["피벗mm"])
부풀캐시 = {}
def 부풀(n):
    if n not in 부풀캐시:
        try: 부풀캐시[n] = MF[n].minkowski_sum(M.Manifold.sphere(0.3, 8))
        except Exception: 부풀캐시[n] = MF[n]
    return 부풀캐시[n]
def bb겹(a, b): return all(a[k] <= b[k + 3] and b[k] <= a[k + 3] for k in range(3))
def V(움, 고, T):
    tot, 짝 = 0.0, {}
    gbb = {g: MF[g].bounding_box() for g in 고}
    for n in 움:
        mt = 부풀(n).transform(T); bb = mt.bounding_box()
        for g in 고:
            if bb겹(bb, gbb[g]):
                v = (mt ^ MF[g]).volume()
                if v > 1e-3: 짝[(n, g)] = v; tot += v
    return tot, 짝
def 재기(jn, k, step=3):
    j = 관[jn]; r = j["범위"][k]; 하 = 하위(j["자식뼈"])
    움 = [n for n, v in 부품.items() if v[1] in 하]; 고 = [n for n in 부품 if n not in 움]
    V0, _ = V(움, 고, 틀(j, r["축"], 0.0)); res = {"목표": [r["최소"], r["최대"]], "V0": round(V0, 1)}
    for sgn, lim in ((-1, r["최소"]), (1, r["최대"])):
        got, who = 0, None
        for θ in range(step, abs(lim) + step, step):
            θ = min(θ, abs(lim)); v, 짝 = V(움, 고, 틀(j, r["축"], sgn * θ))
            if v - V0 >= 0.5:
                who = max(짝.items(), key=lambda q: q[1])[0]; break
            got = θ
            if θ == abs(lim): break
        res["-" if sgn < 0 else "+"] = sgn * got; res["막힘" + ("-" if sgn < 0 else "+")] = "·".join(who) if who else None
    return res
가동 = {}
if "--가동없이" not in sys.argv:
    for jn, ks in [("목위", (0, 1, 2)), ("목아래", (0,)), ("L어깨들기", (0,)), ("R어깨들기", (0,)), ("L어깨스윙", (0,)),
                   ("복부허리", (0,)), ("가슴복부", (0,)), ("L고관절벌림", (0,)), ("L고관절", (0,)), ("L허벅지회전", (0,)),
                   ("L무릎", (0,)), ("L발목", (0,)), ("L발목볼", (1,))]:
        for k in ks:
            가동[f"{jn}[{k}]"] = 재기(jn, k); log(jn, k, 가동[f"{jn}[{k}]"])

# ── 실루엣(골격 척도) : 블록별 정면 · 옆 투영 대 원화 ──
def 원마스크(f): return np.array(Image.open(os.path.join(ART, f)))[:, :, 3] > 127
Af, As = 원마스크("omega_front_clean.png"), 원마스크("omega_side.png")
def 투영(names, ax):   # ax 0 = 정면(x,z) · 1 = 옆(y,z) → 0.5 mm 격자 마스크
    g = np.zeros((360, 700), bool)   # u −90..90 · z −10..340
    from matplotlib.path import Path
    for n in names:
        tm = 부품[n][2]; P = tm.vertices[:, [ax, 2]]
        for f in tm.faces:
            q = P[f]; lo = np.floor((q.min(0) - [-90, -10]) / 0.5).astype(int); hi = np.ceil((q.max(0) - [-90, -10]) / 0.5).astype(int)
            if (hi - lo).prod() == 0: continue
            uu, zz = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1), indexing="ij")
            pts = np.c_[uu.ravel() * 0.5 - 90, zz.ravel() * 0.5 - 10]
            ins = Path(q).contains_points(pts, radius=1e-6) | Path(q[::-1]).contains_points(pts, radius=1e-6)
            u2, z2 = uu.ravel()[ins], zz.ravel()[ins]; ok = (u2 >= 0) & (u2 < 360) & (z2 >= 0) & (z2 < 700); g[u2[ok], z2[ok]] = True
    return g
def 원격자(A, cal):
    cx, r0, s = cal; uu, zz = np.meshgrid(np.arange(360) * 0.5 - 90, np.arange(700) * 0.5 - 10, indexing="ij")
    r = np.round(r0 - zz / s).astype(int); c = np.round(cx + uu / s).astype(int); ok = (r >= 0) & (r < 1024) & (c >= 0) & (c < 1024)
    g = np.zeros(uu.shape, bool); g[ok] = A[r[ok], c[ok]]; return g
원F, 원S = 원격자(Af, FRONT), 원격자(As, SIDE)
def 폭행(g, z, lo, hi):   # z 행의 u 구간 [lo,hi] 안 첫/끝 참
    j = int(round((z + 10) / 0.5)); col = g[:, j]; u = np.arange(360) * 0.5 - 90; w = u[(col) & (u >= lo) & (u <= hi)]
    return (w.min(), w.max()) if len(w) else None
실루 = {}
for 이름, ns, ax, g, zr, ur in [("몸통 정면", [n for n in 부품 if 부품[n][0] == "몸통"], 0, 원F, (190, 250), (-34, 34)),
                              ("머리 정면", [n for n in 부품 if 부품[n][1] == "머리" and "안테나" not in n], 0, 원F, (262, 285), (-16, 16)),
                              ("몸통 옆", [n for n in 부품 if 부품[n][0] == "몸통"], 1, 원S, (190, 250), (-30, 60))]:
    mg = 투영(ns, ax); rows = []
    for z in np.arange(zr[0], zr[1], 2.0):
        a, b = 폭행(mg, z, *ur), 폭행(g, z, *ur)
        if a and b: rows.append((float(z), round(a[0] - b[0], 1), round(a[1] - b[1], 1)))
    실루[이름] = rows; log("실루엣(골격 척도)", 이름, rows)

json.dump(dict(설명=__doc__, 차렷블록겹침mm3=겹침, 블록간최소틈mm=틈, 외장_남의뼈_겹침mm3=뼈겹, 가동=가동, 실루엣_모형빼기원화mm=실루),
          open(os.path.join(D, "조립_1바퀴.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ── 그림 ──
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
def 보기R(yaw, pitch):
    a, b = np.radians(yaw), np.radians(pitch)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    base = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
    Rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    return Rx @ base @ Rz
옆R = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], float)
def 그리기(ax, R, 뼈도=True):
    L = np.array([0.35, -0.6, 0.72]); L /= np.linalg.norm(L)
    items = [(v[2], v[3], 1.0) for v in 부품.values()] + ([(m, (0.55, 0.75, 0.55), 0.35) for m in 뼈메시.values()] if 뼈도 else [])
    P, C, Dd = [], [], []
    for tm, c, al in items:
        v, f = tm.vertices, tm.faces; tri = (v @ R.T)[f]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nn = np.linalg.norm(n, axis=1) + 1e-12
        vis = n[:, 2] / nn > 0
        wn = np.cross(v[f][:, 1] - v[f][:, 0], v[f][:, 2] - v[f][:, 0]) / nn[:, None]
        sh = 0.35 + 0.65 * np.clip(wn @ L, 0, 1)
        cc = np.clip(np.array(c)[None] * sh[:, None], 0, 1); cc = np.c_[cc, np.full(len(cc), al)]
        P += list(tri[vis][:, :, :2]); C += list(cc[vis]); Dd += list(tri[vis][:, :, 2].mean(1))
    o = np.argsort(Dd)
    ax.add_collection(PolyCollection([P[i] for i in o], facecolors=[C[i] for i in o], edgecolors=[C[i] for i in o], linewidths=0.05))
    ax.autoscale(); ax.set_aspect("equal")
def 원그림(ax, f, cal, alpha=1.0):
    cx, r0, s = cal; im = Image.open(os.path.join(ART, f)).convert("RGBA"); bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    ax.imshow(np.array(bg.convert("RGB")), extent=[(0 - cx) * s, (1024 - cx) * s, (r0 - 1024) * s, r0 * s], alpha=alpha)
def 윤곽(ax, g, col="r"):
    ax.contour(np.arange(360) * 0.5 - 90, np.arange(700) * 0.5 - 10, g.T.astype(float), [0.5], colors=col, linewidths=0.7)
fig, axs = plt.subplots(1, 6, figsize=(36, 13))
ax = axs[0]; 원그림(ax, "omega_front_clean.png", FRONT); ax.set_title("원화 정면 (골격 척도 mm)"); ax.set_xlim(-95, 95); ax.set_ylim(-8, 318); ax.grid(alpha=0.3)
ax = axs[1]; 그리기(ax, 보기R(0, 0)); 윤곽(ax, 원F); ax.set_title("조립 정면 · 빨강 = 원화 윤곽 · 초록 = 뼈"); ax.set_xlim(-95, 95); ax.set_ylim(-8, 318); ax.grid(alpha=0.3)
ax = axs[2]; 원그림(ax, "omega_side.png", SIDE); ax.set_title("원화 옆 (왼쪽 = 앞)"); ax.set_xlim(-60, 100); ax.set_ylim(-8, 318); ax.grid(alpha=0.3)
ax = axs[3]; 그리기(ax, 옆R); 윤곽(ax, 원S); ax.set_title("조립 옆 (+x 에서 · 왼쪽 = 앞)"); ax.set_xlim(-60, 100); ax.set_ylim(-8, 318); ax.grid(alpha=0.3)
ax = axs[4]; 그리기(ax, 보기R(-35, 10), False); ax.set_title("3/4 앞"); ax.axis("off")
ax = axs[5]; 그리기(ax, 보기R(145, 10), False); ax.set_title("3/4 뒤"); ax.axis("off")
fig.suptitle("오메가몬 PG 디자인 판 1바퀴 조립 — D1 몸통 · D2 다리 · D3 머리어깨 (%d 부품) · 팔꿈치 아래 · 칼 · 대포 없음" % len(부품), fontsize=16)
fig.tight_layout(); fig.savefig(os.path.join(D, "조립_1바퀴.png"), dpi=80); plt.close(fig)
# 확대: 목 · 어깨 · 골반 경계
fig, axs = plt.subplots(1, 4, figsize=(28, 10))
for ax, R, t, xl, yl in [(axs[0], 보기R(0, 0), "정면 확대 목·어깨", (-65, 65), (215, 300)), (axs[1], 보기R(0, 0), "정면 확대 골반", (-50, 50), (120, 215)),
                         (axs[2], 옆R, "옆 확대 목·어깨", (-25, 60), (215, 300)), (axs[3], 옆R, "옆 확대 골반", (-25, 60), (120, 215))]:
    그리기(ax, R); 윤곽(ax, 원F if R is not 옆R else 원S); ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_title(t); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(D, "조립_1바퀴_경계.png"), dpi=80); plt.close(fig)
log("끝")
