# -*- coding: utf-8 -*-
"""**패널이 내놓은 지표를 잰다** — 말이 아니라 숫자로 (2026-09-21).

    python 패널지표.py [케이스=오메가몬] [키mm=150]   -> out/패널지표_<케이스>.png · out/기록/패널지표_*.json

사용자(09-21): 「gpt, grok, gemini한테 토론 시키는 거지. 니가 사회자로」

패널 규칙: **주장은 측정으로만 채택한다.** 받은 지표 중 **지금 잴 수 있는 둘**을 잰다.

    E_joint = arccos(-n_A · n_B)      두 부품의 **맞대는 면**이 정확히 마주 보는가 (목표 < 1°)
                                      ⚠ 우리는 접촉면에 평면 **하나**를 맞춰 왔다 — 그러면 0 이 나올 수밖에 없다.
                                      그래서 **A 쪽과 B 쪽 경계면에 평면을 따로 맞춰** 잰다.
    V_inter = Vol(A ⊕ t ∩ B ⊕ t)      공차 t 만큼 부풀렸을 때 **부품이 서로 파고드는 부피**
                                      (Boolean 전후 IoU 차 0.0003 은 조립 가부를 증명하지 못한다)

안 잰 것과 까닭도 같이 적는다 — **법선 정렬 오차**(원화 깊이맵이 필요한데 09-19·09-20 에
톤→법선은 세 번 다른 길로 막혔다) · **음영 MSE**(09-21 에 색에 오염돼 실패했다).
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
W = H.W
OUT = H.OUT
공차 = 0.25                     # mm. 패널이 준 값 (given)


def 면법선(mask3d, 이웃, 셀):
    """한쪽 부위의 **경계 껍질**에 평면을 맞춰 법선을 낸다 (양쪽을 따로 재려고)."""
    pts = np.argwhere(mask3d & ndimage.binary_dilation(이웃, np.ones((3, 3, 3), bool))).astype(float)
    if len(pts) < 12:
        return None
    c = pts.mean(0)
    _, _, vt = np.linalg.svd(pts - c, full_matrices=False)
    return vt[2] / max(np.linalg.norm(vt[2]), 1e-12)


def main(case="오메가몬", 키mm=150.0):
    from PIL import Image, ImageDraw
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(q), np.ones(q.shape, np.float32))[0] for v, q in raw.items()}
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    masks = H._warp(masks, H.align(masks, back_sign=bs))
    N = MJ.N
    g, ax = H.field_default(masks, back_sign=bs, n=N)
    셀 = (W.U1 - W.U0) / N
    O = g > 0
    _, lab, _ = MJ.부위(O)
    부품 = [int(i) for i in np.unique(lab) if i > 0]
    mm칸 = 키mm / (np.ptp(np.where(O.any((0, 1)))[0]) + 1)

    # ① E_joint — A 쪽 · B 쪽 경계면에 평면을 **따로** 맞춰 각을 잰다
    각들 = []
    for i, a in enumerate(부품):
        for b in 부품[i + 1:]:
            A, B = lab == a, lab == b
            if not (A & ndimage.binary_dilation(B, np.ones((3, 3, 3), bool))).any():
                continue
            nA, nB = 면법선(A, B, 셀), 면법선(B, A, 셀)
            if nA is None or nB is None:
                continue
            c = float(np.clip(abs(np.dot(nA, nB)), 0, 1))               # 방향 부호는 무시 (면끼리의 각)
            각들.append({"부위": [a, b], "각도": round(float(np.degrees(np.arccos(c))), 2)})
    각들.sort(key=lambda r: -r["각도"])
    중앙각 = float(np.median([r["각도"] for r in 각들])) if 각들 else 0.0

    # ② V_inter — 공차만큼 부풀렸을 때 서로 파고드는 부피 (복셀로 잰다 · 불리언보다 싸고 안 깨진다)
    t칸 = max(1, int(round(공차 / mm칸)))
    간섭 = []
    for i, a in enumerate(부품):
        for b in 부품[i + 1:]:
            A, B = lab == a, lab == b
            if not (A & ndimage.binary_dilation(B, np.ones((3, 3, 3), bool))).any():
                continue
            Ad = ndimage.binary_dilation(A, iterations=t칸)
            Bd = ndimage.binary_dilation(B, iterations=t칸)
            겹 = float((Ad & Bd).sum())
            간섭.append({"부위": [a, b], "간섭 부피 몫": round(겹 / max(float(A.sum() + B.sum()), 1), 5),
                        "간섭 mm³": round(겹 * (mm칸 ** 3), 1)})
    간섭.sort(key=lambda r: -r["간섭 부피 몫"])
    최대간섭 = 간섭[0]["간섭 부피 몫"] if 간섭 else 0.0

    Q = {"E_joint 중앙 < 5°": bool(중앙각 < 5.0),
         "E_joint 최대 < 15°": bool((각들[0]["각도"] if 각들 else 0) < 15.0),
         "공차 %.2fmm 에서 간섭 몫 < 0.05" % 공차: bool(최대간섭 < 0.05)}
    print("  ① E_joint (양쪽 평면을 따로 맞춰 잰 각) 중앙 %.2f° · 최대 %.2f° · 쌍 %d"
          % (중앙각, 각들[0]["각도"] if 각들 else 0, len(각들)), flush=True)
    for r in 각들[:6]:
        print("     부위 %s · %5.2f°" % (r["부위"], r["각도"]), flush=True)
    print("  ② 공차 %.2f mm(= %d 칸) 부풀림 · 최대 간섭 몫 %.5f · 최대 %.1f mm³"
          % (공차, t칸, 최대간섭, 간섭[0]["간섭 mm³"] if 간섭 else 0), flush=True)
    for k, v in Q.items():
        print("   %-30s %s" % (k, "통과" if v else "**짐**"), flush=True)

    S = 1040
    sheet = Image.new("RGB", (S, 190 + 26 * (min(len(각들), 8) + len(Q) + 4)), "white")
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
    except OSError:
        f제 = f본 = None
    y = 16
    dr.text((14, y), "패널이 내놓은 지표를 쟀다 · %s (키 %d mm)" % (case, 키mm), (20, 22, 28), f제); y += 40
    dr.text((14, y), "① E_joint = arccos(-nA·nB) — 맞대는 면이 마주 보는가 (양쪽 평면을 따로 맞췄다)",
            (60, 64, 72), f본); y += 28
    dr.text((14, y), "   중앙 %.2f° · 최대 %.2f° · 쌍 %d" % (중앙각, 각들[0]["각도"] if 각들 else 0, len(각들)),
            (40, 44, 52), f본); y += 30
    for r in 각들[:6]:
        dr.text((40, y), "부위 %s · %5.2f°" % (r["부위"], r["각도"]), (40, 44, 52), f본); y += 26
    y += 8
    dr.text((14, y), "② V_inter — 공차 %.2f mm 부풀렸을 때 파고드는 부피. 최대 몫 %.5f (%.1f mm³)"
            % (공차, 최대간섭, 간섭[0]["간섭 mm³"] if 간섭 else 0), (60, 64, 72), f본); y += 32
    for k, v in Q.items():
        dr.text((14, y), "%s  %s" % (k, "통과" if v else "짐"), (28, 110, 60) if v else (200, 40, 40), f본); y += 28
    o = os.path.join(OUT, "패널지표_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump({"케이스": case, "키mm": 키mm, "공차mm": 공차, "E_joint": 각들, "E_joint 중앙": round(중앙각, 3),
               "간섭": 간섭[:12], "판정": Q,
               "안 잰 것": {"법선 정렬 오차": "원화 깊이맵이 필요 — 톤→법선은 09-19·09-20 에 세 번 막혔다",
                          "음영 MSE": "09-21 에 색에 오염돼 실패 (원화 59.5 vs 우리 26.0 으로 뒤집힘)"}},
              open(os.path.join(OUT, "기록", "패널지표_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    a = sys.argv
    main(a[1] if len(a) > 1 else "오메가몬", float(a[2]) if len(a) > 2 else 150.0)
