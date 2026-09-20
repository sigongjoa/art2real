"""추출 결과를 **설계도(build spec)** 로 묶는다 — 조립 스크립트가 읽을 유일한 입력.

문제: 2D 에서 데이터를 뽑아놓고 **조립할 문서가 없으면** 모델링 스크립트에 숫자를
손으로 타이핑하게 된다. 그러면 (a) 추출값과 스크립트가 갈라지고 (b) 눈으로 고치기
시작하며 (c) 무엇이 실측이고 무엇이 지어낸 값인지 아무도 모른다.
실제로 그렇게 여섯 번 고쳐 여섯 번 틀렸다.

**규칙: 조립 스크립트는 `buildspec.json` 만 읽는다. 상수를 스크립트에 적지 않는다.**

    py -3.11 buildspec.py <art3d출력폴더> --name helm \\
        [--envelope envelope.json] [--depth side_profile.json] [--pdf 설계도.pdf]

내보내는 것:
    buildspec.json   기계가 읽는 설계도 (부품표 + 외형 + 조립 + 신뢰도)
    blueprint.pdf    사람이 읽는 설계도 (치수도 + 부품표 + 조립 트리 + 판정란)

모든 값에 **출처(src)** 를 단다: measured(참조에서 잼) / derived(잰 값에서 계산)
/ guessed(지어냄). LESSON 42 — 신뢰도는 값과 같이 다녀야 하고, 그래야 하류가 거른다.
"""
import argparse
import datetime
import json
import pathlib
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

TYPST = shutil.which("typst") or (
    r"C:\Users\zesky\AppData\Local\Microsoft\WinGet\Packages"
    r"\Typst.Typst_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\typst-x86_64-pc-windows-msvc\typst.exe")

DATUM = {
    "unit": "총높이 = 1.0",
    "origin": "발바닥 z=0 · 몸 중심선 x=0",
    "axes": "+x 화면 오른쪽(캐릭터의 왼쪽) · -y 앞 · +z 위",
    "note": "미러는 원점 (0,0,0) 기준. rotation_euler 는 쓰지 않는다(회전은 정점에 굽는다).",
}
TONE2MAT = {"검정": "dark", "금색": "gold", "청회": "steel", "흰색": "white"}


def classify(p, env_rows):
    """부품 **종류**를 측정값에서 정한다. 전부 같은 원시형으로 만들면 뭉개진다.

      blade   길쭉하고 외형 밖으로 뻗는다        -> 테이퍼진 날 (뿔)
      recess  어둡고 안쪽에 갇혀 있다            -> 파인 구멍 (눈·언더아머)
      band    넓고 납작하며 중심을 걸친다        -> 띠 (목띠·차양)
      plate   나머지                             -> 갑판
    """
    pts = [q for pl in p.get("poly", []) or [] for q in pl]
    if not pts:
        return "plate", {}
    xs = [q[0] for q in pts]; zs = [q[1] for q in pts]
    w, h = max(xs) - min(xs), max(zs) - min(zs)
    area_px = p["px"]["area"]
    diag = (w * w + h * h) ** 0.5
    elong = max(w, h) / max(min(w, h), 1e-6)
    # 외형 밖으로 나가나 (뿔은 실루엣을 넘는다)
    out = 0.0
    if env_rows:
        for x, z in pts:
            rx = None
            for a, b in zip(env_rows, env_rows[1:]):
                if a[0] <= z <= b[0]:
                    t = (z - a[0]) / max(1e-9, b[0] - a[0])
                    rx = a[1] + (b[1] - a[1]) * t
                    break
            if rx is not None and abs(x) > rx * 1.02:
                out += 1
        out /= len(pts)
    feat = {"w": round(w, 4), "h": round(h, 4), "elongation": round(elong, 2),
            "outside_envelope": round(out, 2)}
    if elong >= 2.6 and out >= 0.25:
        return "blade", feat
    if p["material"] == "dark" and out < 0.05:
        return "recess", feat
    if h > 0 and w / max(h, 1e-6) >= 2.4 and p["screen_side"] == "C":
        return "band", feat
    return "plate", feat


def side_of(poly_list, tol=0.004):
    """부품이 화면 좌/우/중앙 어디에 있나. 미러 여부를 판단하는 근거."""
    xs = [q[0] for pl in poly_list for q in pl]
    if not xs:
        return "?"
    lo, hi = min(xs), max(xs)
    if lo < -tol and hi > tol:
        return "C"          # 중심선을 걸친다 -> 대칭 부품
    return "R" if lo >= -tol else "L"


def pair_mirrors(parts, tol_area=0.30, tol_z=0.012, tol_x=0.012):
    """좌우 짝을 찾는다. 짝이 있으면 **한쪽만 만들고 Mirror** 로 넘긴다.
    짝이 없는 비대칭 부품은 따로 만들어야 한다 (오메가몬 어깨 방패가 그런 것)."""
    R = [p for p in parts if p["screen_side"] == "R"]
    L = [p for p in parts if p["screen_side"] == "L"]
    used = set()
    for r in R:
        rx = [abs(q[0]) for pl in r["poly"] for q in pl]
        if not rx or not r.get("z"):
            continue
        best, bd = None, 1e9
        for l in L:
            if l["id"] in used or l["material"] != r["material"] or not l.get("z"):
                continue
            lx = [abs(q[0]) for pl in l["poly"] for q in pl]
            if not lx:
                continue
            da = abs(l["px"]["area"] - r["px"]["area"]) / max(r["px"]["area"], 1)
            dz = abs(l["z"][0] - r["z"][0]) + abs(l["z"][1] - r["z"][1])
            dx = abs(sum(lx) / len(lx) - sum(rx) / len(rx))
            if da < tol_area and dz < tol_z and dx < tol_x and da + dz + dx < bd:
                best, bd = l, da + dz + dx
        if best is not None:
            used.add(best["id"])
            r["mirror"] = True
            r["mirror_of"] = best["id"]
            best["mirror"] = "dropped(미러로 대체)"
    for p in parts:
        if p["screen_side"] in ("L", "R") and p.get("mirror") in (False, None):
            p["asymmetry"] = "unique(짝 없음 — 따로 만들어야 한다)"
    return sum(1 for p in parts if p.get("mirror") is True)


def okt(good, txt):
    c = "#1a7f37" if good else "#c4322d"
    return f'text(fill: rgb("{c}"), weight: "bold")[{txt}]'


def tone(rgb):
    r, g, b = rgb
    if sum(rgb) / 3 < 110:
        return "검정"
    if r - b > 40:
        return "금색"
    if b - r > 12:
        return "청회"
    return "흰색"


