# -*- coding: utf-8 -*-
"""쇼츠 37 프레임(1080×1920) — 줄마다 「왼쪽 정답/사람 부품(노랑) | 오른쪽 AI(파랑)」 세 줄 · 2 번째 줄은 실물 학습 타임랩스
python runs/실물학습/쇼츠37.py <시간표.json> <frames>"""
import os, sys, json, glob, numpy as np, trimesh
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); T0 = os.path.dirname(R)
sys.path[:0] = [os.path.join(R, "조각0"), os.path.join(T0, "s0"), os.path.join(T0, "s0", "stub")]
from PIL import Image, ImageDraw, ImageFont
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n); T = 400; RR = "G:/art2real/원화3d/out/레퍼런스/사람분할/"
부품 = [r["부품"] for k in range(3) for r in json.load(open(os.path.join(R, "사전0", "결과%d.json" % k), encoding="utf-8"))]
BLUE = [0.45, 0.68, 0.98]

def 그림(a):   # (종류, 값, 파랑) → 타일
    kind, v, blue = a
    from render import render
    try:
        if kind == "실물": m = trimesh.load(RR + v, force="mesh"); lo, hi = m.bounds; m.apply_translation(-(lo + hi) / 2); m.apply_scale(2 / (hi - lo).max())
        elif kind == "stl": m = trimesh.load(v)
        elif kind == "조각": from 평가 import 메시; m = 메시(v)
        elif kind == "손":
            sys.path.insert(0, os.path.join(T0, "s0")); from 부품사전 import 짓기; import cadquery as cq, tempfile
            p = os.path.join(tempfile.gettempdir(), "손_%d.stl" % os.getpid()); cq.exporters.export(짓기(open(v, encoding="utf-8").read()), p); m = trimesh.load(p)
            lo, hi = m.bounds; m.apply_translation(-(lo + hi) / 2); m.apply_scale(2 / (hi - lo).max())
        m.apply_scale(0.42); m.apply_translation([.5] * 3)
        return np.asarray(render(np.asarray(m.vertices), np.asarray(m.faces), [1, 0.6, 0.8], img_size=T, cols=np.tile(BLUE, (len(m.faces), 1)) if blue else None))
    except Exception as e: print("못 그림", kind, str(e)[:60]); return np.full((T, T, 3), 245, np.uint8)

if __name__ == "__main__":
    from multiprocessing import Pool
    TL = json.load(open(sys.argv[1], encoding="utf-8"))["lines"]; O = sys.argv[2]; os.makedirs(O, exist_ok=True)
    E3 = json.load(open(os.path.join(R, "조각3", "평가.json"), encoding="utf-8")); 합 = [1, 4, 37]
    각 = [8, 11, 35]; 실패 = [32, 27, 14]; SN = sorted(glob.glob(os.path.join(H, "스냅", "*.json"))); SNAPI = [0, 2, 6, 8, 14, 32]; 타 = [6, 8, 32]
    일 = {}
    for i in 합: 일[("합정", i)] = ("조각", json.load(open(os.path.join(R, "조각0", "정답", "%04d.json" % (3600 + i)), encoding="utf-8")), False); 일[("합AI", i)] = ("조각", E3["예측"][i], True)
    for i in 각 + 실패 + 타: 일[("사람", i)] = ("실물", 부품[i], False)
    for i in 각: 일[("v1", i)] = ("stl", os.path.join(R, "실물0", "디코더", "%02d_예측.stl" % i), True); 일[("손", i)] = ("손", os.path.join(R, "사전0", "%d_%02d.txt" % (i // 12, i % 12)), False)
    for i in 각 + 실패: 일[("v3", i)] = ("stl", os.path.join(R, "실물0", "디코더v3", "%02d_예측.stl" % i), True)
    snaps = [json.load(open(p, encoding="utf-8")) for p in SN]
    for k, s in enumerate(snaps):
        for i in 타: 일[("스냅", k, i)] = ("조각", s["예측"][SNAPI.index(i)], True)
    키 = list(일)
    with Pool(2) as pool: 타일 = dict(zip(키, pool.map(그림, [일[k] for k in 키])))
    def 판(rows, title, cols=("사람 부품", "AI"), sub=None):
        im = Image.new("RGB", (1080, 1920), (30, 31, 36)); d = ImageDraw.Draw(im)
        d.text((540, 120), title, font=F(70), fill="white", anchor="mm")
        if sub: d.text((540, 195), sub, font=F(40), fill=(240, 120, 110), anchor="mm")
        for c, t in enumerate(cols): d.text((70 + c * 540 + T // 2, 262), t, font=F(32), fill=(240, 190, 60) if c == 0 else (120, 170, 250), anchor="mm")
        for r, (a, b) in enumerate(rows):
            for c, k in enumerate((a, b)):
                m = Image.new("L", (T, T), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, T - 1, T - 1), 28, fill=255)
                im.paste(Image.fromarray(타일[k]), (70 + c * 540, 290 + r * 420), m)
        return im
    판들 = {"합": 판([(("합정", i), ("합AI", i)) for i in 합], "연습 문제", ("정답", "AI"), sub="400 / 400 맞힘"),
           "실1": 판([(("사람", i), ("v1", i)) for i in 각], "진짜 피규어 부품", sub="1 / 36 맞힘"),
           "v3": 판([(("사람", i), ("v3", i)) for i in 각], "기울인 조각 + 실물 학습"),
           "실패": 판([(("사람", i), ("v3", i)) for i in 실패], "그래도 안 되는 것"),
           "손": 판([(("사람", i), ("손", i)) for i in 각], "사람(Claude)이 직접 고른 조각", ("사람 부품", "손으로"))}
    def 스냅판(k):
        s = snaps[k]; return 판([(("사람", i), ("스냅", k, i)) for i in 타], "진짜 부품으로 학습 중", sub="스텝 %s" % format(s["스텝"], ","))
    for fr in range(1, TL[-1][1] + 1):
        li = next(j for j, (a, b) in enumerate(TL) if a <= fr <= b); a, b = TL[li]; u = (fr - a) / max(1, b - a)
        if li == 0: im = 판들["합"] if u < .45 else 판들["실1"]
        elif li == 1: im = 판들["실1"]
        elif li == 2: im = 스냅판(min(len(snaps) - 1, int(u * 1.25 * (len(snaps) - 1))))
        elif li == 3: im = 판들["v3"]
        elif li == 4: im = 판들["실패"]
        else: im = 판들["손"]
        im.save(os.path.join(O, "%04d.png" % fr))
    print("ok", TL[-1][1])
