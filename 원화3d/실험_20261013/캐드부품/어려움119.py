# 판정기준119 — 어려운 입력(생성기 어려운 부품 · 실제 CAD · 피규어 부품)을 그림 한 장 → 라이브러리 찾기(Gemma) → 시점 맞추기 → CAD 코드 · 10-20
# 사용: (cadrille venv · ART_MEM_GB=10) 어려움119.py 짓기 → (gemma venv) 어려움119.py 찾기 → (cadrille) 어려움119.py 고르기 → out/설명/캐드부품/어려움119/
import sys, os, json, glob, numpy as np
D = "G:/art2real/out/설명/캐드부품/어려움119/"; os.makedirs(D + "렌더", exist_ok=True)
L = 1000; K = 8
def 저장(p, img):
    import cv2; cv2.imencode(".png", img[..., ::-1])[1].tofile(p)
def 읽(p):
    import cv2; return cv2.imdecode(np.fromfile(p, np.uint8), 1)[..., ::-1].copy()
def _라이브러리(i):
    import 설계116 as S, 데이터117 as Q
    s = S.무작위(np.random.default_rng(10000 + i))
    try:
        w = S.짓기(s); assert w.val().isValid(); m, *_ = S.메시(w); 저장(D + f"렌더/L{i:04d}.png", Q.렌더(m)[0]); return {"이름": f"L{i:04d}", "코드": Q.코드(s), "글": Q.글(s), "종류": s["바탕"]["종류"]}
    except Exception: return None
def 어려운사양(rng):
    import 설계116 as S
    while True:
        s = S.무작위(rng); 특 = [f for f in s["특징"] if f["종류"] != "필렛"]
        if len(특) >= 2 or s["기울임"]: return s
def 짓기():
    import trimesh, 설계116 as S, 데이터117 as Q
    from multiprocessing import Pool
    with Pool(6) as p: 라 = [r for r in p.map(_라이브러리, range(L)) if r]
    입 = []; rng = np.random.default_rng(119)
    while len([x for x in 입 if x["무리"] == "G1"]) < 20:
        s = 어려운사양(rng)
        try: w = S.짓기(s); assert w.val().isValid(); m, *_ = S.메시(w)
        except Exception: continue
        n = f"G1_{len(입):02d}"; 저장(D + f"렌더/{n}.png", Q.렌더(m, 155, 25)[0]); 입.append({"이름": n, "무리": "G1", "코드": Q.코드(s), "종류": s["바탕"]["종류"]})
    파 = sorted(glob.glob("G:/art2real/원화3d/out/레퍼런스/CAD조립/parts/*/*.stl")); rng.shuffle(파); k = 0
    for p in 파:
        if k >= 20: break
        try: m = trimesh.load(p, force="mesh")
        except Exception: continue
        if len(m.faces) < 3000 or m.extents.min() < .08 * m.extents.max(): continue   # 판 · 막대는 뺌
        n = f"G2_{k:02d}"; 저장(D + f"렌더/{n}.png", Q.렌더(m, 155, 25)[0]); 입.append({"이름": n, "무리": "G2", "출처": os.path.relpath(p, "G:/art2real/원화3d/out/레퍼런스/CAD조립/parts"), "면": len(m.faces)}); k += 1
    R3 = "G:/art2real/원화3d/out/레퍼런스/"; 모양 = {"렉스": "G:/art2real/out/설명/캐드부품/어려움102/렉스.stl", "오메가몬머리": R3 + "오메가몬_pomettini/obj_21_Head_fixed.stl", "오메가몬상체": R3 + "오메가몬_pomettini/obj_11_BodyUpper_fixed.stl",
        "거미다리": R3 + "사람분할/1081883_D13SpiderWalkerMech/leg-4x.stl", "부엉이발": R3 + "사람분할/1033970_D13Owl/owl-armor-foot-x2.stl"}   # 어려움102 와 같은 다섯(렉스는 줄인 stl)
    for 이름, q in 모양.items():
        m = trimesh.load(q, force="mesh"); n = f"G3_{이름}"; 저장(D + f"렌더/{n}.png", Q.렌더(m, 155, 25)[0]); 입.append({"이름": n, "무리": "G3"})
    json.dump({"라이브러리": 라, "입력": 입}, open(D + "색인.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0); print("라이브러리", len(라), "입력", len(입))
def 찾기():
    from sentence_transformers import SentenceTransformer
    import torch
    색 = json.load(open(D + "색인.json", encoding="utf-8")); m = SentenceTransformer("google/embeddinggemma-2", device="cuda", model_kwargs={"torch_dtype": torch.bfloat16})
    e = lambda n: np.ravel(m.encode({"text": "<|image|>", "image": [D + f"렌더/{n}.png"]}, normalize_embeddings=True))
    라 = np.stack([e(r["이름"]) for r in 색["라이브러리"]]); out = {}
    for r in 색["입력"]: s = 라 @ e(r["이름"]); out[r["이름"]] = [int(j) for j in np.argsort(-s)[:K]]
    json.dump(out, open(D + "찾기.json", "w"), indent=0); print("찾기", len(out))
def 고르기():
    import 설계116 as S, 데이터117 as Q, 회전118 as R
    색 = json.load(open(D + "색인.json", encoding="utf-8")); 찾 = json.load(open(D + "찾기.json")); 라 = 색["라이브러리"]; rng = np.random.default_rng(7); 결 = []
    for r in 색["입력"]:
        입 = 읽(D + f"렌더/{r['이름']}.png"); 줄 = {"이름": r["이름"], "무리": r["무리"]}
        for 판, 후 in (("찾기", 찾[r["이름"]]), ("대조", [int(j) for j in rng.choice(len(라), K, replace=False)])):
            점 = []
            for j in 후:
                m, *_ = S.메시(S.짓기(json.loads(라[j]["코드"]))); sc, a, e, iou = R.맞추기(m, 입); 점.append((sc, iou, a, e, j))
            sc, iou, a, e, j = max(점); 저장(D + f"렌더/{r['이름']}_{판}.png", Q.렌더(S.메시(S.짓기(json.loads(라[j]["코드"])))[0], a, e)[0])
            줄[판] = {"코드": 라[j]["이름"], "종류": 라[j]["종류"], "글": 라[j]["글"], "점수": round(sc, 3), "IoU": round(iou, 3), "시점": [a, e]}
        if r["무리"] == "G1": 줄["정답 종류"] = r["종류"]
        결.append(줄); print(r["이름"], 줄["찾기"]["종류"], 줄["찾기"]["IoU"], "대조", 줄["대조"]["IoU"], flush=True)
    중 = lambda g, 판: float(np.median([x[판]["IoU"] for x in 결 if x["무리"] == g]))
    요 = {"G1 종류 맞음": float(np.mean([x["찾기"]["종류"] == x["정답 종류"] for x in 결 if x["무리"] == "G1"])), "G1 종류 맞음(대조)": float(np.mean([x["대조"]["종류"] == x["정답 종류"] for x in 결 if x["무리"] == "G1"])),
         **{f"{g} IoU 중앙({판})": 중(g, 판) for g in ("G1", "G2", "G3") for 판 in ("찾기", "대조")}}
    json.dump({"요약": 요, "부품": 결}, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(요, ensure_ascii=False, indent=1))
if __name__ == "__main__": {"짓기": 짓기, "찾기": 찾기, "고르기": 고르기}[sys.argv[1]]()
