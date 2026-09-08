# -*- coding: utf-8 -*-
"""실루엣 겹침을 한 장으로. 초록=맞음 / 빨강=원화에 있는데 메시가 없음 / 파랑=삐져나감."""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", n)
S, PAD, TOP, BG = 320, 14, 46, (24, 24, 28)

ART = np.load(os.path.join(OUT, "sil_art.npy"))
rows = json.load(open(os.path.join(OUT, "sil_rows.json"), encoding="utf-8"))
ms = {r["key"]: np.load(os.path.join(OUT, "sil_%s.npy" % r["key"])) for r in rows}

u = ART.copy()
for m in ms.values():
    u |= m
ys, xs = np.where(u)
y0, y1 = max(ys.min()-14, 0), min(ys.max()+14, ART.shape[0])
x0, x1 = max(xs.min()-14, 0), min(xs.max()+14, ART.shape[1])
n = max(y1-y0, x1-x0)

sh = Image.new("RGB", (1024, 1024), BG)
dr = ImageDraw.Draw(sh)
dr.text((PAD, 12), "정면 실루엣 대조   ·   초록 맞음 / 빨강 원화에 있는데 메시가 없음 / 파랑 원화 밖으로 삐져나감",
        font=F(17), fill=(235, 235, 240))
for i, r in enumerate(rows):
    m = ms[r["key"]]
    img = np.zeros((ART.shape[0], ART.shape[1], 3), np.uint8)
    img[...] = 30
    img[ART & ~m] = (215, 70, 70)
    img[m & ~ART] = (70, 120, 235)
    img[ART & m] = (95, 200, 120)
    im = Image.fromarray(img[y0:y0+n, x0:x0+n]).resize((S, S), Image.NEAREST)
    x = PAD + i*(S+PAD)
    sh.paste(im, (x, TOP))
    dr.rectangle([x, TOP, x+S-1, TOP+S-1], outline=(70, 70, 80))
    dr.text((x, TOP+S+6), r["tag"], font=F(16), fill=(250, 250, 255))
    dr.text((x, TOP+S+28), "IoU %.3f · 덮음 %.0f%% · 삐져나감 %.0f%%"
            % (r["iou"], r["cover"]*100, r["spill"]*100), font=F(14), fill=(170, 170, 180))

ty = TOP + S + 66
for line in ["같은 자로 잰 것이다 — 원화 실측 판(lav+gold) 합집합 9,054px 대 메시 정면 투영.",
             "",
             "생성 71,842면 -> 리토폴로지 723 쿼드 : IoU 0.638 -> 0.642.  **형태는 안 망가졌다.**",
             "면을 100배 줄였는데 실루엣이 그대로다. 오늘 한 일이 형태를 깎은 게 아니다.",
             "",
             "손으로 지은 286면이 0.713 으로 여전히 앞선다 (LESSONS 119 의 0.906 은 다른 자로 잰 값).",
             "생성 메시는 원화의 21.5% 를 아예 못 덮고 자기 화소의 22.1% 는 원화 밖이다 —",
             "빨강이 뿔 자리에, 파랑이 아래 테두리에 몰려 있는 게 그것이다.",
             "",
             "UV 는 오늘 풀렸다 (섬 921 -> 98, 순도 100%, 직접 89.0%). 남은 건 형태 하나다."]:
    dr.text((PAD, ty), line, font=F(15), fill=(180, 180, 190)); ty += 22

p = os.path.join(OUT, "sil_sheet.png")
sh.save(p)
print(p, sh.size, os.path.getsize(p), "bytes")
