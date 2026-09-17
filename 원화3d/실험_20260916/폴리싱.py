# -*- coding: utf-8 -*-
"""**폴리싱 — 표면을 매끈하게 하는 세 문을 같은 자리에서 연다** (2026-09-16).

    python 폴리싱.py [케이스]   -> out/폴리싱_깊이색.png · out/폴리싱_<판본>.glb · out/기록/폴리싱_<때>.json

사용자 (09-16): 「형태 잡는 건 오케이. 중요한 건 안티앨리어싱 · 폴리싱 프로세스」 → 「각각 해보고 결과 비교」.

## 판본 (지금 기본 = 타원 lam1.00 위에 얹는다)

    기준         지금 기본 그대로 — 0/1 복셀 -> 마칭큐브 0.5. 계단 한 단 = 칸 = 키의 1/213
    부화소       **안티앨리어싱.** 칸마다 4×4 화소(원화는 1024, 격자는 256)의 덮인 비율을 세서
                 0.5 면을 칸보다 촘촘히 놓는다. 원화 알파의 회색값도 그대로 쓴다 (`win.art_mask` 는 > 127 로 버린다)
    ITK국소      09-13 에 판정 통과하고 기본값에 안 들어간 것 — 두꺼운 곳만 구속 레벨셋 (가는 곳은 원래 면)
    부화소+ITK국소   둘 다
    Z2           `ZSMOOTH` σ2 — 앞·뒷면 깊이를 높이 방향으로만 민다 (09-13 에 찢김 2.6% -> 0.5%)

## 판정 — 돌리기 전에 적는다 (`앨리어싱.py` 의 셋 그대로)

    되받아 재기   세 판 모두 원화 못 덮음 < 6% (`hull.THRESH`)
    가는 곳       가는 곳(지름 13 원판으로 열면 사라지는 화소 — 칼 · 뿔 · 가시) 덮는 비율이 기준보다 1%p 넘게 안 떨어진다
    hull 상한     결과 칸 중 이진 hull 밖이 2% 이하

셋을 지킨 판본만 「통과」. **매끈함은 숫자로 안 잰다** — 결 지표는 09-11 에 두 번 죽었다. 깊이색 그림으로 본다.
"""
import json
import os
import sys
import time

import cv2
import numpy as np
import trimesh
from scipy import ndimage

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260913"))
os.chdir(HERE)
import hull as H
import win as W
import 앨리어싱 as AL
import 깊이색 as DC

VARIANTS = ("기준", "부화소", "ITK국소", "부화소+ITK국소", "Z2")
SUB = W.RES // H.N                                  # 칸 하나에 든 화소 (1024 / 256 = 4)


def soft_masks(case):
    """원화 → **회색까지 살린 덮임 비율** (0..1). `win.art_mask` 와 같은 길인데 문턱을 안 건다."""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    out = {}
    for v, f in src.items():
        im = cv2.imdecode(np.fromfile(os.path.join(base, f), np.uint8), cv2.IMREAD_UNCHANGED)
        if im.ndim == 3 and im.shape[2] == 4:
            a = im[:, :, 3].astype(np.float32) / 255.0
        else:
            g = im if im.ndim == 2 else im[:, :, :3].min(2)
            a = np.clip((250.0 - g.astype(np.float32)) / 250.0 * 4, 0, 1)   # 색으로 가를 때도 250 문턱 언저리를 회색으로
        out[v] = a
    return out


def build(case):
    """`hull.main` 과 같은 순서 + 소프트 마스크를 **같은 변환으로** 함께 옮긴다."""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    soft = soft_masks(case)
    masks, softs = {}, {}
    for v, f in src.items():
        d = H.declutter(W.art_mask(os.path.join(base, f)))
        a = np.where(d, soft[v], 0.0).astype(np.float32)      # 지시선 뺀 자리는 소프트에서도 뺀다
        masks[v], softs[v] = H.to_win(d, a)
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    softs = {v: H._warp_one(a, v, p) for v, a in softs.items()}
    plain, axes = H.carve(masks, back_sign=bs)
    deps = {v: np.ones((W.RES, W.RES), np.float32) for v in W.VIEWS}
    vox, _ = H.carve_default(masks, deps, back_sign=bs)
    return masks, softs, plain, vox, axes, bs, deps


def coverage_field(softs, vox, bs):
    """**부화소 장.** 칸마다 4×4 화소의 덮임 비율을 세 판에서 세고 min — 그게 hull 의 부드러운 경계다.
    깎은 결과(vox)의 부호거리와 다시 min 을 걸어 **깎인 곳은 그대로** 둔다. 단위는 칸 (0.5 를 빼 수준 0 면으로)."""
    cov = {}
    for v, a in softs.items():
        blk = a.reshape(H.N, SUB, H.N, SUB).mean((1, 3))      # (행=z 내림, 열=u) 화소 -> 칸
        cov[v] = blk
    z_idx = np.arange(H.N)[::-1]                              # 행 0 이 z 위쪽이라 뒤집는다
    f = cov["front"][z_idx][:, :]                             # (z, x)
    b = cov["back"][z_idx][:, ::-1] if bs != W.VIEW_AXIS["front"][1] else cov["back"][z_idx]
    s = cov["side"][z_idx][:, :]                              # (z, y)
    fx = np.minimum(f, b).T[:, None, :]                       # (x, 1, z)
    sy = s.T[None, :, :]                                      # (1, y, z)
    soft = np.minimum(fx, sy) - 0.5                           # 0 면이 실루엣 경계
    return np.minimum(soft, H.sdf_of(vox))


