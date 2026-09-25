# -*- coding: utf-8 -*-
r"""가동검사 — 관절마다 자식 하위 트리를 축 둘레로 돌리며 간섭 부피 V(θ) 를 잰다.

V(θ) = Σ vol( 부풀린 자식 부품(θ) ∩ 고정 부품 )   (부풀림 = 구 c 와 민코프스키 합, c = 0.3 mm)
가동 범위 = 0° 에서 이어진 V < ε 구간 (ε = 0.5 mm³). 2° 간격, −180°~+180°.
고정 부품 = 자식 하위 트리 밖의 모든 부품 (부모만이 아니라 몸 전체).

입력
  부품 : out/출력/오메가몬_E13키트/_조립/부품NN.stl (조립 좌표 mm, z 위, 작은 y 가 앞, 작은 x 가 L)
  관절 : out/가동/관절.json (J1, 300 mm 골격 좌표) — 부품을 골격.py 의 mm() 식으로 옮겨 맞춘다(×2.396).
         뼈→부품은 관절.json 의 '뼈부품' 이 있으면 그것, 없으면 E13 이름 · 가장 가까운 뼈 마디로 배정.
         관절.json 이 없으면 임시 관절(E13 경계면 중심 · 세계축)을 쓰고 out/가동/관절_임시.json 으로 적는다.
  J2 관절 부품이 붙은 키트를 재려면 KIT · 이름.json · E13_J1() 좌표변환 세 곳을 그 키트 것으로 바꾼다.
출력
  out/가동/가동범위.json · 가동범위.png · 막힘_<관절>_<축>.png · 가동검사.log

실행: python 실험_20260925/가동검사.py [--자만]
"""
import json, sys, time
from pathlib import Path
import numpy as np
import trimesh
import manifold3d as M
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
KIT = ROOT / 'out/출력/오메가몬_E13키트/_조립'
OUT = ROOT / 'out/가동'
C = 0.3        # 틈(한쪽) mm — 자식을 이만큼 부풀린다
EPS = 0.5      # mm³
STEP = 2       # °
ANG = np.arange(-180, 180 + STEP, STEP)


# ---------------------------------------------------------------- 기하 기본
def 만(tm):
    return M.Manifold(M.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                             tri_verts=np.asarray(tm.faces, np.uint32)))


def 트(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)


def 부풀(m, c=C):
    return m.minkowski_sum(M.Manifold.sphere(c, 8)) if c > 0 else m


def 회전(axis, pivot, deg):
    return trimesh.transformations.rotation_matrix(np.radians(deg), axis, pivot)[:3, :4]


def 상자겹침(a, b):
    return all(a[k] <= b[k + 3] and b[k] <= a[k + 3] for k in range(3))


def 곡선(움직, 고정, pivot, axis, angles=ANG):
    """움직: {id: 부풀린 manifold}, 고정: {id: manifold}. → V 배열, 각 θ 의 짝 부피 dict."""
    gbb = {j: m.bounding_box() for j, m in 고정.items()}
    V, 짝들 = [], []
    for th in angles:
        T = 회전(axis, pivot, th)
        짝 = {}
        for i, m in 움직.items():
            mt = m.transform(T)
            bb = mt.bounding_box()
            for j, g in 고정.items():
                if 상자겹침(bb, gbb[j]):
                    v = (mt ^ g).volume()
                    if v > 1e-4:
                        짝[(i, j)] = v
        V.append(sum(짝.values()))
        짝들.append(짝)
    return np.array(V), 짝들


def 범위(angles, V, eps=EPS, 기준=0.0):
    """0° 에서 이어진 V−기준 < eps 구간. 0° 부터 막히면 None."""
    W = V - 기준
    i0 = int(np.argmin(np.abs(angles)))
    if W[i0] >= eps:
        return None
    hi = i0
    while hi + 1 < len(W) and W[hi + 1] < eps:
        hi += 1
    lo = i0
    while lo - 1 >= 0 and W[lo - 1] < eps:
        lo -= 1
    return [float(angles[lo]), float(angles[hi])]


