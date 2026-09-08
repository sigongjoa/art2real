# -*- coding: utf-8 -*-
"""**스탠드 판정기.** `judge_part3d.py` 의 자를 빌리되 견갑 전용 항을 갈아끼운다.

    python judge_stand.py in/stand_Doggy_Style.png out/st_doggy.glb [...]

견갑 판정기는 실측 상자(U0..Z1)와 원화 마스크가 박혀 있어 스탠드엔 못 쓴다. 여기서는
**모델의 정면 bbox 를 원화 bbox 에 한 배율로 맞춘다** — 실측 상자가 없으니 종횡비만
안 깨고 맞추는 게 최선이고, 그래서 IoU 는 「크기」가 아니라 「모양」을 재는 수가 된다.

## 축을 짐작하지 않는다

생성 GLB 는 **Y-up** 이다 (PartCrafter·TripoSG 둘 다 확인: 제일 긴 축이 y).
`judge_part3d.silhouette` 은 `topix(x, z)` 로 z 를 위로 읽는데 그건 trail6 손모델이
블렌더 Z-up 이라 맞는 규약이고, GLB 에 그대로 대면 **위에서 내려다본 그림**이 된다.

여기서는 짐작하지 않고 잰다 — **제일 짧은 축이 깊이, 제일 긴 축이 위쪽**, 나머지가 가로다.
서 있는 물건에서는 성립하고, 어긋나면 `--axes` 로 못 박는다. 쓴 축을 항상 같이 찍는다.

## 새로 넣은 항 둘 — 둘 다 실제로 난 실패에서 나왔다

**두께비.** trail7 README 가 못 박은 빈칸이다. OmniPart 판이 cfg 를 올리자 IoU 가 올랐는데
형태가 나아서가 아니라 삐져나감이 줄어서였다 — 실루엣 하나로는 「접시」와 「입체」를
못 가른다. 깊이 범위를 가로세로 중 큰 쪽으로 나눈다. 종이는 0 에 가깝다.

**파트 붙음률.** 견갑에서 PartCrafter 가 낸 실패가 이것이다 — 파트 5개 중 하나가 면의
57% 를 갖고 나머지 넷은 그 물건과 안 붙었다. 같은 그림을 두 번 해석해 공간에 떨어뜨린
꼴이다. 파트 bbox 가 다른 파트와 하나라도 겹치는 비율로 잡는다.
"""
import json
import os
import sys

import cv2
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from judge_part3d import cone_ratio          # PCA 고윳값 — 그대로 빌린다

RES = 512


def art_mask(png):
    """알파는 **흰 바탕에 얹고** 읽는다. IMREAD_COLOR 로 그냥 열면 투명한 데가 검게 들어와
    전경이 99% 로 잡힌다 — 스탠드 PNG 가 RGB 라 여태 안 걸렸을 뿐이다."""
    im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_UNCHANGED)
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    if im.shape[2] == 4:
        a = im[:, :, 3:4].astype(np.float32) / 255.0
        im = (im[:, :, :3] * a + 255 * (1 - a)).astype(np.uint8)
    m = (im[:, :, :3] < 250).any(2)
    return fit_box(m)


