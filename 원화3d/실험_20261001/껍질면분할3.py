# -*- coding: utf-8 -*-
"""껍질 면분할 3 판 — 넓은 창 꺾임 검출 (10-02 사용자 「면분할 제대로 해 봐」).
1 판(이웃 삼각형 각 ≥ 10°): 둥글게 퍼진 꺾임(칸 사이 17~31° 가 몇 화소에 퍼짐)을 못 찾아 뭉침.
2 판(영역 평균 법선과 14°): 둥근 투구를 띠로 썰고 정면이 나빠짐.
3 판: 껍질은 화소 높이장 → 면 방향 지도에서 잰다.
  꺾임 세기(화소 p) = 네 방향 d 중 최대 ∠(n(p − r·d), n(p + r·d))  — 창 r 화소 건너 양쪽 법선 각(법선은 가우스 σ 로 다듬음)
     고르게 휘는 곡면: 창 안 각 ≈ 2r/R(돔이면 수 °) → 안 자름 · 둥글게 퍼진 꺾임: 창이 꺾임을 다 덮어 제 각(17~31°) → 자름
  꺾임 선 = 세기 ≥ τ 이고 그 방향으로 이웃보다 큼(비최대 억제 · 캐니처럼 한 줄로) → 선을 1 화소 이어 붙여 닫음
  면 = S 를 지형으로 워터셰드(선만 쓰면 끊긴 틈으로 새서 한 덩어리) → 경계 S 중앙값 < τ 인 이웃 합침 · 작은 조각(머리 넓이 × 0.004 미만)은 가장 길게 맞닿은 이웃에.
먹선은 쓰지 않는다(3D 만 · 2 판 B 는 채점 반칙). 잰다: 먹선 칸과 겹침(정답 아님) + 눈.
출력 out/오메가몬2/지표/각도데이터/면3_<n>.ply · 면3_<n>_꺾임.png · 면분할3.json"""
import os, sys, json, numpy as np, cv2, trimesh
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 껍질면분할2 import 저장
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "오메가몬", "지표")); from 면분할 import 채점
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"
R_, SIG, TAU, 작은비 = 4, 1.5, 2.5, 0.004   # τ 는 「도/화소」(화소당 법선 방향 변화) — σ1.5 · τ2.5 가 시험 격자(σ 1.5/2 × τ 1.5/2.5/4)에서 옆 · 3/4 · tri 가장 나음

def 세기(Z, m, sig=SIG):
    """화소당 법선 방향 변화(도/화소) — 법선을 꺾임 폭만큼(σ) 다듬은 뒤 네 방향 최대. 창 r 화소 건너 재면(꺾임()) 고원이 생겨 경계 자리가 흔들렸다."""
    Zf = np.where(m, Z, np.nanmean(Z[m])); Zs = ndimage.gaussian_filter(Zf, sig); gy, gx = np.gradient(Zs); N = np.dstack([-gx, -gy, np.ones_like(gx)]); N /= np.linalg.norm(N, axis=2, keepdims=True)
    S = np.zeros(m.shape)
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        a = np.roll(np.roll(N, dy, 0), dx, 1); b = np.roll(np.roll(N, -dy, 0), -dx, 1); S = np.maximum(S, np.degrees(np.arccos(np.clip((a * b).sum(2), -1, 1))) / np.hypot(dy, dx) / 2)
    S[~cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)] = S.max(); return S

def 꺾임(Z, m, r=R_, sig=SIG, tau=15.0):
    Zf = np.where(m, Z, np.nanmean(Z[m])); Zs = ndimage.gaussian_filter(Zf, sig); gy, gx = np.gradient(Zs)
    N = np.dstack([-gx, -gy, np.ones_like(gx)]); N /= np.linalg.norm(N, axis=2, keepdims=True); H, W = m.shape
    dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]; S = np.zeros((H, W)); best = np.zeros((H, W), int)
    def sh(a, dy, dx):   # a 를 (dy, dx) 만큼 민 것(가장자리는 그대로)
        return np.roll(np.roll(a, dy, 0), dx, 1)
    for i, (dy, dx) in enumerate(dirs):
        a = sh(N, r * dy, r * dx); b = sh(N, -r * dy, -r * dx); ang = np.degrees(np.arccos(np.clip((a * b).sum(2), -1, 1)))
        ok = sh(m, r * dy, r * dx) & sh(m, -r * dy, -r * dx) & m; ang[~ok] = 0; up = ang > S; S[up] = ang[up]; best[up] = i
    nms = np.zeros_like(m)
    for i, (dy, dx) in enumerate(dirs):   # 그 방향으로 이웃보다 크면 남김
        q = best == i; nms |= q & (S >= sh(S, dy, dx)) & (S >= sh(S, -dy, -dx))
    선 = nms & (S >= tau) & m
    선 = cv2.dilate(선.astype(np.uint8), np.ones((2, 2), np.uint8)) > 0                     # 한 화소 틈 닫기
    return 선, S

