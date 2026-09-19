# -*- coding: utf-8 -*-
"""**같은 장에서 추출기를 바꾼다** — MC · Reach for the Arcs · (NDC) · 도형 11개 문 (2026-09-19).

    python 메시추출.py 검사      자가검사 (답을 아는 것만)
    python 메시추출.py [n]       아직 안 한 도형 n 개 -> out/기록/메시추출_진행.jsonl
    python 메시추출.py 실물 [n]  실물 4장 (관찰 · 판정 아님)
    python 메시추출.py 판정      -> out/기록/메시추출_<때>.json
    python 메시추출.py 그림      -> out/메시추출_도형.png · out/메시추출_실물.png

계획 `claudedocs/plan_메시추출_20260919.md`. **문턱은 계획 그대로다 — 숫자를 보고 안 바꾼다.**

## 계획과 어긋난 셋 (고치지 않고 적는다)

    FlexiCubes  계획은 「nvdiffrast(nvcc) 라 뺀다」고 적었는데 **틀렸다** — `flexicubes.py` 의
             import 는 `torch` 와 `tables` 둘뿐이다. **판본 둘을 사전 등록으로 더했다**
             (FC·불 · FC·연속 · 숫자를 보기 전 · 문턱은 한 개도 안 바꿨다 · 가중치 기본값)
    NDC      첫 시도는 MSVC 없이 Cython 이 안 돼 졌다. Build Tools 14.44 가 깔린 뒤 들어왔다.
             **64³** 만 (3D CNN 이라 256³ 는 8GB VRAM 에 안 들어간다)
    RFTA 격자  `reach_for_the_arcs` 는 **격자 전체**가 필요하다 (좁은 띠는 부피가 +12.8% 틀렸다 · 합성 구).
             256³ = 1670만 점이라 이 기계에서 못 돈다 (64³ 에 195 초 · 대략 점 수에 비례).
             그래서 **RFTA 는 64³ 에서 돌리고, 같은 64³ 의 MC 를 짝 대조군으로 같이 잰다.**
             Q2 · Q3 는 64³ 짝끼리 비교한다 (해상도가 섞이지 않게).
"""
import gc
import json
import os
import sys
import time

import numpy as np
import trimesh

HERE = r"G:\art2real\원화3d"
sys.path.insert(0, HERE)
for d in ("실험_20260913", "실험_20260915", "실험_20260916", "실험_20260918", "실험_20260919"):
    sys.path.insert(0, os.path.join(HERE, d))
os.chdir(HERE)
import hull as H
import win as W
import 대조 as C_
import 정답 as J
from 겉면채점 import fill_slices
from 생성깎기 import build as gen_build, voxelize
from 면 import dihedral, roughness
import 대각 as DG
import 폴리싱 as PL
import 앨리어싱 as AL
import 깊이색 as DC
from 도형 import FORMS

PROG = os.path.join(HERE, "out", "기록", "메시추출_진행.jsonl")
TILED = os.path.join(HERE, "out", "기록", "메시추출_타일")
TAG = ("메시추출 v2 · MC/FlexiCubes/RFTA · 불리언·연속 장 · 256³ + 짝 64³ · 격자상한 · 균일 · 해상도대조 "
       "· 거칠기/이웃각/대각45/못덮음/IoU128 (2026-09-19)")
NRF = 64                          # RFTA 가 도는 격자. 256³ 는 1670만 점이라 못 돈다 (머리말)
VENV = r"D:\imggen\venv\Scripts\python.exe"        # torch. FlexiCubes 만 여기로 건너간다
FCPY = os.path.join(HERE, "실험_20260919", "fc_추출.py")
도형들 = ["도형_" + n for n, _, _, _ in FORMS]
실물4 = ("mech_Drill_8uBbH7Dvmb", "cloak_Chest_Closed_AngpV0HxD8",
         "cape_Hat_Stylised_lNN3PlrjSa", "avatarsample_d")
# 각진 도형 / 둥근 도형 — Q4 (NDC) 와 Q5 서술이 쓴다. `도형.py` 목록 그대로
각진 = ("도형_상자", "도형_두기둥대각", "도형_두기둥나란히", "도형_상자45도", "도형_L자")
둥근 = ("도형_원기둥", "도형_원뿔", "도형_구", "도형_치마", "도형_토러스세움", "도형_토러스옆")
얇은 = ("도형_치마", "도형_토러스세움", "도형_토러스옆")     # H-RFTA 의 「가는 구조」
V256 = ("MC·불", "MC·연속", "FC·불", "FC·연속", "격자상한", "균일@MC·연속",
        "MC·연속→복셀", "FC·연속→복셀")
V64 = ("MC·불@64", "MC·연속@64", "FC·불@64", "FC·연속@64",
       "RFTA·불@64", "RFTA·연속@64", "NDC·불@64", "격자상한@64", "RFTA·연속@64→복셀")
PROGN = os.path.join(HERE, "out", "기록", "메시추출_ndc_진행.jsonl")   # NDC 는 뒤에 붙은 판이라 따로 적는다
PROGR = os.path.join(HERE, "out", "기록", "메시추출_rfta_진행.jsonl")
# **RFTA 는 따로 돈다.** 나머지 판본을 다 합쳐도 도형 하나에 5 분인데 RFTA 한 번이 10 분을 넘는다
# (합성 구 195 초 · 우리 hull 장은 안쪽에 큰 구가 많아 「locally make feasible」이 훨씬 무겁다).
# 같은 파일 · 같은 자 · 같은 격자로 뒤에 붙인다 (`판정` 이 합친다) — NDC 와 같은 규약.
RFTA_ON = False
VARS = ("정답",) + V256 + V64


def 여유GB():
    import psutil
    return round(psutil.virtual_memory().available / 1e9, 1)


def 봉우리GB():
    import psutil
    return round(psutil.Process().memory_info().peak_wset / 1e9, 2)


# ── 장 ───────────────────────────────────────────────────────────────────────

