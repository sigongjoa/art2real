# -*- coding: utf-8 -*-
"""**도해적인가 회화적인가** — 원화가 얼마나 「뽑히는 그림」인지 잰다 (2026-09-21).

    python 도해도.py 검사
    python 도해도.py 재기     -> out/기록/도해도_<때>.json  (표 출력)
    python 도해도.py 그림     -> out/도해도.png

사용자(09-21): 「오메가몬은 **출력 가능한 상태**로 만들어서 그런 건가? 원화는 **그림적인 장치**가
있어서 우리가 원하는 선과 같은 데이터를 얻기가 어려운 거고?」

가설을 숫자로 바꾼다. 네 칸을 잰다 — **평탄 몫**(그라데이션이 아니라 판판한 칠인가) ·
**색 수**(셀 팔레트인가) · **선 몫**(사람이 그은 검은 선이 있나) · **재구성 오차**(판마다 평균색으로
메우고 뺀 값. **스킬 자신의 문턱이 5/255 다** — 그 위면 「분할이 음영과 안 맞는다」).

**문턱은 우리 것이 아니라 빌린 것이다** — `도안/도구/` 의 `report.py` 가 쓰는 5/255.
그래서 이 바퀴는 새 문턱을 만들지 않는다. **재는 것뿐이다.**
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
S = LR.S
스킬문턱 = 5.0                 # report.py 의 「재구성 오차 < 5/255 면 분할이 음영과 일치」
평탄문턱 = 2.0                 # |기울기| 가 이보다 작으면 판판한 칠
벤치장 = PP.벤치장


def 잰다(rgb, 물):
    """네 칸. 전부 **물건 화소 안에서만** 잰다."""
    g = rgb.astype(np.float32).mean(2)
    gy, gx = np.gradient(g)
    mag = np.hypot(gx, gy)
    안 = 물 & np.pad(물, 1, mode="edge")[1:-1, 1:-1]
    q = (rgb[물] // 8).astype(np.int32)
    색 = len(np.unique(q[:, 0] * 1024 + q[:, 1] * 32 + q[:, 2]))
    return {"평탄몫": round(float((mag[안] < 평탄문턱).mean()), 4),
            "색수(8단위)": int(색),
            "선몫": round(float((g[물] < PP.선문턱).mean()), 4),
            "물건몫": round(float(물.mean()), 4)}


def 원화들():
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
            h, w = rgb.shape[:2]
            s = S / max(h, w)
            rgb = cv2.resize(rgb, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA)
            a = cv2.resize(a, rgb.shape[1::-1], interpolation=cv2.INTER_AREA) if a is not None else None
            물 = PP.배경마스크(rgb, a)
            out.append(("%s/%s" % (nick, v), "원화", rgb, 물, key, v))
    return out


def 벤치들():
    import trimesh
    out = []
    for c in 벤치장:
        t = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        cel, 있 = LR.명암판(t, 45, 45)
        out.append((c, "우리 명암판", cel, 있, c, "위45"))
    return out


def 재구성(key, v, 무리):
    """이미 돌려 둔 추출기 출력에서 재구성 오차를 되읽는다 (새로 안 돌린다)."""
    if 무리 == "원화":
        p = os.path.join(PP.DST, "원화_" + key, v, "전", "art3d.json")
    else:
        p = os.path.join(PP.DST, key, "원본", "art3d.json")
        if not os.path.exists(p):
            p = os.path.join(LR.EXT, key, v, "art3d.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8")).get("metrics", {}).get("recon_error")


def 재기():
    rows = []
    for 이름, 무리, rgb, 물, key, v in 원화들() + 벤치들():
        r = {"장": 이름, "무리": 무리, **잰다(rgb, 물), "재구성오차": 재구성(key, v, 무리)}
        r["스킬문턱통과"] = None if r["재구성오차"] is None else bool(r["재구성오차"] < 스킬문턱)
        rows.append(r)
    o = {"판": "도해도 v1 · 평탄몫 · 색수 · 선몫 · 재구성오차 (2026-09-21)",
         "때": time.strftime("%Y%m%d_%H%M"), "빌린문턱": "재구성오차 < %g/255 (도구/report.py)" % 스킬문턱,
         "장별": rows}
    p = os.path.join(OUT, "도해도_%s.json" % o["때"])
    json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  %-26s %-10s %8s %8s %8s %10s %s" % ("장", "무리", "평탄몫", "색수", "선몫", "재구성오차", "스킬문턱"))
    for r in rows:
        print("  %-26s %-10s %8.3f %8d %8.3f %10s %s"
              % (r["장"][:26], r["무리"], r["평탄몫"], r["색수(8단위)"], r["선몫"],
                 "%.2f" % r["재구성오차"] if r["재구성오차"] is not None else "-",
                 "통과" if r["스킬문턱통과"] else ("짐" if r["스킬문턱통과"] is False else "-")))
    print("\n  ->", p)
    return o


def 그림():
    import glob
    from PIL import Image
    p = sorted(glob.glob(os.path.join(OUT, "도해도_*.json")))[-1]
    rows = json.load(open(p, encoding="utf-8"))["장별"]
    R, ts = [], []
    데 = {r["장"]: r for r in rows}
    for 이름, 무리, rgb, 물, key, v in 원화들() + 벤치들():
        r = 데[이름]
        ts.append((이름, 무리, rgb, r))
    from PIL import ImageDraw as _D
    from 계획 import _font
    칸 = []
    for n, g, im, r in ts:
        pil = Image.fromarray(im).resize((260, 260))
        d = _D.Draw(pil)
        d.rectangle([0, 222, 260, 260], fill=(255, 255, 255))
        d.text((4, 224), n[:30], fill=(20, 20, 20), font=_font(12))
        d.text((4, 240), "평탄 %.2f · 색 %d · 선 %.2f · 재구성 %s" %
               (r["평탄몫"], r["색수(8단위)"], r["선몫"],
                "%.1f" % r["재구성오차"] if r["재구성오차"] is not None else "-"),
               fill=(200, 30, 30) if r["스킬문턱통과"] is False else (60, 60, 60), font=_font(11))
        칸.append((g, np.asarray(pil)))
    K = 4
    for i in range(0, len(칸), K):
        덩 = 칸[i:i + K]
        R.append((덩[0][0], [x[1] for x in 덩] + [np.full((260, 260, 3), 247, np.uint8)] * (K - len(덩))))
    LR.DC.grid(R, ("", "", "", ""),
               "도해도 — 「뽑히는 그림」인가 (평탄 몫 · 색 수 · 선 몫 · 재구성 오차)",
               "재구성 오차는 스킬 자신의 문턱이 5/255 다 — 그 위면 분할이 음영과 안 맞는다",
               os.path.join(HERE, "out", "도해도.png"), S=260)


def selfcheck():
    a = np.full((64, 64, 3), 200, np.uint8)          # 완전 평탄
    물 = np.ones((64, 64), bool)
    r = 잰다(a, 물)
    assert r["평탄몫"] == 1.0 and r["색수(8단위)"] == 1, r
    b = np.tile(np.linspace(0, 255, 64, dtype=np.uint8)[None, :, None], (64, 1, 3))   # 그라데이션
    r2 = 잰다(b, 물)
    assert r2["평탄몫"] < 0.2 and r2["색수(8단위)"] > 20, r2
    print("  자가검사 통과 — 평탄 %.2f/%.2f · 색 %d/%d" %
          (r["평탄몫"], r2["평탄몫"], r["색수(8단위)"], r2["색수(8단위)"]))


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "재기"
    {"검사": selfcheck, "재기": 재기, "그림": 그림}[a]()
