# -*- coding: utf-8 -*-
"""**누끼를 딴다** — 원화에서 배경을 빼고 캐릭터만 남긴 파일을 낸다 (2026-09-21).

    python 누끼.py 검사
    python 누끼.py 따기 [--full]   -> out/누끼/<장>/{투명.png, 흰바탕.png, 마스크.png}
    python 누끼.py 그림            -> out/누끼.png

사용자(09-21): 「배경은 누끼 따서 제거할 수 있잖아」 · 「배경 없고 캐릭터 전용 이미지를
만들어 내서 하는 거지, 오메가몬 하는 것처럼」.

**방법은 이미 정해졌다** — `배경` 바퀴에서 넷을 겨뤄 `cv2.grabCut` 이 27/27 로 이겼다
(마스크 IoU 중앙 **0.992** · 최악 0.883 · 현행 모서리홍수는 0.016). `전처리.배경마스크` 의
기본값도 그때 바꿨다. 여기서는 **그 결과를 파일로 낸다.**

    알파가 있으면 알파를 쓴다 (09-21 에 우리가 이걸 놓치고 있었다)
    없으면 grabCut — 긴 변 1024 로 줄여 계산하고 원본 크기로 되돌린다
    가장자리는 **한 번 다듬는다** — 닫기 3 + 가우시안 1.2 로 반투명 띠 (알파 매팅은 안 한다)

**이 바퀴는 자를 안 만든다.** 합격 여부는 `배경` 바퀴가 이미 쟀다. 여기 숫자는 **물건 몫**뿐이다.

**돌려 보고 알아낸 것** — 알파 없는 한 장(은둔자 채색 · 사진 배경)에서 기본 4% 안쪽 씨앗은
배경을 꽤 남긴다(**물건몫 0.654**, 다른 장은 0.09~0.37). 씨앗을 15% 안쪽으로 조이면 0.339 로
맞는데, **대조군이 그걸 막았다** — 27 합성판에서 IoU 중앙이 0.989 → 0.928 로 내려가고
최악이 0.889 → **0.225**, 0.9 미만이 1 장 → **8 장**이 된다. **기본값은 4% 로 둔다.**
그 한 장은 grabCut 이 원래 그러라고 만든 대로 **사람이 사각형을 한 번 찍어 주는 것**이 맞다.
"""
import json
import os
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260920")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260919")
import 선읽기 as LR
import 전처리 as PP
HERE, OUT = LR.HERE, LR.OUT
DST = os.path.join(HERE, "out", "누끼")
계산폭 = 1024                 # grabCut 은 여기까지만 — 원본이 더 크면 줄여 계산하고 되돌린다
닫기, 깃털 = 3, 1.2


def 누끼(rgb, alpha=None):
    """(알파 0~255, 물건몫). 알파가 있으면 그대로, 없으면 grabCut."""
    import cv2
    from scipy import ndimage
    if alpha is not None:
        return alpha, float((alpha > 127).mean())
    h, w = rgb.shape[:2]
    s = min(1.0, 계산폭 / max(h, w))
    작 = cv2.resize(rgb, (int(round(w * s)), int(round(h * s))),
                    interpolation=cv2.INTER_AREA) if s < 1.0 else rgb
    m = PP.grabcut(작)
    if not m.any():
        return np.zeros((h, w), np.uint8), 0.0
    m = ndimage.binary_closing(m, np.ones((닫기, 닫기), bool))
    big = cv2.resize(m.astype(np.uint8) * 255, (w, h), interpolation=cv2.INTER_LINEAR)
    a = cv2.GaussianBlur(big, (0, 0), 깃털)
    return a, float((a > 127).mean())


