# -*- coding: utf-8 -*-
"""**진짜 물건은 VH 를 얼마나 채우나** — 심사위원 주장을 정답으로 판정한다 (2026-09-21).

    python 정답채움.py   -> out/기록/정답채움_<때>.json

심사(Grok · 1 라운드): 「retention 0.73 은 **과충전** 신호다. 이상적인 값은 **0.4~0.6**」.
측정 근거가 없는 주장이다. 벤치에는 **정답 메시**가 있으니 직접 잰다:

    정답 retention = Vol(정답) / Vol(VH)      VH = 정답의 **진짜 실루엣 세 장**의 교집합

이게 0.4~0.6 이면 Grok 이 맞고, 우리 0.73 은 과충전이다.
0.73 근처거나 더 크면 Grok 이 틀렸고, 우리 타원 가정은 오히려 **덜** 채우는 쪽이다.

`정답.ceiling` 이 이미 `vol = Vol(VH)/Vol(정답)` 을 낸다 — 그 역수다. 새 자를 안 만든다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np

sys.path.insert(0, r"G:\art2real\원화3d")
import hull as H
import 정답 as JD
OUT = H.OUT


def main():
    H.register_sheets()
    cases = [c for c in H.CASES if os.path.exists(os.path.join(OUT, "시트", c, "truth.glb"))]
    표 = []
    for c in cases:
        try:
            r = JD.ceiling(c)
        except Exception as e:                                          # 한 케이스가 깨져도 나머지는 잰다
            print("  %-32s 실패: %s" % (c, str(e)[:60]), flush=True)
            continue
        ret = 1.0 / r["vol"] if r["vol"] else float("nan")
        표.append({"case": c, "Vol(VH)/Vol(정답)": round(float(r["vol"]), 4), "정답 retention": round(ret, 4)})
        print("  %-32s 정답 retention %.3f" % (c, ret), flush=True)
    ret = np.array([r["정답 retention"] for r in 표 if np.isfinite(r["정답 retention"])])
    요약 = {"케이스": int(len(ret)), "중앙": round(float(np.median(ret)), 3),
            "사분위": [round(float(np.percentile(ret, 25)), 3), round(float(np.percentile(ret, 75)), 3)],
            "최소": round(float(ret.min()), 3), "최대": round(float(ret.max()), 3),
            "Grok 구간 0.4~0.6 에 든 몫": round(float(((ret >= 0.4) & (ret <= 0.6)).mean()), 3),
            "우리 0.7312 보다 큰 몫": round(float((ret > 0.7312).mean()), 3)}
    print("\n  요약 %s" % 요약, flush=True)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"표": 표, "요약": 요약, "주장": "Grok 1 라운드 — 이상 retention 0.4~0.6"},
              open(os.path.join(OUT, "기록", "정답채움_%s.json" % time.strftime("%Y%m%d_%H%M")), "w",
                   encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
