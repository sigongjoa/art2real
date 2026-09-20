# -*- coding: utf-8 -*-
"""**입력을 진단한다 — 방법이 아니라 원화 · 시트를 잰다** (2026-09-20).

    python 원화진단.py 검사    자가검사 (합성 마스크로 항목마다 하나씩)
    python 원화진단.py         전부 재고 -> out/기록/원화진단_20260920.{json,csv} + out/원화진단_접촉지.png

09-20 하루의 실패 가운데 방법이 아니라 **입력**에서 온 것이 여럿이었다 —
닫힌 궤짝의 창 잘림(가로키 1.58) · 모자의 축 방향 뷰 · avatar_d 의 1 화소 밀림.
그래서 「우리 벤치 입력 가운데 몇 장이 이런 흠을 갖고 있나」를 **정답 메시 없이 · 입력만으로** 잰다.

계획 · 「흠」 기준값(숫자를 보기 전에 적었다): `claudedocs/plan_원화진단_20260920.md`.

**이 바퀴는 측정이지 판정이 아니다.** Q 도 게이트도 없다. 인과도 주장하지 않는다 —
「흠 있는 장이 몇 개이고 그 장들이 어느 결론에 들어가 있었나」까지만 적는다.

다른 에이전트 파일(`마리골드*` · `픽셀3d*` · `도안천장*` · `알베도*`)은 **읽기 · import 만** 한다.
"""
import csv
import json
import os
import sys

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")

import cv2
import numpy as np
from scipy import ndimage

HERE = r"G:\art2real\원화3d"
REPO = os.path.dirname(HERE)
for p in (HERE, os.path.join(HERE, "실험_20260913"), os.path.join(HERE, "실험_20260919"),
          os.path.join(HERE, "실험_20260920")):
    sys.path.insert(0, p)
import win as W                                                  # noqa: E402  창 규약은 여기 하나뿐이다

OUT = os.path.join(HERE, "out")
REC = os.path.join(OUT, "기록")
TAG = "원화진단 v1 · 실물29 + 도형11 + 진짜원화4 · 입력만 (정답메시는 9번에만) (2026-09-20)"
VIEWS = ("front", "back", "side")                                # 그림의 열 순서

# ── 「흠」 기준값 — **숫자를 보기 전에 계획서에 적은 값 그대로** ──────────────
T_잘림 = 0.01          # 접촉몫 (창 테두리 화소 / 마스크 외곽 화소)
T_폭비 = 0.02          # |앞폭/뒤폭 − 1|
T_높이 = 2             # 판 사이 실루엣 높이 차 (화소)
T_기준선 = 5           # 급변점 z 차 중앙 (화소)
T_거울 = 0.95          # IoU(front, fliplr(back))
T_원형 = 0.80          # 축방향 의심 — 그 판의 원형도
T_원형차 = 0.25        # 나머지 두 판의 최소와의 차
T_검정 = 32            # 마스크 안 평균 명도
T_작다 = 0.05          # 채움 (마스크 화소 / 창 화소)
T_여유 = 0.98          # bbox 폭 / 창 폭
T_정답 = 0.98          # 정답 렌더 대 입력 마스크 IoU (09-20 메시변형이 쓴 값)

흠항목 = ("창잘림", "배율", "기준선", "거울", "축뷰", "정답IoU")


# ── 집합 ────────────────────────────────────────────────────────────────────

도형 = ("상자", "원기둥", "원뿔", "구", "두기둥나란히", "상자45도", "두기둥대각", "L자", "치마",
        "토러스세움", "토러스옆")


def 집합():
    """[(키, 표시이름, 무리, {view: png}, truth.glb 또는 None, 창안인가)]"""
    S = []
    b = json.load(open(os.path.join(HERE, "벤치.json"), encoding="utf-8"))
    for c in b["cases"]:
        S.append(_시트(c["name"], c["name"], "실물%s" % c.get("split", "")))
    for n in 도형:
        S.append(_시트("도형_" + n, n, "도형"))
    tr = os.path.join(REPO, "트레일", "trail7_part3d", "in")
    삼 = os.path.join(OUT, "은둔자_자료", "삼면")
    S.append(("원화_은둔자삼면", "은둔자 삼면도", "원화",
              {v: os.path.join(삼, "%s.png" % v) for v in VIEWS}, None, False))
    S.append(("원화_오메가몬", "오메가몬", "원화",
              {v: os.path.join(tr, "omega_%s.png" % v) for v in VIEWS}, None, False))
    S.append(("원화_폴드론", "폴드론", "원화",
              {v: os.path.join(tr, "pauldron_%s.png" % v) for v in VIEWS}, None, False))
    S.append(("원화_은둔자채색", "은둔자 채색(design3)", "원화",
              {"front": os.path.join(OUT, "은둔자_자료", "design3.png")}, None, False))
    return [s for s in S if all(os.path.exists(p) for p in s[3].values())]


