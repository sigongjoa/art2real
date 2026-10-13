# 학습 타임랩스 쇼츠 프레임 시안 — 왼쪽 세로 진행 막대 = 시간축 · 막대 눈금마다 그 에폭의 형태 · 가운데 지금 형태 크게 · 10-13
# 형태는 예시(구멍 정육면체 CadQuery) — 실제 학습이면 같은 자리에 스냅을 넣는다
from PIL import Image, ImageDraw, ImageFont
A = "G:/art2real/out/설명/구멍/"; O = A + "프레임시안.png"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
W, H = 1080, 1920; 금, 흰, 회, 어둠, 초, 빨 = (255, 205, 60), (240, 240, 245), (110, 112, 125), (24, 25, 32), (110, 220, 130), (255, 110, 100)
에폭 = ["0", "1", "2", "4엇", "3", "4", "6", "5"]   # 에폭 1~8 의 형태(예시 진행: 구멍 없음 → 작음 → 엇나감 → 커짐 → 지나침 → 맞음)
말 = ["구멍 없음", "작다", "작다", "옆으로 샘", "작다", "거의", "너무 큼", "맞음"]
def 그림(p, s, 알파=255):
    im = Image.open(A + p).convert("RGBA").resize((s, s), Image.LANCZOS)
    if 알파 < 255: im.putalpha(im.split()[3].point(lambda v: v * 알파 // 255))
    return im
def 프레임(k):   # k = 지금 에폭(1~8)
    c = Image.new("RGBA", (W, H), (14, 15, 20, 255)); d = ImageDraw.Draw(c)
    d.text((W // 2, 80), "AI가 구멍을 맞춰 가는 중", font=F(60), fill=흰, anchor="mm")
    # 왼쪽 진행 막대(시간축) + 눈금마다 그 에폭 형태
    x0, y0, y1 = 40, 200, 1500; 칸 = (y1 - y0) / 8
    d.rounded_rectangle((x0 + 70, y0, x0 + 90, y1), 10, fill=(45, 47, 58)); d.rounded_rectangle((x0 + 70, y0, x0 + 90, y0 + 칸 * k), 10, fill=금)
    for j in range(8):
        cy = int(y0 + 칸 * (j + .5)); box = (x0, cy - 70, x0 + 160, cy + 70)
        if j < k:
            d.rounded_rectangle(box, 18, fill=어둠, outline=금 if j == k - 1 else (60, 62, 75), width=6 if j == k - 1 else 2)
            c.alpha_composite(그림("비스듬_r%s.png" % 에폭[j], 130, 255 if j == k - 1 else 170), (x0 + 15, cy - 65))
        else:
            d.rounded_rectangle(box, 18, outline=(50, 52, 62), width=2); d.text((x0 + 80, cy), "?", font=F(56), fill=(60, 62, 75), anchor="mm")
        d.text((x0 + 178, cy), "%d" % (j + 1), font=F(28), fill=금 if j == k - 1 else 회, anchor="lm")
    d.text((x0 + 80, y1 + 40), "에폭", font=F(30), fill=회, anchor="mm")
    # 가운데: 지금 형태 크게 + 오른쪽 위에 정답 그림
    d.rounded_rectangle((250, 200, 1050, 1000), 36, fill=어둠)
    c.alpha_composite(그림("비스듬_r%s.png" % 에폭[k - 1], 700), (300, 260))
    d.text((290, 240), "에폭 %d" % k, font=F(54), fill=금, anchor="lt")
    d.rounded_rectangle((820, 220, 1035, 470), 20, fill=(250, 248, 240)); c.alpha_composite(그림("그림_목표.png", 190).convert("RGBA"), (832, 232)); d.text((927, 445), "그림", font=F(28), fill=(40, 40, 50), anchor="mm")
    d.text((650, 955), 말[k - 1], font=F(64), fill=초 if 말[k - 1] == "맞음" else 빨, anchor="mm", stroke_width=6, stroke_fill=(14, 15, 20))
    # 아래: 그림과 겹침(위에서 본 단면) — 숫자는 작게
    겹 = "겹침_r%s.png" % 에폭[k - 1]
    d.rounded_rectangle((250, 1030, 1050, 1500), 36, fill=어둠); d.text((290, 1060), "위에서 본 모양 ↔ 그림", font=F(36), fill=흰, anchor="lt")
    if 겹: c.alpha_composite(그림(겹, 360), (300, 1120))
    else: d.text((480, 1300), "(시안: 겹침 그림 없음)", font=F(28), fill=회, anchor="mm")
    d.text((700, 1200), "파랑 = AI", font=F(34), fill=(120, 160, 245), anchor="lm"); d.text((700, 1260), "빨강 = 그림", font=F(34), fill=빨, anchor="lm")
    # 맨 아래: 대사 · 자막 자리(대화 쇼츠면 인물 + 대사창)
    d.rounded_rectangle((40, 1580, 1040, 1880), 30, outline=(60, 62, 75), width=4); d.text((540, 1730), "대사 · 자막 자리", font=F(44), fill=회, anchor="mm")
    return c.convert("RGB")
fs = [프레임(k) for k in (2, 5, 8)]
s = Image.new("RGB", (3 * 540 + 40, 960 + 70), (40, 40, 48)); d = ImageDraw.Draw(s)
for j, (f, k) in enumerate(zip(fs, (2, 5, 8))):
    s.paste(f.resize((540, 960)), (10 + j * 550, 60)); d.text((10 + j * 550 + 270, 30), "에폭 %d 프레임" % k, font=F(30), fill=흰, anchor="mm")
s.save(O); fs[1].save(A + "프레임시안_한장.png"); print("ok")
