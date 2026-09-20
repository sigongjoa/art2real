# -*- coding: utf-8 -*-
"""**학습된 법선 추정기(Marigold-normals)가 한 컷에서 면을 맞히고 구조를 가르는가** (2026-09-20).

    python 마리골드법선.py 검사        자가검사 (구 해석 법선 · 상자45도 두 면 · 자의 거동)          [저장소 파이썬]
    python 마리골드법선.py 준비        입력 두 조건 · 정답 법선 · 후보 법선 -> out/마리골드법선/          [저장소 파이썬]
    python 마리골드법선.py 천장        Marigold 없이 — 대조군 · 천장만으로 자 전부 (계획서에 옮겨 적는다)   [저장소 파이썬]
    python 마리골드법선.py 추론 [n]    아직 안 한 (장 × 조건) n 개 -> <장>__<조건>.npy                 [imggen venv · GPU 1]
    python 마리골드법선.py 규약        구 한 장으로 축 부호 조합을 고른다 -> 규약.json (배관)             [저장소 파이썬]
    python 마리골드법선.py 재기        장마다 -> out/기록/마리골드법선_진행.jsonl                        [저장소 파이썬]
    python 마리골드법선.py 판정 · 그림

계획 `claudedocs/plan_마리골드법선_20260920.md`. **문턱은 계획 그대로다 — 숫자를 보고 안 바꾼다.**
기하를 안 만든다 — 법선은 **증거로만** 쓴다 (09-19 깊이원: 깊이 모델을 기하에 직접 넣는 건 기각).
렌더 · 정답 평면 · 분할 자는 09-19 `알베도면` · `알베도광원` · `시트.draw` 를 그대로 부른다.
`추론` 은 torch · diffusers · PIL · numpy 만 쓴다 (imggen venv 에 manifold3d 가 없다).
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
import numpy as np

HERE = r"G:\art2real\원화3d"
WORK = os.path.join(HERE, "out", "마리골드법선")
PROG = os.path.join(HERE, "out", "기록", "마리골드법선_진행.jsonl")
CGPROG = os.path.join(HERE, "out", "기록", "코드기하도형_진행.jsonl")
TAG = "마리골드법선 v1 · front 한 컷 512² · 매끈/셀3 · L_A · marigold-normals-v1-1 fp16 기본스텝 앙상블1 씨앗0 (2026-09-20)"
MODEL = r"G:\manga_anim\3d\hf\local_marigold-normals-v1-1"   # HF `prs-eth/marigold-normals-v1-1` 의 fp16 safetensors.
# 허브 캐시(HF_HOME)는 심볼릭 링크 권한(WinError 1314)으로 죽어서 `snapshot_download(local_dir=...)` 로 받았다

도형 = ("상자", "원기둥", "원뿔", "구", "두기둥나란히", "상자45도", "두기둥대각", "L자", "치마", "토러스세움", "토러스옆")
실물 = ("mech_Drill_8uBbH7Dvmb", "cloak_Chest_Closed_AngpV0HxD8", "cape_Hat_Stylised_lNN3PlrjSa", "avatarsample_d")
CASES = tuple("도형_" + n for n in 도형) + 실물
NICK = {**{"도형_" + n: n for n in 도형}, 실물[0]: "드릴", 실물[1]: "닫힌 궤짝", 실물[2]: "모자", 실물[3]: "avatar_d"}
조건 = ("매끈", "셀")
L_CAM = np.array([-1.0, 1.0, 1.0]) / np.sqrt(3)      # 09-19 L_A 좌상단 (월드 (−1,1,1)) 를 카메라 좌표 (X 오른쪽 · Y 위 · Z 보는 이) 로
CEL = (1 / 6, 1 / 2, 5 / 6)                          # 음영 s 를 3 칸으로 나눈 칸 중심
TAU = 15.0                                           # 이웃 화소 법선을 같은 면으로 잇는 각 = **정답 평면의 이면각 문턱과 같은 15°**.
# 처음엔 6° 로 적었는데 대조군만 돌린 단계에서 천장(정답 법선 잇기)이 토러스에서 0.107 로 죽었다 — 토러스 정답 메시의
# 이웃 면이 11.25° 씩 꺾인다. 정답 정의와 같은 값으로 맞췄다 (Marigold 를 보기 전)
TAUS = (6.0, 10.0, 15.0)                             # 민감도 (서술)
FLAT_DEV, FLAT_AREA = 1.0, 200                       # 「평면」 = 정답 평면 조각 안 법선이 평균에서 1° 안 · 200 화소 이상
DIOU, MARGIN, JMIN = 0.03, 2.0, 0.99                 # 판별 쌍: |Δ3D IoU| ≥ 0.03 · 천장 여유 ≥ 2° · 둘 다 J ≥ 0.99 면 「실루엣이 못 가르는 쌍」


# ── 저장소 쪽 모듈 (추론에서는 안 부른다) ─────────────────────────────────────

def _repo():
    for p in (HERE, os.path.join(HERE, "실험_20260913"), os.path.join(HERE, "실험_20260919"), os.path.join(HERE, "실험_20260920")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import 알베도면 as A1
    import 알베도광원 as A2
    import 시트 as SH
    import win as W
    return A1, A2, SH, W


def unit(v):
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-12)


def angmap(P, G):
    return np.degrees(np.arccos(np.clip((P * G).sum(-1), -1, 1)))


# ── 한 컷 — 색 · 삼각형 번호 · 카메라 좌표 법선 ───────────────────────────────

def shot(Vw, F, col=None, mat=None):
    """창 좌표 메시 -> (알베도 512², 마스크, 카메라 법선). `시트.draw` front · 선 없음 · 2 배 줄임 (09-19 와 같다).

    카메라 좌표 = (X 오른쪽 = 월드 +x · Y 위 = 월드 +z · Z 보는 이 쪽 = 월드 +y). 닫힌 메시는 부피 부호로
    법선을 한 번에 맞추고 **뒷면을 뺀 뒤** 칠한다 (화가 알고리즘이 큰 삼각형에서 순서를 틀린다).
    안 닫힌 메시는 보이는 화소 과반으로 전역 부호를 맞추고, 뚜렷이 등진 화소(n_z < −0.3)만 뒤집는다."""
    import trimesh
    _, _, SH, _ = _repo()
    F = np.asarray(F, np.int64)
    m = trimesh.Trimesh(Vw, F, process=False)
    n = np.asarray(m.face_normals, np.float64)
    wt = bool(m.is_watertight)
    if wt and m.volume < 0:
        n = -n
    cam = n[:, [0, 2, 1]]
    keep = np.nonzero(cam[:, 2] > 1e-9)[0] if wt else np.arange(len(F))
    col = np.full((len(F), 3), 200, np.uint8) if col is None else col
    mat = np.zeros(len(F), np.int32) if mat is None else mat
    rgb, ident = SH.draw(Vw, F[keep], col[keep], mat[keep], "front", line=False)
    rgb, ident = rgb[::2, ::2], ident[::2, ::2]
    mask = ident >= 0
    fid = np.where(mask, keep[np.clip(ident, 0, None)], -1)
    N = cam[np.clip(fid, 0, None)]
    if not wt:
        if (N[mask][:, 2] < 0).mean() > 0.5:
            N = -N
        N = np.where((N[:, :, 2] < -0.3)[:, :, None], -N, N)
    mask = mask & (np.linalg.norm(N, axis=-1) > 0.5)             # 퇴화 삼각형
    N = np.where(mask[:, :, None], unit(N), 0.0)
    return rgb, mask, N.astype(np.float32), fid


def load_case(case):
    """-> (Vw, F, col, mat). 모델 glb 가 있으면 `알베도면.cut` 과 같은 길(색 있음), 없으면 truth.glb (회색 200)."""
    import trimesh
    _, _, SH, W = _repo()
    p = os.path.join(HERE, "out", "모델", "%s.glb" % case)
    if os.path.exists(p):
        V, F, col, mat = SH.faces_with_color(trimesh.load(p))
        Vw = W.to_world(V, "xyz")
        Vw[:, 1] *= -1
        return W.normalize(Vw), F, col, mat
    t = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    return np.asarray(t.vertices, np.float64), np.asarray(t.faces), None, None


def shade(rgb, mask, N, cel):
    s = np.clip(N @ L_CAM, 0, 1)
    if cel:
        s = np.asarray(CEL)[np.minimum((s * 3).astype(int), 2)]
    img = np.rint(rgb.astype(np.float64) * s[:, :, None])
    return np.where(mask[:, :, None], img, 255).astype(np.uint8)


# ── 대조군 · 자 ───────────────────────────────────────────────────────────────

def inflation(mask):
    """실루엣만 보는 법선. 높이 h(d) = sqrt(2Rd − d²) · d = 안쪽 거리 · R = 최대 안쪽 거리 (구 · 원기둥에서 정확). 손잡이 없음."""
    from scipy import ndimage
    d = ndimage.distance_transform_edt(mask)
    R = max(float(d.max()), 1.0)
    h = ndimage.gaussian_filter(np.sqrt(np.clip(2 * R * d - d * d, 0, None)), 2.0)
    gy, gx = np.gradient(h)
    return np.where(mask[:, :, None], unit(np.stack([-gx, gy, np.ones_like(h)], -1)), 0.0).astype(np.float32)


def constant(mask):
    return np.where(mask[:, :, None], np.array([0, 0, 1.0]), 0.0).astype(np.float32)


def merge_small(lab, mask, amin):
    """`알베도면.cc` 의 뒷반 — 작은 조각을 제일 가까운 남은 조각에 붙이고 번호를 다시 매긴다."""
    from scipy import ndimage
    out = np.where(mask, lab, -1)
    big = np.bincount(out[mask]) >= amin
    keep = mask & big[np.clip(out, 0, None)]
    if keep.any():
        _, (iy, ix) = ndimage.distance_transform_edt(~keep, return_indices=True)
        out = np.where(mask, np.where(keep, out, out[iy, ix]), -1)
    res = np.full(lab.shape, -1, np.int32)
    res[mask] = np.unique(out[mask], return_inverse=True)[1]
    return res


def link_regions(N, mask, tau, amin):
    """법선 그림 -> 면 조각. 이웃 화소의 법선 사이 각이 tau 미만이면 잇는다 (정답의 「이면각 15° 연결」과 같은 족)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    idx = np.full(mask.shape, -1, np.int64)
    idx[mask] = np.arange(mask.sum())
    c = np.cos(np.radians(tau))
    ea, eb = [], []
    for sa, sb in ((np.s_[:, :-1], np.s_[:, 1:]), (np.s_[:-1, :], np.s_[1:, :])):
        ok = mask[sa] & mask[sb] & ((N[sa] * N[sb]).sum(-1) > c)
        ea.append(idx[sa][ok]); eb.append(idx[sb][ok])
    ea, eb = np.concatenate(ea), np.concatenate(eb)
    k = int(mask.sum())
    lab = np.full(mask.shape, -1, np.int64)
    lab[mask] = connected_components(coo_matrix((np.ones(len(ea)), (ea, eb)), shape=(k, k)), directed=False)[1]
    return merge_small(lab, mask, amin)


