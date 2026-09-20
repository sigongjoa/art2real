# -*- coding: utf-8 -*-
"""**구조가 옳다면 치수는 축 실루엣 3장으로 정해지는가** — 도형 11 (2026-09-20).

    python 코드기하도형.py 검사      자가검사 (닫힘 · 천장 실루엣 IoU >= 0.99 · 오차 0)
    python 코드기하도형.py [n]       아직 안 한 도형 n 개 -> out/기록/코드기하도형_진행.jsonl
    python 코드기하도형.py 판정      -> out/기록/코드기하도형_<때>.json
    python 코드기하도형.py 그림      -> out/코드기하_도형.png

계획 `claudedocs/plan_코드기하도형_20260920.md`. **문턱은 계획 그대로다 — 숫자를 보고 안 바꾼다.**
언어 모델 없음. 구조는 사람이 쓴 정답 구조, θ 만 CMA-ES 로 (목적함수 = 앞·뒤·옆 실루엣 IoU 평균).
자 · 타일 · 카메라는 `메시추출` · `대각` · `win` 것을 그대로 부른다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")           # CPU 를 아낀다 — 프로세스 하나 · BLAS 2 가닥
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260919")
import 메시추출 as ME                                    # 경로 · 자 · 타일 (새로 안 짠다)

H, W, J, DG, DC = ME.H, ME.W, ME.J, ME.DG, ME.DC
from 겉면채점 import fill_slices
from 면 import dihedral, roughness
import 생성3D as G3
import manifold3d as m3

M = m3.Manifold
HERE = ME.HERE
PROG = os.path.join(HERE, "out", "기록", "코드기하도형_진행.jsonl")
TILED = os.path.join(HERE, "out", "기록", "코드기하도형_타일")
TAG = "코드기하도형 v1 · 정답구조 · CMA-ES 실루엣3 · 재시작5 · 자유도대조(상자합) · 1024 (2026-09-20)"
K재시작 = 5
MAXITER = 300                   # 상자 한 개로 **초만** 보고 정했다 — 상자는 72~107 세대에 tol 로 섰다 (59초). 차원이 큰 도형에 여유를 준다
SIGMA0 = 0.2
ANG = (30, 45, 60)

LEN, POS, Z0R, ROT, THK = (0.02, 1.2), (-0.4, 0.4), (-0.1, 0.5), (0.0, 90.0), (0.01, 0.3)
가능 = ("상자", "원기둥", "원뿔", "구", "두기둥나란히", "치마", "토러스세움", "토러스옆")
불가 = ("상자45도", "두기둥대각", "L자")


def tm(man):
    me = man.to_mesh()
    return trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3], np.asarray(me.tri_verts), process=False)


def _box(w, d, h, x, y, z0, rz=0.0):
    b = M.cube([w, d, h], True)
    if rz:
        b = b.rotate([0, 0, rz])
    return b.translate([x, y, z0 + h / 2])


# ── 구조 (사람이 쓴 정답 구조) — 이름: (매개변수[(이름, 범위, 종류)], build, θ_정답, 균등초기 축) ──────
# 종류: L 길이 · P 위치 · A 각도 · T 두께(판정 밖)

def b_상자(t):
    w, d, h, cx, cy, z0 = t
    return _box(w, d, h, cx, cy, z0)


def b_원기둥(t):
    r, h, cx, cy, z0 = t
    return M.cylinder(h, r, r, 96).translate([cx, cy, z0])


def b_원뿔(t):
    r, h, cx, cy, z0 = t
    return M.cylinder(h, 0.0, r, 96).translate([cx, cy, z0])       # 정답이 꼭짓점 아래다 (시트 Y-up 내보내기에서 뒤집혔다)


def b_구(t):
    r, cx, cy, z0 = t
    return M.sphere(r, 96).translate([cx, cy, z0 + r])


def b_나란히(t):
    w, d, h, g, cx, cy, z0 = t
    return _box(w, d, h, cx + g / 2, cy, z0) + _box(w, d, h, cx - g / 2, cy, z0)      # x 거울


def b_대각(t):
    w, d, h, a, b, cx, cy, z0 = t
    return _box(w, d, h, cx + a, cy + b, z0) + _box(w, d, h, cx - a, cy - b, z0)      # 원점 대칭


def b_45(t):
    w, d, h, rz, cx, cy, z0 = t
    return _box(w, d, h, cx, cy, z0, rz)


def b_L(t):
    W1, D1, W2, D2, Hh, x1, y1, x2, z0 = t
    # 작은 상자는 **앞(−y)** 에 붙는다. 창 좌표에서 y 가 `도형.py` 와 반대다 (Y-up 내보내기) —
    # 실루엣 배관은 이걸 못 잡는다 (앞뒤를 바꿔도 J 0.9969 로 같다). 천장 3D IoU 로 잡는다
    return _box(W1, D1, Hh, x1, y1, z0) + _box(W2, D2, Hh, x2, y1 - D1 / 2 - D2 / 2, z0)


def b_치마(t):
    rb, rt, h, th, cx, cy, z0 = t
    out = M.cylinder(h, rb, rt, 96)
    k, e = (rt - rb) / h, 0.01
    lo, hi = rb - th - k * e, rt - th + k * e
    if max(lo, hi) > 1e-3:                                 # 안쪽 원뿔대를 양 끝 밖까지 늘여 뺀다
        out = out - M.cylinder(h + 2 * e, max(lo, 1e-4), max(hi, 1e-4), 96).translate([0, 0, -e])
    return out.translate([cx, cy, z0])


def _torus(R, r):
    return M.revolve(m3.CrossSection.circle(r, 32).translate([R, 0]), 64)       # 축 = z


def b_토세(t):
    R, r, cx, cy, z0 = t
    return _torus(R, r).rotate([90, 0, 0]).translate([cx, cy, z0 + R + r])       # 축 = y (구멍이 앞)


def b_토옆(t):
    R, r, cx, cy, z0 = t
    return _torus(R, r).rotate([0, 90, 0]).translate([cx, cy, z0 + R + r])       # 축 = x (구멍이 옆)


_P3 = [("cx", POS, "P"), ("cy", POS, "P"), ("z0", Z0R, "P")]
_L = lambda *ns: [(n, LEN, "L") for n in ns]
S토 = 1 / 0.96
S치 = 1 / 0.98
구조 = {
    "상자": (_L("w", "d", "h") + _P3, b_상자, [.6, .6, 1, 0, 0, 0], ()),
    "원기둥": (_L("r", "h") + _P3, b_원기둥, [.3, 1, 0, 0, 0], ()),
    "원뿔": (_L("r", "h") + _P3, b_원뿔, [.35, 1, 0, 0, 0], ()),
    "구": (_L("r") + _P3, b_구, [.5, 0, 0, 0], ()),
    "두기둥대각": (_L("w", "d", "h") + [("a", (0.0, 0.4), "P"), ("b", POS, "P")] + _P3, b_대각,
              [.28, .28, 1, .22, -.22, 0, 0, 0], ("b부호",)),   # b < 0 — 창 좌표의 y 가 뒤집혀 있다. 첫 실행은 +.22 로 적어 천장 3D 가 0.000 이었다
    "두기둥나란히": (_L("w", "d", "h", "g") + _P3, b_나란히, [.28, .28, 1, .44, 0, 0, 0], ()),
    "상자45도": (_L("w", "d", "h") + [("rz", ROT, "A")] + _P3, b_45, [.6, .6, 1, 45, 0, 0, 0], ("rz",)),
    "L자": (_L("W1", "D1", "W2", "D2", "H") + [("x1", POS, "P"), ("y1", POS, "P"), ("x2", POS, "P"), ("z0", Z0R, "P")],
           b_L, [.6, .3, .3, .3, 1, 0, .15, -.15, 0], ("W2", "x2")),
    "치마": (_L("rb", "rt", "h") + [("th", THK, "T")] + _P3, b_치마,
           [.055 * S치, .455 * S치, 1, .035 * S치, 0, 0, 0], ()),      # 정답이 좁은 쪽 아래다 (원뿔과 같이 뒤집혔다)
    "토러스세움": (_L("R", "r") + _P3, b_토세, [.32 * S토, .16 * S토, 0, 0, 0], ()),
    "토러스옆": (_L("R", "r") + _P3, b_토옆, [.32 * S토, .16 * S토, 0, 0, 0], ()),
}


def b_상자합(t):
    out = None
    for k in range(len(t) // 6):
        cx, cy, z0, w, d, h = t[6 * k:6 * k + 6]
        b = _box(w, d, h, cx, cy, z0)
        out = b if out is None else out + b
    return out


def 대조구조(d):
    k = -(-d // 6)                                         # ceil — 대조군이 매개변수 수에서 안 밀리게
    return sum([[("cx%d" % i, POS, "P"), ("cy%d" % i, POS, "P"), ("z0%d" % i, Z0R, "P"),
                 ("w%d" % i, LEN, "L"), ("d%d" % i, LEN, "L"), ("h%d" % i, LEN, "L")] for i in range(k)], [])


def build(fn, theta):
    """θ -> 닫힌 다양체 trimesh. 빈 결과면 None."""
    man = fn([float(x) for x in theta])
    if man is None or man.is_empty() or man.status() != m3.Error.NoError:
        return None
    m = tm(man)
    assert m.is_watertight and m.volume > 0, "닫힌 다양체가 아니다"
    return m


# ── 목적함수 — `win.silhouette` 그대로 (같은 카메라) ─────────────────────────────

def sils(m, bs):
    V, F = np.asarray(m.vertices, float), np.asarray(m.faces)
    return {v: np.asarray(W.silhouette(V, F, v, bs if v == "back" else None)).astype(bool) for v in W.VIEWS}


def Jsil(m, masks, bs):
    if m is None:
        return 0.0
    s = sils(m, bs)
    return float(np.mean([(s[v] & masks[v]).sum() / max((s[v] | masks[v]).sum(), 1) for v in W.VIEWS]))


def 초기(name, seed):
    """치수 = 정답 x U(0.5,1.5) · 위치 = 정답 ± 0.18 · **식별 불가 축은 범위 균등** (정답을 안 흘린다)."""
    ps, _, t0, 균등 = 구조[name]
    rng = np.random.default_rng(1000 + seed)
    out = []
    for (n, (lo, hi), kind), v in zip(ps, t0):
        if n in 균등:
            x = rng.uniform(lo, hi)
        elif kind in "LT":
            x = v * rng.uniform(0.5, 1.5)
        else:
            x = v + rng.uniform(-0.18, 0.18)
        if n == "b" and "b부호" in 균등:                     # 부호는 정답과 무관한 동전
            x = abs(x) * (-1 if rng.random() < 0.5 else 1)
        out.append(float(np.clip(x, lo, hi)))
    return out


def 초기_대조(ps, seed):
    rng = np.random.default_rng(2000 + seed)
    out = []
    for n, (lo, hi), kind in ps:
        x = rng.uniform(0.2, 1.0) if kind == "L" else rng.uniform(-0.18, 0.18)
        out.append(float(np.clip(x, lo, hi)))
    return out


def cmaes(fn, ps, x0, masks, bs, seed):
    import cma
    lo = np.array([p[1][0] for p in ps])
    sp = np.array([p[1][1] - p[1][0] for p in ps])
    dec = lambda x: lo + np.clip(x, 0, 1) * sp
    f = lambda x: 1.0 - Jsil(build(fn, dec(x)), masks, bs)
    es = cma.CMAEvolutionStrategy(list((np.asarray(x0) - lo) / sp), SIGMA0,
                                  {"bounds": [0, 1], "seed": 100 + seed, "maxiter": MAXITER,
                                   "verbose": -9, "tolfun": 1e-7, "tolx": 1e-5})
    while not es.stop():
        X = es.ask()
        es.tell(X, [f(x) for x in X])
    return dec(es.result.xbest).tolist(), 1.0 - float(es.result.fbest), int(es.result.iterations), int(es.result.evaluations)


# ── 자 ───────────────────────────────────────────────────────────────────────

def vox(m):
    G, og = J.grid(m, J.PITCH)
    return fill_slices(G), og


def viou(a, b):
    A, B = J.common(a[0], a[1], b[0], b[1])
    return round(float((A & B).sum() / max((A | B).sum(), 1)), 5)


def 가볍(m, tv, tsil):
    """후보 하나마다 — 3D IoU(양쪽 채움) · held-out 30·45·60."""
    r = {"iou3d": viou(tv, vox(m))}
    for a in ANG:
        r["held%d" % a] = DG.iou(DG.sil(m, "front", None, a), tsil[a])
    r["held"] = round(float(np.mean([r["held%d" % a] for a in ANG])), 5)
    return r


def 무겁(m):
    d = dihedral(m)
    return {"거칠기": roughness(m)["거칠기"], "평평": d["평평"], "능선": d["능선"], "계단": d["계단"],
            "면": int(len(m.faces)), "닫힘": bool(m.is_watertight),
            "조각": int(len(trimesh.graph.connected_components(m.face_adjacency, nodes=np.arange(len(m.faces)))))}


def 오차(name, theta):
    ps, _, t0, _ = 구조[name]
    out = {}
    for (n, _, kind), v, x in zip(ps, t0, theta):
        sc = abs(v) if kind in "LT" else (90.0 if kind == "A" else 1.2)
        out[n] = round(abs(x - v) / sc, 4)
    return out


def 타일저장(m, frame, case, label, 글):
    from PIL import Image, ImageDraw
    from 계획 import _font
    os.makedirs(TILED, exist_ok=True)
    im = Image.fromarray(ME.타일(m, frame))
    ImageDraw.Draw(im).text((6, im.size[1] - 24), 글, fill=(200, 30, 30), font=_font(16))
    im.save(os.path.join(TILED, "%s__%s.png" % (case, label)))


# ── 한 도형 ──────────────────────────────────────────────────────────────────

def one(name):
    t0 = time.time()
    case = "도형_" + name
    ps, fn, th정답, _ = 구조[name]
    masks, bs = G3.art_masks(case), H.CASES[case]["back_sign"]
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    frame = ME.AL.frame_of(truth, 45)
    tsil = {a: DG.sil(truth, "front", None, a) for a in ANG}
    tv = vox(truth)
    out = {"case": case, "판": TAG, "군": "가능" if name in 가능 else "불가(예상)", "d": len(ps),
           "매개변수": [p[0] for p in ps], "θ정답": [round(float(x), 5) for x in th정답],
           "정답": 무겁(truth)}

    # 천장 = build(θ_정답). 배관: 실루엣 IoU >= 0.99
    mc = build(fn, th정답)
    jc = Jsil(mc, masks, bs)
    assert jc >= 0.99, "%s 배관 짐 — build(θ_정답) 실루엣 IoU %.4f < 0.99" % (name, jc)
    out["천장"] = {"J": round(jc, 5), **가볍(mc, tv, tsil), **무겁(mc)}
    # 실루엣 배관이 못 보는 것(앞뒤 · 거울)을 여기서 잡는다. 0.90 아래는 이산화가 아니라 build 가 틀린 것이다
    assert out["천장"]["iou3d"] >= 0.90, "%s 배관 짐 — build(θ_정답) 3D IoU %.4f" % (name, out["천장"]["iou3d"])
    print("  %s 천장 J %.4f · 3D %.4f · held %.4f" % (name, jc, out["천장"]["iou3d"], out["천장"]["held"]), flush=True)

    def 팔(fn_, ps_, inits, label):
        rs, ms = [], []
        for k, x0 in enumerate(inits):
            t1 = time.time()
            th, j, it, ev = cmaes(fn_, ps_, x0, masks, bs, k)
            m = build(fn_, th)
            r = {"씨앗": k, "θ0": [round(x, 4) for x in x0], "θ": [round(x, 5) for x in th], "J": round(j, 5),
                 "세대": it, "평가": ev, **가볍(m, tv, tsil), "초": round(time.time() - t1, 1)}
            rs.append(r)
            ms.append(m)
            print("    %s 씨앗%d J %.4f 3D %.4f held %.4f · %d세대 %.0f초"
                  % (label, k, j, r["iou3d"], r["held"], it, r["초"]), flush=True)
        return rs, ms

    rs, ms = 팔(fn, ps, [초기(name, k) for k in range(K재시작)], "코드기하")
    for r in rs:
        r["θ오차"] = 오차(name, r["θ"])
    b1 = int(np.argmax([r["J"] for r in rs]))                # **J 로 고른다** — 3D IoU 로 안 고른다
    t5 = int(np.argmax([r["iou3d"] for r in rs]))
    vs = [vox(m) for m in ms]
    s45 = [DG.sil(m, "front", None, 45) for m in ms]
    out["코드기하"] = {"재시작": rs, "최선1": b1, "top5": t5, **{"최선1_" + k: v for k, v in 무겁(ms[b1]).items()},
                   "후보쌍3D": [[viou(vs[i], vs[j]) for j in range(K재시작)] for i in range(K재시작)],
                   "후보쌍45": [[DG.iou(s45[i], s45[j]) for j in range(K재시작)] for i in range(K재시작)]}
    # 그림용 — J 순으로 서로 다른 최적점(쌍 3D IoU < 0.90)을 셋까지
    order = sorted(range(K재시작), key=lambda i: -rs[i]["J"])
    pick = []
    for i in order:
        if all(out["코드기하"]["후보쌍3D"][i][j] < 0.90 for j in pick):
            pick.append(i)
    out["코드기하"]["서로다른후보"] = pick
    for n_, i in enumerate(pick[:3]):
        타일저장(ms[i], frame, case, "후보%d" % n_, "3D %.3f · held %.3f · J %.4f" % (rs[i]["iou3d"], rs[i]["held"], rs[i]["J"]))

    psc = 대조구조(len(ps))
    rc, mcs = 팔(b_상자합, psc, [초기_대조(psc, k) for k in range(K재시작)], "대조")
    c1 = int(np.argmax([r["J"] for r in rc]))
    out["대조"] = {"d": len(psc), "재시작": rc, "최선1": c1, **{"최선1_" + k: v for k, v in 무겁(mcs[c1]).items()}}
    타일저장(mcs[c1], frame, case, "대조", "3D %.3f · held %.3f · J %.4f" % (rc[c1]["iou3d"], rc[c1]["held"], rc[c1]["J"]))
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
    done = rows()
    for name in [x for x in 구조 if "도형_" + x not in done][:n]:
        r = one(name)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  -> %s %.0f초" % (name, r["초"]), flush=True)


# ── 판정 ─────────────────────────────────────────────────────────────────────

def Hrows():
    return {c: r["판본"]["MC·불"] for c, r in ME.rows().items() if "MC·불" in r["판본"]}


def verdict():
    rs, Hr = rows(), Hrows()
    st = ME._st
    B = lambda n: rs["도형_" + n]["코드기하"]["재시작"][rs["도형_" + n]["코드기하"]["최선1"]]
    T = lambda n: rs["도형_" + n]["코드기하"]["재시작"][rs["도형_" + n]["코드기하"]["top5"]]
    Cn = lambda n: rs["도형_" + n]["대조"]["재시작"][rs["도형_" + n]["대조"]["최선1"]]
    있 = [n for n in 구조 if "도형_" + n in rs]
    뺀 = [n for n in 있 if n in 가능 and rs["도형_" + n]["천장"]["iou3d"] < 0.95]
    g1 = [n for n in 있 if n in 가능 and n not in 뺀]
    a = np.array([B(n)["iou3d"] for n in g1])
    need = int(np.ceil(0.8 * len(g1)))
    v = {"판": TAG, "때": time.strftime("%Y%m%d_%H%M"), "안잰": [n for n in 구조 if n not in 있],
         "천장3D<0.95로뺀도형": 뺀}
    v["Q1"] = {"군": g1, "문턱": "최선1 3D IoU 중앙 >= 0.95 · >=0.90 인 도형 >= 80%% (%d/%d)" % (need, len(g1)),
               "중앙": round(float(np.median(a)), 5), "평균": round(float(a.mean()), 5),
               "최악": round(float(a.min()), 5), "최악도형": g1[int(a.argmin())], ">=0.90": int((a >= 0.90).sum()),
               "통과": bool(np.median(a) >= 0.95 and (a >= 0.90).sum() >= need)}
    q2 = {}
    for n in [x for x in 있 if x in 불가]:
        k = rs["도형_" + n]["코드기하"]
        P3, P45 = np.array(k["후보쌍3D"]), np.array(k["후보쌍45"])
        iu = np.triu_indices(K재시작, 1)
        q2[n] = {"최선1_3D": B(n)["iou3d"], "최선1_J": B(n)["J"], "top5_3D": T(n)["iou3d"],
                 "top5에>=0.90": bool(T(n)["iou3d"] >= 0.90), "후보별3D": [r["iou3d"] for r in k["재시작"]],
                 "후보별J": [r["J"] for r in k["재시작"]], "후보별held": [r["held"] for r in k["재시작"]],
                 "서로다른후보수": len(k["서로다른후보"]), "후보쌍3D_최소": round(float(P3[iu].min()), 4),
                 "후보쌍45실루엣_최소": round(float(P45[iu].min()), 4)}
    v["Q2"] = {"서술": q2, "예상이틀렸나(셋 다 최선1>=0.95)": bool(q2 and all(x["최선1_3D"] >= 0.95 for x in q2.values()))}
    g3 = [n for n in 있 if n != "상자"]
    di = [B(n)["iou3d"] - Cn(n)["iou3d"] for n in g3]
    fl = lambda n, 팔: abs(rs["도형_" + n][팔]["최선1_평평"] - rs["도형_" + n]["정답"]["평평"])
    df = [fl(n, "대조") - fl(n, "코드기하") for n in g3]
    si, sf = st(di), st(df)
    v["Q3"] = {"군": g3, "문턱": "3D IoU 차 중앙 >= +0.02 · 승 과반 그리고 평평거리 차 중앙 > 0 · 승 과반",
               "3D차": si, "평평거리차(대조-코드)": sf,
               "통과": bool(si["중앙"] >= 0.02 and si["승"] * 2 > len(g3) and sf["중앙"] > 0 and sf["승"] * 2 > len(g3))}
    v["Q4(서술) 코드기하 최선1 − H"] = {
        "3D": st([B(n)["iou3d"] - Hr["도형_" + n]["iou128양쪽"] for n in 있]),
        "대각45": st([B(n)["held45"] - Hr["도형_" + n]["대각45"] for n in 있]),
        "거칠기": st([rs["도형_" + n]["코드기하"]["최선1_거칠기"] - Hr["도형_" + n]["거칠기"] for n in 있]),
        "능선거리(H-코드)": st([abs(Hr["도형_" + n]["능선"] - rs["도형_" + n]["정답"]["능선"])
                           - abs(rs["도형_" + n]["코드기하"]["최선1_능선"] - rs["도형_" + n]["정답"]["능선"]) for n in 있])}
    v["표"] = {n: {"군": rs["도형_" + n]["군"], "d": rs["도형_" + n]["d"], "천장3D": rs["도형_" + n]["천장"]["iou3d"],
                  "천장J": rs["도형_" + n]["천장"]["J"],
                  "최선1": {k: B(n)[k] for k in ("J", "iou3d", "held", "held45")}, "top5_3D": T(n)["iou3d"],
                  "대조": {k: Cn(n)[k] for k in ("J", "iou3d", "held")}, "대조d": rs["도형_" + n]["대조"]["d"],
                  "H": {"iou3d": Hr["도형_" + n]["iou128양쪽"], "대각45": Hr["도형_" + n]["대각45"],
                        "거칠기": Hr["도형_" + n]["거칠기"], "평평": Hr["도형_" + n]["평평"], "능선": Hr["도형_" + n]["능선"]},
                  "평평(정답/코드/대조)": [rs["도형_" + n]["정답"]["평평"], rs["도형_" + n]["코드기하"]["최선1_평평"],
                                    rs["도형_" + n]["대조"]["최선1_평평"]],
                  "능선(정답/코드)": [rs["도형_" + n]["정답"]["능선"], rs["도형_" + n]["코드기하"]["최선1_능선"]],
                  "거칠기(정답/코드)": [rs["도형_" + n]["정답"]["거칠기"], rs["도형_" + n]["코드기하"]["최선1_거칠기"]],
                  "θ오차최대": max(v_ for k_, v_ in B(n)["θ오차"].items() if k_ != "th"),
                  "θ오차": B(n)["θ오차"], "초": rs["도형_" + n]["초"]} for n in 있}
    p = os.path.join(HERE, "out", "기록", "코드기하도형_%s.json" % v["때"])
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %-10s %-8s %7s %7s %7s %7s %7s %7s %7s %6s" % ("도형", "군", "천장", "최선1", "top5", "held", "대조3D", "H 3D", "θ오차", "초"))
    for n, t in v["표"].items():
        print("  %-10s %-8s %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f %6.0f"
              % (n, t["군"], t["천장3D"], t["최선1"]["iou3d"], t["top5_3D"], t["최선1"]["held"],
                 t["대조"]["iou3d"], t["H"]["iou3d"], t["θ오차최대"], t["초"]))
    for k in ("Q1", "Q2", "Q3"):
        print("\n  %s %s" % (k, json.dumps(v[k], ensure_ascii=False)[:900]))
    print("\n  ->", p)
    return v


# ── 그림 ─────────────────────────────────────────────────────────────────────

def 그림():
    from PIL import Image
    rs = rows()
    cols = ("정답", "H (hull+깊이 · MC·불)", "자유도 대조 (상자 합)", "코드기하 최선1 (J)", "후보 2", "후보 3")
    R = []
    for name in 구조:
        c = "도형_" + name
        if c not in rs:
            continue
        ps = [os.path.join(ME.TILED, "%s__정답.png" % c), os.path.join(ME.TILED, "%s__MC·불.png" % c)] + \
             [os.path.join(TILED, "%s__%s.png" % (c, k)) for k in ("대조", "후보0", "후보1", "후보2")]
        n다 = len(rs[c]["코드기하"]["서로다른후보"])
        ts = [np.asarray(Image.open(p).convert("RGB")) if os.path.exists(p) and (i < 4 or i - 3 < n다)
              else np.full((300, 300, 3), 240, np.uint8) for i, p in enumerate(ps)]
        R.append((name + ("" if name in 가능 else " *"), ts))
    DC.grid(R, cols, "코드 기하 — 구조가 옳을 때 실루엣 3장이 치수를 정하는가 (45° 명암 · 같은 빛 · 같은 틀)",
            "* = 식별 불가(예상) · 빨간 글 = 3D IoU(양쪽 채움) · held-out 30·45·60 · J(실루엣 3장 IoU) · 후보 = 재시작 5 중 서로 다른 최적점(쌍 3D IoU < 0.90) · 빈 칸 = 다섯이 한 점에 모였다",
            os.path.join(HERE, "out", "코드기하_도형.png"), S=300)


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def selfcheck():
    H.register_sheets()
    rng = np.random.default_rng(0)
    for name, (ps, fn, t0, _) in 구조.items():
        assert len(ps) == len(t0), name
        m = build(fn, t0)
        case = "도형_" + name
        j = Jsil(m, G3.art_masks(case), H.CASES[case]["back_sign"])
        assert j >= 0.99, "%s 천장 실루엣 IoU %.4f" % (name, j)
        assert max(오차(name, t0).values()) == 0
        for _ in range(10):                                  # 범위 안 아무 θ 나 닫힌 다양체거나 None
            th = [rng.uniform(lo, hi) for _, (lo, hi), _ in ps]
            build(fn, th)
        x0 = 초기(name, 0)
        assert all(lo <= x <= hi for x, (_, (lo, hi), _) in zip(x0, ps))
        print("  %-8s d=%d 천장 J %.4f 면 %d" % (name, len(ps), j, len(m.faces)), flush=True)
    assert len(대조구조(7)) == 12 and len(대조구조(6)) == 6 and len(대조구조(4)) == 6
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
    elif a == "판정":
        verdict()
    elif a == "그림":
        그림()
    else:
        run(int(a))
