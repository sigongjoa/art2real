# -*- coding: utf-8 -*-
"""**답을 아는 도형 벤치.** 캐릭터를 재기 전에 상자·기둥·치마를 잰다.

    python 도형.py        -> out/도형.json · out/기록/도형_<날짜>.json + 표

벤치가 둘이다. **`대조.py` 는 실물(CC0 캐릭터 29장), 이건 기본도형 11개**다.
실물 벤치는 「우리 파이프라인이 사람 형상에서 몇 점인가」를 재고, 이 벤치는
**「자가 맞나」**를 잰다. 답을 모르는 물건으로는 자가 틀린 걸 알아낼 수 없다 —
2026-09-10 에 캐릭터 29장에 지표를 바로 걸었다가 하루에 네 번 틀렸다.

## 세 개의 값을 나란히 놓는다

    해석값     손으로 유도한 답. 있는 도형만 (상자 1 · 원단면 pi/4 · 두기둥 1/2 · L 3/4)
    오라클     **정답 메시에서 직접** 계산한 hull 비율. 렌더·마스크·마칭큐브를 안 거친다
    잰 값      파이프라인 전체 (시트 렌더 -> 마스크 -> 정렬 -> 깎기 -> 메시 -> 복셀)

    해석값 vs 오라클   오라클이 맞나 (자의 자)
    오라클 vs 잰 값     파이프라인이 이론값에서 얼마나 새나

오라클이 있어서 **해석적으로 답을 못 구하는 도형도 벤치에 넣을 수 있다** (치마·토러스).

## 왜 이 도형들인가

직교 3판 hull 은 `voxel[x,y,z] = F[z,x] & B[z,x] & S[z,y]` 다. front·back 이 같은 축이라
실효 시점은 **x·y 두 축**이고, 높이마다 단면이 `X(z) x Y(z)` — 집합의 곱이다.
visual hull 이 원리적으로 못 하는 일은 셋이고 (오목부 · 구멍 · 유령 덩어리), 우리 자에는
넷째가 있다 (**축에 대한 방향**). 볼록·축정렬 도형만 넣으면 그 넷을 하나도 안 시험한다 —
처음 넷(상자·기둥·뿔·구)이 그랬고, 그래서 셋이 답이 같은 0.7854 였다.

조사 근거: `../claudedocs/research_visual_hull_test_solids_20260910.md`
"""
import datetime
import json
import os
import subprocess
import sys

import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull as H
import 각도 as ANG
import 대조 as C
import 라벨 as LB
import 정답 as J
import 표면 as SF
from 계획 import _font
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
PI4 = float(np.pi / 4)


def _box(sx, sy, sz, at=(0, 0, 0), rz=0.0):
    m = trimesh.creation.box((sx, sy, sz))
    if rz:
        m.apply_transform(trimesh.transformations.rotation_matrix(rz, [0, 0, 1]))
    m.apply_translation(at)
    return m


def _skirt():
    """속 빈 원뿔. **밑이 뚫려 있어야** 채우기가 들어가 속이 빈 채로 남는다.
    boolean 을 안 쓴다 — 이 환경에 manifold3d 가 없어 `difference` 가 빈 메시를 낸다."""
    prof = np.array([[0.42, 0.0], [0.02, 0.98], [0.055, 0.98], [0.455, 0.0], [0.42, 0.0]])
    m = trimesh.creation.revolve(prof, sections=96)
    if m.volume < 0:
        m.invert()
    return m


def _torus(axis):
    t = trimesh.creation.torus(major_radius=0.32, minor_radius=0.16,
                               major_sections=64, minor_sections=32)
    ang = {"z": 0.0, "y": np.pi / 2, "x": np.pi / 2}[axis]
    if axis == "y":                                   # 구멍이 앞을 본다 (세움)
        t.apply_transform(trimesh.transformations.rotation_matrix(ang, [1, 0, 0]))
    elif axis == "x":                                 # 구멍이 옆을 본다
        t.apply_transform(trimesh.transformations.rotation_matrix(ang, [0, 1, 0]))
        t.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    return t


