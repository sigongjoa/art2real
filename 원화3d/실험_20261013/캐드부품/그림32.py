# 판정기준32 보고 한 장 — 꼬인 윤곽 고친 전후(2b 3 · 34 번) 렌더 + 0 점 가르기 · 10-13
import json, subprocess, numpy as np, cadquery as cq, trimesh
from PIL import Image, ImageDraw, ImageFont
import 짓기 as J
O = "G:/art2real/out/설명/캐드부품/"; A = "G:/art2real/out/설명/구멍/"; K = 30; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
te = np.nonzero(np.load(O + "데이터.npz")["시험"])[0][:200]; L = json.load(open(O + "목록.json", encoding="utf-8")); B = np.load(O + "학습2b/시험예측.npz"); 이름 = []
for j in (3, 34):
    v, f, H = J.정규메시(L[te[j]]); trimesh.Trimesh(v * K, f).export(A + "r32_%d_정답.stl" % j); s = J.짓기(B["P"][j], B["D"][j].astype(np.float32), H, True)
    cq.exporters.export(s.val().scale(K), A + "r32_%d_고침.stl" % j, tolerance=.01, angularTolerance=.05); 이름 += ["32_%d_정답" % j, "32_%d_고침" % j]
subprocess.run(["C:/Program Files/Blender Foundation/Blender 4.0/blender.exe", "-b", "-P", "G:/art2real/원화3d/실험_20261013/구멍/렌더_빛.py", "--"] + 이름, check=True, stdout=subprocess.DEVNULL)
R0, R1 = np.load(O + "부피IoU_31b.npy")[:, 0], np.load(O + "부피IoU_32_2b.npy")[:, 0]; 흰, 초, 빨, 파, 금 = (236, 242, 250), (110, 220, 140), (255, 100, 100), (64, 196, 255), (240, 190, 60)
c = Image.new("RGB", (1800, 1400), (10, 15, 30)); d = ImageDraw.Draw(c); d.text((40, 30), "로드맵 2단계 · 짓기 고치기(판정기준32) — 꼬인 윤곽을 버리지 않고 다시 줄이기", font=F(42), fill=흰)
for j, t in enumerate(("정답", "고치기 전(몸통 버려짐)", "고친 뒤")): d.text((260 + j * 520, 120), t, font=F(32), fill=파, anchor="mm")
for r, k in enumerate((3, 34)):
    y = 150 + r * 420
    c.paste(Image.open(A + "빛_r32_%d_정답.png" % k).convert("RGB").crop((130, 110, 770, 750)).resize((400, 400)), (60, y))
    전 = Image.open(A + "빛_r31_%d_2b.png" % k).convert("RGB").crop((130, 110, 770, 750)).resize((400, 400)) if k == 3 else Image.new("RGB", (400, 400), (25, 30, 45))
    c.paste(전, (580, y)); c.paste(Image.open(A + "빛_r32_%d_고침.png" % k).convert("RGB").crop((130, 110, 770, 750)).resize((400, 400)), (1100, y))
    if k != 3: d.text((780, y + 200), "아무것도 안 지어짐", font=F(30), fill=빨, anchor="mm")
    d.text((1530, y + 160), "%.2f" % R0[k], font=F(40), fill=빨); d.text((1530, y + 220), "→ %.2f" % R1[k], font=F(40), fill=초)
글 = "2b 0 점 10 → 6 · 부피 IoU 0.592 → 0.597 · 판정은 실패(기준 ≤ 3 · 다른 부품 ±0.005)\n남은 0 점 6: 5 개는 부품이 격자 한 칸(0.023)보다 얇아 채점기가 못 잼(정답 지도도 0 점) · 1 개(154)는 모델이 바닥까지 판 것\n다른 부품 변화: 전에 버려지던 홈 · 구멍 윤곽도 이제 깎임 → 2a 30 번 -0.18(틀린 홈이 드러남) · 평균은 ±0.001"
d.multiline_text((40, 1010), 글, font=F(30), fill=흰, spacing=16); c.save(O + "결과32.png"); print("ok")
