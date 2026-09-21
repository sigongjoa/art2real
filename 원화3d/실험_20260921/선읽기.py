# -*- coding: utf-8 -*-
"""**우리 선 추출기가 오목 크리스를 찾나** — 정답표에 대고 채점한다 (2026-09-21).

    python 선읽기.py 검사       자가검사 (틀 맞춤 · 정답표 짝 · 채점 자)
    python 선읽기.py [n]        아직 안 한 장 n 개 -> out/명암판/ · out/선읽기/ · 진행 jsonl
    python 선읽기.py 판정       -> out/기록/선읽기_<때>.json
    python 선읽기.py 그림       -> out/선읽기_접촉지.png
    python 선읽기.py 원화       진짜 원화 넷 (정답표 없음 · 그림만) -> out/선읽기_원화.png

어제 `선채널.py` 가 정답 메시에서 **선의 정답표**를 구웠다 (외곽/가림/볼록크리스/**오목크리스**).
오늘은 그 정답표에 대고 `도안/도구/art3d.py`(스킬에서 복사한 추출기)를 **채점한다.**

**벤치 입력이 못 쓴다는 것을 먼저 쟀다** — 시트 3 판은 고유색이 3~4 개뿐이고 선이 없다
(원화진단 음영단수 중앙 3 · 도형은 1). 그래서 추출기에 줄 **명암 판**을 정답 메시에서 만든다.
셀 4 단 양자화 · **고정 문턱**(90 · 140 · 190) · `폴리싱.shaded` 의 빛 그대로.

**문턱을 돌리기 전에 적는다.**

    Q1  오목 크리스 재현율 중앙 >= 0.50              절반은 찾는다
    Q2  볼록 − 오목 재현율 중앙 <= 0.20              (크면 톤 기반은 볼록 쪽으로 치우친다)
    Q3  추출기가 **Canny 대조군**을 오목 재현율에서 이긴다 (중앙 차 > 0)

재현율 = 정답 선 화소 중 추출 경계가 3 화소 안에 있는 몫 · 정밀도 = 그 반대.
**자는 안 건드린다** — 목적함수도 판정 표도 그대로다. 이건 추출기 채점이다.
"""
import json
import os
import subprocess
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260920")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260919")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260916")
import 선채널 as LC
import 도안천장 as DA
import 폴리싱 as PL
CG, ME = DA.CG, DA.ME
H, W, J, DG, DC = DA.H, DA.W, DA.J, DA.DG, DA.DC
HERE = DA.HERE
OUT = os.path.join(HERE, "out", "기록")
CEL = os.path.join(HERE, "out", "명암판")
EXT = os.path.join(HERE, "out", "선읽기")
도구 = r"G:\art2real\원화3d\도안\도구\art3d.py"
PROG = os.path.join(OUT, "선읽기_진행.jsonl")
TAG = "선읽기 v1 · 명암판(셀4단) -> art3d.py -> 선채널 정답표 채점 · Canny 대조 (2026-09-21)"

S = 512
톤 = (90, 140, 190)                       # 셀 4 단. 한 케이스 보고 고른 값이 아니라 밝기 고정 문턱이다
셀색 = np.array([[40, 40, 40], [110, 110, 110], [175, 175, 175], [235, 235, 235]], np.uint8)
바탕 = 247
TOL = 3                                   # 화소. 재현율 · 정밀도의 허용 거리
뷰 = (("front", 0, 0), ("d45", 45, 0), ("위45", 45, 45))
Q1문턱, Q2차 = 0.50, 0.20
라벨이름 = LC.라벨이름


# ── 명암 판 ──────────────────────────────────────────────────────────────────

def 명암판(mesh, az, el, s=S):
    """정답 메시 -> 셀 4 단 명암 판. `선채널` 과 **같은 틀 · 같은 해상도**라 화소가 맞는다."""
    m = LC.기울(mesh, el)
    fr = ME.AL.frame_of(m, az)
    img = PL.shaded(m, az, fr, S=s)
    g = img.mean(2)
    물 = g < (바탕 - 1)
    q = np.digitize(g, 톤)
    out = np.full((s, s, 3), 바탕, np.uint8)
    out[물] = 셀색[np.clip(q[물], 0, 3)]
    return out, 물


