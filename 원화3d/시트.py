# -*- coding: utf-8 -*-
"""**정답이 있는 턴어라운드를 만든다.** 3D 모델 -> 직교 3판 + 진짜 메시.

    python 시트.py [모델.vrm|.glb] [--이름 이름]
        -> out/시트/<이름>/{front,side,back}.png + truth.glb

## 왜 필요한가

지금 검증은 전부 **실루엣끼리**다. hull 을 되던져 원화와 겹치는 것뿐이라 「형태가 맞나」가
아니라 「그림자가 맞나」를 잰다. trail7 이 남긴 경고가 그거다 —
「판정기에 두께 항이 필요하다. 지금은 이 실패가 숫자로 안 잡힌다.」

3D 모델에서 판을 뽑으면 **원본 메시가 정답으로 남는다.** 그러면 처음으로 3D IoU 를 잰다.
그리고 세 판이 같은 키·직교인 게 **구조적으로 보장**된다 — `win.normalize` 가 높이로 한 번
재고 세 시점이 그 배율을 공유하니까, 손그림에서 겪은 판마다 다른 bbox 키 문제가 없다.

## 이게 검증하지 못하는 것

**렌더한 판은 너무 깨끗하다.** 세 판이 자동으로 완벽히 맞으므로 오메가몬에서 나온 문제들 —
`align` 이 필요한 이유, 발의 작화 모순 — 은 여기서 **재현되지 않는다.**
즉 파이프라인 상수(`LAM`·`THRESH`)는 검증되지만 **판 불일치 처리는 검증이 안 된다.**
손그림 턴어라운드 한 세트는 따로 필요하다.

## 그림 규약

셀 작화 흉내다. 면마다 UV 중심에서 텍스처를 한 번 찍어 **평면으로 칠하고**(그라데이션 없음),
재질이 바뀌는 자리와 깊이가 튀는 자리에 **검은 선**을 넣는다. `art3d` 가 기대하는 입력이
바로 이것 — 톤 계단과 선이다.

깊이 정렬은 화가 알고리즘이다. `ponytail: 머리카락이 얼굴을 덮는 등 상호 관통이 있으면
어긋난다. z 버퍼가 필요해지면 그때.`
"""
import argparse
import os
import sys

import cv2
import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import win as W

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "시트")


def faces_with_color(scene):
    """씬 -> (정점, 면, 면색, 면이 속한 재질번호). 색은 UV 중심에서 텍스처를 한 번 찍는다."""
    Vs, Fs, Cs, Ms = [], [], [], []
    off = 0
    for mi, (name, g) in enumerate(scene.geometry.items()):
        V = np.asarray(g.vertices, np.float64)
        F = np.asarray(g.faces, np.int64)
        if len(F) == 0:
            continue
        col = np.full((len(F), 3), 200, np.uint8)
        vis = g.visual
        img = getattr(getattr(vis, "material", None), "baseColorTexture", None)
        uv = getattr(vis, "uv", None)
        if img is not None and uv is not None and len(uv) == len(V):
            tex = np.asarray(img.convert("RGB"))
            h, w = tex.shape[:2]
            c = np.asarray(uv)[F].mean(1)                       # 면의 UV 중심
            px = np.clip((c[:, 0] * (w - 1)).astype(int), 0, w - 1)
            py = np.clip(((1 - c[:, 1]) * (h - 1)).astype(int), 0, h - 1)
            col = tex[py, px]
        else:
            bc = getattr(getattr(vis, "material", None), "baseColorFactor", None)
            if bc is not None:
                col = np.tile(np.asarray(bc, np.uint8)[:3], (len(F), 1))
        Vs.append(V); Fs.append(F + off); Cs.append(col)
        Ms.append(np.full(len(F), mi, np.int32))
        off += len(V)
    return (np.concatenate(Vs), np.concatenate(Fs),
            np.concatenate(Cs).astype(np.uint8), np.concatenate(Ms))


