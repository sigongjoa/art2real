# -*- coding: utf-8 -*-
"""두 층 이름표 + 장끼리 일관성 잣대 (10-03 외부 패널 채택 1 · 2 · 3 → 사용자 「ㄱㄱ」).
1 층 = 관찰 영역(장마다 먹선 칸) · 2 층 = 부품 ID(물리 부품 · 그 안의 표면 · 무늬를 가름) + 확신.
  옛 이름(이름.json)은 버리지 않고 대응표로 옮긴다 — 두 가설을 한 이름에 넣은 것(「미늘3 · 턱」 등)은 대응표에 그 가설을 적고 확신을 낮춘다.
잣대: 화소 겹침 % 대신 「같은 부품 ID(좌우 포함)가 장끼리 같은 3D 자리로 오나」 — 특징맞춤2 카메라 · 깊이 맞춤으로 장마다 그 부품 화소를 3D 로 옮겨
  무게중심이 장끼리 얼마나 흩어지나(머리 높이 대비 %) · 평균 법선이 장끼리 몇 도 벌어지나. 큰 부품(돔)은 장마다 보이는 쪽이 달라 원래 흩어진다 — 작은 부품이 잣대.
tri(5) 는 참고만(무게 0) · 뒤(6)는 카메라가 없어 뺌. 출력 각도데이터/부품ID.json · 부품ID.ply(장 1~4 껍질을 부품 ID 색으로 · 같은 색이 같은 자리에 오면 일관)"""
import os, json, numpy as np, trimesh
from PIL import Image
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"
이름 = json.load(open(os.path.join(O, "이름.json"), encoding="utf-8")); J = json.load(open(os.path.join(O, "특징맞춤2.json"), encoding="utf-8"))
대응 = {   # 옛 바탕 이름 → (부품 ID, 표면, 확신, 메모)
 "투구 돔": ("H01 투구 껍질", "돔", "중", ""), "이마판": ("H01 투구 껍질", "이마", "중", ""), "차양 · 눈썹 능선": ("H01 투구 껍질", "차양", "중", "차양 = 투구의 앞 처마(마스크 윗변을 덮음)"),
 "뒤통수": ("H01 투구 껍질", "뒤", "낮", "설정화 선화 · 별도 뒤판일 수도"), "뿔": ("H09 뿔", "", "높", ""),
 "미늘1 (코판)": ("H02 마스크", "코판", "중", ""), "미늘2": ("H02 마스크", "미늘2", "낮", ""), "미늘3 · 턱": ("H02 마스크", "턱판", "낮", "가설: 미늘3 = 턱판(한 판)"),
 "마스크 볼판": ("H02 마스크", "볼판", "중", ""), "눈구멍": ("H03 눈 조립", "눈구멍", "높", "속머리가 보이는 구멍"), "눈 둘레 테": ("H03 눈 조립", "테", "중", "차양과 붙어 있어 헷갈림"),
 "눈": ("H03 눈 조립", "눈", "높", "속머리에 달림"), "안테나": ("H04 안테나", "", "높", ""), "안테나 뿌리 · 잔 조각": ("H05 안테나 받침", "", "낮", "잔 조각이 섞임 — 칸마다 따로 볼 것"),
 "볼날개": ("H06 볼날개", "", "중", ""), "목 깃": ("H07 목 깃", "", "높", "머리 아님 · 가슴 고정"), "번개": ("F01 번개 무늬", "", "높", "부품 아님 · H01 위 무늬"),
}
def 풀기(nm):
    t = nm.replace("(뒤)", "").replace("(뒤에서)", "").replace(" 뒤끝", ""); 의심 = "?" in t; t = t.replace("?", "").strip()
    b, 쪽 = (t.split("/") + [""])[:2]; b = b.strip(); 쪽 = 쪽.strip()
    if b not in 대응: return None
    pid, 면, 확신, 메모 = 대응[b]; return pid, 면, ("낮" if 의심 else 확신), 쪽 or "가운데", 메모