def _시트(key, nick, grp):
    d = os.path.join(OUT, "시트", key)
    g = os.path.join(d, "truth.glb")
    return (key, nick, grp, {v: os.path.join(d, "%s.png" % v) for v in VIEWS},
            g if os.path.exists(g) else None, True)


# ── 입력 읽기 ───────────────────────────────────────────────────────────────

def 읽기(png):
    """(RGB 흰바탕합성, 마스크, 알파있나). cv2 는 한글 경로를 못 읽어 `np.fromfile` + `imdecode`."""
    im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_UNCHANGED)
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    if im.shape[2] == 4:
        a = im[:, :, 3]
        rgb = im[:, :, 2::-1].astype(np.float64)
        rgb = (rgb * (a[:, :, None] / 255.0) + 255 * (1 - a[:, :, None] / 255.0)).astype(np.uint8)
        return rgb, a > 127, True
    rgb = im[:, :, 2::-1].copy()
    return rgb, (rgb < 250).any(2), False


def bbox(m):
    ys, xs = np.where(m)
    if len(ys) == 0:
        return None
    return int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())


def 창에앉히기(rgb, m, s, cx, ybot):
    """`win.normalize` 의 2D 판 — **배율은 정면 판에서 한 번** 정하고 세 판이 공유한다.
    각 판은 제 실루엣의 바닥을 z=0 에, 가로 중심을 u=0 에 둔다."""
    py0, px0 = W.topix(np.array([0.0]), np.array([0.0]))
    M = np.array([[s, 0, float(px0[0]) - s * cx], [0, s, float(py0[0]) - s * ybot]], np.float64)
    r = cv2.warpAffine(rgb, M, (W.RES, W.RES), flags=cv2.INTER_AREA, borderValue=(255, 255, 255))
    g = cv2.warpAffine(m.astype(np.uint8) * 255, M, (W.RES, W.RES), flags=cv2.INTER_NEAREST)
    return r, g > 127


def 판들(case):
    """{view: (rgb 1024², mask 1024², raw bbox, 원본크기)} — 시트는 그대로, 원화는 창에 앉힌다."""
    key, nick, grp, paths, glb, inwin = case
    raw = {}
    for v, p in paths.items():
        rgb, m, has_a = 읽기(p)
        raw[v] = (rgb, m, bbox(m), has_a)
    out = {}
    if inwin:
        for v, (rgb, m, bb, ha) in raw.items():
            out[v] = dict(rgb=rgb, mask=m, bb=bb, 알파=ha, 원본=rgb.shape[:2])
    else:
        bbf = raw["front"][2]
        hf = bbf[1] - bbf[0] + 1
        s = (W.RES / (W.U1 - W.U0)) / hf                      # 정면 키가 창 1.0 이 되는 배율
        for v, (rgb, m, bb, ha) in raw.items():
            r2, m2 = 창에앉히기(rgb, m, s, (bb[2] + bb[3]) / 2.0, bb[1])
            out[v] = dict(rgb=r2, mask=m2, bb=bb, 알파=ha, 원본=rgb.shape[:2], 배율=s)
    return out


# ── 항목 1 창 잘림 ──────────────────────────────────────────────────────────

def 외곽(m):
    return m & ~cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)


def 접촉(m):
    n = max(int(외곽(m).sum()), 1)
    return {"좌": float(m[:, 0].sum()) / n, "우": float(m[:, -1].sum()) / n,
            "위": float(m[0, :].sum()) / n, "아래": float(m[-1, :].sum()) / n}


# ── 항목 2 · 3 배율 · 기준선 ────────────────────────────────────────────────

def 프로파일(m):
    """행마다 실루엣 좌우 끝의 벌어짐 (화소). 빈 행은 0."""
    idx = np.arange(m.shape[1])
    w = np.zeros(m.shape[0])
    any_ = m.any(1)
    if any_.any():
        first = np.where(m[any_], True, False).argmax(1)
        last = m.shape[1] - 1 - m[any_][:, ::-1].argmax(1)
        w[any_] = last - first + 1
        _ = idx
    return w


def 급변점(w, k=5, sep=20):
    """|dw/dz| 의 봉우리 위 k 개의 행 번호 — 머리 · 어깨 · 허리에 해당하는 자리."""
    d = np.abs(np.gradient(ndimage.gaussian_filter1d(w, 4.0)))
    got = []
    order = np.argsort(-d)
    for i in order:
        if d[i] <= 0:
            break
        if all(abs(int(i) - g) >= sep for g in got):
            got.append(int(i))
        if len(got) >= k:
            break
    return sorted(got)


