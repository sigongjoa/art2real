# -*- coding: utf-8 -*-
"""**벤치 선 (게이트 A)** — 원화 선을 화가가 긋는 선으로 고치면 원화 판이 정답 면에 가까워지나 (2026-09-14).

    python 벤치선.py 검사          자가검사만
    python 벤치선.py 굽기 [n]      아직 없는 <케이스>_선2 를 n 장 굽는다 (시트.py --선 2 → 깊이.py)
    python 벤치선.py 입력          판 수 · 최대 판 몫 · 선 생존 · 정답 모서리 재현율/정밀도 -> out/기록/벤치선_입력.json
    python 벤치선.py 썸네일        옛/새 판과 판 분할 -> out/벤치선_썸네일.png
    python 벤치선.py [n]           판정 벤치 n 장 -> out/기록/벤치선_진행.jsonl
    python 벤치선.py 판정          -> out/기록/벤치선_<때>.json
    python 벤치선.py 그림          -> out/깊이색_벤치선.png

판정은 `claudedocs/plan_벤치선_20260914.md` 「판정」 절 그대로다 — 돌리기 전에 적었다.
옛 판 숫자(이진 · 오라클 · 원화판 뭉개기)는 `판별평면.py` 기록에서 읽고, 다시 돌리지 않는다.
"""
import gc
import json
import os
import subprocess
import sys
import time

import cv2
import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 판별평면 as P                       # HERE · chdir · H · W · O · SF 를 거기서 맞춘다

H, W, O, SF, HERE = P.H, P.W, P.O, P.SF, P.HERE
CASES, ANGULAR, PEOPLE = P.CASES, P.ANGULAR, P.PEOPLE
LAM = P.LAM
TAG = "벤치선 · 선2(보간가림 · 겹선30 · 6px · 면색120) · lam1.00 · 격자2 · 제부피 · 격자대조 (2026-09-14)"
PROG = os.path.join(HERE, "out", "기록", "벤치선_진행.jsonl")
INPUT = os.path.join(HERE, "out", "기록", "벤치선_입력.json")
NEW = lambda c: c + "_선2"
SPEC = {                                   # 이름: (어느 판, 깊이맵, 판, 뭉개기)
    "기준": ("선2", "파이프", None, None),
    "오라클": ("선2", "오라클", None, None),
    "상수·원화판": ("선2", "오라클", "원화판", "상수"),
    "적합·원화판": ("선2", "오라클", "원화판", "적합"),
    "격자·상수·원화판": ("선2", "오라클", "격자@원화판", "상수"),
    "격자·적합·원화판": ("선2", "오라클", "격자@원화판", "적합"),
    "격자·상수·정답면": ("옛", "오라클", "격자@정답면", "상수"),
}


# ───────────────────────────────────────────── 격자 대조군
def grid_labels(mask, n):
    """mask bbox 를 k×k 로 나눈 번호판. mask 안 칸 수가 n 에 가장 가까운 k — 선 위치 정보 0 인 같은 판 수."""
    ys, xs = np.nonzero(mask)
    y0, x0 = ys.min(), xs.min()
    hh, ww = ys.max() - y0 + 1, xs.max() - x0 + 1
    ids = lambda k: ((ys - y0) * k // hh) * k + (xs - x0) * k // ww + 1
    cnt = lambda k: len(np.unique(ids(k)))
    lo, hi = 1, int(max(hh, ww))
    while lo < hi:                                           # 칸 수는 k 에 거의 단조
        k = (lo + hi) // 2
        lo, hi = (k + 1, hi) if cnt(k) < n else (lo, k)
    k = min({max(lo - 1, 1), lo}, key=lambda k: abs(cnt(k) - n))
    out = np.zeros(mask.shape, np.float32)
    out[ys, xs] = ids(k)
    return out, cnt(k)


def n_parts(lab, mask):
    return int(len(np.unique(lab[mask & (lab > 0)])))


def post_for(case, truth, labels, mode, info):
    if labels in ("원화판", "정답면"):
        return P.post_for(case, truth, labels, mode)

    def post(v, d, dep):
        ref = H.load_labels(v, d, case=case) if labels == "격자@원화판" else P.facet_ids(truth, v)
        n = n_parts(ref, d)
        lab, got = grid_labels(d, n)
        info["%s_%s" % (labels, v)] = [n, got]
        return P.flatten(dep, lab, d, mode)
    return post


# ───────────────────────────────────────────── 굽기 · 입력
def model_of(case):
    p = os.path.join(HERE, "out", "모델", case + ".glb")
    return p if os.path.exists(p) else os.path.join(HERE, "out", "시트", case, "_model.glb")


def bake(n):
    todo = [c for c in CASES if not os.path.exists(os.path.join(HERE, "out", "깊이", NEW(c), "back", "depth.npy"))]
    for c in todo[:n]:
        t0 = time.time()
        for cmd in ([sys.executable, "시트.py", model_of(c), "--이름", NEW(c), "--선", "2"],
                    [sys.executable, "깊이.py", NEW(c)]):
            r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, encoding="utf-8")
            assert r.returncode == 0, "%s 실패: %s" % (cmd[1], (r.stderr or "")[-400:])
        a = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        b = trimesh.load(os.path.join(HERE, "out", "시트", NEW(c), "truth.glb"), force="mesh")
        assert np.array_equal(a.vertices, b.vertices) and np.array_equal(a.faces, b.faces), "%s: 정답 메시가 옛 판과 다르다" % c
        print("  %-28s 구움 · 정답 메시 같다 · %.0f초" % (c[:28], time.time() - t0), flush=True)
    print("  남은 것 %d 장" % max(len(todo) - n, 0))


