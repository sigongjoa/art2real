#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""**정면에서 눕힌 무기 판을 뽑는다.** 재려면 원근이 없어야 한다.

    D:\\imggen\\venv\\Scripts\\python.exe 무기판.py

## 왜 다시 뽑나

`r5_up_hero` 로 잰 프로필 11종이 검도 창도 아닌 **병 모양**이었다.
그 판은 **검이 카메라로 쏟아지는 극단적 원근**이라, 카메라를 향한 날은
화면에서 짧고 뚱뚱하게 찍힌다. 세장비 1.0~9.9 는 무기의 성질이 아니라
**그 무기가 카메라를 얼마나 향했나**를 잰 값이었다.

`LESSONS`(원근 컷에서 길이 쓰지 않기) 에 적혀 있던 그 실수다 —
깊이를 모르면 화면 길이는 실제 길이가 아니다.

## 그래서 판을 셋으로 나눈다

한 프롬프트에 다 넣으면 리본이 된다는 교훈(`blades/README`)대로 **한 덩어리씩** 시킨다.

    앞모습   나란히 눕힌 무기들. 종류가 갈리게 (검·창·도끼·둔기·단검)
    옆모습   **단면을 재려고.** 같은 무기를 옆에서
    자루     손잡이·가드·자루끝만 크게

`side` 판이 핵심이다 — 지금 두께 0.22 와 마름모 단면이 둘 다 `guessed` 인데
옆모습이 있으면 둘 다 `measured` 가 된다.
"""
import os
import sys

sys.path.insert(0, r"D:\tracks\_공용")

from tracks.imggen import pipeline as P                      # noqa: E402

MODEL = r"D:\imggen\models\animagine-xl-4.0-opt.safetensors"
HF = r"D:\imggen\hf"
OUT = r"D:\imggen\weapons"

# **원근을 없앤다.** flat / orthographic / straight-on 을 반복해서 박는다
STYLE = ("anime weapon reference sheet, cel shading, bold black outlines, flat colors, "
         "golden yellow weapons on plain deep indigo background, "
         "orthographic straight-on view, no perspective, laid out flat, evenly spaced")
NEG = (P.NEG + P.NEG_EMPTY + ", perspective, foreshortening, tilted, angle, depth, "
       "3d render, background scenery, hands, ribbon, cloth")

PLATES = [
    ("w_front", "a row of eight different golden weapons standing upright side by side, "
                "broad sword, thin rapier, long spear, war axe, heavy mace, dagger, "
                "halberd, curved sabre, full length, tips up"),
    ("w_side", "the same eight golden weapons seen edge-on from the side, "
               "showing how thin each blade is, thin profiles, upright, side by side"),
    ("w_hilt", "close up of eight different golden weapon hilts and guards, "
               "crossguard, ring guard, pommel, wrapped grip, side by side"),
]

PANELS = [(n, None, STYLE + ", " + b, P.TALL, 701 + i)
          for i, (n, b) in enumerate(PLATES)]


def main():
    os.makedirs(OUT, exist_ok=True)
    pipe = P.load_pipe(MODEL, hf_home=HF, ip=False)
    P.generate(pipe, PANELS, OUT, neg=NEG, steps=32, cfg=6.5)
    print("WEAPON_SHEETS " + OUT)


if __name__ == "__main__":
    main()
