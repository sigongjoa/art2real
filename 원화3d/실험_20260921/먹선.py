# -*- coding: utf-8 -*-
"""**몸을 먼저 매끈하게, 그 위에 먹선을 새긴다** (2026-09-21).

    python 먹선.py [케이스=오메가몬] [σ=3] [깊이=0.005]   -> out/결과물/<케이스>/먹선.ply · out/먹선_<케이스>.png

사용자(09-21): 「스무딩하니깐 디테일 먹선 이런 게 사라지네」 — 순서가 틀렸었다.
매끈한 판본은 선을 새기기 **전**의 몸에서 만들었고, 선 판본은 울퉁불퉁한 몸 위에 새겼다.

    1  몸      타원 장을 높이 방향으로만 편다 (`매끈장` · σ)  -> 마칭큐브 -> 한 번 잘게 나눈다
    2  먹선    **원화에 실제로 그려진 검은 선**을 뽑는다 — 어두운 화소 중 **가는 것만**
               (추출기의 판 경계 132 개는 톤 경계가 섞여 구겨진 은박지가 됐다 · 09-21)
    3  새김    앞 · 뒤를 보는 면의 정점을 시선 방향 안쪽으로 민다. 선 지도를 1 화소 흐려 **부드러운 골**로

앞 · 뒤에서 본 실루엣은 안 바뀐다 (깊이로만 민다). 깊이 값은 **지어낸 값**(guessed)이다.
"""
import os
import subprocess
import sys

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import 결과물 as RS
import 세우기 as SE
import 장타원 as JT
import 연속hull as CH
H, W, HERE = RS.H, RS.W, RS.HERE
어둠 = 120                     # 이보다 어두우면 먹
선최대굵기 = 5                # 화소(1024). 이보다 굵은 어두운 덩어리는 선이 아니라 **검은 칠**이다
칠최소 = 60                    # 이보다 작은 「칠」은 테두리를 안 쓴다 (점 부스러기)
닫기 = 2                       # 끊긴 틈을 잇는 횟수. 3 이면 선이 굵어진다 (화소 4.5 만 -> 5.6 만)
조각최소 = 20                  # 이보다 작은 조각은 버린다
테두리 = 2                     # 실루엣 안쪽 이만큼은 안 새긴다 — **맨 바깥 윤곽은 3D 에서 곧 모양의 가장자리**라
                               # 홈을 파면 윤곽이 패인다. 첫 판은 5 였고 가는 선의 **58%**(16,109/27,598 화소)를
                               # 같이 먹었다 — 팔 · 다리가 가늘어 부위 경계선까지 그 띠에 들어갔다.


def 먹선지도(png, 진단=None):
    """원화 -> 먹선 bool. **선이 끊기지 않게** 세 가지를 한다 (2026-09-21 · 사용자 「선들이 연결이 안 되는 거를 이어서」).

    ① **칠의 테두리를 선으로 되살린다.** 굵은 검은 칠(관절 · 포)을 통째로 빼면 거기 닿는 선이
       **잘린다** — 첫 판이 434 조각으로 부서진 까닭이다. 칠의 **가장자리가 곧 그려진 선**이다.
    ② **닫기 2 회**로 남은 틈을 잇는다 (안티앨리어싱 · 스캔 탓의 한두 화소 구멍).
    ③ **20 화소 미만 조각은 버린다** — 칠 테두리가 남기는 점 부스러기.

    조각 434 -> **72** · 100 화소 이상 조각이 담은 몫 0.68 -> **0.96**.
    """
    import cv2
    im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_UNCHANGED)
    a = im[:, :, 3] > 127 if im.shape[2] == 4 else np.ones(im.shape[:2], bool)
    g = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2GRAY)
    C = np.ones((3, 3), bool)
    dark = (g < 어둠) & a
    k = 선최대굵기 // 2 + 1
    칠 = ndimage.binary_dilation(ndimage.binary_opening(dark, iterations=k), iterations=k) & dark
    가는선 = dark & ~칠
    lab, _ = ndimage.label(칠, C)                                  # 큰 칠만 테두리를 쓴다 (점 부스러기 제외)
    sz = np.bincount(lab.ravel())
    큰칠 = np.isin(lab, np.where(sz >= 칠최소)[0][1:]) if sz.size > 1 else np.zeros_like(칠)
    테 = 큰칠 & ~ndimage.binary_erosion(큰칠, iterations=2)
    sel = ndimage.binary_closing(가는선 | 테, C, iterations=닫기)
    sel &= ndimage.binary_erosion(a, iterations=테두리)             # 맨 바깥 윤곽만 뺀다
    lab2, _ = ndimage.label(sel, C)
    s2 = np.bincount(lab2.ravel())
    sel = np.isin(lab2, np.where(s2 >= 조각최소)[0][1:]) if s2.size > 1 else sel
    if 진단 is not None:
        진단.update({"가는선": 가는선, "칠": 칠, "테": 테, "sel": sel})
    return sel


