# -*- coding: utf-8 -*-
"""부분 그래프 (10-05 사용자 「tripoSG 는 연결 구조는 맞다 · graph 로 각 부분을 표현하고 부분마다 살짝씩 바꿔 맞추자」)
python 부분그래프.py <판 이름> <n>  — 면 특징(PartField) + 약한 위치 → 면 인접 ward 군집 n 부분
노드 = 부분(면 수 · 넓이 · 중심 · 크기) · 간선 = 맞닿은 경계 길이 · 이름은 위치 규칙으로 붙이고 사람이 고친다
출력: 지표/트리포분할/<판>_그래프<n>.json · 블렌더/<판>_부분<n>.ply(부분 색) · <판>_그래프<n>.png"""
import sys, json, numpy as np, trimesh, scipy.sparse as sp
from sklearn.cluster import AgglomerativeClustering
B = "G:/art2real/원화3d/out/오메가몬2/블렌더/"; O = "G:/art2real/원화3d/out/오메가몬2/지표/트리포분할/"
nm, n = sys.argv[1], int(sys.argv[2]); tag = nm.split("_")[-1] + "_"
m = trimesh.load(B + nm + ".ply", process=True); F = np.load(O + tag + "면특징.npy"); F = F / np.linalg.norm(F, axis=1, keepdims=True)
assert len(F) == len(m.faces), (len(F), len(m.faces))
P = m.triangles_center; Pn = (P - P.mean(0)) / P.std()
adj = m.face_adjacency; A = sp.coo_matrix((np.ones(len(adj)), (adj[:, 0], adj[:, 1])), shape=(len(F),) * 2); A = ((A + A.T) > 0).astype(float)
lab = AgglomerativeClustering(n_clusters=n, linkage="ward", connectivity=A).fit_predict(np.c_[F, 0.15 * Pn])
# 노드
ar = m.area_faces; nodes = []
for i in range(n):
    s = lab == i; c = (P[s] * ar[s, None]).sum(0) / ar[s].sum(); v = m.vertices[np.unique(m.faces[s])]
    nodes.append({"id": i, "면": int(s.sum()), "넓이": round(float(ar[s].sum()), 1), "중심": c.round(1).tolist(), "최소": v.min(0).round(1).tolist(), "최대": v.max(0).round(1).tolist()})
# 간선: 서로 다른 부분 사이 공유 모서리 길이
e = m.face_adjacency_edges; L = np.linalg.norm(m.vertices[e[:, 0]] - m.vertices[e[:, 1]], axis=1)
a_, b_ = lab[adj[:, 0]], lab[adj[:, 1]]; k = a_ != b_; E = {}
for x, y, l in zip(a_[k], b_[k], L[k]):
    key = (int(min(x, y)), int(max(x, y))); E[key] = E.get(key, 0) + float(l)
# 이름(위치 규칙 · 첫 추정) — 우리 틀: z 위 · 앞 −y · x 오른쪽
zs = np.array([d["중심"][2] for d in nodes]); top = zs.max()
def 이름(d):
    c, lo, hi = d["중심"], d["최소"], d["최대"]; ext = np.array(hi) - np.array(lo)
    thin = sorted(ext)[0] < 0.25 * sorted(ext)[2] and sorted(ext)[1] < 0.45 * sorted(ext)[2]
    if c[2] > -150 and thin and c[1] < -40: return "뿔"
    if c[2] > -165 and thin: return "안테나"
    if c[1] < -60 and -225 < c[2] < -185: return "눈 · 얼굴"
    if c[1] < -40 and c[2] < -215: return "아래 얼굴"
    if c[2] > -175 and c[1] < -50: return "차양 · 이마"
    if c[2] > -175: return "돔"
    return "옆 · 뒤"
for d in nodes: d["이름"] = 이름(d)
G = {"판": nm, "n": n, "노드": nodes, "간선": [{"a": a, "b": b, "경계": round(l, 1)} for (a, b), l in sorted(E.items())]}
json.dump(G, open(O + f"{nm}_그래프{n}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
import colorsys
pal = (np.array([colorsys.hsv_to_rgb(i / n, 0.65, 0.95) for i in range(n)]) * 255).astype(np.uint8)
fc = np.c_[pal[lab], np.full(len(lab), 255, np.uint8)]
mm = trimesh.Trimesh(m.vertices, m.faces, process=False); vc = np.zeros((len(mm.vertices), 4), np.uint8)
for f, c in zip(mm.faces, fc): vc[f] = c
trimesh.Trimesh(mm.vertices, mm.faces, vertex_colors=vc, process=False).export(B + f"{nm}_부분{n}.ply", encoding="ascii")
# 그래프 그림: 정면(x, z) · 옆(y, z) 에 노드 중심 · 간선(굵기 = 경계 길이)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
fig, axs = plt.subplots(1, 2, figsize=(16, 8))
for ax, (i0, t) in zip(axs, ((0, "정면 (x, z)"), (1, "옆 (y, z) · 왼쪽이 앞"))):
    for (a, b), l in E.items():
        ca, cb = nodes[a]["중심"], nodes[b]["중심"]; ax.plot([ca[i0], cb[i0]], [ca[2], cb[2]], "-", color="gray", lw=0.5 + 6 * l / max(E.values()), alpha=0.6)
    for d in nodes:
        c = d["중심"]; ax.scatter(c[i0], c[2], s=30 + d["넓이"] / 30, color=pal[d["id"]] / 255, edgecolor="k", zorder=3)
        ax.annotate(f'{d["id"]} {d["이름"]}', (c[i0], c[2]), fontsize=9, zorder=4)
    ax.set_title(t); ax.set_aspect("equal")
    if i0 == 1: ax.invert_xaxis()
fig.tight_layout(); fig.savefig(B + f"{nm}_그래프{n}.png", dpi=70)
print({d["id"]: (d["이름"], d["면"]) for d in nodes}); print("간선", len(E))
