# -*- coding: utf-8 -*-
"""**민감도 카드 1 — TripoSG 는 음영에 반응하나** (2026-09-17). 계획 `claudedocs/plan_음영민감도_20260917.md` (판정 먼저 적음).

    python 음영민감도.py 입력    SDXL 점토 렌더 한 장 -> logR · 대조 logN -> 판본 5 장 (k0 k33 k67 k1 C) -> 스크래치 shade/
    python 음영민감도.py 배관    h3/hermit_front.glb 를 3판맞춤 경로로 다시 재서 carve.json 과 대조
    python 음영민감도.py 생성    TripoSG 5 판본 × 씨앗 42 · 7 · 123 (imggen venv · 로드 한 번 · 이어 돌리기)
    python 음영민감도.py 재기    15 메시 -> out/기록/음영민감도_<때>.json
    python 음영민감도.py 판정    Q1 · Q2 · Q3
    python 음영민감도.py 그림    -> out/은둔자_음영민감도.png

음영만 바꾼다: 윤곽(알파) · 색 · 얼굴 창은 다섯 판본이 같다. 흐린 명암(σ 8)만 밝기에 더한다 — 줄무늬 같은 잔결은 안 들어간다.
"""
import glob
import json
import os
import subprocess
import sys
import time

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = r"G:\art2real\원화3d"
for d in ("", "실험_20260913", "실험_20260915", "실험_20260916", "실험_20260917"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)

S = r"C:\Users\zesky\AppData\Local\Temp\claude\G--art2real\612c5d2a-3321-47b1-8ebf-c897df4a0801\scratchpad\shade"
SRC = os.path.join("out", "은둔자_자료", "삼면", "front.png")
PY = r"D:\imggen\venv\Scripts\python.exe"
TRI = r"G:\art2real\트레일\trail4_gen3d\run_triposg.py"
VARS = [("k0", 0.0), ("k33", 0.33), ("k67", 0.67), ("k1", 1.0), ("C", None)]
SEEDS = (42, 7, 123)
UP, SIG, AMP = 2, 8.0, 15.0
FACE = (30, 125, 180, 270)            # 2 배 판 (y0, y1, x0, x1) — 머리 전체
TAG = "음영민감도 v2 · Lab L 더하기 · 세기 σL 15 · σ8 · SDXL 0.50 씨앗5 · 씨앗 42/7/123 · P = 옆 못덮음+넘침 (맞춤 없음) (2026-09-17)"


def blur_in(x, a):
    return nd.gaussian_filter(x * a, SIG) / np.maximum(nd.gaussian_filter(a, SIG), 1e-6)


def labL(rgb):
    lab = cv2.cvtColor(np.rint(rgb).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float64)
    return lab[..., 0] * 100 / 255, lab


def base():
    im = Image.open(SRC).convert("RGBA")
    im = im.resize((im.width * UP, im.height * UP), Image.LANCZOS)
    a = np.asarray(im).astype(np.float64)
    al = a[..., 3] / 255.0
    rgb = a[..., :3] * al[..., None] + 255 * (1 - al[..., None])        # 흰 바탕 (SDXL 입력 · 곱하기 기준)
    return rgb, al, (a[..., 3] > 127)


def make_inputs():
    os.makedirs(S, exist_ok=True)
    rgb, al, m = base()
    white = os.path.join(S, "white.png")
    Image.fromarray(rgb.astype(np.uint8)).save(white)
    clay = os.path.join(S, "clay.png")
    if not os.path.exists(clay):
        subprocess.run([PY, os.path.join(HERE, "실험_20260917", "음영민감도_sdxl.py"), white, clay], check=True)
    c = np.asarray(Image.open(clay).convert("RGB")).astype(np.float64)
    A = m.astype(np.float64)
    # 밝기(Lab L)에 **더한다** — 곱하기는 검은 망토(몫 0.87)에서 0 이 된다 (실행 전 v1 입력에서 확인)
    Lo, lab = labL(rgb)
    dL = blur_in(labL(c)[0], A) - blur_in(Lo, A)
    w = np.zeros(A.shape)
    y0, y1, x0, x1 = FACE
    w[y0:y1, x0:x1] = 1
    keep = 1 - np.clip(nd.gaussian_filter(w, 6) * 1.5, 0, 1)          # 얼굴 창 = 0
    inside = m & (keep > 0.99)
    shade = (dL - dL[inside].mean()) / dL[inside].std() * AMP * keep * A      # 모양은 SDXL · 세기는 AMP
    rng = np.random.default_rng(0)
    n = blur_in(rng.standard_normal(A.shape), A)
    noise = (n - n[inside].mean()) / n[inside].std() * AMP * keep * A
    for name, k in VARS:
        f = noise if k is None else k * shade
        if k == 0:
            out = rgb
        else:
            lab2 = lab.copy()
            lab2[..., 0] = np.clip(Lo + f, 0, 100) * 255 / 100
            out = cv2.cvtColor(np.rint(lab2).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float64)
        img = np.dstack([np.rint(out).astype(np.uint8), (al * 255).astype(np.uint8)])
        Image.fromarray(img).save(os.path.join(S, name + ".png"))
        if k == 0:
            assert np.array_equal(np.asarray(Image.open(os.path.join(S, "k0.png")))[..., :3], np.rint(rgb).astype(np.uint8)), "k0 가 원화와 다르다"
    logR, logN = shade, noise
    np.save(os.path.join(S, "logR.npy"), logR)
    np.save(os.path.join(S, "logN.npy"), logN)
    print("  음영 안쪽 표준편차 %.2f · 얼룩 %.2f (L 단위)" % (logR[inside].std(), logN[inside].std()))
    sheet = [np.asarray(Image.open(os.path.join(S, v + ".png")).convert("RGB")) for v, _ in VARS]
    Image.fromarray(np.hstack([np.asarray(Image.open(clay).convert("RGB"))] + sheet)).save(os.path.join(S, "inputs_sheet.png"))


