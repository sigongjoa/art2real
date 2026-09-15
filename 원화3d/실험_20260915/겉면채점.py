# -*- coding: utf-8 -*-
"""**속을 채운 정답으로 다시 잰다** (2026-09-15).

    python 겉면채점.py 검사
    python 겉면채점.py [케이스...]     기본 VRoid 11장 -> out/기록/겉면채점.json
    python 겉면채점.py 벤치 [n]         실물 29장 판정용 (S1) -> out/기록/겉면채점_벤치_진행.jsonl
    python 겉면채점.py 벤치판정 [뺄 장]  -> out/기록/겉면채점_벤치_<때>.json
    python 겉면채점.py 안보임           3판에서 안 보이는 빈 곳 U 대 층 채움 (사후) -> out/기록/겉면채점_안보임.json
    python 겉면채점.py 그림            옆 단면 -> out/겉면채점_단면.png
    python 겉면채점.py 뷰어 실험_20260915/치마속검수대_틀.html <출력.html>   3D 뷰어 (정답 · 속채움 · hull, gzip 메시 1.7 MB)

사람 판단 (09-15): 레진 굿즈 원형은 치마 속이 안 보여도 된다 — 차 있어도 팔린다.
그런데 정답 메시는 치마 속이 비어 있어 hull 이 채운 속을 **틀린 부피**로 센다.
그래서 정답을 **높이마다 닫힌 구멍을 채운 것**(치마 고리 속 · 소매 속)으로 바꿔 같은 판본을 다시 잰다.

    속채운정답   정답 복셀을 z 층마다 `binary_fill_holes` — 층 안에서 테두리로 둘러싸인 빈 곳만 찬다.
                다리 사이처럼 밖과 이어진 틈은 안 찬다
"""
import json
import os
import sys

import numpy as np
import trimesh
from scipy import ndimage

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "실험_20260913"))
os.chdir(HERE)
import 오라클 as O
import 정답 as J
from 재질 import CASES

OUTJ = os.path.join(HERE, "out", "기록", "겉면채점.json")
SPEC = (("이진", 1.00, "타원", 0), ("타원1.00", 1.00, "타원", 1), ("오라클1.00", 1.00, "오라클", 1))


def fill_slices(T):
    """z 층(마지막 축)마다 닫힌 구멍을 채운다."""
    out = T.copy()
    for k in range(T.shape[2]):
        if T[:, :, k].any():
            out[:, :, k] = ndimage.binary_fill_holes(T[:, :, k])
    return out


def iou(A, B):
    return float((A & B).sum() / max((A | B).sum(), 1))


