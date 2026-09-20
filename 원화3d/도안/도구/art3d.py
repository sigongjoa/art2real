"""2D 원화에서 3D 정보를 뽑는 세 패스 — 누수방지 분할 · T-접합 가림순서 · 목 검출.

    py -3.11 art3d.py <그림.png> [--out 폴더] [--scale 512]

내보내는 것 (모두 `--out` 아래):
    regions.png   판 색 구분        order.png   가림 순서(밝을수록 앞)
    necks.png     목(하위부품 경계) recon.png   판별 평균색 재구성
    art3d.json    판별 수치 + 지표

세 패스의 근거:
  ① **누수방지 분할** (trapped-ball, Zhang et al.) — 선이 끊겨 있어도 새지 않는다.
     연결성분만 쓰면 선 한 픽셀 끊긴 데서 두 판이 통째로 붙는다.
  ② **T-접합 가림순서** (Entem et al. 2018) — T 자 접합의 **가로대는 가리는 쪽**,
     **세로대는 가려지는 쪽**이다. 판 사이 앞뒤를 그림만으로 알 수 있다.
  ③ **반경 변화** (radial variation) — 한 판 안에서 폭이 잘록해지는 자리는
     하위 부품 경계다. 큰 판을 더 가른다.
"""
import argparse
import json
import math
import pathlib
from collections import deque, defaultdict

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

PAL = [(228, 26, 28), (55, 126, 184), (77, 175, 74), (152, 78, 163), (255, 127, 0),
       (166, 86, 40), (247, 129, 191), (0, 178, 178), (188, 189, 34), (23, 190, 207),
       (140, 86, 75), (227, 119, 194), (127, 127, 127), (44, 160, 44), (214, 39, 40),
       (148, 103, 189), (255, 187, 120), (174, 199, 232), (152, 223, 138), (196, 156, 148)]


# ───────────────────────────────────────────────────────────── 공통
def label(mask):
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32); n = 0
    for i in range(h):
        for j in range(w):
            if mask[i, j] and not lab[i, j]:
                n += 1; q = deque([(i, j)]); lab[i, j] = n
                while q:
                    y, x = q.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                            lab[ny, nx] = n; q.append((ny, nx))
    return lab, n


def _mf(m, k, mx=False):
    im = Image.fromarray((m * 255).astype(np.uint8), "L")
    f = ImageFilter.MaxFilter(k) if mx else ImageFilter.MinFilter(k)
    return np.asarray(im.filter(f)) > 127


def edt(mask):
    """마스크 안쪽 -> 경계까지 거리 (2-pass 체임퍼)."""
    d = np.where(mask, 1e9, 0.0)
    H, W = d.shape
    for i in range(H):
        up = d[i - 1] if i else None
        for j in range(W):
            if d[i, j] == 0:
                continue
            v = d[i, j]
            if j: v = min(v, d[i, j - 1] + 1)
            if up is not None:
                v = min(v, up[j] + 1)
                if j: v = min(v, up[j - 1] + 1.41421)
                if j + 1 < W: v = min(v, up[j + 1] + 1.41421)
            d[i, j] = v
    for i in range(H - 1, -1, -1):
        dn = d[i + 1] if i + 1 < H else None
        for j in range(W - 1, -1, -1):
            if d[i, j] == 0:
                continue
            v = d[i, j]
            if j + 1 < W: v = min(v, d[i, j + 1] + 1)
            if dn is not None:
                v = min(v, dn[j] + 1)
                if j + 1 < W: v = min(v, dn[j + 1] + 1.41421)
                if j: v = min(v, dn[j - 1] + 1.41421)
            d[i, j] = v
    return d


