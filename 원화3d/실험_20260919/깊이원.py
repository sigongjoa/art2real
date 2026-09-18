# -*- coding: utf-8 -*-
r"""**깊이원 — 학습 단안 깊이 모델을 타원 규칙 자리에 끼운다** (2026-09-19).

    python 깊이원.py 검사                   자가검사 (답을 아는 합성 판)
    python 깊이원.py 깊이 [케이스...]        모델 깊이 npy 를 만든다  ← **imggen venv 로 돈다**
    python 깊이원.py 입력 [n]                ⓪ 입력 표 — 모델 깊이 대 정답 깊이 (화소 단위)
    python 깊이원.py 민감도 [케이스...]       1½ 민감도 카드 — 손잡이 하나씩
    python 깊이원.py [n]                     아직 안 한 장 n 개 판정 -> out/기록/깊이원_진행.jsonl
    python 깊이원.py 판정                    -> out/기록/깊이원_판정_<때>.json
    python 깊이원.py 그림 [케이스]            모델 · 타원 · 정답 깊이를 한 장에 -> out/깊이원_깊이.png

기본 깊이맵은 **타원 단면**(`hull.ellipse_depths`) — 원화만 보고 세운 해석적 규칙이다. 학습 모델을
깊이원으로 쓴 적이 없다. 이 실험이 묻는 것: **단안 깊이 모델이 읽은 상대 깊이가 타원보다 나은 깊이원인가.**

**이건 생성형 3D 가 아니다.** 깎기는 언제나 hull(실루엣 교집합) **안쪽에서만** 일어난다 (`carve_depth`
는 기둥 [lo, hi] 안에서만 자른다). 모델은 hull 안에서 **어디를 깎을지만** 정하고 없는 것을 지어내지
못한다. 상한은 그대로 실루엣이다.

두 파이썬을 쓴다 — 모델은 GPU 가 있는 `D:\imggen\venv`, 채점은 저장소 파이썬. 그래서 `깊이` 단계는
저장소 모듈을 하나도 안 부른다 (cv2 · numpy · torch 뿐).
"""
import json
import os
import sys
import time

import cv2
import numpy as np

HERE = r"G:\art2real\원화3d"
EXP = os.path.join(HERE, "실험_20260919")
DEP = os.path.join(HERE, "out", "깊이원")
MODELS = {"DAv2-S": "depth-anything/Depth-Anything-V2-Small-hf",
          "DAv2-B": "depth-anything/Depth-Anything-V2-Base-hf"}
MODEL = "DAv2-B"                                  # 기본 깊이원 후보
VIEWS2 = ("front", "back")                        # side 는 규칙이 이진으로 두므로 깊이가 필요 없다

# 첫 게이트의 **얼린 집합** — 계획 `plan_깊이원_20260919.md` 에 돌리기 전에 적었다.
# 벤치 29장에서 물건 종류로 갈라 8장 (사람 3 · 머리/천 2 · 각진 것 2 · 정답판 1)
GATE1 = ("avatarsample_g", "base_male", "sendagaya_shino",
         "hairsample_female", "cloak_Cloche_Qz9XMYysBQ",
         "cloak_Chest_Closed_AngpV0HxD8", "mech_Drill_8uBbH7Dvmb", "소체")


# ---------------------------------------------------------------- 그림 준비 (저장소 모듈 없이)

def sheet_png(case, view):
    return os.path.join(HERE, "out", "시트", case, "%s.png" % view)


def art_rgb(png, bg=255, zoom=1.0, mirror=False, lineonly=False, blob=0.0, seed=0):
    """원화 RGBA -> 모델에 넣을 RGB. **손잡이는 여기 한 곳에만 있다** (민감도 카드).

    bg        배경 값 (255 흰 · 128 회 · 0 검)
    zoom      실루엣 bbox 를 그림의 몇 배로 채울까 (1.0 이면 원본 그대로)
    mirror    좌우 반전
    lineonly  채색을 지운다 — 실루엣 안은 배경색, 어두운 선만 남긴다 (선화 판)
    blob      **정보 0 대조군** — 매끈한 무작위 얼룩을 이 세기(0~1)로 얹는다
    """
    im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_UNCHANGED)
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    a = (im[:, :, 3:4].astype(np.float32) / 255.0) if im.shape[2] == 4 else np.ones(im.shape[:2] + (1,), np.float32)
    rgb = im[:, :, :3].astype(np.float32)
    if lineonly:
        lum = rgb.mean(2, keepdims=True)
        keep = np.clip((lum - 90) / 60.0, 0, 1)               # 어두운 선만 남기고 나머지는 흰색
        rgb = np.where(keep > 0.999, 255.0, rgb * (1 - keep) + 255.0 * keep)
    out = rgb * a + float(bg) * (1 - a)
    m = (a[:, :, 0] > 0.5)
    if mirror:
        out, m = out[:, ::-1], m[:, ::-1]
    if zoom != 1.0 and m.any():
        ys, xs = np.nonzero(m)
        cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
        h = out.shape[0] / zoom
        M = np.float32([[zoom, 0, out.shape[1] / 2 - zoom * cx], [0, zoom, out.shape[0] / 2 - zoom * cy]])
        out = cv2.warpAffine(out, M, (out.shape[1], out.shape[0]),
                             flags=cv2.INTER_LINEAR, borderValue=(bg, bg, bg))
    if blob > 0:
        rng = np.random.default_rng(seed)
        n = rng.normal(0, 1, out.shape[:2]).astype(np.float32)
        n = cv2.GaussianBlur(n, (0, 0), 24.0)
        n = n / max(float(np.abs(n).max()), 1e-6)
        out = out + blob * 255.0 * n[:, :, None]
    return np.ascontiguousarray(np.clip(out, 0, 255).astype(np.uint8)[:, :, ::-1])   # BGR -> RGB


