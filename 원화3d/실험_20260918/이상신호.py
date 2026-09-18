# -*- coding: utf-8 -*-
"""**이상 신호 — 수리를 언제 부르나** (2026-09-18).

    python 이상신호.py 검사      자가검사 (답을 아는 도형)
    python 이상신호.py [n]       아직 안 한 장 n 개 -> out/기록/이상신호_진행.jsonl
    python 이상신호.py 판정      -> out/기록/이상신호_<때>.json
    python 이상신호.py 그림      순위대로 줄 세운 명암 접촉지 -> out/이상신호.png

사용자 결정 (09-18): 「TripoSG만 하고, 서페이스가 이상하다라고 하면 추가적으로 돌린다」.
그러려면 **「이상하다」를 부르는 신호**가 있어야 한다. 새 지표를 만들지 않는다 — 이미 있는 다섯을 모은다.

    못덮음    원화를 안 지킨 몫 (시점 최대)        `앨리어싱.reproject`  ∩hull 뒤엔 0 이어야 정상
    가는곳    칼 · 뿔 · 가시가 남은 몫 (최소)       `앨리어싱.reproject`  낮을수록 먹혔다
    조각      떨어진 덩어리 수                     `표면.pieces`        출력 원형이면 1
    찢김      앞면이 줄끼리 튄 쌍의 비율            `표면.tear`          정답이 2~11%
    실루엣    hull 실루엣 중 잃은 몫                `표면.sil_loss`      약속이라 0 이어야 한다

    불일치    생성∩hull+보충 과 지금 기본이 서로 다른 몫   **실패 — 점수에 안 넣는다** (아래)

**이상 점수 = 다섯 신호의 순위 평균.** 가중치를 안 고른다 (고르면 원하는 답에 자를 맞추게 된다).

판정은 사람 눈이다 — 순위대로 줄 세운 명암 그림에서 **위쪽이 정말 더 이상한가**. 숫자로는 못 답한다
(09-15: IoU 중앙 판정이 「심각하게 이상」한 넷을 못 봤다).
"""
import json
import os
import sys
import time

