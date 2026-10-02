# -*- coding: utf-8 -*-
"""정면 52칸 → 부품 연결 그래프 초안 (10-02 조사 claudedocs/research_부품연결그래프_20261002.md 권고 · 사용자 「일단은 해보자고」).
위치는 쓰지 않는다 — 한 장(정면) 안의 이웃 · 가림 · 이름만.
- 부품 = 이름 묶음 × 쪽(왼 · 가운데 · 오른, 투구 돔 칸 상자 가운데 기준 ±4 단위)
- 덮음(a 가 b 를 가림): 맞닿은 경계 둘레 반지름 R 원 안에서 덜 차지하는 쪽(볼록한 쪽)이 앞 — 볼록성 가림 단서. |점수| < 문턱이면 「모름」.
- 붙음(a 가 b 표면에 고정): 층 규칙 코어 0 · 큰 판 1 · 장식 2. 장식은 맞닿은 큰 판 중 (경계 길이 × 덮으면 2배)가 가장 큰 것, 큰 판은 코어.
- 좌우 짝: 같은 이름의 왼 · 오른.
출력: out/오메가몬2/지표/연결그래프/{그래프.json, 그래프_원화.png, 그래프_나무.png}. 사람이 그림을 보고 고친다."""
import json, os, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); R0 = os.path.dirname(HERE)
K = os.path.join(R0, "out", "오메가몬2", "지표"); O = os.path.join(K, "연결그래프"); os.makedirs(O, exist_ok=True)
L = np.load(os.path.join(K, "선파츠_정면.npz"))["라벨"]
ART = os.path.join(R0, "out", "번역", "디지몬", "장면", "02_역습", "yt_172.0_얼굴_정면.jpg")
D = json.load(open(os.path.join(HERE, "세면_칸.json"), encoding="utf-8"))
층 = {"투구 돔": 1, "이마판": 1, "마스크 볼판": 1, "볼날개": 1, "눈구멍": 1, "부리 윗판 · 미간": 1,
     "뿔": 2, "번개": 2, "차양 · 눈썹 능선": 2, "눈": 2, "눈 둘레 테": 2, "미늘1 (코판)": 2, "미늘2": 2, "미늘3 · 턱": 2, "안테나 뿌리 · 잔 조각": 2}
R = 12; 문턱 = 0.06

ys, xs = np.nonzero(L > 0); top, bot = ys.min(), ys.max(); k = 100 / (bot - top)   # 머리 단위(뿔 끝 0 · 턱 100)
cell2g = {n: g["name"] for g in D["groups"] for n in g["cells"]["정면"]}
dome = np.isin(L, [n for n, g in cell2g.items() if g == "투구 돔"]); dx_ = np.nonzero(dome)[1]; cx = (dx_.min() + dx_.max()) / 2
def 쪽(n):
    m = np.nonzero(L == n)[1].mean(); d = (m - cx) * k
    return "가운데" if abs(d) < 4 else ("왼" if d < 0 else "오른")
부품 = {}
for n in range(1, L.max() + 1):
    if n not in cell2g or not (L == n).any(): continue
    부품.setdefault(f"{cell2g[n]}/{쪽(n)}", []).append(n)
names = sorted(부품, key=lambda p: (층[p.split("/")[0]], p)); idx = {p: i for i, p in enumerate(names)}
P = np.full(L.shape, -1, int)
for p, cs in 부품.items(): P[np.isin(L, cs)] = idx[p]

# 맞닿음: 두 부품을 2 px 씩 부풀려 겹치는 띠 = 경계(칸은 벽 없이 바로 맞닿는다 · 머리의 96 %를 덮음)
ker = np.ones((5, 5), np.uint8); 경계 = {}
for i in range(len(names)):
    di = cv2.dilate((P == i).astype(np.uint8), ker) > 0
    for j in range(i + 1, len(names)):
        b = di & (cv2.dilate((P == j).astype(np.uint8), ker) > 0)
        if b.sum() >= 8: 경계[(i, j)] = b
