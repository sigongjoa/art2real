# -*- coding: utf-8 -*-
"""원화 3판 -> 판 분할 + 크리스 인플레이션 깊이맵. `hull.py` 가 이걸 읽는다.

    python 깊이.py [케이스]  ->  out/깊이/<케이스>/<시점>/{labels_grown.npy, depth.npy, art3d.json, ...}

도구는 `art-to-3d-maps` 스킬의 `art3d.py` · `depth.py` 다. 여기서 하는 일은 셋뿐이다.

## ① 알파를 흰 바탕에 얹는다

원화는 RGBA 이고 **투명한 데의 RGB 가 검정**이다. 스킬 도구는 RGB 로 읽으니 그대로 주면
배경이 검은 판 하나로 들어온다. `win.art_mask` 와 같은 규약으로 맞춰 준다.

## ② `art3d.py` 의 한 줄을 고쳐서 돌린다 (스킬 파일은 안 건드린다)

    thin = line & ~_mf(line, 9)                  <- 침식만 한다
    thin = line & ~_mf(_mf(line, 9), 9, mx=True) <- 열림

규칙은 「얇은 것만 선, 두꺼운 검정은 면」인데 침식만 하면 **검은 면의 테두리 4화소와
폭 9 미만 검정이 통째로 선이 된다** (송곳니·줄무늬·좁은 언더아머). 실측: 덩어리 검정
11,238 화소 중 면으로 남은 건 4,863 (43%) 뿐이었다.

고침은 held-out 11장에서 쟀다 (기준은 Canny — 고침과 무관한 검출기):

    경계 IoU 평균 0.827 -> 0.865 · 좋아진 장 10/11 · 미라벨 34% -> 27%
    배율 320/512/768 에서도 9/9 개선. **튜닝 상수가 아니라 버그 수정이다**

야스호·스탠드 3종처럼 다른 작화도 포함이다. 다만 12장 전부 애니 셀 작화라
채색화·흑백 선화·서양 코믹은 **한 장도 안 테스트했다.**

## ③ 깊이맵

`depth.py` 가 판마다 평면을 맞추고 경계에만 골을 판다. 판 안쪽 평평도가 지표고
10도 이하라야 한다 (실측 front 3.9 · side 2.3 · back 4.9).

**`--cut-bottom 1.0` 을 준다 — 이게 없으면 다리가 사라진다 (2026-09-10).**
`depth.py` 는 흉상 도구라 기본값이 0.78 이다: 그림 아래 22% 를 「어깨」로 보고
`h[~head] = 0` 으로 지운다. 전신 턴어라운드에 그대로 걸면 **다리·발의 깊이가 매번 0** 이고,
`hull.load_depth` 는 0 을 「제일 들어간 곳」으로 읽어 `carve_depth` 가 거기서 앞뒤로
`LAM·D` 를 파낸다.

기본도형 벤치가 이걸 잡았다 — **상자는 이진 hull 이 정확히 1.0000 인데 깊이 깎기가
0.9308** 이었다. 깎을 게 없는 물건에서 7% 를 파냈고, 그게 512 행 중 399 행부터였다
(= int(512 × 0.78)). 캐릭터 12장에서도 라벨 있는 화소의 3~24% 가 깊이 0 이었다.
"""
import io
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "깊이")
SKILL = os.path.join(os.path.expanduser("~"), ".claude", "skills", "art-to-3d-maps")
# 케이스는 hull.CASES 하나에서만 온다 — 두 군데 적으면 언젠가 어긋난다
SCALE = 512                                      # art3d 는 라벨링이 순수 파이썬이라 512 권장

PATCH = ("    thin = line & ~_mf(line, 9)",
         "    thin = line & ~_mf(_mf(line, 9), 9, mx=True)")


def patched_art3d(dst):
    """스킬의 art3d.py 에 한 줄만 바꿔 복사한다. 원본은 그대로 둔다."""
    s = io.open(os.path.join(SKILL, "art3d.py"), encoding="utf-8").read()
    assert PATCH[0] in s, "art3d.py 가 바뀌었다 — 침식/열림 줄을 다시 찾을 것"
    io.open(dst, "w", encoding="utf-8", newline="\n").write(s.replace(PATCH[0], PATCH[1], 1))
    return dst


def on_white(src, dst):
    """알파를 흰 바탕에 얹는다 — `win.art_mask` 와 같은 규약."""
    im = cv2.imdecode(np.fromfile(src, np.uint8), cv2.IMREAD_UNCHANGED)
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    if im.shape[2] == 4:
        a = im[:, :, 3:4].astype(np.float32) / 255.0
        im = (im[:, :, :3] * a + 255 * (1 - a)).astype(np.uint8)
    cv2.imencode(".png", im[:, :, :3])[1].tofile(dst)
    return dst


def main():
    import hull as H
    case = sys.argv[1] if len(sys.argv) > 1 else H.CASE
    root = os.path.join(OUT, case)
    os.makedirs(root, exist_ok=True)
    art3d = patched_art3d(os.path.join(OUT, "_art3d_열림.py"))
    py311 = ["py", "-3.11"] if os.name == "nt" else [sys.executable]
    print("케이스 %s" % case)
    for v, f in H.CASES[case]["src"].items():
        d = os.path.join(root, v)
        w = on_white(os.path.join(H.art_dir(case), f), os.path.join(root, "_흰_%s.png" % v))
        for step in (art3d, os.path.join(SKILL, "depth.py")):
            cmd = py311 + [step, w if step == art3d else d]
            if step == art3d:
                cmd += ["--out", d, "--scale", str(SCALE)]
            else:
                cmd += ["--cut-bottom", "1.0"]      # **전신이다.** 아래 참조
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=root)
            tail = [x for x in (r.stdout or "").strip().split("\n") if x][-1:]
            print("  %-6s %-8s %s" % (v, os.path.basename(step)[:8], tail[0] if tail else r.stderr[-120:]))
        assert os.path.exists(os.path.join(d, "depth.npy")), "%s: depth.npy 가 안 나왔다" % v
        # **라벨이 붙은 자리에 깊이 0 이 넓게 있으면 안 된다.** `hull.load_depth` 가 0 을
        # 「제일 들어간 곳」으로 읽어 그 자리를 통째로 파낸다. 이 문이 없어서 두 달치
        # 깊이맵이 다리 없이 나왔다 (아래 참조)
        dep = np.load(os.path.join(d, "depth.npy"))
        lab = np.load(os.path.join(d, "labels_grown.npy"))
        m = lab > 0
        zr = float(((dep == 0) & m).sum() / max(m.sum(), 1))
        print("       라벨 있는데 깊이 0: %.1f%%" % (100 * zr))
        assert zr < 0.05, "%s: 라벨 있는 자리의 %.1f%% 가 깊이 0 이다 — 깎기가 거길 파낸다" % (v, 100 * zr)


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main()
