# -*- coding: utf-8 -*-
"""_raw/<장면>.png(투명) → 흰 바탕 + 이름표 → v2그림/<장면>.png.  python _마감.py 8-1 [8-2 ...]
그림 영역이 가운데 80% 안인지 찍어 준다."""
import sys, os, json
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
FONT = r"C:\Windows\Fonts\malgunbd.ttf"
for name in sys.argv[1:]:
    raw = os.path.join(HERE, "_raw", name + ".png")
    im = Image.open(raw).convert("RGBA"); W, H = im.size
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    d = ImageDraw.Draw(bg)
    js = raw[:-4] + ".json"
    for t, x, y, s, c in (json.load(open(js, encoding="utf-8")) if os.path.exists(js) else []):
        d.text((x, y), t, font=ImageFont.truetype(FONT, int(s)), fill=c, anchor="mm")
    out = bg.convert("RGB"); out.save(os.path.join(OUT, name + ".png"))
    bb = Image.eval(out.convert("L"), lambda v: 255 if v < 245 else 0).getbbox()
    ok = bb and bb[0] >= W * .1 - 2 and bb[2] <= W * .9 + 2 and bb[1] >= H * .1 - 2 and bb[3] <= H * .9 + 2
    print(name, "bbox", bb, "80% 안" if ok else "⚠ 80% 밖")
