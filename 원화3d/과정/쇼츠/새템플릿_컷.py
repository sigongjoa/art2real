# -*- coding: utf-8 -*-
"""새 쇼츠 템플릿 정지 컷 시안(10-08 · 굽지 않음) — 조사 claudedocs/research_쇼츠템플릿_20261008.md 의 1~4 번을 34 편 재료로.
현재 템플릿 1 컷 + 새 컷 4 개 → out/쇼츠/교사/_새템플릿.png"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
P = "G:/art2real/원화3d/out/쇼츠/교사/"; Q = "G:/claude-faceless-shorts-creator/remotion/out/qa/"
BH = lambda n: ImageFont.truetype("C:/Users/zesky/AppData/Local/Temp/claude/G--art2real/259f23f2-edc9-4277-85f4-fd324dc7cd8f/scratchpad/BlackHanSans.ttf", n)
KR = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
W, H = 1080, 1920; Y = (255, 232, 58)

def full(src, crop=None, zoom=1.0):   # 그림을 전체 화면으로: 뒤는 같은 그림 흐리게 채움, 앞은 크게
    im = Image.open(P + src).convert("RGB")
    if crop: im = im.crop(crop)
    bg = im.resize((W, int(W * im.height / im.width))).resize((int(H * im.width / im.height), H)).filter(ImageFilter.GaussianBlur(40))
    c = Image.new("RGB", (W, H)); c.paste(bg, ((W - bg.width) // 2, 0)); c = Image.blend(c, Image.new("RGB", (W, H)), 0.45)
    w = int(W * zoom); fg = im.resize((w, int(w * im.height / im.width))); c.paste(fg, ((W - w) // 2, (H - fg.height) // 2 - 60)); return c
def text(c, s, y, size, fill=(255, 255, 255), font=BH, box=False):
    d = ImageDraw.Draw(c); f = font(size); bb = d.textbbox((W // 2, y), s, font=f, anchor="mm")
    if box: d.rounded_rectangle((bb[0] - 24, bb[1] - 14, bb[2] + 24, bb[3] + 14), 14, fill=(0, 0, 0))
    d.text((W // 2, y), s, font=f, fill=fill, anchor="mm", stroke_width=0 if box else 10, stroke_fill=(0, 0, 0))
def cap(c, words, hi):   # 자막: 가운데 아래 · 1~3 낱말 · 핵심어 노랑
    d = ImageDraw.Draw(c); f = KR(78); x = W // 2; ws = words.split(); tw = sum(d.textlength(w + " ", font=f) for w in ws); x0 = x - tw / 2
    d.rounded_rectangle((x0 - 24, 1215, x0 + tw + 10, 1325), 12, fill=(0, 0, 0))
    for w in ws: d.text((x0, 1270), w, font=f, fill=Y if w in hi else (255, 255, 255), anchor="lm"); x0 += d.textlength(w + " ", font=f)
def bar(c, p, n=None):   # 위쪽 진행바 + 카운터
    d = ImageDraw.Draw(c); d.rectangle((0, 0, W, 14), fill=(60, 60, 60)); d.rectangle((0, 0, int(W * p), 14), fill=Y)
    if n: d.rounded_rectangle((W - 230, 40, W - 30, 120), 16, fill=(0, 0, 0)); d.text((W - 130, 80), n, font=BH(56), fill=Y, anchor="mm")
def stamp(c, ok, xy, s=220):
    d = ImageDraw.Draw(c); x, y = xy; col = (40, 210, 90) if ok else (235, 45, 45)
    if ok: d.ellipse((x, y, x + s, y + s), outline=col, width=28)
    else: d.line((x, y, x + s, y + s), fill=col, width=30); d.line((x + s, y, x, y + s), fill=col, width=30)
def label(c, s, t):   # 왼쪽 위 「소리」 표시(시안에서만 — 실제엔 효과음)
    d = ImageDraw.Draw(c); d.rounded_rectangle((30, 1500, 30 + 30 + d.textlength(s, font=KR(40)), 1570), 12, fill=(30, 90, 200)); d.text((45, 1535), s, font=KR(40), fill="white", anchor="lm")
    d.text((W // 2, 1640), t, font=KR(36), fill=(170, 170, 170), anchor="mm")

cuts = []
now = Image.open(Q + "Short58Claudecode-f0453.png").convert("RGB").resize((W, H)); ImageDraw.Draw(now).text((W // 2, 1650), "지금 템플릿", font=KR(60), fill=(255, 120, 120), anchor="mm"); cuts.append(now)
# 0.0 초 훅: 결과부터 · 큰 질문 · 제목 글자 없음
c = full("34_실패10.png", zoom=1.0); text(c, "AI 가 0점 받은 부품", 330, 112, Y); text(c, "Claude 한테 줬더니?", 1300, 96)
bar(c, 0.02); label(c, "♪ 쿵 + 배경음 시작", "0.0초 · 결과부터 · 제목 글자 없이 질문"); cuts.append(c)
# 6 초: 전체 화면 · 펀치 줌 · O 팝 · 카운터
c = full("34_공막대.png", crop=(500, 120, 1000, 700), zoom=1.0); cap(c, "한 번에 똑같이", {"똑같이"}); bar(c, 0.12, "1/6")
label(c, "♪ 띵", "6초 · Claude 쪽만 확 당겨서 · O 팝 · 1/6"); cuts.append(c)
# 20 초: 틀린 곳을 짚기 — 확대 + 빨간 원
c = full("34_엉덩이.png", zoom=1.0); d = ImageDraw.Draw(c); d.ellipse((150, 950, 400, 1180), outline=(40, 210, 90), width=12); d.ellipse((680, 950, 930, 1180), outline=(235, 45, 45), width=12)
text(c, "공 관절 있음        → 없음", 1420, 58, (255, 255, 255)); cap(c, "공 관절이 사라졌어요", {"사라졌어요"}); bar(c, 0.36, "4/6")
label(c, "♪ 삐", "20초 · 틀린 곳을 원으로 짚음 · X 팝"); cuts.append(c)
# 40 초: 숫자 대결 카운터
c = Image.new("RGB", (W, H), (14, 14, 18)); text(c, "채점기", 560, 90, (200, 200, 200)); text(c, "9 / 10", 760, 230, (40, 210, 90))
text(c, "내 눈", 1010, 90, (200, 200, 200)); text(c, "7 / 10", 1210, 230, (235, 45, 45)); bar(c, 0.8)
label(c, "♪ 숫자 오르는 소리 → 쿵", "40초 · 숫자가 0 부터 올라감 · 반전"); cuts.append(c)

s = 0.36; sheet = Image.new("RGB", (int(W * s) * 5 + 40, int(H * s)), (40, 40, 40))
for i, c in enumerate(cuts): sheet.paste(c.resize((int(W * s), int(H * s))), (i * (int(W * s) + 10), 0))
sheet.save(P + "_새템플릿.png"); print(sheet.size)