# ────────────────────────────────────────── ① 누수방지 분할 (trapped-ball)
def trapped_ball(free, radii=(6, 4, 2, 1)):
    """큰 공부터 굴려 채운다. 반지름 r 인 공은 폭 2r 보다 좁은 틈을 못 지난다 —
    그래서 **선이 한두 픽셀 끊겨 있어도 옆 판으로 안 샌다.**
    남은 자투리는 마지막에 가장 가까운 라벨로 흡수한다."""
    out = np.zeros(free.shape, np.int32)
    nxt = 1
    for r in radii:
        todo = free & (out == 0)
        core = _mf(todo, 2 * r + 1)
        lc, n = label(core)
        for k in range(1, n + 1):
            m = lc == k
            grown = _mf(m, 2 * r + 1, mx=True) & todo
            if grown.sum() < 12:
                continue
            out[grown & (out == 0)] = nxt
            nxt += 1
    # 자투리 흡수 — 라벨된 곳에서 BFS 로 번져나간다
    H, W = free.shape
    q = deque(zip(*np.where(out > 0)))
    while q:
        y, x = q.popleft()
        v = out[y, x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx_ = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx_ < W and free[ny, nx_] and out[ny, nx_] == 0:
                out[ny, nx_] = v; q.append((ny, nx_))
    return out, nxt - 1


# ────────────────────────────────────────── ② T-접합 가림 순서
def occlusion_order(lab, min_area=200, R=9):
    """T-접합에서 **가로대(연속하는 윤곽)를 가진 판이 앞**이다.

    접합점 둘레 반지름 R 의 고리에서 판별 방향을 재고, 가장 일직선(내적 -1 에 가까운)
    두 가지가 공유하는 판을 가리는 쪽으로 투표한다. 표를 모아 순위를 매긴다.
    """
    H, W = lab.shape
    big = {k for k in np.unique(lab) if k > 0 and (lab == k).sum() >= min_area}
    lab = np.where(np.isin(lab, list(big)), lab, 0)
    # **판 사이에는 선 띠가 있어 라벨이 서로 안 닿는다** — 그대로 3x3 을 보면
    # 접합이 0개다(실측). 선 자리를 가장 가까운 라벨로 메운 뒤 접합을 찾는다.
    grown = lab.copy()
    inside = grown > 0
    q = deque(zip(*np.where(inside)))
    steps = 0
    while q and steps < 4_000_000:
        y, x = q.popleft(); steps += 1
        v = grown[y, x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx_ = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx_ < W and grown[ny, nx_] == 0:
                grown[ny, nx_] = v; q.append((ny, nx_))
    lab = grown
    junc = np.zeros((H, W), bool)
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            s = {int(v) for v in lab[y - 1:y + 2, x - 1:x + 2].ravel() if v in big}
            if len(s) >= 3:
                junc[y, x] = True
    jl, jn = label(junc)
    votes = defaultdict(int)
    used = 0
    yy, xx = np.mgrid[0:H, 0:W]
    for k in range(1, jn + 1):
        py, px = np.where(jl == k)
        cy, cx = py.mean(), px.mean()
        ring = (np.abs(np.hypot(yy - cy, xx - cx) - R) < 1.6)
        ids = [int(v) for v in np.unique(lab[ring]) if v in big]
        if len(ids) != 3:
            continue
        # 각 판의 고리 위 방향(각도 평균)
        ang = {}
        for i in ids:
            m = ring & (lab == i)
            if m.sum() < 3:
                break
            ang[i] = np.arctan2((yy[m] - cy).mean(), (xx[m] - cx).mean())
        if len(ang) != 3:
            continue
        # 세 판 사이 경계 방향 = 이웃한 두 판 각도의 중간
        order = sorted(ang, key=lambda i: ang[i])
        br = {}
        for a, b in ((0, 1), (1, 2), (2, 0)):
            i, j = order[a], order[b]
            d = (ang[i] + ang[j]) / 2
            if abs(ang[i] - ang[j]) > np.pi:
                d += np.pi
            br[frozenset((i, j))] = d
        keys = list(br)
        best, pair = 2.0, None
        for a in range(3):
            for b in range(a + 1, 3):
                v = abs(np.cos(br[keys[a]] - br[keys[b]]) + 1)   # 0 이면 일직선
                if v < best:
                    best, pair = v, (keys[a], keys[b])
        if pair is None or best > 0.35:
            continue
        shared = set(pair[0]) & set(pair[1])
        if len(shared) != 1:
            continue
        front = shared.pop()
        for other in ids:
            if other != front:
                votes[(front, other)] += 1
        used += 1
    score = defaultdict(int)
    for (f, b), v in votes.items():
        score[f] += v; score[b] -= v
    return dict(score), used, len(big)


# ────────────────────────────────────────── 부품 윤곽 폴리곤
_M8 = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]


def trace(mask):
    """**무어 이웃 윤곽 추적.** 경계 픽셀을 실제로 따라 걷는다.

    이전에는 행마다 좌우 끝을 잡았는데, 그러면 오목한 윤곽을 **현으로 가로질러**
    원본에 없는 경계를 만든다 (실측: 우리 경계의 29% 가 아무 선 위에도 없었다).
    추적은 오목·U자를 그대로 따라가므로 중심선에서 자를 필요도 없다.
    """
    ys, xs = np.where(mask)
    if not len(ys):
        return []
    sy, sx = int(ys[0]), int(xs[ys == ys[0]].min())
    H, W = mask.shape
    out = [(sx, sy)]
    b = 7                                   # 되짚어 온 방향 (좌측에서 시작)
    cy, cx = sy, sx
    for _ in range(200000):
        found = False
        for t in range(8):
            k = (b + 1 + t) % 8
            dy, dx = _M8[k]
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < H and 0 <= nx < W and mask[ny, nx]:
                b = (k + 4) % 8             # 새 위치에서 이전 픽셀을 가리키는 방향
                cy, cx = ny, nx
                out.append((cx, cy))
                found = True
                break
        if not found:
            break
        if (cx, cy) == (sx, sy) and len(out) > 2:
            break
    return out


def rdp(pts, eps):
    """램머-더글러스-포이커. 점을 줄이되 **형태를 eps px 안에서 지킨다.**"""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        x0, y0 = pts[i]; x1, y1 = pts[j]
        dx, dy = x1 - x0, y1 - y0
        L = (dx * dx + dy * dy) ** 0.5 or 1.0
        best, bi = -1.0, None
        for m in range(i + 1, j):
            x, y = pts[m]
            d = abs(dy * (x - x0) - dx * (y - y0)) / L
            if d > best:
                best, bi = d, m
        if best > eps:
            keep[bi] = True
            stack += [(i, bi), (bi, j)]
    return [p for p, k in zip(pts, keep) if k]


def rdp_closed(pts, eps):
    """닫힌 윤곽용 RDP. 그냥 rdp 를 걸면 **시작=끝이라 기준선 길이가 0** 이 되어
    모든 점이 버려진다(실측: 사각형이 2점으로 줄었다). 가장 먼 점에서 두 조각으로
    갈라 각각 단순화한 뒤 잇는다."""
    if len(pts) < 4:
        return pts
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    x0, y0 = pts[0]
    far = max(range(len(pts)), key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
    a = rdp(pts[:far + 1], eps)
    b = rdp(pts[far:] + [pts[0]], eps)
    return a[:-1] + b[:-1]


def poly_of(lab, k, cx=None, eps=1.5, min_part=60):
    """판의 윤곽을 (x,y) 폴리곤 목록으로 (px). 조각(연결성분)마다 하나씩."""
    sub, ns = label(lab == k)
    out = []
    for t in range(1, ns + 1):
        m = sub == t
        if m.sum() < min_part:
            continue
        # **허용오차는 조각 크기에 비례해야 한다.** 고정 1.0px 을 41px 짜리 조각에
        # 걸면 면적이 2.4배 부푼다 — 부품 검증에서 실측(작은 부품 비 1.56 / 큰 부품 1.16).
        # 큰 판(약 800px, sqrt≈28)에서 eps 를 그대로 쓰도록 28 로 정규화한다.
        e = min(eps, max(0.3, eps * math.sqrt(m.sum()) / 28.0))
        c = rdp_closed(trace(m), e)
        if len(c) >= 3:
            out.append([[int(x), int(y)] for x, y in c])
    return out


# ────────────────────────────────────────── ③ 반경 변화 (목 검출)
def necks(lab, k, min_area=400, bins=40, drop=0.62):
    """판의 주축을 따라 반경(거리변환 최대)이 잘록해지는 자리 = 하위부품 경계."""
    m = lab == k
    if m.sum() < min_area:
        return []
    d = edt(m)
    ys, xs = np.where(m)
    p = np.stack([xs - xs.mean(), ys - ys.mean()], 1).astype(float)
    u, s, vt = np.linalg.svd(p - p.mean(0), full_matrices=False)
    ax = vt[0]
    t = p @ ax
    lo, hi = t.min(), t.max()
    if hi - lo < 12:
        return []
    idx = np.clip(((t - lo) / (hi - lo) * (bins - 1)).astype(int), 0, bins - 1)
    prof = np.zeros(bins)
    dv = d[ys, xs]
    for i in range(bins):
        sel = idx == i
        prof[i] = dv[sel].max() if sel.any() else 0
    out = []
    for i in range(3, bins - 3):
        left, right = prof[:i].max(), prof[i + 1:].max()
        if prof[i] > 0 and prof[i] < drop * min(left, right):
            out.append(round(float(lo + (hi - lo) * i / (bins - 1)), 2))
    # 이웃한 후보는 하나로
    merged = []
    for v in out:
        if not merged or v - merged[-1] > (hi - lo) / bins * 3:
            merged.append(v)
    return merged


# ───────────────────────────────────────────────────────────── 본체
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", default=None)
    ap.add_argument("--scale", type=int, default=512, help="긴 변 픽셀. 라벨링이 순수 파이썬이라 512 권장")
    ap.add_argument("--line", type=int, default=105)
    ap.add_argument("--tones", type=int, default=7)
    ap.add_argument("--min-area", type=int, default=40)   # IoU 스윕으로 고른 값
    ap.add_argument("--grow", type=int, default=0,
                    help="선 띠로 번지는 거리(px). 0 이 맞다 — GT 고정 후 0/1/2/3 을 "
                         "쓸어 IoU 0.867/0.848/0.801/0.770 로 단조 감소했다. "
                         "검은 선은 패널 사이 홈이고 밝은 영역이 부품이다")
    ap.add_argument("--merge", type=float, default=8.0,    # IoU 스윕으로 고른 값
                    help="인접 판 평균색 차가 이보다 작으면 합친다(0=끄기)")
    ap.add_argument("--rdp", type=float, default=1.0,   # IoU 스윕으로 고른 값
                    help="윤곽 단순화 허용오차(px). 작을수록 원본 선을 그대로 따라간다")
    a = ap.parse_args()
    src = pathlib.Path(a.src)
    out = pathlib.Path(a.out or src.parent / (src.stem + "_art3d"))
    out.mkdir(parents=True, exist_ok=True)

    im = Image.open(src).convert("RGB")
    if max(im.size) != a.scale:
        k = a.scale / max(im.size)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    # **양자화 전에 중앙값 필터.** 안 하면 안티에일리어싱이 판을 수만 개로 부순다
    imf = im.filter(ImageFilter.MedianFilter(5))
    arr = np.asarray(imf).astype(float)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    lum = arr.mean(2)
    bg = (r > 240) & (g > 240) & (b > 240)
    line = (lum < a.line) & ~bg
    thin = line & ~_mf(line, 9)            # 얇은 것만 '선', 두꺼운 검정은 '검은 판'
    free = ~bg & ~thin

    # ① 누수방지 분할 -> 그 안에서 톤 클래스로 다시 나눔
    tb, ntb = trapped_ball(free)
    hue = np.where(bg, -1, np.where((r - b > 40) & (r > 130), 1,
                                    np.where(b - r > 12, 2, 0)))
    tone = np.clip((lum / 256 * a.tones).astype(int), 0, a.tones - 1)
    key = (tb.astype(np.int64) * 100 + hue * a.tones + tone)
    key[~free] = -999
    lab, n = label_by_key(key)

    # **양자화가 만든 가짜 경계를 지운다.** 밝기를 균등 7단으로 자르면 부드러운
    # 그라데이션(밝은금/어두운금, 검은 눈 안의 회색) 한가운데서도 판이 갈린다.
    # 원본엔 선도 톤 계단도 없는 자리라 조립하면 **없는 분할선**이 생긴다.
    # 인접 판의 평균색 차이가 작으면 합친다.
    if a.merge > 0:
        mean = {}
        for k in range(1, n + 1):
            m = lab == k
            if m.sum():
                mean[k] = arr[m].mean(0)
        par = list(range(n + 1))

        def find(x):
            while par[x] != x:
                par[x] = par[par[x]]; x = par[x]
            return x
        adj = set()
        d1 = lab[:, :-1]; d2 = lab[:, 1:]
        for u, v in zip(d1[(d1 != d2) & (d1 > 0) & (d2 > 0)].ravel(),
                        d2[(d1 != d2) & (d1 > 0) & (d2 > 0)].ravel()):
            adj.add((min(u, v), max(u, v)))
        e1 = lab[:-1]; e2 = lab[1:]
        for u, v in zip(e1[(e1 != e2) & (e1 > 0) & (e2 > 0)].ravel(),
                        e2[(e1 != e2) & (e1 > 0) & (e2 > 0)].ravel()):
            adj.add((min(u, v), max(u, v)))
        merged = 0
        for u, v in sorted(adj):
            if u not in mean or v not in mean:
                continue
            if np.abs(mean[u] - mean[v]).mean() < a.merge and find(u) != find(v):
                par[find(u)] = find(v); merged += 1
        if merged:
            remap = np.zeros(n + 1, np.int32)
            for k in range(1, n + 1):
                remap[k] = find(k)
            lab = remap[lab]
            print(f"색이 비슷한 인접 판 {merged}쌍 병합 (임계 {a.merge})")

    keep = [k for k in np.unique(lab) if k > 0 and (lab == k).sum() >= a.min_area]

    # **선 띠 가운데까지 라벨을 키운다.** 안 키우면 우리 윤곽이 선의 *안쪽*을 따라가고,
    # 이웃 판은 반대쪽 안쪽을 따라가서 **선 하나에 경계가 둘** 생긴다 (실측: 빨간 이중선).
    # 키우면 이웃끼리 선 중심에서 만나 경계가 하나가 된다.
    lab_g = np.where(np.isin(lab, keep), lab, 0)
    H0, W0 = lab_g.shape
    # **선 띠만큼만 번진다.** 무한히 번지면 버려진 작은 판까지 통째로 흡수해
    # 그 옆 부품이 원화의 2~3배가 된다 (부품 검증에서 실측: 비 2.92/2.31).
    # 선 띠는 보통 2~4px 이므로 그 절반씩 양쪽에서 만나면 충분하다.
    q = deque((y, x, 0) for y, x in zip(*np.where(lab_g > 0)))
    grow_ok = ~bg
    while q:
        y, x, d = q.popleft()
        if d >= a.grow:
            continue
        v = lab_g[y, x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H0 and 0 <= nx < W0 and grow_ok[ny, nx] and lab_g[ny, nx] == 0:
                lab_g[ny, nx] = v
                q.append((ny, nx, d + 1))
    print(f"누수방지 분할 {ntb}개 -> 톤 분할 {n}개 -> 유효 {len(keep)}개")

    # 재구성 오차 (분할이 음영 경계를 가로지르는지)
    recon = arr.copy(); stds = {}
    for k in keep:
        m = lab == k
        recon[m] = arr[m].mean(0)
        stds[k] = float(arr[m].std(0).mean())
    seg = np.isin(lab, keep)
    err = np.abs(arr - recon).mean(2)
    rec_err = float(err[seg].mean())
    print(f"재구성 오차 {rec_err:.1f}/255  (5 이하면 분할이 음영과 일치)")

    # ② 가림 순서
    sc, nj, nreg = occlusion_order(np.where(np.isin(lab, keep), lab, 0))
    print(f"T-접합 {nj}개에서 순서 투표 · 판 {nreg}개")

    # ③ 목 검출
    nk = {k: necks(lab, k) for k in keep}
    nn = sum(len(v) for v in nk.values())
    print(f"목(하위부품 경계) 후보 {nn}개")

    # ── 출력 이미지
    H, W = lum.shape
    tint = np.zeros_like(arr)
    for i, k in enumerate(keep):
        tint[lab == k] = PAL[i % len(PAL)]
    save(out / "regions.png", np.where(seg[..., None], arr * .3 + tint * .7, arr))
    save(out / "recon.png", recon)
    if sc:
        lo, hi = min(sc.values()), max(sc.values())
        o = np.zeros((H, W))
        for k in keep:
            o[lab == k] = (sc.get(k, 0) - lo) / max(1, hi - lo)
        save(out / "order.png", np.where(seg[..., None], (o[..., None] * 235 + 20) * np.ones(3), 255))
    nv = arr.copy()
    for k, vs in nk.items():
        if not vs:
            continue
        nv[_mf(lab == k, 3) & ~(lab == k)] = (255, 0, 0)
    save(out / "necks.png", nv)

    # 전경 실루엣의 행별 좌우 끝 — 설계도에서 **px->월드 스케일을 자동으로 맞출 때** 쓴다.
    # **금색·청색을 뺀다.** 안 빼면 뿔·견갑이 폭을 부풀려 맞춤이 통째로 틀어진다
    # (실측: 안 뺐더니 이미지 전체가 헬멧 높이에 매핑됐다)
    fgm = ~bg & ~((r - b > 40) & (r > 130)) & ~(b - r > 12)
    rows_px = {}
    for y in range(H):
        xs = np.where(fgm[y])[0]
        if len(xs):
            rows_px[int(y)] = [int(xs.min()), int(xs.max())]
    cxg = float(np.mean([(v[0] + v[1]) / 2 for v in rows_px.values()]))

    js = {"src": src.name, "size": [W, H],
          "silhouette_rows_px": rows_px, "center_x_px": round(cxg, 1),
          "metrics": {"regions": len(keep), "recon_error": round(rec_err, 2),
                      "junctions_used": nj, "neck_candidates": nn},
          "regions": []}
    for k in keep:
        ys, xs = np.where(lab == k)
        js["regions"].append({
            "id": int(k), "area": int(len(ys)),
            "x": [int(xs.min()), int(xs.max())], "y": [int(ys.min()), int(ys.max())],
            "rgb": [int(v) for v in arr[lab == k].mean(0)],
            "color_std": round(stds[k], 1),
            "depth_score": int(sc.get(k, 0)), "necks": nk[k],
            "poly_px": poly_of(lab_g, k, eps=a.rdp)})
    js["regions"].sort(key=lambda d: -d["area"])
    # 라벨맵과 머리 마스크를 남긴다 — `depth.py` 가 여기서 깊이를 만든다
    # **`labels.npy` 는 GT 다 — 원화에 그려진 그대로. 절대 모델 쪽으로 옮기지 않는다.**
    # 번진 라벨을 여기에 저장하면 손실을 줄인 게 아니라 손실의 정의를 바꾼 것이다.
    np.save(out / "labels.npy", np.where(np.isin(lab, keep), lab, 0))
    np.save(out / "labels_grown.npy", lab_g)     # 윤곽 추적용 (GT 아님)
    np.save(out / "mask.npy", (~bg))
    (out / "art3d.json").write_text(json.dumps(js, ensure_ascii=False, indent=1), "utf-8")
    print(f"\n{out}")


def label_by_key(key):
    h, w = key.shape
    lab = np.zeros((h, w), np.int32); n = 0
    for i in range(h):
        for j in range(w):
            if key[i, j] != -999 and not lab[i, j]:
                n += 1; v = key[i, j]; q = deque([(i, j)]); lab[i, j] = n
                while q:
                    y, x = q.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and key[ny, nx] == v \
                                and not lab[ny, nx]:
                            lab[ny, nx] = n; q.append((ny, nx))
    return lab, n


def save(p, arr):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(p)


if __name__ == "__main__":
    main()
