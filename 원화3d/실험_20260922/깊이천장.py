# -*- coding: utf-8 -*-
"""**깊이 천장** — 넘친 부피 중 「보이는 면의 깊이를 알면」 깎이는 몫과 세 판 모두에서 안 보이는 몫을 가른다 (2026-09-22).

    python 깊이천장.py      얼린 10 케이스 -> out/기록/깊이천장_<때>.json

부피 벤치(`부피벤치.py`): hull 은 정답의 1.69 배 · 정밀도 0.57. 타원 가정은 IoU 를 못 올렸다(0.56 = 0.56).
삼면도는 윤곽만 주고 깊이를 안 준다. 그러면 **각 판에서 보이는 겉면의 깊이를 완벽히 안다면**(깊이 신탁) 얼마나 깎이나?

    깊이 신탁   정답 부피 T(`정답.grid(봉합=1)`, 우리 격자) 에서 판마다 첫 닿는 깊이를 읽어 hull 을 깎는다.
                앞 = -y 에서, 뒤 = +y 에서, 옆 = +x 에서 (`win.VIEW_AXIS` 계약). 정답이 없는 기둥은 통째로 비운다.
    판 넷       hull  ·  신탁 앞뒤  ·  신탁 앞뒤옆  ·  (참고) 타원
    나머지      신탁 앞뒤옆 뒤에도 남는 넘침 = 세 판 어디서도 안 보이는 오목 — 깊이로는 못 없앤다

검산(돌리기 전): 신탁은 정답 복셀을 못 지운다 -> 신탁 재현율 ≥ hull 재현율 − 0.01 (assert).
대조(첫 결과 0.905 를 본 뒤 · 신탁이 순환이 아닌지 — 09-22 천장 160 교훈): 신탁이 뜻있으려면
    평면   판마다 깊이를 한 값(정답의 가장 앞 · 가장 뒤)으로 — IoU 가 hull + 0.05 이하여야 한다
    오차   보이는 깊이를 바깥쪽으로 k 칸 틀리게(k = 3 · 8) — 깊이가 얼마나 정확해야 하나
해석 문턱(돌리기 전 · 신탁 앞뒤옆 IoU 중앙):
    ≥ 0.80   깊이가 지렛대다 — 다음은 그림에서 깊이를 읽는 쪽(먹선 · 음영 · 사전)
    < 0.70   보이는 깊이를 다 알아도 모자라다 — 안 보이는 속(가림)이 크다. 사전 · 부품 틀이 필요
    사이     둘 다
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260922")
import hull as H
import 정답 as JD
import 부품분할 as BB
import 도면벤치_천장 as DC
import 부피벤치 as PB
import 깊이추정 as GC

OUT = H.OUT
판들 = ("hull", "신탁 앞뒤", "신탁 앞뒤옆", "타원", "대조 평면", "오차 3칸", "오차 8칸")


def 깊이판(O, T, axis, 앞에서, k=0, 평면=False):
    """판마다 첫 닿는 깊이(인덱스)로 깎는다. k = 바깥쪽 오차(칸) · 평면 = 모든 기둥에 한 깊이."""
    n = T.shape[axis]
    idx = np.arange(n).reshape([-1 if a == axis else 1 for a in range(3)])
    있음 = T.any(axis=axis, keepdims=True)
    if 앞에서:
        d = np.where(있음, np.expand_dims(np.argmax(T, axis=axis), axis), n)
        if 평면: d = np.full_like(d, d[있음].min())
        return O & (idx >= d - k)
    d = np.where(있음, n - 1 - np.expand_dims(np.argmax(np.flip(T, axis), axis=axis), axis), -1)
    if 평면: d = np.full_like(d, d[있음].max())
    return O & (idx <= d + k)


def 셋(O, T, **kw):
    return 깊이판(깊이판(깊이판(O, T, 1, True, **kw), T, 1, False, **kw), T, 0, False, **kw)


def 깎기(O, T, axis, 앞에서):
    """axis 방향 기둥마다 T 의 첫 닿는 칸 앞(앞에서=True 면 작은 인덱스 쪽)을 O 에서 지운다. T 없는 기둥은 통째로."""
    n = T.shape[axis]
    idx = np.arange(n).reshape([-1 if k == axis else 1 for k in range(3)])
    있음 = T.any(axis=axis, keepdims=True)
    if 앞에서:
        첫 = np.where(있음, np.argmax(T, axis=axis)[..., None].swapaxes(-1, axis) if False else np.expand_dims(np.argmax(T, axis=axis), axis), n)
        return O & (idx >= 첫)
    끝 = np.where(있음, n - 1 - np.expand_dims(np.argmax(np.flip(T, axis), axis=axis), axis), -1)
    return O & (idx <= 끝)


def 검사():
    T = np.zeros((1, 6, 1), bool); T[0, 2:4, 0] = True
    O = np.ones_like(T)
    assert 깎기(O, T, 1, True)[0, :, 0].tolist() == [0, 0, 1, 1, 1, 1]
    assert 깎기(O, T, 1, False)[0, :, 0].tolist() == [1, 1, 1, 1, 0, 0]
    assert not 깎기(O, np.zeros_like(T), 1, True).any()


def 한케이스(c):
    raw, masks, bs, p = BB.판(c)
    tm = trimesh.load(os.path.join(OUT, "시트", c, "truth.glb"), force="mesh")
    A, o = JD.grid(tm, 봉합=1)
    gh, ax = H.field_hull(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
    Oh = gh > 0
    앞뒤 = 깎기(깎기(Oh, T, 1, True), T, 1, False)          # 앞 = -y (작은 y 인덱스) · 뒤 = +y
    앞뒤옆 = 깎기(앞뒤, T, 0, False)                        # 옆 = +x 에서 (큰 x 인덱스 쪽을 깎는다)
    ge, _ = H.field_default(masks, back_sign=bs, n=BB.N)
    판 = (("hull", Oh), ("신탁 앞뒤", 앞뒤), ("신탁 앞뒤옆", 앞뒤옆), ("타원", ge > 0),
          ("대조 평면", 셋(Oh, T, 평면=True)), ("오차 3칸", 셋(Oh, T, k=3)), ("오차 8칸", 셋(Oh, T, k=8)))
    r = {k: PB.재기(M, T) for k, M in 판}
    assert (셋(Oh, T) == 앞뒤옆).all()
    넘침 = (Oh & ~T).sum()
    r["넘침 중 깊이로 깎이는 몫"] = float(1 - (앞뒤옆 & ~T).sum() / max(넘침, 1))
    assert r["신탁 앞뒤옆"]["재현율"] >= r["hull"]["재현율"] - 0.01, (c, r)
    return r


def main():
    검사()
    기록 = {}
    for c in GC.케이스들:
        t0 = time.time()
        기록[c] = r = 한케이스(c)
        print("  %-38s " % c + " | ".join("%s %.2f" % (k, r[k]["IoU"]) for k in 판들)
              + " | 넘침 깎임 %.0f%%  %.0f초" % (100 * r["넘침 중 깊이로 깎이는 몫"], time.time() - t0), flush=True)
    요약 = {k: {m: float(np.median([r[k][m] for r in 기록.values()])) for m in ("IoU", "정밀도", "재현율", "부피 비")}
          for k in 판들}
    요약["넘침 중 깊이로 깎이는 몫 중앙"] = float(np.median([r["넘침 중 깊이로 깎이는 몫"] for r in 기록.values()]))
    iou = 요약["신탁 앞뒤옆"]["IoU"]
    요약["대조 통과(평면 ≤ hull + 0.05)"] = 요약["대조 평면"]["IoU"] <= 요약["hull"]["IoU"] + 0.05
    요약["해석"] = "깊이가 지렛대" if iou >= 0.80 else ("안 보이는 속이 크다" if iou < 0.70 else "둘 다")
    print("\n" + json.dumps(요약, ensure_ascii=False, indent=1))
    p = os.path.join(OUT, "기록", "깊이천장_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "케이스": 기록}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(p)


if __name__ == "__main__":
    main()
