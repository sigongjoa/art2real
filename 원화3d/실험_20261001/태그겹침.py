# -*- coding: utf-8 -*-
"""두 태그가 겹치나 (10-03 사용자 「특징점보다 면 · 서브 에이전트로 3D 로 뽑은 걸로 태그 · 이 태그랑 겹치는지 보자」).
A = Claude 가 원화 먹선 칸에 붙인 이름(각도데이터/이름.json · 2D 칸 기준)
B = 서브 에이전트가 3D 껍질 면(껍질면분할2 A · 3D 모양만)에 붙인 이름(태그/에이전트태그.json · A 를 보지 않고)
화소마다(껍질 틀) 두 이름을 비교: 바탕 이름 같음(좌우 무시) · 좌우까지 같음 · 이름별 IoU · 많이 헷갈린 짝.
출력 태그/겹침.json · 태그/겹침_시트.png(초록 = 같음 · 빨강 = 다름 · 회색 = 한쪽만 이름)"""
import os, json, numpy as np, cv2
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
O = r"G:\art2real\원화3d\out\오메가몬2\지표\각도데이터"; T = os.path.join(O, "태그")
A = json.load(open(os.path.join(O, "이름.json"), encoding="utf-8")); B = json.load(open(os.path.join(T, "에이전트태그.json"), encoding="utf-8"))
def 바탕(t):
    t = t.replace("?", "").replace("(뒤)", "").replace("(뒤에서)", "").replace(" 뒤끝", "").strip(); b = t.split("/")[0].strip()
    b = {"차양 · 눈썹 능선": "차양", "차양": "차양", "미늘3 · 턱": "미늘3", "턱": "미늘3", "안테나 뿌리 · 잔 조각": "안테나 뿌리", "뿔(뒤에서)": "뿔"}.get(b, b)
    return b
def 쪽(t): return t.split("/")[1].replace("?", "").strip() if "/" in t else ""
결과 = {}; tiles = []; f = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 18)
for n in "123456":
    if n not in B: continue
    z = np.load(os.path.join(O, f"{n}.npz")); L = z["라벨"]; ys, xs = np.nonzero(L > 0); y0, x0 = ys.min(), xs.min()
    m = np.load(os.path.join(O, f"판_{n}_Z.npz"))["m"]; py, px = np.nonzero(m)
    cell = L[np.clip(y0 + 2 * py, 0, L.shape[0] - 1), np.clip(x0 + 2 * px, 0, L.shape[1] - 1)]; c2n = {c: nm for nm, cs in A[n].items() for c in cs}
    a = np.array([c2n.get(int(c), "") for c in cell], object)
    F = np.load(os.path.join(T, f"면번호_{n}.npy")); fid = F[py, px]; b = np.array([B[n].get(str(int(i)), {}).get("이름", "") for i in fid], object)
    ab = np.array([바탕(t) if t else "" for t in a]); bb = np.array([바탕(t) if t and not t.startswith("기타") else "" for t in b])
    both = (ab != "") & (bb != ""); same = both & (ab == bb); side = same & (np.array([쪽(t) for t in a]) == np.array([쪽(t) for t in b]))
    iou = {}
    for nm in sorted(set(ab[ab != ""]) | set(bb[bb != ""])):
        I = ((ab == nm) & (bb == nm)).sum(); U = ((ab == nm) | (bb == nm)).sum(); iou[nm] = round(float(I / U), 2) if U else 0.0
    헷 = Counter(zip(ab[both & ~same], bb[both & ~same])).most_common(5)
    결과[n] = {"둘 다 이름": int(both.sum()), "바탕 이름 같음": round(float(same.sum() / max(1, both.sum())), 3), "좌우까지 같음": round(float(side.sum() / max(1, both.sum())), 3),
              "이름별 IoU": iou, "많이 헷갈린 짝(칸 이름 → 에이전트)": [[x, y, int(c)] for (x, y), c in 헷]}
    print(n, {k: v for k, v in 결과[n].items() if k not in ("이름별 IoU",)})
    art = np.asarray(Image.open(os.path.join(O, f"판_{n}_원화.png")).convert("RGB")).copy(); v = (art * 0.35).astype(np.uint8)
    col = np.zeros((len(py), 3), np.uint8); col[both & same] = (60, 220, 60); col[both & ~same] = (230, 50, 50); col[~both] = (140, 140, 140); v[py, px] = (0.4 * art[py, px] + 0.6 * col).astype(np.uint8)
    im = Image.fromarray(v).resize((v.shape[1] * 2, v.shape[0] * 2)); d = ImageDraw.Draw(im); d.text((6, 6), f"{n} · 같음 {결과[n]['바탕 이름 같음']:.0%}", font=f, fill=(255, 232, 58), stroke_width=2, stroke_fill=(0, 0, 0)); tiles.append(im)
W = sum(t.width for t in tiles); out = Image.new("RGB", (W, max(t.height for t in tiles)), (20, 20, 24)); x = 0
for t in tiles: out.paste(t, (x, 0)); x += t.width
out.save(os.path.join(T, "겹침_시트.png")); json.dump(결과, open(os.path.join(T, "겹침.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
