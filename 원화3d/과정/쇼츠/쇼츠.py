# -*- coding: utf-8 -*-
"""쇼츠 — <편>.tsv 한 장으로 세로 1080×1920 영상을 굽는다 (템플릿.md 의 다섯 구간).
    python 쇼츠.py 머리_시험.tsv [부위=머리]  -> out/오메가몬2/과정/쇼츠/<편>.mp4 · <편>_0초.png(썸네일 = 0초 프레임)
그림 종류: 훅:NN (원화 | NN 단계 모델) · 카드 (자료) · 단계:NN (모델 3/4 크게 + 원화 모서리 + 기록.md 자막) · 비교:NN (세 시점 원화 | 모델) · 판정."""
import os, sys, csv, json, re, subprocess, shutil
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
편 = sys.argv[1]; 부위 = sys.argv[2] if len(sys.argv) > 2 else "머리"; H_ = os.path.dirname(os.path.abspath(__file__))
O = r"G:\art2real\원화3d\out\오메가몬2\과정"; F = os.path.join(O, 부위, "프레임"); 출 = os.path.join(O, "쇼츠"); os.makedirs(출, exist_ok=True)
기록 = json.load(open(r"G:\art2real\원화3d\out\오메가몬2\자료\자료.json", encoding="utf-8"))
단계자막 = {int(m.group(1)): (m.group(2).strip(), m.group(3).strip()) for m in re.finditer(r"^\| (\d\d) \| (.*?) \| (.*?) \|$", open(os.path.join(O, 부위, "기록.md"), encoding="utf-8").read(), re.M)}
W, H, FPS = 1080, 1920, 30; 굵 = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); 얇 = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", n)
배경 = (24, 26, 32); 강조 = (255, 214, 64)
def 원화(t): x0, y0, x1, y1 = 기록[t]["상자"]; im = cv2.imdecode(np.fromfile(기록[t]["파일"], np.uint8), cv2.IMREAD_COLOR)[y0:y1, x0:x1]; return Image.fromarray(im[:, :, ::-1])
def 모델(n, t="02_3-4"): x0, y0, x1, y1 = 기록[t]["상자"]; return Image.open(os.path.join(F, "%02d_%s.png" % (n, t))).convert("RGB").crop((x0, y0, x1, y1))
def 맞춤(im, w, h): im = im.copy(); im.thumbnail((w, h)); return im
def 감싸(d, s, f, 폭=W - 120):
    out = []
    for 문단 in s.replace("\\n", "\n").split("\n"):
        줄 = ""
        for 낱 in 문단.split(" "):
            t = (줄 + " " + 낱).strip()
            if d.textlength(t, font=f) > 폭 and 줄: out.append(줄); 줄 = 낱
            else: 줄 = t
        out.append(줄)
    return out
def 글(d, xy, s, f, fill=(240, 240, 240), 가운데=True, 줄간=1.25):
    y = xy[1]
    s = s.replace("−", "-").replace("~", "~")                                                              # 맑은 고딕에 없는 글자
    for 줄 in 감싸(d, s, f):
        tw = d.textlength(줄, font=f); d.text(((W - tw) / 2 if 가운데 else xy[0], y), 줄, font=f, fill=fill, stroke_width=3, stroke_fill=(0, 0, 0)); y += int(f.size * 줄간)
    return y
def 판(종류, 큰, 작):
    c = Image.new("RGB", (W, H), 배경); d = ImageDraw.Draw(c); k, _, n = 종류.partition(":"); n = int(n) if n else 0
    if k == "훅":
        a, b = 맞춤(원화("02_3-4"), 520, 900), 맞춤(모델(n), 520, 900); c.paste(a, (20, 420)); c.paste(b, (W - 20 - b.width, 420))
        글(d, (0, 150), 큰, 굵(78), 강조); 글(d, (0, 1400), 작, 굵(60)); d.text((40, 380), "원화", font=굵(40), fill=(200, 200, 200)); d.text((W - 200, 380), "모델", font=굵(40), fill=(200, 200, 200))
    elif k == "카드":
        d.rounded_rectangle((60, 520, W - 60, 1320), 40, fill=(40, 44, 56)); d.text((110, 570), "자료", font=굵(44), fill=강조); 글(d, (0, 720), 큰, 굵(64)); 글(d, (0, 1040), 작, 얇(40), (190, 190, 200))
    elif k == "단계":
        m = 맞춤(모델(n), 1000, 1200); c.paste(m, ((W - m.width) // 2, 300)); r = 맞춤(원화("02_3-4"), 300, 300); c.paste(r, (W - r.width - 30, 320)); d.rectangle((W - r.width - 32, 318, W - 28, 322 + r.height), outline=강조, width=3)
        자, 뜻 = 단계자막.get(n, ("", "")); 글(d, (0, 110), "%d단계" % n, 굵(56), 강조); y = 글(d, (0, 1500), 자, 굵(56)); 글(d, (0, y + 20), 뜻, 얇(32), (190, 190, 200))
    elif k == "비교":
        글(d, (0, 90), 큰, 굵(70), 강조)
        for i, t in enumerate(("02_정면", "02_3-4", "02_옆")):
            a, b = 맞춤(원화(t), 500, 520), 맞춤(모델(n, t), 500, 520); y = 250 + i * 560; c.paste(a, (30, y)); c.paste(b, (W - 30 - b.width, y))
        글(d, (0, 1880 - 60), 작, 얇(34), (190, 190, 200))
    elif k == "판정":
        글(d, (0, 500), 큰, 굵(70)); 글(d, (0, 1250), 작, 굵(50), 강조)
    return c
행 = list(csv.DictReader(open(os.path.join(H_, 편), encoding="utf-8"), delimiter="\t")); 임시 = os.path.join(출, "_판"); os.makedirs(임시, exist_ok=True); [os.remove(os.path.join(임시, x)) for x in os.listdir(임시)]
목록 = []
for i, r in enumerate(행):
    p = os.path.join(임시, "%03d.png" % i); 판(r["그림"], r["큰글"] or "", r["작은글"] or "").save(p); 목록.append((p, float(r["초"])))
이름 = os.path.splitext(편)[0]; shutil.copy(목록[0][0], os.path.join(출, 이름 + "_0초.png"))
with open(os.path.join(임시, "목록.txt"), "w", encoding="utf-8") as f:
    for p, s in 목록: f.write("file '%s'\nduration %.2f\n" % (p.replace("\\", "/"), s))
    f.write("file '%s'\n" % 목록[-1][0].replace("\\", "/"))
mp4 = os.path.join(출, 이름 + ".mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(임시, "목록.txt"), "-vf", "fps=%d,format=yuv420p" % FPS, "-c:v", "libx264", "-crf", "20", mp4], check=True)
print(mp4, "· 길이 %.1f초 · 판 %d" % (sum(s for _, s in 목록), len(목록)))
