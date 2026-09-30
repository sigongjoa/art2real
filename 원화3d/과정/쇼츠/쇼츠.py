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
이름 = os.path.splitext(편)[0]; shutil.copy(목록[0][0], os.path.join(출, 이름 + "_0초.png")); mp4 = os.path.join(출, 이름 + ".mp4")
if "--차분" in sys.argv:                                                                               # 옛 판: 판을 그대로 이어 붙임
    with open(os.path.join(임시, "목록.txt"), "w", encoding="utf-8") as f:
        for p, s in 목록: f.write("file '%s'\nduration %.2f\n" % (p.replace("\\", "/"), s))
        f.write("file '%s'\n" % 목록[-1][0].replace("\\", "/"))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(임시, "목록.txt"), "-vf", "fps=%d,format=yuv420p" % FPS, "-c:v", "libx264", "-crf", "20", mp4], check=True)
    print(mp4, "· 길이 %.1f초 · 판 %d" % (sum(s for _, s in 목록), len(목록))); sys.exit()
# ── 정신없는 판(기본): 컷마다 펀치 줌 · 흔들림 · 번쩍 · 외침 스티커가 튀어나옴 · 진행 막대 · 효과음(합성) ──
import wave, random
random.seed(7); SR = 44100; 총 = sum(s for _, s in 목록); 소리 = np.zeros(int(SR * (총 + 0.5)), np.float32)
def 톡(t, f0=900, f1=260, 길이=0.09, 크기=0.5):
    n = int(SR * 길이); x = np.arange(n) / SR; f = f0 * (f1 / f0) ** (x / 길이); w = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 28) * 크기; a = int(SR * t); 소리[a:a + n] += w[:len(소리[a:a + n])]
def 쉭(t, 길이=0.16, 크기=0.25):
    n = int(SR * 길이); x = np.arange(n) / SR; w = np.random.RandomState(int(t * 100)).randn(n) * np.sin(np.pi * x / 길이) ** 2 * 크기; w = np.convolve(w, np.ones(6) / 6, "same"); a = int(SR * t); 소리[a:a + n] += w[:len(소리[a:a + n])]
def 쿵(t, 크기=0.8):
    n = int(SR * 0.22); x = np.arange(n) / SR; w = np.sin(2 * np.pi * (110 * np.exp(-x * 14) + 45) * x) * np.exp(-x * 13) * 크기; a = int(SR * t); 소리[a:a + n] += w[:len(소리[a:a + n])]
색들 = [(255, 214, 64), (255, 90, 90), (90, 220, 255), (150, 255, 120)]
def 스티커(글자, k):
    f = 굵(150 if len(글자) <= 4 else 110); tmp = Image.new("RGBA", (1000, 320), (0, 0, 0, 0)); d = ImageDraw.Draw(tmp); tw = d.textlength(글자, font=f)
    d.text(((1000 - tw) / 2, 60), 글자, font=f, fill=색들[k % 4] + (255,), stroke_width=10, stroke_fill=(0, 0, 0, 255)); return tmp.rotate(random.choice((-9, -6, 6, 9)), expand=True, resample=Image.BICUBIC)
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-i", os.path.join(임시, "소리.wav"), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", mp4], stdin=subprocess.PIPE) if False else None
프레임들 = []; t0 = 0.0; 몇 = 0
for k, ((p, 초), r) in enumerate(zip(목록, 행)):
    base = Image.open(p).convert("RGB"); 외침 = (r.get("외침") or "").strip(); st = 스티커(외침, k) if 외침 else None; n = int(round(초 * FPS)); 쉭(t0); 톡(t0 + 0.02)
    if st is not None: 쿵(t0 + 0.30)
    sx, sy = random.randint(40, 120), {"카드": 1330, "판정": 820, "훅": 1500}.get(r["그림"].split(":")[0], 1080) + random.randint(-40, 40)      # 글자와 안 겹치는 빈 띠
    for j in range(n):
        z = 1.0 + 0.16 * np.exp(-j / 3.5) + 0.0009 * j                                               # 펀치 줌(컷 첫머리) + 천천히 다가감
        a = 22 * np.exp(-j / 4.0); dx, dy = (random.uniform(-a, a), random.uniform(-a, a))           # 흔들림
        w2, h2 = int(W * z), int(H * z); fr = base.resize((w2, h2), Image.BILINEAR).crop((int((w2 - W) / 2 - dx), int((h2 - H) / 2 - dy), int((w2 - W) / 2 - dx) + W, int((h2 - H) / 2 - dy) + H))
        if j < 3: fr = Image.blend(fr, Image.new("RGB", (W, H), (255, 255, 255)), 0.55 * (1 - j / 3))   # 번쩍
        if st is not None and j >= 9:
            q = j - 9; sc = 1.0 + 0.9 * np.exp(-q / 2.2) * np.cos(q * 1.1)                            # 튕기며 등장
            s2 = st.resize((max(2, int(st.width * sc)), max(2, int(st.height * sc))), Image.BILINEAR); fr.paste(s2, (sx + (st.width - s2.width) // 2, sy + (st.height - s2.height) // 2), s2)
        d = ImageDraw.Draw(fr); d.rectangle((0, 0, W, 14), fill=(60, 60, 70)); d.rectangle((0, 0, int(W * (t0 + j / FPS) / 총), 14), fill=(255, 214, 64))   # 진행 막대
        프레임들.append(np.asarray(fr, np.uint8).tobytes()); 몇 += 1
    t0 += 초
소리 = np.clip(소리, -1, 1); wv = wave.open(os.path.join(임시, "소리.wav"), "wb"); wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((소리 * 32767 * 0.7).astype(np.int16).tobytes()); wv.close()
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-i", os.path.join(임시, "소리.wav"), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", mp4], stdin=subprocess.PIPE)
for b in 프레임들: proc.stdin.write(b)
proc.stdin.close(); proc.wait(); print(mp4, "· 길이 %.1f초 · 컷 %d · 프레임 %d · 효과음 있음" % (총, len(목록), 몇))
