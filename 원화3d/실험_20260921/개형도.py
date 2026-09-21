# -*- coding: utf-8 -*-
"""**개형도** — 원화 3 판이 메시가 되기까지, 단계마다 **그 단계의 실제 그림**을 붙인다 (2026-09-21).

    python 개형도.py [케이스=오메가몬]   -> out/개형도_<케이스>.png (+ _작게)

사용자(09-21): 「우리 파이프라인 개형도? 그걸로 보여 봐 줄래?」

박스만 그린 그림은 안 그린다 — 단계마다 **그 단계에서 실제로 나온 배열**을 그려 넣고,
숫자는 이 자리에서 다시 재서 찍는다 (정렬 값 · 못덮음 · IoU · 지어냄).
손잡이 값은 **잰 값 / 케이스 데이터 / 지어낸 값**으로 나눠 적는다 — 지어낸 값은 빨갛다.
"""
import os
import subprocess
import sys

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
import hull as H
import 결과물 as RS
W = H.W
HERE = H.HERE
OUT = H.OUT
TH = 300                       # 단계 그림 한 변


def 글꼴(sz, bold=False):
    from PIL import ImageFont
    for f in ((r"C:\Windows\Fonts\malgunbd.ttf",) if bold else ()) + (r"C:\Windows\Fonts\malgun.ttf",):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    from PIL import ImageFont as F
    return F.load_default()


def 그림(a, 색=(40, 44, 52), 바탕=(255, 255, 255)):
    """bool 배열 -> 정사각 썸네일."""
    from PIL import Image
    rgb = np.where(a[:, :, None], np.array(색, np.uint8), np.array(바탕, np.uint8))
    return Image.fromarray(rgb.astype(np.uint8)).resize((TH, TH), Image.LANCZOS)


def 가로로(ims, 틈=6):
    from PIL import Image
    w = sum(i.size[0] for i in ims) + 틈 * (len(ims) - 1)
    s = Image.new("RGB", (w, max(i.size[1] for i in ims)), "white")
    x = 0
    for i in ims:
        s.paste(i, (x, 0))
        x += i.size[0] + 틈
    return s.resize((TH, max(1, int(TH * s.size[1] / s.size[0]))), Image.LANCZOS)


def 장그림(g, k):
    """연속 장의 가로 단면 — **0/1 이 아니라 값**이라는 것이 보이게 색으로 찍는다."""
    from PIL import Image
    s = np.clip(g[:, :, k].T / 12.0, -1, 1)                      # 칸 단위 -> -1..1
    안 = s > 0
    rgb = np.zeros(s.shape + (3,), np.uint8)
    rgb[...] = 255
    rgb[안] = np.stack([(255 - 150 * s[안]), (255 - 90 * s[안]), (255 - 20 * s[안])], -1).astype(np.uint8)
    rgb[~안] = np.stack([(250 + 5 * s[~안]), (250 + 30 * s[~안]), (250 + 40 * s[~안])], -1).astype(np.uint8)
    표면 = (np.abs(g[:, :, k].T) < 0.6)
    rgb[표면] = (20, 20, 20)
    return Image.fromarray(rgb).resize((TH, TH), Image.LANCZOS)


