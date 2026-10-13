# 쇼츠 53 재료 — 바깥 선 찾기 · 원 판정 · 꼭짓점 줄이기를 그림으로 보이기 위한 숫자(npz) · 10-13
import os, sys, json, numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 캐드점수2 as K, 윤곽바탕 as B, 진짜그림52 as R
O = "G:/art2real/out/영상05/대화/53_바깥선/자료/"; os.makedirs(O, exist_ok=True)
S = json.load(open("G:/art2real/out/설명/구멍/학습2/스냅.json", encoding="utf-8"))
im = np.asarray(Image.open(R.IMG).convert("RGB")); r0, r1, c0, c1 = R.부위["머리"]
for 이름, g in (("머리", R.입력(im[r0:r1, c0:c1])), ("원기둥", K.그림(S["정답"][3])), ("상자", K.그림(S["정답"][5]))):
    선 = ((g > .3) * 255).astype(np.uint8); 선 = cv2.morphologyEx(선, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    밖 = np.zeros((130, 130), np.uint8); 밖[1:-1, 1:-1] = 선 > 0   # 테두리에서 물 붓기: 선이 아닌 칸을 BFS 로 번지는 순서(걸음 수)
    물 = np.full((130, 130), -1, np.int32); q = [(0, x) for x in range(130)] + [(129, x) for x in range(130)] + [(y, 0) for y in range(130)] + [(y, 129) for y in range(130)]
    for y, x in q: 물[y, x] = 0
    i = 0
    while i < len(q):
        y, x = q[i]; i += 1
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < 130 and 0 <= xx < 130 and 물[yy, xx] < 0 and not 밖[yy, xx]: 물[yy, xx] = 물[y, x] + 1; q.append((yy, xx))
    m, ct = B.바깥(g); f = B.맞추기(ct); (cx, cy), _ = cv2.minEnclosingCircle(ct.astype(np.float32)); 거리 = np.hypot(ct[:, 0] - cx, ct[:, 1] - cy)
    p = cv2.approxPolyDP(ct.reshape(-1, 1, 2).astype(np.float32), 1.5, True)[:, 0, :]
    np.savez(O + 이름 + ".npz", 그림=g, 물=물[1:-1, 1:-1], 윤곽=ct, 중심=np.array([cx, cy]), 거리=거리, 꼭짓점=p, 원=np.array([f[0] == "원"]), 흩어짐=np.array([거리.std() / 거리.mean()]))
    print(이름, f[0], "꼭짓점", len(p), "윤곽점", len(ct), "흩어짐 %.3f" % (거리.std() / 거리.mean()))