표 = {}
for n, d in 이름.items():
    for nm, cs in d.items():
        r = 풀기(nm)
        표.setdefault(n, []).append({"옛 이름": nm, "칸": cs, **({"부품": r[0], "표면": r[1], "확신": r[2], "쪽": r[3], "메모": r[4]} if r else {"부품": "미정", "확신": "낮"})})
# 3D 로 옮기기(특징맞춤2 와 같은 식)
def 껍질(n):
    z = np.load(os.path.join(O, f"판_{n}_Z.npz")); return z["m"], z["Z"]
부품들 = sorted({v[0] for v in 대응.values()}); 팔 = ["e6194b", "3cb44b", "ffe119", "4363d8", "f58231", "911eb4", "46f0f0", "f032e6", "bcf60c", "fabebe", "008080"]
색 = {p: [int(팔[i][k:k + 2], 16) for k in (0, 2, 4)] for i, p in enumerate(부품들)}
점 = {}; meshes = []
for n in ["1", "2", "3", "4"]:
    a = J["장별"][n]; R = np.array(a["R"]); s, tx, ty, A, b0 = a["크기"], a["tx"], a["ty"], a["깊이 배율 a"], a["b0"]
    m, Z = 껍질(n); z = np.load(os.path.join(O, f"{n}.npz")); L = z["라벨"]; ys_, xs_ = np.nonzero(L > 0); y0, x0 = ys_.min(), xs_.min()
    py, px = np.nonzero(m); cell = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)]
    W = np.c_[(px - tx) / s, -(py - ty) / s, A * Z[py, px] / s + b0] @ R          # 세계(정면 틀 · y = 카메라 쪽)
    키 = np.full(len(py), "", object)
    for e in 표[n]:
        if e["부품"] == "미정": continue
        q = np.isin(cell, e["칸"]); 키[q] = e["부품"] + "/" + e["쪽"]
    for k in set(키) - {""}:
        q = 키 == k
        if q.sum() >= 20: 점.setdefault(k, {})[n] = W[q].mean(0).tolist()
    vid = -np.ones(m.shape, int); vid[py, px] = np.arange(len(py)); aa, bb, cc, dd = vid[:-1, :-1], vid[:-1, 1:], vid[1:, :-1], vid[1:, 1:]; ok = (aa >= 0) & (bb >= 0) & (cc >= 0) & (dd >= 0)
    F = np.r_[np.c_[aa[ok], cc[ok], bb[ok]], np.c_[bb[ok], cc[ok], dd[ok]]]; col = np.array([색[k.split("/")[0]] if k else [90, 90, 90] for k in 키], np.uint8)
    me = trimesh.Trimesh(np.c_[W[:, 0], -W[:, 1], W[:, 2]], F, process=False); me.visual.vertex_colors = np.c_[col, np.full(len(col), 255)].astype(np.uint8); meshes.append(me)
trimesh.util.concatenate(meshes).export(os.path.join(O, "부품ID.ply"))
머리 = 300.0   # 정면 화소 기준 머리 높이(뿔 포함 판 높이)
일관 = {}
for k, d in sorted(점.items()):
    if len(d) < 2: continue
    P = np.array(list(d.values())); 흩 = float(np.linalg.norm(P - P.mean(0), axis=1).mean() / 머리 * 100)
    일관[k] = {"장": list(d), "흩어짐(머리 높이 %)": round(흩, 1)}
json.dump({"부품 ID": {p: 색[p] for p in 부품들}, "대응표": 표, "일관성": 일관}, open(os.path.join(O, "부품ID.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in sorted(일관.items(), key=lambda t: t[1]["흩어짐(머리 높이 %)"]): print(f"{k:22s} {v['흩어짐(머리 높이 %)']:5.1f}%  {v['장']}")
print("섞인 이름(가설 둘) →", [e["옛 이름"] for n in 표 for e in 표[n] if "·" in e["옛 이름"]][:20])
