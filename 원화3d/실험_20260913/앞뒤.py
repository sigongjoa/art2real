# -*- coding: utf-8 -*-
"""**부품 앞뒤를 맞히나** — 3D 없이, 순서만. 천장의 22% (깊이맵을 고치면 걷는 몫) 앞에 서는 문.

    python 앞뒤.py              자가검사 (답을 아는 합성 그림)
    python 앞뒤.py <벤치> [n]    벤치 = 실물 · 마네킹 · 스캔   -> out/기록/앞뒤_<벤치>.jsonl

근거는 `claudedocs/research_깊이선행연구_20260913.md`. IoU 벤치(B 단계)는 **여기를 지난 것만** 건다.

## 정답

판 라벨(`labels.npy`, 선 띠는 가장 가까운 판으로 채움)에서 **맞닿은 판 쌍**을 뽑는다 (둘 다 `MIN_AREA` 이상).
오라클 깊이(`오라클.oracle_depth`, 1 이 그 시점 카메라 쪽)가 경계에서 **계단**일 때만 가림이다:

    경계 바로 옆 띠 (GAP, NEAR] 의 양쪽 값이 JUMP 넘게 끊기고
    그 끊김이 한 띠 더 안쪽과의 변화(= 경사)의 STEP 배를 넘는다   -> 높은 쪽이 앞
    아니면 **이어진 면** — 채점에서 뺀다.  판이 얇아 경사를 못 재면 **모른다** — 역시 뺀다

**첫 판본(띠 6 화소 중앙값 · 차이 2%)은 틀렸다 (2026-09-13).** 대조군 「작은 판이 앞」이 마네킹·스캔에서
0.00~0.12 로 동전(0.5)에서 멀리 떨어졌고, 쌍을 뜯어보니 경계 점프가 0.000 인 쌍도 「앞」으로 셌다 —
얇은 판(해칭 선 조각)은 띠가 3 화소에서 끝나고 큰 판 쪽 띠만 비탈로 6 화소 들어가 중앙값이 갈린 것이다.
**경사를 가림으로 셌고, 그건 부풀리기(파이프)에 유리한 자다.** 판정 문턱이 아니라 정답의 정의를 고쳤다.
첫 판본 줄은 `앞뒤_<벤치>.jsonl` 에 옛 TAG 로 남아 있다.

**둘째 판본(붙은 띠 0-3-6 · 최소 면적 200)은 너무 좁았다.** 45 장 중 가림 쌍이 하나라도 있는 게 14 장이었다.
판정기가 잡은 자리를 메시의 계단 위에 그려 보니 **잡은 자리는 진짜 가림이었고** (모자챙-얼굴 · 치마-다리 ·
몸통-뒤로 간 팔 · 드릴 가로대) 놓친 건 선 띠와 메시 가림선이 1~2 화소 어긋난 자리, 면적 200 아래로 쪼개진 판이었다.
그래서 문턱(JUMP · STEP)은 두고 **띠 자리와 최소 면적만** 고쳤다. 고른 근거는 정답 쌍 개수와 그림뿐이다 —
맞히는 것들의 점수는 보지 않았다. 실물: 쌍 1039 중 가림 62 (11 장) -> 2596 중 325 (23 장).

그리고 실루엣은 `mask.npy` 가 아니라 **판의 알파**다 — `mask.npy` 는 색으로 갈라 흰 옷이 빠진다
(avatarsample_g 정면: 정답 실루엣과 0.79, 알파는 1.000).
시점은 front · back 둘 — `carve_depth` 가 그 둘만 읽는다.

## 맞히는 것 셋, 대조군 둘

    T접합    `art3d.py` 가 이미 낸 `depth_score` (Entem 2018). **계산돼 있는데 아무도 안 쓴다**
    환영     Ink-and-Ray 4.3 절. A∪B 에서 A 윤곽=0 · B 윤곽=1 로 라플라스를 풀고 p>0.5 = B′.
             B′ 가 B 보다 크면 B 가 가려진 것 -> A 가 앞
    옆판     옆 판에서 **같은 행 · 같은 색** 화소의 열 중앙값 = 그 판의 y. 추측이 아니라 측정이다.
             색이 한 가지인 물건(마네킹)에서는 기권한다 — 그대로 적는다

    면적     작은 판이 앞 (멍청한 규칙)
    파이프   지금 기본 깊이맵 `depth.npy` 의 같은 띠 중앙값 (지금 이미 가진 정보)

기권은 0.5 로 센다 (동전). 점수 = **경계 길이로 가중한 정답률** (기권 0.5).

## 판정 — 돌리기 전에 적는다 (2026-09-13)

벤치마다 케이스 평균 점수가 **0.5 초과**이고, **대조군 둘(면적 · 파이프) 각각을** 평균으로 이기고
**과반 케이스에서** 이겨야 「통과」. 문턱(TAU · BAND · 색 거리)은 돌리기 전에 정했고 튜닝하지 않는다.
실물은 tune/holdout 을 따로도 적는다.
"""
import gc
import json
import os
import sys
import time

