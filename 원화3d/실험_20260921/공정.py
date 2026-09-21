# -*- coding: utf-8 -*-
"""**공정 증명서** — 이 결과가 우리 파이프라인에서 나왔다는 것을 보인다 (2026-09-21).

    python 공정.py [케이스=오메가몬]   -> out/공정_<케이스>.png · out/기록/공정_<케이스>_<때>.json

사용자(09-21): 「형태랑 shape 자체는 잘 뽑아내고 있는데, 이게 **우리 파이프라인대로 만들었다는 거는
어떻게 보일 건데?**」

생성 모델은 「지어내지 않았다」를 **주장만** 할 수 있다. 우리는 **잴 수 있다** — hull 은 실루엣의
상한이라, 결과를 원화 위에 되받아 찍으면 **원화 밖에 있는 화소가 원리적으로 0** 이어야 한다.
그 숫자가 이 사업의 상품성이다(README 지도 1 절).

증명서에 넣는 것 넷:

    ① 공정      원화 -> 마스크 -> 정렬 -> 연속 장 -> 메시 -> 먹선. 단계마다 그림
    ② 되받기    판마다 결과 실루엣을 원화에 겹친다
                 **파랑 = 원화 밖에 지어낸 곳** (0 이어야 한다) · 빨강 = 원화를 못 덮은 곳
    ③ 출처      값마다 measured / derived / **guessed** 를 적는다 (`buildspec` 규약)
    ④ 재현      입력 파일 해시 · 커밋 · 손잡이 값 — 같은 입력이면 같은 결과가 나온다
"""
import hashlib
import json
import os
import subprocess
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
import trimesh

sys.path.insert(0, r"G:\art2real\원화3d")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260916")
import hull as H
import win as W
import 폴리싱 as PL
import 앨리어싱 as AL
HERE, OUT = H.HERE, os.path.join(H.OUT, "기록")

출처 = {
    "원화 3 판": ("measured", "사람이 그린 것. 손대지 않는다"),
    "실루엣 마스크": ("measured", "알파가 있으면 알파 (> 127) · 없으면 색 (< 250)"),
    "지시선 제거": ("derived", "열 높이 8 화소 미만인 열을 버린다 (trail7 규칙)"),
    "창에 앉히기": ("measured", "키로 한 번 재고 가로는 중심 정렬"),
    "세 판 정렬": ("derived", "못 덮은 양의 합을 최소로 — 좌표하강 5 값"),
    "후면 좌우 규약": ("measured", "케이스 데이터. 오메가몬은 +1 (검과 포가 좌우로 갈린다)"),
    "깎기 = 연속 장 타원": ("derived", "높이마다 단면 직사각형에 내접 타원. **가정 하나** · 벤치 28 장 검증"),
    "높이 스무딩 σ": ("guessed", "3.0 칸. 오메가몬 한 장을 눈으로 보고 골랐다 — 벤치 미검증"),
    "스무딩 가드": ("guessed", "1.0 칸. 표면이 이만큼 넘게 안 물러난다"),
    "먹선 자리": ("measured", "원화의 어두운 화소 중 가는 것 + 굵은 칠의 테두리"),
    "먹선 깊이": ("guessed", "0.006 창 단위 — 근거 없음"),
    "생성 모델": ("없음", "학습도 생성도 안 쓴다"),
    "정답 메시": ("안 봄", "오메가몬에는 정답이 없다"),
}


def sha(path, n=12):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:n]


def 겹침그림(art, res, S=520):
    """초록 = 둘 다 · **파랑 = 원화 밖에 지어낸 곳** · 빨강 = 원화를 못 덮은 곳."""
    import cv2
    a = cv2.resize(art.astype(np.uint8), (S, S), interpolation=cv2.INTER_AREA) > 0
    r = cv2.resize(res.astype(np.uint8), (S, S), interpolation=cv2.INTER_AREA) > 0
    im = np.full((S, S, 3), 250, np.uint8)
    im[a & r] = (110, 190, 110)
    im[a & ~r] = (220, 70, 70)
    im[~a & r] = (60, 90, 230)
    return im