# ---------------------------------------------------------------- 모델 (imggen venv)

_PIPE = {}


def predict(rgb, model=MODEL):
    """단안 깊이 모델 -> 원본 크기 **상대 역깊이** (큰 값 = 가까운 쪽. 모델 규약 그대로 둔다)."""
    import torch
    from transformers import AutoImageProcessor, AutoModelForDepthEstimation
    if model not in _PIPE:
        rid = MODELS[model]
        pr = AutoImageProcessor.from_pretrained(rid)
        md = AutoModelForDepthEstimation.from_pretrained(rid).to("cuda").eval()
        _PIPE[model] = (pr, md)
    pr, md = _PIPE[model]
    inp = pr(images=rgb, return_tensors="pt").to("cuda")
    with torch.no_grad():
        d = md(**inp).predicted_depth
    d = torch.nn.functional.interpolate(d[:, None], size=rgb.shape[:2], mode="bicubic",
                                        align_corners=False)[0, 0]
    return d.float().cpu().numpy()


def depth_path(case, view, model=MODEL, tag=""):
    return os.path.join(DEP, model, case, "%s%s.npy" % (view, ("_" + tag) if tag else ""))


def make_depths(cases, model=MODEL, tags=("",)):
    """케이스마다 front · back 모델 깊이를 낸다. 변형 tag 는 민감도 카드가 쓴다."""
    # **얼룩 세기는 손잡이와 맞춘다** — 화소 평균 |차| 로 확대(0.071)에 얼룩0.60(0.067) ·
    # 선화(0.008)에 얼룩약0.07(0.009) 을 맞췄다. 배경 손잡이는 0.43 · 0.87 이라 훨씬 센 교란이다
    KNOBS = {"": {}, "회배경": {"bg": 128}, "검배경": {"bg": 0}, "확대": {"zoom": 1.25},
             "반전": {"mirror": True}, "선화": {"lineonly": True},
             "얼룩": {"blob": 0.60}, "얼룩2": {"blob": 0.60, "seed": 1},
             "얼룩약": {"blob": 0.07}}
    for case in cases:
        for view in VIEWS2:
            png = sheet_png(case, view)
            if not os.path.exists(png):
                print("  %s/%s 원화가 없다 — 건너뜀" % (case, view)); continue
            for tag in tags:
                p = depth_path(case, view, model, tag)
                if os.path.exists(p):
                    continue
                os.makedirs(os.path.dirname(p), exist_ok=True)
                t0 = time.time()
                d = predict(art_rgb(png, **KNOBS[tag]), model)
                np.save(p, d.astype(np.float32))
                print("  %-28s %-6s %-6s %.1fs  범위 %.2f~%.2f" %
                      (case[:28], view, tag or "기본", time.time() - t0, d.min(), d.max()), flush=True)


def _unzoom(d, png, zoom):
    """`art_rgb(zoom=)` 의 역변환 — 확대해서 잰 깊이를 원래 원화 자리로 되돌린다.
    변환은 알파 마스크의 bbox 로만 정해지니 그대로 다시 구한다 (`art_rgb` 와 같은 식)."""
    im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_UNCHANGED)
    a = im[:, :, 3] if im.shape[2] == 4 else np.full(im.shape[:2], 255, np.uint8)
    ys, xs = np.nonzero(a > 127)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    M = np.float32([[zoom, 0, d.shape[1] / 2 - zoom * cx], [0, zoom, d.shape[0] / 2 - zoom * cy]])
    return cv2.warpAffine(d, M, (d.shape[1], d.shape[0]),
                          flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderValue=float(np.median(d)))


def load_model_depth(case, view, m, model=MODEL, tag="", flip_back=False):
    """모델 깊이를 **`hull.load_depth` 와 같은 규약**으로: 원화 화소 크기 · 0~1 · 1 이 제일 가까운 곳.

    모델은 상대 역깊이(큰 값 = 가까움)를 낸다. 우리 규약도 1 이 제일 튀어나온 곳이라 부호가 같다 —
    그래도 ⓪ 입력 절에서 부호를 **재서** 확인한다. 마스크 밖은 1 (= 안 깎는다) 로 둔다.
    `flip_back` 은 뒷면 깊이의 부호를 뒤집는 배관 시험용이다."""
    d = np.load(depth_path(case, view, model, tag)).astype(np.float32)
    # **변형은 되돌려서 같은 자리에서 비교한다.** 안 되돌리면 「모델이 달라진 양」과 「깊이맵이
    # 어긋난 양」이 섞여, 배관 오차가 민감도로 읽힌다
    if tag == "반전":
        d = d[:, ::-1]
    if tag == "확대":
        d = _unzoom(d, sheet_png(case, view), 1.25)
    if d.shape != m.shape:
        d = cv2.resize(d, (m.shape[1], m.shape[0]), interpolation=cv2.INTER_LINEAR)
    if flip_back and view == "back":
        d = -d
    v = d[m]
    if v.size == 0:
        return np.ones_like(d)
    lo, hi = float(v.min()), float(v.max())
    h = (d - lo) / max(hi - lo, 1e-6)
    return np.where(m, np.clip(h, 0, 1), 1.0).astype(np.float32)


