# -*- coding: utf-8 -*-
"""색 분할 부품 — 원화 색 부류 지도로 장갑을 색마다 끼움 부품으로 나눈다 (2026-09-26).

    python 색분할.py
      -> out/출력/오메가몬_PG/디자인/색분할/*.stl · 부품.json(「대체」 = 이 부품들로 바뀐 원래 부품) · 보기.png

디테일 대조(디테일대조.py)에서 빠진 선 1 순위가 색 경계였다(정면 503 mm · 팔끝 L/R · 대포).
대상 = 짐승 머리 팔끝 8 부품. 앞 반쪽은 정면 원화, 뒤 반쪽은 뒤 원화(「거울 뒤」 · 화면 X = +x)로 가른다.
대포는 원화에서 한 부류(회색)라 색 분할 대상이 아니다 — 빠진 선은 명암 · 띠 홈이다.

가르기 (보는 축 y 로 민 기둥):
  바탕 = 그 부품이 맨 앞에 보이는 화소 중 가장 많은 부류. 나머지 부류 영역(열기 r 1.2 mm · 넓이 ≥ 8 mm²)마다
  겉층 O = 부품 − (부품을 안쪽으로 1 mm 민 것) · 끼움 = (O ∩ 기둥(M)) ∪ ((부품 − O) ∩ 기둥(M ⊕ 1.2)) — 뒤에서 넣는 턱 끼움.
  본체 = 부품 − (O ∩ 기둥(M ⊕ 틈)) − ((부품 − O) ∩ 기둥(M ⊕ 1.2 + 틈)). 겉에서는 틈 0.15 가 선으로 보인다.
  끼움 색 = 그 영역 원화 RGB 중앙값(도색 지침)."""
import os, sys, json, time
import numpy as np, trimesh, manifold3d as M
from scipy import ndimage
from skimage import measure
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 디테일대조 as DD
from 메시출력 import 부채나누기

D = DD.D; SRC = os.path.join(D, "머리어깨"); OUT = os.path.join(D, "색분할"); os.makedirs(OUT, exist_ok=True)
틈, 턱, 겉층, 열기mm, 최소mm2, 부스러기mm3 = 0.15, 1.2, 1.0, 1.2, 100.0, 3.0   # 09-26 검토: 25 → 100 (작은 끼움 11 개가 0.3 g 미만 · 얼룩)
대상 = {"정면": ["L팔끝앞", "L손앞", "R팔끝앞", "R손앞"], "뒤": ["L팔끝뒤", "L손뒤", "R팔끝뒤", "R손뒤"]}
안쪽 = {"정면": 1.0, "뒤": -1.0}          # 겉에서 속으로 가는 y 방향
부류이름 = {1: "흰회", 3: "검", 4: "금", 5: "주황", 6: "빨강", 7: "파랑", 8: "하늘"}
t0 = time.time()
def log(*a): print("[%4.0fs]" % (time.time() - t0), *a, flush=True)