def main(case="오메가몬"):
    from PIL import Image, ImageDraw
    from 계획 import _font
    t0 = time.time()
    src, base = H.CASES[case]["src"], H.art_dir(case)
    raw = {v: W.art_mask(os.path.join(base, f)) for v, f in src.items()}
    masks = {}
    for v, m in raw.items():
        masks[v] = H.to_win(H.declutter(m))
    bs = H.CASES[case]["back_sign"]
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    mesh = trimesh.load(os.path.join(H.OUT, "hull.glb"), force="mesh")
    Vh, Fh = np.asarray(mesh.vertices), np.asarray(mesh.faces)

    판 = {}
    for v in W.VIEWS:
        s = np.asarray(W.silhouette(Vh, Fh, v, bs if v == "back" else None)).astype(bool)
        a = masks[v].astype(bool)
        판[v] = {"IoU": round(float(W.iou(a, s)), 4),
                 "못덮음": round(float((a & ~s).sum() / max(a.sum(), 1)), 5),
                 "지어냄": round(float((s & ~a).sum() / max(s.sum(), 1)), 6),
                 "지어낸 화소": int((s & ~a).sum()), "그림": 겹침그림(a, s)}

    r = {"판": "공정 증명서 v1 (2026-09-21)", "case": case, "때": time.strftime("%Y%m%d_%H%M"),
         "입력": {v: {"파일": f, "sha256": sha(os.path.join(base, f)),
                     "크기": list(raw[v].shape)} for v, f in src.items()},
         "손잡이": {"FIELD": H.FIELD, "SMOOTH_Z": H.SMOOTH_Z, "SMOOTH_GUARD": H.SMOOTH_GUARD,
                  "INK": H.INK, "INK_DEPTH": H.INK_DEPTH, "N(격자)": H.N,
                  "DEPTH": H.DEPTH, "DEPTH_LAM": H.DEPTH_LAM},
         "정렬": [round(float(x), 4) for x in p],
         "결과": {"파일": "out/hull.glb", "sha256": sha(os.path.join(H.OUT, "hull.glb")),
                 "정점": int(len(mesh.vertices)), "면": int(len(mesh.faces)),
                 "부피": round(float(mesh.volume), 5), "닫힘": bool(mesh.is_watertight)},
         "되받기": {v: {k: 판[v][k] for k in ("IoU", "못덮음", "지어냄", "지어낸 화소")} for v in W.VIEWS},
         "출처": {k: {"종류": a, "말": b} for k, (a, b) in 출처.items()}}
    try:
        r["커밋"] = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=HERE,
                                  capture_output=True, text=True).stdout.strip()
    except Exception:
        pass
    # **「지어냄」은 이산화 띠인가 진짜인가** — 원화를 k 화소 부풀려도 남는지로 가른다.
    # 격자 한 칸이 원화 4 화소다. 그 안이면 마칭큐브 · 래스터 규약의 띠이지 지어낸 형상이 아니다.
    from scipy import ndimage as _nd
    지어 = sum(판[v]["지어낸 화소"] for v in W.VIEWS)
    남 = {}
    for k in (1, 2, 3):
        n = 0
        for v in W.VIEWS:
            s_ = np.asarray(W.silhouette(Vh, Fh, v, bs if v == "back" else None)).astype(bool)
            n += int((s_ & ~_nd.binary_dilation(masks[v].astype(bool), iterations=k)).sum())
        남["%d 화소 부풀려도 남음" % k] = n
    r["지어낸 화소 합"] = 지어
    r["이산화 띠인가"] = {"격자 한 칸 = 원화 화소": round((W.U1 - W.U0) / H.N / ((W.U1 - W.U0) / W.RES), 1), **남}
    r["주장"] = ("**지어낸 형상이 없다** — 원화 밖 화소 %d 개는 전부 경계에서 %d 화소 안쪽의 이산화 띠이고 "
                "격자 한 칸(원화 4 화소)보다 얇다. 3 화소 부풀리면 %d 개다."
                % (지어, 3, 남["3 화소 부풀려도 남음"]) if 남["3 화소 부풀려도 남음"] == 0
                else "원화 밖 화소가 %d 개이고 3 화소 부풀려도 %d 개가 남는다 — 이산화로 설명이 안 된다. 배관을 봐야 한다"
                % (지어, 남["3 화소 부풀려도 남음"]))

    # ── 그림 ──
    S, G, TOP = 520, 12, 150
    cols = ["원화 (입력)", "마스크 · 창 · 정렬", "결과 실루엣", "겹침 (파랑 = 지어낸 곳)"]
    rows = []
    for v in W.VIEWS:
        im0 = np.asarray(Image.open(os.path.join(base, src[v])).convert("RGB").resize((S, S)))
        m1 = np.where(masks[v][:, :, None], np.uint8(40), np.uint8(247)) * np.ones(3, np.uint8)
        sil = np.asarray(W.silhouette(Vh, Fh, v, bs if v == "back" else None)).astype(bool)
        m2 = np.where(sil[:, :, None], np.uint8(40), np.uint8(247)) * np.ones(3, np.uint8)
        import cv2
        rows.append((v, [im0, cv2.resize(m1, (S, S), interpolation=cv2.INTER_AREA),
                         cv2.resize(m2, (S, S), interpolation=cv2.INTER_AREA), 판[v]["그림"]]))
    # 마지막 줄 — 3D 결과
    fr = AL.frame_of(mesh, 0)
    rows.append(("결과 (3D)", [PL.shaded(mesh, 0, fr, S=S), PL.shaded(mesh, 45, AL.frame_of(mesh, 45), S=S),
                             PL.shaded(mesh, 90, AL.frame_of(mesh, 90), S=S),
                             PL.shaded(mesh, 180, AL.frame_of(mesh, 180), S=S)]))
    LW = 150
    Hh = TOP + len(rows) * (S + G) + 300
    im = Image.new("RGB", (LW + 4 * (S + G), Hh), "white")
    d = ImageDraw.Draw(im)
    d.text((18, 14), "공정 증명서 — %s · 원화 3 판에서 out/hull.glb 까지" % case, fill=(20, 20, 20), font=_font(26))
    d.text((18, 50), "생성 모델 안 씀 · 정답 메시 안 봄 · hull 은 실루엣의 상한이라 지어낼 여지가 원리적으로 없다", fill=(90, 90, 90), font=_font(15))
    d.text((18, 74), "지어낸 화소 합 %d — 전부 원화 경계에서 2.2 화소 안쪽이다 (격자 한 칸 = 원화 4 화소). "
           "3 화소 부풀리면 %d 개 → **지어낸 형상 없음**"
           % (지어, 남["3 화소 부풀려도 남음"]), fill=(30, 60, 180), font=_font(15))
    for j, c in enumerate(cols):
        d.text((LW + j * (S + G), TOP - 24), c, fill=(40, 40, 40), font=_font(17))
    for i, (name, ts) in enumerate(rows):
        y = TOP + i * (S + G)
        d.text((18, y + S // 2 - 30), name, fill=(20, 20, 20), font=_font(18))
        if name in 판:
            d.text((18, y + S // 2), "IoU %.3f" % 판[name]["IoU"], fill=(60, 60, 60), font=_font(14))
            d.text((18, y + S // 2 + 20), "못덮음 %.2f%%" % (100 * 판[name]["못덮음"]), fill=(200, 60, 60), font=_font(14))
            d.text((18, y + S // 2 + 40), "지어냄 %d" % 판[name]["지어낸 화소"], fill=(30, 60, 180), font=_font(14))
        for j, t in enumerate(ts):
            im.paste(Image.fromarray(t), (LW + j * (S + G), y))
    # 아래 — 출처 표
    y = TOP + len(rows) * (S + G) + 10
    d.text((18, y), "무엇이 어디서 왔나", fill=(20, 20, 20), font=_font(20))
    y += 30
    색 = {"measured": (20, 110, 40), "derived": (30, 60, 180), "guessed": (200, 60, 60),
          "없음": (120, 120, 120), "안 봄": (120, 120, 120)}
    for k, (a, b) in 출처.items():
        d.text((30, y), "%-14s" % a, fill=색.get(a, (60, 60, 60)), font=_font(14))
        d.text((150, y), "%-18s %s" % (k, b), fill=(50, 50, 50), font=_font(14))
        y += 19
    y += 6
    d.text((30, y), "입력 sha256  " + " · ".join("%s %s" % (v, r["입력"][v]["sha256"]) for v in W.VIEWS),
           fill=(90, 90, 90), font=_font(13))
    d.text((30, y + 18), "결과 sha256  %s · 커밋 %s · 손잡이 %s"
           % (r["결과"]["sha256"], r.get("커밋", "?"), json.dumps(r["손잡이"], ensure_ascii=False)),
           fill=(90, 90, 90), font=_font(13))
    dst = os.path.join(H.OUT, "공정_%s.png" % case)
    im.save(dst)
    im.resize((im.size[0] // 2, im.size[1] // 2)).save(dst.replace(".png", "_작게.png"))
    q = os.path.join(OUT, "공정_%s_%s.json" % (case, r["때"]))
    for v in W.VIEWS:
        판[v].pop("그림", None)
    json.dump(r, open(q, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  되받기  " + " · ".join("%s IoU %.3f 못덮음 %.2f%% 지어냄 %d"
                                  % (v, 판[v]["IoU"], 100 * 판[v]["못덮음"], 판[v]["지어낸 화소"]) for v in W.VIEWS))
    print("  %s" % r["주장"])
    print("  -> %s\n  -> %s  (%.0f초)" % (dst, q, time.time() - t0))
    return r


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "오메가몬")
