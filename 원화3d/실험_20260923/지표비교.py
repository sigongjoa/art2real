# -*- coding: utf-8 -*-
"""**지표를 바꾸면 순위가 어떻게 바뀌나** — 같은 판들을 여러 자로 재서 나란히 놓는다 (2026-09-23).

    python 지표비교.py            얼린 10 케이스 · 판 5 개 -> out/기록/지표비교_<때>.json · out/지표비교.png

사용자(09-23): 「지표를 바꾸면 어떻게 되는지 비교하는 거 만들어줘」.
조사(`claudedocs/research_3D평가지표_20260923.md`): 남들은 **F-score@τ** 를 앞세우고 챔퍼 · 법선 일치 · 부피 IoU 를 함께 쓴다.

    판 다섯     hull · 타원(지금) · 색 대응 겉6 · 최소표면(되돌림) · 깊이칸 D2(신탁 · 상한)
    자 여섯     부피 IoU · F@1mm · F@2mm · 챔퍼 중앙(mm) · 법선 일치 · 새 각도 실루엣 IoU
                (전고 150 mm · 정답은 **원본 메시**)
보는 것: 자마다 **순위가 뒤집히나**. 자끼리 스피어만 상관도 함께 적는다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage, stats
from scipy.spatial import cKDTree

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922", r"G:\art2real\원화3d\실험_20260923"]
import hull as H
import 정답 as JD
import 부품분할 as BB
import 면자르기 as MJ
import 도면벤치_천장 as DC
import 부피벤치 as PB
import 지표 as Z
import 색대응 as CC
import 최소표면 as MS
import 깊이칸 as K
import 깊이추정 as GC

전고mm = 150.0
표본 = 60000


def Fscore(a, b, 배율, τ):
    pa = a.sample(표본) * 배율
    pb = b.sample(표본) * 배율
    d1, _ = cKDTree(pb).query(pa)          # 우리 점 -> 정답
    d2, _ = cKDTree(pa).query(pb)          # 정답 점 -> 우리
    정밀 = float((d1 < τ).mean()); 재현 = float((d2 < τ).mean())
    F = 0.0 if 정밀 + 재현 == 0 else 2 * 정밀 * 재현 / (정밀 + 재현)
    return F, 정밀, 재현


def 법선일치(a, b, n=40000):
    pa, ia = a.sample(n, return_index=True)
    pb, ib = b.sample(n, return_index=True)
    na, nb = a.face_normals[ia], b.face_normals[ib]
    d1, j1 = cKDTree(pb).query(pa); d2, j2 = cKDTree(pa).query(pb)
    c1 = np.abs((na * nb[j1]).sum(1)); c2 = np.abs((nb * na[j2]).sum(1))
    return float((c1.mean() + c2.mean()) / 2)


def 판들(c):
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    gh, _ = H.field_hull(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    O = g > 0
    tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
    A, o = JD.grid(tm, 봉합=1)
    T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
    격, _ = CC.판색(c, raw, masks, p, bs)
    _, 부위, _ = MJ.부위(O); 부위 = BB.채우기(부위, O)
    값 = {l: K.숫자읽기(부위, T, l) for l in np.unique(부위) if l}
    값 = {l: v for l, v in 값.items() if v}
    return {"hull": gh > 0, "타원(지금)": O, "색 대응": CC.깎기(O, 격, 6),
            "최소표면": MS.되돌림(O, 1.6, 6), "깊이칸(신탁)": K.조이기(O, 부위, 값, "D2")}, T, tm, (ux, uy, z)


def 한케이스(c):
    판, T, tm, ax = 판들(c)
    배율 = 전고mm / max(tm.extents[2], 1e-9)
    out = {}
    for 이름, V in 판.items():
        m = Z.메시로(V, ax)
        f1, _, _ = Fscore(m, tm, 배율, 1.0)
        f2, _, _ = Fscore(m, tm, 배율, 2.0)
        중, _ = Z.챔퍼(m, tm, 배율, n=40000)
        ious = []
        for yaw, pitch in Z.각도들()[:8]:
            R = (trimesh.transformations.rotation_matrix(np.radians(yaw), [0, 0, 1])[:3, :3]
                 @ trimesh.transformations.rotation_matrix(np.radians(pitch), [1, 0, 0])[:3, :3])
            a, b = Z.그림자(m, R), Z.그림자(tm, R)
            ious.append((a & b).sum() / max((a | b).sum(), 1))
        out[이름] = {"부피 IoU": round(PB.재기(V, T)["IoU"], 3), "F@1mm": round(f1, 3), "F@2mm": round(f2, 3),
                   "챔퍼 mm": round(중, 2), "법선 일치": round(법선일치(m, tm), 3),
                   "새 각도 실루엣": round(float(np.median(ious)), 3)}
    return out


def 그림(요약, 판이름, 자이름, 경로):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt, font_manager
    for f in ("Malgun Gothic", "맑은 고딕"):
        if any(f in x.name for x in font_manager.fontManager.ttflist):
            plt.rcParams["font.family"] = f; break
    plt.rcParams["axes.unicode_minus"] = False
    값 = np.array([[요약[p][m] for m in 자이름] for p in 판이름], float)
    좋을수록 = np.array([1, 1, 1, -1, 1, 1])                 # 챔퍼만 작을수록 좋다
    순위 = np.zeros_like(값)
    for j in range(값.shape[1]):
        순위[:, j] = stats.rankdata(-값[:, j] * 좋을수록[j])
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.4), gridspec_kw={"width_ratios": [1.25, 1]})
    im = ax[0].imshow(순위, cmap="RdYlGn_r", vmin=1, vmax=len(판이름))
    ax[0].set_xticks(range(len(자이름)), 자이름, rotation=18, ha="right")
    ax[0].set_yticks(range(len(판이름)), 판이름)
    for i in range(len(판이름)):
        for j in range(len(자이름)):
            ax[0].text(j, i, "%d위\n%.3g" % (순위[i, j], 값[i, j]), ha="center", va="center", fontsize=9)
    ax[0].set_title("자마다 순위가 다르다 (10 장 중앙값)")
    상 = np.zeros((len(자이름), len(자이름)))
    for i in range(len(자이름)):
        for j in range(len(자이름)):
            상[i, j] = stats.spearmanr(순위[:, i], 순위[:, j]).correlation
    im2 = ax[1].imshow(상, cmap="coolwarm", vmin=-1, vmax=1)
    ax[1].set_xticks(range(len(자이름)), 자이름, rotation=18, ha="right")
    ax[1].set_yticks(range(len(자이름)), 자이름)
    for i in range(len(자이름)):
        for j in range(len(자이름)):
            ax[1].text(j, i, "%.2f" % 상[i, j], ha="center", va="center", fontsize=9)
    ax[1].set_title("자끼리 순위 상관 (스피어만)")
    fig.colorbar(im2, ax=ax[1], fraction=0.046)
    fig.tight_layout(); fig.savefig(경로, dpi=130); plt.close(fig)


def main():
    기록 = {}
    for c in GC.케이스들:
        t0 = time.time()
        기록[c] = 한케이스(c)
        r = 기록[c]["타원(지금)"]
        print("  %-28s 타원: IoU %.3f F@1 %.3f F@2 %.3f 챔퍼 %.1f NC %.3f 실루엣 %.3f  %.0f초"
              % (c[:28], r["부피 IoU"], r["F@1mm"], r["F@2mm"], r["챔퍼 mm"], r["법선 일치"], r["새 각도 실루엣"], time.time() - t0), flush=True)
    판이름 = list(기록[GC.케이스들[0]].keys())
    자이름 = ["부피 IoU", "F@1mm", "F@2mm", "챔퍼 mm", "법선 일치", "새 각도 실루엣"]
    요약 = {p: {m: round(float(np.median([기록[c][p][m] for c in GC.케이스들])), 3) for m in 자이름} for p in 판이름}
    print("\n" + json.dumps(요약, ensure_ascii=False, indent=1))
    pth = os.path.join(H.OUT, "기록", "지표비교_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(pth, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    그림(요약, 판이름, 자이름, os.path.join(H.OUT, "지표비교.png"))
    print(pth, os.path.join(H.OUT, "지표비교.png"))


if __name__ == "__main__":
    main()
