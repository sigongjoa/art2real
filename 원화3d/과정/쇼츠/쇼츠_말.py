# -*- coding: utf-8 -*-
"""쇼츠(말 판) — 코딩애플 식: 무심한 내레이션이 끌고 간다 (2026-09-30 「코딩애플 그런 스타일을 베이스로」).
    python 쇼츠_말.py 머리_말.tsv [부위=머리]  -> out/오메가몬2/과정/쇼츠/<편>.mp4 · <편>_0초.png
틀: 높낮이 없는 빠른 TTS(이 컴퓨터의 한국어 음성 · 밖으로 안 보냄) · 줄마다 화면 하나 · 뚝뚝 넘김(번쩍 · 흔들림 없음) · 웃길 때만 확대 · 자막은 말 그대로 아래에 · **끝은 말하다 끊는다**.
tsv 열: 그림 · 말 · 강조(그 줄에서 확대할 곳: 없음/확대) — 그림 종류: 원화:<장> · 단계:NN[:장] · 실패:NN · 비교:NN · 글:<큰 글자>"""
import os, sys, csv, json, re, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
편 = sys.argv[1]; 부위 = sys.argv[2] if len(sys.argv) > 2 else "머리"; H_ = os.path.dirname(os.path.abspath(__file__))
O = r"G:\art2real\원화3d\out\오메가몬2\과정"; F = os.path.join(O, 부위, "프레임"); 출 = os.path.join(O, "쇼츠"); 임시 = os.path.join(출, "_말"); os.makedirs(임시, exist_ok=True)
기록 = json.load(open(r"G:\art2real\원화3d\out\오메가몬2\자료\자료.json", encoding="utf-8")); W, H, FPS, SR = 1080, 1920, 30, 22050
굵 = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); 배경 = (18, 18, 20)
def 원화(t): x0, y0, x1, y1 = 기록[t]["상자"]; return Image.fromarray(cv2.imdecode(np.fromfile(기록[t]["파일"], np.uint8), cv2.IMREAD_COLOR)[y0:y1, x0:x1, ::-1])
def 모델(n, t="02_3-4"): x0, y0, x1, y1 = 기록[t]["상자"]; return Image.open(os.path.join(F, "%02d_%s.png" % (n, t))).convert("RGB").crop((x0, y0, x1, y1))
def 맞춤(im, w, h): s = min(w / im.width, h / im.height); return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
def 감싸(d, s, f, 폭):
    out, 줄 = [], ""
    for 낱 in s.split(" "):
        t = (줄 + " " + 낱).strip()
        if d.textlength(t, font=f) > 폭 and 줄: out.append(줄); 줄 = 낱
        else: 줄 = t
    return out + [줄]
def 그림(종류):
    c = Image.new("RGB", (W, H), 배경); k, _, 나 = 종류.partition(":")
    if k == "원화": m = 맞춤(원화(나), 1040, 1200); c.paste(m, ((W - m.width) // 2, 200 + (1200 - m.height) // 2))
    elif k in ("단계", "실패"):
        p = 나.split(":"); n = int(p[0]) + (90 if k == "실패" else 0); m = 맞춤(모델(n, p[1] if len(p) > 1 else "02_3-4"), 1040, 1200); c.paste(m, ((W - m.width) // 2, 200 + (1200 - m.height) // 2))
        r = 맞춤(원화(p[1] if len(p) > 1 else "02_3-4"), 300, 300); c.paste(r, (W - r.width - 24, 214))
    elif k == "비교":
        for i, t in enumerate(("02_정면", "02_3-4")):
            a, b = 맞춤(원화(t), 520, 640), 맞춤(모델(int(나), t), 520, 640); y = 200 + i * 660; c.paste(a, (14, y)); c.paste(b, (W - 14 - b.width, y))
    elif k == "파일": m = 맞춤(Image.open(나).convert("RGB"), 1040, 1200); c.paste(m, ((W - m.width) // 2, 200 + (1200 - m.height) // 2))
    elif k == "글":
        d = ImageDraw.Draw(c); f = 굵(120); 줄 = 감싸(d, 나, f, W - 140); y = 760 - len(줄) * 75
        for s in 줄: d.text(((W - d.textlength(s, font=f)) / 2, y), s, font=f, fill=(245, 245, 245)); y += 150
    return c
def 말하기(글, 파일, 속도=6):                                                                        # Windows 내장 한국어 음성(Heami) — 빠르고 평평하게
    ps = "Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.SelectVoice('Microsoft Heami Desktop'); $s.Rate=%d; $s.SetOutputToWaveFile('%s'); $s.Speak([Console]::In.ReadToEnd()); $s.Dispose()" % (속도, 파일)
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], input=글.encode("utf-8"), check=True)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", 파일, "-af", "silenceremove=stop_periods=-1:stop_duration=0.10:stop_threshold=-38dB,atempo=1.25", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout; a = np.frombuffer(raw, np.float32)
    nz = np.nonzero(np.abs(a) > 0.01)[0]; return a[max(0, nz[0] - 400):nz[-1] + 1200] if len(nz) else a      # 앞뒤 빈 소리 잘라 말끝을 빨리 끊는다
행 = list(csv.DictReader(open(os.path.join(H_, 편), encoding="utf-8"), delimiter="\t")); 소리 = []; 프레임 = []; f자 = 굵(58)
for k, r in enumerate(행):
    a = 말하기(r["말"], os.path.join(임시, "%02d.wav" % k)); 끝 = k == len(행) - 1
    if 끝: a = a[:int(len(a) * 0.62)]                                                                # 마지막 줄은 말하다 끊는다
    n = max(8, int(round(len(a) / SR * FPS))); a = np.r_[a, np.zeros(max(0, int(n / FPS * SR) - len(a)), np.float32)][:int(n / FPS * SR)]; 소리.append(a)
    base = 그림(r["그림"]); d0 = ImageDraw.Draw(base); 줄 = 감싸(d0, r["말"], f자, W - 100); y = 1500
    for s in 줄: d0.text(((W - d0.textlength(s, font=f자)) / 2, y), s, font=f자, fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0)); y += 76
    if k == 0: base.save(os.path.join(출, os.path.splitext(os.path.basename(편))[0] + "_0초.png"))
    for j in range(n):
        if (r.get("강조") or "") == "확대":                                                           # 웃길 때만: 천천히 파고든다(무표정하게)
            z = 1.0 + 0.45 * min(1.0, j / max(1, n * 0.6)); w2, h2 = int(W * z), int(H * z); cy = int(800 * z) - 800; fr = base.resize((w2, h2), Image.BILINEAR).crop(((w2 - W) // 2, cy, (w2 - W) // 2 + W, cy + H))
            d1 = ImageDraw.Draw(fr); y = 1500
            for s in 줄: d1.text(((W - d1.textlength(s, font=f자)) / 2, y), s, font=f자, fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0)); y += 76
        else: fr = base
        프레임.append(np.asarray(fr, np.uint8).tobytes())
전체 = np.concatenate(소리); wv = wave.open(os.path.join(임시, "말.wav"), "wb"); wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((np.clip(전체, -1, 1) * 32767).astype(np.int16).tobytes()); wv.close()
mp4 = os.path.join(출, os.path.splitext(os.path.basename(편))[0] + ".mp4")
p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-i", os.path.join(임시, "말.wav"), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", mp4], stdin=subprocess.PIPE)
for b in 프레임: p.stdin.write(b)
p.stdin.close(); p.wait(); print(mp4, "· 길이 %.1f초 · 줄 %d" % (len(프레임) / FPS, len(행)))
