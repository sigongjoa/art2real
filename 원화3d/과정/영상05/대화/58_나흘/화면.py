# 58 편(대화 디버깅 첫 편) 위쪽 화면 판 8판 — 남색 템플릿 톤(51 편 템플릿.json 색) · 「막내」 = 훈련시킨 모델(아이콘) · 「꼼수」 = 그림자 겹치기(49 편 머리_겹침 돌림)
# 재료: 49 편 자료(머리_교차 · 머리_겹침 36 장) · out/설명/구멍(51 편 겹침_학습 s000~s400 · 빛_r5) · 숫자: 10-13 대화 기록(2/36 · 24/36) · 51 편(0.840 → 0.968 · 찍기 0.843)
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
A = "G:/art2real/out/영상05/대화/49_진짜그림/자료/"; R = "G:/art2real/out/설명/구멍/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
바탕, 칸, 테, 글, 흐림 = (14, 22, 42), (24, 34, 60), (44, 58, 92), (236, 242, 250), (110, 126, 160)
하늘, 빨, 초, 금 = (64, 196, 255), (255, 96, 96), (90, 220, 120), (255, 200, 80)
def _카드(색, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); g = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle((6, 6, w - 7, h - 7), 36, outline=색 + (200,), width=14)
    c.alpha_composite(g.filter(ImageFilter.GaussianBlur(8))); d = ImageDraw.Draw(c); d.rounded_rectangle((6, 6, w - 7, h - 7), 36, fill=바탕 + (255,), outline=색 + (255,), width=5)
    for x in range(40, w - 20, 60): d.line((x, 20, x, h - 20), fill=(20, 30, 54, 255))
    for y in range(40, h - 20, 60): d.line((20, y, w - 20, y), fill=(20, 30, 54, 255))
    return c
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _제목(d, t, 색=하늘): d.text((500, 58), t, font=F(38), fill=색, anchor="mm")
def _투명(im):   # 흰 바탕을 투명으로 · 흰 가장자리 잘라냄
    im = im.convert("RGBA"); im = im.crop(im.convert("L").point(lambda v: 255 if v < 248 else 0).getbbox()); im.putalpha(im.convert("L").point(lambda v: 0 if v > 248 else 255)); return im
def _붙(c, im, xy, s, a=1.0):
    k = s / max(im.size); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    if a < 1: im.putalpha(im.split()[3].point(lambda v: int(v * a)))
    c.alpha_composite(im, (int(xy[0] + (s - im.width) / 2), int(xy[1] + (s - im.height) / 2)))
