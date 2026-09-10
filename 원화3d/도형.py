# -*- coding: utf-8 -*-
"""**답을 아는 도형으로 자를 검증한다.** 캐릭터를 재기 전에 상자·원기둥·구를 잰다.

    python 도형.py        -> out/도형.json + 표. 잰 값과 **해석적으로 아는 값**을 대본다

## 왜

2026-09-10 에 계단 지표를 캐릭터 29장에 바로 걸었다가 하루에 네 번을 틀렸다 (격자 다른
둘을 맞대고, 축을 x 로 잰다고 적어놓고 z 를 재고). **답을 모르는 물건으로는 자가 틀린 걸
알아낼 수 없다.** 답을 아는 물건이 먼저다.

## 직교 3판 visual hull 의 3D IoU 는 해석적으로 안다

세 판이 front·side·back 이라 실제로 x·y 두 축의 실루엣만 다르다. 그래서 높이마다
단면이 **(x 구간)×(y 구간) = 축정렬 직사각형**이다.

    상자 (축정렬)   hull 이 원본과 같다                              IoU = 1
    원기둥 (세움)   단면 원 -> 외접 정사각형. 원/사각 = pi/4         IoU = 0.7854
    원뿔  (세움)    높이마다 같은 비율                               IoU = 0.7854
    구            세 원기둥 교집합(슈타인메츠)이 아니라 **두** 축이라
                  단면이 원의 외접 사각형이다. 구/(원기둥 교집합) =
                  (4/3 pi r^3) / (16/3 r^3) = pi/4                  IoU = 0.7854

**셋이 같은 값인 게 우연이 아니다** — 어느 높이에서든 단면이 원이면 외접 정사각형과의
비가 pi/4 로 같다. 그래서 이 셋은 **같은 답을 서로 다른 형태로** 확인해준다.

`정답.grid` 는 표면을 굽고 안을 채우는 근사라 몇 %의 바닥 오차가 깔린다. 문턱은 그 위에
얹었다 — 절대값이 아니라 **아는 값에서 얼마나 벗어나나**를 본다.
"""
import json
import os
import subprocess
import sys

import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull as H
import 대조 as C
import 정답 as J

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
PI4 = float(np.pi / 4)

# 이름, 메시, 아는 IoU, 계단이 어때야 하나
FORMS = {
    "도형_상자":   (lambda: trimesh.creation.box((0.6, 0.6, 1.0)), 1.0, "0 에 가깝다 (평면)"),
    "도형_원기둥": (lambda: trimesh.creation.cylinder(radius=0.3, height=1.0, sections=96), PI4, "낮다 (매끈)"),
    "도형_원뿔":   (lambda: trimesh.creation.cone(radius=0.35, height=1.0, sections=96), PI4, "낮다 (매끈)"),
    "도형_구":     (lambda: trimesh.creation.icosphere(subdivisions=4, radius=0.5), PI4, "낮다 (매끈)"),
}
TOL = 0.06                                       # 아는 값에서 이만큼 벗어나면 자가 틀린 것

# **깨끗함 지표 후보는 여기 등록하면 도형이 문지기가 된다.**
# 문: 정답 도형은 완벽히 깨끗하다. 그러니 어떤 깨끗함 지표든 **정답이 hull 보다 낮아야** 한다.
# hull 은 정답을 상자로 근사한 물건이니까. 이걸 못 넘으면 그 지표는 깨끗함을 재는 게 아니다.
CLEAN = {"계단": C.stair}


def make_models():
    """도형을 glb 로 굽고 판을 뽑는다. 이미 있으면 건너뛴다."""
    d = os.path.join(OUT, "모델")
    os.makedirs(d, exist_ok=True)
    for name, (fn, _, _) in FORMS.items():
        glb = os.path.join(d, name + ".glb")
        if not os.path.exists(glb):
            m = fn()
            # **Y-up 으로 눕혀 내보낸다.** `시트.py` 는 `to_world(V, "xyz")` 로 읽는다 —
            # glTF 규약이라 y 가 위다. trimesh 도형은 z 가 위라 그냥 주면 물건이 누워서
            # 나오고, 그러면 창이 깊이를 잘라 **hull 이 정답보다 작아진다** (실측 부피비 0.72).
            m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
            m.visual = trimesh.visual.ColorVisuals(m, face_colors=np.full((len(m.faces), 4), 210, np.uint8))
            trimesh.Scene(m).export(glb)
        if not os.path.exists(os.path.join(OUT, "시트", name, "truth.glb")):
            print("  판 뽑기 %s" % name)
            r = subprocess.run([sys.executable, os.path.join(HERE, "시트.py"), glb, "--이름", name],
                               cwd=HERE, capture_output=True, text=True, encoding="utf-8")
            if r.returncode:
                print("     실패: %s" % (r.stderr or "")[-200:])
    H.register_sheets()


