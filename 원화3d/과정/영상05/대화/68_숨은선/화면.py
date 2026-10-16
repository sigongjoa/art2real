# 68 편(숨은선) 위쪽 화면 판 — 재료 out/영상05/대화/68_숨은선/자료/(Anatomy 숨은선 96 프레임 · 재료68.py 실제 부품 선 그림 · Remotion 모션 카드 관문 · 결과) · 숫자는 결과판정56_G0 · 결과판정56
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/영상05/대화/68_숨은선/자료/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 40, 50), (130, 130, 140), (220, 160, 30)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _그림(c, n, box, crop=None):
    im = Image.open(A + n + ".png").convert("RGBA"); im = im.crop(crop) if crop else im.crop(im.getbbox())
    x0, y0, x1, y1 = box; s = min((x1 - x0) / im.width, (y1 - y0) / im.height); im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS); c.alpha_composite(im, (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2))
def _프레임(c, 폴, i, box, crop=None): _그림(c, "%s/프레임_%03d" % (폴, i), box, crop)

import math
def _이징(t): t = min(max(t, 0), 1); return 1 - (1 - t) ** 3
def _밀기(c, n, box, p, 배=1.08, crop=None):   # 카메라 밀기: 그림을 p 만큼 키워 같은 상자에(가운데 기준)
    im = Image.open(A + n + ".png").convert("RGBA"); im = im.crop(crop) if crop else im.crop(im.getbbox())
    x0, y0, x1, y1 = box; k = min((x1 - x0) / im.width, (y1 - y0) / im.height) * (1 + (배 - 1) * _이징(p)); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2; 창 = im.crop((max(0, im.width // 2 - (x1 - x0) // 2), max(0, im.height // 2 - (y1 - y0) // 2), im.width // 2 + (x1 - x0) // 2, im.height // 2 + (y1 - y0) // 2)); c.alpha_composite(창, (cx - 창.width // 2, cy - 창.height // 2))
def _붉은쓸기(c, n, box, p, 제=None):   # 검정(겉 선)은 바로 · 빨강(안쪽 점선)은 왼→오로 p 만큼 드러남 · 쓸리는 자리에 빨간 펜 선
    im = Image.open(A + n + ".png").convert("RGBA"); r, g, b, a = im.split(); 빨m = Image.eval(r, lambda v: 255 if v > 150 else 0); 빨m = Image.fromarray((np.array(빨m) > 0) & (np.array(g) < 100) & (np.array(a) > 0)).convert("L")
    검 = im.copy(); 검.putalpha(Image.fromarray(((np.array(a) > 0) & ~(np.array(빨m) > 0)).astype(np.uint8) * 255)); 빨 = im.copy(); e = _이징(p); 가 = Image.new("L", im.size, 0); ImageDraw.Draw(가).rectangle((0, 0, int(im.width * e), im.height), fill=255); 빨.putalpha(Image.fromarray(np.minimum(np.array(빨m), np.array(가))))
    x0, y0, x1, y1 = box; k = min((x1 - x0) / im.width, (y1 - y0) / im.height); W, Hh = int(im.width * k), int(im.height * k); ox, oy = x0 + (x1 - x0 - W) // 2, y0 + (y1 - y0 - Hh) // 2
    c.alpha_composite(검.resize((W, Hh), Image.LANCZOS), (ox, oy)); c.alpha_composite(빨.resize((W, Hh), Image.LANCZOS), (ox, oy))
    if 0 < e < 1: bb = im.getbbox(); ImageDraw.Draw(c).line((ox + int(W * e), oy + int(bb[1] * k) - 6, ox + int(W * e), oy + int(bb[3] * k) + 6), fill=(220, 50, 50, 255), width=4)   # 펜 선은 그림 높이만큼만
    if 제: ImageDraw.Draw(c).text(((x0 + x1) // 2, y0 - 22), 제, font=F(30), fill=먹, anchor="mm")
def _미끄럼(c, n, box, p, 쪽=-1):   # 옆에서 미끄러져 들어옴(쪽 -1 왼 · 1 오른) · 확 들어와 부드럽게 멈춤
    e = _이징(p); x0, y0, x1, y1 = box; d = int(쪽 * 600 * (1 - e)); 층 = Image.new("RGBA", c.size, (0, 0, 0, 0)); _그림(층, n, (x0 + d, y0, x1 + d, y1)); 층.putalpha(층.split()[3].point(lambda v: int(v * min(1, e * 2)))); c.alpha_composite(층)
def _손동그라미(c, box, p, 색):   # 손그림 느낌 타원 호: p 만큼 그어짐 · 세 겹을 조금씩 어긋나게
    d = ImageDraw.Draw(c); x0, y0, x1, y1 = box
    for k in range(3): dx, dy = (k - 1) * 3, (k - 1) * 2; d.arc((x0 + dx, y0 + dy, x1 + dx, y1 + dy), -100, -100 + int(380 * _이징(p)), fill=색 + (255,), width=5)
import numpy as np
자름 = (180, 40, 819, 658)   # Anatomy 숨은선 96 장의 공통 bbox — 프레임마다 getbbox 면 크기가 흔들린다
def _선판(c, n, box, 제, 색):
    _그림(c, n, box); ImageDraw.Draw(c).text(((box[0] + box[2]) // 2, box[1] - 22), 제, font=F(30), fill=색, anchor="mm")
def 판(키, p):
    q = min(max(p, 0), 1)
    if 키 in ("그릇", "그릇끝"):   # 깊이찍기 구간 12–35(덩어리 → 얕게 깎음 → 빨강) · 다시 나오면 마지막
        c = _카드(빨); d = ImageDraw.Draw(c); _프레임(c, "숨은선", 35 if 키 == "그릇끝" else min(35, 12 + int(q * 24)), (60, 120, 940, 620), 자름); d.text((500, 78), "깊이를 몰라 얕게 깎았다", font=F(42), fill=빨, anchor="mm"); d.text((500, 655), "바닥이 어디인지 그림에 없다", font=F(30), fill=회, anchor="mm"); return c
    if 키 in ("숨은선A", "숨은선B", "숨은선C"):   # Anatomy 구간: 소개 0–11 · 깊이찍기 12–35 · 광선 36–59 · 다시깎기 60–83 · 정지 84–95
        a, b, 테, 제, 아래 = {"숨은선A": (0, 11, 먹, "앞에서 보면 네모 하나뿐", "위 그림에만 안쪽 테두리가 있다"), "숨은선B": (36, 59, 금, "벽 뒤 바닥 높이에 점선을 긋는다", "도면의 점선 = 안 보이는 안쪽"), "숨은선C": (60, 95, 초, "점선 높이까지 깎는다", "컵 바닥이 맞는다")}[키]
        c = _카드(테); d = ImageDraw.Draw(c); _프레임(c, "숨은선", min(b, a + int(q * (b - a + 1))), (60, 120, 940, 620), 자름); d.text((500, 78), 제, font=F(42), fill=테, anchor="mm"); d.text((500, 655), 아래, font=F(30), fill=회, anchor="mm"); return c
    if 키 in ("실물컵", "실물컵끝", "실물", "덩어리", "덩어리끝", "끊김"):   # 10-16 모션 스킬 카드(Remotion Ep68b · LottieFiles motion-design 값 · 투명 150 프레임) — 앞 90 = 첫 대사 · 뒤 60 = 다음 대사
        폴, a, b, 테, 제, 아래 = {"실물컵": ("컵68", 0, 89, 빨, "속이 빈 컵 · 모델은 얕게 깎았다", ""), "실물컵끝": ("컵68", 90, 149, 빨, "속이 빈 컵 · 모델은 얕게 깎았다", "위에서 보면 안쪽 테두리가 있다"),
                               "실물": ("부품68", 0, 149, 금, "실제 부품에 적용", ""), "덩어리": ("덩어리68", 0, 89, 빨, "둥근 면까지 선으로 → 안쪽이 덩어리", "빨강 = 안쪽 점선 · 검정 = 겉 선"),
                               "덩어리끝": ("덩어리68", 90, 149, 빨, "둥근 면까지 선으로 → 안쪽이 덩어리", "제 규칙 탓"), "끊김": ("끊김68", 0, 149, 초, "턱 지는 곳만 남기니 점선이 된다", "컵 안쪽 바닥 · 벽이 빨간 점선으로")}[키]
        c = _카드(테); d = ImageDraw.Draw(c); c.alpha_composite(Image.open(A + "%s/프레임_%03d.png" % (폴, min(b, a + int(q * (b - a + 1))))).convert("RGBA")); d.text((500, 78), 제, font=F(42), fill=테, anchor="mm")
        if 아래: d.text((500, 662), 아래, font=F(28), fill=회, anchor="mm")
        return c
    if 키 in ("실물컵_옛", "실물컵끝_옛"):   # 2 판: 실제 컵 5926(판0 0.54 · 정답 깊이 0.92) — 물건 하나로 시작 · 카메라 밀기 + 숫자 세기 · 다시 나오면 안쪽에 손동그라미
        c = _카드(빨); d = ImageDraw.Draw(c); 끝 = 키.endswith("끝"); _밀기(c, "5926_렌더", (200, 130, 800, 610), 1 if 끝 else q, 1.1)
        if 끝: _손동그라미(c, (300, 150, 700, 320), q, 빨)
        d.text((500, 78), "속이 빈 컵 · 모델은 얕게 깎았다", font=F(42), fill=빨, anchor="mm"); d.text((500, 655), "모델 %.2f · 정답 깊이로 지으면 0.92" % (0.54 * (1 if 끝 else _이징(q * 1.5))), font=F(30), fill=회, anchor="mm"); return c
    if 키 == "실물_옛":
        c = _카드(금); d = ImageDraw.Draw(c); _미끄럼(c, "9806_렌더", (60, 140, 480, 600), q * 1.8, -1); _미끄럼(c, "5926_렌더", (520, 140, 940, 600), (q - .3) * 1.8, 1)
        d.text((500, 78), "실제 부품에 적용", font=F(42), fill=먹, anchor="mm"); d.text((270, 650), "나사 이음 9806", font=F(32), fill=회, anchor="mm"); d.text((730, 650), "컵 5926", font=F(32), fill=회, anchor="mm"); return c
    if 키 in ("덩어리_옛", "덩어리끝_옛"):   # 처음: 점선이 왼→오로 쓸리며 덩어리가 드러남(앞 → 옆 시차) · 다시: 앞 판으로 카메라 밀기
        c = _카드(빨); d = ImageDraw.Draw(c); 끝 = 키.endswith("끝"); _그림(c, "9806_렌더", (40, 200, 300, 520))
        if 끝: _붉은쓸기(c, "9806_꺾임_옆", (670, 160, 970, 580), 1, "옆"); _밀기(c, "9806_꺾임_앞", (340, 160, 640, 580), q, 1.12); d.text((490, 138), "앞", font=F(30), fill=먹, anchor="mm")
        else: _붉은쓸기(c, "9806_꺾임_앞", (340, 160, 640, 580), q * 1.6, "앞"); _붉은쓸기(c, "9806_꺾임_옆", (670, 160, 970, 580), (q - .35) * 1.6, "옆")
        d.text((500, 78), "둥근 면까지 선으로 → 안쪽이 덩어리", font=F(42), fill=빨, anchor="mm"); d.text((500, 650), "빨강 = 안쪽 점선 · 검정 = 겉 선", font=F(30), fill=회, anchor="mm"); return c
    if 키 == "끊김_옛":   # 세 판에 점선이 시차를 두고 그어짐
        c = _카드(초); d = ImageDraw.Draw(c); _붉은쓸기(c, "9806_끊김_앞", (40, 160, 340, 580), q * 1.8, "나사 이음 · 앞"); _붉은쓸기(c, "9806_끊김_옆", (350, 160, 650, 580), (q - .25) * 1.8, "나사 이음 · 옆"); _붉은쓸기(c, "5926_끊김_앞", (660, 160, 960, 580), (q - .5) * 1.8, "컵 · 앞")
        d.text((500, 78), "턱 지는 곳만 남기니 점선이 된다", font=F(42), fill=초, anchor="mm"); d.text((500, 650), "컵 안쪽 바닥 · 벽이 빨간 점선으로", font=F(30), fill=회, anchor="mm"); return c
    if 키 in ("관문", "결과", "결과끝"):   # Remotion 모션 카드(투명 PNG 150 장) — 처음 줄은 p 로 움직이고 다시 나오면 마지막 프레임
        폴, 테, 제 = ("관문모션", 초, "속 빈 112 개 · 점선이 제대로 생겼나") if 키 == "관문" else ("결과모션", 금, "점선을 넣고 다시 학습")
        i = 149 if 키.endswith("끝") else min(149, int(q * 150)); c = _카드(테); d = ImageDraw.Draw(c); c.alpha_composite(Image.open(A + "%s/프레임_%03d.png" % (폴, i)).convert("RGBA")); d.text((500, 80), 제, font=F(42), fill=먹, anchor="mm"); return c
    raise KeyError(키)
