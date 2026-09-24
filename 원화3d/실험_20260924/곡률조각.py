# -*- coding: utf-8 -*-
"""**곡률 조각** — 곡률이 비슷한 이웃을 이어 «곡면 판»으로 묶는다 (2026-09-24).

    python 곡률조각.py

사용자(09-24): 「복셀에서의 곡률이 다른 데서는 면이 다르다고 가정한다면?」
평면 자(`평면조각`)는 평면만 판으로 세므로 원통 · 구면이 잘게 쪼개진다.
면마다 «이웃과의 꺾임 / 거리» 를 곡률로 삼고, 곡률이 비슷하면 같은 판으로 잇는다.
"""
import os, sys, time, json
from collections import deque
import numpy as np, trimesh

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922",
                r"G:\art2real\원화3d\실험_20260923", r"G:\art2real\원화3d\실험_20260924"]
import hull as H, 부품분할 as BB, 지표 as Z, 평면조각 as PJ, 깊이추정 as GC, 면합치기 as M


def 곡률(m):
    """면마다 곡률 — 이웃과의 이면각을 면 중심 사이 거리로 나눈 것 (1/길이). 면적 가중 평균."""
    adj = m.face_adjacency
    ang = m.face_adjacency_angles * np.sign(np.sum(
        (m.triangles_center[adj[:, 1]] - m.triangles_center[adj[:, 0]]) *
        np.asarray(m.face_normals)[adj[:, 0]], axis=1))
    d = np.linalg.norm(m.triangles_center[adj[:, 1]] - m.triangles_center[adj[:, 0]], axis=1)
    k = ang / np.maximum(d, 1e-9)
    s = np.zeros(len(m.faces)); c = np.zeros(len(m.faces))
    for a, b in ((adj[:, 0], adj[:, 1]), (adj[:, 1], adj[:, 0])):
        np.add.at(s, a, k); np.add.at(c, a, 1)
    return s / np.maximum(c, 1)


def 조각(m, 문턱κ, 국소=25.0):
    """곡률 차가 문턱보다 작고 이면각이 국소보다 작으면 같은 판."""
    m = m.copy(); m.merge_vertices()
    시작, 이웃 = PJ._이웃(m)
    κ = 곡률(m)
    deg = np.degrees(m.face_adjacency_angles)
    cos국 = np.cos(np.radians(국소))
    fn = np.asarray(m.face_normals); fa = m.area_faces
    라벨 = np.full(len(m.faces), -1, np.int64); L = 0
    for s in np.argsort(fa)[::-1]:
        if 라벨[s] >= 0: continue
        라벨[s] = L; q = deque([s])
        while q:
            i = q.popleft()
            for t in range(시작[i], 시작[i + 1]):
                j = 이웃[t]
                if 라벨[j] >= 0: continue
                if fn[i] @ fn[j] < cos국: continue
                if abs(κ[i] - κ[j]) > 문턱κ: continue
                라벨[j] = L; q.append(j)
        L += 1
    합 = np.bincount(라벨, weights=fa, minlength=L); 전 = fa.sum()
    몫 = np.sort(합)[::-1] / 전
    return L, float(몫[몫 >= 0.01].sum()), 라벨, m


def main():
    케 = [GC.케이스들[i] for i in (0, 4, 9)] + ["avatarsample_d", "knight_Warrior_RaWl2GJ0NZ"]
    문턱 = float(os.environ.get("KAPPA", "10.0"))
    표 = {}
    for c in 케:
        raw, masks, bs, p = BB.판(c)
        g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
        ux, uy, z = [np.asarray(a) for a in ax]
        tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
        우 = Z.메시로(g, (ux, uy, z))
        대, _ = M.다듬기(우, 0.35)                      # 대조군 — 같은 정도로 정점을 움직인 평활화
        줄 = {}
        for 이름, m in (("우리", 우), ("대조:라플라시안", 대), ("정답", tm)):
            평, _, _ = PJ.재기(m, 전체=10)
            n, 큰, _, _ = 조각(m, 문턱)
            줄[이름] = {"평면 조각": 평["조각 수"], "평면 큰판": 평["1% 이상이 덮는 몫"],
                      "곡률 조각": n, "곡률 큰판": round(큰, 3)}
        표[c] = 줄
        print("  %-24s " % c[:24] + " | ".join("%s 평면%5d→곡률%5d (큰판 %.3f→%.3f)" % (
            k, v["평면 조각"], v["곡률 조각"], v["평면 큰판"], v["곡률 큰판"]) for k, v in 줄.items()), flush=True)
    print()
    for 이름 in ("우리", "대조:라플라시안", "정답"):
        a = np.array([[표[c][이름][k] for k in ("평면 조각", "곡률 조각", "평면 큰판", "곡률 큰판")] for c in 표])
        print("%-14s 조각 %6.0f → %6.0f   큰판 %.3f → %.3f" % (이름, *np.median(a, 0)))
    p = os.path.join(H.OUT, "기록", "곡률조각_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"문턱κ": 문턱, "표": 표}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(p)


if __name__ == "__main__":
    main()
