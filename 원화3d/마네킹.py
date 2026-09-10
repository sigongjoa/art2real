# -*- coding: utf-8 -*-
"""**중간 벤치 — 마네킹.** 기본도형과 실물 캐릭터 사이. 축은 **포즈**다.

    python 마네킹.py 그림        포즈별 마네킹을 한 장으로 -> out/마네킹.png (원본 메시만)
    python 마네킹.py smplx      받아둔 SMPL-X npz 를 펴서 glb 로 (있을 때만)
    python 마네킹.py 재기        **파이프라인을 태운다** -> out/마네킹벤치.png · out/마네킹.json

## 왜 가운데 칸이 필요한가

    기본도형(`도형.py`)   실패 모드를 하나씩. 왜 그 값인지 안다. 사람 형상이 아니다
    **마네킹**            실패 모드를 조합하되 **무엇을 조합했는지 안다**
    실물 29장(`대조.py`)  전부 섞여 있다. 왜 0.31 인지 갈라 말할 수 없다

## 포즈가 축인 이유

`도형.py` 가 보여준 것 — 기둥 둘이 **대각으로 서면 0.50, 나란히 서면 1.00** 이다.
같은 물건이 방향만으로 반토막 난다. 사람은 팔다리가 넷이라 이게 포즈마다 다르게 켜진다.

그래서 **같은 몸으로 자세만 바꿔** 잰다. 받아온 마네킹 일곱 개로는 이 비교가 안 된다 —
몸이 달라서 포즈 탓과 몸 탓이 안 갈린다.

나오는 값이 그냥 숫자가 아니라 **포즈 가이드**다. 원화 3판을 우리가 요구할 수 있는
사업이니 「이 포즈로 그려주시면 여기까지 나옵니다」가 곧 견적서 문장이 된다.

## SMPL-X 는 대조군이지 기준이 아니다

**라이선스가 비상업 연구 전용**이다 (상업은 별도 계약). 이 저장소는 상업 사업이므로
**SMPL-X 로 잰 값은 참고용 대조군**으로만 쓰고, 얼린 벤치의 케이스로는 안 넣는다.
쓰는 목적은 하나 — **우리가 조립한 마네킹이 진짜 인체 비례에서 얼마나 벗어나나**.
"""
import os
import sys

import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# 사람 비례 (키 1 기준). 8등신이 아니라 **7.5등신 실측 근사**
HEAD, NECK, TORSO = 0.13, 0.04, 0.32
UPPER, LOWER = 0.16, 0.15                        # 팔 위·아래
THIGH, SHIN = 0.24, 0.23
SHOULDER, HIP = 0.19, 0.10                       # 반너비