def boundary(lab):
    b = np.zeros(lab.shape, bool)
    d = lab[:, 1:] != lab[:, :-1]
    b[:, 1:] |= d
    b[:, :-1] |= d
    d = lab[1:] != lab[:-1]
    b[1:] |= d
    b[:-1] |= d
    return b


def edge_pr(gt, got, mask, tol=3):
    """정답 번호 경계 대 잰 판 경계 — 재현율 · 정밀도 (±tol 화소). 실루엣 테두리는 뺀다."""
    inner = cv2.erode(mask.astype(np.uint8), np.ones((2 * tol + 3,) * 2, np.uint8)).astype(bool)
    g, s = boundary(gt) & inner, boundary(got) & inner
    dist = lambda b: cv2.distanceTransform((~b).astype(np.uint8), cv2.DIST_L2, 3)
    rec = float((dist(s)[g] <= tol).mean()) if g.any() else float("nan")
    pre = float((dist(g)[s] <= tol).mean()) if s.any() else float("nan")
    return rec, pre


def line_stats(png):
    """선(=20) 화소가 `깊이.py` 경로(흰 바탕 · LANCZOS 512 · median5)를 지나 lum<105 로 남는 몫 · 선 아닌 판의 lum<105 몫."""
    from PIL import Image, ImageFilter
    im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_UNCHANGED)
    al = im[:, :, 3] > 0
    a = im[:, :, 3:4].astype(np.float32) / 255
    rgb = (im[:, :, 2::-1] * a + 255 * (1 - a)).astype(np.uint8)
    line = (rgb == 20).all(2) & al
    small = Image.fromarray(rgb).resize((512, 512), Image.LANCZOS).filter(ImageFilter.MedianFilter(5))
    dark = np.asarray(small).astype(np.float32).mean(2) < 105
    ys, xs = np.nonzero(line)
    alive = float(dark[ys // 2, xs // 2].mean()) if len(ys) else float("nan")
    face = al & ~line
    return alive, float((rgb[face].mean(1) < 105).mean())


def input_table():
    rows = []
    for c in CASES:
        if not os.path.exists(os.path.join(HERE, "out", "깊이", NEW(c), "back", "depth.npy")):
            continue
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        for v in ("front", "back"):
            gt = P.facet_ids(truth, v)
            for tag, cc in (("옛", c), ("선2", NEW(c))):
                d = H.declutter(W.art_mask(os.path.join(HERE, "out", "시트", cc, "%s.png" % v)))
                lab512 = np.load(os.path.join(HERE, "out", "깊이", cc, v, "labels_grown.npy"))
                L = lab512[lab512 > 0].astype(np.int64)
                rec, pre = edge_pr(gt, H.load_labels(v, d, case=cc), d)
                alive, dark = line_stats(os.path.join(HERE, "out", "시트", cc, "%s.png" % v))
                rows.append({"case": c, "v": v, "판": tag, "판수": int(len(np.unique(L))),
                             "최대판몫": float(np.bincount(L).max() / max(len(L), 1)),
                             "선생존": alive, "어두운판몫": dark, "재현율": rec, "정밀도": pre})
        print("  %s" % c, flush=True)
    print("\n  %-26s %-5s %-4s %6s %7s %7s %7s %7s %7s" % ("케이스", "시점", "판", "판수", "최대판몫", "선생존", "어두운판", "재현율", "정밀도"))
    for r in rows:
        print("  %-26s %-5s %-4s %6d %7.3f %7.3f %7.3f %7.3f %7.3f" % (
            r["case"][:26], r["v"], r["판"], r["판수"], r["최대판몫"], r["선생존"], r["어두운판몫"], r["재현율"], r["정밀도"]))
    gate = input_gate(rows)
    print("\n  입력 관문 " + json.dumps(gate, ensure_ascii=False))
    json.dump({"때": time.strftime("%Y-%m-%d %H:%M"), "판": TAG, "관문": gate, "rows": rows},
              open(INPUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return gate


def input_gate(rows):
    """계획 「입력 관문」. 케이스·시점마다 한 줄씩을 중앙값으로."""
    med = lambda group, tag, k: float(np.nanmedian([r[k] for r in rows if r["case"] in group and r["판"] == tag]))
    out = {"각진 재현율 옛→새": [med(ANGULAR, "옛", "재현율"), med(ANGULAR, "선2", "재현율")],
           "각진 최대판몫 새": med(ANGULAR, "선2", "최대판몫"),
           "각진 판수 옛→새": [med(ANGULAR, "옛", "판수"), med(ANGULAR, "선2", "판수")],
           "인물 정밀도 옛→새": [med(PEOPLE, "옛", "정밀도"), med(PEOPLE, "선2", "정밀도")]}
    ok = (out["각진 재현율 옛→새"][1] > out["각진 재현율 옛→새"][0] and out["각진 최대판몫 새"] < 0.9
          and out["인물 정밀도 옛→새"][1] > out["인물 정밀도 옛→새"][0] - 0.1)
    out["통과"] = bool(ok)
    return out


def thumbs():
    import 깊이색 as DC
    rows = []
    for c in CASES:
        dd = os.path.join(HERE, "out", "깊이", NEW(c), "front", "regions.png")
        if not os.path.exists(dd):
            continue
        tiles = []
        for cc in (c, NEW(c)):
            im = cv2.imdecode(np.fromfile(os.path.join(HERE, "out", "시트", cc, "front.png"), np.uint8), cv2.IMREAD_UNCHANGED)
            a = im[:, :, 3:4].astype(np.float32) / 255
            tiles.append((im[:, :, 2::-1] * a + 255 * (1 - a)).astype(np.uint8))
        for cc in (c, NEW(c)):
            reg = cv2.imdecode(np.fromfile(os.path.join(HERE, "out", "깊이", cc, "front", "regions.png"), np.uint8), cv2.IMREAD_COLOR)
            tiles.append(np.ascontiguousarray(reg[:, :, ::-1]))
        rows.append((c[:14], tiles))
    DC.grid(rows, ["옛 원화", "새 원화 (선 2)", "옛 판 분할", "새 판 분할"],
            "벤치 선 — 원화 선을 고치면 판이 나뉘나 (front)",
            "새 선 = 보간 가림선 · 겹선 30° · 6px · 면색 120 이상. 판 분할 = art3d (512 · median5 · 선 문턱 105)",
            os.path.join(HERE, "out", "벤치선_썸네일.png"), S=260)
    print("  -> out/벤치선_썸네일.png")


# ───────────────────────────────────────────── 판정 벤치
def old_rows():
    got = {}
    for l in open(P.PROG, encoding="utf-8"):
        r = json.loads(l)
        if r.get("판") == P.TAG:
            got[r["case"]] = r
    return got


def one(case, old):
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", NEW(case), "truth.glb"), force="mesh")
    iou128, iou192 = O._iou_fn(truth), O._iou_fn(truth, P.P192)
    row, cache, plain, info = {"case": case, "판": TAG}, {}, None, {}
    for name, (sheet, which, labels, mode) in SPEC.items():
        cc = NEW(case) if sheet == "선2" else case
        post = post_for(cc, truth, labels, mode, info) if labels else None
        pl, vox, axes, _ = O.build(cc, truth, H.LAM if which == "파이프" else LAM, which, post=post)
        if plain is None:
            plain = pl
            row["이진"], row["이진·192"] = iou128(pl, axes), iou192(pl, axes)
        mesh = O.C.to_mesh(vox, axes)
        em, _ = H.even_control(plain, axes, mesh.volume, cache=cache)
        row[name], row[name + "·192"] = iou128(mesh, axes), iou192(mesh, axes)
        row["균일@" + name], row["균일@%s·192" % name] = iou128(em, axes), iou192(em, axes)
        row["찢김_" + name], row["조각_" + name] = SF.tear(vox), SF.pieces(vox)
        row["실루엣_" + name] = SF.sil_loss(vox, plain)
        del vox, mesh, em
        gc.collect()
        if name == "오라클":                                   # 배관 — 옛 판과 같아야 한다. 틀리면 나머지를 안 돈다
            o = old[case]
            row["배관차"] = max(abs(row["이진"] - o["이진"]), abs(row["오라클"] - o["오라클"]))
            if row["배관차"] >= 1e-4:
                print("  %s 배관 어긋남 %.6f — 멈춘다" % (case, row["배관차"]))
                break
    row["판수"] = info
    row["초"] = round(time.time() - t0, 1)
    return row


def judge(rows, old):
    bad = [r["case"] for r in rows if r["배관차"] >= 1e-4]
    if bad:
        return {"배관": "어긋남 — 숫자를 버린다", "어긋난 장": bad}
    rs = [r for r in rows if r["case"] in ANGULAR]
    n = len(rs)
    g = lambda k, src=None: np.array([(old[r["case"]] if src else r)[k] for r in rs])
    ceil = g("오라클") - g("이진")
    live = ceil > 0.01
    frac = lambda x: float(np.median((x - g("이진"))[live] / ceil[live]))
    beats = lambda a, b: all(d.mean() > 0 and (d > 0).sum() > n / 2
                             for d in (g(a) - g(b), g(a + "·192") - g(b + "·192")))
    out = {"배관": "통과", "천장 있는 장": int(live.sum())}
    for k in ("상수·원화판", "적합·원화판"):
        q = {"천장몫중앙": frac(g(k)), "옛 천장몫중앙": frac(g(k, "옛")), "격자 천장몫중앙": frac(g("격자·" + k)),
             "제대조군": beats(k, "균일@" + k), "격자대조군": beats(k, "격자·" + k)}
        q["통과"] = bool(q["천장몫중앙"] >= 0.5 and q["제대조군"] and q["격자대조군"])
        out[k] = q
    q1 = frac(g("격자·상수·정답면"))
    out["Q1+ 격자·상수·정답면 천장몫중앙"] = q1
    out["Q1+"] = ("Q1 을 결론으로 — 같은 판 수 격자는 못 닿는다" if q1 < 0.8 else
                  "Q1 을 고쳐 적는다 — 판을 잘게만 나누면 된다 (평면이라서가 아니다)")
    inp = json.load(open(INPUT, encoding="utf-8"))["관문"] if os.path.exists(INPUT) else {}
    more = inp.get("각진 판수 옛→새", [0, 0])
    ppl = [r for r in rows if r["case"] in PEOPLE]
    if ppl:
        out["QA2 인물 기준 |새−옛| 중앙"] = float(np.median([abs(r["기준"] - old[r["case"]]["기준"]) for r in ppl]))
    qa1 = out["상수·원화판"]["통과"] or out["적합·원화판"]["통과"]
    only_grid = any(out[k]["천장몫중앙"] >= 0.5 and out[k]["제대조군"] and not out[k]["격자대조군"]
                    for k in ("상수·원화판", "적합·원화판"))
    out["다음"] = ("게이트 B — 벤치 선이 병목이었다. _선2 판에서 옆판 평면 후보" if qa1 else
                  "결론 없음 — 판 수만 늘면 오른다 (격자 대조군에 짐)" if only_grid else
                  "멈추고 보고 — 판은 늘었는데 정답 면과 어긋난다" if more[1] > more[0] else
                  "게이트 A2 — 선이 art3d 에 안 닿았다 (분할기)")
    return out


def report(rows, old):
    names = ["이진", "오라클", "상수·원화판", "적합·원화판", "격자·상수·원화판", "격자·적합·원화판", "격자·상수·정답면"]
    print("\n  케이스별 IoU (격자128) · 괄호 = 옛 판 (판별평면)")
    for r in rows:
        o = old[r["case"]]
        print("  %-26s " % r["case"][:26] + " · ".join(
            "%s %.4f" % (k, r[k]) + (" (%.4f)" % o[k] if k in ("상수·원화판", "적합·원화판") else "") for k in names)
            + ("" if r["case"] in ANGULAR else "  (참고)"))
    v = judge(rows, old)
    print("\n  판정\n  " + json.dumps(v, ensure_ascii=False, indent=1).replace("\n", "\n  "))
    p = os.path.join(HERE, "out", "기록", "벤치선_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"때": time.strftime("%Y-%m-%d %H:%M"), "판": TAG, "케이스": CASES, "판정": v, "rows": rows},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  기록 -> %s" % os.path.relpath(p, HERE))


def figure(cases=("cloak_Chest_O72u4Drp8k", "cape_Hat_Stylised_lNN3PlrjSa", "스캔_Victor_Reversible_Bookend",
                  "mech_Drill_8uBbH7Dvmb")):
    import 깊이색 as DC
    import 앨리어싱 as AL
    cols = ["정답", "이진", "옛 적합·원화판", "새 적합·원화판", "격자·적합·원화판", "오라클"]
    what = {"옛 적합·원화판": ("옛", "원화판", "적합"), "새 적합·원화판": ("선2", "원화판", "적합"),
            "격자·적합·원화판": ("선2", "격자@원화판", "적합"), "오라클": ("선2", None, None), "이진": ("선2", None, None)}
    rows = []
    for case in cases:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        M = {}
        for name in cols[1:]:
            sheet, labels, mode = what[name]
            cc = NEW(case) if sheet == "선2" else case
            post = post_for(cc, truth, labels, mode, {}) if labels else None
            pl, vox, axes, _ = O.build(cc, truth, LAM, "오라클", post=post)
            M[name] = O.C.to_mesh(pl if name == "이진" else vox, axes)
        fr, dr = AL.frame_of(M["이진"], 45), DC.depth_range(M["이진"], 45)
        tiles = [DC.colorize(DC.zbuffer(truth, 45, fr, 360), dr)]
        tiles += [DC.colorize(DC.zbuffer(M[k], 45, fr, 360), dr) for k in cols[1:]]
        rows.append((case[:14], tiles))
        print("  %s 그림" % case, flush=True)
    DC.grid(rows, cols, "벤치 선 — 선을 고친 원화 판으로 정답 깊이를 뭉개면 (45도 · lam 1.00)",
            "옛/새 적합·원화판 = 원화 판마다 평면 적합 · 격자 = 새 판과 같은 판 수의 격자 (선 위치 정보 0). 첫 칸이 정답",
            os.path.join(HERE, "out", "깊이색_벤치선.png"), S=300)


def selfcheck():
    P.selfcheck()
    m = np.zeros((100, 60), bool)
    m[10:90, 5:55] = True
    for n in (1, 7, 40, 500):
        lab, got = grid_labels(m, n)
        assert (lab > 0).sum() == m.sum() and n_parts(lab, m) == got, "격자: mask 를 다 안 덮거나 칸 수가 틀렸다"
        assert abs(got - n) <= max(0.2 * n, 2 * np.sqrt(n) + 1), "격자 칸 수 %d 가 %d 에서 멀다" % (got, n)
    a = np.zeros((40, 40), np.int32)
    a[:, 20:] = 1
    b = np.zeros((40, 40), np.int32)
    b[:, 21:] = 1
    mm = np.ones((40, 40), bool)
    assert edge_pr(a, a, mm) == (1.0, 1.0) and edge_pr(a, b, mm) == (1.0, 1.0), "경계 한 화소 어긋남은 허용 안이다"
    rec, pre = edge_pr(a, np.zeros_like(a), mm)
    assert rec == 0.0 and np.isnan(pre), "판 하나는 재현율 0"
    print("  자가검사 통과 — 격자 칸 수 · 경계 재현율/정밀도")


def main():
    H.register_sheets()
    selfcheck()
    arg = sys.argv[1] if len(sys.argv) > 1 else "1"
    if arg == "검사":
        return
    if arg == "굽기":
        return bake(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    if arg == "입력":
        return input_table()
    if arg == "썸네일":
        return thumbs()
    if arg == "그림":
        return figure()
    old = old_rows()
    done = {}
    if os.path.exists(PROG):
        for l in open(PROG, encoding="utf-8"):
            r = json.loads(l)
            if r.get("판") == TAG:
                done[r["case"]] = r
    if arg != "판정":
        order = ["cloak_Chest_O72u4Drp8k"] + [c for c in CASES if c != "cloak_Chest_O72u4Drp8k"]   # 첫 장은 배관용 열린 궤짝
        for c in [c for c in order if c not in done][:int(arg)]:
            r = one(c, old)
            with open(PROG, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            done[c] = r
            if r["배관차"] >= 1e-4:
                return
            print("  %-26s 이진 %.4f · 오라클 %.4f · 적합·원화판 %.4f (옛 %.4f) · 격자 %.4f · 배관차 %.1e · %.0f초" % (
                c[:26], r["이진"], r["오라클"], r["적합·원화판"], old[c]["적합·원화판"], r["격자·적합·원화판"],
                r["배관차"], r["초"]), flush=True)
    rows = [done[c] for c in CASES if c in done]
    if len(rows) == len(CASES) or arg == "판정":
        report(rows, old)
    else:
        print("  %d/%d 장 — 다시 돌리면 이어 돈다" % (len(rows), len(CASES)))


if __name__ == "__main__":
    main()
