# -*- coding: utf-8 -*-
"""판마다 평면 하나를 푼다 — **그늘이 깊이를 준다** (103번).

    python solve.py     ->  parts/planes.json

판 i 의 깊이를  y = a_i x + b_i z + c_i  로 놓는다 (앞이 -y).
법선은 n_i ∝ (a_i, -1, b_i).

    이웃 등식   공유 경계 화소에서 두 평면의 y 가 같다        (수하라 방식)
    그늘 부등식 n_i . l 의 **부호**가 밝음/그늘과 맞는다
    정칙화      기울기 최소 (a^2+b^2)

**게이지에 주의.** 이웃 등식만으로는 전역 전단 (y += ax+bz) 을 못 고른다 —
평면을 다 같이 기울여도 등식이 그대로다. 그늘 부등식에 **자유 임계 s** 를 두면
전단이 s 에 흡수돼서 역시 못 고른다. 그래서 s=0 으로 못박는다
(그늘 = 광원을 등진 면). 그러면 전단 2자유도 중 l 방향 1개가 잡히고,
나머지 1개는 정칙화가 잡는다. 이게 이 문제에서 얻을 수 있는 전부다.

광원 방향은 모르니 반구를 훑어 에너지가 가장 낮은 것을 고른다.
크기(전체 깊이)는 부호 제약이라 정해지지 않는다 — 측면 실루엣 깊이로 맞춘다.
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W_ADJ = 30.0       # 이웃 등식
W_SHA = float(os.environ.get("W_SHA", 1.0))        # 그늘 부등식 (힌지)
# 0.05 는 밑바탕을 거의 안 지킨다(벗어난 양 0.83). 1.0 이 채택값 —
# 그늘 13/15 를 맞추면서 벗어난 양 0.19 로 어깨 돔을 존중한다
W_REG = float(os.environ.get("W_REG", 1.0))       # 밑바탕(어깨 돔)에서 벗어나는 양
W_BASE_C = 0.5     # 깊이 자체도 밑바탕에 묶는다 — 크기가 더 이상 자유가 아니다
MARGIN = 0.35      # |n.l| 이 이만큼은 돼야 확실히 밝음/그늘이라고 본다
ITERS = 25


def solve_for(l, pan, eqs, sha, base=None):
    """고정된 광원 l 에 대해 (a,b,c) 를 푼다. 힌지는 반복 재가중."""
    n = len(pan)
    idx = {p["id"]: k for k, p in enumerate(pan)}
    lx, ly, lz = l
    rows, rhs = [], []
    # 이웃 등식
    for i, j, x, z, wgt in eqs:
        r = np.zeros(3 * n)
        ki, kj = idx[i], idx[j]
        r[3 * ki:3 * ki + 3] = (x, z, 1)
        r[3 * kj:3 * kj + 3] = (-x, -z, -1)
        rows.append(W_ADJ * wgt * r)
        rhs.append(0.0)
    # 정칙화: **어깨 돔에서 벗어나지 마라**. "기울기 최소"가 아니다 (106번).
    # 밑바탕이 c 까지 주니 전역 전단·크기 게이지가 저절로 잡힌다 — DEPTH 노브가 없어졌다.
    for k in range(n):
        b0 = base[pan[k]["id"]] if base else dict(a=0.0, b=0.0, c=None)
        for o, key in ((0, "a"), (1, "b")):
            r = np.zeros(3 * n)
            r[3 * k + o] = W_REG
            rows.append(r)
            rhs.append(W_REG * b0[key])
        if base:
            r = np.zeros(3 * n)
            r[3 * k + 2] = W_BASE_C
            rows.append(r)
            rhs.append(W_BASE_C * b0["c"])
    if not base:
        r = np.zeros(3 * n)
        r[2::3] = 1.0
        rows.append(r)
        rhs.append(0.0)
    base = np.array(rows), np.array(rhs)
    x = np.zeros(3 * n)
    for _ in range(ITERS):
        R, B = list(base[0]), list(base[1])
        for pid, sgn in sha:
            k = idx[pid]
            f = x[3 * k] * lx + x[3 * k + 1] * lz - ly
            if sgn * f < MARGIN:                       # 위반한 것만 당긴다
                r = np.zeros(3 * n)
                r[3 * k] = W_SHA * lx
                r[3 * k + 1] = W_SHA * lz
                R.append(r)
                B.append(W_SHA * (sgn * MARGIN + ly))
        x = np.linalg.lstsq(np.array(R), np.array(B), rcond=None)[0]
    # 점수
    ok = 0
    for pid, sgn in sha:
        k = idx[pid]
        if sgn * (x[3 * k] * lx + x[3 * k + 1] * lz - ly) > 0:
            ok += 1
    res = 0.0
    for i, j, xx, zz, _w in eqs:
        ki, kj = idx[i], idx[j]
        res += (x[3 * ki] * xx + x[3 * ki + 1] * zz + x[3 * ki + 2]
                - x[3 * kj] * xx - x[3 * kj + 1] * zz - x[3 * kj + 2]) ** 2
    tilt = float(np.sqrt((x[0::3] ** 2 + x[1::3] ** 2).mean()))
    return x, ok, math.sqrt(res / max(len(eqs), 1)), tilt


def main():
    J = json.load(open(os.path.join(HERE, "parts", "panels.json")))
    # 금색(뿔 면)도 넣는다 — 빼면 셸에 구멍이 뚫린다. 다만 라벤더와의 경계는
    # 가림선이라 깊이가 안 이어진다: 등식 가중치를 10분의 1 로 낮춰 **깊이 앵커**로만 쓴다
    pan = [p for p in J["panels"] if p["hue"] in ("lav", "gold")]
    keep = {p["id"] for p in pan}
    hu = {p["id"]: p["hue"] for p in pan}
    eqs = []
    for e in J["edges"]:
        if e["i"] not in keep or e["j"] not in keep:
            continue
        soft = e["occl"] or hu[e["i"]] != hu[e["j"]]
        for x, z in e["pts"]:
            eqs.append((e["i"], e["j"], x, z, 0.1 if soft else 1.0))
    sha = [(p["id"], 1.0 if p["lit"] else -1.0) for p in pan]
    print("판 %d개 (라벤더 %d / 금 %d)  이웃 등식 %d행  밝음 %d / 그늘 %d"
          % (len(pan), sum(v == "lav" for v in hu.values()), sum(v == "gold" for v in hu.values()),
             len(eqs),
             sum(s > 0 for _, s in sha), sum(s < 0 for _, s in sha)))

    base = {p["id"]: p for p in json.load(open(os.path.join(HERE, "parts", "base.json")))["planes"]}
    base = {k: dict(a=v["a"], b=v["b"], c=v["c"]) for k, v in base.items()}
    best = None
    for el in range(-75, 90, 15):
        for az in range(0, 360, 15):
            ce, se = math.cos(math.radians(el)), math.sin(math.radians(el))
            l = (ce * math.cos(math.radians(az)), -se, ce * math.sin(math.radians(az)))
            x, ok, res, tilt = solve_for(l, pan, eqs, sha, base)
            E = -ok * 10 + res * 500 + tilt * 0.5
            if best is None or E < best[0]:
                best = (E, l, x, ok, res, tilt, az, el)
    E, l, x, ok, res, tilt, az, el = best
    print("\n최적 광원  방위 %d도 고도 %+d도   그늘 맞춘 판 %d/%d   이웃 잔차 %.5f   평균기울기 %.3f"
          % (az, el, ok, len(sha), res, tilt))

    # 크기: 측면 실루엣의 깊이에 맞춘다 (부호 제약은 크기를 안 준다)
    # 크기 재조정 없음 — 밑바탕이 절대 깊이를 준다
    s = 1.0
    ys = []
    for k, p in enumerate(pan):
        for xx, zz in p["poly"]:
            ys.append(x[3 * k] * xx + x[3 * k + 1] * zz + x[3 * k + 2])
    d0 = [abs(x[3 * k] - base[p["id"]]["a"]) + abs(x[3 * k + 1] - base[p["id"]]["b"])
          for k, p in enumerate(pan)]
    print("깊이 %.4f..%.4f (폭 %.4f)   밑바탕에서 벗어난 양 평균 %.3f 최대 %.3f"
          % (min(ys), max(ys), max(ys) - min(ys), float(np.mean(d0)), float(np.max(d0))))

    out = []
    for k, p in enumerate(pan):
        a, b, c = x[3 * k] * s, x[3 * k + 1] * s, x[3 * k + 2] * s
        nz = np.array([a, -1.0, b])
        nz /= np.linalg.norm(nz)
        out.append(dict(id=p["id"], a=float(a), b=float(b), c=float(c),
                        lit=p["lit"], normal=[float(v) for v in nz],
                        nl=float(nz @ np.array(l)), poly=p["poly"]))
    out.sort(key=lambda r: -r["nl"])
    print("\n판별 법선 (n.l 큰 순 = 밝은 쪽)")
    for r in out:
        print("  %3d %-4s n(%+.2f,%+.2f,%+.2f)  n.l %+.3f  %s"
              % (r["id"], "밝음" if r["lit"] else "그늘", *r["normal"], r["nl"],
                 "OK" if (r["nl"] > 0) == r["lit"] else "**어긋남**"))
    json.dump(dict(light=list(l), az=az, el=el, scale=s, ok=ok, res=res,
                   planes=out), open(os.path.join(HERE, "parts", "planes.json"), "w"), indent=1)
    print("-> parts/planes.json")


if __name__ == "__main__":
    main()
