# 쇼츠 52 — 로드맵 1 단계 학습 스냅(학습2/스냅.json) → CadQuery STL → 블렌더 EEVEE → 6 칸 프레임 → Chatterbox → mp4 · 10-13
# venv python 굽기52.py [재료]  → out/설명/구멍/학습2/52_여러부품.mp4 · 프레임 png 는 학습2/프레임/
import os, sys, json, math, subprocess, hashlib, wave, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
H_ = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H_)
import 캐드점수2 as K
A = "G:/art2real/out/설명/구멍/"; L = A + "학습2/"; FR = L + "프레임/"; os.makedirs(FR, exist_ok=True)
BL = "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"; CB = "G:/art2real/out/tts/chatterbox/Scripts/python.exe"; CBS = "G:/art2real/원화3d/과정/영상05/tts/굽기_chatterbox.py"
CH = "G:/art2real/out/영상05/캐릭터시안/누끼/"; 인물 = {"나": CH + "표정_2_후드개발자_말.png", "AI": CH + "표정_6_안드로이드_말.png"}
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); W, H = 1080, 1920
바0, 바1, 카, 테, 하, 흰, 회, 빨, 초 = (8, 13, 26), (14, 22, 42), (16, 24, 42), (40, 54, 84), (64, 196, 255), (236, 242, 250), (64, 80, 112), (255, 96, 96), (110, 220, 140)
S = json.load(open(L + "스냅.json", encoding="utf-8")); 스 = S["스냅"]; 범 = S["범주"]; 정 = S["정답"]
대사 = json.load(open(os.path.join(H_, "대사52.json"), encoding="utf-8"))   # [[누구, 말(자막), 스냅 처음, 스냅 끝, 판(없으면 6칸)]]
읽기표 = {"부품 6개": "부품 여섯 개", "200개": "이백 개", "0.83": "영점 팔삼", "0.95": "영점 구오", "23%": "이십삼 퍼센트"}
def 읽기(말):
    for a, b in 읽기표.items(): 말 = 말.replace(a, b)
    return 말

def 선그림(p, s=512):
    a = Image.new("RGB", (s, s), (250, 248, 240)); d = ImageDraw.Draw(a); q = lambda v: (v + K.반) / (2 * K.반) * s; col = (30, 30, 35)
    if p["바탕"] == 0: w, h = p["b"][0] / 2, p["b"][1] / 2; d.rectangle((q(-w), q(-h), q(w), q(h)), outline=col, width=5)
    else: r = p["b"][2]; d.ellipse((q(-r), q(-r), q(r), q(r)), outline=col, width=5)
    for t, x, y, a_, b in p["칸"]:
        if t == 1: d.ellipse((q(x - a_), q(-y - a_), q(x + a_), q(-y + a_)), outline=col, width=5)
        elif t in (2, 3): w, h = (a_ / 2, b / 2) if t == 2 else (b / 2, a_ / 2); d.rectangle((q(x - w), q(-y - h), q(x + w), q(-y + h)), outline=col, width=5)
    return a
def 재료():
    import cadquery as cq
    이름 = []
    for k, p in enumerate(정): 선그림(p).save(L + "그림_%d.png" % k)
    for s in 스:
        for k, w in enumerate(s["지켜볼"]):
            n = "52_s%04d_%d" % (s["걸음"], k); cq.exporters.export(K.짓기(w["프로그램"]), A + "r%s.stl" % n, tolerance=0.01, angularTolerance=0.05); 이름.append(n)
    for i in range(0, len(이름), 40): subprocess.run([BL, "-b", "-P", os.path.join(H_, "렌더_빛.py"), "--"] + 이름[i:i + 40], check=True, stdout=subprocess.DEVNULL)

def 빛테(c, xy, r, col, 굵기=4, 퍼짐=12):
    g = Image.new("RGBA", c.size); ImageDraw.Draw(g).rounded_rectangle(xy, r, outline=col + (255,), width=굵기 + 6); c.alpha_composite(g.filter(ImageFilter.GaussianBlur(퍼짐))); ImageDraw.Draw(c).rounded_rectangle(xy, r, outline=col + (255,), width=굵기)
