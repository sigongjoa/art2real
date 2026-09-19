# -*- coding: utf-8 -*-
"""**메시 변형 — TripoSG 메시를 복셀로 안 보내고, 미분가능 렌더로 세 축 실루엣에 끌어당긴다** (2026-09-19).

    python 메시변형.py 검사              합성 변형(구 -> 타원체) + 판정 함수가 질 수도 이길 수도 있는지
    python 메시변형.py 대조 [n] [케이스…]  정답 · T · T∩H · H · 상한(정답에 같은 변형) — **T→S 보다 먼저**
    python 메시변형.py [n] [케이스…]      T→S (그 장의 상한 행에 카메라 검사 통과가 있어야 돈다)
    python 메시변형.py 판정              -> out/기록/메시변형_<때>.json
    python 메시변형.py 그림              -> out/메시변형_접촉지.png
    <venv python> 메시변형.py 변형 in.npz out.npz     (안쪽 다리 — torch · nvdiffrast 는 D:\\imggen\\venv 에만 있다)

판정은 `claudedocs/plan_메시변형_20260919.md` 「Q」 절 그대로다 — 돌리기 전에 적었다. **문턱을 안 고친다.**
변형 = 정점 오프셋 δ = (I + λL)⁻¹ φ (Nicolet 2021 「large steps」 의 매개변수화 · CG 로 푼다) + 실루엣 L2
(nvdiffrast antialias) + 오프셋 라플라시안 벌점. **색 손실 없음 · 야코비안 필드 없음** (ModelSheetTo3D `mesh_deform` 의 최소판).
자 · 렌더 · 틀은 전부 `대각.py` · `메시추출.py` 의 것을 import 한다 — 새 자 없음.
"""
import json
import os
import sys
import time

import numpy as np

HERE = r"G:\art2real\원화3d"
ME = os.path.join(HERE, "실험_20260919", "메시변형.py")
VENV = r"D:\imggen\venv\Scripts\python.exe"
PROG = os.path.join(HERE, "out", "기록", "메시변형_진행.jsonl")
TILED = os.path.join(HERE, "out", "기록", "메시변형_타일")
MESHD = os.path.join(HERE, "out", "메시변형")                     # 변형된 정점 (npz) — 다시 재거나 볼 때
TAG = "메시변형 v2 · T/T∩H/H/T→S/상한 · 대각 30·45·60 · 축 1024 · IoU128 · 구멍 · 거칠기 (2026-09-19)"

실물4 = ("mech_Drill_8uBbH7Dvmb", "cloak_Chest_Closed_AngpV0HxD8",
         "cape_Hat_Stylised_lNN3PlrjSa", "avatarsample_d")
대조판 = ("정답", "T", "T∩H", "H", "상한")
COLS = ("정답", "T", "T∩H", "H", "T→S", "상한")

# ── 변형 손잡이 — **합성 검사(구 -> 타원체)에서만 정했다. 실물 숫자를 본 뒤 안 바꾼다** (계획 「손잡이」) ──
POOL = (4, 2, 1)                  # 늘 1024 로 찍고, 렌더와 목표를 같이 평균 풀링해 맞댄다 (거친 것부터 — 멀리서 잡힌다).
                                  # 찍는 해상도를 낮추면 삼각형이 2.5 화소 아래일 때 antialias 경사가 0 이 된다 (합성 3만 면에서 확인)
ITERS = (100, 100, 100)
LR = (1e-3, 5e-4, 2.5e-4)         # φ 의 Adam 보폭 (세계 단위 · 키 = 1)
REACH = 0.02                      # 오프셋이 퍼지는 거리 (세계 단위) -> λ = (REACH / 평균 변 길이)²
W_LAP = 0.1                       # 오프셋 라플라시안 벌점 (변 길이로 나눠 무차원)
PROXY_OVER, PROXY_F = 60_000, 30_000   # 면이 이보다 많으면 3만 면 대리 메시를 변형하고 변위장을 원 메시에 옮긴다 (아래 `deform`)
CG_N = 80                         # ponytail: CG 80 회 상한 — λ 가 1000 을 넘는 아주 조밀한 메시에선 덜 풀린 채 쓴다. 촐레스키(cholespy)로 가면 정확


# ═════════════════════════════ 안쪽 다리 (venv · torch + nvdiffrast 만) ═════════════════════════════

