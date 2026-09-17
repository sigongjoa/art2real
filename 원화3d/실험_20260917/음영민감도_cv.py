# -*- coding: utf-8 -*-
"""**민감도 카드 1-CV — 명암을 SDXL 이 아니라 CV 로 만든다** (2026-09-17). 계획 `claudedocs/plan_음영민감도_20260917.md` 「CV 판」.

    python 음영민감도_cv.py 입력    창 좌표 원화 + 명암 판본 5 장 -> 스크래치 shade_cv/
    python 음영민감도_cv.py 생성    TripoSG 5 판본 × 씨앗 42 · 7 · 123
    python 음영민감도_cv.py 재기    -> out/기록/음영민감도CV_<때>.json
    python 음영민감도_cv.py 판정

SDXL 판의 문제 (사용자 「명암을 CV 로 하는 게 아니라 왜 SDXL 을」): SDXL 도 블랙박스라 명암이 어떤 깊이에서 왔는지 모르고,
망토를 검게 둬 신호가 약했다. 여기서는 **높이장을 알고** 램버트로 칠한다.

    k0   원화 (창 좌표) — 네 판본의 기준
    H05  3판 hull(지금 기본) 정면 높이장 명암 × 0.5      ← 옆 판 정보가 들어간다 (그 흘림이 시험 대상)
    H1   같은 명암 × 1
    E1   정면 실루엣 푸아송 부풀리기 명암 × 1             ← 옆 판 정보 없음
    F1   H1 과 같은 높이장, 빛을 위아래 · 좌우 뒤집음     ← 대조: 통계 같고 깊이가 틀림

명암은 알파 안 평균 0 · 표준편차 AMP(15, L 단위)로 맞춰 Lab L 에 더한다 (SDXL 판 v2 와 같은 세기). 머리(z > 0.86)는 0.
"""
import glob
import json
import os
import subprocess
import sys
import time

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage as nd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 음영민감도 as M                                   # setup · measure_one · labL · 씨앗 · 경로 공유
import hull as H
import win as W

S = os.path.join(os.path.dirname(M.S), "shade_cv")
VARS = [("k0", 0.0), ("H05", 0.5), ("H1", 1.0), ("E1", 1.0), ("F1", 1.0)]
L_UP = np.array([-0.45, 0.55, 0.70])                    # (화면 x 오른쪽, 화면 위, 보는 쪽) — 왼쪽 위 앞
SIG_H = 20.0                                            # 높이장 흐리기 (창 화소 · 복셀 약 5 칸) — σ8 은 계단이 가로 줄무늬로 남음 (입력 그림에서 확인 · 생성 전)
TAG = "음영민감도 CV v2 · 램버트 · hull/EDT 높이장 σ20 · 세기 σL 15 · 씨앗 42/7/123 · P = 옆 못덮음+넘침 (맞춤 없음) (2026-09-17)"


def win_art():
    """정면 원화를 `setup` 의 마스크와 **같은 변환**(declutter → to_win)으로 창에 앉힌다 — 채널을 extra 로 넘긴다."""
    im = cv2.imdecode(np.fromfile(M.SRC, np.uint8), cv2.IMREAD_UNCHANGED)
    rgb = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2RGB).astype(np.float32)
    m = H.declutter(W.art_mask(M.SRC))
    got = H.to_win(m, rgb[..., 0], rgb[..., 1], rgb[..., 2])
    mask = got[0]
    art = np.stack(got[1:], -1)
    art[~mask] = 255
    return art.astype(np.float64), mask


def pix_world():
    c = (np.arange(W.RES) + 0.5) / W.RES
    u = W.U0 + c * (W.U1 - W.U0)
    z = W.Z1 - c * (W.Z1 - W.Z0)
    return u, z                                         # 열 → u · 행 → z


