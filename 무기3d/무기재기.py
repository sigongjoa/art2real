# -*- coding: utf-8 -*-
"""**원화에서 무기의 날 프로필을 뽑는다.** 형태를 지어내지 않는다.

    python 무기재기.py D:/imggen/blades5/r5_up_hero.png 무기.json [--min 60] [--thr 0.10]

## 왜 프로필인가

크로켓이 「말린 잎사귀」인 걸 몰라도 **윤곽을 축 따라 훑으면** 형태가 나온다
(`건축3d/research_형태속성` — 일반화 원기둥). 무기도 같다.
길쭉한 물건의 정체는 **길이에 따른 폭의 변화**다 —

    잎사귀 날   가운데가 제일 넓고 양끝이 좁다
    바늘 날     밑에서 끝까지 거의 일정하게 가늘다
    삼각 창끝   밑이 제일 넓고 곧게 좁아진다

그 곡선만 있으면 블렌더가 짓는다. **어휘를 내가 알 필요가 없다.**

## 어떻게 뽑나

**묶는 것도 프로필로 한다.** 처음엔 `kinds.py` 의 푸리에 기술자로 묶었는데,
길쭉한 물건은 세장비가 기술자를 지배해서 **막대와 잎사귀가 한 종류로 묶였다**.
건축 장식에는 맞는 자가 무기에는 안 맞는다 — 자를 물건에 맞춘다.

윤곽마다 —

    1. PCA 로 **긴 축**을 찾는다 (무기는 길쭉하므로 제1주성분이 날의 방향이다)
    2. 그 축을 따라 20 칸으로 나눠 칸마다 **반폭**을 잰다
    3. 축 길이로 나눠 **비율**로 적는다 (크기를 버린다)

돌려주는 건 종류마다 (길이:폭 비, 반폭 프로필 20점, 표본 수)다.
표본이 많은 종류일수록 원화가 자주 쓴 무기다 — 그 비율대로 뿌리면 된다.
"""
import json
import sys

import numpy as np

sys.path.insert(0, r"G:\art2real\건축3d")
import kinds as K                                             # noqa: E402

N_BIN = 20


def axis_profile(c, n=N_BIN):
    """윤곽 하나 -> (길이, 반폭 프로필). **긴 축을 PCA 로 찾는다.**"""
    p = c.reshape(-1, 2).astype(np.float64)
    p = p - p.mean(axis=0)
    u, s, vt = np.linalg.svd(p, full_matrices=False)
    q = p @ vt.T                                              # q[:,0] = 긴 축
    lo, hi = q[:, 0].min(), q[:, 0].max()
    L = hi - lo
    if L < 1e-6:
        return None
    prof = []
    for i in range(n):
        a = lo + L * i / float(n)
        b = lo + L * (i + 1) / float(n)
        w = q[(q[:, 0] >= a) & (q[:, 0] < b), 1]
        prof.append(0.0 if len(w) == 0 else float((w.max() - w.min()) / 2.0 / L))
    # **끝이 뾰족한 쪽을 위로.** 반폭이 작은 끝을 프로필의 끝으로 돌린다
    if sum(prof[:5]) < sum(prof[-5:]):
        prof = prof[::-1]
    return L, prof