def _clip(V, view, bs):
    """세계 (x 가로 · y 깊이 · z 위 · 앞이 −y) -> nvdiffrast 클립. `win.silhouette` · `mask2d.topix` 와 같은 창:
    u ∈ [−0.6, 0.6] · z ∈ [−0.1, 1.1] · 행 0 = z 1.1 (nvdiffrast 행 0 = y_clip −1 이라 뒤집을 필요 없다)."""
    import torch
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    u, d = {"front": (x, y), "side": (y, -x), "back": (bs * x, -y)}[view]
    return torch.stack([u / 0.6, (0.5 - z) / 0.6, d * 0.5, torch.ones_like(x)], 1)[None]


def _cg(M, b, n=CG_N, tol=1e-5):
    import torch
    x = torch.zeros_like(b)
    r, p = b.clone(), b.clone()
    rs = (r * r).sum(0)
    b2 = rs.clamp_min(1e-30)
    for _ in range(n):
        Ap = torch.sparse.mm(M, p)
        a = rs / (p * Ap).sum(0).clamp_min(1e-30)
        x += a * p
        r -= a * Ap
        rn = (r * r).sum(0)
        if float((rn / b2).max()) < tol * tol:
            break
        p = r + (rn / rs.clamp_min(1e-30)) * p
        rs = rn
    return x


def deform(V, F, masks, bs, log=print):
    """조밀한 메시는 **대리 메시**로 푼다. nvdiffrast antialias 는 화소 중심을 덮은 삼각형이 윤곽 변을 가질 때만 경사를 낸다 —
    삼각형이 화소보다 작으면(TripoSG 100만~500만 면) 경사가 **정확히 0** 이다 (09-19 합성 구 65만 정점에서 확인).
    QEM 3만 면 대리를 변형하고, 그 변위를 원 정점에 가까운 대리 정점 16개의 가우스 핵 평균으로 옮긴다 — 원 메시의 디테일은 그대로 실려 간다.
    ponytail: 핵 평균은 대리 한 변보다 가까이 붙은 두 겹(팔과 몸통)을 같이 끈다. 그게 보이면 측지 거리나 면 보간으로."""
    if len(F) <= PROXY_OVER:
        return _deform(V, F, masks, bs, log)
    import pymeshlab
    from scipy.spatial import cKDTree
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(np.asarray(V, np.float64), np.asarray(F, np.int32)))
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum=PROXY_F, preservetopology=False, preserveboundary=True)
    Vp, Fp = ms.current_mesh().vertex_matrix(), ms.current_mesh().face_matrix()
    Vp1, info, s0p, s1p = _deform(Vp, Fp, masks, bs, log)
    dist, idx = cKDTree(Vp).query(np.asarray(V, np.float64), k=16, workers=-1)
    w = np.exp(-0.5 * (dist / info["평균변"]) ** 2) + 1e-12      # 가우스 핵 (σ = 대리 평균 변) — 역거리 가중은 대리 정점마다 옴폭 팬다 (합성에서 거칠기 0 -> 0.059)
    w /= w.sum(1, keepdims=True)
    V1 = np.asarray(V, np.float64) + ((Vp1 - Vp)[idx] * w[:, :, None]).sum(1)
    info.update({"대리": {"면": int(len(Fp)), "정점": int(len(Vp))}, "원면": int(len(F))})
    return V1, info, s0p, s1p


