# -*- coding: utf-8 -*-
"""**화풍이 정말 벽인가** — 연속 계조 입력에서 오목 크리스를 찾나 (2026-09-21).

    python 화풍.py 검사
    python 화풍.py 재기     벤치 6 장 × 입력 넷 -> out/기록/화풍_진행.json
    python 화풍.py 판정     -> out/기록/화풍_<때>.json
    python 화풍.py 그림     -> out/화풍.png

09-21 `셀화` 에서 이상한 것이 나왔다 — **회화적으로 뭉개도 오목 재현율이 안 떨어진다**
(궤짝 0.957 → 0.953 · 드릴 0.802 → **0.890**). 그런데 우리는 「회화적이라 못 읽는다」를
믿어 왔고, 그 근거는 **재구성 오차**였다. 같은 바퀴에서 그 자가 재현율과 **같은 방향이
아니라는 것**도 드러났다. 그러면 **화풍이 벽이라는 증거가 지금 없다.**

그래서 흐림이 아니라 **진짜 연속 계조**로 시험한다 — 정답 메시를 **셀 양자화 없이** 렌더한
것(`폴리싱.shaded` 그대로)이 곧 회화적 입력이다. 톤 계단이 아예 없다.

    셀        명암판 (셀 4 단) — 지금까지 쓰던 입력
    매끈      같은 렌더, **양자화 안 함** — 연속 계조
    매끈+셀화   매끈을 평균이동+양자화로 되돌림 (09-21 셋 중 제일 정직했던 것)
    매끈+흐림   매끈에 가우시안 2.5 — 붓질처럼 경계까지 흐린 것

**자는 둘이다** — 오목 재현율(정답 있음)과 **최대 판 몫**(한 판이 통째로 먹는 것). 재구성 오차는
**참고로만** 적는다. 09-21 에 그 자가 XDoG 선에 속는 것을 봤다.

**문턱을 돌리기 전에 적는다.**

    Q1  「매끈」이 셀보다 오목 재현율을 **0.15 이상** 떨어뜨린다 -> 화풍이 벽이다
        (못 떨어뜨리면 **벽이 아니다**. 그러면 셀화 갈래를 접는다)
    Q2  Q1 이 걸릴 때만 뜻이 있다 — 셀화가 **0.80 이상 회복**한다
    Q3  어느 입력에서도 **최대 판 몫 <= 0.5** (한 판이 절반을 넘게 먹지 않는다)
"""
import json
import os
import subprocess
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260920")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260919")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260916")
import 선읽기 as LR
import 전처리 as PP
import 셀화 as CH
import 도해도 as DH
import 폴리싱 as PL
HERE, OUT, 도구 = LR.HERE, LR.OUT, LR.도구
DST = os.path.join(HERE, "out", "화풍")
PROG = os.path.join(OUT, "화풍_진행.json")
S = LR.S
입력들 = ("셀", "매끈", "매끈+셀화", "매끈+흐림")
벤치장 = PP.벤치장
Q1하락, Q2회복, Q3판몫 = 0.15, 0.80, 0.5


def 판만들기(truth, az=45, el=45):
    """(셀, 매끈, 물건마스크). 둘은 **같은 렌더**에서 나온다 — 양자화 여부만 다르다."""
    import cv2
    m = LR.LC.기울(truth, el)
    fr = LR.ME.AL.frame_of(m, az)
    img = PL.shaded(m, az, fr, S=S)
    g = img.mean(2)
    물 = g < (LR.바탕 - 1)
    q = np.digitize(g, LR.톤)
    셀 = np.full((S, S, 3), LR.바탕, np.uint8)
    셀[물] = LR.셀색[np.clip(q[물], 0, 3)]
    매 = np.full((S, S, 3), LR.바탕, np.uint8)
    매[물] = img[물]
    흐 = np.full((S, S, 3), LR.바탕, np.uint8)
    흐[물] = cv2.GaussianBlur(img, (0, 0), 2.5)[물]
    return 셀, 매, 흐, 물


