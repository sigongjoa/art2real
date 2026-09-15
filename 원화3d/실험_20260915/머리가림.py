# -*- coding: utf-8 -*-
"""**머리카락 가림 — 입력 측정 (연구 루프 1)** (2026-09-15).

    python 머리가림.py 검사          자가검사만
    python 머리가림.py [케이스...]    VRoid 11장 (기본 전부) -> out/기록/머리가림_입력.json
    python 머리가림.py 그림 [케이스...] -> out/머리가림_<케이스>.png

물음 (0 문제): 정답 깊이를 넣어도 긴 머리 장은 0.62 에서 멈추고 짧은 머리 장은 0.84 까지 간다
(`out/기록/천장_실물.jsonl`). 방법을 탓하기 전에 입력부터 — 3판에서 머리카락이 **얼마나 보이고 얼마나 가려지나**.

정답은 VRoid 원본 재질 이름 (`_HAIR`) 이다. `시트.py` 의 그리기를 그대로 다시 돌려 화소마다 면 번호를 얻는다.

    머리몫      실루엣 중 보이는 머리카락 화소
    가려짐      머리카락만 따로 그린 실루엣 중, 전체 그림에서 머리카락으로 안 보이는 몫 (몸 · 옷에 가려진 머리)
    삐져나옴    실루엣 중 머리카락만 있는 화소 (몸 · 옷 실루엣 밖) — hull 이 머리카락 때문에 넓어지는 몫

`시트.py` 의 화가 알고리즘은 상호 관통에서 어긋난다 (그 파일 docstring). 가려짐은 그 오차를 안고 있다.
"""
import json
import os
import sys

import cv2
import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260913"))
os.chdir(HERE)
import win as W
import 시트 as S
from 재질 import CASES, cls_of_name                  # VRoid 11장 · 재질 이름 -> 0 천 · 1 피부 · 2 머리카락 · 3 얼굴/눈

OUTJ = os.path.join(HERE, "out", "기록", "머리가림_입력.json")
HAIR = 2


def load(case):
    """원본 모델 -> 창 좌표 정점 · 면 · 색 · 면 부류. `시트.py main` 과 같은 변환이고 truth.glb 와 정점이 같아야 한다."""
    scene = trimesh.load(os.path.join(HERE, "out", "시트", case, "_model.glb"))
    V, F, col, mat = S.faces_with_color(scene)
    names = [getattr(getattr(g.visual, "material", None), "name", "") for g in scene.geometry.values()]
    fcls = np.array([cls_of_name(names[m]) for m in mat], np.int8)
    Vw = W.to_world(V, "xyz")
    Vw[:, 1] *= -1
    Vw = W.normalize(Vw)
    t = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    assert t.vertices.shape == Vw.shape and np.allclose(t.vertices, Vw, atol=1e-5), "%s: truth.glb 와 정점이 다르다" % case
    return Vw, F, col, mat, fcls


def masks(Vw, F, col, mat, fcls, view):
    """(전체 실루엣, 보이는 머리카락, 머리카락만 그린 실루엣, 머리카락 뺀 실루엣)."""
    _, ident = S.draw(Vw, F, col, mat, view, line=False)
    sil = ident >= 0
    vis = sil & (fcls[np.clip(ident, 0, None)] == HAIR)
    h = fcls == HAIR
    only = lambda sel: S.draw(Vw, F[sel], col[sel], mat[sel], view, line=False)[1] >= 0 if sel.any() else np.zeros_like(sil)
    return sil, vis, only(h), only(~h)


def stats(sil, vis, hair, rest):
    n = max(int(sil.sum()), 1)
    return {"머리몫": round(vis.sum() / n, 4),
            "가려짐": round(float((hair & ~vis).sum() / max(int(hair.sum()), 1)), 4) if hair.any() else None,
            "삐져나옴": round(float((hair & ~rest).sum() / n), 4)}


