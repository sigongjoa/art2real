# 판정기준82 — 학습 없이 판0 의 층 확률을 평균 낸 연속 깊이(기대 깊이)로 깎는다 · 20 부품 · 10-18
# 사용(venv · ART_MEM_GB=8): 기대82.py → out/설명/캐드부품/곡면79_기대/ 메시 · 결과판정82.json
import sys, os, json, numpy as np
from multiprocessing import Pool
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍")
O = "G:/art2real/out/설명/캐드부품/"; D = O + "곡면79_기대/"; N = 128
def 기대(m, a):   # 입력51 한 부품 → (깊이 층 연속 (6, N, N) · nan = 통째, 반올림 층)
    import torch, 고침78 as G8
    x, 껍 = G8.입력(a)
    with torch.no_grad(): p = torch.softmax(m(x), 1)
    통 = p[:, 32] > .5; q = p[:, :32] / p[:, :32].sum(1, keepdim=True).clamp_min(1e-9); E = (q * torch.arange(32, device=q.device).float()[None, :, None, None]).sum(1)
    E = torch.maximum(E, 껍.float()); 통 = 통 | (껍 >= 32); E = torch.where(통, torch.full_like(E, float("nan")), E).cpu().numpy(); 층 = np.where(np.isnan(E), 32, np.clip(np.round(np.nan_to_num(E)), 0, 31)).astype(np.uint8); return E, 층
def 하나(job):
    k, p, E, 층, 반, 선, 그림 = job
    import 곡면79 as Q, 계단80 as T, 짓기 as J, 여섯방향 as S6
    gv, gf, _ = J.정규메시(p); 정 = T.깊이들(gv, gf); u = np.tile(S6.g, (N, 1)); v = -u.T; out = {}
    for 팔, 맞춤 in (("판0기대장", False), ("판0기대맞춤", True)):
        위들 = []
        for j, h in enumerate(반):
            단 = 2 * h / 32; d = E[j] * 단
            if 맞춤: d = np.where(np.isnan(d), np.nan, Q.맞추기(Q.조각(선[j], 층[j]), np.nan_to_num(d), 단, u, v)[0])
            위들.append(h - d)
        mm = Q.장메시(위들, 반)
        if mm is None: out[팔] = [np.nan] * 6; continue
        vv, ff = mm; np.savez_compressed(D + "%s_%d.npz" % (팔, k), v=np.asarray(vv, np.float32), f=np.asarray(ff, np.int32))
        out[팔] = T.계단(T.깊이들(vv, ff), 정) + Q.메시F(vv, ff, gv, gf)[:2]
    print(k, {a: [round(x, 3) for x in b] for a, b in out.items()}, flush=True); return k, out
if __name__ == "__main__":
    import 고침78 as G8
    os.makedirs(D, exist_ok=True); 시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 예부 = te[json.load(open(O + "범위46.json"))]; L = json.load(open(O + "목록.json", encoding="utf-8"))
    ks = json.load(open(O + "곡면79/결과.json", encoding="utf-8"))["요약"]["부품"]; 입 = np.load(O + "입력51.npy", mmap_mode="r"); 반 = np.load(O + "데이터51.npz")["반"]; m = G8.망읽기("판0")
    일 = [(k, L[예부[k]], *기대(m, 입[예부[k]]), 반[예부[k]], np.array(입[예부[k], :, 0]), None) for k in ks]
    with Pool(4, maxtasksperchild=5) as pool: R = dict(pool.map(하나, 일, chunksize=1))
    b80 = json.load(open("결과판정80.json", encoding="utf-8"))["팔별 [기울기 오차 °, 10° 넘는 몫, 깊이 오차 칸, 겉 어긋남 몫]"]["판0맞춤"]; b79 = json.load(open("결과판정79.json", encoding="utf-8"))["팔별 [메시 F 1 칸, 메시 F 반 칸, 법선 오차 °, 15° 넘는 몫, 다시 그린 선 F(참고)]"]["판0맞춤"]
    평 = {팔: [round(float(np.nanmean([R[k][팔][j] for k in ks])), 4) for j in range(6)] for 팔 in ("판0기대장", "판0기대맞춤")}; 평["판0맞춤(대조)"] = b80 + b79[:2]
    결 = {"부품": ks, "팔별 [기울기 오차 °, 10° 넘는 몫, 깊이 오차 칸, 겉 어긋남 몫, 메시 F 1 칸, 반 칸]": 평,
         "판정": {팔: bool(평[팔][1] <= .182 and 평[팔][2] <= .686 and 평[팔][5] >= .769) for 팔 in ("판0기대장", "판0기대맞춤")}, "부품별": {str(k): R[k] for k in ks}}
    json.dump(결, open("결과판정82.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps({a: b for a, b in 결.items() if a != "부품별"}, ensure_ascii=False, indent=1))