def 짝차(a, b):
    """봉우리 두 벌을 가장 가까운 것끼리 짝지어 z 차 중앙 (화소)."""
    if not a or not b:
        return None
    return float(np.median([min(abs(x - y) for y in b) for x in a]))


# ── 항목 5 축 방향 뷰 ───────────────────────────────────────────────────────

def 원형도(m):
    c, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not c:
        return 0.0
    k = max(c, key=cv2.contourArea)
    p = cv2.arcLength(k, True)
    return float(4 * np.pi * cv2.contourArea(k) / max(p * p, 1e-9))


# ── 항목 6 음영 단수 · 광원 ─────────────────────────────────────────────────

def 음영단수(rgb, m):
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)[m]
    if g.size == 0:
        return 0, []
    h = ndimage.gaussian_filter1d(np.histogram(g, 64, (0, 256))[0].astype(float), 1.5)
    thr = 0.02 * g.size
    pk = [i for i in range(1, 63) if h[i] >= thr and h[i] >= h[i - 1] and h[i] > h[i + 1]]
    if h[0] >= thr and h[0] > h[1]:
        pk.insert(0, 0)
    if h[63] >= thr and h[63] > h[62]:
        pk.append(63)
    return len(pk), [int(round(i * 4)) for i in pk]


def 광원(rgb, m):
    """09-19 `알베도광원.estimate_light` 를 그대로 — 512² 로 줄여서 (BAND 가 512² 기준이다).
    `reg` 는 09-19 `알베도면.albedo_regions(q=8)`. 관측이 알베도×음영이 섞인 최종 그림이라
    **근사**다 (09-19 는 알베도 컷을 따로 받았다)."""
    try:
        import 알베도광원 as L2
        import 알베도면 as A1
    except Exception as e:
        return None, str(e)
    r = cv2.resize(rgb, (512, 512), interpolation=cv2.INTER_AREA)
    mm = cv2.resize(m.astype(np.uint8), (512, 512), interpolation=cv2.INTER_NEAREST) > 0
    if mm.sum() < 500:
        return None, "마스크가 작다"
    reg = A1.albedo_regions(r, mm, 8, A1.AMIN)
    obs = cv2.cvtColor(r, cv2.COLOR_RGB2GRAY).astype(np.float64)
    l, s = L2.estimate_light(obs, reg, mm)
    return [round(float(x), 3) for x in l], round(float(s), 3)


# ── 항목 9 정답 렌더 대 입력 ────────────────────────────────────────────────

def 정답IoU(glb, P):
    import trimesh
    t = trimesh.load(glb, force="mesh")
    V, F = np.asarray(t.vertices, np.float64), np.asarray(t.faces)
    return {v: round(W.iou(W.silhouette(V, F, v), P[v]["mask"]), 4) for v in P}


# ── 한 장 ───────────────────────────────────────────────────────────────────

