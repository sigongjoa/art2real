# -*- coding: utf-8 -*-
"""고리 — 판 하나로 분석-합성 고리를 닫는다 (09-29 패널 권고 1 · 「구현해보자고」).
    python 고리.py [부품 이름 …]  -> out/오메가몬2/지표/고리_<판>.png (장마다 전 · 후 겹침) · 고리_<판>.json (점수판) · 판/고리/<부품>.stl (옮긴 부품)
상태 = 6 판 부품(기본: 코 · 부리2 · 부리3 = 부리 판)을 강체로 묶어 3 매개변수 — pitch(x 축 기울기) · yaw(y 축) · dz(앞뒤 깊이, 단위).
감지기 = 오늘 만든 것 그대로: 자세2(실루엣 자세) · 영역(면 라벨). 목표 마스크 = 초기 투영과 40 % 넘게 겹치는 면들의 합(장마다 · 고정).
손실 = 맞춤 장(정면 · 3/4)의 1 − IoU 합. 심판 = 안 쓴 옆 장의 IoU(held-out) — 전 · 후.
지표는 회귀 방지용(옆 IoU 가 나빠지면 실패)이고 판정은 렌더를 보고 사용자가 한다.
"""
import os, sys, json, glob, math, time
import numpy as np, cv2, trimesh
from scipy.optimize import minimize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
from 부품투영 import 단위, 찍기, 읽기, 머리mm, cx_mm, top_mm
from 자세 import 캡처 as 캡처2D
자세 = json.load(open(J(OUT, "자세2.json"), encoding="utf-8")); D6 = J(OUT, "..", "머리", "단계4")
장들 = {"정면 yt_172": "정면", "3/4 M04": "3-4", "옆 yt_235": "옆"}; 맞춤장 = ["정면 yt_172", "3/4 M04"]; 심판장 = "옆 yt_235"
def 마스크(U, F, 자, shape):
    uv, _ = 찍기(U, 자); m = np.zeros(shape, np.uint8); pts = np.round(uv).astype(np.int32)
    for tri in F: cv2.fillPoly(m, [pts[tri]], 1)
    return m > 0
def 변환(U, c, p):
    pitch, yaw, dz = p; Rx = cv2.Rodrigues(np.array([pitch, 0, 0.0]))[0]; Ry = cv2.Rodrigues(np.array([0, yaw, 0.0]))[0]
    return (U - c) @ (Rx @ Ry).T + c + np.array([0, 0, dz])
