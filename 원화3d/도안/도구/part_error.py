"""**부품이 원화와 무엇이 다른지 분해한다.** IoU 한 숫자로는 못 고친다.

    py -3.11 part_error.py <art3d출력폴더> <verify출력폴더> <envelope.json>

원화(`labels.npy`)가 GT 다 — **절대 모델 쪽으로 옮기지 않는다.** 손실의 정의를 바꾸는
것은 손실을 줄이는 게 아니다.

오차를 네 조각으로 가른다. 각각 고치는 방법이 다르다:

    shift       질량중심이 어긋난 거리(px)   -> 매핑/좌표 오류
    scale       면적비                        -> 단순화 허용오차·번짐
    dilate      모델을 몇 px 깎아야 제일 맞나 -> 선 띠를 먹은 만큼 (균일 두꺼움)
    shape       치우침·크기·두께를 다 보정한 뒤 남는 IoU 손실 -> 진짜 모양이 다름

`shape` 만 남으면 생성기를 고쳐야 하고, 앞의 셋은 추출 파라미터로 줄어든다.
"""
import json
import sys

import numpy as np
from PIL import Image, ImageFilter


def erode(m, k):
    if k <= 0:
        return m
    im = Image.fromarray((m * 255).astype(np.uint8), "L")
    return np.asarray(im.filter(ImageFilter.MinFilter(2 * k + 1))) > 127


def iou(a, b):
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 0.0


def shift_to(mod, ref):
    """최적 평행이동을 찾아 적용. 반환: (이동한 모델, dy, dx)"""
    best, bd = iou(mod, ref), (0, 0)
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            v = iou(np.roll(np.roll(mod, dy, 0), dx, 1), ref)
            if v > best:
                best, bd = v, (dy, dx)
    return np.roll(np.roll(mod, bd[0], 0), bd[1], 1), bd


def main():
    d, vo, envp = sys.argv[1], sys.argv[2], sys.argv[3]
    spec = json.load(open(f"{d}/buildspec.json", encoding="utf-8"))
    fr = json.load(open(f"{vo}/frames.json"))
    env = json.load(open(envp, encoding="utf-8"))
    lab = np.load(f"{d}/labels.npy")
    f = spec["px_to_world"]
    k, ytop, ztop = f["world_per_px"], f["y_top_px"], f["z_top"]
    cx0 = env["px"]["center_x"]

    rows = []
    for nm, fi in fr.items():
        m = lab == fi["region"]
        if not m.any():
            continue
        s, R = fi["span"], fi["res"]
        box = (round(cx0 + (fi["cx"] - s / 2) / k),
               round(ytop + (ztop - (fi["cz"] + s / 2)) / k),
               round(cx0 + (fi["cx"] + s / 2) / k),
               round(ytop + (ztop - (fi["cz"] - s / 2)) / k))
        ref = np.asarray(Image.fromarray((m * 255).astype(np.uint8), "L")
                         .crop(box).resize((R, R), Image.NEAREST)) > 127
        mod = np.asarray(Image.open(f"{vo}/{nm}.png"))[..., 3] > 40
        if (ref | mod).sum() < 50:
            continue
        i0 = iou(mod, ref)
        # px 배율: 원화 1px 이 렌더 몇 px 인가 (창을 R 로 늘렸으므로)
        ppx = R / max(1.0, (box[2] - box[0]))
        ry, rx = np.where(ref); my, mx = np.where(mod)
        dcen = float(np.hypot(my.mean() - ry.mean(), mx.mean() - rx.mean())) / ppx
        # ① 치우침 보정
        m1, d1 = shift_to(mod, ref)
        # ② 두께 보정 — 몇 px 깎아야 제일 맞나 (원화 px 단위)
        bestk, best1 = 0, iou(m1, ref)
        for kk in range(1, int(4 * ppx) + 1):
            v = iou(erode(m1, kk), ref)
            if v > best1:
                best1, bestk = v, kk
        m2 = erode(m1, bestk)
        m2, _ = shift_to(m2, ref)          # 깎으면 중심이 또 밀린다
        rows.append({
            "id": nm, "make": fi["make"], "iou": round(i0, 3),
            "scale": round(mod.sum() / max(1, ref.sum()), 2),
            "shift_px": round(dcen, 2),
            "dy": d1[0] / ppx, "dx": d1[1] / ppx,
            "dilate_px": round(bestk / ppx, 2),
            "iou_after": round(iou(m2, ref), 3),
        })
    rows.sort(key=lambda r: r["iou"])
    a = {c: np.array([r[c] for r in rows], float)
         for c in ("iou", "scale", "shift_px", "dilate_px", "iou_after")}
    print(f"부품 {len(rows)}개 · GT = 원화 labels.npy (고정)\n")
    print(f"{'부품':22s}{'종류':8s}{'IoU':>7s}{'크기':>7s}{'치우침px':>9s}"
          f"{'두꺼움px':>9s}{'보정후':>8s}")
    for r in rows[:14]:
        print(f"{r['id']:22s}{str(r['make']):8s}{r['iou']:7.3f}{r['scale']:7.2f}"
              f"{r['shift_px']:9.2f}{r['dilate_px']:9.2f}{r['iou_after']:8.3f}")
    print(f"\n중앙값   IoU {np.median(a['iou']):.3f} · 크기 {np.median(a['scale']):.2f} "
          f"· 치우침 {np.median(a['shift_px']):.2f}px · 두꺼움 "
          f"{np.median(a['dilate_px']):.2f}px · 보정후 {np.median(a['iou_after']):.3f}")
    gain = np.median(a['iou_after']) - np.median(a['iou'])
    print(f"보정으로 회수되는 몫 {gain:+.3f} — 이만큼은 추출 파라미터로 줄일 수 있다.")
    print(f"보정 후에도 남는 손실 {1 - np.median(a['iou_after']):.3f} = 진짜 모양 차이")
    json.dump(rows, open(f"{vo}/part_error.json", "w"), indent=1)


if __name__ == "__main__":
    main()
