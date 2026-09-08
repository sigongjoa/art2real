# -*- coding: utf-8 -*-
"""**재현 구멍 메우기** — 판 분할 라벨맵과 캡 마스크를 다시 만든다.

    python segment.py       ->  out/_L_alb.npy · out/cap_mask.png

이 둘은 세션 중 즉석 코드로 만들어 놓고 스크립트가 없었다. panels.py / graph.py /
horns.py / cap.py / base.py 가 전부 `_L_alb.npy` 를 읽는데 만드는 데가 없으면
트레일이 재현이 안 된다.

    1) albedo 분해   재질별로 **가장 밝은** 톤을 바탕으로 (면적으로 고르면 그늘을
                     고른다 — 견갑은 대부분 그늘이다). 얇은 내부 선은 블랙햇으로
                     따로 지켜서 지우지 않는다 (96·97)
    2) 헤시안 능선   획의 **중심**을 잡는다. 소벨은 획의 양쪽 가장자리를 준다 (88)
    3) 워터셰드      능선을 지형으로 쓴다. 먹선을 마스크로 쓰면 29.8% 를 잃는다 —
                     지형으로 쓰면 판이 100% 타일링된다 (89)

**이 스크립트는 원본을 정확히 재현하지 못한다.** 재 봤다:

    판 수      원본 18  /  재현 33
    경계       원본 924화소, 재현 1114화소
               원본 경계의 **85.3%** 가 재현에도 있다 (재현율)
               재현 경계의 72.6% 가 원본에도 있다 (정밀도) — 나머지는 과분할

그래서 **원본 `_L_alb.npy` 를 `parts/artifacts/` 에 그대로 커밋해 뒀다.**
오늘 README 에 적힌 숫자는 전부 그 파일에서 나온 것이다. 이 스크립트는
"어떻게 만들었나"의 기록이자 근사이지, 그 파일의 대체가 아니다.
`python segment.py --check` 로 언제든 다시 잰다.
"""
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
T4 = os.path.join(HERE, "..", "trail4_gen3d")
RES = 1024
cc = lambda u: (u + 0.6) / 1.2 * (RES - 1)
rr = lambda z: (1.1 - z) / 1.2 * (RES - 1)
WIN = dict(z1=0.985, z0=0.775, u0=0.118, u1=0.252)
MINPX = int(os.environ.get("MINPX", 40))
SEEDQ = float(os.environ.get("SEEDQ", 0.55))
SEEDW = int(os.environ.get("SEEDW", 5))
# 약한 경계 합치기. **기본은 끔(0).** 합치면 판 수는 원본(18)에 가까워지지만
# 진짜 경계까지 지운다 — 27판에서 경계 재현율이 85.3% -> 70.9% 로 떨어졌다
MERGE_T = float(os.environ.get("MERGE_T", 0.0))


def hue(mc):
    r, g, b = mc
    if r - b > 20 and r - g < 60:
        return "gold"
    if b - r > 8:
        return "lav"
    return "white" if min(mc) > 170 else "dark"


def ridge(g):
    """헤시안의 큰 고유값 λ+ = 어두운 선의 능선. 획의 중심에서 최대가 된다."""
    g = cv2.GaussianBlur(g.astype(np.float32), (0, 0), 1.0)
    gxx = cv2.Sobel(g, cv2.CV_32F, 2, 0, ksize=3)
    gyy = cv2.Sobel(g, cv2.CV_32F, 0, 2, ksize=3)
    gxy = cv2.Sobel(g, cv2.CV_32F, 1, 1, ksize=3)
    t = gxx + gyy
    d = np.sqrt(np.maximum((gxx - gyy) ** 2 + 4 * gxy ** 2, 0))
    return (t + d) / 2                                  # λ+


