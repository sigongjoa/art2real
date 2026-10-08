"""장난감 CG 쇼츠 굽기 — 편 폴더 하나(대본.tsv + 장면.py) → out/영상05/장난감/<편>/<편>.mp4
    python 장난감굽기.py <편>          전체
    python 장난감굽기.py <편> still    컷마다 한 장 → 스틸시트.jpg (내가 먼저 본다)
대본.tsv 칸: 카메라(쉼표로 여럿 → 그 줄을 고르게 나눔) · 말 · 큰낱말. 첫 줄에 질문(훅)을 둔다.
나레이션 edge-tts SunHi +5% · 큰 낱말마다 뿅 소리 · 배경음 docu-pluck -22 dB."""
import sys, os, json, glob, asyncio, subprocess, wave, csv, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = sys.argv[1]; STILL = "still" in sys.argv[2:]; BAKE_ONLY = "자막만" in sys.argv[2:]   # 자막만 = 블렌더 건너뛰고 있는 프레임으로 다시 굽기
SRC = os.path.join(HERE, "장난감", NAME); D = "G:/art2real/out/영상05/장난감/" + NAME; FR = D + "/frames"
os.makedirs(FR, exist_ok=True)
LAND = os.path.exists(os.path.join(SRC, "가로"))   # 10-08 가로 긴 영상
if LAND: os.environ["TOY_LAND"] = "1"
VW, VH = (1920, 1080) if LAND else (1080, 1920)
BL = "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"
BG = os.path.join(SRC, "bg.png") if os.path.exists(os.path.join(SRC, "bg.png")) else "G:/art2real/out/영상05/시험판/bg.png"
BGM = "G:/claude-faceless-shorts-creator/media/library/music/clips/docu-pluck.mp3"
VOICE, SR, FPS, GAP = "ko-KR-SunHiNeural", 24000, 24, 0.5

rows = [r for r in csv.reader(open(os.path.join(SRC, "대본.tsv"), encoding="utf-8"), delimiter="\t") if r and not r[0].startswith("#")]
rows = [(r[0].split(","), r[1], r[2] if len(r) > 2 else "") for r in rows[1:]]     # 머리줄 건너뜀

def tts(text):
    key = hashlib.md5(text.encode()).hexdigest()[:10]; mp3, wav = D + "/_tts_%s.mp3" % key, D + "/_tts_%s.wav" % key
    if not os.path.exists(wav):
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, VOICE, rate="+5%").save(mp3))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ac", "1", "-ar", str(SR), wav], check=True)
    with wave.open(wav) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16)
voices = [tts(r[1]) for r in rows]
ns = [int(np.ceil((len(v) / SR + GAP) * FPS)) for v in voices]

cuts, lines, f = [], [], 1
for (cams, _, _), n in zip(rows, ns):
    lines.append([f, f + n - 1]); k = len(cams)
    for j, c in enumerate(cams):
        m = n // k + (1 if j < n % k else 0)
        if cuts and cuts[-1]["cam"] == c: cuts[-1]["n"] += m
        else: cuts.append({"cam": c, "n": m})
    f += n
json.dump({"cuts": cuts, "lines": lines}, open(D + "/시간표.json", "w", encoding="utf-8"))
if not BAKE_ONLY and not os.environ.get("FRAMES"):   # FRAMES=a-b 면 나머지 프레임은 남긴다(끝만 다시 굽기)
    for p in glob.glob(FR + "/*.png"): os.remove(p)
env = dict(os.environ, PYTHONPATH=HERE)
# GPU 8 GB 하나 — 블렌더는 동시에 2 개까지(병렬 에이전트용 자리표). 4 시간 넘은 자리표는 죽은 것으로 보고 치운다.
import time
LOCKS = "G:/art2real/out/영상05/장난감/_자리"; os.makedirs(LOCKS, exist_ok=True); slot = None
while slot is None and not BAKE_ONLY:
    for k in range(2):
        p = "%s/%d.lock" % (LOCKS, k)
        if os.path.exists(p) and time.time() - os.path.getmtime(p) > 4 * 3600: os.remove(p)
        try: os.close(os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)); slot = p; break
        except FileExistsError: pass
    else: time.sleep(5)