def 한장(case):
    key, nick, grp, paths, glb, inwin = case
    P = 판들(case)
    r = {"장": key, "이름": nick, "무리": grp, "판수": len(P), "창안": inwin}
    vs = [v for v in VIEWS if v in P]

    # 1 창 잘림
    tc = {v: {k: round(x, 4) for k, x in 접촉(P[v]["mask"]).items()} for v in vs}
    r["접촉몫"] = tc
    r["잘린변"] = sorted({"%s:%s" % (v, k) for v in vs for k, x in tc[v].items() if x > T_잘림})
    r["창잘림"] = bool(r["잘린변"])

    # 2 배율 · 높이
    ext = {}
    for v in vs:
        bb = bbox(P[v]["mask"])
        ext[v] = dict(h=bb[1] - bb[0] + 1, w=bb[3] - bb[2] + 1, top=bb[0], bot=bb[1]) if bb else None
    r["실루엣"] = ext
    hs = [ext[v]["h"] for v in vs if ext[v]]
    r["높이차"] = int(max(hs) - min(hs)) if len(hs) > 1 else None
    if "front" in ext and "back" in ext and ext["front"] and ext["back"]:
        r["앞뒤폭비"] = round(ext["front"]["w"] / max(ext["back"]["w"], 1), 4)
    else:
        r["앞뒤폭비"] = None
    r["배율"] = bool((r["높이차"] is not None and r["높이차"] > T_높이) or
                     (r["앞뒤폭비"] is not None and abs(r["앞뒤폭비"] - 1) > T_폭비))

    # 3 기준선
    prof = {v: 프로파일(P[v]["mask"]) for v in vs}
    peak = {v: 급변점(prof[v]) for v in vs}
    r["급변점"] = peak
    r["기준선차"] = 짝차(peak.get("front"), peak.get("back")) if len(vs) > 1 else None
    d2 = 짝차(peak.get("front"), peak.get("side")) if "side" in peak else None
    r["기준선차_옆"] = d2
    # 계획의 「시작 · 끝 z 차 > 2 화소」 — 실루엣 위 · 아래 끝이 세 판에서 같은 z 인가
    tops = [ext[v]["top"] for v in vs if ext[v]]
    bots = [ext[v]["bot"] for v in vs if ext[v]]
    r["시작끝차"] = [int(max(tops) - min(tops)), int(max(bots) - min(bots))] if len(tops) > 1 else None
    r["기준선_앞뒤"] = bool(r["기준선차"] is not None and r["기준선차"] > T_기준선)
    r["기준선_앞옆"] = bool(d2 is not None and d2 > T_기준선)
    r["기준선_시작끝"] = bool(r["시작끝차"] is not None and max(r["시작끝차"]) > T_높이)
    r["기준선"] = bool(r["기준선_앞뒤"] or r["기준선_앞옆"] or r["기준선_시작끝"])

    # 4 앞뒤 거울
    if "front" in P and "back" in P:
        r["거울IoU"] = round(W.iou(P["front"]["mask"], P["back"]["mask"][:, ::-1]), 4)
        r["앞옆IoU"] = round(W.iou(P["front"]["mask"], P["side"]["mask"]), 4) if "side" in P else None
    else:
        r["거울IoU"] = r["앞옆IoU"] = None
    r["거울"] = bool(r["거울IoU"] is not None and r["거울IoU"] < T_거울)

    # 5 축 방향 뷰
    circ = {v: round(원형도(P[v]["mask"]), 4) for v in vs}
    r["원형도"] = circ
    axv = []
    if len(vs) == 3:
        for v in vs:
            o = min(circ[k] for k in vs if k != v)
            if circ[v] > T_원형 and circ[v] - o > T_원형차:
                axv.append(v)
    r["축방향판"] = axv
    r["축뷰"] = bool(axv)

    # 6 음영 단수 · 광원
    n, lv = 음영단수(P["front"]["rgb"], P["front"]["mask"])
    r["음영단수"] = n
    r["음영봉우리"] = lv
    l, s = 광원(P["front"]["rgb"], P["front"]["mask"])
    r["광원l"], r["광원s"] = l, s

    # 7 알파 · 배경 · 어두움
    r["알파"] = bool(P["front"]["알파"])
    g = cv2.cvtColor(P["front"]["rgb"], cv2.COLOR_RGB2GRAY)[P["front"]["mask"]]
    r["평균명도"] = round(float(g.mean()), 1) if g.size else None
    r["검은장"] = bool(r["평균명도"] is not None and r["평균명도"] < T_검정)

    # 8 해상도 · 여유
    r["채움"] = round(float(P["front"]["mask"].mean()), 4)
    r["원본크기"] = list(P["front"]["원본"])
    r["bbox폭몫"] = round(ext["front"]["w"] / W.RES, 4) if ext.get("front") else None
    r["작다"] = bool(r["채움"] < T_작다)
    r["여유없음"] = bool(r["bbox폭몫"] is not None and r["bbox폭몫"] > T_여유)

    # 9 정답 렌더 대 입력
    if glb:
        try:
            gi = 정답IoU(glb, P)
            r["정답렌더IoU"] = gi
            r["정답IoU"] = bool(min(gi.values()) < T_정답)
        except Exception as e:
            r["정답렌더IoU"], r["정답IoU"] = {"오류": str(e)}, False
    else:
        r["정답렌더IoU"], r["정답IoU"] = None, False

    r["흠"] = sorted(k for k in 흠항목 if r.get(k))
    r["흠수"] = len(r["흠"])
    # **사후 집합** — 돌린 뒤에 만든 것이다. 3 번의 「앞↔옆 급변점」이 40 장 시트 전부에서 앞↔뒤 0.0 인데도
    # 26/29 를 켰다 (앞과 옆은 애초에 다른 모양이라 폭 급변점이 다른 z 에 있다 = 자가 틀렸다).
    # 계획대로의 집합을 headline 으로 남기고, 이 집합은 **사후**라고 적고 같이 싣는다.
    r["흠2"] = sorted(k for k in 흠항목 if r.get(k) and not (k == "기준선" and not (r["기준선_앞뒤"] or r["기준선_시작끝"])))
    r["흠2수"] = len(r["흠2"])
    return r, P