def _cyl(r, h, a=(0, 0, 0), b=(0, 0, 1)):
    """a 에서 b 로 가는 원기둥."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    v = b - a
    L = np.linalg.norm(v)
    m = trimesh.creation.cylinder(radius=r, height=max(L, 1e-6), sections=24)
    if L > 1e-9:
        m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], v / L))
    m.apply_translation((a + b) / 2)
    return m


def mannequin(arm=(20, 0), leg=0, arm_fb=(0, 0), skirt=False, sword=False):
    """블록아웃 마네킹. **각도는 도(度)** — arm=(좌,우) 벌림, arm_fb=(좌,우) 앞뒤, leg 벌림."""
    z0 = 0.0
    hip_z = SHIN + THIGH
    sh_z = hip_z + TORSO
    parts = [trimesh.creation.box((0.22, 0.13, TORSO)),
             trimesh.creation.icosphere(subdivisions=3, radius=HEAD / 2)]
    parts[0].apply_translation([0, 0, hip_z + TORSO / 2])
    parts[1].apply_translation([0, 0, sh_z + NECK + HEAD / 2])
    parts.append(_cyl(0.035, NECK, (0, 0, sh_z), (0, 0, sh_z + NECK)))
    for s, (out_deg, fb_deg) in zip((-1, 1), zip(arm, arm_fb)):
        o, f = np.radians(out_deg), np.radians(fb_deg)
        top = np.array([s * SHOULDER * 0.55, 0, sh_z])
        d = np.array([s * np.sin(o), np.sin(f), -np.cos(o) * np.cos(f)])
        d /= np.linalg.norm(d)
        elb = top + d * UPPER
        hand = elb + d * LOWER
        parts += [_cyl(0.045, 0, top, elb), _cyl(0.038, 0, elb, hand)]
    for s in (-1, 1):
        o = np.radians(leg)
        top = np.array([s * HIP, 0, hip_z])
        d = np.array([s * np.sin(o), 0, -np.cos(o)])
        knee = top + d * THIGH
        foot = knee + d * SHIN
        parts += [_cyl(0.062, 0, top, knee), _cyl(0.052, 0, knee, foot)]
    if skirt:                                    # 속 빈 원뿔 — `도형.py` 의 치마와 같은 성질
        prof = np.array([[0.30, hip_z - 0.22], [0.10, hip_z + 0.06], [0.125, hip_z + 0.06],
                         [0.325, hip_z - 0.22], [0.30, hip_z - 0.22]])
        sk = trimesh.creation.revolve(prof, sections=64)
        if sk.volume < 0:
            sk.invert()
        parts.append(sk)
    if sword:                                    # **떨어진 부품.** to_mesh 가 조각을 버리면 여기서 걸린다
        s = trimesh.creation.box((0.03, 0.03, 0.55))
        s.apply_translation([0.30, 0.12, hip_z + 0.10])
        parts.append(s)
    m = trimesh.util.concatenate(parts)
    m.apply_translation([0, 0, -m.bounds[0][2] + z0])
    return m


POSES = [
    ("차렷",     dict(arm=(8, 8), leg=0), "기준 — 팔다리가 몸에 붙어 있다"),
    ("A포즈",    dict(arm=(35, 35), leg=6), "팔이 떨어지며 겨드랑이 오목부가 생긴다"),
    ("T포즈",    dict(arm=(85, 85), leg=0), "게임 에셋 기본 자세"),
    ("다리벌림", dict(arm=(20, 20), leg=28), "**유령 덩어리** — 두기둥대각이 사람이 된 것"),
    ("팔앞뒤",   dict(arm=(25, 25), arm_fb=(45, -45)), "**3판 최악** — 깊이축에 정보가 없다"),
    ("치마",     dict(arm=(20, 20), leg=8, skirt=True), "속 빈 원뿔이 몸에 붙으면"),
    ("검들기",   dict(arm=(20, 45), leg=6, sword=True), "**떨어진 부품**이 살아남나"),
]


def smplx_mesh(npz, betas=None, body_pose=None):
    """받아둔 SMPL-X npz 를 **numpy 로만** 편다 (`smplx` 패키지는 torch 를 끌고 온다).

    선형 블렌드 스키닝 그대로다 — 체형 -> 관절 -> 포즈 보정 -> 스키닝."""
    d = np.load(npz, allow_pickle=True)
    V = np.asarray(d["v_template"], np.float64)
    F = np.asarray(d["f"], np.int64)
    SD = np.asarray(d["shapedirs"], np.float64)
    PD = np.asarray(d["posedirs"], np.float64)
    JR = np.asarray(d["J_regressor"], np.float64)
    W = np.asarray(d["weights"], np.float64)
    kin = np.asarray(d["kintree_table"], np.int64)[0]
    K = SD.shape[2]
    b = np.zeros(K)
    if betas is not None:
        b[:len(betas)] = betas
    V = (V.reshape(-1) + SD.reshape(-1, K) @ b).reshape(-1, 3)
    J = JR @ V
    nj = J.shape[0]
    pose = np.zeros((nj, 3))
    if body_pose is not None:
        pose[1:1 + len(body_pose)] = body_pose

    def rod(r):
        t = np.linalg.norm(r)
        if t < 1e-9:
            return np.eye(3)
        k = r / t
        K_ = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        return np.eye(3) + np.sin(t) * K_ + (1 - np.cos(t)) * K_ @ K_

    R = np.stack([rod(p) for p in pose])
    feat = (R[1:] - np.eye(3)).reshape(-1)
    V = V + (PD.reshape(-1, feat.shape[0]) @ feat).reshape(-1, 3)
    A = np.zeros((nj, 4, 4))
    for i in range(nj):
        T = np.eye(4)
        T[:3, :3] = R[i]
        T[:3, 3] = J[i] - (J[kin[i]] if i else 0)
        A[i] = T if i == 0 else A[kin[i]] @ T
    for i in range(nj):                          # 쉼 자세를 빼서 「움직인 양」만 남긴다
        A[i][:3, 3] -= A[i][:3, :3] @ J[i]
    T = np.einsum("vj,jab->vab", W, A)
    Vh = np.concatenate([V, np.ones((len(V), 1))], 1)
    V = np.einsum("vab,vb->va", T, Vh)[:, :3]
    return trimesh.Trimesh(V, F, process=False)


def _find_smplx():
    for root in (os.path.join(OUT, "smplx"), os.path.expanduser("~/Downloads")):
        for dp, _, fs in os.walk(root) if os.path.isdir(root) else []:
            for f in fs:
                if f.startswith("SMPLX_NEUTRAL") and f.endswith(".npz"):
                    return os.path.join(dp, f)
    return None


def 그림(extra=None):
    """포즈별 마네킹을 3/4 각도 깊이색으로 한 장. 파이프라인을 안 태운 **원본 메시**다."""
    import 각도 as ANG
    import 정답 as J
    from 계획 import _font
    from PIL import Image, ImageDraw
    items = [(n, mannequin(**kw), why) for n, kw, why in POSES]
    if extra:
        items.append(extra)
    R, PER = 250, 4
    rows = (len(items) + PER - 1) // PER
    im = Image.new("RGB", (PER * (R + 14) + 14, 76 + rows * (R + 46)), "white")
    g = ImageDraw.Draw(im)
    g.text((18, 16), "마네킹 벤치 — 같은 몸, 자세만 바꾼다", font=_font(21), fill=(20, 20, 20))
    g.text((18, 46), "3/4 각도 깊이색 · 파랑 멀다 -> 빨강 가깝다", font=_font(12), fill=(120, 120, 120))
    for i, (name, m, why) in enumerate(items):
        v, _ = J.grid(m, J.PITCH / 2)
        s = int(max(v.shape[0], v.shape[2]) * 1.06)   # 여백 6% — 팔다리가 테두리에 붙는다
        pad = np.zeros((s, v.shape[1], s), bool)
        ox, oz = (s - v.shape[0]) // 2, (s - v.shape[2]) // 2
        pad[ox:ox + v.shape[0], :, oz:oz + v.shape[2]] = v
        d, hit = ANG.depth(pad, 35)
        x, y = 14 + (i % PER) * (R + 14), 76 + (i // PER) * (R + 46)
        im.paste(ANG.paint(d, hit, R, (d[hit].min(), d[hit].max())), (x, y))
        g.rectangle([x, y, x + R - 1, y + R - 1], outline=(220, 220, 220))
        g.text((x, y + R + 6), name, font=_font(14), fill=(20, 20, 20))
        g.text((x, y + R + 24), why.replace("**", "")[:30], font=_font(10), fill=(150, 150, 150))
    im.save(os.path.join(OUT, "마네킹.png"))
    print("  -> out/마네킹.png")


def _bake(name, mesh):
    """Y-up glb 로 굽고 시트·깊이까지. (`시트.py` 가 glTF Y-up 을 가정한다)"""
    import subprocess
    case = "마네킹_" + name
    d = os.path.join(OUT, "모델")
    os.makedirs(d, exist_ok=True)
    glb = os.path.join(d, case + ".glb")
    if not os.path.exists(glb):
        m = mesh.copy()
        if not name.startswith("SMPL"):          # 조립 마네킹은 z 가 위라 눕혀 내보낸다
            m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        m.visual = trimesh.visual.ColorVisuals(
            m, face_colors=np.full((len(m.faces), 4), 210, np.uint8))
        trimesh.Scene(m).export(glb)
    if not os.path.exists(os.path.join(OUT, "시트", case, "truth.glb")):
        print("  판 뽑기 %s" % case)
        r = subprocess.run([sys.executable, os.path.join(HERE, "시트.py"), glb, "--이름", case],
                           cwd=HERE, capture_output=True, text=True, encoding="utf-8")
        if r.returncode:
            print("     실패: %s" % (r.stderr or "")[-200:])
    if not os.path.exists(os.path.join(OUT, "깊이", case, "front", "depth.npy")):
        subprocess.run([sys.executable, os.path.join(HERE, "깊이.py"), case],
                       cwd=HERE, capture_output=True)
    return case


def 재기():
    """포즈마다 **오라클(천장)과 파이프라인**을 잰다. 이게 포즈 가이드의 숫자다."""
    import json
    import hull as H
    import 대조 as C
    import 도형 as SH
    import 정답 as J
    from 계획 import _font
    from PIL import Image, ImageDraw
    # **SMPL-X 는 여기 안 넣는다.** 비상업 연구 전용이라 벤치 케이스가 될 수 없고,
    # 쓰임은 `python 마네킹.py smplx` 의 그림 한 칸(비례 대조군)으로 끝이다.
    items = [(n, mannequin(**kw), why) for n, kw, why in POSES]
    for n, m, _ in items:
        _bake(n, m)
    H.register_sheets()

    rows, tiles = [], []
    print("  %-10s %8s %8s %8s %8s  %s" % ("포즈", "오라클", "이진", "깊이", "파이프차", "무엇이 켜지나"))
    for name, mesh, why in items:
        case = "마네킹_" + name
        if case not in H.CASES:
            print("  %-10s 판이 없다 — 건너뜀" % name); continue
        t = trimesh.load(os.path.join(OUT, "시트", case, "truth.glb"), force="mesh")
        orc = SH.oracle(t)
        plain, deep, axes, _ = C.build(case)
        T, ot = J.grid(t)
        got = {}
        for tag, vox in (("이진", plain), ("깊이", deep)):
            G, og = J.grid(C.to_mesh(vox, axes))
            A, B = J.common(T, ot, G, og)
            got[tag] = float((A & B).sum() / max((A | B).sum(), 1))
        rows.append({"pose": name, "오라클": round(orc, 4), "이진_iou": round(got["이진"], 4),
                     "깊이_iou": round(got["깊이"], 4),
                     "파이프차": round(got["이진"] - orc, 4), "왜": why})
        tiles.append((name, SH._paint3(case, plain, deep, axes)))
        print("  %-10s %8.4f %8.4f %8.4f %+8.4f  %s"
              % (name, orc, got["이진"], got["깊이"], got["이진"] - orc, why.replace("**", "")[:30]))
    json.dump(rows, open(os.path.join(OUT, "마네킹.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    R2 = SH.R
    im = Image.new("RGB", (3 * R2 + 430, 96 + len(tiles) * (R2 + 26) + 40), "white")
    g = ImageDraw.Draw(im)
    g.text((22, 18), "마네킹 벤치 — 같은 몸, 자세만 바꾼다", font=_font(22), fill=(20, 20, 20))
    g.text((22, 50), "오라클 = 3판이 담을 수 있는 천장 · 잰 값 = 파이프라인",
           font=_font(12), fill=(120, 120, 120))
    for i, (name, three) in enumerate(tiles):
        r, y = rows[i], 96 + i * (R2 + 26)
        g.text((22, y + 4), name, font=_font(16), fill=(20, 20, 20))
        g.text((22, y + 30), "천장  %.4f" % r["오라클"], font=_font(12), fill=(60, 60, 60))
        g.text((22, y + 50), "이진  %.4f" % r["이진_iou"], font=_font(13), fill=(20, 20, 20))
        g.text((22, y + 70), "깊이  %.4f" % r["깊이_iou"], font=_font(12), fill=(90, 90, 90))
        g.text((22, y + 94), r["왜"].replace("**", "")[:26], font=_font(10), fill=(150, 150, 150))
        for k, tl in enumerate(three):
            x = 400 + k * (R2 + 10)
            im.paste(tl, (x, y))
            g.rectangle([x, y, x + R2 - 1, y + R2 - 1], outline=(220, 220, 220))
            if i == 0:
                g.text((x, y - 16), ("정답", "이진 hull", "깊이 깎기")[k], font=_font(12),
                       fill=(90, 90, 90))
    im.save(os.path.join(OUT, "마네킹벤치.png"))
    print("  -> out/마네킹벤치.png · out/마네킹.json")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "그림"
    if cmd == "smplx":
        p = _find_smplx()
        if not p:
            print("  SMPLX_NEUTRAL*.npz 를 못 찾았다. out/smplx/ 나 ~/Downloads 에 풀 것")
            raise SystemExit(1)
        print("  %s" % p)
        m = smplx_mesh(p)
        print("  정점 %d · 면 %d · 키 %.3f m" % (len(m.vertices), len(m.faces), m.extents[1]))
        os.makedirs(os.path.join(OUT, "모델"), exist_ok=True)
        m.export(os.path.join(OUT, "모델", "smplx_neutral.glb"))   # **Y-up 그대로** — 시트.py 가 그렇게 읽는다
        z = m.copy()                                   # 그림은 창 규약(z 가 위)이라 돌려서 그린다
        z.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        그림(("SMPL-X (참고)", z, "비상업 연구 전용 — 대조군으로만"))
    elif cmd == "재기":
        재기()
    elif cmd == "그림":
        그림()
    else:
        print(__doc__)
