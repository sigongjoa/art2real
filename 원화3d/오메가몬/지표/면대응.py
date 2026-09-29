# -*- coding: utf-8 -*-
"""② 면 대응 — 장마다 면 인접 그래프 → 세 시점 사이 대응 **후보** (2026-09-29 밤 · 외부 패널 「면 ↔ 면 대응은 색 · 이름이 아니라 인접 · 경계 위상 · 위치로」).
    python 면대응.py -> out/오메가몬2/자료/면대응_후보.png (정면 기준 면마다 3/4 · 옆 후보 셋을 색으로) · 면대응_후보.json · 면그래프_<장>.json
면 특징(장마다): 재질(흰 · 검 · 파 · 금 · 회 — 알베도 규칙) · 상대 위치(가운데 x · y · 머리 단위) · 넓이 비 · 이웃 면들의 재질 다중집합 · 위아래 이웃.
대응 점수(정면 면 f ↔ 다른 장 면 g) = 재질 같음(필수) · |y 차| · 이웃 재질 다중집합 유사도(Jaccard) · 넓이 비 · x 부호(3/4 · 옆은 한쪽만 보임). 정답을 정하지 않는다 — 상위 3 후보를 사람이 고른다.
장 사이 눈금은 손표3D 와 같음(정면: 뿔 끝 0 · 턱 100 / 옆: 눈 · 턱 맞춤 / 3/4: 눈 · 턱 맞춤).
"""
import os, sys, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
D = J(OUT, "..", "자료"); 기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); S = 3
읽기 = lambda p, f=cv2.IMREAD_COLOR: cv2.imdecode(np.fromfile(p, np.uint8), f)
정이름 = json.load(open(J(D, "자료3D2_이름.json"), encoding="utf-8")); 옆이름 = json.load(open(J(D, "자료3D3_옆이름.json"), encoding="utf-8"))
def 재질(bgr, L흰):
    """캡처마다 흰 갑주 밝기(L흰 = 실루엣 안 흰 면 밝기의 70 분위)에 상대로: 검 < 0.35 · 파/금은 채도 · 나머지 흰(그늘 톤도 흰 — 알베도 규칙)"""
    b, g, r = [float(v) for v in bgr]; L = 0.299 * r + 0.587 * g + 0.114 * b; mx, mn = max(r, g, b), min(r, g, b); sat = (mx - mn) / max(mx, 1)
    if L < 0.35 * L흰: return "검"
    if sat > 0.28 and b > r + 15: return "파"
    if sat > 0.28 and r > b + 15 and g > b: return "금"
    return "흰"
class 장:
    def __init__(s, 태그, 뒤집=False):
        s.태그 = 태그; s.라벨 = np.load(J(D, 태그 + "_영역.npz"))["라벨"]; im = 읽기(기록[태그]["파일"]); s.im3 = cv2.resize(im, (s.라벨.shape[1], s.라벨.shape[0]), interpolation=cv2.INTER_CUBIC); s.뒤집 = 뒤집
        s.ids = [int(i) for i in np.unique(s.라벨) if i > 0]; s.면 = {}
    def 눈금(s, y0, h, cx): s.y0, s.h, s.cx = y0, h, cx
    def 특징(s):
        전체 = float((s.라벨 > 0).sum()); k = np.ones((5, 5), np.uint8); g = cv2.cvtColor(s.im3, cv2.COLOR_BGR2GRAY); L흰 = float(np.percentile(g[s.라벨 > 0], 70))
        for i in s.ids:
            m = s.라벨 == i; ys, xs = np.nonzero(m); ring = (cv2.dilate(m.astype(np.uint8), k) > 0) & ~m; nb = [int(v) for v in np.unique(s.라벨[ring]) if v > 0 and v != i]
            x = (xs.mean() / S - s.cx) / s.h * 100 * (-1 if s.뒤집 else 1); y = (ys.mean() / S - s.y0) / s.h * 100
            s.면[i] = dict(재질=재질(np.median(s.im3[m], 0), L흰), x=round(float(x), 1), y=round(float(y), 1), y0=round(float((ys.min() / S - s.y0) / s.h * 100), 1), y1=round(float((ys.max() / S - s.y0) / s.h * 100), 1), 넓이=round(float(m.sum() / 전체), 4), 이웃=nb)
        for i, f in s.면.items(): f["이웃재질"] = sorted(s.면[j]["재질"] for j in f["이웃"] if j in s.면); f["위이웃"] = sorted(s.면[j]["재질"] for j in f["이웃"] if j in s.면 and s.면[j]["y"] < f["y"] - 3); f["아래이웃"] = sorted(s.면[j]["재질"] for j in f["이웃"] if j in s.면 and s.면[j]["y"] > f["y"] + 3)
        return s
