# -*- coding: utf-8 -*-
"""창 모듈 — 깊은 창 + 립 (10-04 · 창깊이 옆 17.1 · 3/4 17.4 → 「ㄱㄱ」).
숫자는 전부 잰 것: 창 깊이 17(옆 · 3/4 평균) · 립 두께 3.7(옆) · 창 모양 = 정면 눈구멍 · 눈 칸(부품ID H03) · 벽 범위 = 정면 층 L7 − 10 ~ L4 · 축 E' ~ E.
가정(표시): 벽은 평평한 판(두께 6) — 얼굴 곡면은 다음 단계 · 립은 창 윗변을 따라 앞으로 2 내민 띠(내민 길이는 옆에서 0 에 가까워 2 로 둠).
깊이 d: 속머리 눈 앞 = 0 · 앞 = − (기준선 옆 축과 같음). 창 입구(벽 앞면) = −17.
출력 out/오메가몬2/블렌더/창모듈.ply · 창모듈_비교.png(정면 원화 위 윤곽 · 렌더 정면 · 옆 · 3/4)"""
import os, json, numpy as np, cv2, trimesh
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; B = r"G:\art2real\원화3d\out\오메가몬2\블렌더"
기준 = json.load(open(os.path.join(O, "기준선.json"), encoding="utf-8")); 층, 축 = 기준["층(정면 판 화소 행)"], 기준["정면 축(판 화소 열)"]
깊이 = json.load(open(os.path.join(O, "창깊이.json"), encoding="utf-8")); D = round((깊이["창 깊이(옆 · 입구 → 눈)"] + 깊이["창 깊이(3/4 · 옆벽 폭 / sin 35°)"]) / 2, 1); 립 = 깊이["눈썹 턱 두께(옆)"]
대응 = json.load(open(os.path.join(O, "부품ID.json"), encoding="utf-8"))["대응표"]["1"]
z = np.load(os.path.join(O, "1.npz")); L = z["라벨"]; yy, xx = np.nonzero(L > 0); y0, x0 = yy.min(), xx.min()
m = np.load(os.path.join(O, "판_1_Z.npz"))["m"]; H, W = m.shape; py, px = np.mgrid[0:H, 0:W]
cell = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)] * m
창칸 = [c for e in 대응 if e.get("부품") == "H03 눈 조립" and e.get("표면") in ("눈구멍", "눈") for c in e["칸"]]
창 = np.isin(cell, 창칸); 창 = cv2.morphologyEx(창.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
xl, xr = sorted([축["E' 볼날개 끝 L"], 축["E 볼날개 끝 R"]]); top, bot = 층["L7 뿔 뿌리"] - 10, 층["L4 코판 끝"]
벽 = m & (py >= top) & (py <= bot) & (px >= xl) & (px <= xr) & ~창
cu = (np.nonzero(m)[1].min() + np.nonzero(m)[1].max()) / 2
def 판(mask, d_front, 두께, col):
    ys, xs = np.nonzero(mask); vid = -np.ones(mask.shape, int); vid[ys, xs] = np.arange(len(ys)); n = len(ys)
    Vf = np.c_[xs - cu, np.full(n, d_front), -ys.astype(float)]; Vb = Vf + [0, 두께, 0]
    a, b, c, d = vid[:-1, :-1], vid[:-1, 1:], vid[1:, :-1], vid[1:, 1:]; ok = (a >= 0) & (b >= 0) & (c >= 0) & (d >= 0)
    F = np.r_[np.c_[a[ok], b[ok], c[ok]], np.c_[b[ok], d[ok], c[ok]]]; F = np.r_[F, F[:, ::-1] + n]
    # 옆벽(테두리): 마스크 경계 화소마다 앞 · 뒤를 잇는 사각
    e = mask & ~cv2.erode(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool); ey, ex_ = np.nonzero(e)
    side = []
    for dy, dx in ((0, 1), (1, 0)):
        for y_, x_ in zip(ey, ex_):
            y2, x2 = y_ + dy, x_ + dx
            if y2 < mask.shape[0] and x2 < mask.shape[1] and mask[y2, x2] and e[y2, x2]:
                i, j = vid[y_, x_], vid[y2, x2]; side += [[i, j, j + n], [i, j + n, i + n]]
    F = np.r_[F, np.array(side, int).reshape(-1, 3)] if side else F
    me = trimesh.Trimesh(np.r_[Vf, Vb], F, process=False); me.visual.vertex_colors = np.tile(list(col) + [255], (2 * n, 1)).astype(np.uint8); return me
parts = [판(벽, -D, 6, (225, 228, 238)), 판(창 | 벽, 0.5, 4, (25, 25, 32))]   # 벽(창 입구 = −D) · 속머리 뒷판(d = 0.5)
# 눈(파란 원판) — 정면 눈 점 · 속머리 앞(d = 0)
P = json.load(open(os.path.join(O, "특징점.json"), encoding="utf-8"))["1"]
for side in ("왼", "오른"):
    ex, ey = P[f"눈/{side}"]; e = trimesh.creation.cylinder(radius=9, height=1.5, sections=24); e.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    e.apply_translation([ex - cu, -0.5, -ey]); e.visual.vertex_colors = np.tile([70, 130, 230, 255], (len(e.vertices), 1)).astype(np.uint8); parts.append(e)
# 립: 창 윗변 띠(창 바로 위 4 화소 · 앞으로 2 · 두께 3.7 은 세로 폭으로)
윗변 = (cv2.dilate(창.astype(np.uint8), np.ones((int(round(립)) * 2 + 1, 1), np.uint8)) > 0) & ~창 & 벽
윗변 &= np.roll(창, int(round(립)), axis=0)                                                  # 창 위쪽에 있는 띠만
parts.append(판(윗변, -D - 2, 2 + 2, (240, 240, 248)))
allm = trimesh.util.concatenate(parts); allm = trimesh.Trimesh(allm.vertices, allm.faces, vertex_colors=allm.visual.vertex_colors, process=False)
allm.export(os.path.join(B, "창모듈.ply"), encoding="ascii")
print({"창 깊이": D, "립": 립, "벽 화소": int(벽.sum()), "창 화소": int(창.sum()), "립 화소": int(윗변.sum())})
