# -*- coding: utf-8 -*-
"""**도안을 생성해서 시작한다** — 우리 파이프라인 규격에 맞는 원화를 만든다 (2026-09-21).

    python 도안생성.py 시험            앞 판 한 장만 (규격 확인 · 제일 싼 판)
    python 도안생성.py 한벌 [이름]      앞 · 옆 · 뒤 × (색면 · 선화) = 6 장
    python 도안생성.py 검사 <png>       우리 자로 그 그림을 잰다 (생성 없이)

사용자(09-21): 「이미지 도안에서 시작을 해 보자고. 지금은 도안 이미지가 이상한 거니까」
사용자 결정: **3 면도 + 선화 · 색면 레이어** · **오리지널 메카**.

**규격은 오늘 측정에서 나왔다** (지어낸 규격이 아니다):

    배경 없음 · 지시선 없음      `declutter` 가 옆 판에서 2,436 화소를 걷어냈다
    끊기지 않는 일정 굵기 선     다리 먹선이 224 조각(>=100 화소는 14 개)이라 칸이 부서져 흠집이 났다
    평평한 색면 3~6 색          그러데이션이 있으면 `ink_map` 이 거짓 선을 만든다
    정투상 0/90/180 · 같은 키    판 불일치가 지금 못덮음의 큰 몫이다
    A 포즈 · 팔이 몸에서 떨어짐   분수령 분할이 팔을 가를 수 있다 (`면자르기`)

**열쇠는 저장소에 안 둔다** — 환경변수 `OPENAI_API_KEY`, 없으면 `~scratchpad/oai.key`.
"""
import base64
import json
import os
import sys
import time
import urllib.request

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
from scipy import ndimage

sys.path.insert(0, r"G:\art2real\원화3d")
import hull as H
W = H.W
OUT = os.path.join(H.OUT, "도안생성")
열쇠파일 = r"C:\Users\zesky\AppData\Local\Temp\claude\G--art2real\a6668565-5072-459b-9e0f-de16dc1a6c3c\scratchpad\oai.key"
모델 = "gpt-image-1"

몸통 = ("an original humanoid mecha character, hard-surface armor made of flat plates, "
        "simple silhouette, chunky forearms and boots, a small crest on the head, "
        "no weapons, arms held away from the body in a relaxed A-pose, legs slightly apart")

규격 = ("flat vector-style cel shading with only 4 solid colors (white, mid grey, dark grey, gold) "
        "and NO gradients, NO airbrush, NO soft shadows, NO highlights; "
        "clean uniform-width black panel lines that are fully closed loops; "
        "pure white background, no ground shadow, no text, no labels, no arrows, no dimension lines, "
        "no frame, no border; orthographic projection with no perspective and no foreshortening; "
        "the whole figure fits inside the frame with a small margin, centered")

판 = {"front": "seen exactly from the front (0 degrees), perfectly symmetrical",
      "side": "seen exactly from the left side (90 degrees), a pure side profile",
      "back": "seen exactly from behind (180 degrees), perfectly symmetrical"}

레이어 = {"색면": "",
          "선화": " Draw ONLY the black outlines and panel lines on a pure white background: "
                  "no fills, no colors, no shading at all — a pure line drawing."}


def 프롬프트(v, layer):
    return ("A character model sheet drawing of %s, %s. %s.%s"
            % (몸통, 판[v], 규격, 레이어[layer]))


def 열쇠():
    k = os.environ.get("OPENAI_API_KEY")
    if k:
        return k.strip()
    return open(열쇠파일, encoding="utf-8").read().strip()