def variants(case):
    masks, softs, plain, vox, axes, bs, deps = build(case)
    soft = coverage_field(softs, vox, bs)
    out = {}
    out["기준"] = AL.variant("기준", vox, axes)
    out["부화소"] = (AL.clean(*H.mesh_from_field(soft, axes)), soft > 0)
    out["ITK국소"] = AL.variant("ITK국소", vox, axes)
    itk_f = H.sdf_of(out["ITK국소"][1])                        # ITK 결과를 다시 거리장으로 (섞기는 AL 안에서 끝났다)
    out["부화소+ITK국소"] = (AL.clean(*H.mesh_from_field(np.minimum(soft, itk_f), axes)), (np.minimum(soft, itk_f) > 0))
    z0 = H.ZSMOOTH
    try:
        H.ZSMOOTH = 2.0
        v2, _ = H.carve_default(masks, deps, back_sign=bs)
    finally:
        H.ZSMOOTH = z0
    out["Z2"] = AL.variant("기준", v2, axes)
    return out, masks, plain, bs


def shaded(mesh, az, frame, S=400, tint=None):
    """**눈으로 보는 판** — z 버퍼로 면 번호를 남기고 그 면의 법선으로 명암을 준다.
    09-13 의 화가 알고리즘 렌더러는 앞뒤가 섞이고 명암이 거의 검게 나왔다 (README 「렌더러가 틀렸다」).
    여기선 가림은 깊이로 정하고 색은 면 법선으로만 정한다 — 계단이 있으면 칸마다 명암이 뚝뚝 끊긴다."""
    R = 2 * S
    F = np.asarray(mesh.faces)
    P = DC.project(mesh, az, frame, R)[F]                     # (n, 3, 3) x · y · 깊이
    a = np.radians(az)
    c, s = np.cos(a), np.sin(a)
    Nf = np.asarray(mesh.face_normals)
    Nf = np.stack([c * Nf[:, 0] - s * Nf[:, 1], s * Nf[:, 0] + c * Nf[:, 1], Nf[:, 2]], 1)
    # 빛을 옆에서 비스듬히 준다 — 카메라와 같은 쪽에서 비추면 계단의 두 면이 둘 다 밝아 결이 안 보인다
    L = np.array([-0.78, -0.50, 0.38])
    L /= np.linalg.norm(L)
    # **양면 명암** — 마칭큐브 · 생성 메시는 감김이 섞여 각도마다 앞뒤가 뒤집힌다. 가림은 z 버퍼가 이미 정했으니
    # 보이는 면만 |n·L| 로 칠한다 (한 그림 안에서 명암이 뒤집히지 않는다 · 2026-09-16)
    lit = 0.10 + 0.90 * np.abs(Nf @ L)
    zb = np.full((R, R), np.inf)
    idx = np.full((R, R), -1, np.int32)
    lo = np.clip(np.floor(P[:, :, :2].min(1)), 0, R - 1).astype(int)
    hi = np.clip(np.ceil(P[:, :, :2].max(1)), 0, R - 1).astype(int)
    for i in range(len(P)):
        (x1, y1, d1), (x2, y2, d2), (x3, y3, d3) = P[i]
        den = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(lo[i, 0], hi[i, 0] + 1) + 0.5, np.arange(lo[i, 1], hi[i, 1] + 1) + 0.5)
        l1 = ((y2 - y3) * (gx - x3) + (x3 - x2) * (gy - y3)) / den
        l2 = ((y3 - y1) * (gx - x3) + (x1 - x3) * (gy - y3)) / den
        l3 = 1 - l1 - l2
        m = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
        if not m.any():
            continue
        d = l1 * d1 + l2 * d2 + l3 * d3
        sz = zb[lo[i, 1]:hi[i, 1] + 1, lo[i, 0]:hi[i, 0] + 1]
        si = idx[lo[i, 1]:hi[i, 1] + 1, lo[i, 0]:hi[i, 0] + 1]
        up = m & (d < sz)
        sz[up] = d[up]
        si[up] = i
    col = lit[:, None] * (np.ones((1, 3)) if tint is None else tint)   # tint: 면마다 RGB 곱 (감지 표시용)
    img = np.where((idx >= 0)[:, :, None], 255 * col[np.clip(idx, 0, None)], 247.0)
    img = img.reshape(S, 2, S, 2, 3).mean((1, 3))             # 2×2 평균 = 화면 안티앨리어싱 (메시가 아니라 그림만)
    return np.clip(img, 0, 255).astype(np.uint8)


