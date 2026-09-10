# -*- coding: utf-8 -*-
"""**앞모습과 옆모습을 같이 재서 단면까지 뽑는다.**

    python 무기재기2.py D:/imggen/weapons/w_front.png D:/imggen/weapons/w_side.png 무기2.json

## 1차와 뭐가 다른가

1차(`무기재기.py`)는 `r5_up_hero` 로 쟀는데 그건 **검이 카메라로 쏟아지는 원근 컷**이라,
카메라를 향한 날이 짧고 뚱뚱하게 찍혀 **병 모양**이 나왔다. 세장비 1.0~9.9 는
무기의 성질이 아니라 「그 무기가 카메라를 얼마나 향했나」였다.
`LESSONS`(원근 컷에서 길이 쓰지 않기) 에 적혀 있던 실수를 그대로 했다.

여기서는 원근 없는 판 둘을 쓴다 —

    앞모습   반폭 프로필 (검이 얼마나 넓나)
    옆모습   **두께 프로필** (검이 얼마나 얇나)

둘을 곱하면 **단면**이 나온다. 1차에서 `guessed` 였던 두께 0.22 와 마름모 단면이
여기서 `measured` 가 된다. **그게 검과 둔기를 가르는 값이다** — 검은 납작하고 둔기는 굵다.

## 마스크가 바뀐다

1차는 금색을 잡았는데 이 판의 무기는 **흰색/은색이고 자루만 금**이다.
배경이 단색이라 **「배경이 아닌 것」**으로 잡는다 — 네 귀퉁이 색의 중앙값을 배경으로 본다.
"""
import json
import sys

import numpy as np

sys.path.insert(0, r"G:\art2real\건축3d")
import kinds as K                                             # noqa: E402

cv2 = K.cv2
N_BIN = 24


def not_bg(im, tol=42):
    """**배경이 아닌 것.** 네 귀퉁이 색의 중앙값을 배경으로 보고 그것과 먼 화소를 남긴다."""
    h, w = im.shape[:2]
    c = 24
    corners = np.concatenate([im[:c, :c].reshape(-1, 3), im[:c, -c:].reshape(-1, 3),
                              im[-c:, :c].reshape(-1, 3), im[-c:, -c:].reshape(-1, 3)])
    bg = np.median(corners, axis=0)
    d = np.abs(im.astype(np.int16) - bg[None, None, :]).sum(axis=2)
    m = (d > tol).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k, iterations=2)
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, k, iterations=1)


def shapes(path, hgt=1400, min_area=900.0):
    """판에서 무기를 하나씩 뽑아 (반폭 프로필, 화면 길이) 로 돌려준다."""
    im = K.imread(path)
    assert im is not None, path
    im = np.ascontiguousarray(
        cv2.resize(im, (int(round(im.shape[1] * hgt / im.shape[0])), hgt),
                   interpolation=cv2.INTER_AREA))
    m = not_bg(im)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = []
    for c in cs:
        if cv2.contourArea(c) < min_area or len(c) < 12:
            continue
        p = c.reshape(-1, 2).astype(np.float64)
        p -= p.mean(axis=0)
        _, _, vt = np.linalg.svd(p, full_matrices=False)
        q = p @ vt.T
        lo, hi = q[:, 0].min(), q[:, 0].max()
        L = hi - lo
        if L < hgt * 0.12:                       # 무기는 길다. 짧으면 부스러기다
            continue
        prof = []
        for i in range(N_BIN):
            a = lo + L * i / N_BIN
            b = lo + L * (i + 1) / N_BIN
            w = q[(q[:, 0] >= a) & (q[:, 0] < b), 1]
            prof.append(0.0 if len(w) == 0 else float((w.max() - w.min()) / 2.0 / L))
        if sum(prof[:6]) < sum(prof[-6:]):       # 뾰족한 쪽을 앞으로
            prof = prof[::-1]
        # **색도 잰다.** 원화가 이미 은날·금가드·붉은자루로 갈라놨으니 지어낼 필요가 없다.
        # 축을 따라 위 6할이 날, 아래 4할이 자루다
        fill = np.zeros(m.shape, np.uint8)
        cv2.drawContours(fill, [c], -1, 1, -1)
        ys, xs = np.nonzero(fill)
        pp = (np.c_[xs, ys].astype(np.float64) - np.c_[xs, ys].mean(axis=0)) @ vt.T
        t = (pp[:, 0] - lo) / max(L, 1e-6)
        def med(sel):
            # **먹선을 걷어낸다.** 날이 얇아 화소의 절반이 외곽선이라, 그냥 중앙값을 내면
            # 은색 날이 진갈색으로 나온다 (처음에 그렇게 나왔다). 어두운 쪽 55% 를 버린다
            if sel.sum() < 20:
                return None
            px = im[ys[sel], xs[sel]].astype(np.float64)
            v = px.max(axis=1)
            keep = px[v >= np.percentile(v, 55)]
            if len(keep) < 5:
                keep = px
            b, g, r = np.median(keep, axis=0)
            return [round(r / 255.0, 4), round(g / 255.0, 4), round(b / 255.0, 4)]
        blade = med(t < 0.6)
        hilt = med(t >= 0.6)
        out.append({"반폭": [round(v, 5) for v in prof], "길이": round(float(L), 1),
                    "날색": blade, "자루색": hilt})
    out.sort(key=lambda r: -r["길이"])
    return out, m


