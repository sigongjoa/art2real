# -*- coding: utf-8 -*-
"""**GPT 의 파츠 분리도 대 우리가 잰 분할** — 같은 캐릭터에서 맞대 본다 (2026-09-21).

    python 분할비교.py [케이스=메카2]   -> out/분할비교_<케이스>.png · out/기록/분할비교_*.json

사용자(09-21): 「이거랑 **파츠 분할된 것**도 있어야 피규어화하기 좋지 않을까?」

파츠 분리도는 **그림이지 3D 데이터가 아니다** — 그대로는 파이프라인에 못 넣는다.
그래서 **대조군**으로 쓴다: 사람(GPT)이 「여기서 자른다」고 본 자리와
우리가 거리장 분수령으로 **잰** 관절면이 같은 높이인가?

    GPT 쪽    분해도의 흰 여백으로 갈린 **덩어리**들. 각 덩어리의 위 · 아래 끝이 곧 «자른 자리»
    우리 쪽   `면자르기` 의 관절면 z (0~1 · 발바닥 0 · 정수리 1)

두 자리 목록을 **키로 정규화**해서 맞댄다. 가까우면 우리 분할이 사람 감각과 같다는 뜻이고,
어긋나면 어디가 다른지가 곧 다음 할 일이다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
OUT = os.path.join(r"G:\art2real\원화3d", "out")
허용 = 0.03                     # 키의 3% 안이면 «같은 자리»로 본다


def 분해도자리(png, 최소몫=0.0015):
    """분해도 -> 덩어리들의 (위, 아래) z. 키로 정규화한다."""
    import cv2
    im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_COLOR)
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    몸 = ndimage.binary_fill_holes(g < 240)
    lab, n = ndimage.label(몸)
    크 = np.bincount(lab.ravel())
    쓸 = [i for i in range(1, n + 1) if 크[i] >= 최소몫 * 몸.sum()]
    rows = np.where(몸.any(1))[0]
    z0, z1 = rows.min(), rows.max()
    키 = z1 - z0 + 1
    덩 = []
    for i in 쓸:
        r = np.where((lab == i).any(1))[0]
        덩.append((1 - (r.max() - z0) / 키, 1 - (r.min() - z0) / 키))     # (아래 z, 위 z)
    덩.sort(key=lambda t: -t[1])
    자리 = sorted({round(float(v), 3) for a, b in 덩 for v in (a, b) if 0.02 < v < 0.98})
    return 덩, 자리, len(쓸)


def main(case="메카2"):
    from PIL import Image, ImageDraw
    분해 = os.path.join(OUT, "도안생성", case, "분해도.png")
    관절 = os.path.join(OUT, "관절_%s.json" % case)
    덩, GPT자리, 덩수 = 분해도자리(분해)
    j = json.load(open(관절, encoding="utf-8"))
    import hull as H
    W = H.W
    우리자리 = sorted({round((jj["cut"]["point"][2] - W.Z0) / (W.Z1 - W.Z0), 3) for jj in j["joints"]})
    # 우리 z 는 창 좌표라 발바닥 0 · 정수리 1 이 아니다 — 몸이 차지한 구간으로 다시 정규화
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {v: H.to_win(H.declutter(m), np.ones(m.shape, np.float32))[0] for v, m in raw.items()}
    rows = np.where(masks["front"].astype(bool).any(1))[0]
    zr0 = 1 - (rows.max() + 0.5) / masks["front"].shape[0]
    zr1 = 1 - (rows.min() + 0.5) / masks["front"].shape[0]
    def 창z(z):                                                        # 창 z -> 몸 기준 0~1
        t = (z - W.Z0) / (W.Z1 - W.Z0)
        return (t - zr0) / max(zr1 - zr0, 1e-6)
    우리 = sorted({round(float(창z(jj["cut"]["point"][2])), 3) for jj in j["joints"]})

    맞, 못 = [], []
    for a in 우리:
        d = min((abs(a - b), b) for b in GPT자리) if GPT자리 else (9, None)
        (맞 if d[0] <= 허용 else 못).append({"우리": a, "가까운 GPT": d[1], "차": round(d[0], 3)})
    r = {"케이스": case, "GPT 덩어리": 덩수, "GPT 자른 자리": len(GPT자리),
         "우리 관절면": len(우리), "맞은 자리": len(맞), "허용": 허용,
         "맞음": 맞, "어긋남": 못}
    print("  GPT 분해도 덩어리 %d · 자른 자리 %d" % (덩수, len(GPT자리)))
    print("  우리 관절면 %d · 키의 %.0f%% 안에서 맞은 것 **%d / %d**"
          % (len(우리), 허용 * 100, len(맞), len(우리)))
    for m in 맞:
        print("   맞음   우리 z %.3f ~ GPT %.3f (차 %.3f)" % (m["우리"], m["가까운 GPT"], m["차"]))
    for m in 못:
        print("   어긋남 우리 z %.3f ~ 제일 가까운 GPT %.3f (차 %.3f)" % (m["우리"], m["가까운 GPT"], m["차"]))

    # ---- 그림: 분해도 옆에 두 자리 목록을 눈금으로
    S = 700
    im = Image.open(분해).convert("RGB")
    im = im.resize((int(im.width * S / im.height), S))
    sheet = Image.new("RGB", (im.width + 520, S + 110), "white")
    sheet.paste(im, (0, 100))
    dr = ImageDraw.Draw(sheet)
    try:
        from PIL import ImageFont
        f제 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)
        f본 = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)
    except OSError:
        f제 = f본 = None
    dr.text((14, 14), "GPT 파츠 분리도 대 우리가 잰 관절면 · %s" % case, (20, 22, 28), f제)
    dr.text((14, 50), "GPT 덩어리 %d · 자른 자리 %d   /   우리 관절면 %d · 맞은 것 %d (키의 %.0f%% 안)"
            % (덩수, len(GPT자리), len(우리), len(맞), 허용 * 100), (60, 64, 72), f본)
    x = im.width + 20
    dr.text((x, 100), "GPT", (40, 90, 200), f본)
    dr.text((x + 120, 100), "우리", (200, 40, 40), f본)
    for v in GPT자리:
        y = 130 + int((1 - v) * (S - 60))
        dr.line([x, y, x + 90, y], (40, 90, 200), 2)
        dr.text((x + 94, y - 11), "%.2f" % v, (40, 90, 200), f본)
    for v in 우리:
        y = 130 + int((1 - v) * (S - 60))
        c = (28, 110, 60) if any(abs(v - b) <= 허용 for b in GPT자리) else (200, 40, 40)
        dr.line([x + 160, y, x + 250, y], c, 3)
        dr.text((x + 254, y - 11), "%.2f" % v, c, f본)
    o = os.path.join(OUT, "분할비교_%s.png" % case)
    sheet.save(o)
    os.makedirs(os.path.join(OUT, "기록"), exist_ok=True)
    json.dump(r, open(os.path.join(OUT, "기록", "분할비교_%s_%s.json" % (case, time.strftime("%Y%m%d_%H%M"))),
                      "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", o)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "메카2")
