# -*- coding: utf-8 -*-
"""기능0 탐색 맞춤 검사 — 손으로 지은 20 부품에서 정답 깊이 복셀 IoU: 교차 · 손 · 자동 찾기 · 10-11"""
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(R, "조각0")]
import 탐색 as T
from 실물보기 import 실물보기
손 = [4, 21, 24, 8, 32, 22, 13, 10, 23, 17, 29, 33, 34, 11, 3, 15, 16, 18, 26, 31]
X = T.X_("시험"); 표 = {}
for i in 손:
    x = X[i].astype(np.float32); 정 = T.깎기(x[3]); V0 = T.교차(x[0] > .5)
    m = trimesh.load(os.path.join(H, "결과", "%02d.stl" % i)); m.apply_translation([1, 1, 1]); m.apply_scale(.5)   # [-1,1] → 단위 상자
    Sm, Dm = 실물보기(m, T.n); 손V = T.깎기(Dm)
    r = json.load(open(os.path.join(H, "탐색", "시험_%02d.json" % i), encoding="utf-8"))
    손순 = json.load(open(os.path.join(H, "결과", "%02d.json" % i), encoding="utf-8")).get("순서", [])
    표[i] = {"교차": round(T.iou(V0, 정), 4), "손": round(T.iou(손V, 정), 4), "자동": r["끝 IoU"], "자동 순서": [(s["기능"], s["쪽"]) for s in r["순서"]], "손 순서": 손순}
    print(i, 표[i]["교차"], 표[i]["손"], 표[i]["자동"], 표[i]["자동 순서"], "| 손", 손순, flush=True)
a = np.array([[v["교차"], v["손"], v["자동"]] for v in 표.values()])
요 = {"중앙 교차 · 손 · 자동": np.median(a, 0).round(4).tolist(), "자동 ≥ 손": int((a[:, 2] >= a[:, 1] - 1e-4).sum()), "부품": len(a), "중앙 얻음(자동 − 교차)": round(float(np.median(a[:, 2] - a[:, 0])), 4)}
print(요); json.dump({"요약": 요, "표": 표}, open(os.path.join(H, "탐색", "대조.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
