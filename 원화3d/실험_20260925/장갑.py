# -*- coding: utf-8 -*-
"""**장갑** — 오메가몬 PG 급(300 mm) 가동 키트의 장갑(외장) · 뼈 · 관절 부품을 한 벌로 묶는다 (2026-09-25).

    python 장갑.py [틈=0.20]      (단계 캐시: out/출력/오메가몬_PG/_캐시 — 몸.npz · 부품.pkl. 지우면 다시 짓는다)
      -> out/출력/오메가몬_PG/장갑/*.stl · 프레임/*.stl · 관절/*.stl (출력 자세) · _조립/*.stl (조립 좌표) · 키트.json
         out/부품속_PG.html

좌표 = 관절.json 과 같다: mm · 원점 발바닥 중앙 · [x 좌우, y 깊이(작은 y 가 앞), z 높이]. 관절 · 뼈는 **이름으로** 읽는다.
  ① 몸 = 384 장 ∩ 192 키트 몸 (골격.py 와 같은 몸). 윗팔(팔꿈치 ~ 어깨들기 −12 mm)은 원화 정면 폭을 지름으로 하는 원통으로 바꾼다
     (옆 원화에 팔이 없어 몸통 깊이를 빌린 12 × 40 판이었다). 축 = 윗팔 뼈 선(윗팔회전 → 팔꿈치).
  ② 껍질 = 몸 부호거리(σ 1 칸 매끈) 0 등위면 − (−두께) 등위면. 뼈(+비움틈) · 관절 외피(+비움틈) · 관절 부품 볼록껍질(+비움틈)을 뺀다.
  ③ 가르기 = 부품짓기.py 방식(부풀린 라벨 ∩ 껍질 − 이웃 쪽 영역(이음 근처만) − 앞 부품). 같은 뼈 짝 = E13 평면(다보),
     다른 뼈 짝 = 그 사이 관절의 **회전면**: 축 → 축에 수직 평면 · 볼 → 피벗 중심 구 · 힌지 → 축 둘레 원통 ∪ 자식 쪽 반공간.
     회전면이면 자식이 관절을 따라 돌아도 이음면이 제자리에서 미끄러진다. 구 · 원통이 이음을 못 따라가면(맞춤 rms > 문턱) E13 평면 + 틈.
     라벨은 회전면 쪽으로 다시 칠해(이음 근처만) 부풀림 · 이음 근처가 새 면을 덮게 한다.
  ④ 결합: 장갑 → 뼈 = 장갑 안쪽 보스(Ø4) 끝 핀 Ø1.8 × 2.5 가 뼈 구멍(핀 + 틈)에. 같은 뼈 반쪽끼리 = 이음면 다보(패드 Ø4.2 를 껍질 안쪽에 덧대고 핀/구멍).
  ⑤ 관절 부품 = 관절부품.py 만들기(규격) 를 관절 자리에 (지역 z = 자식 쪽 · 힌지 x = 관절 축). 뼈 = 프레임 STL − 관절 부품 볼록껍질 + D 촉.
  ⑥ STL 을 다시 읽어 닫힘 검사. 자기 접촉(한 점에 겹친 정점)은 그 점마다 작은 구(0.06 mm)를 깎아 뗀다."""
import os, sys, json, time, base64, graphlib, pickle, subprocess, shutil
os.environ.setdefault("OMP_NUM_THREADS", "4")
import numpy as np, trimesh, manifold3d as M
from scipy import ndimage
from skimage.measure import marching_cubes
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 부품짓기 as PJ

ROOT = r"G:\art2real\원화3d"
가동 = os.path.join(ROOT, "out", "가동"); E13 = os.path.join(ROOT, "out", "분할후보", "E13")
OUT = os.path.join(ROOT, "out", "출력", "오메가몬_PG"); 캐시 = os.path.join(OUT, "_캐시")
두께, 비움틈, 관절틈 = 2.0, 0.4, 0.3            # 장갑 · 뼈/외피 둘레 빈틈 · 움직이는 이음 틈(전체)
결합틈 = float(sys.argv[1]) if len(sys.argv) > 1 else 0.20      # 한쪽 · 공차 쿠폰 결과로 바꾼다
핀r, 핀길이, 벽, 바닥벽 = 0.9, 2.5, 1.0, 0.8     # 다보 · 보스 핀 (부품짓기와 같음)
보스r = 2.0
맞춤문턱 = 2.5                                 # 회전면 맞춤 rms (mm)
t0 = time.time()
def 로그(*a): print("[%4.0fs]" % (time.time() - t0), *a, flush=True)

# ── 공통 좌표 (골격.py 와 같은 식) ──────────────────────────────
d192 = np.load(os.path.join(ROOT, "out", "분할후보", "입력.npz")); O = d192["O"]; 축i = float(d192["축i"])
zs = np.nonzero(O.any((0, 1)))[0]; C = 300.0 / (zs[-1] - zs[0] + 1)
y0 = np.argwhere(O[:, :, zs[0]:zs[0] + 2])[:, 1].mean()
off = np.array([축i, y0, zs[0] - 0.5])
def mm(p): return (np.asarray(p, float) - off) * C          # 192 색인 → mm
h = C / 2; N4 = 384
b4 = (np.array([-0.25, -0.25, -0.25]) - off) * C           # 384 색인 q → mm = q h + b4
이름표 = {int(k): v for k, v in json.load(open(os.path.join(E13, "이름.json"), encoding="utf-8")).items()}
라벨 = {v: k for k, v in 이름표.items()}                      # E13 원래 이름 (앞/뒤 뒤집힘 그대로) → 번호
def _앞뒤바로():
    """E13 이름의 앞/뒤는 뒤집혀 있다 → y 평균이 작은 쪽을 「앞」으로 (작은 y 가 앞)."""
    lab = np.load(os.path.join(E13, "lab.npy")); 바꿈 = []
    for k, v in list(이름표.items()):
        if v.endswith("앞") and v[:-1] + "뒤" in 라벨:
            j = 라벨[v[:-1] + "뒤"]; ya = np.argwhere(lab == k)[:, 1].mean(); yb = np.argwhere(lab == j)[:, 1].mean()
            if ya > yb: 이름표[k], 이름표[j] = v[:-1] + "뒤", v; 바꿈.append(v[:-1])
    return 바꿈
앞뒤바꿈 = _앞뒤바로()
JJ = json.load(open(os.path.join(가동, "관절.json"), encoding="utf-8"))
관절 = {j["이름"]: j for j in JJ["관절"]}; 뼈 = JJ["뼈"]
X, Y, Z = np.eye(3)
def 단(v): v = np.asarray(v, float); return v / np.linalg.norm(v)
def P(n, k="피벗mm"): return np.array(관절[n][k] if k != "피벗2" else 관절[n]["외피"]["둘째축피벗mm"], float)


def 만(v, f):
    return PJ.만(v, f)


def 트(m):
    return PJ.트(m)


def 메시mm(mask, lo, 칸, b):
    """bool 칸 영역 → 닫힌 메시. 칸 q 중심 = (q + lo) 칸 + b."""
    f = np.pad(mask, 1).astype(np.float32); v, fc, _, _ = marching_cubes(f, 0.5)
    return 만((v - 1 + lo) * 칸 + b, fc)


def 칸메시192(mask):
    idx = np.argwhere(mask); lo = idx.min(0) - 1; hi = idx.max(0) + 2
    return 메시mm(mask[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]], lo, C, -off * C)


