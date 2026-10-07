# -*- coding: utf-8 -*-
"""역산 수확 → 학습 데이터 (10-07 · 판정은 만들기 전에 고정 — 역산평가.py 머리말)
학습 = 학습 쪽 모델 부품에서 cadrille 가 쓴 코드 중 IoU ≥ 문턱 · 입력 그림 = 사람 부품 렌더(코드 결과가 아니라 실제 입력과 같은 것)
시험 = 학습에 한 번도 안 나온 모델의 부품(모델 단위로 가른다 — 같은 피규어의 다른 부품이 새지 않게)
python s0/역산데이터.py <출력 폴더> [문턱=0.8] [시험 모델 비율=0.25]"""
import os, sys, json, random, hashlib, trimesh
H = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.dirname(H), os.path.join(H, "stub"), H]
import s0 as S
R = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; V2 = os.path.join(os.path.dirname(H), "runs", "역산v2")

if __name__ == "__main__":
    O = sys.argv[1]; TH = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8; FR = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25
    rows = [json.loads(l) for l in open(V2 + "/결과.jsonl", encoding="utf-8")]
    models = sorted({r["부품"].split("/")[0] for r in rows}); rng = random.Random(0); rng.shuffle(models)
    test_models = set(models[:max(1, round(len(models) * FR))])
    tr, te = [r for r in rows if r["부품"].split("/")[0] not in test_models], [r for r in rows if r["부품"].split("/")[0] in test_models]
    os.makedirs(O + "/train", exist_ok=True); n = 0; seen = set(); parts = set()
    for r in tr:
        good = [c for (mode, c), v in zip(r.get("코드들", []), r["IoU"]) if v >= TH]
        if not good: continue
        gt = S.unit(trimesh.load(R + r["부품"], force="mesh")); _, g = S.item_img(gt)
        for c in good:
            h = hashlib.md5(c.encode()).hexdigest()
            if h in seen: continue
            seen.add(h); open("%s/train/%04d.py" % (O, n), "w", encoding="utf-8").write(c); g.save("%s/train/%04d.png" % (O, n)); n += 1; parts.add(r["부품"])
    # 학습 과정 그림용(lora.py 의 시험 폴더): 시험 부품 4 개 · 정답 칸에는 그 부품의 최고 코드(판정에는 안 쓴다 — 판정은 역산평가.py)
    os.makedirs(O + "/show", exist_ok=True)
    for k, r in enumerate(sorted(te, key=lambda r: -r["최고"])[:4]):
        gt = S.unit(trimesh.load(R + r["부품"], force="mesh")); _, g = S.item_img(gt)
        open("%s/show/%04d.py" % (O, k), "w", encoding="utf-8").write(r["코드"]); g.save("%s/show/%04d.png" % (O, k))
    json.dump({"시험부품": [r["부품"] for r in te], "시험모델": sorted(test_models), "문턱": TH}, open(O + "/split.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("모델 %d (시험 %d) · 학습 부품 %d 중 코드 있는 부품 %d · 학습 코드 %d · 시험 부품 %d" % (len(models), len(test_models), len(tr), len(parts), n, len(te)))
