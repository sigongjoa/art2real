"""**부품을 뽑은 그 이미지에서 외형을 뽑는다.** 그래야 맞출 게 없다.

    py -3.11 envelope.py <그림.png> --z 0.866 0.948 [--out envelope.json] [--scale 448]

왜: 외형을 다른 그림(전신 시트)에서 뽑고 부품을 이 그림(얼굴 클로즈업)에서 뽑으면
**두 그림을 맞춰야** 하고, 그 맞춤이 계속 틀렸다 — 최소제곱은 어깨에 끌려 33%,
특징점 2개는 뿔 윤곽에 걸려 5091% 오차가 났다. **같은 그림에서 뽑으면 맞출 게 없다.**

실루엣은 **연결성 추적**으로 뽑는다. 색으로는 못 가른다 — 목 보호대가 투구와 같은
흰색이라 색 필터를 다 빠져나간다(LESSON 61). 씨앗은 **제일 큰 검은 판(눈)** 이고,
거기서 위아래로 **이전 행과 제일 많이 겹치는 run** 을 따라간다 (LESSON 82).

z 범위 두 개만 사람이 준다 — 그게 이 그림과 몸 전체를 잇는 유일한 절대값이다.
"""
import argparse
import json
import pathlib
from collections import deque

import numpy as np
from PIL import Image, ImageFilter