def mm(U): return np.stack([U[:, 0] / 100 * 머리mm + cx_mm, -U[:, 2] / 100 * 머리mm, top_mm - U[:, 1] / 100 * 머리mm], 1)
if __name__ == "__main__":
    t0 = time.time(); args = [a for a in sys.argv[1:] if not a.startswith("--")]; 전부 = "--전부" in sys.argv; dz최대 = float(next((a.split("=")[1] for a in sys.argv if a.startswith("--dz최대=")), 100))
    이름들 = args or ["코", "부리2", "부리3"]; 판이름 = "+".join(이름들) + ("_전부" if 전부 else "") + ("_dz%d" % dz최대 if dz최대 < 100 else "")
    if 전부: 맞춤장.append(심판장)
    부품 = [(n, trimesh.load(J(D6, n + ".stl"), process=False, force="mesh")) for n in 이름들]
    U0 = np.concatenate([단위(np.asarray(m.vertices, float)) for _, m in 부품]); F = []; off = 0
    for _, m in 부품: F.append(np.asarray(m.faces) + off); off += len(m.vertices)
    F = np.concatenate(F); c = U0.mean(0)
    장 = {}
    for n, 태그 in 장들.items():
        f, _ = 캡처2D[n]; im = 읽기(J(장면, f)); H, W = im.shape[:2]; 자 = 자세[n]
        라벨3 = np.load(J(OUT, "영역_%s.npz" % 태그))["라벨"]; 라벨 = cv2.resize(라벨3.astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST).astype(np.int32)
        m0 = 마스크(U0, F, 자, (H, W)); 목표 = np.zeros((H, W), bool)
        for i in np.unique(라벨[m0]):
            if i <= 0: continue
            r = 라벨 == i
            if (r & m0).sum() >= 0.4 * r.sum(): 목표 |= r
        sil = None
        if 태그 == "옆":                                                                  # 옆은 면이 새서(그늘) 목표 면을 못 쓴다 → 실루엣으로 심판: 포함률 · 앞끝 틈
            c_ = np.load(J(OUT, "윤곽2_옆_전체.npy")); sil = np.zeros((H, W), np.uint8); cv2.fillPoly(sil, [c_.astype(np.int32)], 1); sil = sil > 0
        장[n] = dict(im=im, 자=자, 목표=목표, m0=m0, sil=sil)
        print("%-12s 목표 면 화소 %6d · 초기 투영 %6d · IoU0 %.3f" % (n, 목표.sum(), m0.sum(), (m0 & 목표).sum() / max(1, (m0 | 목표).sum())))
    def iou(n, p):
        d = 장[n]; m = 마스크(변환(U0, c, p), F, d["자"], d["목표"].shape)
        if d["sil"] is not None:                                                            # 옆: 포함률 − 앞끝 틈 벌점(실루엣 앞끝과 부리 앞끝의 x 차 / 머리 px)
            ys, xs = np.nonzero(m); 
            if len(xs) == 0: return 0.0
            rows = slice(ys.min(), ys.max() + 1); sx = np.nonzero(d["sil"][rows].any(0))[0]; 틈 = abs(int(xs.min()) - int(sx.min())) / (d["자"]["s"] * 100) if len(sx) else 1.0
            return float((m & d["sil"]).sum() / m.sum()) - 틈
        return (m & d["목표"]).sum() / max(1, (m | d["목표"]).sum())
    손실 = lambda p: sum(1 - iou(n, p) for n in 맞춤장) + 0.02 * (abs(p[0]) + abs(p[1])) / math.radians(30) + max(0.0, abs(p[2]) - dz최대) * 0.1     # 큰 기울기는 조금 벌한다 · dz 는 상한 밖에서 벌한다
    p0 = np.zeros(3); best = None
    for 초기 in (p0, np.array([math.radians(15), 0, 8.0]), np.array([math.radians(-15), 0, -8.0])):
        r = minimize(손실, 초기, method="Nelder-Mead", options=dict(maxiter=150, xatol=1e-3, fatol=1e-4))
        if best is None or r.fun < best.fun: best = r
    p = best.x; 전 = {n: round(float(iou(n, p0)), 3) for n in 장}; 후 = {n: round(float(iou(n, p)), 3) for n in 장}
    print("맞춘 값  pitch %.1f° yaw %.1f° dz %.1f 단위  (%.0f 초)" % (math.degrees(p[0]), math.degrees(p[1]), p[2], time.time() - t0))
    print("점수판  " + " · ".join("%s %.3f→%.3f" % (장들[n], 전[n], 후[n]) for n in 장) + "  [옆 = 실루엣 포함률 − 앞끝 틈 · %s]" % ("맞춤에 포함" if 전부 else "held-out"))
    # 그림: 장마다 전(빨강) · 후(초록) 윤곽 + 목표 면(파랑 채움)
    rows = []
    for n, d in 장.items():
        vis = d["im"].copy(); 목 = d["sil"] if d["sil"] is not None else d["목표"]; vis[목] = (vis[목] * 0.5 + np.array((255, 120, 0)) * 0.5).astype(np.uint8)
        for m, col in ((d["m0"], (0, 0, 255)), (마스크(변환(U0, c, p), F, d["자"], d["목표"].shape), (0, 255, 0))):
            cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cv2.drawContours(vis, cs, -1, col, 2)
        ys, xs = np.nonzero(d["목표"] | d["m0"]); y0, y1, x0, x1 = max(0, ys.min() - 60), ys.max() + 60, max(0, xs.min() - 60), xs.max() + 60
        crop = vis[y0:y1, x0:x1]; crop = cv2.resize(crop, (int(crop.shape[1] * 360 / crop.shape[0]), 360)); cv2.putText(crop, "%s %s %.2f->%.2f" % (장들[n], "held-out" if n == 심판장 else "fit", 전[n], 후[n]), (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3); cv2.putText(crop, "%s %s %.2f->%.2f" % (장들[n], "held-out" if n == 심판장 else "fit", 전[n], 후[n]), (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1); rows.append(crop)
    W = max(r.shape[1] for r in rows); S = np.concatenate([np.pad(r, ((0, 0), (0, W - r.shape[1]), (0, 0)), constant_values=245) for r in rows], 0)
    cv2.imencode(".png", S)[1].tofile(J(OUT, "고리_%s.png" % 판이름))
    DO = J(OUT, "판", "고리"); os.makedirs(DO, exist_ok=True); off = 0
    for n, m in 부품:
        V = 변환(단위(np.asarray(m.vertices, float)), c, p); trimesh.Trimesh(mm(V), np.asarray(m.faces), process=False).export(J(DO, n + ".stl"))
    json.dump(dict(판=판이름, 매개변수=dict(pitch_deg=math.degrees(p[0]), yaw_deg=math.degrees(p[1]), dz=float(p[2])), 전=전, 후=후, 초=round(time.time() - t0)), open(J(OUT, "고리_%s.json" % 판이름), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