# ---------------------------------------------------------------- 자 시험 (해석해)
def _원(c, ρ, r, a, L):
    """원기둥 막대(반지름 r, x∈[a,a+L]) 를 y 축 둘레로 돌릴 때, xz 단면 원(중심 c, 반지름 ρ)과
    부풀린 막대(c 만큼 둥근 직사각형)가 닿는 각을 이분법으로 — 닫힌 식 거리의 근."""
    def 거리(th):  # 원 중심을 막대 좌표로 되돌려 직사각형까지 거리
        R = trimesh.transformations.rotation_matrix(np.radians(-th), [0, 1, 0])[:3, :3]
        p = R @ np.array([c[0], 0, c[1]])
        dx = max(a - p[0], 0, p[0] - (a + L)); dz = max(abs(p[2]) - r, 0)
        return np.hypot(dx, dz) - ρ - C
    return 거리


def _근(f, lo, hi):
    """lo 에서 올라가며 f 가 처음 0 이하가 되는 각 (0.01° 훑기 — f 가 단조가 아니어서)."""
    for t in np.arange(lo, hi, 0.01):
        if f(t) <= 0:
            return float(t)
    raise ValueError('안 닿음')


def 자시험():
    y = np.array([0, 1, 0.])
    결과 = {}
    # ① 원기둥 둘: 자식 막대(+x, r=2, x∈[2,20]) · 부모 원기둥(축 ∥ y, 반지름 3) 이 아래(−z)와 위(+z)에
    r, a, L, ρ = 2.0, 2.0, 18.0, 3.0
    막대 = M.Manifold.cylinder(L, r, r, 64).rotate([0, 90, 0]).translate([a, 0, 0])   # z→x
    아래c, 위c = (12.0, -(r + ρ + 2.0)), (9.0, r + ρ + 4.0)
    def 기둥(c):
        return M.Manifold.cylinder(40, ρ, ρ, 96).rotate([90, 0, 0]).translate([c[0], 20, c[1]])  # 축 ∥ y
    고정 = {'아래': 기둥(아래c), '위': 기둥(위c)}
    V, _ = 곡선({'막대': 부풀(막대)}, 고정, [0, 0, 0], y)
    rg = 범위(ANG, V)
    # y 축 +θ 회전은 +x 를 −z 로 → 아래 기둥이 + 쪽, 위 기둥이 − 쪽을 막는다
    해_아래 = _근(_원(아래c, ρ, r, a, L), 0, 90)
    해_위 = -_근(lambda t: _원(위c, ρ, r, a, L)(-t), 0, 90)
    결과['원기둥'] = dict(잰=rg, 해석=[round(해_위, 2), round(해_아래, 2)], V0=float(V[90]))
    assert rg is not None and abs(rg[1] - 해_아래) <= 2 + 1e-6 and abs(rg[0] - 해_위) <= 2 + 1e-6, 결과['원기둥']

    # ② 상자 쌍: 판(x∈[0,20], z∈[0,3]) 을 y 축으로 들어 올려 천장 상자(z ≥ d) 에 닿는 각
    Lb, t, d = 20.0, 3.0, 9.0
    판 = M.Manifold.cube([Lb, 10, t]).translate([0, -5, 0])
    천장 = M.Manifold.cube([60, 30, 10]).translate([-30, -15, d])
    V2, _ = 곡선({'판': 부풀(판)}, {'천장': 천장}, [0, 0, 0], -y)   # −y 축 +θ 가 +x 를 +z 로
    rg2 = 범위(ANG, V2)
    R, φ = np.hypot(Lb, t), np.degrees(np.arctan2(t, Lb))
    해2 = np.degrees(np.arcsin((d - C) / R)) - φ          # L sinθ + t cosθ + c = d
    결과['상자'] = dict(잰상한=rg2 and rg2[1], 해석=round(float(해2), 2), V0=float(V2[90]))
    assert rg2 is not None and abs(rg2[1] - 해2) <= 2 + 1e-6, 결과['상자']

    # ③ 정지 자세 V≈0 · 그리고 겹친 조립은 잡혀야 한다(자가 질 수 있는지)
    assert V[90] < 1e-3 and V2[90] < 1e-3
    겹친 = {'판': 부풀(판.translate([0, 0, d - t + 0.5]))}
    V3, _ = 곡선(겹친, {'천장': 천장}, [0, 0, 0], -y, angles=np.array([0]))
    결과['겹친조립V0'] = float(V3[0])
    assert V3[0] > EPS and 범위(np.array([0]), V3) is None
    # ④ 깎기 칸 자: 구멍 뚫린 상자 · 구의 칸 부피가 참 부피 ±3 % 안
    for 몸 in (M.Manifold.cube([10, 10, 10]) - M.Manifold.cube([4, 4, 20]).translate([3, 3, -5]),
               M.Manifold.sphere(7, 64).translate([1.1, 2.3, 0.7])):
        mat, _ = 격자(몸)
        assert abs(mat.sum() * 칸h ** 3 / 몸.volume() - 1) < 0.03
    결과['칸부피'] = '±3 % 통과'
    return 결과


