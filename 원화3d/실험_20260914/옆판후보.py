# -*- coding: utf-8 -*-
"""**옆판 평면 후보 (게이트 B)** — 판마다 깊이 한 값을 「옆판에서 뽑은 평면 후보 몇 개 중 하나」로 줄여도 남나 (2026-09-14).

    python 옆판후보.py 검사     자가검사만
    python 옆판후보.py [n]      아직 안 한 장 n 개 (첫 장은 열린 궤짝) -> out/기록/옆판후보_진행.jsonl
    python 옆판후보.py 판정     -> out/기록/옆판후보_<때>.json
    python 옆판후보.py 그림     -> out/깊이색_옆판후보.png · out/옆판후보_선.png

판정은 `claudedocs/plan_옆판후보_20260914.md` 「판정」 절 그대로다 — 돌리기 전에 적었다.
**배정은 오라클이다** (판 중앙값에 가장 가까운 후보). 이 게이트는 후보 집합만 잰다.
이진 · 오라클 · 상수·원화판 숫자는 `벤치선.py` 기록에서 읽는다.
"""
import gc
import json
import os
import sys
import time

import cv2
import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 벤치선 as B

P, H, W, O, HERE = B.P, B.H, B.W, B.O, B.HERE
CASES = P.ANGULAR
LAM = P.LAM
TAG = "옆판후보 · _선2 · 오라클 배정 · 정답(|ny|≥cos10 · 0.005 · 0.5%) · 옆판(≥10 · 3열) · lam1.00 · 격자2 (2026-09-14)"
PROG = os.path.join(HERE, "out", "기록", "옆판후보_진행.jsonl")
NAMES = ("후보·자기", "후보·정답", "후보·옆판", "후보·균일")


def cand_truth(mesh, deg=10.0, bin_=0.005, share=0.005):
    """정답 메시에서 앞뒤(y)를 보는 면의 y 자리 — 면적 가중 평균, 면적 합의 share 넘는 칸만."""
    n = np.asarray(mesh.face_normals)
    sel = np.abs(n[:, 1]) >= np.cos(np.radians(deg))
    a = np.asarray(mesh.area_faces)[sel]
    y = np.asarray(mesh.vertices)[np.asarray(mesh.faces)[sel]][:, :, 1].mean(1)
    _, inv = np.unique(np.round(y / bin_).astype(np.int64), return_inverse=True)
    area = np.bincount(inv, a)
    return (np.bincount(inv, a * y) / np.maximum(area, 1e-12))[area > share * a.sum()]


def side_columns(lab, mask, need=10, gap=3):
    """side 판 분할(512)의 세로 경계 열 + mask 맨 앞 · 맨 뒤 열 -> 512 열 좌표 (경계 = 열 c 와 c+1 사이 = c+1)."""
    diff = (lab[:, 1:] != lab[:, :-1]) & mask[:, 1:] & mask[:, :-1]
    cols = np.flatnonzero(diff.sum(0) >= need) + 1
    merged = []
    for c in cols:
        if merged and c - merged[-1][-1] <= gap:
            merged[-1].append(c)
        else:
            merged.append([c])
    xs = np.flatnonzero(mask.any(0))
    return sorted({float(np.mean(g)) for g in merged} | {float(xs.min()), float(xs.max() + 1)})


def cand_side(case):
    """`_선2` side 원화에서 옆판 후보 -> 월드 y. 시트 side 는 topix(+y, z) 로 그렸으니 열이 곧 y 다."""
    from scipy import ndimage
    lab = np.load(os.path.join(HERE, "out", "깊이", B.NEW(case), "side", "labels_grown.npy"))
    if (lab == 0).any() and (lab > 0).any():                            # 선 띠(0)는 가까운 판으로 (`H.load_labels` 와 같다)
        lab = lab[tuple(ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True))]
    m = W.art_mask(os.path.join(HERE, "out", "시트", B.NEW(case), "side.png"))
    m512 = cv2.resize(m.astype(np.uint8), (lab.shape[1], lab.shape[0]), interpolation=cv2.INTER_NEAREST).astype(bool)
    cols = np.array(side_columns(lab, m512))
    return W.U0 + cols * (W.RES / lab.shape[1]) / W.RES * (W.U1 - W.U0)