import cv2
import numpy as np
from scipy import ndimage, sparse
from scipy.sparse.linalg import spsolve

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260912"))
os.chdir(HERE)

S = 512                     # art3d 가 돈 해상도. 라벨·깊이 모두 이 격자
BAND = 6                    # 맞히는 것들이 읽는 띠 두께 (화소)
GAP, NEAR, FAR = 2, 5, 8    # 정답: 경계에서 (GAP, NEAR] 가 바로 옆 띠, (NEAR, FAR] 가 한 띠 안쪽 (화소).
                            # GAP 은 선 띠를 채운 라벨 경계와 메시의 진짜 가림선이 1~2 화소 어긋나는 몫
JUMP = 0.05                 # 정답: 경계에서 깊이가 이만큼 끊겨야 가림 (물건 깊이 범위의 5%)
STEP = 2.0                  # 정답: 그 끊김이 판 안쪽 변화의 이 배는 돼야 — 경사가 아니라 계단
MIN_AREA = 50               # 이보다 작은 판은 쌍에서 뺀다. 얇은 조각은 FAR 띠가 없어 어차피 「모른다」로 빠진다
MIN_LEN = 8                 # 경계가 이보다 짧은 쌍은 안 센다
MIN_PX = 5                  # 띠 화소가 이보다 적으면 그 쌍은 모른다
GROW = 0.02                 # 환영: B′ 가 B 보다 이만큼(작은 판 면적 대비) 커야 판정
MAX_U = 25000               # 환영: 풀 영역 화소 상한
COLOR = 30.0                # 옆판: 같은 색으로 보는 RGB 거리
MIN_SIDE = 20               # 옆판: 짝 화소가 이보다 적으면 기권
MIN_DY = 3                  # 옆판: 두 판의 열 차가 이보다 작으면 기권
PRED = ("T접합", "환영", "옆판", "면적", "파이프")
TAG = "앞뒤 A3 · 계단정답 틈2-5-8 JUMP0.05 STEP2 면적50 · 시트알파 (2026-09-13)"
REC = os.path.join(HERE, "out", "기록")


# ------------------------------------------------------------------ 판 쌍

def fill(lab, mask):
    """선 띠(0)를 가장 가까운 판으로. **실루엣 안에서만** — 밖은 0."""
    if (lab == 0).any() and (lab > 0).any():
        idx = ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
        lab = lab[tuple(idx)]
    return np.where(mask, lab, 0)


def pairs_of(F):
    """맞닿은 판 쌍 -> {(a, b): 경계 길이}. a < b."""
    out = {}
    for x, y in ((F[:, :-1], F[:, 1:]), (F[:-1, :], F[1:, :])):
        m = (x > 0) & (y > 0) & (x != y)
        a, b = np.minimum(x[m], y[m]).astype(np.int64), np.maximum(x[m], y[m]).astype(np.int64)
        k, c = np.unique(a * 65536 + b, return_counts=True)
        for kk, cc in zip(k, c):
            key = (int(kk // 65536), int(kk % 65536))
            out[key] = out.get(key, 0) + int(cc)
    return {k: v for k, v in out.items() if v >= MIN_LEN}


def crop(F, a, b, pad):
    ys, xs = np.nonzero((F == a) | (F == b))
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, F.shape[0])
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, F.shape[1])
    return slice(y0, y1), slice(x0, x1)


def bands(F, a, b):
    """A 쪽 띠 · B 쪽 띠 (경계에서 BAND 화소 안). 원본 격자 크기의 마스크 둘 대신 자른 조각과 자리."""
    sl = crop(F, a, b, BAND + 2)
    f = F[sl]
    da = cv2.distanceTransform((f != a).astype(np.uint8), cv2.DIST_L2, 3)
    db = cv2.distanceTransform((f != b).astype(np.uint8), cv2.DIST_L2, 3)
    return sl, (f == a) & (db <= BAND), (f == b) & (da <= BAND)


