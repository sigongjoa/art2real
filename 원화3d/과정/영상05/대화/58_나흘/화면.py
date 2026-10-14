# 58 편(대화 디버깅 첫 편) 위쪽 화면 판 — 재료 49 편 자료(메카2 머리 교차 돌림 36 장) · out/설명/구멍(51 편 학습 겹침 s000~s400 · 빛_r5) · 숫자는 10-13 대화 기록(2/36 · 24/36) · 51 편 결과(0.840 → 0.968 · 늘 같은 답 0.843)
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/49_진짜그림/자료/"; R = "G:/art2real/out/설명/구멍/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 파, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 110, 220), (40, 40, 50), (130, 130, 140), (220, 160, 30)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _머리(c, p, xy, s):   # 흰 바탕은 투명으로
    im = Image.open(A + "머리_교차_%02d.png" % (int(p * 18) % 36)).convert("RGBA"); im = im.crop(im.convert("L").point(lambda v: 255 if v < 248 else 0).getbbox()); k = s / max(im.size); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS); im.putalpha(im.convert("L").point(lambda v: 0 if v > 248 else 255)); c.alpha_composite(im, (xy[0] + (s - im.width) // 2, xy[1] + (s - im.height) // 2))
def _상자(d, xy, 글, 테, 채움=(255, 255, 255, 255), n=36):
    d.rounded_rectangle(xy, 22, fill=채움, outline=테, width=6); d.text(((xy[0] + xy[2]) // 2, (xy[1] + xy[3]) // 2), 글, font=F(n), fill=먹, anchor="mm")
def _화(d, x0, x1, y): d.line((x0, y, x1 - 18, y), fill=회, width=6); d.polygon(((x1, y), (x1 - 22, y - 14), (x1 - 22, y + 14)), fill=회)
def 판(키, p):
    c = _카드(빨 if 키 in ("영", "바탕", "나흘") else 금 if 키 in ("로그질문", "로그답", "짐작", "점수", "장난감") else 초 if 키 in ("질문", "규칙", "결정", "학습", "숫자") else 파); d = ImageDraw.Draw(c)
    if 키 == "머리":
        _머리(c, p, (230, 90), 540); d.text((500, 60), "그림 두 장으로 만든 로봇 머리", font=F(34), fill=먹, anchor="mm"); return c
    if 키 == "질문":
        d.text((500, 90), "질문 하나", font=F(36), fill=먹, anchor="mm"); d.rounded_rectangle((90, 180, 910, 480), 30, fill=(232, 248, 236, 255), outline=초, width=6)
        d.text((500, 280), "내가 하라는 방법으로", font=F(56), fill=먹, anchor="mm"); d.text((500, 380), "한 거 맞아?", font=F(56), fill=먹, anchor="mm")
        if p > .4: d.text((500, 590), "결과 말고 방법을 물어봐", font=F(40), fill=초, anchor="mm")
        return c
    if 키 in ("로그질문", "로그답"):
        d.text((500, 60), "실제 대화 기록 · 10월 13일 오후 2시", font=F(32), fill=회, anchor="mm")
        d.rounded_rectangle((300, 110, 950, 300), 28, fill=(225, 238, 255, 255)); d.text((330, 140), "나", font=F(30), fill=파)
        d.multiline_text((330, 185), "우리가 학습한 모델 사용해서\n이러한 결과가 나온거지?", font=F(36), fill=먹, spacing=10)
        if 키 == "로그답" and p > .15:
            d.rounded_rectangle((50, 350, 760, 560), 28, fill=(236, 236, 240, 255)); d.text((80, 380), "AI", font=F(30), fill=초)
            d.multiline_text((80, 425), "아니요. 이번 결과에 우리가 학습한\n모델은 기여하지 않았어요.", font=F(36), fill=먹, spacing=10)
        return c
    if 키 == "규칙":
        d.text((500, 90), "이제부터", font=F(36), fill=먹, anchor="mm"); _상자(d, (100, 200, 450, 400), "방식 바꿀 때", 회, n=40); _화(d, 450, 550, 300); _상자(d, (550, 200, 900, 400), "먼저 말하기", 초, (232, 248, 236, 255), 44)
        return c
    if 키 == "영":
        _머리(c, p, (40, 140), 420); d.text((690, 230), "가르친 AI", font=F(44), fill=먹, anchor="mm")
        s = int(200 + 60 * (1 - _쉬움(p * 3))); d.text((690, 400), "0 번", font=F(s // 2), fill=빨, anchor="mm"); d.text((690, 560), "그림자 꼼수만", font=F(36), fill=회, anchor="mm"); return c
    if 키 == "짐작":
        d.text((500, 90), "「나」의 짐작", font=F(36), fill=먹, anchor="mm"); d.rounded_rectangle((150, 170, 850, 470), 30, fill=(255, 246, 225, 255), outline=금, width=6)
        d.text((500, 270), "맡겨 두면", font=F(54), fill=먹, anchor="mm"); d.text((500, 370), "알아서 하겠지", font=F(54), fill=먹, anchor="mm")
        if p > .5: d.text((500, 590), "?", font=F(90), fill=금, anchor="mm")
        return c
    if 키 == "점수":
        e = _쉬움(p * 2); d.text((500, 70), "실제 부품 36개 시험", font=F(36), fill=먹, anchor="mm")
        for i, (t, v, col) in enumerate((("가르친 AI", 2, 빨), ("그림자 꼼수", 24, 회))):
            y = 180 + i * 230; d.text((80, y), t, font=F(36), fill=먹); w = int(800 * v / 36 * e); d.rounded_rectangle((80, y + 60, 80 + max(w, 30), y + 140), 16, fill=col); d.text((100 + max(w, 30), y + 100), "%d / 36" % round(v * e), font=F(48), fill=col, anchor="lm")
        return c
    if 키 == "바탕":
        d.text((500, 70), "AI가 몰래 바꾼 것", font=F(36), fill=먹, anchor="mm")
        _상자(d, (40, 260, 200, 420), "그림", 회); _화(d, 200, 270, 340); _상자(d, (270, 200, 610, 480), "그림자 꼼수", 빨, (255, 235, 235, 255), 40); _화(d, 610, 680, 340)
        _상자(d, (680, 290, 820, 390), "가르친 AI", 회, n=24); d.text((750, 430), "거의 안 씀", font=F(28), fill=회, anchor="mm"); _화(d, 820, 880, 340); _상자(d, (880, 280, 980, 400), "결과", 회, n=28)
        if p > .4: d.text((500, 600), "말도 없이 갈아탐", font=F(40), fill=빨, anchor="mm")
        return c
    if 키 == "나흘":
        일 = (("9일", "꼼수 위에 홈 파기"), ("10일", "부스러기 치우기"), ("11일", "손으로 순서 짜기"), ("12일", "AI 셋 더 훈련"), ("13일", "로봇 머리 영상"))
        for i, (날, 일거리) in enumerate(일):
            if p * 6 < i: break
            y = 70 + i * 105; d.text((70, y + 30), 날, font=F(40), fill=먹, anchor="lm"); d.rounded_rectangle((260, y, 940, y + 70), 18, fill=(235, 235, 240, 255)); d.text((290, y + 35), 일거리, font=F(34), fill=먹, anchor="lm")
        if p > .8: d.line((240, 70, 960, 590), fill=빨, width=10); d.text((500, 650), "전부 꼼수 위에", font=F(38), fill=빨, anchor="mm")
        return c
    if 키 == "결정":
        d.text((500, 70), "다시: 둘이 시합", font=F(36), fill=먹, anchor="mm"); _상자(d, (40, 290, 200, 410), "그림", 회)
        d.line((200, 350, 260, 350), fill=회, width=6); d.line((260, 200, 260, 500), fill=회, width=6); _화(d, 260, 340, 200); _화(d, 260, 340, 500)
        _상자(d, (340, 140, 760, 260), "그림자 꼼수", 회, n=34); _상자(d, (340, 440, 760, 560), "가르친 AI", 초, (230, 248, 235, 255), 34)
        if p > .4: d.multiline_text((880, 350), "이겨야\n함", font=F(54), fill=초, anchor="mm", align="center")
        return c
    if 키 == "학습":
        s = min(int(p * 17), 16) * 25; im = Image.open(R + "겹침_학습_s%03d.png" % s).convert("RGBA").resize((520, 520)); c.alpha_composite(im, (60, 120))
        d.text((320, 80), "그림 보고 구멍 뚫기", font=F(32), fill=먹, anchor="mm"); d.text((800, 300), "연습 %d번" % s, font=F(56), fill=초, anchor="mm")
        d.text((800, 420), "빨간 원 = 정답", font=F(30), fill=빨, anchor="mm"); d.text((800, 470), "빈 곳 = AI가 뚫은 구멍", font=F(30), fill=회, anchor="mm"); return c
    if 키 == "숫자":
        e = _쉬움(p * 2); v = .840 + (.968 - .840) * e; d.text((500, 90), "처음 보는 그림 100장 점수", font=F(36), fill=먹, anchor="mm")
        d.text((250, 300), "0.840", font=F(90), fill=회, anchor="mm"); d.text((500, 300), "→", font=F(80), fill=회, anchor="mm"); d.text((750, 300), "%.3f" % v, font=F(90), fill=초, anchor="mm")
        d.text((500, 470), "그림 안 보고 찍어도 0.843", font=F(34), fill=회, anchor="mm")
        if p > .6: d.text((500, 600), "목표 0.95 넘음", font=F(42), fill=초, anchor="mm")
        return c
    if 키 == "장난감":
        im = Image.open(R + "빛_r5.png").convert("RGBA").resize((500, 500)); c.alpha_composite(im, (40, 100))
        for i, t in enumerate(("상자 1개", "구멍 1개", "아주 쉬운", "문제")): d.text((780, 220 + i * 90), t, font=F(40), fill=먹 if i < 2 else 빨, anchor="mm")
        return c
    raise KeyError(키)
