# -*- coding: utf-8 -*-
"""**원화의 정보량을 손으로 맞춘다 — 배경 빼기 + 레벨** (2026-09-21).

    python 전처리.py 검사     자가검사 (레벨 왕복 · 배경 마스크)
    python 전처리.py 벤치     찌그러뜨린 판에서 전처리가 오목 재현율을 되살리나 (정답 있음)
    python 전처리.py 원화     진짜 원화 넷 — 전 · 후 (정답 없음 · 지표는 정답 없이 되는 것만)
    python 전처리.py 판정     -> out/기록/전처리_<때>.json
    python 전처리.py 그림     -> out/전처리_벤치.png · out/전처리_원화.png

사용자(09-21): 「오메가몬은 뭔가 잘 나오는데, 배경 제거하고 포토샵에서는 **멀티 레벨**?
그걸로 정보량을 조절하잖아. 우리도 원화에서 그런 액션을 해야 하지 않을까?」

맞다. 09-21 `선읽기` 에서 **은둔자 삼면도는 배경이 통째로 큰 판**이 됐고, 오메가몬(흰 바탕 ·
톤이 또렷)은 잘 갈렸다. 추출기의 톤 양자화는 **고정 문턱**인데 원화마다 명도 분포가 다르다
(09-20 원화진단: 음영단수 1~4 · 평균명도 제각각 · `검은장` 표시). 그래서 **레벨**로 물건 화소의
명도를 먼저 펴 준다 — 포토샵 입력 레벨(검은점 · 흰점 · 감마)과 같은 연산이다.

**문턱을 돌리기 전에 적는다.**

    Q1  (원화 · 정답 없음) 지금 실패하는 장에서 **최대 판 몫**이 0.25 아래로 내려간다
        = 배경이 통째로 한 판이 되는 일이 사라진다
    Q2  (벤치 · 정답 있음) 대비를 찌그러뜨린 판에서 전처리가 오목 재현율을
        **원래의 80% 이상 되살린다**  — 회복몫 = (R2 − R1) / (R0 − R1)
    Q3  전처리가 **멀쩡한 판을 망치지 않는다** — 오목 재현율 하락 <= 0.05

레벨은 **물건 화소에서만** 백분위를 잡는다. 배경까지 넣고 잡으면 검은 배경이 검은점을
차지해 물건이 통째로 흰쪽으로 몰린다.
"""
import json
import os
import subprocess
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
import numpy as np

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260920")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260919")
import 선읽기 as LR
import 선채널 as LC
LC_ = LC
HERE, OUT, 도구 = LR.HERE, LR.OUT, LR.도구
DST = os.path.join(HERE, "out", "전처리")
TAG = "전처리 v1 · 배경빼기 + 레벨(물건 화소 백분위) · 벤치 찌그러뜨림 대조 (2026-09-21)"

S = LR.S
백분위 = (1.0, 99.0)
감마 = 1.0
선문턱 = 105                   # `art3d.py --line` 기본값. 이 아래는 추출기가 **선**으로 본다
출력레벨 = (120.0, 240.0)      # 포토샵 출력 레벨. 톤 띠가 선 문턱 아래로 안 내려가게
찌 = (60, 150)                 # 찌그러뜨림 — 명도를 이 구간으로 눌러 「정보량이 적은 판」을 만든다
찌배경 = 70                    # 그리고 배경을 어둡게 (은둔자 삼면도가 그렇다)
Q1문턱, Q2회복, Q3하락 = 0.25, 0.80, 0.05
벤치장 = ("cloak_Chest_Closed_AngpV0HxD8", "mech_Drill_8uBbH7Dvmb", "monster_Mimic_B8HrWzkuNp",
          "wizard_Evil_Wizard_bdxawstqtq", "knight_Warrior_RaWl2GJ0NZ", "witch_Witch_vWI9PHfjcy")
뷰 = "위45"


# ── 연산 둘 ──────────────────────────────────────────────────────────────────

