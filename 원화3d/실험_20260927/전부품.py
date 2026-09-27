# -*- coding: utf-8 -*-
"""EG RX-78-2 — 부품 나열 사진(d_egx01_j1.jpg)의 모든 부품을 자동으로 떼어 1 단계 모델(실루엣 평판)로 짓는다 (2026-09-27).

    python 전부품.py -> out/키트/EG_RX78/전부품/부품_NN.stl · 목록.json · 갤러리.png

1 단계 = 윤곽을 민 평판 + 가장자리 둥글림. 두께는 가정(짧은 변의 0.22 · 사진에 깊이가 없다). 입체 부품은 2 단계에서 하위 도형으로 분해한다(정강이2.py 방식).
척도: 사진 화소 × 0.17 mm(담뱃갑 없음 — 완성 전고 125 mm 와 조립 다리 사진 길이로 맞춘 어림)."""
import os, sys, json, numpy as np, trimesh, manifold3d as M
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage import measure
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260925")
import 방패 as B
import 디테일대조 as DD
from 메시출력 import 부채나누기

D = r"G:\art2real\원화3d\out\키트\EG_RX78"; OUT = os.path.join(D, "전부품"); os.makedirs(OUT, exist_ok=True)
MM = 0.17                     # mm / 화소 (어림)
최소넓이 = 60                  # 화소

def 전경(a):
    r, g, b = [a[..., i] for i in range(3)]; mx, mn = a.max(-1), a.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
    흰 = (g - r) > 3.0; 색 = sat > 0.28; 어둠 = mx < 150
    m = 흰 | 색 | 어둠
    m[:, :] &= ~((np.arange(a.shape[1])[None, :] > 820) & (np.arange(a.shape[0])[:, None] < 30))      # 워터마크
    return ndimage.binary_fill_holes(ndimage.binary_closing(ndimage.binary_opening(m, iterations=1), iterations=2))
def 색이름(c):
    r, g, b = c; mx, mn = max(c), min(c); s = (mx - mn) / max(mx, 1)
    if mx < 120: return "회색"
    if s < 0.2: return "흰"
    if r > g and r > b: return "노랑" if g > 0.6 * r else "빨강"
    if b > r: return "파랑"
    return "기타"

def 짓기(mask, 두께):
    H, W = mask.shape
    big = ndimage.zoom(mask.astype(float), 4, order=1); big = ndimage.gaussian_filter(big, 2.0) > 0.5
    cs_ = [c for c in measure.find_contours(np.pad(big, 1).astype(float), 0.5) if len(c) > 12]
    polys = []
    for c in cs_:
        c = ndimage.gaussian_filter1d(c[:-1] - 1, 2.0, axis=0, mode="wrap"); P = np.c_[c[:, 1], big.shape[0] - c[:, 0]] / 4 * MM
        P = B.rdp(np.vstack([P, P[:1]]), 0.12)[:-1]
        if len(P) >= 3: polys.append(P)
    cs = M.CrossSection([p.tolist() for p in polys], M.FillRule.EvenOdd)
    m = cs.extrude(두께).refine_to_length(0.4)
    거리 = ndimage.distance_transform_edt(mask) * MM; r = min(0.35 * 두께, 0.8)
    def 둥글(V):
        rr = np.clip(big.shape[0] / 4 - V[:, 1] / MM - 0.5, 0, H - 1); cc = np.clip(V[:, 0] / MM - 0.5, 0, W - 1)
        d = ndimage.map_coordinates(거리, [rr, cc], order=1); 위 = np.clip(V[:, 2] / 두께, 0, 1)
        return np.c_[V[:, 0], V[:, 1], V[:, 2] - 위 * r * (1 - np.sqrt(np.clip(1 - (1 - np.clip(d / r, 0, 1)) ** 2, 0, 1)))]
    return m.warp_batch(둥글)

