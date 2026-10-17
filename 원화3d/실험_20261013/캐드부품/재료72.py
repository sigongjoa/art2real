# 72 편 재료 — 그림63 과 같은 고르기로 부품 셋(톱니 링 · 모터 판 · 관)을 정답 · 틀 · 모델 낱장 투명 PNG 로 · 10-17
# 사용(venv): 재료72.py → out/영상05/대화/72_실제모양/자료/부품/<이름>_<종류>.png + 값.json
import os, json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import 그림63 as G   # 그림63 을 불러오면 그 그림도 다시 그려짐(같은 고르기를 그대로 쓰려고)
D = "G:/art2real/out/영상05/대화/72_실제모양/자료/부품/"; os.makedirs(D, exist_ok=True)
쓸 = {"톱니링": G.고른[3][1], "모터판": G.고른[1][1], "관": G.고른[8][1]}; 값 = {}
for 이름, k in 쓸.items():
    i = G.예부[k]; v, fc, _ = G.J.정규메시(G.L[i]); m = G.trimesh.Trimesh(v, fc, process=False)
    if len(m.faces) > 60000: m = m.simplify_quadric_decimation(face_count=60000)
    for 종류, 그 in [("정답", lambda a: G.면(a, np.asarray(m.vertices), np.asarray(m.faces), "#9bd3a8")), ("틀", lambda a: G.칸면(a, G.풀(G.틀b[i]), "#bbbbc4")), ("모델", lambda a: G.칸면(a, G.풀(G.P[k]), "#e8c06a"))]:
        f = plt.figure(figsize=(5, 5)); a = f.add_subplot(projection="3d"); G.축(a, -.42, .42); 그(a); f.subplots_adjust(0, 0, 1, 1); f.savefig(D + "%s_%s.png" % (이름, 종류), dpi=100, transparent=True); plt.close(f)
    값[이름] = {"틀 F": float(G.R[k, 2]), "모델 F": float(G.R[k, 3])}
json.dump(값, open(D + "값.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(값)
