# -*- coding: utf-8 -*-
"""트림 — 원형사 조각 3 단계의 첫 손: 카메라 뷰에서 부품을 영역 윤곽대로 깎는다(스컬프트 Trim Lasso 의 코드판 = 윤곽 프리즘 ∩ 부품).
    python 트림.py -> out/오메가몬2/블렌더/프리즘/<부품>_<장>.stl (직교 카메라 틀에서 영역 윤곽을 앞뒤로 밀어낸 프리즘) · 트림.json(부품 → 장 → 프리즘 파일)
부품 ↔ 장 영역: 면대응_선택 + 옆 · 3/4 손 이름. 뿔 · 안테나는 정면 영역 / 실루엣 · 3/4위 실루엣."""
import os, sys, json
import numpy as np, cv2, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
D = J(OUT, "..", "자료"); B = J(OUT, "..", "블렌더"); P = J(B, "프리즘"); os.makedirs(P, exist_ok=True); S = 3
스펙 = json.load(open(J(B, "블록아웃.json"), encoding="utf-8")); 카 = {c["이름"]: c for c in 스펙["카메라"]}
읽 = lambda p, f=cv2.IMREAD_UNCHANGED: cv2.imdecode(np.fromfile(p, np.uint8), f)
라벨 = {t: np.load(J(D, t + "_영역.npz"))["라벨"] for t in ("02_정면", "02_3-4", "02_옆")}
실루엣 = {t: 읽(J(D, t + "_실루엣.png"), 0) > 127 for t in ("02_정면", "02_3-4", "02_옆", "02_3-4위")}
표적 = {                                                                                             # 부품 → 장 → (영역 ids | "실루엣")
    "부리": {"02_정면": [17, 24, 31], "02_옆": [5, 12, 13, 14, 15], "02_3-4": [12, 19, 22, 11, 14, 15]},
    "눈L": {"02_정면": [13], "02_옆": [3, 4, 6, 7, 8, 9], "02_3-4": [7, 8]},          # +x 눈 = 옆 · 3/4 에 보이는 눈
    "눈R": {"02_정면": [10, 15]},
    "뿔": {"02_정면": [1], "02_3-4위": "실루엣"},
    "안테나L": {"02_정면": "실루엣", "02_3-4위": "실루엣"}, "안테나R": {"02_정면": "실루엣", "02_3-4위": "실루엣"},      # 옆 상자엔 안테나가 안 들어 있다
    "소체": {"02_정면": "실루엣", "02_옆": "실루엣", "02_3-4": "실루엣", "02_3-4위": "실루엣"},
    "볼날개L": {"02_정면": "실루엣", "02_옆": "실루엣"}, "볼날개R": {"02_정면": "실루엣"},
}
def 마스크(t, ids):
    if ids == "실루엣": return 실루엣[t]
    m = np.isin(라벨[t], ids).astype(np.uint8); m = cv2.resize(m, (m.shape[1] // S, m.shape[0] // S), interpolation=cv2.INTER_NEAREST); return cv2.dilate(m, np.ones((3, 3), np.uint8)) > 0   # 먹선 두께만큼 불림
def 프리즘(t, m, 파일):
    c = 카[t]; W, H, s = c["W"], c["H"], c["W"] / c["ortho_scale"]; M = np.array(c["행렬"]); cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    메시들 = []
    for cnt in cs:
        if cv2.contourArea(cnt) < 200: continue
        poly = cv2.approxPolyDP(cnt, 1.5, True)[:, 0, :].astype(float); x = (poly[:, 0] - W / 2) / s; y = -(poly[:, 1] - H / 2) / s
        try: ex = trimesh.creation.extrude_polygon(trimesh.path.polygons.Polygon(np.column_stack([x, y])).buffer(0), height=1500.0)
        except Exception as e: print("  프리즘 실패", t, e); continue
        V = np.asarray(ex.vertices); V = np.column_stack([V[:, 0], V[:, 1], -V[:, 2] - 10.0]); V = (M[:3, :3] @ V.T).T + M[:3, 3]; 메시들.append(trimesh.Trimesh(V, ex.faces, process=False))
    if not 메시들: return None
    mm = trimesh.util.concatenate(메시들); mm.export(파일); return 파일
out = {}
for 부품, 장들 in 표적.items():
    out[부품] = {}
    for t, ids in 장들.items():
        f = 프리즘(t, 마스크(t, ids), J(P, "%s_%s.stl" % (부품, t)))
        if f: out[부품][t] = f
    print(부품, list(out[부품]))
json.dump(out, open(J(B, "트림.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