# ---------------------------------------------------------------- 관절 · 뼈
이름 = json.loads((ROOT / 'out/분할후보/E13/이름.json').read_text(encoding='utf-8'))
nm = lambda i: f'{i}:{이름[str(i)]}'


def E13_J1():
    """E13 조립 mm → J1 골격 mm (골격.py 의 mm() 와 같은 식). E13 mm = 192 색인 × 칸mm."""
    k = json.loads((KIT.parent / '키트.json').read_text(encoding='utf-8'))['칸mm']
    d = np.load(ROOT / 'out/분할후보/입력.npz'); O = d['O']
    zs = np.nonzero(O.any((0, 1)))[0]; Cj = 300.0 / (zs[-1] - zs[0] + 1)
    y0 = np.argwhere(O[:, :, zs[0]:zs[0] + 2])[:, 1].mean()
    T = np.eye(4); T[:3, :3] *= Cj / k; T[:3, 3] = -np.array([float(d['축i']), y0, zs[0] - 0.5]) * Cj
    return T


# J1 관절.json 이 없을 때만 쓰는 임시 관절 (E13 좌표: z 위, 앞 −y, L 은 작은 x)
기본뼈 = {'몸통': [2, 19, 41, 3, 20], '머리': [1, 18], 'L윗팔': [38, 9, 39, 10, 25], 'L팔끝': [11, 12, 26, 30, 13],
         'R윗팔': [14, 40, 15, 27], 'R팔끝': [16, 28, 17, 29], '허리': [4, 21], 'L허벅지': [5, 22], 'L정강이': [6, 7, 23],
         'L발': [8, 24], 'R허벅지': [31, 35], 'R정강이': [32, 33, 36], 'R발': [34, 37]}
X, Y, Z, nX, nY = [1., 0, 0], [0, 1., 0], [0, 0, 1.], [-1., 0, 0], [0, -1., 0]
임시 = [  # 이름, 부모, 자식, [(축, 최소, 최대)]  — 앞으로 들기 = −x 축, 무릎 뒤로 = +x, L 벌림 = +y
    ('목', '몸통', '머리', [(Z, -60, 60), (nX, -15, 30)]),
    ('L어깨', '몸통', 'L윗팔', [(Y, 0, 90), (nX, -180, 180)]), ('R어깨', '몸통', 'R윗팔', [(nY, 0, 90), (nX, -180, 180)]),
    ('L팔꿈치', 'L윗팔', 'L팔끝', [(nX, 0, 150)]), ('R팔꿈치', 'R윗팔', 'R팔끝', [(nX, 0, 150)]),
    ('허리', '몸통', '허리', [(Z, -45, 45), (nX, -15, 15)]),
    ('L고관절', '허리', 'L허벅지', [(nX, 0, 90), (Y, 0, 45)]), ('R고관절', '허리', 'R허벅지', [(nX, 0, 90), (nY, 0, 45)]),
    ('L무릎', 'L허벅지', 'L정강이', [(X, 0, 150)]), ('R무릎', 'R허벅지', 'R정강이', [(X, 0, 150)]),
    ('L발목', 'L정강이', 'L발', [(X, -30, 30), (Y, -25, 25)]), ('R발목', 'R정강이', 'R발', [(X, -30, 30), (nY, -25, 25)])]


def 경계중심(pa_mesh, pc_mesh, tol=0.5):
    pa = trimesh.sample.sample_surface_even(pa_mesh, 30000, seed=0)[0]
    pc = trimesh.sample.sample_surface_even(pc_mesh, 30000, seed=1)[0]
    d, _ = cKDTree(pa).query(pc)
    return pc[d < tol].mean(0)