def inner_boundary(lab, mask):
    b = np.zeros(mask.shape, bool)
    for sa, sb in ((np.s_[:, :-1], np.s_[:, 1:]), (np.s_[:-1, :], np.s_[1:, :])):
        e = mask[sa] & mask[sb] & (lab[sa] != lab[sb])
        b[sa] |= e
    return b


def boundary_f1(gt, seg, mask, tol=2.0):
    from scipy import ndimage
    bg, bs = inner_boundary(gt, mask), inner_boundary(seg, mask)
    if not bg.any() and not bs.any():
        return 1.0
    if not bg.any() or not bs.any():
        return 0.0
    p = float((ndimage.distance_transform_edt(~bg)[bs] <= tol).mean())
    r = float((ndimage.distance_transform_edt(~bs)[bg] <= tol).mean())
    return round(2 * p * r / max(p + r, 1e-9), 4)


def flat_regions(gt, N, mask):
    """정답에서 평면인 조각 번호들 — 조각 안 정답 법선이 평균에서 FLAT_DEV 안 · FLAT_AREA 이상."""
    out = []
    for k in np.unique(gt[mask]):
        m = mask & (gt == k)
        if m.sum() < FLAT_AREA:
            continue
        mu = unit(N[m].mean(0))
        if angmap(N[m], mu).max() < FLAT_DEV:
            out.append(int(k))
    return out


def flatness(P, gt, flats, mask):
    """평면 조각 안 예측 법선의 각 RMS (조각 평균 법선 기준 · 넓이 가중). 평면이 없으면 None."""
    if not flats:
        return None
    a = w = 0.0
    for k in flats:
        m = mask & (gt == k)
        mu = unit(P[m].mean(0))
        a += m.sum() * float(np.sqrt((angmap(P[m], mu) ** 2).mean()))
        w += m.sum()
    return round(a / w, 3)


def crease_err(P, G, gt, flats, mask):
    """이웃한 정답 평면 쌍마다 |예측 면간각 − 정답 면간각| 의 평균 — 「꺾임을 그 각으로 내나」(서술)."""
    fl = set(flats)
    pairs = set()
    for sa, sb in ((np.s_[:, :-1], np.s_[:, 1:]), (np.s_[:-1, :], np.s_[1:, :])):
        e = mask[sa] & mask[sb] & (gt[sa] != gt[sb])
        pairs |= {tuple(sorted(x)) for x in zip(gt[sa][e].tolist(), gt[sb][e].tolist())}
    pairs = [p for p in pairs if p[0] in fl and p[1] in fl]
    if not pairs:
        return None
    mu = lambda X, k: unit(X[mask & (gt == k)].mean(0))
    d = [abs(float(angmap(mu(P, a), mu(P, b))) - float(angmap(mu(G, a), mu(G, b)))) for a, b in pairs]
    return {"쌍": len(pairs), "평균": round(float(np.mean(d)), 2)}


