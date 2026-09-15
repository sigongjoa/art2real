# -*- coding: utf-8 -*-
"""**깨짐 지표 — IoU 가 못 보는 모양 붕괴** (2026-09-15).

    python 깨짐.py 검사     자가검사만
    python 깨짐.py [n]      아직 안 한 장 n 개 -> out/기록/깨짐_진행.jsonl
    python 깨짐.py 표       옛 기본 대 새 기본 표

점수판 판정(IoU 중앙)이 궤짝 · 드릴 · 로봇형 마법사의 얇은 판 · 원통화를 못 봤다 (사용자 09-15 「2 · 4 · 5 · 6 번이 심각하게 이상」).

    얇은판   세로(z)로 3칸 이하만 이어진 복셀의 몫 — 뚜껑 가장자리 · 막처럼 떠 있는 판
    조각     떨어진 덩어리 수 (`표면.pieces`, 50칸 이상) — 원형이면 1
    찢김     앞면이 위아래 줄끼리 3칸 넘게 튄 쌍의 몫 (`표면.tear`)
    창잘림   hull 복셀 중 격자 가로 · 깊이 끝 칸에 닿은 몫 — 물건이 작업 창보다 넓어 잘린 것
"""
import json
import os
import sys
import time

import numpy as np
import trimesh
from scipy import ndimage

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260915"))
os.chdir(HERE)
import hull as H
import 대조 as C
import 오라클 as O
import 표면 as SF
from 겉면채점 import bench_cases

PROG = os.path.join(HERE, "out", "기록", "깨짐_진행.jsonl")
TAG = "깨짐 · 실물28 · 옛 기본(파이프 lam0.20) · 새 기본(carve_default) · 얇은판≤3 · 조각 · 찢김 · 창잘림 (2026-09-15)"
_ZST = np.zeros((3, 3, 3), bool)
_ZST[1, 1, :] = True


def thin_share(vox, k=3):
    lab, _ = ndimage.label(vox, structure=_ZST)
    run = np.bincount(lab.ravel())[lab]
    return float((vox & (run <= k)).sum() / max(int(vox.sum()), 1))


def clip_share(vox):
    edge = np.zeros(vox.shape, bool)
    edge[0], edge[-1], edge[:, 0], edge[:, -1] = True, True, True, True
    return float((vox & edge).sum() / max(int(vox.sum()), 1))


def metrics(vox, plain):
    return {"얇은판": round(thin_share(vox), 5), "조각": SF.pieces(vox), "찢김": round(SF.tear(vox), 4), "창잘림": round(clip_share(plain), 5)}


def one(c):
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
    plain, old, _, _ = O.build(c, truth, H.LAM, "파이프")
    plain2, new, _, _ = C.build(c)
    return {"case": c, "판": TAG, "옛": metrics(old, plain), "새": metrics(new, plain2), "초": round(time.time() - t0, 1)}


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[r["case"]] = r
    return out


def table():
    rs = rows()
    sb = {r["case"]: r for r in map(json.loads, open(os.path.join(HERE, "out", "기록", "점수판_진행.jsonl"), encoding="utf-8"))}
    print("  %-30s %8s %8s | %5s %5s | %6s %6s | %7s | IoU 옛→새" % ("케이스", "얇은 옛", "얇은 새", "조각옛", "조각새", "찢김옛", "찢김새", "창잘림"))
    for c in sorted(rs, key=lambda c: -rs[c]["새"]["얇은판"]):
        o, n = rs[c]["옛"], rs[c]["새"]
        s = sb.get(c)
        print("  %-30s %8.4f %8.4f | %5d %5d | %6.3f %6.3f | %7.4f | %s" % (c[:30], o["얇은판"], n["얇은판"], o["조각"], n["조각"], o["찢김"], n["찢김"], n["창잘림"],
              "%.3f→%.3f" % (s["옛"][1], s["새"][1]) if s else "-"))


def selfcheck():
    v = np.zeros((20, 20, 30), bool)
    v[5:15, 5:15, 0:20] = True                       # 기둥 20칸
    v[2:18, 2:18, 25:27] = True                      # 떠 있는 판 2칸
    t = thin_share(v)
    assert abs(t - (16 * 16 * 2) / v.sum()) < 1e-9, "얇은 판 몫 %s" % t
    e = np.zeros((8, 8, 4), bool)
    e[0, 3, 1] = e[4, 4, 1] = True
    assert clip_share(e) == 0.5, "창 잘림"
    print("  자가검사 통과 — 얇은 판 · 창 잘림")


def main():
    selfcheck()
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        return
    if a != "표":
        done = rows()
        for c in [c for c in bench_cases() if c != "소체" and c not in done][:int(a)]:
            r = one(c)
            with open(PROG, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print("  %-28s 옛 %s · 새 %s · %.0f초" % (c[:28], r["옛"], r["새"], r["초"]), flush=True)
    table()


if __name__ == "__main__":
    main()