def 관절읽기(메시E13):
    """→ (관절 목록[J1 형식], 뼈→부품, 좌표변환 4x4, 출처). J1 형식: 이름·부모뼈·자식뼈·피벗mm·범위[{축,최소,최대}]."""
    p = OUT / '관절.json'
    if p.exists():
        d = json.loads(p.read_text(encoding='utf-8'))
        T = E13_J1()
        return d['관절'], d.get('뼈부품'), d.get('뼈', {}), T, 'J1 관절.json'
    합 = lambda ids: trimesh.util.concatenate([메시E13[i] for i in ids])
    관절 = [dict(이름=n, 부모뼈=a, 자식뼈=b, 피벗mm=[round(float(v), 2) for v in 경계중심(합(기본뼈[a]), 합(기본뼈[b]))],
                 범위=[dict(축=ax, 최소=lo, 최대=hi) for ax, lo, hi in r]) for n, a, b, r in 임시]
    (OUT / '관절_임시.json').write_text(json.dumps(dict(관절=관절, 뼈부품=기본뼈), ensure_ascii=False, indent=1), encoding='utf-8')
    return 관절, 기본뼈, {}, np.eye(4), '임시(E13 경계면 중심)'


def 부품배정(메시, 관절, 뼈):
    """뼈→부품. ① E13 이름(앞/뒤 뗀)에 뼈 이름이 들어 있으면 가장 긴 것 ② 아니면 겉 표본이 가장 많이 가까운 뼈 마디."""
    bones = sorted({j['자식뼈'] for j in 관절} | {j['부모뼈'] for j in 관절})
    node, lab = [], []
    for b in bones:
        for poly in (뼈.get(b) or {}).get('마디', []):
            for q in poly: node.append(q[:3]); lab.append(b)
    tree = cKDTree(np.array(node)); lab = np.array(lab)
    out = {b: [] for b in bones}
    무리 = {}
    for i in 메시:  # 앞/뒤 짝은 같이 간다
        무리.setdefault(이름[str(i)].replace('앞', '').replace('뒤', ''), []).append(i)
    for n, ids in 무리.items():
        hit = sorted([b for b in bones if b in n], key=len)
        if hit:
            out[hit[-1]] += ids; continue
        p = np.vstack([trimesh.sample.sample_surface_even(메시[i], 2000, seed=i)[0] for i in ids])
        v, c = np.unique(lab[tree.query(p)[1]], return_counts=True)
        out[v[np.argmax(c)]] += ids
    return out


def 하위(관절, 뿌리):
    자식 = {}
    for j in 관절: 자식.setdefault(j['부모뼈'], []).append(j['자식뼈'])
    s, 쌓 = [], [뿌리]
    while 쌓:
        b = 쌓.pop(); s.append(b); 쌓 += 자식.get(b, [])
    return s


def 축표기(a):
    a = np.asarray(a, float); k = int(np.argmax(np.abs(a)))
    return ('+' if a[k] > 0 else '-') + 'xyz'[k] + ('' if abs(a[k]) > .99 else '~')


# ---------------------------------------------------------------- 일꾼 (프로세스마다 부품을 한 번 읽는다)
G = {}


def _메시(T):
    out = {}
    for i in range(1, 42):
        m = trimesh.load(KIT / f'부품{i:02d}.stl'); m.apply_transform(T); out[i] = m
    return out


def _부풀일(args):
    i, T, f = args
    m = trimesh.load(KIT / f'부품{i:02d}.stl'); m.apply_transform(T)
    트(부풀(만(m))).export(f)
    return i


def _init(T, 캐시, 표본):
    G['메시'] = _메시(T)
    G['원'] = {i: 만(m) for i, m in G['메시'].items()}
    G['부'] = {i: 만(trimesh.load(캐시 / f'{i:02d}.stl')) for i in range(1, 42)}
    G['표본'] = 표본


