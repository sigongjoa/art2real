"""부품별 IoU — verify_parts.py 가 낸 렌더를 원화의 같은 창과 겹친다."""
import json, sys, numpy as np
from PIL import Image
d = sys.argv[1] if len(sys.argv) > 1 else "art3d_out"
vo = sys.argv[2] if len(sys.argv) > 2 else "verify_out"
env = json.load(open(sys.argv[3], encoding="utf-8"))
spec = json.load(open(f"{d}/buildspec.json", encoding="utf-8"))
fr = json.load(open(f"{vo}/frames.json")); lab = np.load(f"{d}/labels.npy")
f = spec["px_to_world"]; k = f["world_per_px"]; ytop = f["y_top_px"]
ztop = f["z_top"]; cx0 = env["px"]["center_x"]
rows = []
for nm, fi in fr.items():
    m = lab == fi["region"]
    if not m.any(): continue
    s, R = fi["span"], fi["res"]
    box = (round(cx0 + (fi["cx"] - s/2)/k), round(ytop + (ztop - (fi["cz"] + s/2))/k),
           round(cx0 + (fi["cx"] + s/2)/k), round(ytop + (ztop - (fi["cz"] - s/2))/k))
    ref = np.asarray(Image.fromarray((m*255).astype(np.uint8), "L").crop(box)
                     .resize((R, R), Image.NEAREST)) > 127
    mod = np.asarray(Image.open(f"{vo}/{nm}.png"))[..., 3] > 40
    i, u = (ref & mod).sum(), (ref | mod).sum()
    if u < 50: continue
    rows.append({"id": nm, "iou": round(float(i/u), 3), "make": fi["make"],
                 "ref_px": int(ref.sum()), "model_px": int(mod.sum()),
                 "pass": bool(i/u >= 0.7)})
rows.sort(key=lambda r: r["iou"])
v = np.array([r["iou"] for r in rows])
ratio = [r["model_px"]/max(1, r["ref_px"]) for r in rows]
print(f"부품 {len(rows)}개 · 통과(>=0.7) {int((v>=0.7).sum())} · 실패 {int((v<0.7).sum())} "
      f"· 중앙값 {np.median(v):.3f} · 면적비 중앙값 {np.median(ratio):.2f}")
for r in rows[:6]:
    print(f" {r['iou']:.3f}  {r['id']:22s}{str(r['make']):7s} 원화{r['ref_px']:6d} "
          f"모델{r['model_px']:6d} 비{r['model_px']/max(1,r['ref_px']):.2f}")
json.dump(rows, open(f"{vo}/iou.json", "w"), indent=1)
