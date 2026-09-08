# -*- coding: utf-8 -*-
"""재질맵을 메시 공간으로 되돌리고 클래스별 연결성분에 파츠 ID 를 붙인다.

    D:\imggen\venv\Scripts\python.exe build_partmaps.py

블렌더 파이썬에는 cv2 가 없어서 여기서 만들어 .npy 로 넘긴다.
FIT 은 step3b 격자탐색 실측값 — 판이 메시보다 이만큼 이동/축소돼 있다.
"""
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = 1024
# 정렬 상수는 fit_search.py 가 찾아 fit.json 에 넣는다. 여기에 박아두면
# 갱신할 때 파일마다 고쳐야 하고 실제로 한 번 엇갈렸다.
import json as _json
FIT = {k: tuple(v) for k, v in
       _json.load(open(os.path.join(HERE, "fit.json"))).items()}
MIN_BLOB = 260          # 먹선 부스러기 컷

meta_all = {}
for k, (dx, dy, s) in FIT.items():
    q = np.load(os.path.join(HERE, f"win_{k}.npy"))
    yy, xx = np.mgrid[0:RES, 0:RES]
    c = RES / 2
    # step3b 격자탐색은 "**메시**를 s배 축소하고 (dx,dy) 옮기면 원화" 였다.
    # 원화를 메시 공간으로 가져오려면 메시좌표 x -> 원화좌표 s*(x-c)+c+dx 로 표본한다.
    # 같은 식을 원화에 그대로 걸면 방향이 뒤집혀 IoU 0.729 -> 0.478 로 떨어진다.
    sx = np.clip(np.rint(s * (xx - c) + c + dx), 0, RES - 1).astype(int)
    sy = np.clip(np.rint(s * (yy - c) + c + dy), 0, RES - 1).astype(int)
    q = q[sy, sx]
    pid = np.zeros_like(q, np.int32)
    meta, nid = {}, 0
    for cls in (1, 2, 3):
        m = cv2.morphologyEx((q == cls).astype(np.uint8), cv2.MORPH_OPEN,
                             np.ones((3, 3), np.uint8))
        n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
        for i in range(1, n):
            if st[i][4] < MIN_BLOB:
                continue
            nid += 1
            pid[lab == i] = nid
            meta[nid] = {"cls": cls, "px": int(st[i][4]),
                         "bbox": [int(v) for v in st[i][:4]]}
    np.save(os.path.join(HERE, f"pid_{k}.npy"), pid)
    np.save(os.path.join(HERE, f"cls_{k}.npy"), q.astype(np.uint8))
    meta_all[k] = meta
    per = {c: sum(1 for v in meta.values() if v["cls"] == c) for c in (1, 2, 3)}
    print(f"{k:6s} 파츠 {nid:3d}개  (갑주 {per[1]}, 검정 {per[2]}, 금색 {per[3]})")
json.dump(meta_all, open(os.path.join(HERE, "partmeta.json"), "w"), indent=1)
print("pid_*.npy / cls_*.npy / partmeta.json")
