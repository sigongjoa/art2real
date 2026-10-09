# -*- coding: utf-8 -*-
"""윤곽2 — 바탕(윤곽 교차 STEP) 위에 6 방향 깊이 차이로 주머니를 찾아 깎기 · 학습 없음
python runs/윤곽2/깊이깎기.py [시작 끝]"""
import os, sys, json, numpy as np, trimesh, cv2
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(R, "조각0"), os.path.join(R, "윤곽0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
from 실물보기 import 실물보기
from 윤곽 import PL, 메시로
RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; N = 256; TH = 0.02; MINA = 40

def 주머니(Dr, Dh, Sr):   # 한 방향: 실물이 바탕보다 깊은 곳 → [(윤곽 점들(o0,o1), 깊이 d(격자 비율))]
    diff = ((Dr - Dh) > TH) & (Sr > .5)
    im = cv2.morphologyEx(diff.astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    cs, _ = cv2.findContours(im, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); out = []
    for c in cs:
        if cv2.contourArea(c) < MINA: continue
        mk = np.zeros_like(im); cv2.drawContours(mk, [c], -1, 255, -1); d = float(np.median(Dr[mk > 0]))
        a = cv2.approxPolyDP(c, 0.005 * cv2.arcLength(c, True), True)
        pts = [((p[0][1] + .5) / N * 1.1 - .05, (p[0][0] + .5) / N * 1.1 - .05) for p in a]
        if len(pts) >= 3: out.append((pts, d))
    return out

def 깎기(바탕, m_real, m_base):
    import cadquery as cq
    Sr, Dr = 실물보기(m_real, N); Sh, Dh = 실물보기(m_base, N); r = 바탕; n = 0
    for ax in range(3):
        for fl in (False, True):
            k = 2 * ax + (1 if fl else 0)
            for pts, d in 주머니(Dr[k], Dh[k], Sr[k]):
                # 실물보기 규약: 낮은 쪽에서 본 깊이 d → 표면 세계 좌표 w = d·1.1 − 0.05 · 높은 쪽에서 본 것 → w = (1 − d)·1.1 − 0.05
                if not fl: lo, hi = -0.2, d * 1.1 - .05
                else: lo, hi = (1 - d) * 1.1 - .05, 1.2
                s_ = cq.Workplane(PL[ax]).polyline([(a * 100, b * 100) for a, b in pts]).close().extrude((hi - lo) * 100)
                bb = s_.val().BoundingBox(); mn = (bb.xmin, bb.ymin, bb.zmin)[ax]
                off = [0, 0, 0]; off[ax] = lo * 100 - mn                     # 축 방향으로 [lo, hi] 에 오게(작업면 법선 방향과 상관없이)
                try: r = r.cut(s_.translate(tuple(off))); n += 1
                except Exception: pass
    return r, n

if __name__ == "__main__":
    import cadquery as cq
    from s0 import unit
    from 모양자 import 재기
    a_, b_ = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 36)
    부품 = [r["부품"] for k in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % k), encoding="utf-8"))]
    O = os.path.join(H, "결과"); os.makedirs(O, exist_ok=True)
    for i in range(a_, b_):
        sp = os.path.join(R, "윤곽0", "결과", "%02d_교차.step" % i)
        if not os.path.exists(sp): print(i, "바탕 없음"); continue
        m = unit(trimesh.load(RR + 부품[i], force="mesh")); gt = m.copy(); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
        mb = trimesh.load(os.path.join(R, "윤곽0", "결과", "%02d_교차.stl" % i)); mb.apply_translation([1, 1, 1]); mb.apply_scale(.5)   # [-1,1] → 단위 상자
        바탕 = cq.importers.importStep(sp); r, n = 깎기(바탕, m, mb)
        try: pm = 메시로(r); res = 재기(pm, gt); pm.export(os.path.join(O, "%02d_깎음.stl" % i))
        except Exception as e: res = {"edge_f1": 0.0, "iou": 0.0}; print("실패", i, str(e)[:60])
        base = json.load(open(os.path.join(R, "윤곽0", "결과", "%02d.json" % i), encoding="utf-8"))["B"]
        json.dump({"idx": i, "바탕": base, "edge_f1": res["edge_f1"], "iou": res["iou"], "깎은 수": n}, open(os.path.join(O, "%02d.json" % i), "w", encoding="utf-8"), ensure_ascii=False)
        print(i, 부품[i][-30:], "바탕 %.2f → 깎음 %.2f · %d 개" % (base, res["edge_f1"], n), flush=True)