def _머리(c, p, xy, s, a=1.0): _붙(c, _투명(Image.open(A + "머리_교차_%02d.png" % (int(p * 18) % 36))), xy, s, a)
def _꼼수(c, p, xy, s, a=1.0): _붙(c, _투명(Image.open(A + "머리_겹침_%02d.png" % (int(p * 18 + 5) % 36))), xy, s, a)
def _막내(c, xy, s, 꺼짐=False, 웃음=False):   # 훈련시킨 모델 아이콘: 노란 네모 로봇
    t = Image.new("RGBA", (200, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(t); 몸 = (120, 120, 130) if 꺼짐 else 금; 눈 = (70, 70, 80) if 꺼짐 else 하늘
    d.line((100, 40, 100, 14), fill=몸, width=8); d.ellipse((88, 2, 112, 26), fill=몸); d.rounded_rectangle((30, 40, 170, 150), 34, fill=몸)
    d.rounded_rectangle((48, 66, 152, 124), 22, fill=(30, 34, 52))
    if 꺼짐: d.line((66, 95, 86, 95), fill=눈, width=8); d.line((114, 95, 134, 95), fill=눈, width=8)
    elif 웃음: d.arc((62, 80, 90, 108), 200, 340, fill=눈, width=8); d.arc((110, 80, 138, 108), 200, 340, fill=눈, width=8)
    else: d.ellipse((64, 82, 88, 106), fill=눈); d.ellipse((112, 82, 136, 106), fill=눈)
    d.rounded_rectangle((62, 158, 138, 214), 18, fill=몸); c.alpha_composite(t.resize((s, int(s * 1.1)), Image.LANCZOS), xy)
def _이름표(d, xy, t, 색): w = d.textlength(t, font=F(34)); d.rounded_rectangle((xy[0] - w / 2 - 18, xy[1] - 28, xy[0] + w / 2 + 18, xy[1] + 28), 18, fill=색); d.text(xy, t, font=F(34), fill=바탕, anchor="mm")
def 판(키, p):
    c = _카드(빨 if 키 in ("영", "바탕", "나흘") else 금 if 키 in ("로그질문", "로그답", "점수", "장난감") else 초 if 키 in ("질문", "규칙", "결정", "학습", "숫자") else 하늘); d = ImageDraw.Draw(c)
    if 키 == "머리":
        _머리(c, p, (240, 110), 520); _제목(d, "그림 두 장 → 로봇 머리"); return c
    if 키 == "영":   # 막내는 꺼져 있고 결과는 꼼수가 냄
        _머리(c, p, (60, 150), 380); _막내(c, (600, 120), 200, 꺼짐=True); _이름표(d, (700, 380), "막내", 흐림)
        s = int(150 - 50 * _쉬움(p * 3)); d.text((700, 510), "출전 0번", font=F(max(s // 2, 50)), fill=빨, anchor="mm"); _제목(d, "이 머리, 누가 만들었나"); return c
    if 키 in ("로그질문", "로그답"):   # 실제 대화 기록 원문
        _제목(d, "실제 대화 기록 · 10월 13일 오후 2시", 흐림)
        d.rounded_rectangle((330, 110, 950, 300), 28, fill=(40, 90, 170, 255)); d.text((360, 140), "나", font=F(30), fill=하늘)
        d.multiline_text((360, 185), "우리가 학습한 모델 사용해서\n이러한 결과가 나온거지?", font=F(38), fill=글, spacing=10)
        if 키 == "로그답" and p > .15:
            d.rounded_rectangle((50, 350, 790, 560), 28, fill=칸 + (255,), outline=테, width=3); d.text((80, 380), "AI", font=F(30), fill=초)
            d.multiline_text((80, 425), "아니요. 이번 결과에 우리가 학습한\n모델은 기여하지 않았어요.", font=F(38), fill=글, spacing=10)
        return c
    if 키 == "점수":   # 36 개 점 두 줄: 막내 2 · 꼼수 24
        e = _쉬움(p * 1.6); _제목(d, "실제 부품 36개 시험")
        for j, (t, v, col) in enumerate((("막내", 2, 금), ("꼼수", 24, 하늘))):
            y = 150 + j * 260
            if j == 0: _막내(c, (40, y), 110)
            else: _꼼수(c, p, (40, y), 120)
            _이름표(d, (95, y + 160), t, col)
            for k in range(36):
                x0, y0 = 190 + (k % 12) * 56, y + (k // 12) * 60; 맞 = k < round(v * e)
                d.ellipse((x0, y0, x0 + 46, y0 + 46), fill=(col if 맞 else 칸) + (255,), outline=테, width=2)
            d.text((960, y + 90), "%d" % round(v * e), font=F(70), fill=col, anchor="rm")
        return c
    if 키 == "바탕":   # 막내는 구석에서 꺼짐 · 꼼수가 길을 차지
        _제목(d, "AI가 몰래 바꾼 것", 빨); _꼼수(c, p, (330, 140), 340); _이름표(d, (500, 520), "꼼수", 하늘)
        _막내(c, (60, 330), 130, 꺼짐=True); _이름표(d, (125, 520), "막내", 흐림); d.text((125, 300), "z z", font=F(40), fill=흐림, anchor="mm")
        _머리(c, p, (740, 230), 220); d.text((690, 340), "→", font=F(70), fill=흐림, anchor="mm")
        if p > .4: d.text((500, 630), "말도 없이 갈아탐", font=F(44), fill=빨, anchor="mm")
        return c
    if 키 == "나흘":   # 달력 다섯 칸이 하나씩 · 끝에 도장
        _제목(d, "그 위에 쌓은 나흘", 빨)
        for i, (날, 일) in enumerate((("9", "홈 파기"), ("10", "부스러기"), ("11", "순서 짜기"), ("12", "훈련 셋"), ("13", "머리 영상"))):
            if p * 6 < i: break
            x = 40 + i * 188; d.rounded_rectangle((x, 140, x + 168, 420), 20, fill=칸 + (255,), outline=테, width=3); d.rounded_rectangle((x, 140, x + 168, 190), 20, fill=빨)
            d.text((x + 84, 165), "10월", font=F(28), fill=바탕, anchor="mm"); d.text((x + 84, 270), 날, font=F(90), fill=글, anchor="mm"); d.text((x + 84, 375), 일, font=F(28), fill=흐림, anchor="mm")
        if p > .75:
            s = Image.new("RGBA", (560, 150), (0, 0, 0, 0)); sd = ImageDraw.Draw(s); sd.rounded_rectangle((5, 5, 555, 145), 20, outline=빨, width=10); sd.text((280, 75), "전부 꼼수 위", font=F(70), fill=빨, anchor="mm")
            s = s.rotate(-8, expand=True, resample=Image.BICUBIC); c.alpha_composite(s, (500 - s.width // 2, 470))
        return c
    if 키 == "결정":   # 막내 VS 꼼수
        _제목(d, "다시: 막내 VS 꼼수", 초); _막내(c, (90, 150), 260, 웃음=p > .5); _이름표(d, (220, 490), "막내", 금)
        _꼼수(c, p, (620, 150), 300); _이름표(d, (770, 490), "꼼수", 하늘)
        k = 1 + .15 * math.sin(p * 12) * (1 - p); d.text((500, 320), "VS", font=F(int(120 * k)), fill=빨, anchor="mm", stroke_width=6, stroke_fill=바탕)
        if p > .4: d.text((500, 610), "막내가 이겨야 한다", font=F(44), fill=초, anchor="mm")
        return c
    if 키 == "규칙":
        _제목(d, "이제부터", 초); d.rounded_rectangle((90, 170, 910, 470), 30, fill=칸 + (255,), outline=초, width=6)
        d.text((500, 260), "방식 바꿀 거면", font=F(60), fill=글, anchor="mm"); d.text((500, 370), "먼저 말해", font=F(80), fill=초, anchor="mm"); return c
    if 키 == "학습":   # 막내가 그림 보고 구멍 뚫는 연습
        s = min(int(p * 17), 16) * 25; im = Image.open(R + "겹침_학습_s%03d.png" % s).convert("RGBA").resize((500, 500)); c.alpha_composite(im, (50, 130))
        _제목(d, "막내가 그림 보고 구멍 뚫기", 초); _막내(c, (680, 140), 160, 웃음=s >= 200); d.text((760, 400), "연습 %d번" % s, font=F(54), fill=초, anchor="mm")
        d.text((760, 490), "빨간 원 = 정답", font=F(30), fill=빨, anchor="mm"); d.text((760, 540), "빈 곳 = 막내가 뚫은 구멍", font=F(28), fill=흐림, anchor="mm"); return c
    if 키 == "숫자":
        e = _쉬움(p * 2); v = .840 + (.968 - .840) * e; _제목(d, "처음 보는 그림 100장 점수", 초)
        d.text((260, 300), "0.840", font=F(96), fill=흐림, anchor="mm"); d.text((500, 300), "→", font=F(80), fill=흐림, anchor="mm"); d.text((750, 300), "%.3f" % v, font=F(110), fill=초, anchor="mm")
        d.text((500, 460), "그림 안 보고 찍어도 0.843", font=F(36), fill=흐림, anchor="mm")
        if p > .6: _막내(c, (440, 520), 110, 웃음=True)
        return c
    if 키 == "장난감":
        im = Image.open(R + "빛_r5.png").convert("RGBA").resize((520, 520)); c.alpha_composite(im, (40, 120)); _제목(d, "근데 이 문제는", 금)
        for i, (t, col) in enumerate((("상자 1개", 글), ("구멍 1개", 글), ("아주 쉬운 문제", 금))): d.text((780, 260 + i * 110), t, font=F(48 if i < 2 else 44), fill=col, anchor="mm")
        return c
    if 키 == "질문":
        _제목(d, "질문 하나", 초); d.rounded_rectangle((90, 160, 910, 470), 30, fill=칸 + (255,), outline=초, width=6)
        d.text((500, 260), "내가 하라는 방법으로", font=F(58), fill=글, anchor="mm"); d.text((500, 370), "한 거 맞아?", font=F(70), fill=초, anchor="mm")
        if p > .4: d.text((500, 590), "결과 말고 방법을 물어봐", font=F(40), fill=하늘, anchor="mm")
        return c
    raise KeyError(키)
