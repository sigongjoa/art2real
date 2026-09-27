# -*- coding: utf-8 -*-
"""EG RX-78-2 — 조립 검증(EG_조립.py)이 짚은 셋만 최소로 고친다 (2026-09-27). 부품 모양을 사진에 더 맞추지 않는다.

    python EG_조립고침.py      -> out/키트/EG_RX78/2단계/부품_NN_조립.stl (원본 안 덮음) · 조립/고침.json
    python EG_조립.py 후       -> 고친 부품으로 다시 잰다(조립_후.json · 가동한계_후.png · 포징_후.png)

① 볼 소켓: 소켓 쪽 부품 ∪ 컵(r + 0.15 + 벽 0.6) − 구(r + 0.15) − 볼 부품 − 볼·목 덩어리를 X/Y/Z 축 ±15/30/45° 돌린 자취(원뿔 입구).
   고관절: 29 볼이 +X 에 하나뿐 → 그 볼 · 목을 X 거울로 복사해 오른쪽에도 붙이고 31 에 소켓.
② 막는 판: 움직이는 쪽에서 본 상대 부품의 회전 자취(목표 각까지)를 깎는다. 34 앞치마는 검사에서 경첩으로 따로 돈다.
③ 껍질: 갑주 − (속 틀 ⊕ 0.15). ⊕ 는 ±0.15 평행이동 14 개의 합(ponytail: 근사 — 모서리에서 틈이 0.15/√2 까지 준다).
좌표는 모두 몸(체계 척도). 오른쪽 부품만 고치면 왼쪽은 같은 메시의 X 거울이라 저절로 따라온다.
"""
import os, sys, json, numpy as np, manifold3d as M, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import EG_조립 as A

틈 = 0.15; 벽 = 0.6
부 = A.부품들
def 몸(k): return A.매니(A.메시(k))
def 합(ms):
    return M.Manifold.batch_boolean(list(ms), M.OpType.Add)
def 돌림(ax, a, c): return A.회전(ax, a, np.asarray(c, float))[:3, :].astype(np.float64)
def 구(c, r): return M.Manifold.sphere(r, 64).translate(tuple(map(float, c)))
def 부풀(m, d=틈):
    dirs = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)] + [(x, y, z) for x in (1, -1) for y in (1, -1) for z in (1, -1)]
    return 합([m] + [m.translate(tuple(d * np.array(v, float) / np.linalg.norm(v))) for v in dirs])

고친 = {}      # 부품 이름(몸) → Manifold(몸 좌표)
def 현재(k): return 고친.get(k) or 몸(k)
기록 = []

# ---------- ① 볼 소켓 ----------
def 볼(k, 참조):
    bs = A.볼찾기(A.P[부[k]["n"]]); c = [(A.점(k, b[2]), b[1]) for b in bs]
    return min(c, key=lambda x: np.linalg.norm(x[0] - np.asarray(참조, float)))
def 소켓(S, B, c, r, 볼몸=None):
    Bm = 볼몸 or 현재(B)
    덩 = Bm ^ 구(c, r + 1.8)
    자취 = [덩] + [덩.transform(돌림(ax, s * a, c)) for ax in np.eye(3) for a in (15, 30, 45) for s in (1, -1)]
    파기 = 합([구(c, r + 틈)] + 자취)
    전 = 현재(S); 후 = (전 + 구(c, r + 틈 + 벽)) - 파기 - Bm
    고친[S] = 후; 기록.append(dict(고침="소켓", 부품=S, 볼=B, 중심=np.round(c, 2).tolist(), r=r, 부피전=round(전.volume(), 2), 부피후=round(후.volume(), 2), 조각=len(후.decompose())))
    print("소켓", S, "←", B, 기록[-1], flush=True)

c어깨, r어깨 = 볼("R15", A.어깨 + [-3, 0, 0]); 소켓("R12", "R15", c어깨, r어깨)
c손목, r손목 = 볼("R26", A.손목); 소켓("R23", "R26", c손목, r손목); 소켓("R24", "R26", c손목, r손목)
c목아래, r목아래 = 볼("06", [0, 0.3, A.z목 - 1]); 소켓("10", "06", c목아래, r목아래)
c목위, r목위 = 볼("06", [0, 0.3, A.z목 + 3]); 소켓("07", "06", c목위, r목위)
c배, r배 = 볼("21", [0, 0, A.z배 - 2]); 소켓("27", "21", c배, r배)
# 고관절: 29 는 +X 에만 볼이 있고 −X 자리는 속이 찼다 → +X 반쪽을 거울로 붙여 좌우 대칭(몸 X = 0 이 29 가운데)
cL, r엉 = 볼("29", [4.5, 0, A.고관절[2]]); cR = cL * [-1, 1, 1]
m29 = 현재("29"); 반 = m29.trim_by_plane((1, 0, 0), 0.0); m29b = 반 + 반.mirror((1, 0, 0)); 고친["29"] = m29b
기록.append(dict(고침="29 좌우 대칭(+X 반쪽 거울)", 중심=np.round(cR, 2).tolist(), r=r엉, 부피전=round(m29.volume(), 2), 부피후=round(m29b.volume(), 2), 조각=len(m29b.decompose())))
소켓("R31", "29", cR, r엉)