def fit_by_landmarks(rows_px, env_rows):
    """**특징점 두 개로 맞춘다** — 최소제곱 스윕보다 이게 맞다.

    양쪽에 다 있는 특징 둘을 쓴다:
      ① 실루엣 **꼭대기 행**            <-> 외형의 z 최대
      ② 실루엣이 **제일 넓은 행**       <-> 외형에서 반폭이 최대인 z
    두 점이면 스케일과 오프셋이 결정된다. 창 전체를 훑는 최소제곱은 아래 어깨에 끌려
    **머리를 크롭보다 크게 잡아** 비교가 통째로 무의미해졌다(원화 반폭이 모든 z 에서
    크롭 폭의 절반으로 나왔다 = 창을 꽉 채움).
    """
    ys = sorted(int(y) for y in rows_px)
    def half(y):
        v = rows_px.get(str(y)) or rows_px.get(y)
        return (v[1] - v[0]) / 2 if v else 0.0
    y_top = ys[0]
    y_wide = max(ys, key=half)
    z_top = max(r[0] for r in env_rows)
    z_wide = max(env_rows, key=lambda r: r[1])[0]
    if y_wide <= y_top or abs(z_top - z_wide) < 1e-6:
        return None
    k = (z_top - z_wide) / (y_wide - y_top)
    # 폭으로 검증 — 두 방식이 얼마나 어긋나는지 숫자로 남긴다
    hw_ref = half(y_wide) * k
    hw_env = max(r[1] for r in env_rows)
    return {"y_top_px": y_top, "y_bot_px": int(y_top + (z_top - min(r[0] for r in env_rows)) / k),
            "world_per_px": round(k, 6), "z_top": z_top,
            "z_bot": min(r[0] for r in env_rows),
            "width_check": {"ref_halfwidth": round(hw_ref, 4),
                            "envelope_halfwidth": round(hw_env, 4),
                            "rel_error": round(abs(hw_ref - hw_env) / max(hw_env, 1e-6), 3)},
            "median_rel_error": round(abs(hw_ref - hw_env) / max(hw_env, 1e-6), 4),
            "src": "derived(특징점 2개: 꼭대기 행 / 최대폭 행)"}


def fit_px_to_world(rows_px, env_rows):
    """**px -> 월드 스케일을 손으로 안 적고 맞춘다.**

    설계도의 외형(z별 반폭)과 추출 이미지의 행별 반폭이 같은 물건이므로,
    (윗행 -> z_max, 아랫행 -> z_min) 두 점을 최소제곱으로 찾는다.
    앵커를 사람이 타이핑하면 그 순간 또 손으로 흘러간다 — 그래서 자동으로 맞춘다.
    """
    ys = sorted(int(y) for y in rows_px)
    z1 = max(r[0] for r in env_rows)
    z0 = min(r[0] for r in env_rows)
    best = None
    lo, hi = ys[0], ys[-1]
    for ytop in range(lo, hi - 40, 2):
        for ybot in range(ytop + 40, hi + 1, 2):
            k = (z1 - z0) / (ybot - ytop)          # 월드/px
            errs = []
            for z, hw in env_rows:
                y = int(round(ytop + (z1 - z) / k))
                v = rows_px.get(str(y)) or rows_px.get(y)
                if v is None:
                    errs = None; break
                errs.append(abs((v[1] - v[0]) / 2 * k - hw) / max(hw, 1e-6))
            if not errs:
                continue
            # **중앙값 상대오차.** 제곱합을 쓰면 아래쪽 어깨 한두 행이 맞춤을 통째로
            # 끌고 간다 (실측: 이미지 전체가 헬멧 높이에 매핑됐다). 중앙값은 이상치를 무시한다
            e = sorted(errs)[len(errs) // 2]
            if best is None or e < best[0]:
                best = (e, ytop, ybot, k)
    e, ytop, ybot, k = best
    rms = e
    return {"y_top_px": ytop, "y_bot_px": ybot, "world_per_px": round(k, 6),
            "z_top": z1, "z_bot": z0, "median_rel_error": round(rms, 4),
            "src": "derived(외형에 최소제곱 맞춤)"}


def draw_parts(spec, path, W=900, H=760):
    """부품 상세 — 윤곽을 월드 좌표로 겹쳐 그린다. 재질로 색을 나눈다."""
    env = spec["envelope"]["halfwidth"]["rows"]
    if not env:
        return None
    z0 = min(r[0] for r in env); z1 = max(r[0] for r in env)
    hwmax = max(r[1] for r in env)
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    try:
        F = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 12)
    except OSError:
        F = ImageFont.load_default()
    m = 46
    sc = min((W - 2 * m) / (2.4 * hwmax), (H - 2 * m) / (z1 - z0)) * 0.95
    cx, top = W / 2, m
    COL = {"white": (60, 60, 66), "steel": (60, 110, 190), "gold": (190, 150, 40),
           "dark": (200, 60, 50)}

    def P(x, z):
        return (cx + x * sc, top + (z1 - z) * sc)
    # 외형
    L = [P(-r[1], r[0]) for r in env]; R = [P(r[1], r[0]) for r in env]
    d.line(L + R[::-1] + [L[0]], fill=(200, 200, 208), width=3)
    for p in spec["parts"]:
        c = COL.get(p["material"], (120, 120, 120))
        for poly in p.get("poly", []):
            if len(poly) >= 3:
                d.line([P(*q) for q in poly] + [P(*poly[0])], fill=c, width=1)
    for i, (k, c) in enumerate(COL.items()):
        d.rectangle([m + i * 96, H - 26, m + i * 96 + 14, H - 14], fill=c)
        d.text((m + i * 96 + 20, H - 28), k, (40, 40, 46), F)
    d.text((m, 8), "부품 윤곽 (월드 좌표) — 회색은 외형", (40, 40, 46), F)
    im.save(path)
    return path