def run(cases):
    out = json.load(open(OUTJ, encoding="utf-8")) if os.path.exists(OUTJ) else {}
    for c in cases:
        Vw, F, col, mat, fcls = load(c)
        row = {"머리 면": int((fcls == HAIR).sum()), "전체 면": len(F)}
        for v in W.VIEWS:
            row[v] = stats(*masks(Vw, F, col, mat, fcls, v))
        out[c] = row
        print("  %-24s 머리 면 %5d · " % (c[:24], row["머리 면"]) +
              " · ".join("%s 머리몫 %.3f 가려짐 %s 삐져나옴 %.3f" % (v[0], row[v]["머리몫"], row[v]["가려짐"], row[v]["삐져나옴"])
                         for v in W.VIEWS), flush=True)
        json.dump(out, open(OUTJ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  -> %s" % OUTJ)


def figure(cases):
    """시점마다 — 회색 몸·옷 · 파랑 보이는 머리카락 · 빨강 가려진 머리카락 · 주황 삐져나온 머리카락 테두리."""
    for c in cases:
        Vw, F, col, mat, fcls = load(c)
        tiles = []
        for v in W.VIEWS:
            sil, vis, hair, rest = masks(Vw, F, col, mat, fcls, v)
            im = np.full(sil.shape + (3,), 255, np.uint8)
            im[sil] = (190, 190, 190)
            im[vis] = (230, 120, 40)                          # BGR 파랑
            im[hair & ~vis] = (40, 40, 220)                   # 빨강
            ring = hair & ~rest
            im[ring & ~cv2.erode(ring.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)] = (0, 150, 255)
            cv2.putText(im, v, (20, 50), 0, 1.4, (0, 0, 0), 3)
            tiles.append(cv2.resize(im, (512, 512), interpolation=cv2.INTER_AREA))
        p = os.path.join(HERE, "out", "머리가림_%s.png" % c)
        cv2.imencode(".png", np.hstack(tiles))[1].tofile(p)
        print("  -> %s" % p)


def place(grids):
    """(bool 격자, 원점) 여럿을 한 인덱스 공간에. `정답.common` 을 여럿으로 편 것."""
    lo = np.min([o for _, o in grids], 0)
    hi = np.max([o + g.shape for g, o in grids], 0)
    out = []
    for g, o in grids:
        A = np.zeros(hi - lo, bool)
        A[tuple(slice(o[i] - lo[i], o[i] - lo[i] + g.shape[i]) for i in range(3))] = g
        out.append(A)
    return out


def blame(extra, parts):
    """넘친 복셀마다 **가장 가까운 정답 부품**의 이름. 반환: 부품별 몫."""
    from scipy import ndimage
    d = np.stack([ndimage.distance_transform_edt(~p) if p.any() else np.full(p.shape, np.inf) for p in parts])
    who = d[:, extra].argmin(0)
    return np.bincount(who, minlength=len(parts)) / max(int(extra.sum()), 1)


OVERJ = os.path.join(HERE, "out", "기록", "머리가림_넘침.json")
PART = {"머리카락": lambda c: c == HAIR, "천": lambda c: c == 0, "피부·얼굴": lambda c: (c == 1) | (c == 3)}


def overflow(cases):
    """hull 이 정답보다 넘친 부피(이진 · 타원 lam1.00)를 가장 가까운 정답 부품에 나눠 준다 (격자 128)."""
    import 오라클 as O
    import 정답 as J
    out = json.load(open(OVERJ, encoding="utf-8")) if os.path.exists(OVERJ) else {}
    for c in cases:
        Vw, F, _, _, fcls = load(c)
        truth = trimesh.Trimesh(Vw, F, process=False)
        plain, deep, axes, _ = O.build(c, truth, 1.00, "타원")
        grids = [J.grid(truth)] + [J.grid(O.C.to_mesh(v, axes)) for v in (plain, deep)]
        for name, sel in PART.items():
            s = sel(fcls)
            grids.append(J.grid(trimesh.Trimesh(Vw, F[s], process=False)) if s.any() else (np.zeros((1, 1, 1), bool), np.zeros(3, int)))
        T, Gp, Gd, *parts = place(grids)
        row = {}
        for tag, G in (("이진", Gp), ("타원", Gd)):
            extra = G & ~T
            row[tag] = {"넘침/정답": round(extra.sum() / T.sum(), 3),
                        **{k: round(float(v), 3) for k, v in zip(PART, blame(extra, parts))}}
        row["정답 부피 몫"] = {k: round(float(p.sum() / T.sum()), 3) for k, p in zip(PART, parts)}
        out[c] = row
        print("  %-24s 정답몫 %s · 이진 넘침 %.2f %s · 타원 넘침 %.2f %s" % (
            c[:24], row["정답 부피 몫"], row["이진"]["넘침/정답"], {k: row["이진"][k] for k in PART},
            row["타원"]["넘침/정답"], {k: row["타원"][k] for k in PART}), flush=True)
        json.dump(out, open(OVERJ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  -> %s" % OVERJ)


def selfcheck():
    # 몸 상자 뒤에 머리카락 판 — 정면에선 몸이 머리카락을 가리고, 뒤에선 머리카락이 보인다. 위로 삐져나온 몫이 있다
    body = trimesh.creation.box((0.4, 0.3, 0.8))
    hair = trimesh.creation.box((0.3, 0.05, 0.6))
    # `시트.draw` 의 front 카메라는 +y 쪽을 본다 (먼 쪽부터 칠하는 순서로 확인) — 그래서 머리카락은 −y 가 뒤다.
    # 처음에 +y 에 뒀다가 이 검사가 거꾸로 걸렸다 (2026-09-15)
    hair.apply_translation([0, -0.25, 0.2])                  # 뒤 · 위로 0.1 삐져나옴
    m = trimesh.util.concatenate([body, hair])
    Vw = W.normalize(np.asarray(m.vertices, np.float64))
    F = np.asarray(m.faces, np.int64)
    fcls = np.r_[np.zeros(len(body.faces), np.int8), np.full(len(hair.faces), HAIR, np.int8)]
    col = np.full((len(F), 3), 200, np.uint8)
    mat = fcls.astype(np.int32)
    f = stats(*masks(Vw, F, col, mat, fcls, "front"))
    b = stats(*masks(Vw, F, col, mat, fcls, "back"))
    assert f["가려짐"] > 0.6 and b["가려짐"] < 0.02, "앞에선 가려지고 뒤에선 보여야 한다 (%s · %s)" % (f, b)
    assert f["삐져나옴"] > 0 and abs(f["삐져나옴"] - b["삐져나옴"]) < 0.01, "삐져나옴은 앞뒤가 같아야 한다 (%s · %s)" % (f, b)
    # 넘침 나누기 — 두 부품 사이 틈의 복셀은 가까운 쪽으로 간다
    pa, pb = np.zeros((10, 1, 1), bool), np.zeros((10, 1, 1), bool)
    pa[0], pb[9] = True, True
    ex = np.zeros((10, 1, 1), bool)
    ex[1:3] = ex[7] = True
    assert np.allclose(blame(ex, [pa, pb]), [2 / 3, 1 / 3]), "넘침 나누기가 틀렸다 %s" % blame(ex, [pa, pb])
    print("  자가검사 통과 — 앞 가려짐 %.2f · 뒤 가려짐 %.2f · 삐져나옴 %.3f · 넘침 나누기" % (f["가려짐"], b["가려짐"], f["삐져나옴"]))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["검사"]:
        selfcheck()
    elif a[:1] == ["넘침"]:
        overflow(a[1:] or CASES)
    elif a[:1] == ["그림"]:
        figure(a[1:] or ["avatarsample_g", "hairsample_female", "base_female"])
    else:
        selfcheck()
        run(a or CASES)