def run(cases):
    out = json.load(open(OUTJ, encoding="utf-8")) if os.path.exists(OUTJ) else {}
    for c in cases:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        T, ot = J.grid(truth)
        row = {}
        builds = {}
        for name, lam, which, pick in SPEC:
            if which not in builds:
                builds[which] = O.build(c, truth, lam, which)
            plain, deep, axes, _ = builds[which]
            G, og = J.grid(O.C.to_mesh(deep if pick else plain, axes))
            A, B = J.common(T, ot, G, og)
            F = fill_slices(A)
            row[name] = {"빈정답": round(iou(A, B), 4), "속채운정답": round(iou(F, B), 4)}
        row["속채움/정답 부피"] = round(float(F.sum() / A.sum()), 3)
        out[c] = row
        print("  %-24s 속채움 %.2f배 · " % (c[:24], row["속채움/정답 부피"]) +
              " · ".join("%s %.3f → %.3f" % (k, v["빈정답"], v["속채운정답"]) for k, v in row.items() if isinstance(v, dict)), flush=True)
        json.dump(out, open(OUTJ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  -> %s" % OUTJ)


def figure(cases):
    """케이스마다 옆에서 본 가운데 단면 (x 가운데 층) — 회색 정답 · 파랑 속채움으로 더해진 곳 · 빨강 선 타원1.00 hull."""
    import cv2
    rows = []
    for c in cases:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        T, ot = J.grid(truth)
        plain, deep, axes, _ = O.build(c, truth, 1.00, "타원")
        G, og = J.grid(O.C.to_mesh(deep, axes))
        A, B = J.common(T, ot, G, og)
        F = fill_slices(A)
        tiles = []
        for x in (A.shape[0] // 2, int(A.shape[0] * 0.40)):       # 가운데 · 조금 옆 (다리 하나를 지나는 층)
            a, f, b = A[x].T[::-1], F[x].T[::-1], B[x].T[::-1]    # (y 깊이, z 위) -> 화면 (행=위, 열=깊이)
            im = np.full(a.shape + (3,), 255, np.uint8)
            im[f & ~a] = (235, 170, 90)                          # BGR 파랑 — 속채움
            im[a] = (150, 150, 150)
            edge = b & ~ndimage.binary_erosion(b)
            im[edge] = (30, 30, 220)
            tiles.append(cv2.resize(im, (im.shape[1] * 4, im.shape[0] * 4), interpolation=cv2.INTER_NEAREST))
        h = max(t.shape[0] for t in tiles)
        row = np.hstack([cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, 12, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for t in tiles])
        cv2.putText(row, c[:24], (8, 28), 0, 0.8, (0, 0, 0), 2)
        rows.append(row)
    w = max(r.shape[1] for r in rows)
    img = np.vstack([cv2.copyMakeBorder(r, 0, 12, 0, w - r.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for r in rows])
    p = os.path.join(HERE, "out", "겉면채점_단면.png")
    cv2.imencode(".png", img)[1].tofile(p)
    print("  -> %s" % p)


BPROG = os.path.join(HERE, "out", "기록", "겉면채점_벤치_진행.jsonl")
BTAG = "겉면채점 벤치 · 실물29 · 이진/타원1.00/오라클1.00/균일@타원1.00 · 빈/속채운 정답 · 격자128·192 (2026-09-15)"
VARS = ("이진", "타원1.00", "오라클1.00", "균일@타원1.00")


def bench_cases():
    return [c["name"] for c in json.load(open(os.path.join(HERE, "벤치.json"), encoding="utf-8"))["cases"]]


def bench_rows():
    rows = {}
    if os.path.exists(BPROG):
        for line in open(BPROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == BTAG:
                rows[r["case"]] = r
    return rows


def bench_one(c):
    """판본 넷 × 정답 둘 × 격자 둘. 값은 [속 빈 정답, 속 채운 정답]."""
    import hull as H
    import win as W
    import time
    t0 = time.time()
    truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
    plain, deep, axes, _ = O.build(c, truth, 1.00, "타원")
    _, odeep, oaxes, _ = O.build(c, truth, 1.00, "오라클")
    mt = O.C.to_mesh(deep, axes)
    em, _ = H.even_control(plain, axes, mt.volume)
    meshes = {"이진": O.C.to_mesh(plain, axes), "타원1.00": mt, "오라클1.00": O.C.to_mesh(odeep, oaxes), "균일@타원1.00": em}
    row = {"case": c, "판": BTAG}
    for tag, p in (("", J.PITCH), ("·192", (W.U1 - W.U0) / 192.0)):
        T, ot = J.grid(truth, p)
        for name, m in meshes.items():
            G, og = J.grid(m, p)
            A, B = J.common(T, ot, G, og)
            F = fill_slices(A)
            row[name + tag] = [round(iou(A, B), 5), round(iou(F, B), 5)]
        row["속채움배" + tag] = round(float(F.sum() / A.sum()), 4)
    row["초"] = round(time.time() - t0, 1)
    return row


def bench(n):
    done = bench_rows()
    todo = [c for c in bench_cases() if c not in done][:n]
    for c in todo:
        r = bench_one(c)
        with open(BPROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  %-28s 속채움 %.2f배 · " % (c[:28], r["속채움배"]) +
              " · ".join("%s %.3f→%.3f" % (k, r[k][0], r[k][1]) for k in VARS) + " · %.0f초" % r["초"], flush=True)
    print("  남은 것 %d 장" % (len(bench_cases()) - len(bench_rows())))


def unseen(cases):
    """**검토가 낸 가장 싼 검사 (사후).** 정답 복셀에서 앞 · 뒤 · 옆 광선이 처음 닿기 전 빈 칸은 보인다.
    U = 세 광선 어디서도 안 보이는 빈 칸. 속채움 F 는 U 안에 있어야 하고(assert), U 중 F 가 못 채운 몫을 적는다 — 소매 속 · 격자 새기."""
    import win as W
    out = {}
    for c in cases:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        row = {}
        for tag, p in (("128", J.PITCH), ("192", (W.U1 - W.U0) / 192.0)):
            T, _ = J.grid(truth, p)
            T = np.pad(T, 1)
            F = fill_slices(T)
            hit = lambda ax, rev: (np.flip(np.cumsum(np.flip(T, ax), ax), ax) if rev else np.cumsum(T, ax)) > 0
            seen = ~hit(1, False) | ~hit(1, True) | ~hit(0, False)        # 앞(−y 쪽에서) · 뒤 · 옆 한쪽
            # 광선이 물건을 지나기 전 칸만 보인다 — 누적합이 0 인 칸이 카메라와 물건 사이
            U = ~T & ~seen
            added = F & ~T
            assert not (added & ~U).any(), "%s: 속채움이 보이는 칸을 채웠다 (%d 칸)" % (c, int((added & ~U).sum()))
            v = float(T.sum())
            row[tag] = {"안보임/정답": round(U.sum() / v, 3), "속채움/정답": round(added.sum() / v, 3), "못채운안보임/정답": round((U & ~F).sum() / v, 3)}
        out[c] = row
        print("  %-28s 128 %s · 192 %s" % (c[:28], row["128"], row["192"]), flush=True)
    p = os.path.join(HERE, "out", "기록", "겉면채점_안보임.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  -> %s" % p)


def bench_judge(exclude=()):
    """계획 `plan_속채움표준_20260915.md` 「판정」 절 그대로. `exclude` 는 사후로 뺀 장 (검토: `소체` = base_female 중복)."""
    import time
    rows = bench_rows()
    cases = [c for c in bench_cases() if c not in exclude]
    if len([c for c in cases if c in rows]) < len(cases):
        print("  %d/%d 장 — 판정 안 함" % (len(rows), len(cases)))
        return
    rs = [rows[c] for c in cases]
    n = len(rs)
    ceil = {}
    for line in open(os.path.join(HERE, "out", "기록", "천장_실물.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        ceil[r["case"]] = r
    diffs = [abs(rows[c][k][0] - ceil[c][k]["iou"]) for c in cases if c in ceil for k in ("이진", "타원1.00", "오라클1.00")]
    out = {"판": BTAG, "장": n, "배관 최대차": round(max(diffs), 4), "배관 비교 장": len([c for c in cases if c in ceil])}
    if max(diffs) >= 0.002:
        out["배관"] = "어긋남 — 숫자를 버린다"
    else:
        out["배관"] = "통과"
        g = lambda k, t, j: np.array([r[k + t][j] for r in rs])
        med = lambda k, t, j: float(np.median(g(k, t, j)))
        for j, truthname in ((0, "속 빈 정답"), (1, "속 채운 정답")):
            blk = {}
            for t in ("", "·192"):
                d = g("타원1.00", t, j) - g("균일@타원1.00", t, j)
                blk["격자" + (t or "128")] = {
                    "중앙 이진 · 타원 · 오라클": [round(med(k, t, j), 4) for k in ("이진", "타원1.00", "오라클1.00")],
                    "오라클≤이진 장": int((g("오라클1.00", t, j) <= g("이진", t, j)).sum()),
                    "타원−균일 평균 · 이긴 장": [round(float(d.mean()), 4), int((d > 0).sum())],
                    "대조군 통과": bool(d.mean() > 0 and (d > 0).sum() > n / 2),
                    "오라클−이진 중앙": round(float(np.median(g("오라클1.00", t, j) - g("이진", t, j))), 4),
                    "타원−이진 중앙": round(float(np.median(g("타원1.00", t, j) - g("이진", t, j))), 4)}
            out[truthname] = blk
        F, E = out["속 채운 정답"], out["속 빈 정답"]
        q1 = all(a < b < c for a, b, c in (F[k]["중앙 이진 · 타원 · 오라클"] for k in F))
        q2 = all(F[k]["대조군 통과"] for k in F) == all(E[k]["대조군 통과"] for k in E) and \
             all(F[k]["대조군 통과"] == E[k]["대조군 통과"] for k in F)
        q3 = all(F[k]["오라클−이진 중앙"] >= 0.05 and F[k]["타원−이진 중앙"] > 0 for k in F)
        out.update({"Q1 순서": q1, "Q2 판정 보존": q2, "Q3 분해능": q3,
                    "속채움배 중앙 · 최대": [float(np.median([r["속채움배"] for r in rs])), max((r["속채움배"], r["case"]) for r in rs)],
                    "다음": "속 채운 정답을 표준 채점으로" if (q1 and q2 and q3) else "표준으로 안 올린다 — 결과만 적는다"})
    out["뺀 장"] = list(exclude)
    path = os.path.join(HERE, "out", "기록", "겉면채점_벤치_%s%s.json" % (time.strftime("%Y%m%d_%H%M"), "_뺌" if exclude else ""))
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print("  -> %s" % path)


def viewer(cases, template, dst):
    """3D 뷰어 데이터 — 케이스마다 정답 메시 · 속채움으로 더해진 복셀 면 · 타원1.00 hull 복셀 면.
    정점은 케이스 bbox 로 16비트 양자화 · 면은 32비트 · base64. `template` 의 `/*DATA*/null` 을 바꿔 `dst` 에 쓴다."""
    import base64
    import gzip
    from skimage import measure
    enc = lambda a: base64.b64encode(gzip.compress(a.tobytes(), 9)).decode()     # 뷰어가 DecompressionStream 으로 푼다
    scores = json.load(open(OUTJ, encoding="utf-8"))
    res = {}
    for c in cases:
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        T, ot = J.grid(truth)
        _, deep, axes, _ = O.build(c, truth, 1.00, "타원")
        G, og = J.grid(O.C.to_mesh(deep, axes))
        A, B = J.common(T, ot, G, og)
        lo = np.minimum(ot, og)
        F = fill_slices(A)

        def surf(vol):
            v, f, _, _ = measure.marching_cubes(np.pad(vol, 1).astype(np.uint8), 0.5)
            return (v - 1 + lo) * J.PITCH, f

        welded = trimesh.Trimesh(truth.vertices, truth.faces, process=False)
        welded.merge_vertices()                                              # 재질마다 끊긴 같은 자리 정점을 잇는다
        meshes = {"정답": (np.asarray(welded.vertices), np.asarray(welded.faces)), "속채움": surf(F & ~A), "hull": surf(B)}
        allv = np.vstack([v for v, _ in meshes.values()])
        mn, sc = allv.min(0), float((allv.max(0) - allv.min(0)).max())
        res[c] = {"min": mn.tolist(), "scale": sc, "점수": scores[c],
                  "meshes": {k: {"v": enc(np.round((v - mn) / sc * 65535).astype("<u2")), "f": enc(f.astype("<u4"))}
                             for k, (v, f) in meshes.items()}}
        print("  %-24s 면 %s" % (c[:24], {k: len(f) for k, (_, f) in meshes.items()}), flush=True)
    html = open(template, encoding="utf-8").read()
    assert "/*DATA*/null" in html, "틀에 자리표시가 없다"
    open(dst, "w", encoding="utf-8").write(html.replace("/*DATA*/null", json.dumps(res, ensure_ascii=False)))
    print("  -> %s (%.1f MB)" % (dst, os.path.getsize(dst) / 1e6))


def selfcheck():
    # 속 빈 원통(치마) 은 차고, 떨어진 두 기둥(다리) 사이는 안 찬다
    T = np.zeros((20, 20, 6), bool)
    yy, xx = np.mgrid[:20, :20]
    r = np.hypot(yy - 10, xx - 10)
    T[:, :, :3] = ((r >= 6) & (r < 8))[:, :, None]
    T[4:7, 4:7, 3:] = T[13:16, 13:16, 3:] = True
    F = fill_slices(T)
    assert F[10, 10, 0] and not F[10, 10, 4] and F[:, :, 3:].sum() == T[:, :, 3:].sum(), "층 채움이 틀렸다"
    print("  자가검사 통과 — 치마 고리는 차고 다리 사이는 안 찬다")


if __name__ == "__main__":
    a = sys.argv[1:]
    selfcheck()
    if a[:1] == ["벤치"]:
        bench(int(a[1]) if len(a) > 1 else 1)
    elif a[:1] == ["벤치판정"]:
        bench_judge(tuple(a[1:]))
    elif a[:1] == ["안보임"]:
        unseen(a[1:] or bench_cases())
    elif a[:1] == ["뷰어"]:                                 # 뷰어 <틀.html> <출력.html>
        viewer(["avatarsample_d_darkness", "avatarsample_g", "sakurada_fumiriya"], a[1], a[2])
    elif a[:1] == ["그림"]:
        figure(a[1:] or ["avatarsample_d_darkness", "avatarsample_g", "sakurada_fumiriya"])
    elif a[:1] != ["검사"]:
        run(a or CASES)