def 만들기(prompt, out, size="1024x1024", quality="low"):
    """OpenAI Images API. **거부 · 에러면 과금이 없다** — 나온 그림만 돈이다."""
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps({"model": 모델, "prompt": prompt, "size": size,
                         "quality": quality, "n": 1}).encode(),
        headers={"Authorization": "Bearer %s" % 열쇠(), "Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            j = json.load(r)
    except urllib.error.HTTPError as e:
        print("  거부/에러 %s — **과금 없음**\n  %s" % (e.code, e.read().decode()[:500]))
        return None
    b = base64.b64decode(j["data"][0]["b64_json"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "wb").write(b)
    print("  %.0f 초 · %s (%d KB)" % (time.time() - t0, out, len(b) // 1024))
    return out


def 검사(png):
    """**우리 자로** 잰다 — 파이프라인이 요구하는 다섯 가지."""
    import cv2
    im = cv2.imdecode(np.fromfile(png, np.uint8), cv2.IMREAD_UNCHANGED)
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    rgb = im[:, :, :3]
    g = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)
    흰 = g > 240
    몸 = ndimage.binary_fill_holes(~흰)
    lab, n = ndimage.label(몸)
    크 = np.bincount(lab.ravel())
    크[0] = 0
    본 = 크.max() / max(크.sum(), 1)
    선 = H.ink_map(png)
    l2, n2 = ndimage.label(선, np.ones((3, 3), bool))
    s2 = np.bincount(l2.ravel())
    큰선 = int((s2[1:] >= 100).sum())
    q = (rgb // 24 * 24).reshape(-1, 3)
    색수 = len(np.unique(q, axis=0))
    안 = ndimage.binary_erosion(몸, iterations=4)
    칸, nk = ndimage.label(안 & ~ndimage.binary_dilation(선, iterations=1))
    크k = np.bincount(칸.ravel())
    쓸 = [i for i in range(1, nk + 1) if 크k[i] >= 400]
    흔 = float(np.average([g[칸 == i].std() for i in 쓸], weights=[크k[i] for i in 쓸])) if 쓸 else 0.0
    r = {"그림": os.path.basename(png), "크기": list(im.shape[:2]),
         "몸 조각 수": int((크 > 0).sum()), "제일 큰 조각 몫": round(float(본), 3),
         "배경 흰색 몫": round(float(흰.mean()), 3),
         "먹선 조각": int(n2), "100 화소 이상 선": 큰선,
         "선 조각 중 큰 것 몫": round(큰선 / max(n2, 1), 3),
         "색 수(8 단위)": int(색수), "칸 안 밝기 흔들림": round(흔, 1)}
    통과 = {"배경이 희다 (>0.35)": r["배경 흰색 몫"] > 0.35,
            "몸이 한 덩어리다 (>0.9)": r["제일 큰 조각 몫"] > 0.9,
            "선이 안 부서졌다 (큰 것 몫 >0.25)": r["선 조각 중 큰 것 몫"] > 0.25,
            "색이 적다 (<40)": r["색 수(8 단위)"] < 40,
            "색면이 평평하다 (<25)": r["칸 안 밝기 흔들림"] < 25}
    for k, v in r.items():
        print("   %-22s %s" % (k, v))
    for k, v in 통과.items():
        print("   %-28s %s" % (k, "통과" if v else "**짐**"))
    return r, 통과


def main():
    a = sys.argv[1:] or ["시험"]
    if a[0] == "검사":
        검사(a[1])
        return
    이름 = a[1] if len(a) > 1 else "메카1"
    d = os.path.join(OUT, 이름)
    if a[0] == "시험":
        o = 만들기(프롬프트("front", "색면"), os.path.join(d, "front_색면.png"))
        if o:
            print("\n  -- 우리 자로 검사 --")
            r, q = 검사(o)
            json.dump({"이름": 이름, "프롬프트": 프롬프트("front", "색면"), "검사": r,
                       "판정": {k: bool(v) for k, v in q.items()}},
                      open(os.path.join(d, "시험.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return
    if a[0] == "한벌":
        표 = []
        for v in ("front", "side", "back"):
            for L in ("색면", "선화"):
                o = 만들기(프롬프트(v, L), os.path.join(d, "%s_%s.png" % (v, L)), quality="medium")
                if o:
                    r, q = 검사(o)
                    표.append({"판": v, "레이어": L, "검사": r, "판정": {k: bool(x) for k, x in q.items()}})
        json.dump({"이름": 이름, "표": 표}, open(os.path.join(d, "한벌.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("  -> %s" % d)


if __name__ == "__main__":
    main()
