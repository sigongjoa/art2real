# -*- coding: utf-8 -*-
"""역산 수확 시험 (2026-10-06 · 판정 기준은 돌리기 전에 고정)
질문: 사람이 나눈 출력용 부품(메시만 있음)에서, 학습 전 cadrille 가 쓴 코드 중 원본과 겹치는(IoU ≥ 0.8) 것이 몇 개나 나오나 = 공짜 정답 데이터 양
- 부품: 사람분할 60 모델 · 닫힌 부품만 · 모델당 최대 3 개 · 100 개(씨앗 0)
- 부품마다 점 4 번 + 그림 4 번(무작위 표집 · temperature 1) → 실행(60 초 제한) → IoU(64³)
- 판정: 최고 IoU ≥ 0.8 인 부품 비율 ≥ 10 % → A(써 보고 거르기)로 진행 · 아래면 B(규칙 역산) 먼저
python s0/역산수확.py [개수=100]  →  runs/역산/결과.jsonl · 요약.json · 시트.png"""
import os, sys, glob, json, random, time, numpy as np, trimesh
from concurrent.futures import ProcessPoolExecutor, TimeoutError as TO
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.dirname(H), os.path.join(H, "stub"), H]
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; O = os.path.join(os.path.dirname(H), "runs", "역산v2"); os.makedirs(O, exist_ok=True)   # 10-06 v2: 채점기 교체 후 다시(옛 판 runs/역산 은 −2 의 대부분이 채점 시간 초과)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(H)), "trail11_zerotocad", "s")); from score import occ

def 채점(args):   # 별도 프로세스: 코드 실행 → IoU · torch 를 안 올리려고 s0 를 불러오지 않는다(10-06 일꾼 3 개가 각자 transformers 를 올려 메모리 부족으로 잘림)
    code, gpath = args
    try:
        import cadquery as cq, tempfile
        ns = {"cq": cq}; exec(code, ns)
        obj = ns.get("r") or next((v for v in ns.values() if isinstance(v, cq.Workplane)), None)
        p = os.path.join(tempfile.gettempdir(), "역산_%d.stl" % os.getpid()); cq.exporters.export(obj, p)
    except Exception:
        return -1.0
    try:   # −1 = 코드 실패(모델) · −3 = 채점 실패(자) — 섞지 않는다
        pm = trimesh.load(p); pm.apply_scale(1 / 100.0); gt = trimesh.load(gpath); n = 64
        g = (np.indices((n, n, n)).reshape(3, -1).T + 0.5) / n * 2 - 1
        ia = occ(gt, g) if gt.is_watertight else np.zeros(len(g), bool); ib = occ(pm, g) if pm.is_watertight else np.zeros(len(g), bool)
        u = (ia | ib).sum(); return float((ia & ib).sum() / u) if u else 0.0
    except Exception:
        return -3.0

def 부품들(N):
    rng = random.Random(0); out = []
    for d in sorted(glob.glob(R + "*/")):
        if os.path.basename(d[:-1]).startswith("_"): continue
        fs = [f for f in glob.glob(d + "*") if f.lower().endswith((".stl", ".obj")) and os.path.getsize(f) < 30e6]
        rng.shuffle(fs); k = 0
        for f in fs:
            try: m = trimesh.load(f, force="mesh")
            except Exception: continue
            if len(m.faces) < 12 or not m.is_watertight: continue
            out.append(f); k += 1
            if k == 3: break
    rng.shuffle(out); return out[:N]

