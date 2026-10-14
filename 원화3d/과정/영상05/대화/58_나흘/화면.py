# 58 편 위쪽 화면 판 9판 — 도표만(사용자 10-14 「도표 안에 대화를 넣으면 이게 도표냐」 · 「막내 · 출전 0번 이런 거 하지 마」) · 글은 짧은 이름표만 · 남색 톤
# 재료: 49 편 자료(머리_교차 · 머리_앞그림 · 머리_옆그림) · out/설명/구멍(51 편 겹침_학습 · 빛_r5) · 곡선 = 실험_20261013/구멍/스냅26.json(17 점 · 찍기 0.843) · 점수 2/36 · 24/36(10-09)
import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
A = "G:/art2real/out/영상05/대화/49_진짜그림/자료/"; R = "G:/art2real/out/설명/구멍/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
S = json.load(open("G:/art2real/원화3d/실험_20261013/구멍/스냅26.json", encoding="utf-8"))
바탕, 칸, 테, 글, 흐림 = (14, 22, 42), (24, 34, 60), (44, 58, 92), (236, 242, 250), (110, 126, 160)
하늘, 빨, 초, 금 = (64, 196, 255), (255, 96, 96), (90, 220, 120), (255, 200, 80)
def _카드(색, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); g = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle((6, 6, w - 7, h - 7), 36, outline=색 + (200,), width=14)
    c.alpha_composite(g.filter(ImageFilter.GaussianBlur(8))); d = ImageDraw.Draw(c); d.rounded_rectangle((6, 6, w - 7, h - 7), 36, fill=바탕 + (255,), outline=색 + (255,), width=5)
    for x in range(40, w - 20, 60): d.line((x, 20, x, h - 20), fill=(20, 30, 54, 255))
    for y in range(40, h - 20, 60): d.line((20, y, w - 20, y), fill=(20, 30, 54, 255))
    return c
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _투명(im):
    im = im.convert("RGBA"); im = im.crop(im.convert("L").point(lambda v: 255 if v < 248 else 0).getbbox()); im.putalpha(im.convert("L").point(lambda v: 0 if v > 248 else 255)); return im
def _붙(c, im, xy, s):
    k = s / max(im.size); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS); c.alpha_composite(im, (int(xy[0] + (s - im.width) / 2), int(xy[1] + (s - im.height) / 2)))
