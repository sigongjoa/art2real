# -*- coding: utf-8 -*-
"""기능0 디테일 판 — 깔끔한 기능 바탕 위에 선 그림의 닫힌 고리(판 · 홈 · 보스)를 한 층씩 · 10-11
고리 = 여섯 방향 선 그림(메시 모서리선 · A 판)으로 나뉜 면 · 안쪽 실물 깊이가 고르고(평평) 바탕 깊이와 1.5 칸 넘게 다르면
깊으면 홈(그 깊이까지 파기) · 얕으면 보스(바탕 면에서 그 깊이까지 붙이기) · 조각이 늘면 버림
python runs/기능0/디테일.py [그림] 번호…   →  디테일/NN.step · stl · json (그림 = 고를 고리만 그려 봄)"""
import os, sys, json, numpy as np, cv2, trimesh
from 도구 import *
sys.path.insert(0, os.path.join(R, "선고리"))
import importlib.util
_s = importlib.util.spec_from_file_location("선고리", os.path.join(R, "선고리", "선고리.py")); 선 = importlib.util.module_from_spec(_s); _s.loader.exec_module(선)
from 실물보기 import 실물보기
선.MINA = 6
n = 128; 문턱 = float(os.environ.get("TH", .8)) / n; 고름 = float(os.environ.get("IQ", 3.0)) / n

def 바탕깊이(s):   # CAD 바탕 → 6 방향 깊이(128)
    from 윤곽 import 메시로
    m = 메시로(s); m.apply_translation([1, 1, 1]); m.apply_scale(.5); return 실물보기(m, n)

def 고리찾기(i, s):
    from s0 import unit
    X = 입력(i); S = X[0] > .5; D = X[3]; mu = unit(trimesh.load(W.RR + str(부[i]), force="mesh"))
    Sb, Db = 바탕깊이(s); out = []
    for k in range(6):
        L = 선.모서리선(mu, D[k], X[0][k], k)
        for 종, m in 선.면나누기(X[0][k], L):
            안 = m > 0
            if 종 != "고리" or 안.sum() < 6 or 안.sum() > .4 * S[k].sum() or (Sb[k][안] > .5).mean() < .8: continue
            안 = 안 & (Sb[k] > .5)
            d = D[k][안]; db = Db[k][안]
            if np.percentile(d, 75) - np.percentile(d, 25) > 고름: continue           # 바닥이 고르지 않음(비탈 · 여러 층)
            Δ = float(np.median(d) - np.median(db))
            if abs(Δ) < 문턱 or abs(Δ) > .3: continue
            out.append({"쪽": k, "m": m, "종": "홈" if Δ > 0 else "보스", "깊이": float(np.median(d)), "바탕": float(np.median(db)), "넓이": int(안.sum())})
    return out

def 기둥(f, a, b):   # 고리 다각형을 깊이 a~b(보는 쪽 비율) 사이로 민 기둥
    k = f["쪽"]; ax = k // 2; o = [j for j in range(3) if j != ax]
    cs, _ = cv2.findContours(f["m"], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); p = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 1.0, True)[:, 0, :]
    if len(p) < 3: return None
    z = lambda t: (1 - t) * 110 - 5 if k % 2 else t * 110 - 5; za, zb = z(a), z(b); pts = []
    for cc, rr in p:
        q = [0.0, 0.0, 0.0]; q[o[0]] = c8(rr); q[o[1]] = c8(cc); q[ax] = za; pts.append(V(*q))
    d_ = [0, 0, 0]; d_[ax] = zb - za
    return cq.Workplane().add(cq.Solid.extrudeLinear(cq.Face.makeFromWires(cq.Wire.makePolygon(pts, close=True)), V(*d_)))

def 얹기(s, fs):
    n0 = len(s.solids().vals()); 됨 = []
    for f in sorted(fs, key=lambda f: -f["넓이"]):
        try:
            if f["종"] == "홈": t = s.cut(기둥(f, -.2, f["깊이"]))
            else: t = s.union(기둥(f, f["깊이"], f["바탕"] + 2 / n))
            if len(t.solids().vals()) > n0: continue
            s = t; 됨.append(f)
        except Exception: pass
    return s, 됨

if __name__ == "__main__":
    그림 = "그림" in sys.argv; ids = [int(a) for a in sys.argv[1:] if a.isdigit()]; O = os.path.join(H, "디테일"); os.makedirs(O, exist_ok=True)
    for i in ids:
        s = cq.importers.importStep(os.path.join(H, "최종", "%02d.step" % i)); fs = 고리찾기(i, s)
        print(i, "고리", len(fs), "홈", sum(f["종"] == "홈" for f in fs), "보스", sum(f["종"] == "보스" for f in fs), flush=True)
        if 그림:
            X = 입력(i); rows = []
            for k in range(6):
                a = np.full((n, n, 3), 255, np.uint8); a[X[0][k] > .5] = (225, 228, 236)
                for f in fs:
                    if f["쪽"] == k: a[f["m"] > 0] = (220, 60, 60) if f["종"] == "홈" else (40, 140, 220)
                rows.append(cv2.resize(a, (256, 256), interpolation=cv2.INTER_NEAREST))
            cv2.imencode(".png", np.concatenate(rows, 1)[:, :, ::-1])[1].tofile(os.path.join(O, "고리_%02d.png" % i)); continue
        from 윤곽 import 메시로
        from 모양자 import 재기
        from s0 import unit
        r, 됨 = 얹기(s, fs); gt = unit(trimesh.load(W.RR + str(부[i]), force="mesh")); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
        pm = 메시로(r); e = 재기(pm, gt); pm.export(os.path.join(O, "%02d.stl" % i)); cq.exporters.export(r, os.path.join(O, "%02d.step" % i))
        j = {"부품": str(부[i]), "얹음": [(f["종"], f["쪽"], f["넓이"]) for f in 됨], "후보": len(fs), "edge_f1": e["edge_f1"], "iou": e["iou"]}; print(i, "얹음", len(됨), flush=True)
        json.dump(j, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