def band_sign(val, ok, sl, ba, bb, tau):
    """띠 두 개의 중앙값 비교 -> +1 (A 가 큼) · -1 · 0. `ok` 는 값을 믿을 화소."""
    v, o = val[sl], ok[sl]
    pa, pb = v[ba & o], v[bb & o]
    if len(pa) < MIN_PX or len(pb) < MIN_PX:
        return None
    d = float(np.median(pa) - np.median(pb))
    return 1 if d > tau else -1 if d < -tau else 0


def gt_sign(orc, ok, F, a, b):
    """정답 — **계단일 때만** 가림이다. +1 (A 가 앞) · -1 · 0 (이어진 면 · 경사) · None (못 잰다)."""
    sl = crop(F, a, b, FAR + 2)
    f, o, k = F[sl], orc[sl], ok[sl]
    da = cv2.distanceTransform((f != a).astype(np.uint8), cv2.DIST_L2, 3)
    db = cv2.distanceTransform((f != b).astype(np.uint8), cv2.DIST_L2, 3)

    def med(m):
        v = o[m & k]
        return float(np.median(v)) if len(v) >= MIN_PX else None
    an, af = med((f == a) & (db > GAP) & (db <= NEAR)), med((f == a) & (db > NEAR) & (db <= FAR))
    bn, bf = med((f == b) & (da > GAP) & (da <= NEAR)), med((f == b) & (da > NEAR) & (da <= FAR))
    if None in (an, af, bn, bf):
        return None
    jump = an - bn
    if abs(jump) < JUMP or abs(jump) < STEP * (abs(an - af) + abs(bn - bf)):
        return 0
    return 1 if jump > 0 else -1


# ------------------------------------------------------------------ 맞히는 것

def illusory(F, a, b):
    """Ink-and-Ray 4.3 — A∪B 윤곽에서 A=0 · B=1 로 확산, p>0.5 = B′. B′ > B 면 A 가 앞 (+1)."""
    sl = crop(F, a, b, 1)
    f = F[sl]
    k = int(np.ceil(np.sqrt(((f == a) | (f == b)).sum() / MAX_U))) if ((f == a) | (f == b)).sum() > MAX_U else 1
    # ponytail: 큰 쌍은 k 배 성기게 푼다. 경계 모양이 k 화소 안에서 뭉개진다 — 틀리는 게 큰 판에 몰리면 다중격자로
    f = f[::k, ::k]
    U = (f == a) | (f == b)
    if (f == a).sum() < 4 or (f == b).sum() < 4:
        return 0
    edge = U & ~ndimage.binary_erosion(U, border_value=0)
    fixed = edge.copy()
    val = np.where(f == b, 1.0, 0.0)
    free = U & ~fixed
    n = int(free.sum())
    if n == 0:
        return 0
    idx = -np.ones(f.shape, np.int64)
    idx[free] = np.arange(n)
    rows, cols, data = [], [], []
    rhs = np.zeros(n)
    deg = np.zeros(n)
    fy, fx = np.nonzero(free)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ny, nx = fy + dy, fx + dx
        inb = (ny >= 0) & (ny < f.shape[0]) & (nx >= 0) & (nx < f.shape[1])
        i = np.nonzero(inb)[0]
        ny, nx = ny[inb], nx[inb]
        inU = U[ny, nx]
        i, ny, nx = i[inU], ny[inU], nx[inU]
        deg[i] += 1
        j = idx[ny, nx]
        fr = j >= 0
        rows += [i[fr]]; cols += [j[fr]]; data += [-np.ones(fr.sum())]
        np.add.at(rhs, i[~fr], val[ny[~fr], nx[~fr]])
    L = sparse.csr_matrix((np.concatenate(data + [deg]),
                           (np.concatenate(rows + [np.arange(n)]), np.concatenate(cols + [np.arange(n)]))),
                          shape=(n, n))
    p = val.copy()
    p[free] = spsolve(L.tocsc(), rhs)
    grow = float(((p > 0.5) & U).sum() - (f == b).sum()) / max(min((f == a).sum(), (f == b).sum()), 1)
    return 1 if grow > GROW else -1 if grow < -GROW else 0


