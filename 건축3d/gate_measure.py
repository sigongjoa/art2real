# -*- coding: utf-8 -*-
"""**딴 윤곽선을 자로 쓴다.** 형태는 블렌더가 짓는다 — 여기서는 치수만 뽑는다.

    python gate_measure.py gate_front.json gate_spec.json

윤곽선을 그대로 밀어내면 **종이 오린 것**이 된다. 원화가 준 건 치수지 부피가 아니다.
그래서 여기서 잰 값만 `gate_spec.json` 에 넣고, `gate_build.py` 가 그걸 읽어
아치는 아치로 · 기둥은 기둥으로 · 열주는 뒤로 물러나는 칸으로 짓는다.

**규칙: 짓는 스크립트는 이 파일이 낸 spec 만 읽는다.** 상수를 짓는 쪽에 안 적는다
(스킬 `art-to-3d-maps` 의 규율 — 값과 출처가 같이 다녀야 하류가 거른다).

재는 것 —

    아치      꼭짓점 · 기공선(어깨) · 반너비 · **행마다의 반너비 프로필**
    기둥      아치 양옆 금색 기둥의 x 중심과 폭
    바닥      바닥 슬래브가 시작하는 행
    십자가    제일 위 금색 덩어리의 상자
"""
import json
import sys

import numpy as np


def load_mask(path):
    from PIL import Image
    a = np.asarray(Image.open(path).convert("L"))
    return a > 127


def arch(mask):
    """가운데 구멍 = 첨두아치. **행마다 반너비를 재면 그게 아치 곡선이다.**"""
    H, W = mask.shape
    cx = W // 2
    # 가운데 세로줄에서 금색이 아닌 가장 긴 구간이 아치 구멍이다
    col = ~mask[:, cx]
    runs, s = [], None
    for y in range(H):
        if col[y] and s is None:
            s = y
        elif not col[y] and s is not None:
            runs.append((s, y - 1))
            s = None
    if s is not None:
        runs.append((s, H - 1))
    runs = [r for r in runs if r[1] - r[0] > H * 0.05]
    assert runs, "가운데 줄에서 아치 구멍을 못 찾았다"
    top, bot = max(runs, key=lambda r: r[1] - r[0])
    prof = []
    for k in range(17):
        y = int(round(top + (bot - top) * k / 16.0))
        row = ~mask[y]
        # 중심에서 좌우로 뻗어 금색을 만날 때까지
        l = cx
        while l > 0 and row[l - 1]:
            l -= 1
        r = cx
        while r < W - 1 and row[r + 1]:
            r += 1
        prof.append([round((y - top) / float(bot - top), 4),
                     round((r - l) / 2.0 / W, 5)])
    return top, bot, prof


def columns(mask, top, bot):
    """아치 어깨 아래에서 좌우 금색 기둥의 x 중심·폭. **아치를 받치는 것들이다.**"""
    H, W = mask.shape
    y = int(top + (bot - top) * 0.80)                 # 기둥이 확실히 있는 높이
    row = mask[y]
    runs, s = [], None
    for x in range(W):
        if row[x] and s is None:
            s = x
        elif not row[x] and s is not None:
            runs.append((s, x - 1))
            s = None
    if s is not None:
        runs.append((s, W - 1))
    runs = [r for r in runs if r[1] - r[0] > W * 0.01]
    cx = W / 2.0
    left = [r for r in runs if r[1] < cx]
    right = [r for r in runs if r[0] > cx]
    assert left and right, (len(runs), y)
    a = max(left, key=lambda r: r[1])                 # 중심에 제일 가까운 것
    b = min(right, key=lambda r: r[0])
    return [[round((a[0] + a[1]) / 2.0 / W, 5), round((a[1] - a[0]) / float(W), 5)],
            [round((b[0] + b[1]) / 2.0 / W, 5), round((b[1] - b[0]) / float(W), 5)]]


def floor_row(mask, arch_bot):
    """바닥 슬래브가 시작하는 행. **아치 밑에서 아래로** 훑어 폭의 절반이 금색인 첫 행.

    처음엔 맨 아래에서 위로 훑었더니 1.000 이 나왔다 — 맨 아랫줄이 어두운 바닥이라
    조건이 처음부터 참이었다. **찾는 방향이 틀리면 값이 아니라 끝값이 나온다.**"""
    H, W = mask.shape
    frac = mask.mean(axis=1)
    for y in range(arch_bot, H):
        if frac[y] > 0.5:
            return y
    return None


def cross_box(mask, arch_top):
    """제일 위 금색 덩어리(십자가)의 상자. **가운데 3할만** 본다.

    폭 전체를 보면 양옆 열주가 같이 잡혀 x 가 0~1 로 나온다 — 처음에 그렇게 나왔다."""
    H, W = mask.shape
    x0, x1 = int(W * 0.35), int(W * 0.65)
    sub = mask[:arch_top, x0:x1]
    ys, xs = np.nonzero(sub)
    assert len(xs), "아치 위 가운데에 금색이 없다"
    return {"x": [round((xs.min() + x0) / float(W), 5), round((xs.max() + x0) / float(W), 5)],
            "y": [round(ys.min() / float(H), 5), round(ys.max() / float(H), 5)]}



