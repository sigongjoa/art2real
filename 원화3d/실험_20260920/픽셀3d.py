# -*- coding: utf-8 -*-
"""**Pixal3D (다중 뷰 생성기) — 3판을 다 보면 1판만 보는 TripoSG 보다 덜 틀리나** (2026-09-20).

    python 픽셀3d.py 검사                  렌더러 좌우 · 판정 함수가 A/B/C/D 를 다 내나
    python 픽셀3d.py 입력                  네 장의 입력 뷰 (P1 · Pr · Ps) -> out/생성3D/pixal3d/입력/ + 배관 1 (시트 ↔ 궤도 자리)
    python 픽셀3d.py 생성 [n] [판본…]      ComfyUI(127.0.0.1:8199) 에 API 워크플로를 보낸다 -> out/생성3D/pixal3d/<판본>/<case>.glb
    python 픽셀3d.py 대조 [n]              어제 메시(정답 · T · T∩H · T→S)에 새 자(평평 · 능선 몫)만 — **P 를 재기 전에**
    python 픽셀3d.py 재다 [n] [판본…]      P 를 어제와 같은 정렬 · 같은 자로
    python 픽셀3d.py 판정 | 그림
    <venv python> 픽셀3d.py 줄임 in.npz out.npz     (안쪽 다리 — pymeshlab 은 D:\\imggen\\venv 에만 있다)

판정은 `claudedocs/plan_픽셀3d_20260920.md` 「Q」 절 그대로 — 생성 전에 적었다. 정렬 · 자 · 타일 · 틀은 전부 `메시변형.py` 가 쓰는 것을 import 한다.
"""
import json
import os
import sys
import time

import numpy as np

HERE = r"G:\art2real\원화3d"
ME = os.path.abspath(__file__)
VENV = r"D:\imggen\venv\Scripts\python.exe"
PROG = os.path.join(HERE, "out", "기록", "픽셀3d_진행.jsonl")
TILED = os.path.join(HERE, "out", "기록", "픽셀3d_타일")
GEN = os.path.join(HERE, "out", "생성3D", "pixal3d")
INP = os.path.join(GEN, "입력")
TAG = "픽셀3d v1 · P1/P1m/Pr/Ps · 템플릿 기본(56/12 · 42/20 · 1536 42/12) · 텍스처 뺌 (2026-09-20)"
SCRATCH = r"C:\Users\zesky\AppData\Local\Temp\claude\G--art2real\a6668565-5072-459b-9e0f-de16dc1a6c3c\scratchpad"
CIN, COUT = os.path.join(SCRATCH, "cin"), os.path.join(SCRATCH, "cout")      # ComfyUI 입출력 — ASCII 경로
URL = "http://127.0.0.1:8199"

sys.path.insert(0, os.path.join(HERE, "실험_20260919"))
import 메시변형 as MD                                                          # 실물4 · 재다 · rows · 타일 폴더 (torch 없이 import 된다)

판본 = ("P1", "P1m", "Pr", "Ps")
COLS = ("정답", "T", "T∩H", "T→S", "P1", "P1m", "Pr", "Ps")
오염 = "cloak_Chest_Closed_AngpV0HxD8"                                          # 창 잘림 (계획 「입력에서 걸린 것」)
틀린T = ("cloak_Chest_Closed_AngpV0HxD8", "cape_Hat_Stylised_lNN3PlrjSa")
FOV_R, FOV_S, PAD, RES = 20.0, 1.0, 1.1, 1024
AZ = {"front": 0.0, "left": 90.0, "back": 180.0, "right": 270.0}               # `nodes_trellis2._VIEW_AZIMUTHS`
QEM_OVER, QEM_F = 60_000, 30_000                                               # `메시변형.PROXY_OVER · PROXY_F` 와 같은 수
UP_RES = 1536                                                                  # 템플릿 기본. 8 GB 에서 안 돌면 계획서에 적고 내린다


# ═════════════════════════════ 입력 뷰 ═════════════════════════════