def 그림(tm, 색, W=160):
    R = np.array([[1, 0, 0], [0, 0.88, 0.47], [0, -0.47, 0.88]], float)
    V = tm.vertices @ R.T; N = tm.face_normals @ R.T
    x0, x1, y0, y1 = V[:, 0].min(), V[:, 0].max(), V[:, 1].min(), V[:, 1].max(); s = max(x1 - x0, y1 - y0) / (W - 10)
    _, tid = DD.래스터(V - [(x0 + x1) / 2, (y0 + y1) / 2, 0], tm.faces, W / 2, W / 2, s, W)
    img = np.ones((W, W, 3)) * 0.93; A = tid >= 0; Lt = np.array([-0.45, 0.5, 0.74]); Lt /= np.linalg.norm(Lt)
    img[A] = np.array(색) * (np.clip(N[tid[A]] @ Lt, 0, 1) * 0.75 + 0.3)[:, None]
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)

if __name__ == "__main__":
    im = np.array(Image.open(os.path.join(D, "d_egx01_j1.jpg")).convert("RGB")).astype(float)
    fg = 전경(im); lab, n = ndimage.label(fg); 목록 = []; 타일 = []
    objs = ndimage.find_objects(lab)
    for i, sl in enumerate(objs, 1):
        m = lab[sl] == i
        if m.sum() < 최소넓이: continue
        pad = 2; y0, x0 = max(sl[0].start - pad, 0), max(sl[1].start - pad, 0); y1, x1 = min(sl[0].stop + pad, im.shape[0]), min(sl[1].stop + pad, im.shape[1])
        m = lab[y0:y1, x0:x1] == i; crop = im[y0:y1, x0:x1]
        c = np.median(crop[m], 0); 이름색 = 색이름(c)
        h_, w_ = m.shape; 두께 = float(np.clip(0.22 * min(h_, w_) * MM, 1.2, 6.0))
        try: mdl = 짓기(m, 두께)
        except Exception as e: print("실패", i, e); continue
        k = len(목록) + 1; fn = os.path.join(OUT, "부품_%02d.stl" % k); g = mdl.to_mesh()
        tm = trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False); tm.export(fn)
        닫힘 = bool(trimesh.load(fn).is_watertight)
        for 양 in (0.02, 0.05):
            if 닫힘: break
            부채나누기(mdl, 양).export(fn); 닫힘 = bool(trimesh.load(fn).is_watertight)
        목록.append(dict(번호=k, 상자=[int(x0), int(y0), int(x1), int(y1)], 넓이px=int(m.sum()), 색=이름색, 색rgb=(c / 255).round(3).tolist(), 크기mm=[round(w_ * MM, 1), round(h_ * MM, 1), round(두께, 1)], 닫힘=닫힘))
        ph = Image.fromarray(crop.astype(np.uint8)); ph.thumbnail((150, 150)); pt = Image.new("RGB", (160, 160), (240, 240, 240)); pt.paste(ph, ((160 - ph.size[0]) // 2, (160 - ph.size[1]) // 2))
        md = Image.fromarray(그림(trimesh.load(fn), c / 255))
        t = Image.new("RGB", (320, 176), "white"); t.paste(pt, (0, 16)); t.paste(md, (160, 16)); ImageDraw.Draw(t).text((4, 2), "%02d %s %.0fx%.0f mm" % (k, 이름색, w_ * MM, h_ * MM), fill=(0, 0, 0)); 타일.append(t)
    json.dump(목록, open(os.path.join(OUT, "목록.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cols = 6; rows = (len(타일) + cols - 1) // cols; G = Image.new("RGB", (320 * cols, 176 * rows), "white")
    for j, t in enumerate(타일): G.paste(t, ((j % cols) * 320, (j // cols) * 176))
    G.save(os.path.join(OUT, "갤러리.png"))
    ov = Image.fromarray(im.astype(np.uint8)); d = ImageDraw.Draw(ov)
    for e in 목록: d.rectangle(e["상자"], outline=(255, 0, 0)); d.text((e["상자"][0] + 2, e["상자"][1] + 1), str(e["번호"]), fill=(255, 0, 0))
    ov.save(os.path.join(OUT, "번호.png"))
    print("부품 %d 개 · 닫힘 %d" % (len(목록), sum(e["닫힘"] for e in 목록)), {c: sum(e["색"] == c for e in 목록) for c in set(e["색"] for e in 목록)})
