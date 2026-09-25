# -*- coding: utf-8 -*-
"""패널라인(대칭 선)으로 가르기 — 09-24 키트의 몸 그대로, 가르는 선만 바꾼다 (2026-09-25).

    가: 09-24  원화 먹선 + 모양 부위 경계
    나: 대칭 선 + 모양 부위 경계
    다: 대칭 선만
  -> out/대칭분할_오메가몬.png · 부품 수 · 분할선이 선 위에 있는 몫 · 정면 분할 대칭 몫
"""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np, matplotlib
from scipy import ndimage
matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
sys.path[:0] = [r"G:\art2real\원화3d"] + [r"G:\art2real\원화3d\실험_202609%02d" % d for d in (21, 22, 23, 24)]
import hull as H, 부품분할 as BB, 면자르기 as MJ, 먹선분할 as MS

T0 = time.time()
def 찍(s): print("  [%4.0f s] %s" % (time.time() - T0, s), flush=True)


def 대칭먹선(c, raw, p, bs, 넓힘=1):
    """먹선분할.창먹선 과 같고, 원화 먹선 대신 out/선대칭_<c>_<v>.npy (곧게 편 뒤 상체·다리 거울)."""
    낼 = {}
    for v in ("front", "back"):
        선 = np.load(os.path.join(H.OUT, "선대칭_%s_%s.npy" % (c, v)))
        if 넓힘: 선 = ndimage.binary_dilation(선, iterations=넓힘)
        _, w2 = H.to_win(H.declutter(raw[v]), 선.astype(np.float32))
        낼[v] = H._warp_one(w2, v, p) > 0.5
    return 낼


def 가르기6(O, 벽, 최소=MS.최소몫):
    """먹선분할.가르기 와 같고, 이웃을 면 6 방향으로만 본다 — 한 칸 벽을 대각선으로 새지 않게."""
    lab, n = ndimage.label(O & ~벽)
    크 = np.bincount(lab.ravel()); 크[0] = 0
    작 = np.where((크 > 0) & (크 < 최소 * O.sum()))[0]
    lab[np.isin(lab, 작)] = 0
    i = ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
    lab = np.where(O, lab[tuple(i)], 0)
    _, lab = np.unique(lab, return_inverse=True)
    return lab.reshape(O.shape)


def 합치기(lab, 몫=0.012):
    """부피가 전체의 몫보다 작은 부품을 가장 넓게 닿은 이웃에 붙인다 (작은 것부터 하나씩)."""
    lab = lab.copy(); 전 = (lab > 0).sum()
    while True:
        크 = np.bincount(lab.ravel()); 크[0] = 0
        작 = [k for k in np.argsort(크) if 0 < 크[k] < 몫 * 전]
        if not 작: break
        k = 작[0]; M = lab == k
        테 = ndimage.binary_dilation(M) & ~M & (lab > 0)
        if not 테.any(): lab[M] = 0; continue
        lab[M] = np.bincount(lab[테]).argmax()
    _, lab = np.unique(lab, return_inverse=True)
    return lab.reshape(-1).reshape(lab.shape) if False else lab


def 앞모습(lab):
    """깊이 축(1)을 따라 처음 만나는 부품 번호 — 정면에서 본 분할. [z 위→아래, x]"""
    has = lab > 0; first = np.argmax(has, axis=1)
    img = np.take_along_axis(lab, first[:, None, :], axis=1)[:, 0, :]
    return np.where(has.any(1), img, 0).T[::-1]


def 경계대칭(img):
    """정면 분할 경계를 몸 가로 중심에서 뒤집어 1칸 안에 경계가 있는 몫."""
    b = np.zeros_like(img, bool)
    b[:, 1:] |= (img[:, 1:] != img[:, :-1]) & (img[:, 1:] > 0) & (img[:, :-1] > 0)
    b[1:, :] |= (img[1:, :] != img[:-1, :]) & (img[1:, :] > 0) & (img[:-1, :] > 0)
    xs = np.nonzero((img > 0).any(0))[0]; 축2 = xs[0] + xs[-1]
    j = 축2 - np.arange(img.shape[1]); ok = (j >= 0) & (j < img.shape[1])
    f = np.zeros_like(b); f[:, ok] = b[:, j[ok]]
    return (f & ndimage.binary_dilation(b, iterations=1)).sum() / max(b.sum(), 1), b


def main(c="오메가몬"):
    os.environ.setdefault("INK_W", "1")
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]; O = g > 0; 찍("장 %s" % (O.shape,))
    _, 부위, _ = MJ.부위(O); 부위 = BB.채우기(부위, O)
    경 = np.zeros_like(O)
    for a2 in range(3):
        a0 = np.take(부위, range(0, 부위.shape[a2] - 1), axis=a2); a1 = np.take(부위, range(1, 부위.shape[a2]), axis=a2)
        경 |= np.pad((a0 != a1) & (a0 > 0) & (a1 > 0), [(0, 0)] * a2 + [(0, 1)] + [(0, 0)] * (2 - a2))
    찍("부위 경계")
    원선, 대선 = MS.창먹선(c, raw, p, bs), 대칭먹선(c, raw, p, bs)
    굵은 = 대칭먹선(c, raw, p, bs, 넓힘=3)          # 선 폭 7 px ≥ 격자 한 칸 5.3 px
    판 = {"가 · 09-24 그대로": (원선, True, MS.가르기), "나 · 대칭 선 이음 + 굵게 + 면 이웃": (굵은, False, 가르기6),
          "다 · 나 + 작은 조각 합치기 (1.2% 미만)": (굵은, False, lambda O, 벽: 합치기(가르기6(O, 벽)).reshape(O.shape))}
    fig, axs = plt.subplots(1, 3, figsize=(18, 10)); rng = np.random.default_rng(3)
    색 = rng.uniform(.25, .95, (400, 3)); 색[0] = 1
    for a, (이름, (선들, 경씀, 가름)) in zip(axs, 판.items()):
        벽 = MS.먹선벽(O, 선들, ux, z, bs) | ((경 & O) if 경씀 else False)
        lab = 가름(O, 벽); n = int(lab.max()); 찍("가르기 " + 이름)
        몫 = MS.먹선몫(lab, 선들, ux, z, bs, O)
        img = 앞모습(lab); s, b = 경계대칭(img)
        rgb = 색[img % 400]; rgb[b] = 0
        a.imshow(rgb); a.axis("off")
        a.set_title("%s\n부품 %d · 분할선이 선 위 %.3f · 정면 경계 대칭 %.2f" % (이름, n, 몫, s), fontsize=13)
        print("  %s  부품 %d · 선 위 %.3f · 대칭 %.3f" % (이름, n, 몫, s), flush=True)
        np.save(os.path.join(H.OUT, "대칭분할_%s_%s.npy" % (c, 이름[0])), lab.astype(np.int16))
    fig.suptitle("같은 몸(09-24 키트) · 가르는 선만 바꿈 — 정면에서 본 부품, 검정 = 부품 경계", fontsize=15)
    out = os.path.join(H.OUT, "대칭분할_%s.png" % c); fig.savefig(out, dpi=90, bbox_inches="tight"); print(out)


if __name__ == "__main__":
    main(*sys.argv[1:])