# ---------------------------------------------------------------- 채점 (저장소 파이썬)

def _repo():
    sys.path.insert(0, HERE)
    for d in ("실험_20260915",):
        sys.path.insert(0, os.path.join(HERE, d))
    os.chdir(HERE)
    import hull as H, win as W, 오라클 as O, 정답 as J, 대조 as C            # noqa: E401
    return H, W, O, J, C


def post_model(case, model=MODEL, tag="", flip_back=False):
    """`오라클.build` 의 `post` 훅 — 원화 프레임에서 깊이맵을 모델 것으로 갈아끼운다."""
    return lambda v, d, dep: load_model_depth(case, v, d, model, tag, flip_back)


def read_at(dep, plain, axes, back_sign, W, view="front"):
    """`carve_depth` 가 **실제로 읽는 값**. 복셀 중심 화소 · 높이마다 max=1 (`오라클.map_corr` 규약)."""
    u, _, z = axes
    X2, Z2 = np.meshgrid(u, z, indexing="ij")
    py, px = W.topix((back_sign if view == "back" else W.VIEW_AXIS[view][1]) * X2, Z2)
    on = plain.any(1)
    h = dep[view][py, px]
    top = np.maximum(np.where(on, h, 0.0).max(0, keepdims=True), 1e-6)
    return (h / top)[on]


def input_row(case, model=MODEL, tag="", flip_back=False):
    """⓪ 입력 — 모델 깊이 대 **정답 깊이**를 화소 단위로. 마스크(hull 이 선 자리) 안에서만."""
    import trimesh
    H, W, O, J, C = _repo()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    bs = H.CASES[case]["back_sign"]
    out = {"case": case, "모델": model, "변형": tag or "기본"}
    _, _, axes, D_or = O.build(case, truth, 1.0, "오라클")
    plain, _, _, D_el = O.build(case, truth, 1.0, "타원")
    _, _, _, D_md = O.build(case, truth, 1.0, "모델", post=post_model(case, model, tag, flip_back))
    srcs = [("타원", D_el), ("모델", D_md)]
    if os.path.exists(depth_path(case, "front", model, "선화")):
        srcs.append(("모델선화", O.build(case, truth, 1.0, "모델", post=post_model(case, model, "선화"))[3]))
    srcs.append(("얼룩", O.build(case, truth, 1.0, "얼룩", post=post_blob(case))[3]))
    for view in VIEWS2:
        ref = read_at(D_or, plain, axes, bs, W, view)
        for n, D in srcs:
            a = read_at(D, plain, axes, bs, W, view)
            ok = a.std() > 1e-9 and ref.std() > 1e-9
            out["상관_%s_%s" % (n, view)] = round(float(np.corrcoef(a, ref)[0, 1]), 4) if ok else float("nan")
            out["오차_%s_%s" % (n, view)] = round(float(np.abs(a - ref).mean()), 4)
    return out


# ---------------------------------------------------------------- 판본 · 판정

VNAMES = ("기본(타원)", "모델", "모델선화", "모델정합", "모델⊕타원", "모델선화⊕타원",
          "얼룩", "뒤집힌뒤", "오라클")
LAM = 1.00                                        # 규칙은 안 바꾼다 — 기본값 `hull.DEPTH_LAM` 그대로
TAG = "깊이원 v3 · 양쪽 속채움정답 · 격자128·192 · 제 부피 균일 · 음성대조 둘 · 선화 입력 (2026-09-19)"
PROG = os.path.join(HERE, "out", "기록", "깊이원_진행.jsonl")


