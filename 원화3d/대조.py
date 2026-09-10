# -*- coding: utf-8 -*-
"""**여러 데이터로 눈이 맞는지 본다.** CC0 모델 여럿에 파이프라인을 돌리고 정답과 대본다.

    python 대조.py            (있는 건 건너뛰고 이어서 한다)
        -> out/대조.json · out/대조.png · out/기록/대조_<날짜>.json

케이스는 **`벤치.json` 에 손으로 박은 것만** 쓴다. 자동 수집을 하면 집합이 실행마다
달라져서 어제 숫자와 오늘 숫자를 비교할 수 없다 — 실제로 12 -> 48 -> 35 -> 29 로 흔들렸고
그 사이에 내린 결론이 세 번 죽었다.

**튜닝셋과 봉인셋을 나눠 보고한다.** 상수(`LAM`·`THRESH`)는 튜닝셋에서만 맞추고
봉인셋은 그 뒤에 한 번 본다. 안 나누면 같은 데서 맞추고 같은 데서 자랑하게 된다.

한 케이스에서 「깊이 깎기가 이진 hull 보다 낫다」고 말한 게 진짜인지, 아니면 그 한 장에서만
그런 건지는 여러 장으로만 갈린다. 오늘 이 저장소에서 두 번 그 실수를 했다 —
재구성 오차 0.9 를 보고 통과라 했고, 견갑을 턴어라운드로 착각했다.

## 무엇을 대나

같은 모델에서 뽑은 3판으로 **셋**을 만들고 전부 원본 메시와 대본다.

    이진 hull    실루엣 세 장의 교집합. 단면이 축정렬 직사각형이다
    깊이 깎기    거기에 판 분할 + 크리스 인플레이션 깊이를 먹인 것
    균일 깎기    **대조군.** 깊이맵 대신 같은 부피가 될 때까지 균일하게 침식한 것.
                 정보를 0 만큼 쓴다

## 대조군이 왜 있나 — 2026-09-09 에 이것 때문에 결론 하나가 죽었다

「깊이 깎기가 이진보다 3D IoU 가 +0.014 높다」를 근거로 좋아졌다고 했는데,
**균일 깎기가 그보다 더 높았다** (12장에서 깊이맵이 4승, 평균 -0.0034).

즉 그 이득은 깊이맵이 형태를 되찾아서가 아니라 **부피가 줄어서**였다. hull 은 뚱뚱하니까
아무렇게나 깎아도 IoU 가 오른다. 이진 hull 하고만 비교하면 그걸 못 가른다.

**앞으로 「좋아졌다」는 균일 깎기를 이겼을 때만 쓴다.**

## 이게 검증 못 하는 것

전부 렌더한 판이라 세 판이 자동으로 일치한다. 그래서 `align` 과 판 불일치 처리는
여기서 **시험되지 않는다** (`시트.py` 참조). 손그림 턴어라운드는 여전히 오메가몬 하나뿐이다.
"""
import json
import os
import subprocess
import sys

import numpy as np
import trimesh
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull as H
import win as W
import 각도 as ANG
import 정답 as J
from 계획 import _font

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
VROID = os.path.join(OUT, "vroid")


def models():
    """쓸 모델 (이름, 경로). VRoid 는 폴더 안 .vrm, Poly Pizza 는 out/모델 의 .glb."""
    out = []
    if os.path.isdir(VROID):
        for d in sorted(os.listdir(VROID)):
            p = os.path.join(VROID, d)
            if os.path.isdir(p):
                v = [f for f in os.listdir(p) if f.lower().endswith(".vrm")]
                if v:
                    out.append((d, os.path.join(p, v[0])))
    poly = os.path.join(OUT, "모델")
    if os.path.isdir(poly):
        for f in sorted(os.listdir(poly)):
            if f.lower().endswith(".glb"):
                out.append((os.path.splitext(f)[0], os.path.join(poly, f)))
    return out