def _머리(c, p, xy, s): _붙(c, _투명(Image.open(A + "머리_교차_%02d.png" % (int(p * 18) % 36))), xy, s)
def _마디(d, xy, t, 색, 꺼짐=False, n=34):   # 상자 마디 · 꺼지면 점선 회색 + X
    x0, y0, x1, y1 = xy
    if 꺼짐:
        for x in range(x0, x1, 24): d.line((x, y0, min(x + 12, x1), y0), fill=흐림, width=4); d.line((x, y1, min(x + 12, x1), y1), fill=흐림, width=4)
        for y in range(y0, y1, 24): d.line((x0, y, x0, min(y + 12, y1)), fill=흐림, width=4); d.line((x1, y, x1, min(y + 12, y1)), fill=흐림, width=4)
        d.text(((x0 + x1) // 2, (y0 + y1) // 2), t, font=F(n), fill=흐림, anchor="mm"); d.line((x0 + 10, y0 + 10, x1 - 10, y1 - 10), fill=빨, width=6); d.line((x0 + 10, y1 - 10, x1 - 10, y0 + 10), fill=빨, width=6); return
    d.rounded_rectangle(xy, 20, fill=칸 + (255,), outline=색, width=5); d.text(((x0 + x1) // 2, (y0 + y1) // 2), t, font=F(n), fill=글, anchor="mm")
def _화(d, a, b, 색=흐림, 점선=False):
    (x0, y0), (x1, y1) = a, b; L = max(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** .5, 1); ux, uy = (x1 - x0) / L, (y1 - y0) / L; e = (x1 - ux * 20, y1 - uy * 20)
    if 점선:
        for t in range(0, int(L - 20), 22): d.line((x0 + ux * t, y0 + uy * t, x0 + ux * min(t + 12, L - 20), y0 + uy * min(t + 12, L - 20)), fill=색, width=6)
    else: d.line((x0, y0, e[0], e[1]), fill=색, width=6)
    d.polygon(((x1, y1), (e[0] - uy * 14, e[1] + ux * 14), (e[0] + uy * 14, e[1] - ux * 14)), fill=색)
def _길(c, d, p, 실제):   # 그림 → (모델 | 그림자 겹치기) → 머리
    _붙(c, _투명(Image.open(A + "머리_앞그림.png")), (30, 250), 150); d.text((105, 430), "그림", font=F(30), fill=흐림, anchor="mm")
    _마디(d, (300, 140, 600, 250), "모델", 금, 꺼짐=실제 and p > .2); _마디(d, (300, 450, 600, 560), "그림자 겹치기", 하늘 if 실제 else 테, n=32)
    _화(d, (190, 300), (295, 200), 금 if not 실제 else 흐림, 점선=실제); _화(d, (190, 360), (295, 500), 하늘 if 실제 else 흐림, 점선=not 실제)
    _화(d, (605, 200), (740, 300), 금 if not 실제 else 흐림, 점선=실제); _화(d, (605, 500), (740, 380), 하늘 if 실제 else 흐림, 점선=not 실제); _머리(c, p, (740, 220), 220)
    d.text((500, 58), "실제로 간 길" if 실제 else "하라고 한 길", font=F(36), fill=빨 if 실제 else 금, anchor="mm")
def _선로(d, p, 나흘):   # 시간축 두 선로: 위 = 모델 · 아래 = 그림자 겹치기 · 10/9 에 아래로 꺾임
    X = lambda 일: 120 + (일 - 8) * 150; 위, 아래 = 230, 470
    d.text((60, 위), "모델", font=F(30), fill=금, anchor="lm"); d.text((60, 아래 + 60), "그림자 겹치기", font=F(30), fill=하늘, anchor="lm")
    d.line((X(8) + 40, 위, X(9), 위), fill=금, width=12); e = _쉬움(p * 2) if not 나흘 else 1
    d.line((X(9), 위, X(9) + 60 * e, 위 + (아래 - 위) * e), fill=빨, width=12)
    for x in range(int(X(9)), X(13) + 40, 30): d.line((x, 위, x + 14, 위), fill=흐림, width=5)
    끝 = X(9) + 60 + (X(13) + 40 - X(9) - 60) * (_쉬움(p * 1.3) if 나흘 else 0)
    if e >= 1: d.line((X(9) + 60, 아래, 끝, 아래), fill=하늘, width=12)
    for 일 in range(8, 14): d.line((X(일), 아래 + 120, X(일), 아래 + 132), fill=흐림, width=3); d.text((X(일), 아래 + 158), "10/%d" % 일, font=F(26), fill=흐림, anchor="mm")
    d.ellipse((X(9) - 16, 위 - 16, X(9) + 16, 위 + 16), fill=빨)
    if 나흘:
        for i, t in enumerate(("홈 파기", "부스러기", "순서", "훈련 셋", "머리 영상")):
            x = X(9) + 110 + i * 140
            if x < 끝: d.ellipse((x - 10, 아래 - 10, x + 10, 아래 + 10), fill=글); d.text((x, 아래 - 40), t, font=F(24), fill=글, anchor="mm")
def 판(키, p):
    c = _카드(빨 if 키 in ("실제길", "갈림", "나흘", "비교") else 금 if 키 in ("요청길", "점수1", "점수2", "장난감") else 초 if 키 in ("결정", "확인", "학습", "곡선") else 하늘); d = ImageDraw.Draw(c)
    if 키 == "머리":
        _머리(c, p, (240, 90), 540); return c
    if 키 == "입력":   # 앞 · 옆 그림 → 머리
        for j, (f, t) in enumerate((("머리_앞그림.png", "앞"), ("머리_옆그림.png", "옆"))): _붙(c, _투명(Image.open(A + f)), (40 + j * 260, 160), 230); d.text((155 + j * 260, 430), t, font=F(32), fill=흐림, anchor="mm")
        _화(d, (560, 280), (640, 280)); _머리(c, p, (650, 120), 320); return c
    if 키 in ("요청길", "실제길"): _길(c, d, p, 키 == "실제길"); return c
    if 키 in ("점수1", "점수2"):   # 36 칸 점: 모델 2 · 그림자 겹치기 24
        d.text((500, 58), "실제 부품 36개", font=F(36), fill=흐림, anchor="mm")
        for j, (t, v, col) in enumerate((("모델", 2, 금), ("그림자 겹치기", 24, 하늘))):
            if j == 1 and 키 == "점수1": break
            e = _쉬움(p * 1.6) if (j == 0) == (키 == "점수1") else 1; y = 140 + j * 270; d.text((60, y), t, font=F(32), fill=col)
            for k in range(36):
                x0, y0 = 60 + (k % 12) * 64, y + 55 + (k // 12) * 60; d.ellipse((x0, y0, x0 + 48, y0 + 48), fill=(col if k < round(v * e) else 칸) + (255,), outline=테, width=2)
            d.text((950, y + 140), "%d" % round(v * e), font=F(80), fill=col, anchor="rm")
        return c
    if 키 in ("갈림", "나흘"): _선로(d, p, 키 == "나흘"); return c
    if 키 == "결정":   # 같은 그림을 둘 다 풀게 · 모델 막대가 겹치기 선을 넘어야
        d.text((500, 58), "둘 다 풀게 해서 비교", font=F(36), fill=초, anchor="mm"); 바닥 = 600
        for j, (t, v, col) in enumerate((("그림자 겹치기", 24, 하늘), ("모델", 2, 금))):
            x = 220 + j * 380; h = int(420 * v / 36 * (_쉬움(p * 2) if j == 0 else 1)); d.rounded_rectangle((x, 바닥 - max(h, 8), x + 180, 바닥), 14, fill=col); d.text((x + 90, 바닥 + 40), t, font=F(30), fill=col, anchor="mm")
        y = 바닥 - 420 * 24 / 36
        for x in range(160, 860, 30): d.line((x, y, x + 16, y), fill=하늘, width=4)
        if p > .4: _화(d, (690, 바닥 - 30), (690, y - 40), 초)
        return c
    if 키 == "확인":   # 갈림길 앞에 확인 마디
        _선로(d, 0, False); X9 = 270; d.polygon(((X9, 70), (X9 + 60, 130), (X9, 190), (X9 - 60, 130)), fill=초); d.text((X9, 130), "확인", font=F(28), fill=바탕, anchor="mm")
        _화(d, (X9, 190), (X9, 210), 초); return c
    if 키 == "학습":
        s = min(int(p * 17), 16) * 25; im = Image.open(R + "겹침_학습_s%03d.png" % s).convert("RGBA").resize((500, 500)); c.alpha_composite(im, (60, 130))
        d.text((780, 300), "%d" % s, font=F(90), fill=초, anchor="mm"); d.text((780, 380), "걸음", font=F(32), fill=흐림, anchor="mm")
        d.ellipse((690, 470, 720, 500), outline=빨, width=5); d.text((735, 485), "정답", font=F(28), fill=빨, anchor="lm"); return c
    if 키 == "곡선":   # 스냅26 실제 곡선 · 찍기 0.843 · 목표 0.95
        x0, x1, y0, y1 = 130, 940, 600, 120; Y = lambda v: y0 - (v - .80) / .20 * (y0 - y1); X = lambda g: x0 + g / 400 * (x1 - x0)
        d.line((x0, y0, x1, y0), fill=테, width=3); d.line((x0, y0, x0, y1), fill=테, width=3)
        for v in (.8, .9, 1.0): d.text((x0 - 15, Y(v)), "%.1f" % v, font=F(26), fill=흐림, anchor="rm")
        for v, col, t in ((S["평균맞히기"], 흐림, "찍기"), (.95, 초, "목표")):
            for x in range(x0, x1, 26): d.line((x, Y(v), x + 14, Y(v)), fill=col, width=4)
            d.text((x0 + 15, Y(v) + (18 if t == "찍기" else -18)), t, font=F(28), fill=col, anchor="lm")
        n = max(2, int(len(S["스냅"]) * _쉬움(p * 1.4))); pts = [(X(s["걸음"]), Y(s["시험IoU"])) for s in S["스냅"][:n]]; d.line(pts, fill=금, width=8, joint="curve")
        d.ellipse((pts[-1][0] - 10, pts[-1][1] - 10, pts[-1][0] + 10, pts[-1][1] + 10), fill=금); d.text((pts[-1][0], pts[-1][1] - 40), "%.3f" % S["스냅"][n - 1]["시험IoU"], font=F(40), fill=금, anchor="mm")
        d.text((500, 650), "걸음", font=F(26), fill=흐림, anchor="mm"); return c
    if 키 == "장난감":
        im = Image.open(R + "빛_r5.png").convert("RGBA").resize((560, 560)); c.alpha_composite(im, (220, 80)); return c
    if 키 == "비교":   # 하라고 한 길 vs 실제로 간 길 축소
        for j, 실제 in enumerate((False, True)):
            t = Image.new("RGBA", (1000, 700), (0, 0, 0, 0)); _길(t, ImageDraw.Draw(t), .5, 실제); t = t.resize((480, 336), Image.LANCZOS); c.alpha_composite(t, (15 + j * 495, 180))
        return c
    raise KeyError(키)