def side_y(lab, img, rows_of, side_img, side_mask):
    """판마다 옆 판에서 같은 행 · 같은 색 화소의 열 중앙값. 못 찾으면 None."""
    out = {}
    sm = side_mask
    for k, rs in rows_of.items():
        px = img[lab == k]
        if not len(px):                             # 선 띠뿐인 판 — 제 색이 없다
            out[k] = None
            continue
        c = px.mean(0)
        r0, r1 = rs
        seg = side_img[r0:r1 + 1].astype(np.float32)
        hit = sm[r0:r1 + 1] & (np.linalg.norm(seg - c, axis=2) < COLOR)
        _, xs = np.nonzero(hit)
        out[k] = float(np.median(xs)) if len(xs) >= MIN_SIDE else None
    return out


def side_sign(ya, yb, view):
    """옆 판 화면 가로 = +y, 앞이 -y. front 에선 열이 작은 쪽이 카메라 쪽, back 에선 큰 쪽."""
    if ya is None or yb is None or abs(ya - yb) < MIN_DY:
        return 0
    s = 1 if ya < yb else -1
    return s if view == "front" else -s


# ------------------------------------------------------------------ 케이스

def load_img(p, size=S):
    im = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
    return cv2.resize(im, (size, size), interpolation=cv2.INTER_AREA)


def sheet_mask(case, view):
    """판의 **알파**가 실루엣이다 (`win.art_mask`). `mask.npy` 는 색으로 갈라 흰 옷이 빠진다."""
    import win as W
    m = W.art_mask(os.path.join(HERE, "out", "시트", case, view + ".png"))
    return cv2.resize(m.astype(np.uint8), (S, S), interpolation=cv2.INTER_NEAREST).astype(bool)


def view_rows(case, truth, view, side):
    import win as W
    import 오라클 as O
    d = os.path.join(HERE, "out", "깊이", case)
    lab = np.load(os.path.join(d, view, "labels.npy"))
    mask = sheet_mask(case, view)
    dep = np.load(os.path.join(d, view, "depth.npy"))
    js = json.load(open(os.path.join(d, view, "art3d.json"), encoding="utf-8"))
    tscore = {r["id"]: r["depth_score"] for r in js["regions"]}
    img = load_img(os.path.join(d, "_흰_%s.png" % view))

    V, Fc = np.asarray(truth.vertices), np.asarray(truth.faces)
    sil = W.silhouette(V, Fc, view, -1 if view == "back" else None)
    s5 = cv2.resize(sil.astype(np.uint8), (S, S), interpolation=cv2.INTER_NEAREST).astype(bool)
    # **프레임이 맞나.** 뒤집힌 프레임이면 아래 정답이 전부 헛것이다
    iou, iouf = W.iou(s5, mask), W.iou(s5[:, ::-1], mask)
    assert iou > 0.85 and iou >= iouf - 0.005, "%s/%s 정답 실루엣이 판과 안 맞는다 (%.3f · 뒤집으면 %.3f)" % (
        case, view, iou, iouf)
    orc = cv2.resize(O.oracle_depth(truth, view), (S, S), interpolation=cv2.INTER_NEAREST)

    F = fill(lab, mask)
    area = {int(k): int(c) for k, c in zip(*np.unique(F[F > 0], return_counts=True))}
    P = {k: L for k, L in pairs_of(F).items() if min(area[k[0]], area[k[1]]) >= MIN_AREA}
    ys = {}
    for k in area:
        r = np.nonzero((F == k).any(1))[0]
        ys[k] = (int(r.min()), int(r.max()))
    sy = side_y(np.where(lab > 0, F, 0), img, ys, side["img"], side["mask"])

    out = []
    for (a, b), L in P.items():
        sl, ba, bb = bands(F, a, b)
        gt = gt_sign(orc, s5, F, a, b)
        if not gt:                                  # None (띠 부족) · 0 (같은 면) 은 안 센다
            continue
        pr = {
            "T접합": int(np.sign(tscore.get(a, 0) - tscore.get(b, 0))),
            "환영": illusory(F, a, b),
            "옆판": side_sign(sy.get(a), sy.get(b), view),
            "면적": 1 if area[a] < 0.9 * area[b] else -1 if area[b] < 0.9 * area[a] else 0,
            "파이프": band_sign(dep, dep > 0, sl, ba, bb, 1e-6) or 0,
        }
        out.append({"len": L, "gt": gt, "a": a, "b": b, **pr})
    return out, len(P), F


