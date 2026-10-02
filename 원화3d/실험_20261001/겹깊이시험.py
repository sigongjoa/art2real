# -*- coding: utf-8 -*-
"""겹 부피를 깊이 지도로 읽을 수 있나 — 시험만 (10-02 사용자 「heatmap 의 depth 정보로 유추 가능하지 않어? · 테스트만 해보자」).
남이 만든 정답 모델 3(CC0 메크 머리 · Otto · 애니메트로닉 머리)을 정면 직교 광선으로 찍어:
  그림 두 가지 — 평면(부품마다 같은 밝은 회색 + 부품 경계 먹선) · 음영(램버트 + 같은 먹선) · 정답 깊이 · 부품 지도(화소 단위로 같은 광선)
  python 겹깊이시험.py 찍기   → out/오메가몬2/지표/겹깊이/<모델>_{평면,음영}.png · _정답.npz
  D:\\ComfyUI\\venv\\Scripts\\python.exe 겹깊이시험_DA3.py   → <모델>_<그림>_da3.npy
  python 겹깊이시험.py 채점   → 점수.json
채점: 맞닿은 부품 쌍마다 경계 띠(상대 쪽 6 px 안 · 자기 쪽 2 px 안쪽)의 깊이 중앙 차 = 띄움. 정답 띄움과 비교 — ① 앞뒤 부호 맞힘 ② 띄움 순위 상관(스피어만).
대조: 밝기를 깊이로 우기는 가짜(어두울수록 멀다). 통과 = 순위 상관 ≥ 0.5 이고 밝기 대조보다 높음(먼저 적음)."""
import os, sys, glob, json, numpy as np, trimesh, cv2
from scipy.stats import spearmanr
R = r"G:\art2real\원화3d\out"; O = os.path.join(R, "오메가몬2", "지표", "겹깊이"); os.makedirs(O, exist_ok=True)
모델 = {"메크머리": (sorted(glob.glob(os.path.join(R, "샘플", "메크머리_CC0", "지온", "자세_*.obj"))), (0, -1, 0)),
       "Otto": (sorted(glob.glob(os.path.join(R, "샘플", "분할시험", "쉬움_Otto", "부품", "*.stl"))), (0, 1, 0)),
       "애니메트로닉": (sorted(glob.glob(os.path.join(R, "샘플", "분할시험", "중간_애니머리", "부품", "*.stl"))), (0, 1, 0))}
N = 512

