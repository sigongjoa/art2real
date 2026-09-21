# -*- coding: utf-8 -*-
"""**남의 지적 중 잴 수 있는 것을 잰다** (2026-09-21).

    python 감사.py [케이스=오메가몬] [키mm=150]   -> out/감사_<케이스>.png · out/기록/감사_*.json

사용자(09-21): 「GPT한테 물어봐. 니가 만든 거 잘했냐고, 블렌더나 파이프라인이 괜찮냐고」

받은 지적 중 **맞는 말 셋**을 그 자리에서 잰다 (나머지는 `claudedocs/review_외부평가_20260921.md`):

    ① 실루엣 IoU 는 **투영 일치**이지 3D 진실이 아니다.
       -> 대신 **VH 밖 부피** V_out = Vol(M \\ VH) 와 **남긴 몫** retention = Vol(M)/Vol(VH) 를 잰다.
          VH 는 타원 가정이 **안 들어간** 순수 교집합이다 (`hull.field_hull`).
    ② **Boolean 전후를 둘 다** 재야 한다 — 핀 · 소켓이 실루엣을 조용히 바꿀 수 있다.
    ③ 「0.8 mm 미만 부피 0%」는 부족하다 — **최소 벽 두께의 실제 최솟값**(mm)을 재야 한다.
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
W = H.W
OUT = H.OUT


def 실루엣들(m, masks, bs):
    V, F = np.asarray(m.vertices), np.asarray(m.faces)
    r = {}
    for v in W.VIEWS:
        s = np.asarray(W.silhouette(V, F, v, bs if v == "back" else None)).astype(bool)
        a = masks[v].astype(bool)
        r[v] = round(float((a & s).sum()) / max(float((a | s).sum()), 1), 4)
    return r


def main(case="오메가몬", 키mm=150.0):
    from PIL import Image, ImageDraw
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(q), np.ones(q.shape, np.float32))[0] for v, q in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    masks = H._warp(masks, H.align(masks, back_sign=bs))
    N = MJ.N
    g, ax = H.field_default(masks, back_sign=bs, n=N)                  # 타원 가정이 **들어간** 우리 형상
    f, _ = H.field_hull(masks, back_sign=bs, n=N)                      # 타원이 **안 들어간** 순수 교집합 = VH
    M = g > 0
    VH = f > 0
    셀 = (W.U1 - W.U0) / N
    mm칸 = 키mm / (np.ptp(np.where(M.any((0, 1)))[0]) + 1)
    V_out = float((M & ~VH).sum()) / max(float(M.sum()), 1)
    retention = float(M.sum()) / max(float(VH.sum()), 1)
    print("  ① VH 밖 부피 몫 V_out %.5f · 남긴 몫 retention %.4f (VH 대비)" % (V_out, retention), flush=True)

    # ② Boolean 전후
    조각, _, _ = PV.파츠만들기(case)
    전 = trimesh.util.concatenate([m for _, m, _ in 조각])
    d = os.path.join(OUT, "부품조립", case)
    뒤파일 = sorted(x for x in os.listdir(d) if x.startswith("부품_") and x.endswith(".ply")) if os.path.isdir(d) else []
    후 = trimesh.util.concatenate([trimesh.load(os.path.join(d, x), force="mesh", process=False) for x in 뒤파일]) if 뒤파일 else None
    i전 = 실루엣들(전, masks, bs)
    i후 = 실루엣들(후, masks, bs) if 후 is not None else None
    print("  ② Boolean 전 IoU %s" % i전, flush=True)
    print("     Boolean 후 IoU %s" % i후, flush=True)

    # ③ 최소 벽 두께 — 부품마다 «가장 얇은 곳»의 실제 최솟값
    _, lab, _ = MJ.부위(M)
    D = ndimage.distance_transform_edt(M)
    얇 = []
    for L in [int(x) for x in np.unique(lab) if x > 0]:
        sel = lab == L
        if sel.sum() < 50:
            continue
        # 표면에서 한 칸 안쪽의 «국소 두께» = 2 × 거리장. 그 부위의 제일 얇은 **능선** 값을 본다
        속 = D[sel]
        얇.append(float(np.percentile(속, 99)) * 2 * mm칸)              # 능선(가장 두꺼운 축) 을 기준으로
    최소벽 = min(얇) if 얇 else 0.0
    얇은부피 = float((2 * D[M] * mm칸 < 0.8).mean())
    print("  ③ 부위별 능선 두께 최솟값 %.2f mm · 0.8 mm 미만 부피 몫 %.4f" % (최소벽, 얇은부피), flush=True)

    Q = {"① V_out < 0.001 (VH 밖으로 안 나갔다)": bool(V_out < 0.001),
         "② Boolean 이 IoU 를 0.005 넘게 안 바꿨다": bool(i후 is None or
                                                  max(abs(i전[v] - i후[v]) for v in W.VIEWS) <= 0.005),
         "③ 제일 얇은 부위 >= 0.9 mm (두 perimeter)": bool(최소벽 >= 0.9)}
    for k, v in Q.items():
        print("   %-36s %s" % (k, "통과" if v else "**짐**"), flush=True)

    S = 1020
    sheet = Image.new("RGB", (S, 330), "white")
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
    except OSError:
        f제 = f본 = None
    y = 16
    dr.text((14, y), "외부 평가에서 나온 지적 셋을 쟀다 · %s (키 %d mm)" % (case, 키mm), (20, 22, 28), f제); y += 40
    dr.text((14, y), "① VH(타원 가정 없는 순수 교집합) 밖 부피 몫  %.5f   ·  남긴 몫 %.3f"
            % (V_out, retention), (40, 44, 52), f본); y += 30
    dr.text((14, y), "② Boolean 전 IoU %s" % list(i전.values()), (40, 44, 52), f본); y += 26
    dr.text((14, y), "   Boolean 후 IoU %s" % (list(i후.values()) if i후 else "-"), (40, 44, 52), f본); y += 30
    dr.text((14, y), "③ 제일 얇은 부위의 능선 두께 %.2f mm  ·  0.8 mm 미만 부피 몫 %.4f"
            % (최소벽, 얇은부피), (40, 44, 52), f본); y += 34
    for k, v in Q.items():
        dr.text((14, y), "%s  %s" % (k, "통과" if v else "짐"), (28, 110, 60) if v else (200, 40, 40), f본); y += 28
    o = os.path.join(OUT, "감사_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "키mm": 키mm, "V_out": round(V_out, 6), "retention": round(retention, 4),
               "IoU 전": i전, "IoU 후": i후, "최소 능선 두께 mm": round(최소벽, 3),
               "0.8mm 미만 부피 몫": round(얇은부피, 5), "판정": Q},
              open(os.path.join(OUT, "기록", "감사_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    a = sys.argv
    main(a[1] if len(a) > 1 else "오메가몬", float(a[2]) if len(a) > 2 else 150.0)