def score(rows):
    """경계 길이 가중 · 기권 0.5. 그리고 기권 안 한 몫 (덮음)."""
    w = np.array([r["len"] for r in rows], float)
    if not len(w):
        return {}
    gt = np.array([r["gt"] for r in rows])
    res = {}
    for k in PRED:
        p = np.array([r[k] for r in rows])
        right = (p == gt) * 1.0 + (p == 0) * 0.5
        res[k] = float((w * right).sum() / w.sum())
        res[k + "_덮음"] = float(w[p != 0].sum() / w.sum())
    return res


def one(case):
    import trimesh
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    d = os.path.join(HERE, "out", "깊이", case)
    side = {"img": load_img(os.path.join(d, "_흰_side.png")),
            "mask": sheet_mask(case, "side")}
    rows, npair = [], 0
    for v in ("front", "back"):
        r, n, _ = view_rows(case, truth, v, side)
        rows += r
        npair += n
    rec = {"case": case, "판": TAG, "쌍": npair, "가림쌍": len(rows), **score(rows), "초": round(time.time() - t0, 1)}
    del truth
    gc.collect()
    return rec


def report(recs, bench, split=None):
    recs = [r for r in recs if "T접합" in r]
    n = len(recs)
    if not n:
        return {}
    g = lambda k: np.array([r[k] for r in recs])
    print("\n  [%s%s] %d 장 · 가림 쌍 중앙 %d (전체 쌍의 %.0f%%) · 점수 = 경계 가중 정답률, 기권 0.5" % (
        bench, " · " + split if split else "", n, np.median(g("가림쌍")),
        100 * np.median(g("가림쌍") / np.maximum(g("쌍"), 1))))
    verdict = {}
    for k in PRED:
        line = "    %-6s 평균 %.3f · 중앙 %.3f · 덮음 %.0f%%" % (k, g(k).mean(), np.median(g(k)), 100 * np.median(g(k + "_덮음")))
        if k not in ("면적", "파이프"):
            beats = [(g(k) - g(c)).mean() > 0 and (g(k) > g(c)).sum() > n / 2 for c in ("면적", "파이프")]
            ok = g(k).mean() > 0.5 and all(beats)
            verdict[k] = "통과" if ok else "짐"
            line += " · 면적 대비 %+.3f (%d/%d) · 파이프 대비 %+.3f (%d/%d) · **%s**" % (
                (g(k) - g("면적")).mean(), (g(k) > g("면적")).sum(), n,
                (g(k) - g("파이프")).mean(), (g(k) > g("파이프")).sum(), n, verdict[k])
        print(line)
    return verdict


# ------------------------------------------------------------------ 그림

FIG_COLS = ("파이프", "환영", "T접합", "옆판")


