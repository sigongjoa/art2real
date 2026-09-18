# -*- coding: utf-8 -*-
"""**층 분해 오라클 게이트** — 원화를 인체 · 천 · 머리로 갈라 층마다 hull 을 세우면 오르나 (2026-09-18).

    python 층분해.py 검사       자가검사 (합성 두 층) + 배관
    python 층분해.py [n]        아직 안 한 장 n 개 -> out/기록/층분해_진행.jsonl
    python 층분해.py 판정       -> out/기록/층분해_<때>.json
    python 층분해.py 그림       -> out/층분해.png

판정은 `claudedocs/plan_층분해_20260918.md` 「Q」 절 그대로다 — 돌리기 전에 적었다.
얼린 집합은 VRoid 11장. **28장이 아니라 기본값을 바꾸는 근거가 아니다.**

층 마스크는 정답 재질에서 뽑는다 (오라클). 두 갈래다.

    보임   화가 알고리즘이 실제로 보여준 화소만       — 분리기가 가린 곳을 못 메우는 경우
    온전   그 층만 따로 그린 실루엣 (가림 없음)        — See-through 처럼 메워주는 경우
"""
import json
import os
import sys
import time

import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
for d in ("실험_20260913", "실험_20260915"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import hull as H
import win as W
import 대조 as C
import 시트 as S
import 정답 as J
from 겉면채점 import fill_slices
from 머리가림 import load as load_model
from 재질 import CASES, cls_of_name

PROG = os.path.join(HERE, "out", "기록", "층분해_진행.jsonl")
TAG = "층분해 v4 · VRoid11 · 오라클 층마스크(보임 · 온전) · 속채운 정답 · 격자128·192 (2026-09-18)"
P192 = (W.U1 - W.U0) / 192.0
LAYERS = ("인체", "천", "머리")                      # 재질.cls_of_name: 0 천 · 1 피부 · 2 머리카락 · 3 얼굴/눈
CLS2LAYER = {0: 1, 1: 0, 2: 2, 3: 0}
VARS = ("이진", "기본", "층hull", "층기본", "층hull보임", "층기본보임", "무작위층기본",
        "균일@기본", "균일@층hull", "균일@층기본", "균일기본@층기본")
SEEDS = (0, 1, 2)
PAIRS = {"Q1": ("층기본", "기본"), "Q2": ("층기본", "균일@층기본"), "Q3": ("층hull", "이진")}


# ── 층 마스크 ────────────────────────────────────────────────────────────────

def layer_masks(case):
    """판 세 장마다 (전체 실루엣, 층별 보임, 층별 온전, 씨앗별 무작위 세 토막). `시트.py` 의 그리기를 그대로 다시 돌린다."""
    Vw, F, col, mat, fcls = load_model(case)
    lay = np.array([CLS2LAYER[int(c)] for c in fcls], np.int8)
    grp = {s: random_groups(Vw, F, lay, s) for s in SEEDS}
    out = {}
    for v in W.VIEWS:
        ident = S.draw(Vw, F, col, mat, v, line=False)[1]
        sil = ident >= 0
        idx = np.clip(ident, 0, None)
        vis = {L: sil & (lay[idx] == i) for i, L in enumerate(LAYERS)}
        onl = {}
        for i, L in enumerate(LAYERS):
            sel = lay == i
            onl[L] = (S.draw(Vw, F[sel], col[sel], mat[sel], v, line=False)[1] >= 0) if sel.any() \
                else np.zeros_like(sil)
        rnd = {}
        for sd in SEEDS:
            for i in range(len(LAYERS)):
                sel = grp[sd] == i
                rnd[(sd, i)] = (S.draw(Vw, F[sel], col[sel], mat[sel], v, line=False)[1] >= 0) if sel.any()                     else np.zeros_like(sil)
        out[v] = (sil, vis, onl, rnd)
    return out


def random_groups(Vw, F, lay, seed):
    """**자유도 대조군** — 의미 없이 셋으로 가른다. 무작위 방향 축을 따라 세 토막으로 자르되
    토막의 면적 비율을 실제 층 비율과 맞춘다. 층 분해의 이득이 「의미」에서 오는지 「셋으로 나누기」에서
    오는지 가른다. (계획에 없던 사후 대조군 — 코드를 쓰며 더했다)"""
    rng = np.random.default_rng(seed)
    n = rng.normal(size=3)
    n /= np.linalg.norm(n)
    cen = Vw[F].mean(1) @ n
    area = np.abs(np.cross(Vw[F][:, 1] - Vw[F][:, 0], Vw[F][:, 2] - Vw[F][:, 0])).sum(1)
    share = np.array([area[lay == i].sum() for i in range(len(LAYERS))], float)
    share /= share.sum()
    o = np.argsort(cen)
    cum = np.cumsum(area[o]) / area.sum()
    out = np.zeros(len(F), np.int8)
    b1, b2 = share[0], share[0] + share[1]
    out[o[cum > b1]] = 1
    out[o[cum > b2]] = 2
    return out


def build(case):
    """한 덩이 · 층별 판본의 복셀. `대조.build` 와 같은 길을 걷되 층 마스크를 같은 변환으로 함께 옮긴다."""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    bs = H.CASES[case]["back_sign"]
    lm = layer_masks(case)
    masks, vis_m, onl_m, rnd_m, agree = {}, {}, {}, {}, {}
    keys = [(sd, i) for sd in SEEDS for i in range(len(LAYERS))]
    for v, f in src.items():
        art = W.art_mask(os.path.join(base, f))
        sil, vis, onl, rnd = lm[v]
        agree[v] = round(float((art == sil).mean()), 4)          # 배관: 다시 그린 실루엣 == 판 png
        keep = art.sum(0) >= 8                                   # declutter 와 같은 열 규칙
        d = art & keep[None, :]
        ex = ([vis[L] & d for L in LAYERS] + [onl[L] & keep[None, :] for L in LAYERS]
              + [rnd[k] & keep[None, :] for k in keys])
        got = H.to_win(d, *ex)
        masks[v] = got[0]
        nL = len(LAYERS)
        vis_m[v] = {L: got[1 + i] > 0.5 for i, L in enumerate(LAYERS)}
        onl_m[v] = {L: got[1 + nL + i] > 0.5 for i, L in enumerate(LAYERS)}
        rnd_m[v] = {k: got[1 + 2 * nL + j] > 0.5 for j, k in enumerate(keys)}
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    warp = lambda dd: {v: {L: H._warp_one(dd[v][L].astype(np.float32), v, p) > 0.5 for L in LAYERS} for v in dd}
    vis_m, onl_m = warp(vis_m), warp(onl_m)
    rnd_m = {v: {k: H._warp_one(rnd_m[v][k].astype(np.float32), v, p) > 0.5 for k in keys} for v in rnd_m}

    plain, axes = H.carve(masks, back_sign=bs)
    deep, _ = H.carve_default(masks, None, back_sign=bs)

    def union(mm, default, names=LAYERS):
        out = np.zeros_like(plain)
        for L in names:
            one = {v: mm[v][L] for v in W.VIEWS}
            if not all(one[v].any() for v in W.VIEWS):
                continue                                         # 한 판에서라도 안 보이면 그 층 hull 은 빈다
            g = H.carve_default(one, None, back_sign=bs)[0] if default else H.carve(one, back_sign=bs)[0]
            out |= g
        return out

    vox = {"이진": plain, "기본": deep,
           "층hull": union(onl_m, False), "층기본": union(onl_m, True),
           "층hull보임": union(vis_m, False), "층기본보임": union(vis_m, True)}
    for sd in SEEDS:
        vox["무작위층기본#%d" % sd] = union(rnd_m, True, [(sd, i) for i in range(len(LAYERS))])
    return vox, axes, agree


# ── 채점 ─────────────────────────────────────────────────────────────────────

def common_int(a, oa, b, ob):
    """`정답.common` 과 같은 일인데 **dtype 을 지킨다.** 그쪽은 bool 격자를 전제라 라벨을 1 로 뭉갠다
    (v1 측정이 이걸로 죽었다 — 층이 전부 「인체」로 나왔다)."""
    lo = np.minimum(oa, ob)
    hi = np.maximum(oa + a.shape, ob + b.shape)
    A = np.zeros(hi - lo, a.dtype)
    B = np.zeros(hi - lo, bool)
    sa = tuple(slice(oa[i] - lo[i], oa[i] - lo[i] + a.shape[i]) for i in range(3))
    sb = tuple(slice(ob[i] - lo[i], ob[i] - lo[i] + b.shape[i]) for i in range(3))
    A[sa] = a
    B[sb] = b
    return A, B


def shell(mesh, pitch):
    """메시 -> (껍질 복셀, 원점 인덱스). `정답.grid` 에서 홍수채움을 뺀 것."""
    v = mesh.voxelized(pitch=pitch)
    return np.asarray(v.matrix, bool), np.rint(np.asarray(v.transform)[:3, 3] / pitch).astype(int)


def truth_layers(case, pitch):
    """정답 복셀 (속채움) 과 층 라벨. 껍질 층에서 가장 가까운 층으로 속까지 번진다."""
    from scipy import ndimage
    t = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    Vw, F, col, mat, fcls = load_model(case)
    lay = np.array([CLS2LAYER[int(c)] for c in fcls], np.int8)
    T, ot = J.grid(t, pitch)
    lab = np.zeros(T.shape, np.int8)                             # 1..3, 0 = 라벨 없음
    for i, L in enumerate(LAYERS):
        sel = lay == i
        if not sel.any():
            continue
        sub = trimesh.Trimesh(t.vertices, t.faces[sel], process=False)
        A, oa = shell(sub, pitch)                                # **껍질만.** `정답.grid` 는 속을 채워 돌려주므로
                                                                 # 인체 부품이 치마 밑까지 꽉 찬 몸이 되고, 치마 속이 인체로 번진다
        sl = tuple(slice(max(oa[k] - ot[k], 0), max(oa[k] - ot[k], 0) + A.shape[k]) for k in range(3))
        cut = tuple(slice(0, min(A.shape[k], T.shape[k] - sl[k].start)) for k in range(3))
        lab[sl][A[cut]] = i + 1
    Fl = fill_slices(T)
    _, ind = ndimage.distance_transform_edt(lab == 0, return_indices=True)
    return Fl, lab[tuple(ind)], ot, t


def score_all(case, vox, axes):
    """판본마다 격자 둘의 IoU · 128 격자의 층별 재현율 · 넘침. 무작위 씨앗 셋은 중앙값으로 접는다."""
    meshes = {k: C.to_mesh(v, axes) for k, v in vox.items()}
    cache, cache_d = {}, {}
    for tgt, name in (("기본", "균일@기본"), ("층hull", "균일@층hull"), ("층기본", "균일@층기본")):
        meshes[name] = H.even_control(vox["이진"], axes, abs(meshes[tgt].volume), cache=cache)[0]
    # **기본을 층기본 부피까지 민 것.** 「기본에서 아무 데나 그만큼 깎아도 +0.012 가 나오나」를 가른다 (검토 지적)
    meshes["균일기본@층기본"] = H.even_control(vox["기본"], axes, abs(meshes["층기본"].volume), cache=cache_d)[0]

    out = {"iou": {}, "부피": {}, "재현율": {}, "넘침": {}}
    for pitch, tag in ((J.PITCH, ""), (P192, "·192")):
        Fl, lab, ot, _ = truth_layers(case, pitch) if pitch == J.PITCH else (None, None, None, None)
        if pitch != J.PITCH:
            t = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
            T, ot = J.grid(t, pitch)
            Fl = fill_slices(T)
        for k, m in meshes.items():
            G, og = J.grid(m, pitch)
            A, B = J.common(Fl, ot, G, og)
            out["iou"].setdefault(k, {})[tag or "128"] = round(float((A & B).sum() / max((A | B).sum(), 1)), 5)
            if pitch == J.PITCH:
                Lb, _ = common_int(lab, ot, G, og)                 # 라벨을 같은 틀로 (bool 로 뭉개지 않는다)
                out["부피"][k] = int(B.sum())
                for i, L in enumerate(LAYERS):
                    tl = (Lb == i + 1) & A
                    n = max(int(tl.sum()), 1)
                    out["재현율"].setdefault(k, {})[L] = round(float((tl & B).sum() / n), 4)
                    out["넘침"].setdefault(k, {})[L] = round(float(((Lb == i + 1) & ~A & B).sum() / n), 4)
                out.setdefault("넘침밖몫", {})[k] = round(float(1 - ((Lb > 0) & ~A & B).sum() / max(int((~A & B).sum()), 1)), 4)
    for m in ("iou", "재현율", "넘침"):
        seeds = ["무작위층기본#%d" % s for s in SEEDS]
        sub = {k: out[m].pop(k) for k in seeds}
        out[m]["무작위층기본"] = {g: round(float(np.median([sub[k][g] for k in seeds])), 5)
                              for g in sub[seeds[0]]}
    for k in ["무작위층기본#%d" % s for s in SEEDS]:
        out["부피"].pop(k, None)
    return out


# ── 진행 · 판정 ───────────────────────────────────────────────────────────────

def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[r["case"]] = r
    return out


def one(case):
    t0 = time.time()
    vox, axes, agree = build(case)
    r = score_all(case, vox, axes)
    r.update({"case": case, "판": TAG, "일치": agree, "초": round(time.time() - t0, 1),
              "기본값": "%s lam%.2f" % (H.DEPTH, H.DEPTH_LAM)})
    return r


def run(n):
    done = rows()
    todo = [c for c in CASES if c not in done][:n]
    for c in todo:
        r = one(c)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  %-24s 층기본 %.3f · 기본 %.3f · 균일@층기본 %.3f · 일치 %.3f · %.0f초"
              % (c, r["iou"]["층기본"]["128"], r["iou"]["기본"]["128"],
                 r["iou"]["균일@층기본"]["128"], min(r["일치"].values()), r["초"]))


