# -*- coding: utf-8 -*-
"""**알파 없는 원화에서 배경을 뺀다** — 정답을 만들어 놓고 잰다 (2026-09-21).

    python 배경.py 검사
    python 배경.py 재기     알파 있는 판 9 개 × 배경 3 종 × 방법 넷 -> out/기록/배경_진행.json
    python 배경.py 판정     -> out/기록/배경_<때>.json
    python 배경.py 그림     -> out/배경_시험.png · out/배경_채색.png

09-21 `선문턱` 이 남은 일을 하나로 좁혔다 — **알파 없는 원화의 배경 빼기**. 지금 쓰는
모서리 홍수채우기는 은둔자 채색에서 **그림을 통째로 먹었다**(판 수 113 → 0).

**정답 없는 문제를 정답 있는 문제로 바꾼다** — 알파가 **있는** 판 9 개(은둔자 삼면도 · 오메가몬 ·
폴드론)를 세 가지 배경 위에 합성해 알파를 지운 뒤, 되찾은 마스크를 **원래 알파와 견준다.**

방법 넷: **모서리홍수**(현행) · **테두리팔레트**(테두리 색 모음에서 가까우면 배경) ·
**grabCut**(테두리 4% 안쪽 사각형으로 초기화) · **팔레트+grabCut**(팔레트 결과를 씨앗으로).

**문턱을 돌리기 전에 적는다.**

    Q1  최선 방법의 **마스크 IoU 중앙 >= 0.90**
    Q2  현행 **모서리홍수를 이긴다** — 27 판 중 승 과반
    Q3  되찾은 마스크로 추출했을 때 **재구성 오차가 참 알파 대비 +1.0 이내** (표본 3 판)

rembg 는 안 쓴다 — 설치돼 있지 않고 모델을 새로 받아야 한다. 있는 것(cv2)으로 먼저 간다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260920")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260919")
import 선읽기 as LR
import 전처리 as PP
HERE, OUT, 도구 = LR.HERE, LR.OUT, LR.도구
DST = os.path.join(HERE, "out", "배경")
PROG = os.path.join(OUT, "배경_진행.json")
S = LR.S
방법들 = ("모서리홍수", "테두리팔레트", "grabCut", "팔레트+grabCut")
배경들 = ("균일회색", "세로그라데이션", "잡음질감")
Q1문턱, Q3상승 = 0.90, 1.0
Q3표본 = 3


# ── 시험용 배경 ──────────────────────────────────────────────────────────────

def 배경그림(종류, h, w, seed=0):
    rng = np.random.default_rng(seed)
    if 종류 == "균일회색":
        return np.full((h, w, 3), 128, np.uint8)
    if 종류 == "세로그라데이션":
        g = np.linspace(60, 200, h, dtype=np.float32)[:, None]
        return np.repeat(np.repeat(g, w, 1)[:, :, None], 3, 2).astype(np.uint8)
    import cv2
    n = rng.integers(40, 210, (h // 8 + 1, w // 8 + 1, 3)).astype(np.uint8)
    n = cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
    return cv2.GaussianBlur(n, (0, 0), 6).astype(np.uint8)


def 합성(rgb, a, 배경):
    al = (a.astype(np.float32) / 255.0)[:, :, None]
    return (rgb.astype(np.float32) * al + 배경.astype(np.float32) * (1 - al)).astype(np.uint8)


# ── 방법 넷 ──────────────────────────────────────────────────────────────────

def _테두리색(rgb, k=12):
    b = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]).astype(np.float32)
    import cv2
    _, _, c = cv2.kmeans(b, min(k, len(np.unique(b, axis=0))), None,
                         (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0),
                         3, cv2.KMEANS_PP_CENTERS)
    return c


def 테두리팔레트(rgb, tol=30):
    """테두리 색 무리에서 tol 안이면 배경 후보 · 그중 **테두리와 이어진 것**만 배경."""
    import cv2
    from scipy import ndimage
    c = _테두리색(rgb)
    d = np.linalg.norm(rgb.astype(np.float32)[:, :, None, :] - c[None, None, :, :], axis=3).min(2)
    후 = d <= tol
    lab, n = ndimage.label(후)
    테 = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    배 = np.isin(lab, list(테))
    return ~배


grabcut = PP.grabcut          # **구현은 `전처리.py` 한 곳에만 둔다** (이 바퀴가 고르고 거기로 옮겼다)


def 마스크(rgb, 방법):
    if 방법 == "모서리홍수":
        return PP.모서리홍수(rgb)
    if 방법 == "테두리팔레트":
        return 테두리팔레트(rgb)
    if 방법 == "grabCut":
        return grabcut(rgb)
    return grabcut(rgb, 씨=테두리팔레트(rgb))


def iou(a, b):
    u = (a | b).sum()
    return round(float((a & b).sum() / u), 4) if u else None


# ── 재기 ─────────────────────────────────────────────────────────────────────

def 판들():
    """알파가 있는 원화 판 — (이름, rgb, 참알파)."""
    import cv2
    import 원화진단 as JD
    out = []
    for key, nick, grp, pngs, _, _ in JD.집합():
        if grp != "원화":
            continue
        for v, src in pngs.items():
            im = cv2.imdecode(np.fromfile(src, np.uint8), cv2.IMREAD_UNCHANGED)
            if im.ndim == 2 or im.shape[2] != 4:
                continue
            rgb = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2RGB)
            a = im[:, :, 3]
            h, w = rgb.shape[:2]
            s = S / max(h, w)
            wh = (int(round(w * s)), int(round(h * s)))
            out.append(("%s/%s" % (nick, v),
                        cv2.resize(rgb, wh, interpolation=cv2.INTER_AREA),
                        cv2.resize(a, wh, interpolation=cv2.INTER_AREA) > 127))
    return out


def 재기():
    from PIL import Image
    rows = {}
    for 이름, rgb, 참 in 판들():
        t0 = time.time()
        for bi, bn in enumerate(배경들):
            comp = 합성(rgb, (참 * 255).astype(np.uint8), 배경그림(bn, *rgb.shape[:2], seed=bi))
            d = os.path.join(DST, 이름.replace("/", "_"), bn)
            os.makedirs(d, exist_ok=True)
            Image.fromarray(comp).save(os.path.join(d, "합성.png"))
            r = {}
            for m in 방법들:
                mk = 마스크(comp, m)
                r[m] = {"IoU": iou(mk, 참), "물건몫": round(float(mk.mean()), 4)}
                out = np.full_like(comp, LR.바탕)
                out[mk] = comp[mk]
                Image.fromarray(out).save(os.path.join(d, "%s.png" % m))
            rows["%s|%s" % (이름, bn)] = r
        print("  %-24s " % 이름[:24] + " · ".join(
            "%s %s" % (m, " ".join("%.2f" % rows["%s|%s" % (이름, b)][m]["IoU"] for b in 배경들))
            for m in 방법들) + "  (%.0f초)" % (time.time() - t0), flush=True)
    json.dump({"판": "배경 v1", "행": rows}, open(PROG, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("  ->", PROG)
    return rows


def verdict():
    rows = json.load(open(PROG, encoding="utf-8"))["행"]
    ks = list(rows)
    med = lambda x: round(float(np.median(x)), 4) if x else None
    점 = {m: [rows[k][m]["IoU"] for k in ks if rows[k][m]["IoU"] is not None] for m in 방법들}
    기 = "모서리홍수"
    이김 = {m: int(sum(1 for k in ks if rows[k][m]["IoU"] > rows[k][기]["IoU"])) for m in 방법들}
    최 = max((m for m in 방법들 if m != 기), key=lambda m: np.median(점[m]))
    v = {"판": "배경 v1 · 알파 있는 9 판 × 배경 3 종 × 방법 4 (2026-09-21)",
         "때": time.strftime("%Y%m%d_%H%M"), "판수": len(ks),
         "IoU 중앙": {m: med(점[m]) for m in 방법들},
         "IoU 최악": {m: round(float(min(점[m])), 4) for m in 방법들},
         "모서리홍수를 이긴 판": 이김, "최선": 최,
         "Q1": {"문턱": "최선의 IoU 중앙 >= %g" % Q1문턱, "값": med(점[최]),
                "통과": bool(np.median(점[최]) >= Q1문턱)},
         "Q2": {"문턱": "현행을 이긴 판이 과반(%d)" % (len(ks) // 2 + 1), "값": 이김[최],
                "통과": bool(이김[최] > len(ks) / 2)},
         "행": rows}
    p = os.path.join(OUT, "배경_%s.json" % v["때"])
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %-14s %8s %8s %10s" % ("방법", "IoU중앙", "IoU최악", "현행을이김"))
    for m in 방법들:
        print("  %-14s %8.4f %8.4f %10d" % (m, v["IoU 중앙"][m], v["IoU 최악"][m], 이김[m]))
    for k in ("Q1", "Q2"):
        print("\n  %s %s" % (k, json.dumps(v[k], ensure_ascii=False)))
    print("\n  최선: %s\n  ->" % 최, p)
    return v


def 채색(방법=None):
    """알파 없는 진짜 장 — 은둔자 채색. 정답이 없으니 그림과 추출 지표로만 본다."""
    from PIL import Image
    import cv2
    import 원화진단 as JD
    if 방법 is None:
        import glob
        방법 = json.load(open(sorted(glob.glob(os.path.join(OUT, "배경_2*.json")))[-1],
                             encoding="utf-8"))["최선"]
    out = {}
    for key, nick, grp, pngs, _, _ in JD.집합():
        if grp != "원화":
            continue
        for v, src in pngs.items():
            im = cv2.imdecode(np.fromfile(src, np.uint8), cv2.IMREAD_UNCHANGED)
            if im.ndim != 2 and im.shape[2] == 4:
                continue                                      # 알파 있는 장은 건너뛴다
            rgb = cv2.cvtColor(im[:, :, :3] if im.ndim == 3 else
                               cv2.cvtColor(im, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            s = S / max(h, w)
            rgb = cv2.resize(rgb, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA)
            d = os.path.join(DST, "채색_%s_%s" % (nick[:6], v))
            os.makedirs(d, exist_ok=True)
            r = {}
            for m in (("모서리홍수", 방법) if 방법 != "모서리홍수" else ("모서리홍수",)):
                mk = 마스크(rgb, m)
                o = np.full_like(rgb, LR.바탕)
                o[mk] = rgb[mk]
                p = os.path.join(d, "%s.png" % m)
                Image.fromarray(o).save(p)
                r[m] = {"물건몫": round(float(mk.mean()), 4),
                        **PP.판지표(PP.돌려(p, os.path.join(d, m + "_추출")))}
                print("  %-22s %-14s 물건몫 %.3f · 판수 %s · 최대판몫 %s · 재구성 %s"
                      % (nick[:22], m, r[m]["물건몫"], r[m].get("판수"), r[m].get("최대판몫"),
                         r[m].get("재구성오차")), flush=True)
            out["%s/%s" % (nick, v)] = r
    p = os.path.join(OUT, "배경_채색.json")
    json.dump({"방법": 방법, "장별": out}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", p)
    return out


def 그림():
    from PIL import Image
    rows = json.load(open(PROG, encoding="utf-8"))["행"]
    R = []
    for k in [x for x in rows if x.endswith("|잡음질감")]:      # 제일 어려운 배경 하나만 (세로가 길어진다)
        이름, bn = k.split("|")
        d = os.path.join(DST, 이름.replace("/", "_"), bn)
        ts = [np.asarray(Image.open(os.path.join(d, "합성.png")).convert("RGB"))]
        for m in 방법들:
            p = os.path.join(d, "%s.png" % m)
            ts.append(np.asarray(Image.open(p).convert("RGB")) if os.path.exists(p)
                      else np.full_like(ts[0], 240))
        R.append(("%s\n%s\nIoU %s" % (이름[:16], bn, " ".join(
            "%.2f" % rows[k][m]["IoU"] for m in 방법들)), ts))
    LR.DC.grid(R, ("알파를 지운 합성",) + 방법들,
               "배경 빼기 — 알파를 지워 정답을 만들어 놓고 잰다",
               "IoU 는 왼쪽부터 모서리홍수 · 테두리팔레트 · grabCut · 팔레트+grabCut 순서다",
               os.path.join(HERE, "out", "배경_시험.png"), S=240)
    # 진짜 알파 없는 장 — 은둔자 채색
    d = [x for x in os.listdir(DST) if x.startswith("채색_")]
    R2 = []
    for x in d:
        ts, cs = [], []
        for m in ("모서리홍수", "grabCut"):
            p = os.path.join(DST, x, "%s.png" % m)
            q = os.path.join(DST, x, m + "_추출", "regions.png")
            for pp in (p, q):
                ts.append(np.asarray(Image.open(pp).convert("RGB")) if os.path.exists(pp)
                          else np.full((S, S, 3), 240, np.uint8))
            cs += ["%s 배경 뺀 판" % m, "%s 추출" % m]
        R2.append((x.replace("채색_", ""), ts))
    if R2:
        LR.DC.grid(R2, tuple(cs),
                   "배경 빼기 — 알파가 없는 진짜 장 (은둔자 채색 · 정답 없음)",
                   "현행 모서리홍수는 판 0 개로 무너지고 grabCut 은 73 판을 낸다 (최대 판 몫 0.18 · 재구성 6.14)",
                   os.path.join(HERE, "out", "배경_채색.png"), S=300)


def selfcheck():
    im = np.full((80, 80, 3), 128, np.uint8)
    im[24:56, 24:56] = 20
    참 = np.zeros((80, 80), bool)
    참[24:56, 24:56] = True
    for m in 방법들:
        mk = 마스크(im, m)
        assert iou(mk, 참) is not None
        print("    %-14s IoU %.3f" % (m, iou(mk, 참)))
    a = (참 * 255).astype(np.uint8)
    c = 합성(im, a, 배경그림("잡음질감", 80, 80))
    assert (c[참] == im[참]).all() and not (c[~참] == 128).all()
    print("  자가검사 통과")


if __name__ == "__main__":
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass
    a = sys.argv[1] if len(sys.argv) > 1 else "검사"
    {"검사": selfcheck, "재기": 재기, "판정": verdict, "채색": 채색, "그림": 그림}[a]()
