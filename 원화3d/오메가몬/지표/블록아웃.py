# -*- coding: utf-8 -*-
"""블록아웃 — 원형사 순서 0 · 1 · 2 를 블렌더용 수치로 (2026-09-30 「블렌더 스컬핑 + 원형사 pdf 로 짜 봐」).
    python 블록아웃.py -> out/오메가몬2/블렌더/블록아웃.json : 카메라 6(자세3 + 시점추가 → 직교 카메라 · 배경 그림) · 겹 부품 시작 도형(랜드마크3D · 자세3 부품3D 에서)
좌표: 머리 단위 U(x 오른쪽 · y 아래 · z 앞) → 블렌더 B = (x, −z, −y) (앞 = −Y · 위 = +Z). 1 단위 = 1 mm 로 둔다(머리 100 mm · 나중에 스케일).
카메라: 찍기의 u = s·C_xy + t, C = (U·(1,1,−1))·Rᵀ → 직교 카메라 · ortho_scale = W/s · 축 = R 행 · 위치 = 그림 가운데 픽셀이 광축.
부품 값의 출처: 랜드마크3D(맞춤.py 손 랜드마크 · 같은 틀) = 「측정」 · 추정은 표시."""
import os, sys, json
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
D = J(OUT, "..", "자료"); B = J(OUT, "..", "블렌더"); os.makedirs(B, exist_ok=True)
기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); 자세3 = json.load(open(J(OUT, "자세3.json"), encoding="utf-8")); 추가 = json.load(open(J(D, "시점추가.json"), encoding="utf-8"))
L3 = json.load(open(J(OUT, "랜드마크3D.json"), encoding="utf-8")); 가 = L3["가운데"]; 반 = L3["반쪽"]
M = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)                                            # Uf = U·(1,1,−1) → B :  B = (Uf_x, Uf_z, −Uf_y)
def 블렌더점(u): x, y, z = u; return [float(x), float(-z), float(-y)]
def 카메라(이름, 자, 파일, W, H, D=400.0):
    R = cv2.Rodrigues(np.asarray(자["r"], float))[0]; s = float(자["s"]); tx, ty = 자["t"]
    cx, cy = (W / 2 - tx) / s, (H / 2 - ty) / s                                                      # 그림 가운데 픽셀의 카메라 좌표
    axes = np.stack([R[0], -R[1], -R[2]], 1)                                                       # 블렌더 카메라 X · Y(위) · Z(뒤) 를 Uf 틀에서
    loc = R.T @ np.array([cx, cy, -D]); Rw = M @ axes; locw = M @ loc
    return dict(이름=이름, 파일=파일, W=W, H=H, ortho_scale=W / s, 행렬=[[float(Rw[i, j]) for j in range(3)] + [float(locw[i])] for i in range(3)] + [[0, 0, 0, 1]])
카메라들 = []
for t, 자이름 in (("02_정면", "정면 yt_172"), ("02_3-4", "3/4 M04"), ("02_옆", "옆 yt_235")):
    im = cv2.imdecode(np.fromfile(기록[t]["파일"], np.uint8), cv2.IMREAD_COLOR); 카메라들.append(카메라(t, 자세3[자이름], 기록[t]["파일"], im.shape[1], im.shape[0]))
for t, v in 추가.items():
    im = cv2.imdecode(np.fromfile(v["파일"], np.uint8), cv2.IMREAD_COLOR); 카메라들.append(카메라(t, v["자세"], v["파일"], im.shape[1], im.shape[0]))
# ── 겹 부품 시작 도형 (측정 = 랜드마크3D · 추정 표시) ──
P = lambda k: 가[k] if k in 가 else 반[k]
mir = lambda p: [-p[0], p[1], p[2]]
부품 = [
    dict(이름="소체", 꼴="타원체", 중심=[0, 34, -7], 반지름=[38.8, 36, 27], 출처="투구최대폭 38.8(측정) · 세로 −2..70 · 앞뒤 −34..20(껍질 기둥 (0,50))"),
    dict(이름="부리", 꼴="껍질", 점=[P("뿔아래꼭짓점"), P("코끝"), P("턱끝"), P("윗판끝"), mir(P("윗판끝")), [6, 39, 28], [-6, 39, 28], [11, 100, 12], [-11, 100, 12], [14, 70, 34], [-14, 70, 34]], 출처="가운데 능선 3 점 + 윗판끝(측정) · 폭 6/14/11 추정"),
    dict(이름="눈L", 꼴="판", 점=[P("눈안쪽위"), P("눈바깥위"), P("눈바깥아래"), P("눈안쪽아래")], 두께=3, 출처="눈 네 모서리(측정)"),
    dict(이름="눈R", 꼴="판", 점=[mir(P("눈안쪽위")), mir(P("눈바깥위")), mir(P("눈바깥아래")), mir(P("눈안쪽아래"))], 두께=3, 출처="거울"),
    dict(이름="볼날개L", 꼴="판", 점=[P("투구최대폭"), [30, 50, -10], P("볼날개끝"), [36, 62, -30]], 두께=4, 출처="투구최대폭 · 볼날개끝(측정) · 나머지 둘 추정"),
    dict(이름="볼날개R", 꼴="판", 점=[mir(P("투구최대폭")), [-30, 50, -10], mir(P("볼날개끝")), [-36, 62, -30]], 두께=4, 출처="거울"),
    dict(이름="뿔", 꼴="원뿔", 밑=[0, 29, 23], 끝=[0, -57, 30], 반지름=8.5, 출처="뿔밑동 y·z(측정) · 끝 y −57 정면 상자(측정) · 끝 z 30 추정"),
    dict(이름="안테나L", 꼴="원뿔", 밑=P("안테나밑동"), 끝=[63, -22, -55], 반지름=4, 출처="밑동(측정) · 끝 x 63 정면 실루엣(측정) · y·z 추정"),
    dict(이름="안테나R", 꼴="원뿔", 밑=mir(P("안테나밑동")), 끝=[-63, -22, -55], 반지름=4, 출처="거울"),
]
for p in 부품:                                                                                        # U → 블렌더 좌표로
    for k in ("중심", "밑", "끝"):
        if k in p: p[k + "B"] = 블렌더점(p[k])
    if "점" in p: p["점B"] = [블렌더점(q) for q in p["점"]]
    if "반지름" in p and isinstance(p["반지름"], list): p["반지름B"] = [p["반지름"][0], p["반지름"][2], p["반지름"][1]]
json.dump(dict(카메라=카메라들, 부품=부품, 껍질=J(D, "패치", "바탕.stl"), 승인="Claude(사용자 미확인)"), open(J(B, "블록아웃.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(J(B, "블록아웃.json"), "카메라", [c["이름"] for c in 카메라들], "부품", [p["이름"] for p in 부품])
