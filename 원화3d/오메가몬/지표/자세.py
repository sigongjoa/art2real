# -*- coding: utf-8 -*-
"""지표 0 — 캡처의 카메라 방향(구면좌표: 방위 yaw · 고도 pitch · 굴림 roll)을 먼저 푼다. (2026-09-29 사용자: 「구면좌표계 기준으로 얼마나 회전했는지를 봐야 여러 시점 데이터를 처리할 수 있다」)
    python 자세.py -> 캡처마다 yaw/pitch/roll + 재투영 잔차(머리 단위) 표 · out/오메가몬2/지표/자세.json · 자세_<캡처>.png(캡처 위에 잰 점 빨강 · 재투영 파랑)
방법: 3D 랜드마크(도안 2 판 · 머리 높이 100 단위 · x 오른쪽 + · y 아래 + · z 앞 +) ↔ 캡처의 2D 랜드마크(격자에서 손으로 읽은 px) 를 cv2.solvePnP 로 맞춘다.
      초점거리를 아주 크게 두어 약원근(거의 정사영)으로. 잔차 = 맞춘 자세로 3D 점을 다시 찍은 것과 읽은 점의 거리(머리 단위).
쓰임: (1) 캡처가 정면 · 옆이 「몇 도」 돌아 있는지 수치로 — 어림 보정 대신. (2) 후보 모델의 3D 랜드마크를 같은 자세로 찍어 캡처와 비교 → 시점에 안 흔들리는 닮음 자.
"""
import os, json, math
import numpy as np, cv2
from PIL import Image, ImageDraw
from 집합 import OUT, 장면, J
읽기 = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
# ── 3D 랜드마크 (도안 2 판 · 단위) : 이름 → (x, y, z). L = 그림 왼쪽(x −) · R = 그림 오른쪽(x +)
반쪽 = dict(뿔밑동=(10, 27, 26), 눈안쪽위=(7.5, 51, 24), 눈바깥위=(25, 41, -8), 눈바깥아래=(18, 65, -10), 눈안쪽아래=(7, 57, 20), 홍채중심=(13.7, 53, 0),
          윗판끝=(10, 85, 30), 볼날개끝=(33, 80, -40), 번개=(29, 36, -20), 안테나밑동=(21, 15, -12), 투구최대폭=(42, 38, -20))
