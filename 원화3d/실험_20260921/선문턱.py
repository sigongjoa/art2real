# -*- coding: utf-8 -*-
"""**선 문턱을 그림마다 정하면 어두운 원화가 살아나나** (2026-09-21).

    python 선문턱.py 검사
    python 선문턱.py 원화     진짜 원화 10 판 × 문턱 넷  (정답 없음 — 재구성오차 · 최대판몫 · 판수)
    python 선문턱.py 벤치     벤치 3 장 × 문턱 넷        (정답 있음 — 오목 재현율)
    python 선문턱.py 판정     -> out/기록/선문턱_<때>.json
    python 선문턱.py 그림     -> out/선문턱_원화.png · out/선문턱_벤치.png

09-21 `도해도` 가 까닭을 짚었다 — **은둔자 삼면도는 선몫 0.92~0.94**. 그림이 어두워서 물건의
아홉 몫이 `art3d.py --line 105` 아래로 들어가고, 추출기가 거의 전부를 「선」으로 읽는다.
**고정 문턱이 범인이면 그림마다 정하면 살아나야 한다.**

문턱 넷을 견준다 — 현행 고정 **105** · 물건 명도의 **20 백분위** · **30 백분위** · **Otsu**.
(20·30 백분위는 **잘 되는 장에서 거꾸로 읽은 값**이다 — 오메가몬 선몫 0.27~0.36 · 폴드론 0.36~0.55.
그렇게 고른 것을 그대로 적는다.)

입력은 **배경만 뺀 판**이다 — 레벨은 안 건다(09-21 전처리 Q3: 멀쩡하면 건드리지 마라).

**문턱을 돌리기 전에 적는다.**

    Q1  은둔자 삼면도 3 판 중 **2 판 이상**에서 재구성 오차가 **5/255 아래**로 내려간다
    Q2  잘 되던 장(오메가몬 · 폴드론 6 판)이 **안 망가진다** — 재구성 오차 상승 <= 1.0
    Q3  벤치 3 장의 **오목 재현율 하락 <= 0.05** (정답 있는 쪽)
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
DST = os.path.join(HERE, "out", "선문턱")
S = LR.S
스킬문턱 = 5.0
문턱들 = ("고정105", "p20", "p30", "otsu")
벤치장 = PP.벤치장[:3]
Q2상승, Q3하락 = 1.0, 0.05


def 선값(rgb, 물, 방식):
    import cv2
    g = rgb.astype(np.float32).mean(2)
    if 방식 == "고정105":
        return 105
    if 방식.startswith("p"):
        return int(round(float(np.percentile(g[물], float(방식[1:])))))
    t, _ = cv2.threshold(g[물].astype(np.uint8), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # OpenCV 규약은 `> t` 가 앞면이라 두 값짜리 히스토그램에서 **아래쪽 끝값**을 돌려준다
    # (자가검사가 잡았다: {30, 200} 에 30). `--line` 은 `< line` 이라 한 칸 올려 맞춘다.
    return int(round(float(t))) + 1


def 돌려(png, o, line):
    import subprocess
    os.makedirs(o, exist_ok=True)
    subprocess.run([sys.executable, 도구, png, "--out", o, "--scale", str(S), "--line", str(line)],
                   capture_output=True, timeout=1800)
    return PP.판지표(o)


def 원화():
    from PIL import Image
    import cv2
    import 원화진단 as JD
    out = {}
    for key, nick, grp, pngs, _, _ in JD.집합():
        if grp != "원화":
            continue
        for v, src in pngs.items():
            im = cv2.imdecode(np.fromfile(src, np.uint8), cv2.IMREAD_UNCHANGED)
            if im.ndim == 2:
                im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
            a = im[:, :, 3] if im.shape[2] == 4 else None
            rgb = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            s = S / max(h, w)
            rgb = cv2.resize(rgb, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA)
            a = cv2.resize(a, rgb.shape[1::-1], interpolation=cv2.INTER_AREA) if a is not None else None
            물 = PP.배경마스크(rgb, a)
            base = np.full_like(rgb, LR.바탕)
            base[물] = rgb[물]                       # **배경만 뺀다** — 레벨은 안 건다
            d = os.path.join(DST, "원화_" + key, v)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, "입력.png")
            Image.fromarray(base).save(p)
            r = {"선몫(105)": round(float((rgb.astype(np.float32).mean(2)[물] < 105).mean()), 4)}
            for m in 문턱들:
                ln = 선값(rgb, 물, m)
                r[m] = {"line": ln, **돌려(p, os.path.join(d, m), ln)}
            out["%s/%s" % (nick, v)] = r
            print("  %-24s %-6s " % (nick, v) + " · ".join(
                "%s(%d) 재구성 %s 최대판 %s" % (m, r[m]["line"],
                                            ("%.2f" % r[m]["재구성오차"]) if r[m].get("재구성오차") is not None else "-",
                                            ("%.2f" % r[m]["최대판몫"]) if r[m].get("최대판몫") is not None else "-")
                for m in 문턱들), flush=True)
    p = os.path.join(OUT, "선문턱_원화.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", p)
    return out


def 벤치():
    from PIL import Image
    import trimesh
    out = {}
    for c in 벤치장:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        cel, 있 = LR.명암판(truth, 45, 45)
        정 = np.load(os.path.join(HERE, "out", "선채널", c, "위45.npy"))
        d = os.path.join(DST, c)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "입력.png")
        Image.fromarray(cel).save(p)
        r = {}
        for m in 문턱들:
            ln = 선값(cel, 있, m)
            o = os.path.join(d, m)
            g = 돌려(p, o, ln)
            lp = os.path.join(o, "labels_grown.npy")
            r[m] = {"line": ln, **g,
                    **(LR.채점(LR.경계(np.load(lp)), 정, 있) if os.path.exists(lp) else {})}
        out[c] = r
        print("  %-30s " % c[:30] + " · ".join(
            "%s(%d) 오목 %s" % (m, r[m]["line"],
                              ("%.3f" % r[m]["재현_오목크리스"]) if r[m].get("재현_오목크리스") is not None else "-")
            for m in 문턱들), flush=True)
    p = os.path.join(OUT, "선문턱_벤치.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", p)
    return out


def verdict():
    a = json.load(open(os.path.join(OUT, "선문턱_원화.json"), encoding="utf-8"))
    b = json.load(open(os.path.join(OUT, "선문턱_벤치.json"), encoding="utf-8"))
    어둠 = [k for k in a if k.startswith("은둔자 삼면도")]
    멀쩡 = [k for k in a if k.startswith("오메가몬") or k.startswith("폴드론")]
    v = {"판": "선문턱 v1 · 고정105 대 p20 · p30 · otsu (2026-09-21)", "때": time.strftime("%Y%m%d_%H%M"),
         "문턱": {"Q1": "은둔자 삼면도 3 판 중 2 판 이상 재구성오차 < %g" % 스킬문턱,
                 "Q2": "오메가몬 · 폴드론 재구성오차 상승 <= %g" % Q2상승,
                 "Q3": "벤치 오목 재현율 하락 <= %g" % Q3하락}}
    for m in 문턱들:
        e = lambda k: a[k][m].get("재구성오차")
        살 = [k for k in 어둠 if e(k) is not None and e(k) < 스킬문턱]
        상 = [round(e(k) - a[k]["고정105"]["재구성오차"], 3) for k in 멀쩡
              if e(k) is not None and a[k]["고정105"].get("재구성오차") is not None]
        하 = [round(b[c]["고정105"]["재현_오목크리스"] - b[c][m]["재현_오목크리스"], 4) for c in b
              if b[c][m].get("재현_오목크리스") is not None and b[c]["고정105"].get("재현_오목크리스") is not None]
        v[m] = {"은둔자 재구성오차": {k: e(k) for k in 어둠}, "5 아래로 내려간 판": len(살),
                "멀쩡한장 상승": 상, "상승 최대": max(상) if 상 else None,
                "벤치 오목 하락": 하, "하락 최대": max(하) if 하 else None,
                "Q1": bool(len(살) >= 2),
                "Q2": bool(상 and max(상) <= Q2상승),
                "Q3": bool(하 and max(하) <= Q3하락)}
        v[m]["셋 다"] = bool(v[m]["Q1"] and v[m]["Q2"] and v[m]["Q3"])
    p = os.path.join(OUT, "선문턱_%s.json" % v["때"])
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %-8s %-26s %6s %8s %8s %6s" % ("문턱", "은둔자 재구성(앞·뒤·옆)", "5아래", "멀쩡상승", "벤치하락", "셋다"))
    for m in 문턱들:
        x = v[m]
        es = " ".join("%5s" % ("%.2f" % y if y is not None else "-") for y in x["은둔자 재구성오차"].values())
        print("  %-8s %-26s %6d %8s %8s %6s"
              % (m, es, x["5 아래로 내려간 판"],
                 "%+.2f" % x["상승 최대"] if x["상승 최대"] is not None else "-",
                 "%+.3f" % x["하락 최대"] if x["하락 최대"] is not None else "-",
                 "통과" if x["셋 다"] else "짐"))
    print("\n  ->", p)
    return v


def 그림():
    from PIL import Image
    import 원화진단 as JD
    a = json.load(open(os.path.join(OUT, "선문턱_원화.json"), encoding="utf-8"))
    R = []
    for key, nick, grp, pngs, _, _ in JD.집합():
        if grp != "원화":
            continue
        for v in ("front", "side", "back"):
            if v not in pngs:
                continue
            d = os.path.join(DST, "원화_" + key, v)
            ts = [np.asarray(Image.open(os.path.join(d, "입력.png")).convert("RGB"))]
            for m in 문턱들:
                p = os.path.join(d, m, "regions.png")
                ts.append(np.asarray(Image.open(p).convert("RGB")) if os.path.exists(p)
                          else np.full((S, S, 3), 240, np.uint8))
            r = a.get("%s/%s" % (nick, v), {})
            lab = "%s %s\n선몫 %.2f" % (nick[:12], v, r.get("선몫(105)", 0))
            R.append((lab, ts))
    LR.DC.grid(R, ("배경만 뺀 입력",) + tuple(
        "%s" % m for m in 문턱들),
        "선 문턱을 그림마다 — 어두운 원화가 살아나나 (정답 없음 · 재구성 오차로 본다)",
        "추출기의 `--line` 만 바꾼다. 고정 105 은 현행. p20 · p30 은 물건 명도의 백분위 · otsu 는 자동 두 갈래",
        os.path.join(HERE, "out", "선문턱_원화.png"), S=260)
    b = json.load(open(os.path.join(OUT, "선문턱_벤치.json"), encoding="utf-8"))
    R2 = []
    for c in b:
        d = os.path.join(DST, c)
        ts = [np.asarray(Image.open(os.path.join(d, "입력.png")).convert("RGB"))]
        for m in 문턱들:
            p = os.path.join(d, m, "regions.png")
            ts.append(np.asarray(Image.open(p).convert("RGB")) if os.path.exists(p)
                      else np.full((S, S, 3), 240, np.uint8))
        R2.append(("%s\n오목 %s" % (c[:18], " ".join(
            "%.2f" % b[c][m]["재현_오목크리스"] if b[c][m].get("재현_오목크리스") is not None else "-"
            for m in 문턱들)), ts))
    LR.DC.grid(R2, ("명암판 입력",) + 문턱들,
               "선 문턱 — 벤치 (정답 있음 · 오목 크리스 재현율)",
               "왼쪽부터 고정105 · p20 · p30 · otsu 의 오목 재현율을 장 이름 아래 적었다",
               os.path.join(HERE, "out", "선문턱_벤치.png"), S=260)


def selfcheck():
    rng = np.random.default_rng(0)
    g = np.concatenate([np.full(300, 30), np.full(700, 200)]).astype(np.uint8)   # 어두운 몫 30%
    rgb = np.repeat(g.reshape(20, 50, 1), 3, 2)
    물 = np.ones((20, 50), bool)
    assert 선값(rgb, 물, "고정105") == 105
    assert 선값(rgb, 물, "p20") <= 40, 선값(rgb, 물, "p20")
    o = 선값(rgb, 물, "otsu")
    assert (g < o).sum() == 300, "otsu 가 두 무리를 못 갈랐다 (%d, 아래 %d개)" % (o, int((g < o).sum()))
    print("  자가검사 통과 — p20 %d · otsu %d" % (선값(rgb, 물, "p20"), o))


if __name__ == "__main__":
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass
    a = sys.argv[1] if len(sys.argv) > 1 else "검사"
    {"검사": selfcheck, "원화": 원화, "벤치": 벤치, "판정": verdict, "그림": 그림}[a]()
