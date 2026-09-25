# -*- coding: utf-8 -*-
"""분할 후보 채점 — 모든 방식을 같은 자로 (2026-09-25).

    python 채점.py <후보이름> [...]      (out/분할후보/<이름>/lab.npy)
    python 채점.py --모두

lab.npy = 입력.npz 의 O 와 같은 모양(192³) int · 0 = 바깥 · 1..n = 부품.
잰다:
  부품 수 · 가장 작은 부품 몫 · 가장 큰 부품 몫
  대칭     거울 짝이 있는 구역(칸과 그 거울 칸이 둘 다 몸) 안의 부품 경계 칸 중, 거울 자리 1 칸 안에 경계가 있는 몫
  평면     맞닿은 부품 짝마다 경계 칸에 평면을 맞춘 RMS (칸) — 닿은 넓이로 가중한 중앙값
  선 위    부품 경계가 겉에 드러난 자리 중 대칭 패널라인 2 칸 안에 있는 몫 (앞 · 뒤 판)
그림 out/분할후보/<이름>/채점.png (앞 · 뒤 · 위에서 본 단면) · 값 out/분할후보/<이름>/채점.json"""
import json, os, sys
import numpy as np, matplotlib
from scipy import ndimage
matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"
sys.path[:0] = [r"G:\art2real\원화3d"] + [r"G:\art2real\원화3d\실험_202609%02d" % d for d in (21, 22, 23, 24)]
import hull as H, win as W

D = os.path.join(H.OUT, "분할후보")
I = np.load(os.path.join(D, "입력.npz"))
O, ux, z, 축i, bs = I["O"], I["ux"], I["z"], float(I["축i"]), float(I["bs"])


def 거울(a):
    j = np.round(2 * 축i - np.arange(a.shape[0])).astype(int); ok = (j >= 0) & (j < a.shape[0])
    f = np.zeros_like(a); f[ok] = a[j[ok]]; return f


def 경계(lab):
    b = np.zeros(lab.shape, bool); 짝 = {}
    for a in range(3):
        a0 = np.take(lab, range(0, lab.shape[a] - 1), axis=a); a1 = np.take(lab, range(1, lab.shape[a]), axis=a)
        d = (a0 != a1) & (a0 > 0) & (a1 > 0)
        b |= np.pad(d, [(0, 0)] * a + [(0, 1)] + [(0, 0)] * (2 - a))
        idx = np.argwhere(d)
        for (i, j, k), p, q in zip(idx, a0[d], a1[d]):
            짝.setdefault((min(p, q), max(p, q)), []).append((i, j, k))
    return b, 짝


def _열(선판, sign):
    col = (sign * ux - W.U0) / (W.U1 - W.U0) * W.RES - 0.5
    row = (W.Z1 - z) / (W.Z1 - W.Z0) * W.RES - 0.5
    C, R = np.meshgrid(col, row, indexing="ij")
    return ndimage.map_coordinates(선판.astype(np.float32), [R, C], order=1, mode="nearest") > 0.25


