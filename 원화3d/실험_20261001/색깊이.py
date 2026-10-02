# -*- coding: utf-8 -*-
"""색 + 깊이 = 겹 (10-02 사용자 「depth 정보랑 색상 정보랑 조합하면? 뭔가 보이지 않아?」).
색 = 무슨 겹인가(머리 시작 카드: 검정 = 속머리 · 흰 = 마스크 · 투구 · 파랑 = 눈 · 노랑 = 안테나), 깊이 = 얼마나 앞(먹선 굵게 판 DA V2 · 클수록 가까움).
① 칸마다 색 무리(Lab 거리로 가장 가까운 기준색) + 깊이 중앙 → 층 지도  ② 색끼리 맞닿은 경계에서 어느 쪽이 앞인가(검정은 흰 뒤여야)
출력 out/오메가몬2/지표/원화그림자/색깊이.png · 색깊이.json"""
import os, json, numpy as np, cv2
K = r"G:\art2real\원화3d\out\오메가몬2\지표"; O = os.path.join(K, "원화그림자")
ART = r"G:\art2real\원화3d\out\번역\디지몬\장면\02_역습\yt_172.0_얼굴_정면.jpg"
x0, y0, x1, y1 = json.load(open(os.path.join(O, "그림자.json"), encoding="utf-8"))["자르기"]
L = np.load(os.path.join(K, "선파츠_정면.npz"))["라벨"][y0:y1, x0:x1]; img = cv2.imdecode(np.fromfile(ART, np.uint8), 1)[y0:y1, x0:x1]
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(float); D = np.load(os.path.join(O, "먹선굵게_깊이.npy"))
# 이 원화는 갑주 · 눈 · 그늘이 다 같은 푸른 회색(채도 6~22) → 색은 사실상 밝기 하나로만 갈린다(칸 중앙 L 로 셋)
names = ["검정(속머리)", "그늘 갑주", "밝은 갑주"]
칸 = {}
for n in np.unique(L):
    if n == 0: continue
    m = L == n; Lm = float(np.median(lab[m][:, 0])); c = 0 if Lm < 40 else (1 if Lm < 125 else 2)
    칸[int(n)] = {"색": names[c], "깊이": float(np.median(D[m])), "넓이": int(m.sum()), "L": round(Lm)}
# 층 지도: 칸을 그 깊이로 칠함(빨강 = 가까움)
dv = np.array([v["깊이"] for v in 칸.values()]); lo_, hi_ = np.percentile(dv, 3), np.percentile(dv, 97)
층 = np.full(L.shape, np.nan)
for n, v in 칸.items(): 층[L == n] = v["깊이"]
a = np.clip((np.nan_to_num(층, nan=lo_) - lo_) / (hi_ - lo_), 0, 1); 층색 = cv2.applyColorMap((a * 255).astype(np.uint8), cv2.COLORMAP_JET); 층색[L == 0] = 255
색지도 = np.full(img.shape, 255, np.uint8); 표색 = {"밝은 갑주": (235, 235, 235), "그늘 갑주": (150, 140, 130), "검정(속머리)": (30, 30, 30)}
for n, v in 칸.items(): 색지도[L == n] = 표색[v["색"]]
# 색끼리 맞닿은 경계: 칸 쌍(4 이웃)에서 앞 · 뒤 집계
쌍 = {}
for dy, dx in ((0, 1), (1, 0)):
    p = L[: L.shape[0] - dy, : L.shape[1] - dx]; q = L[dy:, dx:]; ok = (p > 0) & (q > 0) & (p != q)
    for i, j in set(zip(p[ok].tolist(), q[ok].tolist())): 쌍[tuple(sorted((i, j)))] = 1
판정 = {}
for i, j in 쌍:
    ci, cj = 칸[i]["색"], 칸[j]["색"]
    if ci == cj: continue
    key = " vs ".join(sorted((ci, cj))); first = sorted((ci, cj))[0]
    앞 = ci if 칸[i]["깊이"] > 칸[j]["깊이"] else cj
    판정.setdefault(key, [0, 0]); 판정[key][0 if 앞 == first else 1] += 1
요약 = {k: f"{sorted(k.split(' vs '))[0]} 이 앞 {v[0]} / {sorted(k.split(' vs '))[1]} 이 앞 {v[1]}" for k, v in 판정.items()}
색별 = {c: round(float(np.median([v["깊이"] for v in 칸.values() if v["색"] == c])), 1) for c in names if any(v["색"] == c for v in 칸.values())}
s = 2; out = np.hstack([cv2.resize(img, None, fx=s, fy=s), cv2.resize(색지도, None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST), cv2.resize(층색, None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST)])
cv2.imencode(".png", out)[1].tofile(os.path.join(O, "색깊이.png"))
json.dump({"칸": 칸, "색별깊이중앙": 색별, "경계앞뒤": 요약}, open(os.path.join(O, "색깊이.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("색별 깊이 중앙(클수록 가까움):", 색별); [print(" ", v) for v in 요약.values()]
