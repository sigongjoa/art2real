# -*- coding: utf-8 -*-
"""**선이 실루엣보다 무엇을 더 들고 있나** — 벤치에 선 채널을 만든다 (2026-09-20).

    python 선채널.py 검사        자가검사 (상자 한 개 · 홈 판 하나)
    python 선채널.py [n]         아직 안 한 장 n 개 -> out/선채널/<case>/*.png + out/기록/선채널_진행.jsonl
    python 선채널.py 판정        -> out/기록/선채널_<때>.json
    python 선채널.py 그림        -> out/선채널_접촉지.png

사용자 결정(09-20 밤): 「데이터를 더 추가하는 걸로 하자. 자는 굳이 건드릴 필요가 없어 보이는데?」
조사(`claudedocs/research_증거채널_20260920.md`)가 가리킨 문 둘 중 **선** 쪽이다.

우리 벤치는 정답 메시를 렌더한 3 판이라 **선이 없다.** 그래서 선을 증거로 쓰는 길을 시험할 수가 없었다.
여기서 정답 메시로부터 **선을 굽는다** — 그러면 선의 **정답표**가 생긴다. 공개 학습 모델이 없다고
조사가 말한 바로 그 칸(윤곽 대 크리스 · 볼록 대 오목)을 우리는 **공짜로** 가질 수 있다.

    0 배경 · 1 외곽선(실루엣 경계) · 2 가림선(안쪽 깊이 불연속) · 3 볼록 크리스 · 4 오목 크리스

**문턱을 돌리기 전에 적는다.**

    Q1  오목 크리스 화소의 **90% 이상이 실루엣 경계에서 떨어져 있다**
        -> 「선은 실루엣이 원리적으로 못 보는 것을 대량으로 들고 있다」가 숫자가 된다
    Q2  선 화소 중 **오목 크리스가 10% 이상**인 장이 절반을 넘는다
        -> 오목이 드문 예외가 아니라 일상이다
    Q3  궤짝 뚜껑의 널 홈이 **오목 크리스로 잡힌다** (눈으로 · 접촉지에서)

**이것은 자가 아니다.** 목적함수도 판정 문턱도 안 바꾼다. 벤치에 **채널 하나를 더하는 일**이다.
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
import 도안천장 as DA
CG, ME = DA.CG, DA.ME
H, W, J, DG, DC = DA.H, DA.W, DA.J, DA.DG, DA.DC
HERE = DA.HERE
OUT = os.path.join(HERE, "out", "기록")
DST = os.path.join(HERE, "out", "선채널")
PROG = os.path.join(OUT, "선채널_진행.jsonl")
TAG = "선채널 v1 · 정답 메시에서 구운 선 · 외곽/가림/볼록크리스/오목크리스 (2026-09-20)"

S = 512                       # 저장 해상도. 래스터는 2S 로 하고 2×2 로 줄인다
각문턱 = 20.0                 # 이면각이 이보다 크면 크리스
깊이문턱 = 0.02               # 창 단위. 화소 사이 깊이 차가 이보다 크면 가림선
# (이름, 방위각, 고도). **우리 렌더 배관은 전부 고도 0 이다** — 그래서 윗면에 팬 홈은
# 어느 판에도 안 나온다. 고도는 카메라가 아니라 **메시를 x 축으로 돌려서** 준다 (`DC.project` 를 안 고친다).
뷰 = (("front", 0, 0), ("side", -90, 0), ("back", 180, 0), ("d45", 45, 0), ("위45", 45, 45))
Q1문턱, Q2몫, Q2장 = 0.90, 0.10, 0.5
라벨색 = np.array([[247, 247, 247], [20, 20, 20], [225, 60, 60], [40, 110, 210], [240, 170, 30]], np.uint8)
라벨이름 = ("배경", "외곽선", "가림선", "볼록크리스", "오목크리스")


# ── 면 번호 + 깊이 버퍼 ──────────────────────────────────────────────────────

def 버퍼(mesh, az, frame, R):
    """(면 번호 idx, 깊이 zb). `폴리싱.shaded` 의 래스터를 그대로 쓴다 — 새로 안 짠다."""
    P = DC.project(mesh, az, frame, R)[np.asarray(mesh.faces)]
    zb = np.full((R, R), np.inf, np.float64)
    idx = np.full((R, R), -1, np.int32)
    lo = np.clip(np.floor(P[:, :, :2].min(1)), 0, R - 1).astype(int)
    hi = np.clip(np.ceil(P[:, :, :2].max(1)), 0, R - 1).astype(int)
    for i in range(len(P)):
        (x1, y1, d1), (x2, y2, d2), (x3, y3, d3) = P[i]
        den = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(lo[i, 0], hi[i, 0] + 1) + 0.5,
                             np.arange(lo[i, 1], hi[i, 1] + 1) + 0.5)
        l1 = ((y2 - y3) * (gx - x3) + (x3 - x2) * (gy - y3)) / den
        l2 = ((y3 - y1) * (gx - x3) + (x1 - x3) * (gy - y3)) / den
        l3 = 1 - l1 - l2
        m = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
        if not m.any():
            continue
        d = l1 * d1 + l2 * d2 + l3 * d3
        sz = zb[lo[i, 1]:hi[i, 1] + 1, lo[i, 0]:hi[i, 0] + 1]
        si = idx[lo[i, 1]:hi[i, 1] + 1, lo[i, 0]:hi[i, 0] + 1]
        up = m & (d < sz)
        sz[up] = d[up]
        si[up] = i
    return idx, zb


def 선(mesh, az, frame, s=S):
    """면 번호가 바뀌는 자리를 네 종류로 가른다. 볼록/오목은 **부호 있는 이면각**으로.

    두 면의 중심 c1 · c2 와 법선 n1 에 대해 (c2 − c1)·n1 < 0 이면 능선(볼록) · > 0 이면 골(오목)."""
    R = 2 * s
    idx, zb = 버퍼(mesh, az, frame, R)
    N = np.asarray(mesh.face_normals)
    C = np.asarray(mesh.triangles_center)
    a = np.radians(az)
    c_, s_ = np.cos(a), np.sin(a)
    rot = lambda A: np.stack([c_ * A[:, 0] - s_ * A[:, 1], s_ * A[:, 0] + c_ * A[:, 1], A[:, 2]], 1)
    N, C = rot(N), rot(C)
    lab = np.zeros((R, R), np.uint8)
    있 = idx >= 0
    for dy, dx in ((0, 1), (1, 0)):
        A = idx[:R - dy, :R - dx]
        B = idx[dy:, dx:]
        다 = (A != B)
        # 1) 외곽선 — 한쪽이 배경
        밖 = 다 & ((A < 0) | (B < 0))
        # 2~4) 둘 다 면인데 번호가 다르다
        안 = 다 & (A >= 0) & (B >= 0)
        ys, xs = np.where(안)
        if len(ys):
            i1, i2 = A[ys, xs], B[ys, xs]
            d1 = zb[:R - dy, :R - dx][ys, xs]
            d2 = zb[dy:, dx:][ys, xs]
            ang = np.degrees(np.arccos(np.clip((N[i1] * N[i2]).sum(1), -1, 1)))
            볼 = ((C[i2] - C[i1]) * N[i1]).sum(1) < 0
            깊 = np.abs(d1 - d2) > 깊이문턱
            v = np.where(깊, 2, np.where(ang < 각문턱, 0, np.where(볼, 3, 4))).astype(np.uint8)
            for k, (yy, xx) in ((0, (ys, xs)), (dy, (ys + dy, xs))):
                np.maximum.at(lab, (yy, xx + (0 if k == 0 else dx)), 0)      # 자리만 맞춘다
            lab[ys, xs] = np.maximum(lab[ys, xs], v)
            lab[ys + dy, xs + dx] = np.maximum(lab[ys + dy, xs + dx], v)
        ys, xs = np.where(밖)
        # 외곽선은 **물건 쪽 화소**에만 찍는다 (배경에 안 찍는다)
        for yy, xx, sel in ((ys, xs, 있[:R - dy, :R - dx][ys, xs]),
                            (ys + dy, xs + dx, 있[dy:, dx:][ys, xs])):
            lab[yy[sel], xx[sel]] = np.maximum(lab[yy[sel], xx[sel]], 1)
    # 2×2 로 줄인다 — 같은 칸 안에서 **큰 번호가 이긴다** (선이 사라지지 않게)
    return lab.reshape(s, 2, s, 2).max((1, 3)), 있.reshape(s, 2, s, 2).any((1, 3))


def 색칠(lab):
    return 라벨색[lab]


def 기울(mesh, elev):
    """고도 `elev` 로 내려다보기 = 메시를 x 축 둘레로 **+elev** 만큼 돌린다.
    부호를 반대로 넣으면 밑바닥을 보게 된다 — 첫 판이 그래서 윗면 홈을 못 찾았다.
    깊이 축은 +y(멀어짐)라 윗면 법선의 y 성분이 **음수**가 되어야 카메라를 향한다."""
    if not elev:
        return mesh
    m = mesh.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(elev), [1, 0, 0]))
    return m


# ── 한 장 ────────────────────────────────────────────────────────────────────

def 사례():
    b = json.load(open(os.path.join(HERE, "벤치.json"), encoding="utf-8"))
    cs = [c["name"] for c in b["cases"]]
    cs += ["도형_" + n for n in CG.구조]
    return [c for c in cs if os.path.exists(os.path.join(HERE, "out", "시트", c, "truth.glb"))]


def one(case):
    from PIL import Image
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    d = os.path.join(DST, case)
    os.makedirs(d, exist_ok=True)
    r = {"case": case, "판": TAG, "면": int(len(truth.faces)), "뷰": {}}
    for 이름, az, el in 뷰:
        m = 기울(truth, el)
        frame = ME.AL.frame_of(m, az)
        lab, 있 = 선(m, az, frame)
        Image.fromarray(색칠(lab)).save(os.path.join(d, "%s.png" % 이름))
        np.save(os.path.join(d, "%s.npy" % 이름), lab)
        n = {라벨이름[k]: int((lab == k).sum()) for k in range(1, 5)}
        선화소 = sum(n.values())
        # **오목 크리스가 실루엣 경계에서 얼마나 떨어져 있나** — 외곽선을 3 화소 부풀려 뺀다
        from scipy import ndimage
        가 = ndimage.binary_dilation(lab == 1, np.ones((7, 7), bool))
        오 = lab == 4
        r["뷰"][이름] = {**n, "선화소": 선화소,
                       "오목몫": round(n["오목크리스"] / max(선화소, 1), 4),
                       "오목_실루엣밖": int((오 & ~가).sum()),
                       "오목_실루엣밖몫": round(float((오 & ~가).sum() / max(오.sum(), 1)), 4) if 오.any() else None,
                       "채움": round(float(있.mean()), 4)}
    v = [r["뷰"][n]["오목_실루엣밖몫"] for n, _, _ in 뷰 if r["뷰"][n]["오목_실루엣밖몫"] is not None]
    r["오목_실루엣밖몫_평균"] = round(float(np.mean(v)), 4) if v else None
    r["오목몫_평균"] = round(float(np.mean([r["뷰"][n]["오목몫"] for n, _, _ in 뷰])), 4)
    r["초"] = round(time.time() - t0, 1)
    return r


def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            x = json.loads(line)
            if x.get("판") == TAG:
                out[x["case"]] = x
    return out


def run(n):
    done = rows()
    todo = [c for c in 사례() if c not in done][:n]
    for c in todo:
        r = one(c)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  %-38s 오목몫 %.3f · 실루엣밖 %s · %.0f초"
              % (c, r["오목몫_평균"],
                 "%.3f" % r["오목_실루엣밖몫_평균"] if r["오목_실루엣밖몫_평균"] is not None else "-",
                 r["초"]), flush=True)


# ── 판정 ─────────────────────────────────────────────────────────────────────

def verdict():
    rs = rows()
    cs = sorted(rs)
    밖 = [rs[c]["오목_실루엣밖몫_평균"] for c in cs if rs[c]["오목_실루엣밖몫_평균"] is not None]
    몫 = [rs[c]["오목몫_평균"] for c in cs]
    v = {"판": TAG, "때": time.strftime("%Y%m%d_%H%M"), "장": len(cs),
         "안잰": [c for c in 사례() if c not in rs],
         "Q1": {"문턱": "오목 크리스 화소의 %g 이상이 실루엣 경계 밖" % Q1문턱,
                "중앙": round(float(np.median(밖)), 4) if 밖 else None,
                "장수": len(밖), "넘은장": int(sum(1 for x in 밖 if x >= Q1문턱)),
                "통과": bool(밖 and np.median(밖) >= Q1문턱)},
         "Q2": {"문턱": "선 화소 중 오목 크리스가 %g 이상인 장이 절반 넘는다" % Q2몫,
                "중앙": round(float(np.median(몫)), 4), "넘은장": int(sum(1 for x in 몫 if x >= Q2몫)),
                "통과": bool(sum(1 for x in 몫 if x >= Q2몫) > Q2장 * len(몫))},
         "표": {c: {"오목몫": rs[c]["오목몫_평균"], "오목_실루엣밖": rs[c]["오목_실루엣밖몫_평균"],
                   "면": rs[c]["면"], "뷰별오목몫": {n: rs[c]["뷰"][n]["오목몫"] for n, _, _ in 뷰},
                   "초": rs[c]["초"]} for c in cs}}
    p = os.path.join(OUT, "선채널_%s.json" % v["때"])
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %-38s %8s %10s" % ("장", "오목몫", "실루엣밖"))
    for c in cs:
        print("  %-38s %8.3f %10s" % (c, rs[c]["오목몫_평균"],
                                      "%.3f" % rs[c]["오목_실루엣밖몫_평균"]
                                      if rs[c]["오목_실루엣밖몫_평균"] is not None else "-"))
    for k in ("Q1", "Q2"):
        print("\n  %s %s" % (k, json.dumps(v[k], ensure_ascii=False)))
    print("\n  ->", p)
    return v


# ── 그림 ─────────────────────────────────────────────────────────────────────

def 그림(cases=None):
    from PIL import Image
    rs = rows()
    cs = cases or [c for c in ("cloak_Chest_Closed_AngpV0HxD8", "mech_Drill_8uBbH7Dvmb",
                               "knight_Warrior_RaWl2GJ0NZ", "wizard_Evil_Wizard_bdxawstqtq",
                               "monster_Mimic_B8HrWzkuNp", "도형_상자") if c in rs]
    R = []
    for c in cs:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        frame = ME.AL.frame_of(truth, 45)
        ts = [ME.타일(truth, frame)]
        for 이름, _, _ in 뷰:
            p = os.path.join(DST, c, "%s.png" % 이름)
            ts.append(np.asarray(Image.open(p).convert("RGB")))
        R.append(("%s\n오목 %.3f · 밖 %s" % (c[:22], rs[c]["오목몫_평균"],
                                          "%.2f" % rs[c]["오목_실루엣밖몫_평균"]
                                          if rs[c]["오목_실루엣밖몫_평균"] is not None else "-"), ts))
    DC.grid(R, ("45° 명암 (정답)", "앞 선", "옆 선", "뒤 선", "45° 선", "위에서 45° 선"),
            "선 채널 — 정답 메시에서 구운 선의 정답표 (벤치에 없던 채널)",
            "검정 = 외곽선(실루엣 경계) · 빨강 = 가림선(안쪽 깊이 불연속) · 파랑 = 볼록 크리스 · 주황 = **오목 크리스**. "
            "실루엣은 검정만 본다 — 나머지 셋이 실루엣이 원리적으로 못 보는 것이다",
            os.path.join(HERE, "out", "선채널_접촉지.png"), S=330)


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def selfcheck():
    import manifold3d as m3
    M = m3.Manifold
    # 상자 하나 — 크리스는 전부 볼록이어야 한다 (오목 0)
    box = CG.tm(M.cube([1, 1, 1], True))
    fr = ME.AL.frame_of(box, 45)
    lab, _ = 선(box, 45, fr, s=256)
    n = {k: int((lab == k).sum()) for k in range(1, 5)}
    assert n[3] > 0 and n[4] == 0, "상자에 오목 크리스가 났다 %s" % n
    # 홈 판 — 위에서 골을 판 상자. 오목이 볼록보다 많아야 한다 (골 벽 둘 × 두 모서리)
    # **윗면에 판 홈** — 고도 0 에서는 바닥도 벽도 안 보여 오목 크리스가 0 이다(그 자체가 발견이라
    # `위45` 판을 더했다). 고도 45 로 내려다보면 나와야 한다. **둘 다 검사한다.**
    슬 = M.cube([0.3, 2, 0.4], True).translate([0, 0, 0.5])
    홈 = CG.tm(M.cube([1, 1, 1], True) - 슬)
    평, _ = 선(홈, 45, ME.AL.frame_of(홈, 45), s=256)
    assert int((평 == 4).sum()) == 0, "고도 0 에서 윗면 홈의 오목 크리스가 보인다 — 배관 짐"
    위 = 기울(홈, 45)
    lab2, _ = 선(위, 45, ME.AL.frame_of(위, 45), s=256)
    n2 = {k: int((lab2 == k).sum()) for k in range(1, 5)}
    assert n2[4] > 0, "홈을 팠는데 오목 크리스가 0 이다 %s" % n2
    print("  자가검사 통과 — 상자 %s · 홈 판 상자 %s" % (n, n2))


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
