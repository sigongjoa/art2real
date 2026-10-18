# 실제 그림(정답 없음 · 실제76 입력)에 판정기준79 · 80 (가) 곡면 맞춤 깎기 — 판0 32 단계 층 → 칸 깎기 대 곡면 맞춤 연속 장 · 시트 한 장 · 10-18
# 사용(venv · ART_MEM_GB=8): 실제80.py <그림.png> ... → out/설명/캐드부품/실제입력/시트80.png
import sys, os, numpy as np, cv2, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍")
from mpl_toolkits.mplot3d.art3d import Poly3DCollection; from skimage.measure import marching_cubes
import torch, 실제76 as R, 곡면79 as Q, 고침78 as G8, 짓기 as J, 여섯방향 as S6, 입력51 as I, 천장쪼개기52 as C
plt.rcParams["font.family"] = "Malgun Gothic"; O = "G:/art2real/out/설명/캐드부품/"; 빛 = matplotlib.colors.LightSource(315, 40); m = G8.망읽기("판0")
u = np.tile(S6.g, (128, 1)); v = -u.T; 행 = []
for p in sys.argv[1:]:
    X, F, S, H = R.그림셋(p); 몸, _ = J.몸통37((X, F, S), H); 반 = [S6.반높이(몸, S6.R(*S6.방향[k])) for k in S6.방향]
    a = I.하나((X, F, S, np.array(반, np.float32))); 층 = G8.고치기(m, a, 반, 0)   # 고치기 0 걸음 = 판0 그대로
    틀 = J.점유_캐드(몸); 칸 = C.깎(틀, {d: np.where(층[j] == 32, np.nan, h - 층[j] * (2 * h / 32)) for j, (d, h) in enumerate(zip(S6.방향, 반))}, 48, False, 반)
    위들 = []
    for j, h in enumerate(반):
        단 = 2 * h / 32; d = np.where(층[j] == 32, np.nan, 층[j] * 단); d, _ = Q.맞추기(Q.조각(a[j, 0], 층[j]), np.nan_to_num(d), 단, u, v); 위들.append(h - d)
    맞 = Q.장메시(위들, 반); vs, fs, _, _ = marching_cubes(np.pad(칸, 1).astype(np.float32), .5); 행.append((p, ((vs - .5) / 48 * 1.1 - .55, fs), 맞)); print(os.path.basename(p), "칸", int(칸.sum()), "맞춤 면", len(맞[1]), flush=True)
f = plt.figure(figsize=(17, 4.2 * len(행)))
for r, (p, 칸m, 맞m) in enumerate(행):
    q = f.add_subplot(len(행), 5, r * 5 + 1); q.imshow(cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)[..., ::-1]); q.set_axis_off(); q.set_title("입력 그림 (정답 없음)", fontsize=13)
    for c, (제, (vv, ff), 색, 각) in enumerate([("지금: 칸 깎기", 칸m, "#e8c06a", -50), ("지금: 칸 깎기", 칸m, "#e8c06a", 40), ("곡면 맞춰 깎기", 맞m, "#5a8fd0", -50), ("곡면 맞춰 깎기", 맞m, "#5a8fd0", 40)]):
        b = f.add_subplot(len(행), 5, r * 5 + 2 + c, projection="3d"); b.set_axis_off(); b.set_box_aspect((1, 1, 1)); b.set_xlim(-.5, .5); b.set_ylim(-.5, .5); b.set_zlim(-.5, .5); b.view_init(25, 각)
        b.add_collection3d(Poly3DCollection(np.asarray(vv)[np.asarray(ff)], facecolors=색, edgecolors=색, linewidths=0, shade=True, lightsource=빛)); b.set_title(제, fontsize=13)
plt.tight_layout(); f.savefig(O + "실제입력/시트80.png", dpi=70); print("ok")
