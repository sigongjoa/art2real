# -*- coding: utf-8 -*-
"""**TripoSG 대 우리** — 사전 지식이 있는 생성 모델과 맞대 본다 (2026-09-23).

    python 트리포비교.py     -> out/트리포비교.png · out/기록/트리포비교_<때>.json

사용자(09-23): 「TripoSG 와 같은 사전 지식 모델이랑 우리 거랑 한번 비교를 해보자」.
TripoSG 는 **3판 맞춤**만 한다(원화 정면 · 측면 실루엣으로 가로 · 깊이를 늘인다 — 정답은 안 본다).
자는 09-23 에 쓰던 것 그대로 + 오늘 만든 판 조각.
"""
import json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np, trimesh, cv2
from PIL import Image, ImageDraw, ImageFont

sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260915", r"G:\art2real\원화3d\실험_20260921",
                r"G:\art2real\원화3d\실험_20260922", r"G:\art2real\원화3d\실험_20260923"]
import hull as H, 정답 as JD, 부품분할 as BB, 도면벤치_천장 as DC
import 지표 as Z, 깊이추정 as GC, 평면조각 as PJ, 면합치기 as M
import 생성3D as G3

생성 = os.path.join(H.OUT, "생성3D", "triposg")
전고mm = 150.0


def main():
    F = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", s)
    기록, 줄들, 이름줄 = {}, [], None
    for c in [GC.케이스들[i] for i in (0, 4, 9)]:
        raw, masks, bs, p = BB.판(c)
        g, ax = H.field_default(masks, back_sign=bs, n=BB.N)
        ux, uy, z = [np.asarray(a) for a in ax]
        O = g > 0
        tm = trimesh.load(os.path.join(H.OUT, "시트", c, "truth.glb"), force="mesh")
        A, o = JD.grid(tm, 봉합=1)
        T = DC.우리격자로(A.astype(np.int32), np.asarray(o), ux, uy, z) > 0
        원 = Z.메시로(O, (ux, uy, z))
        합, _ = M.합치기(원, 정리=0.93)
        # TripoSG — 원화 마스크만 보고 방향을 고르고 가로 · 깊이를 원화에 맞춘다
        gm = trimesh.load(os.path.join(생성, c + ".glb"), force="mesh")
        am = G3.art_masks(c)
        _, V, yaw, mir = G3.orient(gm.vertices, am)
        tr = trimesh.Trimesh(G3.fit_to_art(V, am), np.asarray(gm.faces), process=False)
        배율 = 전고mm / max(tm.extents[2], 1e-9)
        결, 타 = {}, []
        for 이름, m in (("타원(지금)", 원), ("면 합치기", 합), ("TripoSG(3판맞춤)", tr), ("정답", tm)):
            r, 라벨, mm = PJ.재기(m, 전체=10)
            G = M.격자로(m, ux, uy, z)
            r["부피 IoU"] = round(M.iou(G, T), 3)
            r["실루엣 IoU"] = round(float(np.mean([M.iou(G.any(a), O.any(a)) for a in (0, 1, 2)])), 3)
            r["챔퍼 mm"] = round(Z.챔퍼(m, tm, 배율)[0], 2)
            r["표면각"] = round(Z.각(m)[0], 2)
            r["면 수"] = int(len(m.faces))
            결[이름] = r
            pim = Image.fromarray(PJ.칠하기(mm, 라벨))
            ImageDraw.Draw(pim).text((4, 3), "조각 %d · 큰것 %.0f%%\nIoU %.2f · 챔퍼 %.1fmm" % (
                r["조각 수"], 100 * r["1% 이상이 덮는 몫"], r["부피 IoU"], r["챔퍼 mm"]),
                fill=(40, 40, 40), font=F(12))
            타.append(np.asarray(pim))
        기록[c] = 결
        이름줄 = list(결)
        row = np.hstack(타)
        pim = Image.fromarray(np.vstack([np.full((22, row.shape[1], 3), 255, np.uint8), row]))
        ImageDraw.Draw(pim).text((5, 3), c[:34], fill=(80, 80, 80), font=F(14))
        줄들.append(np.asarray(pim))
        print("  " + c[:24], " | ".join("%s 조각%5d 큰것%.2f IoU%.3f 챔퍼%.1f" % (
            k, v["조각 수"], v["1% 이상이 덮는 몫"], v["부피 IoU"], v["챔퍼 mm"]) for k, v in 결.items()), flush=True)
    머리 = Image.fromarray(np.full((28, 줄들[0].shape[1], 3), 255, np.uint8))
    d = ImageDraw.Draw(머리)
    for i, n in enumerate(이름줄):
        d.text((i * 230 + 6, 5), n, fill=(25, 25, 25), font=F(15))
    out = np.vstack([np.asarray(머리)] + 줄들)
    cv2.imencode(".png", out[:, :, ::-1])[1].tofile(os.path.join(H.OUT, "트리포비교.png"))
    pth = os.path.join(H.OUT, "기록", "트리포비교_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(기록, open(pth, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    중 = lambda k, n: float(np.median([기록[c][n][k] for c in 기록]))
    print("중앙값:", {n: dict(조각=int(중("조각 수", n)), 큰판=round(중("1% 이상이 덮는 몫", n), 3),
                          IoU=round(중("부피 IoU", n), 3), 실루엣=round(중("실루엣 IoU", n), 3),
                          챔퍼=round(중("챔퍼 mm", n), 2), 표면각=round(중("표면각", n), 2)) for n in 이름줄})
    print(pth)


if __name__ == "__main__":
    main()
