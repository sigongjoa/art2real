# -*- coding: utf-8 -*-
"""윤곽1 채점 — 바탕(3 방향 윤곽 교차 STEP) 위에 깎는 코드 → 실물과 모서리 F1 · IoU + 비교 그림
python runs/윤곽1/채점.py <부품번호 0~35> <코드.py> [그림.png]
코드 안에서 쓸 수 있는 것: cq · 바탕(cq.Workplane · 단위 = 100 배 단위 상자: 부품이 [0,100]³ 안 · 긴 변 100) · 결과는 변수 r 에 둔다
출력 한 줄 JSON {"edge_f1", "iou", "오류"}"""
import os, sys, json, tempfile, multiprocessing as mp
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"

def _일(q, i, src, png):
    sys.path[:0] = [os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
    try:
        import trimesh, numpy as np, cadquery as cq
        from s0 import unit
        from 모양자 import 재기
        부품 = [r["부품"] for k in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % k), encoding="utf-8"))]
        m = unit(trimesh.load(RR + 부품[i], force="mesh")); gt = m.copy(); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
        sp = os.path.join(R, "윤곽0", "결과", "%02d_교차.step" % i)
        ns = {"cq": cq, "바탕": cq.importers.importStep(sp) if os.path.exists(sp) else None}
        exec(open(src, encoding="utf-8").read(), ns); obj = ns["r"]
        p = os.path.join(tempfile.gettempdir(), "윤곽1_%d.stl" % os.getpid()); cq.exporters.export(obj, p, tolerance=0.05, angularTolerance=0.2)
        pm = trimesh.load(p); pm.apply_scale(1 / 50.0); pm.apply_translation([-1, -1, -1]); r = 재기(pm, gt)
        if png:
            from render import render
            from PIL import Image
            C = 260; im = Image.new("RGB", (C * 3, C * 2), "white")
            g2 = m.copy(); p2 = pm.copy(); p2.apply_translation([1, 1, 1]); p2.apply_scale(.5)
            for j, f in enumerate(([1, 1, 1], [-1, 0.3, 0.2], [0.2, -0.3, 1])):
                for k_, mm in enumerate((g2, p2)): im.paste(render(np.asarray(mm.vertices), np.asarray(mm.faces), f, img_size=C), (j * C, k_ * C))
            im.save(png)
        q.put({"edge_f1": r["edge_f1"], "iou": r["iou"], "오류": None})
    except Exception as e: q.put({"edge_f1": -1, "iou": -1, "오류": str(e)[:200]})

if __name__ == "__main__":
    i, src = int(sys.argv[1]), sys.argv[2]; png = sys.argv[3] if len(sys.argv) > 3 else None
    q = mp.Queue(); pr = mp.Process(target=_일, args=(q, i, src, png)); pr.start(); pr.join(120)
    if pr.is_alive(): pr.kill(); print(json.dumps({"edge_f1": -2, "iou": -2, "오류": "120 초 넘음"}, ensure_ascii=False))
    else: print(json.dumps(q.get(), ensure_ascii=False))
