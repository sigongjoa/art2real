"""패널라인 좌우 대칭 — 선 화소를 몸 중심축으로 뒤집었을 때 반대편 2px 안에 선이 있는 몫.
대조: 실루엣 자체의 대칭 (몸이 비대칭이면 선도 비대칭일 수밖에 없다)."""
import os, sys, numpy as np, matplotlib
from scipy import ndimage
matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hull as H  # noqa

def 축찾기(실):
    xs = np.nonzero(실.any(0))[0]; best = None
    for cx2 in range(2 * xs[0] + 10, 2 * xs[-1] - 10):      # 축 = cx2/2 (반 화소 단위)
        j = np.arange(실.shape[1]); m = cx2 - j; ok = (m >= 0) & (m < 실.shape[1])
        f = np.zeros_like(실); f[:, j[ok]] = 실[:, m[ok]]
        s = (f & 실).sum() / (f | 실).sum()
        if best is None or s > best[0]: best = (s, cx2)
    return best

def 뒤집기(a, cx2):
    j = np.arange(a.shape[1]); m = cx2 - j; ok = (m >= 0) & (m < a.shape[1])
    f = np.zeros_like(a); f[:, j[ok]] = a[:, m[ok]]; return f

def 대칭몫(선, cx2, px=2):
    가까움 = ndimage.distance_transform_edt(~선) <= px
    return (뒤집기(선, cx2) & 가까움).sum() / max(선.sum(), 1)

c = "오메가몬"; src, base = H.CASES[c]["src"], H.art_dir(c)
선 = np.load(os.path.join(H.OUT, "선다듬_%s_front.npy" % c)).astype(bool)
원선 = H.ink_map(os.path.join(base, src["front"])).astype(bool)
실 = ndimage.binary_fill_holes(ndimage.binary_closing(원선 | 선, iterations=3))
s실, cx2 = 축찾기(실)
몫 = 대칭몫(선, cx2); 원몫 = 대칭몫(원선, cx2)
print("실루엣 대칭 IoU %.3f · 먹선(원화) 대칭 몫 %.3f · 다듬은 선 대칭 몫 %.3f · 축 x=%.1f" % (s실, 원몫, 몫, cx2 / 2))

ys, xs = np.nonzero(실); sl = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
뒤 = 뒤집기(선, cx2)
img = np.ones(선.shape + (3,)); img[실] = (.93, .93, .93)
img[선 & ~뒤] = (.85, .1, .1); img[뒤 & ~선] = (.1, .3, .9); img[선 & 뒤] = (0, 0, 0)
fig, ax = plt.subplots(figsize=(8, 10)); ax.imshow(img[sl]); ax.axvline(cx2 / 2 - xs.min(), color="green", lw=1)
ax.set_title("오메가몬 정면 패널라인 — 좌우 대칭\n검정 = 거울 짝 있음 · 빨강 = 이쪽에만 · 파랑 = 거울 쪽에만\n"
             "실루엣 대칭 %.2f · 선 대칭 %.2f (2px 안)" % (s실, 몫), fontsize=12); ax.axis("off")
fig.savefig(os.path.join(H.OUT, "패널라인_대칭.png"), dpi=110, bbox_inches="tight")