def edges2(Vw, F, depth, u, ident, mat, crease_deg=30.0, jump=0.012):
    """`--선 2` 의 선 자리 (굵히기 전). 화가가 긋는 선 — 가림선 · 겹선 · 재질 경계.

    **가림선**은 화소마다 그 삼각형 평면에서 보간한 깊이로 잰다. 옛 규칙은 삼각형 **평균** 깊이 차라
    기울어진 큰 삼각형 두 장이 만나는 대각선에 가짜 선이 났다 (research_각진깊이 ⓪).
    이웃 화소의 두 면 평면을 **경계 중점에서** 비교하므로 붙어 있는 면끼리는 차가 0 이다.
    **겹선**은 두 면 법선 사이 각. |cos| 로 재서 뒤집힌 법선은 같은 면으로 본다."""
    z = Vw[:, 2]
    T = np.stack([u, z, depth], 1)[F]
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    flat = np.abs(n[:, 2]) < 0.05 * np.linalg.norm(n, axis=1) + 1e-12     # 시선과 거의 나란한 면은 평균 깊이
    nd = np.where(flat, 1.0, n[:, 2])
    A, B = np.where(flat, 0, -n[:, 0] / nd), np.where(flat, 0, -n[:, 1] / nd)
    C = np.where(flat, T[:, :, 2].mean(1), T[:, 0, 2] - A * T[:, 0, 0] - B * T[:, 0, 1])
    N3 = np.cross(Vw[F[:, 1]] - Vw[F[:, 0]], Vw[F[:, 2]] - Vw[F[:, 0]])
    N3 /= np.linalg.norm(N3, axis=1, keepdims=True) + 1e-12
    gy, gx = np.mgrid[0:W.RES, 0:W.RES]
    pu, pz = (W.U1 - W.U0) / W.RES, (W.Z1 - W.Z0) / W.RES
    U, Z = W.U0 + (gx + 0.5) * pu, W.Z1 - (gy + 0.5) * pz
    hit, i = ident >= 0, np.clip(ident, 0, None)
    edge = np.zeros(hit.shape, bool)
    cmax = np.cos(np.radians(crease_deg))
    for sa, sb, mu, mz in ((np.s_[:, :-1], np.s_[:, 1:], U[:, :-1] + pu / 2, Z[:, :-1]),
                           (np.s_[:-1, :], np.s_[1:, :], U[:-1, :], Z[:-1, :] - pz / 2)):
        ia, ib = i[sa], i[sb]
        occ = np.abs((A[ia] - A[ib]) * mu + (B[ia] - B[ib]) * mz + C[ia] - C[ib]) > jump
        crease = np.abs((N3[ia] * N3[ib]).sum(-1)) < cmax
        e = hit[sa] & hit[sb] & (ia != ib) & (occ | crease | (mat[ia] != mat[ib]))
        edge[sa] |= e
        edge[sb] |= e
    return edge