def 눈금맞춤(장_, 위ids, 아래ids, 눈ids=None, 눈단위=None):
    L = 장_.라벨; ys, _ = np.nonzero(np.isin(L, 아래ids)); 턱 = ys.max() / S
    if 눈ids is not None: ys, _ = np.nonzero(np.isin(L, 눈ids)); e = ys.mean() / S; h = (턱 - e) / (100 - 눈단위) * 100; y0 = 턱 - h
    else: ys, _ = np.nonzero(np.isin(L, 위ids)); y0 = ys.min() / S; h = 턱 - y0
    m = (L > 0) & (np.arange(L.shape[0])[:, None] < 턱 * S); ys, xs = np.nonzero(m); 장_.눈금(y0, h, (xs.min() + xs.max()) / 2 / S)
def jac(a, b):
    A, B = {}, {}
    for v in a: A[v] = A.get(v, 0) + 1
    for v in b: B[v] = B.get(v, 0) + 1
    inter = sum(min(A.get(k, 0), B.get(k, 0)) for k in set(A) | set(B)); uni = sum(max(A.get(k, 0), B.get(k, 0)) for k in set(A) | set(B)); return inter / uni if uni else 0.0
def 점수(f, g, 한쪽):
    if f["재질"] != g["재질"]: return None
    if 한쪽 and f["x"] > 8: return None                                                            # 3/4 · 옆은 그림 왼쪽(캐릭터 오른쪽 · x<0)만 보인다 → 정면 오른쪽 면(x>8)은 후보 없음
    dy = abs(f["y"] - g["y"]); s_y = max(0.0, 1 - dy / 15); s_nb = 0.5 * jac(f["이웃재질"], g["이웃재질"]) + 0.25 * jac(f["위이웃"], g["위이웃"]) + 0.25 * jac(f["아래이웃"], g["아래이웃"])
    ra = min(f["넓이"], g["넓이"]) / max(f["넓이"], g["넓이"], 1e-6); s_a = ra ** 0.5
    return round(0.5 * s_y + 0.35 * s_nb + 0.15 * s_a, 3), dict(dy=round(dy, 1), 이웃=round(s_nb, 2), 넓이=round(s_a, 2))