# ── 채점 ─────────────────────────────────────────────────────────────────────

def 경계(lab):
    """라벨 맵 -> 경계 화소 (이웃과 번호가 다른 곳)."""
    b = np.zeros(lab.shape, bool)
    d = lab[:, :-1] != lab[:, 1:]
    b[:, :-1] |= d
    b[:, 1:] |= d
    d = lab[:-1] != lab[1:]
    b[:-1] |= d
    b[1:] |= d
    return b


def 가까움(a, b, tol=TOL):
    """a 화소 중 b 에서 tol 안에 있는 몫."""
    from scipy import ndimage
    if not a.any():
        return None
    if not b.any():
        return 0.0
    d = ndimage.distance_transform_edt(~b)
    return round(float((d[a] <= tol).mean()), 4)


def 채점(뽑, 정, 있):
    """뽑 = 추출 경계(bool) · 정 = 정답 라벨맵(uint8) · 있 = 물건 화소."""
    뽑 = 뽑 & 있
    선 = (정 > 0) & 있
    r = {"정밀도": 가까움(뽑, 선), "뽑은화소": int(뽑.sum())}
    for k in range(1, 5):
        r["재현_" + 라벨이름[k]] = 가까움((정 == k) & 있, 뽑)
    return r


def canny(cel):
    import cv2
    g = cv2.cvtColor(cel, cv2.COLOR_RGB2GRAY)
    return cv2.Canny(g, 50, 150) > 0


# ── 한 장 ────────────────────────────────────────────────────────────────────

def 사례():
    return [c for c in LC.rows() if os.path.exists(os.path.join(HERE, "out", "선채널", c, "front.npy"))]


def one(case):
    from PIL import Image
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    r = {"case": case, "판": TAG, "뷰": {}}
    for 이름, az, el in 뷰:
        cel, 있 = 명암판(truth, az, el)
        d = os.path.join(CEL, case)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "%s.png" % 이름)
        Image.fromarray(cel).save(p)
        o = os.path.join(EXT, case, 이름)
        os.makedirs(o, exist_ok=True)
        subprocess.run([sys.executable, 도구, p, "--out", o, "--scale", str(S)],
                       capture_output=True, timeout=900)
        정 = np.load(os.path.join(HERE, "out", "선채널", case, "%s.npy" % 이름))
        lp = os.path.join(o, "labels_grown.npy")
        if not os.path.exists(lp):
            r["뷰"][이름] = {"실패": "추출기가 labels_grown 을 안 냈다"}
            continue
        lab = np.load(lp)
        assert lab.shape == 정.shape, "틀이 안 맞는다 %s vs %s" % (lab.shape, 정.shape)
        r["뷰"][이름] = {"추출기": 채점(경계(lab), 정, 있), "Canny": 채점(canny(cel), 정, 있),
                       "판수": int(len(np.unique(lab)) - 1)}
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
    for c in [x for x in 사례() if x not in rows()][:n]:
        r = one(c)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        v = [r["뷰"][k].get("추출기", {}).get("재현_오목크리스") for k, _, _ in 뷰]
        v = [x for x in v if x is not None]
        print("  %-38s 오목재현 %s · %.0f초"
              % (c, "%.3f" % np.mean(v) if v else "-", r["초"]), flush=True)


# ── 판정 ─────────────────────────────────────────────────────────────────────

def _avg(r, who, key):
    v = [r["뷰"][k].get(who, {}).get(key) for k, _, _ in 뷰]
    v = [x for x in v if x is not None]
    return round(float(np.mean(v)), 4) if v else None


