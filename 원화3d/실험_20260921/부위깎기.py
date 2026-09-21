# -*- coding: utf-8 -*-
"""**부위마다 자기 실루엣으로 다시 깎는다** — 45° 유령과 옆 판때기를 겨냥한다 (2026-09-21 · 바퀴 2).

    python 부위깎기.py [케이스=오메가몬]   -> out/결과물/<케이스>/부위.ply · out/부위깎기_<케이스>.png

통짜가 지금 틀리는 까닭은 **곱**이다. 높이 z 에서 앞 판의 **왼팔 x 구간**과 옆 판의 **몸통 y 구간**이
그대로 곱해진다 — 팔이 몸통만큼 두꺼워지고(옆 판때기), 있지도 않은 덩어리가 생긴다(45° 유령).

부위를 먼저 가르면(`면자르기.py`) 곱을 **부위 안에서만** 시킬 수 있다:

    부위 L · 높이 z
      가로  앞 · 뒤에서 **그 부위가 제일 앞인 화소**의 x 구간        <- 잰 것
      깊이  옆에서 **그 부위가 제일 바깥인 화소**의 y 구간          <- 잰 것
            없으면 **깊이 = 가로**(원통 가정) — 옆 판에서 가려진 부위다. **지어낸 가정**(guessed)
      장    hull 과 같은 타원 식. 마지막에 **통짜 hull 장으로 덮개**를 씌운다 -> 원화 밖으로 못 나간다

문턱을 **먼저 적는다** (대조군은 같은 격자의 통짜):

    Q1  45° 렌더에서 유령이 준다 — **눈으로 본다**(숫자 아님). 옆 못덮음은 나빠지지 않는다
    Q2  **지어냄(원화 밖 화소)이 통짜보다 늘지 않는다**
    Q3  못덮음 앞 · 뒤가 통짜 대비 +1%p 이내
"""
import json
import os
import subprocess
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
import 결과물 as RS
import 면자르기 as MJ
W = H.W
OUT = H.OUT
N = MJ.N                          # 192 — 면자르기와 같은 격자


def 주인(lab, 축, 뒤=False):
    """그 축에서 **제일 바깥 복셀의 이름**. 축 0 = 옆(x) · 1 = 앞뒤(y)."""
    n = lab.shape[축]
    첫 = np.zeros([s for i, s in enumerate(lab.shape) if i != 축], np.int32)
    for j in (range(n - 1, -1, -1) if 뒤 else range(n)):
        v = lab.take(j, 축)
        새 = (첫 == 0) & (v > 0)
        첫[새] = v[새]
    return 첫