def 둥근(im, r=24, 흐림=40):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((흐림 // 2, 흐림 // 2, im.width - 흐림 // 2, im.height - 흐림 // 2), r, fill=255); im = im.convert("RGBA"); im.putalpha(m.filter(ImageFilter.GaussianBlur(흐림 / 3))); return im
_바 = None
def 바탕():
    global _바
    if _바 is None:
        c = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(c)
        for y in range(H): t = math.sin(math.pi * y / H); d.line((0, y, W, y), fill=tuple(int(바0[k] + (바1[k] - 바0[k]) * t) for k in range(3)) + (255,))
        g = Image.new("RGBA", (W, H)); e = ImageDraw.Draw(g)
        for x in range(0, W, 60): e.line((x, 0, x, H), fill=(120, 160, 230, 14))
        for y in range(0, H, 60): e.line((0, y, W, y), fill=(120, 160, 230, 14))
        c.alpha_composite(g); _바 = c
    return _바.copy()
def 프레임(k, 누구, 말, 판=None):
    c = 바탕(); d = ImageDraw.Draw(c); s = 스[k]
    t1, t2 = "AI", "가 여러 부품을 배우는 중"; f = F(60); w1, w2 = d.textlength(t1, font=f), d.textlength(t2, font=f); x = (W - w1 - w2) / 2
    g = Image.new("RGBA", c.size); ImageDraw.Draw(g).text((x, 50), t1, font=f, fill=하 + (255,)); c.alpha_composite(g.filter(ImageFilter.GaussianBlur(10))); d.text((x, 50), t1, font=f, fill=하); d.text((x + w1, 50), t2, font=f, fill=흰)
    # 진행 막대(걸음)
    d.rounded_rectangle((60, 160, 1020, 190), 15, fill=(40, 50, 75, 255)); d.rounded_rectangle((60, 160, 60 + 960 * s["걸음"] / 스[-1]["걸음"], 190), 15, fill=하)
    for j, t in enumerate(스):
        xx = 60 + 960 * t["걸음"] / 스[-1]["걸음"]; d.ellipse((xx - 7, 168, xx + 7, 182), fill=흰 if j <= k else 회)
    d.text((60, 205), "걸음 %d" % s["걸음"], font=F(40), fill=하); d.text((1020, 205), "%d" % 스[-1]["걸음"], font=F(30), fill=회, anchor="ra")
    if 판 == "진짜":
        for j, (부, 글) in enumerate((("머리", "머리"), ("발", "발"))):
            y0 = 300 + j * 620; d.rounded_rectangle((60, y0, 1020, y0 + 580), 30, fill=카 + (255,), outline=테, width=3)
            g_ = Image.open("G:/art2real/out/영상05/대화/49_진짜그림/자료/%s_앞그림.png" % 부).convert("RGBA").resize((400, 400)); c.alpha_composite(둥근(g_, 20, 10), (100, y0 + 80))
            r_ = Image.open(L + "진짜_%s.png" % 부).convert("RGBA").crop((180, 160, 720, 700)).resize((440, 440)); c.alpha_composite(둥근(r_, 24, 50), (540, y0 + 60))
            d.text((300, y0 + 520), "진짜 그림(앞)", font=F(32), fill=흰, anchor="mm"); d.text((760, y0 + 520), "모델이 지은 것", font=F(32), fill=빨, anchor="mm")
    else:   # 6 칸
        for j, w in enumerate(s["지켜볼"]):
            col, row = j % 2, j // 2; x0, y0 = 50 + col * 500, 290 + row * 410; bx = (x0, y0, x0 + 480, y0 + 390)
            d.rounded_rectangle(bx, 26, fill=카 + (255,), outline=테, width=2)
            im = Image.open(A + "빛_r52_s%04d_%d.png" % (s["걸음"], j)).convert("RGB"); im = im.crop((180, 160, 720, 700)).resize((380, 380)); c.alpha_composite(둥근(im, 24, 50), (x0 + 5, y0 + 5))   # 가운데를 잘라 크게
            gm = Image.open(L + "그림_%d.png" % j).convert("RGBA").resize((130, 130)); d.rounded_rectangle((x0 + 338, y0 + 14, x0 + 466, y0 + 142), 14, fill=(244, 246, 250, 255)); c.alpha_composite(gm.resize((118, 118)), (x0 + 343, y0 + 19))
            맞 = w["IoU"] >= .95; pill = (x0 + 140, y0 + 330, x0 + 340, y0 + 378); d.rounded_rectangle(pill, 24, fill=(12, 20, 36, 255)); 빛테(c, pill, 24, 초 if 맞 else 빨, 3, 8)
            d.text(((pill[0] + pill[2]) // 2, (pill[1] + pill[3]) // 2), "맞음" if 맞 else "아직", font=F(30), fill=흰, anchor="mm")
            d.text((x0 + 22, y0 + 18), 범[j].replace("+", " + "), font=F(24), fill=회)
    # 대사
    bb = (400, 1580, 1040, 1840); d.rounded_rectangle(bb, 40, fill=(12, 20, 36, 235)); 빛테(c, bb, 40, (70, 150, 230), 3, 10); d.polygon([(bb[0], bb[1] + 110), (bb[0] - 34, bb[1] + 140), (bb[0], bb[1] + 160)], fill=(12, 20, 36))
    줄, 지금 = [], ""
    for wd in 말.split(" "):
        if 지금 and d.textlength(지금 + " " + wd, font=F(44)) > bb[2] - bb[0] - 90: 줄.append(지금); 지금 = wd
        else: 지금 = (지금 + " " + wd).strip()
    줄.append(지금); d.multiline_text((bb[0] + 50, (bb[1] + bb[3]) // 2), chr(10).join(줄), font=F(44), fill=흰, anchor="lm", spacing=12)
    im = Image.open(인물[누구]).convert("RGBA"); im = im.crop(im.getbbox()); im = im.resize((int(im.width * 420 / im.height), 420), Image.LANCZOS); c.alpha_composite(im, (max(0, bb[0] - im.width + 40), H - im.height))
    return c.convert("RGB")

def 목소리():
    일, 파일 = [], []
    for row in 대사:
        누구, 말 = row[0], row[1]; k = hashlib.md5((누구 + 읽기(말)).encode()).hexdigest()[:10]; f = L + "_tts_%s.wav" % k; 파일.append(f)
        if not os.path.exists(f): 일.append({"말": 읽기(말), "누구": 누구, "출력": f + ".raw.wav"})
    if 일:
        json.dump(일, open(L + "_cb일감.json", "w", encoding="utf-8"), ensure_ascii=False); subprocess.run([CB, CBS, L + "_cb일감.json"], check=True)
        for j in 일: subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", j["출력"], "-af", "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse", "-ac", "1", "-ar", "24000", j["출력"][:-8]], check=True); os.remove(j["출력"])
    return 파일
def 영상(파일):
    FPS, GAP = 24, .35; 소리, 순 = [], []
    for row, f in zip(대사, 파일):
        누구, 말, a, b = row[:4]; 판 = row[4] if len(row) > 4 else None
        with wave.open(f) as w: x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
        n = int(np.ceil((len(x) / 24000 + GAP) * FPS)); 소리.append(np.concatenate([x, np.zeros(int(n / FPS * 24000) - len(x), np.int16)]))
        for i in range(n): 순.append((누구, 말, a + int((b - a + 1) * i / n) if b > a else a, 판))
    with wave.open(L + "_목소리.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(np.concatenate(소리).tobytes())
    캐시 = {}
    for t in 순:
        if t not in 캐시: p = FR + "f_%02d_%s.png" % (t[2], hashlib.md5((t[1] + str(t[3])).encode()).hexdigest()[:6]); 프레임(t[2], t[0], t[1], t[3]).save(p); 캐시[t] = p
    with open(L + "_목록.txt", "w", encoding="utf-8") as f:
        for t in 순: f.write("file '%s'\nduration %.5f\n" % (캐시[t], 1 / FPS))
    out = L + "52_여러부품.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", L + "_목록.txt", "-i", L + "_목소리.wav", "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    print(out, round(len(순) / FPS, 1), "초 · 프레임 그림", len(캐시))

if __name__ == "__main__":
    if "재료" in sys.argv or not os.path.exists(A + "빛_r52_s%04d_5.png" % 스[-1]["걸음"]): 재료()
    영상(목소리())
