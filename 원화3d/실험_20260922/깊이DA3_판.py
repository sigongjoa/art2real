# -*- coding: utf-8 -*-
"""깊이 DA3 1 단계 — 얼린 10 케이스의 앞 · 옆 · 뒤 원화를 **창 좌표**(마스크와 같은 격자 · 흰 바탕)로 옮겨 PNG 로 둔다.
    python 깊이DA3_판.py   -> out/깊이DA3/<케이스>/<판>.png
2 단계(D:\ComfyUI venv 로 Depth Anything 3 Mono-Large)는 `깊이DA3_돌리기.py`."""
import os, sys
import numpy as np
import cv2
sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922"]
import hull as H
import 부품분할 as BB
import 깊이추정 as GC

D = os.path.join(H.OUT, "깊이DA3")


def 창그림(case, raw, p, v, 몸):
    im = cv2.imdecode(np.fromfile(os.path.join(H.art_dir(case), H.CASES[case]["src"][v]), np.uint8), cv2.IMREAD_UNCHANGED)
    rgb = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2RGB).astype(np.float32)
    if im.ndim == 3 and im.shape[2] == 4:
        rgb = np.where(im[:, :, 3:4] > 127, rgb, 255)
    d = H.declutter(raw[v])
    창 = np.dstack([H._warp_one(H.to_win(d, rgb[:, :, k])[1], v, p) for k in range(3)])
    창 = np.where(몸[..., None] > 0.5, 창, 255)
    return np.clip(창, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    for c in GC.케이스들:
        raw, masks, bs, p = BB.판(c)
        os.makedirs(os.path.join(D, c), exist_ok=True)
        for v in ("front", "side", "back"):
            a = 창그림(c, raw, p, v, masks[v])
            cv2.imencode(".png", cv2.cvtColor(a, cv2.COLOR_RGB2BGR))[1].tofile(os.path.join(D, c, v + ".png"))
            np.save(os.path.join(D, c, v + "_mask.npy"), masks[v] > 0.5)
        print(c, a.shape, bs, flush=True)