def snap(dep, lab, mask, cands):
    """판마다 중앙값(`상수` 뭉개기)을 가장 가까운 후보로. cands=None 이면 중앙값 그대로 (배관)."""
    out = P.flatten(dep, lab, mask, "상수")
    if cands is None:
        return out
    c = np.sort(np.asarray(cands, np.float64))
    sel = mask & (lab > 0)
    v = out[sel].astype(np.float64)
    i = np.clip(np.searchsorted(c, v), 1, max(len(c) - 1, 1))
    lo, hi = c[i - 1], c[np.minimum(i, len(c) - 1)]
    out[sel] = np.where(v - lo <= hi - v, lo, hi)
    return out


def cands_of(case, truth):
    y = np.asarray(truth.vertices)[:, 1]
    sy = cand_side(case)
    return {"후보·자기": None, "후보·정답": cand_truth(truth), "후보·옆판": sy,
            "후보·균일": np.linspace(sy.min(), sy.max(), len(sy))}, float(y.min()), float(y.max())


def to_dep(ys, v, lo, hi):
    """월드 y -> `오라클.oracle_depth` 값 (front 는 hi−y · back 은 y−lo, 물건 y 범위로 나눔)."""
    return (hi - ys) / (hi - lo) if v == "front" else (ys - lo) / (hi - lo)


def post_of(case, ys, lo, hi):
    def post(v, d, dep):
        lab = H.load_labels(v, d, case=B.NEW(case))
        return snap(dep, lab, d, None if ys is None else np.clip(to_dep(ys, v, lo, hi), 0, 1))
    return post


def one(case, bench):
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", B.NEW(case), "truth.glb"), force="mesh")
    iou128, iou192 = O._iou_fn(truth), O._iou_fn(truth, P.P192)
    C, lo, hi = cands_of(case, truth)
    row = {"case": case, "판": TAG, "K": {k: (0 if v is None else len(v)) for k, v in C.items()},
           "후보y": {k: (None if v is None else [round(float(x), 4) for x in v]) for k, v in C.items()}}
    for name in NAMES:
        _, vox, axes, _ = O.build(B.NEW(case), truth, LAM, "오라클", post=post_of(case, C[name], lo, hi))
        mesh = O.C.to_mesh(vox, axes)
        row[name], row[name + "·192"] = iou128(mesh, axes), iou192(mesh, axes)
        del vox, mesh
        gc.collect()
        if name == "후보·자기":
            row["배관차"] = abs(row[name] - bench[case]["상수·원화판"])
            if row["배관차"] >= 1e-4:
                print("  %s 배관 어긋남 %.6f — 멈춘다" % (case, row["배관차"]))
                break
    row["초"] = round(time.time() - t0, 1)
    return row


def judge(rows, bench):
    bad = [r["case"] for r in rows if r["배관차"] >= 1e-4]
    if bad:
        return {"배관": "어긋남 — 숫자를 버린다", "어긋난 장": bad}
    rs = [dict(bench[r["case"]], **r) for r in rows]
    n = len(rs)
    g = lambda k: np.array([r[k] for r in rs])
    ceil = g("오라클") - g("이진")
    live = ceil > 0.01
    frac = lambda k: float(np.median((g(k) - g("이진"))[live] / ceil[live]))
    S = frac("상수·원화판")
    ds = [g("후보·옆판") - g("후보·균일"), g("후보·옆판·192") - g("후보·균일·192")]
    beat = all(d.mean() > 0 and (d > 0).sum() > n / 2 for d in ds)
    out = {"배관": "통과", "장": n, "S 상수·원화판": S,
           "천장몫중앙": {k: frac(k) for k in NAMES[1:]},
           "옆판−균일 이김 128·192": [int((ds[0] > 0).sum()), int((ds[1] > 0).sum())],
           "옆판−균일 평균차 128·192": [float(ds[0].mean()), float(ds[1].mean())],
           "K 중앙 정답·옆판": [float(np.median([r["K"]["후보·정답"] for r in rs])),
                             float(np.median([r["K"]["후보·옆판"] for r in rs]))]}
    out["QB1"] = bool(frac("후보·정답") >= 0.8 * S)
    out["QB2"] = bool(frac("후보·옆판") >= 0.8 * S and beat)
    out["다음"] = ("멈춤 — 축정렬 평면 몇 개로는 모자라다 (적합 쪽을 다시 본다)" if not out["QB1"] else
                  "게이트 C — 옆판이 후보를 준다. 판마다 후보를 고르는 규칙" if out["QB2"] else
                  "게이트 B2 — 후보는 되는데 옆판에서 못 뽑는다")
    return out


