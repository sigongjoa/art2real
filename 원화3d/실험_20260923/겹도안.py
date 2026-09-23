# -*- coding: utf-8 -*-
"""**겹 도안 시험** — GPT 가 그린 속 프레임 판이 갑주(원본) 판 안에 드나 · 앞뒤가 맞나 · 속이 작나 (2026-09-23).

    python 겹도안.py            -> out/기록/겹도안_<때>.json · out/겹도안_메카2.png

판정(README 09-23 절 · 보내기 전에 적었다): ① (프레임 ∖ 갑주) ≤ 2% ② 프레임 앞·뒤 거울 IoU ≥ 0.90 ③ 프레임 hull 부피 ≤ 갑주 hull 의 0.60
판을 같은 창에 올리는 일은 `hull.to_win` · `hull.align` 이 한다(겉 판과 같은 길).
"""
import json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np
sys.path[:0] = [r"G:\art2real\원화3d", r"G:\art2real\원화3d\실험_20260921"]
import hull as H
import win as W

D = os.path.join(H.OUT, "겹도안", "메카2")


def 판들(디):
    raw = {v: W.art_mask(os.path.join(디, v + ".png")) for v in W.VIEWS}
    m = {v: H.to_win(H.declutter(q), np.ones(q.shape, np.float32))[0] for v, q in raw.items()}
    bs = H.pick_back_sign(m)
    return H._warp(m, H.align(m, back_sign=bs)), bs


def 부피(m, bs):
    g, _ = H.field_hull(m, back_sign=bs, n=160)
    return int((g > 0).sum())


def main():
    갑주, bs_a = 판들(os.path.join(H.OUT, "도안생성", "메카2", "판"))
    프레임, bs_f = 판들(os.path.join(D, "프레임판"))
    r = {"back_sign": [bs_a, bs_f]}
    삐 = {}
    for v in W.VIEWS:
        a, f = 갑주[v] > 0.5, 프레임[v] > 0.5
        삐[v] = float((f & ~a).sum() / max(f.sum(), 1))
    r["1 삐져나온 몫"] = 삐
    r["1 통과(<=2%)"] = max(삐.values()) <= 0.02
    거울 = lambda x: x[:, ::-1]
    def iou(a, b): return float((a & b).sum() / max((a | b).sum(), 1))
    r["2 거울 IoU"] = {"프레임": iou(프레임["front"] > 0.5, 거울(프레임["back"] > 0.5)),
                    "갑주(참고)": iou(갑주["front"] > 0.5, 거울(갑주["back"] > 0.5))}
    r["2 통과(>=0.90)"] = r["2 거울 IoU"]["프레임"] >= 0.90
    va, vf = 부피(갑주, bs_a), 부피(프레임, bs_f)
    r["3 부피"] = {"갑주": va, "프레임": vf, "비": round(vf / max(va, 1), 3)}
    r["3 통과(<=0.60)"] = vf / max(va, 1) <= 0.60
    print(json.dumps(r, ensure_ascii=False, indent=1))
    p = os.path.join(H.OUT, "기록", "겹도안_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(r, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import cv2
    타일 = []
    for v in W.VIEWS:
        a, f = 갑주[v] > 0.5, 프레임[v] > 0.5
        im = np.full(a.shape + (3,), 255, np.uint8)
        im[a] = (215, 215, 215); im[f & a] = (200, 120, 40); im[f & ~a] = (40, 40, 230)
        타일.append(cv2.resize(im, (360, 360), interpolation=cv2.INTER_AREA))
    cv2.imencode(".png", np.hstack(타일))[1].tofile(os.path.join(H.OUT, "겹도안_메카2.png"))
    print(p)


if __name__ == "__main__":
    main()