def 찍다(V, F, az, fov, res=RES, ss=2):
    """단위 정육면체에 앉힌 메시(Z 위 · 앞이 −y)를 Pixal3D 궤도 카메라로. -> (rgb uint8 검은 바탕 · 면 번호 · 알파).
    카메라는 `nodes_trellis2._orbit_camera_to_world` · `model._project_points_to_image` 와 같은 식이다.
    ponytail: 면마다 도는 numpy z-버퍼 — 정답 메시(1천 ~ 3만 면)에만 쓴다. 수십만 면이면 nvdiffrast 로."""
    import cv2
    R = res * ss
    a, f2 = np.radians(az), np.tan(np.radians(fov) / 2)
    back = np.array([np.sin(a), -np.cos(a), 0.0])
    right = np.array([np.cos(a), np.sin(a), 0.0])
    up = np.cross(back, right)
    P = V - back * (PAD * 0.5 / f2)
    depth = -(P @ back)
    fpx = (R / 2) / f2
    x = fpx * (P @ right) / depth + R / 2
    y = -fpx * (P @ up) / depth + R / 2
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    n /= np.linalg.norm(n, axis=1, keepdims=True).clip(1e-12)
    L = back + 0.35 * up + 0.25 * right
    shade = 0.30 + 0.70 * np.abs(n @ (L / np.linalg.norm(L)))                   # 머리등 (감김 방향 무관)
    zb = np.full((R, R), np.inf)
    ident = np.full((R, R), -1, np.int32)
    for i, (a_, b_, c_) in enumerate(F):
        xs, ys = x[[a_, b_, c_]], y[[a_, b_, c_]]
        x0, x1 = max(int(np.floor(xs.min())), 0), min(int(np.ceil(xs.max())) + 1, R)
        y0, y1 = max(int(np.floor(ys.min())), 0), min(int(np.ceil(ys.max())) + 1, R)
        if x0 >= x1 or y0 >= y1:
            continue
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
        w2 = 1 - w0 - w1
        z = w0 * depth[a_] + w1 * depth[b_] + w2 * depth[c_]
        ok = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9) & (z < zb[y0:y1, x0:x1])
        zb[y0:y1, x0:x1][ok] = z[ok]
        ident[y0:y1, x0:x1][ok] = i
    hit = ident >= 0
    g = np.where(hit, 205 * shade[np.clip(ident, 0, None)], 0).astype(np.float32)
    g = cv2.resize(g, (res, res), interpolation=cv2.INTER_AREA)
    al = cv2.resize(hit.astype(np.float32), (res, res), interpolation=cv2.INTER_AREA)
    return np.dstack([g] * 3).round().astype(np.uint8), ident[ss // 2::ss, ss // 2::ss], al


def 단위(V):
    lo, hi = V.min(0), V.max(0)
    return (V - (lo + hi) / 2) / (hi - lo).max()


def _png(p):
    import cv2
    return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_UNCHANGED)        # 한글 경로 (BGRA)


def _저장(p, rgb):
    import cv2
    cv2.imencode(".png", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))[1].tofile(p)


def _자르기(a, cx, cy, side, res=RES, nearest=False):
    """정사각 (cx, cy, side) 를 잘라 res 로. 그림 밖은 0."""
    from PIL import Image
    im = Image.fromarray(a)
    box = (int(round(cx - side / 2)), int(round(cy - side / 2)), int(round(cx + side / 2)), int(round(cy + side / 2)))
    return np.asarray(im.crop(box).resize((res, res), Image.NEAREST if nearest else Image.LANCZOS))


def 시트틀(case):
    """시트 알파만 보고 (정답 안 봄) 뷰마다 자를 정사각. 한 변 = 1.1 × 최대 치수 — 모든 뷰 같은 배율 (노드 규약)."""
    al = {v: _png(os.path.join(HERE, "out", "시트", case, v + ".png"))[..., 3] > 127 for v in ("front", "side", "back")}
    rows = np.nonzero(al["front"].any(1))[0]
    box, ext = {}, [rows.max() + 1 - rows.min()]
    for v in al:
        c = np.nonzero(al[v].any(0))[0]
        box[v] = ((c.min() + c.max() + 1) / 2, (rows.min() + rows.max() + 1) / 2)
        ext.append(c.max() + 1 - c.min())
    return box, PAD * max(ext)


def 시트뷰(case, view, box, side, flip=False):
    a = _png(os.path.join(HERE, "out", "시트", case, view + ".png"))
    rgba = _자르기(np.ascontiguousarray(a[..., [2, 1, 0, 3]]), box[view][0], box[view][1], side)
    # **면색을 올린다** (64 + 0.75 v) — 노드는 검은 바탕에 알파를 곱한다. 모자 시트는 거의 검은색이라 그대로면 검정 위 검정 = 빈 그림이다 (생성 전에 봤다 · 네 장 · P1 · Ps 에 똑같이)
    out = ((64 + 0.75 * rgba[..., :3].astype(np.float32)) * (rgba[..., 3:4].astype(np.float32) / 255)).round().astype(np.uint8)
    out = np.dstack([out, rgba[..., 3]])
    return out[:, ::-1].copy() if flip else out


