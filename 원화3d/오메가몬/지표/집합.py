# -*- coding: utf-8 -*-
"""닮음 지표 — 얼린 집합 (2026-09-29). 기준 = 02 극장판, 대조군 = FRA 키트(높아야) · RX-78(낮아야), 시험 대상 = 4 · 5 · 6 판 · 도안 2 판.
    python 집합.py -> out/오메가몬2/지표/집합/<이름>_<정면|옆>.png  (머리 높이 100 단위 = 400 px · 캔버스 500×600 · 꼭대기 y 100 · 가운데 x 250 · 옆은 앞 = 왼쪽 · 눈 중심 x 250)
머리 틀(꼭대기 py · 턱 py · 가운데 x 또는 눈 x · 앞이 오른쪽이면 거울)은 격자 그림(_g_*.png · _격자/)에서 손으로 읽었다.
사용자 판정 순서(기대): FRA > 4 판 > 5 판 ≈ 6 판 > RX-78. 지표는 이 순서를 내야 채택.
"""
import os
from PIL import Image, ImageOps
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); OUT = os.path.join(R, "out", "오메가몬2", "지표")
J = os.path.join
장면 = J(R, "out", "번역", "디지몬", "장면", "02_역습"); 키트 = J(R, "out", "키트"); G = J(R, "out", "오메가몬2")
# 이름: {보기: (파일, 꼭대기 py, 턱 py, 가운데 x(정면) / 눈 x(옆), 거울)}
집합 = {
    "02":    {"정면": (J(장면, "yt_172.0_얼굴_정면.jpg"), 197, 492, 885, False), "옆": (J(장면, "yt_235.0_머리_옆.jpg"), 40, 300, 630, False)},
    "FRA":   {"정면": (J(키트, "FRA_오메가몬", "추가", "mh_12.jpg"), 232, 425, 222, False), "옆": (J(키트, "FRA_오메가몬", "추가", "mh_13.jpg"), 170, 360, 178, False)},
    "RX78":  {"정면": (J(OUT, "_rx78_head.png"), 40, 155, 105, False)},
    "4판":   {"정면": (J(OUT, "판4", "머리", "_그림", "4_정면.png"), 326, 712, 280, False), "옆": (J(OUT, "판4", "머리", "_그림", "4_옆.png"), 326, 712, 455, True)},
    "5판":   {"정면": (J(OUT, "판5", "머리", "_그림", "4_정면.png"), 326, 712, 280, False), "옆": (J(OUT, "판5", "머리", "_그림", "4_옆.png"), 326, 712, 400, True)},
    "6판":   {"정면": (J(G, "머리", "_그림", "4_정면.png"), 326, 712, 280, False), "옆": (J(G, "머리", "_그림", "4_옆.png"), 326, 712, 405, True)},
    "도안":  {"정면": (J(G, "머리_도안.png"), 560, 1060, 280, False), "옆": (J(G, "머리_도안.png"), 560, 1060, 830, False)},
}
순서기대 = ["FRA", "4판", "5판", "6판", "RX78"]      # 5 ≈ 6 은 순서 안 따짐
W, H, TOP, CX, U = 500, 600, 100, 250, 4.0            # 1 단위 = 4 px

def 정규화(파일, top, chin, cx, 거울):
    im = Image.open(파일).convert("RGB"); k = 400.0 / (chin - top)
    if 거울: im = ImageOps.mirror(im); cx = im.width - cx
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    x0, y0 = int(cx * k - CX), int(top * k - TOP)
    C = Image.new("RGB", (W, H), (200, 200, 200)); C.paste(im, (-x0, -y0)); return C
def 단위(px, py, top, chin, cx, 거울=False, 폭=None):
    """원본 px → 머리 단위 (dx 바깥 +, y 아래 +). 거울이면 dx 부호 반전(옆에서 앞 = +z 로 두려고)."""
    k = 100.0 / (chin - top); dx = (px - cx) * k; return ((-dx if 거울 else dx), (py - top) * k)
def 경로(이름, 보기): return J(OUT, "집합", "%s_%s.png" % (이름, 보기))

if __name__ == "__main__":
    os.makedirs(J(OUT, "집합"), exist_ok=True)
    for 이름, 보기들 in 집합.items():
        for 보기, (f, top, chin, cx, 거울) in 보기들.items(): 정규화(f, top, chin, cx, 거울).save(경로(이름, 보기))
    # 한눈에: 정면 줄 · 옆 줄
    names = list(집합); S = Image.new("RGB", (len(names) * W // 2, H), (245, 245, 243))
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(S); ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 22)
    for i, n in enumerate(names):
        for r, 보기 in enumerate(("정면", "옆")):
            if 보기 in 집합[n]:
                a = Image.open(경로(n, 보기)).resize((W // 2, H // 2)); S.paste(a, (i * W // 2, r * H // 2)); d.text((i * W // 2 + 6, r * H // 2 + 4), n + " " + 보기, font=ft, fill=(20, 20, 20))
    S.save(J(OUT, "집합.png")); print("집합", J(OUT, "집합.png"))