def versions(case, model=MODEL):
    """판본 여섯. **깊이원만 다르고 깎기 규칙(lam 1.00)은 전부 같다.**"""
    import trimesh
    H, W, O, J, C = _repo()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    plain, el, axes, D_el = O.build(case, truth, LAM, "타원")
    _, orc, _, _ = O.build(case, truth, LAM, "오라클")
    _, md, _, D_md = O.build(case, truth, LAM, "모델", post=post_model(case, model))
    bs = H.CASES[case]["back_sign"]
    masks = _masks_of(case, H, W)
    # 섞기 — 모델과 타원의 평균 깊이맵. 깊이원 둘의 가중합이지 새 규칙이 아니다
    D_mx = {v: (D_md[v] + D_el[v]) / 2 if v in VIEWS2 else D_el[v] for v in W.VIEWS}
    # 정합 — 모델 깊이를 **타원에 최소제곱 shift-scale 정합**. 단안 깊이는 affine 이 미정이고
    # `carve_depth` 의 높이별 정규화는 shift 에 안 불변이라, 모델이 진 게 모양 탓인지 단위 탓인지 가른다
    D_ft = {v: _fit_to(D_md[v], D_el[v], plain, axes, bs, W, v) if v in VIEWS2 else D_el[v]
            for v in W.VIEWS}
    mx, _ = H.carve_depth(masks, D_mx, lam=LAM, back_sign=bs)
    ft, _ = H.carve_depth(masks, D_ft, lam=LAM, back_sign=bs)
    # **음성 대조 둘** — 「틀린 깊이를 넣으면 점수가 내려간다」를 보이는 문이다.
    #   얼룩      정보 0 깊이원 (그림을 안 봤다). 이게 균일을 이기면 대조군 판정 Q2 는 판별력이 0 이다
    #   뒤집힌뒤   뒷면 깊이의 부호만 뒤집은 것 (같은 정보, 틀린 방향)
    _, bl, _, _ = O.build(case, truth, LAM, "얼룩", post=post_blob(case))
    _, fb, _, _ = O.build(case, truth, LAM, "뒤집힌뒤", post=post_model(case, model, flip_back=True))
    # **후보의 제 최선 작동점** — 민감도에서 정답 상관이 가장 높았던 입력(채색 제거 · 선만)
    out = {"이진": plain, "기본(타원)": el, "모델": md, "모델정합": ft, "모델⊕타원": mx,
           "얼룩": bl, "뒤집힌뒤": fb, "오라클": orc}
    if os.path.exists(depth_path(case, "front", model, "선화")):
        _, ln, _, D_ln = O.build(case, truth, LAM, "모델", post=post_model(case, model, "선화"))
        D_lx = {v: (D_ln[v] + D_el[v]) / 2 if v in VIEWS2 else D_el[v] for v in W.VIEWS}
        lx, _ = H.carve_depth(masks, D_lx, lam=LAM, back_sign=bs)
        out["모델선화"], out["모델선화⊕타원"] = ln, lx
    return out, axes, truth


BLOB_SIGMA = 60.0                                 # 정보 0 깊이장의 매끈함 (원화 1024² 화소)


def blob_depth(case, view, m, seed=0):
    """**정보 0 깊이원** — 그림을 안 보고 만든 매끈한 무작위 깊이장. 규약은 모델 깊이와 같다
    (마스크 안 0~1 · 밖은 1). `carve_depth` 가 높이마다 다시 정규화하므로 전역 배율은 안 중요하고,
    중요한 건 **공간 구조가 대상과 무관**하다는 것뿐이다.

    이게 필요한 까닭: 균일 침식 대조군은 깊이원이 아니라 **다른 기전**이다. 「모델이 균일@모델을
    이긴다」가 정보 덕인지 아니면 어떤 깊이든 이기는 자리인지 가르려면, 같은 깎기 규칙에 들어가는
    **정보 없는 깊이맵**이 있어야 한다."""
    rng = np.random.default_rng(hash((case, view, seed)) % (2 ** 32))
    n = cv2.GaussianBlur(rng.normal(0, 1, m.shape).astype(np.float32), (0, 0), BLOB_SIGMA)
    v = n[m]
    if v.size == 0:
        return np.ones_like(n)
    lo, hi = float(v.min()), float(v.max())
    return np.where(m, np.clip((n - lo) / max(hi - lo, 1e-6), 0, 1), 1.0).astype(np.float32)


def post_blob(case, seed=0):
    return lambda v, d, dep: blob_depth(case, v, d, seed)


def _fit_to(src, ref, plain, axes, bs, W, view):
    """`src` 를 `ref` 에 최소제곱 shift-scale 로 앉힌다 — **깎기가 읽는 화소에서만** 푼다."""
    u, _, z = axes
    X2, Z2 = np.meshgrid(u, z, indexing="ij")
    py, px = W.topix((bs if view == "back" else W.VIEW_AXIS[view][1]) * X2, Z2)
    on = plain.any(1)
    a, b = src[py, px][on], ref[py, px][on]
    if a.size < 8 or a.std() < 1e-9:
        return src
    s = float(np.cov(a, b)[0, 1] / max(a.var(), 1e-12))
    t = float(b.mean() - s * a.mean())
    out = src.copy()
    out[py, px] = np.clip(s * src[py, px] + t, 0, 1)
    return out


def _masks_of(case, H, W):
    src, base = H.CASES[case]["src"], H.art_dir(case)
    ms = {v: H.to_win(H.declutter(W.art_mask(os.path.join(base, f)))) for v, f in src.items()}
    return H._warp(ms, H.align(ms, back_sign=H.CASES[case]["back_sign"]))


