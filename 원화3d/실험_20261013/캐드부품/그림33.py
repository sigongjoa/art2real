# 판정기준33 보고 한 장 — 몸통 53 편 그림 윤곽 · 막대(바탕만 · 2a · 2b · 천장) + 부품 넷(정답 · 바탕만 · 2a · 2b) · 10-13
import json, subprocess, numpy as np, cadquery as cq
from PIL import Image, ImageDraw, ImageFont
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"; A = "G:/art2real/out/설명/구멍/"; K = 30; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); 고른 = [171, 120, 3, 142]
d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; X = d["X"][te]; del d
pa, pb = np.load(O + "학습/시험예측.npz"), np.load(O + "학습2b/시험예측.npz"); L = json.load(open(O + "목록.json", encoding="utf-8")); 이름 = []
for j in 고른:
    v, f, H = J.정규메시(L[te[j]]); 몸, _ = J.몸통53(X[j], H); cq.exporters.export(몸.val().scale(K), A + "r33_%d_바탕.stl" % j, tolerance=.01, angularTolerance=.05); 이름.append("33_%d_바탕" % j)
    for t, p in (("2a", pa), ("2b", pb)):
        s = J.짓기(p["P"][j], p["D"][j].astype(np.float32), H, True, X[j]); cq.exporters.export(s.val().scale(K), A + "r33_%d_%s.stl" % (j, t), tolerance=.01, angularTolerance=.05); 이름.append("33_%d_%s" % (j, t))
subprocess.run(["C:/Program Files/Blender Foundation/Blender 4.0/blender.exe", "-b", "-P", "G:/art2real/원화3d/실험_20261013/구멍/렌더_빛.py", "--"] + 이름, check=True, stdout=subprocess.DEVNULL)
r = json.load(open(O + "결과33.json", encoding="utf-8")); R = {k: np.load(O + "부피IoU_33_%s.npy" % k)[:, 0] for k in ("2a", "2b")}
흰, 초, 빨, 파, 회, 금 = (236, 242, 250), (110, 220, 140), (255, 100, 100), (64, 196, 255), (150, 160, 180), (240, 190, 60)
c = Image.new("RGB", (1800, 1900), (10, 15, 30)); dr = ImageDraw.Draw(c); dr.text((40, 30), "로드맵 2단계 다시 · 몸통 = 53 편 그림 윤곽 · 모델은 구멍 · 홈만 (판정기준33)", font=F(42), fill=흰)
막 = [("바탕만(그림 윤곽 밀기)", r["2a"]["바탕만"], 회, ""), ("2a 위 한 장", r["2a"]["부피IoU"], 빨, "바탕만 +%.3f · 기준 +0.04 실패" % (r["2a"]["부피IoU"] - r["2a"]["바탕만"])),
     ("2b 위 · 앞 · 옆", r["2b"]["부피IoU"], 빨, "2a +%.3f · 기준 +0.02 실패" % (r["2b"]["부피IoU"] - r["2a"]["부피IoU"])), ("천장(정답 구멍 · 홈)", r["천장"]["부피IoU"], 금, "")]
for i, (t, v, col, s) in enumerate(막):
    y = 110 + i * 75; dr.text((40, y + 10), t, font=F(30), fill=흰); dr.rounded_rectangle((470, y, 470 + int(1000 * v), y + 54), 12, fill=col); dr.text((480 + int(1000 * v), y + 27), "%.3f  %s" % (v, s), font=F(28), fill=흰, anchor="lm")
dr.text((40, 420), "몸통 지은 길(200): 원 39 · 다각 158 · 다시 줄임 2 · 볼록 껍질 1 · 실패 0 — 몸통이 버려진 부품 없음 · 남은 0 점 5 는 격자보다 얇은 부품(채점기 한계)", font=F(26), fill=초)
for j, t in enumerate(("입력(위)", "정답", "바탕만", "2a", "2b")): dr.text(([100, 420, 760, 1100, 1440][j], 490), t, font=F(30), fill=파, anchor="mm")
for i, k in enumerate(고른):
    y = 520 + i * 340; c.paste(Image.fromarray((255 - X[i * 0 + 고른.index(k) * 0 + 0] * 0 + 0).astype(np.uint8)) if False else Image.fromarray((255 - X[k] * 225).astype(np.uint8)).resize((180, 180)).convert("RGB"), (10, y + 70))
    for q, t in enumerate(("31_%d_정답", "33_%d_바탕", "33_%d_2a", "33_%d_2b")): c.paste(Image.open(A + ("빛_r" + t + ".png") % k).convert("RGB").crop((130, 110, 770, 750)).resize((320, 320)), (260 + q * 340, y))
    dr.text((1100, y + 300), "%.2f" % R["2a"][k], font=F(28), fill=흰, anchor="mm"); dr.text((1440, y + 300), "%.2f" % R["2b"][k], font=F(28), fill=초 if R["2b"][k] > R["2a"][k] else 빨, anchor="mm")
c.save(O + "결과33.png"); print("ok")
