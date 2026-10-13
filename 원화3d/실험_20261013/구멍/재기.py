# 쇼츠 구멍 편 재료 3 — 위 단면 마스크(알파)로 IoU 실제로 잼 · 목표 그림 = r5 단면을 선 그림으로 · 겹침 그림 · 10-13
import numpy as np, json
from PIL import Image, ImageDraw, ImageFilter
O = "G:/art2real/out/설명/구멍/"
m = {r: np.asarray(Image.open(O + "위_r%s.png" % r))[..., 3] > 128 for r in ("0", "1", "2", "3", "4엇", "4", "5", "6")}
iou = {r: float((m[r] & m["5"]).sum() / (m[r] | m["5"]).sum()) for r in m}; json.dump(iou, open(O + "iou.json", "w")); print({r: round(v, 3) for r, v in iou.items()})
# 목표 그림: r5 단면의 윤곽을 손그림처럼(검은 선 · 흰 종이)
t = Image.fromarray((m["5"] * 255).astype(np.uint8)); e = t.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5))
g = Image.new("RGB", t.size, (250, 248, 240)); g.paste((30, 30, 35), (0, 0), e); g.save(O + "그림_목표.png")
# 겹침: AI 단면(파랑 반투명) + 목표 선(빨강)
for r in m:
    c = Image.new("RGB", t.size, (250, 248, 240)); b = Image.new("RGB", t.size, (90, 140, 240)); c.paste(b, (0, 0), Image.fromarray((m[r] * 170).astype(np.uint8)))
    c.paste((220, 40, 40), (0, 0), e); c.save(O + "겹침_r%s.png" % r)
