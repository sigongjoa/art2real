"""**부품 경계가 원본 선화와 1:1 로 맞는지** 잰다. 그리고 그 지표로 튜닝한다.

재구성 오차는 판 **안쪽 색**만 본다 — 경계가 엉뚱한 데 있어도 색만 맞으면 통과한다.
조립에 쓰려면 **부품 윤곽 = 그려진 선**이어야 한다. 그걸 IoU 로 잰다.

    py -3.11 edge_iou.py <원본.png> <buildspec.json> [--tol 2] [--out 폴더]
    py -3.11 edge_iou.py <원본.png> --sweep tones=5,7,9 --scale 448   # 파라미터 튜닝

지표 셋:
    정밀도(precision)  우리 경계 중 실제 선 위에 있는 비율  — 낮으면 **없는 선을 그렸다**
    재현율(recall)     실제 선 중 우리 경계가 덮은 비율     — 낮으면 **선을 놓쳤다**
    IoU               둘의 종합

겹침 그림도 낸다: 초록=맞음 · 빨강=우리만(지어낸 경계) · 파랑=원본만(놓친 선).
"""
import argparse
import json
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = pathlib.Path(__file__).parent


def dil(m, k):
    if k <= 0:
        return m
    im = Image.fromarray((m * 255).astype(np.uint8), "L")
    return np.asarray(im.filter(ImageFilter.MaxFilter(2 * k + 1))) > 127


def line_mask(im, line=105):
    a = np.asarray(im).astype(float)
    lum = a.mean(2)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    bg = (r > 240) & (g > 240) & (b > 240)
    dark = (lum < line) & ~bg
    # **얇은 것만 선이다.** 두꺼운 검정(눈·언더아머)은 면이라 경계로 치면 안 된다
    thick = Image.fromarray((dark * 255).astype(np.uint8), "L")
    thick = np.asarray(thick.filter(ImageFilter.MinFilter(9))) > 127
    return dark & ~thick


def our_edges(spec, size):
    """설계도의 부품 윤곽을 원본 픽셀 좌표로 되돌려 그린다."""
    fit = spec.get("px_to_world")
    if not fit:
        return None
    k, ytop, ztop = fit["world_per_px"], fit["y_top_px"], fit["z_top"]
    cx = spec.get("center_x_px")
    if cx is None:                       # buildspec 에 없으면 이미지 중앙
        cx = size[0] / 2
    im = Image.new("L", size, 0)
    d = ImageDraw.Draw(im)
    n = 0
    for p in spec["parts"]:
        for poly in p.get("poly", []) or []:
            if len(poly) < 3:
                continue
            pts = [(cx + q[0] / k, ytop + (ztop - q[1]) / k) for q in poly]
            d.line(pts + [pts[0]], fill=255, width=1)
            n += 1
    return np.asarray(im) > 127, n


def step_mask(im, lines, thr=6):
    """**톤 계단** — 선은 안 그려졌지만 밝기가 급변하는 자리. 셀 채색의 명암 경계다.
    우리는 여기서도 판을 가르므로, 이걸 빼고 정밀도를 재면 맞는 경계를 틀렸다고 센다."""
    g = np.asarray(im.filter(ImageFilter.MedianFilter(5)).convert("L")).astype(float)
    gy, gx = np.gradient(g)
    return (np.hypot(gx, gy) > thr) & ~dil(lines, 1)


def score(ours, lines, tol, steps=None):
    lo, lt = dil(ours, tol), dil(lines, tol)
    prec_line = (ours & lt).sum() / max(1, ours.sum())
    rec = (lines & lo).sum() / max(1, lines.sum())
    iou = (lo & lt).sum() / max(1, (lo | lt).sum())
    if steps is None:
        return prec_line, rec, iou, prec_line
    real = lt | dil(steps, tol)              # 진짜 경계 = 선 + 톤 계단
    prec_all = (ours & real).sum() / max(1, ours.sum())
    return prec_line, rec, iou, prec_all


ENV = [None]