def sheets():
    """받아둔 모델마다 판을 뽑는다. 이미 있으면 건너뛴다."""
    for name, path in models():
        if os.path.exists(os.path.join(OUT, "시트", name, "truth.glb")):
            continue
        print("  판 뽑기 %s" % name)
        r = subprocess.run([sys.executable, os.path.join(HERE, "시트.py"), path, "--이름", name],
                           cwd=HERE, capture_output=True, text=True, encoding="utf-8")
        if r.returncode:
            print("     실패: %s" % (r.stderr or "")[-160:])
    H.register_sheets()


def build(case):
    """정렬까지 끝낸 마스크·깊이와 두 판본의 복셀."""
    src, base = H.CASES[case]["src"], H.art_dir(case)
    bs = H.CASES[case]["back_sign"]
    masks, deps = {}, {}
    for v, f in src.items():
        d = H.declutter(W.art_mask(os.path.join(base, f)))
        masks[v], deps[v] = H.to_win(d, H.load_depth(v, d, case=case))
    p = H.align(masks, back_sign=bs)
    masks = H._warp(masks, p)
    deps = {v: H._warp_one(a, v, p) for v, a in deps.items()}
    plain, axes = H.carve(masks, back_sign=bs)
    deep, _ = H.carve_depth(masks, deps, back_sign=bs)
    return plain, deep, axes, p


def to_mesh(vox, axes):
    V, F = H.mesh_from(vox, axes)
    m = trimesh.Trimesh(V, F, process=True)
    parts = m.split(only_watertight=False)
    if len(parts) > 1:
        m = max(parts, key=lambda q: abs(q.volume))
    if m.volume < 0:
        m.invert()
    return m


CANON = 192                                      # **계단은 이 래스터에서만 잰다.** 아래 참조


def stair(vox):
    """**표면 계단** — 앞면 깊이의 2D 라플라시안 / 깊이범위. 클수록 표면이 자글자글하다.

    **정답이 없어도 계산된다.** 그래서 고객 원화에도 쓸 수 있는 지표 후보다 — 3D IoU 는
    부피만 맞으면 표면이 누더기여도 오른다.

    ## 이 값은 pitch 를 탄다 — 2026-09-10 에 같은 실수를 네 번 했다

    함수가 float 하나만 돌려주니 어디서 왔는지가 안 남고, 그래서 하루에 네 번을 맞댔다
    (배수 1.61 · hf 대 깎은 결과 · 마칭큐브 무죄 · jf 대 정답). **조심해서 될 일이 아니다.**

    두 가지를 고쳤는데 **하나는 실패했다.**

    - 배열 크기: `CANON` 으로 내려 재운다. 칸 수·여백이 달라도 같은 값이 나온다 (자체검사 1).
    - **복셀 한 칸의 크기(pitch): 못 없앤다.** 이 값이 재는 것의 상당 부분이 그 격자의
      양자화 잡음이라, 같은 물건도 128/192/256 격자에서 0.0156/0.0104/0.0071 로 나온다
      (77% 벌어짐). 캐논으로 내려 재워도 안 없어진다 — 잡음이 이미 데이터에 들어와 있다.

    그래서 규칙은 하나뿐이다 — **같은 pitch 에서 잰 값끼리만 맞댄다.** 값 옆에 `계단_pitch`
    를 같이 적어서 나중에도 확인할 수 있게 한다. `python 대조.py 자체검사` 가 잡는 것은
    「여백·칸수는 안 탄다」와 「물결이 커지면 값도 커진다」 둘이고, pitch 의존은 **못 잡으니
    숫자로 찍어 보여준다.**

    무엇에 반응하는지는 인공 판으로 재봤다 (`_slab`):

        잔결 0 / .004 / .01 / .02   ->  0.0104 / 0.0559 / 0.1147 / 0.1825   (잘 오른다)
        매끈한 물결 진폭 2배         ->  오히려 내려간다. **큰 물결은 계단이 아니다**

    처음엔 「진폭이 크면 값도 커야 한다」로 검사를 짰다가 떨어졌는데, **검사가 틀렸다.**"""
    import cv2
    d, hit = ANG.depth(vox, 0)
    if hit.sum() < 9:
        return float("nan")
    # **물건 자리만 잘라서** 캐논 래스터로 내려 재운다. 안 자르면 여백 넓이가 값을 바꾼다
    # (실측: 여백만 붙였는데 0.0104 -> 0.0086). 값과 마스크를 같이 줄이고 나눈다
    ys, xs = np.where(hit)
    sl = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
    d, hit = d[sl], hit[sl]
    k = (CANON, CANON)
    m = hit.astype(np.float32)
    num = cv2.resize(np.where(hit, d, 0).astype(np.float32), k, interpolation=cv2.INTER_AREA)
    den = cv2.resize(m, k, interpolation=cv2.INTER_AREA)
    on = den > 0.5
    if on.sum() < 9:
        return float("nan")
    dd = np.where(on, num / np.maximum(den, 1e-6), 0.0)
    rng = max(dd[on].max() - dd[on].min(), 1e-6)
    # **축을 안 고른다.** 2차차분을 한 축에서만 재면 축을 잘못 잡는 실수가 그대로 산다 —
    # 실제로 x 를 잰다고 적어놓고 z 를 재고 있었다. 2D 라플라시안이면 고를 게 없다
    lap = np.abs(dd[2:, 1:-1] + dd[:-2, 1:-1] + dd[1:-1, 2:] + dd[1:-1, :-2]
                 - 4 * dd[1:-1, 1:-1])
    mm = (on[2:, 1:-1] & on[:-2, 1:-1] & on[1:-1, 2:] & on[1:-1, :-2] & on[1:-1, 1:-1])
    return float(np.mean(lap[mm]) / rng) if mm.any() else float("nan")