def report(rows, bench):
    print("\n  케이스별 IoU (격자128) · K = 후보 수")
    for r in rows:
        b = bench[r["case"]]
        print("  %-26s 이진 %.4f · 오라클 %.4f · 상수·원화판 %.4f · " % (r["case"][:26], b["이진"], b["오라클"], b["상수·원화판"])
              + " · ".join("%s %.4f" % (k, r[k]) for k in NAMES[1:]) + " · K %s" % r["K"])
    v = judge(rows, bench)
    print("\n  판정\n  " + json.dumps(v, ensure_ascii=False, indent=1).replace("\n", "\n  "))
    p = os.path.join(HERE, "out", "기록", "옆판후보_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"때": time.strftime("%Y-%m-%d %H:%M"), "판": TAG, "케이스": CASES, "판정": v, "rows": rows},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  기록 -> %s" % os.path.relpath(p, HERE))


def figure(cases=("cloak_Chest_O72u4Drp8k", "cloak_Chest_Closed_AngpV0HxD8", "statue_Town_Center_cuQuFJEIfH",
                  "mech_Drill_8uBbH7Dvmb")):
    """① side 원화 위에 후보 선 (빨강 옆판 · 초록 정답) ② 45도 깊이색 — 정답 · 이진 · 상수·원화판 · 후보 셋."""
    import 깊이색 as DC
    import 앨리어싱 as AL
    side_rows, rows = [], []
    for case in cases:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", B.NEW(case), "truth.glb"), force="mesh")
        C, lo, hi = cands_of(case, truth)
        im = cv2.imdecode(np.fromfile(os.path.join(HERE, "out", "시트", B.NEW(case), "side.png"), np.uint8), cv2.IMREAD_UNCHANGED)
        a = im[:, :, 3:4].astype(np.float32) / 255
        rgb = (im[:, :, 2::-1] * a + 255 * (1 - a)).astype(np.uint8)
        for ys, col, off in ((C["후보·정답"], (40, 170, 60), 0), (C["후보·옆판"], (220, 40, 40), 3)):
            for y in ys:
                x = int((y - W.U0) / (W.U1 - W.U0) * W.RES)
                cv2.line(rgb, (x + off, 0), (x + off, W.RES - 1), col, 3)
        side_rows.append((case[:14], [rgb]))
        M = {}
        for name in ("상수·원화판",) + NAMES[1:]:
            ys = None if name == "상수·원화판" else C[name]
            pl, vox, axes, _ = O.build(B.NEW(case), truth, LAM, "오라클", post=post_of(case, ys, lo, hi))
            M.setdefault("이진", O.C.to_mesh(pl, axes))
            M[name] = O.C.to_mesh(vox, axes)
        fr, dr = AL.frame_of(M["이진"], 45), DC.depth_range(M["이진"], 45)
        tiles = [DC.colorize(DC.zbuffer(truth, 45, fr, 360), dr)]
        tiles += [DC.colorize(DC.zbuffer(M[k], 45, fr, 360), dr) for k in ("이진", "상수·원화판") + NAMES[1:]]
        rows.append((case[:14], tiles))
        print("  %s 그림" % case, flush=True)
    DC.grid(side_rows, ["side 원화 · 빨강 = 옆판 후보 · 초록 = 정답 후보"], "옆판 평면 후보 — 세로선 자리가 앞뒤 평면 자리",
            "앞(−y)이 왼쪽. 빨강은 side 판 분할의 세로 경계 열 · 초록은 정답 메시에서 y 를 보는 면", os.path.join(HERE, "out", "옆판후보_선.png"), S=420)
    DC.grid(rows, ["정답", "이진", "상수·원화판", "후보·정답", "후보·옆판", "후보·균일"],
            "옆판 평면 후보 — 판마다 깊이를 후보 중 하나로 (45도 · lam 1.00 · 오라클 배정)",
            "상수·원화판 = 판마다 정답 깊이 중앙값 · 후보·* = 그 중앙값을 가장 가까운 후보로. 균일 = 옆판 후보와 같은 개수를 고르게",
            os.path.join(HERE, "out", "깊이색_옆판후보.png"), S=300)
    print("  -> out/옆판후보_선.png · out/깊이색_옆판후보.png")


