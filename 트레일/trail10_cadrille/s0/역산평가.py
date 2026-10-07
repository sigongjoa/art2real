# -*- coding: utf-8 -*-
"""역산 자가 학습 1 바퀴 판정 (10-07 · 돌리기 전에 고정)
시험 부품(학습에 안 나온 모델)마다 그림 입력으로 8 번 표집(temperature 1) → 실행 → IoU(open3d · 64³) · 바탕 모델과 LoRA 를 같은 조건으로.
판정: LoRA 가 바탕보다 ① 「최고 IoU ≥ 0.8 인 시험 부품 비율」 +10 %p 이상 ② 최고 IoU 중앙값이 오름 — 둘 다면 통과, 아니면 실패로 보고.
python s0/역산평가.py <split.json> <출력.json> [LoRA 폴더]"""
import os, sys, json, time, numpy as np, torch, trimesh
from concurrent.futures import ProcessPoolExecutor
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.dirname(H), os.path.join(H, "stub"), H]
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; W = os.path.join(os.path.dirname(H), "weights")
from 역산수확 import 채점

def 채점2(args):   # 10-07: 모서리 F1(≥0.42 = 맞힘) · IoU 도 기록 — 같은 일꾼 · 8 GB 상한
    code, gtp = args
    from score import cap; cap()
    import cadquery as cq, tempfile
    from 모양자 import 재기
    try:
        ns = {"cq": cq}; exec(code, ns); obj = ns.get("r") or next(v for v in ns.values() if isinstance(v, cq.Workplane))
        p = os.path.join(tempfile.gettempdir(), "평가2_%d.stl" % os.getpid()); cq.exporters.export(obj, p); m = trimesh.load(p); m.apply_scale(1 / 100.0)
        r = 재기(m, trimesh.load(gtp)); return r["edge_f1"], r["iou"]
    except Exception:
        return -1.0, -1.0

if __name__ == "__main__":
    from transformers import AutoProcessor
    from cadrille import Cadrille, collate
    import s0 as S
    sp, out = sys.argv[1], sys.argv[2]; lp = sys.argv[3] if len(sys.argv) > 3 else None; N = int(os.environ.get("NSAMP", "8"))
    model = Cadrille.from_pretrained(os.path.join(W, "cadrille"), torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda")
    if lp:
        from peft import PeftModel; model = PeftModel.from_pretrained(model, lp)
    model.eval(); proc = AutoProcessor.from_pretrained(os.path.join(W, "qwen2vl2b"), min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28, padding_side="left")
    torch.manual_seed(0); pool = ProcessPoolExecutor(1); res = []; tmp = os.path.join(os.path.dirname(out), "_gt_eval_%d.stl" % os.getpid())   # 10-07: 프로세스마다 따로 — 같은 폴더 평가 둘이 서로 덮어써 점수가 섞였다
    for name in json.load(open(sp, encoding="utf-8"))["시험부품"]:
        gt = S.unit(trimesh.load(R + name, force="mesh")); g2 = gt.copy(); g2.apply_translation([-0.5] * 3); g2.apply_scale(2.0); g2.export(tmp)
        b = collate([dict(S.item_img(gt)[0], file_name=name)] * N, processor=proc, n_points=256, eval=True)
        with torch.no_grad():
            o = model.generate(input_ids=b["input_ids"].cuda(), attention_mask=b["attention_mask"].cuda(), point_clouds=b["point_clouds"].cuda(), is_pc=b["is_pc"].cuda(), is_img=b["is_img"].cuda(),
                               pixel_values_videos=b["pixel_values_videos"].cuda() if b.get("pixel_values_videos") is not None else None,
                               video_grid_thw=b["video_grid_thw"].cuda() if b.get("video_grid_thw") is not None else None, max_new_tokens=768, do_sample=True, temperature=1.0, top_p=0.95)
        ious, edges, codes = [], [], proc.batch_decode(o[:, b["input_ids"].shape[1]:], skip_special_tokens=True)
        for c in codes:
            fu = pool.submit(채점2, (c, tmp))
            try: e, i = fu.result(timeout=60); edges.append(round(e, 3)); ious.append(round(i, 3))
            except Exception:
                edges.append(-2.0); ious.append(-2.0)
                for p in list(getattr(pool, "_processes", {}).values()): p.kill()
                pool.shutdown(wait=False, cancel_futures=True); pool = ProcessPoolExecutor(1)
        res.append({"부품": name, "IoU": ious, "모서리": edges, "최고": max(ious), "최고모서리": max(edges), "코드": codes}); print(name[:40], max(edges), max(ious), flush=True)
    b_ = np.array([r["최고"] for r in res]); v = np.array([x for r in res for x in r["IoU"]])
    e_ = np.array([r["최고모서리"] for r in res])
    요약 = {"LoRA": lp, "부품": len(res), "맞힘(모서리≥0.42) 비율": round(float((e_ >= 0.42).mean()), 3), "최고 모서리 중앙": round(float(np.median(e_)), 3), "≥0.8 비율": round(float((b_ >= 0.8).mean()), 3), "≥0.6 비율": round(float((b_ >= 0.6).mean()), 3), "최고 중앙": round(float(np.median(b_)), 3), "실행 실패율": round(float((v == -1).mean()), 3)}
    json.dump({"요약": 요약, "부품별": res}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(요약)