def 채점(이름):
    lab = np.load(os.path.join(D, 이름, "lab.npy")).astype(np.int32)
    assert lab.shape == O.shape, lab.shape
    lab = np.where(O, lab, 0)
    n = len(np.unique(lab)) - 1
    크 = np.bincount(lab.ravel())[1:]; 크 = 크[크 > 0] / O.sum()
    b, 짝 = 경계(lab)
    구역 = O & 거울(O)
    bz = b & 구역
    대칭전체 = float((ndimage.binary_dilation(거울(b), iterations=1) & bz).sum() / max(bz.sum(), 1))
    # 09-25: 팔(칼 · 대포 쪽)은 원래 좌우가 다른 디자인 — 대칭 구역에서 뺀다 (A · B · E 에이전트 제안, E 의 팔 구역 정의)
    X, _, Zk = np.indices(O.shape, sparse=True); dx = np.abs(X - 축i)
    팔 = ((dx > 20) & (Zk >= 62)) | ((dx > 36) & (Zk >= 28))
    bz = bz & ~팔
    # 09-25 고침(E 가 잡음): 전에는 거울(b) & 팽창(b) & bz 라 1 칸 여유가 안 걸렸다 — 거울 쪽을 팽창한다
    대칭 = float((ndimage.binary_dilation(거울(b), iterations=1) & bz).sum() / max(bz.sum(), 1))
    rms, w = [], []
    for k, pts in 짝.items():
        P = np.array(pts, float)
        if len(P) < 20: continue
        c = P.mean(0); s = np.linalg.svd(P - c, compute_uv=False)
        rms.append(s[-1] / np.sqrt(len(P))); w.append(len(P))
    평면 = float(np.median(np.repeat(rms, np.maximum(1, np.array(w) // 10)))) if rms else float("nan")
    # 겉에 드러난 경계: 깊이 축으로 처음 · 마지막 몸 칸의 경계
    선 = {"front": _열(I["선앞"], 1), "back": _열(I["선뒤"], bs)}
    for v in 선: 선[v] = ndimage.binary_dilation(선[v], iterations=2)
    has = O.any(1); 앞 = np.argmax(O, 1); 뒤 = O.shape[1] - 1 - np.argmax(O[:, ::-1], 1)
    ii, kk = np.nonzero(has)
    겉 = np.concatenate([b[ii, 앞[ii, kk], kk], b[ii, 뒤[ii, kk], kk]])
    위 = np.concatenate([선["front"][ii, kk], 선["back"][ii, kk]])
    선위 = float((겉 & 위).sum() / max(겉.sum(), 1))
    값 = {"부품": int(n), "최소몫": round(float(크.min()), 4), "최대몫": round(float(크.max()), 3),
         "대칭": round(대칭, 3), "대칭전체": round(대칭전체, 3), "평면RMS칸": round(평면, 3), "선위": round(선위, 3)}
    # 그림: 앞 · 뒤에서 본 부품 + 높이 3 곳 가로 단면
    rng = np.random.default_rng(7); 색 = rng.uniform(.3, .95, (lab.max() + 1, 3)); 색[0] = 1
    fig, axs = plt.subplots(1, 5, figsize=(22, 8), gridspec_kw={"width_ratios": [1, 1, .7, .7, .7]})
    for a, (제목, 깊) in zip(axs[:2], (("앞", 앞), ("뒤", 뒤))):
        img = np.take_along_axis(lab, 깊[:, None, :], 1)[:, 0, :]; img = np.where(has, img, 0)
        bb = np.take_along_axis(b, 깊[:, None, :], 1)[:, 0, :]
        rgb = 색[img]; rgb[bb & has] = 0
        if 제목 == "뒤": rgb = rgb[::-1]
        a.imshow(np.transpose(rgb, (1, 0, 2))[::-1]); a.set_title(제목); a.axis("off")
        a.axvline(축i if 제목 == "앞" else O.shape[0] - 1 - 축i, color="g", lw=.6)
    zs = np.nonzero(O.any((0, 1)))[0]
    for a, t in zip(axs[2:], (.25, .5, .75)):
        k = int(zs[0] + t * (zs[-1] - zs[0])); s = lab[:, :, k]
        rgb = 색[s]; rgb[b[:, :, k] & (s > 0)] = 0
        a.imshow(np.transpose(rgb, (1, 0, 2))); a.set_title("단면 높이 %d%% (위가 앞)" % int(t * 100)); a.axis("off")
    fig.suptitle("%s — 부품 %d · 대칭 %.2f · 이음면 평면 RMS %.2f 칸 · 선 위 %.2f · 최소 부품 %.1f%%" % (
        이름, n, 대칭, 평면, 선위, 100 * 값["최소몫"]), fontsize=15)
    fig.savefig(os.path.join(D, 이름, "채점.png"), dpi=80, bbox_inches="tight"); plt.close(fig)
    json.dump(값, open(os.path.join(D, 이름, "채점.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(이름, 값, flush=True)
    return 값


if __name__ == "__main__":
    이름들 = sys.argv[1:]
    if 이름들 == ["--모두"]:
        이름들 = sorted(d for d in os.listdir(D) if os.path.exists(os.path.join(D, d, "lab.npy")))
    for 이름 in 이름들: 채점(이름)