try:
  if not BAKE_ONLY:
    r = subprocess.run([BL, "-b", "-P", os.path.join(SRC, "장면.py"), "--", D + "/시간표.json", BG, FR] + (["--still"] if STILL else []),
                   stdout=open(D + "/_블렌더.log", "w", encoding="utf-8"), stderr=subprocess.STDOUT, env=env)
finally:
    if slot: os.remove(slot)
if not BAKE_ONLY:
    log = open(D + "/_블렌더.log", encoding="utf-8", errors="replace").read()
    if "Traceback" in log or r.returncode: print(log[log.find("Traceback"):][:3000]); sys.exit(1)

F = lambda s: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", s)
def text(d, xy, s, size, stroke):
    d.text(xy, s, font=F(size), fill=(255, 255, 255), anchor="mm", stroke_width=stroke, stroke_fill=(20, 20, 30))

if STILL:
    tw, th = (VW // 4, VH // 4); nc = 6 if LAND else 8
    ims = [Image.open(p).convert("RGB").resize((tw, th)) for p in sorted(glob.glob(FR + "/still_*.png"))]
    o = Image.new("RGB", (tw * min(nc, len(ims)), th * ((len(ims) + nc - 1) // nc)), "white")
    for i, im in enumerate(ims): o.paste(im, (tw * (i % nc), th * (i // nc)))
    o.save(D + "/스틸시트.jpg"); print(D + "/스틸시트.jpg", len(ims), "컷"); sys.exit()

# 소리: 나레이션 + 큰 낱말마다 뿅 + 배경음
aud = np.concatenate([np.pad(v, (0, n * SR // FPS - len(v))) for v, n in zip(voices, ns)]).astype(np.float32)
t = np.arange(int(0.14 * SR)) / SR; pop = (np.sin(2 * np.pi * (500 + 2600 * t) * t) * np.exp(-t * 30) * 9000).astype(np.float32)
for (_, _, big), (f0, _) in zip(rows, lines):
    if big: s = (f0 - 1) * SR // FPS; aud[s:s + len(pop)] += pop[:len(aud) - s]
# 효과음(있으면): 편 폴더 효과음.tsv — 줄 · 줄 안 비율 · 종류(발 · 퍽 · 찡 · 휙 · 짹). 줄 기준이라 TTS 길이가 바뀌어도 따라간다. 전부 합성(내려받기 없음)
def sfx(kind):
    t = np.arange(int({"발": 0.07, "퍽": 0.3, "찡": 1.0, "휙": 0.45, "짹": 0.14}[kind] * SR)) / SR; rng = np.random.default_rng(len(t))
    lp = lambda x, k: np.convolve(x, np.ones(k) / k, "same")
    if kind == "발": y = np.sin(2 * np.pi * 150 * t) * np.exp(-t * 60) + 0.3 * lp(rng.standard_normal(len(t)), 8) * np.exp(-t * 80); a = 3500
    if kind == "퍽": y = np.sin(2 * np.pi * (90 - 40 * t) * t) * np.exp(-t * 14) + 0.8 * lp(rng.standard_normal(len(t)), 20) * np.exp(-t * 25); a = 14000
    if kind == "찡": y = sum(np.sin(2 * np.pi * f * t) / (k + 1) for k, f in enumerate((1320, 1980, 2640, 3960))) * np.exp(-t * 4) * np.minimum(1, t * 200); a = 4000
    if kind == "휙": n = rng.standard_normal(len(t)); y = (n - lp(n, 6)) * np.sin(np.pi * t / t[-1]) ** 2; a = 4000
    if kind == "짹": y = np.sin(2 * np.pi * (2800 + 9000 * t) * t) * np.sin(np.pi * t / t[-1]) * (0.6 + 0.4 * np.sin(2 * np.pi * 45 * t)); a = 2200
    return (y / np.abs(y).max() * a).astype(np.float32)
fx_path = os.path.join(SRC, "효과음.tsv")
if os.path.exists(fx_path):
    for r in csv.reader(open(fx_path, encoding="utf-8"), delimiter="\t"):
        if not r or r[0].startswith("#") or not r[0].strip().isdigit(): continue
        f0, f1 = lines[int(r[0])]; s = int((f0 - 1 + float(r[1]) * (f1 - f0)) * SR / FPS); y = sfx(r[2].strip())
        aud[s:s + len(y)] += y[:max(0, len(aud) - s)]
with wave.open(D + "/_소리.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.clip(aud, -32767, 32767).astype(np.int16).tobytes())

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (VW, VH), "-r", str(FPS), "-i", "-",
                       "-i", D + "/_소리.wav", "-stream_loop", "-1", "-i", BGM,
                       "-filter_complex", "[2:a]volume=-22dB[b];[1:a][b]amix=inputs=2:duration=first:normalize=0[a]", "-map", "0:v", "-map", "[a]",
                       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-shortest", D + "/%s.mp4" % NAME],
                      stdin=subprocess.PIPE)
# 자막은 지금 구절만: 쉼표 · 마침표에서 나누고 글자 수 비례로 시간을 준다 · 그래도 넓으면 두 줄
import re
def phrases(line, f0, nvoice):
    ps = [p.strip() for p in re.findall(r"(?:[^,.?!]|(?<=\d)\.(?=\d))+[,.?!]?", line) if p.strip()]   # 10-08: 2.77 · 1.5 의 점에서 자르지 않음
    tot = sum(len(p) for p in ps); out, f = [], f0
    for p in ps: out.append((f, p)); f += nvoice * len(p) / tot
    return out
def wrap(d, s, size, wmax=980):
    if d.textlength(s, font=F(size)) <= wmax: return [s]
    w = s.split(" "); best = min(range(1, len(w)), key=lambda i: abs(len(" ".join(w[:i])) - len(" ".join(w[i:])))) if len(w) > 1 else 1
    return [" ".join(w[:best]), " ".join(w[best:])]
PH = [phrases(r[1], l[0], len(v) / SR * FPS) for r, l, v in zip(rows, lines, voices)]
frames = sorted(glob.glob(FR + "/[0-9]*.png")); k = 0
MP = os.path.join(SRC, "모션.json")   # 10-08: 있으면 모션키트(레퍼런스 실측 규칙) · 없으면 예전 그대로
if os.path.exists(MP):
    import 모션키트 as MK
    PLAN = json.load(open(MP, encoding="utf-8")); AN = json.load(open(FR + "/앵커프레임.json", encoding="utf-8")) if os.path.exists(FR + "/앵커프레임.json") else {}
    for i, p in enumerate(frames, 1):
        while k < len(lines) - 1 and i > lines[k][1]: k += 1
        im = MK.apply(Image.open(p).convert("RGBA"), i, k, lines[k], PLAN, AN)
        if rows[k][2] and str(k) not in PLAN: a_ = MK.ease((i - lines[k][0]) / 5); MK.big_number(im, rows[k][2], a_)
        cur = [p_ for f_, p_ in PH[k] if f_ <= i][-1:] or [PH[k][0][1]]; MK.caption(im, cur[0])
        ff.stdin.write(im.convert("RGB").tobytes())
    ff.stdin.close(); ff.wait()
    print(D + "/%s.mp4" % NAME, round(sum(ns) / FPS, 1), "초 · 모션키트"); sys.exit()
for i, p in enumerate(frames, 1):
    while k < len(lines) - 1 and i > lines[k][1]: k += 1
    im = Image.open(p).convert("RGB"); d = ImageDraw.Draw(im)
    if rows[k][2]: pop_ = min(1.0, (i - lines[k][0]) / 5); text(d, (540, 430), rows[k][2], int(150 * (0.8 + 0.2 * pop_)), 10)
    cur = [p for f_, p in PH[k] if f_ <= i][-1:] or [PH[k][0][1]]
    for j, l in enumerate(wrap(d, cur[0], 58)): text(d, (540, 1250 + j * 74), l, 58, 6)
    ff.stdin.write(im.tobytes())
ff.stdin.close(); ff.wait()
print(D + "/%s.mp4" % NAME, round(sum(ns) / FPS, 1), "초 ·", len(cuts), "컷 · 컷 평균", round(sum(ns) / FPS / len(cuts), 1), "초")
