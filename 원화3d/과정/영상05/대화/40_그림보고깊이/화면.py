# 40 편 위쪽 화면 판 — 판(키, 진행 0~1) → RGBA (가로 ≤ 1000 · 세로 ≤ 760)
import glob
from PIL import Image, ImageDraw, ImageFont
T = "G:/art2real/트레일/trail10_cadrille/runs/깊이학습/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
TL = sorted(glob.glob(T + "타임랩스/*.png")); 비 = Image.open(T + "예시그림.png").convert("RGB")   # 줄 0 = #10(짐작 좋음 · 0.40→0.56) · 줄 1 = #5(짐작 좋은데 박살 0.59→0.41)
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
def _줄(cards, 제목들, 색들):   # 카드 여럿을 화살표로 잇기 (1000 폭)
    n = len(cards); w = 300 if n == 3 else 440; c = Image.new("RGBA", (1000, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(c); gap = (1000 - n * w) // max(n - 1, 1)
    for j, (k, t, col) in enumerate(zip(cards, 제목들, 색들)):
        x = j * (w + gap); c.alpha_composite(k.resize((w, w), Image.LANCZOS), (x, 90)); d.text((x + w // 2, 40), t, font=F(44), fill=col, stroke_width=6, stroke_fill=(10, 10, 20), anchor="mm")
        if j < n - 1: d.text((x + w + gap // 2, 90 + w // 2), "→", font=F(70), fill="white", stroke_width=6, stroke_fill=(10, 10, 20), anchor="mm")
    return c
def _선(i):   # 시험 부품의 앞 · 옆 · 위 선 그림(학습 입력) 한 카드에
    import numpy as np
    X = np.load(T + "시험.npz")["X"][i, 1].astype("float32"); c = _카드(480, 480); d = ImageDraw.Draw(c)
    for j, (k, t) in enumerate(((0, "앞"), (2, "옆"), (4, "위"))):
        im = Image.fromarray((255 - X[k] * 255).astype("uint8")).convert("RGB").resize((200, 200), Image.LANCZOS)
        x, y = (30, 30) if j == 0 else ((250, 30) if j == 1 else (140, 250)); c.paste(im, (x, y)); d.text((x + 10, y + 8), t, font=F(34), fill=(220, 60, 60))
    return c
def _큰(k, 테, 제목=None, 색=(255, 255, 255)):
    c = Image.new("RGBA", (1000, 680), (0, 0, 0, 0)); c.alpha_composite(k.resize((560, 560), Image.LANCZOS), (220, 100))
    if 제목: ImageDraw.Draw(c).text((500, 45), 제목, font=F(52), fill=색, stroke_width=7, stroke_fill=(10, 10, 20), anchor="mm")
    return c
def _깊이(i, 쪽=0, 색=(255, 220, 90)):   # 시험 부품의 진짜 깊이를 음영으로
    import numpy as np
    X = np.load(T + "시험.npz")["X"][i].astype("float32"); S, D = X[0, 쪽], X[3, 쪽]
    gy, gx = np.gradient(-D * 128); n = np.dstack([-gx, -gy, np.ones_like(D) * 1.5]); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    l = np.clip(n @ (np.array([-.5, -.6, .65]) / np.linalg.norm([-.5, -.6, .65])), 0, 1) * .75 + .25
    im = np.ones(D.shape + (3,)) * 245; im[S > .5] = (l[..., None] * np.array(색))[S > .5]
    c = _카드(480, 480); c.paste(Image.fromarray(im.astype("uint8")).resize((440, 440), Image.LANCZOS), (20, 20)); return c
def _선하나(i, 쪽=0):
    import numpy as np
    X = np.load(T + "시험.npz")["X"][i, 1, 쪽].astype("float32"); c = _카드(480, 480); c.paste(Image.fromarray((255 - X * 255).astype("uint8")).convert("RGB").resize((440, 440), Image.LANCZOS), (20, 20)); return c
import numpy as np
E = np.load(T + "예시10.npz"); 쪽 = 4   # 위에서 본 쪽: 두부는 납작 · 짐작엔 마디 홈 (여섯 쪽 다 그려 보고 고름)
def _음영카드(D, S, 색):
    gy, gx = np.gradient(-D * 128); n = np.dstack([-gx, -gy, np.ones_like(D) * 1.5]); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    l = np.clip(n @ (np.array([-.5, -.6, .65]) / np.linalg.norm([-.5, -.6, .65])), 0, 1) * .75 + .25
    im = np.ones(D.shape + (3,)) * 245; im[S > .5] = (l[..., None] * np.array(색))[S > .5]
    c = _카드(480, 480); c.paste(Image.fromarray(im.astype("uint8")).resize((440, 440), Image.LANCZOS), (20, 20)); return c
def _예(키, 색): return _음영카드(E[키][쪽].astype("float32"), E["S"][쪽], 색)
def _예선():
    c = _카드(480, 480); c.paste(Image.fromarray((255 - E["L"][쪽] * 255).astype("uint8")).convert("RGB").resize((440, 440), Image.LANCZOS), (20, 20)); return c
def _칸(i, 열):   # 타임랩스 프레임 i 의 첫 부품 줄에서 열(0 선 · 1 AI · 2 진짜)
    im = Image.open(TL[i]).convert("RGB"); x = 40 + 열 * 340; t = im.crop((x, 260, x + 300, 560)).resize((440, 440)); c = _카드(480, 480); c.paste(t, (20, 20)); return c
def 판(키, p):
    if 키 == "부품": return _큰(_부품(0, 0, (255, 220, 90)), None, "진짜 로봇 부품", (255, 220, 90))
    if 키 == "찍기": return _줄([_선(10), _부품(0, 1, (150, 150, 160))], ["앞 · 옆 · 위 그림", "쿠키 틀로 찍음"], [(230, 230, 230), (180, 180, 190)])
    if 키 == "두부": return _큰(_부품(0, 1, (150, 150, 160)), None, "파인 데가 없음", (255, 120, 120))
    if 키 == "짐작":
        c = _줄([_부품(0, 1, (150, 150, 160)), _부품(0, 0, (255, 220, 90))], ["그림으로 만든 것", "진짜"], [(180, 180, 190), (255, 220, 90)])
        ImageDraw.Draw(c).text((500, 330), "?", font=F(160), fill=(255, 225, 90), stroke_width=10, stroke_fill=(10, 10, 20), anchor="mm"); return c
    if 키 == "문제집":
        c = _줄([_예선(), _예("진짜", (255, 220, 90))], ["문제: 선 그림", "정답: 깊이"], [(230, 230, 230), (255, 220, 90)])
        ImageDraw.Draw(c).text((990, 505), "× 2,883 문제", font=F(40), fill="white", stroke_width=6, stroke_fill=(10, 10, 20), anchor="rs"); return c
    if 키 == "처음나중": return _줄([_예("처음", (110, 170, 255)), _예("나중", (110, 170, 255))], ["처음(두부 그대로)", "스무 번 뒤"], [(255, 120, 120), (110, 170, 255)])
    if 키 == "비교": return _줄([_예("나중", (110, 170, 255)), _예("진짜", (255, 220, 90))], ["AI 짐작", "진짜"], [(110, 170, 255), (255, 220, 90)])
    if 키 == "파냄": return _줄([_부품(0, 1, (150, 150, 160)), _부품(0, 3, (110, 170, 255)), _부품(0, 0, (255, 220, 90))], ["두부", "짐작대로 팜", "진짜"], [(180, 180, 190), (110, 170, 255), (255, 220, 90)])
    if 키 == "목표":   # #7 (비교그림 둘째 줄 · 시험 7)
        return _줄([_부품(0, 0, (255, 220, 90)), _선(10)], ["진짜 부품", "그림(선 · 앞옆위)"], [(255, 220, 90), (230, 230, 230)])
    if 키 == "바탕":
        return _줄([_선(10), _부품(0, 1, (150, 150, 160))], ["그림(선 · 앞옆위)", "윤곽 겹친 덩어리"], [(230, 230, 230), (180, 180, 190)])
    if 키 == "깎기":
        return _줄([_부품(0, 1, (150, 150, 160)), _부품(0, 2, (90, 220, 120)), _부품(0, 0, (255, 220, 90))], ["덩어리", "깊이만큼 팜", "진짜"], [(180, 180, 190), (90, 220, 120), (255, 220, 90)])
    if 키 == "결과":
        c = _타임(len(TL) - 1); return c.convert("RGBA")
    if 키 == "타임랩스":
        c = _타임(min(int(p * (len(TL) - 1) * 1.2), len(TL) - 1)); return c.convert("RGBA")
    if 키 == "점수":
        return _막대([("깎기 전", 24, (150, 150, 160)), ("AI 깊이", 32, (70, 160, 250)), ("진짜 깊이", 33, (240, 190, 60))], p, "진짜 부품과 닮음 (35 개 중)", 35)
    if 키 == "망가짐":
        c = Image.new("RGBA", (1000, 600), (0, 0, 0, 0)); c.alpha_composite(_부품(1, 1, (200, 200, 210)), (0, 90)); c.alpha_composite(_부품(1, 3, (255, 80, 80)), (520, 90))
        d = ImageDraw.Draw(c); d.text((240, 40), "파기 전", font=F(48), fill="white", stroke_width=6, stroke_fill=(10, 10, 20), anchor="mm"); d.text((760, 40), "짐작대로 팜", font=F(48), fill=(255, 120, 120), stroke_width=6, stroke_fill=(10, 10, 20), anchor="mm"); return c
    if 키 == "거르기":
        return _막대([("그냥 깎기", 11, (70, 160, 250)), ("확신만", 11, (150, 120, 220)), ("더 조심", 24, (255, 80, 80))], p, "부순 부품 수", 24)
    if 키 == "스무딩":
        return _막대([("그대로", .553, (70, 160, 250)), ("중앙값 펴기", .534, (150, 150, 160)), ("양방향 펴기", .519, (150, 150, 160))], p, "점수 중앙값", .6)
    if 키 == "범인":
        c = _카드(1000, 600); d = ImageDraw.Draw(c); d.text((500, 60), "박살 난 11 개", font=F(52), fill=(30, 30, 40), anchor="mm")
        for j in range(11):
            x, y = 70 + (j % 6) * 150, 140 + (j // 6) * 170; 방식 = j < 8; on = 진 = min(1, p * 3) * 11 > j
            d.rounded_rectangle((x, y, x + 120, y + 120), 20, fill=((255, 90, 90) if 방식 else (70, 160, 250)) if 진 else (220, 220, 225))
        d.text((500, 520), "빨강 = 정답대로 파도 박살 → 칼 탓", font=F(40), fill=(220, 60, 60), anchor="mm"); return c
    if 키 == "다음":
        c = Image.new("RGBA", (1000, 600), (0, 0, 0, 0)); c.alpha_composite(_부품(1, 0, (200, 200, 210)), (0, 90)); c.alpha_composite(_부품(1, 2, (255, 80, 80)), (520, 90))
        d = ImageDraw.Draw(c); d.text((240, 40), "사람 부품", font=F(48), fill="white", stroke_width=6, stroke_fill=(10, 10, 20), anchor="mm"); d.text((760, 40), "정답대로 파도", font=F(48), fill=(255, 120, 120), stroke_width=6, stroke_fill=(10, 10, 20), anchor="mm"); return c
    raise KeyError(키)
