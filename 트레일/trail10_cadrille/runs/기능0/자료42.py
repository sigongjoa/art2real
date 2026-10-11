# 쇼츠 42 재료 PNG — 돌림판(12 각) · 화면 부품은 변형 허용 라이선스만(#4 #5 #13 #21 #33 #17 …) · ND · 표준 라이선스 부품은 안 씀 · 10-11
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [H, os.path.join(T0, "s0")]
from render import render
from PIL import Image
O = "G:/art2real/out/영상05/대화/42_각진덩어리/자료/"; os.makedirs(O, exist_ok=True)
부 = np.load(os.path.join(R, "깊이학습", "시험.npz"))["부품"]; RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
노, 파, 주, 초 = (0.95, 0.88, 0.45), (0.45, 0.68, 0.98), (0.98, 0.62, 0.35), (0.55, 0.8, 0.5)
def 정(m):
    m = m.copy(); m.apply_translation(-m.bounds.mean(0)); m.apply_scale(0.9 / max(m.extents)); m.apply_translation([.5] * 3); return m
def 돌림(이름, m, 색, c=520):
    m = 정(m)
    for t in range(12):
        a = 2 * np.pi * t / 12; Image.fromarray(np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), [np.cos(a), np.sin(a), .7], img_size=c, cols=np.tile(색, (len(m.faces), 1))))).save(O + "%s_%02d.png" % (이름, t))
사람 = lambda i: trimesh.load(RR + str(부[i]), force="mesh"); 파일 = lambda d, i, s="": trimesh.load(os.path.join(H, d, "%02d%s.stl" % (i, s)))
돌림("21교차", trimesh.load(os.path.join(R, "윤곽0", "결과_모", "21_교차.stl")), 파); 돌림("21기능", 파일("최종", 21), 주)
돌림("4사람", 사람(4), 노); 돌림("4교차", trimesh.load(os.path.join(R, "윤곽0", "결과_모", "04_교차.stl")), 파); 돌림("4기능", 파일("최종", 4), 주)
돌림("5사람", 사람(5), 노); 돌림("5교차", trimesh.load(os.path.join(R, "윤곽0", "결과_모", "05_교차.stl")), 파); 돌림("5기능", 파일("최종", 5), 주)
돌림("33사람", 사람(33), 노); 돌림("33전", 파일("최종", 33), 주); 돌림("33후", 파일("디테일", 33), 주)
돌림("33옛", 파일("B_모델", 33), 파); 돌림("33새", 파일("B_모델T", 33), 초)
돌림("17옛", 파일("B_모델", 17), 파); 돌림("17새", 파일("B_모델T", 17), 초); 돌림("17사람", 사람(17), 노)
돌림("13사람", 사람(13), 노); 돌림("13새", 파일("B_모델T", 13), 초); 돌림("13손", 파일("최종", 13), 주)
# #21 자동 찾기(복셀 계단)
import 탐색 as T
X = T.X_("시험"); x = X[21].astype(np.float32); S = x[0] > .5; 후 = T.후보들(S, x[3], x[2]); r = T.찾기(x); V = T.교차(S)
for s in r["순서"]:
    j = next(j for j, (nm, p, w) in enumerate(후) if nm == s["기능"] and all(p.get(k) == s.get(k) for k in p)); V &= ~후[j][2]
돌림("21계단", trimesh.voxel.VoxelGrid(np.pad(V, 1)).marching_cubes, (0.6, 0.6, 0.9)); 돌림("21사람", 사람(21), 노)
# 35 중 화면에 낼 수 있는 18 (사람 · 디테일 후)
ok = [1, 2, 3, 4, 5, 6, 8, 10, 13, 17, 20, 21, 22, 24, 31, 32, 33, 34]
for i in ok:
    for nm, m, 색 in (("격사", 사람(i), 노), ("격후", 파일("디테일", i), 주)):
        mm = 정(m); Image.fromarray(np.asarray(render(np.asarray(mm.vertices), np.asarray(mm.faces), [1, .6, .8], img_size=240, cols=np.tile(색, (len(mm.faces), 1))))).save(O + "%s_%02d.png" % (nm, i))
json.dump(ok, open(O + "격자.json", "w")); print("ok")