def 렌더(ply, tag, d):
    need = [os.path.join(d, "렌더_%s_%s.png" % (tag, n)) for n in ("앞", "사선", "옆", "뒤")]
    if all(os.path.exists(f) for f in need):
        return need
    open(RS.렌더py, "w", encoding="utf-8").write(RS.렌더소스)
    subprocess.run([RS.BLENDER, "-b", "--python", RS.렌더py, "--", ply, d, tag],
                   capture_output=True, timeout=1800)
    return need


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    d = os.path.join(OUT, "결과물", case)
    os.makedirs(d, exist_ok=True)

    # ---- 파이프라인을 그대로 다시 돈다 (hull.main 의 앞단과 같은 함수들)
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    생, masks = {}, {}
    for v, m in raw.items():
        생[v], _ = H.to_win(m, np.ones(m.shape, np.float32))
        masks[v], _ = H.to_win(H.declutter(m), np.ones(m.shape, np.float32))
    bs = H.CASES[case]["back_sign"] or H.pick_back_sign(masks)
    전 = H.miss(masks, bs)
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    후 = H.miss(masks, bs)
    g, axes = H.field_default(masks, back_sign=bs)
    선 = H.ink_map(os.path.join(base, src["front"]))
    mesh = trimesh.load(os.path.join(OUT, "hull.glb"), force="mesh", process=False)
    V, F = np.asarray(mesh.vertices), np.asarray(mesh.faces)
    iou, 지어 = {}, 0
    for v in W.VIEWS:
        s = np.asarray(W.silhouette(V, F, v, bs if v == "back" else None)).astype(bool)
        iou[v] = W.iou(masks[v], s)
        지어 += int((s & ~masks[v].astype(bool)).sum())

    # ---- 단계 그림
    흰 = [os.path.join(OUT, "누끼", "%s_%s" % (case, v), "흰바탕.png") for v in ("front", "side", "back")]
    원화 = 가로로([Image.open(f).convert("RGB").resize((TH, TH)) for f in 흰 if os.path.exists(f)])
    깎 = {v: H.declutter(raw[v]).astype(bool) for v in W.VIEWS}   # **원화 화소 자리 그대로** 비교한다
    버림 = {v: int((raw[v].astype(bool) & ~깎[v]).sum()) for v in W.VIEWS}
    vd = max(버림, key=버림.get)                                  # 지시선이 제일 많이 붙은 판을 보인다
    a0 = raw[vd].astype(bool)
    지시 = Image.fromarray(np.where(깎[vd][:, :, None], np.array([40, 44, 52], np.uint8),
                                    np.where(a0[:, :, None], np.array([220, 60, 60], np.uint8),
                                             np.array([255, 255, 255], np.uint8))).astype(np.uint8)
                           ).resize((TH, TH), Image.LANCZOS)
    B = masks["back"][:, ::-1] if bs < 0 else masks["back"]
    겹 = Image.fromarray(np.stack([255 - 140 * masks["front"].astype(np.uint8),
                                   255 - 140 * masks["side"].astype(np.uint8),
                                   255 - 140 * B.astype(np.uint8)], -1)).resize((TH, TH), Image.LANCZOS)
    k = int(g.shape[2] * 0.62)                                   # 가슴 높이 단면 (다리 높이는 타원 두 개라 덜 보인다)
    장 = 장그림(g, k)
    몸png = os.path.join(d, "렌더_먹선몸_앞.png")
    몸 = Image.open(몸png).convert("RGB").resize((TH, TH)) if os.path.exists(몸png) else 그림(np.zeros((8, 8), bool))
    먹 = 그림(선)
    ply = os.path.join(d, "개형_hull.ply")
    if not os.path.exists(ply):
        mesh.export(ply)
    r = 렌더(ply, "개형", d)
    결 = 가로로([Image.open(f).convert("RGB") for f in r[:2] if os.path.exists(f)])

    # ---- 단계 표 (제목 · 함수 · 한 줄 · 손잡이[빨강이면 지어낸 값])
    단계 = [
        ("① 원화 3 판을 읽는다", "hull.CASES · window.art_mask", 원화,
         "앞 · 옆 · 뒤 한 장씩. 배경은 누끼로 이미 뺐다 (grabCut · IoU 0.992).",
         [("판 크기 1024²", 0), ("후면 좌우 규약 %+d" % bs, 1)]),
        ("② 지시선을 뺀다", "hull.declutter(minh=8)", 지시,
         "빨강이 버린 것 — 화살표 · 치수선 · 판 밖 부스러기. 사람이 그린 설명은 형상이 아니다.",
         [("%s 판" % vd, 1), ("버린 화소 %d" % 버림[vd], 0), ("높이 문턱 8 화소", 2)]),
        ("③ 창에 앉히고 세 판을 맞춘다", "hull.to_win · hull.align", 겹,
         "빨강 앞 · 초록 옆 · 파랑 뒤. 겹칠수록 어둡다. 세 판이 싸우면 여기서 드러난다.",
         [("옆 dy %+.0f s %.3f" % (p[0], p[1]), 0), ("뒤 dx %+.0f dy %+.0f s %.3f" % (p[2], p[3], p[4]), 0),
          ("못덮음 %.1f%% → %.1f%%" % (100 * max(전.values()), 100 * max(후.values())), 0)]),
        ("④ 연속 장으로 깎는다", "hull.field_default (FIELD=True)", 장,
         "가로 단면. 0/1 복셀이 아니라 **값**이다 — 검은 선이 표면 자리. 높이마다 내접 타원.",
         [("격자 %d³" % g.shape[0], 2), ("높이 스무딩 σ %.1f" % H.SMOOTH_Z, 3), ("가드 %.1f 칸" % H.SMOOTH_GUARD, 3)]),
        ("⑤ 마칭큐브 · 큰 덩어리만", "hull.mesh_from_field · Trimesh.split", 몸,
         "값 장에서 표면을 뽑아 면으로 만든다. 부유 파편은 버리고 뒤집힌 법선은 되돌린다.",
         [("정점 %d" % len(V), 0), ("닫힘 %s" % mesh.is_watertight, 0)]),
        ("⑥ 원화의 먹선을 새긴다", "hull.ink_map · hull.carve_ink", 먹,
         "원화에 실제로 그려진 검은 선만 (가는 것 + 굵은 칠의 테두리). 시선 방향 안쪽으로만 민다.",
         [("어둠 120", 3), ("홈 깊이 %.3f" % H.INK_DEPTH, 3), ("실루엣 안 바뀜", 0)]),
        ("⑦ 결과", "out/hull.glb", 결,
         "앞 · 사선. 3D 프린트 · 굿즈 원형으로 그대로 나간다.",
         [("면 %d" % len(F), 0)]),
        ("⑧ 되받아 재서 증명한다", "실험_20260921/공정.py", None,
         "결과를 원화 위에 되받아 찍는다. hull 은 상한이라 **원화 밖 화소는 0 이어야** 한다.",
         [("IoU 앞 %.3f · 옆 %.3f · 뒤 %.3f" % (iou["front"], iou["side"], iou["back"]), 0),
          ("원화 밖 %d 화소 = 경계 3 화소 띠 (부풀리면 0)" % 지어, 0)]),
    ]

    # ---- 그리기
    색 = {0: (28, 110, 60), 1: (60, 90, 170), 2: (90, 90, 100), 3: (200, 40, 40)}   # 잰 값 · 케이스 · 손잡이 · 지어낸 값
    Wd, 여백, 그림x, 틈 = 1180, 28, 830, 26
    글x = 여백 + 22
    글폭 = 그림x - 글x - 24
    sheet = Image.new("RGB", (Wd, 100), "white")
    dr = ImageDraw.Draw(sheet)
    f제 = 글꼴(34, True); f소 = 글꼴(24, True); f본 = 글꼴(21); f코 = 글꼴(19); f태 = 글꼴(19)

    def 접기(t, f):
        줄, 줄글 = [], ""
        for w in t.replace("**", "").split(" "):
            시 = (줄글 + " " + w).strip()
            if dr.textlength(시, f) > 글폭 and 줄글:
                줄.append(줄글); 줄글 = w
            else:
                줄글 = 시
        return 줄 + ([줄글] if 줄글 else [])

    배치 = []                                                    # 카드마다 (줄들, 태그줄들, 높이)
    for 제목, 함수, im, 설명, 태그 in 단계:
        줄 = 접기(설명, f본)
        줄들, 현, 폭 = [], [], 0
        for t, c in 태그:
            w = dr.textlength(t, f태) + 20
            if 폭 + w > 글폭 and 현:
                줄들.append(현); 현, 폭 = [], 0
            현.append((t, c, w)); 폭 += w + 10
        if 현:
            줄들.append(현)
        h = max(88 + 28 * len(줄) + 8 + 38 * len(줄들) + 14, (im.size[1] if im is not None else 0) + 32)
        배치.append((줄, 줄들, h))

    Hg = 여백 + 96 + sum(h + 틈 for _, _, h in 배치)
    sheet = Image.new("RGB", (Wd, Hg), "white")
    dr = ImageDraw.Draw(sheet)
    dr.text((여백, 여백), "원화 → 3D 개형도 · %s" % case, (20, 22, 28), f제)
    dr.text((여백, 여백 + 46), "파일 하나로 돈다:  python 원화3d/hull.py        "
                              "초록 잰 값 · 파랑 케이스 데이터 · 회색 손잡이 · 빨강 지어낸 값", (90, 92, 100), f본)
    y = 여백 + 96
    for i, ((제목, 함수, im, 설명, 태그), (줄, 줄들, h)) in enumerate(zip(단계, 배치)):
        dr.rounded_rectangle([여백, y, Wd - 여백, y + h], 12, outline=(210, 212, 218), width=2)
        dr.text((글x, y + 18), 제목, (20, 22, 28), f소)
        dr.text((글x, y + 54), 함수, (70, 100, 190), f코)
        for j, line in enumerate(줄):
            dr.text((글x, y + 88 + j * 28), line, (55, 58, 66), f본)
        yy = y + 88 + 28 * len(줄) + 8
        for 한줄 in 줄들:
            x = 글x
            for t, c, w in 한줄:
                dr.rounded_rectangle([x, yy, x + w, yy + 30], 8, fill=(246, 247, 249))
                dr.text((x + 10, yy + 4), t, 색[c], f태)
                x += w + 10
            yy += 38
        if im is not None:
            sheet.paste(im, (그림x, y + (h - im.size[1]) // 2))
        if i < len(단계) - 1:
            cx = Wd // 2
            dr.line([cx, y + h, cx, y + h + 틈 - 8], fill=(170, 175, 185), width=3)
            dr.polygon([(cx - 7, y + h + 틈 - 10), (cx + 7, y + h + 틈 - 10), (cx, y + h + 틈)], fill=(170, 175, 185))
        y += h + 틈
    o = os.path.join(OUT, "개형도_%s.png" % case)
    sheet.save(o)
    sheet.resize((Wd * 2 // 3, Hg * 2 // 3), Image.LANCZOS).save(o.replace(".png", "_작게.png"))
    print("  정렬 후 못덮음 %s" % {v: round(100 * 후[v], 2) for v in W.VIEWS})
    print("  IoU %s · 원화 밖 %d 화소" % ({v: round(iou[v], 3) for v in W.VIEWS}, 지어))
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")
