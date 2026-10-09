# -*- coding: utf-8 -*-
"""실물0 — 사전0 과 같은 사람 부품 36 개: 렌더 → 얼린 인코더 → 조각2 디코더 → 실물 윤곽에 다듬기 → 모서리 F1 · 그림
python runs/실물0/실물.py [box]   (box = 대조: 상자 하나에서 출발)"""
import os, sys, json, glob, time, numpy as np, torch, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(R, "조각0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub"), T0]
os.environ.setdefault("N3", "48")
from 조각 import 이름, 점유, 격자, 보기, 모서리, 정답칸
from 학습 import 디코더, 손실, K, N3
from 평가 import 메시
RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"; BOX = "box" in sys.argv[1:]
O = os.path.join(H, "대조_상자" if BOX else "디코더"); os.makedirs(O, exist_ok=True)
부품 = [r["부품"] for i in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % i), encoding="utf-8"))]

def 단위(m):   # 긴 변 1 · 가운데 0.5 (합성과 같은 규약)
    m = m.copy(); lo, hi = m.bounds; m.apply_translation(-(lo + hi) / 2); m.apply_scale(1.0 / (hi - lo).max()); m.apply_translation([.5] * 3); return m

def 점유격자(m, n):
    g = 격자(n, "cpu").numpy()
    from 모양자 import _occ   # 10-09: trimesh.contains 11 만 점 한 번에 → 66 GB(10-06 과 같은 함정) · open3d 광선 점유로
    return _occ(m, g).astype(np.float32)

if __name__ == "__main__":
    dev = "cuda"; from s0 import item_img
    from transformers import AutoConfig, AutoProcessor
    from transformers.models.qwen2_vl.modeling_qwen2_vl import Qwen2VisionTransformerPretrainedModel
    from safetensors import safe_open
    from cadrille import collate
    W = os.path.join(T0, "weights"); cfg = AutoConfig.from_pretrained(os.path.join(W, "cadrille")).vision_config; cfg._attn_implementation = "sdpa"
    enc = Qwen2VisionTransformerPretrainedModel(cfg)
    with safe_open(os.path.join(W, "cadrille", "model.safetensors"), "pt") as f: enc.load_state_dict({k[7:]: f.get_tensor(k) for k in f.keys() if k.startswith("visual.")}, strict=True)
    enc = enc.to(dev, torch.bfloat16).eval()
    proc = AutoProcessor.from_pretrained(os.path.join(W, "qwen2vl2b"), min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28, padding_side="left")
    dec = 디코더().to(dev); dec.load_state_dict(torch.load(os.path.join(R, "조각2", "디코더.pt"))); dec.eval(); g = 격자(N3, dev)[None]
    from 모양자 import 재기
    결과 = []; t0 = time.time()
    a_, b_ = map(int, os.environ.get("RANGE", "0-36").split("-"))
    for n_, p in list(enumerate(부품))[a_:b_]:
        if os.path.exists(os.path.join(O, "%02d_결과.json" % n_)): continue
        m = 단위(trimesh.load(RR + p, force="mesh")); _, img = item_img(m); img.save(os.path.join(O, "%02d_입력.png" % n_))
        with torch.no_grad():
            x = collate([{"video": [img], "description": "Generate cadquery code", "file_name": ""}], processor=proc, n_points=256, eval=True)
            tok = enc(x["pixel_values_videos"].to(dev, torch.bfloat16), grid_thw=x["video_grid_thw"].to(dev)).float()[None]
            lg, c, s = dec(tok); P = torch.nn.functional.one_hot(lg.argmax(-1), len(이름)).float()
            if BOX:
                lo, hi = m.bounds; P, c, s = map(lambda t: t[None].to(dev), 정답칸([("상자", ((lo + hi) / 2).tolist(), (hi - lo).tolist())], K))
            occ = torch.from_numpy(점유격자(m, N3)).to(dev)[None]; Sil, D = 보기(occ, N3); Y = [Sil, D, 모서리(D)]
        c, s = c.clone().requires_grad_(True), s.clone().requires_grad_(True); opt = torch.optim.Adam([c, s], 3e-3)
        for k in range(200):
            tau = .03 + (.005 - .03) * k / 199; Sl, Dp = 보기(점유(g, P, c, s, tau), N3)
            add = P[..., 1:6].sum(-1); out = (torch.relu(c + s / 2 - 1.05) + torch.relu(-0.05 - (c - s / 2))).sum(-1)
            loss = 손실((Sl, Dp, 모서리(Dp)), Y) + 2 * (add * out).mean(); opt.zero_grad(); loss.backward(); opt.step()
            with torch.no_grad(): s.clamp_(min=0.005)
        t_ = P.argmax(-1)[0]; 예측 = [(이름[int(t_[q])], c[0, q].tolist(), s[0, q].tolist()) for q in range(K) if int(t_[q]) != 0]
        gt = m.copy(); gt.apply_translation([-.5] * 3); gt.apply_scale(2.0)
        try: pm = 메시(예측); r = 재기(pm, gt); pm.export(os.path.join(O, "%02d_예측.stl" % n_))
        except Exception as e: r = {"edge_f1": 0.0, "iou": 0.0}; print("못 지음", n_, e)
        결과.append({"부품": p, "edge_f1": r["edge_f1"], "iou": r["iou"], "조각": [t for t, _, _ in 예측]}); print(n_, p[-40:], r["edge_f1"], "%.0f 초" % (time.time() - t0), flush=True)
        json.dump(예측, open(os.path.join(O, "%02d_예측.json" % n_), "w", encoding="utf-8"), ensure_ascii=False); json.dump(결과[-1], open(os.path.join(O, "%02d_결과.json" % n_), "w", encoding="utf-8"), ensure_ascii=False)
    결과 = [json.load(open(q, encoding="utf-8")) for q in sorted(glob.glob(os.path.join(O, "*_결과.json")))]
    json.dump(결과, open(os.path.join(O, "결과.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(len(결과), "자 통과", sum(r["edge_f1"] >= .42 for r in 결과), "/ 36 · 모서리 중앙", float(np.median([r["edge_f1"] for r in 결과])))