def one(case, model=MODEL):
    """한 장 판정 — IoU 격자 둘 · 판본마다 제 부피 균일 대조군 · 깨짐 셋."""
    import trimesh
    H, W, O, J, C = _repo()
    import 표면 as SF
    from 겉면채점 import fill_slices
    t0 = time.time()
    V, axes, truth = versions(case, model)

    # **속 채운 정답 채점** (09-15 표준 · `실험_20260915/생성깎기.py` 와 같은 규약). 원형도 같은
    # 규칙으로 채운다 — 안 그러면 속 빈 껍질이 실제보다 낮게 나온다. 점수판 0.741 과 같은 자다
    grids = {"": J.grid(truth, J.PITCH), "·192": J.grid(truth, (W.U1 - W.U0) / 192.0)}
    def _iou(mesh, tag):
        p = J.PITCH if tag == "" else (W.U1 - W.U0) / 192.0
        T, ot = grids[tag]
        G, og = J.grid(mesh, p)
        A, B = J.common(fill_slices(T), ot, fill_slices(G), og)
        return float((A & B).sum() / max((A | B).sum(), 1))
    iou, iou2 = lambda m, _a=None: _iou(m, ""), lambda m, _a=None: _iou(m, "·192")
    M = {k: C.to_mesh(v, axes) for k, v in V.items()}
    r = {"case": case, "모델": model, "판": TAG}
    r.update({k: round(iou(m, axes), 4) for k, m in M.items()})
    r.update({k + "·192": round(iou2(m, axes), 4) for k, m in M.items()})
    cache = {}
    for k, m in M.items():
        if k == "이진":
            continue
        em, _ = H.even_control(V["이진"], axes, m.volume, cache=cache)
        r["균일@" + k], r["균일@%s·192" % k] = round(iou(em, axes), 4), round(iou2(em, axes), 4)
        r["찢김_" + k], r["조각_" + k] = round(SF.tear(V[k]), 4), int(SF.pieces(V[k]))
        # **부피와 실루엣 손실을 같이 적는다.** 부피가 없으면 「이득이 깊이인가 부피인가」를 나중에 못 가른다
        # (검토 지적). 실루엣 손실은 계획의 P3 — `hull.main` 의 98% assert 는 이 경로를 안 타므로 여기서 잰다
        r["부피_" + k] = round(float(m.volume), 6)
        r["실루엣_" + k] = round(float(SF.sil_loss(V[k], V["이진"])), 4)
    r["초"] = round(time.time() - t0, 1)
    return r


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[r["case"]] = r
    return out


def verdict(rs):
    """판정 — **돌리기 전에 정한 규칙**: 판본마다 제 부피 균일 대조군을 격자 128·192 **둘 다**에서
    평균 > 0 이고 과반 승이어야 「통과」. 천장몫 = (후보 − 기본) / (오라클 − 기본)."""
    g = lambda k: np.array([r[k] for r in rs], float)
    n = len(rs)
    VN = [k for k in VNAMES if all(k in r for r in rs)]
    base, orc = g("기본(타원)"), g("오라클")
    out = {"장수": n, "TAG": TAG, "케이스": [r["case"] for r in rs], "판본": {}}
    # **배관 P2 — 오라클이 장마다 기본보다 높은가.** 계획에 적어 놓고 코드에 없던 문이다 (검토 지적).
    # 깨진 장은 천장몫의 분모가 음수라 그 장에서 ρ 가 눈금이 아니다
    out["P2_오라클이_기본보다_낮은_장"] = [r["case"] for r in rs if r["오라클"] <= r["기본(타원)"]]
    # **실루엣 손실 P3** — 깊이 깎기가 hull 실루엣을 갉으면 안 된다 (`hull.py:629` 는 이 경로를 안 탄다)
    out["P3_실루엣손실_최대"] = {k: round(float(max(r["실루엣_" + k] for r in rs)), 4) for k in VN}
    for k in VN:
        a = [g(k) - g("균일@" + k), g(k + "·192") - g("균일@%s·192" % k)]
        ok = [float(v.mean()) > 0 and int((v > 0).sum()) > n / 2 for v in a]
        share = float(np.median(g(k) - base) / max(np.median(orc - base), 1e-9)) if k != "기본(타원)" else 0.0
        # **부피 몫과 정보 몫으로 가른다** (검토 지적 — hull 은 뚱뚱해서 아무렇게나 깎아도 IoU 가 오른다).
        #   IoU(k) − IoU(기본) = [균일@k − 균일@기본]  +  [정보(k) − 정보(기본)]
        #   정보(k) = IoU(k) − IoU(균일@k)  = 제 부피 균일 침식 위에 깊이가 더 번 몫
        info = lambda kk, t="": g(kk + t) - g("균일@" + kk + t)
        vol = g("균일@" + k) - g("균일@기본(타원)")
        out["판본"][k] = {
            "정보중앙": round(float(np.median(info(k))), 4),
            "정보중앙192": round(float(np.median(info(k, "·192"))), 4),
            "정보이긴장": int((info(k) > 0).sum()),
            "부피몫중앙": round(float(np.median(vol)), 4),
            "정보차중앙": round(float(np.median(info(k) - info("기본(타원)"))), 4),
            "정보차이긴장": int((info(k) > info("기본(타원)")).sum()),
            "실루엣손실최대": round(float(max(r["실루엣_" + k] for r in rs)), 4),
            "중앙128": round(float(np.median(g(k))), 4), "중앙192": round(float(np.median(g(k + "·192"))), 4),
            "대조128": [round(float(a[0].mean()), 4), int((a[0] > 0).sum())],
            "대조192": [round(float(a[1].mean()), 4), int((a[1] > 0).sum())],
            "기본대비중앙": round(float(np.median(g(k) - base)), 4),
            "중앙끼리차": round(float(np.median(g(k)) - np.median(base)), 4),
            "기본이긴장": int((g(k) > base).sum()),
            "천장몫": round(share, 3),
            "판정": "통과" if all(ok) else ("격자가 갈림" if any(ok) else "짐"),
            "찢김중앙": round(float(np.median(g("찢김_" + k))), 4),
            "조각중앙": float(np.median(g("조각_" + k)))}
    return out


# ---------------------------------------------------------------- 자가검사

