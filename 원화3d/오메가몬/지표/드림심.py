# -*- coding: utf-8 -*-
"""지표 3 — DreamSim (NeurIPS 2023 · 사람 삼중 판정으로 학습한 중간 수준 유사도). 거리 낮을수록 닮음. 선화 · 셀 렌더 검증은 없음 → 대조군 순서로 채택 여부.
    pip install dreamsim ; python 드림심.py -> 표 + out/오메가몬2/지표/드림심.json
"""
import os, json, torch
from PIL import Image
from 집합 import 집합, 경로, OUT, 순서기대
from dreamsim import dreamsim
dev = "cuda" if torch.cuda.is_available() else "cpu"; model, pre = dreamsim(pretrained=True, device=dev)
def 거리(a, b):
    with torch.no_grad(): return float(model(pre(Image.open(a).convert("RGB")).to(dev), pre(Image.open(b).convert("RGB")).to(dev)))
if __name__ == "__main__":
    결과 = {n: {보기: round(거리(경로("02", 보기), 경로(n, 보기)), 4) for 보기 in 집합[n] if 보기 in 집합["02"]} for n in 집합 if n != "02"}
    for n, r in sorted(결과.items(), key=lambda kv: kv[1]["정면"]): print("%-5s 정면 %.3f  옆 %s" % (n, r["정면"], r.get("옆", "-")))
    순 = [n for n in sorted(결과, key=lambda n: 결과[n]["정면"]) if n in 순서기대]; print("순서", " > ".join(순), "| 기대", " > ".join(순서기대))
    json.dump(결과, open(os.path.join(OUT, "드림심.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
