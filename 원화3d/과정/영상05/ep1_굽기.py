# -*- coding: utf-8 -*-
"""가로 다큐 굽기 (10-02): 대본 tsv 한 장 → 1920×1080 mp4 (나레이션 · 자막 · 출처).
    python ep1_굽기.py <대본.tsv> <출력.mp4>
나레이션은 edge-tts(ko-KR-SunHiNeural · 쇼츠 굽기.sh 와 같은 음성) — 대본 글이 Microsoft TTS 로 나간다.
화면 종류: art:full|head · still:<경로> · seq:<프레임폴더> · montage:<경로|경로…> · trii:<폴더(0.5/1.0/1.5 또는 0/1/2)> · tri:<접두> · tri_last:<접두>
           overlay:<폴더> · side:<경로|경로> (art_head = 원화 머리) · card:<큰 글|작은 글> · title:<줄|줄> · chapter:<작은|큰> · reasons:"""
import os, sys, csv, glob, hashlib, asyncio, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
R = r"G:\art2real"; FR = os.path.join(R, r"out\영상05\ep1\프레임"); W, H, FPS, SR = 1920, 1080, 30, 24000
TSV, MP4 = sys.argv[1], sys.argv[2]; CACHE = os.path.join(os.path.dirname(MP4), "_tts"); os.makedirs(CACHE, exist_ok=True)
BG = (16, 16, 22); WHITE = (240, 240, 244); GRAY = (140, 140, 150); GOLD = (255, 200, 110)
F = lambda n, b=False: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf" if b else "C:/Windows/Fonts/malgun.ttf", n)
ART = os.path.join(R, r"트레일\trail7_part3d\in\omega_front_clean.png"); HEAD = (400, 60, 680, 240)
VOICE, PAD, LEAD = "ko-KR-SunHiNeural", 0.55, 0.25

def rgba_on(im, bg=BG):
    im = im.convert("RGBA"); b = Image.new("RGBA", im.size, bg + (255,)); return Image.alpha_composite(b, im).convert("RGB")
def load(p):
    p = p if os.path.isabs(p) else os.path.join(R, p); im = Image.open(p)
    white = p.endswith(".png") and "교재그림" in p
    return rgba_on(im, (255, 255, 255) if white else BG)
def fit(im, w, h):
    s = min(w / im.width, h / im.height); return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
def art(kind):
    im = Image.open(ART)
    if kind == "head": im = im.crop((392, 18, 672, 208))          # 머리 + 깃 (원화 1024 판 · 눈으로 맞춤)
    return rgba_on(im)
def frames_of(d):
    d = d if os.path.isabs(d) else os.path.join(FR, d); return sorted(glob.glob(os.path.join(d, "*.png")))
def wrap(d, s, f, wmax):
    out, line = [], ""
    for w in s.split(" "):
        t = (line + " " + w).strip()
        if d.textlength(t, font=f) > wmax and line: out.append(line); line = w
        else: line = t
    return out + [line]

