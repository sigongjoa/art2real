# -*- coding: utf-8 -*-
"""깊이 히트맵을 원화 위에 겹친다(10-01 「heatmap 은 원화랑 오버레이한 걸 보여 주는 게 좋겠다」).
    python 깊이겹침.py -> out/깊이카드/겹침_da2b.png · 겹침_시차.png (02_정면 상자로 자름)
마스크 = 시차 깊이가 있는 곳(머리 윤곽) · 둘 다 같은 마스크 · turbo(빨강·노랑 = 가까움 · 파랑 = 멀리) · 마스크 안 2~98 백분위로 늘림."""
import json, numpy as np, cv2
O = r"G:\art2real\원화3d\out\깊이카드"
d = json.load(open(r"G:\art2real\원화3d\out\오메가몬2\자료\자료.json", encoding="utf-8"))["02_정면"]; x0, y0, x1, y1 = d["상자"]
art = cv2.imdecode(np.fromfile(d["파일"], np.uint8), cv2.IMREAD_COLOR); m = np.load(O + r"\시차_정면.npy") != 0
for f in ("da2b", "시차"):
    z = np.load(O + "\\%s_정면.npy" % f); lo, hi = np.percentile(z[m], [2, 98]); n = np.clip((z - lo) / (hi - lo), 0, 1)
    col = cv2.applyColorMap((n * 255).astype(np.uint8), cv2.COLORMAP_TURBO); o = art.copy(); o[m] = (0.4 * art[m] + 0.6 * col[m]).astype(np.uint8)
    cv2.imencode(".png", o[y0:y1, x0:x1])[1].tofile(O + "\\겹침_%s.png" % f); print(O + "\\겹침_%s.png" % f)
