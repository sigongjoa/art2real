# -*- coding: utf-8 -*-
"""블렌더 렌더_<장>.png 셋을 캡처 위에 겹치고 키트 사진을 옆에 — python 오버레이시트.py <제목> <출력이름>"""
import json, numpy as np, cv2, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, J
from PIL import Image, ImageDraw, ImageFont
D = J(OUT, "..", "자료"); B = J(OUT, "..", "블렌더"); 기록 = json.load(open(J(D, "자료.json"), encoding="utf-8")); ft = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 20); 판 = []; 제목, 출력 = sys.argv[1], sys.argv[2]
for t in ("02_정면", "02_3-4", "02_옆"):
    im = cv2.imdecode(np.fromfile(기록[t]["파일"], np.uint8), cv2.IMREAD_COLOR); r = cv2.imdecode(np.fromfile(J(B, "렌더_" + t + ".png"), np.uint8), cv2.IMREAD_UNCHANGED)
    x0, y0, x1, y1 = 기록[t]["상자"]; a = (r[:, :, 3:4] / 255.0); vis = (np.full_like(im, 70) * (1 - a) + r[:, :, :3] * a).astype(np.uint8)          # 단색 바탕 위 렌더(겹치지 않음)
    e = cv2.Canny(r[:, :, 3], 50, 150) > 0; sil = im.copy(); sil[e] = (0, 220, 255)
    p = Image.fromarray(np.concatenate([sil[y0:y1, x0:x1], vis[y0:y1, x0:x1]], 1)[:, :, ::-1]); p = p.resize((int(p.width * 420 / p.height), 420)); ImageDraw.Draw(p).text((6, 6), "%s  캡처 | %s" % (t, 제목), font=ft, fill=(0, 0, 0), stroke_width=2, stroke_fill=(255, 255, 255)); 판.append(p)
W = max(p.width for p in 판); 시트 = Image.new("RGB", (W, 3 * 430), (250, 250, 248))
for i, p in enumerate(판): 시트.paste(p, (0, i * 430))
시트.save(J(B, 출력), quality=85); print(J(B, 출력))