def setup():
    import hull as H
    import win as W
    H.CASES["은둔자"] = {"src": {v: v + ".png" for v in W.VIEWS}, "dir": os.path.join("out", "은둔자_자료", "삼면"), "back_sign": +1}
    src, bd = H.CASES["은둔자"]["src"], H.art_dir("은둔자")
    masks = {v: H.to_win(H.declutter(W.art_mask(os.path.join(bd, f)))) for v, f in src.items()}
    bs = H.CASES["은둔자"]["back_sign"]
    masks = H._warp(masks, H.align(masks, back_sign=bs))
    plain, axes = H.carve(masks, back_sign=bs)
    return masks, bs, axes


def measure_one(path, masks, bs, axes, fit):
    import trimesh
    import 생성3D as G3
    from 생성깎기 import sil_fit, voxelize
    from 조각생성 import trim
    g = trim(trimesh.load(path, force="mesh"))
    sc, V, yaw, mir = G3.orient(g.vertices, masks)
    ratio = float(np.ptp(V[:, 1]) / np.ptp(V[:, 0]))
    if fit:
        V = G3.fit_to_art(V, masks)
    r = sil_fit(voxelize(trimesh.Trimesh(V, np.asarray(g.faces), process=False), axes), masks, bs, axes)
    r.update({"회전": yaw, "반전": mir, "두께비": round(ratio, 4)})
    return r


def pipe_check():
    masks, bs, axes = setup()
    r = measure_one(os.path.join(os.path.dirname(S), "h3", "hermit_front.glb"), masks, bs, axes, fit=True)
    want = json.load(open(os.path.join(os.path.dirname(S), "h3", "carve.json"), encoding="utf-8"))["생성(깎기 전)"]
    print("  배관", r, "· 기록", want)
    for k in ("못덮음_side", "넘침_side"):
        assert abs(r[k] - want[k]) <= 0.005, "배관 실패 %s %.4f vs %.4f" % (k, r[k], want[k])
    print("  배관 통과")


def generate():
    ims = [os.path.join(S, v + ".png") for v, _ in VARS]
    subprocess.run([PY, TRI, *ims, "--outdir", os.path.join(S, "tri"), "--no-rmbg", "--seeds", ",".join(map(str, SEEDS))],
                   cwd=os.path.dirname(TRI), check=True)


def art_ratio(masks):
    wf = np.ptp(np.nonzero(masks["front"].any(0))[0])
    ws = np.ptp(np.nonzero(masks["side"].any(0))[0])
    return float(ws / wf)


def run_measure():
    masks, bs, axes = setup()
    rows = []
    for v, _ in VARS:
        for sd in SEEDS:
            p = os.path.join(S, "tri", "%s_s%d.glb" % (v, sd))
            r = {"판본": v, "씨앗": sd}
            a = measure_one(p, masks, bs, axes, fit=False)
            b = measure_one(p, masks, bs, axes, fit=True)
            r.update({"P": round(a["못덮음_side"] + a["넘침_side"], 4), "정면": round(a["못덮음_front"] + a["넘침_front"], 4),
                      "P_맞춤": round(b["못덮음_side"] + b["넘침_side"], 4), "맞춤없음": a, "맞춤": b})
            rows.append(r)
            print("  %-4s s%-4d P %.4f · 정면 %.4f · P맞춤 %.4f · 두께비 %.3f · 회전 %d 반전 %+d"
                  % (v, sd, r["P"], r["정면"], r["P_맞춤"], a["두께비"], a["회전"], a["반전"]), flush=True)
    q = os.path.join("out", "기록", "음영민감도_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"판": TAG, "원화두께비": round(art_ratio(masks), 4), "행": rows}, open(q, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", q)