def one(case):
    from PIL import Image
    t0 = time.time()
    import trimesh
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    셀, 매, 흐, 물 = 판만들기(truth)
    정 = np.load(os.path.join(HERE, "out", "선채널", case, "위45.npy"))
    d = os.path.join(DST, case)
    os.makedirs(d, exist_ok=True)
    판 = {"셀": 셀, "매끈": 매, "매끈+셀화": CH.셀화(매, 물, "평균이동+양자화"), "매끈+흐림": 흐}
    r = {}
    for n, im in 판.items():
        p = os.path.join(d, "%s.png" % n.replace("+", "_"))
        Image.fromarray(im).save(p)
        o = os.path.join(d, n.replace("+", "_") + "_추출")
        os.makedirs(o, exist_ok=True)
        subprocess.run([sys.executable, 도구, p, "--out", o, "--scale", str(S)],
                       capture_output=True, timeout=1800)
        lp = os.path.join(o, "labels_grown.npy")
        r[n] = {**DH.잰다(im, 물), **PP.판지표(o),
                **(LR.채점(LR.경계(np.load(lp)), 정, 물) if os.path.exists(lp) else {})}
    R0 = r["셀"].get("재현_오목크리스")
    R1 = r["매끈"].get("재현_오목크리스")
    R2 = r["매끈+셀화"].get("재현_오목크리스")
    r["하락(셀−매끈)"] = round(R0 - R1, 4) if None not in (R0, R1) else None
    r["회복몫"] = round((R2 - R1) / (R0 - R1), 4) if None not in (R0, R1, R2) and R0 - R1 > 1e-6 else None
    r["초"] = round(time.time() - t0, 1)
    return r