def verdict():
    rs = rows()
    cs = sorted(rs)
    T = {c: {"오목": _avg(rs[c], "추출기", "재현_오목크리스"),
             "볼록": _avg(rs[c], "추출기", "재현_볼록크리스"),
             "외곽": _avg(rs[c], "추출기", "재현_외곽선"),
             "가림": _avg(rs[c], "추출기", "재현_가림선"),
             "정밀도": _avg(rs[c], "추출기", "정밀도"),
             "C오목": _avg(rs[c], "Canny", "재현_오목크리스"),
             "C정밀도": _avg(rs[c], "Canny", "정밀도")} for c in cs}
    오 = [T[c]["오목"] for c in cs if T[c]["오목"] is not None]
    볼 = [T[c]["볼록"] for c in cs if T[c]["볼록"] is not None]
    차 = [T[c]["볼록"] - T[c]["오목"] for c in cs if None not in (T[c]["오목"], T[c]["볼록"])]
    대 = [T[c]["오목"] - T[c]["C오목"] for c in cs if None not in (T[c]["오목"], T[c]["C오목"])]
    med = lambda x: round(float(np.median(x)), 4) if x else None
    v = {"판": TAG, "때": time.strftime("%Y%m%d_%H%M"), "장": len(cs),
         "안잰": [c for c in 사례() if c not in rs],
         "Q1": {"문턱": "오목 재현율 중앙 >= %g" % Q1문턱, "중앙": med(오),
                "통과": bool(오 and np.median(오) >= Q1문턱)},
         "Q2": {"문턱": "볼록 − 오목 재현율 중앙 <= %g" % Q2차, "중앙": med(차),
                "통과": bool(차 and np.median(차) <= Q2차)},
         "Q3": {"문턱": "추출기 − Canny 오목 재현율 중앙 > 0", "중앙": med(대),
                "승": int(sum(1 for x in 대 if x > 0)), "장": len(대),
                "통과": bool(대 and np.median(대) > 0)},
         "곁": {"볼록재현 중앙": med(볼),
                "정밀도 중앙": med([T[c]["정밀도"] for c in cs if T[c]["정밀도"] is not None]),
                "Canny 정밀도 중앙": med([T[c]["C정밀도"] for c in cs if T[c]["C정밀도"] is not None])},
         "표": T}
    p = os.path.join(OUT, "선읽기_%s.json" % v["때"])
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    f = lambda x: "%7.3f" % x if x is not None else "      -"
    print("  %-38s %7s %7s %7s %7s %7s %7s" % ("장", "오목", "볼록", "외곽", "가림", "정밀도", "C오목"))
    for c in cs:
        t = T[c]
        print("  %-38s %s %s %s %s %s %s" % (c[:38], f(t["오목"]), f(t["볼록"]), f(t["외곽"]),
                                             f(t["가림"]), f(t["정밀도"]), f(t["C오목"])))
    for k in ("Q1", "Q2", "Q3", "곁"):
        print("\n  %s %s" % (k, json.dumps(v[k], ensure_ascii=False)))
    print("\n  ->", p)
    return v


# ── 그림 ─────────────────────────────────────────────────────────────────────