def 판들(full=False):
    import cv2
    import 원화진단 as JD
    out = []
    for key, nick, grp, pngs, _, _ in JD.집합():
        if grp != "원화":
            continue
        for v, src in pngs.items():
            im = cv2.imdecode(np.fromfile(src, np.uint8), cv2.IMREAD_UNCHANGED)
            if im.ndim == 2:
                im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
            a = im[:, :, 3] if im.shape[2] == 4 else None
            rgb = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2RGB)
            if not full:
                h, w = rgb.shape[:2]
                s = min(1.0, LR.S / max(h, w))
                if s < 1.0:
                    wh = (int(round(w * s)), int(round(h * s)))
                    rgb = cv2.resize(rgb, wh, interpolation=cv2.INTER_AREA)
                    a = cv2.resize(a, wh, interpolation=cv2.INTER_AREA) if a is not None else None
            out.append(("%s_%s" % (nick, v), rgb, a, src))
    return out


def 따기(full=False):
    from PIL import Image
    rows = {}
    for 이름, rgb, a, src in 판들(full):
        t0 = time.time()
        al, 몫 = 누끼(rgb, a)
        d = os.path.join(DST, 이름.replace("/", "_").replace("(", "").replace(")", ""))
        os.makedirs(d, exist_ok=True)
        Image.fromarray(np.dstack([rgb, al])).save(os.path.join(d, "투명.png"))
        f = al.astype(np.float32)[:, :, None] / 255.0
        흰 = (rgb.astype(np.float32) * f + 255.0 * (1 - f)).astype(np.uint8)
        Image.fromarray(흰).save(os.path.join(d, "흰바탕.png"))
        Image.fromarray(al).save(os.path.join(d, "마스크.png"))
        rows[이름] = {"알파원본": a is not None, "크기": list(rgb.shape[:2]),
                     "물건몫": round(몫, 4), "초": round(time.time() - t0, 1), "원본": src}
        print("  %-28s %-6s 물건몫 %.3f · %dx%d · %.1f초"
              % (이름[:28], "알파" if a is not None else "grabCut", 몫,
                 rgb.shape[1], rgb.shape[0], rows[이름]["초"]), flush=True)
    p = os.path.join(OUT, "누끼_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"판": "누끼 v1 · 알파 or grabCut (2026-09-21)",
               "방법근거": "배경 바퀴 27/27 · IoU 중앙 0.992", "장별": rows},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  -> %s\n  -> %s" % (DST, p))
    return rows


def 그림():
    from PIL import Image
    R = []
    for 이름, rgb, a, src in 판들(False):
        d = os.path.join(DST, 이름.replace("/", "_").replace("(", "").replace(")", ""))
        ts = [rgb]
        for n in ("마스크.png", "흰바탕.png"):
            p = os.path.join(d, n)
            if not os.path.exists(p):
                ts.append(np.full_like(rgb, 240))
                continue
            im = np.asarray(Image.open(p).convert("RGB"))
            ts.append(im)
        R.append(("%s\n%s" % (이름[:20], "알파" if a is not None else "grabCut"), ts))
    LR.DC.grid(R, ("원화 그대로", "누끼 마스크", "배경 뺀 판 (흰 바탕)"),
               "누끼 — 원화에서 캐릭터만 (알파가 있으면 알파 · 없으면 grabCut)",
               "방법은 `배경` 바퀴에서 골랐다 — 27/27 · 마스크 IoU 중앙 0.992 (모서리홍수 0.016)",
               os.path.join(HERE, "out", "누끼.png"), S=300)


def selfcheck():
    im = np.full((200, 160, 3), 128, np.uint8)
    im[50:150, 40:120] = 30
    a, 몫 = 누끼(im)
    assert 0.15 < 몫 < 0.35, 몫
    assert a[100, 80] > 200 and a[5, 5] < 60, (a[100, 80], a[5, 5])
    b = np.zeros((200, 160), np.uint8)
    b[10:20, 10:20] = 255
    a2, m2 = 누끼(im, b)
    assert (a2 == b).all(), "알파가 있으면 그대로 써야 한다"
    print("  자가검사 통과 — grabCut 물건몫 %.3f · 알파 그대로 %.4f" % (몫, m2))


if __name__ == "__main__":
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass
    a = sys.argv[1] if len(sys.argv) > 1 else "검사"
    if a == "따기":
        따기("--full" in sys.argv)
    else:
        {"검사": selfcheck, "그림": 그림}[a]()