def 읽기(fn):
    t = trimesh.load(fn, force="mesh"); t.merge_vertices()
    m = M.Manifold(M.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
    assert m.status() == M.Error.NoError and not m.is_empty(), fn
    return m
def 추림(m):
    """부스러기(< 부스러기mm3 — 겉층 가르기가 옆벽 모서리에 남긴 조각) 버림 → (남은 것, 버린 부피)."""
    ps = m.decompose(); 남 = [p for p in ps if p.volume() >= 부스러기mm3]
    return (M.Manifold.batch_boolean(남, M.OpType.Add) if 남 else M.Manifold()), sum(p.volume() for p in ps if p.volume() < 부스러기mm3)
def 메시(m):
    t = m.to_mesh(); return trimesh.Trimesh(np.asarray(t.vert_properties)[:, :3], np.asarray(t.tri_verts), process=False)
XZ_Y = np.array([[1, 0, 0, 0], [0, 0, 1, -150.0], [0, 1, 0, 0]], float)   # 단면 (x, z) → 밀기 축 y ∈ [−150, 150]
def 기둥(cs): return M.Manifold() if cs.is_empty() else cs.extrude(300.0).transform(XZ_Y)

def 앞부품지도(보기, 부품):
    """조립 전체를 그 보기로 래스터 → 화소마다 맨 앞 부품 이름."""
    f, cx, r0, s, R, sg = DD.보기[보기]; 이름들 = [n for n, v in 부품.items() if v is not None]
    V = np.vstack([np.asarray(부품[n][0].vertices) @ R.T for n in 이름들]); off = np.cumsum([0] + [len(부품[n][0].vertices) for n in 이름들])
    F = np.vstack([np.asarray(부품[n][0].faces) + off[i] for i, n in enumerate(이름들)])
    pid = np.concatenate([np.full(len(부품[n][0].faces), i) for i, n in enumerate(이름들)])
    _, tid = DD.래스터(V, F, cx, r0, s)
    앞 = np.full(tid.shape, -1); 앞[tid >= 0] = pid[tid[tid >= 0]]
    return 앞, 이름들

def 영역단면(mask, 보기):
    """화소 마스크 → 몸 (x, z) mm CrossSection."""
    f, cx, r0, s, R, sg = DD.보기[보기]
    polys = []
    for c in measure.find_contours(np.pad(mask, 1).astype(float), 0.5):
        r, q = c[:, 0] - 1, c[:, 1] - 1
        if len(c) >= 4: polys.append(np.c_[sg * (q + 0.5 - cx) * s, (r0 - (r + 0.5)) * s])
    return M.CrossSection(polys, M.FillRule.EvenOdd).simplify(0.05) if polys else M.CrossSection()

def main():
    import glob
    for f in glob.glob(os.path.join(OUT, "*.stl")): os.remove(f)
    부품 = DD.부품읽기(); 결과 = {"설명": __doc__, "대체": [], "부품": {}}; 보기그림 = []
    for 보기, 목록 in 대상.items():
        원 = DD.원화선(보기); 부 = 원["색"]; rgb = 원["rgb"].astype(np.float32) / 255
        앞, 이름들 = 앞부품지도(보기, 부품); s = DD.보기[보기][3]; r_px = max(1, int(round(열기mm / s)))
        disk = np.hypot(*np.mgrid[-r_px:r_px + 1, -r_px:r_px + 1]) <= r_px
        for n in 목록:
            보임 = (앞 == 이름들.index(n)) & (부 > 0)
            바탕 = int(np.bincount(부[보임]).argmax()); part = 읽기(os.path.join(SRC, n + ".stl"))
            O = part - part.translate([0.011, 안쪽[보기] * 겉층, 0.017]); 속 = part - O   # x·z 흔듦: y 와 나란한 옆벽이 제자리에 겹쳐 붙는 것 막음
            본체 = part; 끼움들 = []; 도색 = []
            영역 = []
            for k in sorted(set(np.unique(부[보임])) - {0, 바탕, 3}):      # 3 = 검: 먹선 · 음영 · 입속 — 끼우면 검은 얼룩이 됐다(09-26 검토) → 도색도 안 함
                mk = ndimage.binary_opening(보임 & (부 == k), disk)
                lab, nl = ndimage.label(mk)
                for i in range(1, nl + 1):
                    reg = lab == i; 넓 = reg.sum() * s * s
                    if 넓 < 최소mm2:
                        if 넓 >= 4.0: 도색.append((부류이름.get(k, str(k)), round(넓, 1)))
                        continue
                    cs = 영역단면(reg, 보기)
                    if not cs.is_empty(): 영역.append((k, reg, cs, 넓))
            for i, (k, reg, cs, 넓) in enumerate(영역):
                rd = lambda d, c=cs: c.offset(d, M.JoinType.Round)
                남 = [c.offset(턱 + 틈, M.JoinType.Round) for j, (_, _, c, _) in enumerate(영역) if j != i]
                턱cs = rd(턱) - M.CrossSection.batch_boolean(남, M.OpType.Add) if 남 else rd(턱)   # 이웃 끼움 턱끼리 겹침 482 mm³ → 이웃 쪽 턱 자리는 본체에 남긴다
                끼, _ = 추림((O ^ 기둥(cs)) + (속 ^ 기둥(턱cs)))
                if 끼.is_empty(): continue
                본체 = 본체 - (O ^ 기둥(rd(틈))) - (속 ^ 기둥(턱cs.offset(틈, M.JoinType.Round)))
                c = np.median(rgb[reg], 0).round(3).tolist()
                끼움들.append(("%s_%s%d" % (n, 부류이름.get(k, str(k)), len(끼움들) + 1), 끼, c, round(넓, 1)))
            if not 끼움들: log(n, "바탕", 부류이름[바탕], "— 나눌 영역 없음"); continue
            본체, 버림 = 추림(본체)
            바탕색 = np.median(rgb[보임 & (부 == 바탕)], 0).round(3).tolist()
            결과["대체"].append(n); 결과.setdefault("도색", {})[n] = 도색
            for 이름, m, c, 넓 in [(n + "_본체", 본체, 바탕색, None)] + 끼움들:
                fn = os.path.join(OUT, 이름 + ".stl"); 메시(m).export(fn); wt = trimesh.load(fn).is_watertight
                for 양 in (0.03, 0.06, 0.10):   # 자기 접촉 정점(STL 병합 때 붙는 곳)을 부채마다 떼기 — 디자인_머리어깨.py 와 같은 법
                    if wt: break
                    부채나누기(m, 양).export(fn); wt = trimesh.load(fn).is_watertight
                결과["부품"][이름] = dict(파일=이름 + ".stl", 색=c, 원래=n, 보기=보기, 원화넓이mm2=넓, 닫힘=bool(wt),
                                       조각=len(m.decompose()), 부피mm3=round(m.volume(), 1), 무게g_PLA=round(m.volume() * 1.24e-3, 2))
            log(n, "바탕", 부류이름[바탕], "끼움", len(끼움들), [(a, 넓) for a, _, _, 넓 in 끼움들], "도색(작은 영역)", 도색, "본체 부스러기 %.1f mm3" % 버림)
    결과["입력해시"] = DD.입력해시(DD.선행["색분할"])
    json.dump(결과, open(os.path.join(OUT, "부품.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    작 = {k: v for k, v in 결과["부품"].items() if v["무게g_PLA"] < 0.3 or not v["닫힘"]}
    log("부품 %d (대체 %d) · 0.3 g 미만 또는 안 닫힘:" % (len(결과["부품"]), len(결과["대체"])), {k: (v["무게g_PLA"], v["닫힘"], v["조각"]) for k, v in 작.items()})

if __name__ == "__main__":
    main()