def main():
    make_models()
    rows, bad = [], []
    for name, (_, want, stair_says) in FORMS.items():
        if name not in H.CASES:
            print("  %-12s 판이 없다 — 건너뜀" % name); continue
        if not os.path.exists(os.path.join(OUT, "깊이", name, "front", "depth.npy")):
            subprocess.run([sys.executable, os.path.join(HERE, "깊이.py"), name],
                           cwd=HERE, capture_output=True)
        t = trimesh.load(os.path.join(OUT, "시트", name, "truth.glb"), force="mesh")
        ex = t.bounds[1] - t.bounds[0]
        assert ex[2] >= max(ex[0], ex[1]) - 1e-6, (
            "%s 정답이 누워 있다 (가로 %.2f 깊이 %.2f 키 %.2f) — 도형을 Y-up 으로 내보낼 것"
            % (name, *ex))
        plain, deep, axes, _ = C.build(name)
        T, ot = J.grid(t)
        got = {}
        for tag, vox in (("이진", plain), ("깊이", deep)):
            G, og = J.grid(C.to_mesh(vox, axes))
            A, B = J.common(T, ot, G, og)
            got[tag] = {"iou": float((A & B).sum() / max((A | B).sum(), 1)),
                        "계단": C.stair(B)}
            if tag == "이진":
                got["정답계단"] = C.stair(A)
        off = got["이진"]["iou"] - want
        rows.append({"case": name, "아는값": round(want, 4),
                     "이진_iou": round(got["이진"]["iou"], 4), "벗어남": round(off, 4),
                     "깊이_iou": round(got["깊이"]["iou"], 4),
                     "계단_정답": round(got["정답계단"], 4),
                     "이진_계단": round(got["이진"]["계단"], 4),
                     "깊이_계단": round(got["깊이"]["계단"], 4)})
        print("  %-12s 아는값 %.4f · 이진 %.4f (%+.4f) · 깊이 %.4f | 계단 정답 %.4f · 이진 %.4f · 깊이 %.4f  <- %s"
              % (name, want, got["이진"]["iou"], off, got["깊이"]["iou"],
                 got["정답계단"], got["이진"]["계단"], got["깊이"]["계단"], stair_says))
        if abs(off) > TOL:
            bad.append((name, want, got["이진"]["iou"]))
    json.dump(rows, open(os.path.join(OUT, "도형.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    if bad:
        print("\n  **자가 틀렸다** — 아는 값에서 %.2f 넘게 벗어난 도형:" % TOL)
        for n, w, g in bad:
            print("    %-12s 알아야 할 값 %.4f · 잰 값 %.4f" % (n, w, g))
        raise SystemExit(1)
    print("\n  %d 도형 전부 아는 값의 %.2f 안에 있다 — 3D IoU 는 믿을 만하다" % (len(rows), TOL))

    # ── 깨끗함 지표의 문 ────────────────────────────────────────────
    print("\n  깨끗함 지표의 문 — 정답 도형은 완벽히 깨끗하다. 그러니 정답 <= hull 이어야 한다")
    for mname in CLEAN:
        ok = 0
        for r in rows:
            good = r["계단_정답"] <= r["이진_계단"] + 1e-9
            ok += good
            print("    %-4s %-8s 정답 %.4f · 이진 hull %.4f   %s"
                  % (mname, r["case"][3:], r["계단_정답"], r["이진_계단"],
                     "통과" if good else "**떨어짐**"))
        print("    -> %s %d/%d. %s" % (mname, ok, len(rows), "쓸 수 있다" if ok == len(rows) else
              "**깨끗함이 아니라 납작함을 잰다** — 곡면인 정답이 상자인 hull 보다 높다"))


if __name__ == "__main__":
    main()