def 깎기(masks, bs, deps):
    """`hull.carve_default` 를 **그대로 부르고** 실수 jf · jb 만 받아온다.

    `carve_depth` 는 마지막 줄 직전에 `if ZSMOOTH > 0: jf, jb = zsmooth(...)` 를 지난다.
    그 자리를 빌려 값을 꺼낸다 — 함수를 베끼지 않으니 기본 깎기가 바뀌면 여기도 같이 바뀐다.
    `tap` 은 받은 것을 그대로 돌려주므로 결과 복셀은 `carve_default` 와 **비트까지 같다**
    (자가검사가 그걸 확인한다). -> (복셀, axes, jf, jb)"""
    got = {}

    def tap(jf, jb, lo, hi, on, s):
        got["jf"], got["jb"] = jf, jb
        return jf, jb

    z0, f0 = H.ZSMOOTH, H.zsmooth
    H.ZSMOOTH, H.zsmooth = 1e-12, tap
    try:
        vox, axes = H.carve_default(masks, deps, back_sign=bs)
    finally:
        H.ZSMOOTH, H.zsmooth = z0, f0
    assert "jf" in got, "zsmooth 자리를 못 지났다 — carve_depth 가 바뀌었나"
    return vox, axes, got["jf"], got["jb"]


def 연속장(plain, jf, jb):
    """**연속 장** (오늘 스크래치) — `min(sdf_of(hull), min(j − jf, jb − j))`. 칸 단위 · 안 + · 밖 −.

    불리언으로 반올림하기 전의 실수 jf · jb 를 살린다. hull 의 부호거리장과 min 이라
    원화 실루엣 밖으로 못 부푼다."""
    n = plain.shape[1]
    j = np.arange(n, dtype=np.float32)[None, :, None]
    return np.minimum(H.sdf_of(plain),
                      np.minimum(j - jf[:, None, :], jb[:, None, :] - j)).astype(np.float32)


def 판(case, n):
    """격자 n³ 에서 마스크 · 이진 hull · 기본 깎기 복셀 · 연속 장. `hull.N` 은 되돌린다."""
    n0 = H.N
    H.N = n
    try:
        masks, bs, plain, _, axes = gen_build(case)
        deps = {v: np.ones((W.RES, W.RES), np.float32) for v in W.VIEWS}
        vox, axes, jf, jb = 깎기(masks, bs, deps)
        f = 연속장(plain, jf, jb)
    finally:
        H.N = n0
    return {"masks": masks, "bs": bs, "plain": plain, "vox": vox, "axes": axes, "f": f}


def 격자상한(truth, axes):
    """**이 격자에서 얻을 수 있는 최선** — 정답 메시를 격자에 실수 SDF 로 표본화해 MC 0.0.
    판본은 이걸 넘을 수 없다. 문턱의 위 끝 (계획 「문턱이 낼 수 있는 값」)."""
    import gpytoolbox as gpy
    u, _, z = axes
    cell = u[1] - u[0]
    V, F = np.asarray(truth.vertices, float), np.asarray(truth.faces)
    f = np.empty((len(u), len(u), len(z)), np.float32)
    X, Y = np.meshgrid(u, u, indexing="ij")
    xy = np.stack([X.ravel(), Y.ravel()], 1)
    del X, Y
    for k in range(0, len(z), 16):                           # **z 를 쪼갠다** — 256³ 를 한 번에 넣으면 5.7GB 를 찍는다
        zs = z[k:k + 16]
        U = np.concatenate([np.repeat(xy, len(zs), 0),
                            np.tile(zs, len(xy))[:, None]], 1)
        S = gpy.signed_distance(U, V, F)[0]
        f[:, :, k:k + len(zs)] = (-S / cell).reshape(len(u), len(u), len(zs))
        del U, S
    return mesh(H.mesh_from_field(f, axes))


def rfta(f, axes):
    """연속 장(칸 단위 · 안 +) -> `gpytoolbox.reach_for_the_arcs`. **매개변수는 기본값만.**

    가벼운 다리(`rfta_추출.py`)로 따로 띄운다 — 윈도우 spawn 이 이 무거운 모듈을 배치마다
    다시 import 해서 합성 구 195 초짜리가 30 분을 넘겼다 (09-19 실측)."""
    import subprocess
    import tempfile
    u, _, z = axes
    cell = u[1] - u[0]
    X, Y, Z = np.meshgrid(u, u, z, indexing="ij")
    d = tempfile.mkdtemp()
    a, b = os.path.join(d, "in.npz"), os.path.join(d, "out.npz")
    np.savez(a, U=np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1),
             S=(-f.ravel() * cell).astype(float))            # RFTA 규약: 안 − · 밖 +
    del X, Y, Z
    r = subprocess.run([sys.executable, os.path.join(HERE, "실험_20260919", "rfta_추출.py"), a, b],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, "RFTA 실패:\n%s" % (r.stderr or "")[-2000:]
    with np.load(b) as o:
        V, F = o["V"].copy(), o["F"].copy()
    for p in (a, b):
        os.remove(p)
    os.rmdir(d)
    return mesh((V, F))


def flexicubes(f, axes):
    """연속 장(칸 단위 · 안 +) -> FlexiCubes. **가중치 없이 기본 호출** (최적화 없는 순수 추출).

    torch 가 이 파이썬에 없어 `D:\\imggen\\venv` 로 건너간다 (`fc_추출.py`). GPU 0 만 쓴다.
    계획에는 「nvdiffrast 라 못 쓴다」고 적혀 있었는데 **틀렸다** — `flexicubes.py` 는 torch 만
    import 한다 (09-19 사전 등록 · 문턱 변경 없음)."""
    import subprocess
    import tempfile
    u, _, z = axes
    d = tempfile.mkdtemp()
    a, b = os.path.join(d, "in.npz"), os.path.join(d, "out.npz")
    np.savez(a, f=np.ascontiguousarray(f, np.float32), u0=u[0], z0=z[0], cell=u[1] - u[0])
    r = subprocess.run([VENV, FCPY, a, b], capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, "CUDA_VISIBLE_DEVICES": "0"})
    assert r.returncode == 0, "FlexiCubes 실패:\n%s" % (r.stderr or "")[-2000:]
    with np.load(b) as o:                                    # npz 는 게을러서 닫아야 지워진다
        V, F = o["V"].copy(), o["F"].copy()
    for p in (a, b):
        os.remove(p)
    os.rmdir(d)
    return mesh((V, F))


NDCD = r"G:\art2real\트레일\trail8_meshext\NDC"