if __name__ == "__main__":
    F = 장("02_정면"); 눈금맞춤(F, 정이름["뿔"], 정이름["부리"][-1:]); F.특징(); 정눈 = float(np.mean([F.면[i]["y"] for i in 정이름["눈L"] + 정이름["눈R"]]))
    Sd = 장("02_옆", 뒤집=True); 눈금맞춤(Sd, 옆이름["투구"], 옆이름["부리3"], 옆이름["눈"], 정눈); Sd.특징()
    Q = 장("02_3-4"); 삼사이름 = json.load(open(J(D, "자료3D3_34이름.json"), encoding="utf-8")); 눈금맞춤(Q, [], 삼사이름["턱"], 삼사이름["눈"], 정눈); Q.특징()
    for 장_ in (F, Q, Sd): json.dump(장_.면, open(J(D, "면그래프_%s.json" % 장_.태그), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    후보 = {}
    for i, f in F.면.items():
        후보[i] = {}
        for 이름_, 장_ in (("3-4", Q), ("옆", Sd)):
            c = [(j, *r) for j in 장_.ids if (r := 점수(f, 장_.면[j], True)) is not None]; c.sort(key=lambda t: -t[1]); 후보[i][이름_] = [dict(면=j, 점수=s, 근거=근) for j, s, 근 in c[:3]]
    json.dump(dict(정면눈=정눈, 후보=후보, 승인="후보만 · 사람이 고른다"), open(J(D, "면대응_후보.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 그림: 정면 면 하나마다 한 줄 — 정면(그 면 강조) | 3/4 후보 3 색 | 옆 후보 3 색
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 16); 색3 = [(230, 40, 40), (40, 160, 60), (40, 90, 230)]
    def 칸(장_, ids색, 제목):
        x0, y0, x1, y1 = [v * S for v in 기록[장_.태그]["상자"]]; im = cv2.cvtColor(장_.im3, cv2.COLOR_BGR2GRAY); im = cv2.cvtColor((im * 0.55 + 100).astype(np.uint8), cv2.COLOR_GRAY2RGB)
        for j, c in ids색: im[장_.라벨 == j] = c
        e = cv2.Laplacian(장_.라벨.astype(np.float32), cv2.CV_32F) != 0; im[e & (장_.라벨 > 0)] = (30, 30, 30); p = Image.fromarray(im[y0:y1, x0:x1]); p.thumbnail((300, 300))
        ImageDraw.Draw(p).text((4, 4), 제목, font=ft, fill=(0, 0, 0), stroke_width=2, stroke_fill=(255, 255, 255)); return p
    뽑 = [i for i in F.ids if F.면[i]["x"] <= 8 and F.면[i]["넓이"] > 0.004]; 줄들 = []
    for i in 뽑:
        f = F.면[i]; A = 칸(F, [(i, (255, 60, 200))], "정면 %d %s y%.0f" % (i, f["재질"], f["y"]))
        B = 칸(Q, [(c["면"], 색3[k]) for k, c in enumerate(후보[i]["3-4"])], "3/4 " + " ".join("%d(%.2f)" % (c["면"], c["점수"]) for c in 후보[i]["3-4"]))
        C = 칸(Sd, [(c["면"], 색3[k]) for k, c in enumerate(후보[i]["옆"])], "옆 " + " ".join("%d(%.2f)" % (c["면"], c["점수"]) for c in 후보[i]["옆"]))
        줄 = Image.new("RGB", (A.width + B.width + C.width + 20, max(A.height, B.height, C.height)), (250, 250, 248)); 줄.paste(A, (0, 0)); 줄.paste(B, (A.width + 10, 0)); 줄.paste(C, (A.width + B.width + 20, 0)); 줄들.append(줄)
    열 = 3; W = max(r.width for r in 줄들); Hr = max(r.height for r in 줄들); 행 = (len(줄들) + 열 - 1) // 열; 시트 = Image.new("RGB", (열 * (W + 12), 행 * (Hr + 12)), (250, 250, 248))
    for k, r in enumerate(줄들): 시트.paste(r, ((k % 열) * (W + 12), (k // 열) * (Hr + 12)))
    시트.save(J(D, "면대응_후보.png")); print("정면 면(왼쪽 · 넓이 > 0.4 %)", len(뽑), "→", J(D, "면대응_후보.png"))
    for i in 뽑: print("정면 %2d %s y%3.0f x%4.0f | 3/4:" % (i, F.면[i]["재질"], F.면[i]["y"], F.면[i]["x"]), " ".join("%d(%.2f)" % (c["면"], c["점수"]) for c in 후보[i]["3-4"]), "| 옆:", " ".join("%d(%.2f)" % (c["면"], c["점수"]) for c in 후보[i]["옆"]))