def 입력(cases):
    """P1 · P1m · Pr · Ps 의 입력 그림을 만들고, 시트 ↔ 궤도 자리 대응을 **면 번호**로 검사한다 (배관 1)."""
    import trimesh
    sys.path.insert(0, HERE)
    os.chdir(HERE)
    import 시트 as ST
    import win as W
    os.makedirs(INP, exist_ok=True)
    iou = lambda a, b: float((a & b).sum() / max((a | b).sum(), 1))
    for case in cases:
        t0 = time.time()
        truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
        Vw = np.asarray(truth.vertices, np.float64)                              # truth.glb 는 창 좌표(z 위 · 앞이 −y) 그대로 저장돼 있다 (`시트.main`)
        F = np.asarray(truth.faces)
        # **truth.glb 는 얼굴이 +y 쪽이고, 시트는 그 메시의 「거울 그림」이다** (`시트.draw` 의 front 는 +y 쪽 겉면을 화면 가로 = +x 로 그린다 — 면 번호로 확인).
        # 시트가 그리는 물체 = truth 의 y 를 뒤집은 것. 그 물체는 −y 를 보고, 시트 front · side · back 은 그 물체의 참 front · right · back 뷰다.
        # 생성 메시가 truth 의 거울로 나와도 `생성3D.orient` 의 좌우 반전 찾기가 되돌린다 (T 도 같은 길이었다)
        Vu = 단위(Vw * np.array([1.0, -1.0, 1.0]))
        box, side = 시트틀(case)
        rec = {"자르기_px": round(side, 1)}
        # Pr — 본래 조건
        for v, az in AZ.items():
            rgb, _, _ = 찍다(Vu, F, az, FOV_R)
            _저장(os.path.join(INP, "%s__Pr_%s.png" % (case, v)), rgb)
        # Ps — 시트 그대로. right = side 그대로 · left = side 좌우 뒤집기(미러 대용)
        ps = {"front": 시트뷰(case, "front", box, side), "back": 시트뷰(case, "back", box, side),
              "right": 시트뷰(case, "side", box, side), "left": 시트뷰(case, "side", box, side, flip=True)}
        for v, rgb in ps.items():
            _저장(os.path.join(INP, "%s__Ps_%s.png" % (case, v)), rgb[..., :3])
        # P1 — T 가 본 그림(시트 front)을 제 bbox 의 1.1 배 정사각으로 (`ImageCropToMask` pad 1.1)
        al = _png(os.path.join(HERE, "out", "시트", case, "front.png"))[..., 3] > 127
        r, c = np.nonzero(al.any(1))[0], np.nonzero(al.any(0))[0]
        s1 = PAD * max(r.max() + 1 - r.min(), c.max() + 1 - c.min())
        _저장(os.path.join(INP, "%s__P1_front.png" % case), 시트뷰(case, "front", {"front": ((c.min() + c.max() + 1) / 2, (r.min() + r.max() + 1) / 2)}, s1)[..., :3])
        # 배관 1 — 시트의 `draw` 가 보는 면 번호 대 내 정사영(fov 1°) 렌더의 면 번호. 같은 자르기
        col, mat = np.full((len(F), 3), 200, np.uint8), np.zeros(len(F), np.int32)
        mine = {v: 찍다(Vu, F, az, FOV_S, ss=1) for v, az in AZ.items()}
        agree = {}
        for sv in ("front", "side", "back"):
            _, ident = ST.draw(Vw, F, col, mat, sv, line=False)
            idc = _자르기(ident.astype(np.int32), box[sv][0], box[sv][1], side, nearest=True)
            for slot in AZ:
                for fl in (False, True):
                    a_ = idc[:, ::-1] if fl else idc
                    b_ = mine[slot][1]
                    both = (a_ >= 0) & (b_ >= 0)
                    agree["%s→%s%s" % (sv, slot, "·뒤집" if fl else "")] = round(float((a_ == b_)[both].mean()) if both.any() else 0.0, 3)
        rec["면번호일치"] = {k: v for k, v in agree.items() if v >= 0.2}
        best = {sv: max((k for k in agree if k.startswith(sv + "→")), key=agree.get) for sv in ("front", "side", "back")}
        rec["자리"] = best
        rec["실루엣IoU"] = {"front": round(iou(mine["front"][2] > 0.5, ps["front"][..., 3] > 127), 4),
                           "right": round(iou(mine["right"][2] > 0.5, ps["right"][..., 3] > 127), 4),
                           "back": round(iou(mine["back"][2] > 0.5, ps["back"][..., 3] > 127), 4)}
        print("  %s  자르기 %.0fpx  자리 %s\n      실루엣 IoU(정사영 렌더 대 시트) %s  (%.0f초)" % (case, side, best, rec["실루엣IoU"], time.time() - t0), flush=True)
        assert best == {"front": "front→front", "side": "side→right", "back": "back→back"}, "시트 ↔ 궤도 자리가 계획과 다르다: %s" % agree
        if case != 오염:
            assert min(rec["실루엣IoU"].values()) >= 0.97, "정사영 렌더가 시트와 안 맞는다 %s" % rec["실루엣IoU"]
        적다(case, "입력", rec)


# ═════════════════════════════ 생성 (ComfyUI API) ═════════════════════════════

