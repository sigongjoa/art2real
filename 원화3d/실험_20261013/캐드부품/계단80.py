# 판정기준80 자 — 기울기 오차: 만든 메시 · 정답 메시를 여섯 방향 같은 광선으로 쏜 깊이 지도에서 유한 차분 법선을 맞댐(정답 = 0 · 1 판 깊이 고주파 자는 감사 실패) · 10-18
# 사용(venv · ART_MEM_GB=8): 계단80.py → 곡면79 메시(20 부품 · 여섯 팔)를 다시 재서 결과판정80.json
import sys, json, numpy as np
from multiprocessing import Pool
sys.path.append("G:/art2real/원화3d/실험_20261013/구멍")
O = "G:/art2real/out/설명/캐드부품/"; 예측 = __import__("os").environ.get("PRED", "판0"); D = O + ("곡면79/" if 예측 == "판0" else "곡면79_%s/" % 예측) if not __import__("os").environ.get("SET") else O + "곡면79_%s/" % __import__("os").environ["SET"]; 칸 = 1.1 / 48; 팔들 = ["정답", "칸32", "연속정답", "단32장", "단32맞춤", "판0칸", "판0맞춤"]
def 깊이들(v, f):
    import 여섯방향 as S6; return S6.깊이지도(v, f)   # {방향: 지역 w 첫 맞음 · nan}
def 계단(만, 정):   # 2 판 자 → [기울기 오차 °, 10° 넘는 몫, 깊이 오차 칸, 겉 어긋남 몫] · 같은 128² 깊이 지도의 유한 차분 법선끼리(삼각형 모양 안 탐)
    import cv2; px = 1.1 / 128; 각, 몫, 오, 어 = [], [], [], []
    def 법(d):
        gy, gx = np.gradient(np.nan_to_num(d, nan=0.), px); n = np.stack([-gx, -gy, np.ones_like(gx)], -1); return n / np.linalg.norm(n, axis=-1, keepdims=True)
    for d in 정:
        a, b = 만[d], 정[d]; ha, hb = np.isfinite(a), np.isfinite(b); 둘 = ha & hb; e = np.where(둘, a - b, 0.) / 칸
        좋 = cv2.erode((둘 & (np.abs(e) <= 1)).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0; bb = np.nan_to_num(b, nan=-9).astype(np.float32); K = np.ones((5, 5), np.uint8)
        좋 &= ~((cv2.dilate(bb, K) - cv2.erode(bb, K)) > .03); 어.append((ha ^ hb).sum() / max((ha | hb).sum(), 1))
        if 둘.any(): 오.append(np.abs(e)[둘].mean())
        if 좋.sum() < 20: continue
        t = np.degrees(np.arccos(np.clip((법(a) * 법(b)).sum(-1), -1, 1)))[좋]; 각.append(t.mean()); 몫.append((t > 10).mean())
    m = lambda x: float(np.mean(x)) if x else np.nan; return [m(각), m(몫), m(오), m(어)]
def 하나(k):
    import 짓기 as J; L = json.load(open(O + "목록.json", encoding="utf-8")); 시 = np.load(O + "데이터.npz")["시험"]; te = np.nonzero(시)[0]; 예부 = te[json.load(open(O + "범위46.json"))]
    gv, gf, _ = J.정규메시(L[예부[k]]); 정 = 깊이들(gv, gf); out = {}
    for 팔 in 팔들:
        if 팔 == "정답": out[팔] = 계단(정, 정); continue
        try: z = np.load(D + "%s_%d.npz" % (팔, k)); out[팔] = 계단(깊이들(z["v"], z["f"]), 정)
        except FileNotFoundError: out[팔] = [np.nan] * 3
    print(k, {a: [round(x, 3) for x in b] for a, b in out.items()}, flush=True); return k, out
if __name__ == "__main__":
    r79 = json.load(open(D + "결과.json", encoding="utf-8")); ks = r79["요약"]["부품"]
    with Pool(4) as pool: R = dict(pool.map(하나, ks))
    평 = {팔: [round(float(np.nanmean([R[k][팔][j] for k in ks])), 4) for j in range(4)] for 팔 in 팔들}
    결 = {"부품": ks, "팔별 [기울기 오차 °, 10° 넘는 몫, 깊이 오차 칸, 겉 어긋남 몫]": 평}
    결["감사"] = {"정답 ≤ 0.05°": bool(평["정답"][0] <= .05), "연속정답 / 칸32 (10° 몫 · 문턱 0.3 · 못 넘으면 잠정)": round(평["연속정답"][1] / 평["칸32"][1], 3)}
    결["판정(잠정)"] = {"(가) 천장": bool(평["단32맞춤"][1] <= 평["칸32"][1] * .7 and 평["단32맞춤"][2] <= 평["칸32"][2] + .05),
                "(가) 실제": bool(평["판0맞춤"][1] <= 평["판0칸"][1] * .7 and 평["판0맞춤"][2] <= 평["판0칸"][2] + .05)}
    결["부품별"] = {str(k): R[k] for k in ks}
    json.dump(결, open("결과판정80%s.json" % ("" if 예측 == "판0" and not __import__("os").environ.get("SET") else "_" + __import__("os").environ.get("SET", 예측)), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps({a: b for a, b in 결.items() if a != "부품별"}, ensure_ascii=False, indent=1))
    assert 결["감사"]["정답 ≤ 0.05°"], "자 감사 실패 — 정답이 0 이 아님"