def 행(r):
    t행 = time.time()
    원, 부, 표본 = G['원'], G['부'], G['표본']
    움, 고 = r['움'], r['고']
    piv, axis, 목표 = np.array(r['피벗']), np.array(r['방향']), r['목표']
    gbb = {j: 원[j].bounding_box() for j in 고}

    def 잼(th, keep):
        T = 회전(axis, piv, th); 짝, 조각 = {}, {}
        for i in 움:
            mt = 부[i].transform(T); bb = mt.bounding_box()
            for j in 고:
                if 상자겹침(bb, gbb[j]):
                    k = mt ^ 원[j]; v = k.volume()
                    if v > 1e-4:
                        짝[(i, j)] = v
                        if keep: 조각.setdefault(j, []).append(k)
        return 짝, 조각

    짝0, _ = 잼(0, False)
    V0 = sum(짝0.values())
    V = {0: V0}; 짝들 = {0: 짝0}
    for side in (1, -1):  # ponytail: 막힌 뒤 10° 까지만 잰다 — 전 구간 곡선이 필요하면 여유를 늘린다
        th, 막 = 0, None
        while abs(th + 2 * side) <= 180:
            th += 2 * side
            if 막 is not None and abs(th - 막) > 10: break
            짝, _ = 잼(th, False)
            V[th] = sum(짝.values()); 짝들[th] = 짝
            if 막 is None and V[th] - V0 >= EPS: 막 = th
    angs = np.array(sorted(V)); Va = np.array([V[a] for a in angs])
    rg, rg_rel = 범위(angs, Va), 범위(angs, Va, 기준=V0)
    top = lambda 짝: [[nm(a), nm(b), round(v, 1)] for (a, b), v in sorted(짝.items(), key=lambda kv: -kv[1])[:4]]
    막는곳 = {}
    for side, 끝 in (('+', 1), ('-', 0)):
        e = rg_rel[끝] if rg_rel else 0
        nxt = e + (STEP if side == '+' else -STEP)
        if nxt in 짝들:
            막는곳[side] = dict(각=float(nxt), 짝=top({k: v - 짝0.get(k, 0) for k, v in 짝들[nxt].items() if v - 짝0.get(k, 0) > 1e-3}))
    채움 = bool(rg and rg[0] <= 목표[0] and rg[1] >= 목표[1])
    out = dict(순=r['순'], 관절=r['관절'], 축=r['축'], 방향=r['방향'], 피벗=r['피벗'], 목표=목표, 움직부품=움,
               잰범위=rg, 잰범위_정지겹침빼고=rg_rel, V0=round(V0, 1), V0짝=top(짝0), 목표채움=채움, 막는곳=막는곳,
               V={int(a): round(float(v), 2) for a, v in zip(angs, Va)})
    if not 채움:
        # 목표 중 못 가는 몫 [잰 끝, 목표 끝] 을 2° 로 쓸어, 고정 부품의 칸(0.4 mm) 중 부풀린 자식이 한 번이라도 지나간 칸 = 깎을 곳.
        # 메시 합집합은 거의 같은 조각(제 축 둘레로 도는 칼 등)에서 멈춰 서서 칸으로 센다.
        e = rg_rel or [0, 0]
        angs_c = np.unique(np.round((np.concatenate([np.arange(e[1], 목표[1] + 1e-9, STEP), np.arange(e[0], 목표[0] - 1e-9, -STEP)]) + 180) % 360 - 180, 3))
        모서리 = {i: np.array(np.meshgrid(*zip(부[i].bounding_box()[:3], 부[i].bounding_box()[3:]))).reshape(3, -1).T for i in 움}
        상자들 = []  # (θ, i, 돌린 자식 i 의 세계 AABB)
        for th in angs_c:
            T = 회전(axis, piv, th)
            for i in 움:
                c = 모서리[i] @ T[:, :3].T + T[:, 3]; 상자들.append((th, i, c.min(0), c.max(0)))
        깎 = []
        for j in 고:
            bb = np.array(원[j].bounding_box())
            mine = [(th, i, lo, hi) for th, i, lo, hi in 상자들 if np.all(lo <= bb[3:]) and np.all(bb[:3] <= hi)]
            if not mine: continue
            pts, nrm, a1, 겉 = 표본[j]
            PV, PS = 칸점(j), pts[겉] - 0.2 * nrm[겉]
            hitV = np.zeros(len(PV), bool); hitS = np.zeros(len(PS), bool)
            for th, i, lo, hi in mine:
                Rinv = 회전(axis, piv, -th)
                for P_, hit in ((PV, hitV), (PS, hitS)):
                    sel = np.flatnonzero(~hit & np.all((P_ >= lo) & (P_ <= hi), axis=1))
                    if len(sel):
                        hit[sel[칸안(i, P_[sel] @ Rinv[:, :3].T + Rinv[:, 3])]] = True
            vol = float(hitV.sum() * 칸h ** 3)
            if vol < EPS: continue
            겉면적 = float(hitS.sum() * a1)
            깎.append(dict(부품=nm(j), 깎을부피mm3=round(vol, 1), 겉면적mm2=round(겉면적, 1),
                          판정='겉 — 장갑을 가르거나 연동' if 겉면적 > 2 else '속 — 깎아도 안 보임'))
        out['깎기'] = sorted(깎, key=lambda d: -d['깎을부피mm3'])
    if r.get('스냅') and 막는곳:
        side = '+' if 목표[1] >= -목표[0] else '-'
        side = side if side in 막는곳 else next(iter(막는곳))
        th = 막는곳[side]['각']
        blk = sorted({int(s[1].split(':')[0]) for s in 막는곳[side]['짝']})
        T = 회전(axis, piv, th)
        겹 = [트(부[a].transform(T) ^ 원[b]) for a in 움 for b in blk if (부[a].transform(T) ^ 원[b]).volume() > 1e-3]
        p = OUT / f"막힘_{r['관절']}_{r['축']}.png"
        그림_막힘(G['메시'], 움, sorted(set(blk) | set(r['부모부품'])), 겹, piv, axis, th,
                 f"{r['관절']} {r['축']} θ={th:+.0f}° 첫 막힘 (파랑 자식 · 빨강 겹침)", p)
        out['스냅샷'] = str(p.relative_to(ROOT))
    out['초'] = round(time.time() - t행, 1)
    return out