def _deform(V, F, masks, bs, log=print):
    """V (n,3) · F (m,3) · masks {front, side, back: 1024² bool} -> (V', 기록). 같은 자리 정점은 묶어서 푼다 (UV 이음매가 찢어지지 않게)."""
    import torch
    import torch.nn.functional as Fn
    import nvdiffrast.torch as dr

    class Solve(torch.autograd.Function):
        @staticmethod
        def forward(ctx, b):
            return _cg(M, b)

        @staticmethod
        def backward(ctx, g):
            return _cg(M, g.contiguous())

    dev = "cuda"
    uniq, inv = np.unique(np.round(np.asarray(V, np.float64), 6), axis=0, return_inverse=True)
    inv = inv.ravel()
    Fw = inv[np.asarray(F)]
    Fw = Fw[(Fw[:, 0] != Fw[:, 1]) & (Fw[:, 1] != Fw[:, 2]) & (Fw[:, 0] != Fw[:, 2])]
    n = len(uniq)
    E = np.unique(np.sort(np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]]), 1), axis=0)
    e_len = float(np.linalg.norm(uniq[E[:, 0]] - uniq[E[:, 1]], axis=1).mean())
    lam = (REACH / max(e_len, 1e-9)) ** 2

    ij = torch.tensor(np.concatenate([E, E[:, ::-1]]).T, device=dev, dtype=torch.long)
    one = torch.ones(ij.shape[1], device=dev)
    deg = torch.zeros(n, device=dev).index_add_(0, ij[0], one)
    di = torch.arange(n, device=dev)
    # M = I + λ(D − A) · Lrw δ = δ − D⁻¹Aδ (벌점용)
    M = torch.sparse_coo_tensor(torch.cat([ij, torch.stack([di, di])], 1),
                                torch.cat([-lam * one, 1 + lam * deg]), (n, n)).coalesce().to_sparse_csr()
    An = torch.sparse_coo_tensor(ij, one / deg.clamp_min(1)[ij[0]], (n, n)).coalesce().to_sparse_csr()

    V0 = torch.tensor(uniq, device=dev, dtype=torch.float32)
    tri = torch.tensor(Fw, device=dev, dtype=torch.int32)
    tgt = {v: torch.tensor(np.asarray(m, np.float32), device=dev)[None, None] for v, m in masks.items()}
    glctx = dr.RasterizeCudaContext()

    def render(Vx, view, res, soft=True):
        pos = _clip(Vx, view, bs).contiguous()
        rast, _ = dr.rasterize(glctx, pos, tri, (res, res))
        m = (rast[..., 3:4] > 0).float()
        return dr.antialias(m, rast, pos, tri)[0, :, :, 0] if soft else m[0, :, :, 0]

    def 보수(Vx, view):
        """`win.silhouette`(fillConvexPoly · 경계 포함)을 흉내 낸 **검사용** 실루엣 — 4096 으로 찍고 4×4 최대 풀링.
        nvdiffrast 는 화소 중심만 본다: 같은 메시가 반 화소 얇게 나온다 (avatarsample_d 에서 nv 대 win 0.979 — 둘레 6000 화소 × 0.5)."""
        return Fn.max_pool2d(render(Vx, view, 4096, soft=False)[None, None], 4)[0, 0].bool().cpu().numpy()

    # 입력 실루엣은 경계를 **포함**해 칠한 것이라 참 모양보다 반 화소 두껍다. 그대로 목표로 쓰면 메시가 반 화소 부푼다 →
    # 안쪽 한 겹(3×3 침식으로 사라지는 화소)을 덮임 0.5 로 둔다: antialias 의 경계 화소 덮임 평균과 같은 뜻
    tgt = {v: 0.5 * (m - Fn.max_pool2d(-m, 3, 1, 1)) for v, m in tgt.items()}
    with torch.no_grad():
        sil0 = {v: 보수(V0, v) for v in masks}

    phi = torch.zeros_like(V0, requires_grad=True)
    hist = []
    for res, iters, lr in zip(POOL, ITERS, LR):
        pool = (lambda x: Fn.avg_pool2d(x[None, None], res)[0, 0]) if res > 1 else (lambda x: x)
        t = {v: pool(m[0, 0]) for v, m in tgt.items()}
        opt = torch.optim.Adam([phi], lr=lr)
        for it in range(iters):
            d = Solve.apply(phi)
            Vx = V0 + d
            l_sil = sum(((pool(render(Vx, v, 1024)) - t[v]) ** 2).mean() for v in t)
            l_lap = (((d - torch.sparse.mm(An, d)) / e_len) ** 2).mean()
            loss = l_sil + W_LAP * l_lap
            opt.zero_grad()
            loss.backward()
            opt.step()
            if it in (0, iters - 1):
                hist.append({"풀": res, "it": it, "실루엣": round(float(l_sil), 6), "라플": round(float(l_lap), 6)})
                log("      풀 %d it %3d 실루엣 %.5f 라플 %.5f" % (res, it, float(l_sil), float(l_lap)))
    with torch.no_grad():
        d = _cg(M, phi.detach())
        V1 = V0 + d
        sil1 = {v: 보수(V1, v) for v in masks}
        dn = d.norm(dim=1)
        info = {"변형정점": int(n), "변형면": int(len(Fw)), "평균변": round(e_len, 6), "λ": round(lam, 2), "손실": hist,
                "이동_중앙": round(float(dn.median()), 6), "이동_평균": round(float(dn.mean()), 6),
                "이동_최대": round(float(dn.max()), 6), "GPU봉우리GB": round(torch.cuda.max_memory_allocated() / 2 ** 30, 2)}
    return V1.cpu().numpy().astype(np.float64)[inv], info, sil0, sil1