def 그림(cases=None):
    from PIL import Image
    rs = rows()
    cs = cases or [c for c in ("cloak_Chest_Closed_AngpV0HxD8", "mech_Drill_8uBbH7Dvmb",
                               "monster_Mimic_B8HrWzkuNp", "wizard_Evil_Wizard_bdxawstqtq")
                   if c in rs]
    R = []
    이름 = "위45"
    for c in cs:
        cel = np.asarray(Image.open(os.path.join(CEL, c, "%s.png" % 이름)).convert("RGB"))
        정 = np.load(os.path.join(HERE, "out", "선채널", c, "%s.npy" % 이름))
        rp = os.path.join(EXT, c, 이름, "regions.png")
        reg = np.asarray(Image.open(rp).convert("RGB")) if os.path.exists(rp) \
            else np.full(cel.shape, 240, np.uint8)
        lab = np.load(os.path.join(EXT, c, 이름, "labels_grown.npy"))
        b = 경계(lab)
        뽑 = np.full(cel.shape, 247, np.uint8)
        뽑[b] = (20, 20, 20)
        겹 = LC.색칠(정).copy()
        겹[b & (정 == 0)] = (150, 150, 150)
        t = rs[c]["뷰"][이름].get("추출기", {})
        g = lambda k: "%.2f" % t[k] if t.get(k) is not None else "-"
        R.append(("%s\n오목 %s · 볼록 %s" % (c[:20], g("재현_오목크리스"), g("재현_볼록크리스")),
                  [cel, reg, 뽑, LC.색칠(정), 겹]))
    DC.grid(R, ("명암 판 (셀 4단 · 추출기 입력)", "추출기가 나눈 판", "추출기 경계", "정답표 (선채널)", "겹쳐 보기"),
            "선 읽기 — 우리 추출기가 오목 크리스를 찾나 (위에서 45°)",
            "정답표: 검정 외곽 · 빨강 가림 · 파랑 볼록 크리스 · **주황 오목 크리스** · 겹쳐 보기의 회색 = 추출기만 그은 선",
            os.path.join(HERE, "out", "선읽기_접촉지.png"), S=340)


def 원화():
    """진짜 원화 넷 — **정답표가 없다.** 눈으로 보는 것뿐이다."""
    from PIL import Image
    import 원화진단 as JD
    R, cs = [], []
    for key, nick, grp, pngs, _, _ in JD.집합():
        if grp != "원화":
            continue
        ts, cc = [], []
        for v in ("front", "side", "back"):
            if v not in pngs:
                continue
            o = os.path.join(EXT, "원화_" + key, v)
            os.makedirs(o, exist_ok=True)
            subprocess.run([sys.executable, 도구, pngs[v], "--out", o, "--scale", str(S)],
                           capture_output=True, timeout=1800)
            src = np.asarray(Image.open(pngs[v]).convert("RGB").resize((S, S)))
            rp = os.path.join(o, "regions.png")
            ts += [src, np.asarray(Image.open(rp).convert("RGB")) if os.path.exists(rp)
                   else np.full((S, S, 3), 240, np.uint8)]
            cc += ["%s 원화" % v, "%s 판" % v]
        if ts:
            R.append((nick, ts))
            cs = cc if len(cc) > len(cs) else cs
            print("  %s 판 %d" % (nick, len(ts) // 2), flush=True)
    n = max(len(t) for _, t in R)
    R = [(k, t + [np.full((S, S, 3), 240, np.uint8)] * (n - len(t))) for k, t in R]
    DC.grid(R, tuple((cs + [""] * n)[:n]),
            "선 읽기 — 진짜 원화 넷 (정답표가 없다 · 눈으로 보는 것뿐)",
            "왼쪽이 사람이 그린 판 · 오른쪽이 추출기가 나눈 판. 벤치와 달리 여기엔 채점할 정답이 없다",
            os.path.join(HERE, "out", "선읽기_원화.png"), S=300)


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def selfcheck():
    c = 사례()[0]
    truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
    cel, 있 = 명암판(truth, 45, 45)
    정 = np.load(os.path.join(HERE, "out", "선채널", c, "위45.npy"))
    assert cel.shape[:2] == 정.shape, "틀이 안 맞는다"
    선있 = 정 > 0
    겹 = float((선있 & 있).sum() / max(선있.sum(), 1))
    assert 겹 > 0.95, "정답 선의 %.3f 만 명암판 안에 있다 — 틀이 어긋났다" % 겹
    assert 가까움(선있, 선있) == 1.0
    assert 가까움(선있, np.zeros_like(선있)) == 0.0
    lab = np.arange(16).reshape(4, 4) // 2           # 세로로 두 갈래
    assert 경계(lab).sum() > 0
    print("  자가검사 통과 — %s · 틀 겹침 %.3f · 셀 %d 색"
          % (c, 겹, len(np.unique(cel.reshape(-1, 3), axis=0))))


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
    elif a == "원화":
        원화()
    else:
        run(int(a))
