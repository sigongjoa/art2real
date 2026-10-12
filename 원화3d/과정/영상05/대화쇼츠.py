"""두 캐릭터 대화 쇼츠 굽기 (10-10) — 나(후드 개발자) · AI(안드로이드) · 2D 누끼 표정 + 위쪽 화면 판 + 대사창
    python 대화쇼츠.py <편>        → out/영상05/대화/<편>/<편>.mp4
    python 대화쇼츠.py <편> still  → 줄마다 한 장 → 스틸시트.jpg
편 폴더(원화3d/과정/영상05/대화/<편>/): 대본.tsv(누구 · 나표정 · AI표정 · 화면 · 큰글 · 말) + 화면.py(def 판(키, 진행 0~1) → RGBA 1000×760)
목소리: 나 = InJoon · AI = SunHi (edge-tts) · 말하는 쪽만 밝고 통통 · 대사는 한 글자씩 · 큰글은 뿅(앞에 초: · 빨: 로 색) · 배경은 죽인 작업실"""
import sys, os, csv, glob, json, asyncio, subprocess, wave, hashlib, importlib.util
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__)); NAME = sys.argv[1]; STILL = "still" in sys.argv[2:]
SRC = os.path.join(HERE, "대화", NAME); D = "G:/art2real/out/영상05/대화/" + NAME; os.makedirs(D, exist_ok=True)
CH = "G:/art2real/out/영상05/캐릭터시안/"; BGM = "G:/claude-faceless-shorts-creator/media/library/music/clips/docu-pluck.mp3"
SR, FPS, GAP, W, H = 24000, 24, 0.35, 1080, 1920
VOICE = {"나": ("ko-KR-InJoonNeural", "+8%"), "AI": ("ko-KR-SunHiNeural", "+10%")}
COL = {"나": (120, 190, 255), "AI": (90, 230, 200)}
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)

rows = [r for r in csv.reader(open(os.path.join(SRC, "대본.tsv"), encoding="utf-8"), delimiter="\t") if r and not r[0].startswith("#")][1:]
rows = [dict(누구=r[0], 나=r[1], AI=r[2], 화면=r[3], 큰글=r[4], 말=r[5]) for r in rows]
spec = importlib.util.spec_from_file_location("화면", os.path.join(SRC, "화면.py")); 화면 = importlib.util.module_from_spec(spec); spec.loader.exec_module(화면)

SAPI = os.environ.get("TTS") == "sapi"   # 10-12 edge-tts 403 → Windows 기본 Heami(여) 하나 · 나 = 음높이 내림 · 서버 돌아오면 TTS 빼고 다시 굽기
def tts(text, who):
    v, rate = VOICE[who]; key = hashlib.md5((("sapi" + who) if SAPI else (v + rate)).encode() + text.encode()).hexdigest()[:10]; mp3, wav = D + "/_tts_%s.mp3" % key, D + "/_tts_%s.wav" % key
    if SAPI and not os.path.exists(wav):
        raw = wav + ".raw.wav"; t = text.replace("'", "''")
        subprocess.run(["powershell", "-NoProfile", "-Command", "Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.SelectVoice('Microsoft Heami Desktop'); $s.Rate = 2; $s.SetOutputToWaveFile('%s'); $s.Speak('%s'); $s.Dispose()" % (raw.replace("/", "\\"), t)], check=True)
        f = "asetrate=24000*0.82,aresample=24000,atempo=1.2195" if who == "나" else "anull"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", f, "-ac", "1", "-ar", str(SR), wav], check=True); os.remove(raw)
    if not os.path.exists(wav):
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, v, rate=rate).save(mp3))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ac", "1", "-ar", str(SR), wav], check=True)
    with wave.open(wav) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16)
voices = [tts(r["말"], r["누구"]) for r in rows]
ns = [int(np.ceil((len(v) / SR + GAP) * FPS)) for v in voices]; starts = np.cumsum([0] + ns)[:-1]; N = sum(ns)

# 바탕 · 인물(표정별 누끼 · 한 번만 읽음)
bg0 = Image.open(CH + "A_작업실.png").convert("RGB").resize((1316, 1920)).crop((118, 0, 1198, 1920))
bg0 = ImageEnhance.Brightness(ImageEnhance.Color(bg0).enhance(.5).filter(ImageFilter.GaussianBlur(16))).enhance(.36)
_인 = {}
def 인물(who, e, h, 어둡게, 뒤집기):
    k = (who, e, h, 어둡게, 뒤집기)
    if k not in _인:
        f = {"나": "2_후드개발자", "AI": "6_안드로이드"}[who]; im = Image.open(CH + "누끼/표정_%s_%s.png" % (f, e)); im = im.crop(im.getbbox())
        im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
        if 뒤집기: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if 어둡게: a = im.split()[3]; im = ImageEnhance.Brightness(im.convert("RGB")).enhance(.42).convert("RGBA"); im.putalpha(a)
        _인[k] = im
    return _인[k]
def 그림자붙(cv, im, xy, a=110):
    s = Image.new("RGBA", im.size, (0, 0, 0, 0)); s.putalpha(im.split()[3].point(lambda v: a if v > 20 else 0))
    cv.alpha_composite(s.filter(ImageFilter.GaussianBlur(14)), (xy[0] + 12, xy[1] + 16)); cv.alpha_composite(im, xy)