def _다리_main(src, dst):
    with np.load(src) as z:
        V, F, bs = z["V"], z["F"], int(z["bs"])
        masks = {v: z[v] for v in ("front", "side", "back")}
    V1, info, s0, s1 = deform(V, F, masks, bs)
    np.savez(dst, V=V1, info=json.dumps(info, ensure_ascii=False),
             **{"s0_" + v: np.packbits(s0[v]) for v in s0}, **{"s1_" + v: np.packbits(s1[v]) for v in s1})


# ═════════════════════════════ 바깥 (저장소 파이썬 · 자와 그림) ═════════════════════════════

def _무거운():
    """자 · 렌더를 늦게 import 한다 — 안쪽 다리(venv)에는 hull · manifold3d 가 없다."""
    global trimesh, W, C_, DG, MX, DC, fitted, gen_build, voxelize, roughness, fill_slices, J
    sys.path.insert(0, HERE)
    for d in ("실험_20260913", "실험_20260915", "실험_20260916", "실험_20260918", "실험_20260919"):
        sys.path.insert(0, os.path.join(HERE, d))
    os.chdir(HERE)
    import trimesh
    import win as W
    import 대조 as C_
    import 정답 as J
    import 대각 as DG
    import 메시추출 as MX                                   # 읽기 · import 만 (타일 · 틀)
    import 깊이색 as DC
    from 불리언 import fitted
    from 생성깎기 import build as gen_build, voxelize
    from 면 import roughness
    from 겉면채점 import fill_slices


def 변형(mesh, masks, bs):
    """메시 -> venv 다리 -> (변형된 메시, 기록, 변형 전 nvdiffrast 실루엣, 변형 후)."""
    import subprocess
    import tempfile
    d = tempfile.mkdtemp()
    a, b = os.path.join(d, "in.npz"), os.path.join(d, "out.npz")
    np.savez(a, V=np.asarray(mesh.vertices, np.float64), F=np.asarray(mesh.faces, np.int64), bs=bs,
             **{v: np.asarray(masks[v], bool) for v in ("front", "side", "back")})
    r = subprocess.run([VENV, ME, "변형", a, b], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "CUDA_VISIBLE_DEVICES": "0", "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, "변형 다리 실패:\n%s" % (r.stderr or "")[-3000:]
    print(r.stdout, end="", flush=True)
    with np.load(b) as o:
        V1, info = o["V"].copy(), json.loads(str(o["info"]))
        un = lambda k: np.unpackbits(o[k])[:1024 * 1024].reshape(1024, 1024).astype(bool)
        s0 = {v: un("s0_" + v) for v in ("front", "side", "back")}
        s1 = {v: un("s1_" + v) for v in ("front", "side", "back")}
    for p in (a, b):
        os.remove(p)
    os.rmdir(d)
    return trimesh.Trimesh(V1, np.asarray(mesh.faces), process=False), info, s0, s1


def 재다(m, tsil, masks, bs, tg):
    r = {"면": int(len(m.faces)), "부피": round(float(abs(m.volume)), 6)}
    for a in DG.ANG:
        s = DG.sil(m, "front", None, a)
        r["대각%d" % a] = DG.iou(s, tsil[a])
        if a == 45:
            r["구멍45"] = DG.holes(s)
    r["대각평균"] = round(float(np.mean([r["대각%d" % a] for a in DG.ANG])), 5)
    r["못덮음"], r["넘침"] = DG.축(m, masks, bs)             # 메시 · 1024 · 부풀리기 없음 — 다섯 판본에 같은 자
    r["iou128"], r["iou128양쪽"] = DG.iou128(tg, m)
    r["거칠기"] = roughness(m, n=DG.NPT)["거칠기"]
    return r


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[(r["case"], r["이름"])] = r
    return out


def 적다(case, name, rec):
    os.makedirs(os.path.dirname(PROG), exist_ok=True)
    with open(PROG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"case": case, "판": TAG, "이름": name, "때": time.strftime("%Y%m%d_%H%M%S"), **rec},
                           ensure_ascii=False) + "\n")