def selfcheck():
    """**답을 아는 판**으로 배관을 검사한다. 이게 통과해야 아래 숫자가 뜻이 있다."""
    # ① art_rgb 손잡이 — 배경 · 반전 · 얼룩이 실제로 그것만 바꾸나
    png = sheet_png(GATE1[0], "front")
    a0 = art_rgb(png)
    assert a0[0, 0].min() == 255, "흰 배경인데 구석이 희지 않다"
    assert art_rgb(png, bg=128)[0, 0].max() == 128, "회 배경 손잡이가 안 먹는다"
    assert np.array_equal(art_rgb(png, mirror=True)[:, ::-1], a0), "좌우 반전이 가역이 아니다"
    b = art_rgb(png, blob=0.60)
    s0 = np.abs(b.astype(float) - a0).mean() / 255
    s1 = np.abs(art_rgb(png, zoom=1.25).astype(float) - a0).mean() / 255
    assert abs(s0 - s1) < 0.25 * s1, "얼룩 대조군 세기(%.4f)가 확대 손잡이(%.4f)와 안 맞는다" % (s0, s1)
    assert np.array_equal(art_rgb(png, blob=0.60), b), "얼룩이 씨앗으로 안 묶였다"
    assert not np.array_equal(art_rgb(png, blob=0.60, seed=1), b), "씨앗이 달라도 같은 얼룩이다"

    # ①-2 확대 되돌리기 — 램프를 확대했다 되돌리면 가운데가 제자리로 와야 한다
    ramp = np.tile(np.linspace(0, 1, 1024, dtype=np.float32), (1024, 1))
    im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_UNCHANGED)
    ys, xs = np.nonzero(im[:, :, 3] > 127)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    M = np.float32([[1.25, 0, 512 - 1.25 * cx], [0, 1.25, 512 - 1.25 * cy]])
    z = cv2.warpAffine(ramp, M, (1024, 1024), flags=cv2.INTER_LINEAR)
    c = np.s_[300:700, 300:700]
    assert np.abs(_unzoom(z, png, 1.25)[c] - ramp[c]).mean() < 0.01, "확대 되돌리기가 제자리로 안 온다"

    # ② read_at — 정답 깊이를 정답과 대면 상관 1.0 이어야 한다 (규약이 어긋나면 여기서 걸린다)
    import trimesh
    H, W, O, J, C = _repo()
    case = GATE1[0]
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    plain, _, axes, D = O.build(case, truth, LAM, "오라클")
    bs = H.CASES[case]["back_sign"]
    a = read_at(D, plain, axes, bs, W, "front")
    assert a.min() >= 0 and a.max() <= 1.0 + 1e-6, "읽은 깊이가 0~1 밖이다"

    # ②-3 **read_at 왕복** — 아는 값을 아는 자리에 찍고 그대로 읽히는지 본다. 좌표가 전치되거나
    # 한 칸 밀려도 상관은 높게 나오므로 「자기 자신과의 상관이 1」 같은 검사는 아무것도 안 막는다 (검토 지적)
    u, _, z = axes
    X2, Z2 = np.meshgrid(u, z, indexing="ij")
    py, px = W.topix(W.VIEW_AXIS["front"][1] * X2, Z2)
    want = ((X2 - u[0]) / (u[-1] - u[0]) * 0.8 + 0.2).astype(np.float32)
    Dr = {v: np.ones((W.RES, W.RES), np.float32) for v in W.VIEWS}
    Dr["front"][py, px] = want
    on = plain.any(1)
    top = np.maximum(np.where(on, want, 0.0).max(0, keepdims=True), 1e-6)
    assert np.abs(read_at(Dr, plain, axes, bs, W, "front") - (want / top)[on]).max() < 1e-5,         "read_at 왕복이 안 맞는다 — 좌표가 어긋났다"

    # ②-2 `_masks_of` 가 `오라클.build` 와 **같은 정렬**을 내나. 혼합 · 정합 판본이 이 마스크로 깎이므로
    # 여기서 갈라지면 두 판본만 다른 자리에서 재게 된다 (조용히)
    m2 = _masks_of(case, H, W)
    p2, _ = H.carve(m2, back_sign=bs)
    assert (p2 == plain).all(), "_masks_of 와 build 의 정렬이 다르다 — 혼합 · 정합 판본이 다른 hull 에서 깎인다"

    # ②-4 **post 훅이 실제로 먹나.** 훅이 조용히 무력화되면 「모델」이 타원과 같은 값이 되고
    # 아무도 안 잡는다 (검토 지적). 두 깊이맵이 읽는 자리에서 달라야 한다
    if os.path.exists(depth_path(case, "front")):
        _, _, _, Dm = O.build(case, truth, LAM, "모델", post=post_model(case))
        _, _, _, De = O.build(case, truth, LAM, "타원")
        am, ae = read_at(Dm, plain, axes, bs, W, "front"), read_at(De, plain, axes, bs, W, "front")
        assert np.abs(am - ae).mean() > 0.01, "모델 깊이가 타원과 같다 — post 훅이 안 먹었다"

    # ②-5 **정보 0 깊이원** 규약 — 모델 깊이와 같은 규약이라야 같은 자리에서 비교된다.
    # 그리고 씨앗이 다르면 달라야 한다 (같으면 대조군이 하나뿐인 셈이다)
    mm = np.zeros((1024, 1024), bool); mm[200:800, 200:800] = True
    b0, b1 = blob_depth(case, "front", mm, 0), blob_depth(case, "front", mm, 1)
    assert abs(b0[mm].min()) < 1e-6 and abs(b0[mm].max() - 1) < 1e-6 and (b0[~mm] == 1).all(),         "얼룩 깊이원이 모델 깊이와 같은 규약이 아니다"
    assert np.abs(b0 - b1).mean() > 0.05, "씨앗이 달라도 같은 얼룩 깊이장이다"
    assert np.array_equal(blob_depth(case, "front", mm, 0), b0), "얼룩 깊이장이 씨앗으로 안 묶였다"

    # ③ 모델 깊이 규약 — 0~1 · 마스크 밖은 1
    m = np.zeros((1024, 1024), bool); m[300:700, 300:700] = True
    p = depth_path(case, "front")
    if os.path.exists(p):
        h = load_model_depth(case, "front", m)
        assert abs(h[m].min()) < 1e-6 and abs(h[m].max() - 1) < 1e-6, "모델 깊이가 0~1 로 안 눕는다"
        assert (h[~m] == 1).all(), "마스크 밖이 1 이 아니다 — 모르는 자리를 깎게 된다"
    print("  자가검사 통과 — 손잡이 넷 · read_at 왕복 · 정렬 일치 · post 훅 · 얼룩 깊이원 · 모델 깊이 0~1")