# ── 그림 ────────────────────────────────────────────────────────────────────

S = 240


def 타일(P, v, r, S=S):
    if v not in P:
        t = np.full((S, S, 3), 245, np.uint8)
        cv2.putText(t, "no panel", (S // 4, S // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (140, 140, 140), 1)
        return t
    t = cv2.resize(P[v]["rgb"], (S, S), interpolation=cv2.INTER_AREA).copy()
    m = cv2.resize(P[v]["mask"].astype(np.uint8), (S, S), interpolation=cv2.INTER_NEAREST) > 0
    # 창 경계 (파랑 점선 틀)
    cv2.rectangle(t, (0, 0), (S - 1, S - 1), (60, 110, 230), 1)
    # 기준선 (초록 = 앞뒤가 맞는 자리 · 주황 = 앞판에만 있는 자리)
    for z in r["급변점"].get(v, []):
        y = int(z * S / W.RES)
        cv2.line(t, (0, y), (S - 1, y), (40, 170, 90), 1)
    # z = 0 · z = 1 (창 규약의 접지 · 키)
    for zz, col in ((0.0, (150, 150, 150)), (1.0, (150, 150, 150))):
        y = int(W.topix(np.array([0.0]), np.array([zz]))[0][0] * S / W.RES)
        cv2.line(t, (0, y), (S - 1, y), col, 1)
    # **잘린 자리 — 빨강**
    tc = r["접촉몫"][v]
    for k, seg in (("좌", m[:, 0]), ("우", m[:, -1]), ("위", m[0, :]), ("아래", m[-1, :])):
        if tc[k] <= T_잘림:
            continue
        ii = np.where(seg)[0]
        if not len(ii):
            continue
        a, b = int(ii.min()), int(ii.max())
        if k == "좌":
            cv2.line(t, (1, a), (1, b), (230, 30, 30), 4)
        elif k == "우":
            cv2.line(t, (S - 2, a), (S - 2, b), (230, 30, 30), 4)
        elif k == "위":
            cv2.line(t, (a, 1), (b, 1), (230, 30, 30), 4)
        else:
            cv2.line(t, (a, S - 2), (b, S - 2), (230, 30, 30), 4)
    return t


def 거울타일(P, S=S):
    if "front" not in P or "back" not in P:
        return np.full((S, S, 3), 245, np.uint8)
    f = cv2.resize(P["front"]["mask"].astype(np.uint8), (S, S), interpolation=cv2.INTER_NEAREST) > 0
    b = cv2.resize(P["back"]["mask"][:, ::-1].astype(np.uint8), (S, S), interpolation=cv2.INTER_NEAREST) > 0
    t = np.full((S, S, 3), 255, np.uint8)
    t[f & ~b] = (225, 60, 60)          # 앞에만
    t[b & ~f] = (60, 110, 225)         # 뒤(거울)에만
    t[f & b] = (200, 200, 200)         # 둘 다
    return t


def 요약타일(r, S=S):
    from PIL import Image, ImageDraw
    sys.path.insert(0, HERE)
    from 계획 import _font
    im = Image.new("RGB", (S, S), (255, 255, 255) if not r["흠"] else (255, 246, 243))
    d = ImageDraw.Draw(im)
    ok = lambda b: "X" if b else "O"
    tc = r["접촉몫"]
    worst = max((x for v in tc for x in tc[v].values()), default=0.0)
    cut = lambda s: (s[:19] + "…") if len(s) > 20 else s
    lines = [
        "창잘림 %s %s" % (ok(r["창잘림"]), cut(",".join(x.replace("front", "앞").replace("back", "뒤")
                                                     .replace("side", "옆") for x in r["잘린변"])) or "%.3f" % worst),
        "배율   %s h차%s w비%s" % (ok(r["배율"]), r["높이차"], r["앞뒤폭비"]),
        "기준선 %s 앞뒤%s 옆%s" % (ok(r["기준선"]), r["기준선차"], r["기준선차_옆"]),
        "  끝z차 %s" % (r["시작끝차"],),
        "거울   %s %s (앞옆 %s)" % (ok(r["거울"]), r["거울IoU"], r["앞옆IoU"]),
        "축뷰   %s %s" % (ok(r["축뷰"]), ",".join(r["축방향판"]) or "-"),
        "정답   %s %s" % (ok(r["정답IoU"]),
                          ("%.4f" % min(r["정답렌더IoU"].values())) if isinstance(r["정답렌더IoU"], dict)
                          and all(isinstance(x, float) for x in r["정답렌더IoU"].values()) else "-"),
        "음영 %d단 · 명도 %s%s" % (r["음영단수"], r["평균명도"], " ·검정" if r["검은장"] else ""),
        "채움 %.1f%%%s · 알파 %s" % (100 * r["채움"], " ·작다" if r["작다"] else "", "O" if r["알파"] else "X"),
        "광원 %s" % (r["광원l"],),
    ]
    for i, s in enumerate(lines):
        d.text((6, 4 + i * 23), s, fill=(200, 30, 30) if " X " in s[:12] else (30, 30, 30), font=_font(14))
    return np.asarray(im)


def 그림(rows, P_of):
    sys.path.insert(0, os.path.join(HERE, "실험_20260913"))
    from 깊이색 import grid
    R = []
    for r in rows:
        P = P_of[r["장"]]
        nm = r["이름"]
        nm = nm if len(nm) <= 16 else nm[:15] + "…"
        R.append(("%s%s" % (nm, ("\n흠 " + ",".join(r["흠"])[:14]) if r["흠"] else ""),
                  [타일(P, "front", r), 타일(P, "back", r), 타일(P, "side", r), 거울타일(P), 요약타일(r)]))
    grid(R, ["앞 (front)", "뒤 (back)", "옆 (side)", "앞 ∩ 뒤거울", "진단 요약"],
         "원화 진단 — 우리 벤치 입력에 어떤 흠이 있나 (측정이지 판정이 아니다) · 실물 29 + 도형 11 + 진짜 원화 4 (2026-09-20)",
         "빨강 = 창 경계에 닿은(잘린) 자리 · 초록 가로선 = 실루엣 폭 급변점 · 회색 = z 0 · 1 · 파랑 틀 = 창 경계 · "
         "겹침 칸 빨강 = 앞에만 · 파랑 = 뒤거울에만 · 회색 = 둘 다. 기준값은 숫자를 보기 전에 계획서에 적었다. **흠 있는 장이 위**",
         os.path.join(OUT, "원화진단_접촉지.png"), S=S)


# ── 오염 대조 (인과 주장 없음 · 두 무리의 중앙과 분모만) ────────────────────

def 오염(rows, 흠키="흠", 이름="계획대로"):
    bad = {r["장"] for r in rows if r[흠키]}
    out = {"정의": 이름, "흠있는장": sorted(bad), "흠없는장": sorted(r["장"] for r in rows if not r[흠키]),
           "주의": "인과가 아니다. 흠과 난이도가 같이 움직인다 (넓은 물건이 잘리기도 하고 hull 이 어렵기도 하다). "
                   "이 바퀴에는 그 둘을 가르는 대조군이 없다."}

    def split(d, key):
        a = [v for k, v in d.items() if k in bad]
        b = [v for k, v in d.items() if k not in bad]
        return {"흠": {"장": len(a), "중앙": round(float(np.median(a)), 4) if a else None},
                "성한": {"장": len(b), "중앙": round(float(np.median(b)), 4) if b else None},
                key: True}

    # 점수판 (28장 · 격자 128 · 속 채운 정답)
    p = os.path.join(REC, "점수판_진행.jsonl")
    if os.path.exists(p):
        new, old = {}, {}
        for ln in open(p, encoding="utf-8"):
            j = json.loads(ln)
            new[j["case"]] = j["새"][1]
            old[j["case"]] = j["옛"][1]
        out["점수판 · 새 기본 IoU128"] = split(new, "속채운정답")
        out["점수판 · 새−옛"] = split({k: new[k] - old[k] for k in new}, "속채운정답")

    # 대각 (28장)
    p = os.path.join(REC, "대각_20260919_1510.json")
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))["장별"]
        out["대각 · V 현행 iou128"] = split({k: v["V 현행"]["iou128"] for k, v in d.items()
                                             if isinstance(v, dict) and "V 현행" in v}, "격자128")
        out["대각 · V 현행 못덮음"] = split({k: v["V 현행"]["못덮음"] for k, v in d.items()
                                             if isinstance(v, dict) and "V 현행" in v}, "격자128")

    # 결론마다 「분모에 흠 있는 장이 몇인가」
    분모 = {
        "메시변형 (09-20 새벽 · n=3 + 뺀 1)":
            ["mech_Drill_8uBbH7Dvmb", "cloak_Chest_Closed_AngpV0HxD8", "cape_Hat_Stylised_lNN3PlrjSa",
             "avatarsample_d"],
        "픽셀3d (09-20 오후 · n=4)":
            ["mech_Drill_8uBbH7Dvmb", "cloak_Chest_Closed_AngpV0HxD8", "cape_Hat_Stylised_lNN3PlrjSa",
             "avatarsample_d"],
        "도안천장 (09-20 저녁 · n=2)":
            ["cloak_Chest_Closed_AngpV0HxD8", "mech_Drill_8uBbH7Dvmb"],
        "깊이원 (09-19 · n=8)":
            ["avatarsample_g", "base_male", "sendagaya_shino", "hairsample_female",
             "cloak_Cloche_Qz9XMYysBQ", "cloak_Chest_Closed_AngpV0HxD8", "mech_Drill_8uBbH7Dvmb", "소체"],
        "대각 (09-19 · n=28)": [r["장"] for r in rows if r["무리"].startswith("실물")],
        "점수판 (09-15 · n=28 · 기본값을 바꾼 판정)":
            [r["장"] for r in rows if r["무리"].startswith("실물")],
        "마리골드법선 · 민감도 실물 4 (09-20)":
            ["mech_Drill_8uBbH7Dvmb", "cloak_Chest_Closed_AngpV0HxD8", "cape_Hat_Stylised_lNN3PlrjSa",
             "avatarsample_d"],
        "코드기하 도형 문 (09-20 · n=11)": [r["장"] for r in rows if r["무리"] == "도형"],
    }
    byname = {r["장"]: r for r in rows}
    out["결론마다 분모 안 흠"] = {
        k: {"분모": len(v), "흠": sorted(x for x in v if x in bad),
            "흠수": sum(1 for x in v if x in bad),
            "흠항목": {x: byname[x]["흠"] for x in v if x in bad}}
        for k, v in 분모.items()}
    return out


