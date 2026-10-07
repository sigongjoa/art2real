# -*- coding: utf-8 -*-
"""관절 인형 갑옷 세 벌을 같은 뼈대(Dummy 13 조립)에 끼운다 — 쇼츠 「이 세 피규어, 뼈대가 똑같습니다」(10-07).
갑옷 조각마다: 덮을 뼈대 부위 중심에 놓고 24 방향 × 위치 격자 → 점수 = 뼈대가 볼록 껍질 안에 든 비율 − 3 × 벽을 뚫은 비율.
앞뒤(180°)는 점수로 못 가를 수 있다 — 렌더를 보고 뼈대.py 의 ROT 로 고친다.
결과는 월드 좌표 STL 로 바로 저장(블렌더는 불러오기만) + 목록.json.
python 갑옷맞춤.py <뼈대_월드.npz> <모델: d13|bk|bs> <출력 폴더> [이름 조각,...]"""
import sys, os, json, itertools, numpy as np, trimesh, open3d as o3d
R0 = "G:/art2real/원화3d/out/레퍼런스/사람분할/"

def scene_of(m):
    s = o3d.t.geometry.RaycastingScene(); s.add_triangles(o3d.core.Tensor(m.vertices.astype(np.float32)), o3d.core.Tensor(m.faces.astype(np.uint32))); return s
def inside(s, p): return s.compute_occupancy(o3d.core.Tensor(p.astype(np.float32))).numpy() > 0.5
ROTS = [R.reshape(3, 3) for R in map(np.array, itertools.product(*[[-1, 0, 1]] * 9))]
ROTS = [R for R in ROTS if np.allclose(R @ R.T, np.eye(3)) and np.isclose(np.linalg.det(R), 1)]; assert len(ROTS) == 24

# 덮을 뼈대 고르기 — 열쇠는 「부품@쪽#번호」. low/high = 같은 이름 중 낮은 것(다리) · 높은 것(어깨)
def K(F, base, side, which=None, zmax=None):
    ks = sorted(k for k in F if k.startswith(base + "@" + side))
    if which == "low": ks = [min(ks, key=lambda k: F[k][0][:, 2].mean())]
    if which == "high": ks = [max(ks, key=lambda k: F[k][0][:, 2].mean())]
    if zmax is not None: ks = [k for k in ks if F[k][0][:, 2].mean() < zmax]
    return ks
T = {"머리": lambda F, s: K(F, "head", "C"), "목": lambda F, s: K(F, "neck", "C"), "가슴": lambda F, s: K(F, "chest", "C"),
     "몸통": lambda F, s: K(F, "chest", "C") + K(F, "abdomen", "C"), "배": lambda F, s: K(F, "abdomen", "C"), "허리": lambda F, s: K(F, "waist", "C"),
     "골반허리": lambda F, s: K(F, "hips", "C") + K(F, "waist", "C"),
     "엉덩관절": lambda F, s: K(F, "hip-and-shoulder-4x", s, "low"), "옆치마": lambda F, s: K(F, "hip-and-shoulder-4x", s, "low") + K(F, "thigh-2x", s),
     "허벅지": lambda F, s: K(F, "thigh-2x", s), "무릎": lambda F, s: K(F, "knee-and-elbow-4x", s, zmax=70), "정강이": lambda F, s: K(F, "shin-2x", s),
     "발목": lambda F, s: K(F, "ankle-2x", s), "어깨": lambda F, s: K(F, "hip-and-shoulder-4x", s, "high"),
     "어깨쇄골": lambda F, s: K(F, "hip-and-shoulder-4x", s, "high") + K(F, "clavicle-2x", s),
     "위팔": lambda F, s: K(F, "upper-arm-2x", s), "팔뚝": lambda F, s: K(F, "forearm-2x", s)}