def albedo(C, S):
    """셀은 바탕색 × 그늘 배수다. 재질별로 **가장 밝은** 톤을 바탕으로 잡아 나눈다."""
    V = C.max(2).astype(np.float32)
    A = C.astype(np.float32).copy()
    cls = np.zeros(S.shape, np.uint8)
    for k, code in (("lav", 1), ("gold", 2), ("white", 3), ("dark", 4)):
        pass
    # 화소별 재질
    r, g, b = C[..., 0].astype(int), C[..., 1].astype(int), C[..., 2].astype(int)
    cls[(r - b > 20) & (r - g < 60) & S] = 2                      # gold
    cls[(b - r > 8) & S] = 1                                      # lav
    cls[(cls == 0) & S & (C.min(2) > 170)] = 3                    # white
    cls[(cls == 0) & S] = 4                                       # dark
    for code in (1, 2, 3):
        m = cls == code
        if m.sum() < 60:
            continue
        v = V[m]
        # **가장 밝은** 톤. 면적으로 고르면 그늘을 고른다 (96). 작은 면적 바닥은 둔다
        hi = np.quantile(v, 0.97)
        base = float(np.median(v[v >= min(hi, np.quantile(v, 0.90))]))
        f = np.clip(V / max(base, 1.0), 0.25, 1.0)
        A[m] = np.clip(C[m].astype(np.float32) / f[m][:, None], 0, 255)
    return A.astype(np.uint8), cls


def segment(view="front", win=None):
    """판을 바꿔 부를 수 있다 — 측면·후면도 같은 파이프라인으로 나눈다.
    win 은 월드 (u0,u1,z0,z1). 안 주면 정면 창(WIN)."""
    win = win or WIN
    raw = np.load(os.path.join(T4, "rgb_%s.npy" % view))
    rgb = raw[..., :3].astype(np.uint8)
    sil = raw[..., 3] > 0
    y0, y1 = int(rr(win["z1"])), int(rr(win["z0"]))
    x0, x1 = int(cc(win["u0"])), int(cc(win["u1"]))
    C = rgb[y0:y1, x0:x1]
    S = sil[y0:y1, x0:x1]
    A, cls = albedo(C, S)
    g = A.max(2).astype(np.float32)
    # 얇은 내부 선은 albedo 가 지워버린다 — 원화의 블랙햇으로 되살린다 (97)
    bh = cv2.morphologyEx(255 - C.max(2), cv2.MORPH_TOPHAT,
                          cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    R = ridge(g) + 0.6 * bh.astype(np.float32)
    R[~S] = R.max()
    # 능선을 지형으로 (먹선을 마스크로 쓰면 29.8% 를 잃는다, 89)
    Rn = cv2.normalize(R, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    seed_src = cv2.GaussianBlur(Rn, (0, 0), 1.2)
    lo = cv2.erode(seed_src, np.ones((SEEDW, SEEDW), np.uint8))
    seeds = (seed_src <= lo + 1) & S & (seed_src < np.quantile(seed_src[S], SEEDQ))
    n, lb = cv2.connectedComponents(seeds.astype(np.uint8), 8)
    mk = np.where(lb > 0, lb + 1, 0).astype(np.int32)
    mk[~S] = 1
    ws = cv2.watershed(cv2.cvtColor(Rn, cv2.COLOR_GRAY2BGR), mk.copy())
    # 워터셰드는 경계를 -1 로 남긴다 -> 라벨이 안 맞닿아 크랙 그래프가 경계를 못 찾는다.
    # 이웃 라벨로 메워 **100% 타일링**으로 만든다 (89 의 요점이 그거다)
    for _ in range(4):
        gap = (ws == -1) & S
        if not gap.any():
            break
        d = cv2.dilate(np.where(ws > 1, ws, 0).astype(np.float32), np.ones((3, 3), np.uint8))
        ws[gap] = d[gap].astype(np.int32)
    ws[(ws == -1) & S] = 1
    # **약한 경계는 합친다.** 워터셰드는 능선의 안장마다 선을 그어 과분할한다 —
    # 공유 경계의 능선이 약하고 색이 비슷하면 같은 판이다
    L0 = ws.copy()
    L0[~S] = 0
    for _ in range(60):
        pairs = {}
        for dy, dx in ((0, 1), (1, 0)):
            a = L0[:L0.shape[0] - dy, :L0.shape[1] - dx]
            b = L0[dy:, dx:]
            r = R[:R.shape[0] - dy, :R.shape[1] - dx]
            m = (a > 1) & (b > 1) & (a != b)
            for va, vb, rv in zip(a[m], b[m], r[m]):
                pairs.setdefault((min(va, vb), max(va, vb)), []).append(rv)
        if not pairs:
            break
        med = {v: np.median(C[L0 == v], 0) for v in np.unique(L0) if v > 1}
        best, bs = None, 1e18
        for (u, v), rs in pairs.items():
            if len(rs) < 4:
                continue
            score = float(np.mean(rs)) + 6.0 * float(np.abs(med[u] - med[v]).sum())
            if score < bs:
                bs, best = score, (u, v)
        if best is None or bs > MERGE_T:
            break
        L0[L0 == best[1]] = best[0]
    ws = L0

    # 작은 조각은 이웃 중 색이 가장 가까운 판에 합친다
    L = ws.copy()
    L[~S] = 0
    for v in [v for v in np.unique(L) if v > 1]:
        m = L == v
        if m.sum() >= MINPX:
            continue
        d = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & ~m
        nb = [w for w in np.unique(L[d]) if w > 1 and w != v]
        if not nb:
            L[m] = 1
            continue
        mc = np.median(C[m], 0)
        L[m] = min(nb, key=lambda w: np.abs(np.median(C[L == w], 0) - mc).sum())
    return L, C, S, (x0, x1, y0, y1), raw, sil


def cap_mask(L, C, raw, sil, win, hues=("lav",)):
    x0, x1, y0, y1 = win
    sys.path.insert(0, HERE)
    from measure import with_ink
    ids = [v for v in np.unique(L) if v > 1
           and (L == v).sum() >= MINPX and hue(np.median(C[L == v], 0)) in hues]
    m = np.zeros((RES, RES), bool)
    m[y0:y1, x0:x1] = np.isin(L, ids)
    k7 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, k7).astype(bool)
    f = with_ink(m, raw[..., :3].astype(np.int16), sil)          # 먹선까지가 원화 형태 (79)
    f = cv2.morphologyEx(f.astype(np.uint8), cv2.MORPH_CLOSE,
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))).astype(bool)
    n, lb, st, _ = cv2.connectedComponentsWithStats(f.astype(np.uint8), 8)
    f = lb == (1 + int(np.argmax([st[i, cv2.CC_STAT_AREA] for i in range(1, n)])))
    return cv2.morphologyEx(f.astype(np.uint8), cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))).astype(bool)


