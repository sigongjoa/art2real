# -*- coding: utf-8 -*-
"""**원형사 순서로 한 바퀴** — 일본 원형사 프로세스를 우리 파이프라인에 그대로 얹어 단계마다 그림을 남긴다 (2026-09-23).

    python 원형사.py [케이스]      -> out/원형사/<케이스>/단계_*.png · out/기록/원형사_<때>.json

조사(`claudedocs/research_형태와분할_일본원형사_20260923.md`)의 단계 대응:
    ② 자료      삼면 판                      ④ 스케일  전고 mm 고정 · 1 칸 몇 mm
    ⑤⑥ 소체 · 겹  hull 을 두께 t 로 소체(속) · 갑주(겉 껍질)로 가른다 (원형사: 소체 + 옷 두께)
    ⑦ 가출력    우리는 실물이 없다 -> 정답 부피와 대 본다(부피 IoU)
    ⑩ 분할      부위(관절) × 색(도색 단위) -> 부품 · **빠짐 방향 검사**(언더컷이면 쪼갠다)
    ⑪ 다보      맞닿는 부품 쌍마다 접촉면 복판에 네모 키 자리
사람 몫(③ 포즈 · ⑧ 감수 · ⑨ 디테일)은 여기서 안 한다.
"""
import json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import cv2
from scipy import ndimage

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921", r"G:\art2real\원화3d\실험_20260922"]
import hull as H
import win as W
import 정답 as JD
import 부품분할 as BB
import 면자르기 as MJ
import 도면벤치_천장 as DC
import 부피벤치 as PB
import trimesh

전고mm = 150.0
두께mm = 1.5


def 글(im, s, xy=(10, 8), c=(30, 30, 30), sc=None):
    """한글은 cv2.putText 가 ??? 로 깨진다 — PIL 로 쓴다. 그림 위에 흰 띠를 얹고 그 위에 쓴다."""
    from PIL import Image, ImageDraw, ImageFont
    band = np.full((34, im.shape[1], 3), 255, np.uint8)
    im = np.vstack([band, im])
    pim = Image.fromarray(im[:, :, ::-1])
    ImageDraw.Draw(pim).text(xy, s, fill=(30, 30, 30), font=ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19))
    return np.asarray(pim)[:, :, ::-1].copy()


def 투영(V, 색=None, 크기=260):
    """복셀 부피 -> 앞 · 옆 세 그림 가로로. 색 = 라벨이면 라벨색, None 이면 회색."""
    out = []
    for axis in (1, 0):                                   # 앞(=y로 누름) · 옆(=x로 누름)
        if 색 is None:
            m = V.max(axis=axis).T[::-1]
            im = np.where(m[..., None], np.array([90, 90, 90], np.uint8), np.array([255, 255, 255], np.uint8)).astype(np.uint8)
        else:
            idx = np.where(V.any(axis=axis), V.argmax(axis=axis), 0)
            lab = np.take_along_axis(색, np.expand_dims(idx, axis), axis).squeeze(axis)
            lab = lab.T[::-1]; msk = V.max(axis=axis).T[::-1]
            im = 색칠(lab, msk)
        h = 크기; w = int(im.shape[1] * h / im.shape[0])
        out.append(cv2.resize(im, (w, h), interpolation=cv2.INTER_NEAREST))
    return np.hstack(out)


_pal = None
고정 = None
def 색칠(lab, msk):
    """고정 이 있으면 그 색표(번호 -> BGR)를 쓴다 — 없으면 라벨마다 다른 색."""
    global _pal
    if 고정 is not None:
        im = np.full(lab.shape + (3,), 255, np.uint8)
        for k, v in 고정.items():
            im[msk & (lab == k)] = v
        return im
    if _pal is None:
        rng = np.random.default_rng(7); _pal = (rng.integers(60, 235, (4096, 3))).astype(np.uint8)
    im = np.full(lab.shape + (3,), 255, np.uint8)
    im[msk] = _pal[lab[msk] % 4096]
    return im


def 빠짐방향(P, 두꼐=None):
    """부품이 ±x · ±y · ±z 여섯 방향 중 하나로 틀에서 빠지나 — 그 방향 기둥마다 채워진 칸이 **한 토막**이면 빠진다."""
    좋 = []
    for axis in range(3):
        for _ in (0, 1):
            cnt = P.sum(axis=axis)
            시작 = np.argmax(P, axis=axis); 끝 = P.shape[axis] - 1 - np.argmax(np.flip(P, axis), axis=axis)
            한토막 = (cnt == 0) | (cnt == (끝 - 시작 + 1))
            좋.append(bool(한토막.all()))
    return 좋                                             # [x+, x-, y+, y-, z+, z-] 중 True 면 그 축으로 빠진다