def runs(row, minlen=4):
    out, s = [], None
    for i, v in enumerate(row):
        if v and s is None:
            s = i
        elif not v and s is not None:
            out.append((s, i - 1)); s = None
    if s is not None:
        out.append((s, len(row) - 1))
    return [r for r in out if r[1] - r[0] >= minlen]


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
                        if 0 <= ny < h and 0 <= nx < w and key[ny, nx] == v                                 and not lab[ny, nx]:
                            lab[ny, nx] = n; q.append((ny, nx))
    return lab, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--z", nargs=2, type=float, required=True,
                    metavar=("Z_BOT", "Z_TOP"), help="이 부품 묶음의 절대 z 범위")
    ap.add_argument("--out", default=None)
    ap.add_argument("--scale", type=int, default=448)
    ap.add_argument("--rows", type=int, default=14, help="외형 행 수")
    ap.add_argument("--depth-out", default=None,
                    help="깊이 프로필 [z, y_앞, y_뒤] 를 낸다. 행마다 가장 큰 덩어리만 "
                         "쓴다 — min~max 로 하면 볏과 두개골 사이 오목한 자리를 몸통이 "
                         "메워 회전체가 통째로 부푼다(실측: 측면 과함 55%)")
    ap.add_argument("--anchor-halfwidth", type=float, default=None,
                    help="최대 반폭을 이 값에 맞춘다(폭 앵커). z 범위는 이 그림의 "
                         "비례에서 따라온다 — 두 그림의 머리 비율이 다를 때 이걸 쓴다")
    a = ap.parse_args()
    src = pathlib.Path(a.src)
    im = Image.open(src).convert("RGB")
    if max(im.size) != a.scale:
        k = a.scale / max(im.size)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    imf = im.filter(ImageFilter.MedianFilter(5))
    arr = np.asarray(imf).astype(int)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    lum = arr.mean(2)
    H, W = lum.shape
    bg = (r > 240) & (g > 240) & (b > 240)
    red = (r > 110) & (r - g > 45) & (r - b > 45)     # 망토
    sil = ~bg & ~red

    # ── 투구 = **판의 합집합**. 실루엣으로는 목·어깨가 안 갈린다(붙어 있어서).
    # 눈(제일 큰 검은 판)에서 시작해 **밝은 판으로만** 번진다. 검은 목이 벽이 되어
    # 자동으로 멈춘다 — 참조가 원래 그렇게 그려져 있다.
    hue = np.where(bg, -1, np.where((r - b > 40) & (r > 130), 1,
                                    np.where(b - r > 12, 2, 0)))
    tone = np.clip((lum / 256 * 7).astype(int), 0, 6)
    cls = hue * 7 + tone
    cls[bg | red] = -999
    plab, pn = label_by_key(cls)
    info = {}
    for k in range(1, pn + 1):
        m = plab == k
        c = int(m.sum())
        if c < 60:
            continue
        ys_, xs_ = np.where(m)
        info[k] = {"n": c, "dark": bool(lum[m].mean() < 105),
                   # **hue 는 0=흰/검, 1=금, 2=청회 다.** `mean()>0.5` 로 쓰면
                   # 청회(2)까지 금색으로 잡혀 헬멧 판이 통째로 차단된다(실측: keep 8개).
                   "gold": bool(round(float(np.median(hue[m]))) == 1),
                   "cy": float(ys_.mean()), "cx": float(xs_.mean())}
    seed = None; best = 0
    for k, v in info.items():
        if v["dark"] and v["cy"] < H * 0.6 and v["n"] > best:
            best, seed = v["n"], k
    assert seed is not None, "씨앗(눈)을 못 찾았다"

    # **선화는 벽이 아니라 이음매다.** 검은 선 전체가 하나의 거대한 어두운 영역이라
    # "큰 검은 판 = 목" 규칙이 **선 네트워크 전체를 막아버렸다** — 그래서 번지기가
    # 눈 주변에서 멈췄다(위쪽에 판이 16개나 있는데 못 갔다).
    # 선 자리를 가장 가까운 판으로 메운 뒤 인접을 만든다 (art3d 의 T-접합과 같은 처리).
    thin = np.zeros_like(bg)
    dk = (lum < 105) & ~bg
    dmm = Image.fromarray((dk * 255).astype(np.uint8), "L")
    thickd = np.asarray(dmm.filter(ImageFilter.MinFilter(9))) > 127
    thin = dk & ~thickd
    gl = np.where(thin, 0, plab)
    q0 = deque(zip(*np.where(gl > 0)))
    while q0:
        y, x = q0.popleft()
        v = gl[y, x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and thin[ny, nx] and gl[ny, nx] == 0:
                gl[ny, nx] = v; q0.append((ny, nx))
    plab_adj = gl

    # 인접 그래프
    adj = {}
    for A, B in ((plab_adj[:, :-1], plab_adj[:, 1:]), (plab_adj[:-1], plab_adj[1:])):
        d = (A != B) & (A > 0) & (B > 0)
        for u, v in zip(A[d].ravel(), B[d].ravel()):
            adj.setdefault(int(u), set()).add(int(v))
            adj.setdefault(int(v), set()).add(int(u))

    keep = {seed}
    q = deque([seed])
    while q:
        u = q.popleft()
        for v in adj.get(u, ()):
            if v in keep or v not in info:
                continue
            if info[v]["dark"] and info[v]["n"] > info[seed]["n"] * 1.4:
                continue                      # 큰 검은 판 = 목. 벽이다
            # **금색 뿔은 외형이 아니다.** 뻗어나가는 날이라 넣으면 위로 갈수록
            # 외형이 넓어진다(실측: z0.942 반폭 0.058 로 돔보다 넓게 나왔다).
            # 뿔은 `blade` 부품으로 따로 만든다
            if info[v]["gold"]:
                continue
            keep.add(v); q.append(v)
    helm = np.isin(plab, list(keep))
    # **아래쪽 큰 검은 판(목)의 윗행 아래는 투구가 아니다.** 판 그래프만으로는 어깨가
    # 어딘가에서 이어져 딸려온다(실측: 44/62 판, 이미지 바닥까지). 목이 자연 경계다.
    neck, nb = None, 0
    for k, v in info.items():
        if v["dark"] and v["cy"] > H * 0.55 and v["n"] > nb:
            nb, neck = v["n"], k
    if neck is not None:
        ytopn = int(np.where(plab == neck)[0].min())
        helm[ytopn:] = False
        print(f"목 판 {neck} 윗행 y={ytopn} 아래를 잘랐다")
    keep = {k for k in keep if (plab == k)[helm].any()}
    print(f"투구 판 {len(keep)}개 / 전체 {len(info)} · 픽셀 {int(helm.sum())}")

    prof = {}
    for y in range(H):
        xs_ = np.where(helm[y])[0]
        if len(xs_):
            prof[y] = (int(xs_.min()), int(xs_.max()))
    ys = sorted(prof)
    ytop, ybot = ys[0], ys[-1]
    zb, zt = a.z
    if a.anchor_halfwidth:
        # **폭으로 앵커.** 참조 두 장의 머리 비율이 다르면(생성본은 원본과 비례가
        # 다르다) 높이로 맞추는 순간 폭이 틀어진다 — 실측 세로/가로 0.85 vs 확정 1.32.
        # 부품을 이 그림에서 뽑았으므로 **모양의 기준은 이 그림**이다. 높이는 따라온다.
        hw_px = max((prof[y][1] - prof[y][0]) / 2 for y in ys)
        kk = a.anchor_halfwidth / hw_px
        zt = zb + (ybot - ytop) * kk
        print(f"폭 앵커: 최대 반폭 {hw_px:.1f}px -> {a.anchor_halfwidth} · "
              f"z 범위가 {zb:.3f}~{zt:.3f} 로 따라옴")
    else:
        kk = (zt - zb) / (ybot - ytop)
    cx = float(np.median([(prof[y][0] + prof[y][1]) / 2 for y in ys]))
    rows = []
    for i in range(a.rows + 1):
        y = int(round(ytop + (ybot - ytop) * i / a.rows))
        if y not in prof:
            continue
        z = zt - (y - ytop) * kk
        rows.append([round(z, 4), round((prof[y][1] - prof[y][0]) / 2 * kk, 4)])
    rows.sort()
    if a.depth_out:
        # **행마다 가장 큰 run.** 회전체는 행마다 볼록한 모양만 만들 수 있으므로
        # 몸통은 제일 큰 덩어리다. 볏·뿔은 따로 만들 것이지 몸통에 먹이지 않는다.
        drows = []
        for i in range(a.rows + 1):
            y = int(round(ytop + (ybot - ytop) * i / a.rows))
            xs_ = np.where(helm[y])[0] if 0 <= y < H else []
            if not len(xs_):
                continue
            rr = runs(helm[y], minlen=2)
            if not rr:
                continue
            b = max(rr, key=lambda r: r[1] - r[0])
            z = zt - (y - ytop) * kk
            drows.append([round(z, 4), round((b[0] - cx) * kk, 4),
                          round((b[1] - cx) * kk, 4)])
        drows.sort()
        json.dump({"src": f"measured({src.name} 행별 최대 run — 볏/뿔 제외)",
                   "px": {"y_top": ytop, "y_bot": ybot, "center_x": round(cx, 1),
                          "world_per_px": round(kk, 6), "scale": a.scale},
                   "rows": [{"z": r[0], "y_front": r[1], "y_back": r[2]} for r in drows]},
                  open(a.depth_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        wid = [r[2] - r[1] for r in drows]
        print(f"깊이 프로필 {len(drows)}행 -> {a.depth_out} · 깊이 폭 "
              f"{min(wid):.4f}~{max(wid):.4f}")

    out = pathlib.Path(a.out or src.parent / (src.stem + "_envelope.json"))
    # **추적한 마스크를 저장한다.** 이게 GT 다 — 하류가 배경 임계값 같은 다른 방법으로
    # 실루엣을 다시 만들면 같은 그림에서 GT 가 둘이 되고 비교가 성립하지 않는다.
    np.save(out.with_suffix(".mask.npy"), helm)
    json.dump({"src": f"measured({src.name} 연결성 추적)",
               "px": {"y_top": ytop, "y_bot": ybot, "center_x": round(cx, 1),
                      "world_per_px": round(kk, 6), "scale": a.scale},
               "rows": rows},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"추적 행 {len(ys)} (y {ytop}~{ybot}) · 월드/px {kk:.6f} · 중심 x {cx:.1f}")
    print("   z      반폭")
    for z, hwv in rows:
        print(f"  {z:.3f}   {hwv:.4f}")
    print(out)


if __name__ == "__main__":
    main()