def 배경마스크(rgb, alpha=None, tol=26):
    """물건 화소 bool. 알파가 있으면 그걸 쓰고, 없으면 **테두리에서 홍수채우기**.
    배경이 물건과 같은 명도면 새어 들어간다 — 그때는 이 함수가 아니라 원화가 문제다(그대로 적는다)."""
    import cv2
    if alpha is not None:
        return alpha > 127
    h, w = rgb.shape[:2]
    ff = np.zeros((h + 2, w + 2), np.uint8)
    img = rgb.copy()
    for seed in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        cv2.floodFill(img, ff, seed, (0, 0, 0), (tol,) * 3, (tol,) * 3,
                      4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8))
    return ff[1:-1, 1:-1] == 0


def 레벨(rgb, 물, p=백분위, gamma=감마, 출력=(0.0, 255.0), 선보존=False):
    """포토샵 입력 레벨 + **출력 레벨**. **물건 화소에서만** 검은점 · 흰점을 잡는다.

    `출력` 이 필요한 이유는 돌려 보고 알았다 — 0~255 로 펴면 어두운 톤 띠가 추출기의
    **선 문턱(`--line 105`)** 아래로 내려가 톤이 통째로 「선」으로 읽힌다 (궤짝: 105 미만 화소가
    0.242 -> 0.749). 포토샵으로 치면 입력 레벨만 만지고 출력 레벨을 안 만진 것이다.
    `선보존` 은 원본에서 이미 선이던 화소(< 선문턱)를 그대로 두고 나머지 톤만 편다."""
    g = rgb.mean(2)
    if not 물.any():
        return rgb.copy(), (0.0, 255.0)
    선 = 물 & (g < 선문턱) if 선보존 else np.zeros_like(물)
    대상 = 물 & ~선
    if not 대상.any():
        대상 = 물
    lo, hi = np.percentile(g[대상], list(p))
    if hi - lo < 1:
        lo, hi = float(g[대상].min()), float(g[대상].max())
    t = np.clip((rgb.astype(np.float32) - lo) / max(hi - lo, 1.0), 0, 1)
    if gamma != 1.0:
        t = t ** (1.0 / gamma)
    out = 출력[0] + t * (출력[1] - 출력[0])
    out = np.clip(out, 0, 255).astype(np.uint8)
    if 선.any():
        out[선] = rgb[선]
    return out, (round(float(lo), 1), round(float(hi), 1))


def 전처리(rgb, alpha=None, 바탕=LR.바탕, 출력=(0.0, 255.0), 선보존=False):
    물 = 배경마스크(rgb, alpha)
    lv, 구간 = 레벨(rgb, 물, 출력=출력, 선보존=선보존)
    out = np.full_like(rgb, 바탕)
    out[물] = lv[물]
    return out, 물, 구간


def 찌그러뜨림(cel, 물):
    """실제 원화의 흠을 흉내 낸다 — 명도를 좁은 구간으로 누르고 배경을 어둡게."""
    g = cel.astype(np.float32)
    lo, hi = 찌
    out = (g - g.min()) / max(g.max() - g.min(), 1) * (hi - lo) + lo
    res = np.full_like(cel, 찌배경)
    res[물] = out[물].astype(np.uint8)
    return res


# ── 지표 (정답 없이 되는 것) ─────────────────────────────────────────────────

def 판지표(o):
    """추출기 출력 폴더 -> 정답 없이 되는 지표. 최대 판 몫 · 판 수 · 재구성 오차."""
    lp = os.path.join(o, "labels_grown.npy")
    if not os.path.exists(lp):
        return {"실패": "labels_grown 없음"}
    lab = np.load(lp)
    n = np.bincount(lab.ravel())
    n[0] = 0
    tot = max(int(n.sum()), 1)
    j = json.load(open(os.path.join(o, "art3d.json"), encoding="utf-8"))
    return {"판수": int((n > 0).sum()), "최대판몫": round(float(n.max() / tot), 4),
            "상위3몫": [round(float(x / tot), 4) for x in np.sort(n)[::-1][:3]],
            "재구성오차": j.get("metrics", {}).get("recon_error")}


def 돌려(png, o):
    os.makedirs(o, exist_ok=True)
    subprocess.run([sys.executable, 도구, png, "--out", o, "--scale", str(S)],
                   capture_output=True, timeout=1800)
    return o


