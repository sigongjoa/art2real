# -*- coding: utf-8 -*-
"""**먹선 분할** — 원화의 먹선을 부피에 밀어 넣어 그 자리를 가른다 (2026-09-24).

    python 먹선분할.py [케이스=오메가몬] [전고=125]

지금까지 먹선은 «표면에 새기는 것»이고 자르는 자리는 «분수령»이 따로 정했다. 둘이 만난 적이 없다.
여기서는 먹선을 벽으로 세워 부피를 가른다 — 그러면 **분할선이 곧 먹선**이다.

    먹선벽(...)   앞 · 뒤 먹선을 시선 방향으로 밀어 3D 벽을 만든다
    가르기(...)   O 에서 벽을 빼고 이어진 덩어리로 나눈 뒤, 벽을 제일 가까운 부품에 돌려준다
    먹선몫(...)   부품 경계 면적 중 먹선 위에 있는 몫 — **뒤섞기 대조군과 같이 잰다**
"""
import json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np, trimesh
from scipy import ndimage

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921",
                r"G:\art2real\원화3d\실험_20260922", r"G:\art2real\원화3d\실험_20260923"]
import hull as H, win as W, 부품분할 as BB, 면자르기 as MJ, 지표 as Z

최소몫 = 0.0015


def 창먹선(c, raw, p, bs, 넓힘=1):
    """앞 · 뒤 먹선을 창 좌표 1024 판으로."""
    src, base = H.CASES[c]["src"], H.art_dir(c)
    낼 = {}
    for v in ("front", "back"):
        선 = H.ink_map(os.path.join(base, src[v]))
        if 넓힘: 선 = ndimage.binary_dilation(선, iterations=넓힘)
        _, w2 = H.to_win(H.declutter(raw[v]), 선.astype(np.float32))
        낼[v] = H._warp_one(w2, v, p) > 0.5
    return 낼


def _열(선판, ux, z, sign):
    """격자 (i,k) 마다 그 자리의 먹선 여부 — 창 화소로 표본."""
    col = (sign * ux - W.U0) / (W.U1 - W.U0) * W.RES - 0.5
    row = (W.Z1 - z) / (W.Z1 - W.Z0) * W.RES - 0.5
    C, R = np.meshgrid(col, row, indexing="ij")
    return ndimage.map_coordinates(선판.astype(np.float32), [R, C], order=1, mode="nearest") > 0.5


def 먹선벽(O, 선들, ux, z, bs, 두께=1):
    """앞 · 뒤 먹선을 **시선 방향으로 끝까지** 밀어 벽을 세운다.
    솔리드에서는 겉면의 판 경계가 안쪽으로 이어진 면이라고 본다."""
    벽 = np.zeros_like(O)
    for v, sign in (("front", 1), ("back", bs)):
        m = _열(선들[v], ux, z, sign)                     # (i,k)
        벽 |= m[:, None, :] & O
    if 두께 > 1:
        벽 = ndimage.binary_dilation(벽, iterations=두께 - 1) & O
    return 벽


def 가르기(O, 벽, 최소=최소몫):
    C = np.ones((3, 3, 3), bool)
    lab, n = ndimage.label(O & ~벽, C)
    크 = np.bincount(lab.ravel()); 크[0] = 0
    작 = np.where((크 > 0) & (크 < 최소 * O.sum()))[0]
    if len(작):
        큰 = ~np.isin(lab, 작) & (lab > 0)
        if 큰.any():
            i = ndimage.distance_transform_edt(~큰, return_distances=False, return_indices=True)
            lab = np.where(np.isin(lab, 작) | (lab == 0), lab[tuple(i)], lab)
    # 벽을 제일 가까운 부품에 돌려준다
    i = ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
    lab = np.where(O, lab[tuple(i)], 0)
    _, lab = np.unique(lab, return_inverse=True)
    return lab.reshape(O.shape)


