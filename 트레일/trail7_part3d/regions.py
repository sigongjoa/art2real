# -*- coding: utf-8 -*-
"""전신 원화를 부위 상자로 나눈다. 상자는 원화 alpha bbox 의 **비율**로 적는다.

    venv/Scripts/python.exe regions.py          # 상자 증명 그림 + 부위별 크롭

왜 나누나: 전신 1회로는 머리가 안 나온다. 머리는 전신 높이의 8% 라 1024 토큰에서
자리를 못 받는다. 토큰을 늘리는 길은 8GB 에서 막히니(전신 8파트가 5.69GB)
**대상을 키운다** — 부위마다 1024² 를 통째로 준다.

상자 값은 노브다. 가로화소 프로파일에서 읽은 것이고 실측이 아니다:
  0.15~0.20 어깨(342~357) · 0.35~0.50 최대폭(479~494, 방패·캐논) · 0.55~0.80 다리(157~248)
"""
import os
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "in", "omega_front_clean.png")

# (이름, x0, x1, y0, y1) — 몸통 bbox 대비 비율. 이음매가 벌어지지 않게 조금씩 겹친다.
REGIONS = [
    # face 는 plan_crops.py 가 "4.3칸" 이라고 계산한 상자다 — 눈·입이 기하로 나온다.
    # head(2.4칸)로는 매끈한 쐐기밖에 안 나왔다. 둘의 차이가 이 한 줄이다.
    ("face",  0.467, 0.606, 0.081, 0.168),
    ("head",  0.34, 0.66, 0.00, 0.17),
    ("torso", 0.28, 0.72, 0.11, 0.45),
    ("armL",  0.00, 0.36, 0.08, 0.95),   # 화면 왼쪽 — 방패 + 그레이소드(칼끝까지)
    ("armR",  0.64, 1.00, 0.08, 0.64),   # 화면 오른쪽 — 가루루캐논
    ("legs",  0.22, 0.80, 0.42, 1.00),
]


def body_box(m):
    ys, xs = np.where(m)
    return xs.min(), xs.max(), ys.min(), ys.max()


def main():
    a = np.array(Image.open(SRC))
    m = a[..., 3] > 0
    X0, X1, Y0, Y1 = body_box(m)
    W, H = X1 - X0 + 1, Y1 - Y0 + 1
    print("몸통 bbox x %d..%d  y %d..%d" % (X0, X1, Y0, Y1))

    proof = Image.fromarray(a).convert("RGB")
    d = ImageDraw.Draw(proof)
    cols = [(220, 60, 60), (60, 160, 220), (60, 190, 90), (230, 150, 40), (170, 90, 210)]

    for (name, fx0, fx1, fy0, fy1), c in zip(REGIONS, cols):
        x0, x1 = int(X0 + fx0*W), int(X0 + fx1*W)
        y0, y1 = int(Y0 + fy0*H), int(Y0 + fy1*H)
        d.rectangle([x0, y0, x1, y1], outline=c, width=5)
        d.text((x0+8, y0+8), name, fill=c)

        # 그 상자 안의 알파만 남겨 1024² 로. 다른 부위가 안 섞인다.
        sub = a.copy()
        keep = np.zeros_like(m)
        keep[y0:y1+1, x0:x1+1] = m[y0:y1+1, x0:x1+1]
        sub[~keep] = 0
        box = Image.fromarray(sub).crop((x0, y0, x1+1, y1+1))
        side = max(box.size)
        pad = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        pad.paste(box, ((side-box.width)//2, (side-box.height)//2))
        pad.resize((1024, 1024), Image.LANCZOS).save(os.path.join(HERE, "in", "omega_%s.png" % name))
        print("  %-6s x %4d..%4d  y %4d..%4d  화소 %6d" % (name, x0, x1, y0, y1, int(keep.sum())))

    proof.save(os.path.join(HERE, "out", "regions_proof.png"))
    print("증명 out/regions_proof.png")


if __name__ == "__main__":
    main()
