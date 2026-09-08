# -*- coding: utf-8 -*-
"""파트 분해에서 **리그 계획**을 뽑는다. 블렌더는 이 json 만 읽는다.

    python rig_plan.py out/st_doggy.glb out/st_doggy_rig.json
    python rig_plan.py --demo

## 왜 이렇게 하나

스탠드는 살이 아니라 갑주다. 스킨을 입히면 **커튼이 생긴다** — `rigid_parts.py` 가 적어둔
대로 한 정점이 반대로 도는 두 본을 섞어 물기 때문이다. 파트가 이미 갈라져 있으니
섞을 일 자체를 안 만든다: 파트 하나에 본 하나, 강체.

## 관절은 짐작 안 하고 잰다

파트 두 개의 **표면이 실제로 닿는 자리**가 관절이다. bbox 겹침은 못 쓴다 —
Brain Storm 이 눈에 보이게 흩어져 있는데도 bbox 로는 붙음 100% 로 찍혔다.

거리는 정점이 아니라 **표면에서 뿌린 점**으로 잰다. 정점만 쓰면 면이 성긴 파트에서
닿아 있는데도 멀다고 나온다(자체검사의 상자 셋이 그 경우다 — 겹쳐 있는데 0.24 span).

본 머리 = 접촉면 중심, 본 꼬리 = 그 파트에서 머리에서 **제일 먼 점**.
다리처럼 긴 파트가 제 길이만큼 본을 갖게 된다.

좌표는 GLB 공간(Y-up)으로 낸다. **블렌더 변환은 해석기 한 곳에서만** 한다.
"""
import json
import os
import sys

import numpy as np
import trimesh
from scipy.spatial import cKDTree

TOUCH = 0.05        # span 대비 이 안이면 닿은 것으로 본다 (실측: 붙은 쌍 0.00~3.6%, 떨어진 쌍 12%+)
SAMPLE = 4000


def surf(parts, rng):
    """표면에서 골고루 뿌린 점. 정점은 성긴 파트에서 거리를 부풀린다."""
    out = []
    for p in parts:
        pts, _ = trimesh.sample.sample_surface(p, SAMPLE, seed=int(rng.integers(1 << 30)))
        out.append(np.asarray(pts))
    return out


def contacts(S, span):
    """파트 쌍마다 표면 최단거리와 접촉면 중심."""
    T = [cKDTree(s) for s in S]
    out = {}
    for i in range(len(S)):
        for j in range(i + 1, len(S)):
            d, _ = T[j].query(S[i])
            if d.min() / span > TOUCH:
                continue
            near = S[i][d <= max(d.min() * 3, span * 0.01)]
            out[(i, j)] = (float(d.min() / span), near.mean(0))
    return out


def plan(path):
    sc = trimesh.load(path)
    parts = list(sc.geometry.values()) if isinstance(sc, trimesh.Scene) else [sc]
    V = [np.asarray(p.vertices) for p in parts]
    allV = np.vstack(V)
    span = float((allV.max(0) - allV.min(0)).max())
    con = contacts(surf(parts, np.random.default_rng(0)), span)

    root = int(np.argmax([len(p.faces) for p in parts]))      # 면이 제일 많은 게 몸통
    # **이미 놓인 것 중 제일 가까운 이웃에 붙인다**(Prim). 정렬 목록을 훑으면
    # 몸통에 먼저 걸려 전부 별 모양이 된다 — 다리 장식이 다리가 아니라 몸통에 매달렸다.
    parent = {root: None}
    while True:
        best = None
        for (i, j), (d, c) in con.items():
            for a, b in ((i, j), (j, i)):
                if a in parent and b not in parent and (best is None or d < best[0]):
                    best = (d, b, a, c)
        if best is None:
            break
        d, b, a, c = best
        parent[b] = (a, c.tolist(), d)

    bones = []
    for i in range(len(parts)):
        if i not in parent:
            continue                                          # 어디에도 안 닿은 파트는 뺀다
        if parent[i] is None:
            lo, hi = V[i].min(0), V[i].max(0)
            head = [float((lo[0] + hi[0]) / 2), float(lo[1]), float((lo[2] + hi[2]) / 2)]
            tail = [head[0], float(hi[1]), head[2]]
            bones.append(dict(id=i, name="b%02d_root" % i, parent=None, head=head, tail=tail,
                              head_src="derived(파트 bbox 중심선)"))
        else:
            p, c, d = parent[i]
            far = V[i][np.argmax(np.linalg.norm(V[i] - np.array(c), axis=1))]
            bones.append(dict(id=i, name="b%02d" % i, parent="b%02d%s" % (p, "_root" if p == root else ""),
                              head=[float(x) for x in c], tail=[float(x) for x in far],
                              head_src="measured(파트 %d 과의 접촉면 중심 · 거리 %.4f span)" % (p, d)))
    return dict(
        schema="rigid-part-rig/1",
        source=os.path.basename(path),
        datum={"space": "GLB (Y-up) · 블렌더 변환은 해석기에서 (x, -z, y)",
               "span": span, "unit": "GLB 원단위"},
        recipe={"parenting": "파트마다 본 하나. 스킨 없음 — 강체 부모",
                "why": "섞지 않으면 커튼이 원리적으로 없다. 늘어남이 1.000 이어야 한다",
                "checks": ["늘어남 == 1.000", "이음매 틈"]},
        touch_threshold=TOUCH,
        parts=[dict(id=i, faces=int(len(p.faces)), verts=int(len(p.vertices)),
                    centroid=[float(x) for x in V[i].mean(0)]) for i, p in enumerate(parts)],
        contacts=[dict(a=i, b=j, dist=d, at=[float(x) for x in c]) for (i, j), (d, c) in con.items()],
        bones=bones,
    )


def demo():
    """상자 셋 — 가운데에 좌우가 닿아 있다. 트리가 가운데를 뿌리로 잡아야 한다."""
    a = trimesh.creation.box((1, 2, 1))
    b = trimesh.creation.box((0.3, 2, 0.3)); b.apply_translation((0.62, -0.5, 0))
    c = trimesh.creation.box((0.3, 2, 0.3)); c.apply_translation((-0.62, -0.5, 0))
    sc = trimesh.Scene({"a": a, "b": b, "c": c})
    p = plan_scene(sc)
    assert len(p["bones"]) == 3, p["bones"]
    roots = [x for x in p["bones"] if x["parent"] is None]
    assert len(roots) == 1 and roots[0]["id"] == 0, "면이 제일 많은 가운데가 뿌리"
    assert all(x["parent"] == roots[0]["name"] for x in p["bones"] if x["id"] != 0)
    far = trimesh.creation.box((1, 1, 1)); far.apply_translation((9, 0, 0))
    p2 = plan_scene(trimesh.Scene({"a": a, "far": far}))
    assert len(p2["bones"]) == 1, "안 닿은 파트는 빠져야 한다: %s" % p2["bones"]
    print("자체검사 통과 · 본 %d개" % len(p["bones"]))


def plan_scene(sc):
    import tempfile
    f = os.path.join(tempfile.gettempdir(), "_rigplan.glb")
    sc.export(f)
    return plan(f)


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo(); raise SystemExit
    src, dst = sys.argv[1], sys.argv[2]
    d = plan(src)
    json.dump(d, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%s · 본 %d개 (파트 %d개 중)" % (dst, len(d["bones"]), len(d["parts"])))
    for b in d["bones"]:
        print("  %-12s <- %-12s  머리 (%.2f %.2f %.2f)  %s"
              % (b["name"], b["parent"] or "(뿌리)", *b["head"], b["head_src"]))