# 이름, 만들기, 해석값(없으면 None), 무엇을 시험하나
FORMS = [
    ("상자",       lambda: _box(.6, .6, 1.), 1.0,  "기준 · 축정렬 볼록. hull 이 정확해야 한다"),
    ("원기둥",     lambda: trimesh.creation.cylinder(radius=.3, height=1., sections=96), PI4, "기준 · 원단면"),
    ("원뿔",       lambda: trimesh.creation.cone(radius=.35, height=1., sections=96), PI4, "기준 · 테이퍼"),
    ("구",         lambda: trimesh.creation.icosphere(subdivisions=4, radius=.5), PI4, "기준 · 곡면"),
    ("두기둥대각", lambda: trimesh.util.concatenate([_box(.28, .28, 1., (.22, .22, 0)),
                                                    _box(.28, .28, 1., (-.22, -.22, 0))]), 0.5,
     "**유령 덩어리.** 기둥 2개가 hull 에서 4개가 된다"),
    ("두기둥나란히", lambda: trimesh.util.concatenate([_box(.28, .28, 1., (.22, 0, 0)),
                                                      _box(.28, .28, 1., (-.22, 0, 0))]), 1.0,
     "같은 물건인데 **방향만 바꾸면 완벽하다** — 위의 대조군"),
    ("상자45도",   lambda: _box(.6, .6, 1., rz=np.pi / 4), 0.5,
     "**축에 대한 방향.** 같은 상자가 1.0 -> 0.5"),
    ("L자",        lambda: trimesh.util.concatenate([_box(.6, .3, 1., (0, -.15, 0)),
                                                     _box(.3, .3, 1., (-.15, .15, 0))]), 0.75,
     "**오목부.** 겨드랑이 · 팔과 몸 사이"),
    ("치마",       _skirt, None,
     "**이 사업의 병목.** 속 빈 원뿔 — 어느 시점도 치마 밑을 못 본다"),
    ("토러스세움", lambda: _torus("y"), None, "**구멍이 정면에 보인다** — hull 이 구멍을 남긴다"),
    ("토러스옆",   lambda: _torus("x"), None, "같은 구멍이 **옆에만 보인다**"),
]
TOL_해석 = 0.02                                  # 오라클이 해석값에서 이만큼 벗어나면 자가 틀렸다
TOL_파이프 = 0.06                                # 파이프라인이 오라클에서 이만큼 벗어나면 새는 것이다
CLEAN = {"계단": C.stair}                        # 깨끗함 지표 후보. 여기 넣으면 도형이 문지기다


def oracle(mesh, pitch=None):
    """**정답 메시에서 직접** 3판 hull 을 만들어 비율을 낸다. 파이프라인을 안 거친다.

    `hull.carve` 와 같은 규칙이다 — `F[z,x] & S[z,y]`. 렌더·마스크·정렬·마칭큐브가
    빠지므로, 이 값과 파이프라인 값의 차이가 **파이프라인이 흘린 양**이다."""
    g, _ = J.grid(mesh, pitch or J.PITCH / 2)
    F, S = g.any(1), g.any(0)                    # (x,z) · (y,z)
    hull = F[:, None, :] & S[None, :, :]
    return float(g.sum() / max(hull.sum(), 1))


R = 200                                          # 그림 타일 크기


def _paint3(case, plain, deep, axes):
    """정답·이진·깊이를 **한 격자·한 눈금**으로 칠한다 (`라벨.py` 와 같은 규약)."""
    ds = [ANG.depth(v, 35) for v in LB._same_frame(case, plain, deep, axes)]
    lo = min(d[h].min() for d, h in ds)
    hi = max(d[h].max() for d, h in ds)
    return [ANG.paint(d, h, R, (lo, hi)) for d, h in ds]