# ── 자가검사 ────────────────────────────────────────────────────────────────

def 검사():
    R = W.RES
    m = np.zeros((R, R), bool)
    m[200:800, 312:712] = True                                # 창 가로 중앙에 놓는다 (312+711 = 1023)
    t = 접촉(m)
    assert max(t.values()) == 0, "창 안에 든 상자가 경계에 닿는다 %s" % t

    c = np.zeros((R, R), bool)
    c[200:800, :] = True                                      # 좌우로 잘린 상자
    t = 접촉(c)
    assert t["좌"] > T_잘림 and t["우"] > T_잘림 and t["위"] == 0, "좌우 잘림을 못 잡는다 %s" % t

    assert W.iou(m, m[:, ::-1]) > 0.99, "좌우대칭 상자의 거울 IoU 가 1 이 아니다"
    a = np.zeros((R, R), bool)
    a[200:800, 312:712] = True
    a[200:800, 712:772] = True                                # 오른쪽에 혹
    assert W.iou(a, a[:, ::-1]) < T_거울, "비대칭인데 거울 IoU 가 문턱을 넘는다 %.3f" % W.iou(a, a[:, ::-1])

    disc = np.zeros((R, R), np.uint8)
    cv2.circle(disc, (R // 2, R // 2), 300, 1, -1)
    bar = np.zeros((R, R), bool)
    bar[200:800, 480:544] = True
    assert 원형도(disc > 0) > T_원형 > 원형도(bar), "원형도가 원과 막대를 못 가른다 %.3f %.3f" % (원형도(disc > 0), 원형도(bar))

    w = 프로파일(m)
    assert w[500] == 400 and w[100] == 0, "폭 프로파일이 틀렸다 %s" % w[500]
    st = np.zeros((R, R), bool)                               # 어깨가 있는 모양 — 급변점이 그 자리에
    st[200:500, 400:600] = True
    st[500:800, 300:700] = True
    pk = 급변점(프로파일(st))
    assert any(abs(p - 500) < 15 for p in pk), "급변점이 어깨(500) 를 못 찾는다 %s" % pk
    assert 짝차(pk, pk) == 0.0, "같은 봉우리 벌의 짝차가 0 이 아니다"

    n, _ = 음영단수(np.full((R, R, 3), 200, np.uint8), m)
    assert n == 1, "평면 칠인데 음영 봉우리가 %d 단" % n
    two = np.full((R, R, 3), 200, np.uint8)
    two[:, :R // 2] = 90
    assert 음영단수(two, m)[0] == 2, "2 단인데 %d" % 음영단수(two, m)[0]

    # 창에앉히기 — 배율 · 바닥 · 중심 규약
    src = np.zeros((400, 200), bool)
    src[50:350, 60:140] = True
    rgb = np.where(src[:, :, None], 0, 255).astype(np.uint8).repeat(3, 2)
    s = (W.RES / (W.U1 - W.U0)) / 300.0
    _, m2 = 창에앉히기(rgb, src, s, 99.5, 349)
    bb = bbox(m2)
    z0 = int(W.topix(np.array([0.0]), np.array([0.0]))[0][0])
    z1 = int(W.topix(np.array([0.0]), np.array([1.0]))[0][0])
    assert abs(bb[1] - z0) <= 2 and abs(bb[0] - z1) <= 3, "창 앉히기가 바닥 z=0 · 키 z=1 을 안 맞춘다 %s (%d %d)" % (bb, z0, z1)
    assert abs((bb[2] + bb[3]) / 2 - W.RES / 2) <= 2, "창 앉히기가 가로 중심을 안 맞춘다 %s" % (bb,)

    print("자가검사 통과 — 항목 1·2·3·4·5·6 과 창 앉히기")


# ── 주 ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "검사":
        return 검사()
    S_ = 집합()
    print("장 %d" % len(S_), flush=True)
    rows, P_of = [], {}
    for c in S_:
        r, P = 한장(c)
        rows.append(r)
        P_of[r["장"]] = P
        print("  %-42s 흠 %s" % (r["이름"][:42], ",".join(r["흠"]) or "-"), flush=True)

    rows.sort(key=lambda r: (-r["흠수"], r["무리"], r["장"]))       # **흠 있는 장을 위로**
    os.makedirs(REC, exist_ok=True)
    doc = {"판": TAG, "기준값": {"창잘림_접촉몫": T_잘림, "앞뒤폭비": T_폭비, "높이차화소": T_높이,
                                 "기준선차화소": T_기준선, "거울IoU": T_거울, "원형도": T_원형,
                                 "원형도차": T_원형차, "검은장명도": T_검정, "작다채움": T_작다,
                                 "여유없음bbox폭몫": T_여유, "정답렌더IoU": T_정답},
           "기준값을 언제 적었나": "숫자를 보기 전 · claudedocs/plan_원화진단_20260920.md",
           "장수": len(rows),
           "흠 장수": {k: sum(1 for r in rows if r.get(k)) for k in 흠항목},
           "무리별 흠": {g: {"장": sum(1 for r in rows if r["무리"] == g),
                            "흠": sum(1 for r in rows if r["무리"] == g and r["흠"])}
                        for g in sorted({r["무리"] for r in rows})},
           "흠2 장수 (사후 · 앞옆 급변점 뺀 것)": {k: sum(1 for r in rows if k in r["흠2"]) for k in 흠항목},
           "오염대조": 오염(rows, "흠", "계획대로 (6 항목 · 기준값은 숫자 보기 전에 적었다)"),
           "오염대조_사후": 오염(rows, "흠2", "사후 · 3 번의 앞↔옆 급변점을 뺀 집합 (그 자가 틀렸다 — 아래 「자가 틀린 곳」)"),
           "자가 틀린 곳": "3 번 기준선의 **앞↔옆 급변점 짝차**는 흠을 재는 자가 아니다. 시트 40 장에서 앞↔뒤 짝차가 "
                          "전부 0.0 화소(같은 메시의 거울상이니 당연하다)인데 앞↔옆은 26/29 에서 5 화소를 넘는다 — "
                          "앞과 옆은 애초에 다른 모양이라 폭 급변점이 다른 z 에 있다. 기준값은 안 고쳤고, 대신 "
                          "앞↔뒤 · 시작끝 z 만 쓰는 사후 집합을 같이 싣는다.",
           "장별": rows}
    jp = os.path.join(REC, "원화진단_20260920.json")
    json.dump(doc, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    cols = ["장", "이름", "무리", "판수", "흠수", "흠", "흠2", "창잘림", "잘린변", "배율", "높이차", "앞뒤폭비",
            "기준선", "기준선_앞뒤", "기준선_앞옆", "기준선_시작끝", "기준선차", "기준선차_옆", "시작끝차",
            "거울", "거울IoU", "앞옆IoU", "축뷰", "축방향판",
            "정답IoU", "음영단수", "평균명도", "검은장", "알파", "채움", "bbox폭몫", "작다", "여유없음", "광원l"]
    cp = os.path.join(REC, "원화진단_20260920.csv")
    with open(cp, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(cols + ["정답렌더IoU최소", "원형도front", "원형도side"])
        for r in rows:
            gi = r["정답렌더IoU"]
            gmin = min(gi.values()) if isinstance(gi, dict) and all(isinstance(x, float) for x in gi.values()) else ""
            w.writerow([",".join(map(str, r[c])) if isinstance(r.get(c), list) else r.get(c) for c in cols]
                       + [gmin, r["원형도"].get("front"), r["원형도"].get("side")])
    print("  -> %s\n  -> %s" % (os.path.relpath(jp, HERE), os.path.relpath(cp, HERE)))
    그림(rows, P_of)


if __name__ == "__main__":
    main()
