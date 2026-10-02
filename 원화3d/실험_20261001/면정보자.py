# -*- coding: utf-8 -*-
"""스무딩이 잃은 면 정보 재는 자 (10-02 사용자 「스무딩을 하면 패널라인이나 그림자 정보가 약해진다가 문제」).
메시 묶음을 원화 정면 틀(부조와 같은 블렌더 좌표 · x = (px − W/2)·k · z = −py·k · 앞 = −y)에서 반 해상도 광선으로 찍어:
  그림자 = 원화에서 찾은 빛(화면 방위 170° · 높이 55°, 원화그림자.py)을 등진 정도 상위 q(원화 그림자 비율과 같게) → 원화 그림자(그림자찾기.png)와 IoU
  선 = 깊이 끊김(> 1.5 단위) · 법선 꺾임(> 35°) · 부품 경계 → 원화 먹선(블랙햇)을 2 화소 안에서 다시 그리는 비율(재현율)과 거짓 선 비율
쓰기: from 면정보자 import 재기 ; 재기(메시목록) → dict"""
import os, json, numpy as np, cv2, trimesh
K = r"G:\art2real\원화3d\out\오메가몬2\지표"; G_ = os.path.join(K, "원화그림자")
ART = r"G:\art2real\원화3d\out\번역\디지몬\장면\02_역습\yt_172.0_얼굴_정면.jpg"
Lf = np.load(os.path.join(K, "선파츠_정면.npz"))["라벨"]; ys_, xs_ = np.nonzero(Lf > 0); top, bot = ys_.min(), ys_.max(); k = 100 / (bot - top)
x0, y0, x1, y1 = json.load(open(os.path.join(G_, "그림자.json"), encoding="utf-8"))["자르기"]
s_ = 2   # 반 해상도
sv = cv2.imdecode(np.fromfile(os.path.join(G_, "그림자찾기.png"), np.uint8), 1); art_sh = (sv[:, :, 2] > 120) & (sv[:, :, 1] < 100); art_lit = (sv[:, :, 0] > 150) & (sv[:, :, 1] > 150)
art_sh, art_lit = art_sh[::s_, ::s_], art_lit[::s_, ::s_]; head = art_sh | art_lit
img = cv2.imdecode(np.fromfile(ART, np.uint8), 1)[y0:y1, x0:x1]; Lum = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[:, :, 0]
ink = cv2.morphologyEx(Lum, cv2.MORPH_BLACKHAT, np.ones((7, 7), np.uint8)) > 28
ink = cv2.dilate(ink.astype(np.uint8), np.ones((2, 2), np.uint8))[::s_, ::s_] > 0; ink &= cv2.dilate(head.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
th, el = np.radians(170), np.radians(55); Ls = np.array([np.cos(th) * np.cos(el), np.sin(th) * np.cos(el), np.sin(el)])   # 화면(x 오른 · y 위 · z 보는 쪽)
L_b = np.array([Ls[0], -Ls[2], Ls[1]])                                                                                  # 블렌더(x · y 앞이 음 · z 위)

def 찍기(meshes):
    m = trimesh.util.concatenate(meshes); owner = np.repeat(np.arange(len(meshes)), [len(q.faces) for q in meshes])
    H, W = head.shape; py, px = np.mgrid[0:H, 0:W]; PX = (px * s_ + x0 + 0.5); PY = (py * s_ + y0 + 0.5)
    X = (PX - Lf.shape[1] / 2) * k; Z = -PY * k; Y = np.full(X.shape, m.bounds[0][1] - 10)
    o = np.c_[X.ravel(), Y.ravel(), Z.ravel()]; d = np.array([0, 1.0, 0])
    dep = np.full(len(o), np.nan); nrm = np.zeros((len(o), 3)); part = np.full(len(o), -1)
    for i0 in range(0, len(o), 20000):
        loc, ray, tri = m.ray.intersects_location(o[i0:i0 + 20000], np.repeat(d[None], len(o[i0:i0 + 20000]), 0), multiple_hits=False)
        dep[i0 + ray] = loc[:, 1] - o[i0 + ray, 1]; n_ = m.face_normals[tri]; n_ = np.where((n_[:, 1] > 0)[:, None], -n_, n_); nrm[i0 + ray] = n_; part[i0 + ray] = owner[tri]
    return dep.reshape(H, W), nrm.reshape(H, W, 3), part.reshape(H, W)

def 재기(meshes, 이름=""):
    dep, nrm, part = 찍기(meshes); hit = ~np.isnan(dep); both = hit & head
    s = -(nrm @ L_b); q = art_sh[head].mean(); thr = np.quantile(s[both], 1 - q) if both.any() else 0
    sh = both & (s >= thr); iou_sh = float((sh & art_sh).sum() / ((sh | art_sh) & both).sum()) if both.any() else 0.0
    dz = np.nan_to_num(dep, nan=1e9); line = np.zeros(dep.shape, bool)
    line[:, 1:] |= np.abs(dz[:, 1:] - dz[:, :-1]) > 1.5; line[1:, :] |= np.abs(dz[1:, :] - dz[:-1, :]) > 1.5
    line[:, 1:] |= (nrm[:, 1:] * nrm[:, :-1]).sum(-1) < np.cos(np.radians(35)); line[1:, :] |= (nrm[1:, :] * nrm[:-1, :]).sum(-1) < np.cos(np.radians(35))
    line[:, 1:] |= (part[:, 1:] != part[:, :-1]); line[1:, :] |= (part[1:, :] != part[:-1, :]); line &= head
    near_l = cv2.dilate(line.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0; near_i = cv2.dilate(ink.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    rec = float((ink & near_l).sum() / max(ink.sum(), 1)); false = float((line & ~near_i).sum() / max(line.sum(), 1))
    vis = np.full(head.shape + (3,), 255, np.uint8); vis[head] = (225, 225, 225); vis[sh] = (150, 110, 170); vis[line] = (30, 30, 30)
    return {"그림자IoU": round(iou_sh, 3), "먹선재현율": round(rec, 3), "거짓선비율": round(false, 3), "맞은화소": int(both.sum())}, vis

def 원화그림():
    vis = np.full(head.shape + (3,), 255, np.uint8); vis[head] = (225, 225, 225); vis[art_sh] = (150, 110, 170); vis[ink] = (30, 30, 30); return vis
