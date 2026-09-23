# -*- coding: utf-8 -*-
"""조립 계획 + 부품 기하 -> 웹 뷰어 한 파일 (2026-09-23). 아티팩트가 glb 를 안 서빙해서 JSON+base64 로 싼다."""
import base64, json, os, sys
import numpy as np
import trimesh

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260923"]
import hull as H
import 조립 as A

디 = sys.argv[1] if len(sys.argv) > 1 else r"G:\art2real\원화3d\out\키트정답\529278"
부품, 간선, 계 = A.계획(디)

# 통짜 본체(다른 부품을 다 담는 것)는 뺀다 — 키트에 완성본 STL 이 같이 들어 있는 경우가 있다
부피 = np.array([abs(p["메시"].volume) for p in 부품])
큰 = int(np.argmax(부피))
if 부피[큰] > 0.55 * 부피.sum():
    뺀 = 부품[큰]["이름"]
    부품 = [p for k, p in enumerate(부품) if k != 큰]
    계 = [c for c in 계 if c["이름"] != 뺀]
    for c in 계:
        if c["붙는 곳"] == 뺀:
            c["붙는 곳"] = None
    print("통짜 본체 제외:", 뺀)
계 = sorted(계, key=lambda c: c["차례"])
for i, c in enumerate(계, 1):
    c["차례"] = i

모두 = trimesh.util.concatenate([p["메시"] for p in 부품])
lo, hi = 모두.bounds
s = float((hi - lo).max()) / 32000.0
rng = np.random.default_rng(4)


def 가볍게(m, 칸=90):
    """**정점 뭉치기** — 격자에 스냅해 용접하고 납작해진 면을 버린다.
    키트 STL 은 열려 있고 비다양체라 감면(quadric)이 95k 에서 멈추고, 복셀로 다시 구우면 계단이 생겨
    면 사이 각 중앙이 0.96° → 13.0° 로 뭉개진다(09-23 사용자 지적 「우둘투둘하다」).
    뭉치기는 원본 면을 그대로 쓰므로 90 칸에서 각 중앙 5° 안쪽을 지킨다."""
    피치 = float(max(m.extents)) / 칸
    v = np.asarray(m.vertices)
    q = np.rint(v / 피치).astype(np.int64)
    key, inv = np.unique(q, axis=0, return_inverse=True)
    nv = np.zeros((len(key), 3)); cnt = np.zeros(len(key))
    np.add.at(nv, inv, v); np.add.at(cnt, inv, 1)
    nv /= np.maximum(cnt, 1)[:, None]
    f = inv[np.asarray(m.faces)]
    f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
    g = trimesh.Trimesh(nv, f, process=False)
    g.remove_unreferenced_vertices(); g.fix_normals()
    return g


def 싸기(m):
    m = 가볍게(m)
    q = np.rint((m.vertices - lo) / s).astype(np.int16)
    return {"v": base64.b64encode(q.tobytes()).decode(), "f": base64.b64encode(m.faces.astype(np.uint32).tobytes()).decode()}


이름표 = {p["이름"]: p["메시"] for p in 부품}
부 = []
for c in 계:
    m = 이름표[c["이름"]]
    색 = "#%02x%02x%02x" % tuple(int(x) for x in rng.integers(90, 225, 3))
    부.append(dict(싸기(m), **{k: c[k] for k in ("차례", "이름", "붙는 곳", "끼우는 방향", "복판", "크기mm")}, 색=색))
꾸 = {"키트": os.path.basename(디.rstrip("\/")), "원점": [float(x) for x in lo], "눈금": s,
     "크기mm": [round(float(x), 1) for x in (hi - lo)], "부품": 부,
     "끼움 경고": A.겹침검사(부품, 계)}
out = os.path.join(H.OUT, "조립", 꾸["키트"]); os.makedirs(out, exist_ok=True)
p = os.path.join(out, "조립자료.json")
json.dump(꾸, open(p, "w", encoding="utf-8"))
print(p, round(os.path.getsize(p) / 1e6, 2), "MB · 부품", len(부), "· 경고", len(꾸["끼움 경고"]))
