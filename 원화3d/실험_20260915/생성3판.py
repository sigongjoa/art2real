# -*- coding: utf-8 -*-
"""**생성 3판** — 정면 한 장에서 옆·뒤를 이미지 생성으로 그려 hull 에 넣는다 (2026-09-15).

    python 생성3판.py 검사                        자가검사만
    python 생성3판.py 생성 <케이스> [flash|pro]    -> out/생성3판/<케이스>_<모델>.png + out/시트/<케이스>_생성<모델>/
    python 생성3판.py 나눔 <케이스> [flash|pro]    받아 둔 날것을 다시 나눠 시트만 새로 쓴다 (API 안 부름)
    python 생성3판.py 잰다 <케이스> [flash|pro]    -> out/기록/생성3판_진행.jsonl 한 줄
    python 생성3판.py 판정                        -> out/기록/생성3판_<때>.json
    python 생성3판.py 부피 <케이스>                사후 제부피 대조 -> out/기록/생성3판_부피_진행.jsonl

판정은 `claudedocs/plan_생성3판_20260915.md` 「판정」 절 그대로다 — 돌리기 전에 적었다.
키는 저장소 밖 `~/.gemini_key` 에서 읽는다.
"""
import base64
import json
import os
import shutil
import sys
import time
import urllib.request

import cv2
import numpy as np
import trimesh
from scipy import ndimage

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
os.chdir(HERE)
import hull as H
import win as W
import 오라클 as O

SHEET = os.path.join(HERE, "out", "시트")
RAW = os.path.join(HERE, "out", "생성3판")
PROG = os.path.join(HERE, "out", "기록", "생성3판_진행.jsonl")
CASES = {                                    # 케이스: 모델에 줄 정면 판 (읽히는 쪽)
    "avatarsample_g": "",
    "마네킹_팔앞뒤": "",
    "cloak_Chest_O72u4Drp8k": "_선2",
    "wizard_Evil_Wizard_bdxawstqtq": "_선2",
}
MODELS = {"flash": "gemini-3.1-flash-image", "pro": "gemini-3-pro-image"}
LAM = 1.00
P192 = (W.U1 - W.U0) / 192.0
CH, CW = 1024, 2389                          # 21:9 캔버스 · 판 셋
TICK = (0, 0, 255)                           # BGR 빨강 — 키 눈금
PROMPT = """This image is a three-panel orthographic model sheet of ONE character/object.
The LEFT panel is the FRONT view and must stay unchanged.
Draw the SIDE view in the MIDDLE panel and the BACK view in the RIGHT panel, of exactly the same character/object.

Rules:
- Orthographic projection. No perspective, no vanishing point, camera at the same height as the front view.
- Same scale in all panels: the top and the bottom of the figure touch the same heights as in the front view (red tick marks at the image edges).
- Same pose. Do not move arms, legs, or any part.
- In the SIDE view the figure faces to the RIGHT of the image.
- Same drawing style as the front view: black outlines and flat colors.
- Pure white background. No shadow, no ground, no text, no extra objects, no panel borders."""


# ───────────────────────────────────────────── 판 읽고 쓰기
def rgba(path):
    return cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_UNCHANGED)


def on_white(im):
    if im.shape[2] == 3:
        return im
    a = im[:, :, 3:4].astype(np.float32) / 255
    return (im[:, :, :3] * a + 255 * (1 - a)).astype(np.uint8)


def write_png(path, im):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imencode(".png", im)[1].tofile(path)


