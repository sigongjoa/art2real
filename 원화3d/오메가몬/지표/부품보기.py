# -*- coding: utf-8 -*-
"""부품 보기 — 부품 21 개를 **같은 색**으로 세 시점에 오버레이 + 부품 × 시점 가시성 표 (09-29 「부품별로 색상 오버레이해서 어떤 부품인지 보여주고, 다음 이미지에서 보이는지 보라고 · 시점 변화 고려」).
    python 부품보기.py -> out/오메가몬2/지표/부품보기.png (세 시점 나란히 + 범례) · 부품보기.json (부품 × 시점: 보이는 화소 · 캡처 실루엣 안 비율)
시점마다 그 시점의 자세(회전 · 배율 · 원근 k · 자세2.json)로 21 부품 래스터 → id 지도 → 색 오버레이. 보임 = 그 시점 렌더에서 화소 ≥ 80. 캡처 지지 = 그 부품 화소 중 캡처 실루엣 안 비율.
"""
import os, sys, json, glob
import numpy as np, cv2, trimesh
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
from 부품투영 import 단위, 찍기, 읽기
from 자세 import 캡처 as 캡처2D
자세 = json.load(open(J(OUT, "자세2.json"), encoding="utf-8")); D6 = J(OUT, "..", "머리", "단계4")
장들 = {"정면 yt_172": "정면", "3/4 M04": "3-4", "옆 yt_235": "옆"}
부품 = [(os.path.basename(f)[:-4], trimesh.load(f, process=False, force="mesh")) for f in sorted(glob.glob(J(D6, "*.stl"))) if os.path.basename(f) != "프레임.stl"]
팔레트 = [(230, 25, 75), (60, 180, 75), (255, 225, 25), (0, 130, 200), (245, 130, 48), (145, 30, 180), (70, 240, 240), (240, 50, 230), (210, 245, 60), (250, 190, 212), (0, 128, 128), (220, 190, 255), (170, 110, 40), (255, 250, 200), (128, 0, 0), (170, 255, 195), (128, 128, 0), (255, 215, 180), (0, 0, 128), (128, 128, 128), (255, 255, 255)]
색 = {n: 팔레트[i % len(팔레트)] for i, (n, _) in enumerate(부품)}
def id지도(자, shape):
    ID = np.zeros(shape, np.int32); 삼 = []
    for i, (n, m) in enumerate(부품, 1):
        uv, z = 찍기(단위(np.asarray(m.vertices, float)), 자); uv = np.round(uv).astype(np.int32)
        for tri in m.faces: 삼.append((z[tri].mean(), i, uv[tri]))
    삼.sort(key=lambda t: -t[0])
    for _, i, q in 삼: cv2.fillPoly(ID, [q], int(i))
    return ID
if __name__ == "__main__":
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 16); 판들 = []; 표 = {n: {} for n, _ in 부품}
    for 이름, 태그 in 장들.items():
        f, _ = 캡처2D[이름]; im = 읽기(J(장면, f)); H, W = im.shape[:2]; ID = id지도(자세[이름], (H, W))
        c_ = np.load(J(OUT, "윤곽2_%s_전체.npy" % 태그)); sil = np.zeros((H, W), np.uint8); cv2.fillPoly(sil, [c_.astype(np.int32)], 1); sil = sil > 0
        ov = im.copy()
        for i, (n, _) in enumerate(부품, 1):
            m = ID == i; px = int(m.sum()); 표[n][태그] = dict(화소=px, 보임=px >= 80, 캡처안=round(float((m & sil).sum() / px), 2) if px else None)
            if px: ov[m] = 색[n][::-1]
        vis = cv2.addWeighted(im, 0.35, ov, 0.65, 0); 경계 = cv2.Laplacian(ID.astype(np.float32), cv2.CV_32F) != 0; vis[경계] = (0, 0, 0)
        cs, _ = cv2.findContours(sil.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cv2.drawContours(vis, cs, -1, (255, 255, 255), 2)
        ys, xs = np.nonzero((ID > 0) | sil); y0, y1, x0, x1 = max(0, ys.min() - 30), ys.max() + 30, max(0, xs.min() - 30), xs.max() + 30
        crop = vis[y0:y1, x0:x1]; crop = cv2.resize(crop, (int(crop.shape[1] * 620 / crop.shape[0]), 620)); p = Image.fromarray(crop[:, :, ::-1]); ImageDraw.Draw(p).text((8, 6), "%s  yaw %.0f pitch %.0f roll %.0f  s %.1f" % (태그, 자세[이름]["yaw"], 자세[이름]["pitch"], 자세[이름]["roll"], 자세[이름]["s"]), font=ft, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0)); 판들.append(p)
    # 범례 + 표
    L = Image.new("RGB", (300, 620), (250, 250, 248)); d = ImageDraw.Draw(L); d.text((8, 6), "부품   정면 3/4 옆  (○보임 ·숫자=캡처안)", font=ft, fill=(0, 0, 0))
    for k, (n, _) in enumerate(부품):
        y = 30 + k * 27; d.rectangle((8, y, 26, y + 18), fill=색[n]); d.text((32, y), n, font=ft, fill=(0, 0, 0))
        for j, 태그 in enumerate(장들.values()):
            r = 표[n][태그]; d.text((150 + j * 50, y), ("%.0f" % (100 * r["캡처안"]) if r["보임"] else "—"), font=ft, fill=(0, 0, 0) if r["보임"] else (160, 160, 160))
    S = Image.new("RGB", (sum(p.width for p in 판들) + L.width + 40, 620), (250, 250, 248)); x = 0
    for p in 판들: S.paste(p, (x, 0)); x += p.width + 10
    S.paste(L, (x, 0)); S.save(J(OUT, "부품보기.png")); json.dump(표, open(J(OUT, "부품보기.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(J(OUT, "부품보기.png")); print("%-10s %6s %6s %6s" % ("부품", "정면", "3/4", "옆"))
    for n, _ in 부품: print("%-10s " % n + " ".join("%6s" % (("%d%%" % (100 * 표[n][t]["캡처안"])) if 표[n][t]["보임"] else "—") for t in 장들.values()))