def ang_stats(P, G, mask):
    e = angmap(P, G)[mask]
    return {"중앙": round(float(np.median(e)), 2), "평균": round(float(e.mean()), 2),
            "11.25": round(float((e < 11.25).mean()), 4), "22.5": round(float((e < 22.5).mean()), 4),
            "30": round(float((e < 30).mean()), 4)}


def seg_marks(gt, seg, mask):
    A1 = _repo()[0]
    return {**A1.marks(gt, seg, mask), "경계F1": boundary_f1(gt, seg, mask)}


def measure(P, d, tau=TAU):
    """법선 예측 하나를 자 전부로."""
    A1 = _repo()[0]
    mask, G, gt, flats = d["mask"], d["N"], d["gt"], d["flats"]
    P = np.where(mask[:, :, None], unit(P), 0.0)
    return {"각오차": ang_stats(P, G, mask), "평면성": flatness(P, gt, flats, mask),
            "면간각": crease_err(P, G, gt, flats, mask),
            "분할": seg_marks(gt, link_regions(P, mask, tau, A1.AMIN), mask)}


def cand_score(P, Mp, Nc, Mc):
    """후보 법선 렌더 대 예측. 합집합 위 평균 각오차 — 겹치지 않는 화소는 90°."""
    U = Mp | Mc
    e = np.full(Mp.shape, 90.0)
    both = Mp & Mc
    e[both] = angmap(P, Nc)[both]
    return float(e[U].mean())


# ── 준비 ─────────────────────────────────────────────────────────────────────

def cg_rows():
    return {json.loads(l)["case"]: json.loads(l) for l in open(CGPROG, encoding="utf-8")}