def draw(Vw, F, col, mat, view, line=True, style=1):
    """한 시점을 칠한다. 화가 알고리즘 + 재질·깊이 경계에 검은 선.

    `style=2` (`--선 2`, 2026-09-14 게이트 A): 선 자리는 `edges2`, 굵기 6px (512 로 줄여 median5 를 버틴다),
    면색은 120 + c·135/255 로 올린다 (선 20 과 art3d 문턱 105 사이에 틈). 알파는 같다."""
    a, sign = W.VIEW_AXIS[view]
    depth = Vw[:, 1 - a] * (-sign if view != "side" else 1)      # 카메라에서 먼 쪽이 큰 값
    py, px = W.topix(sign * Vw[:, a], Vw[:, 2])
    P = np.stack([px, py], 1).astype(np.int32)[F]
    order = np.argsort(depth[F].max(1))[::-1]                   # 먼 것부터
    if style == 2:
        col = (120 + col.astype(np.float32) * 135 / 255).astype(np.uint8)
    rgb = np.full((W.RES, W.RES, 3), 255, np.uint8)
    ident = np.full((W.RES, W.RES), -1, np.int32)
    for i in order:
        cv2.fillConvexPoly(rgb, P[i], [int(v) for v in col[i]])
        cv2.fillConvexPoly(ident, P[i], int(i))
    if not line:
        return rgb, ident
    hit = ident >= 0
    if style == 2:
        edge = edges2(Vw, F, depth, sign * Vw[:, a], ident, mat)
        edge |= hit & ~cv2.erode(hit.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        rgb[cv2.dilate(edge.astype(np.uint8), np.ones((6, 6), np.uint8)).astype(bool)] = (20, 20, 20)
        return rgb, ident
    zz = np.where(hit, depth[F].mean(1)[np.clip(ident, 0, None)], np.nan)
    mm = np.where(hit, mat[np.clip(ident, 0, None)], -1)
    edge = np.zeros((W.RES, W.RES), bool)
    for dy, dx in ((0, 1), (1, 0)):
        s_m = np.roll(mm, dy or dx, 0 if dy else 1) != mm
        s_z = np.abs(np.nan_to_num(np.roll(zz, dy or dx, 0 if dy else 1) - zz)) > 0.012
        edge |= (s_m | s_z) & hit
    edge |= hit & ~cv2.erode(hit.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    rgb[cv2.dilate(edge.astype(np.uint8), np.ones((2, 2), np.uint8)).astype(bool)] = (20, 20, 20)
    return rgb, ident


def coverage(Vw, F, view, ss=4):
    """실루엣을 **ss 배로 그려 줄인다** — 가장자리 화소에 「몇 % 덮였나」(0~1) 가 남는다.

    화소보다 촘촘한 윤곽이다 (2026-09-11 해상도 트랙). 0/1 마스크는 윤곽을 화소 단위로 계단지게 해서
    hull 에 가로 결을 남긴다. 손그림 원화라면 선의 안티앨리어싱 회색값이 같은 정보를 준다.
    삼각형은 하나씩 채운다 — `fillPoly` 로 한꺼번에 채우면 겹친 데가 짝홀 규칙으로 지워진다.
    화소 p 는 연속 좌표 [p, p+1) 이다 (`W.topix` 와 같은 규약) — 그래서 중심 맞춤으로 0.5 를 뺀다."""
    a, sign = W.VIEW_AXIS[view]
    R = W.RES * ss
    px = (sign * Vw[:, a] - W.U0) / (W.U1 - W.U0) * R - 0.5
    py = (W.Z1 - Vw[:, 2]) / (W.Z1 - W.Z0) * R - 0.5
    P = np.round(np.stack([px, py], 1) * 16).astype(np.int32)[F]          # shift=4 -> 1/16 화소
    hit = np.zeros((R, R), np.uint8)
    for tri in P:
        cv2.fillConvexPoly(hit, tri, 1, shift=4)
    return cv2.resize(hit.astype(np.float32), (W.RES, W.RES), interpolation=cv2.INTER_AREA)


def selfcheck():
    """`--선 2` 합성 assert — 기운 상자 · 검은 상자 · 계단. 옛 규칙이 기운 상자에서 가짜 선을 내는 것도 본다."""
    import trimesh.transformations as TT

    def run(mesh, c=200, style=2):
        V = W.normalize(np.asarray(mesh.vertices, np.float64))
        F = np.asarray(mesh.faces, np.int64)
        col = np.full((len(F), 3), c, np.uint8)
        rgb, ident = draw(V, F, col, np.zeros(len(F), np.int32), "front", style=style)
        py, px = W.topix(V[:, 0], V[:, 2])
        inner = cv2.erode((ident >= 0).astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
        return rgb, ident, px, py, inner

    # 1 30° 돌린 상자 — 앞에서 두 면이 보인다. 안쪽 선은 세로 모서리 열에만 (면 대각선엔 없다)
    box = trimesh.creation.box((0.6, 0.6, 1.0))
    box.apply_transform(TT.rotation_matrix(np.radians(30), [0, 0, 1]))
    rgb, ident, px, _, inner = run(box)
    cols = np.unique(px)
    mid = cols[(cols > cols.min() + 8) & (cols < cols.max() - 8)]            # 윤곽 아닌 세로 모서리 열
    ys, xs = np.nonzero((rgb[:, :, 0] == 20) & inner)
    near = np.abs(xs[:, None] - mid[None, :]).min(1) <= 4
    assert len(xs) > 100 and near.all(), "기운 상자: 모서리 밖 선 %d / %d" % ((~near).sum(), len(xs))
    rgb1, _, _, _, _ = run(box, style=1)
    ys1, xs1 = np.nonzero((rgb1[:, :, 0] == 20) & inner)
    fake = (np.abs(xs1[:, None] - mid[None, :]).min(1) > 4).sum()
    assert fake > 100, "옛 규칙에서 대각선 가짜 선이 안 났다 (%d) — 이 검사가 무엇도 못 가른다" % fake
    # 2 검은 상자 — 면은 lum ≥ 120, 선은 20
    rgb, ident, _, _, inner = run(trimesh.creation.box((0.6, 0.4, 1.0)), c=0)
    face = inner & (rgb[:, :, 0] != 20)
    assert face.any() and rgb[face].mean(1).min() >= 119 and (rgb[:, :, 0] == 20).any(), "검은 상자 대비"
    # 3 계단 — 몸통 앞뒤로 튀어나온 혹 (카메라가 어느 쪽이든 하나는 앞에 있다). 혹 윤곽에 가림선
    big = trimesh.creation.box((0.6, 0.4, 1.0))
    bumps = [trimesh.creation.box((0.2, 0.2, 0.3)) for _ in range(2)]
    bumps[0].apply_translation([0, -0.30, 0])
    bumps[1].apply_translation([0, 0.30, 0])
    rgb, ident, px, py, _ = run(trimesh.util.concatenate([big] + bumps))
    nb = len(big.vertices)
    r = int(np.median(py[nb:]))
    c0 = int(px[nb:].min())
    assert (rgb[r, c0 - 4:c0 + 5, 0] == 20).any() and not (rgb[r, c0 + 20:c0 + 30, 0] == 20).any(), \
        "계단: 혹 윤곽에 가림선이 없거나 혹 앞면에 선이 났다"
    print("  자가검사 통과 — 기운 상자(옛 규칙 가짜 선 %d 화소 → 0) · 검은 상자 · 계단" % fake)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "검사":
        selfcheck()
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--이름", dest="name", default=None)
    ap.add_argument("--축", dest="axes", default="xyz",
                    help="만든 도구의 축 규약 (가로,위,깊이). glTF/VRM 은 xyz(y 위), "
                         "블렌더/OpenSCAD 는 xzy, TripoSR 은 yxz(x 위). win.to_world 참고")
    ap.add_argument("--선", dest="style", type=int, default=1,
                    help="2 = 보간 가림선 · 겹선 30° · 6px · 면색 올림 (draw 참고). 기본 1 은 옛 규칙")
    ap.add_argument("--안뒤집기", dest="no_flip", action="store_true",
                    help="모델이 이미 −y 를 본다 (무진.py). VRM 이면 주지 않는다")
    ap.add_argument("--초정밀", dest="ss", action="store_true",
                    help="알파를 4배로 그려 줄인다 — 가장자리에 덮인 비율 (해상도 트랙, `coverage`)")
    a = ap.parse_args()
    name = a.name or os.path.splitext(os.path.basename(a.model))[0]
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)

    src = a.model
    if src.lower().endswith(".vrm"):                            # VRM 0.x 는 glb 컨테이너다
        src = os.path.join(d, "_model.glb")
        import shutil; shutil.copyfile(a.model, src)
    scene = trimesh.load(src)
    V, F, col, mat = faces_with_color(scene)
    print("  면 %d · 재질 %d" % (len(F), mat.max() + 1))

    # **창 규약 그대로.** 높이로 한 번 재고 세 시점이 그 배율을 공유한다 (win.normalize)
    Vw = W.to_world(V, a.axes)
    # VRM/glTF 캐릭터는 **+z 를 본다.** 창 규약은 「앞이 −y」라 깊이를 뒤집어야
    # front 카메라가 얼굴을 본다. 안 뒤집으면 front 에 뒤통수가 나온다 (실측).
    # 다만 무진.py 처럼 **처음부터 −y 를 보게 세운 모델**은 여기서 뒤집으면 반대로
    # front 에 뒤통수가 나온다 — 2026-09-11 에 무진1997 시트가 그렇게 나와 있었다.
    if not a.no_flip:
        Vw[:, 1] *= -1
    Vw = W.normalize(Vw)
    trimesh.Trimesh(Vw, F, process=False).export(os.path.join(d, "truth.glb"))

    for v in W.VIEWS:
        rgb, ident = draw(Vw, F, col, mat, v, style=a.style)
        # **정확한 실루엣을 알파로 같이 적는다** (2026-09-11). 흰 바탕에 색만 적으면 모델의 흰 부분
        # (흰 가슴판·셔츠)이 `win.art_mask` 에서 배경으로 빠져 hull 에 터널이 뚫렸다 (29장 중 9장 > 1%).
        # 윤곽선 굵히기가 바깥으로 번진 1 화소(측정한 「테」)도 알파 0 이라 마스크에 안 든다.
        al = (np.round(coverage(Vw, F, v) * 255).astype(np.uint8) if a.ss      # 가장자리에 덮인 비율
              else np.where(ident >= 0, 255, 0).astype(np.uint8))
        bgra = np.dstack([cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), al])
        cv2.imencode(".png", bgra)[1].tofile(os.path.join(d, "%s.png" % v))
        print("  %-6s 전경 %.1f%% -> %s.png" % (v, 100 * (ident >= 0).mean(), v))
    print("  정답 메시 -> %s/truth.glb" % d)


if __name__ == "__main__":
    main()
