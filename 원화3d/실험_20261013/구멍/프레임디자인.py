# 학습 타임랩스 쇼츠 프레임 — 템플릿.json 만 고쳐서 다시 그린다 · ChatGPT 디자인 시안(out/설명/구멍/GPT_디자인.png)을 옮김 · 10-13
# python 프레임디자인.py            → out/설명/구멍/프레임디자인.png(에폭 2 · 5 · 8 나란히) · 프레임디자인_한장.png
# 다른 스크립트에서: from 프레임디자인 import 프레임 ; 프레임(k) → 1080×1920 RGB
import json, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
H_ = os.path.dirname(os.path.abspath(__file__)); A = "G:/art2real/out/설명/구멍/"; W, H = 1080, 1920
T = json.load(open(os.environ.get("TEMPLATE", os.path.join(H_, "템플릿.json")), encoding="utf-8")); C = {k: tuple(v) for k, v in T["색"].items()}   # TEMPLATE=다른 json
F = lambda n: ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", n)

def 빛테(c, xy, r, col, 굵기=5, 퍼짐=14):   # 바깥으로 번지는 빛 + 선명한 테
    g = Image.new("RGBA", c.size, (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle(xy, r, outline=col + (255,), width=굵기 + 6)
    c.alpha_composite(g.filter(ImageFilter.GaussianBlur(퍼짐))); ImageDraw.Draw(c).rounded_rectangle(xy, r, outline=col + (255,), width=굵기)
def 점선테(d, xy, r, col, 간=14):
    x0, y0, x1, y1 = xy
    for x in range(x0 + r, x1 - r, 간 * 2): d.line((x, y0, x + 간, y0), fill=col, width=3); d.line((x, y1, x + 간, y1), fill=col, width=3)
    for y in range(y0 + r, y1 - r, 간 * 2): d.line((x0, y, x0, y + 간), fill=col, width=3); d.line((x1, y, x1, y + 간), fill=col, width=3)
def 열기(p, s, 알파=255):
    im = Image.open(p if os.path.isabs(p) else A + p).convert("RGBA"); im = im.resize((s, int(im.height * s / im.width)), Image.LANCZOS)
    if 알파 < 255: im.putalpha(im.split()[3].point(lambda v: v * 알파 // 255))
    return im
def 둥근가장자리(im, r, 흐림):   # 불투명 렌더를 카드 안에 녹이기: 둥근 사각 + 가장자리 흐림
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((흐림 // 2, 흐림 // 2, im.width - 흐림 // 2, im.height - 흐림 // 2), r, fill=255)
    im = im.copy(); im.putalpha(m.filter(ImageFilter.GaussianBlur(max(흐림 / 3, 1)))); return im
def 바탕():
    c = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(c); a, b = C["바탕위"], C["바탕가운데"]
    for y in range(H): t = math.sin(math.pi * y / H); d.line((0, y, W, y), fill=tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3)) + (255,))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); e = ImageDraw.Draw(g); s, al = T["격자"]["간격"], T["격자"]["알파"]   # 격자는 따로 그려 겹침
    for x in range(0, W, s): e.line((x, 0, x, H), fill=(120, 160, 230, al))
    for y in range(0, H, s): e.line((0, y, W, y), fill=(120, 160, 230, al))
    c.alpha_composite(g); return c

def 프레임(k):   # k = 지금 에폭(1부터)
    E = T["에폭"]; n = len(E); e = E[k - 1]; c = 바탕(); d = ImageDraw.Draw(c)
    # 제목
    t = T["제목"]; f = F(t["크기"]); w1, w2 = d.textlength(t["강조"], font=f), d.textlength(t["나머지"], font=f); x = (W - w1 - w2) / 2; y = t["y"]
    g = Image.new("RGBA", c.size); ImageDraw.Draw(g).text((x, y), t["강조"], font=f, fill=C["강조"] + (255,)); c.alpha_composite(g.filter(ImageFilter.GaussianBlur(10)))
    d.text((x, y), t["강조"], font=f, fill=C["강조"]); d.text((x + w1, y), t["나머지"], font=f, fill=C["글"])
    d.text((x - 90, y + 8), "///", font=F(44), fill=C["흐림"]); d.text((x + w1 + w2 + 30, y + 8), "///", font=F(44), fill=C["흐림"])
    g = Image.new("RGBA", c.size); ImageDraw.Draw(g).line((240, y + 102, 840, y + 102), fill=C["강조"] + (255,), width=4); c.alpha_composite(g.filter(ImageFilter.GaussianBlur(6))); d.line((340, y + 102, 740, y + 102), fill=C["강조"], width=3)
    # 시간축(보일칸만큼 창 · 지금 칸 아래에 앞으로 올 칸 하나)
    s = T["시간축"]; v = min(s["보일칸"], n); 처음 = max(0, min(k - v + 1, n - v)); x0, y0, 칸, cw, ch = s["x"], s["y"], s["칸높이"], s["카드폭"], s["카드높이"]; cx = x0 + cw // 2
    for yy in range(y0, y0 + 칸 * v, 16): d.line((cx, yy, cx, yy + 8), fill=C["흐림"], width=4)
    d.line((cx, y0, cx, y0 + 칸 * (k - 1 - 처음) + ch // 2), fill=C["강조"], width=4)
    for j in range(v):
        i = 처음 + j; yy = y0 + 칸 * j; box = (x0, yy, x0 + cw, yy + ch)
        if i < k:
            d.rounded_rectangle(box, 22, fill=C["카드"] + (255,), outline=C["테"], width=3)
            th = 둥근가장자리(열기(T["형태"]["파일"] % E[i]["형태"], ch - 12), 16, 8); c.alpha_composite(th, (x0 + (cw - th.width) // 2, yy + 6))
            if i == k - 1: 빛테(c, box, 22, C["강조"], 5, 14)
            else: d.rounded_rectangle(box, 22, outline=C["테"], width=3)
        else:
            d.rounded_rectangle(box, 22, fill=C["바탕위"] + (255,)); 점선테(d, box, 22, C["흐림"]); d.text((cx, yy + ch // 2), "?", font=F(52), fill=C["흐림"], anchor="mm")   # 속을 채워 시간축 선을 카드 뒤로
        d.text((x0 + cw + 8, yy + ch // 2), E[i].get("눈금", "%d" % (i + 1)), font=F(24), fill=C["강조"] if i == k - 1 else C["흐림"], anchor="lm")
    # 큰 형태 카드
    b = T["큰형태"]; mb = tuple(b["상자"]); d.rounded_rectangle(mb, 36, fill=C["카드"] + (255,))
    big = 둥근가장자리(열기(T["형태"]["파일"] % e["형태"], b["형태크기"]), 40, b["가장자리흐림"]); px_, py_ = b["형태위치"]
    c.alpha_composite(big.crop((0, 0, min(big.width, mb[2] - px_ - 4), min(big.height, mb[3] - py_ - 4))), (px_, py_))
    d.rounded_rectangle(mb, 36, outline=C["테"], width=2); d.text((mb[0] + 40, mb[1] + 30), e.get("이름", "에폭 %d" % k), font=F(46), fill=C["강조"])
    g_ = T["그림카드"]; gb = tuple(g_["상자"]); d.rounded_rectangle(gb, 24, fill=(244, 246, 250, 255)); c.alpha_composite(열기(e.get("그림", T["형태"]["그림"]), gb[2] - gb[0] - 50), (gb[0] + 25, gb[1] + 8)); d.text(((gb[0] + gb[2]) // 2, gb[3] - 22), g_["글"], font=F(28), fill=(40, 44, 56), anchor="mm")
    # 판정 알약(큰 형태 카드 아래 경계에 걸침)
    p = T["판정"]; col = C["강조"] if e["맞음"] else C["틀림"]; 글 = e["판정"]; pw = d.textlength(글, font=F(p["글크기"])) + 150; px = (mb[0] + mb[2] - pw) / 2; pb = (px, p["y"] - 42, px + pw, p["y"] + 42)
    d.rounded_rectangle(pb, 42, fill=(12, 20, 36, 255)); 빛테(c, pb, 42, col, 4, 12); ix, iy = px + 52, p["y"]; d.ellipse((ix - 25, iy - 25, ix + 25, iy + 25), fill=col)
    if e["맞음"]: d.line((ix - 11, iy, ix - 3, iy + 9, ix + 12, iy - 9), fill=(12, 20, 36), width=6)
    else: d.line((ix - 9, iy - 9, ix + 9, iy + 9), fill=(12, 20, 36), width=6); d.line((ix - 9, iy + 9, ix + 9, iy - 9), fill=(12, 20, 36), width=6)
    d.text((px + 92, iy), 글, font=F(p["글크기"]), fill=C["글"], anchor="lm")
    # 겹침 카드
    o = T["겹침카드"]; cb = tuple(o["상자"]); d.rounded_rectangle(cb, 36, fill=C["카드"] + (235,), outline=C["테"], width=2); d.text((cb[0] + 40, cb[1] + 28), o["제목"], font=F(38), fill=C["글"])
    s_ = cb[3] - cb[1] - 110; d.rounded_rectangle((cb[0] + 40, cb[1] + 90, cb[0] + 40 + s_, cb[1] + 90 + s_), 14, fill=(244, 246, 250, 255)); c.alpha_composite(열기(T["형태"]["겹침"] % e["형태"], s_ - 20), (cb[0] + 50, cb[1] + 100))
    for j, (t_, sw) in enumerate(o["범례"]):
        yy = cb[1] + 170 + j * 80; d.rounded_rectangle((cb[0] + 100 + s_, yy - 22, cb[0] + 144 + s_, yy + 22), 8, fill=tuple(sw)); d.text((cb[0] + 164 + s_, yy), t_, font=F(38), fill=C["글"], anchor="lm")
    # 대사(인물 + 말풍선)
    q = T["대사"]
    if q["켜기"]:
        bb = tuple(q["말풍선"]); d.rounded_rectangle(bb, 40, fill=(12, 20, 36, 235)); 빛테(c, bb, 40, (70, 150, 230), 3, 10)
        d.polygon([(bb[0], bb[1] + 110), (bb[0] - 34, bb[1] + 140), (bb[0], bb[1] + 160)], fill=(12, 20, 36)); 줄, 지금 = [], ""   # 말풍선 폭에 맞춰 낱말 단위로 줄 바꿈
        for w in q["예시말"].split(" "):
            if 지금 and d.textlength(지금 + " " + w, font=F(46)) > bb[2] - bb[0] - 90: 줄.append(지금); 지금 = w
            else: 지금 = (지금 + " " + w).strip()
        줄.append(지금); d.multiline_text((bb[0] + 50, (bb[1] + bb[3]) // 2), chr(10).join(줄), font=F(46), fill=C["글"], anchor="lm", spacing=14)
        im = Image.open(q["인물"]).convert("RGBA"); im = im.crop(im.getbbox()); im = im.resize((int(im.width * q["인물높이"] / im.height), q["인물높이"]), Image.LANCZOS); c.alpha_composite(im, (max(0, bb[0] - im.width + 40), H - im.height))
    return c.convert("RGB")

if __name__ == "__main__":
    ks = (2, 5, 8); fs = [프레임(k) for k in ks]
    s = Image.new("RGB", (3 * 540 + 40, 960 + 70), (30, 32, 40)); d = ImageDraw.Draw(s)
    for j, (f, k) in enumerate(zip(fs, ks)): s.paste(f.resize((540, 960), Image.LANCZOS), (10 + j * 550, 60)); d.text((10 + j * 550 + 270, 30), "에폭 %d" % k, font=F(30), fill=(236, 242, 250), anchor="mm")
    s.save(A + "프레임디자인.png"); fs[-1].save(A + "프레임디자인_한장.png"); print("ok")
