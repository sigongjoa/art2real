# 57 편(다섯 칸 샘플) 위쪽 화면 판 — 재료 out/영상05/대화/57_덩어리/자료/지도.npz(시험 0 플랜지 · 2a 모델) · 렌더 빛_r2a_모델_0 · 빛_r2a_정답_0 · 빛_r57_덩어리 · 숫자는 결과판정31a
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
R = "G:/art2real/out/설명/구멍/"; Z = np.load("G:/art2real/out/영상05/대화/57_덩어리/자료/지도.npz"); F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
초, 빨, 파, 먹, 회, 금 = (40, 160, 80), (220, 50, 50), (40, 110, 220), (40, 40, 50), (130, 130, 140), (220, 160, 30)
def _카드(테, w=1000, h=700):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 252, 255), outline=테 + (255,), width=8); return c
def _렌(n, s):
    im = Image.open(R + "빛_r%s.png" % n).convert("RGB").crop((130, 110, 770, 750)).resize((s, s)); m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).rounded_rectangle((3, 3, s - 3, s - 3), 22, fill=255); im = im.convert("RGBA"); im.putalpha(m); return im
def _쉬움(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def _지도(깊, 몸):   # 깊이를 색으로(들어감만) · 몸은 연회색 · 관통은 검정
    v = np.full(깊.shape + (3,), 245, np.uint8); v[몸] = (205, 215, 230); m = Z["P"] == 3
    col = cv2.applyColorMap(np.clip(깊 * 255 / .6, 0, 255).astype(np.uint8), cv2.COLORMAP_TURBO)[..., ::-1]; v[m] = col[m]; v[Z["P"] == 2] = (30, 30, 30); return Image.fromarray(v)
def _둘(c, a, b, 왼, 오, 색왼=먹, 색오=먹):
    d = ImageDraw.Draw(c); c.alpha_composite(a, (50, 150)); c.alpha_composite(b, (520, 150)); d.text((265, 100), 왼, font=F(36), fill=색왼, anchor="mm"); d.text((735, 100), 오, font=F(36), fill=색오, anchor="mm")
def 판(키, p):
    c = _카드(빨 if 키 in ("끄트러기", "쪼개짐") else 금 if 키 in ("학습", "층", "접시") else 초); d = ImageDraw.Draw(c)
    if 키 == "끄트러기":
        s = int(480 + 100 * _쉬움(p * 1.5)); c.alpha_composite(_렌("2a_모델_0", s), (500 - s // 2, 390 - s // 2)); d.text((500, 52), "플랜지 — 평평해야 할 판", font=F(34), fill=빨, anchor="mm"); return c
    if 키 == "학습":
        d.text((500, 90), "나의 짐작", font=F(36), fill=먹, anchor="mm"); d.rounded_rectangle((200, 170, 800, 470), 30, fill=(255, 246, 225, 255), outline=금, width=6)
        d.text((500, 270), "학습이 모자라다", font=F(54), fill=먹, anchor="mm"); d.text((500, 380), "→ 부품 더 넣고 다시 학습", font=F(36), fill=회, anchor="mm")
        if p > .5: d.text((500, 580), "?", font=F(90), fill=금, anchor="mm")
        return c
    if 키 == "층":
        m = Z["P"] == 3; 원 = np.where(m, Z["Dp"], 0); 층 = np.round(원 / .1) * .1
        c.paste(_지도(원, Z["P"] > 0).resize((400, 400), Image.NEAREST), (60, 150)); d.text((260, 110), "짐작한 깊이(매끈)", font=F(32), fill=먹, anchor="mm")
        if p > .3: c.paste(_지도(층, Z["P"] > 0).resize((400, 400), Image.NEAREST), (540, 150)); d.text((740, 110), "0.1 층으로 반올림", font=F(32), fill=빨, anchor="mm"); d.text((500, 620), "같은 판이 0.2 · 0.3 · 0.4 층으로 갈라짐", font=F(32), fill=빨, anchor="mm")
        return c
    if 키 == "쪼개짐":
        m = Z["P"] == 3; 층 = np.clip(np.round(np.where(m, Z["Dp"], 0) / .1), 0, 10).astype(int); v = np.full(m.shape + (3,), 245, np.uint8); v[Z["P"] > 0] = (205, 215, 230)
        rng = np.random.default_rng(3)
        for k in range(1, 11):
            n, lab = cv2.connectedComponents((m & (층 == k)).astype(np.uint8), connectivity=4)
            for i in range(1, n): v[lab == i] = rng.integers(60, 240, 3)
        c.paste(Image.fromarray(v).resize((440, 440), Image.NEAREST), (40, 140)); c.alpha_composite(_렌("2a_모델_0", 440), (520, 140)); d.text((260, 100), "층마다 따로 깎을 조각", font=F(32), fill=빨, anchor="mm"); d.text((740, 100), "그래서 이렇게", font=F(32), fill=빨, anchor="mm"); return c
    if 키 == "결정":
        c.paste(_지도(np.where(Z["P"] == 3, Z["Dp"], 0), Z["P"] > 0).resize((400, 400), Image.NEAREST), (60, 150)); d.text((260, 110), "화소마다 깊이", font=F(32), fill=먹, anchor="mm")
        if p > .3: d.text((500, 350), "→", font=F(80), fill=회, anchor="mm"); c.paste(_지도(Z["덩깊"], Z["P"] > 0).resize((400, 400), Image.NEAREST), (540, 150)); d.text((740, 110), "덩어리마다 깊이 하나", font=F(32), fill=초, anchor="mm")
        d.text((500, 620), "이어진 덩어리 = 가운데 값 하나", font=F(32), fill=초, anchor="mm"); return c
    if 키 == "숫자":
        e = _쉬움(p * 2); d.text((500, 80), "시험 부품 200 개 · 학습 그대로", font=F(34), fill=먹, anchor="mm")
        for i, (t, a, b, f) in enumerate((("깎을 덩어리(중앙)", 17, 2, "%d"), ("부피 IoU", .576, .593, "%.3f"))):
            y = 190 + i * 220; v = a + (b - a) * e; d.text((80, y), t, font=F(34), fill=먹); d.text((80, y + 70), f % a, font=F(60), fill=빨); d.text((420, y + 100), "→", font=F(60), fill=회, anchor="mm"); d.text((560, y + 70), f % v, font=F(60), fill=초)
        if p > .6: d.text((500, 640), "판정 통과", font=F(40), fill=초, anchor="mm")
        return c
    if 키 == "전후":
        _둘(c, _렌("2a_모델_0", 430), _렌("57_덩어리", 430), "전 · 층마다", "후 · 덩어리마다", 빨, 초); return c
    if 키 == "접시":
        _둘(c, _렌("2a_정답_0", 430), _렌("57_덩어리", 430), "정답", "덩어리 깊이", 초, 빨)
        if p > .3: d.ellipse((620, 280, 850, 420), outline=빨, width=6); d.text((735, 640), "가운데 얕은 홈이 없다", font=F(34), fill=빨, anchor="mm")
        return c
    raise KeyError(키)
