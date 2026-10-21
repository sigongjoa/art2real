# 123b 에 진짜 복잡한 메시(로봇 · 거미 · 부엉이 · 스트랜드비스트 등) 12 를 넣기 — 3면도 입력 | 정답 | 예측 · 10-21
# 사용: (cadrille) 복잡123b.py 도면 → (gemma) 복잡123b.py 임베딩 → (cadrille) 복잡123b.py 그림 → out/설명/캐드부품/모델123b/확인/복잡실물/
import sys, os, json, numpy as np
os.environ["ART_CL"] = "0"
import 모델123 as T, 모델120 as M
D = T.D + "확인/복잡실물/"; os.makedirs(D, exist_ok=True); P = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
일 = {"메기어렉스": "1712661_Metal_Gear_Solid_Rex/rex-robot.stl", "거미허리": "1081883_D13SpiderWalkerMech/waist-frame-v5.stl", "거미다리": "1081883_D13SpiderWalkerMech/leg-4x.stl",
     "부엉이가슴": "1033970_D13Owl/frame-chest.stl", "부엉이엉덩이": "1033970_D13Owl/frame-hips.stl", "비스트다리": "853015_EasyStrandbeest/beest3-leg.stl", "비스트기어": "853015_EasyStrandbeest/beest3-gear60.stl",
     "애벌레손잡이": "892037_InchwormCaterpillarA/handle_v2.stl", "매드캣몸통": "529454_MWO_Mad_Cat_MKII/MWO_ MadcatmkII_Torso_Opt8 (repaired).stl", "범블비몸": "1304003_G1_Bumblebee_Figure/tfd-bumblebee-conversion-g1_style_body_corestl.stl",
     "로봇머리": "1697069_RobotPoseableForDogg/robot__poseable_head.stl", "거인머리받침": "1000552_GiantArticulated/head-base-electronics.stl"}
def 메시(nm):
    import trimesh
    return trimesh.load(P + 일[nm], force="mesh")
def 도면():
    for nm in 일:
        for v, im in zip(T.뷰, T.도면(m=메시(nm))): M.저장(D + f"{nm}_{v}.png", im)
        print(nm, flush=True)
def 임베딩():
    from sentence_transformers import SentenceTransformer
    import torch
    m = SentenceTransformer("google/embeddinggemma-2", device="cuda", model_kwargs={"torch_dtype": torch.bfloat16})
    E = m.encode([{"text": "<|image|>", "image": [D + f"{n}_{v}.png"]} for n in 일 for v in T.뷰], normalize_embeddings=True, batch_size=12)
    np.save(D + "임베딩.npy", np.asarray(E, np.float32).reshape(len(일), -1)); print("끝")
def 그림():
    import torch, torch.nn as nn, 데이터117 as Q, 설계116 as S
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Malgun Gothic"
    net = nn.Sequential(nn.Linear(2304, 512), nn.GELU(), nn.Dropout(.1), nn.Linear(512, 512), nn.GELU(), nn.Linear(512, 36)); net.load_state_dict(torch.load(T.D + "머리_셋.pt")); net.eval()
    with torch.no_grad(): o = net(torch.tensor(np.load(D + "임베딩.npy"))).numpy()
    시 = lambda v: float(1 / (1 + np.exp(-v))); fig, ax = plt.subplots(6, 10, figsize=(20, 13)); 결 = []
    for t, (nm, oo) in enumerate(zip(일, o)):
        f = oo[16:32].reshape(2, 8).copy(); f[:, 0] = 1 / (1 + np.exp(-f[:, 0])); p = M.사양(int(np.argmax(oo[:7])), oo[7:16], f, [시(oo[32]), float(oo[33])], [시(oo[34]), float(oo[35])])
        pk = np.exp(oo[:7] - oo[:7].max()); pk /= pk.sum(); gi, sg = Q.렌더(메시(nm))
        try: pi, sp = Q.렌더(S.메시(S.짓기(p))[0]); iou = float((sg & sp).sum() / max((sg | sp).sum(), 1))
        except Exception: pi, iou = np.full_like(gi, 255), 0.
        결.append({"이름": nm, "종류": p["바탕"]["종류"], "확신": round(float(pk.max()), 3), "IoU": round(iou, 4), "사양": p})
        for c, im in enumerate([M.읽(D + f"{nm}_{v}.png") for v in T.뷰] + [gi, pi]):
            a = ax[t // 2, (t % 2) * 5 + c]; a.imshow(im); a.set_xticks([]); a.set_yticks([])
            if t < 2: a.set_title(("위", "앞", "옆", "정답", "예측")[c], fontsize=12)
            if c == 3: a.set_xlabel(nm, fontsize=10)
            if c == 4: a.set_xlabel(f"{p['바탕']['종류']} {iou:.2f} · 확신 {pk.max():.2f}", fontsize=10)
        print(결[-1]["이름"], 결[-1]["종류"], 결[-1]["IoU"], 결[-1]["확신"], flush=True)
    fig.suptitle(f"복잡한 실물 12 — 123b 모델 · 3/4 IoU 중앙 {np.median([r['IoU'] for r in 결]):.3f} · 낼 수 있는 모양은 7종류뿐", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, .96)); fig.savefig(D + "복잡실물.png", dpi=75); json.dump(결, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if __name__ == "__main__": {"도면": 도면, "임베딩": 임베딩, "그림": 그림}[sys.argv[1]]()