def ndc(vox, axes):
    """**NDC (사전학습 · 이진 복셀 입력)** — `--input_type voxel --method ndc`. 매개변수 기본값.

    MSVC(Build Tools 14.44) 가 깔린 뒤 Cython 이 빌드돼서 들어왔다. 첫 시도(19:10)는
    `error: Microsoft Visual C++ 14.0 or greater is required` 로 졌다 — 그건 이 기계의 사실이었다.
    NDC 의 DataLoader 는 `num_workers>0` 인데 윈도우 spawn 이라 죽는다 -> 0 으로 내렸다
    (방법이 아니라 이식성 고침. 저장소 파일을 고친 곳은 그 한 줄뿐이다)."""
    import subprocess
    import tempfile
    d = tempfile.mkdtemp()
    b = os.path.join(d, "in.binvox")
    to_binvox(vox, b)
    r = subprocess.run([VENV, "main.py", "--test_input", b, "--input_type", "voxel",
                        "--method", "ndc", "--sample_dir", d],
                       cwd=NDCD, capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, "CUDA_VISIBLE_DEVICES": "0"})
    o = os.path.join(d, "quicktest_ndc_voxel.obj")
    assert r.returncode == 0 and os.path.exists(o), "NDC 실패:\n%s" % (r.stderr or r.stdout)[-2000:]
    m = trimesh.load(o, force="mesh")
    u, _, z = axes
    cell = u[1] - u[0]
    V = np.asarray(m.vertices, float)
    # **눈금 −1.5 는 상자로 쟀다** (배관 · `selfcheck`). 패딩 한 겹(−1) + binvox 칸이 [i, i+1] 을
    # 차지하는 규약(−0.5). 그러면 NDC 와 MC 의 중심이 0.01 칸 안에서 맞는다 (−1 로 두면 +0.50 칸 어긋난다).
    # 남는 것은 NDC 자신의 성질이다 — 상자에서 **양쪽으로 0.47 칸씩 안으로** 들어간다 (부피 −8.6%).
    V = np.stack([u[0] + (V[:, 0] - 1.5) * cell, u[0] + (V[:, 1] - 1.5) * cell,
                  z[0] + (V[:, 2] - 1.5) * cell], 1)
    F = np.asarray(m.faces)
    del m
    for p in os.listdir(d):
        os.remove(os.path.join(d, p))
    os.rmdir(d)
    return mesh((V, F))


def mesh(VF):
    m = trimesh.Trimesh(VF[0], VF[1], process=True)
    if m.volume < 0:
        m.invert()
    return m


def to_binvox(vox, path):
    """**NDC 입력 변환기** — 우리 bool 복셀 -> binvox
    (`main.py --test_input X.binvox --input_type voxel --method ndc`). 규약: binvox 1.0 · 단위 정육면체.

    **축 순서**: `NDC/utils.read_binvox_file_as_3d_array` 는 읽은 뒤 `transpose(0, 2, 1)` 을 한다
    (binvox 원 규약이 x-z-y 라서). 그래서 여기서 미리 y·z 를 바꿔 써야 NDC 가 우리 (x, y, z) 를 본다."""
    n = vox.shape[0]
    assert vox.shape == (n, n, n), "binvox 는 정육면체만"
    a = np.ascontiguousarray(vox.transpose(0, 2, 1).astype(np.uint8))
    flat = a.ravel()
    runs = []
    v, c = int(flat[0]), 0
    for x in flat:                                            # RLE (값, 길이<=255)
        if int(x) == v and c < 255:
            c += 1
        else:
            runs.append((v, c)); v, c = int(x), 1
    runs.append((v, c))
    with open(path, "wb") as fp:
        fp.write(b"#binvox 1\ndim %d %d %d\ntranslate 0 0 0\nscale 1\ndata\n" % (n, n, n))
        fp.write(bytes(b for pair in runs for b in pair))
    return path


# ── 자 (전부 이미 있는 것만 부른다) ──────────────────────────────────────────

def 재다(m, tsil45, masks, bs, tg):
    d = dihedral(m)
    r = {"면": int(len(m.faces)), "부피": round(float(abs(m.volume)), 6),
         "닫힘": bool(m.is_watertight),
         "조각": int(len(trimesh.graph.connected_components(
             m.face_adjacency, nodes=np.arange(len(m.faces))))),
         "평평": d["평평"], "계단": d["계단"], "능선": d["능선"], "중앙각": d["중앙각"],
         "거칠기": roughness(m)["거칠기"]}
    r["대각45"] = DG.iou(DG.sil(m, "front", None, 45), tsil45)
    r["못덮음"], r["넘침"] = DG.축(m, masks, bs)
    r["iou128"], r["iou128양쪽"] = DG.iou128(tg, m)
    return r


def 타일(m, frame, S=300):
    return PL.shaded(m, 45, frame, S=S)


# ── 한 장 ────────────────────────────────────────────────────────────────────