def draw(rows, tiles, stamp):
    """한 장으로. 왼쪽에 숫자, 오른쪽에 정답·이진 hull·깊이 깎기."""
    W_, top = 3 * R + 430, 96
    im = Image.new("RGB", (W_, top + len(tiles) * (R + 26) + 40), "white")
    g = ImageDraw.Draw(im)
    g.text((22, 18), "기본도형 벤치 — 답을 아는 물건으로 자를 잰다", font=_font(22), fill=(20, 20, 20))
    g.text((22, 50), "해석값(손유도) · 오라클(정답 메시에서 직접) · 잰 값(파이프라인 전체)   %s"
           % stamp.replace("_", " "), font=_font(12), fill=(120, 120, 120))
    im.paste(ANG.bar(150, 11), (22, 72))
    g.text((176, 70), "멀다 -> 가깝다 · 세 타일이 같은 눈금", font=_font(11), fill=(120, 120, 120))
    for i, (name, three) in enumerate(tiles):
        r = rows[i]
        y = top + i * (R + 26)
        g.text((22, y + 4), name, font=_font(16), fill=(20, 20, 20))
        g.text((22, y + 28), "해석  %s" % ("%.4f" % r["해석"] if r["해석"] is not None else "—"),
               font=_font(12), fill=(120, 120, 120))
        g.text((22, y + 46), "오라클 %.4f" % r["오라클"], font=_font(12), fill=(60, 60, 60))
        g.text((22, y + 64), "잰 값  %.4f" % r["이진_iou"], font=_font(13), fill=(20, 20, 20))
        g.text((22, y + 84), "%+.4f" % r["파이프차"], font=_font(12),
               fill=(60, 150, 90) if abs(r["파이프차"]) <= 0.03 else (200, 120, 60))
        g.text((22, y + 108), r["시험"].replace("**", "")[:26], font=_font(10), fill=(150, 150, 150))
        for k, t in enumerate(three):
            x = 400 + k * (R + 10)
            im.paste(t, (x, y))
            g.rectangle([x, y, x + R - 1, y + R - 1], outline=(220, 220, 220))
            if i == 0:
                g.text((x, y - 16), ("정답", "이진 hull", "깊이 깎기")[k], font=_font(12),
                       fill=(90, 90, 90))
    im.save(os.path.join(OUT, "도형.png"))
    print("  -> out/도형.png")


def make_models():
    """도형을 glb 로 굽고 판을 뽑는다. 이미 있으면 건너뛴다."""
    d = os.path.join(OUT, "모델")
    os.makedirs(d, exist_ok=True)
    for name, fn, _, _ in FORMS:
        case = "도형_" + name
        glb = os.path.join(d, case + ".glb")
        if not os.path.exists(glb):
            m = fn()
            # **Y-up 으로 눕혀 내보낸다.** `시트.py` 는 `to_world(V, "xyz")` 로 읽는다 —
            # glTF 규약이라 y 가 위다. trimesh 도형은 z 가 위라 그냥 주면 물건이 누워서
            # 나오고, 창이 깊이를 잘라 **hull 이 정답보다 작아진다** (실측 부피비 0.72).
            m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
            m.visual = trimesh.visual.ColorVisuals(
                m, face_colors=np.full((len(m.faces), 4), 210, np.uint8))
            trimesh.Scene(m).export(glb)
        if not os.path.exists(os.path.join(OUT, "시트", case, "truth.glb")):
            print("  판 뽑기 %s" % case)
            r = subprocess.run([sys.executable, os.path.join(HERE, "시트.py"), glb, "--이름", case],
                               cwd=HERE, capture_output=True, text=True, encoding="utf-8")
            if r.returncode:
                print("     실패: %s" % (r.stderr or "")[-200:])
    H.register_sheets()


