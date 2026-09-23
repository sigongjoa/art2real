# -*- coding: utf-8 -*-
"""판 구조 논문의 숫자를 모은다 (2026-09-23).

    python 모으기.py [--개수 5]     못 끝낸 사례를 개수만큼 이어서 잰다 -> 진행.jsonl
    python 모으기.py --정리          진행.jsonl -> 판정.json · 장별.csv

무거워서 한 번에 다 못 돈다. 사례마다 줄 하나를 붙이고 다시 부르면 이어서 한다.
"""
import argparse, json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np, trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260915", r"G:\art2real\원화3d\실험_20260921",
                r"G:\art2real\원화3d\실험_20260922", r"G:\art2real\원화3d\실험_20260923"]
import hull as H, 정답 as JD, 부품분할 as BB, 도면벤치_천장 as DC
import 지표 as Z, 평면조각 as PJ, 면합치기 as M, 생성3D as G3

생성 = os.path.join(H.OUT, "생성3D", "triposg")
전고mm = 150.0
진행 = os.path.join(HERE, "진행.jsonl")
사례들 = sorted(f[:-4] for f in os.listdir(생성) if f.endswith(".glb"))


def 한사례(c):
    raw, masks, bs, p = BB.판(c)
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    ux, uy, z = [np.asarray(a) for a in ax]
    O = g > 0
    tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
    A, o = JD.grid(tm, 봉합=1)
    T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
    원 = Z.메시로(O, (ux, uy, z))
    합, 거리 = M.합치기(원, 정리=0.93)
    대, _ = M.다듬기(원, 거리)
    gm = trimesh.load(os.path.join(생성, c + ".glb"), force="mesh")
    am = G3.art_masks(c)
    _, V, yaw, mir = G3.orient(gm.vertices, am)
    tr = trimesh.Trimesh(G3.fit_to_art(V, am), np.asarray(gm.faces), process=False)
    배율 = 전고mm / max(tm.extents[2], 1e-9)
    줄 = {"case": c, "움직인거리": round(float(거리), 5)}
    for 이름, m in (("타원", 원), ("합치기", 합), ("라플라시안", 대), ("TripoSG", tr), ("정답", tm)):
        평, _, _ = PJ.재기(m, 전체=10)       # 평면 제약 있는 자
        국, _, _ = PJ.재기(m)                # 이웃 각만 보는 자 (깨진 자 · 5.2 절)
        G = M.격자로(m, ux, uy, z)
        줄[이름] = {"조각": 평["조각 수"], "큰판": 평["1% 이상이 덮는 몫"],
                  "조각_국소": 국["조각 수"], "큰판_국소": 국["1% 이상이 덮는 몫"],
                  "iou": round(M.iou(G, T), 4),
                  "실루엣": round(float(np.mean([M.iou(G.any(a), O.any(a)) for a in (0, 1, 2)])), 4),
                  "챔퍼": round(Z.챔퍼(m, tm, 배율)[0], 3),
                  "표면각": round(Z.각(m)[0], 3), "면": int(len(m.faces))}
    return 줄


def 정리():
    줄들 = [json.loads(l) for l in open(진행, encoding="utf-8")]
    이름 = ("타원", "합치기", "라플라시안", "TripoSG", "정답")
    칸 = ("조각", "큰판", "조각_국소", "큰판_국소", "iou", "실루엣", "챔퍼", "표면각", "면")
    중 = lambda n, k: float(np.median([r[n][k] for r in 줄들]))
    판 = {"판": "판 구조 · 실물28 · 판본 5 (2026-09-23)", "n": len(줄들), "목표n": len(사례들),
         "빠진장": [c for c in 사례들 if c not in {r["case"] for r in 줄들}],
         "중앙": {n: {k: round(중(n, k), 4 if k in ("큰판", "큰판_국소", "iou", "실루엣") else 2) for k in 칸} for n in 이름}}
    # 사례 단위 승패 — 중앙값 하나로 가리지 않는다
    판["승패"] = {"TripoSG 대 타원 iou": sum(r["TripoSG"]["iou"] > r["타원"]["iou"] for r in 줄들),
                "TripoSG 대 타원 챔퍼": sum(r["TripoSG"]["챔퍼"] < r["타원"]["챔퍼"] for r in 줄들),
                "합치기 대 타원 큰판": sum(r["합치기"]["큰판"] > r["타원"]["큰판"] for r in 줄들),
                "합치기 대 라플라시안 큰판": sum(r["합치기"]["큰판"] > r["라플라시안"]["큰판"] for r in 줄들),
                "라플라시안이 국소 자에서 1 위": sum(
                    r["라플라시안"]["큰판_국소"] >= max(r[n]["큰판_국소"] for n in 이름) for r in 줄들),
                "합치기 대 타원 조각": sum(r["합치기"]["조각"] < r["타원"]["조각"] for r in 줄들),
                "합치기 대 라플라시안 조각": sum(r["합치기"]["조각"] < r["라플라시안"]["조각"] for r in 줄들),
                "합치기 큰판이 정답을 넘음": sum(r["합치기"]["큰판"] > r["정답"]["큰판"] for r in 줄들),
                "TripoSG 실루엣이 타원보다 낮음": sum(r["TripoSG"]["실루엣"] < r["타원"]["실루엣"] for r in 줄들)}
    from scipy.stats import binomtest
    판["p"] = {k: round(binomtest(v, len(줄들)).pvalue, 5) for k, v in 판["승패"].items()}
    판["차"] = {k: round(float(np.median([r["합치기"][k] - r["타원"][k] for r in 줄들])), 4)
              for k in ("iou", "실루엣", "챔퍼", "큰판")}
    판["차_라플라시안"] = {k: round(float(np.median([r["합치기"][k] - r["라플라시안"][k] for r in 줄들])), 4)
                    for k in ("iou", "실루엣", "큰판", "조각")}
    json.dump(판, open(os.path.join(HERE, "판정.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, "장별.csv"), "w", encoding="utf-8", newline="") as f:
        f.write("case," + ",".join("%s_%s" % (k, n) for n in 이름 for k in 칸) + "\n")
        for r in sorted(줄들, key=lambda r: r["case"]):
            f.write(r["case"] + "," + ",".join(str(r[n][k]) for n in 이름 for k in 칸) + "\n")
    print("n =", len(줄들), "/", len(사례들), "· 빠진장", 판["빠진장"])
    print(json.dumps(판["중앙"], ensure_ascii=False))
    print(json.dumps(판["승패"], ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--개수", type=int, default=4); ap.add_argument("--정리", action="store_true")
    a = ap.parse_args()
    if a.정리:
        정리(); raise SystemExit
    끝 = set()
    if os.path.exists(진행):
        끝 = {json.loads(l)["case"] for l in open(진행, encoding="utf-8")}
    남 = [c for c in 사례들 if c not in 끝][:a.개수]
    for c in 남:
        t = time.time()
        try:
            줄 = 한사례(c)
        except Exception as e:
            print("  건너뜀", c, type(e).__name__, e, flush=True); continue
        with open(진행, "a", encoding="utf-8") as f:
            f.write(json.dumps(줄, ensure_ascii=False) + "\n")
        print("  %-42s %4.0fs  타원 조각%6d 큰판%.3f | 합치기 조각%6d 큰판%.3f | TripoSG iou%.3f" % (
            c[:42], time.time() - t, 줄["타원"]["조각"], 줄["타원"]["큰판"],
            줄["합치기"]["조각"], 줄["합치기"]["큰판"], 줄["TripoSG"]["iou"]), flush=True)
    print("남은 사례", len([c for c in 사례들 if c not in 끝]) - len(남))