def one(case):
    t0 = time.time()
    os.makedirs(TILED, exist_ok=True)
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    frame = AL.frame_of(truth, 45)
    tsil45 = DG.sil(truth, "front", None, 45)
    T, ot = J.grid(truth, J.PITCH)
    tg = (fill_slices(T), T, ot)
    out = {"case": case, "판": TAG, "판본": {}, "때": time.strftime("%Y%m%d_%H%M")}

    def 넣다(name, m, tile=True):
        out["판본"][name] = 재다(m, tsil45, MB[0], MB[1], tg)
        if tile:
            # **PIL 로 쓴다.** `cv2.imwrite` 는 한글 경로에서 조용히 False 를 내고 파일을 안 만든다
            # (09-19 에 등위값 실험이 같은 자리에서 헛돌았다 — 메모리 `bench-runs-get-killed` 옆 줄)
            from PIL import Image
            Image.fromarray(타일(m, frame)).save(os.path.join(TILED, "%s__%s.png" % (case, name)))
        print("    %-16s 거칠기 %.3f 계단 %.3f 능선 %.3f 대각45 %.3f iou128 %.3f 면 %d %s"
              % (name, out["판본"][name]["거칠기"], out["판본"][name]["계단"],
                 out["판본"][name]["능선"], out["판본"][name]["대각45"],
                 out["판본"][name]["iou128"], out["판본"][name]["면"],
                 "닫힘" if out["판본"][name]["닫힘"] else "열림"), flush=True)

    # ── 256³ ────────────────────────────────────────────────────────────
    A = 판(case, 256)
    MB = (A["masks"], A["bs"])
    넣다("정답", truth)
    del truth
    gc.collect()

    m = C_.to_mesh(A["vox"], A["axes"])                      # MC·불 — 현행 기준선
    넣다("MC·불", m)
    del m
    gc.collect()

    m = mesh(H.mesh_from_field(A["f"], A["axes"]))           # MC·연속
    넣다("MC·연속", m)
    vol연속 = float(abs(m.volume))
    vx = voxelize(m, A["axes"])                              # 해상도 대조군 (09-18 규약)
    del m
    gc.collect()
    m = C_.to_mesh(vx, A["axes"])
    넣다("MC·연속→복셀", m, tile=False)
    del m, vx
    gc.collect()

    m = flexicubes(H.sdf_of(A["vox"]).astype(np.float32), A["axes"])   # FC·불 — H-장 의 대조군 (256³)
    넣다("FC·불", m)
    del m
    gc.collect()
    m = flexicubes(A["f"], A["axes"])                        # FC·연속 — 제안 (256³)
    넣다("FC·연속", m)
    vx = voxelize(m, A["axes"])
    del m
    gc.collect()
    m = C_.to_mesh(vx, A["axes"])
    넣다("FC·연속→복셀", m, tile=False)
    del m, vx
    gc.collect()

    넣다("격자상한", 격자상한(trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"),
                                          force="mesh"), A["axes"]))
    gc.collect()

    try:                                                     # 정보 0 대조군
        m, t = H.even_control(A["plain"], A["axes"], vol연속)
        넣다("균일@MC·연속", m, tile=False)
        out["판본"]["균일@MC·연속"]["침식t"] = round(float(t), 4)
        del m
    except AssertionError as e:
        out["판본"]["균일@MC·연속"] = {"실패": str(e)}
    del A
    gc.collect()

    # ── 64³ (RFTA 가 도는 격자 · 짝 MC 를 같이) ─────────────────────────
    B = 판(case, NRF)
    m = C_.to_mesh(B["vox"], B["axes"])
    넣다("MC·불@64", m, tile=False)
    del m
    gc.collect()
    m = mesh(H.mesh_from_field(B["f"], B["axes"]))
    넣다("MC·연속@64", m, tile=False)
    del m
    gc.collect()
    넣다("격자상한@64", 격자상한(trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"),
                                              force="mesh"), B["axes"]), tile=False)
    gc.collect()

    m = flexicubes(H.sdf_of(B["vox"]).astype(np.float32), B["axes"])
    넣다("FC·불@64", m, tile=False)
    del m
    gc.collect()
    m = flexicubes(B["f"], B["axes"])
    넣다("FC·연속@64", m, tile=False)
    del m
    gc.collect()

    if not RFTA_ON:                                          # RFTA 는 `rfta` 판에서 따로 붙인다
        del B
        gc.collect()
        out["초"] = round(time.time() - t0, 1)
        out["봉우리GB"] = 봉우리GB()
        return out

    m = rfta(H.sdf_of(B["vox"]).astype(np.float32), B["axes"])   # RFTA·불 — H-장 의 대조군
    넣다("RFTA·불@64", m)
    del m
    gc.collect()
    m = rfta(B["f"], B["axes"])                                  # RFTA·연속 — 제안
    넣다("RFTA·연속@64", m)
    vx = voxelize(m, B["axes"])
    del m
    gc.collect()
    m = C_.to_mesh(vx, B["axes"])
    넣다("RFTA·연속@64→복셀", m, tile=False)
    del m, vx, B
    gc.collect()

    out["초"] = round(time.time() - t0, 1)
    out["봉우리GB"] = 봉우리GB()
    return out


# ── 기록 ─────────────────────────────────────────────────────────────────────

def rows():
    """본 판 + **뒤에 붙은 NDC 판**을 합친다 (NDC 는 MSVC 가 깔린 뒤에 들어왔다)."""
    out = {}
    if os.path.exists(PROG):
        for line in open(PROG, encoding="utf-8"):
            r = json.loads(line)
            if r.get("판") == TAG:
                out[r["case"]] = r
    for p in (PROGN, PROGR):
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                r = json.loads(line)
                if r.get("판") == TAG and r["case"] in out:
                    out[r["case"]]["판본"].update(r["판본"])
    return out


def one_ndc(case):
    """NDC·불@64 만. 본 판을 다시 안 돌린다 — 같은 격자 · 같은 자 · 같은 틀."""
    t0 = time.time()
    os.makedirs(TILED, exist_ok=True)
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    frame = AL.frame_of(truth, 45)
    tsil45 = DG.sil(truth, "front", None, 45)
    T, ot = J.grid(truth, J.PITCH)
    tg = (fill_slices(T), T, ot)
    del truth
    B = 판(case, NRF)
    m = ndc(B["vox"], B["axes"])
    r = 재다(m, tsil45, B["masks"], B["bs"], tg)
    from PIL import Image
    Image.fromarray(타일(m, frame)).save(os.path.join(TILED, "%s__NDC·불@64.png" % case))
    print("    %-16s 거칠기 %.3f 계단 %.3f 능선 %.3f 대각45 %.3f iou128 %.3f 면 %d %s"
          % ("NDC·불@64", r["거칠기"], r["계단"], r["능선"], r["대각45"], r["iou128"], r["면"],
             "닫힘" if r["닫힘"] else "열림"), flush=True)
    return {"case": case, "판": TAG, "판본": {"NDC·불@64": r}, "초": round(time.time() - t0, 1)}


