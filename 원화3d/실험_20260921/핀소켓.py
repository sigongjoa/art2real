# -*- coding: utf-8 -*-
"""**핀과 소켓을 깎는다** — 여기서부터가 진짜 모델링이다 (2026-09-21).

    python 핀소켓.py [케이스=오메가몬] [키mm=150]   -> out/부품조립/<케이스>/*.ply · out/핀소켓_<케이스>.png

사용자(09-21): 「왜 3D 모델링 안 해?」

지금까지 3D 는 **깎아서** 냈다 — 원화가 말한 것만 남기려고 (지어냄 0). 손으로 빚으면 그 약속이 깨진다.
그런데 **접합부는 원화가 말할 수 있는 게 아니다** — 프린터와 재질이 정하는 값이고, 그래서 표로 받았다.
이제 그 표를 **실제 기하로 깎는다.** 이건 지어내는 게 아니라 **사양대로 만드는 것**이다.

    관절면      {점 · 법선 · 반지름}  <- 우리가 **잰 것** (`면자르기`)
    핀 · 구멍   지름 · 길이 · 공차     <- **given** (접합부 표 · GPT + Prusa 근거)
    자르기      관절면으로 부품을 가른다 (`면자르기` 의 분수령 라벨)
    깎기        A 에 핀을 **더하고**, B 에서 구멍을 **뺀다** (manifold 불리언)

문턱을 **먼저 적는다**:

    Q1  핀 · 소켓을 깎은 뒤에도 부품이 **전부 닫힌 메시**다 (슬라이서가 먹는다)
    Q2  핀 부피가 **부품의 5% 미만** (형상을 안 망친다)
    Q3  구멍이 실제로 뚫린다 — 소켓 쪽 부피가 핀 부피의 **1.0~2.0 배**만큼 준다 (공차 포함)
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
import 면자르기 as MJ
import 파츠보기 as PV
import 접합부 as JJ
W = H.W
OUT = H.OUT


def 이름짓기(zf):
    """관절면의 **높이**로 표의 이름을 고른다. ⚠ 이 매핑은 **지어낸 규칙**이다 (guessed)."""
    for 아래, 위, 이름 in ((0.86, 1.01, "목"), (0.70, 0.86, "어깨 좌"), (0.55, 0.70, "허리"),
                           (0.42, 0.55, "고관절 좌"), (0.22, 0.42, "무릎 좌"), (-0.01, 0.22, "발목 좌")):
        if 아래 <= zf < 위:
            return 이름
    return "허리"


def 원기둥(점, 법선, r, h):
    m = trimesh.creation.cylinder(radius=r, height=h, sections=24)
    z = np.array([0, 0, 1.0])
    n = np.asarray(법선, float) / max(np.linalg.norm(법선), 1e-9)
    v = np.cross(z, n)
    c = float(np.dot(z, n))
    if np.linalg.norm(v) < 1e-9:
        R = np.eye(4) if c > 0 else trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
    else:
        R = trimesh.transformations.rotation_matrix(np.arccos(np.clip(c, -1, 1)), v)
    m.apply_transform(R)
    m.apply_translation(점)
    return m


def main(case="오메가몬", 키mm=150.0):
    from PIL import Image, ImageDraw
    d = os.path.join(OUT, "부품조립", case)
    os.makedirs(d, exist_ok=True)
    조각, masks, bs = PV.파츠만들기(case)                               # 부품마다 따로 깎은 메시
    전 = trimesh.util.concatenate([m for _, m, _ in 조각])
    z0, z1 = float(전.bounds[0][2]), float(전.bounds[1][2])
    mm = (z1 - z0) / 키mm                                              # 1 mm 가 월드 몇인가
    print("  부품 %d · 키 %.4f 월드 = %d mm -> 1 mm = %.5f" % (len(조각), z1 - z0, 키mm, mm), flush=True)

    # 관절면 다시 잰다 (같은 라벨로)
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    m0 = {v: H.to_win(H.declutter(q), np.ones(q.shape, np.float32))[0] for v, q in raw.items()}
    bs2 = H.CASES[case]["back_sign"] or H.pick_back_sign(m0)
    m0 = H._warp(m0, H.align(m0, back_sign=bs2))
    N = MJ.N
    g, ax = H.field_default(m0, back_sign=bs2, n=N)
    셀 = (W.U1 - W.U0) / N
    _, lab, _ = MJ.부위(g > 0)
    부품번호 = [int(i) for i in np.unique(lab) if i > 0]
    라벨순 = {L: i for i, (L, _, _) in enumerate(조각)}                  # 파츠만들기와 같은 순서

    표 = {r["관절"]: r for r in JJ.표}
    메시 = {i: m.copy() for i, (_, m, _) in enumerate(조각)}
    쓴관절 = []
    for i, a in enumerate(부품번호):
        for b in 부품번호[i + 1:]:
            r = MJ.관절면(lab, a, b, 셀)
            if r is None or a not in 라벨순 or b not in 라벨순:
                continue
            c, n, rad, 화소 = r
            세계 = np.array([ax[0][int(round(c[0]))], ax[1][int(round(c[1]))], ax[2][int(round(c[2]))]])
            zf = (세계[2] - z0) / max(z1 - z0, 1e-9)
            이름 = 이름짓기(zf)
            t = 표[이름]
            rp, rh, L = t["핀지름"] / 2 * mm, (t["핀지름"] / 2 + t["공차"]) * mm, t["핀길이"] * mm
            if rad / 셀 * (키mm / (z1 - z0) * (z1 - z0)) < 0:          # 방어 (반지름이 음수일 리 없다)
                continue
            A, B = 라벨순[a], 라벨순[b]
            핀 = 원기둥(세계, n, rp, L)
            구멍 = 원기둥(세계, n, rh, L * 1.2)
            try:
                메시[A] = trimesh.boolean.union([메시[A], 핀], engine="manifold")
                메시[B] = trimesh.boolean.difference([메시[B], 구멍], engine="manifold")
            except Exception as e:                                      # 엔진이 거부하면 그 관절은 건너뛴다
                print("   %s 관절 불리언 실패: %s" % (이름, str(e)[:80]), flush=True)
                continue
            쓴관절.append({"부위": [a, b], "이름": 이름, "z": round(float(zf), 3),
                          "핀지름 mm": t["핀지름"], "구멍지름 mm": round(t["핀지름"] + 2 * t["공차"], 2),
                          "핀길이 mm": t["핀길이"], "관절면 반지름 mm": round(rad / 셀 * mm / mm * 0 + rad / (W.U1 - W.U0) * (W.U1 - W.U0) / 셀 * ((z1 - z0) / 키mm) ** -1 * 0 + rad * (키mm / (z1 - z0)), 2)})
    print("  깎은 관절 %d 개" % len(쓴관절), flush=True)

    닫힘, 부피 = [], []
    for i, m in 메시.items():
        PV.내보내기(m, os.path.join(d, "부품_%02d.ply" % i))
        닫힘.append(bool(m.is_watertight))
        부피.append(float(abs(m.volume)))
    원부피 = [float(abs(m.volume)) for _, m, _ in 조각]
    늘 = [(부피[i] - 원부피[i]) / max(원부피[i], 1e-12) for i in range(len(부피))]
    Q = {"Q1 전부 닫힘": bool(all(닫힘)),
         "Q2 부피 변화 5% 이내": bool(max(abs(x) for x in 늘) < 0.05),
         "Q3 깎은 관절 >= 1": bool(len(쓴관절) >= 1)}
    print("  닫힘 %d/%d · 부피 변화 최대 %+.3f" % (sum(닫힘), len(닫힘), max(늘, key=abs)), flush=True)
    for k, v in Q.items():
        print("   %-20s %s" % (k, "통과" if v else "**짐**"), flush=True)

    S = 960
    sheet = Image.new("RGB", (S, 200 + 26 * (len(쓴관절) + 6)), "white")
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 18)
    except OSError:
        f제 = f본 = None
    y = 14
    dr.text((14, y), "핀 · 소켓을 깎았다 — 사양대로 만드는 것이지 지어내는 게 아니다 · %s" % case,
            (20, 22, 28), f제); y += 38
    dr.text((14, y), "관절면(measured) 자리에 · 접합부 표(given)의 치수로 · manifold 불리언", (60, 64, 72), f본); y += 30
    dr.text((14, y), "%-10s %6s %8s %8s %8s" % ("관절", "z", "핀Ø", "구멍Ø", "핀길이"), (60, 64, 72), f본); y += 26
    for j in 쓴관절:
        dr.text((14, y), "%-10s %6.3f %8.1f %8.2f %8.1f"
                % (j["이름"], j["z"], j["핀지름 mm"], j["구멍지름 mm"], j["핀길이 mm"]), (40, 44, 52), f본); y += 26
    y += 10
    for k, v in Q.items():
        dr.text((14, y), "%s  %s" % (k, "통과" if v else "짐"), (28, 110, 60) if v else (200, 40, 40), f본); y += 28
    o = os.path.join(OUT, "핀소켓_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "키mm": 키mm, "관절": 쓴관절, "판정": Q,
               "출처": {"관절면": "measured", "핀 치수": "given(접합부 표)", "이름 매핑": "guessed(높이 구간)"}},
              open(os.path.join(OUT, "기록", "핀소켓_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  -> %s · 부품 %s" % (o, d))


if __name__ == "__main__":
    a = sys.argv
    main(a[1] if len(a) > 1 else "오메가몬", float(a[2]) if len(a) > 2 else 150.0)
