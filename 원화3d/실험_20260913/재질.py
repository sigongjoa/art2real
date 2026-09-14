# -*- coding: utf-8 -*-
"""**판마다 재질을 맞히나** — 기존 비전 모델을 원화 판에 걸어본다.

    python 재질.py                       자가검사
    python 재질.py 정답                   VRoid 11장 판 정답 + 판 조각 -> out/재질/판.jsonl · out/재질/<케이스>/*.png
    python 재질.py 조각 <판본>             판본 조각 (맥락 · 부품 · 고해상) -> out/재질/판_<판본>.jsonl
    py -3.11 재질.py 모델 <siglip|qwen> [판본]                 -> out/재질/예측_<모델>[_<판본>].jsonl
    python 재질.py 판정                   대조군 둘과 맞대기   -> out/기록/재질_<날짜>.json
    python 재질.py 그림                   원화 위에 칠하기     -> out/재질_그림.png

단계를 가른 이유: torch 는 py -3.11 에만, trimesh · cv2 · 창 규약(win)은 python 3.13 쪽에 있다.
근거는 `claudedocs/research_재질추정모델_20260913.md`. **형상을 만드는 모델이 아니라 라벨을 붙이는 모델**만 건다.

## 정답

벤치의 VRoid 11장(`소체` 는 base_female 과 md5 가 같아 뺀다)은 원본 모델 재질 이름에 종류가 붙어 있다.
`시트.py` 의 그리기(`faces_with_color` · `draw`)를 **그대로 다시 돌려** 화소마다 면 번호를 얻고, 면 -> 기하 -> 재질 이름.
다시 그린 색이 판 png 와 98% 넘게 같아야 한다 (assert) — 아니면 정답의 프레임이 판과 다른 것이다.

    CLOTH -> 천    SKIN -> 피부    HAIR -> 머리카락    FACE · EYE -> 뺀다 (눈썹·속눈썹·입 선)

판(`labels.npy`, 채우지 않은 원래 라벨)마다 그 화소들의 다수 재질. 50 화소 미만 · 한 재질이 80% 미만인 판은 뺀다.

## 맞히는 것 · 대조군

    siglip   google/siglip2-so400m-patch14-384. 판 조각(판 밖은 흰색) vs 문장 셋 × 재질 셋 평균
    qwen     Qwen/Qwen3-VL-2B-Instruct bf16. 같은 조각에 「cloth · skin · hair 중 한 단어」. 딴 답 = 기권
    다수결    다른 10장에서 면적이 가장 큰 재질을 늘 답한다
    색       다른 10장의 재질별 평균 Lab 에 판 평균색이 가장 가까운 재질 (**배운 대조군** — 색만 봐도 되는지)

점수 = 케이스마다 **판 면적 가중 정답률** (기권 = 1/3, 셋 중 찍기).

## 판정 — 돌리기 전에 적는다 (2026-09-13)

모델이 **대조군 둘(다수결 · 색) 각각을** 케이스 평균으로 이기고 **11장 중 6장 이상(과반)에서** 이겨야 「통과」.
프롬프트 · 문턱은 돌리기 전에 정했고 튜닝하지 않는다. 먼저 대조군이 멀쩡한지 본다 (앞뒤 실험에서 정답이 두 번 틀렸다).

대조군 먼저 돌려 봄 (모델 전): 다수결 0.752 (늘 「천」 — 천이 면적의 대부분이다) · 색 0.613 (흰 옷을 피부로 읽는다,
천 판 864 중 519). 둘 다 말이 되는 값이라 정답은 멀쩡하다. **다수결이 0.75 라 문턱이 높다** — 피부·머리를 맞혀야 넘는다.
면적 비율 천 0.762 · 피부 0.165 · 머리카락 0.073.

**정답의 흠 — 그림 재질과 메시 재질이 다르다.** VRoid 는 스타킹·타이츠를 몸 피부 텍스처에 칠한다. 조각을 뽑아 보니
검은 다리가 「피부」로 들어가 있었고, 피부 정답 면적의 26% 가 어두운 판(L* < 35)이다. 모델이 이걸 「천」이라 하면
그림으로는 맞고 채점으로는 틀린다 — 모델 점수의 상한을 깎는 몫이다. 머리카락 판은 가닥 조각이라 선이 대부분이다.

**결과 (첫 판본):** SigLIP 2 0.713 (5/11 · 6/11) 짐 · Qwen3-VL-2B 0.548 짐. 판 크기로 가르면 150 화소 미만 판(전체의 57%)에서
SigLIP 0.43, 2000 이상에서 0.82. **무너지는 건 천의 작은 조각뿐** — 천 0.27 -> 0.81, 피부는 크기와 무관하게 0.71, 머리 0.77~1.0.
어둡고 작은 천 조각의 75% 를 머리카락으로 읽는다. 판이 부품이 아니라 음영·주름선에 잘린 조각이라 **질문 단위가 너무 작았다.**

## 판본 — 결과를 보고 떠올린 것이라 따로 적고 건다 (2026-09-13 오후)

첫 판본에서 **하나씩만** 바꾼다. 정답 · 대조군 · 채점 · 판정은 그대로다.

    맥락     판 bbox 의 3배 창을 512 그림에서 자른다. 판 밖은 흰색 쪽으로 60% 흐리게, 판 윤곽은 빨간 2화소 선.
             qwen 은 「빨간 테 안이 대상, 흐린 곳은 주변」이라고 묻는다.  -> siglip · qwen
    부품     채운 라벨에서 맞닿은 판끼리, 평균색(OpenCV Lab 8비트)의 거리가 20 미만이면 합친다 (union-find).
             합친 영역 하나를 첫 판본과 같은 방식으로 오려 묻고, 답을 속한 판 전부에 준다.  -> siglip · qwen
    고해상   첫 판본과 같은 조각을 1024 그림에서 자른다 (라벨은 최근접으로 2배).  -> siglip

같이 적는 두 줄 (판정엔 안 쓴다): **흠 뺀 점수** — 피부 정답인데 L* < 35 인 판을 뺀 점수 · **작은 판 정답률** — 150 화소 미만.
문턱(3배 · 60% · 20)은 돌리기 전에 정했다.

**이 시험이 못 재는 것:** VRoid 에는 금속·딱딱한 재질이 없다. 「천이냐 판이냐」는 여기서 안 나온다.
"""
import json
import os
import sys
import time

