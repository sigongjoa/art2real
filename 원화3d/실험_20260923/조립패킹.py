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


def 가볍게(m, 칸=120):
    """키트 STL 은 비다양체가 많아 감면이 안 먹는다 — 복셀로 다시 굽는다(보기용)."""
    from scipy import ndimage
    from skimage import measure
    피치 = float(max(m.extents)) / 칸
    V = m.voxelized(pitch=피치).fill()
    A = np.pad(np.asarray(V.matrix, bool), 2)
    f = ndimage.gaussian_filter(A.astype(np.float32), 0.8)
    v, faces, _, _ = measure.marching_cubes(f, 0.5)
    v = (v - 2) * 피치 + np.asarray(V.transform)[:3, 3]
    g = trimesh.Trimesh(v, faces[:, ::-1], process=False)
    g.fix_normals()
    if len(g.faces) > 2500:
        g = g.simplify_quadric_decimation(face_count=2500)
    return g


def 싸기(m, 면한도=2500):
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