def compose(front_bgr, mask):
    """정면을 왼쪽 판에 앉힌 21:9 캔버스 + 캔버스 양 끝에 키 눈금 (위 · 아래). 반환: 캔버스, (위, 아래) 행."""
    ys, xs = np.nonzero(mask)
    crop = front_bgr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    pw = CW // 3
    s = min(0.84 * CH / crop.shape[0], 0.9 * pw / crop.shape[1])
    crop = cv2.resize(crop, (max(1, round(crop.shape[1] * s)), max(1, round(crop.shape[0] * s))), interpolation=cv2.INTER_AREA)
    h, w = crop.shape[:2]
    top = (CH - h) // 2
    can = np.full((CH, CW, 3), 255, np.uint8)
    can[top:top + h, (pw - w) // 2:(pw - w) // 2 + w] = crop
    for y in (top, top + h - 1):
        for x0 in (0, CW - 24):
            can[max(y - 2, 0):y + 3, x0:x0 + 24] = TICK
    return can, (top, top + h - 1)


def extract(panel_bgr, edge=30, min_area=200):
    """흰 바탕 판 -> RGBA. **테두리에서 흘려 채운 흰 곳만** 바탕이다 — 선으로 둘러싸인 흰 옷은 전경으로 남는다.
    판 양 끝 `edge` 열(키 눈금 자리)은 버리고, `min_area` 화소 미만 조각도 버린다."""
    white = (panel_bgr > 235).all(2)
    lab, _ = ndimage.label(white)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    bg = np.isin(lab, border[border > 0])
    fg = ~bg
    fg[:, :edge] = fg[:, -edge:] = False
    lab, n = ndimage.label(fg)
    if n:
        area = ndimage.sum(fg, lab, np.arange(1, n + 1))
        fg = np.isin(lab, 1 + np.flatnonzero(area >= min_area))
    out = np.dstack([panel_bgr, np.where(fg, 255, 0).astype(np.uint8)])
    return out


def front_only(front_mask):
    """대조군 — 옆 = 정면 줄마다 **조각 평균 폭**의 중앙값을 고정 두께로 · 뒤 = 정면 좌우 반전. 옆·뒤 정보 0.
    ponytail: 두께 하나로 몸 전체를 민다. 부위별 두께가 필요하면 그건 이미 정보다."""
    rows = []
    for r in np.flatnonzero(front_mask.any(1)):
        runs = np.flatnonzero(np.diff(np.r_[0, front_mask[r].astype(np.int8), 0]))
        rows.append((runs[1::2] - runs[0::2]).mean())
    d = int(round(np.median(rows)))
    side = np.zeros_like(front_mask)
    c = front_mask.shape[1] // 2
    side[front_mask.any(1), c - d // 2:c - d // 2 + d] = True
    return side, front_mask[:, ::-1].copy(), d


def mask_png(m):
    im = np.full(m.shape + (4,), 255, np.uint8)
    im[:, :, :3] = np.where(m[:, :, None], 128, 255)
    im[:, :, 3] = np.where(m, 255, 0)
    return im


def make_sheet(case, name, side_rgba, back_rgba):
    d = os.path.join(SHEET, name)
    os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(SHEET, case, "front.png"), os.path.join(d, "front.png"))
    shutil.copy(os.path.join(SHEET, case, "truth.glb"), os.path.join(d, "truth.glb"))
    write_png(os.path.join(d, "side.png"), side_rgba)
    write_png(os.path.join(d, "back.png"), back_rgba)
    return d


# ───────────────────────────────────────────── 생성
def call(model, can_bgr):
    key = open(os.path.expanduser("~/.gemini_key")).read().strip()
    body = {"contents": [{"parts": [{"text": PROMPT},
                                    {"inline_data": {"mime_type": "image/png",
                                                     "data": base64.b64encode(cv2.imencode(".png", can_bgr)[1].tobytes()).decode()}}]}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "21:9"}}}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % model,
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key})
    r = json.load(urllib.request.urlopen(req, timeout=300))
    for part in r["candidates"][0]["content"]["parts"]:
        blob = part.get("inlineData") or part.get("inline_data")
        if blob:
            return cv2.imdecode(np.frombuffer(base64.b64decode(blob["data"]), np.uint8), cv2.IMREAD_COLOR)
    raise RuntimeError("이미지가 안 왔다: %s" % json.dumps(r)[:400])


def generate(case, m):
    src = rgba(os.path.join(SHEET, case + CASES[case], "front.png"))
    can, ticks = compose(on_white(src), W.art_mask(os.path.join(SHEET, case + CASES[case], "front.png")))
    t0 = time.time()
    out = call(MODELS[m], can)
    write_png(os.path.join(RAW, "%s_%s_입력.png" % (case, m)), can)
    write_png(os.path.join(RAW, "%s_%s.png" % (case, m)), out)
    print("  %s · %s · %dx%d · %.0f초 -> out/생성3판/%s_%s.png" % (case, MODELS[m], out.shape[1], out.shape[0], time.time() - t0, case, m))
    resplit(case, m)


