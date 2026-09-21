# -*- coding: utf-8 -*-
"""**원화를 「오메가몬 같은 판」으로 만든다** — 배경 빼기 + 화풍 정규화 (2026-09-21).

    python 셀화.py 검사
    python 셀화.py 벤치     회화적으로 뭉갠 판에서 셀화가 오목 재현율을 되살리나 (정답 있음)
    python 셀화.py 원화     진짜 원화 7 판 × 방법 넷 (정답 없음 — 재구성오차 · 평탄몫)
    python 셀화.py 판정     -> out/기록/셀화_<때>.json
    python 셀화.py 그림     -> out/셀화_벤치.png · out/셀화_원화.png

사용자(09-21): 「원화에서 **배경 없고 캐릭터 전용** 어떠한 이미지를 만들어 내서 하는 거지,
**오메가몬 하는 것처럼** 말이야.」

배경은 `배경` 바퀴에서 풀렸다(grabCut · IoU 0.992). 남은 것이 **화풍**이다.
09-21 `도해도` 가 오메가몬이 되는 조건을 숫자로 적어 뒀다 — **평탄몫 0.35~0.43 · 선몫 0.27~0.36 ·
재구성 오차 2.87~3.66(< 5)**. 은둔자 채색은 **평탄몫 0.012** 라 무너진다.
그러니 목표는 분명하다 — **평탄한 칠과 선을 되살려 저 숫자대로 만든다.**

방법 넷: **없음**(대조) · **양방향+양자화** · **평균이동+양자화** · **양방향+양자화+XDoG선**.

**문턱을 돌리기 전에 적는다.**

    배관  회화적으로 뭉갠 판이 오목 재현율을 **0.15 이상 떨어뜨려야** 한다.
          (09-21 전처리에서 대조군이 실제 실패를 흉내 못 내 판정이 헛돌았다 — 그 흠을 여기 박아 둔다)
    Q1  (원화) 은둔자 넷의 **재구성 오차가 5 아래**로 내려간다 — 4 판 중 3 판 이상
    Q2  (원화) 은둔자 넷의 **평탄몫이 0.35 이상** — 4 판 중 3 판 이상
    Q3  (벤치 · 정답) 뭉갠 판에서 **회복몫 >= 0.80**  (R2−R1)/(R0−R1)
    Q4  (원화) **오메가몬을 안 망친다** — 재구성 오차 상승 <= 1.0
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
import 도해도 as DH
HERE, OUT, 도구 = LR.HERE, LR.OUT, LR.도구
DST = os.path.join(HERE, "out", "셀화")
S = LR.S
방법들 = ("없음", "양방향+양자화", "평균이동+양자화", "양방향+양자화+선")
K색 = 12
스킬문턱, 평탄목표 = 5.0, 0.35
배관하락, Q3회복, Q4상승 = 0.15, 0.80, 1.0
벤치장 = PP.벤치장[:3]


# ── 화풍 정규화 ──────────────────────────────────────────────────────────────

def 양자화(rgb, 물, k=K색):
    import cv2
    d = rgb[물].astype(np.float32)
    if len(d) < k:
        return rgb.copy()
    _, lab, c = cv2.kmeans(d, k, None,
                           (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0),
                           3, cv2.KMEANS_PP_CENTERS)
    out = rgb.copy()
    out[물] = c[lab.ravel()].astype(np.uint8)
    return out


def xdog(rgb, 물, s=1.0, k=1.6, p=20.0, eps=0.5, phi=10.0):
    """XDoG — 선만 뽑는다. Winnemöller 2012. 경계가 진한 곳이 검게 남는다."""
    import cv2
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    a = cv2.GaussianBlur(g, (0, 0), s)
    b = cv2.GaussianBlur(g, (0, 0), s * k)
    d = (1 + p) * a - p * b
    e = np.where(d >= eps, 1.0, 1.0 + np.tanh(phi * (d - eps)))
    return (e < 0.5) & 물


def 셀화(rgb, 물, 방법):
    import cv2
    if 방법 == "없음":
        return rgb.copy()
    base = rgb.copy()
    if 방법.startswith("양방향"):
        for _ in range(3):
            base = cv2.bilateralFilter(base, 9, 60, 12)
    else:
        base = cv2.pyrMeanShiftFiltering(base, 12, 24, maxLevel=1)
    out = 양자화(base, 물)
    if 방법.endswith("+선"):
        out[xdog(rgb, 물)] = (25, 25, 25)
    return out


def 회화적(cel, 물, seed=0):
    """셀 판을 **회화적으로 뭉갠다** — 부드러운 명암 기울기 + 흐림. 평탄몫을 무너뜨리는 것이 목표다."""
    import cv2
    rng = np.random.default_rng(seed)
    h, w = cel.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    기울 = (0.55 + 0.45 * (xx / w) + 0.25 * np.sin(3.1 * yy / h))[:, :, None]
    n = rng.normal(0, 1, (h // 6 + 1, w // 6 + 1)).astype(np.float32)
    n = cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)[:, :, None] * 10.0
    out = np.clip(cel.astype(np.float32) * 기울 + n, 0, 255).astype(np.uint8)
    out = cv2.GaussianBlur(out, (0, 0), 3.0)
    res = np.full_like(cel, LR.바탕)
    res[물] = out[물]
    return res


# ── 벤치 (정답 있음) ─────────────────────────────────────────────────────────

def 벤치():
    from PIL import Image
    import trimesh
    out = {}
    for c in 벤치장:
        t0 = time.time()
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        cel, 있 = LR.명암판(truth, 45, 45)
        정 = np.load(os.path.join(HERE, "out", "선채널", c, "위45.npy"))
        d = os.path.join(DST, c)
        os.makedirs(d, exist_ok=True)
        회 = 회화적(cel, 있)
        판 = {"원본": cel, "회화적": 회}
        for m in 방법들[1:]:
            판["회화+" + m] = 셀화(회, 있, m)
        r = {}
        for n, im in 판.items():
            p = os.path.join(d, "%s.png" % n)
            Image.fromarray(im).save(p)
            o = os.path.join(d, n.replace("+", "_"))
            g = PP.돌려(p, o, ) if False else None
            import subprocess
            os.makedirs(o, exist_ok=True)
            subprocess.run([sys.executable, 도구, p, "--out", o, "--scale", str(S)],
                           capture_output=True, timeout=1800)
            lp = os.path.join(o, "labels_grown.npy")
            r[n] = {**DH.잰다(im, 있), **PP.판지표(o),
                    **(LR.채점(LR.경계(np.load(lp)), 정, 있) if os.path.exists(lp) else {})}
        R0 = r["원본"].get("재현_오목크리스")
        R1 = r["회화적"].get("재현_오목크리스")
        r["배관_뭉갠하락"] = round(R0 - R1, 4) if None not in (R0, R1) else None
        r["회복몫"] = {m: (round((r["회화+" + m].get("재현_오목크리스", 0) - R1) / (R0 - R1), 4)
                        if None not in (R0, R1) and R0 - R1 > 1e-6 else None) for m in 방법들[1:]}
        r["초"] = round(time.time() - t0, 1)
        out[c] = r
        print("  %-30s 원본 %.3f · 회화 %.3f (하락 %s) · 회복 %s (%.0f초)"
              % (c[:30], R0 or 0, R1 or 0,
                 "%.3f" % r["배관_뭉갠하락"] if r["배관_뭉갠하락"] is not None else "-",
                 {m: r["회복몫"][m] for m in 방법들[1:]}, r["초"]), flush=True)
    p = os.path.join(OUT, "셀화_벤치.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", p)
    return out


# ── 진짜 원화 (정답 없음) ────────────────────────────────────────────────────

def 원화판들():
    import cv2
    import 원화진단 as JD
    out = []
    for key, nick, grp, pngs, _, _ in JD.집합():
        if grp != "원화" or nick.startswith("폴드론"):
            continue
        for v, src in pngs.items():
            im = cv2.imdecode(np.fromfile(src, np.uint8), cv2.IMREAD_UNCHANGED)
            if im.ndim == 2:
                im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
            a = im[:, :, 3] if im.shape[2] == 4 else None
            rgb = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            s = S / max(h, w)
            wh = (int(round(w * s)), int(round(h * s)))
            rgb = cv2.resize(rgb, wh, interpolation=cv2.INTER_AREA)
            a = cv2.resize(a, wh, interpolation=cv2.INTER_AREA) if a is not None else None
            물 = PP.배경마스크(rgb, a)                      # 알파 or grabCut (09-21 기본값)
            out.append(("%s/%s" % (nick, v), rgb, 물))
    return out


def 원화():
    from PIL import Image
    import subprocess
    out = {}
    for 이름, rgb, 물 in 원화판들():
        t0 = time.time()
        d = os.path.join(DST, "원화_" + 이름.replace("/", "_"))
        os.makedirs(d, exist_ok=True)
        r = {}
        for m in 방법들:
            im = 셀화(rgb, 물, m)
            v = np.full_like(im, LR.바탕)
            v[물] = im[물]
            p = os.path.join(d, "%s.png" % m.replace("+", "_"))
            Image.fromarray(v).save(p)
            o = os.path.join(d, m.replace("+", "_") + "_추출")
            os.makedirs(o, exist_ok=True)
            subprocess.run([sys.executable, 도구, p, "--out", o, "--scale", str(S)],
                           capture_output=True, timeout=1800)
            r[m] = {**DH.잰다(v, 물), **PP.판지표(o)}
        out[이름] = r
        print("  %-24s " % 이름[:24] + " · ".join(
            "%s 평탄 %.2f 재구성 %s" % (m[:9], r[m]["평탄몫"],
                                    "%.2f" % r[m]["재구성오차"] if r[m].get("재구성오차") is not None else "-")
            for m in 방법들) + "  (%.0f초)" % (time.time() - t0), flush=True)
    p = os.path.join(OUT, "셀화_원화.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", p)
    return out


def verdict():
    b = json.load(open(os.path.join(OUT, "셀화_벤치.json"), encoding="utf-8"))
    a = json.load(open(os.path.join(OUT, "셀화_원화.json"), encoding="utf-8"))
    은 = [k for k in a if k.startswith("은둔자")]
    오 = [k for k in a if k.startswith("오메가몬")]
    하 = [b[c]["배관_뭉갠하락"] for c in b if b[c]["배관_뭉갠하락"] is not None]
    med = lambda x: round(float(np.median(x)), 4) if x else None
    v = {"판": "셀화 v1 · 배경 뺀 판을 오메가몬 같은 판으로 (2026-09-21)",
         "때": time.strftime("%Y%m%d_%H%M"),
         "배관": {"문턱": "뭉갠 판이 오목 재현율을 %g 이상 떨어뜨린다" % 배관하락,
                 "장별": {c: b[c]["배관_뭉갠하락"] for c in b}, "중앙": med(하),
                 "통과": bool(하 and min(하) >= 배관하락)}}
    for m in 방법들[1:]:
        e = lambda k: a[k][m].get("재구성오차")
        f = lambda k: a[k][m]["평탄몫"]
        살 = [k for k in 은 if e(k) is not None and e(k) < 스킬문턱]
        평 = [k for k in 은 if f(k) >= 평탄목표]
        회 = [b[c]["회복몫"][m] for c in b if b[c]["회복몫"][m] is not None]
        상 = [round(e(k) - a[k]["없음"]["재구성오차"], 3) for k in 오
              if e(k) is not None and a[k]["없음"].get("재구성오차") is not None]
        v[m] = {"Q1 은둔자 재구성<5": "%d/%d" % (len(살), len(은)), "재구성": {k: e(k) for k in 은},
                "Q2 은둔자 평탄>=%g" % 평탄목표: "%d/%d" % (len(평), len(은)),
                "평탄": {k: f(k) for k in 은},
                "Q3 회복몫 중앙": med(회), "Q4 오메가몬 상승 최대": max(상) if 상 else None,
                "Q1": bool(len(살) >= 3), "Q2": bool(len(평) >= 3),
                "Q3": bool(회 and np.median(회) >= Q3회복),
                "Q4": bool(상 and max(상) <= Q4상승)}
        v[m]["넷 다"] = bool(all(v[m][q] for q in ("Q1", "Q2", "Q3", "Q4")))
    p = os.path.join(OUT, "셀화_%s.json" % v["때"])
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  배관 %s (중앙 %s)" % ("통과" if v["배관"]["통과"] else "짐", v["배관"]["중앙"]))
    print("\n  %-18s %8s %8s %10s %10s %6s" % ("방법", "Q1은둔자", "Q2평탄", "Q3회복중앙", "Q4오메가몬", "넷다"))
    for m in 방법들[1:]:
        x = v[m]
        print("  %-18s %8s %8s %10s %10s %6s"
              % (m, x["Q1 은둔자 재구성<5"], x["Q2 은둔자 평탄>=%g" % 평탄목표],
                 x["Q3 회복몫 중앙"], x["Q4 오메가몬 상승 최대"], "통과" if x["넷 다"] else "짐"))
    print("\n  ->", p)
    return v


def 그림():
    from PIL import Image
    b = json.load(open(os.path.join(OUT, "셀화_벤치.json"), encoding="utf-8"))
    R = []
    for c in b:
        ts, cs = [], []
        for n in ("원본", "회화적") + tuple("회화+" + m for m in 방법들[1:]):
            p = os.path.join(DST, c, "%s.png" % n)
            ts.append(np.asarray(Image.open(p).convert("RGB")) if os.path.exists(p)
                      else np.full((S, S, 3), 240, np.uint8))
            cs.append(n)
        g = lambda n: "%.2f" % b[c][n]["재현_오목크리스"] if b[c][n].get("재현_오목크리스") is not None else "-"
        R.append(("%s\n오목 %s" % (c[:18], " ".join(g(n) for n in ("원본", "회화적") +
                                                   tuple("회화+" + m for m in 방법들[1:]))), ts))
    LR.DC.grid(R, tuple(cs), "셀화 — 회화적으로 뭉갠 판을 되살리나 (벤치 · 정답 있음)",
               "오목 재현율을 장 이름 아래 차례로 적었다 (원본 · 회화적 · 셀화 셋)",
               os.path.join(HERE, "out", "셀화_벤치.png"), S=280)
    a = json.load(open(os.path.join(OUT, "셀화_원화.json"), encoding="utf-8"))
    R2 = []
    for k in a:
        d = os.path.join(DST, "원화_" + k.replace("/", "_"))
        ts = []
        for m in 방법들:
            p = os.path.join(d, "%s.png" % m.replace("+", "_"))
            q = os.path.join(d, m.replace("+", "_") + "_추출", "regions.png")
            for pp in (p, q):
                ts.append(np.asarray(Image.open(pp).convert("RGB")) if os.path.exists(pp)
                          else np.full((S, S, 3), 240, np.uint8))
        R2.append(("%s\n재구성 %s" % (k[:18], " ".join(
            "%.1f" % a[k][m]["재구성오차"] if a[k][m].get("재구성오차") is not None else "-"
            for m in 방법들)), ts))
    cs2 = sum([[m[:12], m[:12] + " 추출"] for m in 방법들], [])
    LR.DC.grid(R2, tuple(cs2), "셀화 — 진짜 원화 (배경은 이미 뺐다 · 정답 없음)",
               "재구성 오차를 장 이름 아래 차례로 적었다. 스킬 문턱은 5/255 다",
               os.path.join(HERE, "out", "셀화_원화.png"), S=230)


def selfcheck():
    import cv2
    rng = np.random.default_rng(0)
    # **이 바퀴가 실제로 하는 일**로 검사한다 — 셀 판을 회화적으로 뭉갠 뒤 셀화가 되돌리나.
    # (앞서 만든 토이 둘은 `평탄문턱 2.0` 과 어긋나 쓸모가 없었다: 완만한 기울기는 이미 평탄으로,
    #  톱니는 양자화 뒤에도 띠가 좁아 평탄이 안 된다)
    물 = np.ones((128, 128), bool)
    cel = np.zeros((128, 128, 3), np.uint8)
    for i, c in enumerate(((40, 40, 40), (110, 110, 110), (175, 175, 175), (235, 235, 235))):
        cel[i * 32:(i + 1) * 32] = c
    기 = DH.잰다(cel, 물)
    회 = 회화적(cel, 물)
    r회 = DH.잰다(회, 물)
    assert r회["평탄몫"] < 기["평탄몫"] - 0.3, "뭉개기가 평탄몫을 안 낮춘다 %s -> %s" % (기, r회)
    r셀 = DH.잰다(셀화(회, 물, "양방향+양자화"), 물)
    assert r셀["평탄몫"] > r회["평탄몫"] + 0.2, "셀화가 평탄몫을 안 올린다 %s -> %s" % (r회, r셀)
    assert r셀["색수(8단위)"] <= K색, r셀
    assert xdog(cel, 물).shape == (128, 128)
    print("  자가검사 통과 — 평탄 %.2f(셀) -> %.2f(회화) -> %.2f(셀화) · 색 %d"
          % (기["평탄몫"], r회["평탄몫"], r셀["평탄몫"], r셀["색수(8단위)"]))


if __name__ == "__main__":
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass
    a = sys.argv[1] if len(sys.argv) > 1 else "검사"
    {"검사": selfcheck, "벤치": 벤치, "원화": 원화, "판정": verdict, "그림": 그림}[a]()
