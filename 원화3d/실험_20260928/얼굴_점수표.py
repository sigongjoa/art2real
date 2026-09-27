"""오메가몬 얼굴 부위별 점수표 — 바깥 실루엣 IoU 가 못 보는 안쪽 구조를 잰다. 재기만 한다(모델 안 고침).
좌표는 얼굴_점수표.json '좌표'(손 · 확대 격자). 결과는 같은 파일 '결과'.

집계식(계산 전에 적음):
  합친 점수 = 0.5 × 부위 IoU 평균(10 부위 · 없는 부위 = 0)
            + 0.5 × (1 − 평균_k min(d_k, D0) / D0)      D0 = 0.15 H, 없는 기준점 = D0
  d_k = 정규화 틀에서 FRA 기준점까지 거리(머리 높이 H 단위). 턱 끝은 정렬 기준이라 항상 0 → 평균에서 뺀다.
정렬: y = (y − 돔 꼭대기)/(턱 끝 − 돔 꼭대기), x = (x − 축)/머리 외곽 폭 × FRA 의 폭/높이. 눈은 기준점으로 안 씀.
실루엣 IoU(참고)는 옛 자 그대로: 높이만으로 등방 정규화한 머리 외곽(뿔 뺌).
ponytail: 반쪽만 찍어 거울 — 사진의 좌우 비대칭은 못 본다. 필요해지면 양쪽 다 찍기."""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H_ = os.path.dirname(os.path.abspath(__file__))
JP = os.path.join(H_, "얼굴_점수표.json")
OUT = r"G:\art2real\원화3d\out\출력\오메가몬_PG\멋\얼굴_점수표.jpg"
J = json.load(open(JP, encoding="utf-8")); D = J["좌표"]
REF = "FRA"; NAMES = list(D)
PARTS = ["머리외곽", "가운데뿔", "금뿔", "눈구멍", "홍채", "눈동자", "눈두덩", "주둥이", "턱", "볼날개"]
AXIAL = {"머리외곽", "가운데뿔", "주둥이", "턱"}
LMS = ["눈안쪽", "눈꼬리", "눈동자", "코끝", "뿔밑동", "볼날개끝", "금뿔뿌리"]  # 턱끝은 정렬 기준 → 뺌
D0 = 0.15; LINE_W = 0.04
COL = {"머리외곽": (150, 150, 150), "가운데뿔": (90, 90, 255), "금뿔": (255, 170, 0), "눈구멍": (255, 0, 0), "홍채": (0, 220, 60),
       "눈동자": (255, 0, 255), "눈두덩": (0, 200, 255), "주둥이": (160, 80, 0), "턱": (120, 0, 200), "볼날개": (0, 120, 120)}
F = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", s)

