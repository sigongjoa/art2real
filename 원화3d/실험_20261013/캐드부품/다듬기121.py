# 판정기준121 — 모델120 예측 코드를 다시 그려 입력 그림에 맞게 치수 다듬기(학습 없음) · 10-21
# 사용(cadrille venv · ART_MEM_GB=10): 다듬기121.py 시작 → 다듬기121.py 돌림 [초=500](이어 하기 · 부품마다 파일) → 다듬기121.py 모음 → out/설명/캐드부품/다듬기121/
import sys, os, json, copy, time, glob, numpy as np
import 모델120 as M
D = "G:/art2real/out/설명/캐드부품/다듬기121/"; os.makedirs(D + "부품", exist_ok=True); os.makedirs(D + "렌더", exist_ok=True)
D119 = M.D119; R3 = "G:/art2real/원화3d/out/레퍼런스/"
G3 = {"렉스": "G:/art2real/out/설명/캐드부품/어려움102/렉스.stl", "오메가몬머리": R3 + "오메가몬_pomettini/obj_21_Head_fixed.stl", "오메가몬상체": R3 + "오메가몬_pomettini/obj_11_BodyUpper_fixed.stl",
      "거미다리": R3 + "사람분할/1081883_D13SpiderWalkerMech/leg-4x.stl", "부엉이발": R3 + "사람분할/1033970_D13Owl/owl-armor-foot-x2.stl"}   # 어려움119 와 같은 다섯
def 시작():   # 머리 다시 돌려 종류 확률 상위 2 · 시작 사양 · 대조② 를 일감 목록으로
    import torch, torch.nn as nn
    z = np.load(M.D + "임베딩.npz"); 색 = json.load(open(M.D + "색인.json", encoding="utf-8")); 입 = json.load(open(D119 + "색인.json", encoding="utf-8"))["입력"]; j = json.load(open(M.D + "학습.json", encoding="utf-8"))
    net = nn.Sequential(nn.Linear(768, 512), nn.GELU(), nn.Dropout(.1), nn.Linear(512, 512), nn.GELU(), nn.Linear(512, 36)); net.load_state_dict(torch.load(M.D + "머리.pt")); net.eval()
    def 후보(e):
        with torch.no_grad(): o = net(torch.tensor(e[None]))[0].numpy()
        p = np.exp(o[:7] - o[:7].max()); p /= p.sum(); f = o[16:32].reshape(2, 8).copy(); f[:, 0] = 1 / (1 + np.exp(-f[:, 0])); 시 = lambda x: float(1 / (1 + np.exp(-x)))
        ks = [int(k) for k in np.argsort(-p)[:2] if p[k] >= .05 or k == np.argmax(p)]
        return [M.사양(k, o[7:16], f, [시(o[32]), float(o[33])], [시(o[34]), float(o[35])]) for k in ks], [round(float(p[k]), 3) for k in ks]
    일 = []
    for r, e in zip(입, z["E119"]):
        s, p = 후보(e); 진 = {"코드": r["코드"]} if r["무리"] == "G1" else {"stl": R3 + "CAD조립/parts/" + r["출처"].replace("\\", "/")} if r["무리"] == "G2" else {"stl": G3[r["이름"][3:]]}
        일.append({"이름": r["이름"], "무리": r["무리"], "그림": D119 + f"렌더/{r['이름']}.png", "방위": 155., "고도": 25., "후보": s, "확률": p, "정답": 진})
    번 = {r["i"]: k for k, r in enumerate(색)}; 대 = j["시험"]["대조"]
    for t, (n, g) in enumerate(list(zip(j["시험"]["번호"], j["시험"]["정답"]))[:40]):
        rng = np.random.default_rng(120000 + n); import 설계116 as S; S.무작위(rng); a, e = float(rng.uniform(0, 360)), float(rng.uniform(15, 35))
        s, p = 후보(z["E"][번[n]]); 일.append({"이름": f"시{n}", "무리": "시험", "그림": M.D + f"렌더/{n:05d}.png", "방위": a, "고도": e, "후보": s, "확률": p, "정답": {"코드": g}, "대조②": 대[t]})
    json.dump(일, open(D + "일감.json", "w", encoding="utf-8"), ensure_ascii=False); print("일감", len(일))
def _메시(s):
    import 설계116 as S
    w = S.짓기(s); assert w.val().isValid(); return S.메시(w)[0]
def 고침(s):   # 생성기 범위로(과녁 → 사양 왕복 · 120 에서 확인)
    g = M.과녁(s); return M.사양(g["k"], g["치"], g["특"], g["필"], g["기"])
def 손잡이(s):   # (경로, 곱셈?) 목록
    b = s["바탕"]; h = [(("바탕", c), True) for c in M.쓰는칸[b["종류"]].split()]
    if s["기울임"]: h.append((("기울임",), False))
    for i, f in enumerate(s["특징"]):
        h += [(("특징", i, "크기"), True)] if f["종류"] == "필렛" else [(("특징", i, "x"), False), (("특징", i, "y"), False), (("특징", i, "크기"), True)]
    return h
def 바꿈(s, 경, 곱, d):
    t = copy.deepcopy(s); o = t
    for k in 경[:-1]: o = o[k]
    o[경[-1]] = o[경[-1]] * (1 + d) if 곱 else o[경[-1]] + d * (40 if 경[0] == "기울임" else .8)
    return 고침(t)
