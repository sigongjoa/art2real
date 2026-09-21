# -*- coding: utf-8 -*-
"""**너무 둥글다** — 단면 지수 p 를 올려 각지게 한다 (2026-09-21).

    python 각면.py [케이스=오메가몬]   -> out/각면_<케이스>.png · out/기록/각면_*.json

사용자(09-21): 「지금은 **너무 면이 곡면**이지 않어?」 맞다. 우리 단면은 **타원**이라
어디를 잘라도 둥글다. 오메가몬은 **딱딱한 갑주**라 평평한 면과 모서리가 있어야 한다.

가정을 바꾸는 게 아니라 **같은 직사각형에 내접하는 모양의 지수**만 바꾼다:

    |x/a|^p + |y/b|^p = 1     p=2 타원(지금) · p=4 모서리가 둥근 상자 · p=8 거의 상자

`hull.superellipse(p)` 가 이미 있던 손잡이다 (09-15 에 복셀 쪽에 쓰고 껐다). 장 쪽에 붙인다.

재는 것 넷. **앞의 둘은 약속, 뒤의 둘이 「각짐」이다**:

    못덮음      원화를 못 덮은 몫 (판마다)
    지어냄      원화 밖 화소 — hull 덮개가 있으니 늘 수 없다
    평탄몫      이웃 면끼리 각이 **5° 미만**인 몫. 평평한 면이 넓을수록 크다
    모서리몫    이웃 면끼리 각이 **30° 이상**인 몫. 각이 살아 있을수록 크다
"""
import json
import os
import subprocess
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
import 결과물 as RS
import 파츠보기 as PV
import 부위깎기 as BK
W = H.W
OUT = H.OUT
지수 = (2.0, 3.0, 4.0, 6.0)


def 각재기(meshes):
    """이웃 면 사이 각 -> (평탄몫, 모서리몫). 면 넓이로 가중한다."""
    평, 모, 합 = 0.0, 0.0, 0.0
    for m in meshes:
        a = m.face_adjacency_angles
        if not len(a):
            continue
        w = m.area_faces[m.face_adjacency].mean(1)
        평 += float(w[a < np.radians(5)].sum())
        모 += float(w[a >= np.radians(30)].sum())
        합 += float(w.sum())
    return 평 / max(합, 1), 모 / max(합, 1)


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    표 = []
    for p in 지수:
        d = os.path.join(OUT, "각면", case, "p%g" % p)
        os.makedirs(d, exist_ok=True)
        for old in os.listdir(d):
            if old.endswith(".ply"):
                os.remove(os.path.join(d, old))
        조각, masks, bs = PV.파츠만들기(case, p)
        for i, (_, m, _) in enumerate(조각):
            PV.내보내기(m, os.path.join(d, "부위_%02d.ply" % i))
        import trimesh
        하나 = trimesh.util.concatenate([m for _, m, _ in 조각])
        못, 지어 = BK.재다(np.asarray(하나.vertices), np.asarray(하나.faces), masks, bs)
        평, 모 = 각재기([m for _, m, _ in 조각])
        표.append({"p": p, "못덮음": 못, "지어냄": 지어, "평탄몫": round(평, 3), "모서리몫": round(모, 3),
                   "파츠": len(조각)})
        print("  p %-3g  못덮음 %s · 지어냄 %5d · 평탄몫 %.3f · 모서리몫 %.3f"
              % (p, [float(v) for v in 못.values()], 지어, 평, 모), flush=True)
        py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_파츠렌더.py")
        open(py, "w", encoding="utf-8").write(PV.렌더소스)
        subprocess.run([RS.BLENDER, "-b", "--python", py, "--", d, d, "p", "0.0", repr(PV.색판)],
                       capture_output=True, timeout=1800)

    S = 520
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원 = Image.open(흰).convert("RGB").resize((S, S)) if os.path.exists(흰) else Image.new("RGB", (S, S), "white")
    sheet = Image.new("RGB", ((len(지수) + 1) * (S + 8), 2 * (S + 8) + 130), "white")
    sheet.paste(원, (0, 130))
    for i, p in enumerate(지수):
        d = os.path.join(OUT, "각면", case, "p%g" % p)
        for j, n in enumerate(("앞", "사선")):
            f = os.path.join(d, "파츠_p_%s.png" % n)
            if os.path.exists(f):
                sheet.paste(Image.open(f).convert("RGB").resize((S, S)), ((i + 1) * (S + 8), 130 + j * (S + 8)))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 30)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 21)
        f표 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
    except OSError:
        f제 = f본 = f표 = None
    dr.text((14, 14), "단면 지수 p — 타원(둥글다)에서 상자(각진다)로 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 50), "|x/a|^p + |y/b|^p = 1.  가정은 그대로(높이마다 직사각형에 내접) · **지수만** 바꿨다. "
                      "hull 장으로 덮개를 씌워 원화 밖으로 못 나간다", (90, 92, 100), f본)
    for i, r in enumerate(표):
        x = (i + 1) * (S + 8) + 8
        dr.text((x, 80), "p %g" % r["p"], (20, 22, 28), f본)
        dr.text((x, 104), "못덮음 %.1f · %.1f · %.1f   지어냄 %d"
                % (r["못덮음"]["front"], r["못덮음"]["side"], r["못덮음"]["back"], r["지어냄"]), (60, 64, 72), f표)
        dr.text((x + 300, 80), "평탄 %.2f" % r["평탄몫"], (60, 64, 72), f표)
        dr.text((x + 300, 104), "모서리 %.3f" % r["모서리몫"], (200, 40, 40), f표)
    o = os.path.join(OUT, "각면_%s.png" % case)
    sheet.save(o)
    sheet.resize((sheet.size[0] // 2, sheet.size[1] // 2)).save(o.replace(".png", "_작게.png"))
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "표": 표},
              open(os.path.join(OUT, "기록", "각면_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")