def 재다(V, F, masks, bs):
    못, 지어 = {}, 0
    for v in W.VIEWS:
        s = np.asarray(W.silhouette(V, F, v, bs if v == "back" else None)).astype(bool)
        a = masks[v].astype(bool)
        못[v] = round(float((a & ~s).sum()) / max(a.sum(), 1) * 100, 2)
        지어 += int((s & ~a).sum())
    return 못, 지어


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    d = os.path.join(OUT, "결과물", case)
    os.makedirs(d, exist_ok=True)
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    masks = H._warp(masks, H.align(masks, back_sign=bs))
    g, (u, _, z) = H.field_default(masks, back_sign=bs, n=N)          # 통짜 (대조군이자 덮개)
    f, _ = H.field_hull(masks, back_sign=bs, n=N)                     # 상한
    cell = (W.U1 - W.U0) / N
    배 = W.RES / N                                                     # 격자 -> 1024 화소
    O = g > 0
    D, lab, _ = MJ.부위(O)
    부품 = [int(i) for i in np.unique(lab) if i > 0]
    print("  부위 %d · 격자 %d" % (len(부품), N), flush=True)

    앞주 = 주인(lab, 1)                    # (x, z) — 앞에서 본 주인
    뒤주 = 주인(lab, 1, 뒤=True)
    옆주 = 주인(lab, 0)                    # (y, z)
    옆주2 = 주인(lab, 0, 뒤=True)

    새 = np.full_like(g, -2.0)
    원통 = 0
    for L in 부품:
        M = lab == L
        앞투 = M.any(1)                                                # (x, z) — 부위 제 그림자. **행마다 안 흔들린다**
        옆투 = M.any(0)                                                # (y, z)
        몫 = float(((옆주 == L) | (옆주2 == L)).sum()) / max(옆투.sum(), 1)   # 옆 실루엣을 제가 가진 몫
        쓴다 = 몫 >= 0.5                                                # **부위마다 한 번** 정한다 (줄마다 정하면 띠가 생긴다)
        원통 += int(not 쓴다)
        for k in range(N):
            fx = 앞투[:, k]
            if not fx.any() or not 옆투[:, k].any():
                continue
            X, A = H._축값([(int(s * 배), int(e * 배)) for s, e in H._구간(fx)], u)
            # 깊이 규칙 둘을 재 봤다 (09-21):
            #   A **부위마다 한 번** — 옆 실루엣의 제 몫 >= 0.5 면 잰 깊이, 아니면 원통 가정
            #     -> 못덮음 7.93 · 6.33 · 6.98 · 지어냄 2269   <- 이것을 쓴다
            #   B 줄마다 min(잰 깊이, 폭) — 절대 안 부푸는 규칙
            #     -> 못덮음 8.33 · **13.54** · 7.40 · 지어냄 1874. **옆을 너무 잃는다**
            if 쓴다 and 옆투[:, k].any():                                # 옆에서 제가 바깥인 부위 — **잰 깊이**
                Y, B = H._축값([(int(s * 배), int(e * 배)) for s, e in H._구간(옆투[:, k])], u)
            else:                                                      # 옆에서 가려진 부위 — **원통 가정**(guessed)
                ys = np.where(M[:, :, k])[1]
                if not len(ys):
                    continue
                cy, a = u[int(ys.mean())], float(np.median(A[fx]))
                Y, B = ((u - cy) / a) ** 2, np.full(N, a, np.float32)
            gl = (1.0 - X[:, None] - Y[None, :]) * np.minimum(A[:, None], B[None, :]) / 2 / cell
            새[:, :, k] = np.maximum(새[:, :, k], np.minimum(gl, f[:, :, k]))
    # hull 과 **같은** 높이 스무딩 — 안 걸면 높이마다 따로 푼 층이 그대로 남는다 (09-21 매끈장)
    from scipy import ndimage as _nd
    새 = np.minimum(np.maximum(_nd.gaussian_filter1d(새, H.SMOOTH_Z, axis=2), 새 - H.SMOOTH_GUARD), f)

    V, Fc = H.mesh_from_field(새, (u, u, z))
    m = trimesh.Trimesh(V, Fc, process=False)
    # **큰덩어리를 쓰면 안 된다** — 부위마다 깎으면 조각이 서로 떨어진다. 부스러기만 버린다
    ps = m.split(only_watertight=False)
    if len(ps) > 1:
        큰 = [q for q in ps if abs(q.volume) >= 0.005 * sum(abs(w.volume) for w in ps)]
        print("  조각 %d -> 부스러기 %d 버림" % (len(ps), len(ps) - len(큰)), flush=True)
        m = trimesh.util.concatenate(큰) if 큰 else m
    m.export(os.path.join(d, "부위.ply"))
    V0, F0 = H.mesh_from_field(g, (u, u, z))
    통 = RS.큰덩어리(trimesh.Trimesh(V0, F0, process=False))
    통.export(os.path.join(d, "통짜%d.ply" % N))

    못1, 지어1 = 재다(np.asarray(통.vertices), np.asarray(통.faces), masks, bs)
    못2, 지어2 = 재다(np.asarray(m.vertices), np.asarray(m.faces), masks, bs)
    Q = {"Q1 옆 못덮음 안 나빠짐": bool(못2["side"] <= 못1["side"] + 0.5),
         "Q2 지어냄 안 늚": bool(지어2 <= 지어1),
         "Q3 앞·뒤 못덮음 +1%p 이내": bool(못2["front"] <= 못1["front"] + 1 and 못2["back"] <= 못1["back"] + 1)}
    print("  통짜 못덮음 %s · 지어냄 %d" % (못1, 지어1), flush=True)
    print("  부위 못덮음 %s · 지어냄 %d · 원통 가정 부위 %d 개" % (못2, 지어2, 원통), flush=True)
    for k, v in Q.items():
        print("   %-24s %s" % (k, "통과" if v else "짐"), flush=True)

    open(RS.렌더py, "w", encoding="utf-8").write(RS.렌더소스)
    for tag, fn in (("통짜", "통짜%d.ply" % N), ("부위", "부위.ply")):
        subprocess.run([RS.BLENDER, "-b", "--python", RS.렌더py, "--", os.path.join(d, fn), d, tag],
                       capture_output=True, timeout=1800)
    S = 560
    흰 = os.path.join(OUT, "누끼", "%s_front" % case, "흰바탕.png")
    원 = Image.open(흰).convert("RGB").resize((S, S)) if os.path.exists(흰) else Image.new("RGB", (S, S), "white")
    rows = []
    for tag in ("통짜", "부위"):
        rows.append([원] + [Image.open(os.path.join(d, "렌더_%s_%s.png" % (tag, n))).convert("RGB").resize((S, S))
                            for n in ("앞", "사선", "옆", "뒤")])
    sheet = Image.new("RGB", (5 * (S + 8), 2 * (S + 8) + 70), "white")
    for i, ims in enumerate(rows):
        for j, im in enumerate(ims):
            sheet.paste(im, (j * (S + 8), 70 + i * (S + 8)))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 28)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 20)
    except OSError:
        f제 = f본 = None
    dr.text((14, 14), "부위마다 자기 실루엣으로 다시 깎았다 · %s   (위 통짜 · 아래 부위 %d 개)"
            % (case, len(부품)), (20, 22, 28), f제)
    dr.text((14, 44), "통짜 못덮음 %s · 지어냄 %d   /   부위 못덮음 %s · 지어냄 %d   · 원통 가정 부위 %d 개(guessed)"
            % ([float(x) for x in 못1.values()], 지어1, [float(x) for x in 못2.values()], 지어2, 원통), (90, 92, 100), f본)
    o = os.path.join(OUT, "부위깎기_%s.png" % case)
    sheet.save(o)
    sheet.resize((sheet.size[0] // 2, sheet.size[1] // 2)).save(o.replace(".png", "_작게.png"))
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "격자": N, "부위": len(부품), "원통 가정 부위": 원통,
               "통짜": {"못덮음": 못1, "지어냄": 지어1}, "부위": {"못덮음": 못2, "지어냄": 지어2}, "판정": Q},
              open(os.path.join(OUT, "기록", "부위깎기_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")



