# -*- coding: utf-8 -*-
"""겹깊이시험 2 — 먹선 강조 · 그림자 (10-02 사용자 「먹선을 강조하고 그림자를 더 넣으면 정보를 찾을 것 같은데?」).
같은 광선 · 같은 정답(겹깊이시험.py 찍기의 _정답.npz)에서 그림만 바꾼다:
  A 음영 + 굵은 먹선(7 px · 원화식: 부품 경계 · 깊이 끊김 · 35° 꺾임)  B A + 드리운 그림자(왼 위 앞 빛 · 그림자 광선)  C B + 틈새 그늘(화면 공간 AO · 정답 깊이에서)
출력 <모델>_{A,B,C}.png → 겹깊이시험_DAv2.py → 채점은 겹깊이시험.py 와 같은 띄움 함수."""
import os, sys, glob, json, numpy as np, trimesh, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import 겹깊이시험 as T
O = T.O; N = T.N
def 그리기():
    for 이름, (fs, d) in T.모델.items():
        parts = [trimesh.load(f, force="mesh") for f in fs]; m = trimesh.util.concatenate(parts); owner = np.repeat(np.arange(len(parts)), [len(p.faces) for p in parts])
        d = np.array(d, float); up = np.array([0, 0, 1.0]); right = np.cross(d, up); c = m.bounds.mean(0); P = m.vertices - c; ext = max(np.ptp(P @ right), np.ptp(P @ up)) * 1.08
        g = (np.arange(N) + 0.5) / N * ext - ext / 2; GX, GY = np.meshgrid(g, -g)
        o = c + GX.reshape(-1, 1) * right + GY.reshape(-1, 1) * up - d * (np.ptp(P @ d) + 10)
        loc, ray, tri = m.ray.intersects_location(o, np.repeat(d[None], len(o), 0), multiple_hits=False)
        dep = np.full(N * N, np.nan); dep[ray] = (loc - o[ray]) @ d; part = np.full(N * N, -1); part[ray] = owner[tri]
        nr = m.face_normals[tri]; nr = np.where(((nr @ d) > 0)[:, None], -nr, nr)          # 카메라 쪽으로
        Ld = -d * 0.55 + up * 0.6 - right * 0.45; Ld /= np.linalg.norm(Ld)
        lam_ = np.clip(nr @ Ld, 0, 1); lam = np.zeros(N * N); lam[ray] = lam_
        eps = ext * 2e-3; so = loc + nr * eps; sh = np.zeros(len(so), bool)
        for i0 in range(0, len(so), 3000): sh[i0:i0 + 3000] = m.ray.intersects_any(so[i0:i0 + 3000], np.repeat(Ld[None], len(so[i0:i0 + 3000]), 0))   # 나눠 쏨(한 번에 7.7 GB)
        shadow = np.zeros(N * N, bool); shadow[ray] = sh
        dep = dep.reshape(N, N); part = part.reshape(N, N); lam = lam.reshape(N, N); shadow = shadow.reshape(N, N); hit = part >= 0
        nrm = np.zeros((N * N, 3)); nrm[ray] = nr; nrm = nrm.reshape(N, N, 3)
        edge = np.zeros((N, N), bool); edge[:, 1:] |= part[:, 1:] != part[:, :-1]; edge[1:, :] |= part[1:, :] != part[:-1, :]
        dz = np.nan_to_num(dep, nan=1e9); px = ext / N
        edge[:, 1:] |= np.abs(dz[:, 1:] - dz[:, :-1]) > 3 * px; edge[1:, :] |= np.abs(dz[1:, :] - dz[:-1, :]) > 3 * px
        edge[:, 1:] |= (nrm[:, 1:] * nrm[:, :-1]).sum(-1) < np.cos(np.radians(35)); edge[1:, :] |= (nrm[1:, :] * nrm[:-1, :]).sum(-1) < np.cos(np.radians(35))
        edge = cv2.dilate(edge.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
        # 틈새 그늘: 둘레 8 방향 · 반지름 6 · 14 px 에서 나보다 앞(가까운) 이웃이 많을수록 어둡게
        dd = np.where(hit, dep, np.nan); ao = np.zeros((N, N)); cnt = 0
        for r in (6, 14):
            for ang in np.linspace(0, 2 * np.pi, 8, endpoint=False):
                sx, sy = int(round(np.cos(ang) * r)), int(round(np.sin(ang) * r)); nb = np.roll(np.roll(dd, sy, 0), sx, 1)
                ao += np.clip((dd - nb) / (r * px * 1.5), 0, 1); cnt += 1
        ao = np.nan_to_num(ao / cnt)
        base = 70 + 175 * lam
        A = base.copy(); B = np.where(shadow, base * 0.45, base); C = B * (1 - 0.6 * ao)
        for k, im in (("A", A), ("B", B), ("C", C)):
            im = np.where(hit, im, 255); im[edge & cv2.dilate(hit.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)] = 15
            cv2.imencode(".png", cv2.cvtColor(np.clip(im, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR))[1].tofile(os.path.join(O, f"{이름}_{k}_강조.png"))
        print(이름, "그림자 화소", int((shadow & hit).sum()), "/", int(hit.sum()))
def 채점():
    점수 = {}
    for 이름 in T.모델:
        if not os.path.exists(os.path.join(O, f"{이름}_C_강조_da3.npy")): continue   # 일부만(사용자: 모든 부분을 볼 필요 없다)
        z = np.load(os.path.join(O, f"{이름}_정답.npz")); gt = z["깊이"]; part = z["부품"]; G_ = T.띄움(gt, part); keys = [k for k, v in G_.items() if abs(v) > 0.05]
        점수[이름] = {"쌍": len(keys)}
        for k in ("A", "B", "C"):
            im = cv2.imdecode(np.fromfile(os.path.join(O, f"{이름}_{k}_강조.png"), np.uint8), cv2.IMREAD_GRAYSCALE).astype(float)
            for 이름2, D in (("밝기대조", 255 - cv2.GaussianBlur(im, (0, 0), 3)), ("DA", cv2.resize(np.load(os.path.join(O, f"{이름}_{k}_강조_da3.npy")), (N, N)))):
                P_ = T.띄움(D, part); ks = [q for q in keys if q in P_]; g = np.array([G_[q] for q in ks]); p = np.array([P_[q] for q in ks])
                from scipy.stats import spearmanr
                점수[이름][f"{k}_{이름2}"] = {"앞뒤맞힘": round(float(np.mean(np.sign(g) == np.sign(p))), 2), "띄움순위상관": round(float(spearmanr(g, p).correlation), 2)}
    json.dump(점수, open(os.path.join(O, "점수_강조.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in 점수.items(): print(k, v)
if __name__ == "__main__":
    {"그리기": 그리기, "채점": 채점}[sys.argv[1]]()
