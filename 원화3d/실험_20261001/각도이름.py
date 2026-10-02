# -*- coding: utf-8 -*-
"""여러 각도 칸에 이름 붙이기 (10-02 「다음은 니가 알아서」 → 껍질 여섯을 합치려면 장끼리 짝이 먼저 · 위치는 안 믿으니 이름으로).
정면: 연결그래프 부품(이름 · 원래 선파츠_정면 칸)을 각도데이터 정면 칸에 겹침 다수결로 옮긴다(자동).
2~6: Claude 가 번호 그림(번호_<n>.png)을 보고 정면 이름표에서 골라 붙였다 — 눈으로 판정 · 사람이 고칠 것(아래 표 `?` = 자신 없음).
좌우는 인물 기준이 아니라 정면 그림 기준(오른 = 정면 그림의 오른쪽 = 인물의 왼쪽). 정면에 없는 이름(뒤통수 · 목 깃)은 새로 둔다.
출력 out/오메가몬2/지표/각도데이터/이름.json · 이름_시트.png(같은 이름 = 같은 색)"""
import os, json, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
K = r"G:\art2real\원화3d\out\오메가몬2\지표"; O = os.path.join(K, "각도데이터"); D = r"G:\art2real\원화3d\out\번역\디지몬"
손 = {   # 장: {이름: [칸 번호]}
 "2": {"투구 돔/오른": [1], "뿔/가운데": [2], "이마판/오른": [3], "눈구멍/오른": [4, 10, 11, 18], "눈/오른": [7, 8], "미늘1 (코판)/가운데": [5, 12],
       "차양 · 눈썹 능선/오른?": [6], "미늘2/오른": [14, 15, 16, 19], "마스크 볼판/오른": [17], "미늘3 · 턱/가운데": [20], "볼날개/오른": [21], "안테나": [9], "번개/오른": [13]},
 "3": {"뿔/가운데": [1], "뿔/오른": [7], "투구 돔/오른": [2], "안테나 뿌리 · 잔 조각/오른": [3, 4, 9], "번개/오른": [5], "미늘1 (코판)/왼?": [8], "이마판/왼": [10],
       "차양 · 눈썹 능선/왼": [19], "눈구멍/왼": [22], "눈구멍/오른": [13], "눈/오른": [16, 17, 18, 21, 23], "눈 둘레 테/오른": [15], "마스크 볼판/왼": [6],
       "볼날개/왼": [25, 27], "볼날개/오른": [11, 12, 14], "마스크 볼판/오른": [20, 24], "미늘3 · 턱/오른": [26, 28, 30], "미늘3 · 턱/왼": [29, 31], "미늘2/가운데": [32, 33, 34, 35, 36]},
 "4": {"차양 · 눈썹 능선/오른": [1], "투구 돔/오른": [2], "미늘1 (코판)/가운데": [3, 12], "번개/오른": [4], "눈/오른": [5, 6, 7, 10], "눈구멍/오른": [8], "눈 둘레 테/오른": [9],
       "마스크 볼판/오른": [11], "미늘2/오른": [13, 14, 15], "미늘3 · 턱/가운데": [17, 21, 22], "볼날개/오른": [16, 20, 23], "목 깃": [18, 19, 24, 25]},
 "5": {"뿔/가운데": [1, 2, 9, 10, 12, 13, 16], "이마판/오른?": [14, 15, 17, 20, 23], "안테나": [4, 5, 6], "투구 돔/오른": [3], "번개/오른": [18], "눈구멍/오른": [21, 24],
       "눈/오른": [25, 26, 29], "눈 둘레 테/오른": [19, 22, 28], "미늘1 (코판)/가운데": [27, 40], "미늘2/오른": [34, 37], "마스크 볼판/오른": [11],
       "볼날개/오른?": [30, 31, 32, 33, 35, 36, 38, 39, 41, 42, 43], "목 깃": [44, 45, 46, 47, 48, 49], "안테나 뿌리 · 잔 조각/오른": [7, 8]},
 "6": {"투구 돔(뒤)": [2, 3], "뒤통수": [4], "볼날개 뒤끝/왼?": [6], "볼날개 뒤끝/오른?": [5], "뿔(뒤에서)": [1], "목 깃": [11, 12, 13], "?": [7, 8, 9, 10]},
}
이름 = {}
# 정면 자동
g = json.load(open(os.path.join(K, "연결그래프", "그래프.json"), encoding="utf-8")); L0 = np.load(os.path.join(K, "선파츠_정면.npz"))["라벨"]
z = np.load(os.path.join(O, "1.npz")); L1 = z["라벨"]; L0s = cv2.resize(L0.astype(np.int32).astype(np.float32), (L1.shape[1], L1.shape[0]), interpolation=cv2.INTER_NEAREST).astype(int)
칸이름 = {c: p["이름"] for p in g["부품"] for c in p["칸"]}; 이름["1"] = {}
for i in range(1, L1.max() + 1):
    v = L0s[L1 == i]; v = v[v > 0]
    if v.size == 0: continue
    nm = 칸이름.get(int(np.bincount(v).argmax()), "?"); 이름["1"].setdefault(nm, []).append(i)
