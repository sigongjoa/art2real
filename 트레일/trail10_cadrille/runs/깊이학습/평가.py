# -*- coding: utf-8 -*-
"""깊이학습 평가 — 예측 깊이로 윤곽2 깊이깎기 → 같은 자 · python runs/깊이학습/평가.py [시작 끝]  →  결과/NN.json · NN_깎음.stl"""
import os, sys, json, numpy as np, torch, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [H, os.path.join(R, "윤곽2"), os.path.join(R, "조각0"), os.path.join(R, "윤곽0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
from 학습 import 망   # 깊이깎기가 조각0 을 경로 앞에 넣어 조각0/학습.py 와 이름이 겹친다 → 먼저 가져옴
import 깊이깎기 as G
from 실물보기 import 실물보기
from 윤곽 import 메시로
from s0 import unit
from 모양자 import 재기
import cadquery as cq
a_, b_ = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 36)
T = np.load(os.path.join(H, "시험.npz")); X, 부품 = T["X"], T["부품"]
m = 망().cuda(); m.load_state_dict(torch.load(os.path.join(H, os.environ.get("MODEL", "모델.pt")))); m.eval()
O = os.path.join(H, os.environ.get("OUTN", "결과")); os.makedirs(O, exist_ok=True)
for i in range(a_, b_):
    sp = os.path.join(R, "윤곽0", "결과", "%02d_교차.step" % i)
    if not os.path.exists(sp): continue
    with torch.no_grad(): P = m(torch.from_numpy(X[i, :3].astype(np.float32)).permute(1, 0, 2, 3).cuda())[:, 0].cpu().numpy()   # (6,N,N)
    mr = unit(trimesh.load(G.RR + str(부품[i]), force="mesh")); Sr, _ = 실물보기(mr, G.N)       # 실루엣은 그림이 준다
    Dp = np.stack([np.where(Sr[k] > .5, cv2.resize(P[k], (G.N, G.N), interpolation=cv2.INTER_LINEAR), 1.0) for k in range(6)])
    gt = mr.copy(); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
    mb = trimesh.load(os.path.join(R, "윤곽0", "결과", "%02d_교차.stl" % i)); mb.apply_translation([1, 1, 1]); mb.apply_scale(.5)
    r, n = G.깎기(cq.importers.importStep(sp), mr, mb, None, (Sr, Dp))
    try: pm = 메시로(r); res = 재기(pm, gt); pm.export(os.path.join(O, "%02d_깎음.stl" % i))
    except Exception as e: res = {"edge_f1": 0.0, "iou": 0.0}; print("실패", i, str(e)[:60])
    base = json.load(open(os.path.join(R, "윤곽0", "결과", "%02d.json" % i), encoding="utf-8"))["B"]
    json.dump({"idx": i, "바탕": base, "edge_f1": res["edge_f1"], "iou": res["iou"], "깎은 수": n}, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
    print(i, "바탕 %.2f → 예측깊이 깎음 %.2f · %d 개" % (base, res["edge_f1"], n), flush=True)