def 다듬기(s, img, 예산=60):
    import 데이터117 as Q, 회전118 as R
    s0, e0 = R.실루엣(img), R.모서리(img); n = [0]
    def 점(t, a, e):
        n[0] += 1
        try: im, sil = Q.렌더(_메시(t), a, e)
        except Exception: return -1.
        return (sil & s0).sum() / max((sil | s0).sum(), 1) * R.F(R.모서리(im), e0)
    try: _, a, e, _ = R.맞추기(_메시(s), img)
    except Exception: return s, -1., (155., 25.)
    best = 점(s, a, e)
    for st in (.25, .1, .04):
        for 경, 곱 in 손잡이(s):
            for d in (st, -st):
                if n[0] >= 예산: break
                t = 바꿈(s, 경, 곱, d); v = 점(t, a, e)
                if v > best: best, s = v, t; break
        try: _, a, e, _ = R.맞추기(_메시(s), img)
        except Exception: pass
    return s, best, (a, e)
def 채점(s, img, 진, a진, e진):   # → 입력 시점 IoU · 찾은 시점 · 다른 시점(+90°) IoU
    import 데이터117 as Q, 회전118 as R, trimesh
    try: m = _메시(s)
    except Exception: return 0., 0., None
    _, a, e, iou = R.맞추기(m, img)
    mt = _메시(json.loads(진["코드"])) if "코드" in 진 else trimesh.load(진["stl"], force="mesh")
    _, sp = Q.렌더(m, (a + 90) % 360, e); _, st = Q.렌더(mt, (a진 + 90) % 360, e진)
    return float(iou), float((sp & st).sum() / max((sp | st).sum(), 1)), (a, e)
def _하나(r):
    p = D + f"부품/{r['이름']}.json"
    if os.path.exists(p): return
    img = M.읽(r["그림"]); a진, e진 = r["방위"], r["고도"]; t0 = time.time()
    판 = [다듬기(s, img) for s in r["후보"]]; s다, v다, _ = max(판, key=lambda x: x[1])
    out = {"이름": r["이름"], "무리": r["무리"], "확률": r["확률"], "120": r["후보"][0], "121": s다, "점수들": [round(x[1], 4) for x in 판]}
    for 키, s in (("120", r["후보"][0]), ("121", s다)): out[키 + " 입력"], out[키 + " 다른"], out[키 + " 시점"] = 채점(s, img, r["정답"], a진, e진)
    if "대조②" in r:
        s3, _, _ = 다듬기(r["대조②"], img); out["③"] = s3; out["③ 입력"], out["③ 다른"], _ = 채점(s3, img, r["정답"], a진, e진)
    out["초"] = round(time.time() - t0, 1); json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False); print(r["이름"], round(out["120 입력"], 3), "→", round(out["121 입력"], 3), "| 다른", round(out["120 다른"], 3), "→", round(out["121 다른"], 3), out["초"], flush=True)
def 돌림(초=500):
    from multiprocessing import Pool
    일 = [r for r in json.load(open(D + "일감.json", encoding="utf-8")) if not os.path.exists(D + f"부품/{r['이름']}.json")]; print("남음", len(일), flush=True); t0 = time.time()
    with Pool(6) as p:
        for _ in p.imap_unordered(_하나, 일):
            if time.time() - t0 > 초: p.terminate(); print("멈춤"); return
def 모음():
    rs = [json.load(open(p, encoding="utf-8")) for p in sorted(glob.glob(D + "부품/*.json"))]; 요 = {}
    for g in ("G1", "G2", "G3", "시험"):
        x = [r for r in rs if r["무리"] == g]; 요[g + " 수"] = len(x)
        for k in ("120 입력", "121 입력", "120 다른", "121 다른", "③ 입력", "③ 다른"):
            if x and k in x[0]: 요[f"{g} {k}"] = round(float(np.median([r[k] for r in x])), 4)
    요["G1 종류(121)"] = None
    입 = {r["이름"]: r for r in json.load(open(D119 + "색인.json", encoding="utf-8"))["입력"]}
    g1 = [r for r in rs if r["무리"] == "G1"]; 요["G1 종류(121)"] = float(np.mean([r["121"]["바탕"]["종류"] == 입[r["이름"]]["종류"] for r in g1])); 요["G1 종류(120)"] = float(np.mean([r["120"]["바탕"]["종류"] == 입[r["이름"]]["종류"] for r in g1]))
    시 = [r for r in rs if r["무리"] == "시험"]; 요["시험 종류 바뀜"] = int(sum(r["120"]["바탕"]["종류"] != r["121"]["바탕"]["종류"] for r in 시 + g1))
    통 = {"G1 입력 ≥ 0.97": 요["G1 121 입력"] >= .97, "G1 다른 > 120": 요["G1 121 다른"] > 요["G1 120 다른"], "시험 다른 > 120": 요["시험 121 다른"] > 요["시험 120 다른"]}
    json.dump({"요약": 요, "통과": 통, "부품": rs}, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(요, ensure_ascii=False, indent=1), 통)
if __name__ == "__main__":
    f = {"시작": 시작, "돌림": 돌림, "모음": 모음}[sys.argv[1]]; f(*[int(a) for a in sys.argv[2:]])