HERE = r"G:\art2real\원화3d"
OUT = os.path.join(HERE, "out", "재질")
REC = os.path.join(HERE, "out", "기록")
CASES = ["avatarsample_d", "avatarsample_d_darkness", "avatarsample_e", "avatarsample_f", "avatarsample_g",
         "base_female", "base_male", "hairsample_female", "hairsample_male", "sakurada_fumiriya", "sendagaya_shino"]
NAMES = ["천", "피부", "머리카락"]
EN = ["cloth", "skin", "hair"]
SYN = {}                                        # qwen 답의 동의어 -> 부류 번호 (넷 부류 판본이 채운다)
MIN_PX, PURE = 50, 0.80
S = 512
TEMPL = ["an anime illustration of {}", "a flat-colored drawing of {}", "a close-up of {} in a character drawing"]
EN_LONG = ["clothing fabric", "bare skin", "hair"]
SIGLIP = "google/siglip2-so400m-patch14-384"
QWEN = "Qwen/Qwen3-VL-2B-Instruct"
ASK = ("This image is a cropped region of an anime character drawing; white is outside the region. "
       "What is this region made of? Answer with exactly one word: cloth, skin, or hair.")
ASK_CTX = ("This image shows part of an anime character drawing. The region outlined in red is the target; "
           "the faded area around it is context. What is the target region made of? "
           "Answer with exactly one word: cloth, skin, or hair.")
VARIANTS = ("맥락", "부품", "고해상")
CTX_SCALE, CTX_FADE, MERGE_DE = 3.0, 0.60, 20.0
SMALL = 150


def cls_of_name(name):
    """재질 이름 -> 0 천 · 1 피부 · 2 머리카락 · 3 뺀다."""
    n = name or ""
    if "_FACE" in n or "_EYE" in n:
        return 3
    return 0 if "_CLOTH" in n else 1 if "_SKIN" in n else 2 if "_HAIR" in n else 3