def groups(CG):
    """판별 후보 집합. -> {이름: [{"이름", "3D", "J", "θ", "mesh"}]}.

    ① 도형 문의 기록 그대로 — 상자45도 · L자 의 재시작 다섯(+정답θ) · 두기둥대각 정답 대 거울상 · 도형마다 코드기하 최선1 대 상자 합 최선1.
    ② **구조 바꿔치기** — 정답 구조 대 「앞·옆 실루엣이 같은 다른 구조」. 대안은 두 판 visual hull(앞 기둥 ∩ 옆 기둥 = 현행 H 의 구조)과
       같은 직사각 실루엣 족(상자 · 원기둥 · 45° 상자). 3D IoU · J 는 도형 문과 같은 함수(`viou` · `Jsil`)로 여기서 잰다."""
    import trimesh
    rs = cg_rows()
    R = lambda n: rs["도형_" + n]
    best = lambda r, 팔: r[팔]["재시작"][r[팔]["최선1"]]
    mk = lambda nm, kind, th, iou, J: {"이름": nm, "3D": iou, "J": J, "θ": [round(float(x), 4) for x in th],
                                       "mesh": CG.build(CG.b_상자합 if kind == "상자합" else CG.구조[kind][1], th)}
    g = {}
    for n in ("상자45도", "L자"):
        r = R(n)
        g[n] = [mk("정답θ", n, r["θ정답"], r["천장"]["iou3d"], r["천장"]["J"])] +                [mk("후보%d" % x["씨앗"], n, x["θ"], x["iou3d"], x["J"]) for x in r["코드기하"]["재시작"]]
    c = best(R("L자"), "대조")
    g["L자"].append(mk("상자합", "상자합", c["θ"], c["iou3d"], c["J"]))
    r = R("두기둥대각")
    x2 = r["코드기하"]["재시작"][2]                                   # 도형 문에서 실제로 나온 거울상 (3D 0.000 · J 0.9986)
    assert abs(x2["θ"][4] + r["θ정답"][4]) < 0.01 and x2["iou3d"] == 0.0
    g["두기둥대각"] = [mk("정답θ", "두기둥대각", r["θ정답"], r["천장"]["iou3d"], r["천장"]["J"]),
                  mk("거울상", "두기둥대각", x2["θ"], x2["iou3d"], x2["J"])]
    for n in 도형:                                                   # 코드기하 최선1 대 자유도 대조(상자 합) 최선1
        if n in ("상자", "상자45도"):                                  # 두 팔이 같은 모양이다 (3D 1.0 대 1.0 · 0.5218 대 0.5218)
            continue
        a, b = best(R(n), "코드기하"), best(R(n), "대조")
        g[n + "·대조"] = [mk("코드기하", n, a["θ"], a["iou3d"], a["J"]), mk("상자합", "상자합", b["θ"], b["iou3d"], b["J"])]

    # ② 구조 바꿔치기
    M = CG.M
    rect = lambda W_: {"상자": CG._box(W_, W_, 1.0, 0, 0, 0), "원기둥": M.cylinder(1.0, W_ / 2, W_ / 2, 96),
                       "상자45": CG._box(W_ / np.sqrt(2), W_ / np.sqrt(2), 1.0, 0, 0, 0, 45.0)}
    sq = lambda h, lo, hi: M.cylinder(h, lo * np.sqrt(2), hi * np.sqrt(2), 4).rotate([0, 0, 45])     # 사각뿔(대) — 앞·옆 반폭 lo · hi
    rb, rt = R("치마")["θ정답"][:2]
    alts = {"상자": {k: v for k, v in rect(0.6).items() if k != "상자"},
            "원기둥": {k: v for k, v in rect(0.6).items() if k != "원기둥"},
            "상자45도": {k: v for k, v in rect(0.6 * np.sqrt(2)).items() if k != "상자45"},
            "원뿔": {"사각뿔(hull)": sq(1.0, 0.0, 0.35)},
            "구": {"두원기둥교차(hull)": (M.cylinder(1.0, 0.5, 0.5, 96, True).rotate([90, 0, 0]) ^
                                     M.cylinder(1.0, 0.5, 0.5, 96, True).rotate([0, 90, 0])).translate([0, 0, 0.5])},
            "치마": {"사각뿔대(hull)": sq(1.0, rb, rt)}}
    CG.H.register_sheets()
    for n, d in alts.items():
        case = "도형_" + n
        masks, bs = CG.G3.art_masks(case), CG.H.CASES[case]["back_sign"]
        tv = CG.vox(trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh"))
        r = R(n)
        g[n + "·바꿈"] = [mk("정답θ", n, r["θ정답"], r["천장"]["iou3d"], r["천장"]["J"])]
        for nm, man in d.items():
            m = CG.tm(man)
            g[n + "·바꿈"].append({"이름": nm, "3D": CG.viou(tv, CG.vox(m)), "J": round(CG.Jsil(m, masks, bs), 5), "θ": [], "mesh": m})
    return g


def prepare():
    import 코드기하도형 as CG
    A1 = _repo()[0]
    from PIL import Image
    os.makedirs(WORK, exist_ok=True)
    for case in CASES:
        Vw, F, col, mat = load_case(case)
        rgb, mask, N, fid = shot(Vw, F, col, mat)
        assert N[mask][:, 2].mean() > 0.3, "%s 보이는 면이 카메라를 등진다 (%.3f)" % (case, N[mask][:, 2].mean())
        gt = A1.cc(A1.plane_faces(Vw, F, 15.0)[np.clip(fid, 0, None)], mask, A1.AMIN)
        np.savez_compressed(os.path.join(WORK, case + ".npz"), rgb=rgb, mask=mask, N=N, gt=gt)
        for c in 조건:
            Image.fromarray(shade(rgb, mask, N, c == "셀")).save(os.path.join(WORK, "%s__%s.png" % (case, c)))
        print("  %-12s 전경 %.3f · 정답 조각 %d · 평면 조각 %d" % (NICK[case], mask.mean(), gt.max() + 1,
                                                        len(flat_regions(gt, N, mask))), flush=True)
    meta = {}
    for gname, cs in groups(CG).items():
        arr, meta[gname] = {}, []
        for i, c in enumerate(cs):
            m = c.pop("mesh")
            _, Mc, Nc, _ = shot(np.asarray(m.vertices, np.float64), np.asarray(m.faces))
            arr["M%d" % i], arr["N%d" % i] = Mc, Nc
            meta[gname].append(c)
        np.savez_compressed(os.path.join(WORK, "판별__%s.npz" % gname), **arr)
        print("  [%s] %s" % (gname, " · ".join("%s 3D %.3f J %.3f" % (c["이름"], c["3D"], c["J"]) for c in meta[gname])), flush=True)
    json.dump(meta, open(os.path.join(WORK, "판별.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  판별 후보 집합 %d" % len(meta))


def load(case):
    z = np.load(os.path.join(WORK, case + ".npz"))
    d = {k: z[k] for k in z.files}
    d["N"] = d["N"].astype(np.float64)
    d["flats"] = flat_regions(d["gt"], d["N"], d["mask"])
    return d


def load_group(g):
    z = np.load(os.path.join(WORK, "판별__%s.npz" % g))
    meta = json.load(open(os.path.join(WORK, "판별.json"), encoding="utf-8"))[g]
    return [(m, z["M%d" % i], z["N%d" % i].astype(np.float64)) for i, m in enumerate(meta)]


def group_case(g):
    return "도형_" + g.split("·")[0]


# ── 판별 ─────────────────────────────────────────────────────────────────────

def discriminate(preds):
    """preds: {팔이름: f(case) -> (P, Mp)}. -> {집합: {후보별 점수 · 쌍별 맞음}}. 쌍은 |Δ3D| ≥ DIOU 인 것만."""
    out = {}
    for g in json.load(open(os.path.join(WORK, "판별.json"), encoding="utf-8")):
        cs = load_group(g)
        case = group_case(g)
        sc = {arm: [round(cand_score(*f(case), Nc, Mc), 3) for _, Mc, Nc in cs] for arm, f in preds.items()}
        pairs = []
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                hi, lo = (i, j) if cs[i][0]["3D"] >= cs[j][0]["3D"] else (j, i)
                if cs[hi][0]["3D"] - cs[lo][0]["3D"] < DIOU:
                    continue
                pairs.append({"높은": cs[hi][0]["이름"], "낮은": cs[lo][0]["이름"],
                              "실루엣이못가름": bool(min(cs[hi][0]["J"], cs[lo][0]["J"]) >= JMIN),
                              **{arm: round(sc[arm][lo] - sc[arm][hi], 3) for arm in preds}})   # > 0 이면 옳게 고름
        out[g] = {"후보": [c[0] for c in cs], "점수": sc, "쌍": pairs,
                  "고른후보": {arm: cs[int(np.argmin(sc[arm]))][0]["이름"] for arm in preds},
                  "후회": {arm: round(max(c[0]["3D"] for c in cs) - cs[int(np.argmin(sc[arm]))][0]["3D"], 4) for arm in preds}}
    return out


def q3_pairs(D):
    """판정 쌍 = 실루엣이 못 가르고 (둘 다 J ≥ JMIN) · 천장(정답 법선)이 MARGIN 이상으로 옳게 가르는 쌍."""
    return [(g, p) for g, r in D.items() for p in r["쌍"] if p["실루엣이못가름"] and p["천장"] >= MARGIN]


def hit(p, arm):
    """쌍에서 「맞음」 = 3D IoU 높은 후보의 각오차가 **MARGIN(2°) 이상** 낮다. 여유가 그보다 작으면 못 가른 것으로 센다 —
    inflation 이 0.1° 차로 13/13 을 내는 것을 대조군만 돌린 단계에서 봤다 (Marigold 를 보기 전에 고쳤다)."""
    return p[arm] >= MARGIN


def base_preds():
    cache = {}

    def L(case):
        if case not in cache:
            cache[case] = load(case)
        return cache[case]
    return {"천장": lambda c: (L(c)["N"], L(c)["mask"]),
            "상수": lambda c: (constant(L(c)["mask"]).astype(np.float64), L(c)["mask"]),
            "inflation": lambda c: (inflation(L(c)["mask"]).astype(np.float64), L(c)["mask"])}, L


def ceiling():
    """Marigold 없이 되는 것 전부 — 계획서의 「천장 · 대조군」 절이 이 출력이다."""
    A1, A2 = _repo()[:2]
    from PIL import Image
    preds, L = base_preds()
    print("  %-10s %4s %4s | %-22s | %-22s | 천장분할(τ=%g) 매칭 F1 | 손알베도(매끈/셀) 매칭" % ("장", "조각", "평면", "상수 중앙 · 평면성", "inflation 중앙 · 평면성 · 매칭 · F1", TAU))
    out = {}
    for case in CASES:
        d = L(case)
        r = {"정답조각": int(d["gt"].max() + 1), "평면조각": len(d["flats"]),
             "상수": measure(constant(d["mask"]), d), "inflation": measure(inflation(d["mask"]), d), "천장": measure(d["N"], d)}
        for c in 조건:
            r["손알베도·" + c] = hand(case, d, c)
        out[case] = r
        print("  %-10s %4d %4d | %6.2f %6s | %6.2f %6s %.3f %.3f | %.3f %.3f | %.3f %.3f"
              % (NICK[case], r["정답조각"], r["평면조각"], r["상수"]["각오차"]["중앙"], r["상수"]["평면성"],
                 r["inflation"]["각오차"]["중앙"], r["inflation"]["평면성"], r["inflation"]["분할"]["매칭IoU"], r["inflation"]["분할"]["경계F1"],
                 r["천장"]["분할"]["매칭IoU"], r["천장"]["분할"]["경계F1"], r["손알베도·매끈"]["매칭IoU"], r["손알베도·셀"]["매칭IoU"]), flush=True)
    D = discriminate(preds)
    for g, r in D.items():
        print("\n  [%s] 후보 %s" % (g, " · ".join("%s(3D %.3f J %.3f)" % (c["이름"], c["3D"], c["J"]) for c in r["후보"])))
        for arm in preds:
            print("    %-10s 점수 %s -> %s (후회 %.3f)" % (arm, r["점수"][arm], r["고른후보"][arm], r["후회"][arm]))
    Q = q3_pairs(D)
    allp = [(g, p) for g, r in D.items() for p in r["쌍"] if p["실루엣이못가름"]]
    print("\n  실루엣이 못 가르는 쌍 %d · 그중 천장이 여유 %.0f° 이상으로 가르는 쌍(= Q3 분모) %d" % (len(allp), MARGIN, len(Q)))
    for arm in ("상수", "inflation"):
        print("    %-10s Q3 분모에서 맞음 %d/%d" % (arm, sum(hit(p, arm) for _, p in Q), len(Q)))
    for g in D:
        n = sum(1 for gg, _ in Q if gg == g)
        m = sum(1 for gg, _ in allp if gg == g)
        if m:
            print("    %-14s 못가르는쌍 %d · 분모 %d" % (g, m, n))
    p = os.path.join(WORK, "천장.json")
    json.dump({"장": out, "판별": D, "Q3분모": [[g, x["높은"], x["낮은"]] for g, x in Q]}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", p)


def hand(case, d, cond, seg_only=False):
    """09-19 손 알베도 방식 — 1차(알베도 영역 · **알베도 컷을 따로 준다** = 09-19 의 계약) 안을 관측 밝기로 쪼갠다."""
    A1, A2 = _repo()[:2]
    from PIL import Image
    obs = np.asarray(Image.open(os.path.join(WORK, "%s__%s.png" % (case, cond))).convert("RGB")).astype(np.float64) @ np.array([0.299, 0.587, 0.114])
    obs = np.clip(np.rint(obs), 0, 255).astype(np.uint8)
    reg = A1.albedo_regions(d["rgb"], d["mask"], 12, A1.AMIN)
    seg = A2.shade_split(obs, reg, d["mask"])
    return seg if seg_only else seg_marks(d["gt"], seg, d["mask"])


# ── 추론 (imggen venv · GPU 1) ────────────────────────────────────────────────

def infer(n):
    os.environ["CUDA_VISIBLE_DEVICES"] = "1"
    import psutil
    import torch
    from diffusers import MarigoldNormalsPipeline
    from PIL import Image
    todo = [(c, k) for c in (("도형_구",) + tuple(x for x in CASES if x != "도형_구")) for k in 조건
            if not os.path.exists(os.path.join(WORK, "%s__%s.npy" % (c, k)))][:n]
    if not todo:
        print("  다 했다")
        return
    t0 = time.time()
    pipe = MarigoldNormalsPipeline.from_pretrained(MODEL, variant="fp16", torch_dtype=torch.float16).to("cuda")
    pipe.set_progress_bar_config(disable=True)
    print("  올림 %.0f초 · 스텝 %s · 처리해상도 %s · %s" % (time.time() - t0, pipe.default_denoising_steps,
                                                  pipe.default_processing_resolution, torch.cuda.get_device_name(0)), flush=True)
    for case, k in todo:
        t1 = time.time()
        torch.cuda.reset_peak_memory_stats()
        img = Image.open(os.path.join(WORK, "%s__%s.png" % (case, k))).convert("RGB")
        out = pipe(img, ensemble_size=1, generator=torch.Generator("cuda").manual_seed(0))
        P = np.asarray(out.prediction)[0].astype(np.float32)
        assert P.shape == (img.size[1], img.size[0], 3), P.shape
        np.save(os.path.join(WORK, "%s__%s.npy" % (case, k)), P)
        r = {"종류": "추론", "판": TAG, "case": case, "조건": k, "초": round(time.time() - t1, 2),
             "VRAM최대MB": round(torch.cuda.max_memory_allocated() / 2 ** 20), "RSS_MB": round(psutil.Process().memory_info().rss / 2 ** 20),
             "스텝": int(pipe.default_denoising_steps), "처리해상도": int(pipe.default_processing_resolution)}
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  %-12s %s %.1f초 · VRAM %d MB · RSS %d MB" % (case, k, r["초"], r["VRAM최대MB"], r["RSS_MB"]), flush=True)


# ── 규약 (배관) ───────────────────────────────────────────────────────────────

def convention():
    """구 · 매끈 한 장에서 각오차 중앙이 최소인 축 부호 조합. 손잡이가 아니라 배관이다."""
    d = load("도형_구")
    raw = unit(np.load(os.path.join(WORK, "도형_구__매끈.npy")).astype(np.float64))
    res = []
    for sx in (1, -1):
        for sy in (1, -1):
            for sz in (1, -1):
                s = np.array([sx, sy, sz], float)
                res.append((float(np.median(angmap(raw * s, d["N"])[d["mask"]])), [sx, sy, sz]))
    res.sort()
    for e, s in res:
        print("  부호 %s 각오차 중앙 %.2f°" % (s, e))
    q0 = bool(res[0][0] <= 15.0 and res[1][0] - res[0][0] >= 20.0)
    # **계획의 Q0 (≤ 15° · 둘째와 ≥ 20° 차)는 짐** — 구 매끈 23.94° · 차 17.4°. 문턱이 「모델이 구에서 정확하다」를 깔고 있었다:
    # 규약은 안 흐리다 (여덟 조합이 x < y < z 뒤집기 순으로 단조 · z 를 뒤집은 넷은 전부 > 90° · diffusers 시각화 기본(뒤집기 없음)과 같다).
    # 흐린 건 모델의 구다 (납작하게 본다). 그래서 멈추지 않고, 부호가 값에 크게 걸리는 둘째 장(상자45도)에서 교차 확인한다 — 재기 단계에 값으로 적는다 (성능과 배관을 또 섞지 않게 assert 는 안 건다)
    assert res[0][0] < 45.0 and all(e > 90 for e, s_ in res if s_[2] == -1) and res[1][0] - res[0][0] > 10.0, "규약이 안 갈린다 — 멈춘다"
    json.dump({"부호": res[0][1], "구 매끈 중앙": round(res[0][0], 2), "둘째": round(res[1][0], 2), "계획의 Q0 통과": q0, "전부": res},
              open(os.path.join(WORK, "규약.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  규약 = raw × %s (X 오른쪽 · Y 위 · Z 보는 이 쪽 기준)" % res[0][1])


def pred(case, cond):
    s = np.array(json.load(open(os.path.join(WORK, "규약.json"), encoding="utf-8"))["부호"], float)
    return unit(np.load(os.path.join(WORK, "%s__%s.npy" % (case, cond))).astype(np.float64) * s)


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
    A1 = _repo()[0]
    done = rows()
    for case in CASES:
        if case in done or not all(os.path.exists(os.path.join(WORK, "%s__%s.npy" % (case, c))) for c in 조건):
            continue
        t0 = time.time()
        d = load(case)
        r = {"종류": "재기", "판": TAG, "case": case, "정답조각": int(d["gt"].max() + 1), "평면조각": len(d["flats"]),
             "천장": measure(d["N"], d), "상수": measure(constant(d["mask"]), d), "inflation": measure(inflation(d["mask"]), d)}
        for c in 조건:
            P = pred(case, c)
            if case == "도형_상자45도" and c == "매끈":               # 규약 교차 확인 — 왼 면은 X < 0 · 오른 면은 X > 0 이어야 한다
                left = d["N"][:, :, 0] < -0.5
                r["규약교차 상자45도 X평균 (왼면 · 오른면 — 정답 −0.707 · +0.707)"] = [round(float(P[left & d["mask"]][:, 0].mean()), 3),
                                                                                 round(float(P[~left & d["mask"]][:, 0].mean()), 3)]
            r["M·" + c] = measure(P, d)
            r["M·" + c]["분할τ"] = {str(t): seg_marks(d["gt"], link_regions(P, d["mask"], t, A1.AMIN), d["mask"])["매칭IoU"] for t in TAUS}
            r["손알베도·" + c] = hand(case, d, c)
        r["초"] = round(time.time() - t0, 1)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  %-10s 각오차 중앙  M매끈 %5.1f · M셀 %5.1f · infl %5.1f · 상수 %5.1f | 평면성 M셀 %s infl %s | 매칭 M셀 %.3f infl %.3f 손셀 %.3f"
              % (NICK[case], r["M·매끈"]["각오차"]["중앙"], r["M·셀"]["각오차"]["중앙"], r["inflation"]["각오차"]["중앙"], r["상수"]["각오차"]["중앙"],
                 r["M·셀"]["평면성"], r["inflation"]["평면성"], r["M·셀"]["분할"]["매칭IoU"], r["inflation"]["분할"]["매칭IoU"], r["손알베도·셀"]["매칭IoU"]), flush=True)


def st(a):
    a = np.asarray(a, float)
    return {"n": int(len(a)), "중앙": round(float(np.median(a)), 3), "평균": round(float(a.mean()), 3),
            "최악": round(float(a.min()), 3), "최선": round(float(a.max()), 3), "승": int((a > 0).sum())}


def verdict():
    rs = rows()
    assert len(rs) == len(CASES), "%d/%d 장만 쟀다" % (len(rs), len(CASES))
    preds, L = base_preds()
    preds["M·매끈"] = lambda c: (pred(c, "매끈"), L(c)["mask"])
    preds["M·셀"] = lambda c: (pred(c, "셀"), L(c)["mask"])
    D = discriminate(preds)
    Q = q3_pairs(D)
    dc = ["도형_" + n for n in 도형]
    v = {"판": TAG, "때": time.strftime("%Y%m%d_%H%M"), "규약": json.load(open(os.path.join(WORK, "규약.json"), encoding="utf-8"))}
    med = lambda arm, c: rs[c][arm]["각오차"]["중앙"]

    # Q1 셀 음영에서 inflation 보다 법선이 맞나 (도형 11) — 승 ≥ 8 그리고 차 중앙 ≥ +3°
    d1 = [med("inflation", c) - med("M·셀", c) for c in dc]
    v["Q1"] = {"문턱": "inflation − M·셀 각오차 중앙: 승 ≥ 8/11 그리고 차의 중앙 ≥ +3°", **st(d1),
               "구뺀10": st([x for x, c in zip(d1, dc) if c != "도형_구"]),
               "상수대비": st([med("상수", c) - med("M·셀", c) for c in dc]),
               "둘중나은정보0대비": st([min(med("상수", c), med("inflation", c)) - med("M·셀", c) for c in dc]),
               "실물4": st([med("inflation", c) - med("M·셀", c) for c in 실물])}
    v["Q1"]["통과"] = bool(v["Q1"]["승"] >= 8 and v["Q1"]["중앙"] >= 3.0)

    # Q2 평면 위에 기울기를 지어내나 — 평면 있는 장에서 inflation 보다 낮은 장 ≥ 75% 그리고 M·셀 평면성 중앙 ≤ 5°
    fc = [c for c in CASES if rs[c]["M·셀"]["평면성"] is not None]
    d2 = [rs[c]["inflation"]["평면성"] - rs[c]["M·셀"]["평면성"] for c in fc]
    m2 = [rs[c]["M·셀"]["평면성"] for c in fc]
    v["Q2"] = {"문턱": "평면 있는 장에서 (inflation − M·셀 평면성) > 0 인 장 ≥ 75% 그리고 M·셀 평면성 중앙 ≤ 5°", "장": [NICK[c] for c in fc],
               **st(d2), "M·셀 평면성": {"중앙": round(float(np.median(m2)), 3), "평균": round(float(np.mean(m2)), 3), "최악": round(float(np.max(m2)), 3)},
               "M·매끈 평면성 중앙": round(float(np.median([rs[c]["M·매끈"]["평면성"] for c in fc])), 3)}
    v["Q2"]["통과"] = bool(v["Q2"]["승"] >= 0.75 * len(fc) and v["Q2"]["M·셀 평면성"]["중앙"] <= 5.0)

    # Q3 구조 판별 — 분모 쌍의 ≥ 75% 그리고 정보 0 대조 둘 중 나은 쪽 + 20 %p
    rate = lambda arm: sum(hit(p, arm) for _, p in Q) / max(len(Q), 1)
    b0 = max(rate("상수"), rate("inflation"))
    v["Q3"] = {"문턱": "분모 쌍에서 M·셀 맞음 ≥ 75% 그리고 ≥ max(상수, inflation) + 20%p", "분모": len(Q),
               "맞음": {arm: "%d/%d" % (sum(hit(p, arm) for _, p in Q), len(Q)) for arm in preds},
               "집합별(M·셀)": {g: "%d/%d" % (sum(hit(p, "M·셀") for gg, p in Q if gg == g), sum(1 for gg, _ in Q if gg == g)) for g in D if any(gg == g for gg, _ in Q)},
               "분모밖(못 가른다고 미리 적은 쌍)에서 M·셀": "%d/%d" % (sum(hit(p, "M·셀") for g, r in D.items() for p in r["쌍"] if p["실루엣이못가름"] and p["천장"] < MARGIN),
                                                        sum(1 for g, r in D.items() for p in r["쌍"] if p["실루엣이못가름"] and p["천장"] < MARGIN)),
               "고른후보": {g: r["고른후보"] for g, r in D.items()}, "후회": {g: r["후회"] for g, r in D.items()},
               "통과": bool(len(Q) and rate("M·셀") >= 0.75 and rate("M·셀") >= b0 + 0.20)}

    # Q4 (서술) 매끈 -> 셀 열화
    v["Q4(서술) 셀 − 매끈"] = {"각오차 중앙 (15장)": st([med("M·셀", c) - med("M·매끈", c) for c in CASES]),
                          "평면성": st([rs[c]["M·셀"]["평면성"] - rs[c]["M·매끈"]["평면성"] for c in fc]),
                          "매칭IoU": st([rs[c]["M·셀"]["분할"]["매칭IoU"] - rs[c]["M·매끈"]["분할"]["매칭IoU"] for c in CASES]),
                          "Q3 분모 맞음": {"매끈": v["Q3"]["맞음"]["M·매끈"], "셀": v["Q3"]["맞음"]["M·셀"]}}

    # Q5 면 분할 — 정답 조각 ≥ 2 이고 천장(정답 법선 잇기) 매칭 ≥ 0.9 인 장에서. 관찰 (n 이 작다)
    sc = [c for c in CASES if rs[c]["정답조각"] >= 2 and c not in ("도형_두기둥나란히", "도형_두기둥대각")]   # 두 기둥은 배경이 갈라 줘서 모든 팔이 1.0 이다
    mi = lambda arm, c: rs[c][arm]["매칭IoU"] if arm.startswith("손") else rs[c][arm]["분할"]["매칭IoU"]
    v["Q5"] = {"문턱": "관찰(n=5) — M·셀 − inflation 매칭IoU ≥ +0.10 인 장 ≥ 4/5 그리고 M·셀 ≥ 손알베도·셀 인 장 ≥ 3/5", "장": [NICK[c] for c in sc],
               "M·셀 − inflation": st([mi("M·셀", c) - mi("inflation", c) for c in sc]),
               "+0.10 넘은 장": int(sum(mi("M·셀", c) - mi("inflation", c) >= 0.10 for c in sc)),
               "M·셀 − 손알베도·셀": st([mi("M·셀", c) - mi("손알베도·셀", c) for c in sc]),
               "M·매끈 − 손알베도·매끈": st([mi("M·매끈", c) - mi("손알베도·매끈", c) for c in sc]),
               "한 조각이 정답인 장에서 M·셀 조각 수": {NICK[c]: rs[c]["M·셀"]["분할"]["조각"] for c in CASES if rs[c]["정답조각"] == 1}}
    v["Q5"]["천장(정답 법선 잇기) 매칭IoU"] = {NICK[c]: rs[c]["천장"]["분할"]["매칭IoU"] for c in sc}
    v["Q5"]["통과"] = bool(v["Q5"]["+0.10 넘은 장"] >= 4 and v["Q5"]["M·셀 − 손알베도·셀"]["승"] + sum(mi("M·셀", c) == mi("손알베도·셀", c) for c in sc) >= 3)

    v["표"] = {NICK[c]: {"정답조각": rs[c]["정답조각"], "평면조각": rs[c]["평면조각"],
                        **{arm: {"중앙": rs[c][arm]["각오차"]["중앙"], "11.25": rs[c][arm]["각오차"]["11.25"], "22.5": rs[c][arm]["각오차"]["22.5"],
                                 "30": rs[c][arm]["각오차"]["30"], "평면성": rs[c][arm]["평면성"], "면간각": rs[c][arm]["면간각"],
                                 "매칭IoU": rs[c][arm]["분할"]["매칭IoU"], "조각": rs[c][arm]["분할"]["조각"], "경계F1": rs[c][arm]["분할"]["경계F1"]}
                           for arm in ("M·매끈", "M·셀", "inflation", "상수", "천장")},
                        "손알베도·매끈": rs[c]["손알베도·매끈"], "손알베도·셀": rs[c]["손알베도·셀"], "M·셀 분할τ": rs[c]["M·셀"]["분할τ"]} for c in CASES}
    v["판별"] = D
    ts = [json.loads(l) for l in open(PROG, encoding="utf-8") if '"추론"' in l]
    ts = [t for t in ts if t.get("판") == TAG]
    v["추론"] = {"장": len(ts), "초 중앙": round(float(np.median([t["초"] for t in ts])), 2), "초 최대": max(t["초"] for t in ts),
               "VRAM최대MB": max(t["VRAM최대MB"] for t in ts), "RSS최대MB": max(t["RSS_MB"] for t in ts), "스텝": ts[0]["스텝"], "처리해상도": ts[0]["처리해상도"]}
    p = os.path.join(HERE, "out", "기록", "마리골드법선_%s.json" % v["때"])
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %-10s %4s | %-27s | %-27s | %-13s | %-6s | 매칭IoU M매끈 M셀 infl 손매끈 손셀" % ("장", "조각", "각오차 중앙 M매끈 M셀 infl 상수", "<22.5° M매끈 M셀 infl", "평면성 M셀 infl", "면간각"))
    for c in CASES:
        t = v["표"][NICK[c]]
        print("  %-10s %4d | %6.1f %6.1f %6.1f %6.1f | %6.3f %6.3f %6.3f | %6s %6s | %6s | %.3f %.3f %.3f %.3f %.3f"
              % (NICK[c], t["정답조각"], t["M·매끈"]["중앙"], t["M·셀"]["중앙"], t["inflation"]["중앙"], t["상수"]["중앙"],
                 t["M·매끈"]["22.5"], t["M·셀"]["22.5"], t["inflation"]["22.5"], t["M·셀"]["평면성"], t["inflation"]["평면성"],
                 (t["M·셀"]["면간각"] or {}).get("평균"), t["M·매끈"]["매칭IoU"], t["M·셀"]["매칭IoU"], t["inflation"]["매칭IoU"],
                 t["손알베도·매끈"]["매칭IoU"], t["손알베도·셀"]["매칭IoU"]))
    for k in ("Q1", "Q2", "Q3", "Q4(서술) 셀 − 매끈", "Q5", "추론"):
        print("\n  %s %s" % (k, json.dumps(v[k], ensure_ascii=False)[:1500]))
    print("\n  ->", p)


# ── 그림 ─────────────────────────────────────────────────────────────────────

def ncolor(N, mask):
    return np.where(mask[:, :, None], np.clip((N + 1) * 127.5, 0, 255), 255).astype(np.uint8)


def label(t, s, size=32):
    from PIL import Image, ImageDraw
    _repo()
    from 계획 import _font
    im = Image.fromarray(t)
    dr = ImageDraw.Draw(im)
    for i, line in enumerate(s.split("\n")):
        dr.text((8, 6 + i * (size + 4)), line, fill=(0, 0, 0), font=_font(size), stroke_width=2, stroke_fill=(255, 255, 255))
    return np.asarray(im)


def figures():
    A1 = _repo()[0]
    from PIL import Image
    from 깊이색 import grid
    rs = rows()
    R = []
    for case in CASES:
        d = load(case)
        m = d["mask"]
        img = lambda c: np.asarray(Image.open(os.path.join(WORK, "%s__%s.png" % (case, c))).convert("RGB"))
        r = rs.get(case)
        e = lambda arm: ("%.1f° · 평면성 %s\n조각 %d · 매칭 %.3f" % (r[arm]["각오차"]["중앙"], r[arm]["평면성"], r[arm]["분할"]["조각"], r[arm]["분할"]["매칭IoU"])) if r else ""
        R.append((NICK[case], [img("매끈"), img("셀"), label(ncolor(d["N"], m), "정답 조각 %d" % (d["gt"].max() + 1)),
                               label(ncolor(pred(case, "매끈"), m), e("M·매끈")), label(ncolor(pred(case, "셀"), m), e("M·셀")),
                               label(ncolor(inflation(m), m), e("inflation")),
                               label(A1.tint(hand(case, d, "매끈", True), m), "매칭 %.3f" % r["손알베도·매끈"]["매칭IoU"] if r else ""),
                               label(A1.tint(hand(case, d, "셀", True), m), "매칭 %.3f" % r["손알베도·셀"]["매칭IoU"] if r else "")]))
    grid(R, ["입력 · 매끈 람베르트", "입력 · 셀 음영 3 단", "정답 법선", "Marigold (매끈)", "Marigold (셀)", "inflation 대조 (실루엣만)", "손 알베도 면 (매끈)", "손 알베도 면 (셀)"],
         "Marigold-normals — 한 컷에서 면을 맞히나 · front · 09-19 L_A 광원 (2026-09-20)",
         "법선색 = (n+1)/2 · X 오른쪽 · Y 위 · Z 보는 이. 글 = 각오차 중앙 · 평면성(정답 평면 안 예측 법선 각 RMS) · 법선 잇기(τ=15°) 조각 수 · 매칭IoU. 손 알베도는 알베도 컷을 따로 받는다 (09-19 계약)",
         os.path.join(HERE, "out", "마리골드법선_접촉지.png"), S=256)

    v = sorted(x for x in os.listdir(os.path.join(HERE, "out", "기록")) if x.startswith("마리골드법선_2") and x.endswith(".json"))
    D = json.load(open(os.path.join(HERE, "out", "기록", v[-1]), encoding="utf-8"))["판별"]
    R = []
    for g in ("상자45도", "상자45도·바꿈", "원기둥·바꿈", "상자·바꿈", "구·바꿈", "원뿔·바꿈", "L자", "두기둥대각"):
        case = group_case(g)
        d = load(case)
        m = d["mask"]
        cs = load_group(g)
        sc = D[g]["점수"]
        top = [np.asarray(Image.open(os.path.join(WORK, "%s__셀.png" % case)).convert("RGB")), label(ncolor(d["N"], m), "정답 법선"),
               label(ncolor(pred(case, "매끈"), m), "Marigold 매끈\n고름: %s" % D[g]["고른후보"]["M·매끈"]),
               label(ncolor(pred(case, "셀"), m), "Marigold 셀\n고름: %s" % D[g]["고른후보"]["M·셀"])]
        cand = [label(ncolor(Nc, Mc), "%s · 3D %.3f\n천장 %.1f° · infl %.1f°\nM매끈 %.1f° · M셀 %.1f°"
                      % (c["이름"], c["3D"], sc["천장"][i], sc["inflation"][i], sc["M·매끈"][i], sc["M·셀"][i]), 28)
                for i, (c, Mc, Nc) in enumerate(cs)]
        blank = np.full((512, 512, 3), 255, np.uint8)
        R.append((g, (top + cand + [blank] * 7)[:11]))
    grid(R, ["입력 (셀)", "정답 법선", "Marigold (매끈)", "Marigold (셀)"] + ["후보 법선 렌더 %d" % (i + 1) for i in range(7)],
         "구조 판별 — 실루엣이 못 가르는 후보를 법선이 가르나 (후보 법선 렌더 대 예측의 평균 각오차 · 작을수록 그 후보)",
         "글 = 후보 이름 · 3D IoU(도형 문 기록) · 천장(정답 법선) · inflation · Marigold 매끈 · 셀 과의 평균 각오차. 옳은 선택 = 3D IoU 가 높은 후보의 각오차가 낮다",
         os.path.join(HERE, "out", "마리골드법선_판별.png"), S=256)


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def selfcheck():
    import trimesh
    import 코드기하도형 as CG
    A1, _, _, W = _repo()
    # 1 구 — 해석 법선과 같다 · inflation 이 구에서 거의 정확하다 · 상수는 아니다
    s = trimesh.creation.icosphere(subdivisions=5, radius=0.5)
    s.apply_translation([0, 0, 0.5])
    _, m, N, _ = shot(np.asarray(s.vertices), np.asarray(s.faces))
    yy, xx = np.nonzero(m)
    cx, cy, r = xx.mean(), yy.mean(), (xx.max() - xx.min() + 1) / 2
    A = np.zeros(N.shape)
    A[m] = np.stack([(xx - cx) / r, -(yy - cy) / r, np.sqrt(np.clip(1 - ((xx - cx) ** 2 + (yy - cy) ** 2) / r ** 2, 0, 1))], 1)
    e = float(np.median(angmap(N, unit(A))[m]))
    ei = float(np.median(angmap(inflation(m).astype(float), N)[m]))
    ec = float(np.median(angmap(constant(m).astype(float), N)[m]))
    assert e < 2.0, "구 법선이 해석값과 다르다 (%.2f°) — 카메라 축이 틀렸다" % e
    assert ei < 6.0 and ec > 20.0, "대조군 거동 (inflation %.1f° · 상수 %.1f°)" % (ei, ec)
    # 2 상자45도 — 두 면이 반반 · 법선 X 가 ∓0.707 · 빛(좌상단)은 왼 면만 밝힌다
    b = CG.build(CG.b_45, CG.구조["상자45도"][2])
    rgb, m, N, fid = shot(np.asarray(b.vertices, np.float64), np.asarray(b.faces))
    left = N[:, :, 0] < -0.5
    assert abs((left & m).sum() / m.sum() - 0.5) < 0.02 and np.allclose(np.abs(N[m][:, 0]), np.sqrt(0.5), atol=1e-3), "상자45도 두 면"
    sh = shade(rgb, m, N.astype(float), False)[:, :, 0]
    assert sh[left & m].mean() > sh[~left & m].mean() + 50, "빛이 왼쪽에서 안 온다"
    assert len(np.unique(shade(rgb, m, N.astype(float), True)[m][:, 0])) <= 3
    # 3 자 — 정답 법선 잇기는 두 면을 되찾고 · 상수는 한 조각 · 평면성은 상수 0 · 잡음에서 오른다
    gt = A1.cc(A1.plane_faces(np.asarray(b.vertices, np.float64), np.asarray(b.faces), 15.0)[np.clip(fid, 0, None)], m, A1.AMIN)
    d = {"mask": m, "N": N.astype(float), "gt": gt, "flats": flat_regions(gt, N.astype(float), m)}
    assert len(d["flats"]) == 2
    a, c = measure(d["N"], d), measure(constant(m).astype(float), d)
    assert a["분할"]["매칭IoU"] > 0.99 and a["분할"]["경계F1"] == 1.0 and a["평면성"] < 0.01 and a["면간각"]["평균"] < 0.1, a
    assert c["분할"]["조각"] == 1 and c["분할"]["경계F1"] == 0.0 and abs(c["각오차"]["중앙"] - 45) < 0.5 and abs(c["면간각"]["평균"] - 90) < 0.5, c
    rng = np.random.default_rng(0)
    nz = measure(unit(d["N"] + rng.normal(0, 0.2, N.shape)), d)
    assert nz["평면성"] > 5 and nz["각오차"]["중앙"] > 5, nz
    # 4 판별 점수 — 제 자신이 0 · 마스크가 어긋나면 90° 벌
    assert cand_score(d["N"], m, d["N"], m) < 0.1
    assert cand_score(d["N"], m, d["N"], np.roll(m, 40, 1)) > 5
    print("  자가검사 통과 — 구 %.2f° · inflation@구 %.1f° · 상수@구 %.1f° · 상자45도 두 면 · 잡음 평면성 %.1f°" % (e, ei, ec, nz["평면성"]))


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
    {"검사": selfcheck, "준비": prepare, "천장": ceiling, "규약": convention, "재기": run, "판정": verdict, "그림": figures,
     "추론": lambda: infer(int(sys.argv[2]) if len(sys.argv) > 2 else 1)}[a]()
