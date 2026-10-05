# -*- coding: utf-8 -*-
"""사람이 만든 3D 대 우리 과정 비교 (10-05 사용자 「다음엔 있는 3D 가 없을 수 있다 · 있는 3D 와 우리 프로세스가 뭐가 다른지 봐야지」)
비교: Pomettini 머리(사람 · 로우폴리) · 우리 CAD v62(원화에서 지음) · TripoSG T6(생성)
재는 것 — 셋 다 「머리 몸통 폭 W(뿔 · 안테나 · 볼 가시 빼고)」로 나눈 비:
  ① 높이별 폭 · 깊이 단면(20 층) — 몸통 모양
  ② 머리 높이 · 깊이 / W
  ③ 뿔: 길이 · 밑동 폭 · 앞 기울기 / W · ④ 안테나: 길이 · 들린 각
  ⑤ 면: 큰 평면 수(법선 10° 안 이웃 면 묶음 · 넓이 상위가 전체 80 % 를 덮는 개수) · 꺾인 모서리(> 30°) 수
출력: 지표/바탕비교.json · 블렌더/바탕비교_단면.png"""
import json, numpy as np, trimesh, networkx as nx
B = "G:/art2real/원화3d/out/오메가몬2/블렌더/"
def load(n):
    m = trimesh.load(B + n + ".ply", process=False); return trimesh.Trimesh(m.vertices, m.faces, process=True)
M = {"사람(Pomettini)": load("포메원본"), "우리 CAD v62": load("CAD_v62"), "생성 TripoSG T6": load("트리포_T6")}
def 단면(m, z):
    s = m.section(plane_normal=[0, 0, 1], plane_origin=[0, 0, z])
    if s is None: return None
    P = np.vstack(s.discrete); return P
def 재기(m):
    v = m.vertices; z0, z1 = v[:, 2].min(), v[:, 2].max()
    prof = []
    for f in np.linspace(0.02, 0.98, 25):
        P = 단면(m, z0 + f * (z1 - z0))
        if P is None: prof.append((f, 0, 0)); continue
        # 몸통만: 가운데 점들(중앙값에서 2.5 IQR 안) — 뿔 · 안테나 · 가시 같은 튀어나온 것 빼기
        c = np.median(P, 0); d = np.linalg.norm(P - c, axis=1); k = d < np.percentile(d, 75) * 1.6
        prof.append((f, np.ptp(P[k, 0]), np.ptp(P[k, 1])))
    prof = np.array(prof); W = prof[:, 1].max()
    body = prof[prof[:, 1] > 0.5 * W]; H = (body[:, 0].max() - body[:, 0].min()) * (z1 - z0)
    D = body[:, 2].max()
    # 면 묶음
    adj = m.face_adjacency; ang = m.face_adjacency_angles; G = nx.Graph(); G.add_nodes_from(range(len(m.faces))); G.add_edges_from(adj[ang < np.radians(10)])
    ar = m.area_faces; regs = sorted([ar[list(c)].sum() for c in nx.connected_components(G)], reverse=True); cs = np.cumsum(regs) / ar.sum()
    n80 = int(np.searchsorted(cs, 0.8) + 1)
    return dict(W=round(W, 1), 높이_W=round(H / W, 2), 깊이_W=round(D / W, 2), 전체높이_W=round((z1 - z0) / W, 2), 면수=len(m.faces), 평면묶음_80=n80,
                꺾인모서리=int((ang > np.radians(30)).sum()), 단면=[(round(a, 2), round(b / W, 3), round(c / W, 3)) for a, b, c in prof])
R = {k: 재기(m) for k, m in M.items()}
for k, r in R.items(): print(k, {a: b for a, b in r.items() if a != "단면"})
json.dump(R, open("G:/art2real/원화3d/out/오메가몬2/지표/바탕비교.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic"; plt.rcParams["axes.unicode_minus"] = False
fig, axs = plt.subplots(1, 2, figsize=(14, 7))
for k, r in R.items():
    p = np.array(r["단면"]); axs[0].plot(p[:, 1], p[:, 0], "-o", ms=3, label=k); axs[1].plot(p[:, 2], p[:, 0], "-o", ms=3, label=k)
axs[0].set_title("높이별 몸통 폭 / W (아래 0 → 위 1)"); axs[1].set_title("높이별 몸통 깊이 / W"); axs[0].legend(); [a.grid(alpha=.3) for a in axs]
fig.tight_layout(); fig.savefig(B + "바탕비교_단면.png", dpi=70)
