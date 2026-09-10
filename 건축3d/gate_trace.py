# -*- coding: utf-8 -*-
"""**형태의 윤곽선을 딴다.** 톤 조각이 아니라 실루엣이다.

    python gate_trace.py D:/imggen/blades6/r6_gate_front.png gate_front.json [--h 1024]

## 왜 다시 쓰나

처음엔 `art3d.py` 의 판 310개(`poly_px`)를 그대로 세웠다. 그건 **톤 분할**이라
같은 기둥도 밝은 면·어두운 면으로 쪼개지고, 하늘로 분류된 조각을 버리면 그 자리가
구멍이 된다 — 세워놓으니 성당이 아니라 **색종이 조각**이었다.

형태를 원하면 형태의 경계를 따야 한다. **금색 덩어리 하나를 마스크로 만들고
그 바깥선과 구멍선을 딴다.** 첨두아치는 「구멍」으로, 열주 사이 틈도 「구멍」으로 나온다.

## 구멍이 핵심이다

`RETR_CCOMP` 는 바깥 윤곽과 그 안의 구멍을 두 층으로 준다. 구멍을 안 쓰면
아치가 **막힌 판**이 되고, 그게 원화와 제일 다른 점이다.
블렌더의 커브는 스플라인 여럿을 주면 짝홀 규칙으로 구멍을 뚫어준다.
"""
import json
import sys

import cv2
import numpy as np

MIN_AREA = 700.0           # 이보다 작은 조각은 버린다 (px^2, 작업 해상도 기준).
                           # 60 으로 두니 옆 열주가 **파편 수십 개**로 부서졌다 —
                           # 원근으로 그려진 잔디테일이라 덩어리가 안 된다
EPS_FRAC = 0.0016          # 폴리곤 단순화. 둘레에 비례해서 준다


def gold_mask(bgr):
    """**금색 덩어리 하나.** 채도·밝기로 가르고 형태학으로 부스러기를 턴다."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    m = ((h > 12) & (h < 45) & (s > 60) & (v > 90)).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k, iterations=2)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k, iterations=1)
    return m


def trace(mask):
    """바깥 윤곽 + 그 안의 구멍. 돌려주는 건 [(바깥, [구멍...]), ...]."""
    cs, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hier is None:
        return []
    hier = hier[0]
    holes = {}
    for i, hh in enumerate(hier):
        if hh[3] != -1:
            holes.setdefault(hh[3], []).append(i)

    def simp(c):
        e = EPS_FRAC * cv2.arcLength(c, True)
        return cv2.approxPolyDP(c, e, True).reshape(-1, 2).tolist()

    out = []
    for i, hh in enumerate(hier):
        if hh[3] != -1 or cv2.contourArea(cs[i]) < MIN_AREA:
            continue
        hs = [simp(cs[j]) for j in holes.get(i, [])
              if cv2.contourArea(cs[j]) >= MIN_AREA]
        o = simp(cs[i])
        if len(o) >= 3:
            out.append((o, [x for x in hs if len(x) >= 3]))
    return out


def main():
    src, dst = sys.argv[1], sys.argv[2]
    hgt = int(sys.argv[sys.argv.index("--h") + 1]) if "--h" in sys.argv else 1024
    im = cv2.imread(src, cv2.IMREAD_COLOR)
    assert im is not None, src
    im = cv2.resize(im, (int(round(im.shape[1] * hgt / im.shape[0])), hgt),
                    interpolation=cv2.INTER_AREA)
    m = gold_mask(im)
    shapes = trace(m)
    n_hole = sum(len(h) for _, h in shapes)
    json.dump({"src": src, "size": [im.shape[1], im.shape[0]],
               "coverage": round(float(m.mean()), 4),
               "shapes": [{"outer": o, "holes": h} for o, h in shapes]},
              open(dst, "w", encoding="utf-8"))
    cv2.imwrite(dst.replace(".json", "_mask.png"), m * 255)
    print("TRACE %d덩어리 · 구멍 %d · 금 면적 %.2f -> %s"
          % (len(shapes), n_hole, m.mean(), dst))


def demo():
    """구멍 뚫린 도넛을 그려, 바깥 하나와 구멍 하나로 나오는지만 본다."""
    im = np.zeros((200, 200, 3), np.uint8)
    im[:] = (40, 20, 10)
    cv2.circle(im, (100, 100), 70, (60, 200, 240), -1)      # BGR 금색
    cv2.circle(im, (100, 100), 30, (40, 20, 10), -1)
    s = trace(gold_mask(im))
    assert len(s) == 1, len(s)
    assert len(s[0][1]) == 1, s[0][1]
    assert 8 <= len(s[0][0]) <= 60, len(s[0][0])
    print("gate_trace.demo OK  덩어리 1 · 구멍 1 · 꼭짓점 %d" % len(s[0][0]))


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        main()
