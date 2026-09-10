# -*- coding: utf-8 -*-
"""**무기를 부품으로 나눈다.** 날 · 가드 · 자루 · 자루끝.

    python 무기분할.py D:/imggen/weapons/w_front.png 무기부품.json [--bins 48]

## 왜 나누나

한 줄기로 훑으면 **물레 기둥**이 된다. 가드는 길이의 3% 인데 24칸으로 훑으면
한 칸도 못 채우고 뭉개진다. 그리고 가드는 날과 **다른 물건**이라 각이 서야 한다.

원화가 이미 나눠 그려놨다 — **은색 날 · 금색 가드 · 붉은 자루 · 금색 자루끝.**
색이 바뀌는 자리가 부품 경계다. 폭도 같이 본다(가드는 갑자기 넓어진다).

## 어떻게 나누나

축을 따라 48칸으로 잘라 칸마다 **반폭과 색**을 잰다. 그리고 —

    색이 바뀌면      경계 (은 -> 금 -> 붉음)
    폭이 1.6배 뛰면  경계 (가드가 튀어나오는 자리)

이웃한 같은 칸을 묶으면 부품이 된다. 너무 짧은 조각(2칸 미만)은 앞 부품에 붙인다.

## 이름은 순서가 아니라 역할로

처음엔 앞에서부터 날·가드·자루 순으로 붙였더니 **끝 2% 짜리 조각이 「날」**이 됐다.
순서가 아니라 생김새가 역할을 말한다 —

    제일 넓은 조각        가드
    가드 앞에서 제일 긴 것  날 (나머지는 날장식)
    가드 뒤 첫 조각        자루
    가드 뒤 마지막 조각    자루끝
"""
import json
import sys

import numpy as np

sys.path.insert(0, r"G:\art2real\건축3d")
import kinds as K                                             # noqa: E402

cv2 = K.cv2
BINS = 48
WIDTH_JUMP = 1.6           # 이 배수 이상 폭이 뛰면 경계
COLOR_STEP = 0.16          # 색이 이만큼 멀어지면 경계 (0~1 RGB 거리)
NAMES = ["날", "가드", "자루", "자루끝", "부품5", "부품6", "부품7", "부품8"]


def not_bg(im, tol=42):
    c = 24
    corners = np.concatenate([im[:c, :c].reshape(-1, 3), im[:c, -c:].reshape(-1, 3),
                              im[-c:, :c].reshape(-1, 3), im[-c:, -c:].reshape(-1, 3)])
    bg = np.median(corners, axis=0)
    d = np.abs(im.astype(np.int16) - bg[None, None, :]).sum(axis=2)
    m = (d > tol).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k, iterations=2)
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, k, iterations=1)


def bins_of(im, c, nb=BINS):
    """무기 하나 -> 칸마다 (반폭, 색). **먹선은 뺀다** — 얇은 날은 절반이 외곽선이다."""
    fill = np.zeros(im.shape[:2], np.uint8)
    cv2.drawContours(fill, [c], -1, 1, -1)
    ys, xs = np.nonzero(fill)
    if len(xs) < 40:
        return None
    p = np.c_[xs, ys].astype(np.float64)
    ctr = p.mean(axis=0)
    _, _, vt = np.linalg.svd(p - ctr, full_matrices=False)
    q = (p - ctr) @ vt.T
    lo, hi = q[:, 0].min(), q[:, 0].max()
    L = hi - lo
    if L < 1e-6:
        return None
    out = []
    for i in range(nb):
        sel = (q[:, 0] >= lo + L * i / nb) & (q[:, 0] < lo + L * (i + 1) / nb)
        if sel.sum() < 4:
            out.append((0.0, None))
            continue
        hw = float((q[sel, 1].max() - q[sel, 1].min()) / 2.0 / L)
        px = im[ys[sel], xs[sel]].astype(np.float64)
        v = px.max(axis=1)
        keep = px[v >= np.percentile(v, 55)]
        if len(keep) < 3:
            keep = px
        b, g, r = np.median(keep, axis=0)
        out.append((hw, (r / 255.0, g / 255.0, b / 255.0)))
    # **가드에서 먼 쪽이 칼끝이다.** 처음엔 「앞 8칸이 뒤 8칸보다 넓으면 뒤집기」로 했는데
    # 검은 양끝이 다 좁아서 못 가린다 — 자루를 칼끝으로 잡는 일이 생겼다.
    # 제일 넓은 칸(가드)이 앞쪽에 있으면 뒤집는다
    wid = [w for w, _ in out]
    if wid and int(np.argmax(wid)) < len(wid) / 2.0:
        out = out[::-1]
    return out, float(L)


