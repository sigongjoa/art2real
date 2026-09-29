# -*- coding: utf-8 -*-
"""지표 2 — 부위별 선 대조 P/R/F1 (ICCV 2025 Langerman: Edge F1 이 전문가 선호와 최상 일치 · 재현율(빠진 선)이 결정적).
    python 선F1.py -> 표 + out/오메가몬2/지표/선F1.json · 선F1_<이름>_<보기>.png(겹침 그림: 기준 선 빨강 · 후보 선 파랑 · 맞은 곳 검정)
집합.py 의 정규화 그림(머리 100 단위 = 400 px)에서 Canny 선을 뽑고, 문턱 2.5 단위(10 px) 안에 상대 선이 있으면 맞음.
부위(정면 · 단위): 투구 = y<34 또는 |dx|>30 · 눈 = 34~70 & 8<|dx|≤30 · 코 = 34~75 & |dx|≤8 · 입 = 70~100 & |dx|≤30. 뿔 · 안테나(y<0)는 뺀다.
"""
import os, json
import numpy as np, cv2
읽기 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)          # 한글 경로: cv2.imread 못 읽음
쓰기 = lambda p, im: cv2.imencode('.png', im)[1].tofile(p)
from 집합 import 집합, 경로, OUT, 순서기대, W, H, TOP, CX, U
문턱 = 2.5 * U
def 선(파일):
    g = cv2.cvtColor(읽기(파일), cv2.COLOR_BGR2GRAY); g = cv2.GaussianBlur(g, (0, 0), 1.2)
    e = cv2.Canny(g, 60, 150) > 0; e[:TOP] = False; e[TOP + 400 + 8:] = False; return e
def 부위마스크(보기):
    yy, xx = np.mgrid[0:H, 0:W]; y = (yy - TOP) / U; dx = np.abs(xx - CX) / U
    if 보기 == "옆": return {"전체": y >= 0}
    return {"전체": y >= 0, "투구": (y >= 0) & ((y < 34) | (dx > 30)), "눈": (y >= 34) & (y <= 70) & (dx > 8) & (dx <= 30), "코": (y >= 34) & (y <= 75) & (dx <= 8), "입": (y > 70) & (y <= 100) & (dx <= 30)}
def prf(A, B):
    """A = 기준 선 · B = 후보 선. 정밀도 = B 중 A 가까이 · 재현율 = A 중 B 가까이."""
    dA = cv2.distanceTransform((~A).astype(np.uint8), cv2.DIST_L2, 3); dB = cv2.distanceTransform((~B).astype(np.uint8), cv2.DIST_L2, 3)
    p = (dA[B] <= 문턱).mean() if B.any() else 0.0; r = (dB[A] <= 문턱).mean() if A.any() else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)
def 점수(이름, 보기, 기준="02"):
    A, B = 선(경로(기준, 보기)), 선(경로(이름, 보기)); out = {}
    for 부위, m in 부위마스크(보기).items():
        p, r, f = prf(A & m, B & m); out[부위] = dict(P=round(p, 3), R=round(r, 3), F1=round(f, 3))
    im = np.full((H, W, 3), 245, np.uint8); dA = cv2.distanceTransform((~A).astype(np.uint8), cv2.DIST_L2, 3)
    im[A] = (60, 60, 230); im[B] = (230, 120, 40); im[B & (dA <= 문턱)] = (20, 20, 20); 쓰기(os.path.join(OUT, "선F1_%s_%s.png" % (이름, 보기)), im)
    return out

if __name__ == "__main__":
    결과 = {}
    for n in 집합:
        if n == "02": continue
        결과[n] = {보기: 점수(n, 보기) for 보기 in 집합[n] if 보기 in 집합["02"]}
    print("%-5s %8s %8s %8s | %6s %6s %6s %6s" % ("이름", "정면F1", "정면R", "옆F1", "투구", "눈", "코", "입"))
    for n, r in sorted(결과.items(), key=lambda kv: -kv[1]["정면"]["전체"]["F1"]):
        f = r["정면"]; print("%-5s %8.3f %8.3f %8s | %6.3f %6.3f %6.3f %6.3f" % (n, f["전체"]["F1"], f["전체"]["R"], ("%.3f" % r["옆"]["전체"]["F1"]) if "옆" in r else "-", f["투구"]["F1"], f["눈"]["F1"], f["코"]["F1"], f["입"]["F1"]))
    순 = [n for n in sorted(결과, key=lambda n: -결과[n]["정면"]["전체"]["F1"]) if n in 순서기대]; print("순서", " > ".join(순), "| 기대", " > ".join(순서기대))
    json.dump(결과, open(os.path.join(OUT, "선F1.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
