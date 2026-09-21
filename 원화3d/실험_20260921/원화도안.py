# -*- coding: utf-8 -*-
"""**진짜 원화 한 벌에서 도안을 뽑는다** — 처음으로 (2026-09-21).

    python 원화도안.py 검사
    python 원화도안.py 짓기 [이름]   -> out/원화도안/<이름>/{앞,옆,뒤}/ · envelope.json · buildspec.json
    python 원화도안.py 판정          -> out/기록/원화도안_<때>.json
    python 원화도안.py 그림          -> out/원화도안_<이름>.png

README 의 오랜 미결 하나 — **「실제 원화 한 판에서 도안 쓰기 · 아직 한 번도 안 했다」.**
09-21 에 앞단이 갖춰졌다: 배경이 빠진 캐릭터 전용 판 10 장(`누끼`) · 선 채널의 정답표 ·
추출기가 오목 크리스를 0.87 찾는다는 측정. 이제 **스킬의 설계된 길을 끝까지 걸어 본다.**

    누끼 흰바탕 3 판 → art3d.py (판 · 가림순서 · 목)
                     → envelope.py (외형 · z 두 값은 사람이 준다)
                     → buildspec.py (부품표 · poly · 대칭 · px→world) = **도안.json 의 조상**

**문턱을 돌리기 전에 적는다.**

    Q1  `buildspec.json` 이 세 판으로 만들어진다 (배관)
    Q2  우리 스키마 30 칸 중 **10 칸 이상**이 자동으로 채워진다
    Q3  **px→world 맞춤 오차 중앙 < 0.15** — 스킬 자신의 문턱을 빌린다
        (`art-to-3d-maps`: 「15% 위면 외형과 추출 그림이 서로 다른 것을 재고 있다」)

**자를 새로 안 만든다.** Q3 은 빌린 것이고 Q2 는 세기다.
z 두 값(0.0 · 1.0)은 **사람이 주는 절대값**이다 — 전신 시트라 온몸이 0~1 이다.
"""
import json
import os
import subprocess
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np

sys.path.insert(0, r"G:\art2real\원화3d\실험_20260921")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260920")
sys.path.insert(0, r"G:\art2real\원화3d\실험_20260919")
import 선읽기 as LR
HERE, OUT = LR.HERE, LR.OUT
도구디 = r"G:\art2real\원화3d\도안\도구"
누끼디 = os.path.join(HERE, "out", "누끼")
DST = os.path.join(HERE, "out", "원화도안")
스키마 = r"G:\art2real\원화3d\도안\궤짝.json"
S = 512
Q2칸, Q3오차 = 10, 0.15
기본이름 = "오메가몬"
뷰맵 = (("front", "앞"), ("side", "옆"), ("back", "뒤"))


