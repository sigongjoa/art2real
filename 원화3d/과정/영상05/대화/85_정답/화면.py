# 85 편 위쪽 화면 판 — 재료 out/영상05/대화/85_정답/자료/(재료.py) · 장치 = anatomy115 영상 프레임 516 장(15 fps · 줄 진행 p 로 구간을 훑음)
from PIL import Image, ImageDraw
A = "G:/art2real/out/영상05/대화/85_정답/자료/"
초, 빨, 금 = (40, 160, 80), (220, 50, 50), (220, 160, 30)
카드 = {"안됨": 빨, "회전": 빨, "교과서": 금, "교과서2": 금, "장치": 초, "장치2": 초, "장치3": 초}
구간 = {"장치": (0, 60), "장치2": (60, 420), "장치3": (440, 486)}   # 프레임 번호(1 회 후보 넷 재기 · 6 회 학습 · 학습 뒤 검산)
def 판(키, p):
    p = min(max(p, 0), 1)
    if 키 in 구간: a, b = 구간[키]; f = "장치/%04d.png" % int(a + p * (b - a - 1))
    else: f = 키 + ".png"
    c = Image.new("RGBA", (1000, 700), (0, 0, 0, 0)); ImageDraw.Draw(c).rounded_rectangle((0, 0, 999, 699), 36, fill=(250, 250, 252, 255), outline=카드[키] + (255,), width=8)
    im = Image.open(A + f).convert("RGBA")
    if 키 in 구간:   # 어두운 장치 그림은 둥근 테 안쪽에 맞춰 잘라 넣음
        m = Image.new("L", (1000, 700), 0); ImageDraw.Draw(m).rounded_rectangle((8, 8, 991, 691), 30, fill=255); c.paste(im, (0, 0), m)
        ImageDraw.Draw(c).rounded_rectangle((0, 0, 999, 699), 36, outline=카드[키] + (255,), width=8); return c
    c.alpha_composite(im); return c
