# 판정기준85 — 원형 패턴 축 찾기 + 회전 대칭 깎기(축 방향 깊이를 반지름마다 중앙값 · 옆은 도면 회전 몸통) · 10-18
# 사용(venv · ART_MEM_GB=8): 회전85.py → out/설명/캐드부품/회전85/ 결과판정85.json
import sys, os, json, numpy as np
os.environ["PATTERN"] = "1"
from multiprocessing import Pool
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍")
O = "G:/art2real/out/설명/캐드부품/"; D = O + "회전85/"; N = 128
축방 = {0: ("옆", "반옆"), 1: ("앞", "뒤"), 2: ("위", "아래")}
def 대칭지도(층, 반, 방들, 축i, 가, 중심):   # 축 방향 두 깊이 지도를 반지름마다 중앙값 → 지역 w 표면(nan = 통째)
    import 여섯방향 as S6; out = {}
    for d in 방들:
        j = list(S6.방향).index(d); h = 반[j]; 단 = 2 * h / 32; 깊 = np.where(층[j] == 32, 2 * h + .1, 층[j] * 단)
        U, V = np.meshgrid(S6.g, -S6.g); P = np.stack([U, V, np.zeros_like(U)], -1) @ S6.R(*S6.방향[d]).T; ρ = np.hypot(P[..., 가[0]] - 중심[0], P[..., 가[1]] - 중심[1])
        b = np.clip((ρ / S6.칸).astype(int), 0, N); 중앙 = np.full(N + 1, np.nan)
        for i in np.unique(b): 중앙[i] = np.median(깊[b == i])
        s = 중앙[b]; out[d] = np.where(s > 2 * h, np.nan, h - s)
    return out
def 하나(job):
    k, p, 층정, 층판, 반, 선, 그림, 채 = job   # 채 = 방향마다 채운 윤곽(입력51 1 번)
    import 곡면79 as Q, 계단80 as T, 짓기 as J, 여섯방향 as S6, 회전84 as R4
    축, 값 = R4.회전장(*그림)
    if 축 is None: return k, None, 값
    a, 덧, 축i, 가, 중심, r = 축; gv, gf, _ = J.정규메시(p); 정 = T.깊이들(gv, gf); u = np.tile(S6.g, (N, 1)); v = -u.T; out = {}; 방 = list(S6.방향)
    def 맞춤(층):
        위들 = []
        for j, h in enumerate(반):
            단 = 2 * h / 32; d = np.where(층[j] == 32, np.nan, 층[j] * 단); d, _ = Q.맞추기(Q.조각(선[j], 층[j]), np.nan_to_num(d), 단, u, v); 위들.append(h - d)
        return 위들
    def 대칭(층):   # 축 방향 둘 = 대칭 지도 · 나머지 = 깊이 없음(위 끝까지 · 실루엣과 회전 몸통이 정함)
        m = 대칭지도(층, 반, 축방[축i], 축i, 가, 중심); return [m[d] if d in m else np.full((N, N), 반[j] + .5) for j, d in enumerate(방)]
    # 10-18 고침(제 실수): 깊이 지도를 꽉 채우면 실루엣(nan)까지 지워져 톱니가 원통이 됐다 → 방향마다 도면의 채운 윤곽 밖은 nan
    윤 = lambda 위들: [np.where(채[j] > 0, w, np.nan) for j, w in enumerate(위들)]
    for 팔, 위들, 쓰기 in (("판0맞춤", 맞춤(층판), False), ("판0대칭", 윤(대칭(층판)), True), ("단32대칭", 윤(대칭(층정)), True), ("회전만", 윤([np.full((N, N), h + .5) for h in 반]), True)):
        mm = Q.장메시(위들, 반, 덧 if 쓰기 else None)
        if mm is None: out[팔] = [np.nan] * 6; continue
        vv, ff = mm; np.savez_compressed(D + "%s_%d.npz" % (팔, k), v=np.asarray(vv, np.float32), f=np.asarray(ff, np.int32)); out[팔] = T.계단(T.깊이들(vv, ff), 정) + Q.메시F(vv, ff, gv, gf)[:2]
    print(k, a, round(값, 3), {x: [round(y, 3) for y in b] for x, b in out.items()}, flush=True); return k, out, 값
if __name__ == "__main__":
    import 회전84 as R4
    os.makedirs(D, exist_ok=True); 시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 범 = json.load(open(O + "범위46.json")); 예부 = te[범]; L = json.load(open(O + "목록.json", encoding="utf-8"))
    묶 = {"어려움": json.load(open(O + "복잡83.json", encoding="utf-8"))["부품"], "보통": json.load(open(O + "곡면79/결과.json", encoding="utf-8"))["요약"]["부품"]}
    층32 = np.load(O + "층32.npy", mmap_mode="r"); P = np.load(O + "학습69_판0/예측.npy", mmap_mode="r"); 입 = np.load(O + "입력51.npy", mmap_mode="r"); 반 = np.load(O + "데이터51.npz")["반"]
    X = np.load(O + "데이터.npz")["X"]; e = np.load(O + "데이터_앞옆.npz"); F, S = e["F"], e["S"]; 결 = {}; 팔들 = ["판0맞춤", "판0대칭", "단32대칭", "회전만"]; 키 = "팔별 [기울기 오차 °, 10° 넘는 몫, 깊이 오차 칸, 겉 어긋남 몫, 메시 F 1 칸, 반 칸]"
    for 이름, ks in 묶.items():
        일 = [(k, L[예부[k]], np.array(층32[예부[k]]), np.array(P[범[k]]), 반[예부[k]], np.array(입[예부[k], :, 0]), (X[예부[k]], F[예부[k]], S[예부[k]]), np.array(입[예부[k], :, 1])) for k in ks]
        with Pool(4, maxtasksperchild=4) as pool: R = pool.map(하나, 일, chunksize=1)
        잡 = [r for r in R if r[1]]; 평 = {팔: [round(float(np.nanmean([r[1][팔][j] for r in 잡])), 4) for j in range(6)] for 팔 in 팔들} if 잡 else {}
        결[이름] = {"축 잡힌 부품": [r[0] for r in 잡], "대칭 점수": {str(r[0]): round(r[2], 3) for r in R}, 키: 평, "반 칸 F 0.05 넘게 떨어진 부품": int(sum(r[1]["판0대칭"][5] < r[1]["판0맞춤"][5] - .05 for r in 잡)), "부품별": {str(r[0]): r[1] for r in 잡}}
    h = 결["어려움"][키]; n = len(결["어려움"]["축 잡힌 부품"])
    결["판정"] = {"통과": bool(h and h["판0대칭"][5] >= h["판0맞춤"][5] + .03 and h["판0대칭"][1] <= h["판0맞춤"][1]), "망침(1/4 넘게 떨어짐)": bool(결["어려움"]["반 칸 F 0.05 넘게 떨어진 부품"] > n / 4)}
    json.dump(결, open("결과판정85.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for 이름 in 묶: print(이름, 결[이름]["축 잡힌 부품"], json.dumps(결[이름][키], ensure_ascii=False), "떨어짐", 결[이름]["반 칸 F 0.05 넘게 떨어진 부품"])
    print(결["판정"])
