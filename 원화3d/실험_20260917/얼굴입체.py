# -*- coding: utf-8 -*-
"""**민감도 카드 2 — 명암이 눈썹 · 눈을 기하로 세우나** (2026-09-17). 계획 `claudedocs/plan_얼굴입체민감도_20260917.md` (판정 먼저).

    python 얼굴입체.py 검사    높이맵 · D 자가검사 (반구 · 돌기)
    python 얼굴입체.py 입력    한푼 · 은둔자 얼굴 × O S V X -> 스크래치 face3d/
    python 얼굴입체.py 생성    TripoSG 8 장 × 씨앗 42 · 7 · 123
    python 얼굴입체.py 재기    -> out/기록/얼굴입체_<때>.json
    python 얼굴입체.py 판정
    python 얼굴입체.py 그림    -> out/얼굴입체.png

카드 1 은 옆 실루엣만 쟀고 머리를 명암에서 뺐다 — 사용자 가설(「명암으로 눈썹이랑 안구가 잘 표현됐다」)을 안 쟀다.
"""
import glob
import json
import os
import subprocess
import sys
import time

import cv2
import numpy as np
import trimesh
from PIL import Image
from scipy import ndimage as nd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 음영민감도 as M                                   # 경로 · 씨앗 · labL · AMP
import win as W

SC = os.path.dirname(M.S)
S = os.path.join(SC, "face3d")
SUBJ = {  # 그림 · 확대 · 얼굴 상자 (x0, x1, y0, y1 · 작업 해상도) · SDXL 판
    "hanbun": dict(src=os.path.join(SC, "hanbun", "hanbun_rgba.png"), up=1, box=(160, 325, 45, 232), sdxl=os.path.join(SC, "hanbun", "shaded.png")),
    "hermit": dict(src=os.path.join(SC, "dg_head", "face.png"), up=4, box=(140, 540, 220, 720), sdxl=None),
}
VARS = ("O", "S", "V", "X")
L_DIR = np.array([-0.45, 0.55, 0.70])
TAG = "얼굴입체 v2(앞 +z 고정 · 표본 6M) · 특징선 램버트 · σh 1.5% · 굴곡 σ 4% · 밀기 5% · 세기 σL 15 · 씨앗 42/7/123 (2026-09-17)"


def load(sub):
    c = SUBJ[sub]
    im = Image.open(c["src"])
    im = im.resize((im.width * c["up"], im.height * c["up"]), Image.LANCZOS)
    a = np.asarray(im.convert("RGBA")).astype(np.float64)
    if im.mode == "RGBA":
        al = a[..., 3] / 255.0
        rgb = a[..., :3] * al[..., None] + 255 * (1 - al[..., None])
        mask = a[..., 3] > 127
    else:
        rgb = a[..., :3]
        m = nd.binary_fill_holes(nd.binary_closing(rgb.min(2) < 245, iterations=2))
        lab, n = nd.label(m)
        mask = lab == 1 + np.argmax(nd.sum(m, lab, range(1, n + 1)))
    return rgb, mask


def box_masks(shape, box):
    x0, x1, y0, y1 = box
    b = np.zeros(shape)
    b[y0:y1, x0:x1] = 1
    return b > 0, nd.gaussian_filter(b, 4)


def features(rgb, box):
    """특징선 세기 0..1 — 주변보다 어두운 곳 (눈썹 · 눈 · 입 · 흉터)."""
    L = M.labL(rgb)[0]
    bw = box[1] - box[0]
    F = np.clip((nd.gaussian_filter(L, 0.03 * bw) - L) / 30.0, 0, 1)
    inb, _ = box_masks(L.shape, box)
    return F * inb


