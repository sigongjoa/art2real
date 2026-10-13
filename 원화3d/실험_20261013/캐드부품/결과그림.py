# 2a 결과 그림 — 시험 앞 8 부품(골라내지 않음): 선 그림 · 정답 부품 · 바탕만 · 모델 CAD · IoU · 10-13
import os, json, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import 짓기 as J
A = "G:/art2real/out/설명/구멍/"; O = "G:/art2real/out/설명/캐드부품/"; F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)
if __name__ == "__main__":
    import cadquery as cq, trimesh
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:8]; X = d["X"][te]; Yg = d["Y"][te]; del d
    p = np.load(O + "학습/시험예측.npz"); P, Dp = p["P"][:8], p["D"][:8].astype(np.float32); L = json.load(open(O + "목록.json", encoding="utf-8")); R = np.load(O + "학습/부피IoU.npy")[:8]
    이름 = []
    for k, i in enumerate(te):
        v, f, H = J.정규메시(L[i]); trimesh.Trimesh(v * 20, f).export(A + "r2a_정답_%d.stl" % k)
        for 종, (Y, D) in (("모델", (P[k], Dp[k])), ("바탕", (np.where(P[k] > 0, 1, 0), Dp[k] * 0))):
            s = J.짓기(Y, D, H)
            if s is not None: cq.exporters.export(s.val().scale(20), A + "r2a_%s_%d.stl" % (종, k), tolerance=0.01, angularTolerance=0.1)
        이름 += ["2a_정답_%d" % k, "2a_모델_%d" % k, "2a_바탕_%d" % k]
    subprocess.run(["C:/Program Files/Blender Foundation/Blender 4.0/blender.exe", "-b", "-P", "G:/art2real/원화3d/실험_20261013/구멍/렌더_빛.py", "--"] + 이름, check=True, stdout=subprocess.DEVNULL)
    W, Hh = 1800, 210 + 8 * 230; c = Image.new("RGB", (W, Hh), (10, 15, 30)); dr = ImageDraw.Draw(c)
    dr.text((W // 2, 50), "로드맵 2a — 실제 CAD 부품 · 위 그림 한 장 (시험 앞 8 개 · 골라내지 않음)", font=F(44), fill=(236, 242, 250), anchor="mm")
    for j, t in enumerate(("선 그림(입력)", "정답 부품", "바탕만(윤곽 밀기)", "모델 CAD")): dr.text((175 + j * 340, 140), t, font=F(30), fill=(64, 196, 255), anchor="mm")
    def 렌(n):
        q = A + "빛_r%s.png" % n; return Image.open(q).convert("RGB").crop((130, 110, 770, 750)).resize((210, 210)) if os.path.exists(q) else Image.new("RGB", (210, 210), (40, 40, 50))
    for k in range(8):
        y = 180 + k * 230; c.paste(Image.fromarray((255 - X[k] * 225).astype(np.uint8)).resize((210, 210)).convert("RGB"), (70, y))
        for j, n in enumerate(("정답", "바탕", "모델")): c.paste(렌("2a_%s_%d" % (n, k)), (410 + j * 340, y))
        차 = R[k, 0] - R[k, 1]; dr.text((1460, y + 70), "바탕만 %.2f" % R[k, 1], font=F(30), fill=(150, 160, 180)); dr.text((1460, y + 120), "모델 %.2f (%+.2f)" % (R[k, 0], 차), font=F(32), fill=(110, 220, 140) if 차 > .01 else (255, 100, 100) if 차 < -.01 else (236, 242, 250))
    c.save(O + "결과_2a.png"); print("ok")
