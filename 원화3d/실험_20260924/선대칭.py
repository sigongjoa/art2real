"""상체 · 다리 패널라인을 좌우 대칭으로 — 팔(무기)은 원화 그대로 둔다 (09-25 사용자).
대칭 구역 안: 선 ∪ 거울선 → 2px 부풀려 뼈대(두 줄이 몇 px 어긋난 것을 한 줄로) → 왼 반만 남겨 거울 복사.
결과 out/선대칭_<c>_<v>.npy — 선다듬 과 같은 꼴이라 홈판이 그대로 읽는다."""
import os, sys, json, numpy as np, matplotlib
from PIL import Image
from scipy import ndimage
from skimage.morphology import skeletonize
matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hull as H  # noqa

# 대칭 구역 (화소 · 1024 판). 허리 위는 몸통 폭만, 아래는 다리 폭까지 — 팔 · 칼 · 대포는 밖
구역 = {"허리y": 560, "상체폭": 105, "다리폭": 200}

def 뒤집기(a, cx2):
    j = np.arange(a.shape[1]); m = cx2 - j; ok = (m >= 0) & (m < a.shape[1])
    f = np.zeros_like(a); f[:, j[ok]] = a[:, m[ok]]; return f

def 대칭몫(선, cx2, px=2):
    return (뒤집기(선, cx2) & (ndimage.distance_transform_edt(~선) <= px)).sum() / max(선.sum(), 1)

def 구역판(shape, cx2, 허리y, 상체폭, 다리폭):
    y, x = np.mgrid[:shape[0], :shape[1]]; dx = np.abs(x - cx2 / 2)
    return np.where(y < 허리y, dx <= 상체폭, dx <= 다리폭)

def 잇기(선, 실, R=28):
    """끊긴 선 끝을 잇는다 — 부품을 가르려면 선이 닫혀야 한다 (09-25: 다리 점선이 한쪽만 닫혀 좌우가 다르게 갈렸다).
    끝점마다 선이 뻗던 방향 ±50° 안, R px 안에서 가장 가까운 다른 선 화소나 실루엣 가장자리로 곧은 선을 긋는다."""
    선 = skeletonize(선); 새 = 선.copy()
    이웃 = ndimage.convolve(선.astype(int), np.ones((3, 3), int), mode="constant") - 1
    끝 = np.argwhere(선 & (이웃 == 1))
    과녁 = 선 | (실 & ~ndimage.binary_erosion(실, iterations=2))
    ty, tx = np.nonzero(과녁); T = np.c_[ty, tx]
    lab, _ = ndimage.label(선, np.ones((3, 3)))
    for y, x in 끝:
        # 뻗던 방향: 같은 선에서 6 px 안 화소들의 평균에서 끝점으로
        w = lab[max(y - 6, 0):y + 7, max(x - 6, 0):x + 7] == lab[y, x]
        py, px = np.nonzero(w); py = py + max(y - 6, 0); px = px + max(x - 6, 0)
        d = np.array([y - py.mean(), x - px.mean()]); nd = np.linalg.norm(d)
        if nd < 1: continue
        d /= nd
        V = T - [y, x]; L = np.linalg.norm(V, axis=1)
        ok = (L > 3) & (L <= R) & ((V @ d) > 0.64 * L)          # cos 50° = 0.64
        if not ok.any(): continue
        ty2, tx2 = T[ok][np.argmin(L[ok])]
        n = int(max(abs(ty2 - y), abs(tx2 - x))) + 1
        새[np.linspace(y, ty2, n).round().astype(int), np.linspace(x, tx2, n).round().astype(int)] = True
    return 새


def 대칭(선, Z, cx2):
    L = 선 & Z
    S = skeletonize(ndimage.binary_dilation(L | 뒤집기(L, cx2), iterations=2))
    왼 = np.arange(선.shape[1])[None, :] * 2 <= cx2
    반 = S & 왼
    return (선 & ~Z) | 반 | 뒤집기(반, cx2)

def main(c="오메가몬"):
    낼 = {}
    fig, axs = plt.subplots(1, 4, figsize=(22, 9))
    for i, v in enumerate(("front", "back")):
        선 = np.load(os.path.join(H.OUT, "선다듬_%s_%s.npy" % (c, v))).astype(bool)
        실 = np.array(Image.open(os.path.join(H.art_dir(c), H.CASES[c]["src"][v])).convert("RGBA"))[..., 3] > 10
        이은 = 잇기(선, 실); print("  %s 선 잇기 +%d px" % (v, int((이은 & ~skeletonize(선)).sum())))
        선 = 이은
        xs = np.nonzero(선.any(0))[0]; 가운데 = int(xs.mean() * 2)
        cx2 = max(range(가운데 - 80, 가운데 + 81), key=lambda k: 대칭몫(선, k))
        Z = 구역판(선.shape, cx2, **구역)
        새 = 대칭(선, Z, cx2)
        assert 대칭몫(새 & Z, cx2, px=0) == 1.0          # 구역 안은 정확히 거울
        np.save(os.path.join(H.OUT, "선대칭_%s_%s.npy" % (c, v)), 새)
        낼[v] = {"축x": cx2 / 2, "구역 전": round(대칭몫(선 & Z, cx2), 3), "구역 후": 1.0,
                 "팔 쪽 그대로": bool(((선 & ~Z) == (새 & ~Z)).all())}
        ys = np.nonzero((선 | 새).any(1))[0]; sl = (slice(ys.min() - 5, ys.max() + 5), slice(xs.min() - 5, xs.max() + 5))
        for k, (a, 제목) in enumerate(((선, "전 — 원화 먹선 그대로"), (새, "후 — 상체 · 다리 거울"))):
            뒤 = 뒤집기(a, cx2); img = np.ones(a.shape + (3,)); img[Z] = (.94, .97, 1)
            img[a & ~뒤] = (.85, .1, .1); img[뒤 & ~a] = (.1, .3, .9); img[a & 뒤] = (0, 0, 0)
            ax = axs[i * 2 + k]; ax.imshow(img[sl]); ax.axvline(cx2 / 2 - sl[1].start, color="g", lw=.8); ax.axis("off")
            ax.set_title("%s %s\n구역 안 대칭 %.2f" % ("정면" if v == "front" else "후면", 제목,
                         대칭몫(a & Z, cx2)), fontsize=13)
    fig.suptitle("하늘색 = 대칭 구역(상체 · 다리) · 검정 = 거울 짝 있음 · 빨강/파랑 = 한쪽에만 · 구역 밖(팔 · 무기)은 손대지 않음", fontsize=14)
    p = os.path.join(H.OUT, "선대칭_%s.png" % c); fig.savefig(p, dpi=100, bbox_inches="tight")
    print(json.dumps(낼, ensure_ascii=False)); print(p)

if __name__ == "__main__":
    main(*sys.argv[1:])
