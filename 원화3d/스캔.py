# -*- coding: utf-8 -*-
"""**진짜 스캔 물건을 받는다.** Google Scanned Objects (CC-BY 4.0) 에서 골라 받고 판을 뽑는다.

    python 스캔.py 목록          쓸 만한 후보를 훑어 out/스캔후보.json 에 적는다
    python 스캔.py 받기 [이름 ...]  받아서 out/모델/스캔_<이름>.glb 로 굽고 시트까지
    python 스캔.py 그림          받은 것들을 한 장으로 -> out/스캔.png

## 왜 이게 필요한가

`대조.py` 가 스스로 적어둔 한계다 — 「전부 렌더한 판이라 세 판이 자동으로 일치한다.
**실제 원화의 지저분함은 여기서 재현되지 않는다**」. 지금 벤치는 둘 다 깨끗한 입력이다
(기본도형은 우리가 지었고, 캐릭터는 게임 에셋이라 표면이 정돈돼 있다).

**GSO 는 실제 스캔이라 표면이 지저분하다** — 구멍, 노이즈, 두께 없는 껍질, 바닥이 잘린 것.
파이프라인이 「깨끗하지 않은 정답」에서 어떻게 되는지 처음으로 시험한다.

## 라이선스

**CC-BY 4.0.** `모으기.py` 의 「CC0 만」 규약과 다르다 — 출처를 적으면 상업 사용이 되므로
받은 것마다 `creator`·`license`·`url` 을 `out/모델/스캔목록.json` 에 남긴다.
그 파일이 곧 저작자 표시다.

## 「서 있는 물건만」

창 규약이 **키로 정규화**하므로 누운 물건은 판을 뽑는 것 자체가 뜻이 없다 (`대조.py` 와
같은 필터). GSO 는 생활용품이라 눕는 게 많아서 1,030개 중 대부분이 걸린다 —
그래서 **자동으로 다 받지 않는다.** 후보를 훑어 적어두고 손으로 고른다.
"""
import io
import json
import os
import subprocess
import sys
import urllib.request
import zipfile

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
MODELS = os.path.join(OUT, "모델")
OWNER = "GoogleResearch"
BASE = "https://fuel.gazebosim.org/1.0/%s/models" % OWNER
UA = {"User-Agent": "Mozilla/5.0 (art2real bench collector)"}
STAND = (1.6, 2.2)                               # 깊이/키 · 가로/키 상한. 대조.py 와 같은 값


def get(url, binary=True, timeout=120):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        b = r.read()
    return b if binary else b.decode("utf-8", "replace")


def _mesh(name):
    """모델 zip 을 받아 메시로. GSO 는 `meshes/model.obj` 하나가 들어 있다."""
    z = zipfile.ZipFile(io.BytesIO(get("%s/%s.zip" % (BASE, name))))
    obj = [n for n in z.namelist() if n.endswith("meshes/model.obj")]
    if not obj:
        raise RuntimeError("model.obj 가 없다")
    m = trimesh.load(io.BytesIO(z.read(obj[0])), file_type="obj", force="mesh", process=True)
    return m


def _standing(ex):
    """(가로, 깊이, 키) 로 봤을 때 서 있나. 키가 대표 치수가 아니면 판이 뜻을 잃는다."""
    return ex[1] <= STAND[0] * ex[2] and ex[0] <= STAND[1] * ex[2]


