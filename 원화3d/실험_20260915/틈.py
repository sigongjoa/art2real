# -*- coding: utf-8 -*-
"""**실루엣 틈 — 입력 측정 (연구 루프 1)** (2026-09-15).

    python 틈.py 검사     자가검사만
    python 틈.py          실물 28장 -> out/기록/틈_입력.json (표 출력)
    python 틈.py 그림 [케이스]  -> out/틈_<케이스>.png

물음: 새 기본(타원)의 얇은 판은 hull 단면이 1 화소 틈으로 갈라져 조각마다 납작한 타원이 들어가서 생긴다 (`out/얇은판_단면.png`).
그 틈은 어디서 생기나 — ① 렌더 알파 ② `declutter` ③ `to_win` 앉히기 ④ `align` 워프.

    틈      시점 마스크를 3×3 닫기로 메워지는 화소 / 마스크 화소 (2 화소 이하 틈)
    갈림    hull 단면(높이마다)을 3×3 닫기 전 · 뒤 조각 수 차이의 합 — 틈 때문에 늘어난 조각
"""
import json
import os
import sys

import cv2
import numpy as np
from scipy import ndimage

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260915"))
os.chdir(HERE)
import hull as H
import win as W
from 겉면채점 import bench_cases

OUTJ = os.path.join(HERE, "out", "기록", "틈_입력.json")
K3 = np.ones((3, 3), bool)


def gap_share(m):
    return float((ndimage.binary_closing(m, K3) & ~m).sum() / max(int(m.sum()), 1))


def stages(case):
    """단계마다 시점 마스크 — 알파 · declutter · to_win · align 워프."""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    dec = {v: H.declutter(m) for v, m in raw.items()}
    win = {v: H.to_win(m) for v, m in dec.items()}
    p = H.align(win, back_sign=H.CASES[case]["back_sign"])
    return {"알파": raw, "declutter": dec, "to_win": win, "align": H._warp(win, p)}


def split_count(plain):
    """높이마다 hull 단면 조각 수 — 닫기 전 · 뒤. 틈이 늘린 조각의 합과, 그런 높이의 수."""
    extra, rows = 0, 0
    for k in np.nonzero(plain.any((0, 1)))[0]:
        s = plain[:, :, k]
        a = ndimage.label(s)[1]
        b = ndimage.label(ndimage.binary_closing(s, K3) | s)[1]
        if a > b:
            extra += a - b
            rows += 1
    return extra, rows


def one(case):
    st = stages(case)
    row = {v: {name: round(gap_share(ms[v]), 5) for name, ms in st.items()} for v in W.VIEWS}
    plain, _ = H.carve(st["align"], back_sign=H.CASES[case]["back_sign"])
    row["갈림"] = dict(zip(("늘어난 조각", "갈린 높이"), split_count(plain)))
    return row


def figure(case):
    """side 마스크의 알파 · to_win · align 단계 — 틈 화소를 빨강으로."""
    st = stages(case)
    tiles = []
    for name in ("알파", "to_win", "align"):
        m = st[name]["side"]
        gap = ndimage.binary_closing(m, K3) & ~m
        im = np.full(m.shape + (3,), 255, np.uint8)
        im[m] = (170, 170, 170)
        im[ndimage.binary_dilation(gap, iterations=3)] = (40, 40, 230)
        tiles.append(cv2.resize(im, (512, 512), interpolation=cv2.INTER_NEAREST))
    p = os.path.join(HERE, "out", "틈_%s.png" % case)
    cv2.imencode(".png", np.hstack(tiles))[1].tofile(p)
    print("  -> %s (왼쪽부터 알파 · to_win · align, 빨강 = 틈)" % p)


def selfcheck():
    m = np.zeros((40, 40), bool)
    m[5:35, 5:35] = True
    assert gap_share(m) == 0, "꽉 찬 사각에 틈이 있다"
    m[20, 5:35] = False                                        # 1 화소 가로 금
    assert abs(gap_share(m) - 30 / m.sum()) < 1e-9, "1 화소 금을 못 센다 %s" % gap_share(m)
    v = np.zeros((20, 20, 3), bool)
    v[2:18, 2:9, 1] = v[2:18, 10:18, 1] = True                 # 1 화소 틈으로 갈린 단면
    v[2:18, 2:18, 2] = True
    assert split_count(v) == (1, 1), "갈림 %s" % (split_count(v),)
    print("  자가검사 통과 — 틈 몫 · 단면 갈림")


def main():
    selfcheck()
    a = sys.argv[1:]
    if a[:1] == ["검사"]:
        return
    if a[:1] == ["그림"]:
        return figure(a[1] if len(a) > 1 else "cloak_Chest_Closed_AngpV0HxD8")
    out = {}
    for c in [c for c in bench_cases() if c != "소체"]:
        out[c] = one(c)
        r = out[c]
        print("  %-28s " % c[:28] + " · ".join("%s 알파 %.4f→align %.4f" % (v[0], r[v]["알파"], r[v]["align"]) for v in W.VIEWS)
              + " · 늘어난 조각 %d (높이 %d)" % (r["갈림"]["늘어난 조각"], r["갈림"]["갈린 높이"]), flush=True)
    json.dump(out, open(OUTJ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  -> %s" % OUTJ)


if __name__ == "__main__":
    main()
