# -*- coding: utf-8 -*-
"""**부품 두께** — 껍데기인가 덩어리인가 (2026-09-24).

    python 두께.py     -> out/기록/두께_<때>.json

비교 항목 ②의 정답값을 사진이 오기 전에 미리 잰다.
실제 키트 부품(Printables 실물 키트)과 우리 부품을 **같은 배율(전고 125mm = 1/144)** 로 맞춘 뒤 잰다.

    두께 ~= 2V/A   껍질이면 살 두께, 덩어리면 «반지름의 2/3» 쯤이 나온다
                   (구 반지름 r: 2*(4/3 pi r^3)/(4 pi r^2) = 2r/3)
"""
import json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np, trimesh

sys.path[:0] = [r"G:\art2real\원화3d"]
import hull as H

전고 = 125.0
키트디 = os.path.join(H.OUT, "키트정답")
우리디 = os.path.join(H.OUT, "출력")


def 재기(경로들, 이름, 배율=None):
    """**닫힌 부품만** 쓴다 — 열린 메시는 부피가 0 이나 음수로 나와 두께가 0.03mm 같은 헛값이 된다.

    주 지표는 **얇기** `(2V/A) / V^(1/3)` 로 크기에 무관하다. 키트마다 좌표계(조립 좌표 · 출력 배치)가
    달라 mm 환산은 믿기 어렵기 때문이다. 속이 꽉 찬 정육면체는 0.333 · 구는 0.414 가 나오고,
    껍질은 그보다 훨씬 작다."""
    ms, 열림 = [], 0
    for p in 경로들:
        try:
            m = trimesh.load(p, force="mesh")
        except Exception:
            continue
        if len(m.faces) == 0 or m.area <= 0:
            continue
        m.merge_vertices()
        if not m.is_watertight or abs(m.volume) < 1e-9:
            열림 += 1
            continue
        ms.append(m)
    if not ms:
        return {"이름": 이름, "부품 수": 0, "열린 부품": 열림}
    if 배율 is None:
        모두 = trimesh.util.concatenate([m.copy() for m in ms])
        배율 = 전고 / max(float(모두.extents.max()), 1e-9)
    두께, 얇기, 부피, 상자몫 = [], [], [], []
    for m in ms:
        V = abs(float(m.volume)) * 배율 ** 3
        A = float(m.area) * 배율 ** 2
        if A <= 0 or V <= 0: continue
        t = 2 * V / A
        두께.append(t); 얇기.append(t / V ** (1 / 3))
        부피.append(V)
        상자몫.append(V / max(float(np.prod(m.extents * 배율)), 1e-9))
    return {"이름": 이름, "부품 수": len(두께), "열린 부품": 열림, "배율": round(배율, 5),
            "얇기 중앙": round(float(np.median(얇기)), 3),
            "두께mm 중앙": round(float(np.median(두께)), 2),
            "두께mm 1~3분위": [round(float(np.percentile(두께, 25)), 2), round(float(np.percentile(두께, 75)), 2)],
            "합계 부피cm³": round(float(np.sum(부피)) / 1000, 1),
            "상자 채움 중앙": round(float(np.median(상자몫)), 3)}


def main():
    줄 = []
    for d in sorted(os.listdir(키트디)):
        p = os.path.join(키트디, d)
        if not os.path.isdir(p): continue
        fs = [os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith(".stl")]
        if len(fs) < 5: continue
        r = 재기(fs, "키트 " + d)
        if r and r["부품 수"] >= 5: 줄.append(r)
    for d in sorted(os.listdir(우리디)) if os.path.isdir(우리디) else []:
        p = os.path.join(우리디, d)
        fs = [os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith(".stl")]
        if fs:
            r = 재기(fs, "우리 " + d, 배율=1.0)   # 이미 전고 125mm 로 내보낸 것
            if r and r["부품 수"]: 줄.append(r)
    키 = [r for r in 줄 if r["이름"].startswith("키트")]
    우 = [r for r in 줄 if r["이름"].startswith("우리")]
    요약 = {"키트 얇기 중앙": round(float(np.median([r["얇기 중앙"] for r in 키])), 3),
           "우리 얇기": [r["얇기 중앙"] for r in 우],
           "속 찬 정육면체": 0.333, "속 찬 구": 0.414,
           "키트 두께mm 중앙": round(float(np.median([r["두께mm 중앙"] for r in 키])), 2),
           "키트 합계부피cm³ 중앙": round(float(np.median([r["합계 부피cm³"] for r in 키])), 1),
           "키트 부품 수 중앙": float(np.median([r["부품 수"] for r in 키])),
           "우리 두께mm 중앙": round(float(np.median([r["두께mm 중앙"] for r in 우])), 2) if 우 else None,
           "우리 합계부피cm³": [r["합계 부피cm³"] for r in 우],
           "우리 부품 수": [r["부품 수"] for r in 우]}
    for r in 줄:
        print("  %-22s 닫힘%3d/열림%3d  얇기 %.3f  두께 %5.2fmm  합계 %6.1fcm³  상자채움 %.3f" % (
            r["이름"][:22], r["부품 수"], r["열린 부품"], r["얇기 중앙"], r["두께mm 중앙"],
            r["합계 부피cm³"], r["상자 채움 중앙"]))
    print("\n" + json.dumps(요약, ensure_ascii=False))
    pth = os.path.join(H.OUT, "기록", "두께_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"요약": 요약, "줄": 줄}, open(pth, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(pth)


if __name__ == "__main__":
    main()