def main(case="오메가몬", sigma=3.0, depth=0.005, N=384):
    from PIL import Image
    d = os.path.join(HERE, "out", "결과물", case)
    os.makedirs(d, exist_ok=True)
    _, masks, p, bs, raw = SE.껍질(case)
    g, ax = JT.타원장(masks, bs, N=N)
    f, _ = CH.연속장(masks, bs, N=N)
    f = f / ((W.U1 - W.U0) / N)
    gg = np.minimum(np.maximum(ndimage.gaussian_filter1d(g, sigma, axis=2), g - 1.0), f)
    몸 = RS.큰덩어리(JT.메시(gg, ax))
    몸.export(os.path.join(d, "먹선_몸.ply"))
    m = 몸.subdivide()
    V = np.asarray(m.vertices, float).copy()
    Nn = np.asarray(m.vertex_normals)
    base = H.art_dir(case)
    새긴 = {}
    지도들 = {}
    for v, sign, 방향 in (("front", +1, -1), ("back", bs, +1)):
        선 = 먹선지도(os.path.join(base, H.CASES[case]["src"][v]))
        지도들[v] = 선
        창선 = SE.창에(선, v, raw, p).astype(np.float32)
        부드 = ndimage.gaussian_filter(창선, 1.0)
        부드 = np.clip(부드 / max(부드.max(), 1e-6) * 1.6, 0, 1)             # 선 가운데가 1
        본다 = Nn[:, 1] * 방향 > SE.법선문턱
        py, px = W.topix(sign * V[:, 0], V[:, 2])
        w = np.where(본다, 부드[py, px], 0.0)
        V[:, 1] -= 방향 * depth * w
        새긴[v] = int((w > 0.3).sum())
    out = trimesh.Trimesh(V, np.asarray(m.faces), process=False)
    out.export(os.path.join(d, "먹선.ply"))
    print("  몸 면 %d -> 새긴 메시 면 %d · 새긴 정점 앞 %d / 뒤 %d · 닫힘 %s"
          % (len(몸.faces), len(out.faces), 새긴["front"], 새긴["back"], out.is_watertight), flush=True)
    print("  못덮음 앞·옆·뒤  몸 %s\n                 먹선 %s" % (SE.못덮음(몸, masks, bs), SE.못덮음(out, masks, bs)), flush=True)
    open(RS.렌더py, "w", encoding="utf-8").write(RS.렌더소스)
    for tag, fn in (("먹선몸", "먹선_몸.ply"), ("먹선", "먹선.ply")):
        subprocess.run([RS.BLENDER, "-b", "--python", RS.렌더py, "--", os.path.join(d, fn), d, tag],
                       capture_output=True, timeout=1500)
    src = Image.open(os.path.join(HERE, "out", "누끼", "%s_front" % case, "흰바탕.png")).convert("RGB").resize((700, 700))
    선그림 = Image.fromarray(np.where(지도들["front"], 0, 255).astype(np.uint8)).convert("RGB").resize((700, 700))
    rows = [[src, 선그림] + [Image.open(os.path.join(d, "렌더_먹선몸_%s.png" % n)).convert("RGB").resize((700, 700)) for n in ("앞", "사선")],
            [src, 선그림] + [Image.open(os.path.join(d, "렌더_먹선_%s.png" % n)).convert("RGB").resize((700, 700)) for n in ("앞", "사선")]]
    뒤 = [Image.open(os.path.join(d, "렌더_%s_뒤.png" % t)).convert("RGB").resize((700, 700)) for t in ("먹선몸", "먹선")]
    for r, b in zip(rows, 뒤):
        r.append(b)
    sheet = Image.new("RGB", (5 * 710 - 10, 2 * 710 - 10), "white")
    for i, ims in enumerate(rows):
        for j, im in enumerate(ims):
            sheet.paste(im, (j * 710, i * 710))
    o = os.path.join(HERE, "out", "먹선_%s.png" % case)
    sheet.save(o)
    sheet.resize((sheet.size[0] // 2, sheet.size[1] // 2)).save(o.replace(".png", "_작게.png"))
    print("  ->", o)


if __name__ == "__main__":
    a = sys.argv
    main(a[1] if len(a) > 1 else "오메가몬", float(a[2]) if len(a) > 2 else 3.0, float(a[3]) if len(a) > 3 else 0.005)