def fit_box(m, res=RES):
    """마스크를 제 bbox 로 잘라 res 격자에 세로 기준으로 앉힌다 (종횡비 유지)."""
    ys, xs = np.where(m)
    if len(ys) == 0:
        return np.zeros((res, res), bool)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    s = (res - 2) / m.shape[0]
    w = max(1, int(round(m.shape[1] * s)))
    r = cv2.resize(m.astype(np.uint8), (w, res - 2), interpolation=cv2.INTER_NEAREST).astype(bool)
    out = np.zeros((res, res), bool)
    x0 = max(0, (res - w) // 2)
    out[1:res - 1, x0:x0 + min(w, res - x0)] = r[:, :min(w, res - x0)]
    return out


def axes(V):
    """(가로, 위, 깊이) 축 번호. 깊이 = 제일 짧은 축, 위 = 제일 긴 축."""
    e = V.max(0) - V.min(0)
    d = int(np.argmin(e)); u = int(np.argmax(e))
    if d == u:
        d, u = 2, 1
    h = ({0, 1, 2} - {d, u}).pop()
    return h, u, d


def mesh_mask(parts, ax):
    """정면 투영. **삼각형을 칠한다.**

    처음엔 정점만 찍고 7x7 로 닫았다. Doggy Style(정점 42만, 뭉툭함)은 메워졌지만
    야스호(13만, 가늘고 김)는 구멍이 나서 덮음 19% · 삐져나감 5.8% 가 나왔다 —
    참조 안에 들어는 있는데 성글다는 뜻이다. 그 조합이 보이면 채우기를 의심한다.

    **삼각형은 하나씩 칠한다 (2026-09-02 고침).** `cv2.fillPoly` 에 여러 개를 한 번에
    넘기면 합집합이 아니라 **짝수-홀수로 칠한다** — 앞면과 뒷면이 서로를 지운다.
    판때기 12면으로 재보면 한 번에 5,533 화소, 하나씩이면 744,309 화소다. 20,000개씩
    끊어 부르던 때는 **청크 경계에서 우연히 살아남은 것만 남았다.** 그전에 이 함수로
    잰 스탠드·야스호 숫자는 그래서 못 쓴다. `judge_part3d.silhouette` 은 제 래스터를
    써서 이 문제가 없다(견갑 숫자는 유효).
    91.8만 면에 1.0초 — 판정에 쓰기 충분하다."""
    h, u, _d = ax
    allV = np.vstack([np.asarray(p.vertices) for p in parts])
    lo, hi = allV.min(0), allV.max(0)
    span = max(hi[h] - lo[h], hi[u] - lo[u], 1e-9)
    g = np.zeros((RES * 2, RES * 2), np.uint8)
    for p in parts:
        V = np.asarray(p.vertices)
        px = ((V[:, h] - lo[h]) / span * (RES * 2 - 4) + 2)
        py = ((hi[u] - V[:, u]) / span * (RES * 2 - 4) + 2)
        P = np.stack([px, py], 1).astype(np.int32)
        for tri in P[np.asarray(p.faces)]:
            cv2.fillConvexPoly(g, tri, 1)                   # 하나씩. 한꺼번에는 XOR 이 된다
    return fit_box(g.astype(bool))


def thickness(V, ax=None):
    """깊이 범위 / 가로세로 중 큰 쪽. 종이는 0, 공은 1 근처."""
    h, u, d = axes(V) if ax is None else ax
    lo, hi = V.min(0), V.max(0)
    return float((hi[d] - lo[d]) / max(hi[h] - lo[h], hi[u] - lo[u], 1e-9))


def attached(parts, tol=0.02):
    """파트 bbox 가 다른 파트와 하나라도 겹치나. 견갑에서 넷이 떨어져 나갔던 항."""
    if len(parts) < 2:
        return 1.0
    B = [(np.asarray(p.vertices).min(0), np.asarray(p.vertices).max(0)) for p in parts]
    span = max(np.vstack([b[1] for b in B]).max(0) - np.vstack([b[0] for b in B]).min(0))
    t = tol * span
    n = 0
    for i, (lo, hi) in enumerate(B):
        if any(((lo - t) <= h2).all() and ((hi + t) >= l2).all()
               for j, (l2, h2) in enumerate(B) if j != i):
            n += 1
    return n / len(B)


def judge(png, path):
    sc = trimesh.load(path)
    parts = list(sc.geometry.values()) if isinstance(sc, trimesh.Scene) else [sc]
    allV0 = np.vstack([np.asarray(p.vertices) for p in parts])
    ax = axes(allV0)
    ART = art_mask(png)
    M = mesh_mask(parts, ax)
    inter, uni = int((M & ART).sum()), int((M | ART).sum())
    allV = np.vstack([np.asarray(p.vertices) for p in parts])

    print("\n== %s  <-  %s" % (os.path.basename(path), os.path.basename(png)))
    print("  %-4s %9s %8s %8s" % ("파트", "면", "두께비", "평판도"))
    for i, p in enumerate(parts):
        V = np.asarray(p.vertices)
        e1e3, _ = cone_ratio(V)
        print("  %-4d %9d %8.3f %8.2f" % (i, len(p.faces), thickness(V, ax), 1.0 / max(e1e3, 1e-9)))
    r = dict(name=os.path.basename(path), parts=len(parts),
             faces=int(sum(len(p.faces) for p in parts)),
             iou=inter / max(uni, 1), cover=inter / max(ART.sum(), 1),
             spill=float((M & ~ART).sum() / max(M.sum(), 1)),
             thickness=thickness(allV, ax), attached=attached(parts),
             axes="".join("xyz"[a] for a in ax))
    print("  실루엣 IoU %.3f · 덮음 %.1f%% · 삐져나감 %.1f%%"
          % (r["iou"], r["cover"] * 100, r["spill"] * 100))
    print("  전체 두께비 %.3f  (0.15 밑이면 접시)   파트 붙음 %.0f%%"
          % (r["thickness"], r["attached"] * 100))
    return r


def demo():
    box = trimesh.creation.box((1, 1, 1))
    plate = trimesh.creation.box((1, 0.02, 1))
    assert thickness(np.asarray(box.vertices)) == 1.0
    assert thickness(np.asarray(plate.vertices)) < 0.05, "판은 두께비가 0 근처여야"
    # 축 추정 — 서 있는 막대는 위 y, 깊이 z
    rod = trimesh.creation.box((0.3, 2.0, 0.1))
    assert axes(np.asarray(rod.vertices)) == (0, 1, 2), axes(np.asarray(rod.vertices))
    lying = trimesh.creation.box((2.0, 0.3, 0.1))
    assert axes(np.asarray(lying.vertices)) == (1, 0, 2), axes(np.asarray(lying.vertices))
    far = trimesh.creation.box((1, 1, 1)); far.apply_translation((9, 0, 0))
    assert attached([box, plate]) == 1.0, "겹친 둘은 100%"
    assert attached([box, far]) == 0.0, "떨어진 둘은 0%"
    m = np.zeros((40, 20), bool); m[5:35, 5:15] = True
    f = fit_box(m, res=64)
    assert f.sum() > 0 and f[0].sum() == 0 and f[-1].sum() == 0, "세로로 꽉 차되 테두리 한 줄은 비어야"
    print("자체검사 통과")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo(); raise SystemExit
    a = sys.argv[1:]
    res = [judge(a[i], a[i + 1]) for i in range(0, len(a) - 1, 2)]
    json.dump(res, open(os.path.join(HERE, "out", "judge_stand.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