def _slab(n=192, amp=0.12, freq=3.0, jitter=0.0, seed=0):
    """앞면이 사인으로 물결치는 판. `jitter` 를 주면 그 위에 잔결을 뿌린다.

    **매끈한 큰 물결과 자글자글한 잔결을 가르는 게 이 지표가 할 일이다.**"""
    r = np.random.default_rng(seed)
    x = np.linspace(0, 1, n)[:, None, None]
    y = np.linspace(0, 1, n)[None, :, None]
    front = 0.35 + amp * np.sin(2 * np.pi * freq * x) + np.zeros((1, 1, n))
    if jitter:
        front = front + r.normal(0, jitter, (n, 1, n))
    return (y >= front) & (y <= 0.75)


def selfcheck():
    """**같은 물건을 다른 격자로 재면 같은 값이 나와야 한다.** 안 나오면 비교를 못 한다.

    문턱은 잰 값 위에 얹었다 — 128/192/256 에서 재고 최대·최소의 벌어짐을 본다."""
    # 1. 같은 pitch 면 여백·칸수는 안 탄다 — 이건 지켜져야 한다
    v = _slab(192)
    pad = np.zeros((192 + 40, 192, 192 + 24), bool)
    pad[20:212, :, 12:204] = v
    a, b = stair(v), stair(pad)
    assert abs(a - b) / max(a, 1e-9) < 0.05, "여백만 붙였는데 값이 바뀐다 (%.4f vs %.4f)" % (a, b)
    # 2. **잔결이 커지면 값도 커야 한다.** 이게 이 지표가 하는 일이다
    js = [stair(_slab(jitter=j)) for j in (0.0, 0.004, 0.01, 0.02)]
    assert all(x < y for x, y in zip(js, js[1:])), "잔결을 뿌렸는데 값이 안 오른다 %s" % js
    # 3. **매끈한 큰 물결은 잔결이 아니다.** 진폭 2배짜리 매끈한 판이, 진폭 절반에
    #    잔결만 조금 뿌린 판보다 낮아야 한다 — 형태와 잡음을 가르는지
    assert stair(_slab(amp=0.24)) < stair(_slab(amp=0.06, jitter=0.004))
    # 3. pitch 는 못 없앤다. 못 잡으니 찍어서 보여준다
    vals = [stair(_slab(n)) for n in (128, 192, 256)]
    print("  같은 물건 · 다른 pitch — 128/192/256 에서 %s  (벌어짐 %.0f%%)"
          % (" · ".join("%.4f" % x for x in vals),
             100 * (max(vals) - min(vals)) / max(np.mean(vals), 1e-9)))
    print("  잔결 0 / .004 / .01 / .02 -> %s" % " · ".join("%.4f" % x for x in js))
    print("  자체검사 통과 — 여백 %.4f=%.4f · 잔결에 오르고 매끈한 물결에는 안 오른다" % (a, b))
    print("  ** pitch 가 다르면 위 숫자들처럼 갈린다. 같은 pitch 끼리만 맞댈 것 **")