def split3(im, edge=30, gap=12):
    """생성 캔버스 -> 그림 셋의 열 구간. **3등분이 아니다** — 모델이 판 폭을 안 지킨다 (뒤판 손끝이 가운데 판을 넘었다).
    전경 열(흰 바탕 아닌 열)의 연속 구간을 `gap` 열 틈까지 잇고, 폭 큰 셋을 x 순서로."""
    col = (im[:, edge:-edge] <= 235).any(2).any(0)
    runs = np.flatnonzero(np.diff(np.r_[0, col.astype(np.int8), 0])).reshape(-1, 2) + edge
    merged = [list(runs[0])]
    for a, b in runs[1:]:
        if a - merged[-1][1] < gap:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    assert len(merged) >= 3, "그림이 셋이 아니다 (%d 구간)" % len(merged)
    big = sorted(sorted(merged, key=lambda r: r[1] - r[0])[-3:])
    return [(max(a - 8, 0), min(b + 8, im.shape[1])) for a, b in big]


def resplit(case, m):
    out = cv2.imdecode(np.fromfile(os.path.join(RAW, "%s_%s.png" % (case, m)), np.uint8), cv2.IMREAD_COLOR)
    (_, _), (s0, s1), (b0, b1) = split3(out)
    pad = lambda p: cv2.copyMakeBorder(p, 0, 0, 40, 40, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    make_sheet(case, case + "_생성" + m, extract(pad(out[:, s0:s1])), extract(pad(out[:, b0:b1])))
    print("  나눔 — 옆 %d~%d · 뒤 %d~%d" % (s0, s1, b0, b1))


def controls(case):
    """배관(렌더 옆·뒤를 흰 바탕에 얹어 같은 추출기로) · 정면만 판을 만든다. 이미 있으면 둔다."""
    if not os.path.exists(os.path.join(SHEET, case + "_배관", "side.png")):
        sv = [extract(on_white(rgba(os.path.join(SHEET, case, v + ".png")))) for v in ("side", "back")]
        make_sheet(case, case + "_배관", *sv)
    if not os.path.exists(os.path.join(SHEET, case + "_정면만", "side.png")):
        s, b, _ = front_only(W.art_mask(os.path.join(SHEET, case, "front.png")))
        make_sheet(case, case + "_정면만", mask_png(s), mask_png(b))


# ───────────────────────────────────────────── 재기
def misfit(name):
    """`O.build` 와 같은 순서로 판을 앉히고 맞춘 뒤 못 덮은 양 (시점마다)."""
    src, base = H.CASES[name]["src"], H.art_dir(name)
    masks = {v: H.to_win(H.declutter(W.art_mask(os.path.join(base, f)))) for v, f in src.items()}
    p = H.align(masks, back_sign=H.CASES[name]["back_sign"])
    return {v: round(x, 4) for v, x in H.miss(H._warp(masks, p), H.CASES[name]["back_sign"]).items()}


def measure(case, m):
    controls(case)
    H.register_sheets()
    truth = trimesh.load(os.path.join(SHEET, case, "truth.glb"), force="mesh")
    i128, i192 = O._iou_fn(truth), O._iou_fn(truth, P192)
    row = {"case": case, "모델": MODELS[m], "판": "생성3판 v1 · 21:9 한 캔버스 · 키 눈금 · 타원 lam1.00 (2026-09-15)"}
    for tag, name in (("렌더", case), ("배관", case + "_배관"), ("생성", case + "_생성" + m), ("정면만", case + "_정면만")):
        t0 = time.time()
        plain, deep, axes, _ = O.build(name, truth, LAM, "타원")
        row["못덮음_" + tag] = misfit(name)
        row["이진_" + tag], row["이진·192_" + tag] = i128(plain, axes), i192(plain, axes)
        row["타원_" + tag], row["타원·192_" + tag] = i128(deep, axes), i192(deep, axes)
        print("  %-6s 못덮음 %s · 이진 %.4f · 타원 %.4f / %.4f (192) · %.0f초"
              % (tag, row["못덮음_" + tag], row["이진_" + tag], row["타원_" + tag], row["타원·192_" + tag], time.time() - t0), flush=True)
    row["배관차"] = abs(row["타원_배관"] - row["타원_렌더"])
    with open(PROG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("  배관차 %.4f (< 0.005) · 생성−정면만 %+.4f / %+.4f (192) · 생성−렌더 %+.4f"
          % (row["배관차"], row["타원_생성"] - row["타원_정면만"], row["타원·192_생성"] - row["타원·192_정면만"],
             row["타원_생성"] - row["타원_렌더"]))


def judge():
    """계획 「판정」 절 그대로. 모델마다 따로 — 케이스마다 마지막 줄을 쓴다."""
    rows = {}
    for line in open(PROG, encoding="utf-8"):
        r = json.loads(line)
        rows[(r["모델"], r["case"])] = r
    out = {}
    for m, model in MODELS.items():
        rs = [rows[(model, c)] for c in CASES if (model, c) in rows]
        g = lambda k: np.array([r[k] for r in rs])
        if len(rs) < len(CASES):
            out[m] = "케이스 %d/%d — 판정 안 함" % (len(rs), len(CASES))
            continue
        if (g("배관차") >= 0.005).any():
            out[m] = "배관 어긋남 — 숫자를 버린다"
            continue
        worst = [max(r["못덮음_생성"]["side"], r["못덮음_생성"]["back"]) for r in rs]
        d = [g("타원_생성") - g("타원_정면만"), g("타원·192_생성") - g("타원·192_정면만")]
        q1 = bool(max(worst) <= 0.0757)
        q2 = all(x.mean() > 0 and (x > 0).sum() > len(rs) / 2 for x in d)
        out[m] = {"Q1 최대 못덮음": round(max(worst), 4), "Q1": q1,
                  "Q2 생성−정면만 평균 128·192": [round(float(x.mean()), 4) for x in d],
                  "Q2 이긴 장 128·192": [int((x > 0).sum()) for x in d], "Q2": q2,
                  "렌더 대비 손실 중앙": round(float(np.median(g("타원_생성") - g("타원_렌더"))), 4),
                  "다음": ("가이드 강화 판본" if not q1 else "넓은 벤치 판정 계획" if q2 else "결과만 적고 멈춤")}
    path = os.path.join(HERE, "out", "기록", "생성3판_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print("  -> %s" % path)


def volume_control(case):
    """**사후 대조군 (계획에 없었다).** 렌더 hull 을 그 판본과 **같은 부피**까지 고르게 안으로 민 면 (`H.even_control`).
    마네킹에서 정면만 · 생성이 렌더를 이겼다 — hull 이 뚱뚱하면 아무렇게나 얇아져도 IoU 가 오른다 (09-09).
    판본이 이걸 이겨야 옆·뒤가 **모양**을 준 것이다."""
    H.register_sheets()
    truth = trimesh.load(os.path.join(SHEET, case, "truth.glb"), force="mesh")
    i128, i192 = O._iou_fn(truth), O._iou_fn(truth, P192)
    plain, _, axes, _ = O.build(case, truth, LAM, "타원")
    row, cache = {"case": case, "판": "생성3판 사후 제부피 대조 (2026-09-15)"}, {}
    for tag in ["렌더"] + ["생성" + m for m in MODELS] + ["정면만"]:
        name = case if tag == "렌더" else case + "_" + tag
        _, deep, ax, _ = O.build(name, truth, LAM, "타원")
        mesh = O.C.to_mesh(deep, ax)
        row[tag] = [i128(mesh, ax), i192(mesh, ax)]
        row["부피비@" + tag] = round(mesh.volume / O.C.to_mesh(plain, axes).volume, 3)
        try:
            em, _ = H.even_control(plain, axes, mesh.volume, cache=cache)
        except AssertionError as e:                      # 목표 부피가 hull 을 고르게 밀어 닿는 범위 밖
            row["균일@" + tag] = None
            print("  %-26s %-8s %.4f / %.4f · 같은 부피 대조군 못 지음 (렌더 hull 대비 부피 %.2f) — %s"
                  % (case[:26], tag, row[tag][0], row[tag][1], row["부피비@" + tag], str(e)[:40]), flush=True)
            continue
        row["균일@" + tag] = [i128(em, axes), i192(em, axes)]
        print("  %-26s %-8s %.4f / %.4f · 같은 부피 렌더 %.4f / %.4f · 차 %+.4f / %+.4f" % (
            case[:26], tag, row[tag][0], row[tag][1], row["균일@" + tag][0], row["균일@" + tag][1],
            row[tag][0] - row["균일@" + tag][0], row[tag][1] - row["균일@" + tag][1]), flush=True)
    with open(os.path.join(HERE, "out", "기록", "생성3판_부피_진행.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


# ───────────────────────────────────────────── 자가검사
def selfcheck():
    # 1 추출기 — 흰 바탕 · 검은 테 흰 상자(속이 흰 옷)는 통째로 전경 · 판 끝 눈금은 버린다
    p = np.full((200, 300, 3), 255, np.uint8)
    cv2.rectangle(p, (100, 40), (180, 160), (0, 0, 0), 3)
    p[20:25, 0:24] = TICK
    a = extract(p)[:, :, 3] > 0
    assert a[100, 140] and a[40, 100] and not a[10, 10] and not a[22, 5], "추출기가 틀렸다"
    # 선 두께 3 이 테 밖으로 한두 칸 나간다
    assert 81 * 121 <= a.sum() <= 86 * 126, "상자 속 흰 곳이 전경으로 안 남았다 (%d)" % a.sum()
    # 2 정면만 — 다리 둘(폭 10)이면 두께 10, 뒤는 좌우 반전
    f = np.zeros((50, 100), bool)
    f[10:30, 30:70] = True                      # 몸 (폭 40) 20 줄
    f[30:50, 35:45] = f[30:50, 55:65] = True    # 다리 둘 (폭 10) 20 줄
    f[0:10, 45:55] = True                       # 머리 (폭 10) 10 줄
    s, b, d = front_only(f)
    assert d == 10 and s[5].sum() == 10 and np.array_equal(b, f[:, ::-1]), "정면만 대조군이 틀렸다 (두께 %d)" % d
    # 3 캔버스 — 정면이 왼쪽 판 안 · 눈금이 정면 위아래 행에
    fr = np.full((400, 200, 3), 255, np.uint8)
    fr[50:350, 60:140] = 0
    can, (t, bt) = compose(fr, (fr < 250).any(2))
    col = (can < 250).any(2)[:, 24:CW - 24]
    ys = np.flatnonzero(col.any(1))
    assert ys.min() == t and ys.max() == bt and (can[t, :24] == TICK).all(), "캔버스 눈금이 정면 키와 안 맞다"
    assert not col[:, CW // 3 - 24:].any(), "정면이 왼쪽 판을 넘었다"
    # 4 나누기 — 셋째 그림이 3등분 선을 넘어도 한 덩어리 · 그림 속 작은 틈은 잇는다
    g = np.full((100, 900, 3), 255, np.uint8)
    g[20:80, 100:200] = g[20:80, 380:480] = g[20:80, 580:700] = g[20:80, 706:800] = 0
    assert split3(g) == [(92, 208), (372, 488), (572, 808)], "나누기가 틀렸다 %s" % split3(g)
    print("  자가검사 통과 — 추출기 · 정면만 대조군 · 캔버스 눈금 · 나누기")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "검사":
        selfcheck()
    elif a[0] == "생성":
        selfcheck()
        generate(a[1], a[2] if len(a) > 2 else "flash")
    elif a[0] == "나눔":
        resplit(a[1], a[2] if len(a) > 2 else "flash")
    elif a[0] == "잰다":
        measure(a[1], a[2] if len(a) > 2 else "flash")
    elif a[0] == "판정":
        judge()
    elif a[0] == "부피":
        volume_control(a[1])