def one_rfta(case):
    """RFTA·불@64 · RFTA·연속@64 · 그 해상도 대조군. 본 판을 다시 안 돌린다."""
    t0 = time.time()
    os.makedirs(TILED, exist_ok=True)
    truth = trimesh.load(os.path.join(HERE, "out", "시트", case, "truth.glb"), force="mesh")
    frame = AL.frame_of(truth, 45)
    tsil45 = DG.sil(truth, "front", None, 45)
    T, ot = J.grid(truth, J.PITCH)
    tg = (fill_slices(T), T, ot)
    del truth
    gc.collect()
    B = 판(case, NRF)
    out = {}
    from PIL import Image
    # **RFTA·연속 은 안 돌린다.** 도형 둘(상자 · 토러스옆)에서 같은 자리로 죽는 것을 확인했고,
    # 원인이 구조적이다 — 우리 연속 장은 거리장이 아니다 (아래 주석). 한 번 도는 데 한 시간이
    # 넘으니 나머지 아홉에서 같은 죽음을 다시 사지 않는다. 사유를 값으로 적는다.
    out["RFTA·연속@64"] = {"실패": "AssertionError: Must supply at least two points. — 연속 장이 "
                                   "1-Lipschitz 가 아니라 RFTA 의 구가 서로 안 맞는다 "
                                   "(도형_상자 · 도형_토러스옆 에서 확인 · 나머지는 안 돌렸다)"}
    for name, fld in (("RFTA·불@64", H.sdf_of(B["vox"]).astype(np.float32)),):
        try:
            m = rfta(fld, B["axes"])
        except AssertionError as e:
            # **연속 장은 거리장이 아니다.** `j − jf(x, z)` 는 y 방향 깊이 한계일 뿐이고
            # jf 가 이웃 x 에서 여러 칸씩 뛴다 (타원 단면의 가장자리) — 1-Lipschitz 가 깨진다.
            # MC · FlexiCubes 는 부호와 국소 보간만 보니 상관없지만 RFTA 는 구 반지름을 |S| 로
            # 잡으므로 구가 서로 안 맞아 점이 하나도 안 남는다. 고치지 않고 적는다.
            out[name] = {"실패": str(e)[-400:]}
            print("    %-16s 실패 — %s" % (name, str(e).strip().splitlines()[-1]), flush=True)
            continue
        out[name] = 재다(m, tsil45, B["masks"], B["bs"], tg)
        Image.fromarray(타일(m, frame)).save(os.path.join(TILED, "%s__%s.png" % (case, name)))
        print("    %-16s 거칠기 %.3f 계단 %.3f 능선 %.3f 대각45 %.3f iou128 %.3f 면 %d %s"
              % (name, out[name]["거칠기"], out[name]["계단"], out[name]["능선"],
                 out[name]["대각45"], out[name]["iou128"], out[name]["면"],
                 "닫힘" if out[name]["닫힘"] else "열림"), flush=True)
        if name == "RFTA·연속@64":
            vx = voxelize(m, B["axes"])
            del m
            gc.collect()
            m2 = C_.to_mesh(vx, B["axes"])
            out["RFTA·연속@64→복셀"] = 재다(m2, tsil45, B["masks"], B["bs"], tg)
            del m2, vx
        else:
            del m
        gc.collect()
    return {"case": case, "판": TAG, "판본": out, "초": round(time.time() - t0, 1),
            "봉우리GB": 봉우리GB()}