def main():
    L, C, S, win, raw, sil = segment()
    ids = [v for v in np.unique(L) if v > 1 and (L == v).sum() >= MINPX]
    kinds = {}
    for v in ids:
        kinds[hue(np.median(C[L == v], 0))] = kinds.get(hue(np.median(C[L == v], 0)), 0) + 1
    print("판 %d개  %s   실루엣 덮임 %.1f%%"
          % (len(ids), kinds, 100 * np.isin(L, ids).sum() / max(S.sum(), 1)))
    if "--check" in sys.argv:
        ref = np.load(os.path.join(HERE, "parts", "artifacts", "_L_alb.npy"))
        rids = [v for v in np.unique(ref) if v > 1 and (ref == v).sum() >= MINPX]
        print("원본 %d판 / 재현 %d판" % (len(rids), len(ids)))
        # 경계 일치율 (라벨 번호는 달라도 되니 경계로 잰다)
        def bnd(X):
            B = np.zeros(X.shape, bool)
            for dy, dx in ((0, 1), (1, 0)):
                a, b = X[:X.shape[0] - dy, :X.shape[1] - dx], X[dy:, dx:]
                B[:X.shape[0] - dy, :X.shape[1] - dx] |= (a > 1) & (b > 1) & (a != b)
            return B
        A_, B_ = bnd(ref), bnd(L)
        k = np.ones((3, 3), np.uint8)
        Ad = cv2.dilate(A_.astype(np.uint8), k).astype(bool)
        Bd = cv2.dilate(B_.astype(np.uint8), k).astype(bool)
        print("경계 화소  원본 %d / 재현 %d   재현이 원본을 %.1f%% 덮고, 원본이 재현을 %.1f%% 덮는다"
              % (A_.sum(), B_.sum(), 100 * (B_ & Ad).sum() / max(B_.sum(), 1),
                 100 * (A_ & Bd).sum() / max(A_.sum(), 1)))
        return
    np.save(os.path.join(HERE, "out", "_L_alb.npy"), L.astype(np.int32))
    cv2.imwrite(os.path.join(HERE, "out", "cap_mask.png"),
                (cap_mask(L, C, raw, sil, win) * 255).astype(np.uint8))
    print("-> out/_L_alb.npy  out/cap_mask.png")


if __name__ == "__main__":
    main()