def one(case, names):
    """한 장. 판본마다 재자마자 jsonl 에 적는다 (세션이 죽어도 남게)."""
    from PIL import Image
    have = rows()
    names = [n for n in names if (case, n) not in have]
    if not names:
        return
    if "T→S" in names:
        assert (case, "상한") in have, "%s: 상한 행(카메라 자기검증)이 먼저 있어야 T→S 를 돌린다" % case
    os.makedirs(TILED, exist_ok=True)
    os.makedirs(MESHD, exist_ok=True)
    t0 = time.time()
    masks, bs, plain, base, axes = gen_build(case)
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    frame = MX.AL.frame_of(truth, 45)
    tsil = {a: DG.sil(truth, "front", None, a) for a in DG.ANG}
    T_, ot = J.grid(truth, J.PITCH)
    tg = (fill_slices(T_), T_, ot)

    def 넣다(name, m, extra=None):
        t1 = time.time()
        rec = 재다(m, tsil, masks, bs, tg)
        rec.update(extra or {})
        old = os.path.join(MX.TILED, "%s__%s.png" % (case, {"H": "MC·불", "정답": "정답"}.get(name, "?")))
        dst = os.path.join(TILED, "%s__%s.png" % (case, name))
        if os.path.exists(old):                              # 메시추출 바퀴의 타일 그대로 (같은 렌더 · 같은 틀)
            Image.open(old).save(dst)
        else:
            Image.fromarray(MX.타일(m, frame)).save(dst)
        rec["초"] = round(time.time() - t1, 1)
        적다(case, name, rec)
        print("    %-5s 대각 %.3f/%.3f/%.3f 못덮음 %.4f 넘침 %.4f iou128 %.3f 구멍 %d 거칠기 %.3f 면 %d (%.0f초)"
              % (name, rec["대각30"], rec["대각45"], rec["대각60"], rec["못덮음"], rec["넘침"], rec["iou128양쪽"],
                 rec["구멍45"], rec["거칠기"], rec["면"], rec["초"]), flush=True)

    print("  %s  %s" % (case, names), flush=True)
    if "정답" in names:
        넣다("정답", truth)
    if "H" in names:
        넣다("H", C_.to_mesh(base, axes))
    if "상한" in names:
        m, info, s0, _ = 변형(truth, masks, bs)
        # **카메라 자기검증** — 정답 메시의 nvdiffrast 렌더가 입력 실루엣 · `win.silhouette` 과 화소 단위로 맞나
        cam = {v: DG.iou(s0[v], masks[v]) for v in s0}
        cam_w = {v: DG.iou(s0[v], DG.sil(truth, v, bs if v == "back" else None)) for v in s0}
        info.update({"카메라_입력IoU": cam, "카메라_winIoU": cam_w, "카메라통과": bool(min(cam.values()) >= 0.98)})
        d = np.linalg.norm(np.asarray(m.vertices) - np.asarray(truth.vertices), axis=1)
        info["이동_px중앙"] = round(float(np.median(d)) / 1.2 * 1024, 3)
        np.savez_compressed(os.path.join(MESHD, case + "__상한.npz"), V=np.asarray(m.vertices, np.float32))
        넣다("상한", m, info)
        assert min(cam_w.values()) >= 0.98, "%s: nvdiffrast 카메라가 win.silhouette 과 안 맞는다 %s — 전부 헛것" % (case, cam_w)
        if not info["카메라통과"]:
            print("    ⚠ 정답 렌더 대 입력 실루엣 %s < 0.98 (win 자로도 같은지 위 값과 견줘라) — 판정에서 뺀다 · 그림에는 남긴다" % cam, flush=True)
    if {"T", "T∩H", "T→S"} & set(names):
        T = fitted(case, masks)
        if "T" in names:
            넣다("T", T)
        if "T∩H" in names:
            넣다("T∩H", C_.to_mesh(voxelize(T, axes) & plain, axes))
        if "T→S" in names:
            m, info, s0, _ = 변형(T, masks, bs)
            info["nv대win_T"] = {v: DG.iou(s0[v], DG.sil(T, v, bs if v == "back" else None)) for v in ("front", "side")}
            np.savez_compressed(os.path.join(MESHD, case + "__TS.npz"), V=np.asarray(m.vertices, np.float32))
            넣다("T→S", m, info)
    print("  %s 끝 %.0f초" % (case, time.time() - t0), flush=True)


# ── 판정 — 집계 함수는 여기 하나. 계획 「Q」 절 그대로 ───────────────────────────────────────────

Q1_몫, Q1_승, Q1_최악, 간격하한 = 0.25, 0.75, -0.25, 0.02
Q2_비, Q2_승 = 0.5, 0.75
Q3_중앙, Q3_최악 = 0.03, 0.08
Q4_대각, Q4_거칠 = 0.97, 0.02


