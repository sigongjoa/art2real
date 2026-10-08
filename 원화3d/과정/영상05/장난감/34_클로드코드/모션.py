# -*- coding: utf-8 -*-
"""34 모션 그래픽(스킬 making-toy-cg-shorts 10-04 규격) — 블렌더 스틸 위에 2D: 점수판(위) · 이름표(점 → 선 → 알약) · 큰 글자 팝(y≈430) · 고리 펄스 · 자막(y≈1270).
앵커.json = 컷마다 3D 점의 화면 좌표(장면.py 가 기록). 지금은 스틸 시안 — 굽기 때는 프레임마다 같은 함수로."""
import json, glob, os
from PIL import Image, ImageDraw, ImageFont
D = "G:/art2real/out/영상05/장난감/34_클로드코드/frames/"; W, H = 1080, 1920
BH = lambda n: ImageFont.truetype("C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/259f23f2-edc9-4277-85f4-fd324dc7cd8f/scratchpad/BlackHanSans.ttf", n)
KR = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
Y, G, R, WH = (255, 226, 60), (60, 220, 120), (255, 80, 80), (255, 255, 255)
LINES = [l.split("\t")[1] for l in open("G:/art2real/원화3d/과정/영상05/장난감/34_클로드코드/대본.tsv", encoding="utf-8").read().strip().split("\n")[1:]]
SCORE = [("AI", "0/10", R), ("Claude", "?/10", WH), ("Claude", "1/10", G), ("Claude", "3/10", G), ("Claude", "3/10", G), ("채점기", "9/10", G), ("내 눈", "7/10", R), ("Claude", "7/10", Y)]
LAB = {0: [("줄부품", "피규어 부품", WH)], 1: [("모니터", "설계도 = 만드는 순서", Y), ("허리", "설계도대로 만든 부품", WH)],
       2: [("공막대사람", "사람이 만든 것", Y), ("공막대클로드", "Claude 설계도", (130, 200, 255))], 3: [("허리", "구멍까지 그대로", G)],
       4: [("엉덩이사람", "관절 공", G), ("엉덩이클로드", "사라짐!", R)], 5: [("채점기", "합격 9개", G)], 6: [("내눈", "진짜 7개", R)], 7: []}
BIG = {0: ("0개 맞힘", R), 2: ("똑같다!", G), 4: ("사라졌다", R), 6: ("채점기가 속았다", Y), 7: ("왜 못 배웠을까?", Y)}
PULSE = {2: "공막대클로드", 6: "내눈"}

def pill(d, x, y, s, col, size=56):
    f = KR(size); w = d.textlength(s, font=f); d.rounded_rectangle((x - 24, y - size * 0.75, x + w + 24, y + size * 0.75), 22, fill=(0, 0, 0, 215), outline=col, width=5); d.text((x, y), s, font=f, fill=col, anchor="lm"); return w
def label(d, p, s, col, side, i=0):
    x, y = p[0] * W, p[1] * H; d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=col, outline=(0, 0, 0), width=4)
    lx, ly = (x + 150 * side, y - 170 - 130 * i)   # 둘째 이름표는 한 칸 위 — 겹침 방지; d.line((x, y, lx, ly), fill=col, width=7)
    f = KR(60); w = d.textlength(s, font=f); x0 = lx if side > 0 else lx - w - 48
    x0 = min(max(x0, 30), W - w - 78); pill(d, x0 + 24, ly, s, col, 60)
def big(d, s, col):
    f = BH(150); d.text((W // 2, 430), s, font=f, fill=col, anchor="mm", stroke_width=12, stroke_fill=(0, 0, 0))
def pulse(d, p):
    x, y = p[0] * W, p[1] * H
    for r, a in ((120, 255), (200, 170), (290, 90)): d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 226, 60, a), width=10)
def caption(d, s):
    f = KR(64); ph = s.split(",")[0].split(".")[0][:18]
    d.text((W // 2, 1270), ph, font=f, fill=WH, anchor="mm", stroke_width=8, stroke_fill=(0, 0, 0))
def board(d, k):
    who, sc, col = SCORE[k]; d.rounded_rectangle((W // 2 - 300, 110, W // 2 + 300, 250), 30, fill=(0, 0, 0, 220), outline=col, width=6)
    d.text((W // 2 - 40, 180), who, font=BH(70), fill=WH, anchor="rm"); d.text((W // 2 + 10, 180), sc, font=BH(96), fill=col, anchor="lm")
    d.rectangle((0, 0, W, 16), fill=(70, 70, 70)); d.rectangle((0, 0, int(W * (k + 1) / 8), 16), fill=Y)

A = json.load(open(D + "앵커.json", encoding="utf-8")); outs = []
for a in A:
    im = Image.open(D + "still_%02d.png" % a["컷"]).convert("RGBA"); ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov); k = a["줄"]
    if k in PULSE and a["점"][PULSE[k]][2]: pulse(d, a["점"][PULSE[k]])
    for i, (nm, s, col) in enumerate(LAB.get(k, [])):
        if a["점"][nm][2]: label(d, a["점"][nm], s, col, -1 if (i == 0 and len(LAB[k]) > 1) or a["점"][nm][0] > 0.6 else 1, i)
    if k in BIG: big(d, *BIG[k])
    board(d, k); caption(d, LINES[k])
    out = Image.alpha_composite(im, ov).convert("RGB"); out.save(D + "mg_%02d.png" % a["컷"]); outs.append(out)
s = Image.new("RGB", (432 * 7, 768 * 2))
for i, o in enumerate(outs[:14]): s.paste(o.resize((432, 768)), ((i % 7) * 432, (i // 7) * 768))
s.save("G:/art2real/out/영상05/장난감/34_클로드코드/_모션시트.jpg"); print(len(outs))