def pts_of(v):
    if isinstance(v, dict):
        cx, cy, rx, ry = v["타원"]
        return [[cx + rx * math.cos(t), cy + ry * math.sin(t)] for t in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
    return v
def width(d):
    return 2 * max(abs(x - d["axis"]) for x, _ in d["부위"]["머리외곽"])
ASP = width(D[REF]) / (D[REF]["chin"] - D[REF]["top"])
def norm(d, p, iso=False):
    h = d["chin"] - d["top"]
    sx = 1 / h if iso else ASP / width(d)
    return [((x - d["axis"]) * sx, (y - d["top"]) / h) for x, y in p]
def mir(p): return [(-x, y) for x, y in p]

N = 900; SC = N / 3.2  # 틀: x −1.6..1.6 · y −1.7..1.5
def px(p): return [((x + 1.6) * SC, (y + 1.7) * SC) for x, y in p]
def raster(d, part, iso=False):
    v = d["부위"].get(part)
    if v is None: return None
    p = norm(d, pts_of(v), iso); im = Image.new("L", (N, N)); dr = ImageDraw.Draw(im)
    if part == "눈두덩":
        for q in (p, mir(p)): dr.line(px(q), fill=1, width=max(1, int(LINE_W * SC)))
    elif part in AXIAL: dr.polygon(px(p + mir(p)[::-1]), fill=1)
    else:
        dr.polygon(px(p), fill=1); dr.polygon(px(mir(p)), fill=1)
    return np.array(im, bool)
def iou(a, b): return float((a & b).sum() / max((a | b).sum(), 1))
def shape(d, part):  # 왼쪽 하나(축부위는 온쪽)의 중심 · 넓이 · 가로세로 비 · 주축 각
    m = raster(d, part)
    if m is None: return None
    if part not in AXIAL: m = m.copy(); m[:, N // 2:] = False
    ys, xs = np.nonzero(m)
    if len(xs) < 3: return None
    c = np.array([xs.mean(), ys.mean()]) / SC - [1.6, 1.7]
    w, v = np.linalg.eigh(np.cov(np.vstack([xs, ys])))
    ang = math.degrees(math.atan2(v[1, 1], v[0, 1])) % 180
    return dict(cx=c[0], cy=c[1], area=len(xs) / SC ** 2, bw=(xs.max() - xs.min() + 1) / SC, bh=(ys.max() - ys.min() + 1) / SC,
                angle=ang if ang <= 90 else ang - 180)

def shape_iou(d, part):  # 보조: 중심을 맞춘 뒤의 IoU — 위치를 빼고 모양 · 크기만 (집계식에는 안 들어감)
    a, b = raster(D[REF], part), raster(d, part)
    if b is None: return 0.0
    if part not in AXIAL: a = a.copy(); b = b.copy(); a[:, N // 2:] = False; b[:, N // 2:] = False
    ca, cb = [np.array(np.nonzero(m)).mean(1) for m in (a, b)]; dy, dx = np.round(ca - cb).astype(int)
    return iou(a, np.roll(np.roll(b, dy, 0), dx, 1))

R = {}
for n in NAMES:
    d = D[n]; r = dict(부위={}, 기준점={})
    for p in PARTS:
        a, b = raster(D[REF], p), raster(d, p)
        if b is None: r["부위"][p] = dict(있음=False, IoU=0.0); continue
        sa, sb = shape(D[REF], p), shape(d, p)
        r["부위"][p] = dict(있음=True, IoU=round(iou(a, b), 3),
                          중심차_pct=round(100 * math.hypot(sb["cx"] - sa["cx"], sb["cy"] - sa["cy"]), 1),
                          넓이비=round(sb["area"] / sa["area"], 2),
                          가로세로=round(sb["bw"] / sb["bh"], 2), 가로세로_FRA=round(sa["bw"] / sa["bh"], 2),
                          기울기차_deg=round(((sb["angle"] - sa["angle"] + 90) % 180) - 90, 1))
    ds = []
    for k in LMS:
        q = d["기준점"].get(k)
        if q is None: r["기준점"][k] = None; ds.append(D0); continue
        (x0, y0), (x1, y1) = norm(D[REF], [D[REF]["기준점"][k]])[0], norm(d, [q])[0]
        dd = math.hypot(x1 - x0, y1 - y0); r["기준점"][k] = round(100 * dd, 1); ds.append(min(dd, D0))
    raw = [v for v in r["기준점"].values() if v is not None]
    r["부위IoU평균"] = round(float(np.mean([r["부위"][p]["IoU"] for p in PARTS])), 3)
    r["기준점거리_평균pct"] = round(float(np.mean(raw)), 1); r["기준점거리_최대pct"] = max(raw)
    r["기준점항"] = round(1 - float(np.mean(ds)) / D0, 3)
    r["합친점수"] = round(0.5 * r["부위IoU평균"] + 0.5 * r["기준점항"], 3)
    r["모양IoU평균_중심맞춤"] = round(float(np.mean([shape_iou(d, p) for p in PARTS])), 3)
    r["부위모양IoU"] = {p: round(shape_iou(d, p), 3) for p in PARTS}
    r["실루엣IoU"] = round(iou(raster(D[REF], "머리외곽", True), raster(d, "머리외곽", True)), 3)
    r["없는부위"] = [p for p in PARTS if not r["부위"][p]["있음"]]
    r["없는기준점"] = [k for k in LMS if r["기준점"][k] is None]
    R[n] = r
J["결과"] = dict(집계식="0.5*부위IoU평균(없음=0) + 0.5*(1 - mean(min(d,0.15H))/0.15H) · 턱끝 제외 · 기준=FRA mh_12", 얼굴=R)
json.dump(J, open(JP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ── 그림: 윗줄 = 얼굴 + 부위 마스크, 아랫줄 = 표 ──
P = 296; W = 8 * (P + 4) + 4; img = Image.new("RGB", (W, P + 60 + 40 * (len(NAMES) + 1) + 70), "white"); dr = ImageDraw.Draw(img)
for i, n in enumerate(NAMES):
    d = D[n]; im = Image.open(d["file"]).convert("RGBA")
    bg = Image.new("RGBA", im.size, (200, 200, 200, 255)); bg.alpha_composite(im); im = bg
    if d["flip"]: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    h = d["chin"] - d["top"]; w2 = width(d) / 2; m = 0.12 * h
    box = [d["axis"] - w2 - m, d["top"] - 0.45 * h, d["axis"] + w2 + m, d["chin"] + m]
    side = max(box[2] - box[0], box[3] - box[1]); cx = d["axis"]; box = [cx - side / 2, box[1], cx + side / 2, box[1] + side]
    k = 3 * P / side; crop = im.crop([int(v) for v in box]).resize((3 * P, 3 * P), Image.LANCZOS)
    ov = Image.new("RGBA", crop.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    T = lambda p: [((x - int(box[0])) * k, (y - int(box[1])) * k) for x, y in p]
    M = lambda p: [[2 * d["axis"] - x, y] for x, y in p]
    for p in PARTS:
        v = d["부위"].get(p)
        if v is None: continue
        q = pts_of(v); c = COL[p]
        if p == "눈두덩":
            for s in (q, M(q)): od.line(T(s), fill=c + (255,), width=5)
        elif p == "머리외곽": od.line(T(q + M(q)[::-1] + q[:1]), fill=c + (255,), width=4)
        elif p in AXIAL: od.polygon(T(q + M(q)[::-1]), fill=c + (90,), outline=c + (255,))
        else:
            for s in (q, M(q)): od.polygon(T(s), fill=c + (110,), outline=c + (255,))
    for kname, q in d["기준점"].items():
        if q is None: continue
        for s in ([q], M([q])):
            (x, y), = T(s); od.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(0, 0, 0, 255), width=2)
    crop.alpha_composite(ov); ox = 4 + i * (P + 4)
    img.paste(crop.convert("RGB").resize((P, P), Image.LANCZOS), (ox, 36))
    dr.text((ox + 4, 2), f"{n}  {R[n]['합친점수']:.2f}", fill="black", font=F(24))
y = P + 44
x = 4
for p in PARTS:
    dr.rectangle([x, y, x + 18, y + 18], fill=COL[p]); dr.text((x + 22, y - 4), p, fill="black", font=F(20)); x += 40 + 21 * len(p)
dr.text((x + 10, y - 4), "○ 기준점", fill="black", font=F(20))
y += 34; cols = [("얼굴", 150), ("합친 점수", 170), ("부위 IoU 평균", 230), ("기준점 거리 평균/최대 %H", 420), ("실루엣 IoU(참고)", 270), ("모양 IoU(중심 맞춤 · 보조)", 400), ("없는 부위", 800)]
x = 10
for c, w in cols: dr.text((x, y), c, fill=(0, 0, 160), font=F(24)); x += w
for n in NAMES:
    y += 40; r = R[n]; x = 10
    vals = [n + ("(정답)" if n == REF else ""), f"{r['합친점수']:.3f}", f"{r['부위IoU평균']:.3f}", f"{r['기준점거리_평균pct']:.1f} / {r['기준점거리_최대pct']:.1f}" + (f"  (없음 {len(r['없는기준점'])})" if r['없는기준점'] else ""),
            f"{r['실루엣IoU']:.3f}", f"{r['모양IoU평균_중심맞춤']:.3f}", f"{len(r['없는부위'])}  " + " · ".join(r["없는부위"])]
    for (c, w), v in zip(cols, vals): dr.text((x, y), v, fill="black", font=F(24)); x += w
dr.text((10, y + 44), "합친 = 0.5 × 부위 IoU 평균(없음 = 0) + 0.5 × (1 - 평균 min(d, 0.15H)/0.15H) · 정렬 = 머리 외곽 폭 · 돔 꼭대기 · 턱 끝 · 기준 = FRA mh_12 · FRA2 = mh_11(위 기준)",
        fill=(90, 90, 90), font=F(20))
img.save(OUT, quality=90)

print(f"{'얼굴':6} {'합친':>6} {'부위IoU':>7} {'기준점항':>7} {'거리평균':>7} {'최대':>6} {'실루엣':>6} 없는부위")
for n in NAMES:
    r = R[n]; print(f"{n:6} {r['합친점수']:6.3f} {r['부위IoU평균']:7.3f} {r['기준점항']:7.3f} {r['기준점거리_평균pct']:7.1f} {r['기준점거리_최대pct']:6.1f} {r['실루엣IoU']:6.3f} 모양{r['모양IoU평균_중심맞춤']:6.3f} {len(r['없는부위'])} {r['없는부위']}")
for n in NAMES:
    print("\n" + n); [print("  ", p, v) for p, v in R[n]["부위"].items()]; print("   기준점", R[n]["기준점"]); print("   모양IoU", R[n]["부위모양IoU"])
s = lambda n: R[n]["합친점수"]
assert s("FRA") > 0.999                                  # 자기 자신 = 1 (좌표 파일이 망가지면 깨짐)
lose = {"위 기준(FRA2)이 우리 것 전부보다 높다": s("FRA2") > max(s(n) for n in ["옛", "1차", "2차", "3차", "눈4"]),
        "달걀(2차)이 3차 · 눈4 보다 낮다": s("2차") < min(s("3차"), s("눈4")),
        "옛 얼굴이 3차 · 눈4 보다 낮다": s("옛") < min(s("3차"), s("눈4"))}
print(); [print(("통과 " if v else "실패 ") + k) for k, v in lose.items()]