# ════════ ① 몸 · 윗팔 원통 · ② 껍질 ════════════════════════════
def 몸짓기():
    up = lambda a: a.repeat(2, 0).repeat(2, 1).repeat(2, 2)
    lab = np.load(os.path.join(E13, "lab.npy")).astype(np.int32)
    B = (np.load(os.path.join(가동, "장384.npz"))["g"] > 0) & up(O)
    lab4 = up(lab)
    q = np.arange(N4); ax = [q * h + b4[k] for k in range(3)]
    팔기록 = {}
    for s in "LR":
        ids = [라벨[s + "윗팔앞"], 라벨[s + "윗팔뒤"]]
        p0, p1 = P(s + "윗팔회전"), P(s + "팔꿈치"); a = 단(p1 - p0)
        zlo, zhi = p1[2], P(s + "어깨들기")[2] - 12.0
        A = np.isin(lab4, ids) & B
        ks = [k for k in range(N4) if zlo <= ax[2][k] <= zhi]
        w = np.array([(lambda xs: (xs[-1] - xs[0] + 1) * h if len(xs) else np.nan)(np.nonzero(A[:, :, k].any(1))[0]) for k in ks])
        w = ndimage.median_filter(np.nan_to_num(w, nan=np.nanmedian(w)), 7, mode="nearest"); r = w / 2
        # 새 원통 칸 (다른 라벨 칸은 건드리지 않는다)
        box = [np.nonzero((ax[i] > min(p0[i], p1[i]) - 25) & (ax[i] < max(p0[i], p1[i]) + 25))[0] for i in range(2)]
        I, Jy = np.meshgrid(box[0], box[1], indexing="ij")
        새 = np.zeros_like(B); 옛 = np.zeros_like(B)
        for k, rk in zip(ks, r):
            G = np.stack([ax[0][I], ax[1][Jy], np.full(I.shape, ax[2][k])], -1)
            t = (G - p0) @ a; d = np.linalg.norm(G - p0 - t[..., None] * a, axis=-1)
            m = (d <= rk) & ((lab4[I, Jy, k] == 0) | np.isin(lab4[I, Jy, k], ids))
            새[I[m], Jy[m], k] = True
            옛[:, :, k] = A[:, :, k]
        B &= ~(옛 & ~새); B |= 새
        # 192 라벨: 새 원통 칸(8 칸 중 4 이상) = 가까운 팔 라벨 · 옛 팔 칸 중 원통 밖 = 0
        n192 = 새.reshape(192, 2, 192, 2, 192, 2).sum((1, 3, 5)) >= 4
        o192 = 옛.reshape(192, 2, 192, 2, 192, 2).any((1, 3, 5))
        팔 = np.isin(lab, ids)
        _, 색인 = ndimage.distance_transform_edt(~팔, return_indices=True)
        가까운 = lab[tuple(색인)]
        lab[o192 & ~n192 & 팔] = 0
        m = n192 & ((lab == 0) | 팔); lab[m] = 가까운[m]
        팔기록[s] = dict(z범위mm=[round(zlo, 1), round(zhi, 1)], 지름mm=[round(float(2 * r.min()), 1), round(float(2 * r.max()), 1)],
                       중앙지름mm=round(float(2 * np.median(r)), 1), 윗팔회전외피R=관절[s + "윗팔회전"]["외피"]["반지름mm"])
        로그("윗팔 %s: z %.0f~%.0f 지름 %.1f~%.1f (중앙 %.1f) — 윗팔회전 외피 R %.1f + 2.4 = %.1f 필요" % (
            s, zlo, zhi, 2 * r.min(), 2 * r.max(), 2 * np.median(r), 관절[s + "윗팔회전"]["외피"]["반지름mm"], 관절[s + "윗팔회전"]["외피"]["반지름mm"] + 2.4))
    # 부호거리 (칸 중심, 밖 +) · 몸 상자만
    idx = np.argwhere(B); lo = np.maximum(idx.min(0) - 6, 0); hi = np.minimum(idx.max(0) + 7, N4)
    Bc = B[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    s = np.where(Bc, -(ndimage.distance_transform_edt(Bc) * h - h / 2), ndimage.distance_transform_edt(~Bc) * h - h / 2).astype(np.float32)
    s = ndimage.gaussian_filter(s, 1.0)
    s = np.pad(s, 1, constant_values=float(s.max()))
    겉 = []
    for lv in (0.0, -두께):
        v, f, _, _ = marching_cubes(s, lv)
        겉.append((v - 1 + lo) * h + b4)
        겉.append(f)
    np.savez_compressed(os.path.join(캐시, "몸.npz"), lab=lab, B=B, v0=겉[0], f0=겉[1], v1=겉[2], f1=겉[3])
    json.dump(팔기록, open(os.path.join(캐시, "팔.json"), "w", encoding="utf-8"), ensure_ascii=False)


# ════════ ⑤ 관절 부품 배치 · 뼈 (촉) ════════════════════════════
막대 = {}                                                     # E13 무기 원통 → 없는 자식 뼈(칼 · 대포)의 선
for e in json.load(open(os.path.join(E13, "평면.json"), encoding="utf-8")):
    if "원통" in e:
        o = e["원통"]; 키 = "L칼" if 라벨["L칼"] in e["짝"] else "R대포"
        a_ = 단(o["축"]); c_ = np.array(o["점"], float)
        막대[키] = dict(a=a_, p0=mm(c_ + o["t"][0] * a_), p1=mm(c_ + o["t"][1] * a_), r=o["반지름"] * C, 원통=o)


def 뼈선(n):
    """뼈 n 의 캡슐 토막들 [(a, b, ra, rb)] mm. 무기(칼 · 대포)는 E13 원통."""
    if n in 뼈:
        return [(np.array(p[:3]), np.array(q[:3]), p[3] / 2, q[3] / 2) for 줄 in 뼈[n]["마디"] for p, q in zip(줄[:-1], 줄[1:])]
    m = 막대[n]; return [(m["p0"], m["p1"], m["r"], m["r"])]


def 뼈중심(n):
    return np.mean([(a + b) / 2 for a, b, _, _ in 뼈선(n)], 0)


def 관절틀(j):
    """지역 → 세계 회전 R (열 = 지역 x, y, z). z = 자식 쪽 · 힌지 x = 관절 축 (관절부품.py 좌표)."""
    p, a = np.array(j["피벗mm"]), 단(j["축"])
    자 = 뼈중심(j["자식뼈"]) - p
    if j["종류"] in ("볼", "축"):
        z = a if a @ 자 >= 0 else -a
        x = 단(np.cross(Y, z)) if abs(z @ Y) < 0.9 else 단(np.cross(Z, z))
    else:
        x = a
        자 = (P(j["이름"], "피벗2") - p) if j["종류"] == "이중힌지" else 자
        z = 단(자 - (자 @ x) * x)
    y = np.cross(z, x); return np.c_[x, y, z]


def 놓기(m, R, t): return m.transform(np.c_[R, np.asarray(t, float)])


def 볼록덧(m, d, n=26):
    """m 의 볼록 껍질을 d 만큼 부풀린 근사 (정점 + 구 방향 점들의 껍질)."""
    v = np.asarray(m.to_mesh().vert_properties)[:, :3]
    k = np.arange(n) + 0.5; φ = np.arccos(1 - 2 * k / n); θ = np.pi * (1 + 5 ** 0.5) * k
    dirs = np.c_[np.cos(θ) * np.sin(φ), np.sin(θ) * np.sin(φ), np.cos(φ)]
    v = M.Manifold.hull_points((v[:, None, :] + d * dirs[None]).reshape(-1, 3))
    return v


def 캡슐(a, b, ra, rb, seg=24):
    return M.Manifold.batch_hull([M.Manifold.sphere(ra, seg).translate(tuple(a)), M.Manifold.sphere(rb, seg).translate(tuple(b))])


def 외피메시(j, 덧=0.0, seg=48):
    p, a = np.array(j["피벗mm"]), 단(j["축"]); e = j["외피"]; R = e["반지름mm"] + 덧
    if j["종류"] == "볼": return M.Manifold.sphere(R, seg).translate(tuple(p))
    L = e.get("길이mm", e.get("폭mm")) + 2 * 덧
    Rz = PJ.회전(a).T
    cy = lambda c: 놓기(M.Manifold.cylinder(L, R, R, seg, True), Rz, c)
    if j["종류"] == "이중힌지": return M.Manifold.batch_hull([cy(p), cy(P(j["이름"], "피벗2"))])
    return cy(p)


def 관절짓기():
    import 관절부품 as JB
    규 = json.load(open(os.path.join(가동, "관절규격.json"), encoding="utf-8"))
    _만듦 = {}
    놓인 = {}; 촉 = {}; 틀표 = {}
    for n, j in 관절.items():
        g = j["규격"].split("(")[0]
        if g not in _만듦: _만듦[g] = JB.만들기(g); 로그("  J2 %s 만듦" % g)
        jb = _만듦[g]; R = 관절틀(j); p = np.array(j["피벗mm"]); 틀표[n] = R
        s = jb["치수"].get("축사이", 0.0)
        for k, m in JB.부품들(jb).items():
            if k == "핀2": m = m.translate([0, 0, s])
            놓인[(n, k)] = dict(m=놓기(m, R, p), 자세=jb["자세"].get(k, "세움"), 지역=m)
        # 뼈 촉 (D 컷 · 구멍 − 2 결합틈) — 부모 뼈는 부모 부품 구멍으로, 자식 뼈는 자식 부품 구멍으로
        for 쪽, 뼈n in (("부모", j["부모뼈"]), ("자식", j["자식뼈"])):
            b = 규[g]["결합"][쪽]; 지 = b["구멍지름"]; 촉d = 지 - 2 * 결합틈; 면 = 지 / 2 - b["D컷"] - 결합틈
            z0 = b["입구xyz"][2]; sgn = 1 if b["방향"] == "+z" else -1
            lo_, hi_ = sorted([z0 - sgn * 3.0, z0 + sgn * (b["깊이"] - 0.3)])
            m = JB.D구멍z(촉d, lo_, hi_, 컷=촉d / 2 - 면)
            촉.setdefault(뼈n, []).append(dict(m=놓기(m, R, p), 관절=n, 쪽=쪽, 지름=round(촉d, 2), 입구=(R @ np.array(b["입구xyz"], float) + p).tolist()))
    return 놓인, 촉, 틀표


def 뼈짓기(놓인, 촉):
    """프레임 STL(J1 그대로) + 촉. 관절 부품을 뼈에서 깎지 않는다 — J2 부품(깃 · 소켓 몸)이 J1 외피보다 길어서 깎으면
    목 · 복부 · 윗팔 뼈가 90 % 넘게 사라진다(09-25 진단). 대신 뼈 ∩ 관절 부품 부피 · 뼈에 안 닿는 촉을 기록한다."""
    out, 기록 = {}, {}
    for n, b in 뼈.items():
        t = trimesh.load(os.path.join(가동, b["파일"])); m0 = 만(t.vertices, t.faces)
        ks = [(jn, k) for (jn, k) in 놓인 if k in ("부모", "자식") and 관절[jn]["부모뼈" if k == "부모" else "자식뼈"] == n]
        겹 = {"%s·%s" % x: round((m0 ^ 놓인[x]["m"]).volume(), 1) for x in ks}
        뜬 = [c["관절"] for c in 촉.get(n, []) if (c["m"] ^ m0).volume() < 0.05 * c["m"].volume()]
        m = m0 + M.Manifold.batch_boolean([c["m"] for c in 촉.get(n, [])], M.OpType.Add) if 촉.get(n) else m0
        out[n] = m; 기록[n] = dict(조각=len(m.decompose()), 촉=len(촉.get(n, [])), 뼈에안닿는촉=뜬,
                                  관절부품과겹침mm3={k: v for k, v in 겹.items() if v > 0.5}, 부피mm3=round(m.volume(), 1))
    return out, 기록


def 비움(놓인, 뼈m):
    """장갑에서 뺄 곳: 관절 외피 + 비움틈 · 관절 부품 볼록껍질 + 비움틈 · 뼈 캡슐 + 비움틈."""
    ms = [외피메시(j, 비움틈) for j in 관절.values()]
    ms += [볼록덧(v["m"], 비움틈) for v in 놓인.values()]
    ms += [캡슐(a, b, ra + 비움틈, rb + 비움틈) for n in 뼈 for a, b, ra, rb in 뼈선(n)]
    return M.Manifold.batch_boolean(ms, M.OpType.Add)


def 껍질짓기(놓인, 뼈m):
    d = np.load(os.path.join(캐시, "몸.npz"))
    def 큰것(m):
        cs = sorted(m.decompose(), key=lambda c: -c.volume()); return M.Manifold.batch_boolean([c for c in cs if c.volume() > 5.0], M.OpType.Add)
    겉 = 큰것(만(d["v0"], d["f0"])); 안 = 만(d["v1"], d["f1"])
    로그("겉 %.1f cm³ · 안 %.1f cm³" % (겉.volume() / 1000, 안.volume() / 1000))
    V = 비움(놓인, 뼈m)
    껍 = 겉 - 안 - V
    cs = sorted(껍.decompose(), key=lambda c: -c.volume())
    버림 = sum(c.volume() for c in cs if c.volume() < 1.0)
    껍 = M.Manifold.batch_boolean([c for c in cs if c.volume() >= 1.0], M.OpType.Add)
    로그("껍질 %.1f cm³ (조각 %d · 1 mm³ 미만 %d 개 %.2f mm³ 버림) · 비움과 겹친 장갑 %.1f mm³" % (
        껍.volume() / 1000, len(cs), sum(c.volume() < 1 for c in cs), 버림, ((겉 - 안) ^ V).volume()))
    return 겉, 껍, V


# ════════ ③ 라벨 → 뼈 · 관절 회전면 ════════════════════════════
뼈목록 = list(뼈) + list(막대)
부모of = {j["자식뼈"]: n for n, j in 관절.items()}               # 자식 뼈 → 그 위 관절


def 조상(b):
    out = [b]
    while b in 부모of: b = 관절[부모of[b]]["부모뼈"]; out.append(b)
    return out


def 길(a, b):
    """뼈 a · b 사이 관절들 (나무 길) · 각 관절에서 a 쪽이 자식이면 True."""
    A, Bn = 조상(a), 조상(b); 공 = next(x for x in A if x in Bn)
    return [(부모of[x], True) for x in A[:A.index(공)]] + [(부모of[x], False) for x in Bn[:Bn.index(공)]]


def 최근뼈(Pm):
    """점들(mm) → 가장 가까운 뼈 번호 (캡슐 겉까지 거리)."""
    D = np.full((len(Pm), len(뼈목록)), np.inf)
    for i, n in enumerate(뼈목록):
        for a, b, ra, rb in 뼈선(n):
            ab = b - a; t = np.clip(((Pm - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
            d = np.linalg.norm(Pm - a - t[:, None] * ab, axis=1) - (ra + t * (rb - ra)); D[:, i] = np.minimum(D[:, i], d)
    return D.argmin(1)


def 줄기(s): return s[:-1] if s[-1:] in ("앞", "뒤") else s


가를관절 = ["L윗팔회전", "R윗팔회전", "L발끝", "R발끝"]        # 한 블록 안에 든 관절 — 블록을 회전면으로 가른다 (J1 과제 ③)
# 규칙(최다 뼈)이 틀린 블록: 팔 덮개(워그레이몬 · 메탈가루루몬 머리)는 팔끝(아래팔)에 붙는다.
# 규칙대로면 L팔끝주황 = 윗팔(0.57 : 팔끝 0.54 : 손 0.53 — 팔꿈치 위까지 덮어서) · R늑대 = 대포(무기 막대가 가장 가까워서).
뼈고정 = {"L팔끝주황": "L팔끝", "L팔끝": "L팔끝", "R늑대": "R팔끝"}


def 뼈배정(lab):
    """블록(앞 · 뒤 반쪽 합) 칸마다 가장 가까운 뼈를 세어 최다 뼈. 둘째가 첫째의 바로 아래 자식이고 몫 ≥ 0.40 이면 자식 (관절 경계)."""
    idx = np.argwhere(lab > 0); nb = 최근뼈(mm(idx)); L = lab[tuple(idx.T)]
    블 = {}
    for k in np.unique(L): 블.setdefault(줄기(이름표[int(k)]), []).append(int(k))
    표 = {}
    for b, ks in 블.items():
        c = np.bincount(nb[np.isin(L, ks)], minlength=len(뼈목록)); o = np.argsort(-c)
        몫 = {뼈목록[i]: round(float(c[i] / c.sum()), 2) for i in o[:3] if c[i]}
        b1 = 뼈목록[o[0]]; b2 = 뼈목록[o[1]] if c[o[1]] else None; 고름 = b1
        if b2 and 몫[b2] >= 0.40 and b2 in 부모of and 관절[부모of[b2]]["부모뼈"] == b1: 고름 = b2
        if b in 뼈고정: 고름 = 뼈고정[b]
        for k in ks: 표[k] = dict(블록=b, 뼈=고름, 몫=몫, 고정=b in 뼈고정)
    return 표


def 가르기(lab, 표):
    """가를관절: 자식 뼈가 붙은 블록 칸 중 부모 쪽(지역 z < 0) 칸 → 새 라벨(부모 뼈) — 또는 반대."""
    새번호 = int(lab.max()) + 1; 기록 = []
    idx = np.argwhere(lab > 0); Pm = mm(idx); L = lab[tuple(idx.T)]
    for n in 가를관절:
        j = 관절[n]; z = 관절틀(j)[:, 2]; p = np.array(j["피벗mm"]); 부, 자 = j["부모뼈"], j["자식뼈"]
        ks = [k for k, v in 표.items() if v["뼈"] in (부, 자) and 부 in v["몫"] and 자 in v["몫"]]
        if not ks: 기록.append((n, "블록 없음")); continue
        t = (Pm - p) @ z
        for k in ks:
            옮길쪽 = (t < 0) if 표[k]["뼈"] == 자 else (t >= 0)
            m = (L == k) & 옮길쪽
            if m.sum() < 20: continue
            lab[tuple(idx[m].T)] = 새번호
            새뼈 = 부 if 표[k]["뼈"] == 자 else 자
            이름표[새번호] = (새뼈 + ("앞" if 이름표[k].endswith("앞") else "뒤" if 이름표[k].endswith("뒤") else "")) + "*"
            표[새번호] = dict(블록=줄기(이름표[새번호]), 뼈=새뼈, 몫={}, 가름=n)
            기록.append((n, 이름표[k], "→", 이름표[새번호], int(m.sum()))); 새번호 += 1
    return 기록


def 상자(idx, r, N=192):
    return np.maximum(idx.min(0) - r - 1, 0), np.minimum(idx.max(0) + r + 2, N)


def 교(a, b):
    """잘린 칸 (lo, arr) 둘의 교집합 → (lo, arr) 또는 None."""
    lo = np.maximum(a[0], b[0]); hi = np.minimum(a[0] + a[1].shape, b[0] + b[1].shape)
    if np.any(hi <= lo): return None
    sa = tuple(slice(l - o, h - o) for l, h, o in zip(lo, hi, a[0])); sb = tuple(slice(l - o, h - o) for l, h, o in zip(lo, hi, b[0]))
    r = a[1][sa] & b[1][sb]; return (lo, r) if r.any() else None


def 칸메시c(cr):
    lo, arr = cr; idx = np.argwhere(arr); l2 = idx.min(0); h2 = idx.max(0) + 1
    return 메시mm(arr[l2[0]:h2[0], l2[1]:h2[1], l2[2]:h2[2]], lo + l2, C, -off * C)


def 면들(lab):
    """짝 → 면 행 [(i, j, k, 축, 부호)] (부품짓기와 같다)."""
    N = lab.shape[0]; 면 = {}
    for a in range(3):
        a0 = np.take(lab, range(N - 1), axis=a); a1 = np.take(lab, range(1, N), axis=a)
        s = (a0 != a1) & (a0 > 0) & (a1 > 0); idx = np.argwhere(s)
        for p, x, y in zip(idx, a0[s], a1[s]):
            k, j = (x, y) if x < y else (y, x)
            면.setdefault((int(k), int(j)), []).append((*p, a, 1 if x < y else -1))
    return {kj: np.array(r) for kj, r in 면.items()}


def 면점(rows):
    Pi = rows[:, :3].astype(float); ax = rows[:, 3]; Pi[np.arange(len(Pi)), ax] += 0.5; return Pi, ax


def 관절짝(표, 면, 뺄=()):
    """다른 뼈 짝 → 관절 { 관절: [((k, j), 자식 쪽 라벨)] }. 뼈 짝마다 하나: 길 위 관절 중 피벗이 (그 뼈 짝 모든 이음의) 무게중심에 가장 가까운 것."""
    묶 = {}
    for (k, j), rows in 면.items():
        if (k, j) in 뺄: continue
        bk, bj = 표[k]["뼈"], 표[j]["뼈"]
        if bk != bj: 묶.setdefault(tuple(sorted((bk, bj))), []).append((k, j))
    짝들 = {}
    for (ba, bb), kjs in 묶.items():
        c = mm(np.concatenate([면점(면[kj])[0] for kj in kjs])).mean(0)
        n, a자식 = min(길(ba, bb), key=lambda t: np.linalg.norm(np.array(관절[t[0]]["피벗mm"]) - c))
        자뼈 = ba if a자식 else bb
        for k, j in kjs: 짝들.setdefault(n, []).append(((k, j), k if 표[k]["뼈"] == 자뼈 else j))
    return 짝들


def 회전면(n, Pm):
    """관절 n 의 이음 점들 Pm(mm) → 회전면 매개변수. Rc = 구/원통(r) ∪ {(p−피벗)·z ≥ t}."""
    j = 관절[n]; R = 관절틀(j); z = R[:, 2]; p = np.array(j["피벗mm"]); e = j["외피"]["반지름mm"]
    t = (Pm - p) @ z; s = dict(관절=n, 종류=j["종류"], c=p, z=z, t=float(np.median(t)), t_rms=float(np.sqrt(np.mean((t - np.median(t)) ** 2))))
    if j["종류"] == "축": s.update(모양="평면", r=0.0); return s
    if j["종류"] == "볼": d = np.linalg.norm(Pm - p, axis=1); s["모양"] = "구"
    else:
        a = R[:, 0]; q = Pm - p; d = np.linalg.norm(q - np.outer(q @ a, a), axis=1); s["모양"] = "원통"; s["a"] = a
    med = float(np.median(d)); rms = float(np.sqrt(np.mean((d - med) ** 2)))
    s["맞춤rms"] = round(rms, 2)
    s["r"] = max(med, e + 0.3) if rms <= 맞춤문턱 else e + 0.3        # 이음을 못 따라가면 외피 + 0.3 (축이 껍질을 뚫는 곳만 둥글게)
    s["r근거"] = "이음 중앙거리" if rms <= 맞춤문턱 else "외피+0.3"
    return s


def Rc안(s, Pm, 덧=0.0):
    t = (Pm - s["c"]) @ s["z"]; m = t >= s["t"] - 덧
    if s["모양"] == "구": m |= np.linalg.norm(Pm - s["c"], axis=1) < s["r"] + 덧
    elif s["모양"] == "원통":
        q = Pm - s["c"]; m |= np.linalg.norm(q - np.outer(q @ s["a"], s["a"]), axis=1) < s["r"] + 덧
    return m


def Rc메시(s, 덧=0.0):
    m = PJ.반공간(s["z"], s["c"] + s["z"] * (s["t"] - 덧))
    if s["모양"] == "구": m = m + M.Manifold.sphere(s["r"] + 덧, 96).translate(tuple(s["c"]))
    elif s["모양"] == "원통": m = m + 놓기(M.Manifold.cylinder(400, s["r"] + 덧, s["r"] + 덧, 96, True), PJ.회전(s["a"]).T, s["c"])
    return m


def 다시칠(lab, 표, 짝들, 면):
    """관절 짝 둘레(이음에서 12 mm) 칸을 회전면 쪽으로 다시 칠한다 — 반대쪽 라벨 중 가장 가까운 것으로."""
    기록 = {}
    for n, 목록 in 짝들.items():
        Pi = np.concatenate([면점(면[kj])[0] for kj, _ in 목록]); s = 회전면(n, mm(Pi)); 기록[n] = s
        자라벨 = {c for _, c in 목록}; 부라벨 = {x for kj, c in 목록 for x in kj} - 자라벨
        # 같은 쪽 뼈 라벨도 대상에 넣는다 (반쪽 짝이 다른 라벨일 수 있음)
        자뼈 = {표[c]["뼈"] for c in 자라벨}; 부뼈 = {표[c]["뼈"] for c in 부라벨}
        자라벨 |= {k for k, v in 표.items() if v["뼈"] in 자뼈}; 부라벨 |= {k for k, v in 표.items() if v["뼈"] in 부뼈}
        q = np.clip(np.floor(Pi).astype(int), 0, lab.shape[0] - 1); lo, hi = 상자(q, 14)
        sl = tuple(slice(a, b) for a, b in zip(lo, hi)); sub = lab[sl]
        zone = np.zeros(sub.shape, bool); zone[tuple((q - lo).T)] = True
        zone = (ndimage.distance_transform_edt(~zone) * C <= 12.0) & np.isin(sub, list(자라벨 | 부라벨))
        idx = np.argwhere(zone); 안 = Rc안(s, mm(idx + lo)); L = sub[tuple(idx.T)]
        틀림자 = 안 & ~np.isin(L, list(자라벨)); 틀림부 = ~안 & ~np.isin(L, list(부라벨))
        새 = sub.copy()
        for 틀림, 쪽 in ((틀림자, 자라벨), (틀림부, 부라벨)):
            if not 틀림.any(): continue
            _, ii = ndimage.distance_transform_edt(~np.isin(sub, list(쪽)), return_indices=True)
            w = idx[틀림]; 새[tuple(w.T)] = sub[tuple(ii[:, w[:, 0], w[:, 1], w[:, 2]])]
        lab[sl] = 새
        s["다시칠한칸"] = int(틀림자.sum() + 틀림부.sum())
    return 기록


# ════════ ③ 짝 · 면 (부품짓기.py 와 같은 절차 · 192 색인에서 맞추고 mm 로 옮김) ═══════
def E13면():
    받은 = {}
    for x in json.load(open(os.path.join(E13, "평면.json"), encoding="utf-8")):
        if x["칸"] < 10: continue
        if "원통" in x:
            o = x["원통"]; s = {"종류": "원통", "c": np.array(o["점"], float), "a": 단(o["축"]), "r": float(o["반지름"]), "t": tuple(o["t"])}
        else:
            s = {"종류": "평면", "n": 단(x["법선"]), "c": np.array(x["점"], float)}
        받은.setdefault(tuple(sorted(x["짝"])), []).append(s)
    return 받은


def 짝짓기(lab, 표, 관절면, 받은):
    면 = 면들(lab); N = lab.shape[0]
    원통짝 = {kj for kj, ss in 받은.items() if any(s["종류"] == "원통" for s in ss)}
    짝관 = {kj: (n, c) for n, v in 관절짝(표, 면, 원통짝).items() for kj, c in v}
    짝 = {}
    for (k, j), R_ in 면.items():
        P, ax = 면점(R_); kc = P.copy(); kc[np.arange(len(P)), ax] -= 0.5 * R_[:, 4]
        if (k, j) in 짝관:
            n, 자 = 짝관[(k, j)]
            if n not in 관절면: 관절면[n] = 회전면(n, mm(P))
            s = dict(관절면[n]); s.update(종류="관절", 자=자, inl=np.ones(len(P), bool), rms=0.0)
            짝[(k, j)] = {"P": P, "ax": ax, "kc": kc, "평면": [s], "버림": 0, "관절": n}; continue
        ss = [dict(s) for s in 받은.get((k, j), [])]
        if ss:
            d = np.stack([np.abs(PJ.거리(s, P)) for s in ss], 1); 가 = d.argmin(1)
            for i, s in enumerate(ss): s["inl"] = (가 == i) & (d.min(1) < PJ.인라이어 + 0.3)
            ss = [s for s in ss if s["inl"].any() and (s["종류"] != "평면" or PJ.일관(s["n"], ax[s["inl"]]))]
        남점 = ~np.logical_or.reduce([s["inl"] for s in ss]) if ss else np.ones(len(P), bool)
        if 남점.sum() >= (max(10, 0.05 * len(P)) if ss else 1):
            ps, _ = PJ.평면들(P[남점], ax[남점]); w = np.nonzero(남점)[0]
            for nn, c, inl in ps:
                full = np.zeros(len(P), bool); full[w[inl]] = True; ss.append({"종류": "평면", "n": nn, "c": c, "inl": full})
        for s in ss:
            if s["종류"] == "평면" and np.abs(s["n"]).max() > 0.995:
                a_ = int(np.abs(s["n"]).argmax()); n_ = np.zeros(3); n_[a_] = np.sign(s["n"][a_]); s["n"] = n_
                s["c"] = s["c"].copy(); s["c"][a_] = np.floor(s["c"][a_]) + 0.5
        for s in ss:
            i_ = s["inl"]; s["σ"] = -1.0 if np.sum(PJ.거리(s, kc[i_]) - PJ.거리(s, P[i_])) > 0 else 1.0
            if s["종류"] == "평면": s["n"] = s["σ"] * s["n"]; s["σ"] = 1.0
            s["rms"] = float(np.sqrt(np.mean(PJ.거리(s, P[s["inl"]]) ** 2)))
        짝[(k, j)] = {"P": P, "ax": ax, "kc": kc, "평면": ss, "버림": int(len(P) - sum(s["inl"].sum() for s in ss))}
    이웃 = {k: set() for k in np.unique(lab) if k > 0}
    for k, j in 짝: 이웃[k].add(j); 이웃[j].add(k)

    def 근처(P, inl):                             # 이음 근처 칸 (잘린 칸 (lo, arr))
        qq = np.concatenate([np.clip(np.floor(P[inl] - 0.5 + d).astype(int), 0, N - 1) for d in (0, 1)])
        lo, hi = 상자(qq, PJ.이음근처, N); m = np.zeros(hi - lo, bool); m[tuple((qq - lo).T)] = True
        return (lo, ndimage.distance_transform_edt(~m) <= PJ.이음근처)
    제약 = {k: set() for k in 이웃}
    for (k, j), s in 짝.items():
        for p in s["평면"]: p["N"] = 근처(s["P"], p["inl"])
        if len(s["평면"]) < 2: continue
        lo = np.min([p["N"][0] for p in s["평면"]], 0); hi = np.max([p["N"][0] + p["N"][1].shape for p in s["평면"]], 0)
        U = np.zeros(hi - lo, bool)
        for p in s["평면"]:
            a_ = p["N"][0] - lo; U[a_[0]:a_[0] + p["N"][1].shape[0], a_[1]:a_[1] + p["N"][1].shape[1], a_[2]:a_[2] + p["N"][1].shape[2]] |= p["N"][1]
        sub = lab[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]; U &= (sub == k) | (sub == j)
        q = np.argwhere(U) + lo + 0.5; isk = sub[U] == k           # (부품짓기와 같게)
        S = np.stack([p.get("σ", 1.0) * PJ.거리(p, q) < 0 for p in s["평면"]], 1)
        교, 합 = np.mean(S.all(1) == isk), np.mean(S.any(1) == isk)
        먼저 = k if 교 >= 합 else j; 제약[j if 먼저 == k else k].add(먼저); s["볼록"] = 먼저
    # 면 → mm
    for s in 짝.values():
        for p in s["평면"]:
            if p["종류"] == "평면": p["cm"] = mm(p["c"])
            elif p["종류"] == "원통": p["cm"] = mm(p["c"]); p["rm"] = p["r"] * C; p["tm"] = (p["t"][0] * C, p["t"][1] * C)
    while True:                                   # 꺾인 짝 차례가 돌면(칼 소켓 13–12–30) 고리의 한 제약을 버린다
        try: return 짝, 이웃, list(graphlib.TopologicalSorter(제약).static_order())
        except graphlib.CycleError as e:
            cy = e.args[1]; 제약[cy[1]].discard(cy[0]); 로그("  차례 고리 %s — 제약 %s←%s 버림" % ([이름표[int(c)] for c in cy], 이름표[int(cy[1])], 이름표[int(cy[0])]))


큰 = M.Manifold.cube([1200, 1200, 1200], center=True)


def 저쪽(p, k, 부):
    """부품 k 쪽에서 본 이웃 쪽 영역 (mm)."""
    if p["종류"] == "평면": return PJ.반공간(부 * p["n"], p["cm"])
    if p["종류"] == "원통":
        σ = 부 * p["σ"]; t0_, t1_ = p["tm"]; R = PJ.회전(p["a"]).T
        통 = lambda r: 놓기(M.Manifold.cylinder(t1_ - t0_, r, r, 96).translate([0, 0, t0_]), R, p["cm"])
        return 통(p["rm"] + 결합틈) if σ < 0 else 큰 - 통(p["rm"])
    g = 관절틈 / 2
    return 큰 - Rc메시(p, -g) if k == p["자"] else Rc메시(p, g)


def 부품만들기(lab, 짝, 이웃, 차례, 껍):
    N = lab.shape[0]
    def 부풂(j, r):                               # 잘린 칸 (lo, arr)
        lo, hi = 상자(np.argwhere(lab == j), r, N); sl = tuple(slice(l, h) for l, h in zip(lo, hi))
        return (lo, ndimage.distance_transform_edt(lab[sl] != j) <= r)
    부품 = {}
    for k in 차례:
        lo, D = 부풂(k, PJ.부풀림); sub = lab[tuple(slice(l, l + n) for l, n in zip(lo, D.shape))]
        D &= ~((sub > 0) & ~np.isin(sub, list(이웃[k] | {k})))
        R = 껍 ^ 칸메시c((lo, D))
        자름 = []; 부2 = {j: 부풂(j, 2) for j in 이웃[k]}
        for j in 이웃[k]:
            s = 짝[(min(k, j), max(k, j))]; 부 = 1.0 if k < j else -1.0
            if s.get("볼록", k) != k: continue
            for p in s["평면"]:
                z_ = 교(p["N"], 부2[j])
                if z_ is not None: 자름.append(저쪽(p, k, 부) ^ 칸메시c(z_))
        if 자름: R = R - M.Manifold.batch_boolean(자름, M.OpType.Add)
        if 부품:
            bb = R.bounding_box(); 앞 = [m for m in 부품.values() if PJ.상자겹침(bb, m.bounding_box())]
            if 앞: R = R - M.Manifold.batch_boolean(앞, M.OpType.Add)
        부품[k] = M.Manifold(R.to_mesh())
        로그("  부품 %-12s %6.2f cm³ 자름 %d" % (이름표[k], 부품[k].volume() / 1000, len(자름)))
    return 부품


def 틈정리(부품, 껍, 짝):
    """부품마다 큰 덩어리(가장 큰 것의 20 % 이상)만 남기고, 부스러기 · 껍질 − 합 조각을 붙인다.
    단 관절 이음 틈 띠(회전면 ± 관절틈/2) 안에 든 조각은 **일부러 둔 틈**이라 안 붙인다."""
    떼 = []
    for k in list(부품):
        조 = sorted(부품[k].decompose(), key=lambda m: -m.volume())
        if len(조) > 1:
            남길 = [m for m in 조 if m.volume() >= 0.2 * 조[0].volume()]
            부품[k] = M.Manifold.batch_boolean(남길, M.OpType.Add); 떼 += [m for m in 조 if m.volume() < 0.2 * 조[0].volume()]
    남 = 껍 - M.Manifold.batch_boolean(list(부품.values()), M.OpType.Add)
    # (manifold decompose 가 이 메시에서 bad allocation 을 낸다 — 면 연결 성분으로 나눈다)
    t남 = 트(남); 성분 = trimesh.graph.connected_components(t남.face_adjacency, nodes=np.arange(len(t남.faces)), min_len=1)
    남조 = []
    for fc in 성분:
        sub = t남.submesh([fc], append=True)
        mm_ = M.Manifold(M.Mesh(vert_properties=np.asarray(sub.vertices, np.float32), tri_verts=np.asarray(sub.faces, np.uint32)))
        if mm_.status() == M.Error.NoError and mm_.volume() > 0: 남조.append(mm_)
    조각 = sorted(남조 + 떼, key=lambda m: -m.volume())
    면들_ = [p for s in 짝.values() for p in s["평면"] if p["종류"] == "관절"]
    from scipy.spatial import cKDTree
    부트 = {k: cKDTree(np.asarray(m.to_mesh().vert_properties)[:, :3]) for k, m in 부품.items()}; 부상 = {k: np.asarray(m.bounding_box()).reshape(2, 3) for k, m in 부품.items()}
    몫들 = {k: [] for k in 부품}; 기록 = dict(관절틈띠mm3=0.0, 붙임mm3=0.0, 외톨mm3=0.0, 버림mm3=0.0)
    for m in 조각:
        if m.volume() < 0.02: 기록["버림mm3"] += m.volume(); continue
        v = np.asarray(m.to_mesh().vert_properties)[:, :3]
        if any(np.mean(Rc안(p, v, 관절틈 / 2 + 0.05) & ~Rc안(p, v, -관절틈 / 2 - 0.05)) > 0.8 for p in 면들_):
            기록["관절틈띠mm3"] += m.volume(); continue
        lo, hi = v.min(0), v.max(0); 최 = (0.0, None)
        for k, b in 부상.items():
            if np.any(lo > b[1] + 0.01) or np.any(hi < b[0] - 0.01): continue
            c = float(np.mean(부트[k].query(v)[0] < 1e-3))       # 조각 정점이 그 부품 정점과 겹치는 몫 (잘린 면을 나눠 가진다)
            if c > 최[0]: 최 = (c, k)
        if 최[1] is None:                                    # 정점이 안 겹치면 가장 가까운 부품 (0.5 mm 안)
            dk = {k: float(np.median(t.query(v)[0])) for k, t in 부트.items() if not (np.any(lo > 부상[k][1] + 0.5) or np.any(hi < 부상[k][0] - 0.5))}
            if dk and min(dk.values()) < 0.5: 최 = (0.0, min(dk, key=dk.get))
            else: 기록["외톨mm3"] += m.volume(); continue
        몫들[최[1]].append(m); 기록["붙임mm3"] += m.volume()
    for k, ms in 몫들.items():
        if ms: 부품[k] = M.Manifold(M.Manifold.batch_boolean([부품[k]] + ms, M.OpType.Add).to_mesh())
    return {k: round(v, 2) for k, v in 기록.items()}


# ════════ ④ 결합 · 무기 막대 ═══════════════════════════════════
def 기둥(a, b, r, seg=32):
    a, b = np.asarray(a, float), np.asarray(b, float); L = np.linalg.norm(b - a)
    return 놓기(M.Manifold.cylinder(L, r, r, seg), PJ.회전(b - a).T, a)


def 겹친(m, 목록):
    bb = m.bounding_box(); ms = [x for x in 목록 if PJ.상자겹침(bb, x.bounding_box())]
    return (m ^ M.Manifold.batch_boolean(ms, M.OpType.Add)).volume() if ms else 0.0


def 무기막대(부품, 표, 촉):
    """② 무기(칼 · 대포) 부품에 E13 꽂이 원통을 손 속 쥠 관절 자식 구멍 앞까지 늘린 막대 + D 촉. 다른 장갑은 막대 + 결합틈을 판다."""
    기록 = {}
    for 무, m_ in 막대.items():
        ks = [k for k in 부품 if 표[k]["뼈"] == 무]
        if not ks or 무 not in 촉: continue
        o = m_["원통"]; c_ = np.array(o["점"], float); a = m_["a"]
        시작 = mm(c_ + (o["t가름"] - 3.0) * a); 끝점 = np.array(촉[무][0]["입구"])
        d = 단(끝점 - 시작); 끝 = 끝점 - d * 결합틈
        봉 = 기둥(시작, 끝, m_["r"], 96) + 촉[무][0]["m"]      # 시작 = 소켓 가름에서 무기 쪽 3 칸(6 mm) — 무기 껍질 고리와 겹쳐 붙는다
        k = max(ks, key=lambda k: 부품[k].volume())
        for j in 부품:
            if j != k and PJ.상자겹침(봉.bounding_box(), 부품[j].bounding_box()): 부품[j] = 부품[j] - 볼록덧(기둥(시작, 끝, m_["r"], 64), 결합틈)
        부품[k] = 부품[k] + 봉
        기록[무] = dict(부품=이름표[k], 지름mm=round(2 * m_["r"], 1), 길이mm=round(float(np.linalg.norm(끝 - 시작)), 1),
                       늘림mm=round(float(np.linalg.norm(끝 - mm(c_ + o["t"][1] * a))), 1), 축각도차=round(float(np.degrees(np.arccos(min(1, abs(d @ a))))), 1),
                       관절=촉[무][0]["관절"])
    return 기록


def 보스(부품, 표, 뼈m, 놓인, 겉):
    """장갑 → 뼈: 뼈 축 위 점 q(반지름 ≥ 2.8) 에서 장갑 안쪽 가장 가까운 점 c 로 Ø4 기둥 · 끝 핀 Ø1.8 × 2.5 → 뼈 구멍."""
    관절몸 = [볼록덧(v["m"], 0.2) for v in 놓인.values()]
    기록 = {}; 구멍 = {}
    for k in 부품:
        b = 표[k]["뼈"]
        if b not in 뼈: continue
        tm = 트(부품[k])
        후 = []
        for a, bb, ra, rb in 뼈선(b):
            for t in np.linspace(0, 1, max(2, int(np.linalg.norm(bb - a) / 2) + 1)):
                q = a + t * (bb - a); rq = ra + t * (rb - ra) - 0.4          # 캡슐보다 조금 안 (J1 뼈는 몸 장에 맞춰 깎였다)
                if rq >= 2.8: 후.append((q, rq))          # 관절 부품과 닿는 자리는 아래 겹침 검사가 거른다
        if not 후: 기록[이름표[k]] = "뼈 위 자리 없음"; continue
        # 장갑 쪽 자리: 안쪽 면(법선이 뼈 쪽) · 다른 장갑에서 3 mm 넘게 떨어진 정점
        남장 = [m for j, m in 부품.items() if j != k]
        Pv = tm.vertices[:: max(1, len(tm.vertices) // 6000)]; Nv = tm.vertex_normals[:: max(1, len(tm.vertices) // 6000)]
        bb = np.r_[Pv.min(0) - 4, Pv.max(0) + 4]; 근 = [np.asarray(m.to_mesh().vert_properties)[:, :3] for m in 남장 if PJ.상자겹침(bb, m.bounding_box())]
        from scipy.spatial import cKDTree
        if 근:
            dd = cKDTree(np.concatenate(근)).query(Pv)[0]; Pv, Nv = Pv[dd >= 보스r + 1.0], Nv[dd >= 보스r + 1.0]
        cand = []
        for q, rq in 후:
            d_ = np.linalg.norm(Pv - q, axis=1); ok = ((q - Pv) * Nv).sum(1) > 0.5 * d_
            for i in np.nonzero(ok)[0][np.argsort(d_[ok])][:40:5]: cand.append((d_[i], q, rq, Pv[i]))     # 방향 여럿 (가까운 40 중 8)
        cand.sort(key=lambda t: t[0])
        남은 = [m for n_, m in 뼈m.items() if n_ != b] + 관절몸 + 남장
        됨 = None; 까닭 = {"거리": 0, "몸밖": 0, "기둥겹침": 0, "핀겹침": 0}
        관절몸b = [x for x in 관절몸 if PJ.상자겹침(np.r_[Pv.min(0) - 20, Pv.max(0) + 20], x.bounding_box())]
        남은b = [m for n_, m in 뼈m.items() if n_ != b] + 남장
        for L, q, rq, c in cand[:200]:
            if not (rq + 0.5 <= L <= 30): 까닭["거리"] += 1; continue
            u = (c - q) / L
            col = 기둥(q + u * (rq + 0.3), c + u * 0.3, 보스r)
            if (col - 겉).volume() > 1.0: 까닭["몸밖"] += 1; continue
            if 겹친(col, 남은b) + 겹친(col, 관절몸b) > 0.5: 까닭["기둥겹침"] += 1; continue
            pin = 기둥(q + u * (rq - 핀길이), q + u * (rq + 0.5), 핀r)
            if 겹친(pin, 남은b) > 0.05: 까닭["핀겹침"] += 1; continue      # 뼈 속 핀이 관절 부품과 겹치는 것은 J1/J2 길이 충돌이라 여기서 안 거른다
            됨 = (q, rq, c, u, col + pin); break
        if 됨 is None: 기록[이름표[k]] = "자리 못 찾음 %s" % {a: b for a, b in 까닭.items() if b}; continue
        q, rq, c, u, m = 됨; 부품[k] = 부품[k] + m
        구멍.setdefault(b, []).append(기둥(q + u * (rq - 핀길이 - 0.3), q + u * (rq + 1.0), 핀r + 결합틈))
        기록[이름표[k]] = dict(뼈=b, 뼈점=np.round(q, 1).tolist(), 기둥길이mm=round(float(np.linalg.norm(c - q) - rq), 1), 방향=np.round(u, 2).tolist(),
                              핀이관절부품과겹침mm3=round(겹친(기둥(q + u * (rq - 핀길이), q + u * (rq + 0.5), 핀r), 관절몸b), 2))
    for b, hs in 구멍.items(): 뼈m[b] = 뼈m[b] - M.Manifold.batch_boolean(hs, M.OpType.Add)
    return 기록


def 다보(부품, 표, 짝, 겉, V):
    """같은 뼈 반쪽 짝 (평면 이음): 이음면 둘레 껍질 안쪽에 패드 Ø4.2 × 7.2 를 덧대고 핀(작은 쪽) · 구멍(큰 쪽) 둘. 패드 = 몸 안 · 비움/다른 부품 밖."""
    padR = 핀r + 결합틈 + 벽; hh = 핀길이 + 0.3 + 바닥벽; 기록 = []
    for (k, j), s in sorted(짝.items()):
        if k not in 부품 or j not in 부품 or 표[k]["뼈"] != 표[j]["뼈"]: continue
        평 = [p for p in s["평면"] if p["종류"] == "평면"]
        if not 평: continue
        최 = None
        for p in 평:
            Rt, c = PJ.평면틀(p["n"], p["cm"])
            cs = PJ.단면(부품[k], Rt, c, -0.02) ^ PJ.단면(부품[j], Rt, c, 0.02)
            if 최 is None or cs.area() > 최[0]: 최 = (cs.area(), p, Rt, c, cs)
        넓이, p, Rt, c, cs = 최; 줄 = dict(짝=[이름표[k], 이름표[j]], 이음넓이mm2=round(넓이, 1), 다보=[])
        if 넓이 < 4: 줄["비고"] = "맞닿은 면 없음"; 기록.append(줄); continue
        r1 = PJ.래스터(cs); rb = PJ.래스터(PJ.단면(겉, Rt, c, 0.0))
        acc, lo, 해 = r1; bacc, blo, _ = rb
        Eb = ndimage.distance_transform_edt(bacc) * 해
        링 = ndimage.distance_transform_edt(~acc) * 해 <= padR - 0.6     # 패드가 이음 껍질에 걸치는 곳
        yy, xx = np.nonzero(링); P2 = np.c_[xx * 해 + lo[0], yy * 해 + lo[1]]
        bi = np.round((P2 - blo) / 해).astype(int); ok = (bi[:, 0] >= 0) & (bi[:, 1] >= 0) & (bi[:, 0] < bacc.shape[1]) & (bi[:, 1] < bacc.shape[0])
        P2 = P2[ok]; e = Eb[bi[ok, 1], bi[ok, 0]]; P2 = P2[(e >= padR + 0.2) & (e <= padR + 1.0)]
        if len(P2) == 0: 줄["비고"] = "패드 자리 없음"; 기록.append(줄); continue
        남 = [m for x, m in 부품.items() if x not in (k, j)]
        P2 = P2[:: max(1, len(P2) // 400)]
        P3 = (Rt @ np.c_[P2, np.zeros(len(P2))].T).T + c
        bb = np.r_[P3.min(0) - 6, P3.max(0) + 6]; 근 = [np.asarray(m.to_mesh().vert_properties)[:, :3] for m in 남 if PJ.상자겹침(bb, m.bounding_box())]
        if 근:
            from scipy.spatial import cKDTree
            dd = cKDTree(np.concatenate(근)).query(P3)[0]; P2 = P2[dd >= np.hypot(padR, hh) + 0.3]
        if len(P2) == 0: 줄["비고"] = "다른 부품과 먼 패드 자리 없음"; 기록.append(줄); continue
        고른 = [P2[np.argmax(np.linalg.norm(P2 - P2.mean(0), axis=1))]]
        먼 = P2[np.argmax(np.linalg.norm(P2 - 고른[0], axis=1))]
        if np.linalg.norm(먼 - 고른[0]) >= 8: 고른.append(먼)
        작은 = k if 부품[k].volume() < 부품[j].volume() else j
        for q in 고른:
            def 통(r_, z0, z1): return PJ.옮김(M.Manifold.cylinder(z1 - z0, r_, r_, 32).translate([q[0], q[1], z0]), Rt, c)
            pad = (통(padR, -hh, hh) ^ 겉) - V
            if 겹친(pad, 남) > 0.5: 줄["다보"].append(dict(자리=np.round(Rt @ np.r_[q, 0] + c, 1).tolist(), 박음=False, 까닭="패드가 다른 부품에 닿음")); continue
            아래 = PJ.옮김(M.Manifold.cube([200, 200, 100]).translate([-100, -100, -100]), Rt, c)     # 평면틀 z<0 = k 쪽
            pk_, pj_ = pad ^ 아래, pad - 아래
            sgn = 1 if 작은 == k else -1                     # 핀이 k(아래) 에서 위로
            pin = 통(핀r, -1.0, 핀길이) if sgn > 0 else 통(핀r, -핀길이, 1.0)
            hole = 통(핀r + 결합틈, -0.5, 핀길이 + 0.3) if sgn > 0 else 통(핀r + 결합틈, -핀길이 - 0.3, 0.5)
            암 = j if 작은 == k else k
            부품[k] = 부품[k] + pk_; 부품[j] = 부품[j] + pj_
            부품[작은] = 부품[작은] + pin; 부품[암] = 부품[암] - hole
            줄["다보"].append(dict(자리=np.round(Rt @ np.r_[q, 0] + c, 1).tolist(), 핀=이름표[작은], 구멍=이름표[암], 박음=True))
        기록.append(줄)
    return 기록


# ════════ ⑥ 닫힘 · 내보내기 ════════════════════════════════════
def 떼기(m, δ=0.02, 번=4):
    """자기 접촉 = 한 자리(1e-3 mm 안)에 정점이 둘 이상 (manifold 위상으로는 따로지만 STL 로 다시 읽으면 합쳐져 한 모서리에 면 4 장).
    그 정점마다 **자기 면 쪽**(한 고리 이웃 무게중심 쪽)으로 δ 만큼 옮겨 떼어 낸다 = 접촉 자리를 δ 만큼 깎는 것과 같다.
    (구를 빼서 깎는 첫 판은 가는 조각면을 더 만들어 열린 모서리가 늘었다.)"""
    from scipy.spatial import cKDTree
    g = m.to_mesh(); V = np.asarray(g.vert_properties)[:, :3].astype(float); F = np.asarray(g.tri_verts); 옮김 = set()
    이웃합 = np.zeros_like(V); 수 = np.zeros(len(V))
    for a_, b_ in ((0, 1), (1, 2), (2, 0), (1, 0), (2, 1), (0, 2)):
        np.add.at(이웃합, F[:, a_], V[F[:, b_]]); np.add.at(수, F[:, a_], 1)
    for _ in range(번):
        pr = cKDTree(V).query_pairs(1e-3, output_type="ndarray")
        if len(pr) == 0: break
        겹 = np.unique(pr.ravel()); 옮김 |= set(겹.tolist())
        c = 이웃합[겹] / np.maximum(수[겹], 1)[:, None]; d = c - V[겹]; L = np.linalg.norm(d, axis=1, keepdims=True)
        V[겹] += d / np.maximum(L, 1e-12) * np.minimum(δ, 0.45 * L)
    return trimesh.Trimesh(V, F, process=False), len(옮김)


def 눕힘(tm, 법선들=()):
    """바닥 평면이 가장 넓은 방향을 아래로 (부품짓기 규칙: 턱 0.5 mm 넘는 방향 제외)."""
    후보 = [np.eye(3)[a] * s for a in range(3) for s in (1, -1)] + [s * np.asarray(n) for n in 법선들 for s in (1, -1)]
    def 바닥(d):
        fc = tm.face_normals @ d > 0.999
        if not fc.any(): return 0.0, 9.0
        lv = np.round(tm.triangles_center[fc] @ d, 2); a_ = tm.area_faces[fc]
        u, inv = np.unique(lv, return_inverse=True); s_ = np.bincount(inv, a_); i_ = s_.argmax()
        return float(s_[i_]), float((tm.vertices @ d).max() - u[i_])
    아래 = max(후보, key=lambda d: 바닥(d)[0] if 바닥(d)[1] < 0.5 else -바닥(d)[1])
    pm = tm.copy(); T = np.eye(4); T[:3, :3] = PJ.회전(-아래); pm.apply_transform(T); pm.apply_translation(-pm.bounds[0])
    return pm, 바닥(아래)[0]


def 납작(tm):
    """가장 얇은 방향(OBB)을 z 로 — 뼈 출력 자세."""
    T, ext = trimesh.bounds.oriented_bounds(tm); pm = tm.copy(); pm.apply_transform(T)
    o = np.argsort(-np.asarray(ext)); P_ = np.eye(4); P_[:3, :3] = np.eye(3)[o]
    if np.linalg.det(P_[:3, :3]) < 0: P_[2, :3] *= -1
    pm.apply_transform(P_); pm.apply_translation(-pm.bounds[0]); return pm


def 견적():
    """out/출력/오메가몬_PG/{장갑,프레임,관절}/*.stl 을 A1 판(236 mm)에 선반 쌓기로 나눠 OrcaSlicer 로 자른다.
    프로필 = 관절쿠폰의 inherits 푼 _machine/_process/_filament (기본 BBL 파일은 판이 200×200 으로 잡힌다) + 나무 서포트 켬.
    판마다 gcode 가 있으면 건너뛴다 (10 분 안에 끊겨도 다시 부르면 이어서)."""
    import 관절부품 as JB
    from 공차쿠폰 import ORCA
    판폴더 = os.path.join(OUT, "_판"); os.makedirs(판폴더, exist_ok=True)
    쿠 = os.path.join(ROOT, "out", "출력", "관절쿠폰")
    proc = json.load(open(os.path.join(쿠, "_process.json"), encoding="utf-8")); proc.update(enable_support="1", support_type="tree(auto)")
    json.dump(proc, open(os.path.join(판폴더, "_process.json"), "w", encoding="utf-8"), ensure_ascii=False)
    판표 = os.path.join(판폴더, "판.json")
    if not os.path.exists(판표):
        판들 = []
        for 층 in ("장갑", "프레임", "관절"):
            ms = [(f, trimesh.load(os.path.join(OUT, 층, f))) for f in sorted(os.listdir(os.path.join(OUT, 층))) if f.endswith(".stl")]
            남 = sorted(ms, key=lambda t: -np.prod(t[1].extents[:2]))
            while 남:
                판 = []
                for f, t in list(남):
                    시도 = 판 + [(f, t)]
                    try: JB.선반쌓기([(ff, 만(tt.vertices, tt.faces)) for ff, tt in 시도]); 판 = 시도; 남.remove((f, t))
                    except AssertionError: pass
                if not 판: 로그("판에 안 들어감: %s" % 남[0][0]); 남.pop(0); continue
                판들.append(dict(층=층, 부품=[f for f, _ in 판]))
        json.dump(판들, open(판표, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    판들 = json.load(open(판표, encoding="utf-8"))
    for i, p in enumerate(판들, 1):
        g = os.path.join(판폴더, "판%02d" % i)
        if os.path.exists(os.path.join(g, "plate_1.gcode")): continue
        os.makedirs(g, exist_ok=True)
        놓음, _ = JB.선반쌓기([(f, 만(*(lambda t: (t.vertices, t.faces))(trimesh.load(os.path.join(OUT, {"장갑": "장갑", "프레임": "프레임", "관절": "관절"}[p["층"]], f))))) for f in p["부품"]])
        tt = trimesh.util.concatenate([트(m) for _, m in 놓음]); tt.apply_translation([128 - tt.bounds[:, 0].mean(), 128 - tt.bounds[:, 1].mean(), 0])
        stl = os.path.join(g, "판.stl"); tt.export(stl)
        r = subprocess.run([ORCA, "--load-settings", os.path.join(쿠, "_machine.json") + ";" + os.path.join(판폴더, "_process.json"), "--load-filaments", os.path.join(쿠, "_filament.json"),
                            "--arrange", "0", "--slice", "0", "--outputdir", g, stl], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
        로그("판%02d %s %d 부품 → 종료 %d" % (i, p["층"], len(p["부품"]), r.returncode))
    합 = dict(판=len(판들), 초=0.0, cm3=0.0, 판별=[])
    for i, p in enumerate(판들, 1):
        g = os.path.join(판폴더, "판%02d" % i, "plate_1.gcode")
        if not os.path.exists(g): 합["판별"].append(dict(판=i, 층=p["층"], 부품=len(p["부품"]), 견적="없음")); continue
        t_, c_ = None, None
        for 줄 in open(g, encoding="utf-8", errors="replace"):
            if "total estimated time" in 줄: t_ = 줄.split("total estimated time:")[-1].strip()
            if "filament used [cm3]" in 줄: c_ = float(줄.split("=")[1])
        sec = sum(int(x[:-1]) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[x[-1]] for x in t_.split()) if t_ else 0
        합["초"] += sec; 합["cm3"] += c_ or 0; 합["판별"].append(dict(판=i, 층=p["층"], 부품=len(p["부품"]), 시간=t_, cm3=c_))
    합["시간"] = "%.1f h" % (합["초"] / 3600); 합["PLA_g"] = round(합["cm3"] * 1.24, 1)
    kj = os.path.join(OUT, "키트.json"); K = json.load(open(kj, encoding="utf-8")); K["요약"]["견적(A1 · PLA 0.2 · 나무 서포트)"] = 합
    json.dump(K, open(kj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(합, ensure_ascii=False, indent=0))


if __name__ == "__main__" and "견적" in sys.argv:
    견적(); sys.exit()

if __name__ == "__main__" and "배정" in sys.argv:
    lab = np.load(os.path.join(캐시, "몸.npz"))["lab"]
    표 = 뼈배정(lab)
    for b in dict.fromkeys(v["블록"] for v in 표.values()): v = next(v for v in 표.values() if v["블록"] == b); print(b, v["뼈"], v["몫"], "고정" if v["고정"] else "")
    print(가르기(lab, 표))
    면 = 면들(lab); 짝들 = 관절짝(표, 면)
    for n, v in 짝들.items(): print(n, [(이름표[k], 이름표[j], 이름표[c]) for (k, j), c in v])
    기 = 다시칠(lab, 표, 짝들, 면)
    for n, s in 기.items(): print(n, s["모양"], "r %.1f (%s) rms %s · t %.1f ±%.1f · 다시칠 %d" % (s["r"], s.get("r근거"), s.get("맞춤rms"), s["t"], s["t_rms"], s["다시칠한칸"]))
    sys.exit()

if __name__ == "__main__":
    os.makedirs(캐시, exist_ok=True)
    if not os.path.exists(os.path.join(캐시, "몸.npz")): 몸짓기()
    로그("몸 끝")
    놓인, 촉, 틀표 = 관절짓기(); 로그("관절 부품 %d" % len(놓인))
    뼈m, 뼈기록 = 뼈짓기(놓인, 촉); 로그("뼈 %d · 여러 조각 %s" % (len(뼈m), [n for n, r in 뼈기록.items() if r["조각"] > 1]))
    겉, 껍, V = 껍질짓기(놓인, 뼈m)
    pk0, pk = os.path.join(캐시, "부품0.pkl"), os.path.join(캐시, "부품.pkl")
    def 풀기(f):
        D_ = pickle.load(open(f, "rb")); 이름표.update(D_["이름표"])
        return {k: 만(*vf) for k, vf in D_["부품"].items()}, D_
    def 담기(f, 부품, **kw):
        pickle.dump(dict(부품={k: (np.asarray(m.to_mesh().vert_properties)[:, :3], np.asarray(m.to_mesh().tri_verts)) for k, m in 부품.items()}, 이름표=이름표, **kw), open(f, "wb"))
    if os.path.exists(pk):
        부품, D_ = 풀기(pk)
    else:
        if os.path.exists(pk0): 부품, D_ = 풀기(pk0)
        else:
            lab = np.load(os.path.join(캐시, "몸.npz"))["lab"]; 표 = 뼈배정(lab); 가름기록 = 가르기(lab, 표)
            받은 = E13면(); 원통짝 = {kj for kj, ss in 받은.items() if any(s["종류"] == "원통" for s in ss)}
            면0 = 면들(lab); 관절면 = 다시칠(lab, 표, 관절짝(표, 면0, 원통짝), 면0); 로그("다시칠 %s" % {n: s["다시칠한칸"] for n, s in 관절면.items()})
            짝, 이웃, 차례 = 짝짓기(lab, 표, 관절면, 받은); 로그("짝 %d · 관절 이음 %d" % (len(짝), sum("관절" in s for s in 짝.values())))
            부품 = 부품만들기(lab, 짝, 이웃, 차례, 껍)
            짝저장 = {kj: {**{a: b for a, b in s.items() if a not in ("P", "ax", "kc")}, "평면": [{a: b for a, b in p.items() if a not in ("N", "inl")} for p in s["평면"]]} for kj, s in 짝.items()}
            D_ = dict(lab=lab, 표=표, 짝=짝저장, 이웃=이웃, 관절면=관절면, 가름=가름기록)
            담기(pk0, 부품, **D_)
        D_["틈"] = 틈정리(부품, 껍, D_["짝"]); 로그("틈 정리 %s" % D_["틈"])
        담기(pk, 부품, **{k: v for k, v in D_.items() if k not in ("부품", "이름표")})
    lab, 표, 짝, 이웃, 관절면 = D_["lab"], D_["표"], D_["짝"], D_["이웃"], D_["관절면"]
    로그("장갑 부품 %d · 합 %.1f cm³" % (len(부품), sum(m.volume() for m in 부품.values()) / 1000))
    막대기록 = 무기막대(부품, 표, 촉); 로그("무기 막대 %s" % 막대기록)
    보스기록 = 보스(부품, 표, 뼈m, 놓인, 겉); 로그("보스 %d / %d" % (sum(isinstance(v, dict) for v in 보스기록.values()), len(보스기록)))
    다보기록 = 다보(부품, 표, 짝, 겉, V); 로그("다보 %d (짝 %d)" % (sum(d["박음"] for x in 다보기록 for d in x["다보"]), len(다보기록)))

    # ── 내보내기 ──
    for d in ("장갑", "프레임", "관절", "_조립"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
        for f in os.listdir(os.path.join(OUT, d)):
            if f.endswith(".stl"): os.remove(os.path.join(OUT, d, f))
    import 관절부품 as JB
    줄들 = []; 보기 = []
    색 = {"장갑": "#e8590c", "뼈": "#1c7ed6", "관절": "#2f9e44"}
    임시 = os.path.join(캐시, "_시험.stl")
    def 닫힌것(m, 출력tm):
        """STL 로 다시 읽어 (조립 · 출력 자세 둘 다) 닫힐 때까지: simplify(짧은 모서리 접기) 허용오차 × 떼기 δ 를 차례로."""
        for tol in (1e-4, 0.0, 1e-3, 3e-4, 3e-3, 1e-2):
            m2 = m.simplify(tol) if tol else m
            for δ in (0.02, 0.05):
                tm, n깎 = 떼기(m2, δ); tm.export(임시)
                if not trimesh.load(임시).is_watertight: continue
                출력tm(tm).export(임시)
                if trimesh.load(임시).is_watertight: return tm, n깎, dict(simplify=tol, δ=δ, 부피차mm3=round(m.volume() - m2.volume(), 3))
        return tm, n깎, None
    찌꺼기 = {}
    def 내보냄(층, 이름, m, 출력tm, 뼈이름, **덧):
        cs = sorted(m.decompose(), key=lambda c: -c.volume()); 찌꺼기[이름] = round(sum(c.volume() for c in cs if c.volume() < 0.05), 4)
        큰 = [c for c in cs if c.volume() >= 0.2 * cs[0].volume()]; 작 = [c for c in cs if 0.05 <= c.volume() < 0.2 * cs[0].volume()]
        if len(큰) > 1:                  # 떨어진 큰 몸 여럿 (예: 가슴앞 = 가슴판 양옆) → 따로 출력
            for i, c in enumerate(큰, 1):
                붙 = [x for x in 작 if PJ.상자겹침(c.bounding_box(), x.bounding_box())]
                내보냄(층, "%s_%d" % (이름, i), M.Manifold.batch_boolean([c] + 붙, M.OpType.Add), 출력tm, 뼈이름, **덧)
            return
        떨어진 = [x for x in 작 if (x ^ 큰[0]).volume() < 1e-6 and x.volume() < 0.02 * 큰[0].volume()]   # 붙지 않은 작은 덩어리 = 뜬 조각 → 버림
        찌꺼기[이름] = round(찌꺼기[이름] + sum(x.volume() for x in 떨어진), 3)
        m = M.Manifold.batch_boolean(큰 + [x for x in 작 if not any(x is y for y in 떨어진)], M.OpType.Add)
        tm, n깎, 닫법 = 닫힌것(m, 출력tm); 조 = len(m.decompose())
        tm.export(os.path.join(OUT, "_조립", "%s_%s.stl" % (층, 이름)))
        pm = 출력tm(tm); pm.export(os.path.join(OUT, {"장갑": "장갑", "뼈": "프레임", "관절": "관절"}[층], 이름 + ".stl"))
        닫 = all(trimesh.load(os.path.join(OUT, dd, f), process=True).is_watertight
                for dd, f in ((os.path.join(OUT, "_조립"), "%s_%s.stl" % (층, 이름)), (os.path.join(OUT, {"장갑": "장갑", "뼈": "프레임", "관절": "관절"}[층]), 이름 + ".stl")))
        줄 = dict(층=층, 이름=이름, 뼈=뼈이름, 부피cm3=round(m.volume() / 1000, 3), 무게g=round(m.volume() / 1000 * 1.24, 1), 치수mm=[round(float(x), 1) for x in pm.extents],
                 manifold=str(m.status()).split(".")[-1], STL닫힘=bool(닫), 조각=조, 접촉뗀정점=n깎, 닫는법=닫법, 찌꺼기버림mm3=찌꺼기[이름.rsplit("_", 1)[0]] if 이름 not in 찌꺼기 else 찌꺼기[이름], **덧)
        줄들.append(줄)
        vt = tm
        목표 = {"장갑": 6000, "뼈": 1500, "관절": 1500}[층]
        if len(tm.faces) > 목표 * 1.5:
            try: vt = tm.simplify_quadric_decimation(face_count=목표)
            except Exception: pass
        vv = (vt.vertices - [0, 15, 150])[:, [0, 2, 1]] * [1, 1, -1]
        보기.append({"부품": 층, "조각": "%s — %s" % (층, 이름), "블록": 층, "종류": "관절" if 층 == "관절" else 층, "벌림": None, "색": 색[층],
                   "치수": 줄["치수mm"], "닫힘": 닫, "부피": 줄["부피cm3"],
                   "v": base64.b64encode(vv.astype(np.float32).tobytes()).decode(), "f": base64.b64encode(vt.faces.astype(np.uint32).tobytes()).decode()})
    법선 = {k: [] for k in 부품}
    for (k, j), s in 짝.items():
        for p in s["평면"]:
            if p["종류"] == "평면":
                for x in (k, j):
                    if x in 법선: 법선[x].append(p["n"])
    for k, m in sorted(부품.items(), key=lambda t: 이름표[t[0]]):
        내보냄("장갑", 이름표[k].replace("*", "_가름"), m, lambda tm, k=k: 눕힘(tm, 법선[k])[0], 표[k]["뼈"],
             짝=sorted(이름표[j] for j in 이웃.get(k, ())), 보스=isinstance(보스기록.get(이름표[k]), dict))
    for n, m in 뼈m.items(): 내보냄("뼈", n, m, 납작, n, 촉=뼈기록[n]["촉"])
    for (n, k), v in 놓인.items():
        def pm(tm, n=n, v=v):          # 출력 자세 = 관절부품.py 자세(지역 좌표) — 떼기 한 정점 그대로 옮긴다
            R = 틀표[n]; p = np.array(관절[n]["피벗mm"]); a = {"눕힘": 90, "뒤집음": 180}.get(v["자세"], 0)
            Rx = np.array([[1, 0, 0], [0, np.cos(np.radians(a)), -np.sin(np.radians(a))], [0, np.sin(np.radians(a)), np.cos(np.radians(a))]])
            t = tm.copy(); t.vertices = (t.vertices - p) @ R @ Rx.T; t.apply_translation(-t.bounds[0]); return t
        내보냄("관절", "%s_%s" % (n, k), v["m"], pm, 관절[n]["부모뼈" if k != "자식" else "자식뼈"], 관절=n, 쪽=k, 자세=v["자세"])
    로그("내보냄 %d · STL 닫힘 %d · 여러 조각 %s" % (len(줄들), sum(x["STL닫힘"] for x in 줄들), [x["이름"] for x in 줄들 if x["조각"] > 1]))

    # ── 키트.json ──
    합 = lambda 층: round(sum(x["부피cm3"] for x in 줄들 if x["층"] == 층), 2)
    팔 = json.load(open(os.path.join(캐시, "팔.json"), encoding="utf-8"))
    관절면표 = {n: {k: (np.round(v, 2).tolist() if isinstance(v, np.ndarray) else v) for k, v in s.items()} for n, s in 관절면.items()}
    이음 = {}
    for x in 다보기록:
        if any(d["박음"] for d in x["다보"]): a_, b_ = x["짝"]; 이음.setdefault(a_, set()).add(b_); 이음.setdefault(b_, set()).add(a_)
    닿음 = {n for n, v in 보스기록.items() if isinstance(v, dict)}; 줄_ = list(닿음)
    while 줄_:
        n = 줄_.pop()
        for m_ in 이음.get(n, ()):
            if m_ not in 닿음: 닿음.add(m_); 줄_.append(m_)
    무기 = [이름표[k] for k in 부품 if 표[k]["뼈"] in 막대]
    뜬장갑 = sorted(이름표[k] for k in 부품 if 이름표[k] not in 닿음 and 이름표[k] not in 무기)
    요약 = dict(전고mm=300.0, 장갑두께mm=두께, 비움틈mm=비움틈, 관절이음틈mm=관절틈, 결합틈mm_한쪽=결합틈, 다보핀=[2 * 핀r, 핀길이], 보스지름=2 * 보스r,
              부품수={층: sum(x["층"] == 층 for x in 줄들) for 층 in ("장갑", "뼈", "관절")},
              STL닫힘={층: "%d/%d" % (sum(x["STL닫힘"] for x in 줄들 if x["층"] == 층), sum(x["층"] == 층 for x in 줄들)) for 층 in ("장갑", "뼈", "관절")},
              부피cm3={층: 합(층) for 층 in ("장갑", "뼈", "관절")}, PLA_g_속찬={층: round(합(층) * 1.24, 1) for 층 in ("장갑", "뼈", "관절")},
              결합=dict(보스=sum(isinstance(v, dict) for v in 보스기록.values()), 보스없음=[k for k, v in 보스기록.items() if not isinstance(v, dict)],
                      다보=sum(d["박음"] for x in 다보기록 for d in x["다보"]), 다보없는반쪽짝=[x["짝"] for x in 다보기록 if not any(d["박음"] for d in x["다보"])],
                      관절이음=sum(1 for s in 짝.values() if any(p["종류"] == "관절" for p in s["평면"])), 뼈촉=sum(r["촉"] for r in 뼈기록.values()),
                      뼈까지이어진장갑=len(닿음), 무기쥠관절로=무기, 뼈에안이어진장갑=뜬장갑),
              윗팔원통=팔, 앞뒤이름바로잡음=앞뒤바꿈, 틈정리=D_["틈"], 가르기=[list(map(str, g)) for g in D_["가름"]], 무기막대=막대기록,
              걸린초=round(time.time() - t0))
    json.dump(dict(설명=__doc__, 요약=요약, 부품=줄들,
                   장갑뼈=[dict(부품=이름표[k], 뼈=v["뼈"], 몫=v["몫"], 고정=v.get("고정", False)) for k, v in 표.items() if k in 부품],
                   관절이음면=관절면표, 보스=보스기록, 다보=다보기록, 뼈=뼈기록,
                   관절틀={n: np.round(R, 4).tolist() for n, R in 틀표.items()}),
              open(os.path.join(OUT, "키트.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    t = open(os.path.join(ROOT, "설계", "부품속.src.html"), encoding="utf-8").read()
    t = (t.replace("부품 속 — 오메가몬", "오메가몬 PG — 장갑 · 뼈 · 관절").replace("<title>오메가몬 부품 속</title>", "<title>오메가몬 PG 키트</title>")
         .replace("색 = 블록 · 회색 = 관절 부품(볼 · 폴리캡 · 플러그) · 반쪽은 속이 빈 컵(벽 1.2 mm)이고 속 기둥(보스) 두 개 — 한쪽 보스에 핀, 다른 쪽에 구멍 · 전고 125 mm",
                  "주황 = 장갑(두께 %.1f) · 파랑 = 뼈 · 초록 = 관절 부품 · 목록에서 층을 누르면 그 층만 진하게 · 전고 300 mm" % 두께)
         .replace("cam.position.set(110, 30, 300)", "cam.position.set(260, 80, 700)").replace("new THREE.PerspectiveCamera(35, 1, 1, 2000)", "new THREE.PerspectiveCamera(35, 1, 1, 5000)")
         .replace("__DATA__", json.dumps(보기, ensure_ascii=False)))
    open(os.path.join(ROOT, "out", "부품속_PG.html"), "w", encoding="utf-8").write(t)
    print(json.dumps({k: v for k, v in 요약.items() if k not in ("틈정리", "가르기")}, ensure_ascii=False, indent=0, default=str))