def _st(d):
    v = np.array(list(d.values()), float)
    k = list(d)
    return {"중앙": round(float(np.median(v)), 4), "평균": round(float(v.mean()), 4),
            "최소": [k[int(v.argmin())], round(float(v.min()), 4)], "최대": [k[int(v.argmax())], round(float(v.max()), 4)],
            "장": {a: round(float(b), 4) for a, b in d.items()}}


def verdict(R, cases):
    """R[(case, 이름)] -> 판정. 다섯 판본 + T→S 가 다 있는 장만 쓴다. 뺀 장은 이름과 이유를 적는다."""
    뺌, cs = {}, []
    for c in cases:
        miss = [n for n in COLS if (c, n) not in R]
        if miss:
            뺌[c] = "판본 없음 %s" % miss
        elif not R[(c, "상한")].get("카메라통과"):
            뺌[c] = "카메라 자기검증 짐 %s" % R[(c, "상한")].get("카메라_입력IoU")
        else:
            cs.append(c)
    g = lambda c, n, k: R[(c, n)][k]
    out = {"판": TAG, "장": cs, "뺌": dict(뺌), "집계": "장별 값 -> 중앙(판정) · 평균 · 최악 · 최선 같이"}
    if not cs:
        return out
    # Q4 — 변형이 정답을 망가뜨리나 (이것이 지면 Q1~Q3 숫자를 버린다)
    q4a = {c: g(c, "상한", "대각평균") for c in cs}
    q4b = {c: abs(g(c, "상한", "거칠기") - g(c, "정답", "거칠기")) for c in cs}
    out["Q4"] = {"상한_대각평균": _st(q4a), "거칠기차": _st(q4b),
                 "통과": bool(min(q4a.values()) >= Q4_대각 and max(q4b.values()) <= Q4_거칠)}
    # Q1 — 닫은 몫 = (T→S − T∩H) / (상한 − T∩H) · 대각평균. 간격이 하한보다 좁은 장은 뺀다
    gap = {c: g(c, "상한", "대각평균") - g(c, "T∩H", "대각평균") for c in cs}
    q1c = [c for c in cs if gap[c] >= 간격하한]
    out["Q1_뺌(간격<%.2f)" % 간격하한] = {c: round(gap[c], 4) for c in cs if c not in q1c}
    if q1c:
        몫 = {c: (g(c, "T→S", "대각평균") - g(c, "T∩H", "대각평균")) / gap[c] for c in q1c}
        T몫 = {c: (g(c, "T", "대각평균") - g(c, "T∩H", "대각평균")) / gap[c] for c in q1c}
        H몫 = {c: (g(c, "H", "대각평균") - g(c, "T∩H", "대각평균")) / gap[c] for c in q1c}
        dT = {c: g(c, "T→S", "대각평균") - g(c, "T", "대각평균") for c in cs}
        s = _st(몫)
        승 = float(np.mean([v > 0 for v in 몫.values()]))
        out["Q1"] = {"간격": _st(gap), "닫은몫": s, "승몫": round(승, 3), "대조_T의몫": _st(T몫), "대조_H의몫": _st(H몫),
                     "통과": bool(s["중앙"] >= Q1_몫 and 승 >= Q1_승 and s["최소"][1] >= Q1_최악)}
        out["Q1b"] = {"T→S−T": _st(dT), "통과": bool(np.median(list(dT.values())) > 0)}
    # Q2 — 축 못덮음이 T 의 절반 아래로. 넘침은 같이 싣는다
    비 = {c: g(c, "T→S", "못덮음") / max(g(c, "T", "못덮음"), 1e-9) for c in cs}
    out["Q2"] = {"못덮음비(T→S/T)": _st(비), "승몫": round(float(np.mean([v <= Q2_비 for v in 비.values()])), 3),
                 "넘침차(T→S−T)": _st({c: g(c, "T→S", "넘침") - g(c, "T", "넘침") for c in cs}),
                 "못덮음": {n: _st({c: g(c, n, "못덮음") for c in cs})["중앙"] for n in COLS},
                 "넘침": {n: _st({c: g(c, n, "넘침") for c in cs})["중앙"] for n in COLS}}
    out["Q2"]["통과"] = bool(out["Q2"]["못덮음비(T→S/T)"]["중앙"] <= Q2_비 and out["Q2"]["승몫"] >= Q2_승)
    # Q3 — 거칠기: T∩H 보다 낮고(당연) · T 보다 나빠지지 않는다(진짜 물음)
    a = {c: g(c, "T→S", "거칠기") - g(c, "T∩H", "거칠기") for c in cs}
    b = {c: g(c, "T→S", "거칠기") - g(c, "T", "거칠기") for c in cs}
    sb = _st(b)
    out["Q3"] = {"T→S−T∩H": _st(a), "T→S−T": sb,
                 "통과a": bool(max(a.values()) < 0), "통과b": bool(sb["중앙"] <= Q3_중앙 and max(b.values()) <= Q3_최악)}
    out["Q3"]["통과"] = out["Q3"]["통과a"] and out["Q3"]["통과b"]
    out["참고"] = {k: {n: _st({c: g(c, n, k) for c in cs})["중앙"] for n in COLS}
                   for k in ("대각30", "대각45", "대각60", "iou128양쪽", "구멍45", "거칠기")}
    # 분기 — 결과만. 원인은 안 적는다 (연구루프 3)
    q = lambda k: out.get(k, {}).get("통과")
    if not q("Q4"):
        out["분기"] = "A · Q4 짐 -> Q1~Q3 숫자를 버린다. 변형(정규화 · 카메라)부터 고친다"
    elif q("Q1") and q("Q2") and q("Q3"):
        out["분기"] = "B · 전부 통과 -> 하드서피스 9장으로 넓힌다 (같은 문턱). 기본값은 그대로"
    elif not q("Q1") and q("Q1b"):
        out["분기"] = "C · Q1 짐 · Q1b 통과 -> 변형은 T 를 올리지만 T∩H 를 못 넘는다. 다음 계획 후보: T→S 뒤에 정확 불리언 ∩hull"
    elif not q("Q1"):
        out["분기"] = "D · Q1 짐 · Q1b 짐 -> 이 변형은 held-out 시점에서 T 도 못 올린다. 접는다"
    else:
        out["분기"] = "E · Q1 통과인데 Q2 또는 Q3 짐 -> 넓히지 않는다. 진 Q 를 적고 멈춘다"
    return out


