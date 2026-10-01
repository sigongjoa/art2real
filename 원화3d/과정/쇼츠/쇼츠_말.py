# -*- coding: utf-8 -*-
"""쇼츠(말 판) — 코딩애플 식: 무심한 내레이션이 끌고 간다 (2026-09-30 「코딩애플 그런 스타일을 베이스로」).
    python 쇼츠_말.py 머리_말.tsv [부위=머리]  -> out/오메가몬2/과정/쇼츠/<편>.mp4 · <편>_0초.png
틀: 높낮이 없는 빠른 TTS(이 컴퓨터의 한국어 음성 · 밖으로 안 보냄) · 줄마다 화면 하나 · 뚝뚝 넘김(번쩍 · 흔들림 없음) · 웃길 때만 확대 · 자막은 말 그대로 아래에 · **끝은 말하다 끊는다**.
tsv 열: 그림 · 말 · 강조(없음/확대) · 라벨(그림 위 작은 설명 · 없어도 됨) — 그림 종류: 원화:<장> · 단계:NN[:장] · 실패:NN · 비교:NN · 나란히:<장>,<장> · 파일:<경로>[@x0,y0,x1,y1] · 글:<큰 글자>
10-01 판(외부 패널 ChatGPT · Grok 공통안): 위 제목 띠 + 단계 막대 · 그림 구역 1000×1140 · 자막 구역 아래 · 말 안 *낱말* 은 노랑 강조(TTS 에선 뺌) · TTS 보통 속도 + 줄 사이 쉼 · tsv 첫 줄 「#제목: …」"""
import os, sys, csv, json, re, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
편 = sys.argv[1]; 부위 = sys.argv[2] if len(sys.argv) > 2 else "머리"; H_ = os.path.dirname(os.path.abspath(__file__))
O = r"G:\art2real\원화3d\out\오메가몬2\과정"; F = os.path.join(O, 부위, "프레임"); 출 = os.path.join(O, "쇼츠"); 임시 = os.path.join(출, "_말"); os.makedirs(임시, exist_ok=True)
기록 = json.load(open(r"G:\art2real\원화3d\out\오메가몬2\자료\자료.json", encoding="utf-8")); W, H, FPS, SR = 1080, 1920, 30, 22050
굵 = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); 배경 = (18, 18, 20); 노랑 = (255, 214, 64); 회 = (85, 85, 90); 흰 = (245, 245, 245)
GX, GY, GW, GH = 0, 330, 1080, 1060; 쉼 = {",": 0.30, ".": 0.60, "줄": 0.70}                 # 그림 구역 · 쉼(초): 쉼표 뒤 · 문장 끝 · 줄 끝 — 10-01 남의 쇼츠(긱블 · 안될과학 · 코딩애플) 보고
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
def 놓기(c, im): m = 맞춤(im, GW, GH); c.paste(m, (GX + (GW - m.width) // 2, GY + (GH - m.height) // 2))
def 그림(종류):
    c = Image.new("RGB", (W, H), 배경); k, _, 나 = 종류.partition(":")
    if k == "원화": m = 맞춤(원화(나), 1040, 1200); c.paste(m, ((W - m.width) // 2, 200 + (1200 - m.height) // 2))
    elif k in ("단계", "실패"):
        p = 나.split(":"); n = int(p[0]) + (90 if k == "실패" else 0); m = 맞춤(모델(n, p[1] if len(p) > 1 else "02_3-4"), 1040, 1200); c.paste(m, ((W - m.width) // 2, 200 + (1200 - m.height) // 2))
        r = 맞춤(원화(p[1] if len(p) > 1 else "02_3-4"), 300, 300); c.paste(r, (W - r.width - 24, 214))
    elif k == "비교":
        for i, t in enumerate(("02_정면", "02_3-4")):
            a, b = 맞춤(원화(t), 520, 640), 맞춤(모델(int(나), t), 520, 640); y = 200 + i * 660; c.paste(a, (14, y)); c.paste(b, (W - 14 - b.width, y))
    elif k == "파일":
        경, _, 상 = 나.partition("@"); im = Image.open(경).convert("RGB"); 놓기(c, im.crop(tuple(int(v) for v in 상.split(","))) if 상 else im)
    elif k == "나란히":
        for i, t in enumerate(나.split(",")): m = 맞춤(원화(t), 530, GH); c.paste(m, (GX + 5 + i * 545, GY + (GH - m.height) // 2))
    elif k == "글":
        d = ImageDraw.Draw(c); f = 굵(120); 줄 = 감싸(d, 나, f, W - 140); y = 760 - len(줄) * 75
        for s in 줄: d.text(((W - d.textlength(s, font=f)) / 2, y), s, font=f, fill=(245, 245, 245)); y += 150
    return c
def 자막(d, s, f, y0):                                                                                # *낱말* 은 노랑 · 낱말 단위로 감싼다
    낱들, 켬 = [], False
    for 조 in re.split(r"(\*)", s):
        if 조 == "*": 켬 = not 켬; continue
        낱들 += [(w, 켬) for w in 조.split(" ") if w]
    줄들, 줄 = [], []
    for w in 낱들:
        if 줄 and d.textlength(" ".join(x for x, _ in 줄 + [w]), font=f) > W - 120: 줄들.append(줄); 줄 = []
        줄.append(w)
    줄들.append(줄); y = y0
    for 줄 in 줄들:
        x = (W - d.textlength(" ".join(x for x, _ in 줄), font=f)) / 2
        for w, 켬 in 줄: d.text((x, y), w, font=f, fill=노랑 if 켬 else 흰, stroke_width=4, stroke_fill=(0, 0, 0)); x += d.textlength(w + " ", font=f)
        y += int(f.size * 1.3)
def 틀(c, 제목, 라벨):                                                                                # 위 큰 제목 두 줄(긱블 · 안될과학 식) + 그림 아래 라벨
    d = ImageDraw.Draw(c); 자막(d, 제목, 굵(78), 90)
    if 라벨: f = 굵(38); tw = d.textlength(라벨, font=f); d.rounded_rectangle(((W - tw) / 2 - 22, GY + GH - 76, (W + tw) / 2 + 22, GY + GH - 16), 12, fill=(0, 0, 0)); d.text(((W - tw) / 2, GY + GH - 72), 라벨, font=f, fill=흰)
목소리 = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--목소리=")), "Heami")   # Heami(Windows 내장) 또는 edge-tts 신경망 음성 이름(ko-KR-SunHiNeural 등 · 글을 MS 서버로 보낸다)
def 말하기(글, 파일, 속도=1):                                                                        # 10-01 「말이 너무 이상해」 → edge-tts 를 고를 수 있게 · Heami 는 속도 1
    if 목소리 == "Heami":
        ps = "Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.SelectVoice('Microsoft Heami Desktop'); $s.Rate=%d; $s.SetOutputToWaveFile('%s'); $s.Speak([Console]::In.ReadToEnd()); $s.Dispose()" % (속도, 파일)
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], input=글.encode("utf-8"), check=True); 거르기 = ["-af", "silenceremove=stop_periods=-1:stop_duration=0.12:stop_threshold=-38dB"]
    else: 파일 = 파일[:-4] + ".mp3"; subprocess.run([sys.executable, "-m", "edge_tts", "--voice", 목소리, "--text", 글, "--write-media", 파일], check=True, capture_output=True); 거르기 = []
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", 파일] + 거르기 + ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout; a = np.frombuffer(raw, np.float32)
    nz = np.nonzero(np.abs(a) > 0.01)[0]; return a[max(0, nz[0] - 400):nz[-1] + 1200] if len(nz) else a      # 앞뒤 빈 소리 잘라 말끝을 빨리 끊는다
줄글 = open(os.path.join(H_, 편), encoding="utf-8").read().splitlines(); 제목 = 줄글.pop(0)[4:].strip() if 줄글[0].startswith("#제목:") else ""
행 = list(csv.DictReader(줄글, delimiter="	")); 소리 = []; 프레임 = []; f자 = 굵(60)
for k, r in enumerate(행):                                                                           # 구절마다 읽고 · 자막은 지금 구절만
    구절들 = [x for x in re.split(r"(?<=[,.?!])\s+", r["말"].strip()) if x]; 조각 = []; 자막표 = []
    for q, 구 in enumerate(구절들):
        a = 말하기(구.replace("*", ""), os.path.join(임시, "%02d_%02d.wav" % (k, q))); 끝 = 구.rstrip("*")[-1:]
        a = np.r_[a, np.zeros(int((쉼["줄"] if q == len(구절들) - 1 else 쉼.get("." if 끝 in ".?!" else ",", 0.3)) * SR), np.float32)]; 조각.append(a); 자막표 += [구] * int(round(len(a) / SR * FPS))
    n = len(자막표); 소리.append(np.r_[np.concatenate(조각), np.zeros(SR, np.float32)][:int(n / FPS * SR)])
    base = 그림(r["그림"]); 끝z = 1.25 if (r.get("강조") or "") == "확대" else 1.06       # 모든 컷이 천천히 다가온다 · 확대 줄은 더
    그 = base.crop((GX, GY, GX + GW, GY + GH))
    for j in range(n):
        z = 1.0 + (끝z - 1.0) * j / max(1, n - 1); w2, h2 = int(GW * z), int(GH * z); fr = base.copy(); fr.paste(그.resize((w2, h2), Image.BILINEAR).crop(((w2 - GW) // 2, (h2 - GH) // 2, (w2 - GW) // 2 + GW, (h2 - GH) // 2 + GH)), (GX, GY))
        틀(fr, 제목, (r.get("라벨") or "").strip()); 자막(ImageDraw.Draw(fr), 자막표[j], 굵(68), 1480)
        if j == 0 and k == 0: fr.save(os.path.join(출, os.path.splitext(os.path.basename(편))[0] + "_0초.png"))
        프레임.append(np.asarray(fr, np.uint8).tobytes())
전체 = np.concatenate(소리); wv = wave.open(os.path.join(임시, "말.wav"), "wb"); wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((np.clip(전체, -1, 1) * 32767).astype(np.int16).tobytes()); wv.close()
mp4 = os.path.join(출, os.path.splitext(os.path.basename(편))[0] + ".mp4")
p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-i", os.path.join(임시, "말.wav"), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", mp4], stdin=subprocess.PIPE)
for b in 프레임: p.stdin.write(b)
p.stdin.close(); p.wait(); print(mp4, "· 길이 %.1f초 · 줄 %d" % (len(프레임) / FPS, len(행)))
