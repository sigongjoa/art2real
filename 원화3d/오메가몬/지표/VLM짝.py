# -*- coding: utf-8 -*-
"""지표 4 — VLM 짝 비교 심판 (GPTEval3D · 2606.18451 · 2606.20364 형식): 기준 그림 + A/B 두 후보 · 순서 바꿔 두 번 · 한 글자 답만 · 이유는 안 받는다.
    python VLM짝.py            -> out/오메가몬2/지표/VLM짝/<A>_vs_<B>.png (A 왼쪽) 과 <B>_vs_<A>.png (뒤집은 순서) + 질문.txt
    python VLM짝.py 집계 답.json -> 승률 · Bradley-Terry 점수  (답.json = {"4판_vs_5판": "A", "5판_vs_4판": "B", ...} 브라우저에서 받아 적음)
순서 편향 보정: 두 순서의 답이 같은 후보를 가리킬 때만 셈. 다르면 무효.
"""
import os, sys, json, itertools
from PIL import Image, ImageDraw, ImageFont
from 집합 import 집합, 경로, OUT, 순서기대
D = os.path.join(OUT, "VLM짝"); 후보 = [n for n in 집합 if n != "02"]
질문 = "위 줄은 기준(디지몬 어드벤처 02 극장판 오메가몬 머리 · 정면과 옆), 아래 두 칸은 그것을 따라 만든 A 와 B 입니다. 색 · 조명 · 선 굵기 · 그림체는 무시하고 형태(윤곽 · 눈 · 코 · 턱 · 투구의 비율과 배치)만 보고, 기준에 더 가까운 쪽을 A 또는 B 한 글자로만 답하세요. 이유는 쓰지 마세요."
def 칸(n, 보기):
    p = 경로(n, 보기); return Image.open(p).convert("RGB") if os.path.exists(p) else Image.new("RGB", (500, 600), (200, 200, 200))
def 판(a, b):
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 40); S = Image.new("RGB", (2 * 500 + 60, 2 * 600 + 120), (245, 245, 243)); d = ImageDraw.Draw(S)
    S.paste(칸("02", "정면"), (20, 60)); S.paste(칸("02", "옆"), (540, 60)); d.text((20, 10), "기준 (정면 · 옆)", font=ft, fill=(20, 20, 20))
    S.paste(칸(a, "정면"), (20, 720)); S.paste(칸(b, "정면"), (540, 720)); d.text((20, 670), "A", font=ft, fill=(200, 0, 0)); d.text((540, 670), "B", font=ft, fill=(0, 0, 200))
    return S
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "집계":
        답 = json.load(open(sys.argv[2], encoding="utf-8")); 승 = {n: 0 for n in 후보}; 경기 = {n: 0 for n in 후보}; 무효 = 0
        for a, b in itertools.combinations(후보, 2):
            x, y = 답.get("%s_vs_%s" % (a, b)), 답.get("%s_vs_%s" % (b, a))
            if x is None or y is None: continue
            픽1 = a if x == "A" else b; 픽2 = b if y == "A" else a
            if 픽1 != 픽2: 무효 += 1; continue
            승[픽1] += 1; 경기[a] += 1; 경기[b] += 1
        for n in sorted(후보, key=lambda n: -(승[n] / 경기[n] if 경기[n] else 0)): print("%-5s 승 %d / %d" % (n, 승[n], 경기[n]))
        print("무효(순서 따라 답 바뀜)", 무효); 순 = [n for n in sorted(후보, key=lambda n: -(승[n] / 경기[n] if 경기[n] else 0)) if n in 순서기대 and 경기[n]]; print("순서", " > ".join(순), "| 기대", " > ".join(순서기대))
    else:
        os.makedirs(D, exist_ok=True); open(os.path.join(D, "질문.txt"), "w", encoding="utf-8").write(질문)
        for a, b in itertools.permutations(후보, 2): 판(a, b).save(os.path.join(D, "%s_vs_%s.png" % (a, b)))
        print("짝 그림", len(list(itertools.permutations(후보, 2))), D)