def selfcheck():
    # 1 정답 후보 — 몸통 앞면 · 뒷면 · 앞으로 튀어나온 혹의 앞면 y 를 되찾는다
    big = trimesh.creation.box((0.6, 0.4, 1.0))
    bump = trimesh.creation.box((0.2, 0.2, 0.3))
    bump.apply_translation([0, -0.30, 0])
    mm = trimesh.util.concatenate([big, bump])
    mm.vertices = W.normalize(np.asarray(mm.vertices, np.float64))
    c = cand_truth(mm)
    V = np.asarray(mm.vertices)
    nb = len(big.vertices)
    want = [V[:nb, 1].min(), V[:nb, 1].max(), V[nb:, 1].min()]
    assert all(np.abs(c - w).min() < 0.006 for w in want), "정답 후보가 상자 면 y 를 못 찾는다 %s vs %s" % (c, want)
    # 2 옆판 열 — 세로 띠 셋의 경계 · 앞뒤 끝
    lab = np.zeros((512, 512), np.int32)
    lab[:, 100:200], lab[:, 200:300], lab[:, 300:400] = 1, 2, 3
    m = np.zeros((512, 512), bool)
    m[50:450, 100:400] = True
    cols = side_columns(lab, m)
    assert cols == [100.0, 200.0, 300.0, 400.0], "옆판 열 %s" % cols
    # 3 배정 — None 은 상수 뭉개기 그대로 · 후보는 가까운 쪽
    dep = np.full((8, 8), 0.3, np.float32)
    dep[:, 4:] = 0.7
    L = np.ones((8, 8), np.float32)
    L[:, 4:] = 2
    mk = np.ones((8, 8), bool)
    assert np.array_equal(snap(dep, L, mk, None), P.flatten(dep, L, mk, "상수")), "자기 후보가 입력을 바꿨다"
    s = snap(dep, L, mk, [0.2, 0.8])
    assert np.allclose(s[:, :4], 0.2) and np.allclose(s[:, 4:], 0.8), "가까운 후보로 안 갔다"
    print("  자가검사 통과 — 정답 후보 %d 개 · 옆판 열 · 배정" % len(c))


def main():
    H.register_sheets()
    selfcheck()
    arg = sys.argv[1] if len(sys.argv) > 1 else "1"
    if arg == "검사":
        return
    if arg == "그림":
        return figure()
    bench = B.read_prog(B.PROG, B.TAG)
    done = B.read_prog(PROG, TAG)
    if arg != "판정":
        order = ["cloak_Chest_O72u4Drp8k"] + [c for c in CASES if c != "cloak_Chest_O72u4Drp8k"]
        for c in [c for c in order if c not in done][:int(arg)]:
            r = one(c, bench)
            with open(PROG, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            done[c] = r
            if r["배관차"] >= 1e-4:
                return
            print("  %-26s 상수·원화판 %.4f · " % (c[:26], bench[c]["상수·원화판"])
                  + " · ".join("%s %.4f" % (k, r[k]) for k in NAMES) + " · K %s · %.0f초" % (r["K"], r["초"]), flush=True)
    rows = [done[c] for c in CASES if c in done]
    if len(rows) == len(CASES) or arg == "판정":
        report(rows, bench)
    else:
        print("  %d/%d 장 — 다시 돌리면 이어 돈다" % (len(rows), len(CASES)))


if __name__ == "__main__":
    main()