if __name__ == "__main__":
    import torch
    from transformers import AutoProcessor
    from cadrille import Cadrille, collate
    import s0 as S
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    L_ = os.path.join(os.path.dirname(O), "역산", "부품목록.json")   # 같은 부품 50
    fs = json.load(open(L_, encoding="utf-8")) if os.path.exists(L_) else 부품들(N)
    json.dump(fs, open(L_, "w", encoding="utf-8"), ensure_ascii=False); fs = fs[:N]; print("부품", len(fs), flush=True)
    W = os.path.join(os.path.dirname(H), "weights")
    model = Cadrille.from_pretrained(os.path.join(W, "cadrille"), torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map="cuda")
    proc = AutoProcessor.from_pretrained(os.path.join(W, "qwen2vl2b"), min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28, padding_side="left")
    done = {json.loads(l)["부품"] for l in open(O + "/결과.jsonl", encoding="utf-8")} if os.path.exists(O + "/결과.jsonl") else set()
    pool = ProcessPoolExecutor(1); t0 = time.time()
    for i, f in enumerate(fs):
        name = os.path.relpath(f, R).replace("\\", "/")
        if name in done: continue
        if time.time() - t0 > float(os.environ.get("STOPAFTER", "1e9")): print("시간 끝 · 이어서 다시 부르면 됨", flush=True); break   # 포그라운드 조각(백그라운드는 메모리 부족 때 잘림)
        gt = S.unit(trimesh.load(f, force="mesh")); g2 = gt.copy(); g2.apply_translation([-0.5] * 3); g2.apply_scale(2.0)
        gp = os.path.join(O, "_gt%d.stl" % (i % 8)); g2.export(gp)
        codes = []
        for mode in ("pc", "img"):
            it = S.item_pc(gt) if mode == "pc" else S.item_img(gt)[0]
            b = collate([dict(it, file_name=name)] * (4 if mode == "pc" else 2), processor=proc, n_points=256, eval=True)
            with torch.no_grad():
                out = model.generate(input_ids=b["input_ids"].cuda(), attention_mask=b["attention_mask"].cuda(), point_clouds=b["point_clouds"].cuda(), is_pc=b["is_pc"].cuda(), is_img=b["is_img"].cuda(),
                                     pixel_values_videos=b["pixel_values_videos"].cuda() if b.get("pixel_values_videos") is not None else None,
                                     video_grid_thw=b["video_grid_thw"].cuda() if b.get("video_grid_thw") is not None else None,
                                     max_new_tokens=768, do_sample=True, temperature=1.0, top_p=0.95)
            codes += [(mode, c) for c in proc.batch_decode(out[:, b["input_ids"].shape[1]:], skip_special_tokens=True)]
        ious = []
        for _, c in codes:   # 하나씩 · 60 초 넘으면 일꾼을 죽이고 새로(앞선 판은 멈춘 일꾼 때문에 뒤 코드까지 취소돼 −2 로 셌다)
            fu = pool.submit(채점, (c, gp))
            try: ious.append(round(fu.result(timeout=float(os.environ.get("CODET", "20"))), 3))
            except Exception:
                ious.append(-2.0)
                for p in list(getattr(pool, "_processes", {}).values()): p.kill()
                pool.shutdown(wait=False, cancel_futures=True); pool = ProcessPoolExecutor(1)
        k = int(np.argmax(ious))
        rec = {"부품": name, "면": int(len(gt.faces)), "IoU": ious, "최고": max(ious), "최고모드": codes[k][0], "코드": codes[k][1], "코드들": codes}
        open(O + "/결과.jsonl", "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(i, name[:40], "최고", rec["최고"], rec["최고모드"], "%.0f초" % (time.time() - t0), flush=True)
    R_ = [json.loads(l) for l in open(O + "/결과.jsonl", encoding="utf-8")]; b_ = np.array([r["최고"] for r in R_])
    요약 = {"부품": len(R_), "IoU≥0.8": int((b_ >= 0.8).sum()), "비율": round(float((b_ >= 0.8).mean()), 3), "IoU≥0.6": int((b_ >= 0.6).sum()), "중앙": round(float(np.median(b_)), 3),
           "실행실패율": round(float(np.mean([v < 0 for r in R_ for v in r["IoU"]])), 3),
           "모드별≥0.8": {m: int(sum(1 for r in R_ if r["최고"] >= 0.8 and r["최고모드"] == m)) for m in ("pc", "img")}, "판정": "A 진행" if (b_ >= 0.8).mean() >= 0.1 else "B 먼저"}
    json.dump(요약, open(O + "/요약.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(요약)
