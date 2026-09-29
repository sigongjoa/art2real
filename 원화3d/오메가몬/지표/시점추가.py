# -*- coding: utf-8 -*-
"""시점 추가 — 02 캡처를 껍질에 더한다 (2026-09-30 「더하면 괜찮게 나올 것 같은데?」).
    python 시점추가.py -> out/오메가몬2/자료/<장>_실루엣.png · <장>_모름.png(가린 것 · 망토 · 방패 · 사람) · 시점추가.json(자세) · 시점추가.png(실루엣 | 껍질 재투영)
장마다 손으로 정한 것: 상자 · 실루엣 방식 · 모름 다각형(가린 것은 깎지 않는다) · 대략 yaw/pitch. 자세는 현재 껍질(면패치_살.npz)에 실루엣 IoU 로 맞춘다(자세2 와 같은 방식 · 모델 대신 껍질).
"""
import os, sys, json
import numpy as np, cv2
from scipy.optimize import minimize
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J
from 윤곽 import 실루엣, 실루엣_먹선벽, 읽기
from 부품투영 import 찍기
from 자세2 import R_of
D = J(OUT, "..", "자료")
대상 = {   # 장: 파일 · 상자 · 방식 · 모름 다각형들 · (yaw°, pitch°)
    "02_3-4위": ("yt_140.5_얼굴_3-4_망토.jpg", (360, 0, 800, 350), "밝기", [[(0, 300), (1188, 300), (1188, 667), (0, 667)], [(740, 150), (1188, 150), (1188, 667), (740, 667)]], (-25, -15)),
    "02_3-4옆": ("yt2_039.0_상체_3-4옆.jpg", (320, 20, 660, 270), "먹선벽", [[(520, 0), (640, 0), (640, 110), (520, 110)]], (-55, 10)),
    "02_위": ("yt_149.5_상체_위에서.jpg", (580, 0, 770, 210), "밝기", [[(740, 0), (1188, 0), (1188, 120), (740, 120)]], (-15, -50)),
    "02_옆뒤": ("yt_149.0_상체_옆뒤_방패.jpg", (420, 0, 700, 320), "밝기", [[(600, 150), (1188, 150), (1188, 667), (600, 667)]], (-120, -30)),
}
Z = np.load(J(D, "면패치_살.npz")); 살, xs, ys, zs = Z["살"], Z["xs"], Z["ys"], Z["zs"]; G = np.stack(np.meshgrid(xs, ys, zs, indexing="ij"), -1).reshape(-1, 3)
V = 살.reshape(len(xs), len(ys), len(zs)); 속 = V.copy()
for ax in (0, 1, 2):
    for d in (1, -1): 속 &= np.roll(V, d, axis=ax)
점 = G[(V & ~속).reshape(-1)]; 중심 = 점.mean(0)
def 재투영(자, sil, 모름):
    H, W = sil.shape; uv, _ = 찍기(점, 자); p = np.round(uv).astype(int); ok = (p[:, 0] >= 0) & (p[:, 0] < W) & (p[:, 1] >= 0) & (p[:, 1] < H)
    m = np.zeros((H, W), np.uint8); m[p[ok, 1], p[ok, 0]] = 1; m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) > 0; a, b = m & ~모름, sil & ~모름
    return float((a & b).sum() / max(1, (a | b).sum())), m
ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 18); 판 = []; 결과 = {}
for 태그, (f, 상자, 방식, 다각, (yaw, pitch)) in 대상.items():
    im = 읽기(J(장면, f)); H, W = im.shape[:2]; x0, y0, x1, y1 = 상자
    sil = (실루엣_먹선벽(im, 상자) if 방식 == "먹선벽" else 실루엣(im, 상자)) > 0
    모름 = np.zeros((H, W), np.uint8); cv2.fillPoly(모름, [np.array(p, np.int32) for p in 다각], 1); b = np.ones_like(모름); b[y0:y1, x0:x1] = 0; 모름 = (모름 | b) > 0
    sil &= ~모름                                                                                     # 가린 것은 실루엣에서도 뺀다(깎지도 · 채우지도 않음)
    ys_, xs_ = np.nonzero(sil); s0 = (ys_.max() - ys_.min()) / 90.0; 중 = np.array([xs_.mean(), ys_.mean()])
    best = None
    for dy in (-15, 0, 15):
        for dp in (-15, 0, 15):
            R = R_of(np.radians(yaw + dy), np.radians(pitch + dp), 0.0); r0 = cv2.Rodrigues(R)[0].ravel(); C = (중심 * (1, 1, -1)) @ R.T; t0 = 중 - s0 * C[:2]
            p0 = np.r_[r0, s0, t0]
            def f_(p, p0=p0):
                dR = cv2.Rodrigues(p[:3])[0] @ cv2.Rodrigues(p0[:3])[0].T; ang = np.degrees(np.arccos(np.clip((np.trace(dR) - 1) / 2, -1, 1)))
                return -재투영(dict(r=p[:3], s=p[3], t=p[4:6]), sil, 모름)[0] + 0.01 * max(0, ang - 25) + 0.5 * max(0, abs(p[3] / p0[3] - 1) - 0.25)
            res = minimize(f_, p0, method="Nelder-Mead", options=dict(maxiter=250, xatol=1e-3, fatol=1e-4, initial_simplex=np.r_[[p0], p0 + np.diag([0.08, 0.08, 0.08, 0.2, 10, 10])]))
            if best is None or res.fun < best.fun: best = res
    자 = dict(r=best.x[:3].tolist(), s=float(best.x[3]), t=best.x[4:6].tolist(), k=0.0); iou, m = 재투영(자, sil, 모름)
    결과[태그] = dict(파일=J(장면, f), 상자=list(상자), 자세=자, iou=round(iou, 3)); print("%-8s 실루엣 %6d px · 자세 IoU %.3f" % (태그, sil.sum(), iou))
    cv2.imencode(".png", (sil * 255).astype(np.uint8))[1].tofile(J(D, 태그 + "_실루엣.png")); cv2.imencode(".png", (모름 * 255).astype(np.uint8))[1].tofile(J(D, 태그 + "_모름.png"))
    vis = im.copy(); vis[sil] = (vis[sil] * 0.5 + np.array((0, 0, 255)) * 0.5).astype(np.uint8); vis[m & ~모름] = (vis[m & ~모름] * 0.5 + np.array((0, 255, 0)) * 0.5).astype(np.uint8); vis[모름] = (vis[모름] * 0.6).astype(np.uint8)
    p_ = Image.fromarray(vis[y0:y1, x0:x1, ::-1]); p_ = p_.resize((int(p_.width * 400 / p_.height), 400)); ImageDraw.Draw(p_).text((4, 4), "%s IoU %.2f (빨 실루엣 · 초 껍질 · 어둠 모름)" % (태그, iou), font=ft, fill=(255, 255, 0), stroke_width=2, stroke_fill=(0, 0, 0)); 판.append(p_)
json.dump(결과, open(J(D, "시점추가.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
시트 = Image.new("RGB", (sum(p.width for p in 판) + 10 * len(판), 400), (30, 30, 30)); x = 0
for p_ in 판: 시트.paste(p_, (x, 0)); x += p_.width + 10
시트.save(J(D, "시점추가.png")); print(J(D, "시점추가.png"))