def main(c="mech_Mech_4UvIHxnoSR"):
    D = os.path.join(H.OUT, "원형사", c); os.makedirs(D, exist_ok=True)
    기록 = {"케이스": c, "전고mm": 전고mm, "두께mm": 두께mm}
    raw, masks, bs, p = BB.판(c)

    # ② 자료 — 삼면 판
    판 = [cv2.resize(np.where(masks[v][..., None] > 0.5, np.array([70, 70, 70], np.uint8), np.array([255, 255, 255], np.uint8)).astype(np.uint8), (260, 260)) for v in W.VIEWS]
    cv2.imencode(".png", 글(np.hstack(판), "2 자료: 삼면 판 (front / side / back)"))[1].tofile(os.path.join(D, "단계_2_자료.png"))

    # ③ 부피 (지금 우리 기본) + ④ 스케일
    g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
    O = g > 0
    ux, uy, z = [np.asarray(a) for a in ax]
    키칸 = int(O.any(axis=(0, 1)).sum())
    mm칸 = 전고mm / 키칸
    t = max(1, int(round(두께mm / mm칸)))
    기록["칸 mm"] = round(mm칸, 3); 기록["두께 칸"] = t; 기록["키 칸"] = 키칸
    im = 투영(O)
    im = 글(im, "4 스케일: 전고 %.0f mm · 1 칸 %.2f mm · 두께 %.1f mm = %d 칸" % (전고mm, mm칸, 두께mm, t))
    cv2.imencode(".png", im)[1].tofile(os.path.join(D, "단계_4_스케일.png"))

    # ⑤⑥ 소체 · 겹
    소체 = ndimage.binary_erosion(O, iterations=t)
    갑주 = O & ~소체
    겹 = np.where(갑주, 2, 0) + np.where(소체, 1, 0)
    global 고정
    고정 = {1: (200, 160, 120), 2: (40, 120, 235)}          # 소체 = 연파랑빛 · 갑주 = 주황
    im = 투영(O, 색=겹.astype(np.int32))
    im = 글(im, "5-6 겹: 소체(속) + 갑주 껍질 %d 칸 — 소체 %.0f%% · 껍질 %.0f%%" % (t, 100 * 소체.sum() / O.sum(), 100 * 갑주.sum() / O.sum()))
    cv2.imencode(".png", im)[1].tofile(os.path.join(D, "단계_56_겹.png"))
    # 가운데 높이 가로 단면
    k = int(np.where(O.any(axis=(0, 1)))[0].mean())
    sl = 색칠(겹[:, :, k].astype(np.int32).T[::-1], O[:, :, k].T[::-1])
    cv2.imencode(".png", 글(cv2.resize(sl, (520, 520), interpolation=cv2.INTER_NEAREST), "5-6 단면(허리 높이): 파랑 = 소체 · 주황 = 갑주"))[1].tofile(os.path.join(D, "단계_56_단면.png"))
    기록["겹"] = {"소체 몫": round(float(소체.sum() / O.sum()), 3), "갑주 몫": round(float(갑주.sum() / O.sum()), 3)}

    # ⑦ 가출력 대신 — 정답 부피와 대 보기
    tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
    A, o = JD.grid(tm, 봉합=1)
    T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
    기록["7 부피"] = PB.재기(O, T)
    고정 = {1: (110, 180, 110), 2: (230, 140, 60), 3: (60, 60, 230)}   # 겹침 = 초록 · 우리만 = 파랑빛 · 정답만 = 빨강
    im = 투영(np.stack([O, T]).any(0), 색=(np.where(O & T, 1, 0) + np.where(O & ~T, 2, 0) + np.where(T & ~O, 3, 0)).astype(np.int32))
    im = 글(im, "7 검산: IoU %.2f 정밀 %.2f 재현 %.2f (겹침/우리만/정답만)" % (기록["7 부피"]["IoU"], 기록["7 부피"]["정밀도"], 기록["7 부피"]["재현율"]))
    cv2.imencode(".png", im)[1].tofile(os.path.join(D, "단계_7_검산.png"))
    cmp = (np.where(O & T, 1, 0) + np.where(O & ~T, 2, 0) + np.where(T & ~O, 3, 0)).astype(np.int32)
    sl = 색칠(cmp[:, :, k].T[::-1], (O | T)[:, :, k].T[::-1])
    sl = cv2.resize(sl, (520, 520), interpolation=cv2.INTER_NEAREST)
    cv2.imencode(".png", 글(sl, "7 단면(허리 높이): 초록 = 맞음 · 파랑 = 우리만(넘침) · 빨강 = 정답만(놓침)"))[1].tofile(os.path.join(D, "단계_7_단면.png"))

    # ⑩ 분할 — 부위(관절) × 색(도색 단위)
    _, 부위, _ = MJ.부위(O); 부위 = BB.채우기(부위, O)
    색, _ = BB.색라벨(c, raw, masks, p, bs, O)
    쌍 = (부위.astype(np.int64) * 1000 + 색.astype(np.int64)) * O
    부품 = np.zeros(O.shape, np.int32); 다음 = 0
    for v in np.unique(쌍):                                # 값이 같고 **붙어 있는** 덩어리마다 한 부품
        if v == 0: continue
        l, k = ndimage.label(쌍 == v, np.ones((3, 3, 3), bool))
        부품 = np.where(l > 0, l + 다음, 부품); 다음 += k
    크기 = np.bincount(부품.ravel()); 크기[0] = 0
    작 = np.where((크기 > 0) & (크기 < 0.002 * O.sum()))[0]
    if len(작):                                            # 부스러기는 가장 큰 이웃에 붙인다
        idx = ndimage.distance_transform_edt(np.isin(부품, 작) | ~O, return_distances=False, return_indices=True)
        부품 = np.where(np.isin(부품, 작), 부품[tuple(idx)], 부품)
    라벨들 = [l for l in np.unique(부품) if l]
    기록["10 분할"] = {"부위": int(부위.max()), "색": int(색.max()), "부품": len(라벨들)}
    고정 = None
    im = 투영(O, 색=부품)
    im = 글(im, "10 분할: 부위 %d x 색 %d -> 부품 %d" % (부위.max(), 색.max(), len(라벨들)))
    cv2.imencode(".png", im)[1].tofile(os.path.join(D, "단계_10_분할.png"))

    # ⑩-b 빠짐 방향 검사
    막힌 = []
    for l in 라벨들:
        P = 부품 == l
        if not any(빠짐방향(P)): 막힌.append(int(l))
    기록["10 언더컷 부품"] = {"수": len(막힌), "몫": round(len(막힌) / max(len(라벨들), 1), 2)}
    고정 = {1: (200, 200, 200), 2: (60, 60, 230)}
    im = 투영(O, 색=np.where(np.isin(부품, 막힌), 2, np.where(부품 > 0, 1, 0)).astype(np.int32))
    im = 글(im, "10b 빠짐 검사: 한 방향으로 못 빠지는 부품 %d / %d (쪼개야 한다)" % (len(막힌), len(라벨들)))
    cv2.imencode(".png", im)[1].tofile(os.path.join(D, "단계_10b_언더컷.png"))

    # ⑪ 다보 — 맞닿는 부품 쌍마다 접촉면 복판
    부푼 = {l: ndimage.binary_dilation(부품 == l) for l in 라벨들}
    키 = []
    for i, a in enumerate(라벨들):
        for b in 라벨들[i + 1:]:
            접 = 부푼[a] & (부품 == b)
            if 접.sum() >= 30:
                c3 = np.argwhere(접).mean(0)
                키.append({"부품": [int(a), int(b)], "칸": [round(float(x), 1) for x in c3], "접촉 칸": int(접.sum()),
                           "다보 mm": 1.5, "수 축소": "3%"})
    기록["11 다보"] = {"쌍": len(키), "예": 키[:5]}
    고정 = None
    im = 투영(O, 색=부품)
    for 키하나 in 키:
        x, y, zz = 키하나["칸"]
        h, w = im.shape[0], im.shape[1] // 2
        px = int(x / O.shape[0] * w); py = int((1 - zz / O.shape[2]) * h)
        cv2.rectangle(im, (px - 4, py - 4), (px + 4, py + 4), (0, 0, 220), 2)
        px2 = w + int(y / O.shape[1] * w)
        cv2.rectangle(im, (px2 - 4, py - 4), (px2 + 4, py + 4), (0, 0, 220), 2)
    im = 글(im, "11 다보: 맞닿는 부품 쌍 %d 곳에 네모 키 (1.5 mm · 수 3%% 축소)" % len(키))
    cv2.imencode(".png", im)[1].tofile(os.path.join(D, "단계_11_다보.png"))

    print(json.dumps(기록, ensure_ascii=False, indent=1))
    pth = os.path.join(H.OUT, "기록", "원형사_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(기록, open(pth, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(pth, D)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "mech_Mech_4UvIHxnoSR")