def draw_three_views(spec, path, W=1180, H=680):
    """**삼면도** — 정면·측면·배면의 부품 윤곽을 같은 z 축으로 나란히."""
    env = spec["envelope"]["halfwidth"]["rows"]
    if not env:
        return None
    z0 = min(r[0] for r in env); z1 = max(r[0] for r in env)
    sets = [("정면", spec["parts"])]
    for nm in ("side", "back"):
        if spec.get("parts_by_view", {}).get(nm):
            sets.append(({"side": "측면", "back": "배면"}[nm], spec["parts_by_view"][nm]))
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    try:
        F = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 15)
    except OSError:
        F = ImageFont.load_default()
    COL = {"white": (60, 60, 66), "steel": (60, 110, 190), "gold": (190, 150, 40),
           "dark": (200, 60, 50)}
    m = 40
    pw = (W - m * 2) // max(1, len(sets))
    hwmax = max(r[1] for r in env)
    sc = min(pw / (2.6 * hwmax), (H - 2 * m) / (z1 - z0)) * 0.92
    for i, (title, ps) in enumerate(sets):
        cx = m + pw * i + pw / 2
        d.text((cx - 22, 10), title, (20, 20, 22), F)
        if i == 0:
            L = [(cx - r[1] * sc, m + (z1 - r[0]) * sc) for r in env]
            R = [(cx + r[1] * sc, m + (z1 - r[0]) * sc) for r in env]
            d.line(L + R[::-1] + [L[0]], fill=(205, 205, 212), width=3)
        for p in ps:
            c = COL.get(p.get("material"), (120, 120, 120))
            if p.get("mirror") == "dropped(미러로 대체)":
                continue                        # 미러로 대체된 쪽은 안 그린다
            for poly in p.get("poly", []) or []:
                if len(poly) >= 3:
                    pts = [(cx + q[0] * sc, m + (z1 - q[1]) * sc) for q in poly]
                    d.line(pts + [pts[0]], fill=c, width=1)
        if i:
            d.line([(m + pw * i - 6, m - 10), (m + pw * i - 6, H - m)],
                   fill=(230, 230, 236))
    for j, (k, c) in enumerate(COL.items()):
        d.rectangle([m + j * 100, H - 26, m + j * 100 + 14, H - 14], fill=c)
        d.text((m + j * 100 + 20, H - 30), k, (40, 40, 46), F)
    im.save(path)
    return path


