# 83 편 위쪽 화면 판 — 재료 out/영상05/대화/83_구조/자료/<카드>/element-NNN.png · 컵 · 옛길 = Remotion Ep83(300 프레임 · 키 뒤 「2」 = 뒤 150) · 구조 = Anatomy 드릴 프레스(scratchpad anatomy83/build.mjs · 단계 1~5 = 60 프레임씩 · 「구조끝」 = 마지막)
from PIL import Image, ImageDraw
A = "G:/art2real/out/영상05/대화/83_구조/자료/"
초, 빨, 금 = (40, 160, 80), (220, 50, 50), (220, 160, 30)
카드 = {"컵": 빨, "옛길": 금, "구조": 초, "결과": 금}
def 판(키, p):
    p = min(max(p, 0), 1)
    if 키.startswith("구조"):
        k = "구조"; 자른 = {1: 18, 3: 15, 4: 46, 5: 38}   # 단계 안 두 줄: a = 앞 [0, 자른) · b = 뒤 [자른, 60)
        if 키 == "구조끝": i = 299
        else:
            n = int(키[2]); 꼬 = 키[3:]; lo, hi = (0, 자른[n]) if 꼬 == "a" else (자른[n], 60) if 꼬 == "b" else (0, 60)
            i = (n - 1) * 60 + lo + min(hi - lo - 1, int(p * (hi - lo)))
    else:
        뒤 = 키.endswith("2"); k = 키[:-1] if 뒤 else 키; i = min(149, int(p * 150)) + (150 if 뒤 else 0)
    c = Image.new("RGBA", (1000, 700), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, 999, 699), 36, fill=(250, 250, 252, 255), outline=카드[k] + (255,), width=8)
    c.alpha_composite(Image.open(A + "%s/element-%03d.png" % (k, i)).convert("RGBA")); return c