def 외형만들기(마스크, out, rows=15):
    """**누끼 마스크에서 외형을 만든다.** `envelope.py` 를 안 쓴다 — 돌려 보니 그건 투구 클로즈업용이라
    눈을 씨앗으로 위아래를 따라가다 **전신의 37% 에서 멈춘다**(오메가몬 앞: y 73~243 을 잡았는데
    실제는 45~968). 그 외형을 쓰면 부품의 「외형 밖 몫」 중앙이 1.000 이 된다.

    형식은 `envelope.py` 와 같다 — `rows = [[z, 반폭], …]` · 반폭은 **전고를 1 로 본 세계 단위**.
    가로로 길게 뻗은 안내선이 알파에 들어 있어 **제일 큰 연결 성분만** 쓴다."""
    from scipy import ndimage
    lab, n = ndimage.label(마스크)
    if n > 1:
        마스크 = lab == (1 + np.argmax(np.bincount(lab.ravel())[1:]))
    ys = np.where(마스크.any(1))[0]
    y0, y1 = int(ys.min()), int(ys.max())
    h = max(y1 - y0, 1)
    cx = float(np.mean([np.where(마스크[y])[0].mean() for y in range(y0, y1 + 1) if 마스크[y].any()]))
    R = []
    for i in range(rows):
        z = i / (rows - 1)
        y = int(round(y1 - z * h))
        xs = np.where(마스크[np.clip(y, y0, y1)])[0]
        hw = (float(np.abs(xs - cx).max()) / h) if len(xs) else 0.0
        R.append([round(z, 4), round(hw, 4)])
    e = {"src": "measured(누끼 마스크 · 제일 큰 연결성분)",
         "px": {"y_top": y0, "y_bot": y1, "center_x": round(cx, 1),
                "world_per_px": round(1.0 / h, 6), "scale": int(마스크.shape[1])},
         "rows": R}
    json.dump(e, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return e


def 돌려(args, 초=1800):
    r = subprocess.run([sys.executable] + args, capture_output=True, timeout=초,
                       cwd=도구디, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def 짓기(이름=기본이름):
    d = os.path.join(DST, 이름)
    os.makedirs(d, exist_ok=True)
    로그 = {"이름": 이름, "때": time.strftime("%Y%m%d_%H%M"), "단계": {}}
    폴더 = {}
    for v, 한 in 뷰맵:
        src = os.path.join(누끼디, "%s_%s" % (이름, v), "흰바탕.png")
        if not os.path.exists(src):
            로그["단계"]["art3d_" + v] = {"짐": "누끼가 없다 %s" % src}
            continue
        o = os.path.join(d, 한)
        os.makedirs(o, exist_ok=True)
        t0 = time.time()
        rc, out = 돌려([os.path.join(도구디, "art3d.py"), src, "--out", o, "--scale", str(S)])
        j = os.path.join(o, "art3d.json")
        m = json.load(open(j, encoding="utf-8"))["metrics"] if os.path.exists(j) else {}
        로그["단계"]["art3d_" + v] = {"rc": rc, "초": round(time.time() - t0, 1), "지표": m}
        폴더[v] = o
        print("  art3d %-6s rc=%d · %s" % (v, rc, json.dumps(m, ensure_ascii=False)), flush=True)
        # 외형 — 같은 그림에서 뽑는다 (스킬의 규칙)
        ej = os.path.join(d, "envelope_%s.json" % v)
        # **art3d 와 같은 화소 공간에서 만든다.** 부품 좌표는 `--scale S` 로 줄인 그림의 화소인데
        # 외형을 원본(1024) 화소로 만들면 중심 x 가 530 대 512 로 어긋나 **모든 부품이 외형 밖**이 된다
        # (첫 판이 그랬다 — 외형 밖 몫 중앙 1.000).
        import cv2
        from PIL import Image as _I
        mk = np.asarray(_I.open(os.path.join(누끼디, "%s_%s" % (이름, v), "마스크.png")).convert("L"))
        s2 = S / max(mk.shape)
        if s2 < 1.0:
            mk = cv2.resize(mk, (int(round(mk.shape[1] * s2)), int(round(mk.shape[0] * s2))),
                            interpolation=cv2.INTER_AREA)
        e = 외형만들기(mk > 127, ej)
        로그["단계"]["envelope_" + v] = {"방법": "누끼 마스크", "px": e["px"], "행": len(e["rows"])}
        print("    외형 %-6s y %d..%d · 중심x %.0f · 반폭 최대 %.3f"
              % (v, e["px"]["y_top"], e["px"]["y_bot"], e["px"]["center_x"],
                 max(r[1] for r in e["rows"])), flush=True)
    # 도안 — 정면 폴더가 뿌리, 옆 · 뒤는 --view 로
    if "front" in 폴더:
        args = [os.path.join(도구디, "buildspec.py"), 폴더["front"], "--name", 이름,
                "--envelope", os.path.join(d, "envelope_front.json")]
        if "side" in 폴더:
            e = os.path.join(d, "envelope_side.json")
            args += ["--view", "side=%s%s" % (폴더["side"], ("," + e) if os.path.exists(e) else "")]
        if "back" in 폴더:
            args += ["--view", "back=%s" % 폴더["back"]]
        t0 = time.time()
        rc, out = 돌려(args)
        bs = os.path.join(폴더["front"], "buildspec.json")
        로그["단계"]["buildspec"] = {"rc": rc, "초": round(time.time() - t0, 1),
                                   "있나": os.path.exists(bs), "말": out.strip()[-600:]}
        print("  buildspec rc=%d · %s" % (rc, "OK" if os.path.exists(bs) else out.strip()[-300:]), flush=True)
        if os.path.exists(bs):
            import shutil
            shutil.copy(bs, os.path.join(d, "buildspec.json"))
    p = os.path.join(OUT, "원화도안_%s_%s.json" % (이름, 로그["때"]))
    json.dump(로그, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ->", p)
    return 로그


def 칸세기(이름=기본이름):
    """우리 스키마 30 칸 중 자동으로 채워진 것."""
    want = list(json.load(open(스키마, encoding="utf-8")))
    p = os.path.join(DST, 이름, "buildspec.json")
    got = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    채 = {}
    for k in want:
        v = got.get(k)
        채[k] = bool(v) and not (isinstance(v, (list, dict)) and len(v) == 0)
    더 = [k for k in got if k not in want]
    return 채, 더, got


def verdict(이름=기본이름):
    채, 더, got = 칸세기(이름)
    p = os.path.join(DST, 이름, "buildspec.json")
    px = (got.get("px_to_world") or {})
    오차 = px.get("median_rel_error")
    v = {"판": "원화도안 v1 · 누끼 3 판 -> art3d -> envelope -> buildspec (2026-09-21)",
         "이름": 이름, "때": time.strftime("%Y%m%d_%H%M"),
         "Q1": {"문턱": "buildspec.json 이 만들어진다", "통과": os.path.exists(p)},
         "Q2": {"문턱": "스키마 30 칸 중 %d 칸 이상 자동" % Q2칸,
                "채운수": sum(채.values()), "전체": len(채),
                "채운칸": [k for k, x in 채.items() if x],
                "빈칸": [k for k, x in 채.items() if not x],
                "통과": bool(sum(채.values()) >= Q2칸)},
         "Q3": {"문턱": "px->world 오차 중앙 < %g (스킬에서 빌림)" % Q3오차, "값": 오차,
                "통과": bool(오차 is not None and 오차 < Q3오차)},
         "buildspec 에만 있는 칸": 더,
         "부품수": len(got.get("parts") or []),
         "판별부품수": {k: len(x) for k, x in (got.get("parts_by_view") or {}).items()},
         "대칭": {k: (len(x) if isinstance(x, list) else x)
                 for k, x in (got.get("symmetry") or {}).items()}}
    q = os.path.join(OUT, "원화도안판정_%s_%s.json" % (이름, v["때"]))
    json.dump(v, open(q, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  Q1 %s · Q2 %d/%d %s · Q3 %s %s"
          % ("통과" if v["Q1"]["통과"] else "짐", v["Q2"]["채운수"], v["Q2"]["전체"],
             "통과" if v["Q2"]["통과"] else "짐", 오차, "통과" if v["Q3"]["통과"] else "짐"))
    print("\n  채운 칸 (%d): %s" % (v["Q2"]["채운수"], ", ".join(v["Q2"]["채운칸"])))
    print("\n  빈 칸 (%d): %s" % (len(v["Q2"]["빈칸"]), ", ".join(v["Q2"]["빈칸"])))
    print("\n  부품 %d · 판별 %s · 대칭 %s" % (v["부품수"], v["판별부품수"], v["대칭"]))
    print("\n  ->", q)
    return v


def 그림(이름=기본이름):
    from PIL import Image
    d = os.path.join(DST, 이름)
    R, cols = [], []
    ts = []
    for v, 한 in 뷰맵:
        src = os.path.join(누끼디, "%s_%s" % (이름, v), "흰바탕.png")
        ts.append(np.asarray(Image.open(src).convert("RGB").resize((S, S))) if os.path.exists(src)
                  else np.full((S, S, 3), 240, np.uint8))
        cols.append("%s 누끼" % 한)
        for f, c in (("regions.png", "판"), ("order.png", "가림순서"), ("necks.png", "목")):
            p = os.path.join(d, 한, f)
            ts.append(np.asarray(Image.open(p).convert("RGB")) if os.path.exists(p)
                      else np.full((S, S, 3), 240, np.uint8))
            cols.append("%s %s" % (한, c))
    n = len(ts) // 3
    R = [("%s" % 한, ts[i * n:(i + 1) * n]) for i, (v, 한) in enumerate(뷰맵)]
    LR.DC.grid(R, tuple(cols[:n]), "진짜 원화에서 도안 — %s (배경 뺀 판 3 장)" % 이름,
               "왼쪽부터 누끼 · 추출한 판 · 가림 순서(밝을수록 앞) · 목(하위 부품 경계)",
               os.path.join(HERE, "out", "원화도안_%s.png" % 이름), S=300)


def selfcheck():
    assert os.path.exists(스키마), 스키마
    want = list(json.load(open(스키마, encoding="utf-8")))
    assert len(want) == 30, len(want)
    for v, 한 in 뷰맵:
        assert os.path.exists(os.path.join(누끼디, "%s_%s" % (기본이름, v), "흰바탕.png")), v
    for f in ("art3d.py", "envelope.py", "buildspec.py"):
        assert os.path.exists(os.path.join(도구디, f)), f
    print("  자가검사 통과 — 스키마 %d 칸 · 누끼 3 판 · 도구 3 개" % len(want))


if __name__ == "__main__":
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass
    a = sys.argv[1] if len(sys.argv) > 1 else "검사"
    n = sys.argv[2] if len(sys.argv) > 2 else 기본이름
    {"검사": selfcheck, "짓기": lambda: 짓기(n), "판정": lambda: verdict(n),
     "그림": lambda: 그림(n)}[a]()