칸h = 0.4


def 격자(m, h=None):
    """manifold → (칸 bool[nx,ny,nz], 원점). 칸 (i,j,k) 중심 = 원점 + h·(i,j,k). z 로 자른 단면을 짝홀 채우기."""
    from skimage.draw import polygon
    h = h or 칸h
    bb = np.array(m.bounding_box()); t0 = bb[:3] - 0.5 * h - 1e-3
    n = np.ceil((bb[3:] - t0) / h).astype(int) + 2
    mat = np.zeros(n, bool)
    for k in range(n[2]):
        for c in m.slice(float(t0[2] + k * h)).to_polygons():
            c = np.asarray(c)
            rr, cc = polygon((c[:, 0] - t0[0]) / h, (c[:, 1] - t0[1]) / h, n[:2])
            mat[rr, cc, k] ^= True
    return mat, t0


def 칸점(j):
    """고정 부품 j(원래 크기)의 채운 칸 중심 — 부피 셈용."""
    k = ('원점', j)
    if k not in G:
        mat, t0 = 격자(G['원'][j])
        G[k] = np.argwhere(mat) * 칸h + t0
    return G[k]


def 칸안(i, P):
    """점 P 가 부풀린 부품 i 안인가 (0.4 mm 칸 격자 조회)."""
    k = ('부칸', i)
    if k not in G:
        G[k] = 격자(G['부'][i])
    mat, t0 = G[k]
    idx = np.round((P - t0) / 칸h).astype(int)
    ok = np.all((idx >= 0) & (idx < mat.shape), axis=1)
    out = np.zeros(len(P), bool)
    out[ok] = mat[idx[ok, 0], idx[ok, 1], idx[ok, 2]]
    return out


def 표본만들기(메시):
    """부품마다 겉 표본(약 1 점/mm², PG 척도) · '몸 겉에 드러남' = 다른 부품에서 0.4 mm 밖."""
    S = {}
    for i, m in 메시.items():
        p, f = trimesh.sample.sample_surface_even(m, max(2000, int(m.area)), seed=i)
        S[i] = [p, m.face_normals[f], m.area / len(p)]
    for i in S:
        others = np.vstack([S[j][0] for j in S if j != i])
        d, _ = cKDTree(others).query(S[i][0], distance_upper_bound=0.6)
        S[i].append(d > 0.4)
    return S


# ---------------------------------------------------------------- 그림
def _한글():
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family'] = 'Malgun Gothic'; plt.rcParams['axes.unicode_minus'] = False
    return plt