def 프롬프트(kind, files, prefix):
    multi = kind != "P1"
    g = {"u": ("UNETLoader", {"unet_name": "pixal3d_multiview_int8_convrot.safetensors" if multi else "pixal3d_int8_convrot.safetensors", "weight_dtype": "default"}),
         "cv": ("CLIPVisionLoader", {"clip_name": "dino_v3_L_naf_fp32.safetensors"}),
         "vae": ("VAELoader", {"vae_name": "trellis_2_shape_vae_bf16.safetensors"})}
    for v, f in files.items():
        g["im_" + v] = ("LoadImage", {"image": f})
    if multi:
        g["c"] = ("Pixal3DMultiViewConditioning", {"clip_vision_model": ["cv", 0], "fov": FOV_S if kind == "Ps" else FOV_R, **{v: ["im_" + v, 0] for v in files}})
    else:
        g["c"] = ("Pixal3DConditioning", {"clip_vision_model": ["cv", 0], "image": ["im_front", 0], "camera_angle_x": FOV_S})
    ks = lambda model, pos, neg, lat, seed, steps, sch: ("KSampler", {"model": model, "positive": pos, "negative": neg, "latent_image": lat, "seed": seed,
                                                                     "steps": steps, "cfg": 7.5, "sampler_name": "euler", "scheduler": sch, "denoise": 1.0})
    g.update({
        "o1": ("CFGOverride", {"model": ["u", 0], "cfg": 1.0, "start_percent": 0.667, "end_percent": 1.0}),
        "r1": ("RescaleCFG", {"model": ["o1", 0], "multiplier": 0.7}),
        "s1": ("ModelSamplingSD3", {"model": ["r1", 0], "shift": 5.0}),
        "o2": ("CFGOverride", {"model": ["u", 0], "cfg": 1.0, "start_percent": 0.769, "end_percent": 1.0}),
        "r2": ("RescaleCFG", {"model": ["o2", 0], "multiplier": 0.5}),
        "e": ("EmptyTrellis2LatentStructure", {"batch_size": 1}),
        "k1": ks(["s1", 0], ["c", 0], ["c", 1], ["e", 0], 56, 12, "normal"),
        "d1": ("VaeDecodeStructureTrellis2", {"samples": ["k1", 0], "vae": ["vae", 0], "resolution": "32"}),
        "st": ("Trellis2ShapeStage", {"positive": ["c", 0], "negative": ["c", 1], "voxel": ["d1", 0]}),
        "k2": ks(["r2", 0], ["st", 0], ["st", 1], ["st", 2], 42, 20, "normal"),
        "up": ("Trellis2UpsampleStage", {"positive": ["st", 0], "negative": ["st", 1], "shape_latent": ["k2", 0], "vae": ["vae", 0], "target_resolution": UP_RES}),
        "k3": ks(["r2", 0], ["up", 0], ["up", 1], ["up", 2], 42, 12, "simple"),
        "d2": ("VaeDecodeShapeTrellis", {"samples": ["k3", 0], "vae": ["vae", 0]}),
        "rm": ("RemeshMesh", {"mesh": ["d2", 0], "resolution": 768, "sign_mode": "udf", "sign_mode.qef": False, "sign_mode.drop_inverted_components": False,
                              "sign_mode.drop_enclosed_components": False, "band": 1.0, "project_back": 0.0, "fix_poles": False, "smooth_iters": 20,
                              "drop_small_components": 0.01, "precluster_max_verts": 20000000}),
        "dc": ("DecimateMesh", {"mesh": ["rm", 0], "target_face_count": 700000, "placement_mode": "midpoint"}),
        "sv": ("SaveGLB", {"mesh": ["dc", 0], "filename_prefix": prefix}),
    })
    return {k: {"class_type": c, "inputs": i} for k, (c, i) in g.items()}


def _http(path, data=None):
    import urllib.request
    req = urllib.request.Request(URL + path, data=json.dumps(data).encode() if data is not None else None, headers={"Content-Type": "application/json"})
    body = urllib.request.urlopen(req, timeout=60).read()
    return json.loads(body) if body.strip() else {}


def _vram():
    import subprocess
    r = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits", "-i", "0"], capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


def 생성(case, kind):
    import glob
    import shutil
    views = {"P1": ("front",), "P1m": ("front",), "Pr": tuple(AZ), "Ps": tuple(AZ)}[kind]
    src = {"P1": "P1", "P1m": "Pr", "Pr": "Pr", "Ps": "Ps"}[kind]
    os.makedirs(CIN, exist_ok=True)
    files = {}
    for v in views:
        files[v] = "%s__%s_%s.png" % (case, src, v)
        shutil.copyfile(os.path.join(INP, files[v]), os.path.join(CIN, files[v]))
    prefix = "px_%s_%s" % (kind, case)
    t0, peak = time.time(), _vram()
    busy = lambda: (lambda q: len(q["queue_running"]) + len(q["queue_pending"]))(_http("/queue"))
    while busy():                                                               # 앞 클라이언트가 죽고 남긴 작업 — 끝나길 기다려 결과를 줍는다
        time.sleep(10)
    out = sorted(glob.glob(os.path.join(COUT, "**", prefix + "*.glb"), recursive=True))
    주움 = bool(out)
    if not out:
        # 생성마다 모델을 내린다 — 안 내리면 서버가 앞 모델을 쥔 채 VRAM 이 밀려 구조 단계가 38 -> 64 -> 83 초/스텝으로 느려졌다 (드릴 P1 · Pr · 궤짝 Ps 에서 봄)
        _http("/free", {"unload_models": True, "free_memory": True})
        t0 = time.time()
        pid = _http("/prompt", {"prompt": 프롬프트(kind, files, prefix)})["prompt_id"]
        while True:
            time.sleep(5)
            peak = max(peak, _vram())
            h = _http("/history/" + pid)
            if pid in h and h[pid].get("status", {}).get("completed") is not None:
                st = h[pid]["status"]
                break
        assert st.get("status_str") == "success", "ComfyUI 실패: %s" % json.dumps(st, ensure_ascii=False)[:3000]
        out = sorted(glob.glob(os.path.join(COUT, "**", prefix + "*.glb"), recursive=True))
    assert out, "GLB 가 안 나왔다 (%s)" % prefix
    dst = os.path.join(GEN, kind, case + ".glb")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(out[-1], dst)
    rec = {"초": None if 주움 else round(time.time() - t0, 1), "주움": 주움, "VRAM봉우리MB": peak, "업샘플": UP_RES, "MB": round(os.path.getsize(dst) / 2 ** 20, 1)}
    적다(case, kind + "·생성", rec)
    print("  %s %s 생성 %s초 · VRAM 봉우리 %d MB · %.1f MB" % (case, kind, rec["초"], peak, rec["MB"]), flush=True)