ease = lambda x: 1 - (1 - min(max(x, 0), 1)) ** 3
def 튐(x):   # 0→1 사이 살짝 넘쳤다 돌아옴
    x = min(max(x, 0), 1); return 1 + .12 * np.sin(np.pi * x) * (1 - x) * 2.2 if x < 1 else 1.0

def 프레임(f):
    li = int(np.searchsorted(starts, f, side="right") - 1); r = rows[li]; t = (f - starts[li]) / FPS; dur = ns[li] / FPS
    z = 1 + .03 * f / N; b = bg0.resize((int(W * z), int(H * z))); cv = b.crop(((b.width - W) // 2, (b.height - H) // 2, (b.width - W) // 2 + W, (b.height - H) // 2 + H)).convert("RGBA")
    # 위쪽 화면 판(편의 화면.py) — 줄이 바뀌면 0.25 초 튀어나옴
    p = 화면.판(r["화면"], min(t / max(dur - GAP, .1), 1)).convert("RGBA"); s = 튐(t / .25) * (.85 + .15 * ease(t / .2))
    p = p.resize((int(p.width * s), int(p.height * s)), Image.LANCZOS); 그림자붙(cv, p, ((W - p.width) // 2, 60 + (760 - p.height) // 2))
    # 인물: 말하는 쪽은 밝고 통통(말하는 동안 사인) · 다른 쪽은 어둡게
    for who, h, x0, flip in (("AI", 800, None, True), ("나", 860, -120, False)):
        말 = r["누구"] == who; im = 인물(who, r[who], h, not 말, flip)
        dy = int(-14 * abs(np.sin(t * 7.5))) if 말 and t < dur - GAP else 0
        x = x0 if x0 is not None else W - im.width + 140; 그림자붙(cv, im, (x, 1560 - h + 50 + dy))
    d = ImageDraw.Draw(cv)
    if r["큰글"]:   # 큰 글: 뿅 커졌다가 자리
        k = 튐(t / .3); 색, 글 = (r["큰글"].split(":", 1) + [""])[:2] if r["큰글"][:2] in ("초:", "빨:", "노:") else ("노", r["큰글"])
        col = {"초": (90, 220, 120), "빨": (255, 90, 90), "노": (255, 225, 90)}[색[:1]]
        d.text((W // 2, 880), 글, font=F(int(104 * k)), fill=col, stroke_width=10, stroke_fill=(10, 10, 20), anchor="mm")
    # 대사창 · 이름표 · 한 글자씩
    c = COL[r["누구"]]; d.rounded_rectangle((40, 1560, 1040, 1880), 30, fill=(18, 20, 36, 238), outline=c, width=6)
    nm = r["누구"]; d.rounded_rectangle((70, 1520, 70 + 60 * len(nm) + 60, 1600), 20, fill=c); d.text((100 + 30 * len(nm), 1560), nm, font=F(48), fill=(18, 20, 36), anchor="mm")
    말 = r["말"]; n = len(말) if STILL else int(len(말) * min(1, t / max(len(voices[li]) / SR * .9, .1)))
    줄 = 줄나눔(d, 말[:n], 말); d.multiline_text((90, 1630), "\n".join(줄), font=F(60), fill="white", spacing=18)
    return cv.convert("RGB")
def 줄나눔(d, 보임, 전체, wmax=900):   # 전체 문장 기준으로 줄을 정해 두고 보이는 만큼만
    w, 줄, cur = 전체.split(" "), [], ""
    for x in w:
        if cur and d.textlength(cur + " " + x, font=F(60)) > wmax: 줄.append(cur); cur = x
        else: cur = (cur + " " + x).strip()
    줄.append(cur); out, k = [], len(보임)
    for l in 줄:
        if k <= 0: break
        out.append(l[:k]); k -= len(l) + 1
    return out[:3]

if STILL:
    ims = [프레임(int(s + n * .8)) for s, n in zip(starts, ns)]; nc = 4; th = 640; tw = 360
    o = Image.new("RGB", (tw * nc, th * ((len(ims) + nc - 1) // nc)), "white")
    for i, im in enumerate(ims): o.paste(im.resize((tw, th)), (tw * (i % nc), th * (i // nc)))
    o.save(D + "/스틸시트.jpg", quality=88); print(D + "/스틸시트.jpg"); sys.exit()

aud = np.zeros(N * SR // FPS + SR, np.float32)
for v, s in zip(voices, starts): a = int(s * SR / FPS); aud[a:a + len(v)] += v
tt = np.arange(int(.14 * SR)) / SR; pop = (np.sin(2 * np.pi * (500 + 2600 * tt) * tt) * np.exp(-tt * 30) * 8000).astype(np.float32)
for r, s in zip(rows, starts):
    if r["큰글"]: a = int(s * SR / FPS); aud[a:a + len(pop)] += pop
with wave.open(D + "/_소리.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.clip(aud, -32767, 32767).astype(np.int16).tobytes())
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                       "-i", D + "/_소리.wav", "-stream_loop", "-1", "-i", BGM,
                       "-filter_complex", "[2:a]volume=-22dB[b];[1:a][b]amix=inputs=2:duration=first:normalize=0[a]", "-map", "0:v", "-map", "[a]",
                       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-shortest", D + "/%s.mp4" % NAME], stdin=subprocess.PIPE)
for f in range(N): ff.stdin.write(프레임(f).tobytes())
ff.stdin.close(); ff.wait(); print(D + "/%s.mp4" % NAME, round(N / FPS, 1), "초 ·", len(rows), "줄")