def split(bins):
    """칸 목록 -> 부품 구간. 색이 바뀌거나 폭이 뛰면 자른다."""
    cuts = [0]
    for i in range(1, len(bins)):
        w0, c0 = bins[i - 1]
        w1, c1 = bins[i]
        if c0 is None or c1 is None:
            continue
        dc = max(abs(a - b) for a, b in zip(c0, c1))
        dw = (max(w0, w1) + 1e-6) / (min(w0, w1) + 1e-6)
        if dc > COLOR_STEP or dw > WIDTH_JUMP:
            cuts.append(i)
    cuts.append(len(bins))
    segs = [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)]
    # 2칸 미만은 앞에 붙인다 — 한 칸짜리 조각은 부품이 아니라 잡음이다
    merged = []
    for a, b in segs:
        if merged and b - a < 2:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


def parts_of(bins, L, nb=BINS):
    segs = split(bins)
    rows = []
    for a, b in segs:
        ws = [bins[i][0] for i in range(a, b)]
        cs = [bins[i][1] for i in range(a, b) if bins[i][1]]
        if cs:
            rows.append((a, b, ws, [round(float(v), 4) for v in np.median(np.array(cs), axis=0)]))
    if not rows:
        return []
    gi = int(np.argmax([max(r[2]) for r in rows]))              # 제일 넓은 = 가드
    front = [i for i in range(len(rows)) if i < gi]
    bi = max(front, key=lambda i: rows[i][1] - rows[i][0]) if front else None
    out = []
    for i, (a, b, ws, col) in enumerate(rows):
        if i == gi:
            nm = "가드"
        elif i == bi:
            nm = "날"
        elif i < gi:
            nm = "날장식"
        elif i == len(rows) - 1:
            nm = "자루끝"
        elif i == gi + 1:
            nm = "자루"
        else:
            nm = "자루장식"
        out.append({"이름": nm, "t0": round(a / float(nb), 4), "t1": round(b / float(nb), 4),
                    "반폭": [round(float(w), 5) for w in ws], "색": col})
    return out


def main():
    src, dst = sys.argv[1], sys.argv[2]
    nb = int(sys.argv[sys.argv.index("--bins") + 1]) if "--bins" in sys.argv else BINS
    im = K.imread(src)
    assert im is not None, src
    hgt = 1400
    im = np.ascontiguousarray(cv2.resize(
        im, (int(round(im.shape[1] * hgt / im.shape[0])), hgt), interpolation=cv2.INTER_AREA))
    m = not_bg(im)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    ws = []
    for c in cs:
        if cv2.contourArea(c) < 900 or len(c) < 12:
            continue
        r = bins_of(im, c, nb)
        if r is None or r[1] < hgt * 0.12:
            continue
        bins, L = r
        ws.append({"길이": round(L, 1), "부품": parts_of(bins, L, nb)})
    ws.sort(key=lambda w: -w["길이"])
    json.dump({"src": src, "칸": nb, "자루수": len(ws), "무기": ws},
              open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("SPLIT %d 자루 · 부품 평균 %.1f 개 -> %s"
          % (len(ws), np.mean([len(w["부품"]) for w in ws]), dst))
    for w in ws[:6]:
        print("  길이 %5.0f  " % w["길이"]
              + "  ".join("%s(%.2f~%.2f)" % (p["이름"], p["t0"], p["t1"]) for p in w["부품"]))


def demo():
    """은날 + 금가드 + 붉은자루를 그려, **셋으로 갈리는지** 본다."""
    im = np.full((700, 200, 3), (90, 120, 120), np.uint8)
    cv2.rectangle(im, (94, 60), (106, 430), (240, 240, 240), -1)      # 은날
    cv2.rectangle(im, (70, 430), (130, 452), (40, 200, 240), -1)      # 금가드
    cv2.rectangle(im, (95, 452), (105, 620), (60, 60, 200), -1)       # 붉은자루
    m = not_bg(im)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    bins, L = bins_of(im, c, 48)
    ps = parts_of(bins, L, 48)
    assert len(ps) >= 3, [p["이름"] for p in ps]
    assert ps[0]["색"][0] > 0.8 and ps[0]["색"][2] > 0.8, ps[0]["색"]      # 날은 흰색
    print("무기분할.demo OK  부품 %d 개 %s" % (len(ps), [p["이름"] for p in ps]))


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        main()