# 덮음: 경계 점마다 반지름 R 원 안 i · j 차지 비율 → 덜 차지하는(볼록한) 쪽이 앞
disk = cv2.circle(np.zeros((2 * R + 1, 2 * R + 1), np.uint8), (R, R), R, 1, -1).astype(np.float32)
fi_all = {}
def 비율(i):
    if i not in fi_all: fi_all[i] = cv2.filter2D((P == i).astype(np.float32), -1, disk) / disk.sum()
    return fi_all[i]
덮음 = []
for (i, j), b in 경계.items():
    a, c = 비율(i)[b], 비율(j)[b]; s = float(np.mean((c - a) / np.maximum(a + c, 1e-6)))   # +: i 가 볼록 → i 앞
    덮음.append({"앞": names[i] if s > 0 else names[j], "뒤": names[j] if s > 0 else names[i], "점수": round(abs(s), 3), "확실": abs(s) >= 문턱, "경계px": int(b.sum())})
# 붙음
def 덮나(a, b): return any(e["앞"] == a and e["뒤"] == b and e["확실"] for e in 덮음)
붙음 = []
for p in names:
    lv = 층[p.split("/")[0]]
    if lv == 1: 붙음.append({"자식": p, "부모": "코어", "근거": "큰 판 → 코어"}); continue
    cand = []
    for (i, j), b in 경계.items():
        q = names[j] if names[i] == p else (names[i] if names[j] == p else None)
        if q and 층[q.split("/")[0]] == 1: cand.append((b.sum() * (2 if 덮나(p, q) else 1), q, 덮나(p, q)))
    if cand:
        sc, q, cov = max(cand); 붙음.append({"자식": p, "부모": q, "근거": f"맞닿은 큰 판 중 최대(경계 {int(sc)}{' · 덮음' if cov else ''})"})
    else: 붙음.append({"자식": p, "부모": "코어", "근거": "맞닿은 큰 판 없음 → 코어(확인 필요)"})