# ---------- 화면 만들기: beat → (t: 0..1, frame_index) → PIL ----------
AREA = (60, 40, W - 60, H - 210)       # 그림 구역 (자막 위)
def place(c, im, box=AREA, zoom=1.0):
    x0, y0, x1, y1 = box; m = fit(im, (x1 - x0) * zoom, (y1 - y0) * zoom); c.paste(m, (x0 + (x1 - x0 - m.width) // 2, y0 + (y1 - y0 - m.height) // 2))
def labels3(c, names, y):
    d = ImageDraw.Draw(c); cw = (W - 120) / 3
    for i, n in enumerate(names): d.text((60 + cw * i + cw / 2, y), n, fill=GOLD, font=F(40, True), anchor="mm")
def three(c, ims, names):
    cw = (W - 120) // 3
    for i, im in enumerate(ims): place(c, im, (60 + cw * i, 90, 60 + cw * (i + 1), H - 230))
    labels3(c, names, 60)
def trio_names(dirname):
    return ["깊이 ×0.5", "×1", "×1.5"] if "b1" in dirname else ["①", "②", "③"]
def trio_files(d):
    fs = sorted(glob.glob(os.path.join(FR, d, "*.png"))); return fs
class Beat:
    def __init__(s, kind, arg, say, src, mins):
        s.kind, s.arg, s.say, s.src, s.min = kind, arg, say, src, mins; s.cache = {}
    def prep(s):
        k, a = s.kind, s.arg
        if k == "art": s.cache["im"] = art(a)
        elif k == "still": s.cache["im"] = load(a)
        elif k == "seq": s.cache["fs"] = frames_of(a)
        elif k == "montage": s.cache["ims"] = [load(p) for p in a.split("|")]
        elif k == "trii": s.cache["ims"] = [rgba_on(Image.open(p)) for p in trio_files(a)]
        elif k in ("tri", "tri_last"):
            ds = sorted(d for d in glob.glob(os.path.join(FR, a + "_*")) if os.path.isdir(d)); s.cache["fss"] = [sorted(glob.glob(os.path.join(d, "*.png"))) for d in ds]
            if k == "tri_last": s.cache["ims"] = [rgba_on(Image.open(fs[-1])) for fs in s.cache["fss"]]
        elif k == "overlay":
            ms = [np.array(Image.open(p))[..., 3] > 0 for p in trio_files(a)]; u = np.zeros(ms[0].shape + (3,), np.uint8)
            for m, col in zip(ms, [(255, 80, 80), (80, 255, 80), (80, 120, 255)]): u[m] = np.clip(u[m].astype(int) + np.array(col) // 1, 0, 255)
            img = np.full(ms[0].shape + (3,), BG, np.uint8); allm = ms[0] & ms[1] & ms[2]; anym = ms[0] | ms[1] | ms[2]
            img[anym] = (230, 60, 60); img[allm] = (235, 235, 240); s.cache["im"] = Image.fromarray(img); s.cache["diff"] = int((anym & ~allm).sum())
        elif k == "side": s.cache["ims"] = [art("head") if p == "art_head" else load(p) for p in a.split("|")]
    def draw(s, t, fi):
        c = Image.new("RGB", (W, H), BG); k, a = s.kind, s.arg; d = ImageDraw.Draw(c)
        if k in ("art", "still"): place(c, s.cache["im"], zoom=1.0 + 0.05 * t)
        elif k == "seq": fs = s.cache["fs"]; place(c, rgba_on(Image.open(fs[min(len(fs) - 1, int(t * len(fs)))])))
        elif k == "montage": ims = s.cache["ims"]; place(c, ims[min(len(ims) - 1, int(t * len(ims)))])
        elif k == "trii": three(c, s.cache["ims"], trio_names(a))
        elif k == "tri":
            ims = [rgba_on(Image.open(fs[min(len(fs) - 1, int(min(1, t * 1.15) * (len(fs) - 1)))])) for fs in s.cache["fss"]]; three(c, ims, trio_names(a))
        elif k == "tri_last": three(c, s.cache["ims"], trio_names(a))
        elif k == "overlay":
            place(c, s.cache["im"]); d.text((W // 2, 70), "세 실루엣 겹침 — 어긋난 픽셀 %d" % s.cache["diff"], fill=GOLD, font=F(40, True), anchor="mm")
        elif k == "side":
            for i, im in enumerate(s.cache["ims"]): place(c, im, (60 + i * (W - 120) // 2, 60, 60 + (i + 1) * (W - 120) // 2, H - 230))
        elif k == "card":
            big, _, small = a.partition("|"); d.text((W // 2, H // 2 - 110), big, fill=WHITE, font=F(96, True), anchor="mm")
            if small: d.text((W // 2, H // 2 + 20), small, fill=GOLD, font=F(54, True), anchor="mm")
        elif k == "title":
            ls = a.split("|"); a_ = min(1, t * 3)
            for i, l in enumerate(ls): d.text((W // 2, H // 2 - 70 + i * 140), l, fill=tuple(int(v * a_ + b * (1 - a_)) for v, b in zip(WHITE, BG)), font=F(110, True), anchor="mm")
        elif k == "chapter":
            small, _, big = a.partition("|"); d.text((W // 2, H // 2 - 80), small, fill=GOLD, font=F(56, True), anchor="mm"); d.text((W // 2, H // 2 + 30), big, fill=WHITE, font=F(84, True), anchor="mm")
        elif k == "reasons":
            for i in range(4):
                d.text((W // 2 - 360, 260 + i * 130), "이유 %d" % (i + 1), fill=GOLD, font=F(64, True), anchor="lm")
                d.rectangle([W // 2 - 120, 235 + i * 130, W // 2 + 420, 285 + i * 130], fill=(60, 60, 70))
        if s.src: d.text((40, 24), s.src, fill=GRAY, font=F(28))
        if s.say:
            f = F(44, True); ls = wrap(d, s.say, f, W - 300)
            # 긴 말은 두 줄씩 나눠 시간 순으로 보여 준다
            chunks = [ls[i:i + 2] for i in range(0, len(ls), 2)]; ch = chunks[min(len(chunks) - 1, int(t * len(chunks)))]
            y = H - 60 - len(ch) * 58
            d.rectangle([0, y - 24, W, H], fill=(10, 10, 14))
            for j, l in enumerate(ch): d.text((W // 2, y + j * 58), l, fill=WHITE, font=f, anchor="mt")
        return c

# ---------- 소리 ----------
def tts(text):
    h = hashlib.md5((VOICE + text).encode()).hexdigest()[:12]; mp3 = os.path.join(CACHE, h + ".mp3"); wav = os.path.join(CACHE, h + ".wav")
    if not os.path.exists(wav):
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, VOICE).save(mp3))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ac", "1", "-ar", str(SR), wav], check=True)
    with wave.open(wav) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16)

rows = list(csv.DictReader(open(TSV, encoding="utf-8"), delimiter="\t"))
beats = []
for r in rows:
    k, _, a = r["화면"].partition(":"); beats.append(Beat(k, a, (r["말"] or "").strip(), (r["출처"] or "").strip(), float(r["최소초"] or 0)))
audio = []; plan = []
for b in beats:
    v = tts(b.say) if b.say else np.zeros(0, np.int16)
    dur = max(b.min, LEAD + len(v) / SR + PAD); n = int(round(dur * SR))
    seg = np.zeros(n, np.int16); s0 = int(LEAD * SR); seg[s0:s0 + len(v)] = v[: n - s0]; audio.append(seg); plan.append(dur)
    print("%-9s %5.1fs  %s" % (b.kind, dur, b.say[:30]))
pcm = np.concatenate(audio); wavp = MP4[:-4] + ".wav"
with wave.open(wavp, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("총 %.1f 초" % (len(pcm) / SR))
p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                      "-i", wavp, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-c:a", "aac", "-b:a", "160k", "-shortest", MP4], stdin=subprocess.PIPE)
for b, dur in zip(beats, plan):
    b.prep(); n = int(round(dur * FPS))
    for i in range(n): p.stdin.write(b.draw(i / max(1, n - 1), i).tobytes())
    b.cache.clear()
p.stdin.close(); p.wait(); print("끝", MP4)