def hull_height(masks, bs):
    """지금 기본 복셀의 정면(−y) 첫 칸 → 창 화소 높이장 (보는 쪽으로 +)."""
    deps = {v: np.ones((W.RES, W.RES), np.float32) for v in W.VIEWS}
    vox, _ = H.carve_default(masks, deps, back_sign=bs)
    _, axes = H.carve(masks, back_sign=bs)
    ux, uy, uz = axes
    occ = vox.any(1)                                     # (x, z)
    first = np.argmax(vox, axis=1)                       # y 가장 작은 칸 = 앞
    hgt = np.where(occ, -uy[first], np.nan)
    pu, pz = pix_world()
    ix = np.interp(pu, ux, np.arange(len(ux)))
    iz = np.interp(pz, uz, np.arange(len(uz)))
    IZ, IX = np.meshgrid(iz, ix, indexing="ij")
    valid = nd.map_coordinates(occ.astype(np.float32), [IX, IZ], order=0) > 0.5
    filled = np.where(occ, hgt, np.nanmin(hgt))
    return np.where(valid, nd.map_coordinates(filled, [IX, IZ], order=1), 0.0)


def edt_height(mask):
    """정면 실루엣만으로 부풀린 둥근 높이 — **푸아송** ∇²u = −1 (경계 0) 의 √. 거리변환은 가운데 능선(지붕)이 남는다 (σ20 에서도 · 입력 그림 확인)."""
    import scipy.sparse as sp
    from scipy.sparse.linalg import spsolve
    px = (W.U1 - W.U0) / W.RES
    idx = -np.ones(mask.shape, np.int64)
    ys, xs = np.nonzero(mask)
    idx[ys, xs] = np.arange(len(ys))
    rows, cols, vals = [np.arange(len(ys))], [np.arange(len(ys))], [np.full(len(ys), 4.0)]
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        yy, xx = ys + dy, xs + dx
        ok = (yy >= 0) & (yy < mask.shape[0]) & (xx >= 0) & (xx < mask.shape[1])
        j = np.full(len(ys), -1)
        j[ok] = idx[yy[ok], xx[ok]]
        k = j >= 0
        rows.append(np.nonzero(k)[0]); cols.append(j[k]); vals.append(-np.ones(k.sum()))
    A = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(len(ys),) * 2)
    u = spsolve(A, np.ones(len(ys)))
    h = np.zeros(mask.shape)
    h[ys, xs] = np.sqrt(np.maximum(u, 0)) * px
    return h


def lambert(hgt, mask, light):
    px = (W.U1 - W.U0) / W.RES
    A = mask.astype(np.float64)
    h = nd.gaussian_filter(hgt * A, SIG_H) / np.maximum(nd.gaussian_filter(A, SIG_H), 1e-6)
    gy, gx = np.gradient(h, px)                          # 행(아래로) · 열(오른쪽)
    n = np.stack([-gx, gy, np.ones_like(h)], -1)         # 화면 위 = −행 이라 gy 부호가 바뀐다
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    L = light / np.linalg.norm(light)
    return np.clip(n @ L, 0, 1)


def make_inputs():
    os.makedirs(S, exist_ok=True)
    masks, bs, axes = M.setup()
    art, mask = win_art()
    assert np.array_equal(mask, masks["front"]), "창 원화 마스크가 채점 마스크와 다르다"
    _, z = pix_world()
    keep = np.clip((0.86 - z) / 0.02, 0, 1)[:, None] * np.ones((1, W.RES))   # 머리 위는 0, 2% 깃털
    inside = mask & (keep > 0.99)
    hh = hull_height(masks, bs)
    fields = {"H": lambert(hh, mask, L_UP), "E": lambert(edt_height(mask), mask, L_UP),
              "F": lambert(hh, mask, L_UP * np.array([-1, -1, 1]))}
    Lo, lab = M.labL(art)
    ys, xs = np.nonzero(mask)
    box = (slice(ys.min(), ys.max() + 1), slice(max(xs.min() - 20, 0), xs.max() + 21))
    tiles = []
    for name, k in VARS:
        if k == 0:
            out = art
        else:
            s = fields[name[0]]
            f = (s - s[inside].mean()) / s[inside].std() * M.AMP * k * keep * mask
            lab2 = lab.copy()
            lab2[..., 0] = np.clip(Lo + f, 0, 100) * 255 / 100
            out = cv2.cvtColor(np.rint(lab2).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float64)
            out[~mask] = 255
        img = np.dstack([np.rint(out).astype(np.uint8), (mask * 255).astype(np.uint8)])
        Image.fromarray(img[box]).save(os.path.join(S, name + ".png"))
        tiles.append(np.rint(out[box]).astype(np.uint8))
    for key in ("H", "E", "F"):
        tiles.append(np.repeat((np.where(mask, fields[key], 1) * 255).astype(np.uint8)[box][..., None], 3, 2))
    Image.fromarray(np.hstack(tiles)).save(os.path.join(S, "inputs_sheet.png"))
    print("  입력 ->", S, "· 명암 H·F 상관 %.2f" % np.corrcoef(fields["H"][inside], fields["F"][inside])[0, 1])


