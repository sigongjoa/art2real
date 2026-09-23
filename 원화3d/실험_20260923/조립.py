# -*- coding: utf-8 -*-
"""**조립** — 키트 부품에서 조립 순서와 끼우는 방향을 코드가 스스로 계산한다 (2026-09-23).

    python 조립.py [키트폴더]     -> out/조립/<키트>/조립.json (계획) · 뷰어자료.json (기하 + 계획)

사용자(09-23): 「이걸로 조립을 해볼래? 조립하는 장면을 코드로 표현해볼래?」
Printables 키트(부품마다 STL · 조립된 좌표)에서:

    ① 닿음 그래프   부품 쌍의 거리가 문턱 이하면 맞닿은 것으로 본다 (KD 트리)
    ② 조립 순서     바닥에 가장 가까운 부품이 뿌리 · 거기서 너비 우선으로 퍼진다 (사람이 아래부터 쌓는 것과 같다)
    ③ 끼우는 방향   부모와 닿는 면의 복판에서 자식 복판으로 가는 방향 — 분해도에서 부품이 날아가는 그 선이다
    ④ 겹침 검사     이미 놓인 부품과 부피가 겹치면 그 방향으로는 못 끼운다(경고로 적는다)
"""
import json
import os
import sys

import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, r"G:\art2real\원화3d")
import hull as H

닿음문턱 = 1.2          # mm — 이보다 가까우면 맞닿은 것으로 본다


def 읽기(디):
    부품 = []
    for f in sorted(os.listdir(디)):
        if not f.lower().endswith(".stl"):
            continue
        m = trimesh.load(os.path.join(디, f), force="mesh")
        if len(m.faces) == 0:
            continue
        부품.append({"이름": os.path.splitext(f)[0], "메시": m})
    return 부품


def 닿음(부품):
    """부품 쌍마다 가장 가까운 거리와 닿는 자리(복판)."""
    점 = [np.asarray(p["메시"].vertices) for p in 부품]
    나무 = [cKDTree(v) for v in 점]
    간선 = {}
    for i in range(len(부품)):
        for j in range(i + 1, len(부품)):
            d, idx = 나무[j].query(점[i], distance_upper_bound=닿음문턱)
            가까 = np.isfinite(d)
            if 가까.sum() >= 8:
                자리 = 점[i][가까].mean(0)
                간선[(i, j)] = {"닿은 점": int(가까.sum()), "자리": 자리.tolist(), "거리": float(d[가까].mean())}
    return 간선


def 순서(부품, 간선, 위=1):
    """바닥(위축이 가장 낮은 곳)에 가까운 부품부터 너비 우선."""
    바닥 = [p["메시"].bounds[0][위] for p in 부품]
    뿌리 = int(np.argmin(바닥))
    이웃 = {i: [] for i in range(len(부품))}
    for (i, j), e in 간선.items():
        이웃[i].append((j, e)); 이웃[j].append((i, e))
    본, 줄, 부모 = {뿌리}, [뿌리], {뿌리: None}
    while True:
        후보 = [(j, i, e) for i in 줄 for j, e in 이웃[i] if j not in 본]
        if not 후보:
            남 = [i for i in range(len(부품)) if i not in 본]
            if not 남:
                break
            j = min(남, key=lambda k: 바닥[k])          # 안 닿은 부품(무기 등)은 낮은 것부터 뒤에 붙인다
            본.add(j); 줄.append(j); 부모[j] = None
            continue
        후보.sort(key=lambda t: (-t[2]["닿은 점"], 바닥[t[0]]))
        j, i, e = 후보[0]
        본.add(j); 줄.append(j); 부모[j] = (i, e)
    return 줄, 부모


def 계획(디, 위=1):
    부품 = 읽기(디)
    간선 = 닿음(부품)
    줄, 부모 = 순서(부품, 간선, 위)
    계 = []
    for 차례, i in enumerate(줄):
        p = 부품[i]
        c = p["메시"].bounds.mean(0)
        par = 부모[i]
        if par is None:
            방향 = np.array([0.0, 1.0, 0.0]); 붙 = None
        else:
            j, e = par
            방향 = c - np.asarray(e["자리"])
            n = np.linalg.norm(방향)
            방향 = 방향 / n if n > 1e-6 else np.array([0.0, 1.0, 0.0])
            붙 = 부품[j]["이름"]
        계.append({"차례": 차례 + 1, "이름": p["이름"], "붙는 곳": 붙,
                   "끼우는 방향": [round(float(x), 3) for x in 방향],
                   "복판": [round(float(x), 2) for x in c],
                   "크기mm": [round(float(x), 1) for x in p["메시"].extents],
                   "면": int(len(p["메시"].faces))})
    return 부품, 간선, 계


def 겹침검사(부품, 계, 칸=1.5):
    """조립 순서대로 넣을 때, 끼우는 방향으로 들어오다 이미 놓인 부품과 부딪히나 (성긴 복셀로)."""
    경고 = []
    놓 = []
    for 항 in 계:
        i = [k for k, p in enumerate(부품) if p["이름"] == 항["이름"]][0]
        m = 부품[i]["메시"]
        d = np.array(항["끼우는 방향"])
        if 놓:
            벽 = trimesh.util.concatenate([부품[k]["메시"] for k in 놓])
            벽점 = np.asarray(벽.vertices)
            나무 = cKDTree(벽점)
            v = np.asarray(m.vertices)
            for t in (6.0, 3.0, 1.5):                      # 들어오는 길에서 몇 mm 앞
                dd, _ = 나무.query(v + d * t, distance_upper_bound=칸)
                if np.isfinite(dd).sum() > len(v) * 0.02:
                    경고.append({"부품": 항["이름"], "막힘 mm": t}); break
        놓.append(i)
    return 경고


def main(디=r"G:\art2real\원화3d\out\키트정답\529278"):
    부품, 간선, 계 = 계획(디)
    경고 = 겹침검사(부품, 계)
    이름 = os.path.basename(디.rstrip("\/"))
    out = os.path.join(H.OUT, "조립", 이름)
    os.makedirs(out, exist_ok=True)
    json.dump({"키트": 이름, "부품": len(부품), "닿은 쌍": len(간선), "순서": 계, "끼움 경고": 경고},
              open(os.path.join(out, "조립.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("키트 %s · 부품 %d · 닿은 쌍 %d" % (이름, len(부품), len(간선)))
    for 항 in 계:
        print("  %2d. %-26s ← %-22s 방향 %s" % (항["차례"], 항["이름"][:26], str(항["붙는 곳"])[:22], 항["끼우는 방향"]))
    if 경고:
        print("  ⚠ 끼우다 막히는 곳:", 경고)
    return 부품, 계


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else r"G:\art2real\원화3d\out\키트정답\529278")
