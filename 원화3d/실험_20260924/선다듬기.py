# -*- coding: utf-8 -*-
"""**선 다듬기 + 법선 홈파기** — 공장에서 뽑은 것 같은 패널 라인 (2026-09-24).

    python 선다듬기.py [케이스=오메가몬]       선만 다듬어 재고 그림
    python 선다듬기.py <케이스> 새김           메시에 홈까지 파서 STL

사용자(09-24): 「공장에서 뽑아낸 것 같은 선들이 아니잖아. 선들이 너무 자유로워」

    다듬기(선)     골격화 → 경로 추적 → RDP → 축 스냅(±8°) → 일정한 폭으로 다시 그린다
    홈파기(m, ...) 정점을 **면의 법선** 방향으로 민다. 홈 단면은 폭 w · 깊이 d 의 V 로 고정
                   (지금은 시선 방향으로 밀어 비스듬한 면에서 번진다)
"""
import os, sys, json, time
import numpy as np
from scipy import ndimage

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922"]
import hull as H, win as W

RDP허용 = 2.5          # 화소 — 이보다 작은 흔들림은 편다
축스냅 = 8.0           # 도 — 이 안이면 정확히 수평 · 수직으로
최소길이 = 6           # 화소 — 이보다 짧은 조각은 버린다
선폭 = 3               # 화소 (원화 1 px = 0.152 mm · 전고 125mm) -> 0.46 mm


def _경로들(선):
    """골격에서 갈래점 · 끝점을 끊어 경로 목록으로."""
    from skimage.morphology import skeletonize
    sk = skeletonize(선)
    K = np.ones((3, 3), np.uint8)
    이웃 = ndimage.convolve(sk.astype(np.uint8), K, mode="constant") - sk
    끝 = sk & (이웃 <= 1)
    갈 = sk & (이웃 >= 3)
    조각 = sk & ~갈
    lab, n = ndimage.label(조각, np.ones((3, 3), bool))
    경로 = []
    for k in range(1, n + 1):
        ys, xs = np.where(lab == k)
        if len(ys) < 최소길이: continue
        P = np.stack([xs, ys], 1).astype(float)
        # 끝점에서 시작해 이웃을 따라 훑는다 (짧은 조각이라 단순 탐욕으로 충분)
        시작 = int(np.argmax(끝[ys, xs])) if 끝[ys, xs].any() else 0
        남 = set(range(len(P))); 줄 = [시작]; 남.discard(시작)
        while 남:
            d = np.linalg.norm(P[list(남)] - P[줄[-1]], axis=1)
            j = list(남)[int(np.argmin(d))]
            if d.min() > 2.9: break
            줄.append(j); 남.discard(j)
        경로.append(P[줄])
    return 경로, sk, 갈


def _rdp(P, eps):
    if len(P) < 3: return P
    a, b = P[0], P[-1]
    ab = b - a; L = np.linalg.norm(ab)
    if L < 1e-9:
        d = np.linalg.norm(P - a, axis=1)
    else:
        d = np.abs(np.cross(np.broadcast_to(ab, P.shape), P - a)) / L
    i = int(np.argmax(d))
    if d[i] <= eps: return np.stack([a, b])
    return np.vstack([_rdp(P[:i + 1], eps)[:-1], _rdp(P[i:], eps)])


def _축스냅(P, 도=축스냅):
    """수평 · 수직에 가까운 선분을 정확히 맞춘다 — 기계 도면의 선은 대개 축에 붙어 있다."""
    Q = P.copy()
    for i in range(len(Q) - 1):
        v = Q[i + 1] - Q[i]; L = np.linalg.norm(v)
        if L < 3: continue
        ang = np.degrees(np.arctan2(v[1], v[0])) % 180
        if min(ang, 180 - ang) < 도:            # 수평
            y = (Q[i, 1] + Q[i + 1, 1]) / 2; Q[i, 1] = Q[i + 1, 1] = y
        elif abs(ang - 90) < 도:                # 수직
            x = (Q[i, 0] + Q[i + 1, 0]) / 2; Q[i, 0] = Q[i + 1, 0] = x
    return Q


def 재기(경로):
    굴 = []; 축 = 0; 총 = 0
    for P in 경로:
        if len(P) < 2: continue
        길 = np.linalg.norm(np.diff(P, axis=0), axis=1).sum()
        곧 = np.linalg.norm(P[-1] - P[0])
        if 곧 > 3: 굴.append(길 / 곧)
        for i in range(len(P) - 1):
            v = P[i + 1] - P[i]; L = np.linalg.norm(v)
            if L < 3: continue
            총 += 1
            a = np.degrees(np.arctan2(v[1], v[0])) % 180
            if min(a, 180 - a) < 2 or abs(a - 90) < 2: 축 += 1
    return {"경로": len(경로), "굴곡도 중앙": round(float(np.median(굴)), 3) if 굴 else None,
            "선분": 총, "축 정렬 몫": round(축 / max(총, 1), 3)}