def figure(bench="실물"):
    """**맞힌 경계를 원화 위에 칠한다.** 숫자 표 말고 어느 경계를 누가 틀렸나.

    케이스는 규칙으로 고른다 — 가림 쌍이 많은 4장 + 파이프가 제일 많이 틀린 2장. 시점은 가림 쌍이 많은 쪽.
    정답 칸: 앞인 쪽 띠 = 주황, 뒤인 쪽 = 파랑. 나머지 칸: 초록 = 맞힘 · 빨강 = 틀림 · 노랑 = 기권."""
    import trimesh
    from PIL import Image, ImageDraw
    from 계획 import _font
    from 천장 import cases_of
    rows = {}
    for l in open(os.path.join(REC, "앞뒤_%s.jsonl" % bench), encoding="utf-8"):
        r = json.loads(l)
        if r.get("판") == TAG and "T접합" in r and r["case"] != "소체":   # 소체 = base_female (md5 같음)
            rows[r["case"]] = r
    by_n = sorted(rows, key=lambda c: -rows[c]["가림쌍"])[:4]
    worst = [c for c in sorted(rows, key=lambda c: rows[c]["파이프"]) if c not in by_n][:2]
    picks = [(c, "가림 쌍 많은 순") for c in by_n] + [(c, "파이프가 제일 틀린 순") for c in worst]

    T, PAD = 300, 10
    cols = ["원화", "정답"] + list(FIG_COLS)
    LW, TOP, RH = 230, 150, T + 40
    im = Image.new("RGB", (LW + len(cols) * (T + PAD) + PAD, TOP + len(picks) * RH + 20), "white")
    dr = ImageDraw.Draw(im)
    f1, f2, f3 = _font(28), _font(17), _font(14)
    dr.text((24, 18), "부품 앞뒤를 누가 맞히나 — %s 벤치 · 케이스마다 가림 쌍이 많은 시점" % bench,
            fill=(20, 20, 20), font=f1)
    dr.text((24, 60), "정답 = 정답 메시 깊이가 판 경계에서 계단인 쌍 · 주황 = 앞 · 파랑 = 뒤. "
                      "나머지 칸: 초록 = 맞힘 · 빨강 = 틀림 · 노랑 = 기권 · 칸 아래 = 이 시점 점수 (기권 0.5)",
            fill=(90, 90, 90), font=f3)
    g = lambda k: np.array([r[k] for r in rows.values()])
    dr.text((24, 84), "%d장 평균 — " % len(rows) + " · ".join("%s %.3f" % (k, g(k).mean()) for k in PRED),
            fill=(40, 40, 40), font=f2)
    for j, name in enumerate(cols):
        dr.text((LW + PAD + j * (T + PAD), TOP - 26), name, fill=(40, 40, 40), font=f2)

    for i, (case, why) in enumerate(picks):
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        d = os.path.join(HERE, "out", "깊이", case)
        side = {"img": load_img(os.path.join(d, "_흰_side.png")), "mask": sheet_mask(case, "side")}
        got = {v: view_rows(case, truth, v, side) for v in ("front", "back")}
        v = max(got, key=lambda k: len(got[k][0]))             # 가림 쌍이 많은 시점
        prs, _, F = got[v]
        sc = score(prs)
        img = load_img(os.path.join(d, "_흰_%s.png" % v))
        base = (img * 0.35 + 255 * 0.65).astype(np.uint8)
        ys, xs = np.nonzero(sheet_mask(case, v))
        c, h = ((ys.min() + ys.max()) // 2, (xs.min() + xs.max()) // 2), max(np.ptp(ys), np.ptp(xs)) // 2 + 8
        tiles = {"원화": img.copy(), "정답": base.copy(), **{k: base.copy() for k in FIG_COLS}}
        for r in prs:
            sl, ba, bb = bands(F, r["a"], r["b"])
            front, back = (ba, bb) if r["gt"] == 1 else (bb, ba)
            t = tiles["정답"][sl]
            t[front], t[back] = (0, 140, 255), (220, 120, 30)          # BGR: 주황 · 파랑
            for k in FIG_COLS:
                col = (60, 170, 60) if r[k] == r["gt"] else (40, 40, 220) if r[k] == -r["gt"] else (0, 200, 230)
                tiles[k][sl][ba | bb] = col
        y0 = TOP + i * RH
        dr.text((24, y0 + 8), case[:22], fill=(20, 20, 20), font=f2)
        dr.text((24, y0 + 32), "%s 가림 %d쌍" % ({"front": "정면", "back": "후면"}[v], len(prs)),
                fill=(90, 90, 90), font=f3)
        dr.text((24, y0 + 52), why, fill=(150, 150, 150), font=f3)
        for j, name in enumerate(cols):
            crop_ = tiles[name][max(c[0] - h, 0):c[0] + h, max(c[1] - h, 0):c[1] + h]
            tile = cv2.resize(crop_, (T, T), interpolation=cv2.INTER_NEAREST)
            xx = LW + PAD + j * (T + PAD)
            im.paste(Image.fromarray(tile[:, :, ::-1]), (xx, y0))
            dr.rectangle([xx, y0, xx + T - 1, y0 + T - 1], outline=(215, 215, 215))
            if name in FIG_COLS and sc:
                v = sc[name]
                dr.text((xx, y0 + T + 4), "%.2f · 덮음 %.0f%%" % (v, 100 * sc[name + "_덮음"]), font=f3,
                        fill=(30, 130, 60) if v > 0.5 else (190, 60, 40) if v < 0.5 else (90, 90, 90))
        print("  %-30s 정면 가림 %d쌍" % (case[:30], len(prs)), flush=True)
    p = os.path.join(HERE, "out", "앞뒤_%s.png" % bench)
    im.save(p)
    print("  -> %s" % os.path.relpath(p, HERE))


# ------------------------------------------------------------------ 자가검사

def selfcheck():
    """답을 손으로 아는 그림. 원판 B(깊이 0.3) 아래쪽을 사각형 A(깊이 0.9)가 가린다."""
    H = 200
    yy, xx = np.mgrid[0:H, 0:H]
    B = (yy - 90) ** 2 + (xx - 100) ** 2 < 55 ** 2
    A = (yy > 110) & (yy < 185) & (xx > 55) & (xx < 145)
    F = np.zeros((H, H), np.int32)
    F[B], F[A] = 2, 1                               # A 가 위에 칠해졌다 = 앞
    orc = np.where(A, 0.9, np.where(B, 0.3, 1.0)).astype(np.float32)
    P = pairs_of(F)
    assert (1, 2) in P, "맞닿은 쌍을 못 찾았다 %s" % P
    assert gt_sign(orc, F > 0, F, 1, 2) == 1, "정답: A 가 앞인데 아니라고 한다"
    # 경사는 가림이 아니다 — 한 비탈 위의 두 판 (첫 판본의 정답이 이걸 가림으로 셌다)
    R = np.zeros((80, 80), np.int32)
    R[10:70, 10:40], R[10:70, 40:70] = 1, 2
    ramp = (np.mgrid[0:80, 0:80][1] / 60.0).astype(np.float32)
    assert gt_sign(ramp, R > 0, R, 1, 2) == 0, "정답: 비탈을 가림으로 센다"
    assert illusory(F, 1, 2) == 1, "환영: 가려진 원판을 못 알아본다"
    # 뒤집어 칠하면 (B 가 A 를 가림) 답도 뒤집혀야 한다
    G = np.zeros((H, H), np.int32)
    G[A], G[B] = 1, 2
    assert illusory(G, 1, 2) == -1, "환영: 뒤집힌 가림에서 답이 안 뒤집힌다"
    # 옆판: 빨강(A)이 열 40, 파랑(B)이 열 120 -> 앞(-y, 작은 열)은 A
    img = np.zeros((H, H, 3), np.uint8)
    img[A], img[B & ~A] = (0, 0, 255), (255, 0, 0)
    sim = np.full((H, H, 3), 255, np.uint8)
    sim[20:190, 35:45], sim[20:190, 115:125] = (0, 0, 255), (255, 0, 0)
    smask = (sim != 255).any(2)
    ys = {k: (int(np.nonzero((F == k).any(1))[0].min()), int(np.nonzero((F == k).any(1))[0].max())) for k in (1, 2)}
    sy = side_y(F, img, ys, sim, smask)
    assert abs(sy[1] - 39.5) < 1 and abs(sy[2] - 119.5) < 1, "옆판: 열을 잘못 읽었다 %s" % sy
    assert side_sign(sy[1], sy[2], "front") == 1 and side_sign(sy[1], sy[2], "back") == -1, "옆판: 앞뒤 부호"
    print("  자가검사 통과 — 정답 (계단 · 비탈) · 환영 (양방향) · 옆판 (front/back 부호)")


def main():
    selfcheck()
    if len(sys.argv) < 2:
        return
    if sys.argv[1] == "그림":
        figure(sys.argv[2] if len(sys.argv) > 2 else "실물")
        return
    import 오라클 as O
    from 천장 import cases_of
    O.H.register_sheets()
    bench = sys.argv[1]
    cases = cases_of(bench)
    if len(sys.argv) > 2:
        cases = cases[:int(sys.argv[2])]
    out = os.path.join(REC, "앞뒤_%s.jsonl" % bench)
    done = {}
    if os.path.exists(out):
        for l in open(out, encoding="utf-8"):
            r = json.loads(l)
            if r.get("판") == TAG:
                done[r["case"]] = r
    recs = []
    for c in cases:
        if c not in done:
            if not os.path.exists(os.path.join(HERE, "out", "시트", c, "truth.glb")):
                print("  %-30s 정답 메시 없음 — 건너뜀" % c[:30]); continue
            r = one(c)
            with open(out, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print("  %-30s 가림쌍 %3d/%3d · %s · %.0f초" % (c[:30], r["가림쌍"], r["쌍"], " ".join(
                "%s %.2f" % (k, r[k]) for k in PRED if k in r), r["초"]), flush=True)
            done[c] = r
        recs.append(done[c])
    report(recs, bench)
    if bench == "실물":
        sp = {c["name"]: c["split"] for c in json.load(open(os.path.join(HERE, "벤치.json"), encoding="utf-8"))["cases"]}
        for s in ("tune", "holdout"):
            report([r for r in recs if sp.get(r["case"]) == s], bench, s)


if __name__ == "__main__":
    main()
