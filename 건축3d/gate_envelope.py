# -*- coding: utf-8 -*-
"""**건물은 인물이 아니다.** `envelope.py` 대신 외형을 여기서 잰다.

    python gate_envelope.py art3d_front 11.0

스킬의 `envelope.py` 는 연결성 추적으로 실루엣을 딴다 — 배경 위에 인물 하나가 서 있는
그림을 전제한다. 정면 성당 그림은 **화면을 꽉 채우고** 배경과 붙어 있어 추적이
512행 중 139행에서 멈췄고, 그 결과 부품 159개가 「외형 밖」으로 잘려 나갔다.

여기서는 추적을 안 한다. `art3d.py` 가 **같은 화소 공간에서** 이미 뽑아둔
`mask.npy` 의 행별 폭을 그대로 외형으로 쓴다 — 맞출 게 없다(스킬이 말한 그 이유 그대로).
사람이 주는 절대값은 **건물 높이 하나**뿐이다.
"""
import json
import os
import sys

import numpy as np


def build(d, height_m):
    """`art3d.py` 출력 폴더 -> envelope.json. 돌려주는 건 (행 수, 최대 반폭 비율)."""
    m = np.load(os.path.join(d, "mask.npy"))
    if m.ndim == 3:
        m = m.any(axis=2)
    m = m.astype(bool)
    H, W = m.shape
    rows = np.nonzero(m.any(axis=1))[0]
    assert len(rows) > 8, "mask 가 비어 있다"
    y0, y1 = int(rows[0]), int(rows[-1])
    cx = float(np.nonzero(m)[1].mean())
    out = []
    for k in range(16):                                  # z 0(바닥) -> 1(꼭대기)
        z = k / 15.0
        y = int(round(y1 - z * (y1 - y0)))
        xs = np.nonzero(m[min(max(y, 0), H - 1)])[0]
        hw = (xs.max() - xs.min()) / 2.0 if len(xs) else 0.0
        out.append([round(z, 4), round(hw / float(W), 4)])
    wpp = height_m / float(y1 - y0)
    env = {"src": "measured(art3d mask.npy 행별 폭 — 추적 안 함)",
           "px": {"y_top": y0, "y_bot": y1, "center_x": round(cx, 1),
                  "world_per_px": round(wpp, 6), "scale": W},
           "rows": out}
    json.dump(env, open(os.path.join(d, "envelope.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return len(out), max(v for _, v in out)


def demo():
    """가운데가 넓고 위가 좁은 가짜 마스크로, 행별 반폭이 위로 갈수록 주는지만 본다."""
    import tempfile
    d = tempfile.mkdtemp()
    H, W = 200, 100
    m = np.zeros((H, W), bool)
    for y in range(H):
        half = int(4 + 40 * (y / (H - 1.0)))             # 아래가 넓다
        m[y, W // 2 - half:W // 2 + half] = True
    np.save(os.path.join(d, "mask.npy"), m)
    n, mx = build(d, 10.0)
    e = json.load(open(os.path.join(d, "envelope.json"), encoding="utf-8"))
    assert n == 16 and e["px"]["y_top"] == 0 and e["px"]["y_bot"] == H - 1
    r = [v for _, v in e["rows"]]
    assert r[0] > r[-1], r                               # z 0 = 바닥이 제일 넓다
    assert abs(e["px"]["world_per_px"] - 10.0 / (H - 1)) < 1e-6
    print("gate_envelope.demo OK  행 %d  최대 반폭 %.3f" % (n, mx))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        print(build(sys.argv[1], float(sys.argv[2])))