def generate():
    ims = [os.path.join(S, v + ".png") for v, _ in VARS]
    subprocess.run([M.PY, M.TRI, *ims, "--outdir", os.path.join(S, "tri"), "--no-rmbg", "--seeds", ",".join(map(str, M.SEEDS))],
                   cwd=os.path.dirname(M.TRI), check=True)


def run_measure():
    masks, bs, axes = M.setup()
    rows = []
    for v, _ in VARS:
        for sd in M.SEEDS:
            a = M.measure_one(os.path.join(S, "tri", "%s_s%d.glb" % (v, sd)), masks, bs, axes, fit=False)
            r = {"판본": v, "씨앗": sd, "P": round(a["못덮음_side"] + a["넘침_side"], 4),
                 "정면": round(a["못덮음_front"] + a["넘침_front"], 4), "맞춤없음": a}
            rows.append(r)
            print("  %-4s s%-4d P %.4f · 정면 %.4f · 두께비 %.3f · 회전 %d 반전 %+d" % (v, sd, r["P"], r["정면"], a["두께비"], a["회전"], a["반전"]), flush=True)
    q = os.path.join("out", "기록", "음영민감도CV_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"판": TAG, "행": rows}, open(q, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", q)


def verdict():
    q = [x for x in sorted(glob.glob(os.path.join("out", "기록", "음영민감도CV_*.json"))) if "판정" not in x][-1]
    P = {(r["판본"], r["씨앗"]): r["P"] for r in json.load(open(q, encoding="utf-8"))["행"]}
    Ss = M.SEEDS

    def rule(a, b):
        d = [P[a, s] - P[b, s] for s in Ss]
        return {"차": d, "중앙": float(np.median(d)), "양수": sum(x > 0 for x in d), "통과": bool(np.median(d) > 0 and sum(x > 0 for x in d) >= 2)}

    spread = float(np.median([abs(P["k0", a] - P["k0", b]) for i, a in enumerate(Ss) for b in Ss[i + 1:]]))
    q1 = rule("k0", "H1")
    out = {"Q1 hull 명암이 옆을 맞추나 (k0−H1)": q1,
           "Q2 깊이가 맞아서인가 (F1−H1)": rule("F1", "H1"),
           "Q3 씨앗 흔들림보다 큰가": {"효과": abs(q1["중앙"]), "흔들림": spread, "통과": bool(abs(q1["중앙"]) > spread)},
           "Q4 옆 정보 없는 둥근 명암도 (k0−E1)": rule("k0", "E1"),
           "관찰 용량 (k0−H05)": rule("k0", "H05"),
           "판정 json": q}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    json.dump(out, open(q.replace(".json", "_판정.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def selfcheck():
    """램버트 부호 — 왼쪽 위에서 비추면 반구의 왼쪽 위가 오른쪽 아래보다 밝아야 한다."""
    yy, xx = np.mgrid[-50:51, -50:51].astype(float)
    m = xx ** 2 + yy ** 2 < 45 ** 2
    h = np.sqrt(np.clip(45 ** 2 - xx ** 2 - yy ** 2, 0, None)) * (W.U1 - W.U0) / W.RES
    s = lambert(h, m, L_UP)
    assert s[30, 30] > s[70, 70], "램버트 부호가 틀렸다 (%.2f vs %.2f)" % (s[30, 30], s[70, 70])
    f = lambert(h, m, L_UP * np.array([-1, -1, 1]))
    assert f[30, 30] < f[70, 70]
    print("  자가검사 통과 — 왼쪽 위 밝음 %.2f > 오른쪽 아래 %.2f" % (s[30, 30], s[70, 70]))


if __name__ == "__main__":
    a = sys.argv[1:] or ["입력"]
    {"검사": selfcheck, "입력": make_inputs, "생성": generate, "재기": run_measure, "판정": verdict}[a[0]]()