가운데 = dict(돔꼭대기=(0, 0, 0), 뿔아래꼭짓점=(0, 34, 36), 코끝=(0, 75, 52), 턱끝=(0, 100, 15))
P3 = {**{k: np.array(v, float) for k, v in 가운데.items()}, **{k + "R": np.array(v, float) for k, v in 반쪽.items()}, **{k + "L": np.array((-v[0], v[1], v[2]), float) for k, v in 반쪽.items()}}
# ── 2D 랜드마크 (원본 px) — 격자 그림에서 읽음. 안 보이는 점은 적지 않는다.
캡처 = {
    "정면 yt_172": ("yt_172.0_얼굴_정면.jpg", dict(돔꼭대기=(887, 197), 턱끝=(890, 492), 뿔아래꼭짓점=(888, 292), 코끝=(880, 415), 뿔밑동L=(860, 280), 뿔밑동R=(915, 280),
                    홍채중심L=(822, 352), 홍채중심R=(905, 370), 눈바깥위L=(792, 300), 눈안쪽위L=(846, 343), 눈안쪽아래L=(850, 368), 눈바깥아래L=(805, 397),
                    눈바깥위R=(935, 320), 눈안쪽위R=(882, 340), 눈안쪽아래R=(880, 365), 눈바깥아래R=(935, 400), 윗판끝L=(835, 445), 윗판끝R=(895, 445),
                    볼날개끝L=(750, 390), 볼날개끝R=(960, 380), 번개L=(787, 262), 번개R=(955, 345), 안테나밑동L=(800, 240), 안테나밑동R=(960, 270), 투구최대폭L=(750, 320), 투구최대폭R=(975, 300))),
    "3/4 M04":   ("wk_Omegamon_M04.jpg", dict(돔꼭대기=(1010, 195), 턱끝=(950, 625), 뿔아래꼭짓점=(1005, 305), 코끝=(995, 445), 뿔밑동R=(1060, 245),
                    홍채중심R=(1090, 350), 눈안쪽위R=(1035, 330), 눈바깥위R=(1150, 308), 눈바깥아래R=(1140, 395), 눈안쪽아래R=(1050, 400),
                    윗판끝R=(1080, 470), 볼날개끝R=(1225, 465), 번개R=(1200, 265), 안테나밑동R=(1175, 240), 투구최대폭R=(1300, 370))),
    "옆 yt_235":  ("yt_235.0_머리_옆.jpg", dict(돔꼭대기=(610, 45), 턱끝=(615, 295), 뿔아래꼭짓점=(520, 112), 코끝=(468, 198), 뿔밑동L=(555, 65),
                    홍채중심L=(630, 118), 눈안쪽위L=(585, 100), 눈바깥위L=(662, 95), 눈바깥아래L=(665, 145), 눈안쪽아래L=(585, 150),
                    윗판끝L=(560, 245), 볼날개끝L=(735, 270), 번개L=(700, 125), 안테나밑동L=(740, 118))),
}
def 풀기(이름):
    f, pts = 캡처[이름]; im = 읽기(J(장면, f)); h, w = im.shape[:2]
    F = 50.0 * max(w, h); K = np.array([[F, 0, w / 2], [0, F, h / 2], [0, 0, 1]], np.float32); 최선 = None
    거울 = lambda k: k[:-1] + {"L": "R", "R": "L"}[k[-1]] if k[-1] in "LR" else k
    for 뒤집 in (False, True):                                                   # 한쪽 점만 있으면 좌우가 거울로 헷갈린다 → 둘 다 풀어 잔차 낮은 쪽
        keys = [k for k in pts if k in P3]; obj = np.array([P3[거울(k) if 뒤집 else k] * (1, 1, -1) for k in keys], np.float32)   # 카메라 z 는 멀어지는 쪽 → 앞(z+) 을 −z 로
        img = np.array([pts[k] for k in keys], np.float32)
        for y0 in (0, 45, -45, 90, -90, 135, -135):                              # 초기 방위를 여럿 — 약원근 PnP 는 국소해에 잘 빠진다
            r0, _ = cv2.Rodrigues(np.array([0, math.radians(y0), 0], np.float32)); rvec = cv2.Rodrigues(r0)[0]; tvec = np.array([[0.0], [0.0], [F / 2]], np.float32)
            ok, rvec, tvec = cv2.solvePnP(obj, img, K, None, rvec, tvec, useExtrinsicGuess=True, flags=cv2.SOLVEPNP_ITERATIVE)
            if not ok: continue
            rvec, tvec = cv2.solvePnPRefineLM(obj, img, K, None, rvec, tvec); 재, _ = cv2.projectPoints(obj, rvec, tvec, K, None); 재 = 재.reshape(-1, 2)
            e = float(np.mean(np.linalg.norm(재 - img, axis=1))); Rr, _ = cv2.Rodrigues(rvec)
            if (Rr @ np.array([0, 0, -1.0]))[2] > 0: continue                   # 코가 카메라 반대쪽 = 뒤통수를 본 해 — 정사영에 가까우면 잔차가 같아 이걸로 거른다
            if 최선 is None or e < 최선[0] - (0.5 if 뒤집 else 0): 최선 = (e, rvec, tvec, 재, keys, img, obj, 뒤집)   # 거울 표찰은 뚜렷이 나을 때만
    e, rvec, tvec, 재, keys, img, obj, 뒤집 = 최선; R, _ = cv2.Rodrigues(rvec)
    # 머리 높이(px) = 돔꼭대기 → 턱끝 을 이 자세로 찍은 길이 → 단위 환산
    top, chin = cv2.projectPoints(np.array([[0, 0, 0], [0, 100, -15]], np.float32), rvec, tvec, K, None)[0].reshape(-1, 2); u = np.linalg.norm(chin - top) / 100.0
    잔 = {k: float(np.linalg.norm(재[i] - img[i]) / u) for i, k in enumerate(keys)}
    # 오일러: R = Ry(yaw) Rx(pitch) Rz(roll) 순으로 풀이(yaw = 좌우 돌림 · pitch = 위아래 · roll = 굴림)
    앞 = R @ np.array([0, 0, -1.0]); 위 = R @ np.array([0, -1.0, 0])         # 모델의 앞(코 방향) · 위 벡터를 카메라 좌표로
    yaw = math.degrees(math.atan2(앞[0], -앞[2])); pitch = math.degrees(math.asin(max(-1, min(1, -앞[1])))); roll = math.degrees(math.atan2(위[0], -위[1]))   # yaw + = 코가 화면 오른쪽 · pitch + = 코가 위 · roll + = 정수리가 화면 오른쪽으로 기움
    d = ImageDraw.Draw(Image.fromarray(im[:, :, ::-1])); 그림 = Image.fromarray(im[:, :, ::-1]); d = ImageDraw.Draw(그림)
    for i, k in enumerate(keys):
        x, y = img[i]; d.ellipse((x - 4, y - 4, x + 4, y + 4), outline=(255, 0, 0), width=2); x2, y2 = 재[i]; d.ellipse((x2 - 4, y2 - 4, x2 + 4, y2 + 4), outline=(0, 90, 255), width=2); d.line((x, y, x2, y2), fill=(255, 255, 0))
    그림.save(J(OUT, "자세_%s.png" % 이름.replace("/", "-").replace(" ", "_")))
    return dict(yaw=round(yaw, 1), pitch=round(pitch, 1), roll=round(roll, 1), 잔차평균=round(float(np.mean(list(잔.values()))), 1), 잔차=dict(sorted(잔.items(), key=lambda kv: -kv[1])), 점수=len(keys), 좌우뒤집=뒤집)
if __name__ == "__main__":
    결과 = {n: 풀기(n) for n in 캡처}
    print("%-12s %6s %6s %6s | %5s %3s %4s | %s" % ("캡처", "yaw", "pitch", "roll", "잔차", "점", "거울", "가장 안 맞는 점"))
    for n, r in 결과.items(): print("%-12s %6.1f %6.1f %6.1f | %5.1f %3d %4s | %s" % (n, r["yaw"], r["pitch"], r["roll"], r["잔차평균"], r["점수"], "예" if r["좌우뒤집"] else "", ", ".join("%s %.0f" % kv for kv in list(r["잔차"].items())[:3])))
    print("yaw + = 코가 화면 오른쪽 · pitch + = 코가 위 · roll + = 정수리가 오른쪽으로 기움 · 잔차 = 머리 높이 100 단위")
    json.dump(결과, open(J(OUT, "자세.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