import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
for d in ("실험_20260913", "실험_20260915", "실험_20260916"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import hull as H
import win as W
import 표면 as SF
import 앨리어싱 as AL
import 대조 as C
from 겉면채점 import bench_cases
from 생성깎기 import variants as gen_variants

PROG = os.path.join(HERE, "out", "기록", "이상신호_진행.jsonl")
TAG = "이상신호 v2 · 실물28 · 생성∩hull+보충 · 지금 기본 · 신호 다섯 (2026-09-18)"
VARS = ("생성∩hull+보충", "지금 기본")
SIGNALS = ("못덮음", "가는곳", "조각", "찢김", "실루엣")          # 점수에 쓰는 것
WORSE = {"못덮음": +1, "가는곳": -1, "조각": +1, "찢김": +1, "실루엣": +1}   # +1 이면 클수록 이상
# **불일치는 재기만 하고 점수에 안 넣는다 — 돌려 보니 안 된다.** 「모양이 통째로 틀린 것」(궤짝 · 모자)을 겨냥해
# 더했는데, 정작 그 둘은 0.196 · 0.226 으로 낮고 **깨끗한 긴 드레스 장이 0.643 으로 1위**를 먹는다
# (치마 속을 두 길이 다르게 채우는 몫이지 틀림이 아니다). 기록에는 남긴다.


def signals(vox, plain, masks, bs, axes):
    mesh = C.to_mesh(vox, axes)
    rp = AL.reproject(mesh, masks, bs)
    return {"못덮음": round(max(rp[v]["miss"] for v in W.VIEWS), 4),
            "가는곳": round(min(rp[v]["thin"] for v in W.VIEWS), 4),
            "조각": SF.pieces(vox),
            "찢김": round(SF.tear(vox), 4),
            "실루엣": round(SF.sil_loss(vox, plain), 4)}


def one(case):
    t0 = time.time()
    vs, plain, axes, masks, bs = gen_variants(case)
    out = {"case": case, "판": TAG, "초": None}
    a, b = vs["생성∩hull+보충"], vs["지금 기본"]
    # **불일치** — 정답 없이 쓸 수 있는 유일한 신호. 두 길로 지은 것이 서로 다르면 둘 중 하나가 틀렸다.
    # 다섯 신호가 못 잡은 실패(모양이 통째로 틀린 것)를 겨냥해 더했다 (짝 그림에서 궤짝 · 모자가 낮게 나왔다)
    dis = round(float(1 - (a & b).sum() / max((a | b).sum(), 1)), 4)
    for n in VARS:
        vox = a if n == "생성∩hull+보충" else b
        out[n] = signals(vox, plain, masks, bs, axes)
        out[n]["불일치"] = dis
    out["초"] = round(time.time() - t0, 1)
    return out


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[r["case"]] = r
    return out


def run(n):
    done = rows()
    todo = [c for c in bench_cases() if c != "소체" and c not in done][:n]
    for c in todo:
        r = one(c)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        g = r["생성∩hull+보충"]
        print("  %-36s 못덮음 %.3f · 가는곳 %.3f · 조각 %d · 찢김 %.3f · 실루엣 %.3f · %.0f초"
              % (c, g["못덮음"], g["가는곳"], g["조각"], g["찢김"], g["실루엣"], r["초"]), flush=True)


def ranked(var="생성∩hull+보충"):
    """이상 점수 = 다섯 신호의 순위 평균 (1 = 제일 멀쩡, n = 제일 이상)."""
    rs = list(rows().values())
    rs.sort(key=lambda r: r["case"])
    names = [r["case"] for r in rs]
    ranks = np.zeros((len(SIGNALS), len(rs)))
    for i, s in enumerate(SIGNALS):
        v = np.array([float(r[var][s]) for r in rs]) * WORSE[s]
        ranks[i] = v.argsort().argsort() + 1                    # 큰 값(=이상)이 높은 순위
    score = ranks.mean(0)
    order = np.argsort(-score)
    return [(names[i], round(float(score[i]), 2), rs[i][var]) for i in order]


def verdict():
    rs = rows()
    assert len(rs) >= 28, "%d 장만 돌았다" % len(rs)
    v = {"판": TAG, "n": len(rs), "신호": SIGNALS,
         "순위": [{"case": c, "이상점수": s, **d} for c, s, d in ranked()],
         "중앙": {n: {s: round(float(np.median([r[n][s] for r in rs.values()])), 4) for s in SIGNALS} for n in VARS},
         "판정": "사람 눈 — out/이상신호.png 위쪽이 정말 더 이상한가"}
    p = os.path.join(HERE, "out", "기록", "이상신호_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  중앙", json.dumps(v["중앙"], ensure_ascii=False))
    for c, s, d in ranked()[:8]:
        print("  %5.2f  %-36s %s" % (s, c, json.dumps(d, ensure_ascii=False)))
    print("  ->", p)
    return v


def selfcheck():
    """신호가 답을 아는 도형에서 옳은 쪽을 가리키나."""
    a = np.zeros((40, 40, 40), bool)
    a[10:30, 10:30, 5:35] = True                                # 멀쩡한 상자 하나
    b = a.copy()
    b[10:30, 10:30, 18:22] = False                              # 허리를 끊어 두 조각으로
    assert SF.pieces(a) == 1 and SF.pieces(b) == 2, "조각 수가 틀렸다"
    c = a.copy()
    c[10:30, 10:20, 20:] = False                                # 위쪽 앞면을 10칸 물리기 -> 찢김
    assert SF.tear(c) > SF.tear(a), "찢김이 안 잡힌다 (%.3f 대 %.3f)" % (SF.tear(c), SF.tear(a))
    assert SF.sil_loss(b, a) > 0 and SF.sil_loss(a, a) == 0, "실루엣 손실이 틀렸다"
    r = [1.0, 3.0, 2.0]
    assert list(np.array(r).argsort().argsort() + 1) == [1, 3, 2], "순위 매기기가 틀렸다"
    print("  자가검사 통과 — 조각 · 찢김 · 실루엣 · 순위")


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        selfcheck()
    elif a == "판정":
        verdict()
    elif a == "그림":
        import 이상신호그림
        이상신호그림.main()
    else:
        H.register_sheets()
        run(int(a))


if __name__ == "__main__":
    main()