def 판정():
    R = rows()
    cases = sorted({c for c, _ in R}, key=lambda c: (c not in 실물4, c))
    v = verdict(R, cases)
    p = os.path.join(HERE, "out", "기록", "메시변형_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in v if k not in ("참고",)}, ensure_ascii=False, indent=1))
    print("->", p)


def 그림():
    from PIL import Image
    R = rows()
    cases = sorted({c for c, _ in R}, key=lambda c: (c not in 실물4, c))
    rs = []
    for c in cases:
        ts = []
        for n in COLS:
            p = os.path.join(TILED, "%s__%s.png" % (c, n))
            ts.append(np.asarray(Image.open(p).convert("RGB")) if os.path.exists(p) else np.full((300, 300, 3), 240, np.uint8))
        rs.append((c.split("_")[0] + "_" + c.split("_")[1] if "_" in c else c, ts))
    DC.grid(rs, COLS, "메시 변형 — TripoSG 메시를 복셀 없이 세 축 실루엣에 끌어당긴다 (45° 명암 · 같은 빛 · 같은 틀)",
            "T = TripoSG 3판맞춤 · T∩H = 복셀 교집합 · H = hull+타원 깊이(MC·불) · T→S = 실루엣 변형 · 상한 = 정답에 같은 변형",
            os.path.join(HERE, "out", "메시변형_접촉지.png"), S=300)
    print("->", os.path.join(HERE, "out", "메시변형_접촉지.png"))


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def selfcheck():
    """(1) 합성: 구를 타원체의 세 축 실루엣에 끌어당기면 축 IoU 가 오르고 45° 도 오른다 · 매끈함이 안 깨진다
    (2) 판정 함수가 질 수도 이길 수도 있다 (가짜 행)."""
    _무거운()
    for sub, 혹 in ((5, 0.0), (7, 0.004)):                 # 성긴 구(직접) · 조밀하고 오돌토돌한 구(대리 메시 길 · 디테일이 실려 가나)
        sph = trimesh.creation.icosphere(subdivisions=sub, radius=0.30)
        P = np.asarray(sph.vertices)
        P = P * (1 + 혹 / 0.30 * np.sin(60 * P[:, 0]) * np.sin(60 * P[:, 1]) * np.sin(60 * P[:, 2]))[:, None]
        sph = trimesh.Trimesh(P + [0, 0, 0.5], sph.faces, process=False)
        tgt = trimesh.Trimesh((P * [1.25, 0.70, 1.0]) + [0.03, 0, 0.5], sph.faces, process=False)
        masks = {v: DG.sil(tgt, v, None) for v in ("front", "side", "back")}
        i0 = {v: DG.iou(DG.sil(sph, v, None), masks[v]) for v in masks}
        d0 = DG.iou(DG.sil(sph, "front", None, 45), DG.sil(tgt, "front", None, 45))
        m, info, s0, s1 = 변형(sph, masks, -1)
        cam = {v: DG.iou(s0[v], DG.sil(sph, v, None)) for v in masks}
        i1 = {v: DG.iou(DG.sil(m, v, None), masks[v]) for v in masks}
        d1 = DG.iou(DG.sil(m, "front", None, 45), DG.sil(tgt, "front", None, 45))
        r0, r1, rt = (roughness(x, n=DG.NPT)["거칠기"] for x in (sph, m, tgt))
        print("  합성 면 %d %s  카메라(nv 대 win) %s\n        축 IoU %s -> %s\n"
              "        45° %.4f -> %.4f · 거칠기 %.4f -> %.4f (목표 %.4f) · λ %.1f · 이동 최대 %.4f"
              % (len(sph.faces), info.get("대리", "직접"), cam, i0, i1, d0, d1, r0, r1, rt, info["λ"], info["이동_최대"]))
        assert min(cam.values()) >= 0.98, "nvdiffrast 카메라가 win.silhouette 과 안 맞는다 %s" % cam
        assert min(i1.values()) >= 0.97, "합성 변형이 축 실루엣에 못 닿았다 %s" % i1
        # 합성 구의 45° 는 실행마다 +0.029 ~ +0.060 으로 흔들린다 (GPU 합산 순서 · 구는 세 축이 말 안 하는 방향이 넓다).
        # 실물은 안 흔들린다 — 드릴 · 궤짝 세 번씩 대각평균 ±0.001 (`out/기록/메시변형_반복.jsonl`)
        assert d1 > d0 + 0.02, "합성에서 45° 가 안 올랐다"
        assert abs(r1 - r0) <= 0.03, "합성에서 거칠기가 바뀌었다 (가시 또는 뭉갬)"

    def 가짜(ts, 상한=0.99, 정답거칠=0.05, 상한거칠=0.05, ts못=0.01, ts거칠=0.11):
        R = {}
        for c in ("a", "b", "c", "d"):
            for n, s, 못, 거 in (("정답", 1.0, 0, 정답거칠), ("T", 0.80, 0.05, 0.10), ("T∩H", 0.80, 0.003, 0.35),
                                ("H", 0.75, 0.003, 0.30), ("T→S", ts, ts못, ts거칠), ("상한", 상한, 0.001, 상한거칠)):
                R[(c, n)] = {"대각평균": s, "못덮음": 못, "넘침": 0.01, "거칠기": 거, "카메라통과": True,
                             "대각30": s, "대각45": s, "대각60": s, "iou128양쪽": s, "구멍45": 0}
        return verdict(R, ("a", "b", "c", "d"))
    v = 가짜(0.90)
    assert v["Q1"]["통과"] and v["Q2"]["통과"] and v["Q3"]["통과"] and v["Q4"]["통과"] and v["분기"][0] == "B", v
    assert not 가짜(0.82)["Q1"]["통과"] and 가짜(0.82)["분기"][0] == "C"                 # 몫 0.105 < 0.25
    assert 가짜(0.78)["분기"][0] == "D"
    assert not 가짜(0.90, ts못=0.04)["Q2"]["통과"] and not 가짜(0.90, ts거칠=0.20)["Q3"]["통과"]
    assert 가짜(0.90, 상한=0.90)["분기"][0] == "A" and 가짜(0.90, 상한거칠=0.10)["분기"][0] == "A"
    print("  자가검사 통과 — 합성 변형 · 카메라 · 판정이 B/C/D/A 와 Q2·Q3 짐을 다 낼 수 있다")


def main():
    a = sys.argv[1:]
    if a and a[0] == "변형":
        return _다리_main(a[1], a[2])
    if a and a[0] == "검사":
        return selfcheck()
    _무거운()
    if a and a[0] == "판정":
        return 판정()
    if a and a[0] == "그림":
        return 그림()
    names = 대조판 if (a and a[0] == "대조") else ("T→S",)
    a = a[1:] if (a and a[0] == "대조") else a
    n = int(a[0]) if a and a[0].isdigit() else 1
    cases = [c for c in a if not c.isdigit()] or list(실물4)
    have = rows()
    todo = [c for c in cases if any((c, k) not in have for k in names)][:n]
    for c in todo:
        one(c, names)


if __name__ == "__main__":
    main()
