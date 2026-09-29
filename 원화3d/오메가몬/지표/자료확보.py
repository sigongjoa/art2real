# -*- coding: utf-8 -*-
"""자료 확보 — 그림마다 GrabCut 실루엣 + Sobel 선, 이것만 (09-29 「회전 생각하지 말고 원화에서 데이터를 뽑아 · GrabCut 이랑 Sobel 한 것만 일단 확보」).
    python 자료확보.py -> out/오메가몬2/자료/<이름>_실루엣.png(마스크) · <이름>_선.png(실루엣 안 Sobel/Canny 선) · <이름>_보기.png(원본 | 실루엣 | 선) · 자료.json(크기 · 상자 · 화소 수)
대상: 우리 원화 정면(omega_front_clean · 알파가 있어 실루엣은 알파로) · 02 정면 · 02 3/4 · 02 옆. 회전 · 모델 · 면 분할은 안 한다.
"""
import os, sys, json
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from 집합 import OUT, 장면, J, R as 원화3d
from 윤곽 import 실루엣, 실루엣_먹선벽, 읽기
from 소벨 import 소벨선
D = J(OUT, "..", "자료"); os.makedirs(D, exist_ok=True)
대상 = {
    "원화_정면": (J(os.path.dirname(원화3d), "트레일", "trail7_part3d", "in", "omega_front_clean.png"), (400, 60, 680, 240), "알파"),
    "02_정면":   (J(장면, "yt_172.0_얼굴_정면.jpg"), (690, 10, 1180, 505), "밝기"),
    "02_3-4":    (J(장면, "wk_Omegamon_M04.jpg"), (830, 0, 1440, 700), "먹선벽"),
    "02_옆":     (J(장면, "yt_235.0_머리_옆.jpg"), (400, 0, 990, 305), "밝기"),
}
def 선(im, sil, S=3):
    """Sobel/Canny ∪ 먹선(블랙햇 15 px · 적응 문턱 31 px) — 둘 다 이미지 필터. Sobel 만으로는 면이 안 닫힌다(09-29 자료영역 첫 판: 정면 투구 + 얼굴이 한 면)."""
    im3 = cv2.bilateralFilter(cv2.resize(im, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC), 7, 30, 7); _, e = 소벨선(im3); e = e > 0
    g = cv2.cvtColor(im3, cv2.COLOR_BGR2GRAY); bh = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    e = e | (bh > 18) | (cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 6) > 0)
    m3 = cv2.erode(cv2.resize(sil, None, fx=S, fy=S, interpolation=cv2.INTER_NEAREST), np.ones((5, 5), np.uint8)) > 0
    테 = cv2.Laplacian(cv2.resize(sil, None, fx=S, fy=S, interpolation=cv2.INTER_NEAREST).astype(np.float32), cv2.CV_32F) != 0
    return (e & m3) | 테
if __name__ == "__main__":
    기록 = {}
    for 이름, (f, 상자, 방식) in 대상.items():
        raw = cv2.imdecode(np.fromfile(f, np.uint8), cv2.IMREAD_UNCHANGED)
        if raw.ndim == 3 and raw.shape[2] == 4:
            a = raw[:, :, 3]; im = raw[:, :, :3].copy(); im[a < 128] = 255
            sil = np.zeros(a.shape, np.uint8); x0, y0, x1, y1 = 상자; sil[y0:y1, x0:x1] = (a[y0:y1, x0:x1] > 128)
        else:
            im = raw; sil = 실루엣_먹선벽(im, 상자) if 방식 == "먹선벽" else 실루엣(im, 상자)
        cs, _ = cv2.findContours(sil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); big = max(cs, key=cv2.contourArea); sil = np.zeros_like(sil); cv2.drawContours(sil, [big], -1, 1, -1)
        e = 선(im, sil)
        cv2.imencode(".png", sil * 255)[1].tofile(J(D, 이름 + "_실루엣.png")); cv2.imencode(".png", (~e).astype(np.uint8) * 255)[1].tofile(J(D, 이름 + "_선.png")); np.save(J(D, 이름 + "_실루엣_컨투어.npy"), big.reshape(-1, 2))
        x0, y0, x1, y1 = 상자; c = im[y0:y1, x0:x1]; s = 3; c3 = cv2.resize(c, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
        m = c3.copy(); sm = cv2.resize(sil[y0:y1, x0:x1], None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST) > 0; m[~sm] = (m[~sm] * 0.25).astype(np.uint8); cv2.drawContours(m, [big * s - np.array([x0 * s, y0 * s])], -1, (0, 0, 255), 3)
        L = np.full(c3.shape, 255, np.uint8); L[e[y0 * s:y1 * s, x0 * s:x1 * s]] = (0, 0, 0)
        보기 = np.concatenate([c3, m, L], 1); cv2.imencode(".png", 보기)[1].tofile(J(D, 이름 + "_보기.png"))
        기록[이름] = dict(파일=f, 상자=상자, 실루엣방식=방식, 실루엣화소=int(sil.sum()), 컨투어점=int(len(big)), 선화소=int(e.sum())); print("%-8s 실루엣 %7d px · 컨투어 %5d 점 · 선 %7d px" % (이름, sil.sum(), len(big), e.sum()))
    json.dump(기록, open(J(D, "자료.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("→", D)