# ---------------------------------------------------------------- 진입점

def main():
    os.makedirs(os.path.join(HERE, "out", "기록"), exist_ok=True)
    a = sys.argv[1:]
    if not a or a[0] in ("검사",):
        selfcheck(); return
    if a[0] == "깊이":
        rest = a[1:]
        tags = None
        if rest and rest[0].startswith("tag="):
            tags, rest = (rest[0][4:],), rest[1:]
        cs = rest or list(GATE1)
        if tags is None:
            tags = ("",) if len(cs) > 1 else ("", "회배경", "검배경", "확대", "반전", "선화", "얼룩", "얼룩2", "얼룩약")
        make_depths(cs, tags=tags); return
    if a[0] == "입력":
        cs = list(GATE1)[:int(a[1])] if len(a) > 1 else list(GATE1)
        out = []
        print("  %-26s %s" % ("케이스", "앞: 타원 모델 선화 얼룩 | 뒤: 타원 모델 선화 얼룩"))
        for c in cs:
            r = input_row(c)
            out.append(r)
            print("  %-26s %6.3f %6.3f %6.3f %6.3f | %6.3f %6.3f %6.3f %6.3f" % (
                c[:26], r["상관_타원_front"], r["상관_모델_front"],
                r.get("상관_모델선화_front", float("nan")), r["상관_얼룩_front"],
                r["상관_타원_back"], r["상관_모델_back"],
                r.get("상관_모델선화_back", float("nan")), r["상관_얼룩_back"]), flush=True)
        p = os.path.join(HERE, "out", "기록", "깊이원_입력_%s.json" % time.strftime("%Y%m%d_%H%M"))
        json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  기록 -> %s" % os.path.relpath(p, HERE)); return
    if a[0] == "모델검사":
        # **venv 로 돈다.** 논문이 인용하는 「결정성」 · 「Small 대 Base 상관」을 기록으로 남긴다 (검토 지적)
        c = a[1] if len(a) > 1 else GATE1[6]
        r0 = art_rgb(sheet_png(c, "front"))
        x1, x2 = predict(r0, "DAv2-B"), predict(r0, "DAv2-B")
        xs = predict(r0, "DAv2-S")
        out = {"case": c, "두번_돌린_최대차": float(np.abs(x1 - x2).max()),
               "S_대_B_상관": float(np.corrcoef(x1.ravel(), xs.ravel())[0, 1])}
        p = os.path.join(HERE, "out", "기록", "깊이원_모델검사.json")
        json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(" ", out, "->", os.path.relpath(p, HERE)); return
    if a[0] == "민감도":
        sens(a[1:] or [GATE1[0]]); return
    if a[0] == "판정":
        rs = list(rows().values())
        v = verdict(rs)
        p = os.path.join(HERE, "out", "기록", "깊이원_판정_%s.json" % time.strftime("%Y%m%d_%H%M"))
        json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(json.dumps(v["판본"], ensure_ascii=False, indent=1))
        print("  기록 -> %s" % os.path.relpath(p, HERE)); return
    if a[0] == "그림":
        figure(a[1:] or list(GATE1)[:4]); return
    # 숫자 -> 아직 안 한 장 n 개
    n = int(a[0])
    done = set(rows())
    todo = [c for c in GATE1 if c not in done][:n]
    for c in todo:
        r = one(c)
        with open(PROG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  %-24s 기본 %.4f · 모델 %.4f · 선화 %.4f · 얼룩 %.4f · 뒤집 %.4f · 천장 %.4f  (%.0fs)" % (
            c[:24], r["기본(타원)"], r["모델"], r.get("모델선화", float("nan")), r["얼룩"],
            r["뒤집힌뒤"], r["오라클"], r["초"]), flush=True)