def _run_붙임(n, cases, prog, fn, 이름):
    H.register_sheets()

    def 끝난것():                                            # **케이스마다 다시 읽는다** — 일꾼 여럿이 같이 돈다
        s = set()
        if os.path.exists(prog):
            for line in open(prog, encoding="utf-8"):
                d = json.loads(line)
                if d.get("판") == TAG:
                    s.add(d["case"])
        return s
    done = 끝난것()
    for c in [x for x in cases if x not in done][:n]:
        if c in 끝난것():
            continue
        print("  %s %s  (여유 %.1fGB)" % (c, 이름, 여유GB()), flush=True)
        r = fn(c)
        with open(prog, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def run_ndc(n, cases=None):
    _run_붙임(n, cases or 도형들, PROGN, one_ndc, "NDC")


def run_rfta(n, cases=None):
    _run_붙임(n, cases or 도형들, PROGR, one_rfta, "RFTA")


def run(n, cases=None):
    H.register_sheets()
    done = rows()
    todo = [c for c in (cases or 도형들) if c not in done][:n]
    for c in todo:
        if 여유GB() < 6:
            print("  %s 건너뜀 — 여유 %.1fGB" % (c, 여유GB()), flush=True)
            continue
        print("  %s  (여유 %.1fGB)" % (c, 여유GB()), flush=True)
        r = one(c)
        with open(PROG, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("  -> %.0f초 · 봉우리 %.1fGB" % (r["초"], r["봉우리GB"]), flush=True)


# ── 판정 ─────────────────────────────────────────────────────────────────────

def _st(d):
    """짝지은 차 한 뭉치 -> 중앙 · 평균 · 최악 · 최선 · 승 (「승」= 값이 0 보다 큰 장 수)."""
    a = np.asarray(d, float)
    return {"중앙": round(float(np.median(a)), 5), "평균": round(float(a.mean()), 5),
            "최악": round(float(a.min()), 5), "최선": round(float(a.max()), 5),
            "승": int((a > 0).sum()), "n": int(len(a))}


def verdict():
    rs = rows()
    cs = [c for c in 도형들 if c in rs]
    안잰 = [c for c in 도형들 if c not in rs]
    P = lambda c, v, k: rs[c]["판본"][v][k]
    # **격자 상한 − 기준선 < 0.01 인 도형은 판정에서 뺀다** (계획 「문턱이 낼 수 있는 값」)
    여유 = {c: round(P(c, "MC·불", "거칠기") - P(c, "격자상한", "거칠기"), 4) for c in cs}
    뺀 = [c for c in cs if 여유[c] < 0.01]
    쓴 = [c for c in cs if c not in 뺀]

    v = {"판": TAG, "때": time.strftime("%Y%m%d_%H%M"), "n": len(cs),
         "얼린집합": 도형들, "안잰": 안잰, "뺀판본": {},
         "배관메모": {
             "NDC": "19:10 첫 시도는 `error: Microsoft Visual C++ 14.0 or greater is required` 로 졌다. "
                    "MSVC Build Tools 14.44 가 깔린 뒤 vcvars64 에서 Cython 이 빌드됐고 "
                    "예제 cad.binvox 를 재현했다 (면 8732 · 닫힘). DataLoader num_workers>0 이 "
                    "윈도우 spawn 에서 죽어 0 으로 내렸다 — 저장소에서 고친 유일한 줄",
             "FlexiCubes": "계획의 「nvcc 라 못 쓴다」가 틀렸다 — torch 만 import 한다",
             "RFTA 격자": "좁은 띠는 부피가 +12.8% 틀렸다 (합성 구) — 전체 격자가 필요하고 "
                          "256³ = 1670만 점은 이 기계에서 못 돈다"},
         "더한판본(사전등록)": {
             "FC·불 · FC·연속": "계획의 「FlexiCubes 는 nvcc 라 뺀다」가 틀렸다 — flexicubes.py 는 "
                                "torch 만 import 한다. 숫자를 보기 전에 더했고 문턱은 안 바꿨다 (09-19)"},
         "RFTA격자": "%d³ (256³ 는 1670만 점이라 못 돈다) · 짝 MC 도 %d³" % (NRF, NRF),
         "거칠기여유(MC·불 − 격자상한)": 여유, "판정에서뺀도형": 뺀,
         "표": {c: {n: {k: rs[c]["판본"][n].get(k) for k in
                        ("거칠기", "계단", "능선", "평평", "대각45", "iou128", "못덮음", "면", "닫힘", "조각")}
                    for n in VARS if n in rs[c]["판본"]} for c in cs}}

    d = lambda a, b, k, sel: [P(c, a, k) - P(c, b, k) for c in sel]
    있 = lambda v: all("거칠기" in rs[c]["판본"].get(v, {}) for c in 쓴)
    Q = {}
    # Q1 장 — 추출기 고정(MC) · 256³
    q1r = _st(d("MC·연속", "MC·불", "거칠기", 쓴))
    q1i = _st(d("MC·연속", "MC·불", "iou128", 쓴))
    낮승 = sum(1 for c in 쓴 if P(c, "MC·연속", "거칠기") < P(c, "MC·불", "거칠기"))
    Q["Q1"] = {"물음": "연속 장이 불리언보다 나은가 (추출기 고정 = MC · 256³)",
               "문턱": "거칠기 차 중앙 <= -0.05 · 11개 중 >= 8 · IoU128 차 >= -0.01",
               "거칠기차": q1r, "거칠기가낮은장": 낮승, "IoU128차": q1i,
               "통과": bool(q1r["중앙"] <= -0.05 and 낮승 >= 8 and q1i["중앙"] >= -0.01)}
    # Q2 추출기 · 불리언 장. **같은 격자끼리만 맞댄다** (RFTA 는 64³ · FC 는 256³ 와 64³ 둘 다)
    def q2of(a, b, 이름):
        # **다 안 돌았으면 돈 것만으로 낸다** — 판정이 아니라 관찰이라고 표시한다 (RFTA 는 도형당 25 분)
        sel = [c for c in 쓴 if "거칠기" in rs[c]["판본"].get(a, {})
               and "거칠기" in rs[c]["판본"].get(b, {})]
        if not sel:
            return "%s 가 한 도형도 안 돌았다" % a
        s = _st([abs(x) for x in d(a, b, "거칠기", sel)])
        return {"짝": "%s − %s" % (a, b), "절대거칠기차": s,
                "부호있는차": _st(d(a, b, "거칠기", sel)),
                "쓴도형": [c.replace("도형_", "") for c in sel],
                "판정자격": "판정" if len(sel) == len(쓴) else
                            "관찰 — %d/%d 만 돌았다 (RFTA 는 도형당 25분)" % (len(sel), len(쓴)),
                "판정": ("H-장 지지" if s["중앙"] < 0.02 else
                         "H-장 기각" if s["중앙"] >= 0.05 else "가운데 — 어느 쪽도 아니다")}
    Q["Q2"] = {"물음": "같은 불리언 장에서 다른 추출기가 MC 와 다른가",
               "문턱": "|거칠기 차| 중앙 < 0.02 -> H-장 지지 · >= 0.05 -> H-장 기각",
               "RFTA@64": q2of("RFTA·불@64", "MC·불@64", "RFTA"),
               "FC@256": q2of("FC·불", "MC·불", "FC"),
               "FC@64": q2of("FC·불@64", "MC·불@64", "FC64"),
               "NDC@64": q2of("NDC·불@64", "MC·불@64", "NDC")}
    # Q3 추출기 · 연속 장
    얇 = [c for c in 쓴 if c in 얇은]

    def q3of(a, b):
        sel = [c for c in 쓴 if "거칠기" in rs[c]["판본"].get(a, {})
               and "거칠기" in rs[c]["판본"].get(b, {})]
        if not sel:
            return "%s 가 한 도형도 안 돌았다" % a
        얇2 = [c for c in 얇 if c in sel]
        r = _st(d(a, b, "거칠기", sel))
        mm = _st(d(a, b, "못덮음", 얇2)) if 얇2 else None
        ii = _st(d(a, b, "iou128", sel))
        return {"짝": "%s − %s" % (a, b), "거칠기차": r, "얇은도형못덮음차": mm, "IoU128차": ii,
                "판정자격": "판정" if len(sel) == len(쓴) else
                            "관찰 — %d/%d 만 돌았다" % (len(sel), len(쓴)),
                "통과": bool((r["중앙"] <= -0.02 or (mm and mm["중앙"] <= -0.005))
                             and ii["중앙"] >= -0.01)}
    Q["Q3"] = {"물음": "같은 연속 장에서 다른 추출기가 MC 보다 나은가",
               "문턱": "거칠기 차 <= -0.02 또는 얇은 도형 못덮음 차 <= -0.005 · 그 외 IoU 비열등",
               "RFTA@64": q3of("RFTA·연속@64", "MC·연속@64"),
               "FC@256": q3of("FC·연속", "MC·연속"),
               "FC@64": q3of("FC·연속@64", "MC·연속@64")}
    # Q4 NDC 모서리. 문턱은 계획 그대로 · 짝은 같은 격자(MC·불@64) — 256³ 것도 같이 싣는다
    def 능선표(v, base):
        각 = [c for c in 쓴 if c in 각진 and "거칠기" in rs[c]["판본"].get(v, {})]
        둥 = [c for c in 쓴 if c in 둥근 and "거칠기" in rs[c]["판본"].get(v, {})]
        return {"n각진": len(각), "n둥근": len(둥),
                "각진_정답과의거리": _st([-abs(P(c, v, "능선") - P(c, "정답", "능선")) for c in 각]),
                "각진_기준선보다가까운장": sum(
                    1 for c in 각 if abs(P(c, v, "능선") - P(c, "정답", "능선"))
                    < abs(P(c, base, "능선") - P(c, "정답", "능선"))),
                "둥근_능선": _st([P(c, v, "능선") for c in 둥]),
                "둥근_기준선대비": _st([P(c, v, "능선") - P(c, base, "능선") for c in 둥])}
    ndc있 = [c for c in 쓴 if "NDC·불@64" in rs[c]["판본"]]
    if ndc있:
        t = 능선표("NDC·불@64", "MC·불@64")
        Q["Q4"] = {"물음": "NDC·불 이 상자류에서 능선 몫을 정답 쪽으로 올리나 (짝 = MC·불@64)",
                   "문턱": "각진 도형에서 |능선 − 정답능선| 이 MC·불 보다 작고 · "
                           "둥근 도형에서 능선이 MC·불 + 0.02 를 안 넘는다",
                   "표": t, "n": len(ndc있),
                   "통과": bool(t["각진_기준선보다가까운장"] == t["n각진"]
                                and t["둥근_기준선대비"]["최선"] <= 0.02)}
    else:
        Q["Q4"] = {"물음": "NDC·불 이 상자류에서 능선 몫을 정답 쪽으로 올리나",
                   "판정": "판정 불가 — NDC 판이 아직 안 돌았다"}
    Q["Q4"]["서술(문턱 밖 · 다른 추출기)"] = {
        v: (능선표(v, "MC·불" if "@64" not in v else "MC·불@64") if 있(v) else "안 돌았다")
        for v in ("FC·불", "FC·연속", "RFTA·불@64")}
    # Q5 격자 상한까지 남은 몫 (서술)
    def 남은(v, k, ceil):
        sel = [c for c in 쓴 if "거칠기" in rs[c]["판본"].get(v, {})]
        return _st([P(c, v, k) - P(c, ceil, k) for c in sel]) if sel else "안 돌았다"
    Q["Q5"] = {"물음": "어느 판본이 격자 상한에 제일 가깝나 (거칠기 · 능선 남은 몫)",
               "거칠기": {v: 남은(v, "거칠기", "격자상한" if "@64" not in v else "격자상한@64")
                          for v in ("MC·불", "MC·연속", "FC·불", "FC·연속", "MC·불@64",
                                    "MC·연속@64", "FC·불@64", "FC·연속@64",
                                    "RFTA·불@64", "RFTA·연속@64")},
               "능선(정답과의 거리)": {
                   v: (_st([-abs(P(c, v, "능선") - P(c, "정답", "능선")) for c in 쓴]) if 있(v)
                       else "안 돌았다")
                   for v in ("MC·불", "MC·연속", "FC·불", "FC·연속", "격자상한", "MC·불@64",
                             "MC·연속@64", "FC·불@64", "FC·연속@64",
                             "RFTA·불@64", "RFTA·연속@64", "NDC·불@64")}}
    # 대조군
    Q["대조군"] = {
        "해상도(MC·연속 → 복셀)": _st(d("MC·연속→복셀", "MC·연속", "거칠기", 쓴)),
        "해상도(FC·연속 → 복셀)": _st(d("FC·연속→복셀", "FC·연속", "거칠기", 쓴)),
        "해상도(RFTA·연속 → 복셀)": (_st(d("RFTA·연속@64→복셀", "RFTA·연속@64", "거칠기", 쓴))
                                     if 있("RFTA·연속@64→복셀") else "안 돌았다"),
        "정보0(균일@MC·연속 − MC·연속)": _st([P(c, "균일@MC·연속", "거칠기") - P(c, "MC·연속", "거칠기")
                                             for c in 쓴 if "거칠기" in rs[c]["판본"].get("균일@MC·연속", {})])}
    v["Q"] = Q
    p = os.path.join(HERE, "out", "기록", "메시추출_%s.json" % time.strftime("%Y%m%d_%H%M"))
    json.dump(v, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("\n  %-18s %8s %7s %7s %7s %8s %8s" % ("판본(중앙)", "거칠기", "계단", "능선", "대각45", "iou128", "면"))
    for n in VARS:
        sel = [c for c in cs if n in rs[c]["판본"] and "거칠기" in rs[c]["판본"][n]]
        if not sel:
            continue
        md = lambda k: float(np.median([P(c, n, k) for c in sel]))
        print("  %-18s %8.3f %7.3f %7.3f %7.3f %8.3f %8d"
              % (n, md("거칠기"), md("계단"), md("능선"), md("대각45"), md("iou128"), md("면")))
    for k in ("Q1", "Q2", "Q3", "Q5"):
        print("\n  %s %s" % (k, json.dumps(Q[k], ensure_ascii=False)[:600]))
    print("\n  -> %s" % p)
    return v


# ── 그림 ─────────────────────────────────────────────────────────────────────

def 그림(cases=None, dst=None):
    from PIL import Image
    cs = [c for c in (cases or 도형들) if c in rows()]
    # RFTA·연속 은 칸이 빈다 — 우리 연속 장이 거리장이 아니라 RFTA 가 아예 안 돈다 (머리말 · 계획 8항).
    # 그 자리에 **RFTA·불** 을 둔다: 같은 불리언 장에서 MC·불 · FC·불 과 나란히 보라는 뜻이다
    cols = ("정답", "격자상한", "MC·불", "MC·연속", "FC·불", "FC·연속",
            "NDC·불@64", "RFTA·불@64")
    rs = []
    for c in cs:
        ts = []
        for n in cols:
            p = os.path.join(TILED, "%s__%s.png" % (c, n))
            ts.append(np.asarray(Image.open(p).convert("RGB")) if os.path.exists(p)
                      else np.full((300, 300, 3), 240, np.uint8))
        rs.append((c.replace("도형_", ""), ts))
    DC.grid(rs, cols, "메시 추출 — 같은 장에서 추출기를 바꾼다 (45° 명암 · 같은 빛 · 같은 틀)",
            "RFTA · NDC 는 64³ (RFTA 256³ = 1670만 점 · NDC 3D CNN 은 8GB 에 안 들어간다) · MC·FC·격자상한은 256³",
            dst or os.path.join(HERE, "out", "메시추출_도형.png"), S=300)


# ── 자가검사 ─────────────────────────────────────────────────────────────────

def selfcheck():
    # (gpytoolbox 는 다리에서만 쓴다)
    # 1. 래퍼가 기본 깎기를 **비트까지** 그대로 낸다
    H.register_sheets()
    c = "도형_상자"
    n0 = H.N
    H.N = 64
    try:
        masks, bs, plain, base, axes = gen_build(c)
        deps = {v: np.ones((W.RES, W.RES), np.float32) for v in W.VIEWS}
        vox, axes2, jf, jb = 깎기(masks, bs, deps)
        assert np.array_equal(vox, base), "래퍼가 기본 깎기와 다른 복셀을 냈다"
        assert jf.shape == (64, 64) and jf.dtype.kind == "f", "jf 가 실수 (x,z) 가 아니다 %s" % (jf.shape,)
        f = 연속장(plain, jf, jb)
        # **기둥꼴 도형에서는 jf 가 정수로 떨어진다.** `ellipse_depths` 가 정수 칸에서 hf 를 읽고
        # `carve_depth` 가 D(기둥 깊이)로 되돌리는데, 기둥꼴은 높이마다 D = 물건 전체 y 폭이라
        # 둘이 약분된다. 그래서 「연속 장」의 칸 아래 정보는 **높이마다 깊이가 변하는 도형에만** 있다
        # (상자·원기둥·L자 0% · 구 73% · 치마 72%). 자가검사는 구로 한다
        ms, bsp, pl, _, ax2 = gen_build("도형_구")
        _, _, jf2, _ = 깎기(ms, bsp, deps)
        비정수 = float((np.abs(jf2[pl.any(1)] - np.round(jf2[pl.any(1)])) > 1e-5).mean())
        assert 비정수 > 0.5, "구에서도 jf 가 정수다 (%.2f) — 실수 값을 못 꺼냈다" % 비정수
        # 2. 연속 장의 수준 0 면이 불리언 MC 와 **같은 물건**이다 (부피 10% 안)
        mb = C_.to_mesh(vox, axes)
        mf = mesh(H.mesh_from_field(f, axes))
        r = abs(mf.volume) / max(abs(mb.volume), 1e-12)
        assert 0.9 < r < 1.1, "연속 장 부피가 불리언과 %.2f 배 다르다" % r
        # 3. 격자 상한이 정답보다 거칠고 정답 쪽으로 간다 (상자: 능선이 커야)
        truth = trimesh.load(os.path.join(HERE, "out", "시트", c, "truth.glb"), force="mesh")
        ce = 격자상한(truth, axes)
        # **격자 상한에도 90° 모서리는 없다** — 정답 상자 능선 0.67 대 상한 0.00 (MC 가 SDF 를 보간해
        # 모서리를 깎아버린다). 그래서 능선은 어느 판본도 정답까지 못 간다 — Q5 가 그걸 싣는다.
        assert dihedral(ce)["평평"] > 0.9, "상자 격자 상한이 평평하지 않다 %s" % dihedral(ce)
        assert roughness(ce)["거칠기"] < roughness(mb)["거칠기"], "격자 상한이 기준선보다 거칠다"
    finally:
        H.N = n0
    # 4. RFTA 가 합성 구를 되찾는다 (부피 오차 < 2% · 닫힘) — 배관 2
    g = (np.arange(32) + 0.5) / 32 * 2 - 1
    cg = g[1] - g[0]
    Xa, Ya, Za = np.meshgrid(g, g, g, indexing="ij")
    ms = rfta(((0.3 - np.sqrt(Xa ** 2 + Ya ** 2 + Za ** 2)) / cg).astype(np.float32), (g, g, g))
    err = abs(ms.volume) / (4 / 3 * np.pi * 0.3 ** 3) - 1
    assert abs(err) < 0.02, "RFTA 가 합성 구를 %.1f%% 틀렸다" % (100 * err)
    # 4b. FlexiCubes 도 합성 구를 되찾는다 (반 칸 오프셋 확인 · 배관)
    g2 = (np.arange(64) + 0.5) / 64 * 2 - 1
    cell = g2[1] - g2[0]
    Xg, Yg, Zg = np.meshgrid(g2, g2, g2, indexing="ij")
    fs = ((0.3 - np.sqrt(Xg ** 2 + Yg ** 2 + Zg ** 2)) / cell).astype(np.float32)
    mf2 = flexicubes(fs, (g2, g2, g2))
    ef = abs(mf2.volume) / (4 / 3 * np.pi * 0.3 ** 3) - 1
    assert abs(ef) < 0.02, "FlexiCubes 가 합성 구를 %.1f%% 틀렸다 — 반 칸 오프셋" % (100 * ef)
    # 4c. NDC 눈금 — 답이 정확한 상자로. **중심이 MC 와 0.1 칸 안에서 맞아야** 좌표 규약이 맞는 것이다
    n2 = 64
    u2 = (np.arange(n2) + 0.5) / n2 * 2 - 1
    c2 = u2[1] - u2[0]
    vb = np.zeros((n2, n2, n2), bool)
    vb[16:48, 16:48, 12:52] = True
    mmc = mesh(H.mesh_from(vb, (u2, u2, u2)))
    mnd = ndc(vb, (u2, u2, u2))
    off = (mnd.bounds.mean(0) - mmc.bounds.mean(0)) / c2
    assert np.abs(off).max() < 0.1, "NDC 좌표 눈금이 %s 칸 어긋난다" % np.round(off, 3)
    안쪽 = float(((mmc.bounds[1] - mmc.bounds[0]) - (mnd.bounds[1] - mnd.bounds[0])).mean() / c2 / 2)
    # 5. binvox 변환기 왕복
    import tempfile
    vx = np.zeros((16, 16, 16), bool)
    vx[4:12, 4:12, 4:12] = True
    p = to_binvox(vx, os.path.join(tempfile.gettempdir(), "t.binvox"))
    raw = open(p, "rb").read()
    body = raw.split(b"data\n", 1)[1]
    back = np.repeat(np.frombuffer(body[0::2], np.uint8),
                     np.frombuffer(body[1::2], np.uint8)).reshape(16, 16, 16).astype(bool)
    assert np.array_equal(back, vx), "binvox 왕복이 깨졌다"
    print("  자가검사 통과 — 래퍼 비트동일 · jf 실수 · 연속/불리언 부피비 %.3f · 상자 상한 능선 %.2f"
          " · RFTA 구 %+.2f%% · FC 구 %+.2f%% · NDC 중심 %s 칸 (상자에서 양쪽 %.2f 칸 안쪽) · binvox 왕복"
          % (r, dihedral(ce)["능선"], 100 * err, 100 * ef, np.round(off, 3).tolist(), 안쪽))


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else "1"
    if a == "검사":
        selfcheck()
    elif a == "판정":
        verdict()
    elif a == "그림":
        그림()
        그림(list(실물4), os.path.join(HERE, "out", "메시추출_실물.png"))
    elif a == "실물":
        if "norfta" in sys.argv:
            globals()["RFTA_ON"] = False
        run(int(sys.argv[2]) if len(sys.argv) > 2 else 4, list(실물4))
    elif a == "뒤":
        # 뒤에서부터. 앞에서 도는 놈과 짝지어 돌리면 벽시계가 반이 된다 (둘 다 PROG 를 먼저 읽고 건너뛴다)
        run(int(sys.argv[2]) if len(sys.argv) > 2 else 11, list(reversed(도형들)))
    elif a in ("ndc", "rfta"):
        f = run_ndc if a == "ndc" else run_rfta
        f(int(sys.argv[2]) if len(sys.argv) > 2 else 11,
          list(실물4) if "실물" in sys.argv else
          list(reversed(도형들)) if "뒤" in sys.argv else
          도형들[len(도형들) // 2:] + 도형들[:len(도형들) // 2] if "가운데" in sys.argv else None)
    else:
        run(int(a))


if __name__ == "__main__":
    main()
