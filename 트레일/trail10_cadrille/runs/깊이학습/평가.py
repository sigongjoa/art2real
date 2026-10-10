# -*- coding: utf-8 -*-
"""깊이학습 평가 — 예측 깊이로 윤곽2 깊이깎기 → 같은 자 · python runs/깊이학습/평가.py [시작 끝]  →  결과/NN.json · NN_깎음.stl"""
import os, sys, json, numpy as np, torch, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [H, os.path.join(R, "윤곽2"), os.path.join(R, "조각0"), os.path.join(R, "윤곽0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
from 학습u import 망u
from 학습 import 망   # 깊이깎기가 조각0 을 경로 앞에 넣어 조각0/학습.py 와 이름이 겹친다 → 먼저 가져옴
import 깊이깎기 as G
from 실물보기 import 실물보기
from 윤곽 import 메시로
from s0 import unit
from 모양자 import 재기
import cadquery as cq
a_, b_ = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 36)
T = np.load(os.path.join(H, "시험.npz")); X, 부품 = T["X"], T["부품"]
GATE, FIX, RK = float(os.environ.get("GATE", 0)), float(os.environ.get("FIX", 0)), float(os.environ.get("RK", 0))   # RK: 주머니 단위 확신 문턱   # 10-10 2 판: 잔차 > k·퍼짐 인 곳만 · 대조: 잔차 > 고정 문턱
m = (망u() if GATE or RK else 망()).cuda(); m.load_state_dict(torch.load(os.path.join(H, "모델u.pt" if GATE or RK else os.environ.get("MODEL", "모델.pt")))); m.eval()
O = os.path.join(H, os.environ.get("OUTN", "결과")); os.makedirs(O, exist_ok=True)
for i in range(a_, b_):
    sp = os.path.join(R, "윤곽0", "결과", "%02d_교차.step" % i)
    if not os.path.exists(sp): continue
    if os.path.exists(os.path.join(O, "%02d.json" % i)): continue   # 이어 하기
    x = torch.from_numpy(X[i, :3].astype(np.float32)).permute(1, 0, 2, 3).cuda(); Dh = x[:, 2]
    with torch.no_grad():
        y = m(x)
        if GATE: P = torch.where(y[:, 2] > GATE * y[:, 1], y[:, 0], Dh)          # 믿는 곳만 예측 · 나머지는 교차(안 깎음)
        elif FIX: P = torch.where(y[:, 0] - Dh > FIX, y[:, 0], Dh)
        else: P = y[:, 0]
        Qm = (y[:, 2] / y[:, 1]).cpu().numpy() if RK else None
    P = P.cpu().numpy()   # (6,N,N)
    SM = os.environ.get("SMOOTH", "")   # 10-10 사용자 제안: 예측 뒤 매끈하게 — 큰 형태는 맞고 잔결이 가짜 주머니를 만든다
    if SM:
        S0 = X[i, 0].astype(np.float32) > .5
        for k in range(6):
            q = P[k].astype(np.float32)
            if SM == "중앙5": q = cv2.medianBlur(q, 5)
            elif SM == "양방향": q = cv2.bilateralFilter(q, 9, 0.03, 4)
            P[k] = np.where(S0[k], np.maximum(q, X[i, 2, k].astype(np.float32)), 1.0)   # 교차보다 얕아지지 않게 · 실루엣 밖은 1
    mr = unit(trimesh.load(G.RR + str(부품[i]), force="mesh")); Sr, _ = 실물보기(mr, G.N)       # 실루엣은 그림이 준다
    Dp = np.stack([np.where(Sr[k] > .5, cv2.resize(P[k], (G.N, G.N), interpolation=cv2.INTER_LINEAR), 1.0) for k in range(6)])
    gt = mr.copy(); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
    mb = trimesh.load(os.path.join(R, "윤곽0", "결과", "%02d_교차.stl" % i)); mb.apply_translation([1, 1, 1]); mb.apply_scale(.5)
    보 = (Sr, Dp) if not RK else (Sr, Dp, np.stack([cv2.resize(Qm[k], (G.N, G.N), interpolation=cv2.INTER_LINEAR) for k in range(6)]), RK)
    r, n = G.깎기(cq.importers.importStep(sp), mr, mb, None, 보)
    try: pm = 메시로(r); res = 재기(pm, gt); pm.export(os.path.join(O, "%02d_깎음.stl" % i))
    except Exception as e: res = {"edge_f1": 0.0, "iou": 0.0}; print("실패", i, str(e)[:60])
    base = json.load(open(os.path.join(R, "윤곽0", "결과", "%02d.json" % i), encoding="utf-8"))["B"]
    json.dump({"idx": i, "바탕": base, "edge_f1": res["edge_f1"], "iou": res["iou"], "깎은 수": n}, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
    print(i, "바탕 %.2f → 예측깊이 깎음 %.2f · %d 개" % (base, res["edge_f1"], n), flush=True)
