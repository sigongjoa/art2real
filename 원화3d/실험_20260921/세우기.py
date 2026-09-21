# -*- coding: utf-8 -*-
"""**껍질을 회전체에서 hull 로 바꾼다 — 그리고 그 위에 도안의 선을 새긴다** (2026-09-21).

    python 세우기.py 검사
    python 세우기.py 짓기     -> out/세우기_오메가몬.glb · out/기록/세우기_<때>.json
    python 세우기.py 그림     -> out/세우기_오메가몬.png

사용자(09-21): 「고쳐야지? 우리 부품을 세우는 방식이 잘못된 거 아니냐?」 — 맞다.
`build_blender.py` 는 **외형 반폭을 돌린 회전체 껍질 하나**에 판을 눌러 넣는다. 투구용 위상이라
전신은 꽃병이 된다(09-21 `원화도안_오메가몬_조립.png`). 그런데 우리는 **세 판 실루엣으로
팔 · 다리 · 검까지 세우는 hull** 을 09-09 부터 갖고 있고, 오메가몬이 `hull.py` 의 기본 케이스다.

    껍질      회전체  ->  **visual hull** (`out/hull.glb` · 닫힌 메시 · 면 19 만)
    디테일    판을 눌러 넣기  ->  **도안의 판 경계(선)를 앞 · 뒤에서 hull 표면에 새긴다**

앞 판은 `hull.align` 의 기준이라 **안 움직인다** — 원화 화소 (행, 열) 이 곧 창 화소다
(`win.topix` · RES 1024 · x ∈ [−0.6, 0.6] · z ∈ [−0.1, 1.1]). 그래서 추출기의 경계 지도를
그대로 hull 앞면에 비출 수 있다. 뒤 판은 `hull.align` 이 찾은 값으로 같이 옮긴다.

**홈 깊이는 지어낸 값이다** — 0.006(복셀 1.3 칸). 도안도 `protrusion: guessed` 라고 적는다.

**정답 메시가 없는 장이다. 그래서 판정이 아니라 시연이고, 거는 문은 하나다.**

    문  디테일을 새겨도 **실루엣 약속이 안 깨진다** — 세 판 못덮음이 새기기 전보다
        **0.5%p 넘게 늘지 않는다** (hull 은 상한이라는 것이 이 사업의 상품성이다)
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260920")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260919")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260916")
import 선읽기 as LR
import 폴리싱 as PL
H, W = LR.H, LR.W
HERE, OUT = LR.HERE, LR.OUT
도안디 = os.path.join(HERE, "out", "원화도안", "오메가몬")
홈깊이 = 0.006                 # **guessed**. 복셀 한 칸이 1.2/256 = 0.0047
선굵기 = 2                     # 창 화소(1024). 경계 지도를 이만큼 부풀린다
안쪽여유 = 6                   # 실루엣 테두리는 홈이 아니다 — 물건 마스크를 이만큼 깎은 안쪽만
법선문턱 = 0.35                # |n_y| 가 이보다 커야 그 판을 「보는」 면이다
문_여유 = 0.005


def 경계지도(view폴더, 마스크):
    """추출기 라벨(512) -> 창(1024) 의 **안쪽 판 경계** bool."""
    import cv2
    from scipy import ndimage
    lab = np.load(os.path.join(도안디, view폴더, "labels_grown.npy"))
    b = LR.경계(lab).astype(np.uint8)
    b = cv2.resize(b, (W.RES, W.RES), interpolation=cv2.INTER_NEAREST) > 0
    b = ndimage.binary_dilation(b, iterations=선굵기)
    안 = ndimage.binary_erosion(마스크, iterations=안쪽여유)
    return b & 안


def 못덮음(m, masks, bs):
    V, F = np.asarray(m.vertices, float), np.asarray(m.faces)
    out = {}
    for v in W.VIEWS:
        s = np.asarray(W.silhouette(V, F, v, bs if v == "back" else None)).astype(bool)
        out[v] = round(float((masks[v] & ~s).sum() / max(int(masks[v].sum()), 1)), 5)
    return out


def 껍질(case="오메가몬", sigma=0.0):
    """`hull.main` 의 배관을 **그대로** 부른다 — 지시선 제거 · 창에 앉히기 · 정렬 · 기본 깎기(타원).
    첫 판은 `out/hull.glb`(09-15 내보낸 것 · 창 좌표가 아니다)를 그냥 읽어 못덮음이 25~33% 였다.
    그리고 `W.art_mask` 만 부르고 `declutter` · `to_win` 을 건너뛰어 지시선이 깊이 ±0.6 을 다 채웠다."""
    bs = H.CASES[case]["back_sign"]
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks, deps, 앉힘 = {}, {}, {}
    for v, m in raw.items():
        d = H.declutter(m)
        masks[v], deps[v] = H.to_win(d, np.ones(d.shape, np.float32))
        앉힘[v] = d
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    deps = {v: H._warp_one(a, v, p) for v, a in deps.items()}
    vox, axes = H.carve_default(masks, deps, back_sign=bs)
    if sigma > 0:      # **보기용.** `hull.SMOOTH_OUT` 은 09-11 에 꺼 둔 기본값이고 여기서 안 바꾼다
        plain, _ = H.carve(masks, back_sign=bs)
        Vv, F = H.mesh_from_field(H.smooth_field(H.sdf_of(vox), H.sdf_of(plain), sigma), axes)
    else:
        Vv, F = H.mesh_from(vox, axes)
    m = trimesh.Trimesh(Vv, F, process=True)
    parts = m.split(only_watertight=False)
    m = max(parts, key=lambda x: len(x.faces)) if len(parts) > 1 else m
    if m.volume < 0:
        m.invert()
    return m, masks, p, bs, raw


def 창에(지도, v, raw, p):
    """원화 화소의 bool 지도를 **마스크와 똑같은 변환**으로 창에 옮긴다 (`to_win` 의 extra 자리)."""
    d = H.declutter(raw[v])
    _, w = H.to_win(d, 지도.astype(np.float32))
    return H._warp_one(w, v, p) > 0.5


def 짓기(sigma=0.0, 꼬리=""):
    t0 = time.time()
    hull, masks, p, bs, raw = 껍질(sigma=sigma)
    전 = 못덮음(hull, masks, bs)
    m = hull.subdivide()                                   # 선(2~4 화소 = 0.002~0.005)보다 촘촘하게
    V = np.asarray(m.vertices, float).copy()
    N = np.asarray(m.vertex_normals)
    선앞 = 창에(경계지도("앞", raw["front"]), "front", raw, p)
    선뒤 = 창에(경계지도("뒤", raw["back"]), "back", raw, p)
    r = {"판": "세우기 v1 · hull + 도안 선 새기기 (2026-09-21)", "때": time.strftime("%Y%m%d_%H%M"),
         "hull면": int(len(hull.faces)), "새긴메시면": int(len(m.faces)), "홈깊이(guessed)": 홈깊이,
         "align": [round(float(x), 4) for x in p]}
    for 이름, 선, sign, 방향 in (("앞", 선앞, +1, -1), ("뒤", 선뒤, bs, +1)):
        # 방향 = 그 판을 보는 면의 법선 y 부호. 앞은 −y 를 본다(카메라가 −y 쪽)
        본다 = N[:, 1] * 방향 > 법선문턱
        py, px = W.topix(sign * V[:, 0], V[:, 2])
        on = 본다 & 선[py, px]
        V[on, 1] -= 방향 * 홈깊이                          # 안쪽으로
        r["새긴정점_" + 이름] = int(on.sum())
        r["보는정점_" + 이름] = int(본다.sum())
    out = trimesh.Trimesh(V, np.asarray(m.faces), process=False)
    후 = 못덮음(out, masks, bs)
    r["못덮음_전"], r["못덮음_후"] = 전, 후
    r["문"] = {"문턱": "세 판 못덮음 증가 <= %g" % 문_여유,
              "증가": {v: round(후[v] - 전[v], 5) for v in W.VIEWS},
              "통과": bool(all(후[v] - 전[v] <= 문_여유 for v in W.VIEWS))}
    r["닫힘"] = bool(out.is_watertight)
    out.export(os.path.join(HERE, "out", "세우기_오메가몬%s.glb" % 꼬리))
    hull.export(os.path.join(HERE, "out", "세우기_껍질%s.glb" % 꼬리))
    r["sigma"] = sigma
    r["초"] = round(time.time() - t0, 1)
    q = os.path.join(OUT, "세우기%s_%s.json" % (꼬리, r["때"]))
    json.dump(r, open(q, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  hull 면 %d -> 새긴 메시 면 %d · 새긴 정점 앞 %d / 뒤 %d · 닫힘 %s"
          % (r["hull면"], r["새긴메시면"], r["새긴정점_앞"], r["새긴정점_뒤"], r["닫힘"]))
    print("  못덮음 전 %s\n        후 %s\n  문 %s (%.0f초)" % (전, 후, "통과" if r["문"]["통과"] else "짐", r["초"]))
    print("  ->", q)
    return r


def 그림():
    from PIL import Image
    import 앨리어싱 as AL
    L = lambda n: trimesh.load(os.path.join(HERE, "out", n), force="mesh")
    src = np.asarray(Image.open(os.path.join(HERE, "out", "누끼", "오메가몬_front", "흰바탕.png"))
                     .convert("RGB").resize((700, 700)))
    병 = os.path.join(HERE, "out", "원화도안", "오메가몬", "조립_앞.png")
    가슴 = ((-0.19, 0.56), 0.38)                          # 확대 틀 — 가슴 · 어깨
    R = []
    for 이름, 껍, 새 in (("격자 그대로", "세우기_껍질.glb", "세우기_오메가몬.glb"),
                       ("보기용 σ1", "세우기_껍질_매끈.glb", "세우기_오메가몬_매끈.glb")):
        if not os.path.exists(os.path.join(HERE, "out", 새)):
            continue
        a, b = L(껍), L(새)
        fr = AL.frame_of(a, 0)
        R.append((이름, [src, np.asarray(Image.open(병).convert("RGB").resize((700, 700))),
                        PL.shaded(a, 0, fr, S=700), PL.shaded(b, 0, fr, S=700),
                        PL.shaded(a, 0, 가슴, S=700), PL.shaded(b, 0, 가슴, S=700)]))
    LR.DC.grid(R, ("원화", "스킬 조립 (회전체 껍질)", "hull", "hull + 도안 선", "hull 가슴 확대", "hull + 선 가슴 확대"),
               "세우기 — 껍질을 회전체에서 hull 로 · 그 위에 도안의 선을 새긴다",
               "정답 메시가 없는 장이라 판정이 아니라 시연이다 · 홈 깊이 0.006 은 지어낸 값(guessed) · σ1 은 보기용이고 기본값이 아니다",
               os.path.join(HERE, "out", "세우기_오메가몬.png"), S=420)


def selfcheck():
    assert "오메가몬" in H.CASES
    for v in ("앞", "뒤"):
        assert os.path.exists(os.path.join(도안디, v, "labels_grown.npy")), v
    m = np.zeros((W.RES, W.RES), bool)
    m[200:800, 300:700] = True
    b = 경계지도("앞", m)
    assert b.shape == (W.RES, W.RES) and not b[:190].any(), "마스크 밖에 선이 있다"
    print("  자가검사 통과 — 경계 화소 %d" % int(b.sum()))


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "검사"
    {"검사": selfcheck, "짓기": 짓기, "매끈": lambda: 짓기(1.0, "_매끈"), "그림": 그림}[a]()
