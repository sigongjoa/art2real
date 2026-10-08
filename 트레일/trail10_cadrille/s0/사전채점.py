# -*- coding: utf-8 -*-
"""구조 문장 하나 채점(10-08 · 사전 0 단계) — 사람 부품과 모서리 F1 · IoU + 나란히 그림
python s0/사전채점.py <부품 상대 경로> <구조 문장 파일> [그림.png]
  출력 한 줄 JSON: {"edge_f1", "iou", "낱말수", "오류"} · 그림은 위 = 사람, 아래 = 구조 문장(3 방향)
채점 규약은 다시채점.py 와 같다: gt = unit → −0.5 → ×2 · 예측 메시 ÷100"""
import os, sys, json, tempfile, multiprocessing as mp
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.dirname(H), os.path.join(H, "stub"), H]
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"

def _일(q, part, src, png):
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(H)), "trail11_zerotocad", "s"))
    try:
        from score import cap; cap()
        import trimesh, numpy as np, cadquery as cq, s0 as S
        from 부품사전 import 짓기, 읽기
        from 모양자 import 재기
        gt = S.unit(trimesh.load(R + part, force="mesh")); g2 = gt.copy(); g2.apply_translation([-0.5] * 3); g2.apply_scale(2.0)
        문장 = open(src, encoding="utf-8").read(); obj = 짓기(문장)
        p = os.path.join(tempfile.gettempdir(), "사전_%d.stl" % os.getpid()); cq.exporters.export(obj, p)
        m = trimesh.load(p); m.apply_scale(1 / 100.0); r = 재기(m, g2)
        if png:
            from render import render
            from PIL import Image
            pm = S.unit(trimesh.load(p)); C = 260; im = Image.new("RGB", (C * 3, C * 2), "white")
            for j, f in enumerate(([1, 1, 1], [-1, 0.3, 0.2], [0.2, -0.3, 1])):
                for i, mm in enumerate((gt, pm)): im.paste(render(np.asarray(mm.vertices), np.asarray(mm.faces), f, img_size=C), (j * C, i * C))
            im.save(png)
        q.put({"edge_f1": r["edge_f1"], "iou": r["iou"], "낱말수": len(읽기(문장)), "오류": None})
    except Exception as e:
        q.put({"edge_f1": -1, "iou": -1, "낱말수": 0, "오류": str(e)[:200]})

if __name__ == "__main__":
    part, src = sys.argv[1], sys.argv[2]; png = sys.argv[3] if len(sys.argv) > 3 else None
    q = mp.Queue(); pr = mp.Process(target=_일, args=(q, part, src, png)); pr.start(); pr.join(90)
    if pr.is_alive(): pr.kill(); print(json.dumps({"edge_f1": -2, "iou": -2, "낱말수": 0, "오류": "90 초 넘음"}, ensure_ascii=False))
    else: print(json.dumps(q.get(), ensure_ascii=False))
