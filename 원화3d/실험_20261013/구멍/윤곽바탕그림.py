# 「처음 형태를 어떻게 잡나」 단계 그림 — 그림 → 바깥 선만 → 원/꼭짓점 맞춤 → 밀어 올린 바탕(블렌더) · 합성 2 + 메카2 머리 앞 그림 · 10-13
import os, sys, json, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
H_ = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H_)
import 캐드점수2 as K, 윤곽바탕 as B, 진짜그림52 as R
A = "G:/art2real/out/설명/구멍/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
if __name__ == "__main__":
    import cadquery as cq
    S = json.load(open(A + "학습2/스냅.json", encoding="utf-8"))
    im = np.asarray(Image.open(R.IMG).convert("RGB")); r0, r1, c0, c1 = R.부위["머리"]
    줄 = [("합성 · 원기둥 + 구멍", K.그림(S["정답"][3])), ("합성 · 상자 + 구멍 · 홈", K.그림(S["정답"][5])), ("진짜 그림 · 메카2 머리(앞)", R.입력(im[r0:r1, c0:c1]))]
    for k, (_, g) in enumerate(줄): 바, f = B.짓기(g); cq.exporters.export(바, A + "r윤곽바탕_%d.stl" % k, tolerance=0.01, angularTolerance=0.05)
    subprocess.run(["C:/Program Files/Blender Foundation/Blender 4.0/blender.exe", "-b", "-P", os.path.join(H_, "렌더_빛.py"), "--"] + ["윤곽바탕_%d" % k for k in range(3)], check=True, stdout=subprocess.DEVNULL)
    W, H = 1800, 1560; 바색, 카, 테, 흰, 회, 초, 하, 금 = (10, 15, 30), (18, 26, 46), (44, 58, 90), (236, 242, 250), (120, 134, 160), (110, 220, 140), (64, 196, 255), (255, 205, 70)
    c = Image.new("RGB", (W, H), 바색); d = ImageDraw.Draw(c); d.text((W // 2, 55), "처음 형태(바탕)를 어떻게 잡나", font=F(54), fill=흰, anchor="mm")
    for j, t in enumerate(("① 그림", "② 가장 바깥 닫힌 선만", "③ 원 / 꼭짓점으로 맞춤", "④ CadQuery 로 밀어 올림")): d.text((210 + j * 420, 125), t, font=F(32), fill=(금 if j == 3 else 하), anchor="mm")
    for k, (이름, g) in enumerate(줄):
        y = 170 + k * 450; S_ = 360; d.text((40, y), 이름, font=F(28), fill=회)
        a = Image.fromarray((255 - g * 225).astype(np.uint8)).convert("RGB").resize((S_, S_), Image.NEAREST); c.paste(a, (30, y + 40))
        m, ct = B.바깥(g); b = np.full((128, 128, 3), 245, np.uint8); b[g > .3] = (190, 190, 200); cv2.drawContours(b, [ct.reshape(-1, 1, 2)], -1, (40, 170, 90), 2)
        c.paste(Image.fromarray(b).resize((S_, S_), Image.NEAREST), (450, y + 40))
        f = B.맞추기(ct); e = Image.new("RGB", (S_, S_), (245, 245, 245)); de = ImageDraw.Draw(e); s = S_ / 128
        if f[0] == "원": (x, yy), r = f[1], f[2]; de.ellipse(((x - r) * s, (yy - r) * s, (x + r) * s, (yy + r) * s), outline=(30, 120, 220), width=5); de.text((S_ // 2, S_ - 30), "원 하나", font=F(28), fill=(30, 120, 220), anchor="mm")
        else:
            p = [(x * s, yy * s) for x, yy in f[1]]; de.line(p + [p[0]], fill=(30, 120, 220), width=4)
            for x, yy in p: de.ellipse((x - 6, yy - 6, x + 6, yy + 6), fill=(220, 60, 60))
            de.text((S_ // 2, S_ - 30), "꼭짓점 %d 개 · 직선" % len(p), font=F(28), fill=(30, 120, 220), anchor="mm")
        c.paste(e, (870, y + 40))
        r_ = Image.open(A + "빛_r윤곽바탕_%d.png" % k).convert("RGB").crop((180, 160, 720, 700)).resize((S_ + 40, S_ + 40)); c.paste(r_, (1290, y + 20))
        for j in range(3): d.text((400 + j * 420, y + 220), "→", font=F(50), fill=회, anchor="mm")
    d.text((40, H - 50), "안쪽 선(구멍 · 홈 · 얼굴 무늬)은 바탕에 안 쓴다 — 그건 학습 모델이 깎는 몫 · 높이는 이번 판에선 10 고정(앞 · 옆 그림이 있으면 거기서)", font=F(26), fill=흰)
    c.save(A + "윤곽바탕_단계.png"); print("ok")
