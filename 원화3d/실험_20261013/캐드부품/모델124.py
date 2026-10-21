# 판정기준124 — 복잡한 부품(조립124: 몸 1~6) 12000 으로 학습 · 입력 3면도 셋(123b 와 같은 그림 · 얼린 Gemma) · 머리는 몸 칸 6 개를 냄 · 10-21
# 사용: (cadrille · ART_MEM_GB=10) 모델124.py 짓기 [초] → (gemma) 모델124.py 임베딩 → (cadrille) 모델124.py 학습 → 모델124.py 평가 → out/설명/캐드부품/모델124/
import sys, os, json, time, glob, numpy as np
os.environ.setdefault("ART_CL", "0")
import 모델120 as M, 조립124 as C
D = "G:/art2real/out/설명/캐드부품/모델124/"; NT, NV = 12000, 300; 뷰 = ("위", "앞", "옆"); 배 = 60.
for d in ("도면", "사양", "렌더"): os.makedirs(D + d, exist_ok=True)
D123 = "G:/art2real/out/설명/캐드부품/모델123b/"
def _하나(i):
    import 모델123 as T
    p = D + f"사양/{i:05d}.json"
    if os.path.exists(p): return
    try:
        c = C.무작위(np.random.default_rng(124000 + i)); w = C.짓기(c); assert w.val().isValid(); m = C.메시(w)[0]
        for nm, im in zip(뷰, T.도면(m=m)): M.저장(D + f"도면/{i:05d}_{nm}.png", im)
        json.dump({"i": i, "코드": c, "가운데": [float(x) for x in m.bounds.mean(0)], "크기": float(m.extents.max())}, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception as ex: json.dump({"i": i, "실패": str(ex)[:80]}, open(p, "w", encoding="utf-8"), ensure_ascii=False)
def 짓기(초=540):
    from multiprocessing import Pool
    일 = [i for i in range(NT + NV) if not os.path.exists(D + f"사양/{i:05d}.json")]; print("남음", len(일), flush=True); t0 = time.time()
    with Pool(6) as p:
        for k, _ in enumerate(p.imap_unordered(_하나, 일, chunksize=4)):
            if time.time() - t0 > 초: p.terminate(); print("멈춤", k, flush=True); return
    print("끝")
def 색인():
    rs = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(D + "사양/*.json"))]; return [r for r in rs if "코드" in r]
def 임베딩():   # 이어 하기 · 8 분 넘으면 멈춤 · 이름도 같이 저장(123 의 조각 이름 없음 위험 막기)
    from sentence_transformers import SentenceTransformer
    import torch
    m = SentenceTransformer("google/embeddinggemma-2", device="cuda", model_kwargs={"torch_dtype": torch.bfloat16}); 이 = [f"{r['i']:05d}" for r in 색인()]
    조 = D + "임베딩_조각.npz"; E, 길이름 = (list(np.load(조)["E"]), list(np.load(조)["길"])) if os.path.exists(조) else ([], []); t0 = time.time(); 길 = [f"{n}_{nm}" for n in 이 for nm in 뷰]
    assert 길이름 == 길[:len(길이름)], "조각 순서가 어긋남"
    while len(E) < len(길):
        b = 길[len(E):len(E) + 16]; e = m.encode([{"text": "<|image|>", "image": [D + f"도면/{x}.png"]} for x in b], normalize_embeddings=True, batch_size=16)
        E += list(np.asarray(e, np.float32).reshape(len(b), -1)); 길이름 += b
        if len(E) % 1600 < 16 or len(E) == len(길): np.savez(조, E=np.stack(E), 길=np.array(길이름)); print(len(E), flush=True)
        if time.time() - t0 > 480: np.savez(조, E=np.stack(E), 길=np.array(길이름)); print("멈춤", len(E)); return
    np.savez(D + "임베딩.npz", E=np.stack(E).reshape(len(이), 3, -1), 이름=np.array(이)); print("끝", len(이))
# ── 과녁 ↔ 사양 · 몸 칸 = 있음 1 · 종류 7 · 치수 9 · 축 3 · 자리 3 · 특징 2×8 · 필렛 2 = 41 ──
W = 41
def 부피(s):
    b = s["바탕"]; return b["w"] * b["d"] * b["h"] if b["종류"] == "상자" else 4 * b["r"] ** 2 * b["h"]
def 과녁(r):
    c = r["코드"]; cen = np.array(r["가운데"]); E = r["크기"]; 칸들 = np.zeros((C.K, W), np.float32); 쓰 = np.zeros((C.K, 9), np.float32)
    for t, s in enumerate(sorted(c["몸"], key=lambda s: -부피(s))):
        g = M.과녁({**s, "기울임": 0.}); 칸들[t, 0] = 1; 칸들[t, 1 + g["k"]] = 1; 칸들[t, 8:17] = g["치"] * 배 / E; 쓰[t] = g["칸쓰"]
        칸들[t, 17 + C.축들.index(s["축"])] = 1; 칸들[t, 20:23] = (np.array(s["자리"]) - cen) / E; 칸들[t, 23:39] = g["특"].ravel(); 칸들[t, 39:41] = g["필"]
    return 칸들, 쓰
def 사양(o):   # 머리 출력(K×W) → 조립 사양(부품 크기 60 기준 · 자리 그대로)
    몸들 = []
    for v in o:
        if 1 / (1 + np.exp(-v[0])) < .5: continue
        f = v[23:39].reshape(2, 8).copy(); f[:, 0] = 1 / (1 + np.exp(-f[:, 0]))
        s = M.사양(int(np.argmax(v[1:8])), v[8:17], f, [1 / (1 + np.exp(-v[39])), float(v[40])], [0, 0])
        s["축"] = C.축들[int(np.argmax(v[17:20]))]; s["자리"] = [float(x) * 60 for x in v[20:23]]; 몸들.append(s)
    return {"몸": 몸들}
