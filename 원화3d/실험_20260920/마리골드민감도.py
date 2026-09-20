# -*- coding: utf-8 -*-
"""**무엇을 주면 Marigold 가 도형을 입체로 보나** — 민감도 카드 (2026-09-20 · 연구루프 1½).

직전 바퀴(`마리골드법선.py`)는 **질감 없는 회색 · 흰 바탕 · 선 없음 · 정사영 · 정면 축정렬** 한 컷에서 쟀고
모델이 도형을 종이로 봤다 (예측 ≈ (0,0,1)). 질감 · 색이 있는 실물에서만 상수 대조를 이겼다.
그래서 이 바퀴는 성능이 아니라 **반응**을 잰다 — 기준선에서 인자 하나씩 켠다.

    A 기준선   직전 바퀴 그대로 (무질감 회색 · 흰 바탕 · 선 없음 · 정사영 · 정면 축정렬 · 셀 3단)
    B 시점     A + 3/4 시점 (방위 35° · 고도 20°)
    C 투영     A + 원근 (FOV 40°)
    D 질감     A + 질감 · 색 (도형은 절차적 나뭇결 · 실물은 있는 그대로)
    E 바탕     A + 바닥 그림자 · 배경 그라데이션
    F 선       A + 외곽선 + 내부 경계선 (겹선 30° · 재질 경계 · 깊이 점프)
    G 전부     B+C+D+E+F
    H 매끈     G 에서 셀 3단 대신 매끈 람베르트

    python 마리골드민감도.py 검사      자가검사 (항등 변환 = A · 구의 해석 법선 · 원근 되돌리기)   [저장소 파이썬]
    python 마리골드민감도.py 입력      구 하나를 A~H 로 -> out/마리골드민감도_입력.png (싼 확인 먼저)  [저장소 파이썬]
    python 마리골드민감도.py 준비      15 장 × 8 조건 입력 · 정답 법선 · 후보 법선(G)               [저장소 파이썬]
    python 마리골드민감도.py 원화      진짜 원화(채색 설정화)를 512² 로 -> 같은 작업 폴더           [저장소 파이썬]
    python 마리골드민감도.py 천장      Marigold 없이 — 조건마다 「상수가 얼마나 좋은가」(= 이길 간격)  [저장소 파이썬]
    python 마리골드민감도.py 추론 [n]  아직 안 한 (장 × 조건) n 개                              [imggen venv · GPU 1]
    python 마리골드민감도.py 재기 · 판정 · 그림

계획 `claudedocs/plan_마리골드민감도_20260920.md`. **문턱은 계획 그대로다.**
규약(축 부호)은 직전 바퀴가 정한 `out/마리골드법선/규약.json` 을 그대로 쓴다 — 카메라가 바뀌어도
규약은 카메라 좌표계(X 오른쪽 · Y 위 · Z 보는 이) 기준이라 조건마다 다시 맞추지 않는다.
**직전 파일은 수정하지 않는다** — import 해서 `load_case` · `shade` · `inflation` · `constant` ·
`angmap` · `cand_score` · `groups` 를 그대로 쓴다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
import numpy as np

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, os.path.join(HERE, "실험_20260920"))
import 마리골드법선 as M0                                      # noqa: E402  직전 바퀴 (수정 금지)

WORK = os.path.join(HERE, "out", "마리골드민감도")
PROG = os.path.join(HERE, "out", "기록", "마리골드민감도_진행.jsonl")
TAG = "마리골드민감도 v1 · A~H 8 조건 512² · marigold-normals-v1-1 fp16 기본스텝 앙상블1 씨앗0 (2026-09-20)"

CASES = M0.CASES
NICK = dict(M0.NICK)
도형 = M0.도형
AZ, EL, FOV = 35.0, 20.0, 40.0
DCAM = 0.6 / np.tan(np.radians(FOV / 2))                        # 창 반높이 0.6 을 FOV 40° 로 담는 거리 = 1.6485
ZC = 0.5                                                        # 투영 중심 (창 z 중앙)

조건 = ("A", "B", "C", "D", "E", "F", "G", "H")
_A = dict(rot=False, persp=False, tex=False, bg=False, line=False, cel=True)
CFG = {"A": dict(_A),
       "B": dict(_A, rot=True),
       "C": dict(_A, persp=True),
       "D": dict(_A, tex=True),
       "E": dict(_A, bg=True),
       "F": dict(_A, line=True),
       "G": dict(rot=True, persp=True, tex=True, bg=True, line=True, cel=True),
       "H": dict(rot=True, persp=True, tex=True, bg=True, line=True, cel=False)}
설명 = {"A": "A 기준선 (직전 바퀴)", "B": "B 시점 3/4 (az35 el20)", "C": "C 원근 (FOV40)", "D": "D 질감 · 색",
       "E": "E 바탕 (그림자 · 그라데이션)", "F": "F 선 (외곽 · 겹선 · 재질)", "G": "G 전부 (B+C+D+E+F)", "H": "H = G 인데 매끈"}

unit, angmap = M0.unit, M0.angmap


# ── 변환 ─────────────────────────────────────────────────────────────────────

def rotmat(az, el):
    """물체를 돌려 3/4 시점을 만든다. 카메라는 그대로 +y 쪽 (X 오른쪽 · Y=월드z 위 · Z=월드y 보는 이).

    R = Rx(−el) @ Rz(+az) — 방위 az 는 물체의 +x 쪽을 카메라로 돌리고, 고도 el 은 윗면을 카메라로 눕힌다."""
    a, e = np.radians(az), np.radians(-el)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1.0]])
    Rx = np.array([[1.0, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    return Rx @ Rz


def place(Vw, rot):
    """-> (Vg, R, s, c). Vg = s·(R·Vw) − c. `win.normalize` 와 같은 규약 (키로 한 번 재고 접지·중앙)."""
    R = rotmat(AZ, EL) if rot else np.eye(3)
    V = Vw @ R.T
    lo, hi = V.min(0), V.max(0)
    s = 1.0 / max(hi[2] - lo[2], 1e-9)
    V = V * s
    lo, hi = V.min(0), V.max(0)
    c = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
    return V - c, R, s, c


def warp(Vg, persp):
    """원근 -> (그리기용 Vd, 되돌리기 계수). 화면 좌표(x, z)만 카메라 거리로 나눈다.
    **깊이 y 는 그대로** 둬서 화가 알고리즘 순서를 지킨다. 카메라는 +y 쪽 (가까울수록 y 가 크다).

    나눈 뒤 **같은 틀에 다시 앉힌다** — 안 그러면 물건이 1.1 ~ 1.5 배 커져 창에 잘린다 (잘리면 실루엣이
    바뀌어 조건 C 가 「원근」이 아니라 「원근 + 잘림」이 된다). 가까운 면이 먼 면보다 크다는 단서는 그대로 남는다."""
    if not persp:
        return Vg, None
    k = DCAM / np.maximum(DCAM - Vg[:, 1], 1e-3)
    V = np.stack([Vg[:, 0] * k, Vg[:, 1], ZC + (Vg[:, 2] - ZC) * k], 1)
    s2 = np.ptp(Vg[:, 2]) / max(np.ptp(V[:, 2]), 1e-9)
    V[:, 0] *= s2
    V[:, 2] *= s2
    dx = (Vg[:, 0].min() + Vg[:, 0].max()) / 2 - (V[:, 0].min() + V[:, 0].max()) / 2
    dz = Vg[:, 2].min() - V[:, 2].min()
    V[:, 0] += dx
    V[:, 2] += dz
    return V, (float(s2), float(dx), float(dz))


def unwarp_px(U, Z, depth, p):
    """화면 좌표 + 그 화소의 깊이 -> 원래 (u, z). `warp` 를 그대로 되돌린다 (질감을 물체에 붙이려고)."""
    if p is None:
        return U, Z
    s2, dx, dz = p
    k = (DCAM + depth) / DCAM                                   # depth = −y
    return (U - dx) / s2 * k, ZC + ((Z - dz) / s2 - ZC) * k


# ── 한 컷 (`마리골드법선.shot` 을 카메라 둘로 늘린 것) ───────────────────────────

def _grid512():
    import win as W
    pu, pz = (W.U1 - W.U0) / 512, (W.Z1 - W.Z0) / 512
    gy, gx = np.mgrid[0:512, 0:512]
    return W.U0 + (gx + 0.5) * pu, W.Z1 - (gy + 0.5) * pz


def plane_abc(Vd, F):
    """삼각형마다 depth = A·u + B·z + C (화면 좌표 위 평면). `시트.edges2` 의 앞부분과 같은 식."""
    T = np.stack([Vd[:, 0], Vd[:, 2], -Vd[:, 1]], 1)[F]
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    flat = np.abs(n[:, 2]) < 0.05 * np.linalg.norm(n, axis=1) + 1e-12
    nd = np.where(flat, 1.0, n[:, 2])
    A, B = np.where(flat, 0, -n[:, 0] / nd), np.where(flat, 0, -n[:, 1] / nd)
    C = np.where(flat, T[:, :, 2].mean(1), T[:, 0, 2] - A * T[:, 0, 0] - B * T[:, 0, 1])
    return A, B, C


def shot2(Vg, Vd, F, col, mat, line=False):
    """(기하용 Vg, 그리기용 Vd) -> (알베도 512², 마스크, 카메라 법선, 면번호 512², 선 512²).

    법선은 **Vg**(원근 왜곡 전)에서 잰다 — 원근은 면의 법선을 바꾸지 않는다.
    뒷면 제거 · 부호 규약은 `마리골드법선.shot` 그대로."""
    import trimesh
    import 시트 as SH
    F = np.asarray(F, np.int64)
    m = trimesh.Trimesh(Vg, F, process=False)
    n = np.asarray(m.face_normals, np.float64)
    wt = bool(m.is_watertight)
    if wt and m.volume < 0:
        n = -n
    cam = n[:, [0, 2, 1]]
    keep = np.nonzero(cam[:, 2] > 1e-9)[0] if wt else np.arange(len(F))
    col = np.full((len(F), 3), 200, np.uint8) if col is None else col
    mat = np.zeros(len(F), np.int32) if mat is None else mat
    rgb, ident = SH.draw(Vd, F[keep], col[keep], mat[keep], "front", line=False)
    edge = np.zeros(ident.shape, bool)
    if line:
        import cv2
        Fk = F[keep]
        edge = SH.edges2(Vd, Fk, -Vd[:, 1], Vd[:, 0], ident, mat[keep], crease_deg=30.0)
        hit = ident >= 0
        edge |= hit & ~cv2.erode(hit.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        edge = cv2.dilate(edge.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)   # 1024 에서 9px = 512 에서 4~5px (원화 선 굵기)
    rgb, ident, edge = rgb[::2, ::2], ident[::2, ::2], edge[::2, ::2]
    mask = ident >= 0
    fid = np.where(mask, keep[np.clip(ident, 0, None)], -1)
    N = cam[np.clip(fid, 0, None)]
    if not wt:
        if (N[mask][:, 2] < 0).mean() > 0.5:
            N = -N
        N = np.where((N[:, :, 2] < -0.3)[:, :, None], -N, N)
    mask = mask & (np.linalg.norm(N, axis=-1) > 0.5)
    N = np.where(mask[:, :, None], unit(N), 0.0)
    return rgb, mask, N.astype(np.float32), fid, edge & mask


# ── 질감 · 바탕 ───────────────────────────────────────────────────────────────

def _noise3(P, seed, cells=24):
    """싼 값잡음 — 씨앗 고정 격자 + 삼선형 보간."""
    from scipy import ndimage
    g = np.random.default_rng(seed).random((cells, cells, cells))
    c = np.mod(P, 1.0) * cells
    return ndimage.map_coordinates(g, [c[..., 0], c[..., 1], c[..., 2]], order=1, mode="wrap")


def wood(P):
    """절차적 나뭇결 — z 축 둘레의 나이테 + 잔결. P 는 물체 좌표 (키 ≈ 1)."""
    r = np.sqrt(P[..., 0] ** 2 + P[..., 1] ** 2)
    t = 0.5 + 0.5 * np.sin(r * 45.0 + _noise3(P * 1.5, 1) * 2.5 + P[..., 2] * 1.2)
    fine = 0.5 + 0.5 * np.sin(_noise3(np.stack([P[..., 0] * 14, P[..., 1] * 14, P[..., 2] * 2], -1), 2) * 14.0)
    base, lit = np.array([146.0, 99.0, 58.0]), np.array([216.0, 176.0, 130.0])
    c = base + (lit - base) * (t ** 0.7)[..., None]
    return np.clip(c * (0.90 + 0.10 * fine[..., None]), 0, 255)


def apply_tex(rgb, mask, fid, Vd, F, R, s, c, wp):
    """화소마다 물체 좌표를 되찾아 나뭇결을 칠한다.

    화소 -> 화면 (U, Z) · 그 삼각형의 평면으로 깊이 -> 원근 되돌리기 -> Vg 좌표 -> R⁻¹((p+c)/s) = 물체 좌표.
    `ponytail: 평면 보간이라 큰 삼각형의 곡면 안쪽은 근사다 — 질감 무늬의 왜곡일 뿐 법선 정답에는 안 걸린다.`"""
    U, Z = _grid512()
    A, B, C = plane_abc(Vd, np.asarray(F, np.int64))
    i = np.clip(fid, 0, None)
    dep = A[i] * U + B[i] * Z + C[i]
    u0, z0 = unwarp_px(U, Z, dep, wp)
    P = (np.stack([u0, -dep, z0], -1) + c) / s @ R                  # (R⁻¹ p) = p @ R  (R 직교)
    return np.where(mask[:, :, None], wood(P), rgb).astype(np.uint8)


def apply_bg(img, mask):
    """바닥 그림자 + 배경 세로 그라데이션 — 물체가 공간에 놓인 것처럼."""
    from scipy import ndimage
    H = img.shape[0]
    g = np.linspace(238, 196, H)[:, None, None] * np.array([1.0, 0.995, 0.975])
    bg = np.clip(g + np.zeros((H, H, 3)), 0, 255)
    if mask.any():
        y1 = int(np.nonzero(mask)[0].max())
        sh = ndimage.zoom(mask.astype(np.float32), (0.20, 1.0), order=1)
        pad = np.zeros_like(mask, np.float32)
        y0 = min(max(y1 - sh.shape[0] // 2 + 6, 0), H - sh.shape[0])
        pad[y0:y0 + sh.shape[0]] = sh
        sh = np.clip(ndimage.gaussian_filter(pad, 9.0) * 1.6, 0, 1)
        bg = bg * (1 - 0.42 * sh)[:, :, None]
    return np.where(mask[:, :, None], img, np.rint(bg)).astype(np.uint8)


# ── 렌더 ─────────────────────────────────────────────────────────────────────

def render(case, k):
    """조건 k 의 (입력 그림 512², 마스크, 정답 카메라 법선). 정답 법선은 **조건마다 그 카메라로 다시** 낸다."""
    cfg = CFG[k]
    Vw, F, col, mat = M0.load_case(case)
    Vg, R, s, c = place(Vw, cfg["rot"])
    Vd, wp = warp(Vg, cfg["persp"])
    rgb, mask, N, fid, edge = shot2(Vg, Vd, F, col, mat, cfg["line"])
    if cfg["tex"] and case.startswith("도형_"):                     # 실물은 있는 그대로 (glb 면색 · avatar_d 회색)
        rgb = apply_tex(rgb, mask, fid, Vd, F, R, s, c, wp)
    img = M0.shade(rgb, mask, N.astype(np.float64), cfg["cel"])
    if cfg["bg"]:
        img = apply_bg(img, mask)
    if cfg["line"]:
        img = np.where(edge[:, :, None], np.uint8(20), img)
    return img, mask, N


# ── 준비 ─────────────────────────────────────────────────────────────────────

def png(case, k):
    return os.path.join(WORK, "%s__%s.png" % (case, k))


def npy(case, k):
    return os.path.join(WORK, "%s__%s.npy" % (case, k))


def prepare():
    from PIL import Image
    os.makedirs(WORK, exist_ok=True)
    for case in CASES:
        line = []
        for k in 조건:
            img, mask, N = render(case, k)
            assert N[mask][:, 2].mean() > 0.1, "%s %s 보이는 면이 카메라를 등진다" % (case, k)
            Image.fromarray(img).save(png(case, k))
            np.savez_compressed(os.path.join(WORK, "%s__%s.npz" % (case, k)), mask=mask, N=N)
            b = mask[0].any() or mask[-1].any() or mask[:, 0].any() or mask[:, -1].any()
            line.append("%s %.3f%s" % (k, mask.mean(), "*" if b else ""))
        print("  %-12s %s" % (NICK[case], " · ".join(line)), flush=True)
    print("  (* = 실루엣이 창에 닿음)")


def load(case, k):
    z = np.load(os.path.join(WORK, "%s__%s.npz" % (case, k)))
    return z["mask"], z["N"].astype(np.float64)


def prepare_cand():
    """판별 후보 메시를 **조건 G 의 카메라**로 법선 렌더 (같은 조건이라야 공정하다). A 도 같이 낸다 (대조)."""
    import 코드기하도형 as CG
    os.makedirs(WORK, exist_ok=True)
    meta = {}
    for gname, cs in M0.groups(CG).items():
        arr, meta[gname] = {}, []
        for i, cd in enumerate(cs):
            m = cd.pop("mesh")
            V, F = np.asarray(m.vertices, np.float64), np.asarray(m.faces)
            for k in ("A", "G"):
                Vg = place(V, CFG[k]["rot"])[0]
                _, Mc, Nc, _, _ = shot2(Vg, warp(Vg, CFG[k]["persp"])[0], F, None, None, False)
                arr["M%s%d" % (k, i)], arr["N%s%d" % (k, i)] = Mc, Nc
            meta[gname].append(cd)
        np.savez_compressed(os.path.join(WORK, "판별__%s.npz" % gname), **arr)
        print("  [%s] %s" % (gname, " · ".join("%s 3D %.3f" % (c["이름"], c["3D"]) for c in meta[gname])), flush=True)
    json.dump(meta, open(os.path.join(WORK, "판별.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def load_group(g, k):
    z = np.load(os.path.join(WORK, "판별__%s.npz" % g))
    meta = json.load(open(os.path.join(WORK, "판별.json"), encoding="utf-8"))[g]
    return [(m, z["M%s%d" % (k, i)], z["N%s%d" % (k, i)].astype(np.float64)) for i, m in enumerate(meta)]


# ── 진짜 원화 (정답 없음 · 관찰만) ────────────────────────────────────────────

ART = []                                                         # 원화() 가 채운다 -> 원화.json


def art_list():
    p = os.path.join(WORK, "원화.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def art_prepare(paths):
    """채색 설정화를 512² 흰 바탕 위에 앉힌다 (자르지 않는다 · 비율 유지). cv2 는 한글 경로를 못 읽어 PIL 로 연다."""
    from PIL import Image
    os.makedirs(WORK, exist_ok=True)
    got = []
    for i, p in enumerate(paths):
        im = Image.open(p).convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im).convert("RGB")
        w, h = im.size
        r = 512 / max(w, h)
        im = im.resize((max(int(w * r), 1), max(int(h * r), 1)), Image.LANCZOS)
        out = Image.new("RGB", (512, 512), (255, 255, 255))
        out.paste(im, ((512 - im.size[0]) // 2, (512 - im.size[1]) // 2))
        name = "원화%d" % i
        out.save(png(name, "원본"))
        got.append({"이름": name, "경로": p, "원크기": [w, h]})
        print("  %s  %s  %dx%d" % (name, os.path.basename(p), w, h), flush=True)
    json.dump(got, open(os.path.join(WORK, "원화.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


# ── 천장 (Marigold 없이 · 이길 간격) ──────────────────────────────────────────

def gap_table():
    """조건마다 「정답 법선 대 상수 (0,0,1)」 각오차 중앙 = 이길 수 있는 간격. 작으면 그 칸은 판정에서 뺀다."""
    out = {}
    print("  %-12s %s" % ("장", " ".join("%6s" % k for k in 조건)))
    for case in CASES:
        r = {}
        for k in 조건:
            mask, N = load(case, k)
            r[k] = {"상수": round(float(np.median(angmap(M0.constant(mask).astype(np.float64), N)[mask])), 2),
                    "inflation": round(float(np.median(angmap(M0.inflation(mask).astype(np.float64), N)[mask])), 2),
                    "전경": round(float(mask.mean()), 4)}
        out[case] = r
        print("  %-12s %s" % (NICK[case], " ".join("%6.1f" % r[k]["상수"] for k in 조건)), flush=True)
    print("\n  inflation")
    for case in CASES:
        print("  %-12s %s" % (NICK[case], " ".join("%6.1f" % out[case][k]["inflation"] for k in 조건)))
    p = os.path.join(WORK, "천장.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", p)


# ── 추론 (imggen venv · GPU 1) ────────────────────────────────────────────────

def infer(n):
    os.environ["CUDA_VISIBLE_DEVICES"] = "1"
    import psutil
    import torch
    from diffusers import MarigoldNormalsPipeline
    from PIL import Image
    todo = [(c, k) for c in CASES for k in 조건] + [(a["이름"], "원본") for a in art_list()]
    todo = [(c, k) for c, k in todo if os.path.exists(png(c, k)) and not os.path.exists(npy(c, k))][:n]
    if not todo:
        print("  다 했다")
        return
    t0 = time.time()
    pipe = MarigoldNormalsPipeline.from_pretrained(M0.MODEL, variant="fp16", torch_dtype=torch.float16).to("cuda")
    pipe.set_progress_bar_config(disable=True)
    print("  올림 %.0f초 · 스텝 %s · 처리해상도 %s · %s" % (time.time() - t0, pipe.default_denoising_steps,
                                                  pipe.default_processing_resolution, torch.cuda.get_device_name(0)), flush=True)
    for case, k in todo:
        t1 = time.time()
        torch.cuda.reset_peak_memory_stats()
        img = Image.open(png(case, k)).convert("RGB")
        out = pipe(img, ensemble_size=1, generator=torch.Generator("cuda").manual_seed(0))
        P = np.asarray(out.prediction)[0].astype(np.float32)
        assert P.shape == (512, 512, 3), P.shape
        np.save(npy(case, k), P)
        r = {"종류": "추론", "판": TAG, "case": case, "조건": k, "초": round(time.time() - t1, 2),
             "VRAM최대MB": round(torch.cuda.max_memory_allocated() / 2 ** 20),
             "RSS_MB": round(psutil.Process().memory_info().rss / 2 ** 20),
             "스텝": int(pipe.default_denoising_steps), "처리해상도": int(pipe.default_processing_resolution)}
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  %-14s %-4s %.1f초 · VRAM %d MB" % (case, k, r["초"], r["VRAM최대MB"]), flush=True)


def pred(case, k):
    s = np.array(json.load(open(os.path.join(HERE, "out", "마리골드법선", "규약.json"), encoding="utf-8"))["부호"], float)
    return unit(np.load(npy(case, k)).astype(np.float64) * s)


# ── 재기 · 판정 ───────────────────────────────────────────────────────────────

def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG and r.get("종류") == "재기":
                out[r["case"]] = r
    return out


def run():
    done = rows()
    for case in CASES:
        if case in done or not all(os.path.exists(npy(case, k)) for k in 조건):
            continue
        r = {"종류": "재기", "판": TAG, "case": case}
        for k in 조건:
            mask, N = load(case, k)
            P = pred(case, k)
            r[k] = {"M": round(float(np.median(angmap(P, N)[mask])), 2),
                    "M평균": round(float(angmap(P, N)[mask].mean()), 2),
                    "상수": round(float(np.median(angmap(M0.constant(mask).astype(np.float64), N)[mask])), 2),
                    "inflation": round(float(np.median(angmap(M0.inflation(mask).astype(np.float64), N)[mask])), 2),
                    "Z평균": round(float(P[mask][:, 2].mean()), 3)}
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  %-12s %s" % (NICK[case], " ".join("%s %5.1f" % (k, r[k]["M"]) for k in 조건)), flush=True)


def st(a):
    a = np.asarray(a, float)
    return {"n": int(len(a)), "중앙": round(float(np.median(a)), 2), "평균": round(float(a.mean()), 2),
            "최악": round(float(a.min()), 2), "최선": round(float(a.max()), 2), "승": int((a > 0).sum())}


def discriminate(k):
    """조건 k 의 카메라에서 후보 고르기. 팔 = 천장 · 상수 · inflation · M."""
    out = {}
    for g in json.load(open(os.path.join(WORK, "판별.json"), encoding="utf-8")):
        cs = load_group(g, k)
        case = M0.group_case(g)
        mask, N = load(case, k)
        arms = {"천장": N, "상수": M0.constant(mask).astype(np.float64),
                "inflation": M0.inflation(mask).astype(np.float64)}
        if os.path.exists(npy(case, k)):                        # Marigold 전(대조군만) 에도 분모를 셀 수 있게
            arms["M"] = pred(case, k)
        sc = {a: [round(M0.cand_score(P, mask, Nc, Mc), 3) for _, Mc, Nc in cs] for a, P in arms.items()}
        pairs = []
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                hi, lo = (i, j) if cs[i][0]["3D"] >= cs[j][0]["3D"] else (j, i)
                if cs[hi][0]["3D"] - cs[lo][0]["3D"] < M0.DIOU:
                    continue
                pairs.append({"높은": cs[hi][0]["이름"], "낮은": cs[lo][0]["이름"],
                              "실루엣이못가름": bool(min(cs[hi][0]["J"], cs[lo][0]["J"]) >= M0.JMIN),
                              **{a: round(sc[a][lo] - sc[a][hi], 3) for a in arms}})
        out[g] = {"후보": [c[0] for c in cs], "점수": sc, "쌍": pairs,
                  "고른후보": {a: cs[int(np.argmin(sc[a]))][0]["이름"] for a in arms},
                  "후회": {a: round(max(c[0]["3D"] for c in cs) - cs[int(np.argmin(sc[a]))][0]["3D"], 4) for a in arms}}
    return out


def denominators():
    """Marigold 없이 — 조건 A · G 에서 판별 분모(실루엣이 못 가르고 천장이 가르는 쌍)와 정보 0 대조의 맞음."""
    out = {}
    for k in ("A", "G"):
        D = discriminate(k)
        Q = [(g, p) for g, r in D.items() for p in r["쌍"] if p["실루엣이못가름"] and p["천장"] >= M0.MARGIN]
        allp = [(g, p) for g, r in D.items() for p in r["쌍"] if p["실루엣이못가름"]]
        out[k] = {"실루엣이못가르는쌍": len(allp), "분모": len(Q), "영상": sorted({g for g, _ in Q}),
                  "상수": sum(p["상수"] >= M0.MARGIN for _, p in Q), "inflation": sum(p["inflation"] >= M0.MARGIN for _, p in Q),
                  "집합별분모": {g: sum(1 for gg, _ in Q if gg == g) for g in D if any(gg == g for gg, _ in Q)}}
        print("  %s  못가르는쌍 %d · 분모 %d · 상수 %d · inflation %d · 영상 %d" %
              (k, len(allp), len(Q), out[k]["상수"], out[k]["inflation"], len(out[k]["영상"])), flush=True)
        print("     %s" % out[k]["집합별분모"])
    json.dump(out, open(os.path.join(WORK, "분모.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


GAP = 15.0                                                       # 「이길 간격」 문턱 — 상수 각오차 중앙이 이보다 작은 칸은 Q1 · Q2 판정에서 뺀다


def verdict():
    rs = rows()
    assert len(rs) == len(CASES), "%d/%d 장만 쟀다" % (len(rs), len(CASES))
    dc = ["도형_" + n for n in 도형]
    v = {"판": TAG, "때": time.strftime("%Y%m%d_%H%M"), "간격문턱": GAP,
         "규약": json.load(open(os.path.join(HERE, "out", "마리골드법선", "규약.json"), encoding="utf-8"))["부호"]}
    M = lambda c, k: rs[c][k]["M"]
    gap = lambda c, k: rs[c][k]["상수"]

    # Q0 배관 — A 를 다시 돌리면 직전 바퀴의 M·셀 과 같아야 한다 (같은 그림 · 같은 씨앗 · 같은 모델)
    prev = {}
    pp = os.path.join(HERE, "out", "기록", "마리골드법선_진행.jsonl")
    if os.path.exists(pp):
        for l in open(pp, encoding="utf-8"):
            r = json.loads(l)
            if r.get("종류") == "재기" and "M·셀" in r:
                prev[r["case"]] = r["M·셀"]["각오차"]["중앙"]
    d0 = {NICK[c]: [M(c, "A"), prev.get(c)] for c in CASES}
    v["Q0"] = {"문턱": "A 의 각오차 중앙이 직전 바퀴 M·셀 과 전부 0.1° 안", "A 대 직전": d0,
               "최대차": round(max(abs(a - b) for a, b in d0.values() if b is not None), 3) if prev else None}
    v["Q0"]["통과"] = bool(prev and v["Q0"]["최대차"] <= 0.1)

    # Q1 살아나는 인자가 있나 — 한 조건 X 에서 (A − X) 개선 중앙 ≥ 10° 이고 간격 ≥ GAP 인 도형 칸의 64% 이상
    q1 = {}
    for k in ("B", "C", "D", "E", "F", "G", "H"):
        use = [c for c in dc if gap(c, k) >= GAP and gap(c, "A") >= GAP]
        d = [M(c, "A") - M(c, k) for c in use]
        q1[k] = {"쓴 장": [NICK[c] for c in use], **(st(d) if d else {"n": 0, "중앙": None, "승": 0}),
                 "필요한 승": int(np.ceil(0.64 * len(use))),
                 "전체 11 장": st([M(c, "A") - M(c, k) for c in dc]),
                 "실물 4": st([M(c, "A") - M(c, k) for c in M0.실물])}
        q1[k]["통과"] = bool(d and q1[k]["중앙"] >= 10.0 and q1[k]["승"] >= q1[k]["필요한 승"])
    v["Q1"] = {"문턱": "한 조건 X 에서 (A − X) 각오차 개선 중앙 ≥ 10° 이고 (간격 ≥ %g° 인) 도형 칸의 64%% 이상에서 개선" % GAP,
               "조건별": q1, "한 인자(B~F) 중 통과": [k for k in ("B", "C", "D", "E", "F") if q1[k]["통과"]]}
    v["Q1"]["통과"] = bool(v["Q1"]["한 인자(B~F) 중 통과"])

    # Q2 전부 켜면 사나 — G 에서 min(상수, inflation) − M > 0 인 도형 ≥ 8/11
    d2 = [min(rs[c]["G"]["상수"], rs[c]["G"]["inflation"]) - M(c, "G") for c in dc]
    v["Q2"] = {"문턱": "G 에서 min(상수, inflation) − M > 0 인 도형 ≥ 8/11", **st(d2),
               "장별": {NICK[c]: round(x, 2) for c, x in zip(dc, d2)},
               "A 에서 같은 자": st([min(rs[c]["A"]["상수"], rs[c]["A"]["inflation"]) - M(c, "A") for c in dc]),
               "실물 4 (G)": st([min(rs[c]["G"]["상수"], rs[c]["G"]["inflation"]) - M(c, "G") for c in M0.실물])}
    v["Q2"]["통과"] = bool(v["Q2"]["승"] >= 8)

    # Q3 구조 판별 — Q3a (A 가 정한 24 쌍 · 카메라 G) · Q3b (같은 쌍의 상수 대비) · Q3c (G 의 새 분모)
    DD = {k: discriminate(k) for k in ("A", "G")}
    for k in DD:
        v["판별_" + k] = DD[k]
    QA = {(g, p["높은"], p["낮은"]) for g, r in DD["A"].items() for p in r["쌍"] if p["실루엣이못가름"] and p["천장"] >= M0.MARGIN}
    cnt = lambda k, arm, S_: sum(1 for g, r in DD[k].items() for p in r["쌍"] if (g, p["높은"], p["낮은"]) in S_ and p[arm] >= M0.MARGIN)
    arms = ("천장", "상수", "inflation", "M")
    QG = [(g, p) for g, r in DD["G"].items() for p in r["쌍"] if p["실루엣이못가름"] and p["천장"] >= M0.MARGIN]
    SG = {(g, p["높은"], p["낮은"]) for g, p in QG}
    v["Q3"] = {"문턱": "Q3a: A 가 정한 24 쌍 · 카메라 G 에서 M ≥ 12/24 -> 증거가 된다 · < 8/24 -> 접는다. "
                     "Q3b: 같은 쌍에서 M ≥ 상수 + 3 쌍이어야 「법선이 실루엣 위에 더한다」",
               "Q3a (A-24 쌍 · 카메라 G)": {a: "%d/%d" % (cnt("G", a, QA), len(QA)) for a in arms},
               "같은 쌍 · 카메라 A (직전 바퀴 재현)": {a: "%d/%d" % (cnt("A", a, QA), len(QA)) for a in arms},
               "Q3c (G 의 새 분모)": {"분모": len(QG), **{a: "%d/%d" % (cnt("G", a, SG), len(QG)) for a in arms},
                                  "집합별(M)": {g: "%d/%d" % (sum(1 for gg, p in QG if gg == g and p["M"] >= M0.MARGIN),
                                                          sum(1 for gg, _ in QG if gg == g)) for g in DD["G"] if any(gg == g for gg, _ in QG)}},
               "고른후보 G": {g: r["고른후보"] for g, r in DD["G"].items()}, "후회 G": {g: r["후회"] for g, r in DD["G"].items()},
               "고른후보 A": {g: r["고른후보"] for g, r in DD["A"].items()}}
    ma, ca = cnt("G", "M", QA), cnt("G", "상수", QA)
    v["Q3"]["Q3a 판정"] = "증거가 된다" if ma >= 12 else ("접는다" if ma < 8 else "중간 — 접지도 쓰지도 않는다")
    v["Q3"]["Q3b 판정"] = "법선이 실루엣 위에 더한다" if ma >= ca + 3 else "3/4 실루엣의 공이지 법선의 공이 아니다 (M %d · 상수 %d)" % (ma, ca)

    # Q4 서술 — 인자별 기여
    v["Q4(서술) 인자별 기여 A − X"] = {k: {"도형11": st([M(c, "A") - M(c, k) for c in dc]),
                                    "실물4": st([M(c, "A") - M(c, k) for c in M0.실물]),
                                    "15장": st([M(c, "A") - M(c, k) for c in CASES])} for k in 조건[1:]}
    v["Q4(서술) 셀 G − 매끈 H"] = {"도형11": st([M(c, "H") - M(c, "G") for c in dc]), "15장": st([M(c, "H") - M(c, "G") for c in CASES])}
    v["Q4(서술) 예측 Z 평균 (1.0 이면 종이)"] = {NICK[c]: {k: rs[c][k]["Z평균"] for k in 조건} for c in CASES}
    v["표"] = {NICK[c]: {k: rs[c][k] for k in 조건} for c in CASES}
    ts = [json.loads(l) for l in open(PROG, encoding="utf-8") if '"추론"' in l]
    ts = [t for t in ts if t.get("판") == TAG]
    v["추론"] = {"장": len(ts), "초 중앙": round(float(np.median([t["초"] for t in ts])), 2), "초 최대": max(t["초"] for t in ts),
               "VRAM최대MB": max(t["VRAM최대MB"] for t in ts), "RSS최대MB": max(t["RSS_MB"] for t in ts)}
    p = os.path.join(HERE, "out", "기록", "마리골드민감도_%s.json" % v["때"])
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("\n  각오차 중앙 (M) · 괄호는 상수")
    print("  %-12s %s" % ("장", " ".join("%13s" % k for k in 조건)))
    for c in CASES:
        print("  %-12s %s" % (NICK[c], " ".join("%6.1f (%5.1f)" % (rs[c][k]["M"], rs[c][k]["상수"]) for k in 조건)))
    for k in ("Q0", "Q1", "Q2", "Q3"):
        print("\n  %s %s" % (k, json.dumps(v[k], ensure_ascii=False)[:2000]))
    print("\n  Q4 %s" % json.dumps(v["Q4(서술) 인자별 기여 A − X"], ensure_ascii=False)[:1200])
    print("\n  ->", p)


# ── 그림 ─────────────────────────────────────────────────────────────────────

def ncolor(N, mask):
    return np.where(mask[:, :, None], np.clip((N + 1) * 127.5, 0, 255), 255).astype(np.uint8)


def figures():
    import sys as _s
    _s.path.insert(0, os.path.join(HERE, "실험_20260913"))
    from PIL import Image
    from 깊이색 import grid
    rs = rows()
    R = []
    for case in CASES:
        mA, NA = load(case, "A")
        tiles = [M0.label(ncolor(NA, mA), "정답 법선 (A 카메라)")]
        for k in 조건:
            mask, N = load(case, k)
            e = angmap(pred(case, k), N)[mask]
            tiles.append(M0.label(ncolor(pred(case, k), mask), "%s\n%.1f° (상수 %.1f°)" % (k, np.median(e), rs[case][k]["상수"]), 28))
        R.append((NICK[case], tiles))
    for a in art_list():
        n = a["이름"]
        im = np.asarray(Image.open(png(n, "원본")).convert("RGB"))
        P = pred(n, "원본")
        R.append((n + "\n(정답 없음)", [M0.label(im, "진짜 원화 (입력)", 26),
                                    M0.label(ncolor(P, np.ones(P.shape[:2], bool)),
                                             "Marigold 예측\nZ 중앙 %.3f (1.0 이면 종이)" % float(np.median(P[:, :, 2])), 26)]
                  + [np.full((512, 512, 3), 255, np.uint8)] * 7))
    grid(R, ["정답 법선 (A 카메라)"] + ["%s" % 설명[k] for k in 조건],
         "Marigold-normals 민감도 — 무엇을 주면 도형을 입체로 보나 (인자 하나씩 · 2026-09-20)",
         "법선색 = (n+1)/2 · X 오른쪽 · Y 위 · Z 보는 이. 배경색(0,0,1)과 같은 파랑 = 「종이로 본다」. 글 = 각오차 중앙 (그 조건의 정답 법선 대비) · 괄호는 상수 대조. 진짜 원화는 정답이 없어 판정에 안 쓴다",
         os.path.join(HERE, "out", "마리골드민감도_접촉지.png"), S=256)


def fig_input(case="도형_구"):
    """싼 확인 — 한 장을 A~H 여덟 조건으로 렌더해서 조건이 실제로 달라 보이는지 눈으로."""
    import sys as _s
    _s.path.insert(0, os.path.join(HERE, "실험_20260913"))
    from 깊이색 import grid
    os.makedirs(WORK, exist_ok=True)
    R = []
    for c in (case, "도형_상자45도", "mech_Drill_8uBbH7Dvmb"):
        R.append((NICK[c], [M0.label(render(c, k)[0], 설명[k], 24) for k in 조건]))
        print("  %s 그림" % NICK[c], flush=True)
    grid(R, [설명[k] for k in 조건], "민감도 입력 — 기준선 A 에서 인자 하나씩 (2026-09-20)",
         "A = 직전 바퀴 그대로. B 시점 · C 원근 · D 질감 · E 바탕 · F 선 · G 전부 · H = G 인데 매끈 람베르트",
         os.path.join(HERE, "out", "마리골드민감도_입력.png"), S=300)


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def selfcheck():
    import trimesh
    s = trimesh.creation.icosphere(subdivisions=4, radius=0.5)
    s.apply_translation([0, 0, 0.5])
    V, F = np.asarray(s.vertices), np.asarray(s.faces)
    # 1 항등 변환 = 직전 바퀴의 shot 과 같다
    Vg, R, sc, c = place(V, False)
    assert np.allclose(R, np.eye(3)) and abs(sc - 1.0) < 1e-6 and np.allclose(c, 0, atol=1e-6), (sc, c)
    a = M0.shot(V, F)
    b = shot2(Vg, warp(Vg, False)[0], F, None, None, False)
    assert (a[1] == b[1]).all() and np.allclose(a[2], b[2], atol=1e-6), "항등 변환이 직전 바퀴와 다르다"
    # 2 구 — 정사영에서는 카메라가 돌아도 해석 법선과 같아야 한다 (C 는 원근이라 이 식이 안 맞는다 — 아래 3 으로 본다)
    for k in ("A", "B"):
        cfg = CFG[k]
        Vg, R, sc, c = place(V, cfg["rot"])
        _, m, N, _, _ = shot2(Vg, warp(Vg, cfg["persp"])[0], F, None, None, False)
        yy, xx = np.nonzero(m)
        cx, cy, r = xx.mean(), yy.mean(), (xx.max() - xx.min() + 1) / 2
        A = np.zeros(N.shape)
        A[m] = np.stack([(xx - cx) / r, -(yy - cy) / r, np.sqrt(np.clip(1 - ((xx - cx) ** 2 + (yy - cy) ** 2) / r ** 2, 0, 1))], 1)
        e = float(np.median(angmap(N.astype(np.float64), unit(A))[m]))
        assert e < 6.0, "구 %s 법선이 해석값과 %.1f° 다르다" % (k, e)
        print("  구 %s 해석 법선 차 %.2f° · 전경 %.3f" % (k, e, m.mean()))
    # 3 원근 되돌리기 — 왜곡 전후가 같은 점으로 돌아온다
    Vg, _, _, _ = place(V, False)
    Vd, wp = warp(Vg, True)
    u0, z0 = unwarp_px(Vd[:, 0], Vd[:, 2], -Vd[:, 1], wp)
    assert np.allclose(u0, Vg[:, 0], atol=1e-6) and np.allclose(z0, Vg[:, 2], atol=1e-6), "원근 되돌리기가 안 맞는다"
    # 3b 원근은 같은 틀에 다시 앉히므로 키는 같고, 모양은 달라야 한다 (가까운 쪽이 상대적으로 크다)
    _, mo, _, _, _ = shot2(Vg, Vg, F, None, None, False)
    _, mp, _, _, _ = shot2(Vg, Vd, F, None, None, False)
    hi = lambda m: (np.nonzero(m)[0].max() - np.nonzero(m)[0].min() + 1)
    assert abs(hi(mp) - hi(mo)) <= 2, "원근 되앉히기가 키를 바꿨다 (%d -> %d)" % (hi(mo), hi(mp))
    print("  원근 — 구는 대칭이라 키 %d -> %d · 넓이 %d -> %d (거의 그대로가 맞다)" % (hi(mo), hi(mp), mo.sum(), mp.sum()))
    # 4 3/4 시점이 정말 다르다 — 상자45도에서 A 와 B 의 법선이 크게 다르다 · 원근은 모양을 바꾼다
    import 코드기하도형 as CG
    bx = CG.build(CG.b_45, CG.구조["상자45도"][2])
    Vb, Fb = np.asarray(bx.vertices, np.float64), np.asarray(bx.faces)
    Vgb = place(Vb, False)[0]
    _, mob, _, _, _ = shot2(Vgb, Vgb, Fb, None, None, False)
    _, mpb, _, _, _ = shot2(Vgb, warp(Vgb, True)[0], Fb, None, None, False)
    assert abs(hi(mpb) - hi(mob)) <= 2 and (mob ^ mpb).sum() > 0.05 * mob.sum(), "원근이 상자 모양을 안 바꿨다"
    NN = {}
    for k in ("A", "B"):
        Vg, _, _, _ = place(Vb, CFG[k]["rot"])
        _, m, N, _, _ = shot2(Vg, Vg, Fb, None, None, False)
        NN[k] = (m, N)
    both = NN["A"][0] & NN["B"][0]
    d = float(np.median(angmap(NN["A"][1][both].astype(np.float64), NN["B"][1][both].astype(np.float64))))
    assert d > 15.0, "3/4 시점이 A 와 거의 같다 (%.1f°)" % d
    # 5 선 · 바탕 · 질감이 그림을 실제로 바꾼다
    imgs = {k: render("도형_구", k)[0] for k in 조건}
    for k in ("B", "C", "D", "E", "F"):
        assert not np.array_equal(imgs[k], imgs["A"]), "조건 %s 가 A 와 같다" % k
    assert imgs["E"][0, 0].mean() < 250 and imgs["A"][0, 0].mean() > 250, "바탕 조건이 배경을 안 바꿨다"
    assert (imgs["F"] < 40).sum() > (imgs["A"] < 40).sum() + 500, "선 조건이 선을 안 그렸다"
    assert imgs["D"][:, :, 0].astype(int).std() > imgs["A"][:, :, 0].astype(int).std(), "질감 조건이 평평하다"
    print("  자가검사 통과 — 상자45도 A 대 B 법선 차 %.1f°" % d)


if __name__ == "__main__":
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    a = sys.argv[1] if len(sys.argv) > 1 else "검사"
    {"검사": selfcheck, "입력": fig_input, "준비": prepare, "후보": prepare_cand,
     "원화": lambda: art_prepare(sys.argv[2:]), "천장": gap_table, "분모": denominators, "재기": run, "판정": verdict, "그림": figures,
     "추론": lambda: infer(int(sys.argv[2]) if len(sys.argv) > 2 else 1)}[a]()