# ---------- ② 막는 판 비키기 ----------
def 비키기(T이름, 상대, c, ax, 각들, 움직이는쪽=True):
    """T이름이 c · ax 로 각들만큼 돌 때(움직이는쪽) 상대 부품이 지나가는 자리를 깎는다. 움직이는쪽=False 면 상대가 돈다."""
    G = 합([현재(k) for k in 상대]); s = -1 if 움직이는쪽 else 1
    자취 = 합([G.transform(돌림(ax, s * a, c)) for a in 각들])
    전 = 현재(T이름); 후 = 전 - 부풀(자취, 0.1)
    고친[T이름] = 후; 기록.append(dict(고침="비키기", 부품=T이름, 상대=상대, 각=[min(각들), max(각들)], 부피전=round(전.volume(), 2), 부피후=round(후.volume(), 2), 조각=len(후.decompose())))
    print("비키기", 기록[-1], flush=True)
X_, Y_, Z_ = np.eye(3)
고친["R43"] = 몸("R43").translate((0, 0.5, -2.0))          # 물리기: 무릎 축에서 2 mm 아래 · 0.5 뒤(46 자취 밖으로 · 44 겹침 0.11)
기록.append(dict(고침="물리기", 부품="R43", 이동mm=[0, 0.5, -2.0]))
비키기("R43", ["R46"], A.무릎몸, X_, range(0, 96, 5))                                          # 무릎 굽힘(+X) · 135° 까지 깎으면 31 % 만 남아 95°
비키기("R39", ["29", "27", "36", "34", "40"], cR, Y_, range(0, 71, 5))                                   # 고관절 벌리기(+Y) 70°
비키기("27", ["21"], c배, Z_, list(range(-30, 31, 5)))                                         # 허리 돌 때 27 소켓 둘레가 21 틀을 비킨다
비키기("R48", ["R44", "R45"], A.요람몸, X_, list(range(-30, 1, 5)))                              # 발끝 올림: 발목 가드가 정강이를 비킨다
비키기("20", ["27", "36", "34", "29", "40", "41", "42"], c배, Z_, list(range(-30, 31, 5)), 움직이는쪽=False)  # 허리 ±30°
발볼 = A.점("R54", [A.Xb, 0, A.Zb])
m54 = 현재("R54") + 현재("R48"); 전53 = 현재("R53")
c발, r발 = 볼("R54", 발볼)
자취 = 합([m54.transform(돌림(Y_, a, 발볼)) for a in range(-30, 31, 5)]) - 구(c발, r발 + 틈 + 0.6)   # 컵 벽(볼 둘레 0.6)은 남긴다 — 다 깎으면 감쌈 0.56 → 0.46
고친["R53"] = 전53 - 부풀(자취, 0.1)
기록.append(dict(고침="발목 컵 입구", 부품="R53", 상대=["R54", "R48"], 각=[-30, 30], 부피전=round(전53.volume(), 2), 부피후=round(고친["R53"].volume(), 2), 조각=len(고친["R53"].decompose())))
print(기록[-1], flush=True)

# ---------- ③ 껍질 ----------
for 겉, 속 in (("14", "10"), ("20", "21"), ("R11", "R12")):
    전 = 현재(겉); 후 = 전 - 부풀(몸(속))
    고친[겉] = 후; 기록.append(dict(고침="껍질", 부품=겉, 속=속, 부피전=round(전.volume(), 2), 부피후=round(후.volume(), 2), 조각=len(후.decompose())))
    print("껍질", 기록[-1], flush=True)

# ---------- 저장(지역 좌표 · 부스러기 < 0.05 mm³ 버림) ----------
for k, m in 고친.items():
    n = 부[k]["n"]; Ti = np.linalg.inv(부[k]["T"])
    조각 = sorted(m.transform(Ti[:3, :].astype(np.float64)).decompose(), key=lambda p: -p.volume())
    버림 = round(sum(p.volume() for p in 조각[1:]), 2)          # 떨어진 조각은 붙일 데가 없다 → 가장 큰 하나만
    mm = 조각[0].to_mesh(); t = trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts, process=False)
    assert t.is_watertight, k
    기록.append(dict(저장=k, 파일="부품_%02d_조립.stl" % n, 부피=round(t.volume, 2), 버린조각mm3=버림))
    t.export(os.path.join(A.SRC, "부품_%02d_조립.stl" % n)); print("저장", 기록[-1])
json.dump(기록, open(os.path.join(A.OUT, "고침.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