def measure(path, min_area=60.0, thr=0.10, hgt=1024):
    im = K.imread(path)
    assert im is not None, path
    im = np.ascontiguousarray(
        K.cv2.resize(im, (int(round(im.shape[1] * hgt / im.shape[0])), hgt),
                     interpolation=K.cv2.INTER_AREA))
    m = K.gold_mask(im)
    cs, _ = K.cv2.findContours(m, K.cv2.RETR_LIST, K.cv2.CHAIN_APPROX_NONE)
    cs = [c for c in cs if K.cv2.contourArea(c) >= min_area and len(c) >= 8]
    cs.sort(key=K.cv2.contourArea, reverse=True)
    rows = []
    for c in cs:
        r = axis_profile(c)
        if r:
            rows.append((r[0], r[1], float(K.cv2.contourArea(c))))
    lab, n = K.cluster([np.array(r[1]) for r in rows], thr)
    kinds = {}
    for r, k in zip(rows, lab):
        kinds.setdefault(k, []).append(r)
    out = []
    for k, rows in sorted(kinds.items(), key=lambda kv: -len(kv[1])):
        L = float(np.median([r[0] for r in rows]))
        prof = np.median(np.array([r[1] for r in rows]), axis=0)
        # 세장비 — 길이를 제일 넓은 반폭의 두 배로 나눈 값. 클수록 가늘고 길다
        slim = 1.0 / max(float(prof.max()) * 2.0, 1e-6)
        out.append({"종류": int(k), "표본": len(rows), "세장비": round(slim, 2),
                    "반폭": [round(float(v), 5) for v in prof]})
    return {"src": path, "종류수": n, "무기": out}


def demo():
    """가는 막대와 잎사귀를 그려, **세장비가 갈리고 프로필 모양이 맞는지** 본다."""
    im = np.zeros((400, 400, 3), np.uint8)
    gold = (60, 200, 240)
    K.cv2.rectangle(im, (60, 40), (72, 360), gold, -1)         # 가는 막대
    pts = np.array([[200, 40], [240, 200], [200, 360], [160, 200]], np.int32)
    K.cv2.fillPoly(im, [pts], gold)                            # 잎사귀
    r = measure_array(im, 60.0, 0.03)
    slim = sorted(w["세장비"] for w in r["무기"])
    assert len(r["무기"]) == 2, r
    assert slim[1] > slim[0] * 2.5, slim                       # 막대가 훨씬 가늘다
    leaf = [w for w in r["무기"] if w["세장비"] == slim[0]][0]["반폭"]
    assert leaf[len(leaf) // 2] > leaf[0] and leaf[len(leaf) // 2] > leaf[-1], leaf
    print("무기재기.demo OK  세장비 %s · 잎사귀는 가운데가 제일 넓다" % slim)


def measure_array(im, min_area, thr):
    m = K.gold_mask(im)
    cs, _ = K.cv2.findContours(m, K.cv2.RETR_LIST, K.cv2.CHAIN_APPROX_NONE)
    cs = [c for c in cs if K.cv2.contourArea(c) >= min_area and len(c) >= 8]
    cs.sort(key=K.cv2.contourArea, reverse=True)
    rows = []
    for c in cs:
        r = axis_profile(c)
        if r:
            rows.append((r[0], r[1], 0))
    lab, n = K.cluster([np.array(r[1]) for r in rows], thr)
    kinds = {}
    for r, k in zip(rows, lab):
        kinds.setdefault(k, []).append(r)
    out = []
    for k, rows in sorted(kinds.items(), key=lambda kv: -len(kv[1])):
        prof = np.median(np.array([r[1] for r in rows]), axis=0)
        out.append({"종류": int(k), "표본": len(rows),
                    "세장비": round(1.0 / max(float(prof.max()) * 2.0, 1e-6), 2),
                    "반폭": [round(float(v), 5) for v in prof]})
    return {"종류수": n, "무기": out}


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        av = [a for a in sys.argv[1:] if not a.startswith("--")]
        mn = float(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else 60.0
        th = float(sys.argv[sys.argv.index("--thr") + 1]) if "--thr" in sys.argv else 0.10
        av = [a for a in av if a not in (str(mn), str(th))]
        r = measure(av[0], mn, th)
        json.dump(r, open(av[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("MEASURE 종류 %d -> %s" % (r["종류수"], av[1]))
        for w in r["무기"][:8]:
            print("  종류 %2d  표본 %2d  세장비 %5.1f  %s"
                  % (w["종류"], w["표본"], w["세장비"],
                     " ".join("%.2f" % v for v in w["반폭"][::4])))
