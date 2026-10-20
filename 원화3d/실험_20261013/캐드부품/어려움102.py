# 어려운 모양(CAD 부품 밖) — 렉스 · 오메가몬 머리 · 상체 · 거미 메카 다리 · 부엉이 발을 CAD 부품과 같은 파이프라인(데이터 · 앞옆 · 숨은선88 · 반 · 층32 · 입력51 · 껍질32)에 넣고 판정기준97 넓은 ∪ / ∩ 후보 덮음 · 10-20
# 사용(venv · ART_MEM_GB=12): 어려움102.py → out/설명/캐드부품/어려움102/자료.npz · 결과.json (150k 면 넘으면 open3d 로 줄인 stl 을 씀)
import sys, os, json, numpy as np
import 데이터 as D0, 데이터_앞옆 as DF, 숨은선88 as H88, 데이터69 as D69, 입력51 as I51, 껍질94 as K94, 짓기 as J, 여섯방향 as S6, 후보96 as H, 후보101 as P
O = "G:/art2real/out/설명/캐드부품/"; D = O + "어려움102/"; R = "G:/art2real/원화3d/out/레퍼런스/"; os.makedirs(D, exist_ok=True); N = 128; K = 32
모양 = {"렉스": "사람분할/1712661_Metal_Gear_Solid_Rex/rex-robot.stl", "오메가몬머리": "오메가몬_pomettini/obj_21_Head_fixed.stl", "오메가몬상체": "오메가몬_pomettini/obj_11_BodyUpper_fixed.stl",
        "거미다리": "사람분할/1081883_D13SpiderWalkerMech/leg-4x.stl", "부엉이발": "사람분할/1033970_D13Owl/owl-armor-foot-x2.stl"}
def 줄임(이름, p, 상한=140000):
    import trimesh
    m = trimesh.load(p, force="mesh")
    if len(m.faces) <= 상한: return p
    import open3d as o3d
    t = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(m.vertices), o3d.utility.Vector3iVector(m.faces)).simplify_quadric_decimation(상한); t.compute_vertex_normals()
    q = D + 이름 + ".stl"; o3d.io.write_triangle_mesh(q, t); print(이름, len(m.faces), "→", len(t.triangles), "면", flush=True); return q
def 하나(이름, p):
    p = 줄임(이름, R + p); r = D0.하나(p); assert r is not None, "데이터.하나 실패"; X, _, _, Hh = r
    F, S = DF.하나(p); 풀 = lambda b: np.unpackbits(b)[:N * N].reshape(N, N).astype(np.uint8); HX, HF, HS = [풀(b) for b in H88.하나(p)]
    v, f, _ = J.정규메시(p); 몸, _ = J.몸통37((X, F, S), Hh); 반 = np.array([S6.반높이(몸, S6.R(축, 도)) for k, (축, 도) in S6.방향.items()], np.float32)
    층 = D69.하나((p, 반)); 입 = I51.하나((X, F, S, 반)); 껍 = K94.하나((X, F, S, 반))
    return dict(X=X, F=F, S=S, HX=HX, HF=HF, HS=HS, 반=반, 층=층, 입=입, 껍=껍)
from math import comb
def 우연(c, g):   # 화소마다 후보 c 개를 32 층에서 무작위로 고르면 정답 g ±1 창(끝이면 2 칸)에 하나라도 들 몫
    w = np.where((g == 0) | (g == K - 1), 2, 3); t = np.array([[1 - comb(K - ww, cc) / comb(K, cc) for cc in range(K + 1)] for ww in (2, 3)])
    return t[w - 2, np.clip(c, 0, K)]
def 덮음(z, I):
    out = {}
    for 넓게, 합들 in ((False, (False,)), (True, (False, True))):
        H.열후보 = P.열후보_넓게 if 넓게 else P.원열후보; C = H.하나(z["X"], z["F"], z["S"], z["HX"], z["HF"], z["HS"], z["반"])
        for 합 in 합들:
            a = np.zeros(5); 빠 = np.zeros((6, N, N), bool)
            for n in range(6):
                q = ((C[n, 0][I[n, 0]] | C[n, 1][I[n, 1]]) if 합 else (C[n, 0][I[n, 0]] & C[n, 1][I[n, 1]])).astype(np.int64); g = z["층"][n].astype(np.int64)
                안 = (z["입"][n, 1] > 0) & (g < K); 깎 = 안 & (g >= z["껍"][n].astype(np.int64) + 2); bit = lambda L: ((q >> np.clip(L, 0, 31)) & 1) > 0; 곁 = bit(g) | bit(g - 1) | bit(g + 1)
                c = np.unpackbits(q.astype("<u4").view(np.uint8).reshape(N, N, 4), axis=-1).sum(-1); 우 = 우연(c, g)
                a += [깎.sum(), (곁 & 깎).sum(), 안.sum(), c[안].sum(), 우[깎].sum()]; 빠[n] = 깎 & ~곁
            out[("넓게 " if 넓게 else "96 수평 ") + ("∪" if 합 else "∩")] = {"깎인 화소": int(a[0]), "깎인 속 ±1": round(a[1] / max(a[0], 1), 3), "화소당 후보": round(a[3] / max(a[2], 1), 2), "무작위 후보 같은 수 ±1": round(a[4] / max(a[0], 1), 3)}
            if 넓게 and 합: z["빠"] = 빠
    return out
if __name__ == "__main__":
    I = np.load(O + "후보96_색인.npy").astype(np.int64); 결 = {}; 모두 = {}
    for 이름, p in [(a, b) for a, b in 모양.items() if len(sys.argv) < 2 or a in sys.argv[1:]]:
        try: z = 하나(이름, p)
        except Exception as ex: print(이름, "실패", type(ex).__name__, str(ex)[:120], flush=True); continue
        결[이름] = 덮음(z, I); 모두[이름] = z; print(이름, 결[이름], flush=True)
    np.savez_compressed(D + "자료.npz", **{f"{k}__{a}": v for k, z in 모두.items() for a, v in z.items()})
    json.dump(결, open(D + "결과.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("끝")