def sweep(src, spec_args, opts, out):
    """파라미터를 바꿔가며 IoU 로 고른다 — 눈으로 고르지 않는다."""
    rows = []
    for key, vals in opts.items():
        for v in vals:
            wd = out / f"sw_{key}{v}"
            subprocess.run([sys.executable, str(HERE / "art3d.py"), str(src),
                            "--out", str(wd), f"--{key}", str(v)] + spec_args,
                           capture_output=True)
            # buildspec 은 art3d 파라미터를 모른다 — 외형만 넘긴다
            bs = [sys.executable, str(HERE / "buildspec.py"), str(wd), "--name", "sw"]
            if ENV[0]:
                bs += ["--envelope", ENV[0]]
            subprocess.run(bs, capture_output=True)
            sp = wd / "buildspec.json"
            if not sp.exists():
                continue
            spec = json.loads(sp.read_text(encoding="utf-8"))
            art = json.loads((wd / "art3d.json").read_text(encoding="utf-8"))
            spec["center_x_px"] = art.get("center_x_px")
            im = Image.open(src).convert("RGB")
            if max(im.size) != art["size"][0]:
                im = im.resize(tuple(art["size"]), Image.LANCZOS)
            lines = line_mask(im)
            oe = our_edges(spec, im.size)
            if not oe:
                continue
            p, r, i, pa = score(oe[0], lines, 2, step_mask(im, lines))
            rows.append((key, v, len(spec["parts"]), p, r, i, pa))
            print(f"  --{key} {v:>3}  판 {len(spec['parts']):3d}  "
                  f"정밀도(선) {p:.3f}  정밀도(선+톤) {pa:.3f}  "
                  f"재현율 {r:.3f}  IoU {i:.3f}")
    if rows:
        best = max(rows, key=lambda t: t[5])
        print(f"\n최고: --{best[0]} {best[1]}  IoU {best[5]:.3f}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--tol", type=int, default=2, help="허용 오차 px")
    ap.add_argument("--out", default=None)
    ap.add_argument("--sweep", default=None,
                    help="예: tones=5,7,9  또는 min-area=80,120,200")
    ap.add_argument("--scale", type=int, default=448)
    ap.add_argument("--envelope", default=None, help="스윕 때 쓸 외형 json")
    a = ap.parse_args()
    src = pathlib.Path(a.src)
    out = pathlib.Path(a.out or src.parent / "edge_iou")
    out.mkdir(parents=True, exist_ok=True)

    if a.sweep:
        opts = {}
        for chunk in a.sweep.split(";"):
            k, v = chunk.split("=")
            opts[k] = [x for x in v.split(",")]
        ENV[0] = a.envelope
        sweep(src, ["--scale", str(a.scale)], opts, out)
        return

    spec = json.loads(pathlib.Path(a.spec).read_text(encoding="utf-8"))
    art_dir = pathlib.Path(a.spec).parent
    art = json.loads((art_dir / "art3d.json").read_text(encoding="utf-8"))
    spec["center_x_px"] = art.get("center_x_px")
    im = Image.open(src).convert("RGB")
    if list(im.size) != art["size"]:
        im = im.resize(tuple(art["size"]), Image.LANCZOS)
    lines = line_mask(im)
    oe = our_edges(spec, im.size)
    if not oe:
        print("px_to_world 가 없다 — 설계도에 매핑이 있어야 잰다"); sys.exit(1)
    ours, npoly = oe
    steps = step_mask(im, lines)
    p, r, i, pa = score(ours, lines, a.tol, steps)
    print(f"윤곽 {npoly}개 · 허용오차 {a.tol}px")
    print(f"  재현율        {r:.3f}   (그려진 선 중 우리 경계가 덮은 비율) <- 제일 중요")
    print(f"  정밀도(선만)   {p:.3f}   (우리 경계 중 선 위)")
    print(f"  정밀도(선+톤)  {pa:.3f}   (선 또는 **톤 계단** 위 — 이게 맞는 기준)")
    print(f"  IoU(선 기준)   {i:.3f}")
    print(f"  진짜 지어낸 경계 {1 - pa:.1%}")

    lo, lt = dil(ours, a.tol), dil(lines, a.tol)
    ls = dil(steps, a.tol)
    vis = np.asarray(im).astype(float) * 0.25 + 191
    # **빨간 것을 뭉뚱그리지 않는다** — 톤 계단 위(맞는 경계)와 진짜 지어낸 것은 다르다
    vis[lo & lt] = (40, 170, 70)             # 초록 = 그려진 선 위
    vis[lo & ~lt & ls] = (240, 150, 40)      # 주황 = 톤 계단 위 (선은 없지만 진짜 경계)
    vis[lo & ~lt & ~ls] = (220, 45, 40)      # 빨강 = 진짜 지어낸 것
    vis[~lo & lt] = (60, 110, 220)           # 파랑 = 놓친 선
    Image.fromarray(np.clip(vis, 0, 255).astype(np.uint8)).save(out / "edge_iou.png")
    json.dump({"tolerance_px": a.tol, "outlines": npoly,
               "precision_line": round(float(p), 4),
               "precision_line_or_tone": round(float(pa), 4),
               "recall": round(float(r), 4), "iou_line": round(float(i), 4),
               "invented": round(float(1 - pa), 4)},
              open(out / "edge_iou.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n{out / 'edge_iou.png'}")


if __name__ == "__main__":
    main()