# 모델별 표: (파일, 조각 번호 — None = 가장 큰 조각, 쪽, 부위, 방식 fit | front | hand)
LR = lambda f, part, mode="fit": [(f, None, "L", part, mode), (f, None, "R", part, mode)]
D13, BK, BS = "981111_Dummy13/", "1630920_블랙나이트_D13/", "1038885_베르세르크13/"
HANDS = [(D13 + "hand-fist-left.stl", None, "L", "손", "hand"), (D13 + "hand-fist-right.stl", None, "R", "손", "hand")]
PLANS = {
 "d13": [(D13 + "armor-head.stl", None, "C", "머리", "fit"), (D13 + "armor-neck.stl", None, "C", "목", "fit"), (D13 + "armor-outer-chest.stl", None, "C", "가슴", "fit"),
         (D13 + "armor-inner-chest.stl", None, "C", "가슴", "fit"), (D13 + "armor-abdomen.stl", None, "C", "배", "fit"), (D13 + "armor-waist.stl", None, "C", "허리", "fit"),
         (D13 + "armor-crotch.stl", None, "C", "골반허리", "front")]
        + LR(D13 + "armor-hip-2x.stl", "엉덩관절") + LR(D13 + "armor-thigh-2x.stl", "허벅지") + LR(D13 + "armor-knee-2x.stl", "무릎", "front") + LR(D13 + "armor-shin-2x.stl", "정강이")
        + LR(D13 + "armor-foot-2x.stl", "발목") + LR(D13 + "armor-shoulder-2x.stl", "어깨") + LR(D13 + "armor-upper-arm-2x.stl", "위팔") + LR(D13 + "armor-forearm-2x.stl", "팔뚝") + HANDS,
 "bk": [(BK + "armor-helmet.stl", None, "C", "머리", "fit"), (BK + "armor-chest.stl", None, "C", "몸통", "fit"), (BK + "armor-waist.stl", None, "C", "골반허리", "fit")]
       + [(BK + "armor-%s-%s.stl" % (n, s), None, s, p, "fit") for s in "LR" for n, p in
          (("hip", "엉덩관절"), ("side-plate", "옆치마"), ("thigh", "허벅지"), ("knee", "무릎"), ("shin", "정강이"), ("ankle", "발목"), ("foot", "발목"),
           ("shoulder", "어깨쇄골"), ("pauldron-plate", "어깨"), ("upper-arm", "위팔"), ("lower-arm", "팔뚝"))] + HANDS,
 "bs": [(BS + "1-helmjaws.stl", None, "C", "머리", "fit"), (BS + "2-chestplate-v3-hotfix.stl", 0, "L", "몸통반", "fit"), (BS + "2-chestplate-v3-hotfix.stl", 1, "R", "몸통반", "fit"), (BS + "21-innerchest.stl", None, "C", "가슴", "fit"),
        (BS + "3-abplate.stl", None, "C", "배", "fit"), (BS + "4-buttplate.stl", None, "C", "골반허리", "fit"), (BS + "41-crotch.stl", None, "C", "골반허리", "front"),
        (BS + "5-upperlegs-hotfix-v3.stl", 0, "L", "허벅지", "fit"), (BS + "5-upperlegs-hotfix-v3.stl", 1, "R", "허벅지", "fit"),
        (BS + "6-lowerlegs.stl", 0, "L", "정강이", "fit"), (BS + "6-lowerlegs.stl", 1, "R", "정강이", "fit")]
       + LR(BS + "61-footx1-hotfixv2.stl", "발목") + LR(BS + "7-shoulder-2x.stl", "어깨쇄골") + LR(BS + "8-forearm-2x.stl", "팔뚝")
       + [(BS + "91-hands.stl", 0, "L", "손", "hand"), (BS + "91-hands.stl", 1, "R", "손", "hand")]}

SCALE = {"d13": 1.0, "bk": 1 / 1.5, "bs": 1 / 1.5}   # 베르세르크 동봉 뼈대가 D13 의 1.5 배(정강이 50.2 대 33.5) — 150 % 출력용 갑옷을 100 % 뼈대에 맞춰 줄인다
def load_piece(path, comp, k=1.0):
    m = trimesh.load(R0 + path, force="mesh"); cs = sorted(m.split(only_watertight=False), key=lambda c: -c.area)
    c = cs[0] if comp is None else cs[comp] if comp < len(cs) else cs[0]; c = c.copy(); c.apply_scale(k); return c

