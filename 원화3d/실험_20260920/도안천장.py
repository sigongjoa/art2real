# -*- coding: utf-8 -*-
"""**사람이 쓴 도안 하나면 실물 하드서피스가 어디까지 복원되는가** — 궤짝 · 드릴 (2026-09-20).

    python 도안천장.py 검사      자가검사 (아치 · 팔각 · 기울인 상자 · 닫힘 · 도안만 배관)
    python 도안천장.py 대조자    어제 판본(T · T∩H · T→S · H · 정답)의 **평평 · 능선만** 더 잰다 (재실행 아님)
    python 도안천장.py [n]       아직 안 한 장 n 개 -> out/기록/도안천장_진행.jsonl
    python 도안천장.py 판정      -> out/기록/도안천장_<때>.json
    python 도안천장.py 그림      -> out/도안_궤짝.png · out/도안_드릴.png · out/도안천장_접촉지.png

계획 `claudedocs/plan_도안천장_20260920.md` · 도안 `원화3d/도안/궤짝.md` · `드릴.md`.
**문턱은 도안을 쓰기 전에 적었다 — 숫자를 보고 안 바꾼다.**
언어 모델 없음. 구조 · 치수는 사람이 3면 렌더를 보고 손으로 썼고, CMA-ES 는 도안이 「못 읽음」으로
표시한 자유도만 만진다. 목적함수 · 재시작 · 자 · 45° 타일은 `코드기하도형.py` 것을 그대로 부른다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260920")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260919")
import 코드기하도형 as CG                 # build · Jsil · cmaes · 자 · 타일 — 새로 안 짠다
import 메시추출 as ME
import manifold3d as m3

H, W, J, DG, DC = ME.H, ME.W, ME.J, ME.DG, ME.DC
M = m3.Manifold
HERE = ME.HERE
PROG = os.path.join(HERE, "out", "기록", "도안천장_진행.jsonl")
DAEJO = os.path.join(HERE, "out", "기록", "도안천장_대조자.json")
TILED = os.path.join(HERE, "out", "기록", "도안천장_타일")
MVD = os.path.join(HERE, "out", "메시변형")
TAG = "도안천장 v1 · 손으로 쓴 도안 · 도안만/도안+맞춤/도안+전맞춤 · 자유도대조 · 재시작5 · 1024 (2026-09-20)"
ANG = CG.ANG
K재시작 = 5
K전맞춤 = 2                       # 「도안+전맞춤」은 참고라 재시작을 둘만 (차원이 13 · 31 이라 비싸다)
사례 = ("cloak_Chest_Closed_AngpV0HxD8", "mech_Drill_8uBbH7Dvmb")
한글 = {"cloak_Chest_Closed_AngpV0HxD8": "궤짝", "mech_Drill_8uBbH7Dvmb": "드릴"}
# **잰 값이다** (파일 mtime). 공통 렌더·자 읽기 12 분은 두 장이 나눠 가졌다.
# 진행 jsonl 에는 첫 실행 때 적은 어림값(62 · 71)이 남아 있다 — 지우지 않고 여기에 고쳐 적는다.
도안시간분 = {"cloak_Chest_Closed_AngpV0HxD8": 15, "mech_Drill_8uBbH7Dvmb": 26}


# ── 프리미티브 ───────────────────────────────────────────────────────────────

def box(w, d, h, x, y, z0):
    return M.cube([w, d, h], True).translate([x, y, z0 + h / 2])


def 팔각(a, c, z0, z1):
    """상자 ∩ 45° 돌린 상자 — 축 반폭 a · 대각 반폭 c."""
    h = z1 - z0
    s = M.cube([2 * a, 2 * a, h], True) ^ M.cube([2 * c, 2 * c, h], True).rotate([0, 0, 45])
    return s.translate([0, 0, (z0 + z1) / 2])


def 아치(pts, L, axis):
    """pts = [(반폭, z), …] z 오름차순 -> |축| <= L 로 밀어낸 아치 기둥. 단면은 축에 수직인 (반폭, z)."""
    poly = [(-h, -z) for h, z in pts] + [(h, -z) for h, z in reversed(pts)]   # 반시계 (넓이 > 0)
    s = m3.CrossSection([poly]).extrude(2 * L).translate([0, 0, -L]).rotate([-90, 0, 0])
    return s if axis == "y" else s.rotate([0, 0, 90])


def 기울인(p0, p1, w, d, az=0.0):
    """(x, z) 평면 안에서 p0 -> p1 로 누운 상자를 az 만큼 z 둘레로 돌린다. w = 반지름 방향 폭 · d = 깊이."""
    dx, dz = p1[0] - p0[0], p1[1] - p0[1]
    L = float(np.hypot(dx, dz))
    ry = float(np.degrees(np.arctan2(dx, dz)))
    b = M.cube([w, d, L], True).rotate([0, ry, 0]).translate([(p0[0] + p1[0]) / 2, 0, (p0[1] + p1[1]) / 2])
    return b.rotate([0, 0, az]) if az else b


def 사중(mk, az):
    """z 둘레 90° 4 중 대칭. mk(각도) 가 그 각도에 놓인 부품 하나를 낸다."""
    out = None
    for k in range(4):
        p = mk(az + 90 * k)
        out = p if out is None else out + p
    return out


# ── 도안 -> build(θ) ─────────────────────────────────────────────────────────
# 항목: (이름, 도안값, (아래, 위), 못읽음?)  — 못읽음 = True 면 「도안+맞춤」이 만지는 자유도

궤짝_θ = [
    ("sx",      1.000, (0.60, 1.60), True),    # ㄱ 전체 가로 배율 (앞 실루엣이 창에 잘렸다)
    ("b1w",     0.655, (0.40, 1.00), False),
    ("b1d",     0.956, (0.50, 1.20), True),    # ㄴ
    ("stepz",   0.250, (0.10, 0.40), True),    # ㄷ
    ("b2w",     0.6225, (0.40, 1.00), False),
    ("b2d",     0.975, (0.50, 1.20), False),
    ("bandz",   0.390, (0.25, 0.50), True),    # ㄹ
    ("bandtop", 0.475, (0.35, 0.60), False),
    ("bandw",   0.788, (0.50, 1.00), False),
    ("bandd",   1.008, (0.60, 1.30), True),    # ㅁ
    ("ringR",   0.128, (0.05, 0.25), True),    # ㅂ
    ("ringx",   0.740, (0.55, 0.95), True),    # ㅅ
    ("ringz",   0.330, (0.12, 0.55), True),    # ㅇ
]
궤짝_깊이아치 = [(0.504, 0.475), (0.489, 0.520), (0.448, 0.560), (0.382, 0.780), (0.213, 0.960), (0.0, 1.001)]
궤짝_가로아치 = [(0.788, 0.475), (0.636, 0.520), (0.605, 0.560), (0.587, 0.840), (0.505, 0.900), (0.130, 1.001)]
궤짝_관r = 0.037
궤짝_고리y = -0.015


def 궤짝_부품(t):
    sx, b1w, b1d, stepz, b2w, b2d, bandz, bandtop, bandw, bandd, rR, rx, rz = t
    lid = 아치(궤짝_깊이아치, 1.0, "x") ^ 아치([(h * sx, z) for h, z in 궤짝_가로아치], 1.0, "y")
    lid = lid ^ M.cube([4, 4, 2 * (1.001 - bandtop)], True).translate([0, 0, bandtop + (1.001 - bandtop)])
    ring = lambda s: (m3.CrossSection.circle(궤짝_관r, 24).translate([rR, 0]).revolve(48)
                      .rotate([0, 90, 0]).translate([s * rx, 궤짝_고리y, rz]))
    return [("아래몸통", box(2 * b1w * sx, b1d, stepz, 0, 0, 0.0)),
            ("위몸통", box(2 * b2w * sx, b2d, bandz - stepz, 0, 0, stepz)),
            ("띠", box(2 * bandw * sx, bandd, bandtop - bandz, 0, 0, bandz)),
            ("고리+", ring(+1)), ("고리−", ring(-1)),
            ("뚜껑", lid)]


드릴_θ = [
    ("conr",    0.135, (0.06, 0.30), True),    # ㅇ 날 밑반지름
    ("conz",    0.270, (0.15, 0.40), False),
    ("neckr",   0.175, (0.10, 0.28), False),
    ("neckz0",  0.265, (0.15, 0.35), False),
    ("neckz1",  0.315, (0.25, 0.42), False),
    ("houa",    0.210, (0.12, 0.35), False),   # 마름모의 축 방향 반대각
    ("houc",    0.155, (0.09, 0.30), True),    # ㅅ 하우징 대각 반폭 (45° 한 장에서만 나온다)
    ("houz0",   0.310, (0.25, 0.42), False),
    ("houz1",   0.500, (0.42, 0.65), False),
    ("colw",    0.055, (0.02, 0.15), True),    # ㅂ 기둥 굵기
    ("colz0",   0.480, (0.40, 0.60), False),
    ("colz1",   0.930, (0.85, 1.00), False),
    ("barL",    0.290, (0.15, 0.45), False),
    ("bart",    0.070, (0.01, 0.10), False),
    ("barz0",   0.672, (0.55, 0.80), False),
    ("barz1",   0.710, (0.58, 0.85), False),
    ("topa",    0.210, (0.12, 0.35), False),
    ("topc",    0.235, (0.14, 0.40), False),
    ("topz0",   0.910, (0.82, 0.97), False),
    ("armang",  0.000, (-45.0, 45.0), True),   # ㄱ 팔 넷의 방위 (축인가 대각인가)
    ("armd",    0.098, (0.02, 0.15), True),    # ㄴ 팔 단면 깊이
    ("footd",   0.085, (0.03, 0.20), True),    # ㄷ 발 깊이
    ("footx",   0.232, (0.12, 0.40), True),    # ㄹ 발 가로 위치 (중심선)
    ("elbz",    0.700, (0.55, 0.85), True),    # ㅁ 팔꿈치 높이
    ("elbx",    0.235, (0.15, 0.45), False),   # 팔꿈치 **중심선**
    ("armw",    0.098, (0.03, 0.20), False),
    ("armtopx", 0.130, (0.08, 0.35), False),
    ("armtopz", 0.940, (0.85, 1.00), False),
    ("footz0",  0.310, (0.20, 0.42), False),
    ("footz1",  0.420, (0.30, 0.55), False),
    ("footw",   0.085, (0.03, 0.20), False),
]


def 드릴_부품(t):
    (conr, conz, neckr, neckz0, neckz1, houa, houc, houz0, houz1, colw, colz0, colz1,
     barL, bart, barz0, barz1, topa, topc, topz0, ang, armd, footd, footx, elbz, elbx,
     armw, armtopx, armtopz, footz0, footz1, footw) = t
    콘 = M.cylinder(conz, 0.0, conr, 64)                                     # 꼭짓점 아래
    목 = M.cylinder(max(neckz1 - neckz0, 1e-3), neckr, neckr, 64).translate([0, 0, neckz0])
    dz = max(barz1 - barz0, 1e-3)
    막대 = 사중(lambda a: box(barL, bart, dz, barL / 2, 0, barz0).rotate([0, 0, a]), ang)   # 팔꿈치끼리 잇는 십자
    팔아래 = 사중(lambda a: 기울인((footx, footz0 + footw / 2), (elbx, elbz), armw, armd, a), ang)
    팔위 = 사중(lambda a: 기울인((elbx, elbz - armw / 2), (armtopx, armtopz), armw, armd, a), ang)
    발 = 사중(lambda a: box(footw, footd, max(footz1 - footz0, 1e-3), footx, 0, footz0).rotate([0, 0, a]), ang)
    return [("날", 콘), ("날목", 목), ("하우징", 팔각(houa, houc, houz0, houz1)),
            ("기둥", box(2 * colw, 2 * colw, max(colz1 - colz0, 1e-3), 0, 0, colz0)),
            ("십자막대", 막대), ("윗판", 팔각(topa, topc, topz0, 1.001)),
            ("팔아래", 팔아래), ("팔위", 팔위), ("발", 발)]


도안 = {"cloak_Chest_Closed_AngpV0HxD8": (궤짝_θ, 궤짝_부품),
        "mech_Drill_8uBbH7Dvmb": (드릴_θ, 드릴_부품)}


def 합(parts):
    out = None
    for _, p in parts:
        out = p if out is None else out + p
    return out


def 만들기(case):
    _, fn = 도안[case]
    return lambda t: 합(fn(t))


def ps_of(case, 전부=False):
    """CMA-ES 에 넘길 (이름, 범위, 종류) 목록과, 자유 축의 자리 번호."""
    sp = 도안[case][0]
    idx = [i for i, (_, _, _, fr) in enumerate(sp) if 전부 or fr]
    return [(sp[i][0], sp[i][2], "L") for i in idx], idx


def 채우기(case, idx, x):
    t = [v for _, v, _, _ in 도안[case][0]]
    for i, v in zip(idx, x):
        t[i] = float(v)
    return t


def 부분build(case, idx):
    mk = 만들기(case)
    return lambda x: mk(채우기(case, idx, x))


# ── 어제 판본의 평평 · 능선만 더 재기 (재실행 아님) ──────────────────────────

def 대조자():
    """`메시변형` 의 판본 다섯에서 **평평 · 능선만** 더 잰다. 형상은 어제 것 그대로다 —
    T 는 `불리언.fitted` 가 결정적이고, T→S 는 저장해 둔 정점 npz 를 쓴다."""
    from 불리언 import fitted
    from 생성깎기 import build as gen_build, voxelize
    import 대조 as C_
    from 면 import dihedral, roughness
    H.register_sheets()
    out = {}
    for case in 사례:
        t0 = time.time()
        masks, bs, plain, base, axes = gen_build(case)
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        r = {}

        def 재(name, m):
            d = dihedral(m)
            r[name] = {"평평": d["평평"], "능선": d["능선"], "계단": d["계단"],
                       "거칠기": roughness(m, n=DG.NPT)["거칠기"], "면": int(len(m.faces))}
            print("    %-5s 평평 %.3f 능선 %.3f" % (name, d["평평"], d["능선"]), flush=True)

        재("정답", truth)
        재("H", C_.to_mesh(base, axes))
        T = fitted(case, masks)
        재("T", T)
        재("T∩H", C_.to_mesh(voxelize(T, axes) & plain, axes))
        p = os.path.join(MVD, case + "__TS.npz")
        with np.load(p) as o:
            재("T→S", trimesh.Trimesh(o["V"].copy(), np.asarray(T.faces), process=False))
        out[case] = r
        print("  %s %.0f초" % (case, time.time() - t0), flush=True)
    json.dump(out, open(DAEJO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", DAEJO)
    return out


# ── 한 장 ────────────────────────────────────────────────────────────────────

def 팔(fn, ps, inits, masks, bs, tv, tsil, label):
    rs, ms = [], []
    for k, x0 in enumerate(inits):
        t1 = time.time()
        th, j, it, ev = CG.cmaes(fn, ps, x0, masks, bs, k)
        m = CG.build(fn, th)
        rs.append({"씨앗": k, "θ": [round(float(x), 5) for x in th], "J": round(j, 5), "세대": it,
                   "평가": ev, **CG.가볍(m, tv, tsil), "초": round(time.time() - t1, 1)})
        ms.append(m)
        print("    %s 씨앗%d J %.4f 3D %.4f held %.4f · %d세대 %.0f초"
              % (label, k, j, rs[-1]["iou3d"], rs[-1]["held"], it, rs[-1]["초"]), flush=True)
    return rs, ms


def 초기_자유(case, idx, seed):
    """자유 축만 **범위 균등**으로 뽑는다 — 도안 값 근처에서 시작하면 「맞춤이 도안을 베낀다」."""
    sp = 도안[case][0]
    rng = np.random.default_rng(3000 + seed)
    return [float(rng.uniform(sp[i][2][0], sp[i][2][1])) for i in idx]


def one(case):
    t0 = time.time()
    masks, bs = CG.G3.art_masks(case), H.CASES[case]["back_sign"]
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    frame = ME.AL.frame_of(truth, 45)
    tsil = {a: DG.sil(truth, "front", None, a) for a in ANG}
    tv = CG.vox(truth)
    sp = 도안[case][0]
    out = {"case": case, "판": TAG, "이름": 한글[case], "도안분": 도안시간분[case],
           "d": len(sp), "못읽음": [n for n, _, _, fr in sp if fr],
           "매개변수": [n for n, _, _, _ in sp], "θ도안": [v for _, v, _, _ in sp],
           "정답": CG.무겁(truth)}
    # 배관 ② 입력 마스크 대 정답 실루엣
    ts = CG.sils(truth, bs)
    out["입력대정답실루엣"] = {v: round(float((ts[v] & masks[v]).sum() / max((ts[v] | masks[v]).sum(), 1)), 4)
                            for v in W.VIEWS}
    assert min(out["입력대정답실루엣"].values()) >= 0.98, "배관 짐 — 입력 마스크가 정답과 %s" % out["입력대정답실루엣"]

    mk = 만들기(case)
    m0 = CG.build(mk, [v for _, v, _, _ in sp])                       # **도안만**
    j0 = CG.Jsil(m0, masks, bs)
    out["도안만"] = {"J": round(j0, 5), **CG.가볍(m0, tv, tsil), **CG.무겁(m0)}
    print("  %s 도안만 J %.4f 3D %.4f held %.4f" % (한글[case], j0, out["도안만"]["iou3d"], out["도안만"]["held"]), flush=True)
    CG.타일저장(m0, frame, case, "도안만", "3D %.3f · held %.3f · J %.4f" % (out["도안만"]["iou3d"], out["도안만"]["held"], j0))

    for 이름, 전부, K in (("도안+맞춤", False, K재시작), ("도안+전맞춤", True, K전맞춤)):
        ps, idx = ps_of(case, 전부)
        fn = 부분build(case, idx)
        rs, ms = 팔(fn, ps, [초기_자유(case, idx, k) for k in range(K)], masks, bs, tv, tsil, 이름)
        b = int(np.argmax([r["J"] for r in rs]))                      # **J 로 고른다**
        vs = [CG.vox(m) for m in ms]
        out[이름] = {"자유축": [sp[i][0] for i in idx], "재시작": rs, "최선1": b,
                     "θ최선": 채우기(case, idx, rs[b]["θ"]),
                     "top": int(np.argmax([r["iou3d"] for r in rs])),
                     "후보쌍3D": [[CG.viou(vs[i], vs[j]) for j in range(K)] for i in range(K)],
                     **{"최선1_" + k: v for k, v in CG.무겁(ms[b]).items()}}
        CG.타일저장(ms[b], frame, case, 이름, "3D %.3f · held %.3f · J %.4f"
                   % (rs[b]["iou3d"], rs[b]["held"], rs[b]["J"]))

    psc = CG.대조구조(len(sp))                                        # 자유도 대조 — 같은 매개변수 수의 상자 합집합
    rc, mcs = 팔(CG.b_상자합, psc, [CG.초기_대조(psc, k) for k in range(K재시작)], masks, bs, tv, tsil, "자유도대조")
    c = int(np.argmax([r["J"] for r in rc]))
    out["자유도대조"] = {"d": len(psc), "상자수": len(psc) // 6, "재시작": rc, "최선1": c,
                       **{"최선1_" + k: v for k, v in CG.무겁(mcs[c]).items()}}
    CG.타일저장(mcs[c], frame, case, "자유도대조", "3D %.3f · held %.3f · J %.4f"
               % (rc[c]["iou3d"], rc[c]["held"], rc[c]["J"]))
    out["초"] = round(time.time() - t0, 1)
    return out


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[r["case"]] = r
    return out


def run(n):
    H.register_sheets()
    for case in [c for c in 사례 if c not in rows()][:n]:
        r = one(case)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  -> %s %.0f초" % (한글[case], r["초"]), flush=True)


# ── 판정 ─────────────────────────────────────────────────────────────────────

def 어제():
    """`메시변형_진행.jsonl` 의 판본 값. **다시 안 돌린다.**"""
    p = os.path.join(HERE, "out", "기록", "메시변형_진행.jsonl")
    out = {}
    for line in open(p, encoding="utf-8"):
        r = json.loads(line)
        out[(r["case"], r["이름"])] = r
    return out


def verdict():
    rs, R = rows(), 어제()
    D = json.load(open(DAEJO, encoding="utf-8")) if os.path.exists(DAEJO) else {}
    cs = [c for c in 사례 if c in rs]
    B = lambda c, k: rs[c][k]["재시작"][rs[c][k]["최선1"]]
    v = {"판": TAG, "때": time.strftime("%Y%m%d_%H%M"), "장": cs,
         "안잰": [c for c in 사례 if c not in cs],
         "집계": "장이 둘이라 중앙값을 안 쓴다 — **두 장 다** 넘어야 통과 (계획 「집계」)",
         "도안쓴시간분": {한글[c]: rs[c]["도안분"] for c in cs}}
    # Q1 — 도안+맞춤 대 T∩H : held-out · 평평 거리 · 능선 거리
    q1 = {}
    for c in cs:
        b = B(c, "도안+맞춤")
        tp = R[(c, "T∩H")]["대각평균"]
        d = D.get(c, {})
        참 = d.get("정답", {})
        거리 = lambda x, k: abs(x - 참[k]) if 참 else None
        코 = {"평평": rs[c]["도안+맞춤"]["최선1_평평"], "능선": rs[c]["도안+맞춤"]["최선1_능선"]}
        q1[한글[c]] = {"held(도안+맞춤)": b["held"], "held(T∩H)": tp, "held차": round(b["held"] - tp, 4),
                      "평평거리(도안+맞춤)": None if not 참 else round(거리(코["평평"], "평평"), 4),
                      "평평거리(T∩H)": None if not 참 else round(거리(d["T∩H"]["평평"], "평평"), 4),
                      "능선거리(도안+맞춤)": None if not 참 else round(거리(코["능선"], "능선"), 4),
                      "능선거리(T∩H)": None if not 참 else round(거리(d["T∩H"]["능선"], "능선"), 4)}
        x = q1[한글[c]]
        x["통과"] = bool(x["held차"] > 0 and 참 and x["평평거리(도안+맞춤)"] < x["평평거리(T∩H)"]
                        and x["능선거리(도안+맞춤)"] < x["능선거리(T∩H)"])
    v["Q1"] = {"문턱": "두 장 다 held-out 이 T∩H 보다 높고 평평 거리 · 능선 거리가 둘 다 더 작다",
               "장별": q1, "통과": bool(len(q1) == len(사례) and all(x["통과"] for x in q1.values()))}
    # Q2 — 3D IoU >= 0.90 (두 장 다)
    q2 = {한글[c]: {"3D(도안+맞춤)": B(c, "도안+맞춤")["iou3d"], "3D(도안만)": rs[c]["도안만"]["iou3d"],
                   "3D(도안+전맞춤)": B(c, "도안+전맞춤")["iou3d"],
                   "어제최고": round(max(R[(c, n)]["iou128양쪽"] for n in ("T", "T∩H", "H", "T→S")), 4),
                   "이산화상한": R[(c, "정답")]["iou128양쪽"]} for c in cs}
    for k in q2:
        q2[k]["통과"] = bool(q2[k]["3D(도안+맞춤)"] >= 0.90)
    v["Q2"] = {"문턱": "두 장 다 3D IoU(128 양쪽) >= 0.90 · 어제 도형 8 개 중앙 0.998 대비 낙폭 <= 0.10",
               "장별": q2, "통과": bool(len(q2) == len(사례) and all(x["통과"] for x in q2.values()))}
    # Q3 — 도안만 대 자유도 대조
    q3 = {한글[c]: {"도안만": rs[c]["도안만"]["iou3d"], "자유도대조": B(c, "자유도대조")["iou3d"],
                   "대조상자수": rs[c]["자유도대조"]["상자수"], "대조d": rs[c]["자유도대조"]["d"], "프로그램d": rs[c]["d"],
                   "차(도안만−대조)": round(rs[c]["도안만"]["iou3d"] - B(c, "자유도대조")["iou3d"], 4),
                   "맞춤의몫(도안+맞춤−도안만)": round(B(c, "도안+맞춤")["iou3d"] - rs[c]["도안만"]["iou3d"], 4),
                   "전맞춤의몫": round(B(c, "도안+전맞춤")["iou3d"] - rs[c]["도안만"]["iou3d"], 4)} for c in cs}
    for k in q3:
        q3[k]["통과"] = bool(q3[k]["차(도안만−대조)"] > 0)
    v["Q3"] = {"문턱": "두 장 다 「도안만」이 같은 매개변수 수의 상자 합집합을 3D IoU 로 이긴다",
               "장별": q3, "통과": bool(len(q3) == len(사례) and all(x["통과"] for x in q3.values()))}
    # Q4 — 못 읽은 축이 어디로 갔나 (서술)
    q4 = {}
    for c in cs:
        sp = 도안[c][0]
        idx = [i for i, (_, _, _, fr) in enumerate(sp) if fr]
        th = rs[c]["도안+맞춤"]["θ최선"]
        te = rs[c]["도안+전맞춤"]["θ최선"]
        q4[한글[c]] = {"자유축수": len(idx), "표": {sp[i][0]: {"도안": sp[i][1], "맞춤": round(th[i], 4),
                                                            "전맞춤": round(te[i], 4),
                                                            "범위": list(sp[i][2])} for i in idx},
                      "고정축이전맞춤에서움직인양": {sp[i][0]: round(te[i] - sp[i][1], 4)
                                                for i in range(len(sp)) if i not in idx}}
    v["Q4(서술)"] = q4
    # 표
    v["표"] = {한글[c]: {"정답": rs[c]["정답"],
                       "T": {"3D": R[(c, "T")]["iou128양쪽"], "held": R[(c, "T")]["대각평균"], "거칠기": R[(c, "T")]["거칠기"]},
                       "T∩H": {"3D": R[(c, "T∩H")]["iou128양쪽"], "held": R[(c, "T∩H")]["대각평균"], "거칠기": R[(c, "T∩H")]["거칠기"]},
                       "H": {"3D": R[(c, "H")]["iou128양쪽"], "held": R[(c, "H")]["대각평균"], "거칠기": R[(c, "H")]["거칠기"]},
                       "T→S": {"3D": R[(c, "T→S")]["iou128양쪽"], "held": R[(c, "T→S")]["대각평균"], "거칠기": R[(c, "T→S")]["거칠기"]},
                       "상한(정답)": {"3D": R[(c, "정답")]["iou128양쪽"], "held": R[(c, "상한")]["대각평균"]},
                       "자유도대조": {k: B(c, "자유도대조")[k] for k in ("J", "iou3d", "held")},
                       "도안만": {k: rs[c]["도안만"][k] for k in ("J", "iou3d", "held", "held45", "거칠기", "평평", "능선", "닫힘", "조각")},
                       "도안+맞춤": {**{k: B(c, "도안+맞춤")[k] for k in ("J", "iou3d", "held", "held45")},
                                  **{k: rs[c]["도안+맞춤"]["최선1_" + k] for k in ("거칠기", "평평", "능선", "닫힘", "조각")}},
                       "도안+전맞춤": {k: B(c, "도안+전맞춤")[k] for k in ("J", "iou3d", "held")},
                       "평평·능선(어제 판본)": D.get(c, "대조자 안 돌았다"),
                       "초": rs[c]["초"]} for c in cs}
    p = os.path.join(HERE, "out", "기록", "도안천장_%s.json" % v["때"])
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n  %-6s %-12s %7s %7s %7s %7s" % ("장", "판본", "J", "3D", "held", "평평"))
    for c in cs:
        for n in ("도안만", "도안+맞춤", "도안+전맞춤", "자유도대조"):
            g = rs[c][n] if n == "도안만" else B(c, n)
            fl = rs[c][n].get("평평") if n == "도안만" else rs[c][n].get("최선1_평평")
            print("  %-6s %-12s %7.4f %7.4f %7.4f %7s"
                  % (한글[c], n, g["J"], g["iou3d"], g["held"], "%.3f" % fl if fl is not None else "-"))
    for k in ("Q1", "Q2", "Q3"):
        print("\n  %s %s" % (k, json.dumps(v[k], ensure_ascii=False)[:800]))
    print("\n  ->", p)
    return v


# ── 그림 ─────────────────────────────────────────────────────────────────────

def 제도(case, dst):
    """**도안 자체를 그림으로** — 3면 실루엣 위에 부품 상자 · 치수선 · 치수 숫자. 못 읽음은 `?`."""
    from PIL import Image, ImageDraw
    from 계획 import _font
    H.register_sheets()
    sp, fn = 도안[case]
    parts = fn([v for _, v, _, _ in sp])
    못 = {n for n, _, _, fr in sp if fr}
    masks = CG.G3.art_masks(case)
    # 어느 부품 치수가 「못 읽음」에 걸려 있나 — 자유 축을 흔들어 상자가 움직이면 `?` 다
    바닥 = [np.asarray(CG.tm(p).bounds) for _, p in parts]
    흔 = np.zeros((len(parts), 3), bool)
    for i, (n, v, (lo, hi), fr) in enumerate(sp):
        if not fr:
            continue
        t2 = [x[1] for x in sp]
        t2[i] = float(np.clip(v * 1.08 + 0.01, lo, hi))
        for k, (_, p) in enumerate(fn(t2)):
            흔[k] |= np.abs(np.asarray(CG.tm(p).bounds) - 바닥[k]).max(0) > 1e-4
    U, Z0, Z1 = 0.92, -0.06, 1.12                    # **창보다 넓게 그린다** — 궤짝은 창(±0.6)에 잘린다
    S, PAD, TOP = 540, 30, 150
    views = [("앞 (x–z)", "front", 0), ("옆 (y–z)", "side", 1), ("뒤 (x–z)", "back", 0)]
    im = Image.new("RGB", (PAD + 3 * (S + PAD), TOP + S + 30 + 34 * (1 + (len(못) + 3) // 4)), "white")
    d = ImageDraw.Draw(im)
    f1, f2, f3 = _font(30), _font(17), _font(13)
    d.text((PAD, 18), "도안 — %s   (부품 %d · 못 읽은 자유도 %d · 쓴 시간 %d 분)"
           % (한글[case], len(parts), len(못), 도안시간분[case]), fill=(20, 20, 20), font=f1)
    d.text((PAD, 58), "회색 = 정답 실루엣(입력 마스크) · 파랑 = 도안 부품의 상자 · 빨강 = 치수 (창 단위 · 키 = 1)",
           fill=(90, 90, 90), font=f2)
    d.text((PAD, 82), "**?** = 그림에서 못 읽은 치수 — CMA-ES 가 맞춘다 · 노랑 띠 = 창의 좌우 끝(±0.6) · "
                      "자세한 것은 원화3d/도안/%s.md" % 한글[case], fill=(90, 90, 90), font=f2)
    u2p = lambda u: (u + U) / (2 * U) * S
    z2p = lambda z: (Z1 - z) / (Z1 - Z0) * S
    mw, mh = int(1.2 / (2 * U) * S), int(1.2 / (Z1 - Z0) * S)
    for k, (라, view, ax) in enumerate(views):
        x0 = PAD + k * (S + PAD)
        m = np.asarray(Image.fromarray((~masks[view]).astype(np.uint8) * 255).resize((mw, mh)))
        im.paste(Image.fromarray(np.where(m[:, :, None] > 127, 250, 200).astype(np.uint8).repeat(3, 2)),
                 (x0 + int(u2p(-0.6)), TOP + int(z2p(1.1))))
        d.rectangle([x0, TOP, x0 + S, TOP + S], outline=(160, 160, 160))
        for s in (-0.6, 0.6):                                    # 창의 끝 — 여기 밖은 그림이 말 안 해 준다
            d.line([(x0 + u2p(s), TOP), (x0 + u2p(s), TOP + S)], fill=(230, 180, 40), width=2)
        d.text((x0 + 6, TOP - 26), 라, fill=(20, 20, 20), font=f2)
        sgn = -1 if view == "back" else 1
        for i, (nm, p) in enumerate(parts):
            b = 바닥[i]
            u0, u1 = sorted([sgn * b[0][ax], sgn * b[1][ax]])
            r = [x0 + u2p(u0), TOP + z2p(b[1][2]), x0 + u2p(u1), TOP + z2p(b[0][2])]
            d.rectangle(r, outline=(30, 90, 220))
            d.text((r[0] + 3, r[1] + 2), nm, fill=(30, 90, 220), font=f3)
            y = TOP + z2p(b[0][2] + (b[1][2] - b[0][2]) * (0.25 + 0.5 * (i % 2)))
            d.line([(r[0], y), (r[2], y)], fill=(220, 40, 40))
            d.line([(r[0], y - 4), (r[0], y + 4)], fill=(220, 40, 40))
            d.line([(r[2], y - 4), (r[2], y + 4)], fill=(220, 40, 40))
            글 = "%.3f%s" % (u1 - u0, " ?" if 흔[i][ax] else "")
            d.text(((r[0] + r[2]) / 2 - 4 * len(글), y - 17), 글, fill=(220, 40, 40), font=f3)
            if k == 0:                                           # 높이는 앞 판에만
                글 = "h %.3f%s" % (b[1][2] - b[0][2], " ?" if 흔[i][2] else "")
                d.text((r[2] + 3, (r[1] + r[3]) / 2 - 7), 글, fill=(220, 40, 40), font=f3)
    y = TOP + S + 22
    d.text((PAD, y), "못 읽은 치수 %d 개 (도안에 적은 값 · CMA-ES 가 이것만 만진다):" % len(못),
           fill=(220, 40, 40), font=f2)
    for i, (n, val, rng, fr) in enumerate([x for x in sp if x[3]]):
        d.text((PAD + 430 * (i % 4), y + 34 + 26 * (i // 4)),
               "%s = %.3f ?   (범위 %.2f ~ %.2f)" % (n, val, rng[0], rng[1]), fill=(220, 40, 40), font=f2)
    im.save(dst)
    print("  ->", dst)


def 접촉지():
    from PIL import Image
    rs = rows()
    cols = ("정답", "T", "T∩H (현행)", "T→S", "자유도 대조", "도안만", "도안+맞춤")
    src = {"정답": (ME.TILED, "정답"), "T": (os.path.join(HERE, "out", "기록", "메시변형_타일"), "T"),
           "T∩H (현행)": (os.path.join(HERE, "out", "기록", "메시변형_타일"), "T∩H"),
           "T→S": (os.path.join(HERE, "out", "기록", "메시변형_타일"), "T→S"),
           # `CG.타일저장` 은 제 모듈의 타일 폴더에 쓴다 (같은 렌더 · 같은 틀이라 그대로 쓴다)
           "자유도 대조": (CG.TILED, "자유도대조"), "도안만": (CG.TILED, "도안만"),
           "도안+맞춤": (CG.TILED, "도안+맞춤")}
    R = []
    for c in 사례:
        if c not in rs:
            continue
        ts = []
        for n in cols:
            dr, nm = src[n]
            p = os.path.join(dr, "%s__%s.png" % (c, nm))
            ts.append(np.asarray(Image.open(p).convert("RGB")) if os.path.exists(p)
                      else np.full((300, 300, 3), 240, np.uint8))
        R.append((한글[c], ts))
    DC.grid(R, cols, "도안 천장 — 사람이 쓴 도안 하나로 실물이 어디까지 서나 (45° 명암 · 같은 빛 · 같은 틀)",
            "빨간 글 = 3D IoU(128 양쪽 채움) · held-out 30·45·60 · J(앞·뒤·옆 실루엣 IoU) · "
            "자유도 대조 = 같은 매개변수 수의 축정렬 상자 합집합 + 같은 CMA-ES",
            os.path.join(HERE, "out", "도안천장_접촉지.png"), S=300)


def 그림():
    for c in 사례:
        제도(c, os.path.join(HERE, "out", "도안_%s.png" % 한글[c]))
    접촉지()


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def selfcheck():
    # 1. 아치의 축 규약 — y 아치는 y 로 길고, x 아치는 x 로 길다
    a = CG.tm(아치([(0.3, 0.0), (0.1, 1.0)], 0.7, "y")).bounds
    assert abs(a[1][1] - 0.7) < 1e-6 and abs(a[1][0] - 0.3) < 1e-6 and abs(a[1][2] - 1.0) < 1e-6, "y 아치 %s" % a
    b = CG.tm(아치([(0.3, 0.0), (0.1, 1.0)], 0.7, "x")).bounds
    assert abs(b[1][0] - 0.7) < 1e-6 and abs(b[1][1] - 0.3) < 1e-6 and abs(b[1][2] - 1.0) < 1e-6, "x 아치 %s" % b
    # 2. 팔각 — 축 반폭 a · 대각 반폭 c
    o = CG.tm(팔각(0.3, 0.36, 0.0, 1.0))
    V = np.asarray(o.vertices)
    assert abs(V[:, 0].max() - 0.3) < 1e-6, "팔각 축 반폭 %.4f" % V[:, 0].max()
    assert abs((V[:, 0] + V[:, 1]).max() / np.sqrt(2) - 0.36) < 1e-3, "팔각 대각 반폭 %.4f" % ((V[:, 0] + V[:, 1]).max() / np.sqrt(2))
    # 3. 기울인 상자 — 두 끝이 맞다
    t = CG.tm(기울인((0.2, 0.3), (0.4, 0.9), 0.1, 0.05))
    assert abs(t.bounds[0][2] - 0.3) < 0.03 and abs(t.bounds[1][2] - 0.9) < 0.03, "기울인 z %s" % t.bounds
    # 4. 사중 대칭 — 0° 는 x·y 축, 45° 는 대각
    q = CG.tm(사중(lambda ag: box(0.1, 0.1, 0.1, 0.3, 0, 0).rotate([0, 0, ag]), 0.0))
    assert abs(q.bounds[1][0] - 0.35) < 1e-6 and abs(q.bounds[1][1] - 0.35) < 1e-6, "4중 %s" % q.bounds
    # 5. 도안만이 닫힌 다양체 · 실루엣이 헛것이 아니다
    H.register_sheets()
    for c in 사례:
        sp, fn = 도안[c]
        m = CG.build(만들기(c), [v for _, v, _, _ in sp])
        j = CG.Jsil(m, CG.G3.art_masks(c), H.CASES[c]["back_sign"])
        n못 = sum(1 for x in sp if x[3])
        assert m.is_watertight and j > 0.4, "%s 도안만 J %.4f" % (한글[c], j)
        assert all(lo <= v <= hi for _, v, (lo, hi), _ in sp), "%s 도안 값이 범위 밖" % 한글[c]
        # 자유 축을 범위 균등으로 흔들어도 build 가 안 죽는다
        ps, idx = ps_of(c, False)
        for k in range(5):
            CG.build(부분build(c, idx), 초기_자유(c, idx, 100 + k))
        print("  %-4s 부품 %d · d %d · 못읽음 %d · 도안만 J %.4f · 면 %d"
              % (한글[c], len(fn([v for _, v, _, _ in sp])), len(sp), n못, j, len(m.faces)), flush=True)
    print("  자가검사 통과")


if __name__ == "__main__":
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        selfcheck()
    elif a == "대조자":
        대조자()
    elif a == "판정":
        verdict()
    elif a == "그림":
        그림()
    else:
        run(int(a))