def main():
    front, side, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    fw, fm = shapes(front)
    sw, sm = shapes(side)
    K.imwrite(dst.replace(".json", "_front_mask.png"), fm * 255)
    K.imwrite(dst.replace(".json", "_side_mask.png"), sm * 255)

    # 두께 — 옆모습 무기들의 반폭 중앙값. **날 부분(위 6할)만** 본다. 가드는 튀어나온다
    def blade_part(prof):
        return prof[:int(len(prof) * 0.6)]
    sv = sorted(np.median(blade_part(r["반폭"])) for r in sw)
    wd = float(np.median([np.median(blade_part(r["반폭"])) for r in fw])) if fw else None
    # **판이 반만 옆모습이다.** 0.0105~0.0362 로 3.4배 벌어졌다 — 어떤 건 날을 눕혀 그렸다.
    # 제일 얇은 것이 진짜 날세운 것이므로 그걸 쓰고, 중앙값도 같이 적어 의심을 남긴다
    ratio = (float(sv[0]) / wd) if (sv and wd) else None
    ratio_med = (float(np.median(sv)) / wd) if (sv and wd) else None

    out = {"front": front, "side": side,
           "앞모습": {"자루수": len(fw), "무기": fw},
           "옆모습": {"자루수": len(sw), "무기": sw},
           "두께비": {"v": round(ratio, 4) if ratio else None,
                      "중앙값판": round(ratio_med, 4) if ratio_med else None,
                      "src": "measured(제일 얇은 옆모습 / 앞모습 중앙값) — "
                             "판이 반만 옆모습이라 중앙값을 쓰면 0.65 로 과대"}}
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("MEASURE2 앞 %d 자루 · 옆 %d 자루 · **두께비 %s** -> %s"
          % (len(fw), len(sw), ("%.3f" % ratio) if ratio else "못 쟀다", dst))
    for r in fw[:6]:
        p = r["반폭"]
        print("  길이 %5.0f  세장비 %5.1f  %s"
              % (r["길이"], 1.0 / max(max(p) * 2, 1e-6),
                 " ".join("%.3f" % v for v in p[::4])))


def demo():
    """배경 위에 얇은 막대 셋을 그려, **셋을 다 찾고 프로필이 일정한지** 본다."""
    im = np.full((600, 400, 3), (90, 120, 120), np.uint8)
    for i, w in enumerate((6, 12, 20)):
        cv2.rectangle(im, (80 + i * 110 - w, 80), (80 + i * 110 + w, 520), (240, 240, 240), -1)
    m = not_bg(im)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    big = [c for c in cs if cv2.contourArea(c) > 900]
    assert len(big) == 3, len(big)
    print("무기재기2.demo OK  막대 %d 개를 배경에서 분리" % len(big))


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        main()