이름.update(손)
json.dump(이름, open(os.path.join(O, "이름.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# 같은 이름 = 같은 색(좌우 · ? 떼고 바탕 이름으로)
바탕 = lambda s: s.split("/")[0].replace("?", "").replace("(뒤)", "").replace("(뒤에서)", "").replace(" 뒤끝", "").strip()
모두 = sorted({바탕(n) for v in 이름.values() for n in v});
모두 = [n for n in 모두 if n]   # 「?」만인 칸은 이름 없음
T20 = ["e6194b", "3cb44b", "ffe119", "4363d8", "f58231", "911eb4", "46f0f0", "f032e6", "bcf60c", "fabebe", "008080", "e6beff", "9a6324", "fffac8", "800000", "aaffc3", "808000", "ffd8b1", "000075"]
pal = {n: tuple(int(T20[i][k:k + 2], 16) for k in (4, 2, 0)) for i, n in enumerate(모두)}; pal[""] = (40, 40, 40)
J = json.load(open(os.path.join(O, "각도데이터.json"), encoding="utf-8")); tiles = []
for 장, info in J.items():
    n = 장.split()[0]; z = np.load(os.path.join(O, n + ".npz")); L = z["라벨"]
    im = cv2.imdecode(np.fromfile(os.path.join(D, info["파일"]), np.uint8), 1); big = cv2.resize(im, None, fx=float(z["s"]), fy=float(z["s"]), interpolation=cv2.INTER_CUBIC); ov = big.copy()
    for nm, cs in 이름[n].items():
        mk = np.isin(L, cs); ov[mk] = pal[바탕(nm)]
        if "?" in nm: ov[mk & ((np.indices(L.shape).sum(0) // 6) % 2 == 0)] = (40, 40, 40)   # 자신 없음 = 줄무늬
    a = cv2.addWeighted(big, 0.35, ov, 0.65, 0); m = L > 0; ys, xs = np.nonzero(m); a = a[max(0, ys.min() - 15):ys.max() + 15, max(0, xs.min() - 15):xs.max() + 15]
    tiles.append(cv2.resize(a, (int(a.shape[1] * 330 / a.shape[0]), 330)))
W = 1400; rows, row, x = [], [], 0
for t in tiles:
    if x + t.shape[1] > W: rows.append(row); row, x = [], 0
    row.append(t); x += t.shape[1]
rows.append(row); H = len(rows) * 340 + 70 + 34 * ((len(모두) + 5) // 6); out = Image.new("RGB", (W, H), (20, 20, 24)); d = ImageDraw.Draw(out); f = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 20)
y = 0
for r in rows:
    x = 0
    for t in r: out.paste(Image.fromarray(t[:, :, ::-1]), (x, y)); x += t.shape[1] + 6
    y += 340
for i, nm in enumerate(모두):
    c = pal[nm][::-1]; xx, yy = 10 + (i % 6) * 230, y + 10 + (i // 6) * 34; d.rectangle([xx, yy, xx + 22, yy + 22], fill=c); d.text((xx + 30, yy), nm, font=f, fill=(255, 255, 255))
d.text((10, y + 14 + 34 * ((len(모두) + 5) // 6)), "줄무늬 = 자신 없음(사람 확인) · 회색 = 이름 없음", font=f, fill=(255, 232, 58))
out.save(os.path.join(O, "이름_시트.png")); print({k: len(v) for k, v in 이름.items()}, len(모두))
# 부품마다 주 뷰: 머리 넓이 대비 그 이름 넓이가 가장 큰 장(「?」 포함 · 자신 없음은 표시) — 컷 사이엔 추상, 수치는 주 뷰 하나
넓이 = {}
for 장, info in J.items():
    n = 장.split()[0]; L = np.load(os.path.join(O, n + ".npz"))["라벨"]; tot = (L > 0).sum()
    for nm, cs in 이름[n].items():
        b = 바탕(nm)
        if b: 넓이.setdefault(b, {})[장] = 넓이.get(b, {}).get(장, 0) + round(float(np.isin(L, cs).sum() / tot), 3)
주뷰 = {b: max(v, key=v.get) for b, v in 넓이.items()}
json.dump({"넓이비": 넓이, "주뷰": 주뷰}, open(os.path.join(O, "주뷰.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for b in 모두: print(f"{b:16s} 주뷰 {주뷰[b]:12s} 보이는 장 {len(넓이[b])}")