def sens(cases):
    """**1½ 민감도 카드** — 손잡이 하나씩만 바꾼 반응. 대조군은 같은 세기의 무작위 얼룩이다."""
    import trimesh
    H, W, O, J, C = _repo()
    tags = ("", "회배경", "검배경", "확대", "반전", "선화", "얼룩", "얼룩2", "얼룩약")
    out = []
    for case in cases:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        bs = H.CASES[case]["back_sign"]
        plain, _, axes, D_or = O.build(case, truth, LAM, "오라클")
        base = None
        for tag in tags:
            if not os.path.exists(depth_path(case, "front", MODEL, tag)):
                continue
            _, _, _, D = O.build(case, truth, LAM, "모델", post=post_model(case, MODEL, tag))
            a = read_at(D, plain, axes, bs, W, "front")
            ref = read_at(D_or, plain, axes, bs, W, "front")
            if base is None:
                base = a
            r = {"case": case, "손잡이": tag or "기본",
                 "반응": round(float(np.abs(a - base).mean()), 4),
                 "상관_기본과": round(float(np.corrcoef(a, base)[0, 1]), 4),
                 "상관_정답과": round(float(np.corrcoef(a, ref)[0, 1]), 4)}
            out.append(r)
            print("  %-22s %-6s 반응 %.4f · 기본과 %.3f · 정답과 %+.3f" %
                  (case[:22], r["손잡이"], r["반응"], r["상관_기본과"], r["상관_정답과"]), flush=True)
    p = os.path.join(HERE, "out", "기록", "깊이원_민감도_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  기록 -> %s" % os.path.relpath(p, HERE))


def figure(cases):
    """**이 바퀴의 핵심 그림** — 같은 장에서 모델 깊이 · 타원 깊이 · 정답 깊이를 나란히."""
    import trimesh
    from PIL import Image, ImageDraw
    H, W, O, J, C = _repo()
    from 계획 import _font
    S, G, LW, TOP = 260, 16, 210, 106
    cols = ["원화", "모델(%s)" % MODEL, "타원(지금 기본)", "정답(오라클)"]
    im = Image.new("RGB", (LW + len(cols) * (S + G) + G, TOP + len(cases) * (S + 40) + 20), "white")
    d = ImageDraw.Draw(im)
    f1, f2, f3 = _font(26), _font(15), _font(13)
    d.text((22, 16), "깊이원 — 학습 모델 · 타원 규칙 · 정답을 같은 장에서", fill=(20, 20, 20), font=f1)
    d.text((22, 52), "앞면 깊이. 밝을수록 앞(가까움). 깎기가 실제로 읽는 값 — 높이마다 max=1 로 눕혔다. "
                     "hull 이 선 자리만 칠했다", fill=(90, 90, 90), font=f3)
    d.text((22, 72), "괄호는 정답 깊이와의 상관", fill=(90, 90, 90), font=f3)
    for j, c in enumerate(cols):
        d.text((LW + G + j * (S + G), TOP - 22), c, fill=(40, 40, 40), font=f2)
    for r, case in enumerate(cases):
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        bs = H.CASES[case]["back_sign"]
        plain, _, axes, D_or = O.build(case, truth, LAM, "오라클")
        _, _, _, D_el = O.build(case, truth, LAM, "타원")
        _, _, _, D_md = O.build(case, truth, LAM, "모델", post=post_model(case, MODEL))
        u, _, z = axes
        X2, Z2 = np.meshgrid(u, z, indexing="ij")
        py, px = W.topix(W.VIEW_AXIS["front"][1] * X2, Z2)
        on = plain.any(1)
        y0 = TOP + r * (S + 40)
        d.text((22, y0 + S // 2), case[:24], fill=(20, 20, 20), font=f2)
        art = cv2.imdecode(np.fromfile(sheet_png(case, "front"), np.uint8), cv2.IMREAD_UNCHANGED)
        a = art[:, :, 3:4].astype(np.float32) / 255 if art.shape[2] == 4 else 1.0
        tile0 = (art[:, :, :3].astype(np.float32) * a + 255 * (1 - a)).astype(np.uint8)[:, :, ::-1]
        im.paste(Image.fromarray(cv2.resize(tile0, (S, S))), (LW + G, y0))
        for j, D in enumerate((D_md, D_el, D_or), 1):
            h = D["front"][py, px]
            top = np.maximum(np.where(on, h, 0.0).max(0, keepdims=True), 1e-6)
            h = np.where(on, h / top, np.nan)
            g = np.uint8(np.clip(np.nan_to_num(h, nan=0.0), 0, 1) * 255)
            g = cv2.applyColorMap(g, cv2.COLORMAP_BONE)[:, :, ::-1]
            g[~on] = 245
            g = np.rot90(g)                                   # (x, z) -> 화면 (위가 머리)
            im.paste(Image.fromarray(cv2.resize(g, (S, S), interpolation=cv2.INTER_NEAREST)),
                     (LW + G + j * (S + G), y0))
        rr = read_at(D_or, plain, axes, bs, W, "front")
        for j, D in enumerate((D_md, D_el), 1):
            aa = read_at(D, plain, axes, bs, W, "front")
            c = float(np.corrcoef(aa, rr)[0, 1])
            d.text((LW + G + j * (S + G), y0 + S + 4), "상관 %+.3f" % c, font=f3,
                   fill=(30, 130, 70) if c > 0.3 else (190, 60, 40))
        print("  %s" % case, flush=True)
    p = os.path.join(HERE, "out", "깊이원_깊이.png")
    im.save(p)
    print("  -> %s" % os.path.relpath(p, HERE))


if __name__ == "__main__":
    main()