def 목록(n=120):
    """앞에서 n 개를 훑어 서 있는 것만 후보로 적는다. **받지는 않는다.**"""
    names, page = [], 1
    while len(names) < n:
        d = json.loads(get("%s?per_page=50&page=%d" % (BASE, page), binary=False))
        if not d:
            break
        names += [x["name"] for x in d]
        page += 1
    names = names[:n]
    cand = []
    for i, nm in enumerate(names, 1):
        try:
            m = _mesh(nm)
        except Exception as e:
            print("  %-40s 실패 %s" % (nm[:40], type(e).__name__)); continue
        ex = m.extents                            # GSO 는 z 가 위 (Gazebo 규약)
        ok = _standing(ex)
        cand.append({"name": nm, "extents": [round(float(v), 3) for v in ex],
                     "서있음": bool(ok), "faces": int(len(m.faces)),
                     "watertight": bool(m.is_watertight)})
        print("  %3d/%d %-42s %s 가로%.2f 깊이%.2f 키%.2f · 면 %6d %s"
              % (i, len(names), nm[:42], "서있음" if ok else "누움  ", *ex, len(m.faces),
                 "닫힘" if m.is_watertight else "열림"))
    json.dump(cand, open(os.path.join(OUT, "스캔후보.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    up = [c for c in cand if c["서있음"]]
    print("\n  %d 개 중 서 있는 것 %d 개 -> out/스캔후보.json" % (len(cand), len(up)))
    print("  받으려면: python 스캔.py 받기 %s" % " ".join(c["name"] for c in up[:6]))


def 받기(names):
    """골라 받아서 **Y-up glb** 로 굽고 시트까지 뽑는다."""
    os.makedirs(MODELS, exist_ok=True)
    lp = os.path.join(MODELS, "스캔목록.json")
    have = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else []
    seen = {r["name"] for r in have}
    for nm in names:
        case = "스캔_" + nm[:36]
        glb = os.path.join(MODELS, case + ".glb")
        if not os.path.exists(glb):
            m = _mesh(nm)
            if not _standing(m.extents):
                print("  %-40s 건너뜀 — 누운 물건" % nm[:40]); continue
            # GSO 는 z 가 위, `시트.py` 는 y 가 위(glTF)를 가정한다. 돌려서 내보낸다
            m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
            if m.visual is None or not hasattr(m.visual, "face_colors"):
                m.visual = trimesh.visual.ColorVisuals(
                    m, face_colors=np.full((len(m.faces), 4), 210, np.uint8))
            trimesh.Scene(m).export(glb)
        if nm not in seen:
            have.append({"name": nm, "case": case, "license": "CC-BY 4.0",
                         "creator": "Google Research (Scanned Objects)",
                         "url": "https://app.gazebosim.org/%s/fuel/models/%s" % (OWNER, nm)})
            seen.add(nm)
        if not os.path.exists(os.path.join(OUT, "시트", case, "truth.glb")):
            print("  판 뽑기 %s" % case)
            r = subprocess.run([sys.executable, os.path.join(HERE, "시트.py"), glb, "--이름", case],
                               cwd=HERE, capture_output=True, text=True, encoding="utf-8")
            if r.returncode:
                print("     실패: %s" % (r.stderr or "")[-200:])
        print("  %s" % case)
    json.dump(have, open(lp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n  %d 개 · 저작자 표시는 %s 에 남는다" % (len(have), os.path.basename(lp)))


def 그림():
    """받은 것들을 한 장으로. 정답 메시를 3/4 각도 깊이색으로."""
    sys.path.insert(0, HERE)
    import 정답 as J
    import 각도 as ANG
    from 계획 import _font
    from PIL import Image, ImageDraw
    lp = os.path.join(MODELS, "스캔목록.json")
    have = json.load(open(lp, encoding="utf-8"))
    R, PER = 240, 4
    rows = (len(have) + PER - 1) // PER
    im = Image.new("RGB", (PER * (R + 12) + 12, 70 + rows * (R + 34)), "white")
    g = ImageDraw.Draw(im)
    g.text((16, 14), "Google Scanned Objects — 받은 것 %d 개 (CC-BY 4.0)" % len(have),
           font=_font(20), fill=(20, 20, 20))
    g.text((16, 42), "정답 메시를 3/4 각도 깊이색으로. 파랑 멀다 -> 빨강 가깝다",
           font=_font(12), fill=(120, 120, 120))
    for i, r in enumerate(have):
        p = os.path.join(OUT, "시트", r["case"], "truth.glb")
        if not os.path.exists(p):
            continue
        t = trimesh.load(p, force="mesh")
        v, _ = J.grid(t, J.PITCH / 2)
        d, hit = ANG.depth(v, 35)
        x, y = 12 + (i % PER) * (R + 12), 70 + (i // PER) * (R + 34)
        im.paste(ANG.paint(d, hit, R, (d[hit].min(), d[hit].max())), (x, y))
        g.rectangle([x, y, x + R - 1, y + R - 1], outline=(220, 220, 220))
        g.text((x, y + R + 6), r["name"][:34], font=_font(11), fill=(90, 90, 90))
    im.save(os.path.join(OUT, "스캔.png"))
    print("  -> out/스캔.png")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "목록"
    if cmd == "목록":
        목록(int(sys.argv[2]) if len(sys.argv) > 2 else 120)
    elif cmd == "받기":
        받기(sys.argv[2:])
    elif cmd == "그림":
        그림()
    else:
        print(__doc__)
