# -*- coding: utf-8 -*-
"""여러 각도 원화 → 장마다 접힌 판 3D (10-02 사용자 「3d 까지 부탁해」).
입력: 각도데이터.py 의 장별 라벨(먹선 칸) · 그림자 · 배율. 정면 접힌판2 와 같은 틀을 이름 없이 모든 장에 똑같이 쓴다(정면도 다시 — 비교되게):
  바탕 깊이 h = 윤곽 부풀림(구: √(2Rd − d²), d = 윤곽까지 거리)  ← 부조_Z(이름 · 색 규칙) 대신. 생성 AI 없음
  빛 L = 원화 밝기 ~ 부풀림 법선 최소제곱(장마다 따로 · 셀 그림자 방향을 그림에서 읽음)
  면 = 칸 ∩ (그림자 / 밝음) 연결 조각 · 면마다 평면 하나: 부풀림 평균 법선을 L 쪽으로 돌려 n·L = 그 면 밝기 순위(0.1~0.95)
  적분 = 같은 면 이웃은 면 기울기(무게 1) · 다른 면 이웃은 바탕 차(무게 0.3 · 단 허용) · 전체 바탕 쪽 0.02
좌표: 화면 x 오른 · y 아래 · z 보는 쪽. 출력 out/오메가몬2/지표/각도데이터/판_<n>.ply · 판.json · 판_시트.png(앞면 높이장 · 정면 · 40° · 80°)"""
import os, json, numpy as np, cv2, trimesh, scipy.sparse as sp
from scipy.sparse.linalg import lsqr
from scipy import ndimage
R = r"G:\art2real\원화3d\out"; O = os.path.join(R, "오메가몬2", "지표", "각도데이터"); D = os.path.join(R, "번역", "디지몬")
장 = json.load(open(os.path.join(O, "각도데이터.json"), encoding="utf-8")); 결과 = {}
S2 = 2   # 반 해상도로 풂(머리 높이 300 px)
for 이름, info in 장.items():
    n_ = 이름.split()[0]; z = np.load(os.path.join(O, n_ + ".npz")); s = float(z["s"])
    im = cv2.imdecode(np.fromfile(os.path.join(D, info["파일"]), np.uint8), 1); big = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    lab_, sh_ = z["라벨"], z["그림자"]; ys, xs = np.nonzero(lab_ > 0); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    lab = lab_[y0:y1:S2, x0:x1:S2]; sh = sh_[y0:y1:S2, x0:x1:S2]; img = big[y0:y1:S2, x0:x1:S2]; m = lab > 0; H, W = m.shape
    Lum = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[:, :, 0].astype(float); ink = cv2.morphologyEx(Lum.astype(np.uint8), cv2.MORPH_BLACKHAT, np.ones((5, 5), np.uint8)) > 28
    # 바탕: 부풀림
    d = ndimage.distance_transform_edt(m); Rm = d.max(); h = np.sqrt(np.clip(2 * Rm * d - d * d, 0, None)); h[~m] = 0
    hy, hx = np.gradient(ndimage.gaussian_filter(h, 2)); N0 = np.dstack([-hx, -hy, np.ones_like(h)]); N0 /= np.linalg.norm(N0, axis=2, keepdims=True)
    # 빛: 밝기 ~ a + n·L
    use = m & ~ink & (d > 2); A = np.c_[N0[use], np.ones(use.sum())]; c = np.linalg.lstsq(A, Lum[use], rcond=None)[0]; L = c[:3] / max(1e-6, np.linalg.norm(c[:3]))
    if L[2] < 0.2: L[2] = 0.2; L /= np.linalg.norm(L)
    # 면
    FACE = np.full((H, W), -1); 법선 = []; lo, hi = np.percentile(Lum[m & ~ink], [5, 95])
    for i in range(1, lab.max() + 1):
        for part in ((lab == i) & sh, (lab == i) & ~sh):
            nl, cc = cv2.connectedComponents(part.astype(np.uint8))
            for j in range(1, nl):
                q = cc == j
                if q.sum() < 6: continue
                n0 = N0[q].mean(0); n0 /= np.linalg.norm(n0); qq = q & ~ink
                t = 0.1 + 0.85 * np.clip(((Lum[qq].mean() if qq.any() else Lum[q].mean()) - lo) / max(1, hi - lo), 0, 1)
                best = n0
                for a in np.linspace(-3, 3, 241)[np.argsort(np.abs(np.linspace(-3, 3, 241)))]:   # 작게 돌리는 것부터
                    v = n0 + a * L; v /= np.linalg.norm(v)
                    if v[2] > 0.15 and abs(v @ L - t) < 0.03: best = v; break
                FACE[q] = len(법선); 법선.append(best)
    hole = m & (FACE < 0)
    if hole.any() and (FACE >= 0).any():
        _, (iy, ix) = ndimage.distance_transform_edt(FACE < 0, return_indices=True); FACE[hole] = FACE[iy[hole], ix[hole]]
    Nf = np.array(법선); nb = np.zeros((H, W, 3)); nb[m] = Nf[FACE[m]]; nz = np.maximum(nb[..., 2], 0.15); p_ = -nb[..., 0] / nz; q_ = -nb[..., 1] / nz
    # 적분
    idx = -np.ones((H, W), int); idx[m] = np.arange(m.sum()); n = int(m.sum()); R_, C_, V_, B_ = [], [], [], []
    for dy, dx in ((0, 1), (1, 0)):
        a_ = m[:H - dy, :W - dx] & m[dy:, dx:]; yy, xx = np.nonzero(a_); ia, ib = idx[yy, xx], idx[yy + dy, xx + dx]
        same = FACE[yy, xx] == FACE[yy + dy, xx + dx]; g = (p_[yy, xx] + p_[yy + dy, xx + dx]) / 2 if dx else (q_[yy, xx] + q_[yy + dy, xx + dx]) / 2
        tgt = np.where(same, g, h[yy + dy, xx + dx] - h[yy, xx]); w = np.where(same, 1.0, 0.3); r0 = len(B_); r = np.arange(r0, r0 + len(ia))
        R_ += list(r) + list(r); C_ += list(ib) + list(ia); V_ += list(w) + list(-w); B_ += list(w * tgt)
    r0 = len(B_); R_ += list(range(r0, r0 + n)); C_ += list(range(n)); V_ += [0.02] * n; B_ += list(0.02 * h[m])
    sol = lsqr(sp.csr_matrix((V_, (R_, C_)), shape=(len(B_), n)), np.array(B_), atol=1e-8, btol=1e-8, iter_lim=20000)[0]
    Z = np.full((H, W), np.nan); Z[m] = sol
    np.savez_compressed(os.path.join(O, f"판_{n_}_Z.npz"), Z=Z, m=m)   # 합치기(장합치기.py)용
    # 높이장 → 메시(앞면만 · 뒤판은 옆벽 없이 떠 보여 뺐다)
    py, px = np.nonzero(m); vid = -np.ones((H, W), int); vid[py, px] = np.arange(len(py)); k = 100.0 / H   # 머리 높이 = 100
    zb = np.nanmin(Z) - 0.08 * H; Vf = np.c_[px * k, -(Z[py, px]) * k, -py * k]; Vb = np.c_[px * k, np.full(len(py), -zb * k), -py * k]
    F = []
    for (a, b, c_, d_) in ((vid[:-1, :-1], vid[:-1, 1:], vid[1:, :-1], vid[1:, 1:]),):
        ok = (a >= 0) & (b >= 0) & (c_ >= 0) & (d_ >= 0); F = np.r_[np.c_[a[ok], c_[ok], b[ok]], np.c_[b[ok], c_[ok], d_[ok]]]
    nv = len(Vf); Fb = F[:, ::-1] + nv
    front = trimesh.Trimesh(Vf, F, process=False)
    col = (255 * (img[py, px][:, ::-1] / 255.0) ** 0.7).astype(np.uint8); front.visual.vertex_colors = np.c_[col, np.full(nv, 255)].astype(np.uint8)
    front.export(os.path.join(O, f"판_{n_}.ply"))
    hm = np.zeros((H, W, 3), np.uint8); a = (Z - np.nanpercentile(Z, 2)) / max(1e-6, np.nanpercentile(Z, 98) - np.nanpercentile(Z, 2)); hm[m] = cv2.applyColorMap((np.clip(a[m], 0, 1) * 255).astype(np.uint8).reshape(-1, 1), cv2.COLORMAP_JET).reshape(-1, 3)
    cv2.imencode(".png", hm)[1].tofile(os.path.join(O, f"판_{n_}_깊이.png")); cv2.imencode(".png", img)[1].tofile(os.path.join(O, f"판_{n_}_원화.png"))
    결과[이름] = {"면": len(법선), "빛(x오른,y아래,z앞)": [round(float(v), 2) for v in L], "깊이/높이": round(float((np.nanmax(Z) - np.nanmin(Z)) / H), 2)}; print(이름, 결과[이름])
json.dump(결과, open(os.path.join(O, "판.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