def ornament(src, W, H, top, bot, cols):
    """**장식의 수를 센다.** 형태가 아니라 수다 — 규칙으로 깔려면 수만 있으면 된다.

    셀에서 선은 기하가 낸다(`LESSONS` 73·74). 그래서 **선 덩어리 수 = 부품 수**로 읽는다.
    원화는 10만 화소당 118 덩어리인데 손으로 놓은 판은 11 이었다. 그 격차가
    「조촐하다」의 정체다 — 띠마다 몇 개인지를 세서 그만큼 깔아야 한다."""
    import cv2
    im = cv2.imread(src, cv2.IMREAD_COLOR)
    im = cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA)
    e = cv2.Canny(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), 60, 160)

    def cnt(x0, x1, y0, y1):
        x0, x1 = max(0, int(x0)), min(W, int(x1))
        y0, y1 = max(0, int(y0)), min(H, int(y1))
        if x1 - x0 < 4 or y1 - y0 < 4:
            return 0
        n, _, st, _ = cv2.connectedComponentsWithStats(
            (e[y0:y1, x0:x1] > 0).astype(np.uint8), 8)
        return int((st[1:, cv2.CC_STAT_AREA] >= 10).sum())

    ty, by = top, bot
    spring = ty + (by - ty) * 0.37
    cx0, cw0 = cols[0][0] * W, cols[0][1] * W
    cx1, cw1 = cols[1][0] * W, cols[1][1] * W
    return {
        "column": cnt(cx0 - cw0, cx0 + cw0, spring, by)
                  + cnt(cx1 - cw1, cx1 + cw1, spring, by),
        "arch": cnt(cx0 - cw0, cx1 + cw1, ty, spring),
        "pinnacle": cnt(cx0 - cw0 * 1.5, cx0 + cw0 * 1.5, ty * 0.55, spring)
                    + cnt(cx1 - cw1 * 1.5, cx1 + cw1 * 1.5, ty * 0.55, spring),
        "cross": cnt(W * 0.35, W * 0.65, 0, ty * 0.75),
        "colonnade": cnt(0, cx0 - cw0, ty * 0.4, by) + cnt(cx1 + cw1, W, ty * 0.4, by),
        "src": "measured — 띠마다 캐니 선 덩어리 수(10px 이상)",
    }


def main():
    src, dst = sys.argv[1], sys.argv[2]
    js = json.load(open(src, encoding="utf-8"))
    W, H = js["size"]
    mask = load_mask(src.replace(".json", "_mask.png"))
    assert mask.shape == (H, W), (mask.shape, (H, W))
    top, bot, prof = arch(mask)
    spec = {
        "src": js["src"],
        "size_px": [W, H],
        "height_m": {"v": 11.0, "src": "given — 사람이 정한 절대값 하나"},
        "thickness_m": {"v": 1.20, "src": "guessed — 옆모습 원화가 없다"},
        "arch": {"top": round(top / float(H), 5), "bottom": round(bot / float(H), 5),
                 "profile": prof, "src": "measured — 가운데 구멍의 행별 반너비"},
        "columns": {"v": columns(mask, top, bot), "src": "measured — 어깨 아래 좌우 금색 런"},
        "floor": ({"v": round(_fl / float(H), 5), "src": "measured — 아치 밑 폭 50% 문턱"}
              if (_fl := floor_row(mask, bot)) is not None else
              {"v": None, "src": "못 쟀다 — 바닥이 금색으로 안 잡힌다"}),
        "cross": {"v": cross_box(mask, top), "src": "measured — 아치 위 금색 상자"},
        "bay": {"n": 5, "spacing_m": 4.2, "src": "guessed — 원근으로 그려져 못 쟀다"},
        "ornament": ornament(js["src"], W, H, top, bot, columns(mask, top, bot)),
    }
    json.dump(spec, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("MEASURE 아치 %.3f~%.3f · 기둥 %s · 바닥 %.3f -> %s"
          % (spec["arch"]["top"], spec["arch"]["bottom"],
             spec["columns"]["v"], spec["floor"]["v"], dst))


def demo():
    """가짜 아치 마스크를 만들어 꼭짓점·기공선·기둥이 제 자리에 잡히는지 본다."""
    H, W = 400, 300
    m = np.ones((H, W), bool)
    for y in range(80, 340):                            # 첨두아치 구멍
        t = (y - 80) / 260.0
        half = int(70 * min(1.0, t * 2.2) ** 0.7)
        m[y, W // 2 - half:W // 2 + half] = False
    top, bot, prof = arch(m)
    assert abs(top - 80) <= 2 and abs(bot - 339) <= 2, (top, bot)
    assert prof[0][1] < prof[-1][1], (prof[0], prof[-1])   # 위가 좁고 아래가 넓다
    c = columns(m, top, bot)
    assert c[0][0] < 0.5 < c[1][0], c
    print("gate_measure.demo OK  아치 %d~%d · 기둥 %.2f/%.2f" % (top, bot, c[0][0], c[1][0]))


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        main()