def 그림_곡선(rows, path):
    plt = _한글()
    n = len(rows); cols = 6; rr = (n + cols - 1) // cols
    fig, axs = plt.subplots(rr, cols, figsize=(3.3 * cols, 2.3 * rr), squeeze=False)
    for ax, r in zip(axs.flat, rows):
        a = np.array(sorted(r['V'])); V = np.array([r['V'][k] for k in a])
        ax.axvspan(*r['목표'], color='#9ecae1', alpha=.5, lw=0)
        if r['잰범위_정지겹침빼고']: ax.axvspan(*r['잰범위_정지겹침빼고'], color='#fdae6b', alpha=.6, lw=0)
        if r['잰범위']: ax.axvspan(*r['잰범위'], color='#31a354', alpha=.5, lw=0)
        ax.plot(a, np.maximum(V, 1e-2), '.-', color='#333', lw=.8, ms=1.5)
        ax.axhline(EPS, color='#d62728', lw=.7, ls='--')
        ax.axhline(r['V0'] + EPS, color='#e6550d', lw=.7, ls=':')
        ax.set_yscale('log'); ax.set_ylim(1e-2, max(10, V.max() * 2)); ax.set_xlim(-180, 180)
        ax.set_xticks([-180, -90, 0, 90, 180]); ax.tick_params(labelsize=6)
        rel = r['잰범위_정지겹침빼고']
        ax.set_title(f"{r['관절']} {r['축']} 목표{r['목표']}\n잰 {r['잰범위'] or '0°부터'} · 정지빼고 {rel or '0°부터'}", fontsize=7)
    for ax in list(axs.flat)[n:]: ax.axis('off')
    fig.suptitle(f'V(θ) mm³ (log, 2° 간격) · 자식 +{C} mm 부풀림 · 파랑 = 목표 · 초록 = V<ε({EPS}) 구간 · 주황 = V-V(0)<ε 구간 · '
                 '빨간 점선 ε · 주황 점선 V(0)+ε', fontsize=10)
    fig.tight_layout(); fig.savefig(path, dpi=100); plt.close(fig)


def 그림_막힘(메시, 움직ids, 고정ids, 겹침들, pivot, axis, th, 제목, path):
    plt = _한글()
    from matplotlib.collections import PolyCollection
    a = np.asarray(axis, float); a /= np.linalg.norm(a)
    u = np.cross(a, [0, 0, 1.]) if abs(a[2]) < .9 else np.cross(a, [1., 0, 0]); u /= np.linalg.norm(u)
    v = np.cross(a, u)
    if v[2] < 0: u, v = -u, -v   # 위가 위로
    T4 = np.vstack([회전(axis, pivot, th), [0, 0, 0, 1]])
    fig, ax = plt.subplots(figsize=(5, 5))
    def 그려(tm, col):
        P = tm.vertices[tm.faces]; o = np.argsort(-(P.mean(1) @ a))   # 축 + 쪽에서 본다 → 먼 것부터
        c = np.clip(np.outer(np.abs(tm.face_normals @ a) * .55 + .45, col), 0, 1)
        ax.add_collection(PolyCollection(np.stack([P @ u, P @ v], -1)[o], facecolors=c[o], edgecolors='none'))
    moved = [메시[i].copy().apply_transform(T4) for i in 움직ids]
    for j in 고정ids: 그려(메시[j], [.8, .8, .8])
    for m in moved: 그려(m, [.35, .55, .85])
    for k in 겹침들: 그려(k, [1, .1, .1])
    P = np.vstack([메시[j].vertices for j in 고정ids] + [m.vertices for m in moved])
    ax.set_xlim((P @ u).min() - 2, (P @ u).max() + 2); ax.set_ylim((P @ v).min() - 2, (P @ v).max() + 2)
    pv = np.asarray(pivot); ax.plot(pv @ u, pv @ v, 'k+', ms=12)
    ax.set_aspect('equal'); ax.set_title(제목, fontsize=9); ax.set_xticks([]); ax.set_yticks([])
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


# ---------------------------------------------------------------- 본체
스냅관절 = ('목위', 'L어깨들기', 'L팔꿈치', 'L고관절', 'L무릎', '복부허리', 'L발목', 'R팔꿈치',
          '목', 'L어깨', '허리')


