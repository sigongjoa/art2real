# -*- coding: utf-8 -*-
"""**여러 데이터로 눈이 맞는지 본다.** CC0 모델 여럿에 파이프라인을 돌리고 정답과 대본다.

    python 대조.py            (있는 건 건너뛰고 이어서 한다)
        -> out/대조.json · out/대조.png · out/기록/대조_<날짜>.json

케이스는 **`벤치.json` 에 손으로 박은 것만** 쓴다. 자동 수집을 하면 집합이 실행마다
달라져서 어제 숫자와 오늘 숫자를 비교할 수 없다 — 실제로 12 -> 48 -> 35 -> 29 로 흔들렸고
그 사이에 내린 결론이 세 번 죽었다.

**튜닝셋과 봉인셋을 나눠 보고한다.** 상수(`LAM`·`THRESH`)는 튜닝셋에서만 맞추고
봉인셋은 그 뒤에 한 번 본다. 안 나누면 같은 데서 맞추고 같은 데서 자랑하게 된다.

한 케이스에서 「깊이 깎기가 이진 hull 보다 낫다」고 말한 게 진짜인지, 아니면 그 한 장에서만
그런 건지는 여러 장으로만 갈린다. 오늘 이 저장소에서 두 번 그 실수를 했다 —
재구성 오차 0.9 를 보고 통과라 했고, 견갑을 턴어라운드로 착각했다.

## 무엇을 대나

같은 모델에서 뽑은 3판으로 두 가지를 만들고, **둘 다 원본 메시와** 대본다.

    이진 hull    실루엣 세 장의 교집합. 단면이 축정렬 직사각형이다
    깊이 깎기    거기에 판 분할 + 크리스 인플레이션 깊이를 먹인 것

이기는 쪽이 몇 장에서 이기는지가 답이다. 3D IoU 차이의 **부호가 뒤집히는 장이 있으면**
「좋아졌다」는 말을 못 한다.

## 이게 검증 못 하는 것

전부 렌더한 판이라 세 판이 자동으로 일치한다. 그래서 `align` 과 판 불일치 처리는
여기서 **시험되지 않는다** (`시트.py` 참조). 손그림 턴어라운드는 여전히 오메가몬 하나뿐이다.
"""
import json
import os
import subprocess
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull as H
import win as W
import 정답 as J
from 계획 import _font

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
VROID = os.path.join(OUT, "vroid")


def models():
    """쓸 모델 (이름, 경로). VRoid 는 폴더 안 .vrm, Poly Pizza 는 out/모델 의 .glb."""
    out = []
    if os.path.isdir(VROID):
        for d in sorted(os.listdir(VROID)):
            p = os.path.join(VROID, d)
            if os.path.isdir(p):
                v = [f for f in os.listdir(p) if f.lower().endswith(".vrm")]
                if v:
                    out.append((d, os.path.join(p, v[0])))
    poly = os.path.join(OUT, "모델")
    if os.path.isdir(poly):
        for f in sorted(os.listdir(poly)):
            if f.lower().endswith(".glb"):
                out.append((os.path.splitext(f)[0], os.path.join(poly, f)))
    return out


def sheets():
    """받아둔 모델마다 판을 뽑는다. 이미 있으면 건너뛴다."""
    for name, path in models():
        if os.path.exists(os.path.join(OUT, "시트", name, "truth.glb")):
            continue
        print("  판 뽑기 %s" % name)
        r = subprocess.run([sys.executable, os.path.join(HERE, "시트.py"), path, "--이름", name],
                           cwd=HERE, capture_output=True, text=True, encoding="utf-8")
        if r.returncode:
            print("     실패: %s" % (r.stderr or "")[-160:])
    H.register_sheets()


def build(case):
    """정렬까지 끝낸 마스크·깊이와 두 판본의 복셀."""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    bs = H.CASES[case]["back_sign"]
    masks, deps = {}, {}
    for v, f in src.items():
        d = H.declutter(W.art_mask(os.path.join(base, f)))
        masks[v], deps[v] = H.to_win(d, H.load_depth(v, d, case=case))
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    deps = {v: H._warp_one(a, v, p) for v, a in deps.items()}
    plain, axes = H.carve(masks, back_sign=bs)
    deep, _ = H.carve_depth(masks, deps, back_sign=bs)
    return plain, deep, axes, p


