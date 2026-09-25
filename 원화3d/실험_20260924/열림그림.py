"""닫힌 입체 대 열린 입체 — 부품마다 구멍 가장자리(삼각형 하나에만 붙은 모서리)를 빨갛게."""
import glob, os, numpy as np, trimesh, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
plt.rcParams["font.family"] = "Malgun Gothic"

def 가장자리(m):
    e = m.edges_sorted; u, c = np.unique(e, axis=0, return_counts=True)
    return u[c == 1], u[c > 2]

def 부품하나(d, 열린=True):
    for f in sorted(glob.glob(d + "/**/*.stl", recursive=True)):
        m = trimesh.load(f, force="mesh")
        if m.is_watertight != 열린 and len(m.faces) < 150000: return f, m

칸 = [("사람 키트 529483 — 닫힘", "out/키트정답/529483", False),
      ("사람 키트 529278 — 열림", "out/키트정답/529278", True),
      ("우리 오메가몬 — 홈 파기 전", "out/출력/오메가몬", True),
      ("우리 오메가몬 — 출력한 판", "out/출력/오메가몬_키트", True)]
fig = plt.figure(figsize=(20, 6))
for i, (제목, d, 열린) in enumerate(칸):
    f, m = 부품하나(d, 열린)
    b, n = 가장자리(m)
    ax = fig.add_subplot(1, 4, i + 1, projection="3d")
    ax.add_collection3d(Poly3DCollection(m.triangles, facecolor=(.82, .82, .80, .35), edgecolor="none"))
    if len(b): ax.add_collection3d(Line3DCollection(m.vertices[b], colors="red", linewidths=2.2))
    if len(n): ax.add_collection3d(Line3DCollection(m.vertices[n], colors="blue", linewidths=2.2))
    lo, hi = m.bounds; c = (lo + hi) / 2; r = (hi - lo).max() / 2
    ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(c[2]-r, c[2]+r)
    ax.view_init(20, -60); ax.set_axis_off()
    ax.set_title("%s\n%s · 삼각형 %d\n구멍 가장자리 %d · 세 겹 모서리 %d" % (제목, os.path.basename(f), len(m.faces), len(b), len(n)), fontsize=11)
fig.suptitle("빨강 = 삼각형 하나에만 붙은 모서리(구멍의 테두리)   파랑 = 삼각형 셋 이상이 붙은 모서리", fontsize=13)
fig.savefig("out/열림_비교.png", dpi=110, bbox_inches="tight"); print("out/열림_비교.png")