def 재기():
    out = json.load(open(PROG, encoding="utf-8")) if os.path.exists(PROG) else {}
    for c in [x for x in 벤치장 if x not in out]:
        out[c] = one(c)
        json.dump(out, open(PROG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        r = out[c]
        print("  %-30s 오목 " % c[:30] + " ".join(
            "%s %s" % (n, "%.3f" % r[n]["재현_오목크리스"] if r[n].get("재현_오목크리스") is not None else "-")
            for n in 입력들) + " · 하락 %s (%.0f초)"
            % ("%.3f" % r["하락(셀−매끈)"] if r["하락(셀−매끈)"] is not None else "-", r["초"]), flush=True)
    print("  ->", PROG)
    return out


def verdict():
    o = json.load(open(PROG, encoding="utf-8"))
    cs = list(o)
    med = lambda x: round(float(np.median(x)), 4) if x else None
    하 = [o[c]["하락(셀−매끈)"] for c in cs if o[c]["하락(셀−매끈)"] is not None]
    회 = [o[c]["회복몫"] for c in cs if o[c]["회복몫"] is not None]
    판몫 = {n: [o[c][n].get("최대판몫") for c in cs if o[c][n].get("최대판몫") is not None] for n in 입력들}
    v = {"판": "화풍 v1 · 셀 대 연속 계조 (2026-09-21)", "때": time.strftime("%Y%m%d_%H%M"), "장": len(cs),
         "Q1": {"문턱": "매끈이 오목 재현율을 %g 이상 떨어뜨린다" % Q1하락, "중앙": med(하),
                "장별": {c: o[c]["하락(셀−매끈)"] for c in cs},
                "통과": bool(하 and np.median(하) >= Q1하락)},
         "Q2": {"문턱": "Q1 이 걸릴 때만 뜻이 있다 — 셀화 회복몫 >= %g" % Q2회복, "중앙": med(회)},
         "Q3": {"문턱": "모든 입력에서 최대 판 몫 <= %g" % Q3판몫,
                "입력별 최악": {n: round(float(max(판몫[n])), 4) for n in 입력들 if 판몫[n]},
                "통과": bool(all(max(판몫[n]) <= Q3판몫 for n in 입력들 if 판몫[n]))},
         "오목 재현율 중앙": {n: med([o[c][n].get("재현_오목크리스") for c in cs
                                 if o[c][n].get("재현_오목크리스") is not None]) for n in 입력들},
         "재구성오차 중앙(참고)": {n: med([o[c][n].get("재구성오차") for c in cs
                                    if o[c][n].get("재구성오차") is not None]) for n in 입력들},
         "평탄몫 중앙": {n: med([o[c][n]["평탄몫"] for c in cs]) for n in 입력들},
         "장별": o}
    p = os.path.join(OUT, "화풍_%s.json" % v["때"])
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %-12s %10s %10s %12s %10s" % ("입력", "오목중앙", "평탄중앙", "재구성(참고)", "최대판몫"))
    for n in 입력들:
        print("  %-12s %10s %10s %12s %10s"
              % (n, v["오목 재현율 중앙"][n], v["평탄몫 중앙"][n], v["재구성오차 중앙(참고)"][n],
                 v["Q3"]["입력별 최악"].get(n)))
    for k in ("Q1", "Q2", "Q3"):
        print("\n  %s %s" % (k, json.dumps(v[k], ensure_ascii=False)[:400]))
    print("\n  ->", p)
    return v


def 그림():
    from PIL import Image
    o = json.load(open(PROG, encoding="utf-8"))
    R = []
    for c in o:
        d = os.path.join(DST, c)
        ts = []
        for n in 입력들:
            for suf in ("", "_추출"):
                p = os.path.join(d, n.replace("+", "_") + (".png" if not suf else
                                                           os.path.join("_추출", "regions.png")))
                p = os.path.join(d, "%s.png" % n.replace("+", "_")) if not suf else \
                    os.path.join(d, n.replace("+", "_") + "_추출", "regions.png")
                ts.append(np.asarray(Image.open(p).convert("RGB")) if os.path.exists(p)
                          else np.full((S, S, 3), 240, np.uint8))
        R.append(("%s\n오목 %s" % (c[:18], " ".join(
            "%.2f" % o[c][n]["재현_오목크리스"] if o[c][n].get("재현_오목크리스") is not None else "-"
            for n in 입력들)), ts))
    cs = sum([[n, n + " 추출"] for n in 입력들], [])
    LR.DC.grid(R, tuple(cs), "화풍이 정말 벽인가 — 셀 4 단 대 연속 계조 (정답 있음)",
               "오목 크리스 재현율을 장 이름 아래 차례로 적었다 (셀 · 매끈 · 매끈+셀화 · 매끈+흐림)",
               os.path.join(HERE, "out", "화풍.png"), S=230)


def selfcheck():
    import trimesh
    truth = trimesh.load(os.path.join(HERE, "out", "시트", 벤치장[0], "truth.glb"), force="mesh")
    셀, 매, 흐, 물 = 판만들기(truth)
    a, b = DH.잰다(셀, 물), DH.잰다(매, 물)
    assert a["색수(8단위)"] <= 5 and b["색수(8단위)"] > 20, (a, b)
    assert b["평탄몫"] < a["평탄몫"], "매끈이 셀보다 평탄하면 안 된다 %s %s" % (a, b)
    정 = np.load(os.path.join(HERE, "out", "선채널", 벤치장[0], "위45.npy"))
    assert 셀.shape[:2] == 정.shape
    겹 = float(((정 > 0) & 물).sum() / max((정 > 0).sum(), 1))
    assert 겹 > 0.95, 겹
    print("  자가검사 통과 — 셀 색 %d 평탄 %.2f · 매끈 색 %d 평탄 %.2f · 틀 겹침 %.3f"
          % (a["색수(8단위)"], a["평탄몫"], b["색수(8단위)"], b["평탄몫"], 겹))


if __name__ == "__main__":
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass
    a = sys.argv[1] if len(sys.argv) > 1 else "검사"
    {"검사": selfcheck, "재기": 재기, "판정": verdict, "그림": 그림}[a]()
