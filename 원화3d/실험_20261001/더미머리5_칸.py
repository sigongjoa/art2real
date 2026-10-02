# -*- coding: utf-8 -*-
"""더미 5판 준비 — 이름 붙은 선파츠 칸(세면_칸.json)에서 부품 윤곽 · 비율 · 이웃을 가져온다 (10-02 「기준이 없잖아? 분할된 모양에서 가져왔어?」).
지어낸 숫자 없음: 정면 칸 = 부품 앞모습(x, z) · 옆 칸 = 같은 이름 부품의 옆모습(y, z) · 이웃 = 정면 칸끼리 맞닿음.
옆모습은 부품마다 자기 틀에서 정면 높이 범위로 늘인다(컷끼리 위치를 믿지 않는다). 앞뒤 자리(y)는 옆 그림 하나에서만 — 눈 기준 · 눈→턱 길이로 맞춤.
출력: 더미머리5_칸.out.json (단위 = 정면 머리 단위, 뿔 끝 0 · 턱 100)."""
import json, os, numpy as np, cv2
H = os.path.dirname(os.path.abspath(__file__)); D = json.load(open(os.path.join(H, "세면_칸.json"), encoding="utf-8")); V = D["views"]
K = 4  # 래스터 px / 단위
빼기 = {"깃 (머리 아님)"}

def 칸(view, i): return np.array(V[view][str(i)]["poly"], float)
def 마스크(polys, x0, y0, W, Hh):
    m = np.zeros((Hh, W), np.uint8)
    for p in polys: cv2.fillPoly(m, [((p - [x0, y0]) * K).astype(np.int32).reshape(-1, 1, 2)], 1)
    return m
def 윤곽(m, x0, y0, 최소=6.0):
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)); cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in cs:
        if cv2.contourArea(c) / K**2 < 최소: continue
        c = cv2.approxPolyDP(c, 1.5, True).reshape(-1, 2) / K + [x0, y0]; out.append(c.round(2).tolist())
    return out

# 정면 가운데 = 투구 돔 칸 상자 가운데 · 옆 기준 = 눈 가운데 x · 옆 배율 = 정면 눈→턱 / 옆 눈→턱
G = {g["name"]: g["cells"] for g in D["groups"] if g["name"] not in 빼기}
dome = np.vstack([칸("정면", i) for i in G["투구 돔"]["정면"]]); cx = (dome[:, 0].min() + dome[:, 0].max()) / 2
def 가운데(view, ids): return np.vstack([칸(view, i) for i in ids]).mean(0)
eF = 가운데("정면", G["눈"]["정면"]); eS = 가운데("옆", G["눈"]["옆"])
chinF = np.vstack([칸("정면", i) for i in G["미늘3 · 턱"]["정면"]])[:, 1].max(); chinS = np.vstack([칸("옆", i) for i in G["미늘3 · 턱"]["옆"]])[:, 1].max()
sS = (chinF - eF[1]) / (chinS - eS[1])
# 옆 그림의 얼굴 방향: 미늘(부리)이 돔보다 작은 x 면 얼굴이 -x
앞부호 = -1 if 가운데("옆", G["미늘1 (코판)"]["옆"])[0] < 가운데("옆", G["투구 돔"]["옆"])[0] else 1

부품 = []
for 이름, cells in G.items():
    쪽 = {"왼": [], "가운데": [], "오른": []}
    for i in cells["정면"]:
        dx = 칸("정면", i)[:, 0].mean() - cx; 쪽["가운데" if abs(dx) < 4 else ("왼" if dx < 0 else "오른")].append(i)
    side = [칸("옆", i) for i in cells["옆"]]
    if side:
        P = np.vstack(side); x0, y0 = P.min(0) - 2; W, Hh = (np.ceil((P.max(0) - P.min(0) + 4) * K)).astype(int)
        옆윤곽 = max(윤곽(마스크(side, x0, y0, W, Hh), x0, y0, 1.0), key=lambda c: cv2.contourArea(np.array(c, np.float32)))
        sy = np.array(옆윤곽); y_앞뒤 = ((sy[:, 0] - eS[0]) * sS * 앞부호 * -1)  # 세계 y: 앞 = 음수
        t = (sy[:, 1] - sy[:, 1].min()) / max(np.ptp(sy[:, 1]), 1e-6)   # 옆 높이를 0~1 로 · 정면 z범위로 늘인다
        옆 = {"yt": np.c_[y_앞뒤, t].round(3).tolist(), "y범위": [float(y_앞뒤.min()), float(y_앞뒤.max())]}
    else: 옆 = None
    for s, ids in 쪽.items():
        if not ids: continue
        polys = [칸("정면", i) for i in ids]; P = np.vstack(polys); x0, y0 = P.min(0) - 2; W, Hh = (np.ceil((P.max(0) - P.min(0) + 4) * K)).astype(int)
        조각 = 윤곽(마스크(polys, x0, y0, W, Hh), x0, y0)
        if not 조각: continue
        색 = V["정면"][str(ids[0])]["color"]
        부품.append({"이름": 이름, "쪽": s, "칸": ids, "앞윤곽": 조각, "z범위": [float(P[:, 1].min()), float(P[:, 1].max())], "x가운데": cx, "색": 색, "옆": 옆,
                   "_m": (마스크(polys, 0, 0, int(90 * K), int(105 * K)))})
# 이웃: 정면 마스크를 1.5 단위 부풀려 겹치면 이웃 · 뿌리 = 가장 큰 돔 조각 · 넓이 우선 탐색으로 부모
n = len(부품); ker = np.ones((int(3 * K), int(3 * K)), np.uint8); dil = [cv2.dilate(p["_m"], ker) for p in 부품]
닿음 = {(a, b): int((dil[a] & 부품[b]["_m"]).sum()) for a in range(n) for b in range(n) if a != b}
root = max((i for i, p in enumerate(부품) if p["이름"] == "투구 돔"), key=lambda i: 부품[i]["_m"].sum())
부모 = {root: -1}; 줄 = [root]
while 줄:
    a = 줄.pop(0)
    for b in sorted(range(n), key=lambda b: -닿음.get((a, b), 0)):
        if b not in 부모 and 닿음.get((a, b), 0) > 0: 부모[b] = a; 줄.append(b)
for i, p in enumerate(부품):
    p["부모"] = 부모.get(i, root)
    if p["부모"] >= 0:
        both = dil[i] & dil[p["부모"]]; ys, xs = np.nonzero(both) if both.any() else np.nonzero(p["_m"])
        p["붙는자리"] = [float(xs.mean() / K), float(ys.mean() / K)]
    del p["_m"]
json.dump({"부품": 부품, "옆배율": sS, "정면가운데": cx, "외톨이": [부품[i]["이름"] for i in range(n) if i not in 부모]},
          open(os.path.join(H, "더미머리5_칸.out.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(len(부품), "부품 · 옆 배율", round(sS, 3), "· 얼굴 방향", 앞부호, "· 부모 못 찾음", [부품[i]["이름"] for i in range(n) if i not in 부모])
for i, p in enumerate(부품): print(i, p["이름"], p["쪽"], "← ", (부품[p["부모"]]["이름"] + "/" + 부품[p["부모"]]["쪽"]) if p["부모"] >= 0 else "뿌리", "옆" if p["옆"] else "옆없음")