def bench():
    """`벤치.json` — 손으로 고정한 케이스 목록. 없으면 멈춘다."""
    p = os.path.join(HERE, "벤치.json")
    assert os.path.exists(p), "벤치.json 이 없다. 케이스를 손으로 고정하고 시작할 것"
    return json.load(open(p, encoding="utf-8"))


def main():
    sheets()
    b = bench()
    split = {c["name"]: c["split"] for c in b["cases"]}
    cases = [c["name"] for c in b["cases"]]
    missing = [c for c in cases if c not in H.CASES]
    assert not missing, "벤치.json 에 있는데 판이 없다: %s" % missing[:3]
    rows, broken = [], []
    for c in cases:
        if not os.path.exists(os.path.join(OUT, "깊이", c, "front", "depth.npy")):
            print("  깊이 %s" % c)
            subprocess.run([sys.executable, os.path.join(HERE, "깊이.py"), c],
                           cwd=HERE, capture_output=True)
        try:
            t = trimesh.load(os.path.join(OUT, "시트", c, "truth.glb"), force="mesh")
            # **서 있는 물건만 센다.** 창 규약이 키로 정규화하므로, 키가 대표 치수가 아닌
            # 물건(옆으로 퍼진 조각상·누운 것)은 판을 뽑는 것 자체가 뜻이 없다.
            # 실측: statue_Stag 은 높이 1.0 에 깊이 3.64 였다
            ex = t.bounds[1] - t.bounds[0]
            if ex[1] > 1.6 * ex[2] or ex[0] > 2.2 * ex[2]:
                print("  %-22s 건너뜀 — 서 있는 물건이 아니다 (가로 %.2f 깊이 %.2f 키 %.2f)"
                      % (c, ex[0], ex[1], ex[2]))
                continue
            plain, deep, axes, fit = build(c)
            T, ot = J.grid(t)
            # 대조군 — 깊이맵과 **같은 부피**가 될 때까지 균일 침식. 정보를 안 쓴다
            even, k = plain.copy(), 0
            while even.sum() > deep.sum() and k < 40:
                even = ndimage.binary_erosion(even); k += 1
            got, bad = {}, None
            for tag, vox in (("이진", plain), ("깊이", deep), ("균일", even)):
                G, og = J.grid(to_mesh(vox, axes))
                A, B = J.common(T, ot, G, og)
                if tag == "이진":
                    bad = J.invariant(A, B)      # **자가 틀렸는지 먼저 본다**
                    truth_stair = stair(A)       # 정답의 계단 — 비교 기준
                got[tag] = {"iou": (A & B).sum() / max((A | B).sum(), 1),
                            "vol": B.sum() / max(A.sum(), 1),
                            "miss": (A & ~B).sum() / max(A.sum(), 1),
                            "계단": stair(B), "계단_pitch": J.PITCH}
            if bad:
                broken.append({"case": c, "why": bad})
                print("  %-22s 채점 불가 — %s" % (c, " · ".join(bad)))
                continue
            r = {"case": c, "fit": [round(float(x), 3) for x in fit],
                 "box": round(H.box_score(deep), 2), "계단_정답": round(truth_stair, 4),
                 **{k + "_" + kk: round(float(vv), 4 if kk == "계단" else 3)
                    for k, v in got.items() for kk, vv in v.items()}}
            rows.append(r)
            print("  %-22s 이진 %.3f -> 깊이 %.3f  (%+.3f)"
                  % (c, r["이진_iou"], r["깊이_iou"], r["깊이_iou"] - r["이진_iou"]))
        except Exception as e:
            print("  %-22s 실패 %s: %s" % (c, type(e).__name__, str(e)[:90]))
            continue

    if broken:
        print("\n  채점 불가 %d 장 — 불변식(hull 은 정답을 포함한다)을 어긴다:" % len(broken))
        for b in broken:
            print("    %-38s %s" % (b["case"][:38], " · ".join(b["why"])))
        json.dump(broken, open(os.path.join(OUT, "채점불가.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    if not rows:
        return
    json.dump(rows, open(os.path.join(OUT, "대조.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    for r in rows:
        r["split"] = split.get(r["case"], "?")
    d = np.array([r["깊이_iou"] - r["이진_iou"] for r in rows])
    print("\n  %d 장 · 깊이 깎기가 이긴 장 %d · 평균 차 %+.3f (최소 %+.3f · 최대 %+.3f)"
          % (len(rows), int((d > 0).sum()), d.mean(), d.min(), d.max()))
    st = np.array([[r["계단_정답"], r["이진_계단"], r["깊이_계단"]] for r in rows])
    print("  표면 계단(정답 없이 잰다) 중앙 — 정답 %.4f · 이진 %.4f · 깊이 %.4f"
          % tuple(np.nanmedian(st, 0)))
    e = np.array([r["깊이_iou"] - r["균일_iou"] for r in rows])
    print("  **대조군 대비** 깊이맵이 이긴 장 %d/%d · 평균 %+.4f"
          % (int((e > 0).sum()), len(rows), e.mean()))
    if e.mean() <= 0:
        print("     -> 깊이맵이 균일 침식만도 못하다. 이득은 형태가 아니라 부피 감소다")
    for sp in ("tune", "holdout"):
        v = [r for r in rows if r["split"] == sp]
        if not v:
            continue
        dd = np.array([r["깊이_iou"] - r["이진_iou"] for r in v])
        print("    %-8s n=%2d · 형태 중앙 %.3f · 못덮음 중앙 %.3f · 이득 %+.4f · 이긴장 %d/%d"
              % (sp, len(v), np.median([r["깊이_iou"] for r in v]),
                 np.median([r["깊이_miss"] for r in v]), dd.mean(), (dd > 0).sum(), len(v)))
    # **헤드라인 한 줄.** 봉인셋 기준이다 — 튜닝셋 숫자는 자기 자랑이다
    ho = [r for r in rows if r["split"] == "holdout"] or rows
    print("\n  기준선 | 형태 %.3f · 못덮음 %.3f · 완주 %d/%d · 채점불가 %d  (봉인 %d장)"
          % (np.median([r["깊이_iou"] for r in ho]), np.median([r["깊이_miss"] for r in ho]),
             len(rows), len(cases), len(broken), len(ho)))

    # 기록을 쌓는다 — 덮어쓰면 진행이 안 보인다
    import datetime
    hist = os.path.join(OUT, "기록")
    os.makedirs(hist, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    json.dump({"때": stamp, "케이스": len(cases), "점수낸장": len(rows),
               "채점불가": [b["case"] for b in broken],
               "LAM": H.LAM, "THRESH": H.THRESH, "rows": rows},
              open(os.path.join(hist, "대조_%s.json" % stamp), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("  기록 -> out/기록/대조_%s.json" % stamp)
    _ = stamp

    # 그림 — 위에 기준선 카드, 아래에 장별 이진 -> 깊이
    TOP = 214
    Wd, Ht = 960, TOP + len(rows) * 30 + 60
    im = Image.new("RGB", (Wd, Ht), "white")
    g = ImageDraw.Draw(im)
    lo, hi = min(min(r["이진_iou"], r["깊이_iou"]) for r in rows) - .02, \
             max(max(r["이진_iou"], r["깊이_iou"]) for r in rows) + .02
    xf = lambda v: 320 + (v - lo) / max(hi - lo, 1e-6) * (Wd - 400)

    # ── 기준선 카드 ─────────────────────────────────────────
    g.rectangle([16, 12, Wd - 16, TOP - 34], fill=(248, 248, 246), outline=(225, 225, 222))
    g.text((32, 24), "기준선  %s" % stamp.replace("_", " "), font=_font(13), fill=(120, 120, 120))
    hoi = np.median([r["깊이_iou"] for r in ho])
    hom = np.median([r["깊이_miss"] for r in ho])
    for i, (lab, val, sub) in enumerate((
            ("형태 (3D IoU)", "%.3f" % hoi, "봉인 %d장 중앙" % len(ho)),
            ("못덮음", "%.3f" % hom, "낮을수록 좋다"),
            ("완주", "%d/%d" % (len(rows), len(cases)), "채점불가 %d" % len(broken)),
            ("깊이맵 vs 대조군", "%+.3f" % np.mean([r["깊이_iou"] - r["균일_iou"] for r in ho]),
             "균일 침식 대비 %d/%d 승" % (sum(1 for r in ho if r["깊이_iou"] > r["균일_iou"]), len(ho))))):
        x = 32 + i * 228
        g.text((x, 50), lab, font=_font(12), fill=(110, 110, 110))
        g.text((x, 68), val, font=_font(30), fill=(25, 25, 25))
        g.text((x, 106), sub, font=_font(11), fill=(150, 150, 150))
    g.text((32, 134), "잰다     형태 정확도 · 파이프라인 상수 · 스타일 일반화",
           font=_font(12), fill=(70, 110, 70))
    g.text((32, 152), "못 잰다  판 불일치 · 작화 모순 · 실제 원화의 지저분함 — 케이스가 전부 렌더 판이다",
           font=_font(12), fill=(180, 80, 60))
    g.text((32, 170), "상수     LAM %.2f · THRESH %.2f  |  튜닝 %d장 / 봉인 %d장 (상수는 튜닝셋에서만 맞춘다)"
           % (H.LAM, H.THRESH, sum(1 for r in rows if r["split"] == "tune"), len(ho)),
           font=_font(12), fill=(110, 110, 110))

    g.text((20, TOP - 24), "3D IoU — 이진 hull → 깊이 깎기 · ● = 봉인셋",
           font=_font(13), fill=(20, 20, 20))
    for i, r in enumerate(rows):
        y = TOP + i * 30
        up = r["깊이_iou"] > r["이진_iou"]
        g.text((20, y - 7), ("● " if r.get("split") == "holdout" else "  ") + r["case"][:32],
               font=_font(12), fill=(40, 40, 40))
        x0, x1 = xf(r["이진_iou"]), xf(r["깊이_iou"])
        g.line([x0, y, x1, y], fill=(60, 150, 90) if up else (200, 80, 80), width=3)
        g.ellipse([x0 - 4, y - 4, x0 + 4, y + 4], fill="white", outline=(150, 150, 150), width=2)
        g.ellipse([x1 - 4, y - 4, x1 + 4, y + 4], fill=(60, 150, 90) if up else (200, 80, 80))
        g.text((x1 + 10, y - 7), "%.3f (%+.3f)" % (r["깊이_iou"], r["깊이_iou"] - r["이진_iou"]),
               font=_font(11), fill=(60, 150, 90) if up else (200, 80, 80))
    g.text((20, Ht - 34), "%d 장 중 %d 장에서 깊이 깎기가 이겼다 · 평균 %+.3f"
           % (len(rows), int((d > 0).sum()), d.mean()), font=_font(13), fill=(20, 20, 20))
    im.save(os.path.join(OUT, "대조.png"))
    print("  -> out/대조.png · out/대조.json")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "자체검사":
        selfcheck()
    else:
        main()