# ── 벤치 (정답 있음) ─────────────────────────────────────────────────────────

def 벤치():
    from PIL import Image
    import trimesh
    out = {}
    for c in 벤치장:
        t0 = time.time()
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        cel, 있 = LR.명암판(truth, 45, 45)
        정 = np.load(os.path.join(HERE, "out", "선채널", c, "%s.npy" % 뷰))
        d = os.path.join(DST, c)
        os.makedirs(d, exist_ok=True)
        판 = {"원본": cel, "찌그러뜨림": 찌그러뜨림(cel, 있)}
        판["찌+레벨"] = 전처리(판["찌그러뜨림"])[0]
        # **사후 판본 둘** — 위 「찌+레벨」이 크게 지고 나서 까닭(선 문턱)을 찾아 더한 것이다
        판["찌+레벨출력"] = 전처리(판["찌그러뜨림"], 출력=출력레벨)[0]
        판["찌+레벨선보존"] = 전처리(판["찌그러뜨림"], 출력=출력레벨, 선보존=True)[0]
        판["원본+레벨출력"] = 전처리(cel, 출력=출력레벨)[0]
        r = {}
        for n, im in 판.items():
            p = os.path.join(d, "%s.png" % n)
            Image.fromarray(im).save(p)
            o = 돌려(p, os.path.join(d, n))
            lp = os.path.join(o, "labels_grown.npy")
            if not os.path.exists(lp):
                r[n] = {"실패": "추출 실패"}
                continue
            r[n] = {**LR.채점(LR.경계(np.load(lp)), 정, 있), **판지표(o)}
        g_ = lambda n: r.get(n, {}).get("재현_오목크리스")
        R0, R1, R3 = g_("원본"), g_("찌그러뜨림"), g_("원본+레벨출력")
        회 = lambda R2: round((R2 - R1) / (R0 - R1), 4) if None not in (R0, R1, R2) and R0 - R1 > 1e-6 else None
        r["회복몫"] = {n: 회(g_(n)) for n in ("찌+레벨", "찌+레벨출력", "찌+레벨선보존")}
        r["멀쩡한판하락"] = round(R0 - R3, 4) if None not in (R0, R3) else None
        R2 = g_("찌+레벨출력")
        r["초"] = round(time.time() - t0, 1)
        out[c] = r
        print("  %-34s 원본 %s · 찌 %s · 찌+전 %s · 회복 %s · 하락 %s (%.0f초)"
              % (c[:34], "%.3f" % R0 if R0 else "-", "%.3f" % R1 if R1 else "-",
                 "%.3f" % R2 if R2 else "-",
                 "%.2f" % r["회복몫"]["찌+레벨출력"] if r["회복몫"]["찌+레벨출력"] is not None else "-",
                 "%+.3f" % r["멀쩡한판하락"] if r["멀쩡한판하락"] is not None else "-",
                 r["초"]), flush=True)
    p = os.path.join(OUT, "전처리_벤치.json")
    json.dump({"판": TAG, "장별": out}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", p)
    return out


# ── 진짜 원화 (정답 없음) ────────────────────────────────────────────────────

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
            d = os.path.join(DST, "원화_" + key, v)
            os.makedirs(d, exist_ok=True)
            pre, 물, 구간 = 전처리(rgb, a)
            r = {"알파": a is not None, "물건몫": round(float(물.mean()), 4), "레벨구간": 구간}
            for n, im2 in (("전", rgb), ("후", pre)):
                p = os.path.join(d, "%s.png" % n)
                Image.fromarray(im2).save(p)
                r[n] = 판지표(돌려(p, os.path.join(d, n)))
            out["%s/%s" % (nick, v)] = r
            print("  %-22s %-6s 알파 %-5s 최대판몫 %s -> %s · 판수 %s -> %s"
                  % (nick, v, r["알파"],
                     r["전"].get("최대판몫"), r["후"].get("최대판몫"),
                     r["전"].get("판수"), r["후"].get("판수")), flush=True)
    p = os.path.join(OUT, "전처리_원화.json")
    json.dump({"판": TAG, "장별": out}, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", p)
    return out


# ── 판정 ─────────────────────────────────────────────────────────────────────

def verdict():
    b = json.load(open(os.path.join(OUT, "전처리_벤치.json"), encoding="utf-8"))["장별"]
    a = json.load(open(os.path.join(OUT, "전처리_원화.json"), encoding="utf-8"))["장별"]
    med = lambda x: round(float(np.median(x)), 4) if x else None
    회 = {n: [v["회복몫"][n] for v in b.values() if v.get("회복몫", {}).get(n) is not None]
          for n in ("찌+레벨", "찌+레벨출력", "찌+레벨선보존")}
    하 = [v["멀쩡한판하락"] for v in b.values() if v.get("멀쩡한판하락") is not None]
    나쁨 = {k: v for k, v in a.items() if v["전"].get("최대판몫", 0) >= 0.5}
    고침 = {k: v["후"].get("최대판몫") for k, v in 나쁨.items()}
    v = {"판": TAG, "때": time.strftime("%Y%m%d_%H%M"),
         "Q1": {"문턱": "지금 실패하는 장(최대판몫 >= 0.5)의 최대판몫이 %g 아래로" % Q1문턱,
                "실패장": list(나쁨), "전": {k: x["전"].get("최대판몫") for k, x in 나쁨.items()},
                "후": 고침,
                "통과": bool(나쁨) and all(x is not None and x < Q1문턱 for x in 고침.values())},
         "Q2": {"문턱": "찌그러뜨린 판에서 회복몫 중앙 >= %g" % Q2회복,
                "원래 걸었던 판본(찌+레벨)": med(회["찌+레벨"]),
                "통과": bool(회["찌+레벨"] and np.median(회["찌+레벨"]) >= Q2회복),
                "사후 판본": {n: med(회[n]) for n in ("찌+레벨출력", "찌+레벨선보존")},
                "주석": "「찌+레벨」이 먼저 크게 졌고, 까닭(선 문턱 105)을 찾아 뒤에 둘을 더했다. 문턱은 안 바꿨다",
                "장별": {k: v["회복몫"] for k, v in b.items()}},
         "Q3": {"문턱": "멀쩡한 판의 오목 재현율 하락 중앙 <= %g" % Q3하락, "중앙": med(하),
                "장별": {k: v["멀쩡한판하락"] for k, v in b.items()},
                "통과": bool(하 and np.median(하) <= Q3하락)},
         "벤치": b, "원화": a}
    p = os.path.join(OUT, "전처리_%s.json" % v["때"])
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k in ("Q1", "Q2", "Q3"):
        print("\n  %s %s" % (k, json.dumps(v[k], ensure_ascii=False)[:700]))
    print("\n  ->", p)
    return v


# ── 그림 ─────────────────────────────────────────────────────────────────────

def 그림():
    from PIL import Image
    b = json.load(open(os.path.join(OUT, "전처리_벤치.json"), encoding="utf-8"))["장별"]
    R = []
    for c, r in b.items():
        ts = []
        for n in ("원본", "찌그러뜨림", "찌+전처리"):
            ts.append(np.asarray(Image.open(os.path.join(DST, c, "%s.png" % n)).convert("RGB")))
            rp = os.path.join(DST, c, n, "regions.png")
            ts.append(np.asarray(Image.open(rp).convert("RGB")) if os.path.exists(rp)
                      else np.full((S, S, 3), 240, np.uint8))
        g = lambda n: "%.2f" % r[n]["재현_오목크리스"] if r.get(n, {}).get("재현_오목크리스") is not None else "-"
        R.append(("%s\n오목 %s → %s → %s" % (c[:18], g("원본"), g("찌그러뜨림"), g("찌+전처리")), ts))
    LR.DC.grid(R, ("원본 명암판", "판", "찌그러뜨림", "판", "찌 + 전처리", "판"),
               "전처리 — 레벨로 정보량을 되살리나 (벤치 · 정답 있음 · 위에서 45°)",
               "찌그러뜨림 = 명도를 %d~%d 로 누르고 배경을 %d 으로 (실제 원화의 흠을 흉내). 전처리 = 배경 빼기 + 물건 화소 백분위 레벨"
               % (찌[0], 찌[1], 찌배경),
               os.path.join(HERE, "out", "전처리_벤치.png"), S=300)
    a = json.load(open(os.path.join(OUT, "전처리_원화.json"), encoding="utf-8"))["장별"]
    R2 = []
    for k, r in a.items():
        nick, v = k.rsplit("/", 1)
        d = os.path.join(DST, "원화_" + [x for x in os.listdir(DST) if x.startswith("원화_")][0].split("원화_")[-1])
        ts = []
        for n in ("전", "후"):
            p0 = None
            for cand in os.listdir(DST):
                if not cand.startswith("원화_"):
                    continue
                p = os.path.join(DST, cand, v, "%s.png" % n)
                if os.path.exists(p) and nick[:2] in cand or os.path.exists(p):
                    p0 = p if p0 is None else p0
            ts.append(np.full((S, S, 3), 240, np.uint8))
        R2.append((k, ts))
    print("  -> out/전처리_벤치.png")


def 원화그림():
    """원화 전/후 접촉지 — 폴더 이름을 `원화()` 가 적어 둔 대로 되짚는다."""
    from PIL import Image
    import 원화진단 as JD
    R, cols = [], None
    for key, nick, grp, pngs, _, _ in JD.집합():
        if grp != "원화":
            continue
        ts, cs = [], []
        for v in ("front", "side", "back"):
            if v not in pngs:
                continue
            d = os.path.join(DST, "원화_" + key, v)
            for n in ("전", "후"):
                p = os.path.join(d, n, "regions.png")
                ts.append(np.asarray(Image.open(p).convert("RGB")) if os.path.exists(p)
                          else np.full((S, S, 3), 240, np.uint8))
                cs.append("%s 판 (%s)" % (v, n))
        if ts:
            R.append((nick, ts))
            cols = cs if cols is None or len(cs) > len(cols) else cols
    n = max(len(t) for _, t in R)
    R = [(k, t + [np.full((S, S, 3), 240, np.uint8)] * (n - len(t))) for k, t in R]
    LR.DC.grid(R, tuple((list(cols) + [""] * n)[:n]),
               "전처리 — 진짜 원화 넷, 배경 빼기 + 레벨 전 · 후 (정답 없음)",
               "각 판 쌍의 왼쪽이 전 · 오른쪽이 후. 배경이 통째로 한 판이 되는 것이 사라지는가",
               os.path.join(HERE, "out", "전처리_원화.png"), S=280)


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def selfcheck():
    rng = np.random.default_rng(0)
    im = rng.integers(60, 150, (64, 64, 3), dtype=np.uint8)      # 좁은 구간
    물 = np.ones((64, 64), bool)
    lv, (lo, hi) = 레벨(im, 물)
    g = lv.mean(2)
    assert g.min() < 20 and g.max() > 235, "레벨이 구간을 안 폈다 %.1f~%.1f" % (g.min(), g.max())
    # 배경 마스크 — 흰 바탕 가운데 검은 사각형
    im2 = np.full((64, 64, 3), 250, np.uint8)
    im2[20:44, 20:44] = 30
    물2 = 배경마스크(im2)
    assert 0.1 < 물2.mean() < 0.35, "배경 마스크 몫 %.3f" % 물2.mean()
    assert 물2[32, 32] and not 물2[2, 2]
    # 알파가 있으면 그걸 쓴다
    a = np.zeros((64, 64), np.uint8)
    a[10:20, 10:20] = 255
    assert 배경마스크(im2, a).sum() == 100
    print("  자가검사 통과 — 레벨 %.1f~%.1f -> 0~255 · 배경 마스크 물건몫 %.3f" % (lo, hi, 물2.mean()))


if __name__ == "__main__":
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass
    a = sys.argv[1] if len(sys.argv) > 1 else "검사"
    {"검사": selfcheck, "벤치": 벤치, "원화": 원화, "판정": verdict,
     "그림": 그림, "원화그림": 원화그림}[a]()