def verdict():
    q = [x for x in sorted(glob.glob(os.path.join("out", "기록", "음영민감도_*.json"))) if "판정" not in x][-1]
    D = json.load(open(q, encoding="utf-8"))
    P = {(r["판본"], r["씨앗"]): r["P"] for r in D["행"]}
    d = [P["k0", s] - P["k1", s] for s in SEEDS]
    e = [P["C", s] - P["k1", s] for s in SEEDS]
    spread = float(np.median([abs(P["k0", a] - P["k0", b]) for i, a in enumerate(SEEDS) for b in SEEDS[i + 1:]]))
    out = {
        "Q1 음영이 옆을 맞추나": {"d_s": d, "중앙": float(np.median(d)), "양수": sum(x > 0 for x in d), "통과": bool(np.median(d) > 0 and sum(x > 0 for x in d) >= 2)},
        "Q2 깊이 정보 덕인가": {"e_s": e, "중앙": float(np.median(e)), "양수": sum(x > 0 for x in e), "통과": bool(np.median(e) > 0 and sum(x > 0 for x in e) >= 2)},
        "Q3 씨앗 흔들림보다 큰가": {"효과": abs(float(np.median(d))), "흔들림": spread, "통과": bool(abs(np.median(d)) > spread)},
    }
    from scipy.stats import spearmanr
    ks = ["k0", "k33", "k67", "k1"]
    out["관찰 단조성(씨앗별 순위상관 k↑ P↓ 이면 −)"] = [round(float(spearmanr(range(4), [P[k, s] for k in ks])[0]), 3) for s in SEEDS]
    F = {(r["판본"], r["씨앗"]): r["정면"] for r in D["행"]}
    out["관찰 정면 k1−k0"] = [round(F["k1", s] - F["k0", s], 4) for s in SEEDS]
    out["판정 json"] = q
    print(json.dumps(out, ensure_ascii=False, indent=1))
    json.dump(out, open(q.replace(".json", "_판정.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def figure():
    import trimesh
    from PIL import ImageDraw
    import 생성3D as G3
    import 폴리싱 as PL
    import 앨리어싱 as AL
    from 조각생성 import trim
    from 계획 import _font
    masks, bs, axes = setup()
    q = sorted(glob.glob(os.path.join("out", "기록", "음영민감도_2*.json")))
    D = json.load(open([x for x in q if "판정" not in x][-1], encoding="utf-8"))
    P = {(r["판본"], r["씨앗"]): r["P"] for r in D["행"]}
    T, G, LW, TOP, CAP = 230, 8, 70, 80, 26
    sd = SEEDS[0]
    im = Image.new("RGB", (LW + len(VARS) * (T * 2 + G * 2), TOP + CAP + 2 * (T + G)), "white")
    d = ImageDraw.Draw(im)
    d.text((16, 12), "은둔자 삼면도 정면 — 음영만 바꿔 TripoSG 에 넣으면 (씨앗 %d)" % sd, fill="black", font=_font(24))
    d.text((16, 46), "윗줄 입력 · 아랫줄 생성 메시 정면 / 옆 (명암) · P = 옆 판 못덮음+넘침 (낮을수록 옆이 맞음) · C = 같은 세기 무작위 얼룩", fill=(90, 90, 90), font=_font(14))
    for i, (v, _) in enumerate(VARS):
        x = LW + i * (T * 2 + G * 2)
        d.text((x, TOP), "%s · P %.3f" % (v, P[v, sd]), fill="black", font=_font(16))
        inp = Image.open(os.path.join(S, v + ".png")).convert("RGBA")
        bg = Image.new("RGBA", inp.size, "white"); bg.alpha_composite(inp)
        bg = bg.convert("RGB"); bg.thumbnail((T * 2, T))
        im.paste(bg, (x + (T * 2 - bg.width) // 2, TOP + CAP))
        g = trim(trimesh.load(os.path.join(S, "tri", "%s_s%d.glb" % (v, sd)), force="mesh"))
        _, V, _, _ = G3.orient(g.vertices, masks)
        m = trimesh.Trimesh(V, np.asarray(g.faces), process=False)
        for j, az in enumerate((0, 90)):
            im.paste(Image.fromarray(PL.shaded(m, az, AL.frame_of(m, az), T)), (x + j * (T + G), TOP + CAP + T + G))
        print("  그림", v, flush=True)
    p = os.path.join("out", "은둔자_음영민감도.png")
    im.save(p)
    print(" ->", p)


if __name__ == "__main__":
    a = sys.argv[1:] or ["입력"]
    {"입력": make_inputs, "배관": pipe_check, "생성": generate, "재기": run_measure, "판정": verdict, "그림": figure}[a[0]]()
