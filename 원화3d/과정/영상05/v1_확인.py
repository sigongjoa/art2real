# -*- coding: utf-8 -*-
"""v1 영상 확인 시트: python v1_확인.py <mp4> [장 수=8] → <mp4>_qa.jpg (고르게 뽑은 프레임 · 사람이 보기 전에 내가 먼저 본다)"""
import sys, subprocess, json, os
from PIL import Image
mp4 = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout)
ims = []
for k in range(n):
    t = dur * (k + 0.5) / n; p = mp4[:-4] + "_f%d.png" % k
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "%.2f" % t, "-i", mp4, "-frames:v", "1", "-vf", "scale=640:-1", p], check=True)
    ims.append(Image.open(p).copy()); os.remove(p)
s = Image.new("RGB", (640 * 4, 360 * ((n + 3) // 4)))
for i, im in enumerate(ims): s.paste(im, ((i % 4) * 640, (i // 4) * 360))
s.save(mp4[:-4] + "_qa.jpg", quality=80); print("%s %.0f초" % (os.path.basename(mp4), dur))