# ═════════════════════════════ 자 ═════════════════════════════

def rows():
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[(r["case"], r["이름"])] = r
    return out


def 적다(case, name, rec):
    os.makedirs(os.path.dirname(PROG), exist_ok=True)
    with open(PROG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"case": case, "판": TAG, "이름": name, "때": time.strftime("%Y%m%d_%H%M%S"), **rec}, ensure_ascii=False) + "\n")


def _줄임_main(src, dst):
    import pymeshlab
    with np.load(src) as z:
        V, F = z["V"], z["F"]
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(np.asarray(V, np.float64), np.asarray(F, np.int32)))
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum=QEM_F, preservetopology=False, preserveboundary=True)   # `메시변형.deform` 과 같은 호출
    np.savez(dst, V=ms.current_mesh().vertex_matrix(), F=ms.current_mesh().face_matrix())


def 면자(m):
    """`면.dihedral` — 면 수에 휘둘리는 자라 6만 면 넘는 메시는 QEM 3만 면으로 줄여서 잰다 (계획 「자」)."""
    import subprocess
    import tempfile
    import trimesh
    from 면 import dihedral
    n0 = len(m.faces)
    if n0 > QEM_OVER:
        d = tempfile.mkdtemp()
        a, b = os.path.join(d, "in.npz"), os.path.join(d, "out.npz")
        np.savez(a, V=np.asarray(m.vertices, np.float64), F=np.asarray(m.faces, np.int64))
        r = subprocess.run([VENV, ME, "줄임", a, b], capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert r.returncode == 0, "줄임 다리 실패:\n%s" % (r.stderr or "")[-2000:]
        with np.load(b) as o:
            m = trimesh.Trimesh(o["V"], o["F"], process=False)
        for p in (a, b):
            os.remove(p)
        os.rmdir(d)
    r = dihedral(m)
    return {"평평": r["평평"], "계단": r["계단"], "능선": r["능선"], "중앙각": r["중앙각"], "면자_면": r["면"], "면자_원면": n0}


def _장(case):
    import trimesh
    masks, bs, plain, base, axes = MD.gen_build(case)
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    return masks, bs, plain, axes, truth


def 대조(case):
    """어제 메시에 새 자만 댄다. 어제 자(대각 · 축 · 거칠기)는 `메시변형_진행.jsonl` 값을 그대로 쓴다 — 다시 안 잰다."""
    import trimesh
    have = rows()
    names = [n for n in ("정답", "T", "T→S", "T∩H") if (case, n + "·면") not in have]
    if not names:
        return
    masks, bs, plain, axes, truth = _장(case)
    T = MD.fitted(case, masks) if set(names) - {"정답"} else None
    for n in names:
        t1 = time.time()
        if n == "정답":
            m = truth
        elif n == "T":
            m = T
        elif n == "T→S":
            with np.load(os.path.join(MD.MESHD, case + "__TS.npz")) as z:
                m = trimesh.Trimesh(z["V"].astype(np.float64), np.asarray(T.faces), process=False)
        else:
            m = MD.C_.to_mesh(MD.voxelize(T, axes) & plain, axes)
        rec = 면자(m)
        rec["초"] = round(time.time() - t1, 1)
        적다(case, n + "·면", rec)
        print("    %s %-4s 평평 %.3f 계단 %.3f 능선 %.3f 중앙각 %.1f (면 %d <- %d · %.0f초)"
              % (case[:14], n, rec["평평"], rec["계단"], rec["능선"], rec["중앙각"], rec["면자_면"], rec["면자_원면"], rec["초"]), flush=True)


def 재다(case, kinds):
    import trimesh
    from PIL import Image
    have = rows()
    kinds = [k for k in kinds if (case, k) not in have and (case, k + "·생성") in have]      # 생성 행이 적힌 뒤에만 (옮기는 중인 파일을 안 읽게)
    if not kinds:
        return
    os.makedirs(TILED, exist_ok=True)
    masks, bs, plain, axes, truth = _장(case)
    frame = MD.MX.AL.frame_of(truth, 45)
    tsil = {a: MD.DG.sil(truth, "front", None, a) for a in MD.DG.ANG}
    T_, ot = MD.J.grid(truth, MD.J.PITCH)
    tg = (MD.fill_slices(T_), T_, ot)
    import 생성3D as G3
    for k in kinds:
        t1 = time.time()
        g = trimesh.load(os.path.join(GEN, k, case + ".glb"), force="mesh")
        sc, V, yaw, mir = G3.orient(g.vertices, masks)                          # `불리언.fitted` 와 같은 두 줄 — 정렬점수를 남기려고 풀어 썼다
        m = trimesh.Trimesh(G3.fit_to_art(V, masks), np.asarray(g.faces), process=False)
        rec = MD.재다(m, tsil, masks, bs, tg)
        rec.update(면자(m))
        rec.update({"정렬점수": round(float(sc), 4), "회전": yaw, "반전": mir})
        if case == 오염:                                                        # 맞춤 없는 값 (참고 · 판정 밖) — 계획 「입력에서 걸린 것」
            m0 = trimesh.Trimesh(V, np.asarray(g.faces), process=False)
            rec["맞춤없음"] = {"대각평균": round(float(np.mean([MD.DG.iou(MD.DG.sil(m0, "front", None, a), tsil[a]) for a in MD.DG.ANG])), 5),
                              "가로": round(float(np.ptp(V[:, 0])), 4), "깊이": round(float(np.ptp(V[:, 1])), 4)}
        Image.fromarray(MD.MX.타일(m, frame)).save(os.path.join(TILED, "%s__%s.png" % (case, k)))
        rec["초"] = round(time.time() - t1, 1)
        적다(case, k, rec)
        print("    %s %-4s 대각 %.3f/%.3f/%.3f 못덮음 %.4f 넘침 %.4f iou128 %.3f 구멍 %d 거칠기 %.3f 평평 %.3f 능선 %.3f 정렬 %.3f 면 %d (%.0f초)"
              % (case[:14], k, rec["대각30"], rec["대각45"], rec["대각60"], rec["못덮음"], rec["넘침"], rec["iou128양쪽"], rec["구멍45"],
                 rec["거칠기"], rec["평평"], rec["능선"], sc, rec["면"], rec["초"]), flush=True)


# ═════════════════════════════ 판정 — 집계 함수는 여기 하나 ═════════════════════════════

Q1_중앙, Q1_승, Q1_최소 = 0.03, 3, -0.05
Q2_중앙, Q2_승 = 0.02, 3
Q3_중앙, Q3_최대, Q3_뜻 = 0.03, 0.08, 0.03
Q4_축비, Q4_평평하한, Q4_거칠 = 0.5, 0.03, 0.08


def _st(d):
    v, k = np.array(list(d.values()), float), list(d)
    return {"중앙": round(float(np.median(v)), 4), "평균": round(float(v.mean()), 4), "최소": [k[int(v.argmin())], round(float(v.min()), 4)],
            "최대": [k[int(v.argmax())], round(float(v.max()), 4)], "양": int((v > 0).sum()), "n": len(v), "장": {a: round(float(b), 4) for a, b in d.items()}}


def verdict(R, cases):
    """R[(case, 이름)] — 어제 행(정답 · T · T→S …)과 오늘 행(P · <이름>·면)을 합친 것."""
    g = lambda c, n, k: R[(c, n)][k]
    has = lambda n: all((c, n) in R for c in cases)
    out = {"판": TAG, "장": list(cases), "집계": "장별 값 -> 중앙(판정) · 평균 · 최소 · 최대 · 양의 수 같이", "지위": "관찰 (n = %d · 씨앗 1)" % len(cases)}
    diff = lambda a, b, cs=cases: {c: g(c, a, "대각평균") - g(c, b, "대각평균") for c in cs}
    s = _st(diff("Ps", "T"))
    out["Q1"] = {"Ps−T": s, "오염뺀3장": _st(diff("Ps", "T", [c for c in cases if c != 오염])),
                 "통과": bool(s["양"] >= Q1_승 and s["중앙"] >= Q1_중앙 and s["최소"][1] >= Q1_최소)}
    ctl = "P1m" if has("P1m") else "P1"
    s2 = _st(diff("Pr", ctl))
    out["Q2"] = {"대조": ctl + ("" if ctl == "P1m" else " (교란: 모델 · 그림체 · 원근이 같이 다르다)"), "Pr−" + ctl: s2, "Pr−P1": _st(diff("Pr", "P1")),
                 "통과": bool(s2["양"] >= Q2_승 and s2["중앙"] >= Q2_중앙)}
    prT, s3 = _st(diff("Pr", "T")), _st(diff("Pr", "Ps"))
    뜻 = prT["중앙"] >= Q3_뜻
    out["Q3"] = {"Pr−Ps": s3, "Pr−T": prT, "오염뺀3장": _st(diff("Pr", "Ps", [c for c in cases if c != 오염])),
                 "통과": (bool(s3["중앙"] <= Q3_중앙 and s3["최대"][1] <= Q3_최대) if 뜻 else None), "뜻": "있음" if 뜻 else "뜻 없음 — Pr 이 T 를 +%.2f 못 넘는다" % Q3_뜻}
    q4 = {}
    for c in [c for c in 틀린T if c in cases]:
        ax = lambda n: max(g(c, n, "못덮음"), g(c, n, "넘침"))
        fl = lambda n: abs(g(c, n, "평평") - g(c, "정답·면", "평평"))
        r = {"축오차": {n: round(ax(n), 4) for n in ("T", "T→S", "P1", "Pr", "Ps")}, "a": bool(ax("Ps") <= Q4_축비 * ax("T")),
             "평평": {"정답": g(c, "정답·면", "평평"), "T": g(c, "T·면", "평평"), "T→S": g(c, "T→S·면", "평평"), **{n: g(c, n, "평평") for n in ("P1", "Pr", "Ps")}},
             "b": (bool(fl("Ps") < fl("T·면")) if fl("T·면") >= Q4_평평하한 else None),
             "거칠기": {n: g(c, n, "거칠기") for n in ("정답", "T", "T→S", "P1", "Pr", "Ps")}, "c": bool(g(c, "Ps", "거칠기") - g(c, "T", "거칠기") <= Q4_거칠)}
        r["통과"] = bool(r["a"] and r["b"] is not False and r["c"])
        q4[c] = r
    out["Q4"] = {"장": q4, "b_뺀장": [c for c, r in q4.items() if r["b"] is None], "통과": bool(q4 and all(r["통과"] for r in q4.values()))}
    out["참고_P1−T"] = _st(diff("P1", "T"))
    names = [n for n in COLS if has(n)]
    out["참고"] = {k: {n: _st({c: g(c, n, k) for c in cases})["중앙"] for n in names} for k in ("대각평균", "못덮음", "넘침", "iou128양쪽", "구멍45", "거칠기")}
    out["참고"]["평평"] = {n: _st({c: g(c, n if (c, n) in R and "평평" in R[(c, n)] else n + "·면", "평평") for c in cases})["중앙"] for n in names}
    if out["Q1"]["통과"]:
        out["분기"] = ("A · Q1 통과 · Q4 통과 -> 하드서피스 9장으로 넓힌다 (같은 문턱). 기본값은 그대로" + ("" if out["Q3"]["통과"] else " · Q3 가 통과가 아니다 -> 넓히기 전에 입력 조건 민감도 카드")
                       if out["Q4"]["통과"] else "B · Q1 통과 · Q4 짐 -> held-out 실루엣은 이기는데 궤짝 · 모자는 아직 틀렸다. 넓히지 않는다")
    else:
        out["분기"] = ("C · Q1 짐 · Pr−T 중앙 ≥ +0.03 -> 본래 조건에서는 T 를 이기는데 시트 조건에서 못 이긴다. 다음 후보: 시트 -> 입력 변환 민감도 카드"
                       if 뜻 else "D · Q1 짐 · Pr−T 중앙 < +0.03 -> 이 4장에서 다중 뷰가 T 를 못 넘는다. 접는다")
    return out


def _R():
    MD._무거운()
    R = dict(MD.rows())
    R.update(rows())
    return R


def 판정():
    R = _R()
    cases = [c for c in MD.실물4 if all((c, n) in R for n in ("T", "P1", "Pr", "Ps", "정답·면", "T·면", "T→S·면"))]
    v = verdict(R, cases)
    v["생성"] = {k: _st({c: R[(c, k + "·생성")]["초"] for c in cases if R.get((c, k + "·생성"), {}).get("초")}) for k in 판본 if any((c, k + "·생성") in R for c in cases)}
    v["VRAM봉우리MB"] = max(r["VRAM봉우리MB"] for (c, n), r in R.items() if n.endswith("·생성"))
    p = os.path.join(HERE, "out", "기록", "픽셀3d_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in v if k != "참고"}, ensure_ascii=False, indent=1))
    print("->", p)


def 그림():
    from PIL import Image
    MD._무거운()
    R = rows()
    cols = [n for n in COLS if n not in 판본 or any((c, n) in R for c in MD.실물4)]
    blank = np.full((300, 300, 3), 240, np.uint8)
    img = lambda p: np.asarray(Image.open(p).convert("RGB")) if os.path.exists(p) else blank
    short = lambda c: "_".join(c.split("_")[:2]) if c.count("_") > 1 else c
    rs = [(short(c), [img(os.path.join(TILED if n in 판본 else MD.TILED, "%s__%s.png" % (c, n))) for n in cols]) for c in MD.실물4]
    MD.DC.grid(rs, cols, "Pixal3D — 3판을 다 보는 생성기 대 1판만 보는 TripoSG (45° 명암 · 같은 빛 · 같은 틀)",
               "T = TripoSG 3판맞춤 · T∩H = 복셀 교집합 · T→S = 실루엣 변형 (어제 타일) · P1 = 단일 뷰(시트 정면) · P1m = 다중 뷰 모델에 정면만 · Pr = 원근 4뷰 · Ps = 시트 3판+미러",
               os.path.join(HERE, "out", "픽셀3d_접촉지.png"), S=300)
    names = ["P1 front"] + ["Pr " + v for v in AZ] + ["Ps " + v for v in AZ]
    rs = [(short(c), [img(os.path.join(INP, "%s__%s.png" % (c, n.replace(" ", "_")))) for n in names]) for c in MD.실물4]
    MD.DC.grid(rs, names, "Pixal3D 에 준 그림 — 검은 바탕 · 1024² · 물체가 프레임의 1/1.1",
               "P1 = 시트 정면(T 가 본 그림 · 제 bbox 로 자름 · fov 1°) · Pr = 정답 메시 fov 20° 궤도 렌더 (P1m 은 이 중 front 만) · Ps = 시트 정사영 그대로(면색 64+0.75v) · right = side 그대로 · left = side 좌우 뒤집기(미러 대용) · fov 1° · 궤짝 시트는 창에서 잘려 있다",
               os.path.join(HERE, "out", "픽셀3d_입력.png"), S=200)


# ═════════════════════════════ 자가검사 ═════════════════════════════

def selfcheck():
    import trimesh
    # (1) 렌더러 좌우 — +x 면만 밝은 표식이 되도록, 상자의 +x 쪽에 혹을 붙인다: front 에서 화면 오른쪽 · back 에서 왼쪽 · left(카메라 +x)에서 가운데 · right 에서 안 보임
    box = trimesh.creation.box((0.6, 0.4, 1.0))
    bump = trimesh.creation.box((0.2, 0.1, 0.1))
    bump.apply_translation((0.4, -0.1, 0.3))                                     # +x 로 튀어나옴 · 앞(−y)쪽 · 위쪽
    m = trimesh.util.concatenate([box, bump])
    V, F = np.asarray(m.vertices), np.asarray(m.faces)
    nb = len(box.faces)
    cx = lambda az: (lambda idt: np.nonzero((idt >= nb).any(0))[0])(찍다(V, F, az, FOV_R, ss=1)[1])
    f, b, l, r = cx(0), cx(180), cx(90), cx(270)
    assert f.mean() > RES * 0.6 and b.mean() < RES * 0.4, "front/back 좌우가 뒤집혔다 %s %s" % (f.mean(), b.mean())
    assert l.mean() < RES * 0.5 and len(r) == 0, "left(카메라 +x)에서 앞쪽(−y) 혹은 화면 왼쪽 · right(카메라 −x)에서는 가려져야 한다 %s %s" % (l.mean(), len(r))
    al = 찍다(단위(V), F, 0, FOV_S, ss=1)[2] > 0.5
    w = np.nonzero(al.any(0))[0]
    assert abs((w.max() + 1 - w.min()) / RES - (np.ptp(V[:, 0]) / np.ptp(V, 0).max()) / PAD) < 0.01, "정사영에서 물체 폭이 프레임의 (폭/최대치수)/1.1 이 아니다"

    # (2) 판정이 A/B/C/D 를 다 낼 수 있다
    def 가짜(ps, pr, p1m=0.84, 축=0.05, 평=0.60, 거=0.10):
        R = {}
        for c in ("a", "b", 틀린T[0], 틀린T[1]):
            for n, s in (("T", 0.85), ("T→S", 0.88), ("P1", 0.84), ("P1m", p1m), ("Pr", pr), ("Ps", ps)):
                R[(c, n)] = {"대각평균": s, "못덮음": 0.4 if n == "T" else 축, "넘침": 0.01, "거칠기": 0.06 if n == "T" else 거, "평평": 평,
                             "iou128양쪽": s, "구멍45": 0}
            R[(c, "정답")] = {"대각평균": 1.0, "못덮음": 0, "넘침": 0, "거칠기": 0.05, "iou128양쪽": 1, "구멍45": 0}
            R[(c, "정답·면")], R[(c, "T·면")], R[(c, "T→S·면")] = {"평평": 0.62}, {"평평": 0.30}, {"평평": 0.20}
        return verdict(R, ("a", "b") + 틀린T)
    v = 가짜(0.92, 0.93)
    assert v["Q1"]["통과"] and v["Q2"]["통과"] and v["Q3"]["통과"] and v["Q4"]["통과"] and v["분기"][0] == "A", v
    assert 가짜(0.92, 0.93, 축=0.3)["분기"][0] == "B" and 가짜(0.92, 0.93, 평=0.1)["분기"][0] == "B" and 가짜(0.92, 0.93, 거=0.3)["분기"][0] == "B"
    assert 가짜(0.86, 0.93)["분기"][0] == "C" and 가짜(0.86, 0.93)["Q3"]["통과"] is False
    assert 가짜(0.86, 0.86)["분기"][0] == "D" and 가짜(0.86, 0.86)["Q3"]["통과"] is None
    assert not 가짜(0.92, 0.93, p1m=0.925)["Q2"]["통과"]
    print("  자가검사 통과 — 궤도 렌더 좌우 · 정사영 배율 · 판정이 A/B/C/D 와 Q2 짐 · Q3 뜻 없음을 다 낸다")


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else "검사"
    if cmd == "줄임":
        return _줄임_main(a[1], a[2])
    if cmd == "검사":
        return selfcheck()
    rest = a[1:]
    n = int(rest[0]) if rest and rest[0].isdigit() else 99
    kinds = [k for k in rest if k in 판본] or list(판본)
    cases = [c for c in rest if c in MD.실물4] or list(MD.실물4)
    if cmd == "입력":
        return 입력(cases)
    if cmd == "생성":
        have = rows()
        todo = [(c, k) for c in cases for k in kinds if (c, k + "·생성") not in have][:n]
        for c, k in todo:
            생성(c, k)
        return
    if cmd == "판정":
        return 판정()
    if cmd == "그림":
        return 그림()
    MD._무거운()
    have = rows()
    if cmd == "대조":
        for c in [c for c in cases if any((c, x + "·면") not in have for x in ("정답", "T", "T→S", "T∩H"))][:n]:
            대조(c)
    elif cmd == "재다":
        for c in [c for c in cases if any((c, k) not in have for k in kinds)][:n]:
            재다(c, kinds)


if __name__ == "__main__":
    main()
