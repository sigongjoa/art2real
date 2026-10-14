# 판정기준37 그림 — 정답 · 예전(위 윤곽 + 모델 2b) · 새 몸통(위 · 앞 · 옆 교차) · 새 몸통 + 모델 2b · 복셀 48 · 10-14
import json, numpy as np
from PIL import Image, ImageDraw, ImageFont
import 짓기 as J, 그림34 as G
O = "G:/art2real/out/설명/캐드부품/"
if __name__ == "__main__":
    d = np.load(O + "데이터.npz"); te = np.nonzero(d["시험"])[0][:200]; e = np.load(O + "데이터_앞옆.npz"); L = json.load(open(O + "목록.json", encoding="utf-8")); B = np.load(O + "학습2b/시험예측.npz")
    고름 = [131, 182, 0, 129]; F = lambda s: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", s)
    열 = ["정답", "예전 (위 윤곽 + 모델)", "새 몸통 (위·앞·옆)", "새 몸통 + 모델"]
    W = Image.new("RGB", (60 + 4 * 310, 120 + len(고름) * 330), (14, 20, 36)); D = ImageDraw.Draw(W)
    D.text((30, 20), "판정기준37 — 몸통을 세 장 교차로 (학습 없음 · 같은 모델)", font=F(40), fill="white")
    for j, t in enumerate(열): D.text((60 + j * 310, 80), t, font=F(24), fill=(240, 200, 90))
    for i, k in enumerate(고름):
        n = te[k]; v, f, H = J.정규메시(L[n]); 정 = J.점유_메시(v, f); Y, Dp = B["P"][k], B["D"][k].astype(np.float32)
        옛 = J.깎기(J.몸통53(d["X"][n], H)[0], Y, Dp, H, True); 새, _ = J.몸통37((d["X"][n], e["F"][n], e["S"][n]), H); 새모 = J.깎기(새, Y, Dp, H, True)
        r = lambda q: (q & 정).sum() / max((q | 정).sum(), 1)
        for j, m in enumerate([정] + [J.점유_캐드(s) for s in (옛, 새, 새모)]):
            W.paste(Image.fromarray(G.그리기(m, 300)), (60 + j * 310, 120 + i * 330))
            if j: D.text((70 + j * 310, 125 + i * 330), "%.2f" % r(m), font=F(30), fill="white")
    W.save(O + "결과37.png"); print("ok")
