# 판정기준123 G2 실패 원인 찾기 — A: 생성 시험 40 을 G2 와 같은 STL 경로(중심선 없음)로 · B: G2 를 x · y · z 축을 위로 세워 셋 · 10-21
# 사용: (cadrille) 확인123.py 도면 → (gemma) 확인123.py 임베딩 → (cadrille) 확인123.py 채점 → out/설명/캐드부품/모델123/확인/
import sys, os, json, numpy as np
import 모델123 as T, 모델120 as M
D = T.D + "확인/"; os.makedirs(D, exist_ok=True); 축들 = ("z", "x", "y")
def 세움(m, 축):   # 축을 z 로 돌림
    import trimesh
    m = m.copy()
    if 축 == "x": m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]))
    if 축 == "y": m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    return m
def 일():
    j = json.load(open(T.D + "학습.json", encoding="utf-8")); 입 = {r["이름"]: r for r in json.load(open(M.D119 + "색인.json", encoding="utf-8"))["입력"]}
    A = [(f"A{n}", json.loads(g), None, "z") for n, g in list(zip(j["번호"], j["정답"]))[:40]]
    B = [(f"B{nm}_{a}", None, T.R3 + 입[nm]["출처"].replace("\\", "/"), a) for nm in j["G 이름"] if nm.startswith("G2") for a in 축들]
    return A + B
def 메시(x):
    import 설계116 as S, trimesh
    _, s, stl, a = x
    return S.메시(S.짓기(s))[0] if s else 세움(trimesh.load(stl, force="mesh"), a)
def 도면():
    for x in 일():
        for nm, im in zip(T.뷰, T.도면(m=메시(x))): M.저장(D + f"{x[0]}_{nm}.png", im)
    print("끝")
def 임베딩():
    from sentence_transformers import SentenceTransformer
    import torch
    m = SentenceTransformer("google/embeddinggemma-2", device="cuda", model_kwargs={"torch_dtype": torch.bfloat16}); 이 = [x[0] for x in 일()]
    E = m.encode([{"text": "<|image|>", "image": [D + f"{n}_{v}.png"]} for n in 이 for v in T.뷰], normalize_embeddings=True, batch_size=16)
    np.save(D + "임베딩.npy", np.asarray(E, np.float32).reshape(len(이), -1)); print("끝")
def 채점():
    import torch, torch.nn as nn, 데이터117 as Q, 설계116 as S
    net = nn.Sequential(nn.Linear(2304, 512), nn.GELU(), nn.Dropout(.1), nn.Linear(512, 512), nn.GELU(), nn.Linear(512, 36)); net.load_state_dict(torch.load(T.D + "머리_셋.pt")); net.eval()
    j = json.load(open(T.D + "학습.json", encoding="utf-8")); 원 = dict(zip(j["번호"], j["셋"]["시험"])); E = torch.tensor(np.load(D + "임베딩.npy"))
    with torch.no_grad(): o = net(E).numpy()
    시 = lambda v: float(1 / (1 + np.exp(-v))); 결 = []
    for x, oo in zip(일(), o):
        f = oo[16:32].reshape(2, 8).copy(); f[:, 0] = 1 / (1 + np.exp(-f[:, 0])); p = M.사양(int(np.argmax(oo[:7])), oo[7:16], f, [시(oo[32]), float(oo[33])], [시(oo[34]), float(oo[35])])
        _, sg = Q.렌더(메시(x))
        try: ip, sp = Q.렌더(S.메시(S.짓기(p))[0]); iou = float((sg & sp).sum() / max((sg | sp).sum(), 1)); M.저장(D + f"{x[0]}_예측.png", ip)
        except Exception: iou = 0.
        r = {"이름": x[0], "IoU": round(iou, 4), "종류": p["바탕"]["종류"]}
        if x[0].startswith("A"): r["원래 경로와 같은 종류"] = p["바탕"]["종류"] == 원[int(x[0][1:])]["바탕"]["종류"]; r["정답 종류"] = x[1]["바탕"]["종류"]
        결.append(r); print(r, flush=True)
    A = [r for r in 결 if r["이름"].startswith("A")]; B = [r for r in 결 if r["이름"].startswith("B")]; 부 = sorted({r["이름"][1:-2] for r in B})
    요 = {"A STL 경로 IoU 중앙": float(np.median([r["IoU"] for r in A])), "A 종류 맞음": float(np.mean([r["종류"] == r["정답 종류"] for r in A])),
         **{f"B {a} 위 IoU 중앙": float(np.median([r["IoU"] for r in B if r["이름"].endswith("_" + a)])) for a in 축들},
         "B 축 셋 중 가장 좋은 것 IoU 중앙": float(np.median([max(r["IoU"] for r in B if r["이름"][1:-2] == n) for n in 부]))}
    json.dump({"요약": 요, "부품": 결}, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(요, ensure_ascii=False, indent=1))
if __name__ == "__main__": {"도면": 도면, "임베딩": 임베딩, "채점": 채점}[sys.argv[1]]()