def draw_blueprint(spec, path, W=940, H=620):
    """치수도 한 장 — 정면 외형(반폭)과 측면 깊이를 z 축 공유로 나란히 그린다."""
    env = spec["envelope"]
    hw = env.get("halfwidth", {}).get("rows", [])
    dp = env.get("depth", {}).get("rows", [])
    if not hw:
        return None
    zs = [r[0] for r in hw]
    z0, z1 = min(zs), max(zs)
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    try:
        F = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 13)
        FB = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 15)
    except OSError:
        F = FB = ImageFont.load_default()
    m, gap = 56, 40
    pw = (W - m * 2 - gap) // 2
    ph = H - m * 2
    maxr = max(max(r[1] for r in hw), 1e-6)
    maxd = max((max(abs(r[1]), abs(r[2])) for r in dp), default=maxr)
    sc = min(pw / (2 * maxr), ph / (z1 - z0)) * 0.86
    scd = min(pw / (2 * maxd), ph / (z1 - z0)) * 0.86

    def Y(z):
        return m + ph - (z - z0) / (z1 - z0) * ph

    for k, (title, cx, s, rows, two) in enumerate((
            ("정면 — 반폭", m + pw // 2, sc, hw, False),
            ("측면 — 깊이(앞 -y / 뒤 +y)", m + pw + gap + pw // 2, scd, dp, True))):
        d.text((cx - 60, m - 30), title, (20, 20, 22), FB)
        d.line([(cx, m - 6), (cx, m + ph + 6)], fill=(150, 170, 255), width=1)
        if not rows:
            d.text((cx - 50, m + ph // 2), "데이터 없음", (200, 60, 60), F)
            continue
        L = [(cx - (r[1] if not two else -r[1]) * s, Y(r[0])) for r in rows]
        R = [(cx + (r[1] if not two else r[2]) * s, Y(r[0])) for r in rows]
        if two:
            L = [(cx + r[1] * s, Y(r[0])) for r in rows]
            R = [(cx + r[2] * s, Y(r[0])) for r in rows]
        d.line(L, fill=(20, 20, 22), width=2)
        d.line(R, fill=(20, 20, 22), width=2)
        d.line([L[0], R[0]], fill=(20, 20, 22), width=2)
        d.line([L[-1], R[-1]], fill=(20, 20, 22), width=2)
        step = max(1, len(rows) // 8)
        for i in range(0, len(rows), step):
            z = rows[i][0]
            y = Y(z)
            d.line([(m - 14, y), (cx + pw // 2, y)], fill=(230, 230, 235))
            d.text((6, y - 8), f"z {z:.3f}", (90, 90, 96), F)
            if two:
                d.text((R[i][0] + 5, y - 8),
                       f"{rows[i][2]-rows[i][1]:.3f}", (196, 60, 40), F)
            else:
                d.line([(L[i][0], y), (R[i][0], y)], fill=(196, 60, 40))
                d.text((R[i][0] + 5, y - 8), f"{rows[i][1]*2:.3f}", (196, 60, 40), F)
    d.text((m, H - 26), f"단위: {DATUM['unit']} · {DATUM['origin']}", (110, 110, 116), F)
    im.save(path)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", help="정면 추출 폴더")
    ap.add_argument("--view", action="append", default=[],
                    metavar="NAME=DIR[,ENVELOPE]",
                    help="추가 뷰. 예: side=art3d_side,envelope_side.json / back=art3d_back")
    ap.add_argument("--name", required=True, help="부품 묶음 이름 (helm, lower, ...)")
    ap.add_argument("--envelope", default=None, help="외형 json (halfwidth rows)")
    ap.add_argument("--depth", default=None, help="측면 깊이 json (side_profile)")
    ap.add_argument("--verify", default=None,
                    help="verify_iou.py 가 낸 iou.json — 기준 미달 부품은 조립에서 뺀다")
    ap.add_argument("--verify-min", type=float, default=0.7)
    ap.add_argument("--pdf", default=None)
    ap.add_argument("--refdir", default=None,
                    help="참조 원화가 있는 폴더 (PDF 에 원본을 같이 싣는다)")
    ap.add_argument("--anchor", nargs=2, type=int, default=None,
                    metavar=("Y_TOP", "Y_BOT"),
                    help="맞춤이 나쁠 때 px 앵커를 직접 준다 (z_top 행, z_bot 행)")
    a = ap.parse_args()
    d = pathlib.Path(a.dir).resolve()
    art = json.loads((d / "art3d.json").read_text(encoding="utf-8"))
    extra_views = []
    for v in a.view:
        nm, rest = v.split("=", 1)
        parts_ = rest.split(",")
        vd = pathlib.Path(parts_[0]).resolve()
        ve = parts_[1] if len(parts_) > 1 else a.envelope
        extra_views.append((nm, vd, ve))

    env = {"halfwidth": {"rows": [], "src": "none"},
           "depth": {"rows": [], "src": "none"}}
    env_px = None
    if a.envelope:
        e = json.loads(pathlib.Path(a.envelope).read_text(encoding="utf-8"))
        env["halfwidth"] = {"rows": e["rows"], "src": e.get("src", "measured")}
        env_px = e.get("px")     # 같은 이미지에서 뽑았으면 매핑이 여기 이미 있다
    if a.depth:
        s = json.loads(pathlib.Path(a.depth).read_text(encoding="utf-8"))
        rows = s["rows"]
        if rows and isinstance(rows[0], dict):
            env["depth"] = {"rows": [[r["z"], r["y_front"], r["y_back"]] for r in rows],
                            "src": s.get("src", "measured")}
        else:
            # **측면 외형(envelope.py 산출물)을 깊이로 쓴다.**
            # 깊이 행이 비면 `ry = rx` 로 떨어져 **순수 회전체**가 된다 — 중앙 볏처럼
            # x 로 얇고 y 로 긴 것이 가느다란 못이 되고 측면이 통째로 무너진다
            # (실측: z 0.918 에서 정면 반폭 0.0028 vs 측면 0.0290, 10.4배).
            # z 범위는 두 그림이 다르므로(0.866~0.919 vs 0.870~0.930) **비례로 맞춘다** —
            # 절대값으로 맞추면 머리 비율이 어긋난다(LESSON 117).
            fz = [r[0] for r in env["halfwidth"]["rows"]]
            sz = [r[0] for r in rows]
            f0, f1, s0, s1 = min(fz), max(fz), min(sz), max(sz)
            env["depth"] = {
                "rows": [[round(f0 + (z - s0) / max(1e-9, s1 - s0) * (f1 - f0), 4),
                          round(-h, 4), round(h, 4)] for z, h in rows],
                "src": f"measured({pathlib.Path(a.depth).name} 측면 반폭 · z 는 정면 범위로 비례 정규화)"}
            print(f"    측면 깊이 {len(rows)}행 · z {s0:.3f}~{s1:.3f} -> {f0:.3f}~{f1:.3f} "
                  f"· 깊이/폭 중앙값 "
                  f"{sorted(h / max(min(env['halfwidth']['rows'], key=lambda r: abs(r[0] - f0 - (z - s0) / max(1e-9, s1 - s0) * (f1 - f0)))[1], 1e-9) for z, h in rows)[len(rows) // 2]:.2f}")

    # px -> 월드 매핑을 외형에 맞춰 자동으로 찾는다
    fit = None
    if env["halfwidth"]["rows"] and art.get("silhouette_rows_px"):
        if env_px:
            # **맞출 필요가 없다.** 외형을 부품과 같은 이미지에서 뽑았으면 매핑이
            # 이미 확정돼 있다. 다시 맞추면 오차만 생긴다 (실측: 33% / 5091% / 74.8%).
            zt = max(r[0] for r in env["halfwidth"]["rows"])
            zb = min(r[0] for r in env["halfwidth"]["rows"])
            fit = {"y_top_px": env_px["y_top"], "y_bot_px": env_px["y_bot"],
                   "world_per_px": env_px["world_per_px"], "z_top": zt, "z_bot": zb,
                   "median_rel_error": 0.0,
                   "src": "given(외형과 같은 이미지에서 나옴 — 맞춤 없음)"}
        elif a.anchor:
            yt, yb = a.anchor
            z1 = max(r[0] for r in env["halfwidth"]["rows"])
            z0 = min(r[0] for r in env["halfwidth"]["rows"])
            fit = {"y_top_px": yt, "y_bot_px": yb,
                   "world_per_px": round((z1 - z0) / (yb - yt), 6),
                   "z_top": z1, "z_bot": z0, "median_rel_error": None,
                   "src": "given(사람이 지정)"}
        else:
            fit = (fit_by_landmarks(art["silhouette_rows_px"], env["halfwidth"]["rows"])
                   or fit_px_to_world(art["silhouette_rows_px"], env["halfwidth"]["rows"]))
        kk, ytop = fit["world_per_px"], fit["y_top_px"]
        cxg = (env_px or {}).get("center_x", art["center_x_px"])
        ztop = fit["z_top"]

        def W2(px, py):
            # **+0.5 는 픽셀 중심이다.** 무어 추적은 픽셀 *인덱스*를 내놓는데 픽셀
            # (i,j) 는 [j,j+1)x[i,i+1) 영역을 차지한다 — 인덱스를 그대로 꼭짓점으로
            # 쓰면 폴리곤이 좌상단 모서리에 놓여 부품 전체가 반 픽셀 밀린다.
            # 실측: 부품 36개 치우침 dx +0.60px / dy +0.59px, 위치와 무상관(순수 평행이동).
            return [round((px + 0.5 - cxg) * kk, 5),
                    round(ztop - (py + 0.5 - ytop) * kk, 5)]

    # 돌출은 아직 실측이 없다 — T-접합 순위를 진폭 하나로 펴서 준다.
    # **손으로 부품마다 타이핑하지 않기 위해** 진폭을 스펙 머리에 한 번만 둔다.
    ranks = [r["depth_score"] for r in art["regions"]] or [0]
    rlo, rhi = min(ranks), max(ranks)
    PROT = {"base": 0.004, "span": 0.010, "src": "guessed(진폭). 순위는 derived"}

    parts = []
    for r in art["regions"]:
        t = tone(r["rgb"])
        parts.append({
            "id": f'{a.name}_r{r["id"]}',
            "from": {"source": art["src"], "region": r["id"]},
            "material": TONE2MAT[t], "tone": t,
            "px": {"x": r["x"], "y": r["y"], "area": r["area"]},
            "depth_rank": r["depth_score"],
            "necks": r["necks"],
            "poly": [[W2(*q) for q in poly] for poly in r.get("poly_px", [])] if fit else [],
            "z": ([round(min(q[1] for pl in
                             [[W2(*q) for q in pp] for pp in r.get("poly_px", [])]
                             for q in pl), 4),
                   round(max(q[1] for pl in
                             [[W2(*q) for q in pp] for pp in r.get("poly_px", [])]
                             for q in pl), 4)]
                  if fit and r.get("poly_px") else None),
            "protrusion": round(PROT["base"] + PROT["span"] *
                                (r["depth_score"] - rlo) / max(1, rhi - rlo), 4),
            "mirror": False,
            "src": {"outline": "measured", "material": "measured",
                    "depth_rank": "derived(T-junction)",
                    "world_coords": fit["src"] if fit else "none",
                    "protrusion": PROT["src"]},
        })
    # **외형 z 범위 밖 부품은 이 묶음이 아니다.** 목·어깨가 그것이다. 두면 `_at` 이
    # 바닥 링으로 클램프해 전부 거기 뭉쳐 파편이 된다 (실측: 모델 아래가 통째로 부서짐).
    if env["halfwidth"]["rows"]:
        zlo = min(r[0] for r in env["halfwidth"]["rows"])
        zhi = max(r[0] for r in env["halfwidth"]["rows"])
        drop = [p for p in parts
                if p.get("z") and (p["z"][1] < zlo - 0.004 or p["z"][0] > zhi + 0.004)]
        for p in drop:
            parts.remove(p)
        if drop:
            print(f"    외형 z[{zlo:.3f},{zhi:.3f}] 밖 부품 {len(drop)}개 제외")

    for p in parts:
        p["screen_side"] = side_of(p["poly"])
    n_mirror = pair_mirrors(parts)
    parts.sort(key=lambda p: -p["px"]["area"])

    # ── 추가 뷰 (측면·배면). 같은 기준(datum)에 각자 외형으로 맞춘다
    views = {"front": {"source": art["src"], "parts": len(parts),
                       "px_to_world": fit, "metrics": art["metrics"]}}
    view_parts = {}
    for nm, vd, ve in extra_views:
        va = json.loads((vd / "art3d.json").read_text(encoding="utf-8"))
        vrows = []
        if ve:
            vrows = json.loads(pathlib.Path(ve).read_text(encoding="utf-8"))["rows"]
        vfit = (fit_px_to_world(va["silhouette_rows_px"], vrows)
                if vrows and va.get("silhouette_rows_px") else None)
        vp = []
        for r in va["regions"]:
            item = {"id": f"{a.name}_{nm}_r{r['id']}", "material": TONE2MAT[tone(r["rgb"])],
                    "px": {"area": r["area"], "x": r["x"], "y": r["y"]},
                    "depth_rank": r["depth_score"], "necks": r["necks"]}
            if vfit:
                kk2, yt2, cx2 = vfit["world_per_px"], vfit["y_top_px"], va["center_x_px"]
                zt2 = vfit["z_top"]
                item["poly"] = [[[round((q[0] - cx2) * kk2, 5),
                                  round(zt2 - (q[1] - yt2) * kk2, 5)] for q in pl]
                                for pl in r.get("poly_px", [])]
                zz = [q[1] for pl in item["poly"] for q in pl]
                item["z"] = [round(min(zz), 4), round(max(zz), 4)] if zz else None
            vp.append(item)
        vp.sort(key=lambda x: -x["px"]["area"])
        view_parts[nm] = vp
        views[nm] = {"source": va["src"], "parts": len(vp),
                     "px_to_world": vfit, "metrics": va["metrics"],
                     "envelope_src": ve or "none"}

    # ── 공정(ops) — **치수만으로는 못 만든다.** 어떤 조작으로 만드는지가 있어야 한다.
    # 규칙은 여기 한 번만 적고, 부품마다는 그 규칙에서 **파생**시킨다(손 타이핑 금지).
    CONV = {
        "quads_only": True,
        "mirror_origin": [0, 0, 0],
        "no_rotation_euler": "회전은 정점에 굽는다 (미러 오브젝트에 회전 금지)",
        "shade": "hard surface 는 flat. 판은 평면이고 경계에서만 꺾인다",
        "units": DATUM["unit"],
    }
    RECIPE = {
        "plate":  "윤곽을 부모 표면에 얹은 **평평한 갑판**. 테두리에서만 꺾인다",
        "blade":  "주축을 따라 **테이퍼진 날**. 끝으로 갈수록 얇아지고 뾰족해진다 (뿔)",
        "recess": "표면 **안쪽으로 파낸다**(protrusion 음수). 검은 면 — 눈·언더아머",
        "band":   "가로로 넓은 **띠**. 표면을 감싸며 얇게 얹힌다",
        "classify_rules": "elongation>=2.6 & 외형밖>=25% -> blade · dark & 안쪽 -> recess "
                          "· 가로/세로>=2.4 & 중심걸침 -> band · 나머지 plate",
        "modifier_rules": {
            "MIRROR": "symmetry.mirror=true 인 부품에만. use_mirror_merge=false",
            "SOLIDIFY": "**plate 에는 걸지 않는다.** plate 는 이미 앞뒤 껍질이 있어서 "
                        "두께를 또 주면 겹껍질이 된다",
            "SUBSURF": "**plate 에는 levels=0.** 작은 닫힌 껍질에 Subsurf 를 걸면 "
                       "공으로 굴러간다 — 첫 조립본이 통째로 물집이 된 원인",
        },
        "protrusion_model": PROT,
    }
    ENV_ROWS = env["halfwidth"]["rows"]
    for p in parts:
        p["make"], p["features"] = classify(p, ENV_ROWS)
        mods = []
        if p.get("mirror") is True:
            mods.append({"type": "MIRROR", "axis": "X", "use_mirror_merge": False})
        # plate 는 자체 두께가 있다 -> Solidify 없음, Subsurf 0 (LESSON: 물집의 원인)
        mods.append({"type": "SUBSURF", "levels": 0})
        p["ops"] = {
            "make": p["make"],
            "onto": f"{a.name}_envelope",
            "protrusion": p["protrusion"],
            "shade": "flat",
            "modifiers": mods,
            "skip": p.get("mirror") == "dropped(미러로 대체)",
        }
    order = ([p["id"] for p in parts if p["screen_side"] == "C"]
             + [p["id"] for p in parts if p["screen_side"] != "C"])

    # ── 부품별 검증 결과를 붙인다. **확인하고 붙이는 순서**를 파일이 강제하게.
    verify = {}
    if a.verify and pathlib.Path(a.verify).exists():
        for r in json.loads(pathlib.Path(a.verify).read_text(encoding="utf-8")):
            verify.setdefault(r["id"].rsplit("_", 1)[0]
                              if r["id"] not in {p["id"] for p in parts} else r["id"],
                              []).append(r)
        for p in parts:
            rs = verify.get(p["id"])
            if not rs:
                continue
            iou = min(r["iou"] for r in rs)
            p["verify"] = {"iou": iou, "pass": iou >= a.verify_min,
                           "pieces": len(rs),
                           "src": "measured(부품 단독 렌더 vs 원화 같은 창)"}
            if not p["verify"]["pass"]:
                p["ops"]["skip"] = True
                p["ops"]["skip_reason"] = f"부품 검증 IoU {iou:.3f} < {a.verify_min}"

    spec = {
        "schema": "art-to-3d/buildspec/2",
        "conventions": CONV,
        "recipes": RECIPE,
        "build_order": order,
        "checks": [
            {"name": "사각면 100%", "expr": "ngon_count == 0"},
            {"name": "정수리 높이", "expr": f"abs(bbox_z_max - {env['halfwidth']['rows'][-1][0] if env['halfwidth']['rows'] else 1.0}) < 0.01"},
            {"name": "미러 원점", "expr": "all mirrored objects at (0,0,0)"},
        ],
        "generated": datetime.date.today().isoformat(),
        "group": a.name,
        "datum": DATUM,
        "sources": [{"file": art["src"], "role": "판 분할", "size": art["size"]}],
        "envelope": env,
        "px_to_world": fit,
        "protrusion_model": PROT,
        "metrics": art["metrics"],
        "views": views,
        "parts": parts,
        "parts_by_view": view_parts,
        "symmetry": {"mirror_pairs": n_mirror,
                     "unique": sum(1 for p in parts if p.get("asymmetry")),
                     "center": sum(1 for p in parts if p["screen_side"] == "C"),
                     "note": "짝이 있으면 한쪽만 만들고 Mirror. unique 는 따로 만든다"},
        "assembly": [{"parent": a.name, "child": p["id"], "relation": "표면에 얹음"}
                     for p in parts if p.get("verify", {}).get("pass", True)],
        "rule": "조립 스크립트는 이 파일만 읽는다. 상수를 스크립트에 적지 않는다.",
    }
    if verify:
        ok = sum(1 for p in parts if p.get("verify", {}).get("pass"))
        nov = sum(1 for p in parts if not p.get("verify"))
        spec["verification"] = {
            "metric": "silhouette IoU (부품 하나를 자기 bbox 창으로 렌더 vs 원화 같은 창)",
            "min": a.verify_min, "checked": len(parts) - nov, "passed": ok,
            "not_checked": nov,
            "rule": "**통과한 부품만 조립한다.** 붙여놓고 전체 IoU 를 보면 어느 "
                    "부품이 틀렸는지 알 수 없다",
        }
        print(f"부품 검증: 통과 {ok} / 검사 {len(parts) - nov} "
              f"(미검사 {nov}) · 조립 대상 {len(spec['assembly'])}개")
    # ── **비교 창을 설계도가 정한다.** 외형(투구 돔)에만 맞추면 뿔이 잘려서
    #    모델이 창보다 커지고 비교가 무의미해진다(실측: 모델 반폭 0.048 vs 창 0.032).
    #    GT 실루엣의 bbox 로 한 번 정하고 **모든 모델을 같은 창에서** 잰다.
    lp = pathlib.Path(a.dir) / "labels.npy"
    labels = np.load(lp) if lp.exists() else None
    keep_r = {p["from"]["region"] for p in parts if not p["ops"].get("skip")}
    occm = np.isin(labels, list(keep_r)) if labels is not None else None
    if occm is not None and occm.any():
        oy, ox = np.where(occm)
        wx0 = (ox.min() + 0.5 - cxg) * kk; wx1 = (ox.max() + 0.5 - cxg) * kk
        wz1 = ztop - (oy.min() + 0.5 - ytop) * kk
        wz0 = ztop - (oy.max() + 0.5 - ytop) * kk
        spec["view_front"] = {
            "cx": round((wx0 + wx1) / 2, 5), "cz": round((wz0 + wz1) / 2, 5),
            "span": round(max(wx1 - wx0, wz1 - wz0) * 1.06, 5),
            "src": "derived(GT 실루엣 bbox — 모델과 무관하게 한 번 정한다)"}
    fit["center_x_px"] = cxg      # **하류가 중심을 다시 추측하지 않게 남긴다**
    spec["px_to_world"] = fit
    (d / "buildspec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1),
                                      encoding="utf-8")

    # typst 의 --root 가 정면 폴더라 **다른 뷰의 그림을 여기로 복사**해야 참조된다
    assets = {}
    src_imgs = {"front": pathlib.Path(a.src_front) if getattr(a, "src_front", None) else None}
    for nm, vd, _ in extra_views:
        for what in ("regions", "order", "necks", "recon",
                     "depth", "normal", "shade"):
            f = vd / f"{what}.png"
            if f.exists():
                t = d / f"v_{nm}_{what}.png"
                shutil.copyfile(f, t)
                assets[f"{nm}_{what}"] = t.name
    for nm, vd, _ in [("front", d, None)] + extra_views:
        j = json.loads((vd / "art3d.json").read_text(encoding="utf-8"))
        cand = pathlib.Path(a.refdir or ".") / j["src"] if a.refdir else None
        if cand and cand.exists():
            t = d / f"ref_{nm}.png"
            shutil.copyfile(cand, t)
            assets[f"{nm}_ref"] = t.name

    bp = draw_blueprint(spec, d / "blueprint_dims.png")
    pp = draw_parts(spec, d / "blueprint_parts.png")
    tv = draw_three_views(spec, d / "blueprint_views.png")
    pdf = pathlib.Path(a.pdf) if a.pdf else d / "blueprint.pdf"

    if fit and fit.get("median_rel_error") is not None:
        me = fit["median_rel_error"]
        good = me <= 0.15
        fit_err = "#" + okt(good, f"중앙값 상대오차 {me:.0%}") + ("" if good else
                                   r" — 외형과 추출 이미지의 실루엣이 다른 것을 재고 있다는 뜻이다. "
                                   r"`--anchor Y_TOP Y_BOT` 로 직접 주거나, 외형을 같은 이미지에서 다시 뽑아라")
    else:
        fit_err = "—"
    fit_txt = (f'y {fit["y_top_px"]} → z {fit["z_top"]} · y {fit["y_bot_px"]} → z {fit["z_bot"]}'
               if fit else "없음")

    cnt = {}
    for p in parts:
        for k, v in p["src"].items():
            cnt[v] = cnt.get(v, 0) + 1
    conf = ", ".join(f"{k} {v}" for k, v in sorted(cnt.items()))
    rows = parts[:24]
    def _row(p):
        z = f"{p['z'][0]:.3f}-{p['z'][1]:.3f}" if p.get("z") else "-"
        return ("[" + p["id"] + "], [" + p["material"] + "], ["
                + format(p["px"]["area"], ",") + "], [" + z + "], ["
                + str(p["protrusion"]) + "], [" + f"{p['depth_rank']:+d}" + "], ["
                + str(len(p["necks"])) + "],\n")

    tbl = "".join(_row(p) for p in rows)

    def _img(key, cap, w="100%"):
        return (f'figure(image("{assets[key]}", width: {w}), caption: [{cap}])'
                if key in assets else f'[#text(fill: red)[{cap} 없음]]')

    names = {"front": "정면", "side": "측면", "back": "배면"}
    NL = chr(10)
    refs = [k for k in ("front", "side", "back") if f"{k}_ref" in assets]
    if refs:
        cols = ", ".join(["1fr"] * len(refs))
        body = ("," + NL + "  ").join(_img(f"{k}_ref", names[k]) for k in refs)
        ref_fig = "#grid(columns: (" + cols + "), gutter: 6pt," + NL + "  " + body + "," + NL + ")"
    else:
        ref_fig = "#text(fill: gray)[원화 없음 — `--refdir` 를 주면 실린다]"

    vm = []
    for k in ("side", "back"):
        if f"{k}_regions" in assets:
            want = [("regions", "판 분할"), ("order", "가림 순서"), ("necks", "목"),
                    ("depth", "깊이"), ("normal", "법선"), ("shade", "법선 셰이딩")]
            cs = [_img(f"{k}_{w}", c) for w, c in want if f"{k}_{w}" in assets]
            vm.append("=== " + names[k] + NL * 2
                      + "#grid(columns: (1fr, 1fr, 1fr), gutter: 6pt," + NL + "  "
                      + ("," + NL + "  ").join(cs) + "," + NL + ")")
    view_maps = (NL * 2).join(vm) if vm else "#text(fill: gray)[추가 뷰 없음]"

    def _vt(ps, n=12):
        rr = "".join(
            "[" + q["id"] + "], [" + q["material"] + "], ["
            + format(q["px"]["area"], ",") + "], ["
            + ((f'{q["z"][0]:.3f}-{q["z"][1]:.3f}') if q.get("z") else "-") + "], ["
            + f'{q["depth_rank"]:+d}' + "]," + NL for q in ps[:n])
        return ("#table(columns: 5, stroke: 0.4pt, inset: 4pt," + NL
                + "  [*id*], [*재질*], [*면적px*], [*z 범위*], [*깊이순위*]," + NL
                + "  " + rr + ")")

    vt = []
    for k in ("side", "back"):
        ps = spec.get("parts_by_view", {}).get(k)
        if ps:
            vt.append("=== " + names[k] + " (상위 12 / 전체 " + str(len(ps)) + ")"
                      + NL * 2 + _vt(ps))
    view_tables = (NL * 2).join(vt) if vt else "#text(fill: gray)[추가 뷰 없음]"

    NL2 = chr(10)
    have = lambda f: (d / f).exists()
    fm = [("regions.png", "판 분할"), ("order.png", "가림 순서 (T-접합)"),
          ("necks.png", "목"), ("depth.png", "깊이 (crease 팽창)"),
          ("normal.png", "법선"), ("shade.png", "그 법선으로 셰이딩")]
    cells = [f'figure(image("{f}", width: 100%), caption: [{c}])'
             for f, c in fm if have(f)]
    front_maps = ("#grid(columns: (1fr, 1fr, 1fr), gutter: 6pt," + NL2 + "  "
                  + ("," + NL2 + "  ").join(cells) + "," + NL2 + ")") if cells else         "#text(fill: red)[맵 없음]"
    dj = d / "depth.json"
    if dj.exists():
        djs = json.loads(dj.read_text(encoding="utf-8"))
        flat_ok = djs["flatness_deg"] <= 15
        depth_tbl = ("#table(columns: (auto, auto, 1fr), stroke: 0.4pt, inset: 5pt," + NL2
                     + '  [깊이/폭], [' + str(djs["depth_over_width"])
                     + '], [측면 참조 실측. 지어내면 1.4배 깊어진다],' + NL2
                     + '  [판 안쪽 평평도], [#'
                     + okt(flat_ok, str(djs["flatness_deg"]) + "도")
                     + '], [10도 이하 평면 / 30도 이상 물집. bevel '
                     + str(djs["bevel_px"]) + 'px],' + NL2
                     + '  [평면 맞춘 판], [' + str(djs["panels"]) + '], [나머지는 전체 팽창 그대로],'
                     + NL2 + ")")
    else:
        depth_tbl = "#text(size: 8pt, fill: gray)[깊이 맵 없음 — `depth.py` 를 돌려라]"

    def _ops_row(p):
        o = p["ops"]
        mods = " → ".join(
            m["type"] + (f'({m["thickness"]})' if m["type"] == "SOLIDIFY" else
                         (f'({m["levels"]})' if m["type"] == "SUBSURF" else ""))
            for m in o["modifiers"])
        mir = "skip" if o["skip"] else ("O" if p.get("mirror") is True else "-")
        return ("[" + p["id"] + "], [" + o["make"] + "], [" + str(o["protrusion"])
                + "], [" + mods + "], [" + o["shade"] + "], [" + mir + "],\n")

    sym = spec["symmetry"]
    views_fig = ('#figure(image("blueprint_views.png", width: 100%), '
                 'caption: [삼면도 — 같은 z 축. 미러로 대체된 쪽은 그리지 않는다])'
                 if tv else "#text(fill: red)[삼면도 없음 — `--view side=... --view back=...`]")
    views_tbl = "".join(
        "[" + k + "], [" + v["source"] + "], [" + str(v["parts"]) + "], ["
        + str(v["metrics"]["junctions_used"]) + "], ["
        + str(v["metrics"]["recon_error"]) + "],\n"
        for k, v in spec["views"].items())
    # **부품 검증표** — 붙이기 전에 하나씩 확인한 결과. 설계도에 이게 없으면
    # "다 붙였는데 안 닮았다" 에서 어느 부품 탓인지 끝내 알 수 없다.
    vrows = sorted((p for p in parts if p.get("verify")),
                   key=lambda p: p["verify"]["iou"])
    ver_tbl = "".join(
        f'[{p["id"]}], [{p["ops"]["make"]}], [{p["verify"]["iou"]:.3f}], '
        f'[#{okt(p["verify"]["pass"], "통과" if p["verify"]["pass"] else "실패 — 조립 제외")}],\n'
        for p in vrows[:26])
    vpass = sum(1 for p in vrows if p["verify"]["pass"])
    vmed = (sorted(p["verify"]["iou"] for p in vrows)[len(vrows) // 2]
            if vrows else 0.0)
    ops_tbl = "".join(_ops_row(p) for p in parts[:20])
    checks_tbl = "".join("[" + c["name"] + "], [" + c["expr"].replace("_", "-") + "],\n"
                         for c in spec["checks"])
    parts_fig = ('#figure(image("blueprint_parts.png", width: 88%), '
                 'caption: [부품 윤곽 — 월드 좌표. 회색이 외형])'
                 if pp else "#text(fill: red)[부품 윤곽 없음]")
    dims = ('#figure(image("blueprint_dims.png", width: 100%), '
            'caption: [외형 치수 — 정면 반폭과 측면 깊이. 붉은 숫자가 실측값])'
            if bp else "#text(fill: red)[외형 데이터 없음]")

    src = f"""#set page(paper: "a4", margin: 1.5cm)
#set text(font: ("Malgun Gothic", "Segoe UI"), size: 9pt)

#align(center)[#text(size: 16pt, weight: "bold")[설계도 — {a.name}]]
#align(center)[#text(size: 8pt, fill: gray)[{spec["generated"]} · schema {spec["schema"]} · art-to-3d-maps]]
#v(2pt)
#rect(width: 100%, inset: 6pt, fill: rgb("#fff6e5"))[
  *규칙* — 조립 스크립트는 `buildspec.json` **만** 읽는다. 상수를 스크립트에 적지 않는다.
  스크립트에 숫자를 손으로 넣는 순간 추출값과 갈라지고, 눈으로 고치기 시작한다.
]

== 기준 (datum)

#table(columns: (auto, 1fr), stroke: 0.4pt, inset: 5pt,
  [단위], [{DATUM["unit"]}],
  [원점], [{DATUM["origin"]}],
  [축], [{DATUM["axes"]}],
  [주의], [{DATUM["note"]}],
)

== 외형

{dims}

== 참조 원화

{ref_fig}

== 삼면도

{views_fig}

#table(columns: 5, stroke: 0.4pt, inset: 5pt,
  [*뷰*], [*출처*], [*판 수*], [*T-접합*], [*재구성 오차*],
  {views_tbl}
)

== 좌우 대칭

#table(columns: (auto, auto, 1fr), stroke: 0.4pt, inset: 5pt,
  [미러 쌍], [{sym["mirror_pairs"]}], [한쪽만 만들고 Mirror 로 넘긴다],
  [중심 걸침], [{sym["center"]}], [좌우 대칭 부품. 중심선을 지난다],
  [*비대칭(unique)*], [*{sym["unique"]}*], [짝이 없다 — **따로 만들어야 한다**],
)
#text(size: 8pt, fill: gray)[
비대칭 부품을 미러로 처리하면 원작에 없는 대칭이 생긴다 — 오메가몬의 어깨 방패가 그런 것.
반대로 **대칭인 캐릭터인데 unique 가 많다면** 짝짓기 허용오차가 빡빡하거나 **참조 그림 자체가
좌우 비대칭**이라는 뜻이다(생성 이미지는 완전 대칭이 아니다). 숫자를 그대로 믿지 말고
삼면도에서 눈으로 확인해라 — LESSON 47.
]

== 맵 (정면)

{front_maps}

{depth_tbl}

== 뷰별 맵

{view_maps}

== 뷰별 부품표

{view_tables}

#pagebreak()

== 공정표 (build ops)

#rect(width: 100%, inset: 5pt, fill: rgb("#eef5ff"))[
  *규약* — 사각면 100% · 미러 원점 (0,0,0) · #raw("rotation_euler") 금지(회전은 정점에 굽는다) ·
  하드서피스는 flat 셰이딩
]

#table(columns: 6, stroke: 0.4pt, inset: 4pt,
  align: (left, center, right, left, center, center),
  [*id*], [*make*], [*protrusion*], [*modifier 스택*], [*셰이딩*], [*미러*],
  {ops_tbl}
)

#text(size: 8pt, fill: gray)[
모디파이어 값은 규칙에서 **파생**된다 — Solidify = protrusion x 0.9, Subsurf = 1,
Mirror 는 좌우 짝이 있는 부품에만. 규칙은 `recipes` 에 한 번만 적혀 있고
부품마다 손으로 타이핑하지 않는다. `skip` 인 부품은 미러로 대체되므로 만들지 않는다.
]

== 조립 후 점검

#table(columns: (auto, 1fr), stroke: 0.4pt, inset: 5pt,
  {checks_tbl}
)

== 부품 상세 (정면)

{parts_fig}

== 부품표 (면적 상위 {len(rows)} / 전체 {len(parts)})

#table(columns: 7, stroke: 0.4pt, inset: 4pt,
  align: (left, center, right, center, center, right, right),
  [*id*], [*재질*], [*면적px*], [*z 범위(월드)*], [*돌출*], [*깊이순위*], [*목*],
  {tbl}
)

== px → 월드 매핑

#table(columns: (auto, 1fr), stroke: 0.4pt, inset: 5pt,
  [앵커], [{fit_txt}],
  [월드/px], [{fit["world_per_px"] if fit else "—"}],
  [출처], [{fit["src"] if fit else "없음"}],
  [맞춤 오차], [{fit_err}],
)

== 신뢰도

#table(columns: (auto, 1fr), stroke: 0.4pt, inset: 5pt,
  [값 출처], [{conf}],
  [분할 재구성 오차], [{spec["metrics"]["recon_error"]} / 255],
  [T-접합], [{spec["metrics"]["junctions_used"]}],
)
#text(size: 8pt, fill: gray)[
`guessed` 로 표시된 값은 **하류가 다시 재야 한다.** 지금 돌출(protrusion)이 전부 guessed 다 —
측면/3-4 참조에서 부품별 앞뒤를 재면 derived 로 바뀐다.
]

#pagebreak()

= 부품 검증 — **붙이기 전에 하나씩 확인한다**

한 부품만 만들어 **자기 bbox 에 맞춘 창**으로 렌더하고, 그 부품이 나온 원화의 같은 창과
실루엣을 겹쳐 IoU 를 낸다. 전체 창으로 보면 작은 부품은 몇 픽셀이라 판정이 안 된다.

#table(columns: (auto, auto, auto, auto), stroke: 0.4pt, inset: 5pt, align: left,
  [*부품*], [*종류*], [*IoU*], [*판정*],
  {ver_tbl}
)

#table(columns: (auto, 1fr), stroke: 0.4pt, inset: 5pt,
  [검사한 부품], [{len(vrows)}],
  [통과 (IoU >= {a.verify_min})], [{vpass}],
  [중앙값 IoU], [{vmed:.3f}],
  [조립 대상], [{len(spec.get("assembly", []))}],
)

#text(size: 8pt, fill: gray)[
**실패한 부품은 조립에서 뺀다.** 49개를 한꺼번에 붙여놓고 전체 IoU 를 보면 숫자가
안 움직여도 어느 부품이 틀렸는지 알 수 없다 — 실제로 0.537\~0.615 에서 다섯 번
안 움직였다. 부품별로 재기 시작하자 원인이 한 번에 나왔다 (윤곽 단순화 허용오차가
크기에 비례하지 않아 작은 부품이 2.4배 부풀었고, 라벨 번짐이 버려진 판까지 흡수했다).
]

#pagebreak()

== 판정

#table(columns: (auto, 1fr), stroke: 0.4pt, inset: 6pt,
  [기준이 맞나], [],
  [부품 검증을 통과했나], [],
  [외형 치수가 맞나], [],
  [부품표에서 뺄 것 / 합칠 것], [],
  [이 설계도로 조립해도 되나], [],
)
#text(size: 8pt, fill: gray)[판정란은 사람이 적는다 (LIMS 규약).]
"""
    typ = d / "blueprint.typ"
    typ.write_text(src, encoding="utf-8")
    r = subprocess.run([TYPST, "compile", str(typ), str(pdf), "--root", str(d)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        print(r.stdout, r.stderr, file=sys.stderr)
        sys.exit(1)
    print(d / "buildspec.json")
    print(pdf)


if __name__ == "__main__":
    main()