짝 = [[f"{g}/왼", f"{g}/오른"] for g in {p.split("/")[0] for p in names} if f"{g}/왼" in idx and f"{g}/오른" in idx]
json.dump({"부품": [{"이름": p, "층": 층[p.split("/")[0]], "칸": 부품[p]} for p in names], "붙음": 붙음, "덮음": 덮음, "좌우짝": 짝,
           "규칙": {"R": R, "덮음문턱": 문턱, "층": 층}}, open(os.path.join(O, "그래프.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ── 그림 1: 원화 위 · 층 색 + 붙음 화살표(자식 → 부모) + 덮음 표시(앞 쪽에 ▲)
art = cv2.cvtColor(cv2.imdecode(np.fromfile(ART, np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB).astype(float)
col = {1: np.array([60, 130, 255.]), 2: np.array([255, 150, 40.])}
for i, p in enumerate(names): m = P == i; art[m] = art[m] * 0.45 + col[층[p.split("/")[0]]] * 0.55
y0, y1 = max(0, top - 20), min(L.shape[0], bot + 20); xs0 = np.nonzero(L.any(0))[0]; x0, x1 = max(0, xs0.min() - 20), min(L.shape[1], xs0.max() + 20)
sc = 3.0; im = Image.fromarray(art[y0:y1, x0:x1].astype(np.uint8)).resize((int((x1 - x0) * sc), int((y1 - y0) * sc)), Image.LANCZOS); dr = ImageDraw.Draw(im)
F = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 22); Fs = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 17)
def 중심(p): yy, xx = np.nonzero(P == idx[p]); return ((xx.mean() - x0) * sc, (yy.mean() - y0) * sc)
core = ((cx - x0) * sc, ((top + bot) / 2 - y0) * sc + 60)
for e in 붙음:
    a = 중심(e["자식"]); b = core if e["부모"] == "코어" else 중심(e["부모"])
    if e["부모"] == "코어": dr.line([a, b], fill=(40, 80, 200), width=2)
    else:
        dr.line([a, b], fill=(255, 255, 255), width=6); dr.line([a, b], fill=(200, 30, 30), width=3); dr.ellipse([b[0] - 7, b[1] - 7, b[0] + 7, b[1] + 7], fill=(200, 30, 30))
dr.ellipse([core[0] - 16, core[1] - 16, core[0] + 16, core[1] + 16], fill=(40, 80, 200)); dr.text((core[0] + 20, core[1] - 12), "코어", font=F, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
for p in names:
    c = 중심(p); t = p.split("/")[0].split(" ")[0] + ("" if p.endswith("가운데") else ("·왼" if p.endswith("왼") else "·오"))
    dr.text((c[0] - 18, c[1] - 10), t, font=Fs, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
W2 = im.width; leg = Image.new("RGB", (W2, 70), (255, 255, 255)); dl = ImageDraw.Draw(leg)
dl.rectangle([10, 15, 40, 40], fill=tuple(col[1].astype(int))); dl.text((48, 14), "큰 판(층 1)", font=F, fill=(0, 0, 0))
dl.rectangle([220, 15, 250, 40], fill=tuple(col[2].astype(int))); dl.text((258, 14), "장식(층 2)", font=F, fill=(0, 0, 0))
dl.line([420, 28, 480, 28], fill=(200, 30, 30), width=4); dl.ellipse([474, 21, 488, 35], fill=(200, 30, 30)); dl.text((496, 14), "붙음: 장식 → 부모(점)", font=F, fill=(0, 0, 0))
dl.line([760, 28, 820, 28], fill=(40, 80, 200), width=3); dl.text((828, 14), "큰 판 → 코어", font=F, fill=(0, 0, 0))
out = Image.new("RGB", (W2, im.height + 70), (255, 255, 255)); out.paste(im, (0, 0)); out.paste(leg, (0, im.height)); out.save(os.path.join(O, "그래프_원화.png"))

# ── 그림 2: 나무(코어 → 큰 판 → 장식) + 덮음 「모름」 목록
kids = {}
for e in 붙음: kids.setdefault(e["부모"], []).append(e["자식"])
big = [p for p in names if 층[p.split("/")[0]] == 1]; rows = sum(max(1, len(kids.get(b, []))) for b in big)
T = Image.new("RGB", (1300, 90 + rows * 34 + 40), (255, 255, 255)); dt = ImageDraw.Draw(T); y = 60
dt.text((20, 15), "코어(안 보임 · 두개골 + 목 볼)", font=F, fill=(40, 80, 200))
for b in big:
    ch = kids.get(b, []); yb = y + 34 * (max(1, len(ch)) - 1) / 2
    dt.line([60, 45, 60, yb + 14], fill=(150, 150, 150), width=2); dt.line([60, yb + 14, 90, yb + 14], fill=(150, 150, 150), width=2)
    dt.text((95, yb), b, font=F, fill=tuple(col[1].astype(int)))
    for i, c in enumerate(ch):
        cy = y + i * 34; dt.line([380, yb + 14, 470, cy + 14], fill=(200, 30, 30), width=2)
        cov = "  (덮음 확인)" if 덮나(c, b) else ""; dt.text((480, cy), c + cov, font=F, fill=tuple(col[2].astype(int)))
    y += 34 * max(1, len(ch))
orphan = [e["자식"] for e in 붙음 if e["부모"] == "코어" and 층[e["자식"].split("/")[0]] == 2]
dt.text((20, y + 6), "맞닿은 큰 판 없는 장식(→ 코어 · 확인 필요): " + (", ".join(orphan) or "없음"), font=Fs, fill=(120, 0, 0))
T.save(os.path.join(O, "그래프_나무.png"))
n_cov = sum(e["확실"] for e in 덮음)
print(len(names), "부품 ·", len(경계), "맞닿음 · 덮음 확실", n_cov, "/ 모름", len(덮음) - n_cov, "· 좌우짝", len(짝), "· 코어로 간 장식", orphan)