def main():
    make_models()
    rows, bad, tiles = [], [], []
    print("  %-12s %8s %8s %8s | %8s %8s  %s"
          % ("도형", "해석", "오라클", "잰 값", "오라클차", "파이프차", "무엇을 시험하나"))
    for name, fn, want, says in FORMS:
        case = "도형_" + name
        if case not in H.CASES:
            print("  %-12s 판이 없다 — 건너뜀" % name); continue
        if not os.path.exists(os.path.join(OUT, "깊이", case, "front", "depth.npy")):
            subprocess.run([sys.executable, os.path.join(HERE, "깊이.py"), case],
                           cwd=HERE, capture_output=True)
        t = trimesh.load(os.path.join(OUT, "시트", case, "truth.glb"), force="mesh")
        src = trimesh.load(os.path.join(OUT, "모델", case + ".glb"), force="mesh")
        # **누웠는지 본다.** 원본(Y-up)의 (가로, 위, 깊이) 가 창의 (x, z, y) 로 가야 한다
        a, b = src.bounds[1] - src.bounds[0], t.bounds[1] - t.bounds[0]
        want_ratio = np.array([a[0], a[2], a[1]]) / max(a[1], 1e-9)
        got_ratio = b / max(b[2], 1e-9)
        assert np.allclose(want_ratio[:2], got_ratio[:2], atol=0.03), (
            "%s 가 누웠거나 잘렸다 — 원본 비 %s · 정답 비 %s" % (name, want_ratio.round(2), got_ratio.round(2)))

        orc = oracle(t)
        plain, deep, axes, _ = C.build(case)
        tiles.append((name, _paint3(case, plain, deep, axes)))
        got = {}
        for tag, vox in (("이진", plain), ("깊이", deep)):
            m = C.to_mesh(vox, axes)
            G, og = J.grid(m)
            A, B = J.common(J.grid(t)[0], J.grid(t)[1], G, og)
            got[tag] = {"iou": float((A & B).sum() / max((A | B).sum(), 1)), "계단": C.stair(B),
                        **SF.score(t, m)}                # **표면으로도 본다** (`표면.py`)
            if tag == "이진":
                got["정답계단"] = C.stair(A)
        d_orc = (orc - want) if want is not None else None
        d_pipe = got["이진"]["iou"] - orc
        rows.append({"case": name, "해석": want, "오라클": round(orc, 4),
                     "이진_iou": round(got["이진"]["iou"], 4), "깊이_iou": round(got["깊이"]["iou"], 4),
                     "오라클차": None if d_orc is None else round(d_orc, 4),
                     "파이프차": round(d_pipe, 4),
                     "계단_정답": round(got["정답계단"], 4), "이진_계단": round(got["이진"]["계단"], 4),
                     "정답_각짐": round(SF.angularity(t), 4),
                     **{"%s_%s" % (tag, k): round(float(got[tag][k]), 4)
                        for tag in ("이진", "깊이") for k in ("챔퍼", "F", "정밀도", "재현율", "각짐")},
                     "시험": says})
        print("  %-12s %8s %8.4f %8.4f | %8s %+8.4f  %s"
              % (name, "%.4f" % want if want is not None else "—", orc, got["이진"]["iou"],
                 "%+.4f" % d_orc if d_orc is not None else "—", d_pipe, says[:34]))
        if d_orc is not None and abs(d_orc) > TOL_해석:
            bad.append(("오라클", name, want, orc))
        if abs(d_pipe) > TOL_파이프:
            bad.append(("파이프라인", name, orc, got["이진"]["iou"]))

    json.dump(rows, open(os.path.join(OUT, "도형.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    hist = os.path.join(OUT, "기록")
    os.makedirs(hist, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    json.dump({"때": stamp, "LAM": H.LAM, "SMOOTH": H.SMOOTH, "N": H.N, "rows": rows},
              open(os.path.join(hist, "도형_%s.json" % stamp), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # ── 깨끗함 지표의 문 ────────────────────────────────────────────
    print("\n  깨끗함 지표의 문 — 정답 도형은 완벽히 깨끗하다. 그러니 정답 <= hull 이어야 한다")
    for mname in CLEAN:
        ok = sum(r["계단_정답"] <= r["이진_계단"] + 1e-9 for r in rows)
        print("    %s %d/%d 통과. %s" % (mname, ok, len(rows), "쓸 수 있다" if ok == len(rows) else
              "**깨끗함이 아니라 납작함을 잰다** — 곡면인 정답이 상자인 hull 보다 높다"))

    draw(rows, tiles, stamp)
    pipe = np.array([r["파이프차"] for r in rows])
    print("\n  기본도형 벤치 | %d 개 · 오라클차 최대 %.4f · 파이프차 중앙 %+.4f (최악 %+.4f)"
          % (len(rows), max([abs(r["오라클차"]) for r in rows if r["오라클차"] is not None] or [0]),
             np.median(pipe), pipe[np.argmax(np.abs(pipe))]))
    print("  기록 -> out/기록/도형_%s.json" % stamp)
    if bad:
        print("\n  **떨어졌다**")
        for kind, n, want, got in bad:
            print("    %-8s %-12s 나와야 %.4f · 나온 값 %.4f" % (kind, n, want, got))
        raise SystemExit(1)
    print("  전부 문턱 안 (해석 %.2f · 파이프 %.2f)" % (TOL_해석, TOL_파이프))


if __name__ == "__main__":
    main()
