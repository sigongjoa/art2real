# -*- coding: utf-8 -*-
"""손으로 짓는 부품. 지금은 +x 어깨 견갑 하나.

    "D:/Program Files/Blender Foundation/Blender 4.0/blender.exe" -b --python build.py -- out/pauldron.blend

부품 하나 = 함수 하나. 파라미터는 전부 위쪽 상수로 빼 둔다 —
좌표를 메시에 굽지 말고 매번 원본에서 계산한다 (LESSONS 27).

좌표는 trail4 정규화 공간 그대로다: z=0 접지, z=1 정수리, x=0 중심선, y=0 허리, 앞이 -y.
"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 노브 (실측이 아닌 것은 전부 여기에. 실측인 척하지 않는다) ----
# y 방향 단면 개수. 5 는 큰 갑판, 15 는 골판지 (LESSONS 64). 눈이 고른 쪽은 5 다.
STATIONS = int(os.environ.get("STATIONS", 5))
# 셰이딩 — 하드서피스 CG 의 표준 조합은 오토스무스(각도) + 베벨 + 가중 노멀이다.
# 플랫/스무스 이분법은 조잡하다. 전부 환경변수 노브로 둔다.
# stack 11단은 flat 이면 층층이 계단으로 보인다. auto 30 이면 얕은 층은 녹고
# 진짜 모서리만 남는다. 45 는 베개가 된다 (LESSONS 65·75)
SHADE = os.environ.get("SHADE", "auto")            # flat | auto | smooth
SHADE_ANGLE = float(os.environ.get("SHADE_ANGLE", 30))   # auto 일 때 이 각 넘으면 하드 엣지
BEVEL = float(os.environ.get("BEVEL", 0))          # 모서리 챔퍼 폭 (0 = 끔). 부품 폭이 ~0.10 이다
BEVEL_SEG = int(os.environ.get("BEVEL_SEG", 2))
WN = os.environ.get("WN") == "1"                   # 가중 노멀 — 베벨 친 하드서피스의 짝
SUBD = int(os.environ.get("SUBD", 0))              # 섭디비전 레벨 (0 = 끔)
BUILDER = os.environ.get("BUILDER", "stack")   # stack | loft. loft 는 아몬드가 된다(기각)
# z 로 쌓는 단면 수. 실루엣 IoU 가 5:0.752 / 7:0.827 / 11:0.891 / 17:0.896 — 11에서 포화한다
STACK_N = int(os.environ.get("STACK_N", 11))
STACK_SEG = int(os.environ.get("STACK_SEG", 12))   # 단면 분할
# 초타원 지수. 2=타원, 크면 사각. **실루엣 지표로는 절대 못 고른다** —
# 축 정렬 투영은 지수와 무관하게 같은 bbox 를 채운다(2.5/3.5/6.0 이 소수점까지 같았다).
# 3/4 뷰와 명암에서만 드러나니 눈으로 고를 것.
Z_INSET = float(os.environ.get("Z_INSET", 0.05))   # 위아래 끝을 높이의 이만큼 물려서 자른다
THICK = float(os.environ.get("THICK", 0.008))   # 껍질 두께. 실측 아님 — 원화에 단면이 안 보인다
SUPER_N = float(os.environ.get("SUPER_N", 3.5))
GROOVE_AT = 2       # 테두리 밴드를 만드는 고리 번호 (앞에서 셋째)
GROOVE_S = 0.90     # 그 고리를 얼마나 조일지. 셀에서 선 하나로 읽히는 홈
END_S = 0.55        # 앞/뒤 끝단면이 줄어드는 비율
HORN_SIDES = 8      # 뿔 원뿔 분할. 셀에서는 적을수록 면이 읽힌다
LAVENDER = (0.52, 0.52, 0.70, 1)
GOLD = (0.84, 0.71, 0.30, 1)


def span_at(poly, t):
    """폴리곤을 세로선 u=t 로 잘라 [min,max] 를 낸다. 없으면 None."""
    hits = []
    n = len(poly)
    for i in range(n):
        (a0, b0), (a1, b1) = poly[i], poly[(i + 1) % n]
        if (a0 - t) * (a1 - t) > 0 or a0 == a1:
            continue
        hits.append(b0 + (b1 - b0) * (t - a0) / (a1 - a0))
    return (min(hits), max(hits)) if len(hits) >= 2 else None


def new_mesh(name, verts, faces, color, mat_name, uvs=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    # UV 는 언랩기에 맡기지 않고 **지을 때 같이 쓴다.** 로프트는 원기둥이라
    # u=고리 둘레, v=단면 번호 로 두면 섬 1개에 왜곡이 없다.
    # 스마트 언랩에 맡기면 각진 면마다 쪼개 262면을 섬 56개로 만든다.
    if uvs:
        uvl = me.uv_layers.new(name="UVMap")
        k = 0
        for fi, poly in enumerate(me.polygons):
            for j in range(poly.loop_total):
                uvl.data[poly.loop_start + j].uv = uvs[fi][j]
            k += 1
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.45
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = SHADE != "flat"
    if SHADE == "auto":
        # 4.0 문법이다. 4.1 에서 use_auto_smooth 가 없어졌다 (LESSONS 6)
        me.use_auto_smooth = True
        me.auto_smooth_angle = math.radians(SHADE_ANGLE)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    # 손으로 굽지 말고 모디파이어를 써라 (LESSONS 9) — 되돌릴 수 있게 스택으로 둔다
    if BEVEL > 0:
        b = ob.modifiers.new("bevel", 'BEVEL')
        b.width = BEVEL
        b.segments = BEVEL_SEG
        b.limit_method = 'ANGLE'
        b.angle_limit = math.radians(25)
        b.harden_normals = WN
    if SUBD > 0:
        sd = ob.modifiers.new("subd", 'SUBSURF')
        sd.levels = sd.render_levels = SUBD
    if WN:
        ob.modifiers.new("wn", 'WEIGHTED_NORMAL')
    return ob


def spans_at_z(poly, z):
    """폴리곤을 가로선 z 로 잘라 [min,max]. 실루엣이 주는 건 이 바깥 봉투다."""
    hits = []
    n = len(poly)
    for i in range(n):
        (a0, b0), (a1, b1) = poly[i], poly[(i + 1) % n]
        if (b0 - z) * (b1 - z) > 0 or b0 == b1:
            continue
        hits.append(a0 + (a1 - a0) * (z - b0) / (b1 - b0))
    return (min(hits), max(hits)) if len(hits) >= 2 else None


def stack(fp, sp, levels=STACK_N, seg=STACK_SEG, n=SUPER_N, zlist=None):
    """**두 원화가 실제로 정하는 것**을 짓는다 — 높이마다 정면이 폭을, 측면이 깊이를 준다.

    y 로 로프트하면 측면 윤곽의 양 끝(=점)이 단면 배율이 되어 아몬드가 된다.
    닫힌 윤곽은 bbox 끝에서 무조건 0으로 수렴하니 그건 형태가 아니라 표본 오류다.

    대신 z 를 따라 쌓는다. 각 높이에서
        x 범위는 정면 실루엣이,  y 범위는 측면 실루엣이 준다
    단면은 초타원 |x/a|^n + |y/b|^n = 1 (n=1 마름모, 2 타원, 큰 n 사각형).
    갑주는 모서리가 둥근 판이라 n=3~4 가 맞다.
    실루엣은 "정의로 맞는" 게 아니다 — 단면 사이를 직선으로 이으니 곡률이 깎인다.
    11단에서 정면 0.891 / 측면 0.888 로 포화한다 (로프트는 0.872 / 0.797 이었다).
    """
    zs = [p[1] for p in fp]
    z0, z1 = min(zs), max(zs)
    # 닫힌 윤곽은 z 최솟/최댓값에서 폭이 0 으로 수렴한다(0.8079 에서 0.0005,
    # 한 칸 위 0.8186 에서 0.0754). 그 점을 단면으로 쓰면 아래가 바늘구멍이 된다.
    # 그렇다고 z 범위를 잘라내면 **높이가 짧아진다**(겹침에서 바닥에 빨간 띠가 남았다).
    # 높이는 그대로 두고 **재는 높이만** 물린다 — 아래위 끝이 수직 치마가 된다.
    h = z1 - z0
    zs_lo, zs_hi = z0 + h * Z_INSET, z1 - h * Z_INSET
    # zlist 가 있으면 **원화가 선을 그은 높이**에 고리를 놓는다 (70번). 없으면 균일하게.
    if zlist:
        key = sorted(set([z0] + [z for z in zlist if z0 < z < z1] + [z1]))
        zpos = []
        for a, b in zip(key[:-1], key[1:]):
            zpos.append(a)
            if b - a > h * 0.22:                   # 능선 사이가 넓으면 한 칸 채운다
                zpos.append((a + b) / 2)
        zpos.append(key[-1])
    else:
        zpos = [z0 + h * k / (levels - 1) for k in range(levels)]
    rings, prof = [], []
    for k, z in enumerate(zpos):
        zc = min(max(z, zs_lo), zs_hi)             # 폭·깊이를 **재는** 높이 (끝만 물린다)
        fx = spans_at_z(fp, zc)
        sy = spans_at_z(sp, zc)
        if not fx or not sy:
            continue
        cx, ax = (fx[0] + fx[1]) / 2, (fx[1] - fx[0]) / 2
        cy, ay = (sy[0] + sy[1]) / 2, (sy[1] - sy[0]) / 2
        ring = []
        for j in range(seg):
            t = 2 * math.pi * j / seg
            ct, st = math.cos(t), math.sin(t)
            # 초타원의 매개화. 부호는 살리고 크기만 지수로 눌러 모서리를 만든다
            ring.append((cx + ax * math.copysign(abs(ct) ** (2.0 / n), ct),
                         cy + ay * math.copysign(abs(st) ** (2.0 / n), st),
                         z))
        rings.append(ring)
        prof.append((z, ax, ay))
    return rings, prof


def bridge(rings, caps=(True, True)):
    """고리 N 개를 사각면으로 잇는다. caps 로 양 끝을 막을지 고른다. UV 도 같이 낸다.

    UV 를 **번호**(i/m, k/n)로 주면 안 된다 — 고리 둘레와 고리 간격이 변하는 만큼
    면적비가 튀어 왜곡이 3.4 가 나온다. u 는 둘레 호 길이, v 는 고리 사이 실제 거리로 준다.
    그리고 끝 고리는 둘레가 짧으니 **UV 에서도 좁게** 만든다 (직사각형을 고집하지 않는다).
    """
    m, n = len(rings[0]), len(rings)
    verts, faces, uvs = [], [], []
    for ring in rings:
        verts.extend(ring)

    def seg(r, i):
        return (Vector(r[i]) - Vector(r[(i + 1) % m])).length

    peri = [sum(seg(r, i) for i in range(m)) for r in rings]
    mean_p = sum(peri) / n
    # u: 평균 고리의 누적 호 길이 (모든 고리가 같은 u 를 써야 사각면이 안 꼬인다)
    mean_seg = [sum(seg(r, i) for r in rings) / n for i in range(m)]
    cum, acc = [0.0], 0.0
    for i in range(m):
        acc += mean_seg[i]
        cum.append(acc / sum(mean_seg))
    # v: 고리 중심 사이 실제 거리 누적
    cen = [Vector((sum(p[0] for p in r) / m, sum(p[1] for p in r) / m, sum(p[2] for p in r) / m))
           for r in rings]
    dv, tot = [0.0], 0.0
    for k in range(n - 1):
        tot += (cen[k + 1] - cen[k]).length
        dv.append(tot)
    # UV 를 **3D 거리 단위**로 낸다. 0~1 로 정규화하는 건 마지막 layout() 이 한 번에 한다.
    # 오브젝트마다 제 0~1 을 쓰면 섬이 겹치고 텍셀 밀도가 2.4배 갈린다.
    def u_of(k, i):
        return (cum[i] - 0.5) * peri[k]

    for k in range(n - 1):
        a, b = k * m, (k + 1) * m
        for i in range(m):
            j = (i + 1) % m
            faces.append([a + i, a + j, b + j, b + i])
            uvs.append([(u_of(k, i), dv[k]), (u_of(k, i + 1), dv[k]),
                        (u_of(k + 1, i + 1), dv[k + 1]), (u_of(k + 1, i), dv[k + 1])])
    band_w = max(peri)
    # 양 끝 뚜껑. 반지름은 그 고리의 실제 반지름 (3D 단위 그대로)
    for slot, pi in enumerate((0, n - 1)):
        if not caps[slot]:
            continue
        rad = peri[pi] / (2 * math.pi)
        cx = -band_w / 2 + rad + slot * (band_w / 2 + rad)
        cy = tot + rad * 1.15
        faces.append(list(range(m))[::-1] if pi == 0 else [pi * m + i for i in range(m)])
        uvs.append([(cx + rad * math.cos(2 * math.pi * cum[i]),
                     cy + rad * math.sin(2 * math.pi * cum[i])) for i in range(m)])
    return verts, faces, uvs


def cone(root, tip, radius, sides=HORN_SIDES):
    """뿌리에서 끝으로 가는 원뿔. 뿌리는 캡 안으로 조금 파묻는다."""
    root, tip = Vector(root), Vector(tip)
    axis = tip - root
    L = axis.length
    axis = axis.normalized()
    # 뿌리를 캡 속에 묻되 **반지름도 같은 비율로 키운다**.
    # 안 키우면 실측 뿌리 자리의 굵기가 measured r 보다 얇아져 뿔이 바늘이 된다.
    sink = 0.25
    root = root - axis * (L * sink)
    radius *= 1 + sink
    up = Vector((0, 0, 1))
    if abs(axis.dot(up)) > 0.95:
        up = Vector((1, 0, 0))
    e0 = axis.cross(up).normalized()
    e1 = axis.cross(e0).normalized()
    verts = [root + (e0 * math.cos(a) + e1 * math.sin(a)) * radius
             for a in (2 * math.pi * i / sides for i in range(sides))]
    verts.append(tip)
    faces = [[i, (i + 1) % sides, sides] for i in range(sides)]
    # 원뿔은 **부채꼴**로 편다. 온전한 원으로 펴면 둘레가 늘어나 왜곡이 3.4 가 된다.
    #   모선 L = sqrt(r^2 + h^2),  펼친 부채꼴 각 PHI = 2*pi*r/L
    # 끝점에 삼각형마다 다른 UV 를 주면 뿔 하나가 섬 8개로 갈라진다. 끝점은 하나여야 한다.
    h = (tip - root).length
    L = math.hypot(radius, h)
    PHI = 2 * math.pi * radius / L
    ap = (0.0, 0.0)                                  # UV 도 3D 거리 단위. 배치는 layout() 이 한다
    ang = lambda i: -PHI / 2 + PHI * i / sides
    arc = lambda i: (L * math.cos(ang(i)), L * math.sin(ang(i)))
    uvs = [[arc(i), arc(i + 1), ap] for i in range(sides)]
    # 밑뚜껑은 만들지 않는다. 뿌리를 캡 속에 25% 묻어 두니 **보이지 않는 면**인데
    # 섬 하나씩(합쳐 4개)을 먹고 있었다. 안 보이는 면에 UV 를 주지 않는다.
    return verts, faces, uvs


def shell(verts, faces, uvs, t=THICK):
    """열린 껍질에 두께를 준다 (bmesh solidify). 굽기·UV 가 실제 기하를 봐야 해서 적용한다.

    두께는 실측이 아니다 — 원화에 껍질 단면이 안 보인다. 노브다.
    """
    bm = bmesh.new()
    vs = [bm.verts.new(tuple(v)) for v in verts]
    bm.verts.index_update()
    for f in faces:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    bm.faces.index_update()
    # 원본 면에 표를 달아 둔다. solidify 뒤에 인덱스로는 구분이 안 된다
    tag = bm.faces.layers.int.new("orig")
    for f in bm.faces:
        f[tag] = f.index + 1
    # **법선부터 맞춘다.** 내 면 감김이 옆면과 뚜껑에서 달라 절반이 안쪽을 봤고,
    # 그 상태로 solidify 하니 두께가 반은 밖으로 나가 실루엣이 0.008 부풀었다.
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    # 부호는 실측으로 정했다. -t 는 바깥으로 나가 실루엣이 0.008 부풀고(x 0.1239..0.2379),
    # +t 는 바깥면을 그대로 두고 안쪽으로만 두꺼워진다(0.1320..0.2294, 원화 0.1320..0.2305).
    res = bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=t)
    # 태그(int 레이어)는 solidify 가 **복사한다** — 안쪽 면이 같은 표를 달고 나와
    # 같은 UV 를 물려받아 바깥면 텍셀을 덮어썼다(원화를 읽은 면 107 -> 32).
    # 새로 생긴 면은 반환값에서 직접 받는다.
    made = {f.index for f in res["geom"] if isinstance(f, bmesh.types.BMFace)}
    bm.verts.index_update()
    bm.faces.index_update()
    nv = [tuple(v.co) for v in bm.verts]
    nf, nu = [], []
    for f in bm.faces:
        idx = [v.index for v in f.verts]
        nf.append(idx)
        o = f[tag] - 1
        if f.index not in made and 0 <= o < len(uvs) and len(uvs[o]) == len(idx):
            nu.append(list(uvs[o]))
        else:
            # 안쪽면·테두리는 거의 안 보인다. **바깥면의 한 점으로 접는다** —
            # 면적이 0 이라 텍셀을 안 먹고, bbox 밖(-0.02)에 두면 layout 이 판 전체를
            # 그만큼 늘려 진짜 섬이 줄어든다 (원화를 읽은 면이 107 -> 32 로 떨어졌었다)
            nu.append([uvs[0][0]] * len(idx))
    bm.free()
    return nv, nf, nu


def horn_tilt(root_xz, tip_xz, y, L0, tilt_deg, r0, sign=1.0, seg=HORN_SIDES, nsta=7):
    """뿔을 **기울어진 곧은 원뿔**로 짓는다.

    폭 프로파일을 그대로 쌓으면 단축(foreshortening)을 형태로 굳힌다 —
    소켓 뿔이 물방울로 나온 게 그거다. 뿔 넷의 r/L 이 0.251/0.265/0.291 로 거의 같고
    (반각 14~16도) 3번만 0.500 인데, 그건 굵어서가 아니라 60도 기울어 짧아 보이는 것이다.

        참 길이 L0 = r0 / tan(alpha),  cos(theta) = 보이는 L / L0

    부호(앞/뒤)는 정면 한 장으로 못 정한다 — sign 이 노브다.
    """
    root = Vector((root_xz[0], y, root_xz[1]))
    tipf = Vector((tip_xz[0], y, tip_xz[1]))
    d = tipf - root
    Lf = d.length
    if Lf < 1e-9:
        return None
    u = (d / Lf)
    dy = L0 * math.sin(math.radians(tilt_deg)) * sign
    tip = root + u * Lf + Vector((0, dy, 0))
    ax = (tip - root).normalized()
    up = Vector((0, 1, 0))
    if abs(ax.dot(up)) > 0.95:
        up = Vector((1, 0, 0))
    e0 = ax.cross(up).normalized()
    e1 = ax.cross(e0).normalized()
    verts, faces, uvs = [], [], []
    rings = []
    for k in range(nsta):
        t = k / (nsta - 1)
        c = root + (tip - root) * t
        r = max(r0 * (1 - t), 1e-5)
        rings.append([c + (e0 * math.cos(a) + e1 * math.sin(a)) * r
                      for a in (2 * math.pi * i / seg for i in range(seg))])
    for ring in rings:
        verts.extend([tuple(v) for v in ring])
    for k in range(nsta - 1):
        a, b = k * seg, (k + 1) * seg
        v0, v1 = L0 * k / (nsta - 1), L0 * (k + 1) / (nsta - 1)
        c0, c1 = 2 * math.pi * max(r0 * (1 - k / (nsta - 1)), 1e-5), 2 * math.pi * max(r0 * (1 - (k + 1) / (nsta - 1)), 1e-5)
        for i in range(seg):
            j = (i + 1) % seg
            faces.append([a + i, a + j, b + j, b + i])
            uvs.append([((i / seg - .5) * c0, v0), (((i + 1) / seg - .5) * c0, v0),
                        (((i + 1) / seg - .5) * c1, v1), ((i / seg - .5) * c1, v1)])
    faces.append(list(range(seg))[::-1])
    uvs.append([(r0 * math.cos(2 * math.pi * i / seg), -r0 * 1.3 + r0 * math.sin(2 * math.pi * i / seg))
                for i in range(seg)])
    return verts, faces, uvs


def horn_profile(root_xz, tip_xz, y, half, seg=HORN_SIDES):
    """뿔을 **폭 프로파일**로 짓는다 — PCA 반지름 하나가 아니라.

    horns.py 가 축을 따라 N 지점에서 잰 반폭을 준다. 소켓 뿔은
    0.0087 -> 0.0125 -> 0.0018 로 **부풀었다 줄어드는 물방울**인데
    반지름 하나로는 그게 안 담긴다. 단면을 그 반폭으로 쌓으면 실루엣이 정의로 맞는다.

    깊이(y)는 정면 원화가 안 준다 — 단면을 원으로 가정하고 y 는 노브로 받는다.
    """
    root = Vector((root_xz[0], y, root_xz[1]))
    tip = Vector((tip_xz[0], y, tip_xz[1]))
    d = tip - root
    Lp = d.length
    if Lp < 1e-9:
        return None
    u = d / Lp
    up = Vector((0, 1, 0))
    if abs(u.dot(up)) > 0.95:
        up = Vector((1, 0, 0))
    e0 = u.cross(up).normalized()
    e1 = u.cross(e0).normalized()
    n = len(half)
    rings, uvs, verts, faces = [], [], [], []
    for k in range(n):
        c = root + u * (Lp * k / (n - 1))
        r = max(half[k], 1e-5)
        rings.append([c + (e0 * math.cos(a) + e1 * math.sin(a)) * r
                      for a in (2 * math.pi * i / seg for i in range(seg))])
    for ring in rings:
        verts.extend([tuple(v) for v in ring])
    # UV: u = 둘레, v = 축 길이 (3D 거리 단위. layout 이 정규화한다)
    circ = [2 * math.pi * max(h, 1e-5) for h in half]
    for k in range(n - 1):
        a, b = k * seg, (k + 1) * seg
        v0, v1 = Lp * k / (n - 1), Lp * (k + 1) / (n - 1)
        for i in range(seg):
            j = (i + 1) % seg
            faces.append([a + i, a + j, b + j, b + i])
            uvs.append([((i / seg - 0.5) * circ[k], v0), (((i + 1) / seg - 0.5) * circ[k], v0),
                        (((i + 1) / seg - 0.5) * circ[k + 1], v1), ((i / seg - 0.5) * circ[k + 1], v1)])
    faces.append(list(range(seg))[::-1])                       # 뿌리 뚜껑
    rad = circ[0] / (2 * math.pi)
    uvs.append([(rad * math.cos(2 * math.pi * i / seg),
                 -rad * 1.3 + rad * math.sin(2 * math.pi * i / seg)) for i in range(seg)])
    return verts, faces, uvs


def layout(parts, margin=0.01):
    """3D 거리 단위로 나온 UV 조각들을 **한 판(0~1)** 에 선반 배치한다.

    오브젝트마다 제 0~1 을 쓰면 섬이 겹치고(채움 1.60) 텍셀 밀도가 2.4배 갈려서
    나중에 pack 을 따로 돌려야 했다. 축척을 하나만 쓰면 둘 다 저절로 없어진다.
    """
    boxes = []
    for _, _, uvs in parts:
        xs = [p[0] for f in uvs for p in f]
        ys = [p[1] for f in uvs for p in f]
        boxes.append((min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)))
    order = sorted(range(len(parts)), key=lambda i: -boxes[i][3])   # 큰 것부터
    # 선반 폭: 넓은 조각(캡 띠)은 무조건 들어가야 하고, 그 위에서 정사각에 가깝게.
    # max_width * 1.6 으로 잡았더니 채움이 11% 였다
    area = sum(b[2] * b[3] for b in boxes)
    W = max(max(b[2] for b in boxes), math.sqrt(area) * 1.15)
    place, x, y, shelf = {}, 0.0, 0.0, 0.0
    for i in order:
        _, _, w, h = boxes[i]
        if x > 0 and x + w > W:
            x, y, shelf = 0.0, y + shelf, 0.0
        place[i] = (x, y)
        x += w
        shelf = max(shelf, h)
    H = y + shelf
    k = (1 - 2 * margin) / max(W, H)
    out = []
    for i, (v, f, uvs) in enumerate(parts):
        ox, oy = place[i]
        bx, by = boxes[i][0], boxes[i][1]
        out.append((v, f, [[(margin + (p[0] - bx + ox) * k, margin + (p[1] - by + oy) * k)
                            for p in face] for face in uvs]))
    return out


def pauldron(spec):
    """정면 단면을 측면 윤곽에 맞춰 y 로 로프트한 캡 + 테두리 + 금뿔."""
    fp = [tuple(p) for p in spec["front"]["poly_xz"]]
    sp = [tuple(p) for p in spec["side"]["poly_yz"]]
    fz0 = min(p[1] for p in fp)
    fz1 = max(p[1] for p in fp)
    fxc = (min(p[0] for p in fp) + max(p[0] for p in fp)) / 2
    y0, y1 = spec["side"]["y"]

    def ring(y, s, zc):
        return [(fxc + (x - fxc) * s, y, zc + (z - (fz0 + fz1) / 2) * s) for x, z in fp]

    def span_scale(y, nudge):
        span = span_at(sp, y + nudge)
        if span is None:
            return None
        za, zb = span
        # 측면이 그 y 에서 허용하는 높이에 정면 단면을 맞춘다 (LESSONS 48 — 깊이는 읽는 것)
        return (zb - za) / (fz1 - fz0), (za + zb) / 2

    rings = []
    for k in range(STATIONS):
        t = k / (STATIONS - 1)
        y = y0 + (y1 - y0) * t
        nudge = 1e-4 if k == 0 else (-1e-4 if k == STATIONS - 1 else 0)
        sc = span_scale(y, nudge)
        if sc is None:
            continue
        s_, zc = sc
        if k in (0, STATIONS - 1):
            s_ *= END_S                       # 앞뒤 끝은 오므린다
        if k == GROOVE_AT:
            s_ *= GROOVE_S                    # 테두리 밴드 = 고리 홈 (셀에서 선으로 읽힌다)
        rings.append(ring(y, s_, zc))

    if BUILDER == "stack":
        rings, _ = stack(fp, sp, zlist=spec.get("crease_z"))
        # 견갑은 **속이 빈 껍질**이다. 원화에서 견갑 바로 아래는 74.6% 가 팔(dark)이고
        # 폭이 견갑 0.113 -> 팔 0.045 로 줄어든다 — 팔보다 2.5배 넓게 덮는 물건이다.
        # 아래를 막으면 감싸는 게 아니라 혹이 된다.
        parts = [shell(*bridge(rings, caps=(False, True)))]
    else:
        parts = [bridge(rings)]
    for h in spec["horns"]:
        parts.append(cone((h["root_xz"][0], h["root_y"], h["root_xz"][1]),
                          (h["tip_xz"][0], h["tip_y"], h["tip_xz"][1]), h["radius"]))
    parts = layout(parts)
    names = ["sh_pauldron_cap"] + [f"sh_horn{i}" for i in range(len(parts) - 1)]
    cols = [(LAVENDER, "m_lavender")] + [(GOLD, "m_gold")] * (len(parts) - 1)
    return [new_mesh(nm, v, f, c, mn, u)
            for nm, (v, f, u), (c, mn) in zip(names, parts, cols)]


def horns_only():
    """PART=horns 일 때 — horns.py 가 뽑은 프로파일로 뿔만 짓는다."""
    hj = json.load(open(os.path.join(HERE, "parts", "horns.json"), encoding="utf-8"))
    spec = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
    ymid = float(np.mean(spec["side"]["y"])) if "side" in spec else 0.0
    # 깊이(y)를 옛 계측에서 가져온다. **인덱스로 짝지으면 안 된다** —
    # 두 목록의 정렬이 달라 네 뿔이 전부 남의 y 를 받았다(0<->1, 2<->3 뒤집힘).
    # 뿌리 좌표로 최근접 짝짓기한다. 인덱스는 정렬 순서지 정체성이 아니다.
    old = spec.get("horns", [])
    def y_for(h):
        if not old:
            return ymid
        r = h["root_xz"]
        j = min(range(len(old)),
                key=lambda k: (old[k]["root_xz"][0] - r[0]) ** 2 + (old[k]["root_xz"][1] - r[1]) ** 2)
        d = math.hypot(old[j]["root_xz"][0] - r[0], old[j]["root_xz"][1] - r[1])
        return old[j].get("root_y", ymid) if d < 0.03 else ymid
    # 단축을 형태로 굳히지 않는다 — 공통 반각을 재고 기울기로 되돌린다
    rl = [(max(h["halfwidth"]) / max(h["length"], 1e-9)) for h in hj["horns"]]
    tan_a = min(rl)
    parts = []
    for i, h in enumerate(hj["horns"]):
        y = y_for(h)
        r0 = max(h["halfwidth"])
        L0 = r0 / tan_a
        c = min(h["length"] / max(L0, 1e-9), 1.0)
        tilt = math.degrees(math.acos(c))
        sign = 1.0 if i % 2 == 0 else -1.0        # 앞/뒤는 정면이 안 준다. 노브
        if os.environ.get("HORN_MODE") == "profile":
            r = horn_profile(h["root_xz"], h["tip_xz"], y, h["halfwidth"])
        else:
            r = horn_tilt(h["root_xz"], h["tip_xz"], y, L0, tilt, r0, sign)
        if r:
            parts.append(r)
    parts = layout(parts)
    return [new_mesh("horn%d" % i, v, f, GOLD, "m_gold", u)
            for i, (v, f, u) in enumerate(parts)]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    dst = os.path.abspath(argv[0])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if os.environ.get("PART") == "horns":
        obs = horns_only()
    elif os.environ.get("PART") == "cap":
        spec = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
        cj = json.load(open(os.path.join(HERE, "parts", "cap.json"), encoding="utf-8"))
        spec["front"]["poly_xz"] = cj["poly_xz"]
        if os.environ.get("CREASE", "1") == "1":
            spec["crease_z"] = cj["crease_z"]
        obs = pauldron(spec)
    else:
        spec = json.load(open(os.path.join(HERE, "parts", "sh_pauldron.json"), encoding="utf-8"))
        obs = pauldron(spec)
    tri = sum(len(o.data.polygons) for o in obs)
    v = sum(len(o.data.vertices) for o in obs)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=dst)
    print(f"BUILD OK objects={len(obs)} verts={v} faces={tri} -> {dst}")


if __name__ == "__main__":
    main()