def 면들(m, 선, S=None, 작은비=작은비, tau=TAU, 씨앗=6.0):
    # 선만으로 나누면 끊긴 틈으로 새서 한 덩어리(3/4: 93 %) → 꺾임 세기 S 를 지형으로 워터셰드(틈이 저절로 닫힘)
    # 씨앗 = 꺾임 약한 곳(S < 6°)을 2 화소 깎은 성분 · 그다음 경계 따라 잰 S 중앙값 < τ 인 이웃은 합침(진짜 꺾임이 아닌 경계)
    from skimage.segmentation import watershed
    seed = cv2.erode(((S < 씨앗) & m).astype(np.uint8), np.ones((5, 5), np.uint8)); _, mk = cv2.connectedComponents(seed, connectivity=4)
    lab = watershed(S, mk, mask=m); n = lab.max() + 1; tot = m.sum()
    par = np.arange(n)
    def f(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for _ in range(3):
        a = lab[:, :-1]; b = lab[:, 1:]; c = lab[:-1, :]; d = lab[1:, :]
        A = np.r_[a.ravel(), c.ravel()]; B = np.r_[b.ravel(), d.ravel()]; V = np.r_[np.maximum(S[:, :-1], S[:, 1:]).ravel(), np.maximum(S[:-1, :], S[1:, :]).ravel()]
        q = (A != B) & (A > 0) & (B > 0); A, B, V = np.minimum(A[q], B[q]), np.maximum(A[q], B[q]), V[q]
        key = A.astype(np.int64) * n + B; o = np.argsort(key); key, V = key[o], V[o]; uk, st = np.unique(key, return_index=True); med = [np.median(v) for v in np.split(V, st[1:])]
        for k_, md in zip(uk, med):
            if md < tau: ra, rb = f(int(k_ // n)), f(int(k_ % n)); par[max(ra, rb)] = min(ra, rb)
        lab = np.array([f(i) for i in range(n)])[lab]
    n = lab.max() + 1
    for _ in range(8):
        area = np.bincount(lab.ravel(), minlength=n); small = [i for i in range(1, n) if 0 < area[i] < 작은비 * tot]
        if not small: break
        for i in small:
            q = lab == i; ring = cv2.dilate(q.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & ~q & m; nb = lab[ring]; nb = nb[(nb > 0) & (nb != i)]
            if len(nb): lab[q] = np.bincount(nb).argmax()
    _, idx = ndimage.distance_transform_edt(lab == 0, return_indices=True); lab = np.where(m, lab[idx[0], idx[1]], 0)   # 선 화소 → 가장 가까운 면
    _, lab2 = np.unique(lab, return_inverse=True); return lab2.reshape(lab.shape)

if __name__ == "__main__":
    결과 = {}
    for n in "123456":
        zz = np.load(os.path.join(O, f"판_{n}_Z.npz")); Z, m = zz["Z"], zz["m"]; S = 세기(Z, m); 선 = S >= TAU; lab = 면들(m, 선, S, tau=TAU, 씨앗=0.4 * TAU)
        mesh = trimesh.load(os.path.join(O, f"판_{n}.ply"), process=False); py, px = np.nonzero(m); flab = lab[py, px][mesh.faces[:, 0]]
        _, flab = np.unique(flab, return_inverse=True); 저장(mesh, flab, os.path.join(O, f"면3_{n}.ply"))
        z = np.load(os.path.join(O, f"{n}.npz")); L = z["라벨"]; ys, xs = np.nonzero(L > 0); y0, x0 = ys.min(), xs.min()
        칸 = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)]; s = 채점(flab, 칸[mesh.faces[:, 0]], mesh.area_faces)
        v = cv2.applyColorMap(np.clip(S / 10 * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO); v[~m] = 40; v[선] = (255, 255, 255)
        cv2.imencode(".png", v)[1].tofile(os.path.join(O, f"면3_{n}_꺾임.png"))
        결과[n] = {"먹선 칸": int(L.max()), "면": int(flab.max() + 1), "칸과 겹침": s["평균IoU"], "쪼갬": s["쪼갬"], "뭉침": s["뭉침"]}; print(n, 결과[n])
    json.dump({"창 r": R_, "σ": SIG, "τ": TAU, "장": 결과}, open(os.path.join(O, "면분할3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