def main():
    from multiprocessing import Pool
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    로그 = open(OUT / '가동검사.log', 'w', encoding='utf-8')
    def 말(*a):
        s = ' '.join(map(str, a)); print(s, flush=True); 로그.write(s + '\n'); 로그.flush()
    자 = 자시험()
    말('자 시험 통과', json.dumps(자, ensure_ascii=False))
    if '--자만' in sys.argv: return
    메시E13 = {i: trimesh.load(KIT / f'부품{i:02d}.stl') for i in range(1, 42)}
    관절, 뼈부품, 뼈, T, 출처 = 관절읽기(메시E13)
    메시 = {i: m.copy().apply_transform(T) for i, m in 메시E13.items()}
    tag = 'J1' if 출처.startswith('J1') else 'E13'
    캐시 = OUT / f'_부풀림c{C}_{tag}'; 캐시.mkdir(exist_ok=True)
    일 = [(i, T, 캐시 / f'{i:02d}.stl') for i in range(1, 42) if not (캐시 / f'{i:02d}.stl').exists()]
    with Pool(8) as P:
        P.map(_부풀일, 일)
    말(f'부풀림 {len(일)} 부품 {time.time() - t0:.0f}s')
    뼈부품 = 뼈부품 or 부품배정(메시, 관절, 뼈)
    말('뼈→부품', json.dumps({b: [nm(i) for i in v] for b, v in 뼈부품.items() if v}, ensure_ascii=False))
    표본 = 표본만들기(메시)
    말(f'표본 {time.time() - t0:.0f}s')
    rows = []
    for j in 관절:
        움 = sorted({p for b in 하위(관절, j['자식뼈']) for p in 뼈부품.get(b, [])})
        if not 움: 말('움직일 부품 없음', j['이름']); continue
        고 = [i for i in 메시 if i not in 움]
        for k, rr in enumerate(j['범위']):
            a = np.asarray(rr['축'], float); a /= np.linalg.norm(a)
            rows.append(dict(순=len(rows), 관절=j['이름'], 축=축표기(a) if len(j['범위']) > 1 else 축표기(a), 방향=a.round(4).tolist(),
                             피벗=[float(x) for x in j.get('피벗mm', j.get('피벗'))], 목표=[rr['최소'], rr['최대']],
                             움=움, 고=고, 부모부품=뼈부품.get(j['부모뼈'], []),
                             스냅=(j['이름'] in 스냅관절 and k == 0)))
    말(f'{len(rows)} 행 ({출처})')
    결과 = []
    with Pool(8, initializer=_init, initargs=(T, 캐시, 표본)) as P:
        for o in P.imap_unordered(행, rows):
            결과.append(o)
            말(f"{o['관절']} {o['축']}: 목표 {o['목표']} 잰 {o['잰범위']} 정지빼고 {o['잰범위_정지겹침빼고']} V0={o['V0']}"
              f" 막음 {[(s, d['각'], d['짝'][:2]) for s, d in o['막는곳'].items()]}  행 {o['초']}s · {time.time() - t0:.0f}s")
    결과.sort(key=lambda o: o['순'])
    그림_곡선(결과, OUT / '가동범위.png')
    요약 = dict(설명='V(θ) = Σ vol(자식 하위 트리 부품을 +c 부풀려 θ 회전 ∩ 하위 트리 밖 모든 부품). 잰범위 = 0° 에서 이어진 V<ε. '
                   '잰범위_정지겹침빼고 = V(θ)−V(0)<ε (E13 처럼 정지 자세부터 붙어 있는 조립의 참고치). 막는곳 = 정지겹침빼고 범위 바로 바깥 각의 '
                   '늘어난 짝. 깎기 = 목표 중 못 가는 몫(6° 간격, 한쪽 12 각 이하) 쓸린 부피 ∩ 부품, 겉면적 = 그중 몸 겉(다른 부품에서 0.4 mm 밖) 면적.',
              관절출처=출처, 부품=str(KIT.relative_to(ROOT)), 좌표변환E13to관절=np.round(T, 5).tolist(), c_mm=C, eps_mm3=EPS, 간격도=STEP,
              자시험=자, 뼈부품={b: v for b, v in 뼈부품.items() if v}, 결과=결과)
    (OUT / '가동범위.json').write_text(json.dumps(요약, ensure_ascii=False, indent=1), encoding='utf-8')
    말(f'끝 {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
