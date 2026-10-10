# 40 편 위쪽 화면 판 — 판(키, 진행 0~1) → RGBA (가로 ≤ 1000 · 세로 ≤ 760)
import glob
from PIL import Image, ImageDraw, ImageFont
T = "G:/art2real/트레일/trail10_cadrille/runs/깊이학습/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
TL = sorted(glob.glob(T + "타임랩스/*.png")); 비 = Image.open(T + "비교그림.png").convert("RGB")
def _카드(w, h, 테=(255, 255, 255)):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _타임(i):   # 타임랩스 프레임에서 두 부품 줄(선 · AI · 진짜)만
    im = Image.open(TL[i]).convert("RGB"); c = im.crop((30, 200, 1050, 900)); return c
def _막대(항목, 진행, 제목, 최대):
    c = _카드(1000, 700); d = ImageDraw.Draw(c); d.text((500, 60), 제목, font=F(52), fill=(30, 30, 40), anchor="mm")
    for j, (이름, v, 색) in enumerate(항목):
        y = 150 + j * 170; d.text((40, y + 40), 이름, font=F(44), fill=(40, 40, 50), anchor="lm")
        w = int(560 * v / 최대 * min(1, 진행 * 2.5)); d.rounded_rectangle((300, y + 5, 300 + max(w, 8), y + 75), 18, fill=색)
        d.text((310 + max(w, 8), y + 40), ("%g" % v), font=F(48), fill=(30, 30, 40), anchor="lm")
    return c
def _부품(row, col, 테):   # 비교그림.png 의 칸 하나 (줄: #4 #7 #16 #5 #25 #8 · 칸: 사람 · 바탕 · 실물 깊이 · AI 깊이)
    x = 20 + col * 230; y = 50 + row * 244; t = 비.crop((x, y, x + 210, y + 210)).resize((440, 440)); c = _카드(480, 480, 테); c.paste(t, (20, 20)); return c
def 판(키, p):
    if 키 == "결과":
        c = _타임(len(TL) - 1); return c.convert("RGBA")
    if 키 == "타임랩스":
        c = _타임(min(int(p * (len(TL) - 1) * 1.2), len(TL) - 1)); return c.convert("RGBA")
    if 키 == "점수":
        return _막대([("깎기 전", 24, (150, 150, 160)), ("AI 깊이", 32, (70, 160, 250)), ("진짜 깊이", 33, (240, 190, 60))], p, "35 개 중 통과", 35)
    if 키 == "망가짐":
        c = Image.new("RGBA", (1000, 600), (0, 0, 0, 0)); c.alpha_composite(_부품(3, 1, (200, 200, 210)), (0, 90)); c.alpha_composite(_부품(3, 3, (255, 80, 80)), (520, 90))
        d = ImageDraw.Draw(c); d.text((240, 40), "깎기 전 0.59", font=F(48), fill="white", stroke_width=6, stroke_fill=(10, 10, 20), anchor="mm"); d.text((760, 40), "AI 가 깎음 0.41", font=F(48), fill=(255, 120, 120), stroke_width=6, stroke_fill=(10, 10, 20), anchor="mm"); return c
    if 키 == "거르기":
        return _막대([("그냥 깎기", 11, (70, 160, 250)), ("확신만", 11, (150, 120, 220)), ("더 조심", 24, (255, 80, 80))], p, "부순 부품 수", 24)
    if 키 == "스무딩":
        return _막대([("그대로", .553, (70, 160, 250)), ("중앙값 펴기", .534, (150, 150, 160)), ("양방향 펴기", .519, (150, 150, 160))], p, "점수 중앙값", .6)
    if 키 == "범인":
        c = _카드(1000, 600); d = ImageDraw.Draw(c); d.text((500, 60), "AI 가 부순 11 개", font=F(52), fill=(30, 30, 40), anchor="mm")
        for j in range(11):
            x, y = 70 + (j % 6) * 150, 140 + (j // 6) * 170; 방식 = j < 8; on = 진 = min(1, p * 3) * 11 > j
            d.rounded_rectangle((x, y, x + 120, y + 120), 20, fill=((255, 90, 90) if 방식 else (70, 160, 250)) if 진 else (220, 220, 225))
        d.text((500, 520), "빨강 = 진짜 깊이로 깎아도 부서짐", font=F(40), fill=(220, 60, 60), anchor="mm"); return c
    if 키 == "다음":
        c = Image.new("RGBA", (1000, 600), (0, 0, 0, 0)); c.alpha_composite(_부품(3, 0, (200, 200, 210)), (0, 90)); c.alpha_composite(_부품(3, 2, (255, 80, 80)), (520, 90))
        d = ImageDraw.Draw(c); d.text((240, 40), "사람 부품", font=F(48), fill="white", stroke_width=6, stroke_fill=(10, 10, 20), anchor="mm"); d.text((760, 40), "진짜 깊이로 깎아도", font=F(48), fill=(255, 120, 120), stroke_width=6, stroke_fill=(10, 10, 20), anchor="mm"); return c
    raise KeyError(키)