def to_mesh(vox, axes):
    V, F = H.mesh_from(vox, axes)
    m = trimesh.Trimesh(V, F, process=True)
    parts = m.split(only_watertight=False)
    if len(parts) > 1:
        m = max(parts, key=lambda q: abs(q.volume))
    if m.volume < 0:
        m.invert()
    return m


def bench():
    """`벤치.json` — 손으로 고정한 케이스 목록. 없으면 멈춘다."""
    p = os.path.join(HERE, "벤치.json")
    assert os.path.exists(p), "벤치.json 이 없다. 케이스를 손으로 고정하고 시작할 것"
    return json.load(open(p, encoding="utf-8"))


def main():
    sheets()
    b = bench()
    split = {c["name"]: c["split"] for c in b["cases"]}
    cases = [c["name"] for c in b["cases"]]
    missing = [c for c in cases if c not in H.CASES]
    assert not missing, "벤치.json 에 있는데 판이 없다: %s" % missing[:3]
    rows, broken = [], []
    for c in cases:
        if not os.path.exists(os.path.join(OUT, "깊이", c, "front", "depth.npy")):
            print("  깊이 %s" % c)
            subprocess.run([sys.executable, os.path.join(HERE, "깊이.py"), c],
                           cwd=HERE, capture_output=True)
        try:
            t = trimesh.load(os.path.join(OUT, "시트", c, "truth.glb"), force="mesh")
            # **서 있는 물건만 센다.** 창 규약이 키로 정규화하므로, 키가 대표 치수가 아닌
            # 물건(옆으로 퍼진 조각상·누운 것)은 판을 뽑는 것 자체가 뜻이 없다.
            # 실측: statue_Stag 은 높이 1.0 에 깊이 3.64 였다
            ex = t.bounds[1] - t.bounds[0]
            if ex[1] > 1.6 * ex[2] or ex[0] > 2.2 * ex[2]:
                print("  %-22s 건너뜀 — 서 있는 물건이 아니다 (가로 %.2f 깊이 %.2f 키 %.2f)"
                      % (c, ex[0], ex[1], ex[2]))
                continue
            plain, deep, axes, fit = build(c)
            T, ot = J.grid(t)
            got, bad = {}, None
            for tag, vox in (("이진", plain), ("깊이", deep)):
                G, og = J.grid(to_mesh(vox, axes))
                A, B = J.common(T, ot, G, og)
                if tag == "이진":
                    bad = J.invariant(A, B)      # **자가 틀렸는지 먼저 본다**
                got[tag] = {"iou": (A & B).sum() / max((A | B).sum(), 1),
                            "vol": B.sum() / max(A.sum(), 1),
                            "miss": (A & ~B).sum() / max(A.sum(), 1)}
            if bad:
                broken.append({"case": c, "why": bad})
                print("  %-22s 채점 불가 — %s" % (c, " · ".join(bad)))
                continue
            r = {"case": c, "fit": [round(float(x), 3) for x in fit],
                 "box": round(H.box_score(deep), 2), **{k + "_" + kk: round(float(vv), 3)
                                                        for k, v in got.items() for kk, vv in v.items()}}
            rows.append(r)
            print("  %-22s 이진 %.3f -> 깊이 %.3f  (%+.3f)"
                  % (c, r["이진_iou"], r["깊이_iou"], r["깊이_iou"] - r["이진_iou"]))
        except Exception as e:
            print("  %-22s 실패 %s: %s" % (c, type(e).__name__, str(e)[:90]))
            continue

    if broken:
        print("\n  채점 불가 %d 장 — 불변식(hull 은 정답을 포함한다)을 어긴다:" % len(broken))
        for b in broken:
            print("    %-38s %s" % (b["case"][:38], " · ".join(b["why"])))
        json.dump(broken, open(os.path.join(OUT, "채점불가.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    if not rows:
        return
    json.dump(rows, open(os.path.join(OUT, "대조.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    for r in rows:
        r["split"] = split.get(r["case"], "?")
    d = np.array([r["깊이_iou"] - r["이진_iou"] for r in rows])
    print("\n  %d 장 · 깊이 깎기가 이긴 장 %d · 평균 차 %+.3f (최소 %+.3f · 최대 %+.3f)"
          % (len(rows), int((d > 0).sum()), d.mean(), d.min(), d.max()))
    for sp in ("tune", "holdout"):
        v = [r for r in rows if r["split"] == sp]
        if not v:
            continue
        dd = np.array([r["깊이_iou"] - r["이진_iou"] for r in v])
        print("    %-8s n=%2d · 형태 중앙 %.3f · 못덮음 중앙 %.3f · 이득 %+.4f · 이긴장 %d/%d"
              % (sp, len(v), np.median([r["깊이_iou"] for r in v]),
                 np.median([r["깊이_miss"] for r in v]), dd.mean(), (dd > 0).sum(), len(v)))
    # **헤드라인 한 줄.** 봉인셋 기준이다 — 튜닝셋 숫자는 자기 자랑이다
    ho = [r for r in rows if r["split"] == "holdout"] or rows
    print("\n  기준선 | 형태 %.3f · 못덮음 %.3f · 완주 %d/%d · 채점불가 %d  (봉인 %d장)"
          % (np.median([r["깊이_iou"] for r in ho]), np.median([r["깊이_miss"] for r in ho]),
             len(rows), len(cases), len(broken), len(ho)))

    # 기록을 쌓는다 — 덮어쓰면 진행이 안 보인다
    import datetime
    hist = os.path.join(OUT, "기록")
    os.makedirs(hist, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    json.dump({"때": stamp, "케이스": len(cases), "점수낸장": len(rows),
               "채점불가": [b["case"] for b in broken],
               "LAM": H.LAM, "THRESH": H.THRESH, "rows": rows},
              open(os.path.join(hist, "대조_%s.json" % stamp), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("  기록 -> out/기록/대조_%s.json" % stamp)

    # 그림 — 장마다 이진 -> 깊이
    Wd, Ht = 960, 80 + len(rows) * 30 + 60
    im = Image.new("RGB", (Wd, Ht), "white")
    g = ImageDraw.Draw(im)
    lo, hi = min(min(r["이진_iou"], r["깊이_iou"]) for r in rows) - .02, \
             max(max(r["이진_iou"], r["깊이_iou"]) for r in rows) + .02
    xf = lambda v: 320 + (v - lo) / max(hi - lo, 1e-6) * (Wd - 400)
    g.text((20, 14), "3D IoU — 이진 hull → 깊이 깎기. 기준은 **원본 메시**", font=_font(18), fill=(20, 20, 20))
    g.text((20, 40), "벤치.json 의 %d 장. ● = 봉인셋. 판은 전부 렌더라 세 판이 자동으로 일치한다" % len(rows),
           font=_font(11), fill=(130, 130, 130))
    for i, r in enumerate(rows):
        y = 76 + i * 30
        up = r["깊이_iou"] > r["이진_iou"]
        g.text((20, y - 7), ("● " if r.get("split") == "holdout" else "  ") + r["case"][:32],
               font=_font(12), fill=(40, 40, 40))
        x0, x1 = xf(r["이진_iou"]), xf(r["깊이_iou"])
        g.line([x0, y, x1, y], fill=(60, 150, 90) if up else (200, 80, 80), width=3)
        g.ellipse([x0 - 4, y - 4, x0 + 4, y + 4], fill="white", outline=(150, 150, 150), width=2)
        g.ellipse([x1 - 4, y - 4, x1 + 4, y + 4], fill=(60, 150, 90) if up else (200, 80, 80))
        g.text((x1 + 10, y - 7), "%.3f (%+.3f)" % (r["깊이_iou"], r["깊이_iou"] - r["이진_iou"]),
               font=_font(11), fill=(60, 150, 90) if up else (200, 80, 80))
    g.text((20, Ht - 34), "%d 장 중 %d 장에서 깊이 깎기가 이겼다 · 평균 %+.3f"
           % (len(rows), int((d > 0).sum()), d.mean()), font=_font(13), fill=(20, 20, 20))
    im.save(os.path.join(OUT, "대조.png"))
    print("  -> out/대조.png · out/대조.json")


if __name__ == "__main__":
    main()