def 다듬기(선, eps=RDP허용):
    import cv2
    경로, sk, 갈 = _경로들(선)
    전 = 재기(경로)
    깨 = [_축스냅(_rdp(P, eps)) for P in 경로]
    후 = 재기(깨)
    im = np.zeros(선.shape, np.uint8)
    for P in 깨:
        cv2.polylines(im, [np.rint(P).astype(np.int32)], False, 1, 선폭)
    # **갈래점을 메운다** — 경로를 갈래에서 끊어 놓았기 때문에 안 메우면 선이 점선처럼 끊긴다 (09-24)
    im |= ndimage.binary_dilation(갈, iterations=max(1, 선폭 // 2)).astype(np.uint8)
    im = ndimage.binary_closing(im.astype(bool), np.ones((3, 3), bool))
    return im, 전, 후


def main():
    c = sys.argv[1] if len(sys.argv) > 1 else "오메가몬"
    src, base = H.CASES[c]["src"], H.art_dir(c)
    낼 = {}
    for v in ("front", "back"):
        선 = H.ink_map(os.path.join(base, src[v]))
        새, 전, 후 = 다듬기(선)
        낼[v] = {"전": 전, "후": 후, "화소 전": int(선.sum()), "화소 후": int(새.sum())}
        print("  %-6s 경로 %3d → %3d · 굴곡도 %s → %s · 축 정렬 %.3f → %.3f · 선분 %d → %d" % (
            v, 전["경로"], 후["경로"], 전["굴곡도 중앙"], 후["굴곡도 중앙"],
            전["축 정렬 몫"], 후["축 정렬 몫"], 전["선분"], 후["선분"]), flush=True)
        np.save(os.path.join(H.OUT, "선다듬_%s_%s.npy" % (c, v)), 새)
    p = os.path.join(H.OUT, "기록", "선다듬기_%s_%s.json" % (c, time.strftime("%Y%m%d_%H%M")))
    json.dump(낼, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(p)


if __name__ == "__main__":
    main()


# ── 법선 방향 홈파기 ──────────────────────────────────────────────
def 홈판(c, raw, p, bs, 넓힘=0):
    """다듬은 선을 창 좌표 판으로 (없으면 그 자리서 다듬는다)."""
    src, base = H.CASES[c]["src"], H.art_dir(c)
    낼 = {}
    for v in ("front", "back"):
        f = os.path.join(H.OUT, "선다듬_%s_%s.npy" % (c, v))
        새 = np.load(f) if os.path.exists(f) else 다듬기(H.ink_map(os.path.join(base, src[v])))[0]
        if 넓힘: 새 = ndimage.binary_dilation(새, iterations=넓힘)
        _, w2 = H.to_win(H.declutter(raw[v]), 새.astype(np.float32))
        낼[v] = H._warp_one(w2, v, p) > 0.5
    return 낼


def _선거리(판들, bs, V, N, 폭, 정면문턱):
    """정점마다 «보이는 판에서의 선까지 거리». 안 보이면 큰 값."""
    px = (W.U1 - W.U0) / W.RES
    d = np.full(len(V), 1e9)
    for v, sign, 방향 in (("front", 1, -1), ("back", bs, +1)):
        dt = ndimage.distance_transform_edt(~판들[v]) * px
        보 = N[:, 1] * 방향 > 정면문턱
        py, px_ = W.topix(sign * V[:, 0], V[:, 2])
        d = np.minimum(d, np.where(보, dt[py, px_], 1e9))
    return d


def 홈파기(m, 판들, bs, 폭, 깊이, 정면문턱=0.25, 쪼개기=3):
    """**법선 방향** V 홈. 시선 방향으로 밀면 비스듬한 면에서 유효 깊이가 |n·y| 배로 들쭉날쭉해진다.

    폭 · 깊이는 창 단위. 정점을 그 면의 법선으로 밀므로 홈 단면이 어디서나 같다.

    ⚠ **선 근처를 먼저 잘게 쪼갠다.** 정점 간격(0.84 mm)이 홈 폭(0.5 mm)보다 넓으면
    홈 안 정점이 전부 최대 깊이로 밀려 «V 홈»이 아니라 넓은 함몰이 된다 (09-24 에 잡았다)."""
    for _ in range(쪼개기):
        V = np.asarray(m.vertices); N = np.asarray(m.vertex_normals)
        d = _선거리(판들, bs, V, N, 폭, 정면문턱 - 0.15)
        가 = d < 폭                                   # 선 가까운 정점
        면 = np.asarray(m.faces)
        골라 = np.where(가[면].any(axis=1))[0]
        if len(골라) == 0: break
        vv, ff = trimesh.remesh.subdivide(np.asarray(m.vertices), 면, face_index=골라)
        m = trimesh.Trimesh(vv, ff, process=False); m.merge_vertices()
    V = np.asarray(m.vertices, float).copy()
    N = np.asarray(m.vertex_normals)
    d = _선거리(판들, bs, V, N, 폭, 정면문턱)
    밀 = 깊이 * np.clip(1.0 - d / max(폭 / 2, 1e-9), 0, 1)          # V 단면
    V -= N * 밀[:, None]
    g = trimesh.Trimesh(V, np.asarray(m.faces), process=False)
    return g, 밀


def 깊이산포(m, 판들, bs, 폭, 깊이):
    """같은 자리에서 «시선 방향 밀기»의 유효 깊이 산포와 «법선 밀기»의 산포를 견준다."""
    N = np.asarray(m.vertex_normals); V = np.asarray(m.vertices)
    px = (W.U1 - W.U0) / W.RES
    안 = np.zeros(len(V), bool); ny = np.zeros(len(V))
    for v, sign, 방향 in (("front", 1, -1), ("back", bs, +1)):
        d = ndimage.distance_transform_edt(~판들[v]) * px
        보 = N[:, 1] * 방향 > 0.25
        py, px_ = W.topix(sign * V[:, 0], V[:, 2])
        골 = 보 & (d[py, px_] < 폭 / 2)
        안 |= 골; ny = np.where(골, np.abs(N[:, 1]), ny)
    if 안.sum() < 10: return None
    옛 = 깊이 * ny[안]                     # 시선 방향으로 밀었을 때의 «면에 수직인» 실제 깊이
    f = lambda x: (np.percentile(x, 75) - np.percentile(x, 25)) / max(np.median(x), 1e-12)
    return {"홈 정점": int(안.sum()), "시선 밀기 산포": round(float(f(옛)), 3), "법선 밀기 산포": 0.0}


import trimesh