def adopt(diffs):
    """채택 규칙 — 격자 둘 다에서 중앙 > 0 · 과반 승 · 한 장씩 빼도 중앙 > 0."""
    out = {}
    for g, d in diffs.items():
        d = np.asarray(d, float)
        loo = [float(np.median(np.delete(d, i))) for i in range(len(d))]
        out[g] = {"중앙": round(float(np.median(d)), 5), "승": int((d > 0).sum()), "n": len(d),
                  "한장빼기최소": round(min(loo), 5),
                  "통과": bool(np.median(d) > 0 and (d > 0).sum() > len(d) / 2 and min(loo) > 0)}
    return out


def verdict():
    rs = [rows()[c] for c in CASES if c in rows()]
    assert len(rs) == len(CASES), "%d/%d 장만 돌았다" % (len(rs), len(CASES))
    v = {"판": TAG, "n": len(rs), "케이스": [r["case"] for r in rs], "Q": {}}
    for q, (a, b) in PAIRS.items():
        diffs = {g: [r["iou"][a][g] - r["iou"][b][g] for r in rs] for g in ("128", "·192")}
        res = adopt(diffs)
        v["Q"][q] = {"뺄셈": "%s − %s" % (a, b), **res,
                     "통과": bool(res["128"]["통과"] and res["·192"]["통과"])}
    v["중앙"] = {k: {g: round(float(np.median([r["iou"][k][g] for r in rs])), 5) for g in ("128", "·192")}
                 for k in VARS}
    v["층별"] = {k: {m: {L: round(float(np.median([r[m][k][L] for r in rs])), 4) for L in LAYERS}
                     for m in ("재현율", "넘침")} for k in VARS}
    post = {"층기본−균일기본@층기본": ("층기본", "균일기본@층기본"),
            "층기본−무작위층기본": ("층기본", "무작위층기본"),
            "층hull−균일@층hull": ("층hull", "균일@층hull"),
            "기본−균일@기본": ("기본", "균일@기본"),
            "층hull보임−이진": ("층hull보임", "이진"),
            "층기본보임−기본": ("층기본보임", "기본")}
    v["사후"] = {n: adopt({g: [r["iou"][a][g] - r["iou"][b][g] for r in rs] for g in ("128", "·192")})
                for n, (a, b) in post.items()}
    v["일치최소"] = round(min(min(r["일치"].values()) for r in rs), 4)
    v["다음"] = ("Q1·Q2 통과 -> 층 분리기(See-through)를 3판에 걸 값어치가 있다" if v["Q"]["Q1"]["통과"] and v["Q"]["Q2"]["통과"]
                 else "Q1 통과·Q2 짐 -> 이득은 부피 몫이다" if v["Q"]["Q1"]["통과"]
                 else "Q1 짐·Q3 통과 -> 층 이득을 깊이 깎기가 먹는다" if v["Q"]["Q3"]["통과"]
                 else "다 짐 -> 완벽한 층 마스크로도 안 오른다. 멈춤")
    p = os.path.join(HERE, "out", "기록", "층분해_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(v["Q"], ensure_ascii=False, indent=1))
    print("  중앙", json.dumps(v["중앙"], ensure_ascii=False))
    print("  ->", p)
    return v


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def _bar(u0, u1, z0=0.1, z1=0.9):
    m = np.zeros((W.RES, W.RES), bool)
    (py0, px0), (py1, px1) = W.topix(u0, z1), W.topix(u1, z0)
    m[int(py0):int(py1) + 1, int(px0):int(px1) + 1] = True
    return m


def selfcheck():
    """**층을 가르면 유령 기둥이 안 생긴다.** 층 A 는 (x,y)=(−,−), 층 B 는 (+,+) 에 선 막대다.
    한 덩이 hull 은 (−,+)·(+,−) 유령까지 네 기둥, 층별 hull 은 두 기둥이어야 한다."""
    A = {"front": _bar(-0.25, -0.15), "side": _bar(-0.25, -0.15), "back": _bar(-0.25, -0.15)}
    B = {"front": _bar(0.15, 0.25), "side": _bar(0.15, 0.25), "back": _bar(0.15, 0.25)}
    both = {v: A[v] | B[v] for v in W.VIEWS}
    one_v, axes = H.carve(both, back_sign=+1)
    lay = H.carve(A, back_sign=+1)[0] | H.carve(B, back_sign=+1)[0]
    assert lay.sum() * 1.9 < one_v.sum(), "층별 hull 이 유령을 안 지웠다 (%d 대 %d)" % (lay.sum(), one_v.sum())
    assert not (lay & ~one_v).any(), "층별 hull 이 한 덩이 hull 밖으로 나갔다"
    from scipy import ndimage
    assert ndimage.label(lay)[1] == 2 and ndimage.label(one_v)[1] == 4, "기둥 수가 2 · 4 가 아니다"
    print("  자가검사 통과 — 층별 hull 이 유령 기둥 둘을 지운다 (%d -> %d 칸)" % (one_v.sum(), lay.sum()))


def plumb(case=CASES[0]):
    vox, axes, agree = build(case)
    assert min(agree.values()) > 0.98, "%s: 다시 그린 실루엣이 판과 다르다 %s" % (case, agree)
    for k in ("층hull", "층hull보임"):
        assert not (vox[k] & ~vox["이진"]).any(), "%s 가 이진 hull 밖으로 나갔다" % k
    assert not (vox["층기본"] & ~vox["이진"]).any(), "층기본이 이진 hull 밖으로 나갔다"
    # 계획의 「층기본 ⊆ 기본」은 틀린 전제였다 — 층마다 깊이맵이 달라 밖으로 나갈 수 있다. 몫으로 적는다
    밖 = (vox["층기본"] & ~vox["기본"]).sum() / max(int(vox["층기본"].sum()), 1)
    assert vox["층hull보임"].sum() <= vox["층hull"].sum(), "보임이 온전보다 크다"
    Fl, lab, ot, _ = truth_layers(case, J.PITCH)
    assert (lab[Fl] > 0).all(), "정답 속채움에 라벨 없는 칸이 있다"
    assert 0 < min(((lab == i + 1) & Fl).sum() / Fl.sum() for i in range(len(LAYERS))), "부피가 0 인 층이 있다"
    Fl2, lab2, _, _ = truth_layers(case, J.PITCH)
    share = {L: round(float(((lab2 == i + 1) & Fl2).sum() / Fl2.sum()), 3) for i, L in enumerate(LAYERS)}
    print("  배관 통과 — %s · 일치 %s · 이진 %d · 층hull %d · 층기본 %d · 층기본이 기본 밖 %.1f%% · 층 부피몫 %s"
          % (case, agree, vox["이진"].sum(), vox["층hull"].sum(), vox["층기본"].sum(), 100 * 밖, share))


def 논문자료():
    """줄기 논문이 읽을 판정 json · 장별 csv · 그림을 `논문/층분해/` 에 둔다 (숫자를 손으로 안 박는다)."""
    import csv
    import glob
    import shutil
    d = os.path.join(HERE, "논문", "층분해")
    os.makedirs(os.path.join(d, "그림"), exist_ok=True)
    src = sorted(glob.glob(os.path.join(HERE, "out", "기록", "층분해_2026*.json")))[-1]
    shutil.copyfile(src, os.path.join(d, "판정.json"))
    for f in ("층분해.png", "층분해_층.png"):
        shutil.copyfile(os.path.join(HERE, "out", f), os.path.join(d, "그림", f))
    rs = [rows()[c] for c in CASES]
    cols = ["case"] + ["iou_%s" % k for k in VARS] + ["넘침_%s_%s" % (k, L) for k in ("이진", "기본", "층기본") for L in LAYERS]
    with open(os.path.join(d, "장별.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rs:
            w.writerow([r["case"]] + ["%.3f" % r["iou"][k]["128"] for k in VARS]
                       + ["%.3f" % r["넘침"][k][L] for k in ("이진", "기본", "층기본") for L in LAYERS])
    print("  -> %s" % d)


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        selfcheck(); plumb()
    elif a == "판정":
        verdict()
    elif a == "논문자료":
        논문자료()
    elif a == "그림":
        import 층분해그림
        층분해그림.main()
    else:
        run(int(a))


if __name__ == "__main__":
    main()
