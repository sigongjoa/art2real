# -*- coding: utf-8 -*-
"""쇼츠 38 프레임 — 줄마다 「사람 부품(노랑) | 결과(파랑)」 세 줄: 학습 AI → 윤곽 교차 → 오목 못 함 → 깊이 깎기 → 곡면 부스러기
python runs/윤곽2/쇼츠38.py <시간표.json> <frames>"""
import os, sys, json, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R); sys.path[:0] = [os.path.join(T0, "s0")]
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); T = 400; RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
부품 = [r["부품"] for k in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % k), encoding="utf-8"))]
def 그림(a):
    kind, v, blue = a
    from render import render
    try:
        m = trimesh.load(RR + v if kind == "실물" else v, force="mesh"); lo, hi = m.bounds; m.apply_translation(-(lo + hi) / 2); m.apply_scale(0.84 / (hi - lo).max()); m.apply_translation([.5] * 3)
        return np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), [1, 0.6, 0.8], img_size=T, cols=np.tile([0.45, 0.68, 0.98], (len(m.faces), 1)) if blue else None))
    except Exception as e: print("못 그림", v[-30:], str(e)[:50]); return np.full((T, T, 3), 245, np.uint8)
if __name__ == "__main__":
    from multiprocessing import Pool
    TL = json.load(open(sys.argv[1], encoding="utf-8"))["lines"]; O = sys.argv[2]; os.makedirs(O, exist_ok=True)
    P = {"AI": ([2, 8, 17], "v3", "학습시킨 AI", "2 / 36"), "교차": ([2, 8, 17], "교차", "그림자 세 장 교차 · 학습 없음", "24 / 36"),
         "오목": ([7, 19, 24], "교차", "안으로 파인 곳은 못 봄", None), "깎음": ([7, 19, 24], "깎음", "+ 깊이 차이로 파냄", "32 / 35"), "곡면": ([5, 25, 35], "깎음", "둥근 면은 부스러기", None)}
    경로 = lambda kind, i: {"v3": os.path.join(R, "실물0", "디코더v3", "%02d_예측.stl" % i), "교차": os.path.join(R, "윤곽0", "결과", "%02d_교차.stl" % i), "깎음": os.path.join(H, "결과", "%02d_깎음.stl" % i)}[kind]
    일 = {}
    for ids, kind, _, _ in P.values():
        for i in ids: 일[("사람", i)] = ("실물", 부품[i], False); 일[(kind, i)] = ("stl", 경로(kind, i), True)
    키 = list(일)
    with Pool(2) as pool: 타일 = dict(zip(키, pool.map(그림, [일[k] for k in 키])))
    def 판(ids, kind, title, sub):
        im = Image.new("RGB", (1080, 1920), (30, 31, 36)); d = ImageDraw.Draw(im)
        d.text((540, 120), title, font=F(62), fill="white", anchor="mm")
        if sub: d.text((540, 195), sub + " 통과", font=F(42), fill=(240, 120, 110), anchor="mm")
        for c, t in enumerate(("사람 부품", "결과")): d.text((70 + c * 540 + T // 2, 262), t, font=F(32), fill=(240, 190, 60) if c == 0 else (120, 170, 250), anchor="mm")
        for r, i in enumerate(ids):
            for c, k in enumerate((("사람", i), (kind, i))):
                m = Image.new("L", (T, T), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, T - 1, T - 1), 28, fill=255); im.paste(Image.fromarray(타일[k]), (70 + c * 540, 290 + r * 420), m)
        return im
    판들 = {k: 판(*v) for k, v in P.items()}; 줄 = ["AI", "교차", "교차", "오목", "깎음", "곡면"]
    for fr in range(1, TL[-1][1] + 1):
        li = next(j for j, (a, b) in enumerate(TL) if a <= fr <= b); 판들[줄[li]].save(os.path.join(O, "%04d.png" % fr))
    print("ok", TL[-1][1])
