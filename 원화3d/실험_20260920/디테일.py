# -*- coding: utf-8 -*-
"""**디테일은 도안으로 살릴 수 있는가** — 궤짝 뚜껑의 널 홈 (2026-09-20).

    python 디테일.py 읽기     앞 실루엣에서 뚜껑 마루 높이 곡선 -> 홈 찾기 (측정만) -> out/디테일_읽기.png
    python 디테일.py 판정     v0(홈 없음) 대 v1(홈) -> out/기록/디테일_<때>.json
    python 디테일.py 그림     -> out/디테일_궤짝.png

사용자(09-20 밤): 「shape 은 잘 찾아. 그런데 디테일은 그냥 싹 다 뭉개졌는데?」
잔차가 그 말을 숫자로 받았다 — 궤짝은 정답의 99.5% 를 덮고(못덮음 0.005) 잃은 것은
**넘침 0.105** 이며 그 56% 가 뚜껑 하나다. 오목한 디테일(홈)은 **안 깎아서** 넘침으로 나온다.

**문턱은 돌리기 전에 적는다.**

    Q1  v1 이 넘침을 0.105 -> **0.08 이하**로 낮춘다
    Q2  v1 의 3D IoU 가 0.892 -> **0.91 이상**
    Q3  v1 이 게이트를 그대로 지난다 (조각 1 · 접촉 한 덩어리 · 부착 선언 참)
    Q4  홈 축이 목적함수에 **반응한다** (max|ΔJ| >= 0.001) — 고리처럼 안 보이는 축이면
        「도안에 적을 수는 있어도 맞출 수는 없다」가 된다

**홈은 원화에서 읽는다.** 정답 메시를 안 본다 — 앞 실루엣 마스크의 열마다 제일 위 화소를
z 로 바꾼 곡선(`마루높이`)에서, 널 꼭대기 포락선보다 깊이 꺼진 구간을 홈으로 잡는다.
포락선은 홈 폭보다 넓은 창의 이동 최대값이다.
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
import 게이트 as GT
CG, ME = DA.CG, DA.ME
H, W, J, DG, DC = DA.H, DA.W, DA.J, DA.DG, DA.DC
HERE, M = DA.HERE, DA.M
OUT = os.path.join(HERE, "out", "기록")
CASE = "cloak_Chest_Closed_AngpV0HxD8"
TAG = "디테일 v1 · 궤짝 뚜껑 널 홈 · 원화 앞 실루엣에서 읽음 (2026-09-20)"

포락창 = 0.26          # 창 단위. 홈 폭(≈0.15)보다 넓게 — 이동 최대값이 널 꼭대기만 잇게 한다
홈문턱 = 0.012         # 포락선보다 이만큼 꺼지면 홈. 격자 한 칸(0.0078)의 1.5 배
최소홈폭 = 0.02
Q1넘침, Q2삼디 = 0.08, 0.91


# ── 원화에서 읽기 ────────────────────────────────────────────────────────────

def 눈금(case):
    """도안 v0 의 실루엣으로 화소 ↔ 창 좌표를 맞춘다 (정답 메시를 안 본다)."""
    sp = DA.도안[case][0]
    m = CG.tm(DA.합(DA.도안[case][1]([float(x[1]) for x in sp])))
    S = CG.sils(m, H.CASES[case]["back_sign"])["front"]
    ys, xs = np.where(S.any(1))[0], np.where(S.any(0))[0]
    전고 = 1.001
    반폭 = max(abs(v) for n, v, _, _ in sp if n == "bandw") * \
           [v for n, v, _, _ in sp if n == "sx"][0]
    z_of = lambda y: 전고 * (ys.max() - y) / (ys.max() - ys.min())
    x_of = lambda c: 반폭 * (2 * (c - xs.min()) / (xs.max() - xs.min()) - 1)
    return z_of, x_of, (xs.min(), xs.max())


def 마루높이(case):
    """앞 마스크의 열마다 제일 위 화소 -> (x, z_top). 뚜껑 위는 y 로 밀어낸 홈이라
    앞 투영의 꼭대기가 곧 **홈 바닥 높이**다."""
    Mk = CG.G3.art_masks(case)["front"]
    z_of, x_of, _ = 눈금(case)
    xs, zs = [], []
    for c in range(Mk.shape[1]):
        col = np.where(Mk[:, c])[0]
        if len(col):
            xs.append(x_of(c))
            zs.append(z_of(col.min()))
    return np.asarray(xs), np.asarray(zs)


def 홈찾기(case):
    x, z = 마루높이(case)
    dx = float(np.median(np.diff(x)))
    k = int(round(포락창 / dx)) | 1
    # **양쪽이 다 솟아야 홈이다.** 한쪽 이동 최대만 쓰면 아치가 내려가는 비탈이 통째로 홈으로 잡힌다
    # (첫 판에서 x ±0.66 이 그렇게 잡혔다 — 널이 아니라 뚜껑 옆면이다).
    pad = np.pad(z, k, mode="edge")
    n = len(z)
    좌 = np.array([pad[i:i + k + 1].max() for i in range(n)])          # 왼쪽 창의 최대
    우 = np.array([pad[i + k:i + 2 * k + 1].max() for i in range(n)])  # 오른쪽 창의 최대
    env = np.minimum(좌, 우)
    깊 = env - z
    안 = 깊 > 홈문턱
    홈, i = [], 0
    while i < len(안):
        if 안[i]:
            k0 = i
            while i < len(안) and 안[i]:
                i += 1
            if x[i - 1] - x[k0] >= 최소홈폭:
                s = slice(k0, i)
                홈.append({"중심": round(float((x[k0] + x[i - 1]) / 2), 4),
                          "반폭": round(float((x[i - 1] - x[k0]) / 2), 4),
                          "바닥z": round(float(np.median(z[s])), 4),
                          "깊이": round(float(np.median(깊[s])), 4)})
        else:
            i += 1
    return 홈, (x, z, env)


# ── 도안 v1 = v0 + 뚜껑 홈 ───────────────────────────────────────────────────

def 부품_v1(t, 홈):
    parts = DA.궤짝_부품(t)
    lid = [p for n, p in parts if n == "뚜껑"][0]
    for g in 홈:
        top = 2.0
        lid = lid - M.cube([2 * g["반폭"], 4.0, 2 * (top - g["바닥z"])], True) \
                     .translate([g["중심"], 0, g["바닥z"] + (top - g["바닥z"])])
    return [(n, p) for n, p in parts if n != "뚜껑"] + [("뚜껑", lid)]


def 부품_v2(t, 홈):
    """**v1 을 돌려 본 뒤에 쓴 판본이다** (문턱은 안 바꿨다 — 같은 Q1 · Q2 를 건다).
    v1 은 홈을 마루에서만 판다. 앞 실루엣은 홈이 윤곽을 자르는 마루 근처만 보여 주니
    거기까지가 **읽은 것**이다. v2 는 「홈이 같은 깊이로 비탈까지 이어진다」는 **가정**을 더한다
    (출처 derived). 깊이는 v1 과 같은 측정값을 쓴다.

    안쪽 뚜껑 = 여섯 방향 평행이동의 교집합 = 깊이 d 의 (축방향) 침식."""
    parts = DA.궤짝_부품(t)
    lid = [p for n, p in parts if n == "뚜껑"][0]
    for g in 홈:
        d = g["깊이"]
        속 = lid
        for ax in range(3):
            for s in (+d, -d):
                v = [0.0, 0.0, 0.0]
                v[ax] = s
                속 = 속 ^ lid.translate(v)
        슬 = M.cube([2 * g["반폭"], 4.0, 4.0], True).translate([g["중심"], 0, 0])
        lid = (lid - 슬) + (속 ^ 슬)
    return [(n, p) for n, p in parts if n != "뚜껑"] + [("뚜껑", lid)]


def 만들기_v1(홈):
    return lambda t: DA.합(부품_v1([float(x) for x in t], 홈))


# ── 판정 ─────────────────────────────────────────────────────────────────────

def 재기(m, truth, masks, bs):
    (T, ot), (O, oo) = CG.vox(truth), CG.vox(m)
    A, B = J.common(T, ot, O, oo)
    return {"3D IoU": round(float((A & B).sum() / max((A | B).sum(), 1)), 5),
            "못덮음몫": round(float((A & ~B).sum() / max(A.sum(), 1)), 4),
            "넘침몫": round(float((B & ~A).sum() / max(B.sum(), 1)), 4),
            "J": round(CG.Jsil(m, masks, bs), 5),
            "조각": GT.조각(m), "부피": round(float(m.volume), 5)}


def verdict():
    H.register_sheets()
    홈, _ = 홈찾기(CASE)
    sp = DA.도안[CASE][0]
    t = [float(x[1]) for x in sp]
    masks, bs = CG.G3.art_masks(CASE), H.CASES[CASE]["back_sign"]
    truth = trimesh.load(os.path.join(HERE, "out", "시트", CASE, "truth.glb"), force="mesh")
    스펙 = GT.스펙읽기(CASE)
    v = {"판": TAG, "때": time.strftime("%Y%m%d_%H%M"),
         "문턱": {"Q1": "넘침 <= %g" % Q1넘침, "Q2": "3D IoU >= %g" % Q2삼디,
                 "Q3": "게이트 그대로 통과", "Q4": "홈 축 max|dJ| >= %g" % GT.민감_문턱},
         "홈": 홈, "홈수": len(홈), "읽은법": "앞 실루엣 마루높이 − 이동최대 포락선(창 %g) > %g" % (포락창, 홈문턱)}
    m0 = CG.tm(DA.합(DA.도안[CASE][1](t)))
    m1 = CG.tm(DA.합(부품_v1(t, 홈)))
    m2 = CG.tm(DA.합(부품_v2(t, 홈)))
    v["v0"] = 재기(m0, truth, masks, bs)
    v["v1"] = 재기(m1, truth, masks, bs)
    v["v2"] = 재기(m2, truth, masks, bs)
    v["v2판정"] = {"Q1": bool(v["v2"]["넘침몫"] <= Q1넘침), "Q2": bool(v["v2"]["3D IoU"] >= Q2삼디),
                 "note": "v2 는 v1 을 본 뒤에 쓴 판본이다. 문턱은 그대로 쓴다"}
    # Q5 — **어느 자가 눈과 같은 순위를 내나.** 45° 명암 이미지 거리 · 면 통계 거리
    frame = ME.AL.frame_of(truth, 45)
    타 = {n: ME.타일(mm, frame, S=512).astype(np.float32)
         for n, mm in (("정답", truth), ("v0", m0), ("v1", m1), ("v2", m2))}
    from 면 import dihedral, roughness
    통 = {n: {**{k: dihedral(mm)[k] for k in ("평평", "능선", "계단")},
              "거칠기": roughness(mm)["거칠기"]}
         for n, mm in (("정답", truth), ("v0", m0), ("v1", m1), ("v2", m2))}
    v["Q5 자"] = {"45°명암 L1(정답 대비 · 낮을수록 닮음)":
                 {n: round(float(np.abs(타[n] - 타["정답"]).mean()), 3) for n in ("v0", "v1", "v2")},
                 "면통계": 통,
                 "면통계 거리(정답 대비 · 평평+능선)":
                 {n: round(sum(abs(통[n][k] - 통["정답"][k]) for k in ("평평", "능선")), 4)
                  for n in ("v0", "v1", "v2")}}
    # 게이트 — v1 의 부품으로
    ps = [(n, CG.tm(p)) for n, p in 부품_v1(t, 홈)]
    names = [n for n, _ in ps]
    붙음 = [[False] * len(ps) for _ in ps]
    for i in range(len(ps)):
        for k in range(i + 1, len(ps)):
            d = min(GT.표면거리(ps[i][1], ps[k][1]), GT.표면거리(ps[k][1], ps[i][1]))
            붙음[i][k] = 붙음[k][i] = bool(d <= GT.EPS)
    ds = GT.덩어리(names, 붙음)
    v["v1게이트"] = {"조각": v["v1"]["조각"], "기대": 스펙["조각수"], "덩어리": ds,
                   "G1": "통과" if v["v1"]["조각"] == 스펙["조각수"] else "실패",
                   "G2": "통과" if len(ds) == 1 else "실패"}
    # Q4 — 홈 축(바닥z)을 흔들어 J 가 반응하나
    반응 = []
    J1 = v["v1"]["J"]
    for i in range(len(홈)):
        ds_ = []
        for s in (+1, -1):
            g2 = [dict(g) for g in 홈]
            g2[i]["바닥z"] = float(np.clip(g2[i]["바닥z"] + s * 0.05 * 0.4, 0.5, 1.0))
            ds_.append(abs(CG.Jsil(CG.tm(DA.합(부품_v1(t, g2))), masks, bs) - J1))
        반응.append(round(max(ds_), 6))
    v["Q4 홈바닥 dJ"] = 반응
    v["판정"] = {"Q1": bool(v["v1"]["넘침몫"] <= Q1넘침), "Q2": bool(v["v1"]["3D IoU"] >= Q2삼디),
                "Q3": bool(v["v1게이트"]["G1"] == "통과" and v["v1게이트"]["G2"] == "통과"),
                "Q4": bool(min(반응) >= GT.민감_문턱)}
    p = os.path.join(OUT, "디테일_%s.json" % v["때"])
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  홈 %d 개 %s" % (len(홈), [(g["중심"], g["반폭"], g["깊이"]) for g in 홈]))
    for n in ("v0", "v1", "v2"):
        r = v[n]
        print("  %-3s 3D %.4f · 못덮음 %.3f · 넘침 %.3f · J %.4f · 조각 %d · 부피 %.4f"
              % (n, r["3D IoU"], r["못덮음몫"], r["넘침몫"], r["J"], r["조각"], r["부피"]))
    print("  Q4 홈바닥 dJ %s" % 반응)
    print("  판정 %s" % json.dumps(v["판정"], ensure_ascii=False))
    print("  ->", p)
    return v


# ── 그림 ─────────────────────────────────────────────────────────────────────

def 읽기그림():
    from PIL import Image, ImageDraw
    from 계획 import _font
    H.register_sheets()
    홈, (x, z, env) = 홈찾기(CASE)
    Wd, Ht = 1400, 460
    im = Image.new("RGB", (Wd, Ht), "white")
    d = ImageDraw.Draw(im)
    d.text((16, 12), "뚜껑 마루 높이 — 앞 실루엣의 열마다 제일 위 화소 (정답 메시를 안 본다)",
           fill=(20, 20, 20), font=_font(20))
    d.text((16, 40), "회색 = 널 꼭대기 포락선(이동 최대 %g) · 검정 = 읽은 마루 · 빨강 = 홈으로 잡은 구간 (%d 개)"
           % (포락창, len(홈)), fill=(90, 90, 90), font=_font(14))
    L, Rr, T, B = 70, Wd - 20, 80, Ht - 40
    z0, z1 = 0.85, 1.01
    px = lambda xx: L + (xx - x.min()) / (x.max() - x.min()) * (Rr - L)
    py = lambda zz: B - (zz - z0) / (z1 - z0) * (B - T)
    for g in 홈:
        d.rectangle([px(g["중심"] - g["반폭"]), T, px(g["중심"] + g["반폭"]), B], fill=(255, 232, 232))
    d.line([(L, py(z0)), (L, py(z1))], fill=(0, 0, 0))
    for zz in (0.85, 0.90, 0.95, 1.00):
        d.text((20, py(zz) - 8), "%.2f" % zz, fill=(60, 60, 60), font=_font(13))
        d.line([(L - 4, py(zz)), (L, py(zz))], fill=(0, 0, 0))
    d.line([(px(a), py(b)) for a, b in zip(x, env)], fill=(170, 170, 170), width=3)
    d.line([(px(a), py(b)) for a, b in zip(x, z)], fill=(0, 0, 0), width=2)
    for g in 홈:
        d.text((px(g["중심"]) - 26, B + 6), "%.2f" % g["중심"], fill=(200, 30, 30), font=_font(13))
        d.text((px(g["중심"]) - 26, T - 18), "깊이 %.3f" % g["깊이"], fill=(200, 30, 30), font=_font(13))
    dst = os.path.join(HERE, "out", "디테일_읽기.png")
    im.save(dst)
    print("  ->", dst)


def 그림():
    from PIL import Image, ImageDraw
    from 계획 import _font
    H.register_sheets()
    ps_ = sorted([f for f in os.listdir(OUT) if f.startswith("디테일_")])
    v = json.load(open(os.path.join(OUT, ps_[-1]), encoding="utf-8"))
    홈 = v["홈"]
    sp = DA.도안[CASE][0]
    t = [float(x[1]) for x in sp]
    truth = trimesh.load(os.path.join(HERE, "out", "시트", CASE, "truth.glb"), force="mesh")
    frame = ME.AL.frame_of(truth, 45)
    m0 = CG.tm(DA.합(DA.도안[CASE][1](t)))
    m1 = CG.tm(DA.합(부품_v1(t, 홈)))
    m2 = CG.tm(DA.합(부품_v2(t, 홈)))
    (T, ot) = CG.vox(truth)
    ts, cs = [], []
    for n, mm, r in (("정답", truth, None), ("도안 v0 (홈 없음)", m0, v["v0"]),
                     ("v1 홈 %d · 마루만" % len(홈), m1, v["v1"]),
                     ("v2 홈이 비탈까지 (가정)", m2, v["v2"])):
        im = Image.fromarray(ME.타일(mm, frame))
        if r:
            ImageDraw.Draw(im).text((6, im.size[1] - 22), "3D %.3f · 넘침 %.3f" % (r["3D IoU"], r["넘침몫"]),
                                    fill=(200, 30, 30), font=_font(15))
        ts.append(np.asarray(im))
        cs.append(n)
    for n, mm in (("v0 넘친 곳", m0), ("v2 넘친 곳", m2)):
        O, oo = CG.vox(mm)
        A, B = J.common(T, ot, O, oo)
        r = GT.잔차메시(B & ~A, np.minimum(ot, oo))
        ts.append(np.asarray(Image.fromarray(ME.타일(r, frame))) if r is not None
                  else np.full((300, 300, 3), 240, np.uint8))
        cs.append(n)
    dst = os.path.join(HERE, "out", "디테일_궤짝.png")
    DC.grid([("궤짝 뚜껑 널 홈", ts)], cs,
            "디테일 — 홈을 도안에 넣으면 살아나는가 (45° 명암 · 같은 틀)",
            "홈은 원화 앞 실루엣의 마루 높이에서 읽었다 (정답 메시를 안 봤다) · 빨간 글 = 3D IoU · 넘침 몫",
            dst, S=380)


if __name__ == "__main__":
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass
    a = sys.argv[1] if len(sys.argv) > 1 else "판정"
    {"읽기": 읽기그림, "판정": verdict, "그림": 그림}[a]()