def selfcheck():
    """부화소 장이 **칸 안에서** 면을 옮기는지 — 반만 덮인 칸의 0 면은 칸 가운데가 아니라 경계 쪽이다."""
    a = np.zeros((SUB, SUB), np.float32)
    a[:, :SUB // 2] = 1.0                                     # 칸 하나가 정확히 반 덮임
    assert abs(a.mean() - 0.5) < 1e-6
    q = np.array([1.0, 1.0, 0.75, 0.25, 0.0]) - 0.5
    i = np.where(np.diff(np.sign(q)))[0][0]
    t = q[i] / (q[i] - q[i + 1])                              # 선형 보간 위치
    assert i == 2 and abs(t - 0.5) < 1e-6, "부화소 면 위치가 틀렸다 (%d %.3f)" % (i, t)
    print("  자가검사 통과 — 부화소 면 위치")


def main():
    case = sys.argv[1] if len(sys.argv) > 1 else H.CASE
    H.register_sheets()
    selfcheck()
    t0 = time.time()
    vs, masks, plain, bs = variants(case)
    rows, rec = [], {"case": case, "때": time.strftime("%Y-%m-%d %H:%M"), "판본": {}}
    base = None
    for n in VARIANTS:
        mesh, occ = vs[n]
        rp = AL.reproject(mesh, masks, bs)
        outside = float((occ & ~plain).sum() / max(occ.sum(), 1))
        r = {"못덮음": {v: round(rp[v]["miss"], 4) for v in W.VIEWS},
             "가는곳": {v: round(rp[v]["thin"], 4) for v in W.VIEWS},
             "hull밖": round(outside, 4), "면": len(mesh.faces), "닫힘": bool(mesh.is_watertight)}
        if base is None:
            base = r
            r["판정"] = "기준"
        else:
            ok = (max(r["못덮음"].values()) < H.THRESH
                  and all(r["가는곳"][v] >= base["가는곳"][v] - AL.THIN_DROP for v in W.VIEWS)
                  and outside <= AL.OUTSIDE)
            r["판정"] = "통과" if ok else "짐"
        rec["판본"][n] = r
        mesh.export(os.path.join(HERE, "out", "폴리싱_%s.glb" % n))
        print("  %-12s 못덮음 %s · 가는곳 %s · hull밖 %.2f%% · 면 %d · %s"
              % (n, " ".join("%.2f%%" % (100 * r["못덮음"][v]) for v in W.VIEWS),
                 " ".join("%.1f%%" % (100 * r["가는곳"][v]) for v in W.VIEWS),
                 100 * outside, len(mesh.faces), r["판정"]), flush=True)
    q = os.path.join(HERE, "out", "기록", "폴리싱_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(rec, open(q, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 그림 — 깊이색 (조명 없음 · z 버퍼). 같은 열은 틀 · 깊이 범위가 같다
    ref = vs["기준"][0]
    views = (-90, 45)
    fr = {az: AL.frame_of(ref, az) for az in views}
    dr = {az: DC.depth_range(ref, az) for az in views}
    (x0, z0), span = fr[-90]
    zoom = ((x0 + 0.30 * span, z0 + 0.45 * span), 0.35 * span)
    for n in VARIANTS:
        m = vs[n][0]
        tiles = [DC.colorize(DC.zbuffer(m, az, fr[az], 400), dr[az]) for az in views]
        tiles.append(DC.colorize(DC.zbuffer(m, -90, zoom, 400), dr[-90]))
        rows.append((n, tiles))
        print("  %s 그림" % n, flush=True)
    DC.grid(rows, ["옆 (az −90)", "45도", "옆 확대"],
            "폴리싱 — %s · 지금 기본(타원 lam1.00) 위에 얹은 네 문 (깊이색 · 조명 없음)" % case,
            "빨강 = 가깝다 · 검은 선 = 같은 깊이. 선이 매끈하면 면이 매끈하고 톱니면 계단이다 · 부화소 = 칸 안 4×4 화소 덮임으로 면을 칸보다 촘촘히",
            os.path.join(HERE, "out", "폴리싱_깊이색.png"))

    # 그리고 **그냥 보이는 판** — 같은 메시 · 같은 틀 · 면 법선 명암
    srows = []
    for n in VARIANTS:
        m = vs[n][0]
        tiles = [shaded(m, az, fr[az], 400) for az in views] + [shaded(m, -90, zoom, 400)]
        srows.append((n, tiles))
        print("  %s 명암" % n, flush=True)
    DC.grid(srows, ["옆 (az −90)", "45도", "옆 확대"],
            "폴리싱 — %s · 같은 메시를 그냥 본 것 (면 법선 명암 · z 버퍼)" % case,
            "빛 하나 · 회색 한 가지. 면이 매끈하면 명암이 이어지고, 칸 계단이면 줄무늬로 끊긴다",
            os.path.join(HERE, "out", "폴리싱_명암.png"))
    print("  %.0f초 · -> %s" % (time.time() - t0, q))


if __name__ == "__main__":
    main()