def fit(A, tgt, near_all, coarse=2.0, span=6.0):
    c0 = (A.bounds[0] + A.bounds[1]) / 2; ctr = tgt.mean(0); best = (-9, None, None)
    near = near_all[np.linalg.norm(near_all - ctr, axis=1) < max(A.extents) * 1.2]
    span = max(span, max(A.extents) * 0.25); coarse = max(coarse, span / 5)   # 큰 갑옷은 넓게 · 성기게(격자 11³ 유지)
    for R in ROTS:
        Ar = A.copy(); Ar.apply_translation(-c0); Ar.apply_transform(np.block([[R, np.zeros((3, 1))], [0, 0, 0, 1]]))
        hs, ss = scene_of(Ar.convex_hull), scene_of(Ar)
        def score(t): return inside(hs, tgt - ctr - t).mean() - 3 * inside(ss, near - ctr - t).sum() / len(tgt)
        g = np.arange(-span, span + 1e-6, coarse); cand = max(((score(np.array(t)), np.array(t)) for t in itertools.product(g, g, g)), key=lambda x: x[0])
        for step in (1.0, 0.5):
            g2 = np.arange(-step, step + 1e-6, step / 2 if step < 1 else step)
            cand = max([cand] + [(score(cand[1] + np.array(d)), cand[1] + np.array(d)) for d in itertools.product(g2, g2, g2)], key=lambda x: x[0])
        if cand[0] > best[0]: best = (cand[0], R, cand[1])
    sc, R, t = best; M = np.eye(4); M[:3, :3] = R; M[:3, 3] = ctr + t - R @ c0
    return sc, M

def front_plate(A, P):   # 감싸지 않고 앞(−Y)에 붙는 판: 얇은 축 = 앞뒤 · 긴 축 = 세로
    e = A.extents; o = np.argsort(e); R = np.zeros((3, 3)); R[1, o[0]] = 1; R[2, o[2]] = 1; R[0, o[1]] = 1
    if np.linalg.det(R) < 0: R[0] *= -1
    ctr = P.mean(0); c0 = (A.bounds[0] + A.bounds[1]) / 2; M = np.eye(4); M[:3, :3] = R
    M[:3, 3] = np.array([ctr[0], P[:, 1].min() - e[o[0]] / 2 - 0.3, ctr[2]]) - R @ c0; return 1.0, M

if __name__ == "__main__":
    npz, model, out = sys.argv[1:4]; only = sys.argv[4].split(",") if len(sys.argv) > 4 else None
    os.makedirs(out, exist_ok=True)
    Z = np.load(npz); F = {k[:-2]: (Z[k], Z[k[:-2] + "|f"]) for k in Z.files if k.endswith("|v") and not k.startswith("Cube")}
    def pts(keys, n=1500):
        ms = [trimesh.Trimesh(*F[k], process=False) for k in keys]; return np.concatenate([trimesh.sample.sample_surface_even(m, n // len(ms) + 1, seed=0)[0] for m in ms])
    ALL = pts(list(F), 9000); res = []
    for path, comp, side, part, mode in PLANS[model]:
        name = os.path.basename(path)[:-4] + ("" if comp is None else "#%d" % comp)
        if only and not any(o in name for o in only): continue
        A = load_piece(path, comp, 1.0 if path.startswith(D13) else SCALE[model])
        if mode == "hand":   # 손목 공(팔뚝 맨 아래)을 손 소켓이 물고 · 손은 그 아래로
            fv = F[K(F, "forearm-2x", side)[0]][0]; w = fv[fv[:, 2] < fv[:, 2].min() + 5.8].mean(0); w[2] = fv[:, 2].min() + 3.0
            sph = trimesh.creation.icosphere(2, 3.0).vertices + w; sc, M = fit(A, np.concatenate([sph, sph - [0, 0, 6]]), ALL, span=4.0)
        elif mode == "front": sc, M = front_plate(A, pts(T[part](F, side)))
        elif part == "몸통반":   # 반쪽 갑옷: 그 쪽 몸통 점만(L = +X)
            P = pts(T["몸통"](F, side) if False else K(F, "chest", "C") + K(F, "abdomen", "C"), 3000); P = P[(P[:, 0] > 0) == (side == "L")]
            sc, M = fit(A, P, ALL)
        else: sc, M = fit(A, pts(T[part](F, side)), ALL)
        B = A.copy(); B.apply_transform(M); f = "%s/%s@%s.stl" % (out, name, side); B.export(f)
        res.append({"갑옷": name, "쪽": side, "부위": part, "파일": f, "점수": round(float(sc), 3), "손": mode == "hand"}); print(name, side, part, "점수 %.2f" % sc, flush=True)
    J = out + "/목록.json"; old = json.load(open(J, encoding="utf-8")) if os.path.exists(J) else []
    keep = {(r["갑옷"], r["쪽"]) for r in res}; json.dump([r for r in old if (r["갑옷"], r["쪽"]) not in keep] + res, open(J, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