def 먹선몫(lab, 선들, ux, z, bs, O):
    """부품 «경계 겉면» 중 먹선 위에 있는 몫. 경계면을 겉에서 본 자리로 판단한다."""
    # **둘 다 부품일 때만** 경계다. `lab` 은 바깥이 0 이라 그냥 diff 를 쓰면 겉면 전체가 경계가 된다
    # (09-24 에 네 판본이 모두 0.378 로 같아서 잡았다).
    경 = np.zeros_like(O)
    for ax in range(3):
        a0 = np.take(lab, range(0, lab.shape[ax] - 1), axis=ax)
        a1 = np.take(lab, range(1, lab.shape[ax]), axis=ax)
        d = (a0 != a1) & (a0 > 0) & (a1 > 0)
        경 |= np.pad(d, [(0, 0)] * ax + [(0, 1)] + [(0, 0)] * (2 - ax))
        경 |= np.pad(d, [(0, 0)] * ax + [(1, 0)] + [(0, 0)] * (2 - ax))
    경 &= O
    겉 = O & ~ndimage.binary_erosion(O)
    표 = 경 & 겉                                   # 겉면에 드러난 분할선
    if 표.sum() == 0: return 0.0
    선3 = np.zeros_like(O)
    for v, sign in (("front", 1), ("back", bs)):
        선3 |= _열(선들[v], ux, z, sign)[:, None, :]
    return float((표 & 선3).sum() / 표.sum())


def 뒤섞기(선판, rng):
    """**대조군** — 먹선 덩어리를 같은 개수 · 같은 모양으로 자리만 무작위로 옮긴다."""
    lab, n = ndimage.label(선판)
    낼 = np.zeros_like(선판)
    for k in range(1, n + 1):
        ys, xs = np.where(lab == k)
        dy = rng.integers(-W.RES // 6, W.RES // 6); dx = rng.integers(-W.RES // 6, W.RES // 6)
        y2 = np.clip(ys + dy, 0, W.RES - 1); x2 = np.clip(xs + dx, 0, W.RES - 1)
        낼[y2, x2] = True
    return 낼


def main():
    c = sys.argv[1] if len(sys.argv) > 1 else "오메가몬"
    전고 = float(sys.argv[2]) if len(sys.argv) > 2 else 125.0
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    O = g > 0
    선들 = 창먹선(c, raw, p, bs)
    _, 부위, _ = MJ.부위(O); 부위 = BB.채우기(부위, O)
    벽 = 먹선벽(O, 선들, ux, z, bs)
    print("  먹선 벽이 차지하는 칸 %.1f%%" % (100 * 벽.sum() / O.sum()))
    판 = {"지금(분수령)": 부위, "먹선만": 가르기(O, 벽)}
    경 = np.zeros_like(O)
    for a2 in range(3):
        a0 = np.take(부위, range(0, 부위.shape[a2] - 1), axis=a2)
        a1 = np.take(부위, range(1, 부위.shape[a2]), axis=a2)
        d = (a0 != a1) & (a0 > 0) & (a1 > 0)
        경 |= np.pad(d, [(0, 0)] * a2 + [(0, 1)] + [(0, 0)] * (2 - a2))
    판["분수령+먹선"] = 가르기(O, 벽 | (경 & O))
    rng = np.random.default_rng(0)
    섞 = {v: 뒤섞기(선들[v], rng) for v in 선들}
    판["대조:먹선 뒤섞기"] = 가르기(O, 먹선벽(O, 섞, ux, z, bs))
    낼 = {}
    for 이름, lab in 판.items():
        n = int(lab.max())
        몫 = 먹선몫(lab, 선들, ux, z, bs, O)
        낼[이름] = {"부품": n, "먹선 위 몫": round(몫, 3)}
        print("  %-14s 부품 %3d   분할선이 먹선 위 %.3f" % (이름, n, 몫), flush=True)
    pth = os.path.join(H.OUT, "기록", "먹선분할_%s_%s.json" % (c, time.strftime("%Y%m%d_%H%M")))
    json.dump(낼, open(pth, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    np.save(os.path.join(H.OUT, "먹선분할_%s.npy" % c), 판["분수령+먹선"].astype(np.int16))
    print(pth)


if __name__ == "__main__":
    main()
