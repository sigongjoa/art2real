# 세 그림을 실제 자리로 세우기(회전) — 위는 바닥 · 앞은 뒤 벽 · 옆은 옆 벽 · 182 번 · 10-14
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"; j = 182
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; X = d["X"][te[j]]; e = np.load(O + "데이터_앞옆.npz"); F = e["F"][te[j]]; S = e["S"][te[j]]
u = (np.arange(128) + .5) / 128 * 1.1 - .55   # 데이터.py 격자: 열 → x · 행 → −y(위) / −z(앞 · 옆)
fig = plt.figure(figsize=(18, 8))
a = fig.add_subplot(1, 2, 1); 겹 = np.ones(X.shape + (3,)); 겹[X > 0] = [0, .6, 1]; 겹[F > 0] = [1, 0, .6]; a.imshow(겹); a.axis("off")
a.set_title("지금: 앞 그림(분홍)을 눕힌 채 위 그림(하늘)에 겹침\n분홍 세로 = 높이인데 하늘 세로 = 앞뒤", fontsize=16)
a = fig.add_subplot(1, 2, 2, projection="3d")
r, c = np.nonzero(X); a.scatter(u[c], -u[r], np.full(len(r), -.55), s=2, c=[(0, .6, 1)], label="위 그림 → 바닥에")
r, c = np.nonzero(F); a.scatter(u[c], np.full(len(r), .55), -u[r], s=2, c=[(1, 0, .6)], label="앞 그림 → 90° 세워 뒤 벽에")
r, c = np.nonzero(S); a.scatter(np.full(len(r), .55), u[c], -u[r], s=2, c=[(.2, .7, .2)], label="옆 그림 → 90° 세워 옆 벽에")
for x in (-.3, 0, .3): a.plot([x, x], [-.55, .55], [-.55, -.55], c="#bbb", lw=1); a.plot([x, x], [.55, .55], [-.55, .55], c="#bbb", lw=1)
a.set_xlim(-.55, .55); a.set_ylim(-.55, .55); a.set_zlim(-.55, .55); a.view_init(22, -60); a.set_box_aspect((1, 1, 1)); a.set_xticks([]); a.set_yticks([]); a.set_zticks([])
a.set_xlabel("좌우", fontsize=14); a.set_ylabel("앞뒤", fontsize=14); a.set_zlabel("높이", fontsize=14); a.legend(fontsize=13, loc="upper left", markerscale=6)
a.set_title("회전: 세 그림을 실제 자리로 세움\n회색 줄 = 같은 좌우 위치가 바닥과 벽에서 이어짐", fontsize=16)
plt.savefig(O + "회전_182.png", dpi=75, bbox_inches="tight")
