"""영상05 시험판 15 초 — 「고양이 몇 마리?」 (신비한 건축사전 식: 컷 짧게 · 가운데 한 줄 자막 · 핵심 낱말 크게).
    python 시험판.py still   컷마다 한 장(싼 확인)
    python 시험판.py         전체 굽기 → out/영상05/시험판/시험판.mp4
배경은 시험판_배경.py(SDXL) · 장면은 시험판_블렌더.py · 나레이션은 edge-tts SunHi(v1_굽기.py 와 같은 음성)."""
import sys, os, json, glob, asyncio, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

D = "G:/art2real/out/영상05/시험판"; FR = D + "/frames"; os.makedirs(FR, exist_ok=True)
BL = "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"
VOICE, SR, FPS, GAP = "ko-KR-SunHiNeural", 24000, 24, 0.55
# (카메라, 나레이션, 크게 띄울 낱말)
CUTS = [("wide", "울타리 뒤로 고양이가 지나갑니다.", ""),
        ("head", "머리는 여기 있고,", ""),
        ("tail", "꼬리는 저기 있죠.", ""),
        ("push", "그럼 이건, 아주 긴 고양이 한 마리일까요?", "몇 마리?"),
        ("top", "위에서 보면, 두 마리입니다.", "두 마리"),
        ("ghost", "가려진 몸통은 당신 뇌가 지어낸 겁니다.", ""),
        ("ghost", "이걸 아모달 완성이라고 합니다.", "아모달 완성")]

def tts(i, text):
    mp3, wav = "%s/_tts%d.mp3" % (D, i), "%s/_tts%d.wav" % (D, i)
    if not os.path.exists(wav):
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, VOICE, rate="+5%").save(mp3))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ac", "1", "-ar", str(SR), wav], check=True)
    with wave.open(wav) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16)

voices = [tts(i, c[1]) for i, c in enumerate(CUTS)]
# 마지막 두 줄은 한 컷(ghost) — 블렌더에는 합쳐서 넘긴다
ns = [int(np.ceil((len(v) / SR + GAP) * FPS)) for v in voices]
bl_cuts = []
for (cam, _, _), n in zip(CUTS, ns):
    if bl_cuts and bl_cuts[-1]["cam"] == cam: bl_cuts[-1]["n"] += n
    else: bl_cuts.append({"cam": cam, "n": n})
json.dump(bl_cuts, open(D + "/컷.json", "w", encoding="utf-8"))
still = sys.argv[1:] == ["still"]
subprocess.run([BL, "-b", "-P", "시험판_블렌더.py", "--", D + "/컷.json", D + "/bg.png", FR] + (["--still"] if still else []), check=True,
               stdout=open(D + "/_블렌더.log", "w"))
if still: sys.exit()

# 소리: 줄마다 나레이션 + 남는 칸은 쉼
aud = np.concatenate([np.pad(v, (0, n * SR // FPS - len(v))) for v, n in zip(voices, ns)])
with wave.open(D + "/_소리.wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(aud.tobytes())

F = lambda s: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", s)
def text(d, xy, s, size, fill, stroke):
    d.text(xy, s, font=F(size), fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(20, 20, 30))
frames = sorted(glob.glob(FR + "/*.png"))
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(FPS), "-i", "-",
                       "-i", D + "/_소리.wav", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-shortest", D + "/시험판.mp4"],
                      stdin=subprocess.PIPE)
k, start = 0, 0
for i, p in enumerate(frames):
    while k < len(CUTS) - 1 and i >= start + ns[k]: start += ns[k]; k += 1
    im = Image.open(p).convert("RGB"); d = ImageDraw.Draw(im)
    if CUTS[k][2]:
        pop = min(1.0, (i - start) / 5); text(d, (540, 430), CUTS[k][2], int(150 * (0.8 + 0.2 * pop)), (255, 255, 255), 10)
    text(d, (540, 1250), CUTS[k][1], 54, (255, 255, 255), 6)
    ff.stdin.write(im.tobytes())
ff.stdin.close(); ff.wait()
print(D + "/시험판.mp4", sum(ns) / FPS, "초")