def lambert_px(h, light=L_DIR):
    gy, gx = np.gradient(h)
    n = np.stack([-gx, gy, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return np.clip(n @ (light / np.linalg.norm(light)), 0, 1)


def add_L(rgb, f):
    Lo, lab = M.labL(rgb)
    lab2 = lab.copy()
    lab2[..., 0] = np.clip(Lo + f, 0, 100) * 255 / 100
    return cv2.cvtColor(np.rint(lab2).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float64)


def make_inputs():
    os.makedirs(S, exist_ok=True)
    sheet = []
    for sub, c in SUBJ.items():
        rgb, mask = load(sub)
        box = c["box"]
        inb, feather = box_masks(mask.shape, box)
        bw = box[1] - box[0]
        F = features(rgb, box)
        h = -nd.gaussian_filter(F, 0.015 * bw)
        g = np.hypot(*np.gradient(h)).max()
        s = lambert_px(h / max(g, 1e-9))                  # 가장 가파른 곳 기울기 1
        sel = inb & mask
        f = (s - s[sel].mean()) / s[sel].std() * M.AMP * feather * mask
        d = int(round(0.05 * bw))
        fx = np.roll(f / np.maximum(feather, 1e-6) * inb, (d, d), (0, 1)) * feather * mask
        sd = c["sdxl"]
        if sd is None:
            white = os.path.join(S, sub + "_white.png")
            Image.fromarray(rgb.astype(np.uint8)).save(white)
            sd = os.path.join(S, sub + "_sdxl.png")
            if not os.path.exists(sd):
                P = ("close up portrait bust of a pale man with slicked back grey hair, scarred face, "
                     "3d render, painted resin figure, soft studio lighting from upper left, strong ambient occlusion, clear facial relief, plain white background")
                subprocess.run([M.PY, os.path.join(os.path.dirname(os.path.abspath(__file__)), "음영민감도_sdxl.py"), white, sd, P, "0.50"], check=True)
        sx = np.asarray(Image.open(sd).convert("RGB").resize(mask.shape[::-1], Image.LANCZOS)).astype(np.float64)
        outs = {"O": rgb, "S": rgb * (1 - feather[..., None]) + sx * feather[..., None], "V": add_L(rgb, f), "X": add_L(rgb, fx)}
        for v in VARS:
            o = outs[v]
            if v == "O":
                assert np.array_equal(o, rgb)
            img = np.dstack([np.rint(o).astype(np.uint8), (mask * 255).astype(np.uint8)])
            Image.fromarray(img).save(os.path.join(S, "%s_%s.png" % (sub, v)))
        np.save(os.path.join(S, sub + "_F.npy"), F)
        x0, x1, y0, y1 = box
        sheet.append(np.hstack([cv2.resize(np.rint(outs[v][y0:y1, x0:x1]).astype(np.uint8), (240, 270)) for v in VARS]
                               + [cv2.resize((np.repeat(F[y0:y1, x0:x1, None], 3, 2) * 255).astype(np.uint8), (240, 270))]))
        print("  %s 상자폭 %d · 선 화소 %d · 밀기 %d" % (sub, bw, int((F > 0.3).sum()), d))
    Image.fromarray(np.vstack(sheet)).save(os.path.join(S, "inputs_sheet.png"))


def generate():
    ims = [os.path.join(S, "%s_%s.png" % (sub, v)) for sub in SUBJ for v in VARS]
    subprocess.run([M.PY, M.TRI, *ims, "--outdir", os.path.join(S, "tri"), "--no-rmbg", "--seeds", ",".join(map(str, M.SEEDS))],
                   cwd=os.path.dirname(M.TRI), check=True)


def heightmap(mesh, mask, n=6_000_000):
    """메시 → 입력 시점 높이맵 (그림 화소 격자). 4 방향 × 반전 중 실루엣 IoU 최대 · bbox 선형 대응."""
    pts, _ = trimesh.sample.sample_surface(mesh, n)
    base = W.to_world(pts, "xyz")                          # (x 가로, y 깊이 · 앞 −, z 위)
    ys, xs = np.nonzero(mask)
    H_, W_ = mask.shape

    def splat(P):
        X, Z = P[:, 0], P[:, 2]
        px = xs.min() + (X - X.min()) / max(np.ptp(X), 1e-9) * (xs.max() - xs.min())
        py = ys.min() + (Z.max() - Z) / max(np.ptp(Z), 1e-9) * (ys.max() - ys.min())
        return np.clip(np.rint(py).astype(int), 0, H_ - 1), np.clip(np.rint(px).astype(int), 0, W_ - 1), np.ptp(X) / max(xs.max() - xs.min(), 1)

    best = None
    # **앞은 원좌표 +z 로 고정한다.** 앞뒤는 실루엣이 같아 IoU 로 못 가른다 — v1 은 −z 를 앞으로 잡아 한푼 뒤통수를 쟀다 (그림에서 발견).
    # TripoSG 앞 = +z 는 09-17 한푼 · 은둔자 명암 렌더(az 180)에서 확인. 가로 반전만 IoU 로 고른다.
    for k in (0,):
        R = np.diag([1.0, 1.0, 1.0])
        for mir in (1, -1):
            P = base @ R.T * np.array([mir, -1, 1])       # 깊이 부호를 뒤집어 앞(+z)이 −y 가 되게
            py, px, _ = splat(P[::20])
            sil = np.zeros(mask.shape, bool)
            sil[py, px] = True
            sil = nd.binary_closing(sil, iterations=3)
            iou = (sil & mask).sum() / max((sil | mask).sum(), 1)
            if best is None or iou > best[0]:
                best = (iou, P, k * 90, mir)
    iou, P, yaw, mir = best
    py, px, wpp = splat(P)
    Hm = np.full(mask.shape, -np.inf)
    np.maximum.at(Hm, (py, px), -P[:, 1])
    valid = np.isfinite(Hm)
    Hm = np.where(valid, Hm, -1e9)
    # 앞면 점이 안 떨어진 화소엔 뒷면 점만 찍힌다 (타원체 자가검사에서 −1 로 튐) — 주변 5×5 최댓값보다 8 화소 폭 넘게 낮으면 버린다
    valid &= Hm >= nd.grey_dilation(Hm, size=5) - 8 * wpp
    return np.where(valid, Hm, 0.0), valid, wpp, dict(iou=round(float(iou), 4), 회전=yaw, 반전=mir)


def relief_D(Hm, valid, F, box, wpp):
    bw = box[1] - box[0]
    inb, _ = box_masks(F.shape, box)
    A = valid.astype(float)
    low = nd.gaussian_filter(Hm * A, 0.04 * bw) / np.maximum(nd.gaussian_filter(A, 0.04 * bw), 1e-6)
    R = np.abs(Hm - low) / (bw * wpp)
    line = nd.binary_dilation(F > 0.3, iterations=2) & inb & valid
    off = ~nd.binary_dilation(F > 0.3, iterations=6) & inb & valid
    return float(R[line].mean() - R[off].mean()), R, line


def selfcheck():
    m = trimesh.creation.icosphere(subdivisions=5, radius=1.0)
    V = m.vertices * np.array([1.4, 1.0, 1.0])               # 가로로 긴 타원체 — 구는 대칭이라 방향이 90° 로 잡혔다
    bump = np.exp(-((V[:, 0] + 0.42) ** 2 + (V[:, 1] - 0.3) ** 2) / 0.01) * (V[:, 2] > 0)   # 앞(원좌표 +z)
    V[:, 2] += 0.08 * bump
    back = trimesh.Trimesh(V * np.array([1, 1, -1]), m.faces)   # 돌기를 뒤로 — 앞을 재면 안 잡혀야 한다
    m = trimesh.Trimesh(V, m.faces)
    yy, xx = np.mgrid[0:200, 0:260]
    mask = ((xx - 130) / 133.0) ** 2 + ((yy - 100) / 95.0) ** 2 < 1
    Hm, valid, wpp, info = heightmap(m, mask, 400_000)
    assert info["회전"] == 0
    assert info["회전"] in (0, 180), "타원체 방향을 못 잡는다 %s" % info
    assert Hm[100, 130] > Hm[100, 12], "높이맵: 가운데가 가장자리보다 낮다"
    F = np.zeros(mask.shape)
    cy, cx = int(100 - 0.3 * 95), int(130 - 0.3 * 133) if info["반전"] * (1 if info["회전"] == 0 else -1) > 0 else int(130 + 0.3 * 133)
    F[cy - 4:cy + 5, cx - 4:cx + 5] = 1
    D, _, _ = relief_D(Hm, valid, F, (30, 230, 20, 180), wpp)
    F2 = np.roll(F, (60, 80), (0, 1))
    D2, _, _ = relief_D(Hm, valid, F2, (30, 230, 20, 180), wpp)
    print("  자가검사 — 돌기 자리 D %.4f · 빈 자리 D %.4f · %s" % (D, D2, info))
    assert D > 2 * max(D2, 0) and D > 0, "D 가 돌기 자리를 못 잡는다"
    Hb, vb, wb, ib = heightmap(back, mask, 400_000)
    Db, _, _ = relief_D(Hb, vb, F, (30, 230, 20, 180), wb)
    print("  돌기를 뒤에 둔 타원체 — 같은 자리 D %.4f (앞 돌기 %.4f 보다 작아야)" % (Db, D))
    assert Db < D / 2, "뒤 돌기를 앞으로 잰다 — 앞뒤가 뒤집혔다"
    print("  자가검사 통과")


def run_measure():
    rows = []
    for sub, c in SUBJ.items():
        rgb, mask = load(sub)
        F = np.load(os.path.join(S, sub + "_F.npy"))
        for v in VARS:
            for sd in M.SEEDS:
                g = trimesh.load(os.path.join(S, "tri", "%s_%s_s%d.glb" % (sub, v, sd)), force="mesh")
                Hm, valid, wpp, info = heightmap(g, mask)
                D, _, _ = relief_D(Hm, valid, F, c["box"], wpp)
                rows.append({"대상": sub, "판본": v, "씨앗": sd, "D": round(D, 5), **info})
                print("  %-6s %s s%-4d D %+.5f · IoU %.3f · 회전 %d 반전 %+d" % (sub, v, sd, D, info["iou"], info["회전"], info["반전"]), flush=True)
    q = os.path.join("out", "기록", "얼굴입체_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"판": TAG, "행": rows}, open(q, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", q)


def verdict():
    q = [x for x in sorted(glob.glob(os.path.join("out", "기록", "얼굴입체_*.json"))) if "판정" not in x][-1]
    rows = json.load(open(q, encoding="utf-8"))["행"]
    out = {}
    for sub in SUBJ:
        D = {(r["판본"], r["씨앗"]): r["D"] for r in rows if r["대상"] == sub}
        Ss = M.SEEDS

        def rule(a, b):
            d = [D[a, s] - D[b, s] for s in Ss]
            return {"차": d, "중앙": float(np.median(d)), "양수": sum(x > 0 for x in d), "통과": bool(np.median(d) > 0 and sum(x > 0 for x in d) >= 2)}

        spread = float(np.median([abs(D["O", a] - D["O", b]) for i, a in enumerate(Ss) for b in Ss[i + 1:]]))
        q2 = rule("V", "O")
        out[sub] = {"Q1 SDXL (S−O)": rule("S", "O"), "Q2 CV (V−O)": q2, "Q3 자리 (V−X)": rule("V", "X"),
                    "Q4 흔들림": {"효과": abs(q2["중앙"]), "흔들림": spread, "통과": bool(abs(q2["중앙"]) > spread)},
                    "관찰 SDXL 흔들림 대비": {"효과": abs(rule("S", "O")["중앙"]), "흔들림": spread}}
    out["판정 json"] = q
    print(json.dumps(out, ensure_ascii=False, indent=1))
    json.dump(out, open(q.replace(".json", "_판정.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def figure():
    from PIL import ImageDraw
    import 폴리싱 as PL
    from 계획 import _font
    q = [x for x in sorted(glob.glob(os.path.join("out", "기록", "얼굴입체_*.json"))) if "판정" not in x][-1]
    rows = json.load(open(q, encoding="utf-8"))["행"]
    T, G, LW, TOP = 220, 8, 110, 80
    sd = 42
    im = Image.new("RGB", (LW + 4 * (3 * T + 3 * G), TOP + 2 * (T + 40)), "white")
    d = ImageDraw.Draw(im)
    d.text((16, 12), "얼굴 국소 입체 — 명암이 눈썹 · 눈을 기하로 세우나 (씨앗 42)", fill="black", font=_font(24))
    d.text((16, 46), "칸마다: 입력 얼굴 · 생성 메시 얼굴(명암) · 굴곡 |R| (빨강 윤곽 = 원본 특징선) · D = 선 위 굴곡 − 선 밖 굴곡 (씨앗 42/7/123)", fill=(80, 80, 80), font=_font(14))
    names = {"O": "원본", "S": "SDXL 음영", "V": "CV 선 명암", "X": "대조: 밀린 CV"}
    for r, (sub, c) in enumerate(SUBJ.items()):
        rgb, mask = load(sub)
        F = np.load(os.path.join(S, sub + "_F.npy"))
        x0, x1, y0, y1 = c["box"]
        y = TOP + r * (T + 40)
        d.text((12, y + T // 2), sub, fill="black", font=_font(18))
        for i, v in enumerate(VARS):
            x = LW + i * (3 * T + 3 * G)
            Ds = [rr["D"] for rr in rows if rr["대상"] == sub and rr["판본"] == v]
            d.text((x, y), "%s · D %s" % (names[v], " / ".join("%+.4f" % t for t in Ds)), fill="black", font=_font(13))
            inp = np.asarray(Image.open(os.path.join(S, "%s_%s.png" % (sub, v))).convert("RGB"))[y0:y1, x0:x1]
            im.paste(Image.fromarray(cv2.resize(inp, (T, T))), (x, y + 20))
            g = trimesh.load(os.path.join(S, "tri", "%s_%s_s%d.glb" % (sub, v, sd)), force="mesh")
            Hm, valid, wpp, info = heightmap(g, mask)
            D, R, line = relief_D(Hm, valid, F, c["box"], wpp)
            # 명암 대신 높이맵으로 음영 (같은 시점 · 화소 정렬) — 메시 렌더와 달리 입력 칸과 화소가 맞는다
            A = valid.astype(float)
            hs = nd.gaussian_filter(Hm * A, 1.0) / np.maximum(nd.gaussian_filter(A, 1.0), 1e-6)
            sh = lambert_px(hs / (wpp + 1e-12))
            sh = np.where(valid & mask, sh, 1.0)[y0:y1, x0:x1]
            im.paste(Image.fromarray(cv2.resize((sh * 255).astype(np.uint8), (T, T))).convert("RGB"), (x + T + G, y + 20))
            rr = R[y0:y1, x0:x1]
            vis = np.clip(rr / (np.percentile(rr[valid[y0:y1, x0:x1]], 99) + 1e-12), 0, 1)
            col = np.repeat((255 - vis * 255).astype(np.uint8)[..., None], 3, 2)
            edge = line[y0:y1, x0:x1] & ~nd.binary_erosion(line[y0:y1, x0:x1])
            col[edge] = (220, 40, 40)
            im.paste(Image.fromarray(cv2.resize(col, (T, T), interpolation=cv2.INTER_NEAREST)), (x + 2 * (T + G), y + 20))
            print("  그림", sub, v, flush=True)
    p = os.path.join("out", "얼굴입체.png")
    im.save(p)
    print(" ->", p)


if __name__ == "__main__":
    a = sys.argv[1:] or ["검사"]
    {"검사": selfcheck, "입력": make_inputs, "생성": generate, "재기": run_measure, "판정": verdict, "그림": figure}[a[0]]()