def panel_gt(classes):
    """판 화소들의 재질 번호 -> 정답 번호 또는 None (섞였거나 뺄 재질)."""
    import numpy as np
    c = classes[classes >= 0]
    if len(c) < MIN_PX:
        return None
    cnt = np.bincount(c, minlength=4)
    top = int(cnt.argmax())
    return top if top < 3 and cnt[top] >= PURE * len(c) else None


def masked_tile(img, m, pad=4, up=224):
    """판 화소만 남기고 흰 바탕에 정사각형으로. 작으면 키운다. **첫 판본 · 부품 · 고해상이 같은 함수를 쓴다.**"""
    import cv2
    import numpy as np
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    side = max(y1 - y0, x1 - x0) + 2 * pad
    tile = np.full((side, side, 3), 255, np.uint8)
    oy, ox = (side - (y1 - y0)) // 2, (side - (x1 - x0)) // 2
    sub = tile[oy:oy + y1 - y0, ox:ox + x1 - x0]
    mm = m[y0:y1, x0:x1]
    sub[mm] = img[y0:y1, x0:x1][mm]
    if side < up:
        tile = cv2.resize(tile, (up, up), interpolation=cv2.INTER_NEAREST)
    return tile


def context_tile(img, m, up=384):
    """판 bbox 의 CTX_SCALE 배 창. 판 밖은 흐리게, 판 윤곽은 빨간 선 (BGR)."""
    import cv2
    import numpy as np
    ys, xs = np.nonzero(m)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    half = int(max(ys.max() - ys.min(), xs.max() - xs.min(), 8) * CTX_SCALE / 2) + 4
    y0, y1 = max(int(cy) - half, 0), min(int(cy) + half, img.shape[0])
    x0, x1 = max(int(cx) - half, 0), min(int(cx) + half, img.shape[1])
    t = img[y0:y1, x0:x1].astype(np.float32)
    mm = m[y0:y1, x0:x1]
    t[~mm] = t[~mm] * (1 - CTX_FADE) + 255 * CTX_FADE
    t = t.astype(np.uint8)
    k = max(1, round(up / max(t.shape[:2])))
    t = cv2.resize(t, (t.shape[1] * k, t.shape[0] * k), interpolation=cv2.INTER_NEAREST)
    big = cv2.resize(mm.astype(np.uint8), (t.shape[1], t.shape[0]), interpolation=cv2.INTER_NEAREST)
    cs, _ = cv2.findContours(big, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(t, cs, -1, (0, 0, 255), 2)
    return t


# ------------------------------------------------------------------ 1. 정답 (python 3.13)

def build():
    import cv2
    import numpy as np
    import trimesh
    sys.path.insert(0, HERE)
    import win as W
    import 시트 as SH
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for case in CASES:
        t0 = time.time()
        scene = trimesh.load(os.path.join(HERE, "out", "시트", case, "_model.glb"))
        V, F, col, mat = SH.faces_with_color(scene)
        cls_mi = np.array([cls_of_name(getattr(getattr(g.visual, "material", None), "name", None))
                           for g in scene.geometry.values()])            # `faces_with_color` 의 mi 와 같은 순서
        Vw = W.to_world(V, "xyz")
        Vw[:, 1] *= -1                                                   # 시트.py 기본값 (VRM 은 +z 를 본다)
        Vw = W.normalize(Vw)
        os.makedirs(os.path.join(OUT, case), exist_ok=True)
        n0 = len(rows)
        for v in W.VIEWS:
            rgb, ident = SH.draw(Vw, F, col, mat, v)
            sheet = cv2.imdecode(np.fromfile(os.path.join(HERE, "out", "시트", case, v + ".png"), np.uint8),
                                 cv2.IMREAD_UNCHANGED)
            hit = ident >= 0
            same = float((cv2.cvtColor(sheet[:, :, :3], cv2.COLOR_BGR2RGB) == rgb).all(2)[hit].mean())
            assert same > 0.98, "%s/%s 다시 그린 판이 png 와 다르다 (%.3f) — 정답 프레임이 어긋났다" % (case, v, same)
            pix = np.where(hit, cls_mi[mat[np.clip(ident, 0, None)]], -1)[::2, ::2]
            lab, img = view_data(case, v)
            for k in np.unique(lab):
                if k == 0:
                    continue
                m = lab == k
                gt = panel_gt(pix[m])
                if gt is None:
                    continue
                name = "%s_%d.png" % (v, k)
                cv2.imencode(".png", masked_tile(img, m))[1].tofile(os.path.join(OUT, case, name))
                bgr = img[m].mean(0)
                lab_c = cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2LAB)[0, 0].tolist()
                rows.append({"key": "%s/%s" % (case, name), "case": case, "view": v, "k": int(k),
                             "area": int(m.sum()), "gt": gt, "lab": lab_c})
        print("  %-24s 판 %3d · %.0f초" % (case, len(rows) - n0, time.time() - t0), flush=True)
    with open(os.path.join(OUT, "판.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    import collections
    print("  판 %d · 정답 분포 %s" % (len(rows), dict(collections.Counter(NAMES[r["gt"]] for r in rows))))


def view_data(case, v, size=S):
    """판 라벨(512) 과 art3d 가 본 그림 (size 로 줄인 흰 바탕 판, BGR)."""
    import cv2
    import numpy as np
    d = os.path.join(HERE, "out", "깊이", case)
    lab = np.load(os.path.join(d, v, "labels.npy"))
    img = cv2.resize(cv2.imdecode(np.fromfile(os.path.join(d, "_흰_%s.png" % v), np.uint8), 1),
                     (size, size), interpolation=cv2.INTER_AREA)
    return lab, img


# ------------------------------------------------------------------ 1b. 판본 조각 (python 3.13)

def build_variant(variant):
    """판본마다 「묻는 것」 목록을 만든다: {key: 그림 경로, members: [판 key ...]}."""
    import cv2
    import numpy as np
    assert variant in VARIANTS, variant
    rows = load_rows()
    items = []
    root = os.path.join(OUT, variant)
    for case in CASES:
        os.makedirs(os.path.join(root, case), exist_ok=True)
        for v in ("front", "side", "back"):
            mine = {r["k"]: r for r in rows if r["case"] == case and r["view"] == v}
            if not mine:
                continue
            lab, img = view_data(case, v)
            if variant == "맥락":
                for k, r in mine.items():
                    name = "%s_%d.png" % (v, k)
                    cv2.imencode(".png", context_tile(img, lab == k))[1].tofile(os.path.join(root, case, name))
                    items.append({"key": "%s/%s/%s" % (variant, case, name), "members": [r["key"]]})
            elif variant == "고해상":
                _, big = view_data(case, v, size=2 * S)
                lab2 = np.kron(lab, np.ones((2, 2), lab.dtype))          # 최근접 2배
                for k, r in mine.items():
                    name = "%s_%d.png" % (v, k)
                    cv2.imencode(".png", masked_tile(big, lab2 == k, pad=8))[1].tofile(os.path.join(root, case, name))
                    items.append({"key": "%s/%s/%s" % (variant, case, name), "members": [r["key"]]})
            else:                                                        # 부품
                for gi, ks in enumerate(merge_parts(case, v, lab, img)):
                    members = [mine[k]["key"] for k in ks if k in mine]
                    if not members:
                        continue
                    name = "%s_part%d.png" % (v, gi)
                    m = np.isin(lab, list(ks))
                    cv2.imencode(".png", masked_tile(img, m))[1].tofile(os.path.join(root, case, name))
                    items.append({"key": "%s/%s/%s" % (variant, case, name), "members": members})
        print("  %-24s %s 묻는 것 누적 %d" % (case, variant, len(items)), flush=True)
    with open(os.path.join(OUT, "판_%s.jsonl" % variant), "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    sizes = [len(it["members"]) for it in items]
    print("  %s · 묻는 것 %d · 판 %d · 한 번에 판 최대 %d" % (variant, len(items), sum(sizes), max(sizes)))


def merge_parts(case, v, lab, img):
    """맞닿은 판끼리 평균색이 MERGE_DE 안이면 합친다. -> [set(판 번호), ...]"""
    import cv2
    import numpy as np
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import 앞뒤 as A                                                     # 선 띠 채우기 · 맞닿은 쌍 · 판 알파 — 같은 규약
    F = A.fill(lab, A.sheet_mask(case, v))
    ids = [int(k) for k in np.unique(lab) if k > 0]
    labc = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    mean = {k: labc[lab == k].mean(0) for k in ids}
    parent = {k: k for k in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for (a, b) in A.pairs_of(F):
        if a in mean and b in mean and np.linalg.norm(mean[a] - mean[b]) < MERGE_DE:
            parent[find(a)] = find(b)
    groups = {}
    for k in ids:
        groups.setdefault(find(k), set()).add(k)
    return list(groups.values())


# ------------------------------------------------------------------ 2. 모델 (py -3.11)

def load_rows():
    return [json.loads(l) for l in open(os.path.join(OUT, "판.jsonl"), encoding="utf-8")]


def load_items(variant):
    if not variant:
        return [{"key": r["key"], "members": [r["key"]]} for r in load_rows()]
    return [json.loads(l) for l in open(os.path.join(OUT, "판_%s.jsonl" % variant), encoding="utf-8")]


def pred_path(model, variant):
    return os.path.join(OUT, "예측_%s%s.jsonl" % (model, "_" + variant if variant else ""))


def run_model(which, variant=None):
    import torch
    from PIL import Image
    items = load_items(variant)
    out = pred_path(which, variant)
    done = set()
    if os.path.exists(out):
        done = {json.loads(l)["key"] for l in open(out, encoding="utf-8")}
    todo = [r for r in items if r["key"] not in done]
    print("  %s %s · 묻는 것 %d 중 %d 남음" % (which, variant or "첫판본", len(items), len(todo)), flush=True)
    if not todo:
        return
    open_img = lambda r: Image.open(os.path.join(OUT, r["key"])).convert("RGB")
    t0 = time.time()
    if which == "siglip":
        from transformers import AutoModel, AutoProcessor
        model = AutoModel.from_pretrained(SIGLIP, dtype=torch.float16).to("cuda:0").eval()
        proc = AutoProcessor.from_pretrained(SIGLIP)
        feats = lambda o: o if torch.is_tensor(o) else o.pooler_output
        texts = [t.format(n) for n in EN_LONG for t in TEMPL]
        with torch.no_grad():
            tin = proc(text=texts, padding="max_length", max_length=64, return_tensors="pt").to("cuda:0")
            tf = feats(model.get_text_features(**tin)).float()
            tf = tf / tf.norm(dim=-1, keepdim=True)
            tf = tf.view(len(EN_LONG), len(TEMPL), -1).mean(1)
            tf = tf / tf.norm(dim=-1, keepdim=True)
        for i in range(0, len(todo), 32):
            batch = todo[i:i + 32]
            with torch.no_grad():
                iin = proc(images=[open_img(r) for r in batch], return_tensors="pt").to("cuda:0")
                iin["pixel_values"] = iin["pixel_values"].half()
                f = feats(model.get_image_features(**iin)).float()
                f = f / f.norm(dim=-1, keepdim=True)
                logit = (f @ tf.T).cpu().tolist()
            with open(out, "a", encoding="utf-8") as fh:
                for r, lg in zip(batch, logit):
                    fh.write(json.dumps({"key": r["key"], "pred": int(max(range(len(EN_LONG)), key=lambda j: lg[j])),
                                         "score": [round(x, 4) for x in lg]}) + "\n")
            if (i // 32) % 10 == 0:
                print("    %d/%d · %.0f초" % (i + len(batch), len(todo), time.time() - t0), flush=True)
    elif which == "qwen":
        from transformers import AutoModelForImageTextToText, AutoProcessor
        model = AutoModelForImageTextToText.from_pretrained(QWEN, dtype=torch.bfloat16, device_map="cuda:0").eval()
        proc = AutoProcessor.from_pretrained(QWEN)
        ask = ASK_CTX if variant == "맥락" else ASK
        for i, r in enumerate(todo):
            msgs = [{"role": "user", "content": [{"type": "image", "image": open_img(r)},
                                                 {"type": "text", "text": ask}]}]
            inp = proc.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True, return_dict=True,
                                           return_tensors="pt").to(model.device)
            with torch.no_grad():
                gen = model.generate(**inp, max_new_tokens=6, do_sample=False)
            ans = proc.batch_decode(gen[:, inp["input_ids"].shape[1]:], skip_special_tokens=True)[0].strip().lower()
            words = {w: j for j, w in enumerate(EN)}
            words.update(SYN)
            hits = sorted({j for w, j in words.items() if w in ans})
            pred = hits[0] if len(hits) == 1 else -1                     # 딴 답 · 둘 이상 = 기권
            with open(out, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"key": r["key"], "pred": pred, "answer": ans}, ensure_ascii=False) + "\n")
            if (i + 1) % 100 == 0:
                print("    %d/%d · %.0f초" % (i + 1, len(todo), time.time() - t0), flush=True)
    print("  -> %s" % os.path.relpath(out, HERE))


# ------------------------------------------------------------------ 3. 판정 (python 3.13)

def controls(rows):
    """케이스마다 다른 케이스로만 배운 대조군 둘 -> {key: pred}."""
    import numpy as np
    maj, col = {}, {}
    for c in CASES:
        tr = [r for r in rows if r["case"] != c]
        K = len(NAMES)
        area = np.bincount([r["gt"] for r in tr], weights=[r["area"] for r in tr], minlength=K)
        cen = np.array([np.average([r["lab"] for r in tr if r["gt"] == j], axis=0,
                                   weights=[r["area"] for r in tr if r["gt"] == j])
                        if any(r["gt"] == j for r in tr) else np.full(3, 1e9) for j in range(K)])
        for r in rows:
            if r["case"] == c:
                maj[r["key"]] = int(area.argmax())
                col[r["key"]] = int(np.argmin(np.linalg.norm(cen - np.array(r["lab"]), axis=1)))
    return {"다수결": maj, "색": col}


def all_preds(rows):
    """대조군 둘 + 있는 예측 파일 전부 -> {이름: {판 key: pred}}. 판본의 답은 속한 판 전부에 준다."""
    preds = controls(rows)
    for m in ("siglip", "qwen"):
        for variant in (None,) + VARIANTS:
            p = pred_path(m, variant)
            if not os.path.exists(p):
                continue
            got = {json.loads(l)["key"]: json.loads(l)["pred"] for l in open(p, encoding="utf-8")}
            out = {}
            for it in load_items(variant):
                if it["key"] in got:
                    for k in it["members"]:
                        out[k] = got[it["key"]]
            preds[m + ("_" + variant if variant else "")] = out
    return preds


def score(rows, pred):
    import numpy as np
    if not rows:
        return float("nan")
    w = np.array([r["area"] for r in rows], float)
    p = np.array([pred.get(r["key"], -1) for r in rows])
    g = np.array([r["gt"] for r in rows])
    return float((w * np.where(p == -1, 1 / len(NAMES), p == g)).sum() / w.sum())


def flawed(r):
    """정답 흠 — 피부 정답인데 어두운 판 (피부 텍스처에 칠한 스타킹)."""
    return r["gt"] == 1 and r["lab"][0] * 100 / 255 < 35


def judge():
    import numpy as np
    rows = load_rows()
    preds = all_preds(rows)
    cases = [c for c in CASES if any(r["case"] == c for r in rows)]
    table = {k: np.array([score([r for r in rows if r["case"] == c], v) for c in cases]) for k, v in preds.items()}
    clean = {k: np.array([score([r for r in rows if r["case"] == c and not flawed(r)], v) for c in cases])
             for k, v in preds.items()}
    small = [r for r in rows if r["area"] < SMALL]
    n = len(cases)
    print("\n  판 %d · %d 장 · 점수 = 판 면적 가중 정답률 (기권 1/3)" % (len(rows), n))
    print("  %-24s " % "케이스" + " ".join("%13s" % k for k in table))
    for i, c in enumerate(cases):
        print("  %-24s " % c + " ".join("%13.3f" % table[k][i] for k in table))
    verdict = {}
    print()
    for k in table:
        sm = np.mean([preds[k].get(r["key"], -1) == r["gt"] for r in small])
        line = "    %-13s 평균 %.3f · 흠 뺀 %.3f · 작은 판 %.2f" % (k, table[k].mean(), clean[k].mean(), sm)
        if k not in ("다수결", "색"):
            wins = [(table[k] - table[c]).mean() > 0 and (table[k] > table[c]).sum() > n / 2 for c in ("다수결", "색")]
            verdict[k] = "통과" if all(wins) else "짐"
            line += " · 다수결 대비 %+.3f (%d/%d) · 색 대비 %+.3f (%d/%d) · **%s**" % (
                (table[k] - table["다수결"]).mean(), (table[k] > table["다수결"]).sum(), n,
                (table[k] - table["색"]).mean(), (table[k] > table["색"]).sum(), n, verdict[k])
        print(line)
    print()
    for k, v in preds.items():                                           # 혼동표 — 어느 재질을 무엇으로 읽나
        cm = np.zeros((len(NAMES), len(NAMES) + 1), int)
        for r in rows:
            cm[r["gt"], v.get(r["key"], -1)] += 1
        print("    %-13s 혼동 (행 정답 · 열 %s/기권) %s" % (k, "/".join(NAMES), cm.tolist()))
    os.makedirs(REC, exist_ok=True)
    p = os.path.join(REC, "재질_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump({"때": time.strftime("%Y-%m-%d %H:%M"), "판정": verdict, "케이스": cases,
               "점수": {k: v.tolist() for k, v in table.items()},
               "흠뺀점수": {k: v.tolist() for k, v in clean.items()}}, open(p, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("  기록 -> %s" % os.path.relpath(p, HERE))


# ------------------------------------------------------------------ 4. 그림 (python 3.13)

def figure(cols_models=None, picks=None):
    """**판마다 무엇으로 읽었나를 원화 위에 칠한다.** 정답 칸 = 재질색, 나머지 = 예측 재질색 · 틀린 판은 빨간 테.

    케이스는 규칙으로 고른다 — 첫 모델이 다수결보다 제일 나은 3장 + 제일 못한 3장. 정면만."""
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw
    sys.path.insert(0, HERE)
    from 계획 import _font
    rows = load_rows()
    preds = all_preds(rows)
    models = cols_models or [k for k in preds if k not in ("다수결", "색")]
    sc = {k: {c: score([r for r in rows if r["case"] == c], v) for c in CASES} for k, v in preds.items()}
    if picks is None:
        gap = sorted(CASES, key=lambda c: sc[models[0]][c] - sc["다수결"][c])
        picks = [(c, "%s 가 다수결보다 나은 순" % models[0]) for c in gap[::-1][:3]] + \
                [(c, "%s 가 다수결보다 못한 순" % models[0]) for c in gap[:3]]
    COL = [(70, 130, 230), (240, 160, 60), (160, 90, 200), (60, 170, 90)]   # RGB · 천 파랑 · 피부 주황 · 머리 보라 · 딱딱함 초록
    cols = ["원화", "정답", "색"] + models
    T, PAD, LW, TOP = 300, 10, 250, 160
    RH = T + 44
    im = Image.new("RGB", (LW + len(cols) * (T + PAD) + PAD, TOP + len(picks) * RH + 20), "white")
    dr = ImageDraw.Draw(im)
    f1, f2, f3 = _font(28), _font(17), _font(14)
    dr.text((24, 18), "판마다 재질을 무엇으로 읽었나 — %s · %d장 · 정면" % (os.path.basename(OUT), len(CASES)),
            fill=(20, 20, 20), font=f1)
    dr.text((24, 60), "파랑 = 천 · 주황 = 피부 · 보라 = 머리카락 · 초록 = 딱딱함 · 회색 = 기권 · 빨간 테 = 틀림 · 칸 아래 = 이 케이스 점수(세 시점, 면적 가중)",
            fill=(90, 90, 90), font=f3)
    dr.text((24, 84), "평균 — " + " · ".join("%s %.3f" % (k, np.mean(list(sc[k].values())))
                                           for k in ["다수결", "색"] + models), fill=(40, 40, 40), font=f2)
    for j, name in enumerate(cols):
        dr.text((LW + PAD + j * (T + PAD), TOP - 26), name, fill=(40, 40, 40), font=f2)
    for i, (case, why) in enumerate(picks):
        lab, img = view_data(case, "front")
        img = img[:, :, ::-1].copy()
        base = (img * 0.35 + 255 * 0.65).astype(np.uint8)
        tiles = {"원화": img, **{k: base.copy() for k in cols[1:]}}
        rr = [r for r in rows if r["case"] == case and r["view"] == "front"]
        wrong = {k: np.zeros((S, S), bool) for k in cols[2:]}
        for r in rr:
            m = lab == r["k"]
            tiles["정답"][m] = COL[r["gt"]]
            for k in cols[2:]:
                p_ = preds[k].get(r["key"], -1)
                tiles[k][m] = COL[p_] if p_ >= 0 else (200, 200, 200)
                if p_ != r["gt"]:
                    wrong[k] |= m & ~cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        for k in cols[2:]:
            tiles[k][cv2.dilate(wrong[k].astype(np.uint8), np.ones((2, 2), np.uint8)).astype(bool)] = (220, 30, 30)
        ys, xs = np.nonzero((img < 250).any(2))
        cy, cx, h = (ys.min() + ys.max()) // 2, (xs.min() + xs.max()) // 2, max(np.ptp(ys), np.ptp(xs)) // 2 + 8
        y0 = TOP + i * RH
        dr.text((24, y0 + 8), case[:24], fill=(20, 20, 20), font=f2)
        dr.text((24, y0 + 32), "정면 판 %d" % len(rr), fill=(90, 90, 90), font=f3)
        dr.text((24, y0 + 52), why, fill=(150, 150, 150), font=f3)
        for j, name in enumerate(cols):
            crop_ = tiles[name][max(cy - h, 0):cy + h, max(cx - h, 0):cx + h]
            xx = LW + PAD + j * (T + PAD)
            im.paste(Image.fromarray(cv2.resize(crop_, (T, T), interpolation=cv2.INTER_NEAREST)), (xx, y0))
            dr.rectangle([xx, y0, xx + T - 1, y0 + T - 1], outline=(215, 215, 215))
            if name in sc:
                v = sc[name][case]
                dr.text((xx, y0 + T + 4), "%.3f (다수결 %.3f)" % (v, sc["다수결"][case]), font=f3,
                        fill=(30, 130, 60) if v > sc["다수결"][case] else (190, 60, 40))
    p = OUT + "_그림.png"                                              # out/재질_그림.png · out/재질넷_그림.png
    im.save(p)
    print("  -> %s" % os.path.relpath(p, HERE))


def selfcheck():
    import numpy as np
    assert [cls_of_name(n) for n in ("F00_002_01_Onepice_01_CLOTH", "F00_002_02_Body_00_SKIN",
            "F00_000_Hair_00_HAIR_01", "F00_000_00_FaceBrow_00_FACE", "F00_000_00_EyeIris_00_EYE",
            "F00_000_00_Face_00_SKIN", None)] == [0, 1, 2, 3, 3, 1, 3], "재질 이름 규칙"
    assert panel_gt(np.array([0] * 90 + [2] * 10)) == 0, "순도 90% 는 받는다"
    assert panel_gt(np.array([0] * 70 + [2] * 30)) is None, "순도 70% 는 뺀다"
    assert panel_gt(np.array([3] * 100)) is None, "얼굴·눈 판은 뺀다"
    assert panel_gt(np.array([1] * 40 + [-1] * 60)) is None, "재질 화소가 50 미만이면 뺀다"
    # 판본 조각: 흰 바탕 조각은 판 화소만 · 맥락 조각은 판보다 넓고 빨간 선이 있다
    img = np.zeros((100, 100, 3), np.uint8)
    img[:] = (10, 200, 30)
    m = np.zeros((100, 100), bool)
    m[40:60, 45:55] = True
    t = masked_tile(img, m, pad=4, up=0)
    assert (t == 255).all(2).sum() > 0 and ((t == (10, 200, 30)).all(2)).sum() == m.sum(), "흰 바탕 조각"
    c = context_tile(img, m, up=0)
    assert c.shape[0] > 20 and ((c == (0, 0, 255)).all(2)).any(), "맥락 조각에 빨간 테가 없다"
    print("  자가검사 통과 — 재질 이름 · 판 순도 · 조각 둘")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else ""
    if what == "모델":
        run_model(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        selfcheck()
        if what == "정답":
            build()
        elif what == "조각":
            build_variant(sys.argv[2])
        elif what == "판정":
            judge()
        elif what == "그림":
            figure(sys.argv[2:] or None)
