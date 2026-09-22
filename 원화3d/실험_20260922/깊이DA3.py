# -*- coding: utf-8 -*-
"""**깊이 DA3** — 깊이 신탁 자리에 그림에서 읽은 깊이(Depth Anything 3 Mono-Large · ComfyUI)를 넣는다 (2026-09-22).

    python 깊이DA3_판.py                                   원화 -> 창 좌표 PNG
    D:\ComfyUI\venv\Scripts\python.exe 깊이DA3_돌리기.py   PNG -> <판>_da3.npy
    python 깊이DA3.py                                     -> out/기록/깊이DA3_<때>.json

깊이 천장(`깊이천장.py`): 보이는 겉 깊이를 정답에서 읽으면 hull 0.56 -> 0.91. 여기선 **정답 없이** 그림만으로 한다.
DA3 는 상대 깊이만 준다(값이 클수록 멀다고 둔다). 눈금은 **실루엣에서** 맞춘다 — 정답을 안 쓴다:
    줄마다 가장 가까운 점 = hull 의 그 줄 가장 앞(앞 판) · 가장 뒤(뒤 판) · 가장 +x(옆 판).
      (그 높이에서 옆 윤곽의 맨 앞 점은 앞에서 반드시 보인다 — 원리상 맞는 맞춤)
    배율 둘 (모른다 · 돌리기 전에 둘 다 적는다)
      행맞춤   줄마다 가장 먼 점 = 그 줄 두께의 가운데
      전역     배율 하나 = 줄마다 (두께 반 / DA3 폭) 의 중앙값
    여유 k    깎는 깊이를 바깥쪽으로 k 칸 (0 · 3)
판정(돌리기 전 · 판마다 IoU 중앙, 가장 좋은 판):
    ≥ 0.73   hull→신탁 사이의 절반 넘게 회수 — 이 길로 간다
    0.60 ~   일부 회수 — 눈금 · 모델을 더 본다
    < 0.60   그림 깊이는 아직 못 쓴다
재현율도 적는다 — 신탁과 달리 안쪽 오차(정답 깎임)가 생긴다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage, stats

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260922")
import hull as H
import win as W
import 정답 as JD
import 부품분할 as BB
import 도면벤치_천장 as DC
import 부피벤치 as PB
import 깊이천장 as KC
import 깊이추정 as GC

OUT = H.OUT
DD = os.path.join(OUT, "깊이DA3")


def 표본(S2, uu, zz):
    """창 그림(RES²) -> (len(uu), len(zz)) — `hull.field_hull` 과 같은 사상."""
    col = (uu - W.U0) / (W.U1 - W.U0) * W.RES - 0.5
    row = (W.Z1 - zz) / (W.Z1 - W.Z0) * W.RES - 0.5
    C, R = np.meshgrid(col, row, indexing="ij")
    return ndimage.map_coordinates(S2, [R, C], order=1, mode="nearest")


def 깊이면(d, O, axis, 앞에서, 배율):
    """d(가로, z) 상대 깊이 -> 깊이축 인덱스 면. 줄(z)마다 가장 가까운 점을 O 의 그 줄 끝에 맞춘다."""
    n = O.shape[axis]
    other = 1 - axis if axis < 2 else None
    idx = np.arange(n)
    열있음 = O.any(axis=axis)                                  # (가로, z)
    zs = O.any(axis=(0, 1))
    면 = np.full(d.shape, np.nan)
    폭들, 줄 = [], {}
    for k in np.where(zs)[0]:
        sl = O[:, :, k]                                        # (x, y)
        깊이있음 = sl.any(axis=1 - axis)
        lo, hi = idx[깊이있음].min(), idx[깊이있음].max()
        m = 열있음[:, k]
        if m.sum() < 2: continue
        dd = d[m, k]; dmin, dmax = dd.min(), dd.max()
        반 = (hi - lo) / 2
        줄[k] = (lo, hi, dmin, dmax, 반, m)
        if dmax - dmin > 1e-6: 폭들.append(반 / (dmax - dmin))
    a = float(np.median(폭들)) if 폭들 else 0.0
    for k, (lo, hi, dmin, dmax, 반, m) in 줄.items():
        s = (반 / (dmax - dmin) if dmax - dmin > 1e-6 else 0.0) if 배율 == "행맞춤" else a
        t = s * (d[m, k] - dmin)
        면[m, k] = (lo + t) if 앞에서 else (hi - t)
    return 면


def 깎기(O, 면, axis, 앞에서, k):
    n = O.shape[axis]
    idx = np.arange(n).reshape([-1 if a == axis else 1 for a in range(3)])
    f = np.expand_dims(np.nan_to_num(면, nan=(-1e9 if 앞에서 else 1e9)), axis)
    return O & ((idx >= f - k) if 앞에서 else (idx <= f + k))


def 한케이스(c):
    raw, masks, bs, p = BB.판(c)
    tm = trimesh.load(os.path.join(OUT, "시트", c, "truth.glb"), force="mesh")
    A, o = JD.grid(tm, 봉합=1)
    gh, ax = H.field_hull(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
    Oh = gh > 0
    d = {v: np.load(os.path.join(DD, c, v + "_da3.npy")) for v in W.VIEWS}
    df = 표본(d["front"], ux, z)                               # (x, z)
    db = 표본(d["back"], bs * ux, z)                           # (x, z)
    ds = 표본(d["side"], uy, z)                                # (y, z)
    r = {"hull": PB.재기(Oh, T), "신탁 앞뒤옆": PB.재기(KC.셋(Oh, T), T)}
    # 진단(맞춤에 안 쓴다): DA3 앞 깊이 대 정답 앞 깊이 순위 상관
    첫 = np.argmax(T, axis=1).astype(float); 첫[~T.any(axis=1)] = np.nan
    ok = ~np.isnan(첫) & Oh.any(axis=1)
    r["진단 앞 순위상관"] = float(stats.spearmanr(df[ok], 첫[ok]).correlation)
    for 배율 in ("행맞춤", "전역"):
        f = 깊이면(df, Oh, 1, True, 배율); b = 깊이면(db, Oh, 1, False, 배율)
        s = 깊이면(ds, Oh.transpose(1, 0, 2), 1, False, 배율)    # 옆: (y, x, z) 로 보고 +x 쪽이 가깝다
        for k in (0, 3):
            M = 깎기(깎기(Oh, f, 1, True, k), b, 1, False, k)
            r["DA3 앞뒤 %s k%d" % (배율, k)] = PB.재기(M, T)
            M2 = 깎기(M.transpose(1, 0, 2), s, 1, False, k).transpose(1, 0, 2)
            r["DA3 앞뒤옆 %s k%d" % (배율, k)] = PB.재기(M2, T)
    return r


def 검사():
    O = np.ones((3, 5, 2), bool)
    d = np.tile(np.array([0.0, 1.0, 2.0])[:, None], (1, 2))
    f = 깊이면(d, O, 1, True, "행맞춤")
    assert np.allclose(f[:, 0], [0, 1, 2]), f                  # 줄 두께 4 -> 반 2 · DA3 폭 2 -> 배율 1
    M = 깎기(O, f, 1, True, 0)
    assert M[0, :, 0].sum() == 5 and M[2, :, 0].sum() == 3


def main():
    검사()
    기록 = {}
    for c in GC.케이스들:
        t0 = time.time()
        기록[c] = r = 한케이스(c)
        best = max((k for k in r if k.startswith("DA3")), key=lambda k: r[k]["IoU"])
        print("  %-38s hull %.2f 신탁 %.2f | 앞 상관 %+.2f | 최고 %s %.2f (재현 %.2f)  %.0f초"
              % (c, r["hull"]["IoU"], r["신탁 앞뒤옆"]["IoU"], r["진단 앞 순위상관"], best, r[best]["IoU"], r[best]["재현율"], time.time() - t0), flush=True)
    판들 = [k for k in 기록[GC.케이스들[0]] if isinstance(기록[GC.케이스들[0]][k], dict)]
    요약 = {k: {m: float(np.median([r[k][m] for r in 기록.values()])) for m in ("IoU", "정밀도", "재현율", "부피 비")} for k in 판들}
    요약["진단 앞 순위상관 중앙"] = float(np.median([r["진단 앞 순위상관"] for r in 기록.values()]))
    최고 = max((k for k in 판들 if k.startswith("DA3")), key=lambda k: 요약[k]["IoU"])
    iou = 요약[최고]["IoU"]
    요약["판정"] = {"최고 판": 최고, "IoU": iou, "해석": "이 길로 간다" if iou >= 0.73 else ("일부 회수" if iou >= 0.60 else "아직 못 쓴다")}
    for k in 판들:
        print("  %-22s IoU %.3f 정밀 %.3f 재현 %.3f 비 %.2f" % (k, 요약[k]["IoU"], 요약[k]["정밀도"], 요약[k]["재현율"], 요약[k]["부피 비"]))
    print(json.dumps({k: 요약[k] for k in ("진단 앞 순위상관 중앙", "판정")}, ensure_ascii=False, indent=1))
    p = os.path.join(OUT, "기록", "깊이DA3_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(p)


if __name__ == "__main__":
    main()