def 찍기(먹선="부품경계"):
    for 이름, (fs, d) in 모델.items():
        parts = [trimesh.load(f, force="mesh") for f in fs]; m = trimesh.util.concatenate(parts); owner = np.repeat(np.arange(len(parts)), [len(p.faces) for p in parts])
        d = np.array(d, float); up = np.array([0, 0, 1.0]); right = np.cross(d, up)
        c = m.bounds.mean(0); P = m.vertices - c; ext = max(np.ptp(P @ right), np.ptp(P @ up)) * 1.08
        g = (np.arange(N) + 0.5) / N * ext - ext / 2; GX, GY = np.meshgrid(g, -g)
        o = c + GX.reshape(-1, 1) * right + GY.reshape(-1, 1) * up - d * (np.ptp(P @ d) + 10)
        loc, ray, tri = m.ray.intersects_location(o, np.repeat(d[None], len(o), 0), multiple_hits=False)
        dep = np.full(N * N, np.nan); dep[ray] = (loc - o[ray]) @ d; part = np.full(N * N, -1); part[ray] = owner[tri]
        nrm = np.zeros((N * N, 3)); nrm[ray] = m.face_normals[tri]
        dep = dep.reshape(N, N); part = part.reshape(N, N); nrm = nrm.reshape(N, N, 3)
        L = np.array([-0.4, -0.6, 0.7]) @ np.stack([right, -d, up]); L /= np.linalg.norm(L)        # 왼 위 앞에서 빛
        lam = np.clip(np.abs(nrm @ (np.array([-0.4, 0, 0.7]) * 0 + (-d * 0.6 + up * 0.5 - right * 0.4))) / np.linalg.norm(-d * 0.6 + up * 0.5 - right * 0.4), 0, 1)
        edge = np.zeros((N, N), bool); edge[:, 1:] |= part[:, 1:] != part[:, :-1]; edge[1:, :] |= part[1:, :] != part[:-1, :]
        if 먹선 == "원화식":   # 10-02 사용자 지적: 부품 경계만 그리면 한 부품 안의 단차 · 꺾임 먹선이 사라진다 → 원화처럼 깊이 끊김 · 꺾인 모서리에도
            dz = np.nan_to_num(dep, nan=1e9); px = ext / N
            edge[:, 1:] |= np.abs(dz[:, 1:] - dz[:, :-1]) > 3 * px; edge[1:, :] |= np.abs(dz[1:, :] - dz[:-1, :]) > 3 * px
            cosx = (nrm[:, 1:] * nrm[:, :-1]).sum(-1); cosy = (nrm[1:, :] * nrm[:-1, :]).sum(-1)
            edge[:, 1:] |= cosx < np.cos(np.radians(35)); edge[1:, :] |= cosy < np.cos(np.radians(35))
        edge = cv2.dilate(edge.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        hit = part >= 0; 접미 = "" if 먹선 == "부품경계" else "_원화식"
        평면 = np.where(hit, 225, 255).astype(np.uint8); 평면[edge & (hit | np.roll(hit, 1, 0) | np.roll(hit, 1, 1))] = 20
        음영 = np.where(hit, 60 + 180 * lam, 255).astype(np.uint8); 음영[edge & (hit | np.roll(hit, 1, 0) | np.roll(hit, 1, 1))] = 20
        for k, im in (("평면", 평면), ("음영", 음영)): cv2.imencode(".png", cv2.cvtColor(im, cv2.COLOR_GRAY2BGR))[1].tofile(os.path.join(O, f"{이름}_{k}{접미}.png"))
        np.savez_compressed(os.path.join(O, f"{이름}_정답.npz"), 깊이=dep, 부품=part)
        접미 = ""
        print(이름, "부품", len(parts), "보이는 부품", len(np.unique(part[hit])), "맞은 화소", int(hit.sum()))

def 띄움(depth, part, 최소=20):
    out = {}; ids = [i for i in np.unique(part) if i >= 0]; M = {i: part == i for i in ids}
    big = {i: cv2.dilate(M[i].astype(np.uint8), np.ones((13, 13), np.uint8)) > 0 for i in ids}
    core = {i: cv2.erode(M[i].astype(np.uint8), np.ones((5, 5), np.uint8)) > 0 for i in ids}
    for a in ids:
        for b in ids:
            if b <= a: continue
            ba = core[a] & big[b]; bb = core[b] & big[a]
            if ba.sum() < 최소 or bb.sum() < 최소: continue
            out[(a, b)] = float(np.nanmedian(depth[ba]) - np.nanmedian(depth[bb]))   # + 면 a 가 더 멂
    return out

def 채점(접미=""):
    점수 = {}
    for 이름 in 모델:
        z = np.load(os.path.join(O, f"{이름}_정답.npz")); gt = z["깊이"]; part = z["부품"]; G_ = 띄움(gt, part); keys = [k for k, v in G_.items() if abs(v) > 0.05]
        점수[이름] = {"쌍": len(keys)}
        for 그림 in ("평면", "음영"):
            im = cv2.imdecode(np.fromfile(os.path.join(O, f"{이름}_{그림}{접미}.png"), np.uint8), cv2.IMREAD_GRAYSCALE).astype(float)
            후보 = {"밝기대조": 255 - cv2.GaussianBlur(im, (0, 0), 3)}            # 어두울수록 멀다고 우김
            f = os.path.join(O, f"{이름}_{그림}{접미}_da3.npy")
            if os.path.exists(f): da = np.load(f); 후보["DA3"] = cv2.resize(da, (N, N), interpolation=cv2.INTER_LINEAR)
            for 이름2, D in 후보.items():
                P_ = 띄움(D, part); ks = [k for k in keys if k in P_]
                g = np.array([G_[k] for k in ks]); p = np.array([P_[k] for k in ks])
                부호 = float(np.mean(np.sign(g) == np.sign(p))); rho = float(spearmanr(g, p).correlation) if len(ks) > 3 else float("nan")
                rho_abs = float(spearmanr(np.abs(g), np.abs(p)).correlation) if len(ks) > 3 else float("nan")
                점수[이름][f"{그림}_{이름2}"] = {"앞뒤맞힘": round(부호, 2), "띄움순위상관": round(rho, 2), "크기순위상관": round(rho_abs, 2)}
    json.dump(점수, open(os.path.join(O, f"점수{접미}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in 점수.items(): print(k, v)

if __name__ == "__main__":
    a = sys.argv[1:]; 원 = "원화식" in a
    if a[0] == "찍기": 찍기("원화식" if 원 else "부품경계")
    else: 채점("_원화식" if 원 else "")
